"""Round 5, weak point "missed-deadline robustness".

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.

    python3 analysis/r5_miss_stress.py                 # all sections, seeds 1-5, all CPU cores
    python3 analysis/r5_miss_stress.py --seeds 3       # fewer seeds
    python3 analysis/r5_miss_stress.py --procs 1       # no multiprocessing
    python3 analysis/r5_miss_stress.py --quick         # regression + forecast stats only

Question: the headline "0 of ~32,000 / ~37,000 accepted jobs missed" (docs/overnight.md,
analysis/r4_headline.py section 3) holds with (i) a forecast from the same model family as
the 'truth', (ii) restart kept outside execution, (iii) no server failures, (iv) no runtime
overruns. This script stresses each one alone and all together, under the headline
scenario, for N = 6 and N = 8, with and without the 2 K guard band.

Headline scenario reproduced here
  offers    shaped100. Seed 1 = read from the committed analysis/r4_offers_shaped100_seed1.csv
            (what both drivers will read). Seeds 2..S = the same generator
            (r4_headline.offer_stream) with other seeds, for arrival noise.
  policy    cap + 8 kWh band, EDF admission dry run with the same permit function
            (r3_policy_check.step_permit), causal heating-day flag, guard band 2 K (or 0 K).
  forecast  ifs025 = archived ECMWF IFS 0.25 deg (analysis/r2_data/prev_ecmwf_ifs025.csv).

Stresses (each one switchable; every number below is an ASSUMPTION unless the research
file docs/research/r5-missed-deadline-robustness.md gives it a source)
  (a) forecast  gfs  = archived NOAA GFS (Open-Meteo Previous Runs, models=gfs_seamless)
                icon = archived DWD ICON (models=icon_seamless; it has no day-7 value, so
                       day 7 is taken from gfs_seamless, labelled)
                xxx_cold = the same series with its own yearly mean bias per lead removed
                       (in-sample, hindsight) and then 1 K subtracted: a forecast that is
                       too cold, i.e. promises too many permits.
                Files: analysis/r5_data/prev_gfs_seamless.csv, prev_icon_seamless.csv.
  (b) failures  each server fails as a Poisson process at `fail_rate` per server-year while
                up, and is then down for `repair_h` hours (no heat, no work). Failure at an
                hour boundary; J1/J2 checkpoint per file/batch, so no work is lost
                (ASSUMPTION). The scheduler knows servers that are down now and their repair
                end (dry run uses N minus those), but cannot foresee future failures.
  (c) overrun   true runtime = nominal x (1 + U(0, 2*o)), so mean overrun o; the scheduler
                admits and dry-runs on NOMINAL runtime (remaining = nominal - done, floored
                at 0). Optional mitigation pad: admission assumes nominal x (1 + pad).
  (d) restart   minutes per server start that use power, give heat and do no work, now
                INSIDE execution (r3_policy_check restart arithmetic). aware = the dry run
                derates the permits of servers it would have to start.
Seeds drive offers (2..S) and the failure / overrun draws (independent streams).

Nothing is edited. Imports: baseline_sweep (constants), r2_deadline_sim (base, poisson,
forward_fail, demand_from_temps, read_prev_runs layout), r3_policy_check (step_permit, pol,
run for regression), r4_headline (run, HEADLINE, offer_stream for regression).
"""
import math
import multiprocessing as mp
import random
import sys
from operator import itemgetter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from baseline_sweep import HEAT_VALUE, P_EL, PRICE, REC, TANK  # noqa: E402
import r2_deadline_sim as R  # noqa: E402
import r3_policy_check as P3  # noqa: E402
import r4_headline as H4  # noqa: E402

Q1 = REC * P_EL
H_YEAR = 8760
HORIZON = 168
JT = R.JT
MONTH = R.MONTH
EPS = 1e-9
OFFER_CSV = HERE / "r4_offers_shaped100_seed1.csv"
DATA5 = HERE / "r5_data"


# ---------------------------------------------------------------- inputs
def read_offer_csv():
    out = {6: [], 8: []}
    for ln in OFFER_CSV.read_text().split("\n"):
        if not ln or ln.startswith("#") or ln.startswith("hour"):
            continue
        p = ln.split(",")
        for n, a, b, c in ((6, 2, 3, 4), (8, 5, 6, 7)):
            f = None if p[c] == "" else (0 if p[c] == "J1" else 1)
            out[n].append((int(p[a]), int(p[b]), f))
    assert len(out[6]) == H_YEAR and len(out[8]) == H_YEAR
    return out


_C = {}


def offers(n, seed):
    key = ("off", n, seed)
    if key not in _C:
        if seed == 1:
            _C[key] = read_offer_csv()[n]
        else:
            _C[key] = H4.offer_stream(R.offer_rates("shaped100", n), seed)
    return _C[key]


def read_prev(path):
    """Previous Runs CSV -> list K=0..7 of 8760 temperatures; NaN kept as None."""
    cols = [[] for _ in range(8)]
    for ln in path.read_text().split("\n")[4:]:
        if not ln:
            continue
        p = ln.split(",")
        for k in range(8):
            v = p[1 + k]
            cols[k].append(None if v.lower() == "nan" or v == "" else float(v))
    return cols


def stats(fc, act):
    e = [a - b for a, b in zip(fc, act)]
    m = sum(e) / len(e)
    return m, math.sqrt(sum(x * x for x in e) / len(e))


def fc_temps(name):
    """-> list K=0..7 of temperatures; K=0 is the actual weather (the reference house)."""
    if ("ft", name) in _C:
        return _C[("ft", name)]
    b = R.base()
    act = b["act_t"]
    base_name = name.replace("_cold", "")
    if base_name == "perfect":
        ft = [act] * 8
    elif base_name == "ifs025":
        ft = [act] + b["ifs"][1:]
    elif base_name in ("gfs", "icon"):
        gfs = read_prev(DATA5 / "prev_gfs_seamless.csv")
        if base_name == "gfs":
            ft = [act] + gfs[1:]
        else:
            icon = read_prev(DATA5 / "prev_icon_seamless.csv")
            ft = [act]
            for k in range(1, 8):
                ft.append([g if v is None else v for v, g in zip(icon[k], gfs[k])])
    else:
        raise ValueError(name)
    if name.endswith("_cold"):
        new = [act]
        for k in range(1, 8):
            bias, _ = stats(ft[k], act)
            new.append([t - bias - 1.0 for t in ft[k]])
        ft = new
    _C[("ft", name)] = ft
    return ft


def fc_dem(name, guard):
    key = ("fd", name, guard)
    if key not in _C:
        ft = fc_temps(name)
        _C[key] = [R.base()["act_d"]] + [R.demand_from_temps(ft[k], 12.0 - guard) for k in range(1, 8)]
    return _C[key]


def outages(n, rate, repair_h, seed):
    """Per server: list of (start_hour, end_hour) down intervals. Poisson while up."""
    if rate <= 0:
        return []
    rng = random.Random(7_000_000 + 1000 * seed + n)
    out = []
    lam_h = rate / H_YEAR
    for s in range(n):
        t = 0.0
        while True:
            t += rng.expovariate(lam_h)
            if t >= H_YEAR:
                break
            st = int(t)
            en = st + int(repair_h)
            out.append((st, en, s))
            t = float(en)
    return sorted(out)


def cfg(**kw):
    c = dict(fc="ifs025", guard=2.0, fail_rate=0.0, repair_h=72, overrun=0.0, pad=0.0,
             restart=0.0, aware=True, fail_at=None, fail_aware=True)
    c.update(kw)
    return c


# ---------------------------------------------------------------- one year
def run(n, C, seed=1):
    b = R.base()
    act_d = b["act_d"]
    Fd = fc_dem(C["fc"], C["guard"])
    offs = offers(n, seed)
    rule, band, cap1 = "band", 8.0, True
    LEAD = [min(7, (L + 46) // 24) for L in range(HORIZON)]          # causal flag, as r3/r4
    r = C["restart"] / 60.0
    o, pad = C["overrun"], C["pad"]
    orng = random.Random(9_000_000 + 1000 * seed + n)
    outs = outages(n, C["fail_rate"], C["repair_h"], seed)
    if C["fail_at"] is not None:                                        # forced outage(s)
        st, k, dur = C["fail_at"]
        outs = sorted(outs + [(st, st + dur, 100 + i) for i in range(k)])
    oi, active = 0, []
    key0 = itemgetter(0)

    soc = used = dem_tot = dumped = sold_h = run_h = 0.0
    charging, kprev, on_prev = True, 0, 0
    starts = 0
    jobs = []                       # [deadline, type, true_remaining, est_remaining, nominal]
    off = [0, 0]; acc = [0, 0]; done = [0, 0]; missed = [0, 0]
    acc_w = missed_w = 0.0
    down_h = 0
    miss_month = [0] * 12

    for h in range(H_YEAR):
        m = MONTH[h]
        d = act_d[h]
        dem_tot += d
        # outages: start the ones that begin now, drop the repaired ones
        while oi < len(outs) and outs[oi][0] <= h:
            active.append(outs[oi])
            oi += 1
        if active:
            active = [x for x in active if x[1] > h]
        n_up = max(0, n - len(active))
        down_h += n - n_up
        if jobs:
            keep = []
            for j in jobs:
                if j[0] - h < math.ceil(j[2] - 1e-9):
                    missed[j[1]] += 1
                    missed_w += j[4]
                    miss_month[m] += 1
                else:
                    keep.append(j)
            jobs = keep
        ch_prev = charging
        cap, charging = P3.step_permit(rule, band, cap1, n_up, d, soc, charging, kprev)

        a0, a1, first = offs[h]
        arr = [a0, a1]
        if a0 or a1:
            c0 = cap
            if active and not C["fail_aware"]:          # scheduler not told: plans with all N servers
                c0, _ = P3.step_permit(rule, band, cap1, n, d, soc, ch_prev, kprev)
            cf = [c0]
            s = soc + c0 * Q1
            s -= min(d, s)
            ch, kp = charging, c0
            for L in range(1, HORIZON):
                nav = n
                if active and C["fail_aware"]:
                    nav = n - sum(1 for x in active if x[1] > h + L)
                dF = Fd[LEAD[L]][(h + L) % H_YEAR]
                c, ch = P3.step_permit(rule, band, cap1, nav, dF, s, ch, kp)
                s += c * Q1
                s -= min(dF, s)
                kp = c
                cf.append(c)
            if C["aware"] and r > 0:
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
                W[j[0] - h] += j[3]
            slack, w = [0.0] * (HORIZON + 1), 0.0
            for L in range(HORIZON + 1):
                w += W[L]
                slack[L] = cum[L] - w
            order = (0, 1) if first == 0 else (1, 0)
            new = []
            for i in order:
                if not arr[i]:
                    continue
                _, rt, dl = JT[i]
                rte = rt * (1.0 + pad)
                off[i] += arr[i]
                room = min(slack[dl:])
                k = max(0, min(arr[i], int(room / rte + 1e-9)))
                if k:
                    for L in range(dl, HORIZON + 1):
                        slack[L] -= k * rte
                    for _ in range(k):
                        true_rt = rt * (1.0 + orng.uniform(0.0, 2.0 * o)) if o > 0 else rt
                        new.append([h + dl, i, true_rt, rte, rt])
                    jobs.extend(new[-k:])
                    acc[i] += k
                    acc_w += k * rt
            jobs.sort(key=key0)
            while new:
                prox = [[j[0], j[1], j[3], j] for j in jobs]
                failing = [p[3] for p in R.forward_fail(prox, h, cf, 1.0)]
                if not failing:
                    break
                pick = next((j for j in failing if any(j is x for x in new)), None) or new[-1]
                new = [x for x in new if x is not pick]
                jobs = [j for j in jobs if j is not pick]
                acc[pick[1]] -= 1
                acc_w -= pick[4]

        # execution on the actual permits, earliest deadline first
        if r <= 0:
            work = 0.0
            if jobs and cap > 0:
                fin = False
                for j in jobs:
                    step = min(j[2], 1.0, cap - work)
                    j[2] -= step
                    j[3] = max(0.0, j[3] - step)
                    work += step
                    if j[2] <= 1e-9:
                        done[j[1]] += 1
                        fin = True
                    if work >= cap - 1e-9:
                        break
                if fin:
                    jobs = [j for j in jobs if j[2] > 1e-9]
            on = int(math.ceil(work - 1e-9))
            new_starts = max(0, on - on_prev)
            ran = work
        else:
            warm = float(min(cap, on_prev))
            cold = (cap - min(cap, on_prev)) * (1.0 - r)
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
                    j[3] = max(0.0, j[3] - step)
                    if j[2] <= 1e-9:
                        done[j[1]] += 1
                        fin = True
                if fin:
                    jobs = [j for j in jobs if j[2] > 1e-9]
            work = w_warm + w_cold
            new_starts = int(math.ceil(w_cold / (1.0 - r) - 1e-9)) if w_cold > 1e-9 else 0
            on = (int(min(cap, on_prev)) + new_starts) if new_starts else int(math.ceil(w_warm - 1e-9))
            ran = work + new_starts * r
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

    closed = sum(done) + sum(missed)
    elec = run_h * P_EL * PRICE
    return dict(n=n, seed=seed, coverage=used / dem_tot, dumped=dumped, util=run_h / (n * H_YEAR),
                run_h=run_h, sold_h=sold_h, starts=starts, offered=sum(off), accepted=sum(acc),
                acc_jobs=sum(acc) / max(1, sum(off)), missed_n=sum(missed), closed_n=closed,
                missed_j=list(missed), missed=sum(missed) / max(1, closed),
                missed_work=missed_w / max(EPS, acc_w), down_h=down_h, outages=len(outs),
                miss_month=miss_month, used=used,
                breakeven=(elec - used * HEAT_VALUE) / sold_h if sold_h else float("nan"))


# ---------------------------------------------------------------- scenarios
FAIL_LO, FAIL_HI, FAIL_X = 0.08, 0.55, 1.0     # per server-year (see research file for sources)

SCEN = [
    # label, config, uses randomness beyond offers?
    ("BASE headline (ifs025)", cfg(), False),
    ("check: perfect forecast", cfg(fc="perfect"), False),
    ("a1 forecast GFS (independent)", cfg(fc="gfs"), False),
    ("a2 forecast ICON (independent)", cfg(fc="icon"), False),
    ("a3 GFS debiased -1 K (cold)", cfg(fc="gfs_cold"), False),
    ("a4 ICON debiased -1 K (cold)", cfg(fc="icon_cold"), False),
    ("a5 ifs025 debiased -1 K (cold)", cfg(fc="ifs025_cold"), False),
    (f"b1 failures {FAIL_LO}/srv-yr, 72 h repair", cfg(fail_rate=FAIL_LO), True),
    (f"b2 failures {FAIL_HI}/srv-yr, 72 h repair", cfg(fail_rate=FAIL_HI), True),
    (f"b3 failures {FAIL_HI}/srv-yr, 24 h repair", cfg(fail_rate=FAIL_HI, repair_h=24), True),
    (f"b4 failures {FAIL_HI}/srv-yr, 168 h repair", cfg(fail_rate=FAIL_HI, repair_h=168), True),
    (f"b5 failures {FAIL_X}/srv-yr, 72 h repair", cfg(fail_rate=FAIL_X), True),
    (f"b6 failures {FAIL_HI}/srv-yr, 72 h, scheduler NOT told", cfg(fail_rate=FAIL_HI, fail_aware=False), True),
    ("b7 failures 2.0/srv-yr, 168 h, NOT told (break-point probe)", cfg(fail_rate=2.0, repair_h=168, fail_aware=False), True),
    ("b8 failures 4.0/srv-yr, 168 h, NOT told (break-point probe)", cfg(fail_rate=4.0, repair_h=168, fail_aware=False), True),
    ("b9 1 server down all year, NOT told (bound)", cfg(fail_at=(0, 1, 8760), fail_aware=False), False),
    ("c1 overrun mean +10%", cfg(overrun=0.10), True),
    ("c2 overrun mean +30%", cfg(overrun=0.30), True),
    ("c3 overrun +30%, admission pads 30%", cfg(overrun=0.30, pad=0.30), True),
    ("d0 restart 2.1 s in exec (laptop, measured), aware", cfg(restart=2.1 / 60.0), False),
    ("d1 restart 5 min in exec, aware", cfg(restart=5.0), False),
    ("d2 restart 15 min in exec, aware", cfg(restart=15.0), False),
    ("d3 restart 15 min in exec, NOT aware", cfg(restart=15.0, aware=False), False),
    ("d4 restart 30 min in exec, aware", cfg(restart=30.0), False),
    ("E1 COMBINED plausible: ICON + fail 0.55/72h + overrun 10% + restart 15 aware",
     cfg(fc="icon", fail_rate=FAIL_HI, overrun=0.10, restart=15.0), True),
    ("E2 COMBINED plausible, GFS", cfg(fc="gfs", fail_rate=FAIL_HI, overrun=0.10, restart=15.0), True),
    ("E3 COMBINED harsh: ICON cold + fail 1.0/72h + overrun 30% + restart 15 NOT aware",
     cfg(fc="icon_cold", fail_rate=FAIL_X, overrun=0.30, restart=15.0, aware=False), True),
    ("E4 E1 + admission pads 30%", cfg(fc="icon", fail_rate=FAIL_HI, overrun=0.10, restart=15.0, pad=0.30), True),
]


def task(args):
    label, n, guard, seed = args
    c = dict(next(x[1] for x in SCEN if x[0] == label))
    c["guard"] = guard
    res = run(n, c, seed)
    return (label, n, guard, seed), res


def coldest_days():
    """Coldest day of the year that is at least 8 days before year end (31 Dec is the coldest
    day but a failure there is cut off by the end of the simulated year), and the coldest
    January day."""
    rows = R.base()["rows"]
    act = R.base()["act_t"]
    means = [sum(act[d * 24:(d + 1) * 24]) / 24 for d in range(365)]
    out = []
    for lo, hi in ((0, 357), (0, 31)):
        di = min(range(lo, hi), key=lambda d: means[d])
        out.append((di, rows[di * 24][0][:10], means[di]))
    yd = max(range(365), key=lambda d: -means[d])
    return out, (yd, rows[yd * 24][0][:10], means[yd])


def fmt_counts(rs):
    return " ".join(f"{r['missed_n']}/{r['closed_n']:,}" for r in rs)


def main():
    argv = sys.argv[1:]
    nseeds = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else 5
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    seeds = list(range(1, nseeds + 1))
    b = R.base()
    act = b["act_t"]

    print("r5_miss_stress.py. Stand-in reference house 2025; headline shaped100 offers (seed 1 from the committed CSV,")
    print("seeds 2.. from r4_headline.offer_stream); cap + 8 kWh band; EDF dry-run admission; causal flag. Currency CHF.\n")

    # ---- 0. regression
    print("== 0. Regression ==")
    ok = True
    for n in (6, 8):
        st = H4.offer_stream(R.offer_rates("shaped100", n), 1)
        same = st == read_offer_csv()[n]
        a = H4.run(n, H4.HEADLINE, "shaped100", 1)
        me = run(n, cfg(), 1)
        g = (a["accepted"], a["missed_n"], a["starts"]) == (me["accepted"], me["missed_n"], me["starts"]) \
            and abs(a["coverage"] - me["coverage"]) < 1e-12
        A = P3.pol(fc="ifs025", guard=2.0, restart=15.0, aware=True, rule="band", band=8.0, cap1=True)
        a3 = P3.run(n, A, "shaped100", 1)
        me3 = run(n, cfg(restart=15.0), 1)
        g3 = (a3["accepted"], a3["missed_n"], a3["starts"]) == (me3["accepted"], me3["missed_n"], me3["starts"]) \
            and abs(a3["coverage"] - me3["coverage"]) < 1e-12
        ok &= same and g and g3
        print(f"  N={n}: offer_stream(seed 1) == CSV: {same}; no stress vs r4_headline.run(HEADLINE): accepted {a['accepted']} / "
              f"{me['accepted']}, missed {a['missed_n']} / {me['missed_n']}, coverage {a['coverage']*100:.3f}% / "
              f"{me['coverage']*100:.3f}% -> {'OK' if g else 'MISMATCH'}")
        print(f"        restart 15 aware vs r3_policy_check.run(policy A, shaped100, seed 1): accepted {a3['accepted']} / "
              f"{me3['accepted']}, missed {a3['missed_n']} / {me3['missed_n']}, starts {a3['starts']} / {me3['starts']} "
              f"-> {'OK' if g3 else 'MISMATCH'}")
    print(f"  all regression checks: {'OK' if ok else 'MISMATCH'}")

    # ---- 1. forecast error of each source against the reference-house temperature
    print("\n== 1. Forecast error against the reference-house temperature (forecast - truth, K, 8,760 h of 2025) ==")
    for name in ("ifs025", "gfs", "icon", "gfs_cold", "icon_cold", "ifs025_cold"):
        ft = fc_temps(name)
        row = []
        for k in (1, 3, 5, 7):
            bi, rm = stats(ft[k], act)
            row.append(f"d{k} bias {bi:+.2f} RMSE {rm:.2f}")
        win = [h for h in range(H_YEAR) if MONTH[h] in (0, 1, 11)]
        bw, rw = stats([ft[1][h] for h in win], [act[h] for h in win])
        print(f"  {name:<12} " + " | ".join(row) + f" | Dec-Feb d1 bias {bw:+.2f} RMSE {rw:.2f}")
    for name in ("ifs025", "gfs", "icon", "icon_cold"):
        ft = fc_temps(name)
        for k in (1, 3, 7):
            wrong_h = wrong_c = 0
            for dd in range(365):
                tf = sum(ft[k][dd * 24:(dd + 1) * 24]) / 24
                ta = sum(act[dd * 24:(dd + 1) * 24]) / 24
                if tf < 12 and ta >= 12:
                    wrong_h += 1
                if tf >= 12 and ta < 12:
                    wrong_c += 1
            print(f"  {name:<12} day {k}: heating-day flag wrong, forecast heating but not: {wrong_h:>2} days; "
                  f"forecast no heating but yes: {wrong_c:>2} days")
    if "--quick" in argv:
        return

    # ---- 2. scenario runs
    cfgs = []
    for label, c, rnd in SCEN:
        for n in (6, 8):
            for guard in (2.0, 0.0):
                for s in seeds:
                    cfgs.append((label, n, guard, s))
    print(f"\n({len(cfgs)} simulated years)", flush=True)
    if procs == 1:
        out = [task(x) for x in cfgs]
    else:
        with mp.Pool(procs) as pool:
            out = pool.map(task, cfgs, chunksize=1)
    res = dict(out)

    print("\n== 2. Missed deadlines under each stress, headline shaped100 offers ==")
    print("  missed x/y per seed (seed 1 = committed CSV offers); mean missed % of accepted jobs; % of accepted work in missed jobs;")
    print("  accepted % of offered jobs; coverage; utilisation (run h incl. restart / N x 8760); deltas vs BASE in brackets\n")
    for guard in (2.0, 0.0):
        print(f"  ---- guard band {guard:g} K ----")
        for n in (6, 8):
            base = [res[("BASE headline (ifs025)", n, guard, s)] for s in seeds]
            bc = sum(r["coverage"] for r in base) / len(base)
            bu = sum(r["util"] for r in base) / len(base)
            print(f"  N={n}")
            print(f"    {'scenario':<78} {'missed x/y per seed':<58} {'miss%':>7} {'work%':>7} {'acc%':>5} {'cover':>14} {'util':>13}")
            for label, c, rnd in SCEN:
                rs = [res[(label, n, guard, s)] for s in seeds]
                mm = sum(r["missed"] for r in rs) / len(rs)
                mw = sum(r["missed_work"] for r in rs) / len(rs)
                ac = sum(r["acc_jobs"] for r in rs) / len(rs)
                cv = sum(r["coverage"] for r in rs) / len(rs)
                ut = sum(r["util"] for r in rs) / len(rs)
                print(f"    {label[:78]:<78} {fmt_counts(rs):<58} {mm*100:>6.3f}% {mw*100:>6.3f}% {ac*100:>4.1f}% "
                      f"{cv*100:>6.2f}% ({(cv-bc)*100:+.2f}) {ut*100:>5.1f}% ({(ut-bu)*100:+.1f})")
            print()

    # ---- 3. pooled summaries for the pitch
    print("== 3. Pooled over seeds (sum of missed / sum of closed accepted jobs), guard 2 K ==")
    for label, c, rnd in SCEN:
        line = []
        for n in (6, 8):
            rs = [res[(label, n, 2.0, s)] for s in seeds]
            x, y = sum(r["missed_n"] for r in rs), sum(r["closed_n"] for r in rs)
            j2 = sum(r["missed_j"][1] for r in rs)
            mx = max(r["missed_n"] for r in rs)
            line.append(f"N={n}: {x}/{y:,} = {x/y*100:.3f}% (max/yr {mx}, J2 {j2})")
        print(f"  {label[:60]:<60} " + " | ".join(line))
    print("\n  Missed by month (pooled over seeds, guard 2 K), E1 combined plausible:")
    for n in (6, 8):
        mmn = [sum(res[(SCEN[24][0], n, 2.0, s)]["miss_month"][m] for s in seeds) for m in range(12)]
        print(f"    N={n}: " + " ".join(f"{m+1}:{v}" for m, v in enumerate(mmn)))
    for n in (6, 8):
        rs = [res[(SCEN[8][0], n, 2.0, s)] for s in seeds]
        print(f"  b2 N={n}: outages per year per seed {[r['outages'] for r in rs]}, server-hours down {[r['down_h'] for r in rs]}")

    # ---- 4. a server (or two) dies on the coldest day
    days, yd = coldest_days()
    print(f"\n== 4. Q&A: servers die at 00:00 on a cold day, headline offers seed 1, guard 2 K ==")
    print(f"  (coldest day of 2025 is {yd[1]}, mean {yd[2]:.1f} C, but it is the last day of the simulated year; used instead:)")
    seen = set()
    for di, date, tm in days:
        if di in seen:
            continue
        seen.add(di)
        dem = b["act_d"][di * 24:(di + 1) * 24]
        print(f"  -- {date}, daily mean {tm:.1f} C, demand {sum(dem):.0f} kWh that day; one server gives at most "
              f"{24*Q1:.1f} kWh/day = {24*Q1/sum(dem)*100:.0f}% of it --")
        for n in (6, 8):
            for fc in ("ifs025", "icon"):
                b0 = run(n, cfg(fc=fc), 1)
                for k, dur, aw in ((1, 72, True), (1, 168, True), (2, 72, True), (1, 72, False), (2, 72, False)):
                    r1 = run(n, cfg(fc=fc, fail_at=(di * 24, k, dur), fail_aware=aw), 1)
                    print(f"    N={n} {fc:<6} {k} server(s) down {dur:>3} h, scheduler {'told   ' if aw else 'NOT told'}: missed "
                          f"{b0['missed_n']} -> {r1['missed_n']} of {r1['closed_n']:,}; accepted {b0['accepted']:,} -> {r1['accepted']:,}; "
                          f"server heat lost {b0['used']-r1['used']:.0f} kWh (backup heater); coverage "
                          f"{b0['coverage']*100:.2f}% -> {r1['coverage']*100:.2f}%")

if __name__ == "__main__":
    main()
