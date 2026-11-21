"""Round 4, weak point "demand side and the headline run".

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.

    python3 analysis/r4_headline.py                    # all sections, seeds 1-3, all CPU cores
    python3 analysis/r4_headline.py --seeds 5          # more seeds
    python3 analysis/r4_headline.py --procs 1          # no multiprocessing
    python3 analysis/r4_headline.py --write-offers analysis/r4_offers_shaped100_seed1.csv

What it does
  Recomputes the reference-house key figures under ONE headline offer scenario
  (heat-shaped contract at 100 % of the 2020-24 normal capacity, "shaped100") with the
  policy the plan now adopts (cap + 8 kWh band, EDF admission dry run that calls the
  same permit function, archived ECMWF ifs025 forecast with causal heating-day flag and
  2 K guard band, restart NOT inside execution but as an accounting line), for N = 6 and
  N = 8, plus half / double the offer rate, the saturating reference, a "named customer
  only" row, and the pinned real job (R6) in two variants.

Nothing is edited. It imports
  baseline_sweep.py    case constants, simulate() (regression)
  r2_deadline_sim.py   base(), offer_rates(), poisson(), forward_fail(), MONTH, JT, WORK_SHARE
  r3_policy_check.py   step_permit() (the permit rule), fc_demand(), pol(), run() (regression)
  r3_income.py         prices P1 / P2, FX, E_PROBE, J2 tokens per kWh, WHOLESALE
The yearly loop below is r3_policy_check.run() with restart = 0, plus (i) custom offer
rates, (ii) sold server-hours per job type, (iii) an optional pinned real job.
Section 0 checks that, without the pin, it reproduces r3_policy_check.run() exactly.

Pinned real job (R6), as specified in docs/overnight.md:
  the real job is bound to slot s and runs in an hour iff the permit count k >= s;
  while it runs it uses one of the k permitted servers, the rest go to the EDF pool;
  the admission dry run subtracts it from the forecast permits in the same way.
  It has no deadline (a backlog item) -> its hours are SOLD J1 work, it is excluded
  from the missed-deadline denominator, and this is printed.
  mode 'year' = always ready all year;  mode 'day' = only on the demo date.
"""
import math
import random
import sys
from operator import itemgetter
from pathlib import Path

sys.dont_write_bytecode = True  # do not touch analysis/__pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import HEAT_VALUE, P_EL, PRICE, REC, TANK, simulate  # noqa: E402
import r2_deadline_sim as R  # noqa: E402
import r3_policy_check as P3  # noqa: E402
import r3_income as I  # noqa: E402

Q1 = REC * P_EL
H_YEAR = 8760
HORIZON = 168
JT = R.JT
MONTH = R.MONTH
MDAYS = R.MDAYS
RESTART_H = 0.25          # ASSUMPTION (plan): 15 min per start, accounting line only

# headline policy: cap + 8 kWh band, archived ifs025, causal flag, 2 K guard, no restart in execution
HEADLINE = P3.pol(fc="ifs025", guard=2.0, rule="band", band=8.0, cap1=True)
PERFECT = P3.pol(rule="band", band=8.0, cap1=True)        # consistency check: must give 0 missed

# ---------------------------------------------------------------- customer volumes (section 1)
# Each row: label, volume, unit, status, source URL. Read 2026-11-21.
CUSTOMERS = [
    ("A Swiss public broadcaster archive (SRF), spoken audio digitised", 1.25e6, "audio-hours (stock, one-off)",
     "SOURCED", "https://www.srf.ch/news/automatische-spracherkennung-computer-schryb-aues-mit-won-ig-hie-saege (22 Jan 2023)"),
    ("  same archive, audio material in the basement", 1.0e6, "audio-hours (stock; 'ueber eine Million')",
     "SOURCED", "https://www.srf.ch/radio-srf-musikwelle/audio-und-videomaterial-der-schatz-des-srf-im-archiv-roboter (27 Mar 2024)"),
    ("B Swiss hospitals, inpatient stays per year (discharge documents)", 1.5e6, "stays per year (2023)",
     "SOURCED", "https://www.admin.ch/gov/de/start/dokumentation/medienmitteilungen.msg-id-103286.html (26 Nov 2024)"),
    ("C Swiss accident insurer (Suva), doctor and hospital invoices checked", 2.7e6, "invoices per year (2024)",
     "SOURCED", "https://www.suva.ch/de-ch/ueber-uns/magazin-und-medien/medien/heilkosten (24 Sep 2025)"),
]
# MLPerf v5.1 5.1-0062 (8 x B200, llama3.1-8b, Offline): 1,148.12 samples/s at 9,436.05 W (sourced in round 3)
SAMPLES_PER_KWH_B200 = 1148.12 * 3600 / 9.43605      # one sample = one news article summarised to 128 tokens
# MLPerf v6.1 6.1-0032 (2 x Xeon 6787P): 1,227.99 tokens/s; 128 output tokens per sample; 1 kW ASSUMPTION
SAMPLES_PER_KWH_CPU = 1227.99 / 128 * 3600
SAMPLES_PER_DOC = 10.0    # ASSUMPTION: one hospital stay / invoice = 10 MLPerf-sized summarisation calls


# ---------------------------------------------------------------- offers
def rates_for(demand, n, flat=None):
    if demand == "flat_custom":
        return [flat] * 12
    return R.offer_rates(demand, n)


def offer_stream(rates, seed):
    """Per hour: (j1 offers, j2 offers, j2 first?). Same RNG call order as r2/r3 run()."""
    rng = random.Random(seed)
    out = []
    for h in range(H_YEAR):
        m = MONTH[h]
        lam = [rates[m] * R.WORK_SHARE[i] / JT[i][1] / 24.0 for i in (0, 1)]
        a0, a1 = R.poisson(rng, lam[0]), R.poisson(rng, lam[1])
        first = None
        if a0 or a1:
            first = 0 if rng.random() < 0.5 else 1
        out.append((a0, a1, first))
    return out


# ---------------------------------------------------------------- one year
def run(n, P, demand="shaped100", seed=1, flat=None, pin=None):
    """pin = None | dict(slot=s, mode='year') | dict(slot=s, mode='day', day=index 0..364)."""
    b = R.base()
    act_d = b["act_d"]
    Fd = P3.fc_demand(P["fc"], P["guard"], seed)
    rates = rates_for(demand, n, flat)
    rng = random.Random(seed)
    key0 = itemgetter(0)
    rule, band, cap1 = P["rule"], P["band"], P["cap1"]
    lead = (lambda L: min(7, (L + 46) // 24)) if P["causal"] else (lambda L: (L + 23) // 24)
    LEAD = [lead(L) for L in range(HORIZON)]
    ps = pin["slot"] if pin else None

    def pin_on(hh):
        if not pin:
            return False
        return True if pin["mode"] == "year" else (hh // 24 == pin["day"])

    soc = used = dem_tot = dumped = sold_h = run_h = 0.0
    charging, kprev, on_prev = True, 0, 0
    starts = 0
    jobs = []
    off = [0, 0]; acc = [0, 0]; done = [0, 0]; missed = [0, 0]
    off_w = acc_w = 0.0
    sold_t = [0.0, 0.0]
    pin_h = 0.0
    summer = dict(off=[0, 0], acc=[0, 0])
    ks_cap, ks_on, pin_run = [], [], []

    for h in range(H_YEAR):
        m = MONTH[h]
        d = act_d[h]
        dem_tot += d
        if jobs:
            keep = []
            for j in jobs:
                if j[0] - h < math.ceil(j[2] - 1e-9):
                    missed[j[1]] += 1
                else:
                    keep.append(j)
            jobs = keep
        cap, charging = P3.step_permit(rule, band, cap1, n, d, soc, charging, kprev)
        prun = pin_on(h) and cap >= ps
        pool = cap - (1 if prun else 0)

        lam = [rates[m] * R.WORK_SHARE[i] / JT[i][1] / 24.0 for i in (0, 1)]
        arr = [R.poisson(rng, lam[0]), R.poisson(rng, lam[1])]
        if arr[0] or arr[1]:
            cf = [pool]
            s = soc + cap * Q1
            s -= min(d, s)
            ch, kp = charging, cap
            for L in range(1, HORIZON):
                dF = Fd[LEAD[L]][(h + L) % H_YEAR]
                c, ch = P3.step_permit(rule, band, cap1, n, dF, s, ch, kp)
                s += c * Q1
                s -= min(dF, s)
                kp = c
                cf.append(c - (1 if (pin_on(h + L) and c >= ps) else 0))
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
                    for L in range(dl, HORIZON + 1):
                        slack[L] -= k * rt
                    for _ in range(k):
                        new.append([h + dl, i, rt])
                    jobs.extend(new[-k:])
                    acc[i] += k
                    acc_w += k * rt
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
                if m in (5, 6, 7):
                    summer["acc"][pick[1]] -= 1

        # execution: pinned job first (if its slot has a permit), then EDF on the pool
        work = 0.0
        if prun:
            work += 1.0
            pin_h += 1.0
            sold_t[0] += 1.0
        if jobs and pool > 0:
            fin = False
            w0 = 0.0
            for j in jobs:
                step = min(j[2], 1.0, pool - w0)
                j[2] -= step
                w0 += step
                sold_t[j[1]] += step
                if j[2] <= 1e-9:
                    done[j[1]] += 1
                    fin = True
                if w0 >= pool - 1e-9:
                    break
            if fin:
                jobs = [j for j in jobs if j[2] > 1e-9]
            work += w0
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
        ks_cap.append(cap)
        ks_on.append(on)
        pin_run.append(1 if prun else 0)

    closed = [done[i] + missed[i] for i in (0, 1)]
    elec = run_h * P_EL * PRICE
    heat = used * HEAT_VALUE
    return dict(
        n=n, coverage=used / dem_tot, dumped=dumped, util=run_h / (n * H_YEAR), run_h=run_h,
        sold_h=sold_h, sold_t=sold_t, pin_h=pin_h, starts=starts,
        offered=sum(off), off=off, accepted=sum(acc), acc=acc, acc_jobs=sum(acc) / max(1, sum(off)),
        acc_work=acc_w / max(1e-9, off_w), missed_n=sum(missed), closed_n=sum(closed),
        missed=sum(missed) / max(1, sum(closed)),
        acc_j1_summer=summer["acc"][0] / max(1, summer["off"][0]),
        elec=elec, heat_val=heat,
        breakeven=(elec - heat) / sold_h if sold_h else float("nan"),
        be_restart=(elec - heat) / (sold_h - starts * RESTART_H) if sold_h else float("nan"),
        ks_cap=ks_cap, ks_on=ks_on, pin_run=pin_run)


# ---------------------------------------------------------------- money
def values_per_sh(e=I.E_PROBE):
    """List value (CHF) of one sold server-hour per job type, low/central/high (r3_income prices)."""
    v1 = {k: I.chf(I.P1[k][0]) * 1000.0 / e for k in I.P1}                 # J1 at laptop efficiency
    v2 = {k: I.chf(I.P2[k][0]) * I.J2_TOK_PER_KWH_B200 / 1e6 for k in I.P2}   # J2 at B200-slice efficiency
    return v1, v2


def money(r, w=I.WHOLESALE):
    v1, v2 = values_per_sh()
    lv = {k: r["sold_t"][0] * v1[k] + r["sold_t"][1] * v2[k] for k in v1}
    lv_j1only = {k: r["sold_h"] * v1[k] for k in v1}
    net = r["elec"] - r["heat_val"]
    return dict(list_value=lv, income={k: w * lv[k] for k in lv}, share_needed={k: net / lv[k] for k in lv},
                income_j1only={k: w * lv_j1only[k] for k in lv}, net=net)


# ---------------------------------------------------------------- tasks
def task(cfg):
    key, n, pname, demand, seed, flat, pin = cfg
    P = {"headline": HEADLINE, "perfect": PERFECT}[pname]
    res = run(n, P, demand, seed, flat, pin)
    if seed != 1:
        for f in ("ks_cap", "ks_on", "pin_run"):
            res.pop(f)
    return (key, n, seed), res


def mean_of(res, key, n, seeds, f):
    v = [res[(key, n, s)][f] for s in seeds]
    return sum(v) / len(v), min(v), max(v)


def day_index(date):
    return R.base()["rows"].index(next(r for r in R.base()["rows"] if r[0].startswith(date))) // 24


def date_of(di):
    return R.base()["rows"][di * 24][0][:10]


def pause_resume_days(ks, slot, month, pinrun=None):
    """Days of month where the slot pattern (k >= slot, or the pinned-run flag) pauses then resumes."""
    rows = R.base()["rows"]
    out = []
    for di in range(365):
        if rows[di * 24][0][5:7] != month:
            continue
        seg = (pinrun[di * 24:(di + 1) * 24] if pinrun else [1 if k >= slot else 0 for k in ks[di * 24:(di + 1) * 24]])
        pat = "".join("#" if x else "." for x in seg)
        ev = [(i + 1, "P" if a == "#" else "R") for i, (a, b) in enumerate(zip(pat, pat[1:])) if a != b]
        pr = [(a[0], bb[0]) for a, bb in zip(ev, ev[1:]) if a[1] == "P" and bb[1] == "R"]
        if pr and pr[0][0] >= 2 and pr[0][1] <= 22:
            out.append((date_of(di), pat, pr[0][0], pr[0][1]))
    return out


def write_offers(path, seed=1):
    rows = R.base()["rows"]
    st = {n: offer_stream(R.offer_rates("shaped100", n), seed) for n in (6, 8)}
    with open(path, "w") as f:
        f.write("# r4_headline.py offer stream: shaped100 (heat-shaped contract, 100% of 2020-24 mean follow capacity per month),"
                f" Poisson, random.Random({seed}), J1 0.5 server-h / 24 h deadline, J2 4 server-h / 168 h deadline, 50/50 by work\n")
        f.write("hour,time_local,n6_j1,n6_j2,n6_first,n8_j1,n8_j2,n8_first\n")
        for h in range(H_YEAR):
            a, b = st[6][h], st[8][h]
            fa = "" if a[2] is None else ("J1" if a[2] == 0 else "J2")
            fb = "" if b[2] is None else ("J1" if b[2] == 0 else "J2")
            f.write(f"{h},{rows[h][0]},{a[0]},{a[1]},{fa},{b[0]},{b[1]},{fb}\n")
    print(f"wrote {path}")


# ---------------------------------------------------------------- report
def main():
    argv = sys.argv[1:]
    if "--write-offers" in argv:
        write_offers(argv[argv.index("--write-offers") + 1])
        return
    nseeds = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else 3
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    seeds = list(range(1, nseeds + 1))
    rows = R.base()["rows"]
    v1, v2 = values_per_sh()

    print("r4_headline.py. Currency CHF; 1 USD = %.4f CHF (ECB 20 Nov 2026, sourced in round 1). Stand-in reference house, 2025." % I.FX)
    print("Headline policy: cap + 8 kWh band; EDF admission dry run with the same permit function; archived ECMWF ifs025 forecast,")
    print("causal heating-day flag, 2 K guard band; restart NOT in execution (accounting line, 15 min ASSUMPTION).")
    print("Jobs: J1 0.5 server-h / 24 h, J2 4 server-h / 168 h, 50/50 by work, Poisson (ASSUMPTIONS, round 1-3). No partner site,")
    print("no failures or overruns. Forecast and 'actual' weather come from the same model family (errors understated).\n")

    # ---- 0. regression
    print("== 0. Regression: this loop without a pin = r3_policy_check.run() ==")
    ok_all = True
    for n in (6, 8):
        for dm in ("shaped100", "saturating"):
            a = P3.run(n, HEADLINE, dm, 1)
            me = run(n, HEADLINE, dm, 1)
            ok = (a["accepted"], a["missed_n"], a["starts"]) == (me["accepted"], me["missed_n"], me["starts"]) \
                and abs(a["coverage"] - me["coverage"]) < 1e-12 and abs(a["sold_h"] - me["sold_h"]) < 1e-6
            ok_all &= ok
            print(f"  N={n} {dm:<10} seed 1: r3 accepted {a['accepted']}, missed {a['missed_n']}, starts {a['starts']}, "
                  f"coverage {a['coverage']*100:.3f}% | r4 {me['accepted']}, {me['missed_n']}, {me['starts']}, "
                  f"{me['coverage']*100:.3f}% -> {'OK' if ok else 'MISMATCH'}")
        b0 = simulate(rows, n)
        print(f"  N={n} unlimited reference (baseline_sweep follow): coverage {b0['coverage']*100:.2f}%, {b0['run_h']:.0f} server-h")
    print(f"  all regression checks: {'OK' if ok_all else 'MISMATCH'}")

    # ---- 1. customer volumes
    print("\n== 1. Customer volumes in 1 kW server-hours (scaling rules of round 3) ==")
    ah_per_sh = 1000.0 / I.E_PROBE
    print(f"  J1 transcription: {ah_per_sh:.0f} audio-h per server-h (laptop rule, E = {I.E_PROBE} Wh/audio-h, COMPUTED r3); "
          f"149 at E = 6.7 (2 x RTX 4090, UNVERIFIED)")
    print(f"  J2 summarisation: {SAMPLES_PER_KWH_B200:,.0f} MLPerf samples per server-h (B200 slice, COMPUTED from SOURCED); "
          f"{SAMPLES_PER_KWH_CPU:,.0f} (2 x Xeon, 1 kW ASSUMPTION); {SAMPLES_PER_DOC:g} samples per document ASSUMPTION")
    house6 = simulate(rows, 6)["run_h"]
    for lab, vol, unit, st, src in CUSTOMERS:
        if "audio" in unit:
            sh_lo, sh_hi = vol / ah_per_sh, vol / 149.0
        else:
            sh_lo, sh_hi = vol * SAMPLES_PER_DOC / SAMPLES_PER_KWH_B200, vol * SAMPLES_PER_DOC / SAMPLES_PER_KWH_CPU
        print(f"  {lab}: {vol:,.0f} {unit} [{st}]")
        print(f"      = {sh_lo:,.0f} to {sh_hi:,.0f} server-h = {sh_lo/house6*100:.2f}% to {sh_hi/house6*100:.1f}% of ONE N=6 house-year "
              f"({house6:,.0f} permit server-h)   src {src}")
    # derivation for one house
    vol, years, houses = 1.25e6, 1.0, 1
    j1_per_day = vol / (ah_per_sh * 0.5) / (365 * years) / houses
    print(f"  Derivation (ASSUMPTION: archive A transcribed in {years:g} year by {houses} house): {vol:,.0f} audio-h / 333 audio-h per J1 "
          f"/ 365 = {j1_per_day:.1f} J1 jobs per day = {j1_per_day*0.5:.1f} server-h/day per house")
    for n in (6, 8):
        rt = R.offer_rates("shaped100", n)
        yr = sum(rt[m] * MDAYS[m] for m in range(12)) / 365
        print(f"     against the shaped100 contract at N={n}: {yr:.1f} server-h/day yearly mean -> the archive fills "
              f"{j1_per_day*0.5/yr*100:.1f}% of it; houses one such archive keeps busy for a year: {j1_per_day*0.5/yr:.3f}")

    # ---- 2. offer specification
    print("\n== 2. Headline offer generator: shaped100, jobs offered per day by month (expected values) ==")
    print("  rate_m = 1.00 x mean heat-permit server-h/day of month m under plain follow, 2020-24 Open-Meteo archive (cannot see 2025)")
    print("  lambda_J1 per hour = rate_m x 0.5 / 0.5 / 24;  lambda_J2 per hour = rate_m x 0.5 / 4 / 24;  Poisson, random.Random(seed)")
    for n in (6, 8):
        rt = R.offer_rates("shaped100", n)
        print(f"  N={n}  month     " + " ".join(f"{m+1:>6}" for m in range(12)) + "   year")
        yr = lambda v: sum(v[m] * MDAYS[m] for m in range(12)) / 365
        print("        server-h/d " + " ".join(f"{x:>6.1f}" for x in rt) + f" {yr(rt):>6.1f}")
        j1 = [x * 0.5 / 0.5 for x in rt]
        j2 = [x * 0.5 / 4.0 for x in rt]
        print("        J1 jobs/d  " + " ".join(f"{x:>6.1f}" for x in j1) + f" {yr(j1):>6.1f}")
        print("        J2 jobs/d  " + " ".join(f"{x:>6.2f}" for x in j2) + f" {yr(j2):>6.2f}")
        print(f"        J1 audio-h/d at 333 per job: Jan {j1[0]*333:,.0f}, Jul {j1[6]*333:,.0f}, year mean {yr(j1)*333:,.0f}")

    # ---- runs
    jan25 = day_index("2025-01-25")
    cfgs = []
    for n in (6, 8):
        for s in seeds:
            cfgs += [(("headline", "shaped100"), n, "headline", "shaped100", s, None, None),
                     (("perfect", "shaped100"), n, "perfect", "shaped100", s, None, None),
                     (("headline", "shaped50"), n, "headline", "shaped50", s, None, None),
                     (("headline", "shaped200"), n, "headline", "shaped200", s, None, None),
                     (("headline", "saturating"), n, "headline", "saturating", s, None, None),
                     (("headline", "named"), n, "headline", "flat_custom", s, j1_per_day * 0.5, None),
                     (("pin_year", "shaped100"), n, "headline", "shaped100", s, None, dict(slot=1, mode="year"))]
    print(f"\n({len(cfgs)} simulated years, seeds {seeds})", flush=True)
    if procs == 1:
        out = [task(c) for c in cfgs]
    else:
        import multiprocessing as mp
        with mp.Pool(procs) as pool:
            out = pool.map(task, cfgs, chunksize=1)
    res = dict(out)

    # pinned on the demo day only: pick the day from the no-pin run (seed 1), rerun with the pin
    demo = {}
    for n, month, slot in ((6, "07", 1), (8, "01", 7)):
        r1 = res[(("headline", "shaped100"), n, 1)]
        cands = pause_resume_days(r1["ks_cap"], slot, month)
        demo[n] = dict(slot=slot, month=month, cands=cands)
    day_cfgs = []
    for n in (6, 8):
        c = demo[n]["cands"]
        if not c:
            continue
        pick = min(c, key=lambda x: abs(int(x[0][8:]) - 15)) if demo[n]["month"] == "07" else \
            next((x for x in c if x[0] == "2025-01-25"), c[0])
        demo[n]["pick"] = pick
        for s in seeds:
            day_cfgs.append((("pin_day", "shaped100"), n, "headline", "shaped100", s, None,
                             dict(slot=demo[n]["slot"], mode="day", day=day_index(pick[0]))))
    if procs == 1:
        out = [task(c) for c in day_cfgs]
    else:
        import multiprocessing as mp
        with mp.Pool(procs) as pool:
            out = pool.map(task, day_cfgs, chunksize=1)
    res.update(dict(out))

    # ---- 3. headline key figures
    print("\n== 3. HEADLINE key figures: shaped100 offers, headline policy, archived forecast + 2 K guard (seed mean [min-max]) ==")
    for n in (6, 8):
        k = ("headline", "shaped100")
        g = lambda f: mean_of(res, k, n, seeds, f)
        mo = [money(res[(k, n, s)]) for s in seeds]
        avg = lambda f, kk: sum(x[f][kk] for x in mo) / len(mo)
        cnt = [(res[(k, n, s)]["missed_n"], res[(k, n, s)]["closed_n"]) for s in seeds]
        print(f"  N={n}")
        print(f"    coverage {g('coverage')[0]*100:.2f}% [{g('coverage')[1]*100:.2f}-{g('coverage')[2]*100:.2f}]   dumped {g('dumped')[0]:.0f} kWh   "
              f"utilisation {g('util')[0]*100:.2f}%   starts/yr {g('starts')[0]:.0f}")
        print(f"    offered jobs {g('offered')[0]:,.0f}/yr ({g('offered')[0]/365:.1f}/day); accepted {g('acc_jobs')[0]*100:.1f}% of jobs, "
              f"{g('acc_work')[0]*100:.1f}% of work; summer (Jun-Aug) J1 accepted {g('acc_j1_summer')[0]*100:.1f}% of offers")
        print(f"    missed deadlines: " + ", ".join(f"{a} of {b}" for a, b in cnt) + f" accepted jobs closed in 2025 (seeds {seeds}) = "
              f"{g('missed')[0]*100:.4f}% [{g('missed')[1]*100:.4f}-{g('missed')[2]*100:.4f}]; not accepted (sent elsewhere): "
              f"{(1-g('acc_jobs')[0])*100:.1f}% of offered jobs")
        print(f"    server-hours sold {g('sold_h')[0]:,.0f} (J1 {sum(res[(k,n,s)]['sold_t'][0] for s in seeds)/len(seeds):,.0f}, "
              f"J2 {sum(res[(k,n,s)]['sold_t'][1] for s in seeds)/len(seeds):,.0f}) = {g('sold_h')[0]/simulate(rows, n)['run_h']*100:.1f}% of the unlimited-demand permit hours")
        print(f"    electricity {g('elec')[0]:,.0f} CHF; heat value used {g('heat_val')[0]:,.0f} CHF; electricity - heat {sum(x['net'] for x in mo)/len(mo):,.0f} CHF")
        print(f"    break-even per sold server-hour: {g('breakeven')[0]:.4f} CHF (case formula; 0.3325 if the homeowner keeps the heat); "
              f"with the 15-min restart accounting line {g('be_restart')[0]:.4f}")
        print(f"    list value of the sold work (J1 laptop efficiency, J2 B200 slice: NOT one machine), CHF/yr: "
              f"low {avg('list_value','low'):,.0f} / central {avg('list_value','central'):,.0f} / high {avg('list_value','high'):,.0f}")
        print(f"    share of list value needed to cover electricity - heat: low {avg('share_needed','low')*100:.1f}% / central "
              f"{avg('share_needed','central')*100:.1f}% / high {avg('share_needed','high')*100:.1f}%")
        print(f"    SCENARIO computing income at operator share {I.WHOLESALE:.0%} (ASSUMPTION), sold share = computed above: "
              f"low {avg('income','low'):,.0f} / central {avg('income','central'):,.0f} / high {avg('income','high'):,.0f} CHF/yr; "
              f"if every sold hour were J1 (one machine, laptop efficiency): {avg('income_j1only','low'):,.0f} / "
              f"{avg('income_j1only','central'):,.0f} / {avg('income_j1only','high'):,.0f}")

    # ---- 4. comparison and sensitivity table
    print("\n== 4. Sensitivity and comparison rows (seed means) ==")
    hdr = (f"  {'row':<44}{'N':>2} {'cover':>7} {'dump':>5} {'util':>6} {'acc%job':>7} {'sumJ1%':>6} {'missed x of y (seed 1)':>22} "
           f"{'missed%':>8} {'sold h':>7} {'BE':>7} {'BE+rst':>7} {'income c':>9} {'need c':>7} {'starts':>6}")
    print(hdr)
    labels = [(("headline", "shaped100"), "HEADLINE shaped100, archived + 2 K"),
              (("perfect", "shaped100"), "check: shaped100, perfect forecast"),
              (("headline", "shaped50"), "sensitivity: half rate (shaped50)"),
              (("headline", "shaped200"), "sensitivity: double rate (shaped200)"),
              (("headline", "saturating"), "reference: saturating (N x 24 h/day)"),
              (("headline", "named"), f"named customer only ({j1_per_day*0.5:.1f} srv-h/d flat)"),
              (("pin_year", "shaped100"), "shaped100 + real job pinned slot 1, all year"),
              (("pin_day", "shaped100"), "shaped100 + real job pinned, demo day only")]
    for n in (6, 8):
        for k, lab in labels:
            if (k, n, seeds[0]) not in res:
                continue
            g = lambda f: mean_of(res, k, n, seeds, f)[0]
            r1 = res[(k, n, 1)]
            mo = [money(res[(k, n, s)]) for s in seeds]
            print(f"  {lab:<44}{n:>2} {g('coverage')*100:>6.2f}% {g('dumped'):>5.0f} {g('util')*100:>5.1f}% {g('acc_jobs')*100:>6.1f}% "
                  f"{g('acc_j1_summer')*100:>5.1f}% {str(r1['missed_n'])+' of '+format(r1['closed_n'], ','):>22} {g('missed')*100:>8.4f} "
                  f"{g('sold_h'):>7,.0f} {g('breakeven'):>7.4f} {g('be_restart'):>7.4f} "
                  f"{sum(x['income']['central'] for x in mo)/len(mo):>9,.0f} {sum(x['share_needed']['central'] for x in mo)/len(mo)*100:>6.1f}% "
                  f"{g('starts'):>6.0f}")
        print()
    print("  income c = scenario income, central prices, operator share 20% (ASSUMPTION); need c = share of list value needed (central)")

    # ---- 5. pinned real job
    print("\n== 5. The pinned real job (R6) in the yearly balance ==")
    for n in (6, 8):
        ky, kd, k0 = ("pin_year", "shaped100"), ("pin_day", "shaped100"), ("headline", "shaped100")
        g = lambda kk, f: mean_of(res, kk, n, seeds, f)[0]
        print(f"  N={n}: all-year pin on slot 1: pinned hours {g(ky,'pin_h'):,.0f}/yr = {g(ky,'pin_h')/g(ky,'sold_h')*100:.1f}% of sold hours; "
              f"coverage {g(k0,'coverage')*100:.2f}% -> {g(ky,'coverage')*100:.2f}%; accepted jobs {g(k0,'acc_jobs')*100:.1f}% -> "
              f"{g(ky,'acc_jobs')*100:.1f}%; summer J1 accepted {g(k0,'acc_j1_summer')*100:.1f}% -> {g(ky,'acc_j1_summer')*100:.1f}%; "
              f"missed {g(k0,'missed')*100:.4f}% -> {g(ky,'missed')*100:.4f}%")
        if (kd, n, seeds[0]) in res:
            pk = demo[n]["pick"]
            r1 = res[(kd, n, 1)]
            di = day_index(pk[0])
            pat = "".join("#" if x else "." for x in r1["pin_run"][di * 24:(di + 1) * 24])
            ev = [(i + 1, "PAUSE" if a == "#" else "RESUME") for i, (a, bb) in enumerate(zip(pat, pat[1:])) if a != bb]
            print(f"  N={n}: demo-day pin on {pk[0]} slot {demo[n]['slot']} (chosen from the no-pin seed-1 run, pattern there {pk[1]}, "
                  f"pause {pk[2]:02d}:00 resume {pk[3]:02d}:00)")
            print(f"        with the pin, seed 1: pinned job ran {r1['pin_h']:.0f} h that day; its pattern {pat}; events "
                  + ", ".join(f"{e} {hh:02d}:00" for hh, e in ev))
            print(f"        yearly figures with vs without the demo-day pin (seed means): coverage {g(k0,'coverage')*100:.3f}% -> {g(kd,'coverage')*100:.3f}%, "
                  f"sold h {g(k0,'sold_h'):,.0f} -> {g(kd,'sold_h'):,.0f}, accepted {g(k0,'acc_jobs')*100:.2f}% -> {g(kd,'acc_jobs')*100:.2f}%, "
                  f"missed {g(k0,'missed')*100:.4f}% -> {g(kd,'missed')*100:.4f}%")
        print(f"  N={n}: demo candidates in the no-pin run (seed 1), slot {demo[n]['slot']}, month {demo[n]['month']}: "
              + ", ".join(f"{c[0][5:]} P{c[2]:02d} R{c[3]:02d}" for c in demo[n]["cands"]))


if __name__ == "__main__":
    main()
