"""Round-1 exploratory job simulation (assessment only, NOT the team's scheduler).

    python3 analysis/r1_job_sim.py            # summary tables
    python3 analysis/r1_job_sim.py --monthly  # adds month-by-month view for N=8

Hourly year on the reference house, heat-following permits exactly as 'follow'
in baseline_sweep.py (a permit = one server-hour whose heat fits demand + tank).

Job model (see docs/research/r1-job-model.md; sizes are in reference-server hours):
  J1 short batch   0.5 server-h = 0.5 kWh, deadline 24 h,  pausable any time
  J2 long backlog  4.0 server-h = 4.0 kWh, deadline 168 h, pausable any time
  A job runs on one server at a time. Half of the arriving WORK is J1, half J2.
  Arrivals are flat and deterministic (no random seed): R server-hours per day.
Scheduling: earliest deadline first into the permits. A job is 'urgent' when it
must run every remaining hour to finish (deadline - now <= ceil(remaining)).
Deadline policies for urgent jobs that get no permit:
  nodump  never dump: the job leaves the house at its last possible moment.
          With a partner site it is 'moved' (finished elsewhere, assumed on time,
          NOT counted as completed here); without one it is a missed deadline.
          The script reports this one number as 'left%'.
  dump    run it anyway (up to N servers) and dump the heat; jobs beyond N are
          'missed'.
Demand scenarios:
  unlimited  every permit is filled (declared: infinite backlog, no deadlines)
  winter     flat R = mean follow server-h/day in Dec-Feb for that N
  annual     flat R = mean follow server-h/day over the year for that N
  summer     flat R = mean follow server-h/day in Jun-Aug (hot water only)
"""
import sys
from collections import deque
from math import ceil

from baseline_sweep import HEAT_VALUE, P_EL, PRICE, REC, TANK, load

TYPES = {"J1": dict(rt=0.5, deadline=24), "J2": dict(rt=4.0, deadline=168)}
WORK_SHARE = {"J1": 0.5, "J2": 0.5}
Q1 = REC * P_EL


def follow_rates(rows, n):
    """Mean permitted server-hours per day under pure heat-following."""
    soc, by_m = 0.0, {}
    for t, sh, dhw in rows:
        d = sh + dhw
        k = min(n, int((d + TANK - soc) / Q1 + 1e-9))
        soc = soc + k * Q1 - min(d, soc + k * Q1)
        by_m[t[5:7]] = by_m.get(t[5:7], 0) + k
    days = lambda ms: sum({"01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30, "07": 31,
                           "08": 31, "09": 30, "10": 31, "11": 30, "12": 31}[m] for m in ms)
    rate = lambda ms: sum(by_m[m] for m in ms) / days(ms)
    return {"winter": rate(["12", "01", "02"]), "annual": rate(sorted(by_m)),
            "summer": rate(["06", "07", "08"])}


def simulate(rows, n, rate=None, policy="nodump", types=TYPES):
    """rate = server-hours of work arriving per day (None = unlimited jobs)."""
    soc = used = dumped = run_h = demand = 0.0
    q = {j: deque() for j in types}            # each deque is sorted by deadline
    acc = {j: 0.0 for j in types}
    c = dict(arrived=0, done=0, left=0, missed=0, left_work=0.0)
    monthly = {}
    for h, (t, sh, dhw) in enumerate(rows):
        d = sh + dhw
        demand += d
        cap = min(n, int((d + TANK - soc) / Q1 + 1e-9))      # heat permits
        m = monthly.setdefault(t[5:7], dict(arr=0, done=0, left=0, missed=0, work=0.0, dump=0.0))
        if rate is None:
            work = float(cap)
        else:
            for j, ty in types.items():                      # flat arrivals
                acc[j] += rate * WORK_SHARE[j] / ty["rt"] / 24.0
                while acc[j] >= 1.0 - 1e-9:
                    acc[j] -= 1.0
                    q[j].append([h + ty["deadline"], ty["rt"]])
                    c["arrived"] += 1
                    m["arr"] += 1
            urgent = sorted((job for j in types for job in q[j]
                             if job[0] - h <= ceil(types[j]["rt"]) and job[0] - h <= ceil(job[1])),
                            key=lambda job: job[0])
            need = sum(min(job[1], 1.0) for job in urgent)
            if policy == "dump":
                cap = max(cap, min(n, ceil(need - 1e-9)))    # run urgent work, dump surplus
            work = 0.0
            for job in urgent:
                step = min(job[1], 1.0)
                if work + step <= cap + 1e-9:
                    job[1] -= step
                    work += step
                else:                                        # no server-hour for it
                    key = "missed" if policy == "dump" else "left"
                    c[key] += 1
                    m[key] += 1
                    c["left_work"] += job[1]
                    job[1] = -1.0                            # removed from the queue
            served = {id(job) for job in urgent}
            idx = {j: 0 for j in types}
            while work < cap - 1e-9:                         # EDF over the two queues
                best = None
                for j in types:
                    while idx[j] < len(q[j]) and (q[j][idx[j]][1] <= 0 or id(q[j][idx[j]]) in served):
                        idx[j] += 1
                    if idx[j] < len(q[j]) and (best is None or q[j][idx[j]][0] < q[best][idx[best]][0]):
                        best = j
                if best is None:
                    break
                job = q[best][idx[best]]
                step = min(job[1], 1.0, cap - work)
                job[1] -= step
                work += step
                idx[best] += 1
            for j in types:                                  # drop finished / removed jobs
                keep = deque()
                for job in q[j]:
                    if job[1] > 1e-9:
                        keep.append(job)
                    elif job[1] > -0.5:
                        c["done"] += 1
                        m["done"] += 1
                q[j] = keep
        avail = soc + work * Q1
        u = min(d, avail)
        soc = avail - u
        dump = max(0.0, soc - TANK)
        soc -= dump
        used += u
        dumped += dump
        run_h += work
        m["work"] += work
        m["dump"] += dump
    closed = max(1, c["done"] + c["left"] + c["missed"])     # jobs still open at year end excluded
    elec = run_h * P_EL * PRICE
    return dict(n=n, rate=rate, coverage=used / demand, dumped=dumped, util=run_h / (n * 8760),
                run_h=run_h, arrived=c["arrived"], done=c["done"] / closed, left=c["left"] / closed,
                missed=c["missed"] / closed, left_work=c["left_work"],
                breakeven=(elec - used * HEAT_VALUE) / run_h if run_h else float("nan"), monthly=monthly)


HDR = (f"{'N':>2} {'demand':<10}{'policy':<7} {'srv-h/d':>7} {'jobs/d':>6} {'cover':>6} {'dump kWh':>8} "
       f"{'util':>6} {'sold h':>7} {'done%':>6} {'left%':>6} {'miss%':>6} {'moved h':>7} {'BE CHF/h':>8}")


def line(r, name, policy):
    if r["rate"] is None:
        return (f"{r['n']:>2} {name:<10}{'-':<7} {'inf':>7} {'inf':>6} {r['coverage']*100:>5.1f}% {r['dumped']:>8.0f} "
                f"{r['util']*100:>5.1f}% {r['run_h']:>7.0f} {'n/a':>6} {'n/a':>6} {'n/a':>6} {'n/a':>7} {r['breakeven']:>8.4f}")
    jobs_d = sum(r["rate"] * WORK_SHARE[j] / TYPES[j]["rt"] for j in TYPES)
    return (f"{r['n']:>2} {name:<10}{policy:<7} {r['rate']:>7.1f} {jobs_d:>6.1f} {r['coverage']*100:>5.1f}% "
            f"{r['dumped']:>8.0f} {r['util']*100:>5.1f}% {r['run_h']:>7.0f} {r['done']*100:>5.1f}% "
            f"{r['left']*100:>5.1f}% {r['missed']*100:>5.1f}% {r['left_work']:>7.0f} {r['breakeven']:>8.4f}")


if __name__ == "__main__":
    rows = load()
    print("left% = urgent jobs with no heat permit under 'nodump': MOVED to another site if one exists,\n"
          "        otherwise MISSED deadlines. miss% = jobs that could not run even with dumping.\n"
          "moved h = server-hours of work that left the house. BE = break-even CHF per server-hour sold.\n")
    print(HDR)
    for n in (4, 6, 8, 10):
        rates = follow_rates(rows, n)
        print(line(simulate(rows, n), "unlimited", "-"))
        for name in ("winter", "annual", "summer"):
            for policy in ("nodump", "dump"):
                print(line(simulate(rows, n, rates[name], policy), name, policy))
        print()
    print("== sensitivity, N=8, annual-mean rate: do longer deadlines remove the problem? ==\n" + HDR)
    r8 = follow_rates(rows, 8)["annual"]
    for d1, d2 in ((24, 168), (72, 720), (168, 2160)):
        ty = {"J1": dict(rt=0.5, deadline=d1), "J2": dict(rt=4.0, deadline=d2)}
        for policy in ("nodump", "dump"):
            print(line(simulate(rows, 8, r8, policy, ty), f"{d1}h/{d2}h", policy))
    print("\n== sensitivity, N=8, nodump: flat rate between summer and winter sizing ==\n" + HDR)
    for rate in (15, 30, 50, 75, 100, 125, 150, 190):
        print(line(simulate(rows, 8, float(rate), "nodump"), f"flat {rate}", "nodump"))
    if "--monthly" in sys.argv:
        for policy in ("nodump", "dump"):
            r = simulate(rows, 8, r8, policy)
            print(f"\n== monthly, N=8, annual-mean rate {r8:.1f} srv-h/day, {policy} ==")
            print(f"{'month':<6}{'arrived':>8}{'done':>8}{'left':>8}{'missed':>8}{'sold h':>8}{'dump kWh':>9}")
            for mo, v in sorted(r["monthly"].items()):
                print(f"{mo:<6}{v['arr']:>8}{v['done']:>8}{v['left']:>8}{v['missed']:>8}{v['work']:>8.0f}{v['dump']:>9.0f}")
