"""Round 7, weak point "forecast inside the team scheduler (foresight)".

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.
Writes no files.

    python3 analysis/r7_forecast_paths.py            # all sections (about 1-3 min, all cores)
    python3 analysis/r7_forecast_paths.py --procs 1  # no multiprocessing
    python3 analysis/r7_forecast_paths.py --quick    # sections 0-2 only (no outage sweep)

Question: what is the CHEAPEST decision-time forecast the team can plug into the
fc_demand[0..167] hook of decide(), and what does each candidate cost in coverage and
give as "x of y accepted jobs missed" under the headline shaped100 offers (seed 1 = the
offer CSV analysis/r4_offers_shaped100_seed1.csv), cap + 8 kWh band, restart outside
execution, N = 6 and N = 8?

Candidates (fc_demand[L] for the target hour h+L, decided at hour h)
  perfect      actual 2025 demand (the plan's MUST stage; look-ahead by construction)
  perfect+kK   actual temperature + k kelvin (forecast warmer = fewer permits): a "safety
               haircut" on the perfect forecast. STILL uses the future weather.
  ifs025       archived ECMWF IFS 0.25 deg, Open-Meteo Previous Runs (analysis/r2_data/
               prev_ecmwf_ifs025.csv): column previous_dayK, K = LEAD[L]
  persist      the house's own past temperature: value of the same hour K days earlier,
               K = LEAD[L]; first days of January read late December 2024 from
               analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv (no wrap into
               December 2025, which would be look-ahead)
  trail7       mean of the same hour over the 7 days K..K+6 before (causal)
  clim         2020-24 mean of the same hour, +-3 days (past years only)
  blend        (persist + clim) / 2
  each with guard g: a forecast day counts as a heating day only if its forecast mean
  temperature < 12 - g degC.

Look-ahead rules checked here
  LEAD[L] = min(7, ceil((L + 23) / 24)) (= r3/r4/r5 'causal'): every hour of the target
  day, which the heating-day flag averages, was issued at or before h IF previous_dayK
  means "issued exactly 24 K h before valid time". For L >= 146 the needed K is 8, so the
  cap at 7 lets the flag of the 7th-day tail use values issued up to 22 h after h. The
  'strict' variants fix that tail (persist: K = 8 from the past series; ifs025: no day 8
  exists, so those hours get hot water only, i.e. no space-heating permits). The '+1d'
  variant adds one more day of lead for the ECMWF publication delay (not modelled by the
  archive).
  fc_demand[0] = the current hour's actual demand (the house's measured heat draw). In the
  case formula that hour's heating-day flag depends on the rest of today: a modelling
  convention, declared, not a forecast.

Outage section (n_avail hook): whole house dark 72 h from the 15th 00:00 of each month,
  modes  told      scheduler knows the outage and its end (r5/r6 'told')
         nottold   scheduler plans with all N servers throughout (r5/r6 'not told')
         detect    heartbeat: from the 2nd dark hour on, the scheduler knows the house is
                   dark now, does not know when it returns, and plans n_avail = 0 for the
                   whole 168 h horizon until the house reports back
         detect24  same, but assumes the house returns 24 h after detection

Imports without editing: r2_deadline_sim (R), r3_policy_check (step_permit),
r5_miss_stress (offers from the CSV, run() for the regression check), r6_build_scope
(line census for the LOC anchors).
"""
import csv
import math
import multiprocessing as mp
import sys
import time
from operator import itemgetter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from baseline_sweep import HEAT_VALUE, P_EL, PRICE, REC, ROOT, TANK  # noqa: E402
import r2_deadline_sim as R  # noqa: E402
import r3_policy_check as P3  # noqa: E402
import r5_miss_stress as S  # noqa: E402

Q1 = REC * P_EL
H = 8760
HZ = 168
JT = R.JT
PAD_DAYS = 14                      # days of December 2024 prepended for causal look-back


# ---------------------------------------------------------------- forecast series
def lead_table(kind="causal"):
    if kind == "causal":           # as r3/r4/r5
        return [min(7, (L + 46) // 24) for L in range(HZ)]
    if kind == "strict8":          # exact causal K, may be 8
        return [(L + 46) // 24 for L in range(HZ)]
    if kind == "plus1d":           # one extra day for publication delay, capped at 7
        return [min(7, (L + 46) // 24 + 1) for L in range(HZ)]
    raise ValueError(kind)


_C = {}


def padded_temps():
    """2024-12-18..31 from the 2020-24 archive + the 2025 reference temperatures."""
    if "pad" not in _C:
        yrs = R.read_archive_years()
        _C["pad"] = yrs["2024"][-PAD_DAYS * 24:] + R.base()["act_t"]
    return _C["pad"]


def shifted(days):
    """Temperature series of 2025 shifted back by `days` whole days (causal look-back)."""
    p = padded_temps()
    o = PAD_DAYS * 24 - days * 24
    return p[o:o + H]


def clim_series():
    if "clim" not in _C:
        yrs = list(R.read_archive_years().values())
        out = []
        for t in range(H):
            v = [y[(t + 24 * d) % H] for y in yrs for d in range(-3, 4)]
            out.append(sum(v) / len(v))
        _C["clim"] = out
    return _C["clim"]


def temps_for(src, k, warm=0.0):
    """Forecast temperature series for lead K=k (1..8)."""
    act = R.base()["act_t"]
    if src == "perfect":
        return [t + warm for t in act]
    if src == "ifs025":
        return R.base()["ifs"][min(k, 7)]
    if src == "persist":
        return shifted(k)
    if src == "persist_nopad":     # no 2024 data: hours before 1 Jan count as 'no heating' (30 degC)
        sh = shifted(k)
        return [30.0 if t < 24 * k else sh[t] for t in range(H)]
    if src == "trail7":
        cols = [shifted(k + j) for j in range(7)]
        return [sum(c[t] for c in cols) / 7.0 for t in range(H)]
    if src == "clim":
        return clim_series()
    if src == "blend":
        p, c = shifted(k), clim_series()
        return [(a + b) / 2.0 for a, b in zip(p, c)]
    raise ValueError(src)


HW_ONLY = 9                        # index of the 'hot water only' series in Fd


def fd_series(src, guard, warm=0.0):
    """Fd[0] = actual, Fd[1..8] = forecast demand by lead K, Fd[9] = hot water only."""
    key = (src, guard, warm)
    if key not in _C:
        act_d = R.base()["act_d"]
        Fd = [act_d] + [R.demand_from_temps(temps_for(src, k, warm), 12.0 - guard) for k in range(1, 9)]
        Fd.append([0.5] * H)
        _C[key] = Fd
    return _C[key]


def lead_for(variant):
    """variant -> LEAD list indexing Fd (strict ifs025: K=8 hours -> HW_ONLY)."""
    src, guard, warm, lk = variant
    if lk == "strict8" and src == "ifs025":
        return [HW_ONLY if (L + 46) // 24 > 7 else (L + 46) // 24 for L in range(HZ)]
    return lead_table(lk)


# ---- the 'least code' persistence the team would write: CSV columns only, no temperature
def persist_from_csv_columns(guard):
    """fc for target t at lead K = demand of hour t-24K, read from the reference CSV columns.
    Heating day with guard: day_mean_temperature_c < 12 - guard. Same as R.demand_from_temps
    on the shifted temperatures (asserted in section 0). Pre-2025 hours: archive via padding."""
    with open(ROOT / "data" / "reference_house_2025_hourly.csv") as f:
        rows = list(csv.DictReader(f))
    sh = [float(r["space_heating_kwh"]) for r in rows]
    dm = [float(r["day_mean_temperature_c"]) for r in rows]
    own = [(sh[t] if dm[t] < 12.0 - guard else 0.0) + 0.5 for t in range(H)]
    return own                      # the driver then reads own[h + L - 24 * K]


# ---------------------------------------------------------------- one year (compact copy of r5 run, restart 0)
def run(n, variant, outage=None, mode="none", seed=1):
    """outage = (start_hour, duration_h) for all n servers; mode told|nottold|detect|detect24."""
    src, guard, warm, lk = variant
    act_d = R.base()["act_d"]
    Fd = fd_series(src, guard, warm)
    LEAD = lead_for(variant)
    offs = S.offers(n, seed)
    rule, band, cap1 = "band", 8.0, True
    key0 = itemgetter(0)
    o_st, o_en = (outage[0], outage[0] + outage[1]) if outage else (-1, -1)

    soc = used = dem_tot = dumped = sold_h = run_h = 0.0
    charging, kprev, on_prev, starts = True, 0, 0, 0
    jobs = []                      # [deadline, type, remaining]
    off = [0, 0]; acc = [0, 0]; done = [0, 0]; missed = [0, 0]
    stranded = 0                   # accepted jobs missed whose deadline fell in or <= 7 d after the outage
    for h in range(H):
        d = act_d[h]
        dem_tot += d
        dark = o_st <= h < o_en
        n_up = 0 if dark else n
        if jobs:
            keep = []
            for j in jobs:
                if j[0] - h < math.ceil(j[2] - 1e-9):
                    missed[j[1]] += 1
                    if outage and o_st <= h < o_en + HZ:
                        stranded += 1
                else:
                    keep.append(j)
            jobs = keep
        ch_prev = charging
        cap, charging = P3.step_permit(rule, band, cap1, n_up, d, soc, charging, kprev)

        a0, a1, first = offs[h]
        if a0 or a1:
            # what the scheduler believes: n_avail[0..167]
            if not dark or mode == "none":
                nav = [n] * HZ     # no mode foresees an outage before it starts (as r5)
                believed_dark_now = False
            elif mode == "told":
                nav = [0 if h + L < o_en else n for L in range(HZ)]
                believed_dark_now = True
            elif mode == "nottold" or (mode.startswith("detect") and h < o_st + 1):
                nav = [n] * HZ
                believed_dark_now = False
            elif mode == "detect":
                nav = [0] * HZ
                believed_dark_now = True
            elif mode == "detect24":
                back = o_st + 1 + 24
                nav = [0 if h + L < back else n for L in range(HZ)]
                believed_dark_now = True
            else:
                raise ValueError(mode)
            if believed_dark_now or not dark:
                c0 = cap
            else:                  # dark but not known: plans with all N (r5 'not told')
                c0, _ = P3.step_permit(rule, band, cap1, n, d, soc, ch_prev, kprev)
            cf = [c0]
            s = soc + c0 * Q1
            s -= min(d, s)
            ch, kp = charging, c0
            for L in range(1, HZ):
                dF = Fd[LEAD[L]][(h + L) % H]
                c, ch = P3.step_permit(rule, band, cap1, nav[L], dF, s, ch, kp)
                s += c * Q1
                s -= min(dF, s)
                kp = c
                cf.append(c)
            cum, tot = [0.0], 0.0
            for c in cf:
                tot += c
                cum.append(tot)
            W = [0.0] * (HZ + 1)
            for j in jobs:
                W[j[0] - h] += j[2]
            slack, w = [0.0] * (HZ + 1), 0.0
            for L in range(HZ + 1):
                w += W[L]
                slack[L] = cum[L] - w
            new = []
            for i in ((0, 1) if first == 0 else (1, 0)):
                k_off = (a0, a1)[i]
                if not k_off:
                    continue
                _, rt, dl = JT[i]
                off[i] += k_off
                room = min(slack[dl:])
                k = max(0, min(k_off, int(room / rt + 1e-9)))
                if k:
                    for L in range(dl, HZ + 1):
                        slack[L] -= k * rt
                    for _ in range(k):
                        new.append([h + dl, i, rt])
                    jobs.extend(new[-k:])
                    acc[i] += k
            jobs.sort(key=key0)
            while new:
                failing = R.forward_fail(jobs, h, cf, 1.0)
                if not failing:
                    break
                pick = next((j for j in failing if any(j is x for x in new)), None) or new[-1]
                new = [x for x in new if x is not pick]
                jobs = [j for j in jobs if j is not pick]
                acc[pick[1]] -= 1

        work = 0.0
        if jobs and cap > 0:
            fin = False
            for j in jobs:
                step = min(j[2], 1.0, cap - work)
                j[2] -= step
                work += step
                if j[2] <= 1e-9:
                    done[j[1]] += 1
                    fin = True
                if work >= cap - 1e-9:
                    break
            if fin:
                jobs = [j for j in jobs if j[2] > 1e-9]
        on = int(math.ceil(work - 1e-9))
        starts += max(0, on - on_prev)
        avail = soc + work * Q1
        u = min(d, avail)
        soc = avail - u
        dump = max(0.0, soc - TANK)
        soc -= dump
        used += u
        dumped += dump
        sold_h += work
        run_h += work
        kprev, on_prev = cap, on
    closed = sum(done) + sum(missed)
    elec = run_h * P_EL * PRICE
    return dict(missed=sum(missed), closed=closed, accepted=sum(acc), offered=sum(off),
                acc=sum(acc) / max(1, sum(off)), cov=used / dem_tot, util=run_h / (n * H),
                sold=sold_h, dumped=dumped, starts=starts, stranded=stranded,
                be=(elec - used * HEAT_VALUE) / sold_h)


def _task(a):
    key, n, variant, outage, mode = a[:5]
    return (key, n), run(n, variant, outage, mode, a[5] if len(a) > 5 else 1)


def _r5task(a):
    key, n, kw = a
    r = S.run(n, S.cfg(**kw), 1)
    return (key, n), dict(missed=r["missed_n"], closed=r["closed_n"], cov=r["coverage"], acc=r["acc_jobs"])


def day_hour(month, day=15):
    return (sum(R.MDAYS[:month - 1]) + day - 1) * 24


# ---------------------------------------------------------------- forecast error vs truth
def err(fc, act):
    e = [a - b for a, b in zip(fc, act)]
    return sum(e) / len(e), math.sqrt(sum(x * x for x in e) / len(e))


def flag_errors(src, guard, k):
    act = R.base()["act_t"]
    ft = temps_for(src, k)
    a = [sum(act[d * 24:(d + 1) * 24]) / 24 < 12.0 for d in range(365)]
    f = [sum(ft[d * 24:(d + 1) * 24]) / 24 < 12.0 - guard for d in range(365)]
    over = sum(1 for d in range(365) if f[d] and not a[d])
    under = sum(1 for d in range(365) if a[d] and not f[d])
    return over, under


VARIANTS = [
    # key, (src, guard, warm, lead kind), label
    ("perfect", ("perfect", 0.0, 0.0, "causal"), "perfect forecast (MUST; reads the future)"),
    ("perfect+g2", ("perfect", 2.0, 0.0, "causal"), "perfect + 2 K guard (still reads the future)"),
    ("perfect+1K", ("perfect", 0.0, 1.0, "causal"), "perfect temps +1 K (still reads the future)"),
    ("perfect+2K", ("perfect", 0.0, 2.0, "causal"), "perfect temps +2 K (still reads the future)"),
    ("perfect+3K", ("perfect", 0.0, 3.0, "causal"), "perfect temps +3 K (still reads the future)"),
    ("ifs025", ("ifs025", 0.0, 0.0, "causal"), "archived ECMWF, no guard"),
    ("ifs025+g2", ("ifs025", 2.0, 0.0, "causal"), "archived ECMWF + 2 K guard (O3)"),
    ("ifs025+g2 strict", ("ifs025", 2.0, 0.0, "strict8"), "O3 with the 7th-day tail fixed (HW only)"),
    ("ifs025+g2 +1d", ("ifs025", 2.0, 0.0, "plus1d"), "O3 with one extra day of lead (publication delay)"),
    ("persist", ("persist", 0.0, 0.0, "causal"), "persistence, no guard"),
    ("persist+g1", ("persist", 1.0, 0.0, "causal"), "persistence + 1 K guard"),
    ("persist+g2", ("persist", 2.0, 0.0, "causal"), "persistence + 2 K guard"),
    ("persist+g2 strict", ("persist", 2.0, 0.0, "strict8"), "persistence + 2 K, exact K up to 8"),
    ("persist+g3", ("persist", 3.0, 0.0, "causal"), "persistence + 3 K guard"),
    ("persist+g2 nopad", ("persist_nopad", 2.0, 0.0, "causal"), "persistence + 2 K, no Dec-2024 data (CSV only)"),
    ("trail7+g2", ("trail7", 2.0, 0.0, "causal"), "7-day same-hour mean + 2 K guard"),
    ("clim", ("clim", 0.0, 0.0, "causal"), "2020-24 climatology, no guard"),
    ("clim+g2", ("clim", 2.0, 0.0, "causal"), "2020-24 climatology + 2 K guard"),
    ("blend+g2", ("blend", 2.0, 0.0, "causal"), "(persistence + climatology)/2 + 2 K guard"),
]


def main():
    argv = sys.argv[1:]
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    quick = "--quick" in argv
    t0 = time.time()
    print("r7_forecast_paths.py. Assessment only; not the team scheduler. Stand-in reference house 2025.")
    print("Headline shaped100 offers, seed 1 = analysis/r4_offers_shaped100_seed1.csv; cap + 8 kWh band; restart outside execution.\n")

    act = R.base()["act_t"]
    print("== 0. Checks ==")
    p_ok = all(abs(shifted(1)[t] - act[t - 24]) < 1e-12 for t in range(24, H))
    print(f"  shifted(1) equals actual 24 h earlier for t >= 24: {p_ok}; first January day reads 2024-12-31 "
          f"(archive) {shifted(1)[0]:+.1f} degC, not 2025-12-31 {act[-24]:+.1f} degC")
    for g in (0.0, 2.0):
        own = persist_from_csv_columns(g)
        ref = R.demand_from_temps(act, 12.0 - g)
        mx = max(abs(a - b) for a, b in zip(own, ref))
        print(f"  CSV-column persistence (guard {g:.0f} K) vs demand_from_temps on the same temperatures: max |diff| {mx:.5f} kWh")
    print("  forecast temperature error vs the reference temperature (bias, RMSE in K), lead K = 1 / 2 / 7:")
    for src in ("ifs025", "persist", "trail7", "clim", "blend"):
        cells = []
        for k in (1, 2, 7):
            b, r = err(temps_for(src, k), act)
            cells.append(f"K{k} {b:+.2f}/{r:.2f}")
        ov, un = flag_errors(src, 2.0, 2)
        ov0, un0 = flag_errors(src, 0.0, 2)
        cells.append(f"heating-day flag wrong at K2: {ov0} too many / {un0} too few days (guard 0); "
                     f"{ov} / {un} (guard 2 K)")
        print(f"    {src:<8} " + "  ".join(cells))

    # regression: compact run vs r5_miss_stress.run on the same inputs
    reg = [("perfect", dict(fc="perfect", guard=0.0), ("perfect", 0.0, 0.0, "causal")),
           ("ifs025+g2", dict(fc="ifs025", guard=2.0), ("ifs025", 2.0, 0.0, "causal")),
           ("ifs025", dict(fc="ifs025", guard=0.0), ("ifs025", 0.0, 0.0, "causal"))]
    otold = (day_hour(4), 72)
    tasks = []
    r5tasks = []
    for n in (6, 8):
        for key, kw, v in reg:
            tasks.append(("REG " + key, n, v, None, "none"))
            r5tasks.append(("REG " + key, n, kw))
        tasks.append(("REG Apr told", n, ("ifs025", 2.0, 0.0, "causal"), otold, "told"))
        r5tasks.append(("REG Apr told", n, dict(fail_at=(otold[0], n, 72), fail_aware=True)))
        tasks.append(("REG Apr nottold", n, ("ifs025", 2.0, 0.0, "causal"), otold, "nottold"))
        r5tasks.append(("REG Apr nottold", n, dict(fail_at=(otold[0], n, 72), fail_aware=False)))
        for key, v, _ in VARIANTS:
            tasks.append((key, n, v, None, "none"))
    SEEDV = (("perfect", ("perfect", 0.0, 0.0, "causal")), ("persist+g2", ("persist", 2.0, 0.0, "causal")),
             ("persist+g2 nopad", ("persist_nopad", 2.0, 0.0, "causal")), ("ifs025+g2", ("ifs025", 2.0, 0.0, "causal")))
    if not quick:
        for fkey, v in SEEDV:
            for n in (6, 8):
                for sd in (2, 3, 4, 5):
                    tasks.append((f"SEED {fkey} {sd}", n, v, None, "none", sd))
        for fkey, v in (("perfect", ("perfect", 0.0, 0.0, "causal")),
                        ("persist+g2", ("persist", 2.0, 0.0, "causal")),
                        ("ifs025+g2", ("ifs025", 2.0, 0.0, "causal"))):
            for n in (6, 8):
                for m in range(1, 13):
                    for mode in ("told", "nottold", "detect", "detect24"):
                        tasks.append((f"OUT {fkey} {mode} M{m:02d}", n, v, (day_hour(m), 72), mode))
    # warm caches before forking
    for _, v, _ in VARIANTS:
        fd_series(v[0], v[1], v[2])
    for n in (6, 8):
        for sd in (1, 2, 3, 4, 5):
            S.offers(n, sd)
    if procs == 1:
        res = dict(_task(t) for t in tasks)
        r5 = dict(_r5task(t) for t in r5tasks)
    else:
        with mp.Pool(procs) as pool:
            res = dict(pool.map(_task, tasks, chunksize=1))
            r5 = dict(pool.map(_r5task, r5tasks, chunksize=1))

    print("\n  regression: this script's compact run vs r5_miss_stress.run (missed of closed; coverage)")
    for key in [k for k, _, _ in reg] + ["Apr told", "Apr nottold"]:
        for n in (6, 8):
            a, b = res[("REG " + key, n)], r5[("REG " + key, n)]
            same = a["missed"] == b["missed"] and a["closed"] == b["closed"] and abs(a["cov"] - b["cov"]) < 1e-12
            print(f"    {key:<12} N={n}: here {a['missed']} of {a['closed']:,}, {a['cov']*100:.2f}% | r5 {b['missed']} of "
                  f"{b['closed']:,}, {b['cov']*100:.2f}% -> {'IDENTICAL' if same else 'DIFFERENT'}")

    print("\n== 1. Forecast candidates for the fc_demand hook (seed 1, headline shaped100) ==")
    print(f"  {'key':<18} {'N=6 missed of accepted':>24} {'acc%':>6} {'cover':>7} {'util':>6} {'BE CHF':>7}   "
          f"{'N=8 missed of accepted':>24} {'acc%':>6} {'cover':>7} {'util':>6}  label")
    for key, v, lab in VARIANTS:
        c = []
        for n in (6, 8):
            r = res[(key, n)]
            c.append(f"{r['missed']:>5} of {r['closed']:>7,} ({r['missed']/r['closed']*100:.3f}%) {r['acc']*100:>5.1f}% "
                     f"{r['cov']*100:>6.2f}% {r['util']*100:>5.2f}%" + (f" {r['be']:.4f}" if n == 6 else ""))
        print(f"  {key:<18} {c[0]}   {c[1]}  {lab}")
    p6, p8 = res[("perfect", 6)], res[("perfect", 8)]
    print("\n  coverage cost vs perfect (points) and accepted-share cost (points):")
    for key, v, lab in VARIANTS[1:]:
        r6, r8 = res[(key, 6)], res[(key, 8)]
        print(f"    {key:<18} N=6 {(r6['cov']-p6['cov'])*100:+.2f} cov, {(r6['acc']-p6['acc'])*100:+.1f} acc | "
              f"N=8 {(r8['cov']-p8['cov'])*100:+.2f} cov, {(r8['acc']-p8['acc'])*100:+.1f} acc")

    print("\n== 2. LOC anchors (r6_build_scope.census(), non-blank non-comment non-docstring lines) ==")
    import r6_build_scope as B
    c = B.census()
    for k in ("fc_read", "fc_formula", "fc_demand", "fc_lead", "persist"):
        print(f"  {k:<12} {c[k][0]:>3}  {c[k][1]}")
    src = (HERE / "r7_forecast_paths.py").read_text().split("\n")
    a = next(i for i, s in enumerate(src) if s.startswith("def persist_from_csv_columns"))
    b = next(i for i, s in enumerate(src) if i > a and s.strip().startswith("return own"))
    loc = sum(1 for s in src[a:b + 1] if s.strip() and not s.strip().startswith("#")
              and not s.strip().startswith(('"""', "fc for", "Heating day", "on the shifted")))
    print(f"  persist_from_csv_columns() in this file: {loc} code lines (incl. def and CSV read)")

    if quick:
        print(f"\n(done in {time.time()-t0:.1f} s)")
        return
    print("\n== 2b. Seed robustness (offer seeds 2-5 from r4_headline.offer_stream; the team scheduler reads seed 1 only) ==")
    for fkey, _ in SEEDV:
        for n in (6, 8):
            rr = [res[(f"SEED {fkey} {sd}", n)] for sd in (2, 3, 4, 5)]
            print(f"  {fkey:<17} N={n}: missed " + ", ".join(f"{r['missed']} of {r['closed']:,}" for r in rr)
                  + f"; coverage {min(r['cov'] for r in rr)*100:.2f}-{max(r['cov'] for r in rr)*100:.2f}%"
                  + f"; accepted {min(r['acc'] for r in rr)*100:.1f}-{max(r['acc'] for r in rr)*100:.1f}%")

    print("\n== 3. Whole house dark 72 h from the 15th 00:00, by month, seed 1 (n_avail hook modes) ==")
    print("  missed of accepted per start month Jan..Dec; stranded = of those, missed while dark or within 168 h after")
    for fkey in ("perfect", "persist+g2", "ifs025+g2"):
        for n in (6, 8):
            for mode in ("told", "nottold", "detect", "detect24"):
                row = [res[(f"OUT {fkey} {mode} M{m:02d}", n)] for m in range(1, 13)]
                ms = [r["missed"] for r in row]
                print(f"  {fkey:<11} N={n} {mode:<9} {ms}  max {max(ms)}  (closed {min(r['closed'] for r in row):,}-"
                      f"{max(r['closed'] for r in row):,}; stranded max {max(r['stranded'] for r in row)})")
    print(f"\n(done in {time.time()-t0:.1f} s)")


if __name__ == "__main__":
    main()
