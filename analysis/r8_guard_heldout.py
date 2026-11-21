"""Round 8, weak point "missed-deadline tile cannot discriminate between forecast inputs,
and the 2 K guard was chosen and scored on the same 2025 weather".

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.
Writes no files.

    python3 analysis/r8_guard_heldout.py              # all sections, offer seeds 1-5 (about 2 min, 12 cores)
    python3 analysis/r8_guard_heldout.py --seeds 3    # fewer offer seeds per year
    python3 analysis/r8_guard_heldout.py --procs 1    # no multiprocessing

(a) Leave-one-year-out (LOYO) check of the heating-day guard g in {0, 1, 2, 3} K.
    Weather years 2020-2024 (analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv, the same
    Open-Meteo ecmwf_ifs model and grid cell as the reference house; 29 Feb dropped by
    r2_deadline_sim.read_archive_years) and 2025 (the reference-house temperatures).
    Heat demand of year Y = the case formula, unchanged, on Y's hourly temperatures:
        space heating = max(0, 10 * (20 - T) / 25.6) kWh on a heating day (day mean < 12 degC),
        else 0; + 0.5 kWh hot water every hour   (r2_deadline_sim.demand_from_temps)
    The 25.6 constant is KEPT FIXED for every year (it is the case's constant, tuned so that
    2025's coldest hour, -5.6 degC, gives 10 kWh). Colder years therefore peak above 10 kWh.
    Offers of year Y (default 'normal'): the headline shaped100 construction applied out of
    sample: monthly offer rate = 100% of the mean plain-follow heat-permit capacity of that
    month over the OTHER five years (r2_deadline_sim.follow_monthly), Poisson arrivals from
    r4_headline.offer_stream(rates, seed). For 2025 that is exactly the headline contract
    (2020-24 normal); seed 1 for 2025 is asserted equal to analysis/r4_offers_shaped100_seed1.csv.
    Sensitivity 'own': rates = 100% of Y's OWN monthly capacity (a contract that knows the
    year's monthly weather; harsher in cold months).
    Planning inputs (fc_demand[L] for target hour h+L, lead K = min(7, ceil((L+23)/24))):
      check   actual demand of Y, no guard (the MUST check run)
      P1      persistence: own[t - 24K], own = case formula on Y's temperatures with heating-day
              threshold 12 - g; t - 24K < 0 -> 0.5 (hot water only; no data from the previous
              year, exactly the plan's P1 rule)
      O3      archived ECMWF IFS 0.25 deg, Open-Meteo Previous Runs, previous_dayK, threshold
              12 - g. Exists only for 2025 (analysis/r2_data/prev_ecmwf_ifs025.csv) and for
              3 Feb 2024 onwards (analysis/r8_data/prev_ecmwf_ifs025_2024.csv, downloaded in
              round 8). Missing 2024 hours (1 Jan - 9 Feb, lead dependent) fall back to P1's
              persisted temperature (labelled).
    Guard selection on the training years (the other five, all offer seeds): the smallest g
    with 0 training misses; if none, the g with the fewest training misses (tie -> smaller g).
    Then scored on the held-out year.
(b) Section 4, tile-line values for 2025, seed 1: refused work (jobs, server-hours, share of
    offered work, summer vs rest of year) for the check run, P1 (+2 K, +3 K) and O3.
Section 5: why P1 misses (by deadline month and day, with daily mean temperatures) and P1 with a
    magnitude margin w in {0..3} K on the persisted hourly temperature (flag guard 2 K), LOYO on w.
Section 6: pooled out-of-sample miss rates.

Run rules = r7_forecast_paths.run (cap + 8 kWh band, EDF dry run, restart outside execution,
no outages), copied here with the demand, the forecast and the offers as arguments; section 0
asserts IDENTICAL results to r7_forecast_paths.run on the 2025 inputs.
Imports without editing: r2_deadline_sim, r3_policy_check, r4_headline, r5_miss_stress,
r7_forecast_paths.
"""
import math
import multiprocessing as mp
import sys
import time
from operator import itemgetter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from baseline_sweep import P_EL, REC, TANK  # noqa: E402
import r2_deadline_sim as R  # noqa: E402
import r3_policy_check as P3  # noqa: E402
import r4_headline as H4  # noqa: E402
import r5_miss_stress as S  # noqa: E402
import r7_forecast_paths as F  # noqa: E402

Q1 = REC * P_EL
H = 8760
HZ = 168
JT = R.JT                      # [("J1", 0.5, 24), ("J2", 4.0, 168)]
YEARS = ["2020", "2021", "2022", "2023", "2024", "2025"]
GUARDS = (0.0, 1.0, 2.0, 3.0)
WARM = (0.0, 1.0, 2.0, 3.0)    # section 5: magnitude margin on P1 (K), with the 2 K flag guard
LEAD = [min(7, (L + 46) // 24) for L in range(HZ)]
SUMMER = (5, 6, 7)             # June, July, August (month index 0..11)
IFS24 = HERE / "r8_data" / "prev_ecmwf_ifs025_2024.csv"

_C = {}


# ---------------------------------------------------------------- inputs per year
def temps():
    if "T" not in _C:
        t = dict(R.read_archive_years())
        t["2025"] = R.base()["act_t"]
        assert all(len(t[y]) == H for y in YEARS)
        _C["T"] = t
    return _C["T"]


def act_dem(y):
    k = ("D", y)
    if k not in _C:             # 2025: the reference CSV values (equal to the formula within 0.00005 kWh)
        _C[k] = list(R.base()["act_d"]) if y == "2025" else R.demand_from_temps(temps()[y], 12.0)
    return _C[k]


def capacity(y, n):
    k = ("cap", y, n)
    if k not in _C:
        _C[k] = R.follow_monthly(act_dem(y), n)
    return _C[k]


def rates(y, n, mode):
    if mode == "own":
        return list(capacity(y, n))
    other = [x for x in YEARS if x != y]
    return [sum(capacity(x, n)[m] for x in other) / len(other) for m in range(12)]


def offers(y, n, seed, mode):
    k = ("off", y, n, seed, mode)
    if k not in _C:
        _C[k] = H4.offer_stream(rates(y, n, mode), seed)
    return _C[k]


def read_ifs2024():
    """2024 previous_day1..7 temperatures, 29 Feb dropped; NaN -> None."""
    cols = [[] for _ in range(8)]
    for ln in IFS24.read_text().split("\n")[4:]:
        if not ln or ln[5:10] == "02-29":
            continue
        p = ln.split(",")
        for k in range(8):
            v = p[1 + k]
            cols[k].append(None if v.lower() == "nan" or v == "" else float(v))
    assert len(cols[0]) == H
    return cols


def persisted_temps(y, k):
    T = temps()[y]
    return [T[t - 24 * k] if t - 24 * k >= 0 else 30.0 for t in range(H)]   # 30 degC = no heating


def fc_temps(y, src, k):
    if src == "O3":
        if y == "2025":
            return R.base()["ifs"][k]
        if y == "2024":
            if "ifs24" not in _C:
                _C["ifs24"] = read_ifs2024()
            col, per = _C["ifs24"][k], persisted_temps(y, k)
            return [p if v is None else v for v, p in zip(col, per)]
        raise ValueError("no archived forecast for " + y)
    raise ValueError(src)


def fd(y, src, g):
    """Fd[0] = actual demand, Fd[1..7] = planning demand by lead K, indexed by target hour
    t = h + L in 0 .. H + HZ - 2. check / O3: targets past 31 Dec wrap to January (as in
    r5/r7, so the regression is exact). P1: own[t - 24K], which is always <= h (causal, no
    wrap), t - 24K < 0 -> 0.5: the code the round-7 critic called the team's natural lookup."""
    key = ("fd", y, src, g)
    if key in _C:
        return _C[key]
    a = act_dem(y)
    T2 = H + HZ
    if src == "check":
        out = [[a[t % H] for t in range(T2)]] * 8
    elif src.startswith("P1w"):    # P1 + magnitude margin: plan as if each persisted hour were w K warmer
        w = float(src[3:])         # (heating-day flag still uses guard g on the persisted day mean)
        T = temps()[y]
        own = []
        for dd in range(H // 24):
            day = T[dd * 24:(dd + 1) * 24]
            heat = sum(day) / 24.0 < 12.0 - g
            own += [(max(0.0, 10.0 * (20.0 - (t + w)) / 25.6) if heat else 0.0) + 0.5 for t in day]
        out = [a] + [[own[t - 24 * k] if 0 <= t - 24 * k < H else 0.5 for t in range(T2)] for k in range(1, 8)]
    elif src == "P1":
        if y == "2025":            # identical to the plan's CSV-column rule (r7 persist_from_csv_columns)
            own = F.persist_from_csv_columns(g)
        else:
            own = R.demand_from_temps(temps()[y], 12.0 - g)
        out = [a] + [[own[t - 24 * k] if 0 <= t - 24 * k < H else 0.5 for t in range(T2)] for k in range(1, 8)]
        # (t - 24K >= H happens only for (t, K) pairs the LEAD table never reads)
    else:
        out = [a]
        for k in range(1, 8):
            d = R.demand_from_temps(fc_temps(y, src, k), 12.0 - g)
            out.append([d[t % H] for t in range(T2)])
    _C[key] = out
    return out


# ---------------------------------------------------------------- one year (copy of r7_forecast_paths.run, no outage)
def run_year(n, act_d, Fd, offs):
    rule, band, cap1 = "band", 8.0, True
    key0 = itemgetter(0)
    soc = used = dem_tot = run_h = 0.0
    charging, kprev = True, 0
    jobs = []
    off = [0, 0]; acc = [0, 0]; done = [0, 0]; missed = [0, 0]
    ref_m = [[0, 0] for _ in range(12)]          # refused jobs by month and type
    miss_m = [[0, 0] for _ in range(12)]         # missed jobs by month of deadline and type
    miss_d = {}                                  # missed jobs by day of deadline
    for h in range(H):
        d = act_d[h]
        dem_tot += d
        if jobs:
            keep = []
            for j in jobs:
                if j[0] - h < math.ceil(j[2] - 1e-9):
                    missed[j[1]] += 1
                    miss_m[R.MONTH[min(H - 1, j[0])]][j[1]] += 1
                    dd = min(H - 1, j[0]) // 24
                    miss_d[dd] = miss_d.get(dd, 0) + 1
                else:
                    keep.append(j)
            jobs = keep
        cap, charging = P3.step_permit(rule, band, cap1, n, d, soc, charging, kprev)
        a0, a1, first = offs[h]
        if a0 or a1:
            cf = [cap]
            s = soc + cap * Q1
            s -= min(d, s)
            ch, kp = charging, cap
            for L in range(1, HZ):
                dF = Fd[LEAD[L]][h + L]
                c, ch = P3.step_permit(rule, band, cap1, n, dF, s, ch, kp)
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
            acc_h = [0, 0]
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
                    acc_h[i] += k
            jobs.sort(key=key0)
            while new:
                failing = R.forward_fail(jobs, h, cf, 1.0)
                if not failing:
                    break
                pick = next((j for j in failing if any(j is x for x in new)), None) or new[-1]
                new = [x for x in new if x is not pick]
                jobs = [j for j in jobs if j is not pick]
                acc[pick[1]] -= 1
                acc_h[pick[1]] -= 1
            m = R.MONTH[h]
            ref_m[m][0] += a0 - acc_h[0]
            ref_m[m][1] += a1 - acc_h[1]
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
        avail = soc + work * Q1
        u = min(d, avail)
        soc = avail - u
        soc -= max(0.0, soc - TANK)
        used += u
        run_h += work
        kprev = cap
    rt = (JT[0][1], JT[1][1])
    ref = [off[i] - acc[i] for i in (0, 1)]
    off_w = off[0] * rt[0] + off[1] * rt[1]
    ref_w = ref[0] * rt[0] + ref[1] * rt[1]
    ref_w_m = [ref_m[m][0] * rt[0] + ref_m[m][1] * rt[1] for m in range(12)]
    sdays = sum(R.MDAYS[m] for m in SUMMER)
    return dict(missed=sum(missed), closed=sum(done) + sum(missed), accepted=sum(acc), offered=sum(off),
                acc=sum(acc) / max(1, sum(off)), cov=used / dem_tot, util=run_h / (n * H),
                ref_j=ref, ref_w=ref_w, off_w=off_w, ref_share_w=ref_w / max(1e-9, off_w),
                ref_w_summer=sum(ref_w_m[m] for m in SUMMER),
                ref_w_summer_day=sum(ref_w_m[m] for m in SUMMER) / sdays,
                ref_w_m=ref_w_m, ref_m=ref_m, miss_m=miss_m, missed_t=missed, miss_d=miss_d)


def _task(a):
    y, n, src, g, seed, mode = a
    return a, run_year(n, act_dem(y), fd(y, src, g), offers(y, n, seed, mode))


# ---------------------------------------------------------------- helpers
def err(fc, act):
    e = [f - x for f, x in zip(fc, act) if f is not None]
    return sum(e) / len(e), math.sqrt(sum(v * v for v in e) / len(e)), len(e)


def pick_guard(res, held, n, src, seeds, mode, years):
    train = [y for y in years if y != held]
    tm = {g: sum(res[(y, n, src, g, s, mode)]["missed"] for y in train for s in seeds) for g in GUARDS}
    zero = [g for g in GUARDS if tm[g] == 0]
    g = zero[0] if zero else min(GUARDS, key=lambda x: (tm[x], x))
    return g, tm


def agg(res, y, n, src, g, seeds, mode):
    rr = [res[(y, n, src, g, s, mode)] for s in seeds]
    return dict(missed=sum(r["missed"] for r in rr), closed=sum(r["closed"] for r in rr),
                per_seed=[r["missed"] for r in rr], r1=rr[0],
                acc=sum(r["acc"] for r in rr) / len(rr), cov=sum(r["cov"] for r in rr) / len(rr))


def main():
    argv = sys.argv[1:]
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    nseed = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else 5
    seeds = tuple(range(1, nseed + 1))
    t0 = time.time()
    print("r8_guard_heldout.py. Assessment only; not the team scheduler. Case demand formula, 25.6 fixed.")
    print(f"Offer seeds per year: {seeds}; cap + 8 kWh band; restart outside execution; no outages.\n")

    # ------------------------------------------------------------ 0. checks
    print("== 0. Checks ==")
    csvd = R.base()["act_d"]
    mx = max(abs(a - b) for a, b in zip(act_dem("2025"), csvd))
    print(f"  2025 demand from the case formula vs data/reference_house_2025_hourly.csv: max |diff| {mx:.6f} kWh")
    for n in (6, 8):
        same_r = all(abs(a - b) < 1e-12 for a, b in zip(rates("2025", n, "normal"), R.offer_rates("shaped100", n)))
        same_o = offers("2025", n, 1, "normal") == S.offers(n, 1)
        print(f"  N={n}: 2025 'normal' rates == headline shaped100 rates: {same_r}; seed-1 offers == offer CSV: {same_o}")
        assert same_r and same_o
    regs = [("check", 0.0, ("perfect", 0.0, 0.0, "causal")), ("O3", 2.0, ("ifs025", 2.0, 0.0, "causal")),
            ("O3", 0.0, ("ifs025", 0.0, 0.0, "causal")), ("P1", 2.0, ("persist", 2.0, 0.0, "causal")),
            ("P1", 1.0, ("persist", 1.0, 0.0, "causal")), ("P1", 0.0, ("persist", 0.0, 0.0, "causal"))]
    for n in (6, 8):
        for src, g, v in regs:
            a = run_year(n, act_dem("2025"), fd("2025", src, g), offers("2025", n, 1, "normal"))
            b = F.run(n, v)
            same = a["missed"] == b["missed"] and a["closed"] == b["closed"] and abs(a["cov"] - b["cov"]) < 1e-12 \
                and a["accepted"] == b["accepted"]
            note = "" if src != "P1" else " (P1 here: t<0 -> 0.5, no year-end wrap; r7: Dec-2024 pad + wrap)"
            print(f"    regression N={n} {src}+g{g:.0f}: here {a['missed']} of {a['closed']:,}, cov {a['cov']*100:.2f}% | "
                  f"r7_forecast_paths.run {b['missed']} of {b['closed']:,}, {b['cov']*100:.2f}% -> "
                  f"{'IDENTICAL' if same else 'DIFFERENT'}{note}")

    # ------------------------------------------------------------ 1. the six weather years
    print("\n== 1. Weather years through the case formula (25.6 fixed) ==")
    print(f"  {'year':<5} {'min T':>6} {'heat days':>9} {'space kWh':>9} {'peak kWh/h':>10} {'Jan cap N6':>10} "
          f"{'Jul cap N6':>10} {'year cap N6 srv-h/d':>19} {'N8':>6}  P1 temp error K1 / K2 (bias/RMSE)")
    for y in YEARS:
        T, D = temps()[y], act_dem(y)
        hd = sum(1 for d in range(365) if sum(T[d * 24:(d + 1) * 24]) / 24 < 12.0)
        sp = sum(D) - 0.5 * H
        c6, c8 = capacity(y, 6), capacity(y, 8)
        yc6 = sum(c6[m] * R.MDAYS[m] for m in range(12)) / 365
        yc8 = sum(c8[m] * R.MDAYS[m] for m in range(12)) / 365
        e1 = err(persisted_temps(y, 1)[24:], T[24:])
        e2 = err(persisted_temps(y, 2)[48:], T[48:])
        print(f"  {y:<5} {min(T):>6.1f} {hd:>9} {sp:>9,.0f} {max(D):>10.2f} {c6[0]:>10.1f} {c6[6]:>10.1f} "
              f"{yc6:>19.1f} {yc8:>6.1f}  {e1[0]:+.2f}/{e1[1]:.2f}  {e2[0]:+.2f}/{e2[1]:.2f}")
    ifs24 = read_ifs2024()
    T24, T25 = temps()["2024"], temps()["2025"]
    for k in (1, 2, 7):
        b4, r4, n4 = err(ifs24[k], T24)
        b5, r5, _ = err(R.base()["ifs"][k], T25)
        print(f"  archived ifs025 day {k}: 2024 bias {b4:+.2f} RMSE {r4:.2f} K ({n4:,} of 8,760 hours present) | "
              f"2025 bias {b5:+.2f} RMSE {r5:.2f} K")
    first = next(t for t, v in enumerate(ifs24[7]) if v is not None)
    print(f"  2024 previous_day7 first present at hour {first} (day {first // 24 + 1} of the year); earlier hours use P1's persisted temperature")

    # ------------------------------------------------------------ run the grid
    tasks = []
    for mode in ("normal", "own"):
        for y in YEARS:
            for n in (6, 8):
                for s in seeds:
                    tasks.append((y, n, "check", 0.0, s, mode))
                    for g in GUARDS:
                        tasks.append((y, n, "P1", g, s, mode))
                        if y in ("2024", "2025"):
                            tasks.append((y, n, "O3", g, s, mode))
                    if mode == "normal":
                        for w in WARM[1:]:
                            tasks.append((y, n, f"P1w{w:.0f}", 2.0, s, mode))
    for y in YEARS:                # warm caches (helps with fork)
        for g in GUARDS:
            fd(y, "P1", g)
            if y in ("2024", "2025"):
                fd(y, "O3", g)
        fd(y, "check", 0.0)
    if procs == 1:
        res = dict(_task(t) for t in tasks)
    else:
        try:
            ctx = mp.get_context("fork")
        except ValueError:
            ctx = mp.get_context()
        with ctx.Pool(procs) as pool:
            res = dict(pool.map(_task, tasks, chunksize=2))
    print(f"\n  ({len(tasks)} yearly runs)")

    for mode in ("normal", "own"):
        title = ("offers = 100% of the OTHER five years' mean monthly capacity (headline construction, out of sample)"
                 if mode == "normal" else "SENSITIVITY: offers = 100% of the held-out year's OWN monthly capacity")
        print(f"\n== 2{'a' if mode == 'normal' else 'b'}. Grid, {title} ==")
        print("  per year: missed of closed at seed 1 | missed summed over all seeds of closed | accepted % | coverage %")
        for n in (6, 8):
            for src in ("check", "P1", "O3"):
                for g in ((0.0,) if src == "check" else GUARDS):
                    for y in YEARS:
                        if src == "O3" and y not in ("2024", "2025"):
                            continue
                        a = agg(res, y, n, src, g, seeds, mode)
                        r1 = a["r1"]
                        print(f"  N={n} {src:<5} g{g:.0f} {y}: seed1 {r1['missed']:>3} of {r1['closed']:>6,} | seeds "
                              f"{a['missed']:>3} of {a['closed']:>7,} {a['per_seed']} | acc {a['acc']*100:5.1f}% "
                              f"refused work {r1['ref_share_w']*100:4.1f}% | cov {a['cov']*100:6.2f}%")

        print(f"\n== 3{'a' if mode == 'normal' else 'b'}. Leave-one-year-out guard choice ({mode} offers) ==")
        print("  rule: smallest guard with 0 misses on the training years (all seeds); else fewest misses")
        for n in (6, 8):
            for src, yrs in (("P1", YEARS), ("O3", ["2024", "2025"])):
                print(f"  -- N={n} {src} (training years: the other {len(yrs) - 1})")
                for y in yrs:
                    g, tm = pick_guard(res, y, n, src, seeds, mode, yrs)
                    a = agg(res, y, n, src, g, seeds, mode)
                    a2 = agg(res, y, n, src, 2.0, seeds, mode)
                    c = agg(res, y, n, "check", 0.0, seeds, mode)
                    r1 = a["r1"]
                    tms = " ".join(f"g{int(k)}:{v}" for k, v in tm.items())
                    print(f"    held out {y}: train misses [{tms}] -> pick {g:.0f} K | held-out seed1 {r1['missed']} of "
                          f"{r1['closed']:,}, all seeds {a['missed']} of {a['closed']:,} {a['per_seed']}, acc "
                          f"{a['acc']*100:.1f}% (check {c['acc']*100:.1f}%), refused work {r1['ref_share_w']*100:.1f}%, "
                          f"cov {a['cov']*100:.2f}% (check {c['cov']*100:.2f}%) | fixed 2 K: {a2['missed']} of "
                          f"{a2['closed']:,} {a2['per_seed']}")

    # ------------------------------------------------------------ 5. why P1 misses, and a magnitude margin
    print("\n== 5. Why P1 + 2 K misses in other years (normal offers, seed 1): missed by deadline month, J1+J2 ==")
    for n in (6, 8):
        for y in YEARS:
            r = res[(y, n, "P1", 2.0, 1, "normal")]
            print(f"  N={n} {y}: J1 {r['missed_t'][0]:>3} J2 {r['missed_t'][1]:>3} | by month "
                  + " ".join(f"{a + b:>3}" for a, b in r["miss_m"]))
    print("\n  Days with misses (N=6, P1 + 2 K, seed 1) and the daily mean temperature from 3 days before to 1 day after:")
    for y in YEARS:
        r = res[(y, 6, "P1", 2.0, 1, "normal")]
        T = temps()[y]
        dm = [sum(T[d * 24:(d + 1) * 24]) / 24 for d in range(365)]
        for dd in sorted(r["miss_d"]):
            print(f"    {y} day {dd + 1:>3} ({R.MONTH[dd * 24] + 1:>2}): {r['miss_d'][dd]:>3} missed | day means "
                  + " ".join(f"{dm[x]:5.1f}" for x in range(max(0, dd - 3), min(365, dd + 2))))
    print("\n  P1 with a magnitude margin w (persisted hourly temperature + w K in the space-heating term; flag guard 2 K)")
    print("  causal (uses only measured past temperatures); w = 0 is P1 + 2 K")
    def key_w(w):
        return ("P1", 2.0) if w == 0 else (f"P1w{w:.0f}", 2.0)
    for n in (6, 8):
        for w in WARM:
            src, g = key_w(w)
            cells = []
            for y in YEARS:
                a = agg(res, y, n, src, g, seeds, "normal")
                cells.append(f"{y} {a['r1']['missed']:>3}/{a['missed']:>4} {a['cov']*100:5.2f}%")
            print(f"  N={n} w={w:.0f}: seed1/all-seeds missed, mean coverage | " + " | ".join(cells))
        print(f"  N={n} LOYO choice of w (smallest w with 0 training misses, else fewest):")
        for y in YEARS:
            tm = {w: sum(res[(x, n, *key_w(w), s, "normal")]["missed"] for x in YEARS if x != y for s in seeds)
                  for w in WARM}
            zero = [w for w in WARM if tm[w] == 0]
            wp = zero[0] if zero else min(WARM, key=lambda v: (tm[v], v))
            a = agg(res, y, n, *key_w(wp), seeds, "normal")
            c = agg(res, y, n, "check", 0.0, seeds, "normal")
            p = agg(res, y, n, "P1", 2.0, seeds, "normal")
            print(f"    held out {y}: train " + " ".join(f"w{int(k)}:{v}" for k, v in tm.items())
                  + f" -> w={wp:.0f} | held-out seed1 {a['r1']['missed']} of {a['r1']['closed']:,}, all seeds "
                  f"{a['missed']} of {a['closed']:,} {a['per_seed']}, acc {a['acc']*100:.1f}%, cov {a['cov']*100:.2f}% "
                  f"(P1+2K {p['cov']*100:.2f}%, check {c['cov']*100:.2f}%)")

    # ------------------------------------------------------------ 4. tile line values (2025, seed 1)
    print("\n== 4. Tile line values: 2025, seed 1 (= the offer CSV), headline construction ==")
    stages = (("check run on the recorded 2025 weather", "check", 0.0), ("P1 persistence + 2 K", "P1", 2.0),
              ("P1 persistence + 3 K", "P1", 3.0), ("O3 archived ECMWF + 2 K", "O3", 2.0))
    for n in (6, 8):
        base = res[("2025", n, "check", 0.0, 1, "normal")]
        for lab, src, g in stages:
            r = res[("2025", n, src, g, 1, "normal")]
            win = r["ref_w"] - r["ref_w_summer"]
            print(f"  N={n} {lab:<40} missed {r['missed']} of {r['closed']:,} | accepted {r['acc']*100:.1f}% of "
                  f"{r['offered']:,} offered jobs | refused {r['ref_j'][0] + r['ref_j'][1]:,} jobs "
                  f"(J1 {r['ref_j'][0]:,}, J2 {r['ref_j'][1]:,}) = {r['ref_w']:,.0f} server-h = "
                  f"{r['ref_share_w']*100:.1f}% of {r['off_w']:,.0f} offered server-h | Jun-Aug {r['ref_w_summer']:,.0f} "
                  f"server-h ({r['ref_w_summer_day']:.1f}/day), rest of year {win:,.0f} | vs check run "
                  f"{r['ref_w'] - base['ref_w']:+,.0f} server-h, cov {(r['cov'] - base['cov'])*100:+.2f} pts "
                  f"(cov {r['cov']*100:.2f}%)")
        print(f"  N={n} refused server-h by month (check / P1+2K / O3+2K):")
        for lab, src, g in (stages[0], stages[1], stages[3]):
            r = res[("2025", n, src, g, 1, "normal")]
            print(f"      {src:<5} " + " ".join(f"{v:6.0f}" for v in r["ref_w_m"]))
    print("\n== 6. Pooled out-of-sample miss rates (all offer seeds; missed of closed) ==")
    for mode in ("normal", "own"):
        for n in (6, 8):
            for src, g, yrs in (("P1", 2.0, YEARS[:5]), ("P1", 3.0, YEARS[:5]), ("P1", 2.0, YEARS),
                                ("O3", 2.0, ["2024"]), ("O3", 0.0, ["2024"]), ("check", 0.0, YEARS)):
                m = sum(res[(y, n, src, g, s, mode)]["missed"] for y in yrs for s in seeds)
                c = sum(res[(y, n, src, g, s, mode)]["closed"] for y in yrs for s in seeds)
                yz = sum(1 for y in yrs if all(res[(y, n, src, g, s, mode)]["missed"] == 0 for s in seeds))
                s1 = [res[(y, n, src, g, 1, mode)]["missed"] for y in yrs]
                print(f"  {mode:<6} N={n} {src:<5} g{g:.0f} years {yrs[0]}-{yrs[-1]}: {m:,} of {c:,} = {m / c * 100:.3f}% | "
                      f"years with 0 in every seed: {yz} of {len(yrs)} | seed-1 misses by year {s1}")
    print(f"\n(done in {time.time()-t0:.1f} s)")


if __name__ == "__main__":
    main()
