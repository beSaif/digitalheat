"""Round 2: host-side fleet economics per server rank, and a mixed fleet.

    python3 analysis/r2_fleet_economics.py

Exploratory. NOT the scheduler. Imports the hourly balance from
analysis/baseline_sweep.py (not modified). Standard library only.

Rank k = the k-th server under the 'follow' policy (never dumps heat). Its run
hours and used heat are the difference between the N=k and N=k-1 simulations.

Per rank and year:
    margin = host income per sold hour x sold share x run hours
             - electricity (run hours x 1 kW x 0.3325 CHF/kWh)
             + heat value (used heat x 0.133 CHF/kWh), only if the operator is
               credited the heat (case formula); 0 if the homeowner gets it free
    payback = hardware cost / margin
An unsold run hour still runs and heats the house (the task's formula). The
variant "stop when unsold" is printed separately.

The official case break-even formula is NOT changed: section 1 prints it from
baseline_sweep.simulate() and, next to it, the same figure without heat credit.

Every web number used below has its URL and status in
docs/research/r2-host-income-hardware.md. Hardware cost and income are per
1 kW of electrical draw, because the case's server is 1 kW.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import load, simulate, PRICE, HEAT_VALUE, REC  # noqa: E402

USD = 0.9223 / 1.0990   # CHF per USD, ECB reference rates 2026-11-20 (sourced in round 1)
EUR = 0.9223            # CHF per EUR, same source

# --- host-side income, USD per GPU-hour (what the hardware owner receives) ---------------
# Salad network monitor feed, read 2026-11-21 01:11 UTC (sourced)
SALAD_4090 = {"min": 0.128, "avg": 0.2302, "top25": 0.2663, "max": 0.352}
SALAD_5090 = {"min": 0.200, "avg": 0.3227, "top25": 0.3867, "max": 0.480}
# Vast.ai article of 2026-05-18 (sourced, vendor's own statement)
VAST_5090_HOST = (0.30, 0.60)
VAST_H100_HOST = (2.15, 4.00)
VAST_MARKUP = 1.25      # "Live GPU prices are typically about 25% above what hosts earn"
# Vast.ai public offer list, verified single-GPU unrented offers, 2026-11-21 01:13 UTC
# (computed medians of asking prices; renter side is our reading, see research file)
VAST_4090_BID_MED, VAST_4090_OD_MED = 0.347, 0.467
VAST_5090_BID_MED, VAST_5090_OD_MED = 0.533, 0.667

# --- GPUs per 1 kW of wall power ----------------------------------------------------------
G4090_PER_KW = 2.0            # 2 x 450 W cards (sourced) + ~100 W host (ASSUMPTION), as in round 1
RIG_5090_KW = 1.35            # 2 x 575 W cards (sourced) + ~200 W for CPU and rest (ASSUMPTION)
G5090_PER_KW = 2.0 / RIG_5090_KW
H100_PER_KW = 8.0 / 10.2      # DGX H100: 8 GPUs, 10.2 kW max (sourced in round 1)

# --- hardware purchase price, CHF per 1 kW of wall power ----------------------------------
HW = {
    "refurb CPU (R740, 2x Gold 6148)": 2196.31 * USD / 0.457,      # sourced price / 457 W of a similar R740 (power = our transfer)
    "used 2x RTX 4090 rig (round 1)": 2 * 2338.0 * USD + 2000.0,   # cards sourced, 2,000 CHF host ASSUMPTION
    "new CPU (R760, 1 CPU, floor)": 14239.01 * USD,                # sourced; one CPU only, real 1 kW machine costs more
    "new 2x RTX 5090 workstation": 25279.0 * USD / RIG_5090_KW,    # sourced price / assumed 1.35 kW
    "H100 server share (round 1)": (250000.0 + 400000.0) / 2 / 10.2 * USD,
}
DLC_PER_SERVER = 356.31 * USD   # sourced: direct-to-chip parts per server at 754-server scale (not a house)

BE_CREDIT = PRICE - REC * HEAT_VALUE   # operator credited the heat value (case formula)
BE_FREE = PRICE                        # homeowner gets the heat free


def ranks(rows):
    out, prev_h, prev_u = [], 0.0, 0.0
    for n in range(1, 14):
        r = simulate(rows, n)
        out.append({"k": n, "h": r["run_h"] - prev_h, "used": r["used"] - prev_u,
                    "cov": r["coverage"], "util": r["util"]})
        prev_h, prev_u = r["run_h"], r["used"]
    return out


def margin(rk, p, sold=1.0, credit=True, stop_unsold=False):
    """CHF/yr for one rank. p = host income per sold hour."""
    h = rk["h"] * sold if stop_unsold else rk["h"]
    used = rk["used"] * sold if stop_unsold else rk["used"]
    income = p * (rk["h"] * sold)
    return income - h * PRICE + (used * HEAT_VALUE if credit else 0.0)


def n_star(rks, p, hw, life, sold=1.0, credit=True, stop_unsold=False):
    """Largest N such that every rank 1..N pays back its hardware within `life` years."""
    n = 0
    for rk in rks:
        m = margin(rk, p, sold, credit, stop_unsold)
        if m > 0 and hw / m <= life:
            n = rk["k"]
        else:
            break
    return n


def grid(rks, incomes, hws, life, sold, credit, stop_unsold=False):
    print(f"{'income/h':>9} | " + " ".join(f"{hw:>6,.0f}" for hw in hws) + "   <- hardware CHF per 1 kW server")
    for p in incomes:
        print(f"{p:>9.2f} | " + " ".join(f"{n_star(rks, p, hw, life, sold, credit, stop_unsold):>6}" for hw in hws))


def band(rks, n, hw, life, be):
    """Net income per RUN hour (= income per sold hour x sold share) for which N* == n."""
    lo = be + hw / life / rks[n - 1]["h"]
    hi = be + hw / life / rks[n]["h"] if n < len(rks) else float("inf")
    return lo, hi


if __name__ == "__main__":
    rows = load()
    rks = ranks(rows)
    INC = (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.75, 1.00, 1.50, 2.00, 3.00)
    HWS = (2000, 3000, 4000, 6000, 8000, 10000, 15000, 20000, 27000)

    print("== 1. Who receives the heat value? Operator break-even both ways ==")
    print(f"FX: 1 USD = {USD:.4f} CHF, 1 EUR = {EUR:.4f} CHF (ECB reference rates 2026-11-20)")
    print(f"{'N':>2} {'srv-h':>7} {'elec CHF':>9} {'heat CHF':>9} {'official BE (heat credited)':>28} {'BE if homeowner gets heat free':>31}")
    for n in (1, 6, 8):
        r = simulate(rows, n)
        print(f"{n:>2} {r['run_h']:>7.0f} {r['elec']:>9.0f} {r['heat_val']:>9.0f} {r['breakeven']:>28.4f} {r['elec'] / r['run_h']:>31.4f}")
    print("Official formula (unchanged): (electricity cost - value of heat actually used) / server-hours sold.")
    print("Both columns assume every run hour is sold. With sold share s the break-even per SOLD hour is the figure / s:")
    print("  sold share    " + "  ".join(f"{s:>5.0%}" for s in (1.0, 0.9, 0.8, 0.7, 0.5)))
    print("  heat credited " + "  ".join(f"{BE_CREDIT / s:>5.3f}" for s in (1.0, 0.9, 0.8, 0.7, 0.5)))
    print("  heat free     " + "  ".join(f"{BE_FREE / s:>5.3f}" for s in (1.0, 0.9, 0.8, 0.7, 0.5)))
    print("If the homeowner pays the operator a share f of the heat value (0.133 CHF/kWh heat), break-even per sold hour at 100% sold:")
    print("  " + "  ".join(f"f={f:.2f}: {PRICE - f * REC * HEAT_VALUE:.4f}" for f in (0.0, 0.25, 0.5, 0.75, 1.0)))
    r6 = simulate(rows, 6)
    print(f"Heat value at stake, N=6: {r6['heat_val']:.0f} CHF/yr; N=8: {simulate(rows, 8)['heat_val']:.0f} CHF/yr; N=1: {simulate(rows, 1)['heat_val']:.0f} CHF/yr.")

    print("\n== 2. Server ranks, follow policy ==")
    print(f"{'rank':>4} {'run h/yr':>9} {'used heat kWh':>14} {'cover at N=rank':>16} {'util at N=rank':>15}")
    for rk in rks:
        print(f"{rk['k']:>4} {rk['h']:>9.0f} {rk['used']:>14.0f} {rk['cov'] * 100:>15.1f}% {rk['util'] * 100:>14.1f}%")

    print("\n== 3. Host-side income points, converted to CHF per 1-kW-server-hour SOLD ==")
    pts = [
        ("Salad RTX 4090 host rate, lowest (most interruptible tier)", SALAD_4090["min"] * G4090_PER_KW * USD),
        ("Salad RTX 4090 host rate, average of all hosts", SALAD_4090["avg"] * G4090_PER_KW * USD),
        ("Salad RTX 4090 host rate, average of top 25%", SALAD_4090["top25"] * G4090_PER_KW * USD),
        ("Salad RTX 4090 host rate, highest", SALAD_4090["max"] * G4090_PER_KW * USD),
        ("Salad RTX 5090 host rate, lowest", SALAD_5090["min"] * G5090_PER_KW * USD),
        ("Salad RTX 5090 host rate, average of all hosts", SALAD_5090["avg"] * G5090_PER_KW * USD),
        ("Salad RTX 5090 host rate, highest", SALAD_5090["max"] * G5090_PER_KW * USD),
        ("Vast article, RTX 5090 host, low end", VAST_5090_HOST[0] * G5090_PER_KW * USD),
        ("Vast article, RTX 5090 host, high end", VAST_5090_HOST[1] * G5090_PER_KW * USD),
        ("Vast offers, RTX 4090 interruptible floor median / 1.25", VAST_4090_BID_MED / VAST_MARKUP * G4090_PER_KW * USD),
        ("Vast offers, RTX 4090 on-demand median / 1.25", VAST_4090_OD_MED / VAST_MARKUP * G4090_PER_KW * USD),
        ("Vast offers, RTX 5090 interruptible floor median / 1.25", VAST_5090_BID_MED / VAST_MARKUP * G5090_PER_KW * USD),
        ("Vast offers, RTX 5090 on-demand median / 1.25", VAST_5090_OD_MED / VAST_MARKUP * G5090_PER_KW * USD),
        ("Vast article, H100/H200 host, low end (vendor claim)", VAST_H100_HOST[0] * H100_PER_KW * USD),
        ("Vast article, H100/H200 host, high end (vendor claim)", VAST_H100_HOST[1] * H100_PER_KW * USD),
    ]
    for name, v in pts:
        print(f"  {v:>6.3f} CHF  {v / BE_CREDIT:>5.2f}x BE(credited)  {v / BE_FREE:>5.2f}x BE(free)  {name}")
    print(f"GPUs per kW: RTX 4090 {G4090_PER_KW:.2f}, RTX 5090 {G5090_PER_KW:.2f}, H100 {H100_PER_KW:.3f}")
    print("Host share on Salad (host rate / renter price): "
          + ", ".join(f"{g} {a:.3f}/{b:.3f}={a / b:.2f}" for g, a, b in (
              ("4090 lowest", 0.128, 0.160), ("4090 highest", 0.352, 0.440),
              ("5090 lowest", 0.200, 0.250), ("5090 highest", 0.480, 0.600))))
    print(f"Vast interruptible floor / on-demand asking median: RTX 4090 {VAST_4090_BID_MED / VAST_4090_OD_MED:.2f}, RTX 5090 {VAST_5090_BID_MED / VAST_5090_OD_MED:.2f}")

    print("\n== 4. Hardware cost per 1 kW of wall power (CHF) ==")
    for name, v in HW.items():
        print(f"  {v:>8,.0f}  {name}")
    print(f"  {DLC_PER_SERVER:>8,.0f}  direct-to-chip liquid cooling parts per server, data-centre scale (adder, NOT a house installation)")

    print("\n== 5. N* = number of servers such that every rank pays back within the life ==")
    print("   rows: host income CHF per SOLD 1-kW-server-hour; unsold run hours still run as heaters")
    for life, sold, credit in ((5, 1.0, True), (5, 0.8, True), (5, 0.5, True), (3, 0.8, True), (7, 0.8, True), (5, 0.8, False), (5, 1.0, False)):
        print(f"\n-- life {life} y, sold share {sold:.0%}, heat value {'credited to operator' if credit else 'given to homeowner free'} --")
        grid(rks, INC, HWS, life, sold, credit)
    print("\n-- variant: server stops when it has no paying job (coverage falls with sold share); life 5 y, sold 50%, heat credited --")
    grid(rks, INC, HWS, 5, 0.5, True, stop_unsold=True)

    print("\n== 6. When are N=1, N=6, N=8 each the right answer? ==")
    print("Rank k pays back within L years iff  income x sold share >= BE + (hardware / L) / h_k.")
    print("So N* depends only on X = (hardware / L) / (income x sold share - BE), in run hours per year:")
    for n in (1, 6, 8):
        print(f"  N*={n}: {rks[n]['h']:.0f} < X <= {rks[n - 1]['h']:.0f}")
    print(f"  N*=0: X > {rks[0]['h']:.0f} or income x sold share <= BE.   BE = {BE_CREDIT:.4f} (heat credited) or {BE_FREE:.4f} (heat free)")
    for credit, be in ((True, BE_CREDIT), (False, BE_FREE)):
        print(f"\nNet income per RUN hour (= income per sold hour x sold share), CHF, heat {'credited' if credit else 'free to homeowner'}:")
        print(f"{'hardware':>9} {'life':>4} | {'N*=0 below':>10} | {'N*=1 from..to':>15} | {'N*=6 from..to':>15} | {'N*=8 from..to':>15} | {'N*>=11 from':>11}")
        for hw in (2000, 4000, 6000, 9000, 16000, 27000):
            for life in (3, 5, 7):
                b1, b6, b8 = band(rks, 1, hw, life, be), band(rks, 6, hw, life, be), band(rks, 8, hw, life, be)
                print(f"{hw:>9,} {life:>4} | {b1[0]:>10.3f} | {b1[0]:>6.3f}..{b1[1]:<7.3f} | {b6[0]:>6.3f}..{b6[1]:<7.3f} | "
                      f"{b8[0]:>6.3f}..{b8[1]:<7.3f} | {band(rks, 11, hw, life, be)[0]:>11.3f}")
    print("\nHardware budget (CHF per 1 kW server, life 5 y, 100% sold, heat credited) for which N* is 1, 6, 8 at sourced income points:")
    print(f"{'income':>7} | {'N*=0 above':>10} | {'N*=1':>15} | {'N*=6':>15} | {'N*=8':>15} | point")
    for name, p in (("Salad 4090 lowest", pts[0][1]), ("Salad 4090 average", pts[1][1]), ("Salad 5090 average", pts[5][1]),
                    ("Vast 4090 interruptible floor /1.25", pts[9][1]), ("Salad 4090 highest", pts[3][1]),
                    ("Vast 5090 host high end", pts[8][1]), ("Vast H100 host low end", pts[13][1])):
        d = p - BE_CREDIT
        if d <= 0:
            print(f"{p:>7.3f} | {'any':>10} | {'-':>15} | {'-':>15} | {'-':>15} | {name}: below break-even, no hardware budget at all")
            continue
        f = lambda n: f"{d * 5 * rks[n]['h']:>6,.0f}..{d * 5 * rks[n - 1]['h']:<7,.0f}"
        print(f"{p:>7.3f} | {d * 5 * rks[0]['h']:>10,.0f} | {f(1):>15} | {f(6):>15} | {f(8):>15} | {name}")

    print("\n== 7. Named scenarios ==")
    scen = [
        ("used 2x4090 rig, Salad lowest", pts[0][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("used 2x4090 rig, Salad average", pts[1][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("used 2x4090 rig, Vast interruptible floor", pts[9][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("used 2x4090 rig, Salad highest", pts[3][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("new 2x5090 workstation, Salad average", pts[5][1], HW["new 2x RTX 5090 workstation"]),
        ("new 2x5090 workstation, Vast host high end", pts[8][1], HW["new 2x RTX 5090 workstation"]),
        ("H100 share, Vast host low end (claim)", pts[13][1], HW["H100 server share (round 1)"]),
        ("H100 share, Vast host high end (claim)", pts[14][1], HW["H100 server share (round 1)"]),
    ]
    print("N* and payback in years of rank 1 / 6 / 8, life 5 y. 'inst' adds 3,000 CHF per server for plumbing and installation (ASSUMPTION).")
    print(f"{'scenario':<44}{'inc':>6}{'hw':>8} | {'sold100 credit':>20} | {'sold80 credit':>20} | {'sold80 credit +inst':>20} | {'sold80 heat free':>20}")

    def cell(p, hw, sold, credit):
        n = n_star(rks, p, hw, 5, sold, credit)
        pbs = []
        for k in (1, 6, 8):
            m = margin(rks[k - 1], p, sold, credit)
            pbs.append("never" if m <= 0 else (f"{hw / m:.1f}" if hw / m < 100 else ">100"))
        return f"N*={n} " + "/".join(pbs)

    for name, p, hw in scen:
        print(f"{name:<44}{p:>6.3f}{hw:>8,.0f} | {cell(p, hw, 1.0, True):>20} | {cell(p, hw, 0.8, True):>20} | "
              f"{cell(p, hw + 3000, 0.8, True):>20} | {cell(p, hw, 0.8, False):>20}")

    print("\n== 8. Mixed fleet: per rank pick the option with the best yearly net = margin - hardware / life ==")
    print("Options per rank: A (expensive, high income), B (cheap, low income), or none (backup heater, net 0).")

    def mixed(pa, ca, pb, cb, life=5, sold=0.8, credit=True):
        pick, tot, cov = [], 0.0, 0.0
        for rk in rks:
            a = margin(rk, pa, sold, credit) - ca / life
            b = margin(rk, pb, sold, credit) - cb / life
            best = max(("A", a), ("B", b), ("-", 0.0), key=lambda x: x[1])
            if best[0] == "-":
                break
            pick.append(best[0])
            tot += best[1]
            cov = rk["cov"]

        def homog(p, c):
            t, n = 0.0, 0
            for rk in rks:
                v = margin(rk, p, sold, credit) - c / life
                if v <= 0:
                    break
                t, n = t + v, n + 1
            return n, t
        return pick, tot, cov, homog(pa, ca), homog(pb, cb)

    cases = [
        ("A = H100 share at Vast host low end (claim); B = used 2x4090 rig at Salad average",
         pts[13][1], HW["H100 server share (round 1)"], pts[1][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("A = H100 share at Vast host low end (claim); B = used 2x4090 rig at Salad highest",
         pts[13][1], HW["H100 server share (round 1)"], pts[3][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("A = H100 share at HALF the Vast low end; B = used 2x4090 rig at Salad average",
         pts[13][1] / 2, HW["H100 server share (round 1)"], pts[1][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("A = new 2x5090 workstation at Vast host high end; B = used 2x4090 rig at Salad average",
         pts[8][1], HW["new 2x RTX 5090 workstation"], pts[1][1], HW["used 2x RTX 4090 rig (round 1)"]),
        ("A = used 2x4090 rig at Salad highest; B = refurbished CPU server earning nothing (pure heater)",
         pts[3][1], HW["used 2x RTX 4090 rig (round 1)"], 0.0, HW["refurb CPU (R740, 2x Gold 6148)"]),
        ("A = used 2x4090 rig at Salad average; B = refurbished CPU server at 0.30 CHF/h (ASSUMPTION, no source)",
         pts[1][1], HW["used 2x RTX 4090 rig (round 1)"], 0.30, HW["refurb CPU (R740, 2x Gold 6148)"]),
    ]
    for sold in (1.0, 0.8):
        for label, pa, ca, pb, cb in cases:
            pick, tot, cov, ha, hb = mixed(pa, ca, pb, cb, sold=sold)
            print(f"\nsold {sold:.0%}, life 5 y, heat credited. {label}")
            print(f"  A: {pa:.3f} CHF/h, {ca:,.0f} CHF   B: {pb:.3f} CHF/h, {cb:,.0f} CHF")
            print(f"  best mix by rank: {''.join(pick) or '(no server)'}  -> N={len(pick)}, coverage {cov * 100:.1f}%, net {tot:,.0f} CHF/yr after straight-line hardware cost")
            print(f"  all-A fleet: N={ha[0]}, net {ha[1]:,.0f} CHF/yr   all-B fleet: N={hb[0]}, net {hb[1]:,.0f} CHF/yr")
            if pa != pb:
                hx = (ca - cb) / 5 / ((pa - pb) * sold)
                print(f"  A beats B on a rank only if it runs more than {hx:,.0f} h/yr")

    print("\n== 9. When the model does not pay off (computed thresholds) ==")
    print(f"Operation only, every run hour sold: below {BE_CREDIT:.4f} CHF per sold server-hour (heat credited) / {BE_FREE:.4f} (heat free).")
    for s in (0.8, 0.5):
        print(f"Operation only, {s:.0%} of run hours sold: below {BE_CREDIT / s:.3f} / {BE_FREE / s:.3f} CHF per sold hour.")
    print("With hardware, income per sold hour needed for rank k to pay back (sold 80%, life 5 y):")
    print(f"{'hardware CHF':>12} | " + " ".join(f"{'rank ' + str(k):>8}" for k in (1, 2, 6, 8)) + " | same, heat free: " + " ".join(f"{'rank ' + str(k):>8}" for k in (1, 6, 8)))
    for hw in (2000, 4000, 5924, 8924, 15714, 26740):
        a = " ".join(f"{(BE_CREDIT + hw / 5 / rks[k - 1]['h']) / 0.8:>8.3f}" for k in (1, 2, 6, 8))
        b = " ".join(f"{(BE_FREE + hw / 5 / rks[k - 1]['h']) / 0.8:>8.3f}" for k in (1, 6, 8))
        print(f"{hw:>12,} | {a} |                  {b}")
