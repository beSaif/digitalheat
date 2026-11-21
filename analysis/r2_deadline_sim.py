"""Round-2 exploratory missed-deadline assessment (NOT the team's scheduler).

    python3 analysis/r2_deadline_sim.py              # all tables, 5 seeds, all CPU cores
    python3 analysis/r2_deadline_sim.py --seeds 3    # fewer seeds
    python3 analysis/r2_deadline_sim.py --procs 1    # no multiprocessing

Standard library only. Imports load() and the case constants from baseline_sweep.py and
the job types from r1_job_sim.py. Reads three small Open-Meteo downloads in
analysis/r2_data/ (URLs in docs/research/r2-missed-deadlines.md).

What round 1 lacked and this adds
  ADMISSION   A job offer is accepted only if the FORECAST heat-permit capacity before
              its deadline, times (1 - margin), minus the work already accepted with an
              earlier-or-equal deadline, still fits it (checked at every later deadline
              too, so no accepted job is pushed out). The hour's acceptances are then
              re-checked with an earliest-deadline-first dry run on the forecast that
              respects 'one server per job'; acceptances are taken back until no accepted
              job is forecast to fail. Rejected offers are 'not accepted' (they go to
              another site) and are never counted as missed.
  FORECAST    Admission and hand-off decisions see a forecast; execution sees the actual
              2025 weather of the reference house. Forecast for a target hour L hours
              ahead = the value issued ceil(L/24) days before (1..7). Variants:
                perfect    forecast = actual
                ifs025     REAL archived forecasts, ECMWF IFS 0.25 deg, Open-Meteo
                           Previous Runs API (same model family as the reference weather)
                ifs025gX   same, but a future day counts as a heating day only if its
                           forecast mean is below 12 - X degC (guard band against the
                           case's heating-day cliff)
                bestmatch  REAL archived forecasts, Open-Meteo 'best match' model mix
                synS       synthetic: actual + AR(1) error, day-1 RMSE S kelvin, growing
                           with lead like the measured ifs025 error, seeded
                syn2cold   syn2 plus a -1 K bias (forecast too cold = too many permits)
                persist    worst case: tomorrow and the next 7 days = the last 24 h
  HAND-OFF    An accepted job that the forecast says will miss is moved to a partner site
              at its last safe moment (deadline - now - remaining runtime == delay H).
              'moved' is counted separately. If the job was kept and the weather then
              turns out warmer, it is too late to move: 'missed'. H = none means there is
              no partner at all. The partner is assumed to have room (partner_full = share
              of hand-offs it refuses, sensitivity only).
  DEMAND      saturating  offers of N*24 server-h/day: the declared 'unlimited jobs' case
              flat        offers flat at the 2020-24 mean heat-following capacity
              shapedXX    monthly contract = XX % of the 2020-24 mean capacity of that
                          month (the contract cannot know the 2025 weather)
  SOLD SHARE  realised = paid server-hours hosted / heat-permit hours of the plain follow
              rule. shaped100/70/40 set it. An unsold permit hour is either
                idle    server off, backup heater covers the heat (default), or
                filler  server runs unpaid work; the hour counts as run, not as sold.
              Break-even = (electricity cost - value of heat used) / server-hours SOLD.

Job types (round 1, unchanged): J1 0.5 server-h, 24 h deadline; J2 4 server-h, 168 h
deadline; half the offered WORK each; a job uses at most one server at a time; Poisson
arrivals (seeded). Execution: earliest deadline first into the actual heat permits of the
'follow' rule (never dumps). A job that can no longer finish is removed as missed.
"""
import csv
import math
import random
import sys
from operator import itemgetter

from baseline_sweep import HEAT_VALUE, P_EL, PRICE, REC, ROOT, TANK, load
from baseline_sweep import simulate as follow_simulate
from r1_job_sim import TYPES

Q1 = REC * P_EL
H_YEAR = 8760
HORIZON = 168
DATA = ROOT / "analysis" / "r2_data"
JT = [("J1", TYPES["J1"]["rt"], TYPES["J1"]["deadline"]),
      ("J2", TYPES["J2"]["rt"], TYPES["J2"]["deadline"])]
WORK_SHARE = (0.5, 0.5)
MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# ---------------------------------------------------------------- inputs
def actual_temps():
    with open(ROOT / "data" / "reference_house_2025_hourly.csv") as f:
        return [float(r["temperature_2m_c"]) for r in csv.DictReader(f)]


def demand_from_temps(temps, thr=12.0):
    """Case formula applied to any temperature series (heating-day rule per 24 h block)."""
    out = []
    for d in range(len(temps) // 24):
        day = temps[d * 24:(d + 1) * 24]
        heating = sum(day) / 24.0 < thr
        for t in day:
            out.append((max(0.0, 10.0 * (20.0 - t) / 25.6) if heating else 0.0) + 0.5)
    return out


def read_prev_runs(name):
    """Open-Meteo Previous Runs CSV -> list K=0..7 of 8760 temperatures (K = days before)."""
    lines = (DATA / name).read_text().split("\n")[4:]
    cols = [[] for _ in range(8)]
    for ln in lines:
        if not ln:
            continue
        p = ln.split(",")
        for k in range(8):
            cols[k].append(float(p[1 + k]))
    return cols


def read_archive_years():
    """2020-2024 hourly temperatures (29 Feb dropped) -> {year: [8760]}."""
    years = {}
    for ln in (DATA / "archive_basel_2020_2024_ecmwf_ifs.csv").read_text().split("\n")[4:]:
        if not ln or ln[5:10] == "02-29":
            continue
        t, v = ln.split(",")
        years.setdefault(t[:4], []).append(float(v))
    return years


def month_of_hour():
    out = []
    for m, d in enumerate(MDAYS):
        out += [m] * (d * 24)
    return out


MONTH = month_of_hour()


def follow_monthly(dem, n):
    """Mean heat-permit server-hours per day by month under the plain follow rule."""
    soc, by_m = 0.0, [0.0] * 12
    for h, d in enumerate(dem):
        k = min(n, int((d + TANK - soc) / Q1 + 1e-9))
        soc = soc + k * Q1 - min(d, soc + k * Q1)
        by_m[MONTH[h]] += k
    return [by_m[m] / MDAYS[m] for m in range(12)]


def err_stats(fc, act):
    e = [a - b for a, b in zip(fc, act)]
    n = len(e)
    mean = sum(e) / n
    rmse = math.sqrt(sum(x * x for x in e) / n)
    mae = sum(abs(x) for x in e) / n
    var = sum((x - mean) ** 2 for x in e)
    rho = sum((e[i] - mean) * (e[i - 1] - mean) for i in range(1, n)) / var if var else 0.0
    return mean, mae, rmse, rho


# ---------------------------------------------------------------- forecasts
_CACHE = {}


def base():
    if "base" not in _CACHE:
        act_t = actual_temps()
        rows = load()
        act_d = [sh + dhw for _, sh, dhw in rows]
        rebuilt = demand_from_temps(act_t)
        assert max(abs(a - b) for a, b in zip(act_d, rebuilt)) < 1e-3, "demand rebuild mismatch"
        ifs = read_prev_runs("prev_ecmwf_ifs025.csv")
        ratios = [err_stats(ifs[k], act_t)[2] for k in range(1, 8)]
        rho = err_stats(ifs[1], act_t)[3]
        _CACHE["base"] = dict(act_t=act_t, act_d=act_d, rows=rows, ifs=ifs,
                              ratios=[r / ratios[0] for r in ratios], rho=rho)
    return _CACHE["base"]


def forecast_temps(name, seed):
    """-> list K=0..7 of temperature series; K=0 is the actual weather."""
    b = base()
    act = b["act_t"]
    if name == "perfect":
        return [act] * 8
    if name.startswith("ifs025"):          # ifs025gX = same temperatures, guard band in demand
        return [act] + b["ifs"][1:]
    if name == "bestmatch":
        return [act] + read_prev_runs("prev_runs_basel_2025.csv")[1:]
    if name == "persist":
        return [act] + [[act[(t - 24 * k) % H_YEAR] for t in range(H_YEAR)] for k in range(1, 8)]
    if name.startswith("syn"):
        bias = -1.0 if name.endswith("cold") else 0.0
        s1 = float(name[3:].replace("cold", ""))
        rng = random.Random(100000 + seed)
        rho = b["rho"]
        inn = math.sqrt(1.0 - rho * rho)
        out, prev_e, prev_s = [act], [0.0] * H_YEAR, 0.0
        for k in range(1, 8):
            s = s1 * b["ratios"][k - 1]
            add = math.sqrt(max(0.0, s * s - prev_s * prev_s))
            z, e = rng.gauss(0, 1), []
            for t in range(H_YEAR):
                z = rho * z + inn * rng.gauss(0, 1)
                e.append(prev_e[t] + add * z)      # error grows with lead, revisions independent
            out.append([a + x + bias for a, x in zip(act, e)])
            prev_e, prev_s = e, s
        return out
    raise ValueError(name)


def forecast_demand(name, seed):
    key = (name, seed if name.startswith("syn") else 0)
    if key not in _CACHE:
        ft = forecast_temps(name, seed)
        guard = float(name[7:]) if name.startswith("ifs025g") else 0.0
        _CACHE[key] = [base()["act_d"]] + [demand_from_temps(ft[k], 12.0 - guard) for k in range(1, 8)]
    return _CACHE[key]


def normal_capacity(n):
    key = ("normal", n)
    if key not in _CACHE:
        per_year = {y: follow_monthly(demand_from_temps(t), n) for y, t in read_archive_years().items()}
        mean = [sum(v[m] for v in per_year.values()) / len(per_year) for m in range(12)]
        _CACHE[key] = (mean, per_year)
    return _CACHE[key]


def offer_rates(demand, n):
    """Offered work in server-hours per day, by month."""
    if demand == "saturating":
        return [24.0 * n] * 12
    mean, _ = normal_capacity(n)
    if demand == "flat":
        return [sum(mean[m] * MDAYS[m] for m in range(12)) / 365.0] * 12
    if demand.startswith("shaped"):
        s = float(demand[6:]) / 100.0
        return [s * x for x in mean]
    raise ValueError(demand)


def poisson(rng, lam):
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


# ---------------------------------------------------------------- simulation
def forward_fail(jobs, h, cf, scale):
    """Earliest-deadline-first dry run on the forecast permits cf (hours h..h+167), each job
    on at most one server per hour. Returns the jobs that would not finish in time."""
    rem = [j[2] for j in jobs]
    nj, start = len(jobs), 0
    for L in range(HORIZON):
        c = cf[L] * scale
        if c <= 1e-9:
            continue
        while start < nj and rem[start] <= 1e-9:
            start += 1
        if start >= nj:
            break
        x, now = start, h + L
        while x < nj and c > 1e-9:
            r = rem[x]
            if r > 1e-9 and jobs[x][0] > now:
                step = r if r < 1.0 else 1.0
                if step > c:
                    step = c
                rem[x] = r - step
                c -= step
            x += 1
    return [jobs[x] for x in range(nj) if rem[x] > 1e-9]


def run(n, fc="ifs025", demand="saturating", margin=0.0, handoff=1, unsold="idle",
        partner_full=0.0, seed=1):
    """One year. handoff: hours of hand-off delay, or None for 'no partner site'."""
    b = base()
    act_d = b["act_d"]
    F = forecast_demand(fc, seed)
    rates = offer_rates(demand, n)
    rng = random.Random(seed)
    key0 = itemgetter(0)

    soc = used = dem_tot = dumped = sold_h = run_h = 0.0
    jobs = []                       # [deadline, type, remaining, movable]
    off = [0, 0]; acc = [0, 0]; done = [0, 0]; moved = [0, 0]; missed = [0, 0]
    off_w = acc_w = moved_w = missed_w = 0.0
    refused = 0
    mon = [dict(acc=0, done=0, moved=0, missed=0, sold=0.0) for _ in range(12)]

    for h in range(H_YEAR):
        m = MONTH[h]
        d = act_d[h]
        dem_tot += d
        # 0. jobs that can no longer finish are missed
        if jobs:
            keep = []
            for j in jobs:
                if j[0] - h < math.ceil(j[2] - 1e-9):
                    missed[j[1]] += 1
                    missed_w += j[2]
                    mon[m]["missed"] += 1
                else:
                    keep.append(j)
            jobs = keep
        # 1. actual heat permits this hour
        cap = min(n, int((d + TANK - soc) / Q1 + 1e-9))
        # 2. forecast permits for the next 168 h (this hour is known)
        cf = [cap]
        cum = [0.0, float(cap)]
        s = soc + cap * Q1
        s -= min(d, s)
        tot = float(cap)
        for L in range(1, HORIZON):
            dF = F[(L + 23) // 24][(h + L) % H_YEAR]
            c = min(n, int((dF + TANK - s) / Q1 + 1e-9))
            s += c * Q1
            s -= min(dF, s)
            cf.append(c)
            tot += c
            cum.append(tot)
        # 3. offers and admission
        lam = [rates[m] * WORK_SHARE[i] / JT[i][1] / 24.0 for i in (0, 1)]
        arr = [poisson(rng, lam[0]), poisson(rng, lam[1])]
        if arr[0] or arr[1]:
            W = [0.0] * (HORIZON + 1)
            for j in jobs:
                W[j[0] - h] += j[2]
            slack, w = [0.0] * (HORIZON + 1), 0.0
            for L in range(HORIZON + 1):
                w += W[L]
                slack[L] = (1.0 - margin) * cum[L] - w
            order = (0, 1) if rng.random() < 0.5 else (1, 0)
            new = []
            for i in order:
                if not arr[i]:
                    continue
                _, rt, dl = JT[i]
                off[i] += arr[i]
                off_w += arr[i] * rt
                room = min(slack[dl:])
                k = max(0, min(arr[i], int(room / rt + 1e-9)))
                if k:
                    for L in range(dl, HORIZON + 1):
                        slack[L] -= k * rt
                    for _ in range(k):
                        new.append([h + dl, i, rt, True])
                    jobs.extend(new[-k:])
                    acc[i] += k
                    acc_w += k * rt
                    mon[m]["acc"] += k
            jobs.sort(key=key0)
            # exact re-check on the forecast, with the one-server-per-job limit:
            # take back this hour's acceptances until no accepted job is forecast to fail
            while new:
                failing = forward_fail(jobs, h, cf, 1.0 - margin)
                if not failing:
                    break
                pick = next((j for j in failing if any(j is x for x in new)), None) or new[-1]
                new = [x for x in new if x is not pick]
                jobs = [j for j in jobs if j is not pick]
                acc[pick[1]] -= 1
                acc_w -= pick[2]
                mon[m]["acc"] -= 1
        # 4. hand-off at the last safe moment, decided on the forecast
        if handoff is not None and jobs:
            cand = [j for j in jobs if j[3] and j[0] - h - math.ceil(j[2] - 1e-9) == handoff]
            while cand:
                dmax = max(j[0] for j in cand)
                near = [j for j in jobs if j[0] <= dmax]
                rem = [j[2] for j in near]
                for L in range(dmax - h):
                    c = float(cf[L])
                    if c <= 0:
                        continue
                    for x, j in enumerate(near):
                        if rem[x] > 1e-9 and j[0] > h + L:
                            step = min(rem[x], 1.0, c)
                            rem[x] -= step
                            c -= step
                            if c <= 1e-9:
                                break
                failing = [near[x] for x in range(len(near)) if rem[x] > 1e-9]
                pick = next((j for j in failing if any(j is c_ for c_ in cand)), None)
                if pick is None:
                    break
                cand = [c_ for c_ in cand if c_ is not pick]
                if partner_full and rng.random() < partner_full:
                    pick[3] = False             # partner refused, job stays here
                    refused += 1
                    continue
                moved[pick[1]] += 1
                moved_w += pick[2]
                mon[m]["moved"] += 1
                jobs = [j for j in jobs if j is not pick]
        # 5. execution on the actual permits, earliest deadline first
        work = 0.0
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
        ran = float(cap) if unsold == "filler" else work
        avail = soc + ran * Q1
        u = min(d, avail)
        soc = avail - u
        dump = max(0.0, soc - TANK)
        soc -= dump
        used += u
        dumped += dump
        sold_h += work
        run_h += ran
        mon[m]["sold"] += work

    closed = [done[i] + moved[i] + missed[i] for i in (0, 1)]
    ctot = max(1, sum(closed))
    elec = run_h * P_EL * PRICE
    return dict(
        n=n, coverage=used / dem_tot, dumped=dumped, util=run_h / (n * H_YEAR), run_h=run_h,
        sold_h=sold_h, offered=sum(off), accepted=sum(acc),
        acc_jobs=sum(acc) / max(1, sum(off)), acc_work=acc_w / max(1e-9, off_w),
        missed=sum(missed) / ctot, moved=sum(moved) / ctot, done=sum(done) / ctot,
        missed_n=sum(missed), moved_n=sum(moved), done_n=sum(done),
        missed_j1=missed[0] / max(1, closed[0]), missed_j2=missed[1] / max(1, closed[1]),
        missed_work=missed_w / max(1e-9, acc_w), moved_work=moved_w / max(1e-9, acc_w),
        refused=refused, breakeven=(elec - used * HEAT_VALUE) / sold_h if sold_h else float("nan"),
        elec=elec, heat_val=used * HEAT_VALUE, mon=mon)


def task(cfg):
    n, fc, demand, margin, handoff, unsold, pfull, seed = cfg
    return cfg, run(n, fc, demand, margin, handoff, unsold, pfull, seed)


# ---------------------------------------------------------------- reporting
def agg(res, cfg7, seeds, field):
    v = [res[cfg7 + (s,)][field] for s in seeds]
    return sum(v) / len(v), min(v), max(v)


HDR = (f"{'N':>2} {'demand':<10} {'forecast':<9} {'marg':>4} {'hand':>4} {'unsold':<6} {'cover':>6} {'dump':>5} "
       f"{'util':>6} {'sold h':>7} {'sold%':>6} {'acc%job':>7} {'acc%wrk':>7} {'done%':>6} {'moved%':>6} "
       f"{'MISSED% mean [min-max]':>24} {'BE/sold h':>9} {'mJ1%':>6} {'mJ2%':>6} {'mWork%':>6}")


def fmt(res, cfg7, seeds, follow_h):
    n, fc, demand, margin, handoff, unsold, _ = cfg7
    a = lambda f: agg(res, cfg7, seeds, f)
    ms = a("missed")
    return (f"{n:>2} {demand:<10} {fc:<9} {margin*100:>3.0f}% {('none' if handoff is None else str(handoff)+'h'):>4} "
            f"{unsold:<6} {a('coverage')[0]*100:>5.1f}% {a('dumped')[0]:>5.0f} {a('util')[0]*100:>5.1f}% "
            f"{a('sold_h')[0]:>7.0f} {a('sold_h')[0]/follow_h[n]*100:>5.1f}% {a('acc_jobs')[0]*100:>6.1f}% "
            f"{a('acc_work')[0]*100:>6.1f}% {a('done')[0]*100:>5.1f}% {a('moved')[0]*100:>5.2f}% "
            f"{ms[0]*100:>8.3f} [{ms[1]*100:.3f}-{ms[2]*100:.3f}] {a('breakeven')[0]:>9.4f} "
            f"{a('missed_j1')[0]*100:>6.3f} {a('missed_j2')[0]*100:>6.3f} {a('missed_work')[0]*100:>6.3f}")


def main():
    argv = sys.argv[1:]
    nseeds = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else 5
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    seeds = list(range(1, nseeds + 1))
    b = base()
    act_t = b["act_t"]

    print("== 0. Forecast error against the reference-house temperature (2025, 8,760 h, kelvin) ==")
    print("   forecast - actual; 'day K' = value issued K days before the valid hour")
    for label, cols in (("ECMWF IFS 0.25 (ifs025)", b["ifs"]),
                        ("Open-Meteo best match (bestmatch)", read_prev_runs("prev_runs_basel_2025.csv")),
                        ("persistence (persist)", forecast_temps("persist", 0)),
                        ("synthetic 2 K, seed 1 (syn2)", forecast_temps("syn2", 1))):
        print(f"   {label}")
        for k in range(1, 8):
            bias, mae, rmse, rho = err_stats(cols[k], act_t)
            print(f"     day {k}: bias {bias:+.2f}  MAE {mae:.2f}  RMSE {rmse:.2f}  lag-1h autocorr {rho:.3f}")
    print(f"   synthetic model uses rho = {b['rho']:.3f} and RMSE growth day1..7 = "
          + ", ".join(f"{r:.2f}" for r in b["ratios"]))
    wd = [k for k in range(H_YEAR) if MONTH[k] in (0, 1, 11)]
    for k in (1, 3, 7):
        e = [b["ifs"][k][t] - act_t[t] for t in wd]
        print(f"   ifs025 day {k}, Dec-Feb only: bias {sum(e)/len(e):+.2f}  RMSE {math.sqrt(sum(x*x for x in e)/len(e)):.2f}")

    print("\n== 0b. The heating-day cliff: days of 2025 whose forecast heating-day flag is wrong ==")
    print("   (case rule: space heating only if the day's mean temperature is below 12 degC)")
    act_flag = [sum(act_t[d*24:(d+1)*24]) / 24.0 < 12.0 for d in range(365)]
    act_day = [sum(b["act_d"][d*24:(d+1)*24]) for d in range(365)]
    for label, cols in (("ifs025", b["ifs"]), ("bestmatch", read_prev_runs("prev_runs_basel_2025.csv")),
                        ("persist", forecast_temps("persist", 0))):
        for k in (1, 3, 5, 7):
            fl = [sum(cols[k][d*24:(d+1)*24]) / 24.0 < 12.0 for d in range(365)]
            fd = demand_from_temps(cols[k])
            over = [d for d in range(365) if fl[d] and not act_flag[d]]
            under = [d for d in range(365) if act_flag[d] and not fl[d]]
            lost = sum(sum(fd[d*24:(d+1)*24]) - act_day[d] for d in over)
            e = [sum(fd[d*24:(d+1)*24]) - act_day[d] for d in range(365)]
            print(f"   {label:<9} day {k}: forecast 'heating' but actually not: {len(over):>2} days "
                  f"({lost:>5.0f} kWh of permits promised that never came); forecast 'no heating' but actually yes: "
                  f"{len(under):>2} days; daily demand error RMSE {math.sqrt(sum(x*x for x in e)/365):.1f} kWh/day")

    print("\n== 1. Heat-permit capacity by month, follow rule, server-h/day ==")
    follow_h = {}
    for n in (6, 8):
        mean, per_year = normal_capacity(n)
        y25 = follow_monthly(b["act_d"], n)
        follow_h[n] = follow_simulate(b["rows"], n)["run_h"]
        print(f"   N={n}   follow permit hours 2025 = {follow_h[n]:.0f}")
        print("     month      " + " ".join(f"{m+1:>6}" for m in range(12)) + "   year")
        yr = lambda v: sum(v[m] * MDAYS[m] for m in range(12)) / 365.0
        print("     2020-24 avg" + " ".join(f"{x:>6.1f}" for x in mean) + f" {yr(mean):>6.1f}")
        print("     min of 5 yr" + " ".join(f"{min(v[m] for v in per_year.values()):>6.1f}" for m in range(12)))
        print("     max of 5 yr" + " ".join(f"{max(v[m] for v in per_year.values()):>6.1f}" for m in range(12)))
        print("     2025 actual" + " ".join(f"{x:>6.1f}" for x in y25) + f" {yr(y25):>6.1f}")

    # ---- task list
    T = {}
    def add(group, n, fc="ifs025", demand="saturating", margin=0.0, handoff=1, unsold="idle", pfull=0.0):
        T.setdefault(group, []).append((n, fc, demand, margin, handoff, unsold, pfull))
    for n in (6, 8):
        for dm in ("saturating", "flat", "shaped100"):
            for ho in (None, 0, 1, 4):
                add("2. Main: real archived forecast (ifs025), no safety margin, unsold hours idle", n, demand=dm, handoff=ho)
        for fc in ("perfect", "ifs025", "bestmatch", "syn1", "syn2", "syn3", "syn2cold", "persist"):
            for ho in (None, 1, 4):
                add("3. Forecast-error sensitivity, saturating offers, no margin", n, fc=fc, handoff=ho)
        for dm in ("saturating", "shaped100"):
            for mg in (0.0, 0.05, 0.10, 0.20, 0.30):
                for ho in (None, 4):
                    add("4. Admission safety margin (share of forecast permits left unsold), ifs025", n, demand=dm, margin=mg, handoff=ho)
        for fc in ("ifs025", "ifs025g1", "ifs025g2", "ifs025g3"):
            for ho in (None, 1):
                add("4b. Guard band on the heating-day threshold in the forecast, saturating, no margin", n, fc=fc, handoff=ho)
        for dm in ("shaped100", "shaped70", "shaped40"):
            for us in ("idle", "filler"):
                add("5. Sold share and the unsold-hour rule, ifs025, hand-off 1 h, no margin", n, demand=dm, unsold=us)
        for us in ("idle", "filler"):
            add("5. Sold share and the unsold-hour rule, ifs025, hand-off 1 h, no margin", n, demand="saturating", unsold=us)
        for pf in (0.0, 0.2, 0.5, 1.0):
            add("6. Partner site refuses a share of hand-offs, saturating, ifs025, hand-off 1 h", n, pfull=pf)
        for fc in ("syn3", "persist"):
            for mg in (0.10, 0.20):
                add("7. Bad forecast plus margin, saturating, no partner", n, fc=fc, margin=mg, handoff=None)
    uniq = sorted({c + (s,) for g in T.values() for c in g for s in seeds},
                  key=lambda c: tuple(str(x) for x in c))
    print(f"\n({len(uniq)} simulated years, seeds {seeds})", flush=True)
    if procs == 1:
        out = [task(c) for c in uniq]
    else:
        import multiprocessing as mp
        with mp.Pool(procs) as pool:
            out = pool.map(task, uniq, chunksize=4)
    res = dict(out)

    for group, cfgs in T.items():
        print(f"\n== {group} ==\n{HDR}")
        last = None
        for c in cfgs:
            if last is not None and (c[0], c[2]) != last and group.startswith(("2", "4")):
                print()
            last = (c[0], c[2])
            line = fmt(res, c, seeds, follow_h)
            if c[6]:
                line += f"   partner refuses {c[6]*100:.0f}%"
            print(line)

    print("\n== 8. Detail: saturating offers, ifs025, no margin, seed 1 ==")
    for n in (6, 8):
        for ho in (None, 4):
            r = res[(n, "ifs025", "saturating", 0.0, ho, "idle", 0.0, 1)]
            print(f"   N={n} hand-off {'none' if ho is None else str(ho)+' h'}: accepted {r['accepted']}, "
                  f"completed here {r['done_n']}, moved {r['moved_n']}, missed {r['missed_n']}; "
                  f"missed J1 {r['missed_j1']*100:.3f}% / J2 {r['missed_j2']*100:.3f}% of accepted jobs of that type; "
                  f"missed work {r['missed_work']*100:.3f}% of accepted work")
            print("     month   " + " ".join(f"{m+1:>6}" for m in range(12)))
            for f in ("acc", "done", "moved", "missed"):
                print(f"     {f:<8}" + " ".join(f"{r['mon'][m][f]:>6}" for m in range(12)))
    print("\n== 9. Check: follow rule with every permit sold (baseline_sweep.simulate) ==")
    for n in (6, 8):
        r = follow_simulate(b["rows"], n)
        print(f"   N={n}: coverage {r['coverage']*100:.1f}%, dumped {r['dumped']:.0f} kWh, utilisation {r['util']*100:.1f}%, "
              f"{r['run_h']:.0f} server-h, break-even {r['breakeven']:.4f} CHF/server-h")


if __name__ == "__main__":
    main()
