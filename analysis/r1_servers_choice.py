"""Round 1: how many servers per house, judged on the marginal server's economics.

    python3 analysis/r1_servers_choice.py

Imports the hourly balance from analysis/baseline_sweep.py (not modified) and adds,
for N = 1..13 under the 'follow' policy (never dumps heat):
  - coverage, utilisation, the marginal (N-th) server's run hours
  - the marginal server's yearly margin = compute income - electricity + heat value
  - simple payback of that server's hardware price
for three hardware/price scenarios. Hardware cost is NOT part of the official
break-even (case formula); it is used here only to justify N.

Every price below is documented with its source URL and status in
docs/research/r1-servers-and-price.md. USD->CHF and EUR->CHF from the ECB
reference rates of 2026-11-20 (EUR/USD 1.0990, EUR/CHF 0.9223).
Standard library only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import load, simulate, PRICE, HEAT_VALUE  # noqa: E402

USD = 0.9223 / 1.0990      # CHF per USD = 0.8392
EUR = 0.9223               # CHF per EUR
LIFE = 5.0                 # years of service life: ASSUMPTION (not sourced)
H_MONTH = 730.0            # hours per month used to convert monthly rents

# name: (low, central, high compute income in CHF per 1-kW-server-hour SOLD,
#        hardware price in CHF per 1-kW server, note)
SCEN = {
    "CPU  (96-core dual-socket)": (
        0.5 * 319.0 * 2 / H_MONTH * EUR,   # low: half of bare-metal rent (haircut = ASSUMPTION)
        319.0 * 2 / H_MONTH * EUR,         # central: 2 x Hetzner AX162 (48 cores each), EUR 319/mo
        2.259 * USD,                       # high: AWS c7i.48xlarge spot, USD 2.259/h
        20000.0,                           # ASSUMPTION; sourced floor is 11,950 (single-CPU Dell R760)
        "hardware 20,000 CHF = assumption"),
    "GPU-A (2x RTX 4090 rig)": (
        2 * 0.160 * USD,                   # low: cheapest tracked 4090 price, any provider
        2 * 0.361 * USD,                   # central: cheapest Vast.ai 4090 listing
        2 * 0.89 * USD,                    # high: RunPod Secure Cloud 4090
        2 * 2338.0 * USD + 2000.0,         # 2 used cards (sourced) + 2,000 CHF host (ASSUMPTION)
        "hardware = 2 used cards + 2,000 CHF host (assumption)"),
    "GPU-B (0.78 H100, DGX share)": (
        1.99 * 8 / 10.2 * USD,             # low: RunPod community H100 PCIe
        30.584 / 10.2 * USD,               # central: AWS p5.48xlarge spot / 10.2 kW
        4.59 * 8 / 10.2 * USD,             # high: Lambda 8x H100 on-demand
        (250000.0 + 400000.0) / 2 / 10.2 * USD,   # mid of USD 250k-400k per 8-GPU server
        "hardware = mid of 250k-400k USD per 10.2 kW server"),
}


def marginal(rows):
    out, prev = [], None
    for n in range(1, 14):
        r = simulate(rows, n)
        p_run = prev["run_h"] if prev else 0.0
        p_used = prev["used"] if prev else 0.0
        out.append({"n": n, "cov": r["coverage"], "util": r["util"], "dump": r["dumped"],
                    "h": r["run_h"] - p_run, "used": r["used"] - p_used,
                    "run_h": r["run_h"], "tot_used": r["used"]})
        prev = r
    return out


def margin(m, price, sold=1.0):
    """CHF/yr for the marginal server: income - electricity + value of its used heat."""
    return m["h"] * price * sold - m["h"] * PRICE + m["used"] * HEAT_VALUE


def pb(hw, mg):
    return hw / mg if mg > 0 else float("inf")


def fmt(x):
    return "  never" if x == float("inf") else f"{x:7.1f}"


if __name__ == "__main__":
    rows = load()
    ms = marginal(rows)
    be = PRICE - 0.8 * HEAT_VALUE
    print(f"FX: 1 USD = {USD:.4f} CHF, 1 EUR = {EUR:.4f} CHF (ECB 2026-11-20). Service life {LIFE:.0f} y (assumption).")
    print(f"Operating break-even (case formula, follow policy): {be:.4f} CHF per server-hour sold")
    print("\n== Physical balance, follow policy ==")
    print(f"{'N':>2} {'cover':>7} {'util':>6} {'dump':>5} {'marg h/yr':>9} {'marg heat kWh':>13} {'marg cover pts':>14}")
    tot = sum(a + b for _, a, b in rows)
    for m in ms:
        print(f"{m['n']:>2} {m['cov']*100:>6.1f}% {m['util']*100:>5.1f}% {m['dump']:>5.0f} {m['h']:>9.0f} "
              f"{m['used']:>13.0f} {m['used']/tot*100:>14.1f}")

    for name, (lo, ce, hi, hw, note) in SCEN.items():
        print(f"\n== {name}: income low/central/high = {lo:.3f}/{ce:.3f}/{hi:.3f} CHF per server-h; "
              f"hardware {hw:,.0f} CHF ({note}) ==")
        print(f"{'N':>2} {'marg h':>7} | {'margin CHF/yr  low':>18} {'central':>8} {'high':>8} | "
              f"{'payback y  low':>14} {'central':>8} {'high':>8} | {'fleet payback central':>21}")
        best = {"low": 0, "central": 0, "high": 0}
        cum = 0.0
        for m in ms:
            mg = [margin(m, p) for p in (lo, ce, hi)]
            pbs = [pb(hw, x) for x in mg]
            cum += mg[1]
            for key, p in zip(("low", "central", "high"), pbs):
                if p <= LIFE and best[key] == m["n"] - 1:
                    best[key] = m["n"]
            print(f"{m['n']:>2} {m['h']:>7.0f} | {mg[0]:>18.0f} {mg[1]:>8.0f} {mg[2]:>8.0f} | "
                  f"{fmt(pbs[0]):>14} {fmt(pbs[1]):>8} {fmt(pbs[2]):>8} | {fmt(pb(hw*m['n'], cum)):>21}")
        print(f"Rule 'add servers while the marginal server pays back within {LIFE:.0f} y': "
              f"N = {best['low']} (low) / {best['central']} (central) / {best['high']} (high)")
        # price needed so that the N-th server pays back within LIFE
        print("Compute price (CHF/server-h sold) at which the N-th server pays back in "
              f"{LIFE:.0f} y:  " + "  ".join(
                  f"N={m['n']}:{be + hw / LIFE / m['h']:.2f}" for m in ms if m["n"] in (1, 2, 4, 6, 8, 10)))
        print(f"Share of run hours that must be sold at the central price just to cover operation: "
              f"{be / ce * 100:.0f}%")

    print("\n== Sold-share sensitivity (unsold run hours still heat the house), central prices, N-th server margin CHF/yr ==")
    print(f"{'scenario':<30}{'sold':>5} " + " ".join(f"{'N='+str(n):>7}" for n in (1, 4, 6, 8)))
    for name, (lo, ce, hi, hw, note) in SCEN.items():
        for s in (1.0, 0.7, 0.5):
            print(f"{name:<30}{s*100:>4.0f}% " + " ".join(f"{margin(ms[n-1], ce, s):>7.0f}" for n in (1, 4, 6, 8)))
