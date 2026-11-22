"""The DigitalHeat scheduler: one hourly step, used by the yearly balance, the real-job
controller and the dashboard. Nothing else decides which job runs where.

Two input signals per site (what the case owner named):
 A. Heat: the heat demand d[t] from the weather forecast, the tank's state, and the supply
    temperature the site asks for (`supply_c`). No heat pump, no booster: a site that needs
    water hotter than the server loop gives (SERVER_OUTLET_C) gets no server heat.
 B. Redundancy: where each job's copies and data already are. Jobs of a type with
    `replicas` > 1 run as that many copies, never two on one site (RAID-1 across buildings),
    and go to the site that holds the fewest copies of other jobs, so losing one building
    touches as few jobs as possible.

Every hour t, for every site s (N servers of 1 kW, 80 % of the power recovered as heat,
a lossless tank of C kWh holding `soc` kWh, heat demand d[t]):

 1. Heat signal      room = C - soc                     (kWh the tank can still take)
 2. Heat permit      permit = min(N, floor((d[t] + room) / 0.8))
                     the most servers whose heat is used this hour, now or later from the tank.
                     0 if the site asks for a supply temperature above SERVER_OUTLET_C.
 3. Deadline reserve Deadline jobs arrive at fixed hours. Looking 24 h ahead, the scheduler
                     keeps tank room for the short-deadline ones, so that filling the tank with
                     flexible work never forces a deadline job to dump heat later.
                     Backwards over the next 24 h, with q[h] = heat of the deadline jobs expected
                     at h (each placed at its last possible start):
                        U[t+25] = C
                        U[h]    = clamp(min(C, U[h+1]) - q[h] + d[h], 0, C)
                     U[t+1] is the most heat the tank may hold at the end of this hour, so
                        limit = min(permit, floor((U[t+1] + d[t] - soc) / 0.8))
 4. Queue manager    Deadline jobs, earliest deadline first, go to the site whose `limit` has
                     the largest free share of its servers (a job may move between sites);
                     replicated jobs follow input B. Long-deadline batch jobs (simulations, due
                     in months) sit in the same queue: in summer there is little heat, so they
                     wait, and winter works them off ("defer to winter").
                     A deadline job that has no heat anywhere waits; in its last possible hour
                     it runs anyway on a spare server where the tank has most room ("forced";
                     heat the house cannot take is dumped). Embedding jobs (unlimited backlog)
                     fill every remaining permitted server: jobs already started first, then
                     jobs waiting at a checkpoint, then new ones.
 5. Jobs without heat An embedding job that gets no server this hour is
                       - paused (SIGSTOP, kept in memory on its server) if its site will have
                         heat again within 2 h,
                       - otherwise stopped at a checkpoint (SIGTERM, exit 75) and put back in
                         the fleet queue, where any site with heat resumes it ("moved").
 6. Heat balance     heat = 0.8 x servers running; served = min(d, soc + heat);
                     soc = soc + heat - served; anything above C is dumped.

Options (all off by default, so the reference figures do not change):
 - partial power: servers run at 30-100 % of their power (power capping), so the permit is
   no longer a whole number of servers. When heat demand is low, one server stays on 24/7
   at part load instead of filling the tank at full power and then switching off.
 - dry cooler (`Site.drycooler_kw` > 0): an outdoor radiator that dumps heat to the air
   (60 °C water is always warmer than outside). Forced and overflow heat go there. With
   `cool_fill`, spare servers also run backlog work whose heat goes straight to the cooler:
   more computing in summer, paid at the full electricity price plus fan power.
 - outages: a site is down for some hours (power cut, fire, network). Work held there is
   lost back to the last checkpoint stored elsewhere: a single job restarts from zero, a
   replicated job carries on from its copy on another site.

The forecast is perfect (the weather itself): an assumption the case's own use case makes
("the system checks the weather forecast").
"""

import math
from dataclasses import dataclass, field

REC = 0.8  # recoverable share of a 1 kW server's power (case)
HORIZON = 24  # hours of look-ahead for the deadline reserve
RESUME_SOON_H = 2  # pause (SIGSTOP) if heat returns within this many hours, else checkpoint
SERVER_OUTLET_C = 60.0  # warm-water cooled servers: loop outlet up to ~60 °C (DigitalHeat: 50-70 °C)
P_MIN = 0.3  # partial power: lowest power cap of a running server (share of 1 kW)
FAN_KW_PER_KW = 0.02  # dry cooler fan electricity per kW of heat rejected (Kelvion datasheet, design point)
EPS = 1e-9


@dataclass
class JobType:
    name: str
    sh: float  # server-hours per job on the 1 kW reference server
    due_h: float
    arrival_hours: tuple  # () = unlimited backlog
    deadline_job: bool  # True: arrives on a schedule and must meet its deadline
    replicas: int = 1  # copies on distinct sites (redundancy tier)
    per_site: bool = True  # True: one job per site at each arrival hour; False: `count` for the fleet
    count: int = 1


def job_types():
    """The measured job types (docs/workloads.md, workloads/catalog.py, team mean, gross basis)."""
    from workloads.catalog import reference_job_types

    jt = reference_job_types()
    return {
        "embed": JobType("embed", round(jt["embed"].server_hours_per_job, 4), jt["embed"].deadline_h, (), False),
        "rerank": JobType("rerank", round(jt["rerank"].server_hours_per_job, 4), jt["rerank"].deadline_h,
                          tuple(jt["rerank"].arrival_hours), True),
    }


SIM_SH, SIM_DUE_H = 8.0, 120 * 24
TWIN_SH, TWIN_DUE_H, TWIN_REPLICAS = 4.0, 24, 2


def service_job_types(sim_per_day=100, twin_per_day=6, replicas=TWIN_REPLICAS):
    """The service mix of the business case: the measured jobs plus two job types we define
    (our assumptions, docs/business-model.md):
      sim   simulation batch (e.g. a pharma customer's molecular dynamics or CFD runs):
            8 server-h each, due within 120 days, `sim_per_day` arrive for the whole fleet at
            midnight. Not time-critical, so it can wait for winter.
      twin  redundancy tier: a 4 server-h job (e.g. a day of bodycam video to analyse) run on
            `replicas` sites at once, due in 24 h, `twin_per_day` arrive for the fleet at 06:00.
    """
    t = job_types()
    if sim_per_day:
        t["sim"] = JobType("sim", SIM_SH, SIM_DUE_H, (0,), True, per_site=False, count=sim_per_day)
    if twin_per_day:
        t["twin"] = JobType("twin", TWIN_SH, TWIN_DUE_H, (6,), True, replicas=replicas, per_site=False,
                            count=twin_per_day)
    return t


@dataclass(slots=True)
class Job:
    id: int
    type: str
    origin: int
    arrive: int
    due: int
    work: float
    done: float = 0.0
    site: int = -1  # where it last ran / is held, -1 = fleet queue
    state: str = "queued"  # queued, running, paused, checkpointed, done, missed, lost
    start: int = -1
    finish: int = -1
    forced: bool = False
    moves: int = 0
    pauses: int = 0
    checkpoints: int = 0
    group: int = -1  # replicated jobs: id of the first copy; -1 = not replicated
    restarts: int = 0
    _ran: int = -1  # last hour it ran

    @property
    def left(self):
        return self.work - self.done


@dataclass
class SiteHour:
    """Everything the scheduler computed for one site in one hour (the dashboard shows it)."""
    demand: float
    soc0: float
    room: float
    permit: float
    reserve_u: float
    limit: float
    running: float = 0
    forced: int = 0
    rerank_sh: float = 0.0
    embed_sh: float = 0.0
    other_sh: float = 0.0  # sim, twin and other job types
    heat: float = 0.0
    served: float = 0.0
    soc: float = 0.0
    dumped: float = 0.0
    cooled: float = 0.0  # server-hours whose heat went straight to the dry cooler (cool_fill)
    fan_kwh: float = 0.0
    on: int = 0  # servers switched on (partial power: part-loaded servers count)
    down: bool = False
    paused: int = 0
    checkpointed: int = 0
    moved_in: int = 0
    started: int = 0
    finished: int = 0
    actions: list = field(default_factory=list)  # (job id, type, action)


class Scheduler:
    def __init__(self, sites, demand, types=None, pool=True, partial=False, cool_fill=False, outages=(),
                 keep_jobs=True):
        """sites: list of scheduler.sites.Site; demand: list of 8,760-hour lists (kW), the forecast.
        outages: (site index, first hour, hours) tuples.
        keep_jobs: keep every job ever created in self.jobs (the yearly balance counts them). With False
        only open jobs are kept: a year of backlog fill is millions of jobs, so a fast-forward to one
        moment (scheduler.day) runs in a fraction of the time and memory, with the same decisions."""
        self.sites = sites
        self.d = demand
        self.types = types or job_types()
        self.pool = pool
        self.partial = partial
        self.cool_fill = cool_fill
        self.outages = list(outages)
        self.n = len(sites)
        self.soc = [0.0] * self.n
        self.jobs = []
        self.keep_jobs = keep_jobs
        self.n_jobs = 0  # jobs created so far (job ids), also when they are not kept
        self.open = []
        self.groups = {}  # group id -> copies
        self.count = {}  # jobs created per type
        self.lost_sh = 0.0  # server-hours of work lost to outages
        self.H = len(demand[0]) if demand else 0
        self.deadline_types = [t for t in self.types.values() if t.deadline_job]
        self.backlog = [t for t in self.types.values() if not t.deadline_job]
        self.max_work = max((t.sh for t in self.types.values()), default=1.0)
        self._rr = 0  # round-robin origin for fleet-level arrivals

    # ---- helpers -------------------------------------------------------------------------
    def _new(self, jt, origin, t, group=-1):
        j = Job(self.n_jobs, jt.name, origin, t, t + int(jt.due_h), jt.sh, group=group)
        self.n_jobs += 1
        if self.keep_jobs:
            self.jobs.append(j)
        self.count[jt.name] = self.count.get(jt.name, 0) + 1
        self.open.append(j)
        return j

    def _arrive(self, jt, origin, t):
        if jt.replicas <= 1:
            return self._new(jt, origin, t)
        first = self._new(jt, origin, t, group=self.n_jobs)
        copies = [first] + [self._new(jt, origin, t, group=first.id) for _ in range(jt.replicas - 1)]
        self.groups[first.id] = copies
        return first

    def _d(self, s, h):
        return self.d[s][h] if h < self.H else self.d[s][h - self.H]  # after 31 Dec, January stands in

    def _down(self, s, t):
        return any(o[0] == s and o[1] <= t < o[1] + o[2] for o in self.outages)

    def _usable(self, s):
        return self.sites[s].supply_c <= SERVER_OUTLET_C + EPS

    def _blocked(self, j, c):
        """Input B, hard rule: no two copies of one job on one site."""
        if j.group < 0:
            return False
        return any(o is not j and o.site == c and o.state not in ("missed", "lost") for o in self.groups[j.group])

    def _exposure(self):
        """Input B, soft rule: per site, the open replicated jobs that hold a copy there."""
        held = [set() for _ in range(self.n)]
        for j in self.open:
            if j.group >= 0 and j.site >= 0:
                held[j.site].add(j.group)
        return [len(x) for x in held]

    def _arrivals(self, t):
        """Deadline-job arrivals expected at every site in the next 24 h, as (hour index, heat) in the
        order _reserve adds them; the same for all sites, so step() works it out once per hour."""
        out = []
        for jt in self.deadline_types:
            if not jt.per_site or jt.due_h > HORIZON:
                continue
            for k in range(1, HORIZON + 1):
                h = t + k
                if h % 24 in jt.arrival_hours:
                    last = k + int(jt.due_h) - math.ceil(jt.sh)
                    if last <= HORIZON:
                        out.append((last, REC * jt.sh * jt.replicas))
        return out

    def _reserve(self, s, t, short, arrivals=None):
        """U[t+1]: most heat the tank may hold after hour t without a later deadline job dumping.
        short: waiting deadline jobs (all, or only this site's); arrivals: self._arrivals(t)."""
        C = self.sites[s].tank_kwh
        q = [0.0] * (HORIZON + 2)
        for j in short:  # waiting deadline jobs of this site, at their last possible start
            if j.state == "queued" and j.origin == s:
                k = j.due - math.ceil(j.left - EPS) - t
                if 1 <= k <= HORIZON:
                    q[k] += REC * min(1.0, j.left)
        for k, v in (self._arrivals(t) if arrivals is None else arrivals):  # arrivals expected at this site
            q[k] += v
        u = C
        d, H = self.d[s], self.H
        for k in range(HORIZON, 0, -1):
            h = t + k
            u = min(C, max(0.0, min(C, u) - q[k] + (d[h] if h < H else d[h - H])))  # = self._d(s, h)
        return u

    def _will_have_heat(self, s, t):
        """Forecast: will site s have a heat permit in one of the next RESUME_SOON_H hours?"""
        soc = self.soc[s]
        C = self.sites[s].tank_kwh
        for k in range(1, RESUME_SOON_H + 1):
            dd = self._d(s, t + k)
            if dd + C - soc >= REC - EPS and not self._down(s, t + k):
                return True
            soc = max(0.0, soc - dd)
        return False

    def _outage_starts(self, t):
        """Work held on a site that goes down now is lost back to a copy elsewhere."""
        for s, start, hours in self.outages:
            if start != t or hours <= 0:
                continue
            for j in self.open:
                if j.site != s or j.state not in ("running", "paused", "checkpointed"):
                    continue
                alive = [o for o in self.groups.get(j.group, []) if o is not j and o.state not in ("missed", "lost")
                         and o.site != s]
                if alive:  # a copy on another site carries the job: this copy is dropped
                    j.state = "lost"
                    self.lost_sh += j.done
                    continue
                self.lost_sh += j.done
                j.done, j.site, j.state = 0.0, -1, "queued"
                j.restarts += 1
            self.open = [j for j in self.open if j.state != "lost"]

    # ---- one hour ------------------------------------------------------------------------
    def step(self, t):
        """Decide and apply hour t. Returns the list of SiteHour (one per site)."""
        n = self.n
        if self.outages:
            self._outage_starts(t)
        hours = []
        short = [j for j in self.open if j.type != "embed" and j.due - t <= HORIZON + math.ceil(self.max_work) + 1]
        by_site = [[] for _ in range(n)]  # the same jobs per origin, in the same order
        for j in short:
            if j.state == "queued" and 0 <= j.origin < n:
                by_site[j.origin].append(j)
        arrivals = self._arrivals(t)
        # 1-3: heat signal, permit, reserve
        for s, site in enumerate(self.sites):
            d = self.d[s][t]
            room = site.tank_kwh - self.soc[s]
            down = self._down(s, t)
            u = self._reserve(s, t, by_site[s], arrivals)
            if down or not self._usable(s):
                permit = limit = 0
            elif self.partial:
                permit = max(0.0, min(site.servers, (d + room) / REC))
                limit = max(0.0, min(permit, (u + d - self.soc[s]) / REC))
                if limit < P_MIN - EPS:
                    limit = 0.0
            else:
                permit = max(0, min(site.servers, math.floor((d + room) / REC + EPS)))
                limit = max(0, min(permit, math.floor((u + d - self.soc[s]) / REC + EPS)))
            hours.append(SiteHour(demand=d, soc0=self.soc[s], room=room, permit=permit, reserve_u=u, limit=limit,
                                  down=down))
        # arrivals
        for jt in self.deadline_types:
            if t % 24 in jt.arrival_hours:
                if jt.per_site:
                    for s, site in enumerate(self.sites):
                        if site.servers > 0 or self.pool:
                            self._arrive(jt, s, t)
                else:
                    for _ in range(jt.count):
                        self._arrive(jt, self._rr % n, t)
                        self._rr += 1
        cap = [float(h.limit) for h in hours]  # server-hours of heat-useful capacity left
        extra = [0] * n  # forced servers
        spare = lambda c: self.sites[c].servers - hours[c].limit - extra[c]  # noqa: E731
        # 4a: deadline jobs, earliest deadline first
        # (a started embedding job close to its deadline joins them, so long batch work cannot starve it)
        deadline = sorted((j for j in self.open if j.type != "embed" or (
            j.start >= 0 and j.due - t <= math.ceil(j.left - EPS) + RESUME_SOON_H)), key=lambda j: (j.due, j.id))
        far = math.ceil(self.max_work) + 1
        expo = self._exposure() if self.groups else [0] * n
        for j in deadline:
            need = min(1.0, j.left)
            last = j.due - t <= math.ceil(j.left - EPS)
            if sum(cap) <= EPS and not last:
                if j.due - t > far:
                    break  # sorted by deadline: no later job is in its last hour either
                continue
            cands = [c for c in (range(n) if self.pool else [j.origin])
                     if self.sites[c].servers > 0 and not hours[c].down and not self._blocked(j, c)]
            take = need if (last or not self.partial) else min(need, P_MIN)
            ok = [c for c in cands if cap[c] >= take - EPS]
            best = -1
            if ok:
                if j.site in ok:  # a started job stays where its data is while that site has heat
                    best = j.site
                elif j.group >= 0:  # input B: fewest copies of other jobs, then most free heat
                    best = min(ok, key=lambda c: (expo[c], -cap[c] / self.sites[c].servers, c != j.origin))
                else:
                    for c in ok:
                        share = cap[c] / self.sites[c].servers
                        if best < 0 or share > cap[best] / self.sites[best].servers + EPS or (
                                abs(share - cap[best] / self.sites[best].servers) < EPS and c == j.origin):
                            best = c
            if best >= 0:
                if j.group >= 0 and j.site != best:
                    expo[best] += 1
                w = min(need, cap[best])
                cap[best] -= w
                self._run(j, best, w, t, hours)
                continue
            if last:  # last possible hour: run anyway
                f = -1
                for c in cands:
                    if spare(c) >= 1 - EPS:
                        if f < 0 or self.sites[c].tank_kwh - self.soc[c] > self.sites[f].tank_kwh - self.soc[f]:
                            f = c
                if f >= 0:
                    extra[f] += 1
                    cap[f] += 1.0 - need  # the rest of the forced server's hour goes to embedding
                    j.forced = True
                    hours[f].forced += 1
                    self._run(j, f, need, t, hours, action="forced")
        # 4b: embedding fills every permitted server
        self._fill(cap, t, hours)
        cool = [0] * n
        if self.cool_fill:  # spare servers run backlog work, heat straight to the dry cooler
            ccap = [0.0] * n
            for s, site in enumerate(self.sites):
                if site.drycooler_kw > 0 and not hours[s].down:
                    ccap[s] = float(max(0, min(math.floor(spare(s) - cap[s] + EPS),
                                               math.floor(site.drycooler_kw / REC + EPS))))
            before = list(ccap)
            self._fill(ccap, t, hours)
            cool = [before[s] - ccap[s] for s in range(n)]
        # 6: heat balance
        for s, site in enumerate(self.sites):
            h = hours[s]
            useful = max(0.0, h.limit - cap[s]) if cap[s] > EPS else h.limit  # capacity no job took stays off
            h.running = useful + extra[s] + cool[s]
            h.cooled = cool[s]
            h.on = math.ceil(h.running - EPS)
            h.heat = REC * (useful + extra[s])
            avail = self.soc[s] + h.heat
            h.served = min(h.demand, avail)
            soc = avail - h.served
            if soc > site.tank_kwh:
                h.dumped = soc - site.tank_kwh
                soc = site.tank_kwh
            h.dumped += REC * cool[s]
            if site.drycooler_kw > 0:
                h.fan_kwh = FAN_KW_PER_KW * h.dumped
            self.soc[s] = soc
            h.soc = soc
        # 5: jobs that got no heat this hour; finish and miss
        keep = []
        for j in self.open:
            if j.done >= j.work - EPS:
                j.state, j.finish = "done", t + 1
                if j.site >= 0:
                    hours[j.site].finished += 1
                continue
            ran = getattr(j, "_ran", -1) == t
            if not ran and j.state in ("running", "paused") and j.type == "embed":
                if j.state == "running":
                    if self._will_have_heat(j.site, t):
                        j.state = "paused"
                        j.pauses += 1
                        hours[j.site].paused += 1
                        hours[j.site].actions.append((j.id, j.type, "paused"))
                    else:
                        j.state = "checkpointed"
                        j.checkpoints += 1
                        hours[j.site].checkpointed += 1
                        hours[j.site].actions.append((j.id, j.type, "checkpoint"))
                elif not self._will_have_heat(j.site, t):  # paused too long: free the server
                    j.state = "checkpointed"
                    j.checkpoints += 1
                    hours[j.site].checkpointed += 1
                    hours[j.site].actions.append((j.id, j.type, "checkpoint"))
            elif not ran and j.state == "running":  # a deadline job without heat waits at its checkpoint
                j.state = "checkpointed"
            if t + 1 >= j.due and j.done < j.work - EPS:
                j.state, j.finish = "missed", t + 1
                continue
            keep.append(j)
        self.open = keep
        return hours

    def _fill(self, cap, t, hours):
        """Embedding (unlimited backlog) fills the capacity left in `cap` (server-hours per site)."""
        n = self.n
        free = lambda j: getattr(j, "_ran", -1) != t  # noqa: E731  one server per job and hour
        for s in range(n):
            if cap[s] <= EPS:
                continue
            here = sorted((j for j in self.open if j.type == "embed" and j.site == s
                           and j.state in ("running", "paused") and free(j)), key=lambda j: (j.due, j.id))
            for j in here:
                if cap[s] <= EPS:
                    break
                w = min(1.0, j.left, cap[s])
                cap[s] -= w
                self._run(j, s, w, t, hours)
        waiting = sorted((j for j in self.open if j.type == "embed" and j.state in ("queued", "checkpointed")
                          and free(j)), key=lambda j: (j.due, j.id))
        taken = set()
        for s in range(n):  # a job waiting at a checkpoint resumes at its own site first
            for j in waiting:
                if cap[s] <= EPS:
                    break
                if j.site == s and j.id not in taken:
                    taken.add(j.id)
                    w = min(1.0, j.left, cap[s])
                    cap[s] -= w
                    self._run(j, s, w, t, hours)
        waiting = [j for j in waiting if j.id not in taken]
        wi = 0
        for s in range(n):
            while cap[s] > EPS:
                if wi < len(waiting):
                    j = waiting[wi]
                    wi += 1
                elif self.backlog:
                    j = self._new(self.backlog[0], s, t)
                else:
                    break
                w = min(1.0, j.left, cap[s])
                cap[s] -= w
                self._run(j, s, w, t, hours)

    def _run(self, j, s, w, t, hours, action=None):
        h = hours[s]
        if j.start < 0:
            j.start = t
            h.started += 1
            a = action or "start"
        elif j.site != s and j.site >= 0:
            j.moves += 1
            h.moved_in += 1
            a = action or "moved"
        elif j.state in ("paused", "checkpointed"):
            a = action or "resume"
        else:
            a = action or "run"
        j.site = s
        j.state = "running"
        j.done += w
        j._ran = t
        if j.type == "embed":
            h.embed_sh += w
        elif j.type == "rerank":
            h.rerank_sh += w
        else:
            h.other_sh += w
        if a != "run":
            h.actions.append((j.id, j.type, a))
