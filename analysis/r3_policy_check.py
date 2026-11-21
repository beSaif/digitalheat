"""Round 3: does the ADOPTED policy hold together, and what does each extra rule buy?

ASSESSMENT ONLY. This is NOT the team's scheduler and must not become it.

    python3 analysis/r3_policy_check.py              # all sections, 3 seeds, all CPU cores
    python3 analysis/r3_policy_check.py --seeds 5    # more seeds
    python3 analysis/r3_policy_check.py --procs 1    # no multiprocessing
    python3 analysis/r3_policy_check.py --demo-only  # sections 0 and 4 only (fast)

Standard library only. Nothing is edited: it imports
  baseline_sweep.py     load(), simulate(), case constants
  r2_deadline_sim.py    base(), forecast_temps(), demand_from_temps(), offer_rates(),
                        poisson(), forward_fail() (the EDF dry run), run() (regression)
  r2_realism.py         sim() (regression of the run rules)

What round 2 never did: run the adopted rules TOGETHER. r2_deadline_sim.py has admission
and forecasts but only the plain follow rule; r2_realism.py has cap, band, hold and the
restart time but unlimited jobs and no deadlines. Here one loop has all of them:

  run rule      follow | band (stop when the tank is full, restart after it dropped by
                `band` kWh) | hold (band + servers that run keep running); cap1 = at most
                one server while there is no space heating
  admission     edf  = earliest-deadline-first dry run on forecast permits (r2 code)
                all  = no admission, every offer is accepted (what a core without
                       admission would do)
  adm_rule      the run rule the dry run rolls forward. Default: the execution rule.
                Set to 'follow' to see what happens when admission and execution disagree.
  forecast      perfect | persist | ifs025 (archived real forecasts), guard band in K,
                causal = the heating-day flag of a target hour uses only a series issued
                before now (lead index ceil((L+23)/24), clamped at 7 days)
  restart       minutes per server start that draw power and give heat but do no work;
                restart_aware = the dry run derates the permits of starting servers
  offers        saturating (N*24 server-h/day) | shaped100 (heat-shaped contract)

Simplifications to keep in mind (all stated again in docs/research/r3-one-scheduler-scope.md):
  no partner site, no hardware or network failure, no runtime overrun; work on a job that
  later misses still counts as sold; a job is not bound to a server (capacity is a pool,
  one job uses at most one server-hour per hour); the dry run assumes every forecast permit
  is used; 'causal' clamps at 7 days, so leads of 145 to 167 h still use a series that is up
  to 23 h fresher than available.
"""
import math
import random
import sys
from operator import itemgetter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import HEAT_VALUE, P_EL, PRICE, REC, TANK, load, simulate  # noqa: E402
import r2_deadline_sim as R  # noqa: E402

Q1 = REC * P_EL
EPS = 1e-9
HW = 0.5                      # flat hot water per hour, as in the reference profile
H_YEAR = 8760
HORIZON = 168
JT = R.JT
MONTH = R.MONTH


def pol(**kw):
    p = dict(rule="follow", band=0.0, cap1=False, adm="edf", adm_rule=None, fc="perfect",
             guard=0.0, causal=True, restart=0.0, aware=False)
    p.update(kw)
    if p["adm_rule"] is None:
        p["adm_rule"] = p["rule"]
    return p


BAND = dict(rule="band", band=8.0, cap1=True)
HOLD = dict(rule="hold", band=8.0, cap1=True)
POLICIES = {
    # --- minimal combination: plain follow + admission dry run, no forecast ingestion
    "M1 MINIMAL follow + adm(perfect)":          pol(),
    "M2 MINIMAL follow + adm(persistence)":      pol(fc="persist"),
    "M3  M2 + 2 K guard":                        pol(fc="persist", guard=2.0),
    # --- adding the round-2 rules one at a time
    "S1 follow + adm(archived ifs025)":          pol(fc="ifs025"),
    "S2  S1 + 2 K guard":                        pol(fc="ifs025", guard=2.0),
    "S3  S2 + cap + 8 kWh band":                 pol(fc="ifs025", guard=2.0, **BAND),
    "A  ADOPTED = S3 + restart 15 min, aware":   pol(fc="ifs025", guard=2.0, restart=15.0, aware=True, **BAND),
    # --- what the restart time does when the dry run does not know about it
    "A-  ADOPTED but dry run ignores restart":   pol(fc="ifs025", guard=2.0, restart=15.0, **BAND),
    "M1r M1 under a real 15 min restart":        pol(restart=15.0),
    "M2r M2 under a real 15 min restart":        pol(fc="persist", restart=15.0),
    "M3r M3 under a real 15 min restart":        pol(fc="persist", guard=2.0, restart=15.0),
    "M3a M3 + restart 15 min, aware":            pol(fc="persist", guard=2.0, restart=15.0, aware=True),
    # --- rules that fight
    "X1 cap+band executes, dry run uses follow": pol(fc="ifs025", guard=2.0, adm_rule="follow", **BAND),
    "X2 cap+band, perfect forecast":             pol(**BAND),
    "X3 band 8 without cap, perfect forecast":   pol(rule="band", band=8.0),
    "X4 cap only (no band), perfect forecast":   pol(cap1=True),
    # --- candidate and fallback
    "H  hold candidate (hold+cap+8), as A":      pol(fc="ifs025", guard=2.0, restart=15.0, aware=True, **HOLD),
    "F  FALLBACK no admission, plain follow":    pol(adm="all"),
    "Fr FALLBACK under a real 15 min restart":   pol(adm="all", restart=15.0),
}
DEMANDS = ("saturating", "shaped100")
NS = (6, 8)


# ---------------------------------------------------------------- the run rules
def step_permit(rule, band, cap1, n, d, soc, charging, kprev):
    """Servers allowed to run this hour. Same arithmetic as baseline_sweep.simulate()
    (follow) and r2_realism.sim() (r1band = 'band', hold); checked in section 0."""
    cap = n if (not cap1 or d - HW > EPS) else min(n, 1)
    kmax = min(cap, int((d + TANK - soc) / Q1 + 1e-9))
    if rule == "follow":
        return kmax, charging
    if rule == "band":
        if not charging and (soc <= TANK - band + EPS or soc < d):
            charging = True
        k = kmax if charging else 0
        if charging and kmax == 0:
            charging = False
        return k, charging
    if rule == "hold":
        kneed = min(kmax, max(0, math.ceil((d - soc) / Q1 - EPS)))
        if kprev > kmax:
            charging = False
        elif soc <= TANK - band + EPS:
            charging = True
        keep = min(kprev, kmax)
        if charging:
            return max(keep, kneed, min(kmax, math.ceil(d / Q1 - EPS) + 1)), charging
        return max(keep, kneed), charging
    raise ValueError(rule)


def permit_trace(n, rule="follow", band=0.0, cap1=False):
    """Unlimited jobs: every permit is used. -> list of (time, demand, k, soc_after, backup)."""
    rows = R.base()["rows"]
    soc, charging, kprev, out = 0.0, True, 0, []
    for t, sh, dhw in rows:
        d = sh + dhw
        k, charging = step_permit(rule, band, cap1, n, d, soc, charging, kprev)
        avail = soc + k * Q1
        u = min(d, avail)
        soc = avail - u
        kprev = k
        out.append((t, d, k, soc, d - u))
    return out


_FC = {}


def fc_demand(name, guard, seed):
    key = (name, guard)
    if key not in _FC:
        ft = R.forecast_temps(name, seed)
        _FC[key] = [R.base()["act_d"]] + [R.demand_from_temps(ft[k], 12.0 - guard) for k in range(1, 8)]
    return _FC[key]


# ---------------------------------------------------------------- one year with jobs
def run(n, P, demand="saturating", seed=1):
    b = R.base()
    act_d = b["act_d"]
    Fd = fc_demand(P["fc"], P["guard"], seed)
    rates = R.offer_rates(demand, n)
    rng = random.Random(seed)
    key0 = itemgetter(0)
    rule, band, cap1 = P["rule"], P["band"], P["cap1"]
    arule = P["adm_rule"]
    r = P["restart"] / 60.0
    lead = (lambda L: min(7, (L + 46) // 24)) if P["causal"] else (lambda L: (L + 23) // 24)
    LEAD = [lead(L) for L in range(HORIZON)]

    soc = used = dem_tot = dumped = sold_h = run_h = 0.0
    charging, kprev, on_prev = True, 0, 0
    starts = 0
    blocked_h = 0.0                    # server-hours a plain-follow permit existed, the rule
    jobs = []                          # withheld it, and accepted work was waiting
    off = [0, 0]; acc = [0, 0]; done = [0, 0]; missed = [0, 0]
    off_w = acc_w = missed_w = 0.0
    mon = [dict(acc=0, done=0, missed=0) for _ in range(12)]
    summer = dict(off=[0, 0], acc=[0, 0])
    ks_cap, ks_on = [], []

    for h in range(H_YEAR):
        m = MONTH[h]
        d = act_d[h]
        dem_tot += d
        if jobs:                       # jobs that can no longer finish are missed
            keep = []
            for j in jobs:
                if j[0] - h < math.ceil(j[2] - 1e-9):
                    missed[j[1]] += 1
                    missed_w += j[2]
                    mon[m]["missed"] += 1
                else:
                    keep.append(j)
            jobs = keep
        kfol = min(n, int((d + TANK - soc) / Q1 + 1e-9))
        ch_before = charging
        cap, charging = step_permit(rule, band, cap1, n, d, soc, charging, kprev)

        lam = [rates[m] * R.WORK_SHARE[i] / JT[i][1] / 24.0 for i in (0, 1)]
        arr = [R.poisson(rng, lam[0]), R.poisson(rng, lam[1])]
        if arr[0] or arr[1]:
            order = None
            if P["adm"] == "edf":
                # forecast permits for the next 168 h with the admission rule
                if arule == rule:
                    c0, ch = cap, charging
                else:
                    c0, ch = step_permit(arule, band, cap1, n, d, soc, ch_before, kprev)
                cf = [c0]
                s = soc + c0 * Q1
                s -= min(d, s)
                kp = c0
                for L in range(1, HORIZON):
                    dF = Fd[LEAD[L]][(h + L) % H_YEAR]
                    c, ch = step_permit(arule, band, cap1, n, dF, s, ch, kp)
                    s += c * Q1
                    s -= min(dF, s)
                    kp = c
                    cf.append(c)
                if P["aware"] and r > 0:
                    prev, cfe = on_prev, []
                    for c in cf:
                        cfe.append(min(c, prev) + max(0, c - prev) * (1.0 - r))
                        prev = c
                    cf = cfe
                cum, tot = [0.0], 0.0
                for c in cf:
                    tot += c
                    cum.append(tot)
                W = [0.0] * (HORIZON + 1)
                for j in jobs:
                    W[j[0] - h] += j[2]
                slack, w = [0.0] * (HORIZON + 1), 0.0
                for L in range(HORIZON + 1):
                    w += W[L]
                    slack[L] = cum[L] - w
            order = (0, 1) if rng.random() < 0.5 else (1, 0)
            new = []
            for i in order:
                if not arr[i]:
                    continue
                _, rt, dl = JT[i]
                off[i] += arr[i]
                off_w += arr[i] * rt
                if m in (5, 6, 7):
                    summer["off"][i] += arr[i]
                if P["adm"] == "edf":
                    room = min(slack[dl:])
                    k = max(0, min(arr[i], int(room / rt + 1e-9)))
                else:
                    k = arr[i]
                if k:
                    if P["adm"] == "edf":
                        for L in range(dl, HORIZON + 1):
                            slack[L] -= k * rt
                    for _ in range(k):
                        new.append([h + dl, i, rt])
                    jobs.extend(new[-k:])
                    acc[i] += k
                    acc_w += k * rt
                    mon[m]["acc"] += k
                    if m in (5, 6, 7):
                        summer["acc"][i] += k
            jobs.sort(key=key0)
            while new and P["adm"] == "edf":
                failing = R.forward_fail(jobs, h, cf, 1.0)
                if not failing:
                    break
                pick = next((j for j in failing if any(j is x for x in new)), None) or new[-1]
                new = [x for x in new if x is not pick]
                jobs = [j for j in jobs if j is not pick]
                acc[pick[1]] -= 1
                acc_w -= pick[2]
                mon[m]["acc"] -= 1
                if m in (5, 6, 7):
                    summer["acc"][pick[1]] -= 1

        # execution on the actual permits, earliest deadline first
        work = 0.0
        new_starts = 0
        if r <= 0:
            if jobs and cap > 0:
                fin = False
                for j in jobs:
                    step = min(j[2], 1.0, cap - work)
                    j[2] -= step
                    work += step
                    if j[2] <= 1e-9:
                        done[j[1]] += 1
                        mon[m]["done"] += 1
                        fin = True
                    if work >= cap - 1e-9:
                        break
                if fin:
                    jobs = [j for j in jobs if j[2] > 1e-9]
            on = int(math.ceil(work - 1e-9))
            new_starts = max(0, on - on_prev)
            ran = work
        else:
            warm = float(min(cap, on_prev))          # servers already running
            cold = (cap - min(cap, on_prev)) * (1.0 - r)   # work the newly started ones can do
            w_warm = w_cold = 0.0
            if jobs and cap > 0:
                fin = False
                for j in jobs:
                    if warm - w_warm > 1e-9:
                        step = min(j[2], 1.0, warm - w_warm)
                        w_warm += step
                    elif cold - w_cold > 1e-9:
                        step = min(j[2], 1.0 - r, cold - w_cold)
                        w_cold += step
                    else:
                        break
                    j[2] -= step
                    if j[2] <= 1e-9:
                        done[j[1]] += 1
                        mon[m]["done"] += 1
                        fin = True
                if fin:
                    jobs = [j for j in jobs if j[2] > 1e-9]
            work = w_warm + w_cold
            new_starts = int(math.ceil(w_cold / (1.0 - r) - 1e-9)) if w_cold > 1e-9 else 0
            on = (int(min(cap, on_prev)) + new_starts) if new_starts else int(math.ceil(w_warm - 1e-9))
            ran = work + new_starts * r
        if kfol > cap and jobs:
            waiting = sum(min(j[2], 1.0) for j in jobs) - 0.0
            blocked_h += min(float(kfol - cap), waiting)
        starts += new_starts
        avail = soc + ran * Q1
        u = min(d, avail)
        soc = avail - u
        dump = max(0.0, soc - TANK)
        soc -= dump
        used += u
        dumped += dump
        sold_h += work
        run_h += ran
        kprev, on_prev = cap, on
        ks_cap.append(cap)
        ks_on.append(on)

    closed = [done[i] + missed[i] for i in (0, 1)]
    ctot = max(1, sum(closed))
    elec = run_h * P_EL * PRICE
    sh_m = (3, 4, 9)                   # April, May, October
    sh_closed = sum(mon[m]["done"] + mon[m]["missed"] for m in sh_m)
    return dict(
        n=n, coverage=used / dem_tot, dumped=dumped, util=run_h / (n * H_YEAR), run_h=run_h,
        sold_h=sold_h, unsold_h=run_h - sold_h, starts=starts, blocked_h=blocked_h,
        offered=sum(off), accepted=sum(acc), acc_jobs=sum(acc) / max(1, sum(off)),
        acc_work=acc_w / max(1e-9, off_w), missed=sum(missed) / ctot, missed_n=sum(missed),
        done_n=sum(done), missed_j1=missed[0] / max(1, closed[0]), missed_j2=missed[1] / max(1, closed[1]),
        missed_work=missed_w / max(1e-9, acc_w),
        missed_shoulder=sum(mon[m]["missed"] for m in sh_m) / max(1, sh_closed),
        acc_j1_summer=summer["acc"][0] / max(1, summer["off"][0]),
        acc_j2_summer=summer["acc"][1] / max(1, summer["off"][1]),
        breakeven=(elec - used * HEAT_VALUE) / sold_h if sold_h else float("nan"),
        elec=elec, heat_val=used * HEAT_VALUE, ks_cap=ks_cap, ks_on=ks_on)


def task(cfg):
    n, demand, label, seed = cfg
    res = run(n, POLICIES[label], demand, seed)
    if seed != 1:                      # hourly traces are only needed once
        res.pop("ks_cap")
        res.pop("ks_on")
    return cfg, res


# ---------------------------------------------------------------- reporting
HDR = (f"{'policy':<44}{'cover':>7} {'dump':>5} {'util':>6} {'starts':>6} {'acc%job':>7} {'acc%wrk':>7} "
       f"{'MISSED% of accepted jobs':>26} {'mJ1%':>6} {'mJ2%':>6} {'mWork%':>6} {'AprMayOct%':>10} "
       f"{'sold h':>7} {'restart h':>9} {'BE/sold h':>9} {'blocked h':>9}")


def mean(res, key3, seeds, f):
    v = [res[key3 + (s,)][f] for s in seeds]
    return sum(v) / len(v), min(v), max(v)


def fmt(res, key3, seeds):
    a = lambda f: mean(res, key3, seeds, f)
    ms = a("missed")
    return (f"{key3[2]:<44}{a('coverage')[0]*100:>6.1f}% {a('dumped')[0]:>5.0f} {a('util')[0]*100:>5.1f}% "
            f"{a('starts')[0]:>6.0f} {a('acc_jobs')[0]*100:>6.1f}% {a('acc_work')[0]*100:>6.1f}% "
            f"{ms[0]*100:>9.3f} [{ms[1]*100:.3f}-{ms[2]*100:.3f}] {a('missed_j1')[0]*100:>6.3f} "
            f"{a('missed_j2')[0]*100:>6.3f} {a('missed_work')[0]*100:>6.3f} {a('missed_shoulder')[0]*100:>10.3f} "
            f"{a('sold_h')[0]:>7.0f} {a('unsold_h')[0]:>9.0f} {a('breakeven')[0]:>9.4f} {a('blocked_h')[0]:>9.0f}")


def slot_pattern(ks, slot):
    return "".join("#" if k >= slot else "." for k in ks)


def events(pat):
    """-> list of (hour, 'PAUSE'|'RESUME') for transitions inside the day."""
    return [(i + 1, "PAUSE" if a == "#" else "RESUME") for i, (a, b) in enumerate(zip(pat, pat[1:])) if a != b]


def demo_candidates(tr, n, month, slots, lo=2):
    """Days of `month` on which a slot is paused AND resumed (pause first), with the paused
    stretch lo..16 h, first event not before hour 2, last not after hour 22."""
    out = []
    days = sorted({x[0][:10] for x in tr if x[0][5:7] == month})
    for dd in days:
        day = [x for x in tr if x[0].startswith(dd)]
        ks = [x[2] for x in day]
        for s in slots:
            pat = slot_pattern(ks, s)
            ev = events(pat)
            pr = [(a, b) for a, b in zip(ev, ev[1:]) if a[1] == "PAUSE" and b[1] == "RESUME"]
            if not pr:
                continue
            (hp, _), (hr, _) = pr[0]
            if hp >= 2 and hr <= 22 and lo <= hr - hp <= 16:
                out.append(dict(date=dd, slot=s, pat=pat, pause=hp, resume=hr, n_events=len(ev),
                                demand=sum(x[1] for x in day), kmax=max(ks), kmin=min(ks),
                                backup=sum(x[4] for x in day)))
    return out


def section0():
    print("== 0. Regression checks (this file against the scripts it builds on) ==")
    rows = R.base()["rows"]
    import r2_realism as Z
    ok_all = True
    for n in NS:
        a = simulate(rows, n)
        tr = permit_trace(n)
        run_h = sum(x[2] for x in tr)
        ok = run_h == a["run_h"]
        ok_all &= ok
        print(f"  N={n} follow: baseline_sweep run_h {a['run_h']:.0f} | this file {run_h:.0f} -> {'OK' if ok else 'MISMATCH'}")
        for lab, kw_z, kw_me in (("cap + 8 kWh band", dict(rule="r1band", band=8, summer_cap=1), dict(rule="band", band=8.0, cap1=True)),
                                 ("hold + cap + 8", dict(rule="hold", band=8, summer_cap=1), dict(rule="hold", band=8.0, cap1=True))):
            z = Z.sim(rows, n, **kw_z)
            tr = permit_trace(n, **kw_me)
            ks = [x[2] for x in tr]
            st = sum(max(0, k - (ks[i - 1] if i else 0)) for i, k in enumerate(ks))
            ok = ks == z["ks"] and st == z["starts"]
            ok_all &= ok
            print(f"  N={n} {lab}: r2_realism starts {z['starts']}, coverage {z['coverage']*100:.2f}% | "
                  f"this file starts {st}, same hourly server counts: {ks == z['ks']} -> {'OK' if ok else 'MISMATCH'}")
    for n in NS:
        ref = R.run(n, "ifs025", "saturating", 0.0, None, "idle", 0.0, 1)
        me = run(n, pol(fc="ifs025", causal=False), "saturating", 1)
        ok = (ref["missed_n"], ref["accepted"]) == (me["missed_n"], me["accepted"]) and abs(ref["coverage"] - me["coverage"]) < 1e-12
        ok_all &= ok
        print(f"  N={n} follow + adm(ifs025, non-causal flag), saturating, seed 1: r2_deadline_sim accepted {ref['accepted']}, "
              f"missed {ref['missed_n']}, coverage {ref['coverage']*100:.3f}% | this file accepted {me['accepted']}, "
              f"missed {me['missed_n']}, coverage {me['coverage']*100:.3f}% -> {'OK' if ok else 'MISMATCH'}")
    print(f"  all regression checks: {'OK' if ok_all else 'MISMATCH'}")


def section4(res, seeds):
    print("\n== 4. Demo days: a pause AND a resume inside one simulated day ==")
    print("  permit level (every permit used); slot j runs in an hour iff at least j servers run; '#' run, '.' paused")
    print("  hour h in the event list = the transition happens at the START of simulated hour h (00..23)")
    tr_all = {}
    chosen = {}
    for plab, kw in (("ADOPTED rule: cap + 8 kWh band", dict(rule="band", band=8.0, cap1=True)),
                     ("MINIMAL rule: plain follow", dict()),
                     ("HOLD candidate: hold + cap + 8", dict(rule="hold", band=8.0, cap1=True))):
        for n in NS:
            tr = permit_trace(n, **kw)
            tr_all[(plab, n)] = tr
            print(f"\n  -- {plab}, N={n} --")
            for month, name, slots in (("01", "January", tuple(range(n, 0, -1))), ("07", "July", (1,))):
                c = demo_candidates(tr, n, month, slots)
                dates = sorted({x["date"] for x in c})
                print(f"  {name}: {len(dates)} of 31 days have a slot with pause-then-resume (stretch 2-16 h, events between hour 2 and 22)")
                if month == "07":
                    alld = sorted({x[0][:10] for x in tr if x[0][5:7] == "07"})
                    pats = [slot_pattern([y[2] for y in tr if y[0].startswith(dd)], 1) for dd in alld]
                    nev = [len(events(p)) for p in pats]
                    print(f"     July slot 1 transitions per day: min {min(nev)}, median {sorted(nev)[len(nev)//2]}, max {max(nev)}; "
                          f"days with no transition at all: {sum(1 for x in nev if x == 0)}")
                alld = sorted({x[0][:10] for x in tr if x[0][5:7] == month})
                if month == "01":
                    anyt = [dd for dd in alld if any(len(events(slot_pattern([y[2] for y in tr if y[0].startswith(dd)], s))) for s in slots)]
                    cold = max(alld, key=lambda dd: sum(y[1] for y in tr if y[0].startswith(dd)))
                    cd = [y for y in tr if y[0].startswith(cold)]
                    print(f"     January days with any pause or resume on any slot: {len(anyt)} of 31; coldest day {cold}: demand "
                          f"{sum(y[1] for y in cd):.1f} kWh, servers per hour {min(y[2] for y in cd)}-{max(y[2] for y in cd)}, "
                          f"backup {sum(y[4] for y in cd):.1f} kWh, transitions 0" if not any(len(events(slot_pattern([y[2] for y in cd], s))) for s in slots)
                          else f"     January days with any pause or resume on any slot: {len(anyt)} of 31; coldest day {cold} has transitions")
                else:
                    mid = [y[2] for y in tr if y[0].startswith("2025-07-15")]
                    print(f"     2025-07-15 slot 1: {slot_pattern(mid, 1)}")
                if not c and month == "07":   # plain follow: only one-hour pauses exist
                    c = [x for x in demo_candidates(tr, n, month, slots, lo=1) if x["date"] == "2025-07-15"]
                    if c:
                        print("     no pause of 2 h or more; falling back to 2025-07-15 and its first one-hour pause")
                if not c:
                    continue
                if month == "01":       # 'a cold January day': one clean pause if possible, then highest demand
                    best = max(c, key=lambda x: (x["n_events"] == 2, x["demand"], x["slot"]))
                else:                   # at least 4 h of running before the pause, then closest to mid-July
                    best = min(c, key=lambda x: (x["pause"] < 4, abs(int(x["date"][8:]) - 15), x["n_events"]))
                chosen[(plab, n, name)] = best
                for x in sorted(c, key=lambda x: -x["demand"])[:4] if month == "01" else sorted(c, key=lambda x: x["date"])[:6]:
                    print(f"     {x['date']} slot {x['slot']}: {x['pat']}  demand {x['demand']:5.1f} kWh, backup {x['backup']:4.1f} kWh, servers {x['kmin']}-{x['kmax']}, "
                          f"PAUSE {x['pause']:02d}:00 RESUME {x['resume']:02d}:00 ({x['resume']-x['pause']} h), {x['n_events']} transitions")
                print(f"     -> pick {best['date']} slot {best['slot']}")
    print("\n  -- band size as the demo knob: cap + band B (permit level, unlimited jobs) --")
    print(f"  {'N':>3} {'band':>5} {'starts/yr':>9} {'coverage':>9} {'July days with pause-then-resume':>33} {'July pause h':>12} {'July run h':>10} {'July transitions/day (median)':>30}")
    for n in NS:
        for bd in (0.0, 1.0, 2.0, 4.0, 8.0):
            tr = permit_trace(n, rule="band" if bd else "follow", band=bd, cap1=True)
            ks = [x[2] for x in tr]
            st = sum(max(0, k - (ks[i - 1] if i else 0)) for i, k in enumerate(ks))
            cov = 1.0 - sum(x[4] for x in tr) / sum(x[1] for x in tr)
            jul = "".join("#" if x[2] >= 1 else "." for x in tr if x[0][5:7] == "07")
            off = [len(z) for z in jul.replace("#", " ").split()]
            onn = [len(z) for z in jul.replace(".", " ").split()]
            c = demo_candidates(tr, n, "07", (1,))
            alld = sorted({x[0][:10] for x in tr if x[0][5:7] == "07"})
            nev = sorted(len(events(slot_pattern([y[2] for y in tr if y[0].startswith(dd)], 1))) for dd in alld)
            print(f"  {n:>3} {bd:>5.0f} {st:>9} {cov*100:>8.2f}% {len({x['date'] for x in c}):>33} "
                  f"{sorted(off)[len(off)//2]:>12} {sorted(onn)[len(onn)//2]:>10} {nev[len(nev)//2]:>30}")
            if bd in (2.0, 4.0):
                d15 = [y[2] for y in tr if y[0].startswith("2025-07-15")]
                pat = slot_pattern(d15, 1)
                print(f"        2025-07-15 slot 1: {pat}  events: " + ", ".join(f"{k} {h:02d}:00" for h, k in events(pat)))
    print("\n  -- real seconds from the start of that day, at s real seconds per simulated hour --")
    print(f"  {'policy':<32}{'N':>2} {'day':<8} {'date':<11}{'slot':>4} {'PAUSE':>6} {'RESUME':>7} {'paused':>7} "
          + " ".join(f"{'@'+format(s, '.1f')+'s: pause/resume/len':>28}" for s in (1.0, 1.5, 2.0, 2.5)))
    for (plab, n, name), x in chosen.items():
        cols = " ".join(f"{x['pause']*s:>9.1f}s/{x['resume']*s:>5.1f}s/{(x['resume']-x['pause'])*s:>5.1f}s   " for s in (1.0, 1.5, 2.0, 2.5))
        print(f"  {plab[:31]:<32}{n:>2} {name:<8} {x['date']:<11}{x['slot']:>4} {x['pause']:>4}:00 {x['resume']:>5}:00 "
              f"{x['resume']-x['pause']:>5} h {cols}")
    if res:
        print("\n  -- cross-check at job level (seed 1): servers actually working on those dates when jobs are finite --")
        print("     pattern of the same slot from the job-level run ('#' = at least `slot` servers have work)")
        rows = R.base()["rows"]
        idx = {}
        for i, (t, _, _) in enumerate(rows):
            idx.setdefault(t[:10], []).append(i)
        for (plab, n, name), x in chosen.items():
            labs = (["A  ADOPTED = S3 + restart 15 min, aware", "S3  S2 + cap + 8 kWh band"] if plab.startswith("ADOPTED")
                    else ["H  hold candidate (hold+cap+8), as A"] if plab.startswith("HOLD")
                    else ["M1 MINIMAL follow + adm(perfect)", "M2 MINIMAL follow + adm(persistence)"])
            for lab in labs:
                for dm in DEMANDS:
                    r1 = res.get((n, dm, lab, 1))
                    if not r1:
                        continue
                    on = [r1["ks_on"][i] for i in idx[x["date"]]]
                    cap = [r1["ks_cap"][i] for i in idx[x["date"]]]
                    pat = slot_pattern(on, x["slot"])
                    same = "same as permit level" if pat == x["pat"] else "DIFFERS from permit level"
                    print(f"     N={n} {name} {x['date']} slot {x['slot']} | {lab[:36]:<36} {dm:<10} {pat}  ({same}); "
                          f"permits {''.join(str(min(c, 9)) for c in cap)}")
    return chosen


def main():
    argv = sys.argv[1:]
    nseeds = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else 3
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    seeds = list(range(1, nseeds + 1))
    section0()
    if "--demo-only" in argv:
        section4({}, seeds)
        return

    cfgs = [(n, dm, lab, s) for n in NS for dm in DEMANDS for lab in POLICIES for s in seeds]
    print(f"\n({len(cfgs)} simulated years: {len(POLICIES)} policies x N in {NS} x {DEMANDS} x seeds {seeds})", flush=True)
    if procs == 1:
        out = [task(c) for c in cfgs]
    else:
        import multiprocessing as mp
        with mp.Pool(procs) as pool:
            out = pool.map(task, cfgs, chunksize=2)
    res = dict(out)

    print("\n== 1. ADOPTED against MINIMAL, and every step between ==")
    print("  no partner site; forecast error only; 'restart h' = server-hours spent starting (power and heat, no work);")
    print("  'blocked h' = server-hours where plain follow had a permit, the rule withheld it and accepted work waited;")
    print("                it measures DELAY, not lost work (compare 'sold h'): the band lowers the tank, which itself creates follow permits;")
    print("  AprMayOct% = missed share of accepted jobs closed in April, May and October")
    for n in NS:
        for dm in DEMANDS:
            print(f"\n  N={n}, offers: {dm}\n  {HDR}")
            for lab in POLICIES:
                print("  " + fmt(res, (n, dm, lab), seeds))

    print("\n== 2. What each extra rule buys (differences of seed means; cov in points, missed in points of accepted jobs) ==")
    steps = [("archived forecast instead of persistence (S1 - M2)", "M2 MINIMAL follow + adm(persistence)", "S1 follow + adm(archived ifs025)"),
             ("2 K guard on persistence (M3 - M2)", "M2 MINIMAL follow + adm(persistence)", "M3  M2 + 2 K guard"),
             ("2 K guard on archived forecast (S2 - S1)", "S1 follow + adm(archived ifs025)", "S2  S1 + 2 K guard"),
             ("cap + 8 kWh band (S3 - S2)", "S2  S1 + 2 K guard", "S3  S2 + cap + 8 kWh band"),
             ("restart 15 min, dry run aware (A - S3)", "S3  S2 + cap + 8 kWh band", "A  ADOPTED = S3 + restart 15 min, aware"),
             ("dry run aware of restart (A - A-)", "A-  ADOPTED but dry run ignores restart", "A  ADOPTED = S3 + restart 15 min, aware"),
             ("hold instead of band (H - A)", "A  ADOPTED = S3 + restart 15 min, aware", "H  hold candidate (hold+cap+8), as A"),
             ("ADOPTED - MINIMAL(perfect) (A - M1)", "M1 MINIMAL follow + adm(perfect)", "A  ADOPTED = S3 + restart 15 min, aware"),
             ("ADOPTED - MINIMAL(persist+guard, real restart) (A - M3r)", "M3r M3 under a real 15 min restart", "A  ADOPTED = S3 + restart 15 min, aware"),
             ("ADOPTED - M3a (persist+guard, restart aware)", "M3a M3 + restart 15 min, aware", "A  ADOPTED = S3 + restart 15 min, aware")]
    print(f"  {'step':<58}{'N':>2} {'offers':<10} {'d cover':>8} {'d util':>7} {'d starts':>8} {'d acc%wrk':>9} {'d missed':>9} {'d BE':>8}")
    for name, a, bb in steps:
        for n in NS:
            for dm in DEMANDS:
                g = lambda lab, f: mean(res, (n, dm, lab), seeds, f)[0]
                print(f"  {name:<58}{n:>2} {dm:<10} {(g(bb,'coverage')-g(a,'coverage'))*100:>+8.2f} {(g(bb,'util')-g(a,'util'))*100:>+7.2f} "
                      f"{g(bb,'starts')-g(a,'starts'):>+8.0f} {(g(bb,'acc_work')-g(a,'acc_work'))*100:>+9.2f} "
                      f"{(g(bb,'missed')-g(a,'missed'))*100:>+9.3f} {g(bb,'breakeven')-g(a,'breakeven'):>+8.4f}")

    print("\n== 3. Interactions: where rules fight ==")
    for n in NS:
        for dm in DEMANDS:
            g = lambda lab, f: mean(res, (n, dm, lab), seeds, f)
            print(f"  N={n} {dm}:")
            for lab in ("M1 MINIMAL follow + adm(perfect)", "X4 cap only (no band), perfect forecast", "X3 band 8 without cap, perfect forecast",
                        "X2 cap+band, perfect forecast", "X1 cap+band executes, dry run uses follow",
                        "S3  S2 + cap + 8 kWh band", "A-  ADOPTED but dry run ignores restart", "A  ADOPTED = S3 + restart 15 min, aware"):
                print(f"     {lab:<44} missed {g(lab,'missed')[0]*100:>7.3f}% (J1 {g(lab,'missed_j1')[0]*100:.3f}, J2 {g(lab,'missed_j2')[0]*100:.3f}), "
                      f"accepted work {g(lab,'acc_work')[0]*100:>5.1f}%, summer accepted J1 {g(lab,'acc_j1_summer')[0]*100:>5.1f}% / J2 {g(lab,'acc_j2_summer')[0]*100:>5.1f}% of offers, "
                      f"blocked {g(lab,'blocked_h')[0]:>5.0f} h, starts {g(lab,'starts')[0]:>5.0f}, coverage {g(lab,'coverage')[0]*100:.1f}%")

    section4(res, seeds)


if __name__ == "__main__":
    main()
