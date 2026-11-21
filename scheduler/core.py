"""The DigitalHeat scheduler: one hourly step, used by the yearly balance, the real-job
controller and the dashboard. Nothing else decides which job runs where.

Every hour t, for every site s (N servers of 1 kW, 80 % of the power recovered as heat,
a lossless tank of C kWh holding `soc` kWh, heat demand d[t] from the weather forecast):

 1. Heat signal      room = C - soc                     (kWh the tank can still take)
 2. Heat permit      permit = min(N, floor((d[t] + room) / 0.8))
                     the most servers whose heat is used this hour, now or later from the tank.
 3. Deadline reserve Rerank jobs arrive at fixed hours with a 4 h deadline. Looking 24 h
                     ahead, the scheduler keeps tank room for them, so that filling the tank
                     with flexible embedding work never forces a deadline job to dump heat later.
                     Backwards over the next 24 h, with q[h] = heat of the deadline jobs expected
                     at h (each placed at its last possible start):
                        U[t+25] = C
                        U[h]    = clamp(min(C, U[h+1]) - q[h] + d[h], 0, C)
                     U[t+1] is the most heat the tank may hold at the end of this hour, so
                        limit = min(permit, floor((U[t+1] + d[t] - soc) / 0.8))
 4. Queue manager    Deadline jobs, earliest deadline first, go to the site whose `limit` has
                     the largest free share of its servers (a job may move between sites).
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

The forecast is perfect (the 2025 weather itself): an assumption the case's own use case makes
("the system checks the weather forecast").
"""

import math
from dataclasses import dataclass, field

REC = 0.8  # recoverable share of a 1 kW server's power (case)
HORIZON = 24  # hours of look-ahead for the deadline reserve
RESUME_SOON_H = 2  # pause (SIGSTOP) if heat returns within this many hours, else checkpoint
EPS = 1e-9


@dataclass
class JobType:
    name: str
    sh: float  # server-hours per job on the 1 kW reference server
    due_h: float
    arrival_hours: tuple  # () = unlimited backlog
    deadline_job: bool  # True: arrives on a schedule and must meet its deadline


def job_types():
    """The measured job types (docs/workloads.md, workloads/catalog.py, team mean, gross basis)."""
    from workloads.catalog import reference_job_types

    jt = reference_job_types()
    return {
        "embed": JobType("embed", round(jt["embed"].server_hours_per_job, 4), jt["embed"].deadline_h, (), False),
        "rerank": JobType("rerank", round(jt["rerank"].server_hours_per_job, 4), jt["rerank"].deadline_h,
                          tuple(jt["rerank"].arrival_hours), True),
    }


@dataclass
class Job:
    id: int
    type: str
    origin: int
    arrive: int
    due: int
    work: float
    done: float = 0.0
    site: int = -1  # where it last ran / is held, -1 = fleet queue
    state: str = "queued"  # queued, running, paused, checkpointed, done, missed
    start: int = -1
    finish: int = -1
    forced: bool = False
    moves: int = 0
    pauses: int = 0
    checkpoints: int = 0

    @property
    def left(self):
        return self.work - self.done


@dataclass
class SiteHour:
    """Everything the scheduler computed for one site in one hour (the dashboard shows it)."""
    demand: float
    soc0: float
    room: float
    permit: int
    reserve_u: float
    limit: int
    running: int = 0
    forced: int = 0
    rerank_sh: float = 0.0
    embed_sh: float = 0.0
    heat: float = 0.0
    served: float = 0.0
    soc: float = 0.0
    dumped: float = 0.0
    paused: int = 0
    checkpointed: int = 0
    moved_in: int = 0
    started: int = 0
    finished: int = 0
    actions: list = field(default_factory=list)  # (job id, type, action)


class Scheduler:
    def __init__(self, sites, demand, types=None, pool=True):
        """sites: list of scheduler.sites.Site; demand: list of 8,760-hour lists (kW), the forecast."""
        self.sites = sites
        self.d = demand
        self.types = types or job_types()
        self.pool = pool
        self.n = len(sites)
        self.soc = [0.0] * self.n
        self.jobs = []
        self.open = []
        self.count = {}  # jobs created per type  # deadline and started jobs not finished
        self.H = len(demand[0]) if demand else 0
        self.deadline_types = [t for t in self.types.values() if t.deadline_job]
        self.backlog = [t for t in self.types.values() if not t.deadline_job]

    # ---- helpers -------------------------------------------------------------------------
    def _new(self, jt, origin, t):
        j = Job(len(self.jobs), jt.name, origin, t, t + int(jt.due_h), jt.sh)
        self.jobs.append(j)
        self.count[jt.name] = self.count.get(jt.name, 0) + 1
        self.open.append(j)
        return j

    def _d(self, s, h):
        return self.d[s][h] if h < self.H else self.d[s][h - self.H]  # after 31 Dec, January stands in

    def _reserve(self, s, t):
        """U[t+1]: most heat the tank may hold after hour t without a later deadline job dumping."""
        C = self.sites[s].tank_kwh
        q = [0.0] * (HORIZON + 2)
        for j in self.open:  # waiting deadline jobs of this site, at their last possible start
            if j.type != "embed" and j.state == "queued" and (j.origin == s):
                k = j.due - math.ceil(j.left - EPS) - t
                if 1 <= k <= HORIZON:
                    q[k] += REC * min(1.0, j.left)
        for jt in self.deadline_types:  # arrivals expected at this site in the next 24 h
            for k in range(1, HORIZON + 1):
                h = t + k
                if h % 24 in jt.arrival_hours:
                    last = k + int(jt.due_h) - math.ceil(jt.sh)
                    if last <= HORIZON:
                        q[last] += REC * jt.sh
        u = C
        for k in range(HORIZON, 0, -1):
            u = min(C, max(0.0, min(C, u) - q[k] + self._d(s, t + k)))
        return u

    def _will_have_heat(self, s, t):
        """Forecast: will site s have a heat permit in one of the next RESUME_SOON_H hours?"""
        soc = self.soc[s]
        C = self.sites[s].tank_kwh
        for k in range(1, RESUME_SOON_H + 1):
            dd = self._d(s, t + k)
            if dd + C - soc >= REC - EPS:
                return True
            soc = max(0.0, soc - dd)
        return False

    # ---- one hour ------------------------------------------------------------------------
    def step(self, t):
        """Decide and apply hour t. Returns the list of SiteHour (one per site)."""
        n = self.n
        hours = []
        # 1-3: heat signal, permit, reserve
        for s, site in enumerate(self.sites):
            d = self.d[s][t]
            room = site.tank_kwh - self.soc[s]
            permit = max(0, min(site.servers, math.floor((d + room) / REC + EPS)))
            u = self._reserve(s, t)
            limit = max(0, min(permit, math.floor((u + d - self.soc[s]) / REC + EPS)))
            hours.append(SiteHour(demand=d, soc0=self.soc[s], room=room, permit=permit, reserve_u=u, limit=limit))
        # arrivals
        if self.deadline_types:
            for jt in self.deadline_types:
                if t % 24 in jt.arrival_hours:
                    for s, site in enumerate(self.sites):
                        if site.servers > 0 or self.pool:
                            self._new(jt, s, t)
        cap = [float(h.limit) for h in hours]  # server-hours of heat-useful capacity left
        extra = [0] * n  # forced servers
        # 4a: deadline jobs, earliest deadline first
        deadline = sorted((j for j in self.open if j.type != "embed"), key=lambda j: (j.due, j.id))
        for j in deadline:
            need = min(1.0, j.left)
            cands = range(n) if self.pool else [j.origin]
            best = -1
            for c in cands:
                if cap[c] >= need - EPS and self.sites[c].servers > 0:
                    share = cap[c] / self.sites[c].servers
                    if best < 0 or share > cap[best] / self.sites[best].servers + EPS or (
                            abs(share - cap[best] / self.sites[best].servers) < EPS and c == j.origin):
                        best = c
            if best >= 0:
                cap[best] -= need
                self._run(j, best, need, t, hours)
                continue
            if j.due - t <= math.ceil(j.left - EPS):  # last possible hour: run anyway
                f = -1
                for c in cands:
                    if hours[c].limit + extra[c] < self.sites[c].servers:
                        if f < 0 or self.sites[c].tank_kwh - self.soc[c] > self.sites[f].tank_kwh - self.soc[f]:
                            f = c
                if f >= 0:
                    extra[f] += 1
                    cap[f] += 1.0 - need  # the rest of the forced server's hour goes to embedding
                    j.forced = True
                    hours[f].forced += 1
                    self._run(j, f, need, t, hours, action="forced")
        # 4b: embedding fills every permitted server
        for s in range(n):
            if cap[s] <= EPS:
                continue
            here = sorted((j for j in self.open if j.type == "embed" and j.site == s and j.state in ("running", "paused")),
                          key=lambda j: (j.due, j.id))
            for j in here:
                if cap[s] <= EPS:
                    break
                w = min(1.0, j.left, cap[s])
                cap[s] -= w
                self._run(j, s, w, t, hours)
        waiting = sorted((j for j in self.open if j.type == "embed" and j.state in ("queued", "checkpointed")),
                         key=lambda j: (j.due, j.id))
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
        # 6: heat balance
        for s, site in enumerate(self.sites):
            h = hours[s]
            h.running = h.limit + extra[s]
            h.heat = REC * h.running
            avail = self.soc[s] + h.heat
            h.served = min(h.demand, avail)
            soc = avail - h.served
            if soc > site.tank_kwh:
                h.dumped = soc - site.tank_kwh
                soc = site.tank_kwh
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
            if t + 1 >= j.due and j.done < j.work - EPS:
                j.state, j.finish = "missed", t + 1
                continue
            keep.append(j)
        self.open = keep
        return hours

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
        else:
            h.rerank_sh += w
        if a != "run":
            h.actions.append((j.id, j.type, a))
