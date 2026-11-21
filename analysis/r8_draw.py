"""Round 8, weak point "heat-gated hours versus seller reality".

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.

    python3 analysis/r8_draw.py              # seed 1, all cores (about 10-40 s)
    python3 analysis/r8_draw.py --seeds 3    # seeds 1-3 (means)
    python3 analysis/r8_draw.py --procs 1    # no multiprocessing

Question (a): a rented GPU draws what the renter's workload makes it draw, not its rating.
What does a draw of d = 90 / 70 / 50 % of rated wall power do to heat delivered, coverage,
server-hours needed per kWh of heat permit, and the break-even price per sold server-hour?

  One server-hour at draw d uses d kWh of electricity and delivers 0.8 * d kWh of heat
  (case: 1 kW server, 80 % recovered). Job runtimes stay in server-hours (the renter's hours).

  Two scheduler variants, both on the round-4 headline loop r4_headline.run (cap + 8 kWh band,
  EDF admission dry run, archived ECMWF ifs025 + 2 K guard), N = 6 and N = 8:
    naive   permits in SERVER-HOURS: the permit count is computed as if every server-hour gave
            0.8 kWh (r3_policy_check.Q1 = 0.8), while the tank physics and electricity use the
            real draw d (r4_headline.Q1 = 0.8 d, r4_headline.P_EL = d). The dry run therefore
            plans with the same (wrong-sized) permits that execution uses, so it stays consistent.
    kwh     permits in kWh of HEAT, converted to server-hours at the real draw:
            r3_policy_check.Q1 = r4_headline.Q1 = 0.8 d, P_EL = d.
    under:x stress: permits sized for an assumed draw x (e.g. 0.5) while the renter runs at full draw
            d = 1.0 (r3_policy_check.Q1 = 0.8 x, r4_headline.Q1 = 0.8). Execution trusts the permit count.
  Offer contracts:
    h       the headline shaped100 offers in server-hours, computed once at full draw
            (r2_deadline_sim.offer_rates, untouched), i.e. the contract is NOT resized
    kwh     the same contract resized in heat: offered server-hours x 1/d
  Unlimited demand ('saturating' offers, every permit hour offered) is the F1 spot form of round 7.

Question (b): the interruptible discount. Sourced on-demand vs interruptible GPU prices (see
docs/research/r8-seller-reality.md for the URLs), converted to CHF per reference server-hour of
work, compared with the price per sold server-hour needed incl. hardware (r7_payback formula).

Nothing is edited. Module attributes are set at run time inside this process only:
r3_policy_check.Q1, r4_headline.Q1, r4_headline.P_EL, r4_headline.rates_for.
Imports (read-only): baseline_sweep, r2_deadline_sim, r3_policy_check, r4_headline, r7_payback.
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True   # do not touch analysis/__pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_sweep as BS      # noqa: E402
import r2_deadline_sim as R      # noqa: E402
import r3_policy_check as P3     # noqa: E402
import r4_headline as H          # noqa: E402
import r7_payback as PB          # noqa: E402

Q1_FULL = BS.REC * BS.P_EL       # 0.8 kWh of recovered heat per full-draw server-hour (case)
DRAWS = (1.0, 0.9, 0.7, 0.5)     # wall draw as share of rated power: 1.0 = plan basis; 0.9/0.7/0.5 = task grid
NS = (6, 8)
LIFE = 5.0                       # years (plan ASSUMPTION)
OCC = (0.6, 1.0)                 # occupancy of heat-permitted hours (r7 central ASSUMPTION, and 100 %)
HOST_SHARE = PB.HOST_SHARE       # 0.80 of the renter price reaches a marketplace host (sourced r2, not re-opened)
USD_CHF = PB.USD_CHF             # 0.8392 CHF per USD, ECB 20 Nov 2026 (sourced r1/r6, not re-opened in r8)

# ------------------------------------------------------------------ (b) interruptible vs on-demand, read 21 Nov 2026
# (provider, product, region, on-demand, interruptible, unit, status)
SPOT = [
    ("Azure", "NC144lds_xl RTX PRO 6000 BSE v6 (1 GPU)", "Switzerland North", 7.865, 1.453452,
     "USD per VM-h", "SOURCED: Azure Retail Prices API (prices.azure.com), Linux consumption meters"),
    ("Azure", "NC144ds_xl RTX PRO 6000 BSE v6 (1 GPU)", "Switzerland North", 9.123, 1.68593,
     "USD per VM-h", "SOURCED: same API"),
    ("Azure", "NC288lds_xl RTX PRO 6000 BSE v6 (2 GPU)", "Switzerland North", 15.73, 2.906904,
     "USD per VM-h", "SOURCED: same API"),
    ("Google", "g4-standard-48 RTX PRO 6000 (1 GPU)", "us-central1", 4.4999, 1.7178,
     "USD per VM-h", "SOURCED via third-party aggregator gcloud-compute.com (updated 18 Nov 2026)"),
    ("Google", "g4-standard-48 RTX PRO 6000 (1 GPU)", "europe-west4", 4.9499, 2.0496,
     "USD per VM-h", "SOURCED via the same aggregator"),
    ("Google", "g2-standard-4 L4 (1 GPU)", "europe-west6 Zurich", 0.9757, 0.584,
     "USD per VM-h", "SOURCED via the same aggregator"),
    ("SaladCloud", "RTX 4090, Lowest (batch) vs High tier", "community (homes)", 0.440, 0.160,
     "USD per GPU-h", "SOURCED: salad.com/pricing (tiers, not on-demand vs spot; all tiers can disconnect)"),
]
# RTX PRO 6000 GPU-hours per reference server-hour of work (50/50 J1/J2), r7_payback ratios (team-sourced MLPerf)
GPU6K_PER_SH = 0.5 * PB.GPU_PER_SH / PB.SPEED_6K_J1 + 0.5 * PB.GPU_PER_SH / PB.SPEED_6K_J2


def task(cfg):
    """cfg = (n, d, mode, contract, demand, seed). Patches module attributes in THIS process only."""
    n, d, mode, contract, demand, seed = cfg
    base = R.offer_rates(demand, n)                       # R.Q1 untouched -> contract at full draw
    rates = list(base) if (demand == "saturating" or contract == "h") else [x / d for x in base]
    H.rates_for = lambda dem, nn, flat=None, _r=rates: list(_r)
    if mode.startswith("under:"):
        d_plan = float(mode.split(":")[1])               # permits sized for a draw lower than the real one
    else:
        d_plan = 1.0 if mode == "naive" else d
    P3.Q1 = Q1_FULL * d_plan                             # what the permit count assumes
    H.Q1 = Q1_FULL * d                                    # real heat per server-hour (dry run and execution)
    H.P_EL = d                                            # real electricity per server-hour
    r = H.run(n, H.HEADLINE, demand, seed)
    for f in ("ks_cap", "ks_on", "pin_run"):
        r.pop(f, None)
    r["dem_tot"] = (r["heat_val"] / BS.HEAT_VALUE) / r["coverage"] if r["coverage"] else 0.0
    return cfg, r


def econ(r, n, o=1.0, heat_to_host=False):
    """r7_payback F1 formula, per house: p* = (I/L + K + e*o*S) / (o*S), S = sold_h of the run."""
    f = PB.fixed_costs(n)
    S = r["sold_h"]
    net = r["elec"] - (0.0 if heat_to_host else r["heat_val"])
    e = net / S
    return (f["inst"] / LIFE + f["K"] + e * o * S) / (o * S), e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--procs", type=int, default=0)
    a = ap.parse_args()
    seeds = list(range(1, a.seeds + 1))
    cfgs = []
    for n in NS:
        for d in DRAWS:
            for sd in seeds:
                cfgs.append((n, d, "naive", "h", "saturating", sd))
                cfgs.append((n, d, "kwh", "h", "saturating", sd))
                cfgs.append((n, d, "naive", "h", "shaped100", sd))
                cfgs.append((n, d, "kwh", "h", "shaped100", sd))
                cfgs.append((n, d, "kwh", "kwh", "shaped100", sd))
        for x in (0.7, 0.5):
            for sd in seeds:
                cfgs.append((n, 1.0, f"under:{x}", "h", "shaped100", sd))
    if a.procs == 1:
        res = dict(task(c) for c in cfgs)
    else:
        import multiprocessing as mp
        with mp.Pool(a.procs or None) as p:
            res = dict(p.map(task, cfgs))

    def m(n, d, mode, contract, demand, key):
        return sum(res[(n, d, mode, contract, demand, s)][key] for s in seeds) / len(seeds)

    def mr(n, d, mode, contract, demand):
        """mean result dict over seeds (numeric fields only)."""
        rs = [res[(n, d, mode, contract, demand, s)] for s in seeds]
        out = {}
        for k, v in rs[0].items():
            if isinstance(v, (int, float)):
                out[k] = sum(x[k] for x in rs) / len(rs)
        out["missed_s1"] = (rs[0]["missed_n"], rs[0]["closed_n"])
        return out

    print("r8_draw.py. Currency CHF; 1 USD = %.4f CHF (ECB 20 Nov 2026, not re-opened). Seeds %s%s." %
          (USD_CHF, seeds, " (means)" if len(seeds) > 1 else ""))
    print("Loop: r4_headline.run, policy HEADLINE (cap + 8 kWh band, EDF dry run, archived ifs025 + 2 K guard).")
    print("Installed cost and fixed costs: r7_payback.fixed_costs (central). p* = price per sold server-hour needed,")
    print("5 y, no interest, heat credited unless marked. Draw d = wall power as share of rated (1 kW per server).\n")

    # ------------------------------------------------------------ 0. regression
    print("== 0. Regression at d = 1.00 (must equal the plan's seed-1 HEADLINE values) ==")
    for n in NS:
        r = mr(n, 1.0, "kwh", "h", "shaped100")
        rn = mr(n, 1.0, "naive", "h", "shaped100")
        print(f"  N={n} shaped100 coverage {r['coverage']*100:.2f}% (naive variant {rn['coverage']*100:.2f}%), "
              f"util {r['util']*100:.2f}%, missed {r['missed_s1'][0]} of {r['missed_s1'][1]:,}, BE {r['breakeven']:.4f}")
    print("  plan, seed 1, archived ECMWF + 2 K: 73.20% / 85.73%, util 54.37% / 47.76%, 0 of 31,908 / 0 of 36,771\n")

    # ------------------------------------------------------------ 1. unlimited demand (F1 spot form)
    print("== 1. Unlimited demand (every permit hour offered = round-7 F1 spot form); naive vs kWh permits ==")
    print(f"{'N':>2} {'d':>5} {'permits':<7} {'cover':>7} {'heat MWh':>8} {'srv-h':>7} {'util':>6} {'sh/kWh':>6} "
          f"{'op BE/sh':>8} {'p* o=.6':>8} {'p* o=1':>7} {'p* .6 host':>10} {'p*/kWh .6':>9} {'cov o=.6':>8}")
    P1 = {}
    for n in NS:
        for d in DRAWS:
            for mode in ("naive", "kwh"):
                r = mr(n, d, mode, "h", "saturating")
                used = r["heat_val"] / BS.HEAT_VALUE
                p6, e = econ(r, n, 0.6)
                p10, _ = econ(r, n, 1.0)
                p6h, _ = econ(r, n, 0.6, heat_to_host=True)
                P1[(n, d, mode)] = dict(p6=p6, p10=p10, p6h=p6h, cov=r["coverage"], S=r["sold_h"], e=e)
                print(f"{n:>2} {d:>5.2f} {mode:<7} {r['coverage']*100:>6.2f}% {used/1000:>8.2f} {r['sold_h']:>7,.0f} "
                      f"{r['util']*100:>5.1f}% {r['run_h']/used:>6.2f} {e:>8.4f} {p6:>8.2f} {p10:>7.2f} {p6h:>10.2f} "
                      f"{p6/d:>9.2f} {r['coverage']*0.6*100:>7.1f}%")
    print("  sh/kWh = server-hours run per kWh of heat used (= 1 / (0.8 d) when nothing is dumped).")
    print("  op BE/sh = (electricity - heat value) / sold server-h. p*/kWh .6 = p* (o = 0.6) / d = price per kWh at the wall.")
    print("  cov o=.6 = coverage x 0.6: linear estimate if a buyer takes 60 % of permit hours and unsold hours stay off.\n")

    # ------------------------------------------------------------ 2. headline offers
    print("== 2. Headline offers (shaped100); contract h = server-hours as sized at full draw, kwh = resized x 1/d ==")
    print(f"{'N':>2} {'d':>5} {'permits':<7} {'contr':<5} {'cover':>7} {'heat MWh':>8} {'sold sh':>8} {'acc%':>6} "
          f"{'missed s1':>16} {'util':>6} {'sh/kWh':>6} {'op BE/sh':>8} {'p* contr':>8} {'dump':>5}")
    P2 = {}
    for n in NS:
        for d in DRAWS:
            for mode, contract in (("naive", "h"), ("kwh", "h"), ("kwh", "kwh")):
                r = mr(n, d, mode, contract, "shaped100")
                used = r["heat_val"] / BS.HEAT_VALUE
                p, e = econ(r, n, 1.0)
                P2[(n, d, mode, contract)] = dict(p=p, cov=r["coverage"], S=r["sold_h"])
                ms = r["missed_s1"]
                print(f"{n:>2} {d:>5.2f} {mode:<7} {contract:<5} {r['coverage']*100:>6.2f}% {used/1000:>8.2f} "
                      f"{r['sold_h']:>8,.0f} {r['acc_jobs']*100:>5.1f}% {ms[0]:>5} of {ms[1]:>7,} {r['util']*100:>5.1f}% "
                      f"{r['run_h']/used:>6.2f} {e:>8.4f} {p:>8.2f} {r['dumped']:>5.0f}")
    print("  p* contr = price per sold server-hour needed if every accepted contract hour is paid (no occupancy factor).")
    print("  acc% = accepted share of offered jobs; missed = seed 1, 'x of y accepted jobs whose deadline fell in the year'.\n")

    # ------------------------------------------------------------ 3. what the scheduler should do: summary per d
    print("== 3. Summary: change against d = 1.00 (kWh permits, headline contract in server-hours) ==")
    for n in NS:
        b = P2[(n, 1.0, "kwh", "h")]
        for d in DRAWS[1:]:
            k = P2[(n, d, "kwh", "h")]
            kk = P2[(n, d, "kwh", "kwh")]
            nv = P2[(n, d, "naive", "h")]
            print(f"  N={n} d={d:.2f}: coverage {b['cov']*100:.1f}% -> {k['cov']*100:.1f}% (contract in server-h), "
                  f"{kk['cov']*100:.1f}% (contract resized in kWh, sold {kk['S']:,.0f} vs {b['S']:,.0f} sh), "
                  f"naive permits {nv['cov']*100:.1f}%; p* contract {b['p']:.2f} -> {k['p']:.2f} / {kk['p']:.2f} / {nv['p']:.2f}")
    print()

    print("== 3b. Stress: permits sized for a LOW assumed draw while the renter runs at full draw (shaped100) ==")
    for n in NS:
        b = mr(n, 1.0, "kwh", "h", "shaped100")
        for x in (0.7, 0.5):
            r = mr(n, 1.0, f"under:{x}", "h", "shaped100")
            ms = r["missed_s1"]
            print(f"  N={n} assumed d={x:.1f}, real 1.0: coverage {r['coverage']*100:.2f}% (vs {b['coverage']*100:.2f}%), "
                  f"dumped {r['dumped']:,.0f} kWh, accepted {r['acc_jobs']*100:.1f}%, missed {ms[0]} of {ms[1]:,}, "
                  f"BE {r['breakeven']:.4f}")
    print("  Execution trusts the permit count, so heat beyond demand + tank is dumped: a permit counted in server-hours")
    print("  with a guessed draw breaks 'nothing is dumped'. Permits must be kWh, checked against metered power.\n")

    # ------------------------------------------------------------ 4. interruptible discount
    print("== 4. Interruptible vs on-demand GPU prices (read 21 Nov 2026) and the price needed ==")
    print(f"  RTX PRO 6000 GPU-h per reference server-hour of work (50/50 J1/J2, r7 MLPerf ratios): {GPU6K_PER_SH:.3f}")
    print(f"{'provider':<11}{'product':<42}{'region':<20}{'on-dem':>8} {'interr':>8} {'ratio':>6}  unit")
    ratios = []
    for prov, prod, reg, od, sp, unit, st in SPOT:
        ratios.append((prov, prod, reg, sp / od))
        print(f"{prov:<11}{prod:<42}{reg:<20}{od:>8.4f} {sp:>8.4f} {sp/od:>6.3f}  {unit}  [{st}]")
    print()
    # direct interruptible price of the same work (RTX PRO 6000 per GPU, 1-GPU VMs)
    direct = []
    for prov, prod, reg, od, sp, unit, st in SPOT:
        if "RTX PRO 6000" in prod and "(1 GPU)" in prod:
            chf = sp * GPU6K_PER_SH * USD_CHF
            direct.append((f"{prov} {reg} spot, {prod.split(' (')[0]}", chf))
    # ratio applied to the on-demand prices of the same work already in the plan
    od_same = {"RunPod RTX PRO 4500 on-demand": PB.FALLBACK["runpod_same"][0],
               "Exoscale CH RTX Pro 6000 on-demand": PB.FALLBACK["exo_ch_4gpu"][0]}
    rset = {"Azure CH 0.185": ratios[0][3], "Google RTX PRO 6000 0.382-0.414": None,
            "Salad Lowest/High 0.364": ratios[-1][3]}
    g_lo, g_hi = ratios[3][3], ratios[4][3]
    print("  A. Interruptible price of the SAME WORK, CHF per reference server-hour of work:")
    cands = []
    for lab, chf in direct:
        print(f"     {lab:<62} {chf:6.2f}  (direct spot list x {GPU6K_PER_SH:.3f} GPU-h x {USD_CHF})")
        cands.append((lab, chf))
    for olab, odv in od_same.items():
        for rlab, rv in rset.items():
            if rv is None:
                lo, hi = odv * g_lo, odv * g_hi
                print(f"     {olab} {odv:.2f} x {rlab:<32} {lo:6.2f}-{hi:.2f}")
                cands.append((f"{olab} x Google ratio", hi))
            else:
                print(f"     {olab} {odv:.2f} x {rlab:<32} {odv*rv:6.2f}")
                cands.append((f"{olab} x {rlab}", odv * rv))
    print()
    print("  B. Price needed per sold server-hour (unlimited demand, kWh permits) vs those prices.")
    print("     direct = DigitalHeat keeps 100 %; mkt = sold through a marketplace, host keeps 80 %.")
    short = []
    for lab, c in cands:
        short.append((lab, c))
    print("     candidates (CHF per reference server-hour of work): " +
          "; ".join(f"[{i}] {c:.2f}" for i, (lab, c) in enumerate(short)))
    for i, (lab, c) in enumerate(short):
        print(f"       [{i}] {lab}")
    print(f"{'':5}{'N':>2} {'d':>5} {'o':>4} {'p*':>6}  {'clears direct':<24} {'clears via mkt':<24}")
    for n in NS:
        for d in DRAWS:
            q = P1[(n, d, "kwh")]
            for o, ps in ((0.6, q["p6"]), (1.0, q["p10"])):
                cd = [str(i) for i, (lab, c) in enumerate(short) if c >= ps]
                cm = [str(i) for i, (lab, c) in enumerate(short) if c * HOST_SHARE >= ps]
                print(f"{'':5}{n:>2} {d:>5.2f} {o:>4.1f} {ps:>6.2f}  {','.join(cd) or 'none':<24} {','.join(cm) or 'none':<24}")
    lo_p = min(min(v["p6"], v["p10"]) for k, v in P1.items() if k[2] == "kwh")
    ratio_max = max(c for lab, c in short if " x " in lab)
    print(f"     lowest p* in the grid {lo_p:.2f}; highest ratio-based interruptible price {ratio_max:.2f}.")
    print()
    print("  Reading: at o = 0.6 only hyperscaler spot LIST prices for the same work in their own bundled VMs [0]-[3]")
    print("  clear p*; at o = 1.0 also Swiss on-demand x the Google or Salad ratio [8], [9]. No ratio applied to the cheapest")
    print("  on-demand price of the same work [4]-[6] clears any p*. The same work rents UNINTERRUPTED for %.2f CHF" %
          PB.FALLBACK["runpod_same"][0])
    print("  (RunPod on-demand, same card).")

if __name__ == "__main__":
    main()
