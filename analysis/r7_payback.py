"""Round 7, weak point "economics with a real seller form".

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.

    python3 analysis/r7_payback.py              # seeds 1-3, all cores (about 5-15 s)
    python3 analysis/r7_payback.py --seeds 1    # seed 1 only
    python3 analysis/r7_payback.py --procs 1    # no multiprocessing

ONE payback formula per server, every cost in it (per house-year, then divided by N):

    margin = p_c * V + p_s * o * S  -  e * (A + o * S)  -  c_f * (V - A)  -  K
    payback (years) = I / margin              (simple payback, no interest, constant prices)
    break-even price p* (one price for every sold hour, payback = life L):
        p* = (I / L + K + e * (A + o * S) + c_f * (V - A)) / (V + o * S)

    V   committed flat volume sold to a buyer who expects delivery (server-h a year)
    A   part of V the house actually runs (admission accepts it; simulated)
    V-A committed work the house refuses at intake -> run in a cloud at the operator's cost c_f
    S   heat-permitted hours left after the committed work = P - A (P = every permit hour, simulated
        'pool' run; approximation: committed and spot hours do not interact)
    o   occupancy: share of S that a spot / marketplace buyer actually takes (ASSUMPTION, sensitivity)
    e   operation cost per hour run in the house: (electricity - heat value used) / hours, i.e. 0.2261
        with the heat credited to the operator (case formula), or electricity / hours = 0.3325 with the
        heat given to the host free (what Heata, Leafcloud, Deep Green do)
    K   fixed per house-year: maintenance + leak reserve, card failures (self-insured, every year),
        insurance, internet uplink
    I   installed cost per house (r5 cold-plate chain, central), L = life (5 or 8 years)

Seller forms evaluated (all with the same formula):
    F1 spot only           V = 0: sell only heat-permitted hours into a marketplace that tolerates the
                           node leaving (SaladCloud form); no fallback, income only when rented.
    F2 committed flat      V = flat customer of the house's yearly volume (r6 'flat'); refused work
                           (about 30 % of it) runs in a cloud at c_f; winter surplus sold spot at o.
    F3 committed floor     V = 15 server-h a day (the July rate: the house can always run it, r6
                           'flat_july', 100 % accepted, no fallback) + winter surplus sold spot at o.

Imports (read-only, nothing edited): r6_buyer_scenarios (task, GPU_PER_SH, HOST_SHARE, USD_CHF, GBP_CHF,
YEARS, CHAIN), r4_headline (JT), r4_machine (CARD, wall_kw, N_GPU, NET_CHF_YR, list_value), r5_chain
(installed), r6_machine (yearly_cost, installed, SERVICE_CHF_H). Sources: docs/research/r7-seller-form-economics.md.
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r4_headline as H          # noqa: E402
import r4_machine as M           # noqa: E402
import r5_chain as C             # noqa: E402
import r6_buyer_scenarios as B   # noqa: E402
import r6_machine as RM          # noqa: E402

USD_CHF = B.USD_CHF              # 0.8392 CHF per USD, ECB 20 Nov 2026 (sourced, round 1/6)
GBP_CHF = B.GBP_CHF              # 1.1014 CHF per GBP, ECB 20 Nov 2026 (computed in r6)
GPU_PER_SH = B.GPU_PER_SH        # 4.19 RTX PRO 4500 GPU-hours per 1 kW server-hour (wall power ASSUMPTION)
HOST_SHARE = B.HOST_SHARE        # 0.80 host share of renter price (sourced in round 2, not re-opened)

# ------------------------------------------------------------------ income per sold server-hour (CHF)
RUNPOD_4500_USD = 0.72           # SOURCED: runpod.io/gpu-models/rtx-pro-4500-se, Secure Cloud on-demand, re-read r7
CHEAPEST_4500_USD = 0.48         # SOURCED in r6: getdeploying.com cheapest listing (Lium, sponsored)
SALAD_4090 = {"High": 0.440, "Medium": 0.347, "Low": 0.253, "Lowest": 0.160}   # SOURCED: salad.com/pricing, r7
SALAD_SPOT_RATIO = SALAD_4090["Lowest"] / SALAD_4090["High"]   # 0.364 (computed); applying it to a PRO 4500: ASSUMPTION
HEATA_T2_GBP = B.HEATA_T2_GBP    # 1.19 GBP per GPU-h, Heata list "from" surcharge (sourced r6)

PRICES = {   # key: (CHF per sold server-hour, label)
    "spot_salad": (RUNPOD_4500_USD * SALAD_SPOT_RATIO * HOST_SHARE * GPU_PER_SH * USD_CHF,
                   "RunPod 0.72 USD x SaladCloud Lowest/High 0.364 x 80% host share (spot host, ASSUMPTION mix)"),
    "host048": (CHEAPEST_4500_USD * HOST_SHARE * GPU_PER_SH * USD_CHF, "cheapest always-on listing 0.48 USD x 80%"),
    "host072": (RUNPOD_4500_USD * HOST_SHARE * GPU_PER_SH * USD_CHF, "RunPod Secure 0.72 USD x 80% (always-on host)"),
    "direct072": (RUNPOD_4500_USD * GPU_PER_SH * USD_CHF, "direct sale at RunPod's renter price, operator keeps 100%"),
    "heata_list": (HEATA_T2_GBP * GPU_PER_SH * GBP_CHF, "Heata Tier-2 'from' list surcharge, GPU only (list price)"),
}

# ------------------------------------------------------------------ cloud fallback cost per server-hour of work (CHF)
EXO_PRO6K_4GPU_CHF_H = 8.19444444   # SOURCED: Exoscale price API (portal.exoscale.com/api/pricing/opencompute),
                                    # 'gpurtx6000pro large' = 4 x RTX Pro 6000 (exoscale.com/pricing table), CHF/h
                                    # excl. tax; zones incl. CH-DK-2 (Switzerland); read 21 Nov 2026
EXO_PRO6K_1GPU_CHF_H = 2.15277778   # same, 'small' = 1 GPU
# RTX PRO 6000 SE vs RTX PRO 4500 SE on the same Intel host (MLPerf v6.1 6.1-0018 vs 6.1-0017, local xlsx, round-6
# critic): whisper 7,801.36 vs 3,878 tok/s, llama3.1-8b 14,860.7 vs 9,518.66 tok/s -> 2.01x and 1.56x per GPU (computed)
SPEED_6K_J1 = 7801.36 / 3878.0
SPEED_6K_J2 = 14860.7 / 9518.66


def fallback_exo(per_gpu_chf_h):
    """CHF per reference server-hour of work, 50/50 J1/J2 by server-hours (plan ASSUMPTION)."""
    return 0.5 * GPU_PER_SH / SPEED_6K_J1 * per_gpu_chf_h + 0.5 * GPU_PER_SH / SPEED_6K_J2 * per_gpu_chf_h


FALLBACK = {
    "runpod_same": (RUNPOD_4500_USD * GPU_PER_SH * USD_CHF, "RunPod RTX PRO 4500, same card, renter price (regions unnamed)"),
    "exo_ch_4gpu": (fallback_exo(EXO_PRO6K_4GPU_CHF_H / 4), "Exoscale RTX Pro 6000 x4, Swiss zone, excl. VAT"),
    "exo_ch_1gpu": (fallback_exo(EXO_PRO6K_1GPU_CHF_H), "Exoscale RTX Pro 6000 x1, Swiss zone, excl. VAT"),
}

# ------------------------------------------------------------------ occupancy of heat-permitted spot hours
OCC = {   # value: label
    0.337: "Akash GPUs Q1 2026, 84 of 334 (Messari via TokenPost)",
    0.50: "Heata's own hackathon floor '>50% on each node in any given month'",
    0.60: "Akash 2025 year in review, self-reported average",
    0.80: "Heata's planning assumption (team report, not re-opened)",
    1.00: "plan so far: every permit hour sold",
}
OCC_CENTRAL = 0.60

# ------------------------------------------------------------------ fixed costs per house-year (CHF)
MTBF_H = 864500.0                 # SOURCED (r6 critic): PNY RTX PRO 6000 SE brief, predicted MTBF, uncontrolled, 35 C
AFR = 8760.0 / MTBF_H             # 1.01 % of cards a year; applied to the RTX PRO 4500 and to every year: ASSUMPTION
INSURANCE = {"low": 0.005, "central": 0.010, "high": 0.020}   # share of installed cost a year: ASSUMPTION (no
                                  # published Swiss rate found; AXA / Allianz / Zurich pages give no rate)
UPLINK = M.NET_CHF_YR             # 1,200 CHF a year internet line: ASSUMPTION (r4)
LIFE = (5.0, 8.0)                 # ASSUMPTION (plan)

SCEN = [   # key, demand, work share, flat rate (r6_buyer_scenarios conventions)
    ("pool", "saturating", (0.5, 0.5), None),
    ("flat", "flat", (0.5, 0.5), None),
    ("flat_july", "flat_custom", (0.5, 0.5), 15.0),
]


def fixed_costs(n, case="central"):
    inst = C.installed(n, B.CHAIN)[0]
    boxes = n / M.wall_kw("central")
    maint_cdu = RM.yearly_cost("R5", n, retrofit=False)[0]          # one CDU loop, 4 h a year (r6 ASSUMPTION)
    maint_box = maint_cdu + (3.0 * boxes - RM.SERVICE_H) * RM.SERVICE_CHF_H   # 3 h per box a year (r6 critic)
    cards = AFR * boxes * M.N_GPU * M.CARD["central"]
    maint = {"low": maint_cdu, "central": maint_cdu, "high": maint_box}[case]
    ins = INSURANCE[case] * inst
    return dict(inst=inst, maint=maint, cards=cards, ins=ins, uplink=UPLINK,
                K=maint + cards + ins + UPLINK, maint_box=maint_box)


def margin(p_c, p_s, V, A, S, o, e, c_f, K):
    return p_c * V + p_s * o * S - e * (A + o * S) - c_f * (V - A) - K


def payback(I, m, decline=0.0, revenue=0.0):
    """Simple payback. With decline > 0 the income part (revenue) falls by that share every year."""
    if decline <= 0.0:
        return I / m if m > 0 else float("inf")
    cum, y = 0.0, 0
    cost = revenue - m
    while y < 60:
        inc = revenue * (1.0 - decline) ** y
        if inc - cost <= 0:
            return float("inf")
        if cum + inc - cost >= I:
            return y + (I - cum) / (inc - cost)
        cum += inc - cost
        y += 1
    return float("inf")


def p_star(I, L, K, e, V, A, S, o, c_f):
    sold = V + o * S
    return (I / L + K + e * (A + o * S) + c_f * (V - A)) / sold if sold > 0 else float("inf")


def fmt(y):
    return " never" if y == float("inf") or y > 99 else f"{y:6.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--procs", type=int, default=0)
    a = ap.parse_args()
    seeds = list(range(1, a.seeds + 1))
    cfgs = [(k, n, d, s, f, sd) for (k, d, s, f) in SCEN for n in (6, 8) for sd in seeds]
    if a.procs == 1:
        res = dict(B.task(c) for c in cfgs)
    else:
        import multiprocessing as mp
        with mp.Pool(a.procs or None) as p:
            res = dict(p.map(B.task, cfgs))

    def mean(key, n, fn):
        return sum(fn(res[(key, n, s)]) for s in seeds) / len(seeds)

    def offered_work(r):
        return sum(r["off"][i] * H.JT[i][1] for i in (0, 1))

    print("r7_payback.py. Currency CHF. 1 USD = %.4f CHF, 1 GBP = %.4f CHF (ECB 20 Nov 2026). Seeds %s (means)."
          % (USD_CHF, GBP_CHF, seeds))
    print("Policy r4_headline.HEADLINE (cap + 8 kWh band, EDF admission, archived ifs025 + 2 K guard). Simple payback,")
    print("no interest, constant prices unless marked. Installed cost: r5 cold-plate chain, central.\n")

    print("== 0. Inputs ==")
    for k, (v, lab) in PRICES.items():
        print(f"  income  {k:<11} {v:6.3f} CHF per sold server-h   {lab}")
    for k, (v, lab) in FALLBACK.items():
        print(f"  fallbk  {k:<11} {v:6.3f} CHF per server-h of work {lab}")
    print(f"  RTX PRO 6000 / 4500 per GPU, same host: J1 {SPEED_6K_J1:.2f}x, J2 {SPEED_6K_J2:.2f}x (MLPerf 6.1-0018 vs 6.1-0017)")
    for o, lab in OCC.items():
        print(f"  occupancy {o:5.3f}  {lab}")
    print(f"  card failures {AFR*100:.2f} % of cards a year (MTBF {MTBF_H:,.0f} h), every year; insurance "
          f"{INSURANCE['central']*100:.1f} % of installed a year (ASSUMPTION, low {INSURANCE['low']*100:.1f} / high "
          f"{INSURANCE['high']*100:.1f}); uplink {UPLINK:,.0f} CHF a year (ASSUMPTION)\n")

    print("== 1. Hours per house-year from the yearly loop (computed) ==")
    print(f"{'N':>2} {'P permit h':>10} {'flat V':>8} {'flat A':>8} {'V-A':>7} {'July V':>7} {'July A':>7} "
          f"{'e heat cred':>11} {'e heat host':>11}")
    H_ = {}
    for n in (6, 8):
        P = mean("pool", n, lambda r: r["sold_h"])
        Vf = mean("flat", n, offered_work)
        Af = mean("flat", n, lambda r: r["sold_h"])
        Vj = mean("flat_july", n, offered_work)
        Aj = mean("flat_july", n, lambda r: r["sold_h"])
        e_hc = mean("pool", n, lambda r: (r["elec"] - r["heat_val"]) / r["sold_h"])
        e_hh = mean("pool", n, lambda r: r["elec"] / r["sold_h"])
        H_[n] = dict(P=P, Vf=Vf, Af=Af, Vj=Vj, Aj=Aj, e={"heat credited": e_hc, "heat to host": e_hh})
        print(f"{n:>2} {P:>10,.0f} {Vf:>8,.0f} {Af:>8,.0f} {Vf-Af:>7,.0f} {Vj:>7,.0f} {Aj:>7,.0f} {e_hc:>11.4f} {e_hh:>11.4f}")
    print("  P = every heat-permitted hour run ('pool'); flat = r6 flat customer (same yearly volume); July = 15 server-h a day.")
    print("  V = offered work, A = work run in the house (accepted); V-A = refused at intake (-> cloud in form F2).\n")

    print("== 2. Fixed costs per house-year and per server (CHF) ==")
    FX = {}
    for n in (6, 8):
        f = fixed_costs(n)
        FX[n] = f
        print(f"  N={n}: installed {f['inst']:,.0f} ({f['inst']/n:,.0f} per server); maintenance + leak {f['maint']:,.0f} "
              f"(3 h per box: {f['maint_box']:,.0f}); card failures {f['cards']:,.0f}; insurance {f['ins']:,.0f}; "
              f"uplink {f['uplink']:,.0f}; K = {f['K']:,.0f} a year ({f['K']/n:,.0f} per server)")
    print()

    lv = M.list_value("central", "central")[2]   # US batch list value of one server-hour of work, 50/50 (CHF)

    def line(n, form, conv, o, p_c, p_s, c_f, L=5.0, case="central"):
        h, f = H_[n], fixed_costs(n, case)
        e = h["e"][conv]
        if form == "F1":
            V, A = 0.0, 0.0
        elif form == "F2":
            V, A = h["Vf"], h["Af"]
        else:
            V, A = h["Vj"], h["Aj"]
        S = max(0.0, h["P"] - A)
        m = margin(p_c, p_s, V, A, S, o, e, c_f, f["K"])
        ps = p_star(f["inst"], L, f["K"], e, V, A, S, o, c_f)
        rev = p_c * V + p_s * o * S
        return dict(m=m, pb=payback(f["inst"], m), ps=ps, sold=V + o * S, house_run=A + o * S, V=V, A=A, S=S,
                    rev=rev, I=f["inst"], K=f["K"], e=e)

    # ------------------------------------------------------------ 3. the one line
    print("== 3. THE LINE, per server (house figures / N). Central: F1 spot only, occupancy 0.60, heat credited ==")
    print("  margin = p_c*V + p_s*o*S - e*(A + o*S) - c_f*(V - A) - K ;  payback = I / margin ;")
    print("  p* = (I/L + K + e*(A + o*S) + c_f*(V - A)) / (V + o*S)")
    for n in (6, 8):
        for conv in ("heat credited", "heat to host"):
            for pk in ("spot_salad", "host048", "host072"):
                p = PRICES[pk][0]
                r = line(n, "F1", conv, OCC_CENTRAL, 0.0, p, 0.0)
                print(f"  N={n} {conv:<13} p={p:5.2f} ({pk:<10}) sold {r['sold']/n:6,.0f} h/server  income "
                      f"{r['rev']/n:6,.0f}  op {r['e']*r['house_run']/n:5,.0f}  K {r['K']/n:5,.0f}  margin {r['m']/n:6,.0f} "
                      f"CHF/server-yr  I {r['I']/n:,.0f}  payback {fmt(r['pb'])} y   p*(5 y) {r['ps']:.2f}  p*(8 y) "
                      f"{line(n, 'F1', conv, OCC_CENTRAL, 0, p, 0, L=8.0)['ps']:.2f}")
    print()

    # ------------------------------------------------------------ 4. break-even price per sold server-hour
    print("== 4. Break-even price p* per sold server-hour (CHF; one price for every sold hour), central costs ==")
    print(f"  share of list = p* / US batch list value of one server-hour of work ({lv:.2f} CHF, r4_machine central)")
    print(f"{'form':<34}{'N':>2} {'conv':<13}" + "".join(f"{'o=%.2f' % o:>15}" for o in OCC))
    rows = [("F1 spot only", "F1", None), ("F2 flat + cloud fb runpod_same", "F2", "runpod_same"),
            ("F2 flat + cloud fb exo_ch_4gpu", "F2", "exo_ch_4gpu"), ("F3 July floor + spot", "F3", None)]
    for L in LIFE:
        print(f"  life {L:.0f} y:")
        for lab, form, fb in rows:
            for n in (6, 8):
                for conv in ("heat credited", "heat to host"):
                    c_f = FALLBACK[fb][0] if fb else 0.0
                    cells = []
                    for o in OCC:
                        ps = line(n, form, conv, o, 0, 0, c_f, L=L)["ps"]
                        cells.append(f"{ps:6.2f} ({ps/lv*100:4.1f}%)")
                    print(f"  {lab:<32}{n:>2} {conv:<13}" + "".join(f"{c:>15}" for c in cells))
    print("  F2 o = occupancy of the winter surplus sold spot; the committed volume is always sold. F2 o=0 not shown:")
    for n in (6, 8):
        for fb in ("runpod_same", "exo_ch_4gpu"):
            r = line(n, "F2", "heat credited", 0.0, 0, 0, FALLBACK[fb][0])
            print(f"    N={n} F2 {fb:<12} surplus idle: p* {r['ps']:.2f} (5 y, heat credited); fallback {r['V']-r['A']:,.0f} h "
                  f"= {(r['V']-r['A'])/r['V']*100:.0f}% of committed work")
    print()

    # ------------------------------------------------------------ 5. payback grid at sourced price anchors
    print("== 5. Payback (years) at price anchors, central costs, life-independent ==")
    print(f"{'form / price':<44}{'N':>2} {'conv':<13}" + "".join(f"{'o=%.2f' % o:>8}" for o in OCC))
    grid = [
        ("F1 spot @ spot_salad", "F1", "spot_salad", "spot_salad", None),
        ("F1 spot @ host048", "F1", "host048", "host048", None),
        ("F1 spot @ host072", "F1", "host072", "host072", None),
        ("F2 commit direct072, fb runpod, spot salad", "F2", "direct072", "spot_salad", "runpod_same"),
        ("F2 commit direct072, fb exo_ch, spot salad", "F2", "direct072", "spot_salad", "exo_ch_4gpu"),
        ("F2 commit heata_list, fb exo_ch, spot salad", "F2", "heata_list", "spot_salad", "exo_ch_4gpu"),
        ("F3 floor direct072 + spot host048", "F3", "direct072", "host048", None),
        ("F3 floor direct072 + spot salad", "F3", "direct072", "spot_salad", None),
    ]
    for lab, form, pc, pscur, fb in grid:
        for n in (6, 8):
            for conv in ("heat credited", "heat to host"):
                c_f = FALLBACK[fb][0] if fb else 0.0
                cells = [fmt(line(n, form, conv, o, PRICES[pc][0], PRICES[pscur][0], c_f)["pb"]) for o in OCC]
                print(f"  {lab:<42}{n:>2} {conv:<13}" + "".join(f"{c:>8}" for c in cells))
    print()

    # ------------------------------------------------------------ 6. cost-case and price-decline sensitivity
    print("== 6. Sensitivity of the central line (F1, o = 0.60, p = host072 2.03, heat credited) ==")
    for n in (6, 8):
        for case in ("low", "central", "high"):
            r = line(n, "F1", "heat credited", OCC_CENTRAL, 0, PRICES["host072"][0], 0, case=case)
            print(f"  N={n} fixed-cost case {case:<8} K {r['K']:>7,.0f}/house-yr  payback {fmt(r['pb'])} y  p*(5 y) {r['ps']:.2f}")
        r = line(n, "F1", "heat credited", OCC_CENTRAL, 0, PRICES["host072"][0], 0)
        for d in (0.05, 0.10, 0.20):
            pb = payback(r["I"], r["m"], decline=d, revenue=r["rev"])
            print(f"  N={n} income falling {d*100:.0f} % a year (ASSUMPTION): payback {fmt(pb)} y (constant prices {fmt(r['pb'])} y)")
        r0 = line(n, "F1", "heat credited", 1.0, 0, PRICES["host072"][0], 0)
        f = fixed_costs(n)
        r_nok = r0["m"] + f["K"]
        print(f"  N={n} plan basis (o = 1.00, no K): payback {fmt(r0['I'] / r_nok)} y; with K {fmt(r0['pb'])} y")
    print()
    print("  Reading: payback = I / margin; any 'never' means margin <= 0 or > 99 years. Prices are snapshots of 21 Nov 2026.")


if __name__ == "__main__":
    main()
