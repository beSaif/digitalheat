"""Round 7: bridge between the two economics bases in analysis/.

ASSESSMENT ONLY. Not the team's scheduler. Standard library only. Read-only imports of
one_rack_model.py (the team's file: its argparse defaults are read, nothing is edited),
baseline_sweep.py and r5_chain.py.

    python3 analysis/r7_econ_bridge.py

Basis 1, one_rack_model.py (team): one house, ONE 1 kW server = 2 x RTX 4090 (used rig 5,924 CHF
  + 3,000 install), consumer-GPU marketplace prices (Vast.ai / Salad), 80 % of RUN hours sold while
  the server also runs the unsold 20 % (heat still delivered), 80 % platform share, heat free to
  the house, 300 CHF/yr opex, 5-year life.
Basis 2, r4/r5/r6 machine scripts (overnight loop): reference server 2U, 4 x RTX PRO 4500 Blackwell
  per ~0.95 kW, cold-plate chain installed ~212,600 CHF per house at N = 6, server OFF when unsold,
  heat credited to the operator (case convention) unless marked, price per sold server-hour needed.

The bridge changes ONE input at a time from basis 1 to basis 2 and prints the price per sold
server-hour the operator needs for a 5-year simple payback (CHF). Common metric:
    need = (electricity - heat credit + capex / life + opex) / sold server-hours  [/ platform share]
Unlimited demand (every permit hour can be sold), follow policy of baseline_sweep.py.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_sweep as bs  # noqa: E402
import one_rack_model as orm  # noqa: E402
import r5_chain as rc  # noqa: E402


def defaults():
    """one_rack_model's own argparse defaults (no CLI args)."""
    saved = sys.argv
    sys.argv = ["one_rack_model.py"]
    try:
        return orm.args()
    finally:
        sys.argv = saved


def need(rows, n, capex_house, opex_house, life, sold_share, unsold_runs, heat_credit, platform):
    r = bs.simulate(rows, n, policy="follow")
    run_h = r["run_h"]
    sold_h = run_h * sold_share
    ran_h = run_h if unsold_runs else sold_h            # unsold hours: server runs (basis 1) or is off
    used = r["used"] if unsold_runs else r["used"] * sold_share   # off when unsold: heat scales with sold h
    elec = ran_h * bs.P_EL * bs.PRICE
    heat = used * bs.HEAT_VALUE if heat_credit else 0.0
    cost = elec - heat + capex_house / life + opex_house
    return cost / sold_h / platform, r, sold_h


def main():
    a = defaults()
    rows = bs.load()
    capex1 = a.hardware + a.install
    inst6 = rc.installed(6, "DLC")[0]
    price1 = orm.PRICES_USD_PER_GPU_H["central"][0] * orm.GPU_PER_SERVER * orm.USD
    print("r7_econ_bridge.py  (assessment only; CHF; 1 USD = %.4f CHF, ECB 20 Nov 2026)" % orm.USD)
    print(f"one_rack_model defaults read from its argparse: sold {a.sold}, platform {a.platform_share}, "
          f"heat fee {a.heat_fee}, hardware {a.hardware:,.0f} + install {a.install:,.0f}, life {a.life}, opex {a.opex}")
    print(f"basis-2 installed cost per house, cold-plate chain, central, N=6 (r5_chain.installed): {inst6:,.0f} CHF\n")

    steps = [
        ("0 one_rack_model as is (client price, N=1)", dict(n=1, capex_house=capex1, opex_house=a.opex, life=a.life,
                                                             sold_share=a.sold, unsold_runs=True, heat_credit=False,
                                                             platform=a.platform_share)),
        ("1 sold direct (platform share 1.0)", dict(platform=1.0)),
        ("2 server OFF when unsold (basis-2 convention)", dict(unsold_runs=False)),
        ("3 every run hour sold (sold share 1.0)", dict(sold_share=1.0)),
        ("4 heat credited to the operator (case rule)", dict(heat_credit=True)),
        ("5 N = 6 servers, 6 x one_rack capex and opex", dict(n=6, capex_house=6 * capex1, opex_house=6 * a.opex)),
        ("6 basis-2 installed cost (cold-plate chain)", dict(capex_house=inst6)),
        ("7 no separate opex (r6_buyer_scenarios has none)", dict(opex_house=0.0)),
    ]
    kw = {}
    print(f"  {'step':<52}{'need CHF/sold h':>16}{'sold h':>9}{'coverage':>9}")
    for label, ch in steps:
        kw.update(ch)
        v, r, sold_h = need(rows, **kw)
        print(f"  {label:<52}{v:>16.3f}{sold_h:>9,.0f}{r['coverage']*100:>8.1f}%")

    print("\n  reference: one_rack_model prints 'client price needed 0.947' (step 0) and 'case break-even 0.2826'")
    print("  (= 0.2261 / 0.80: unsold hours still run). Basis 2 prints 0.2261 for every N and sold share,")
    print("  because unsold servers are off (r2_fleet_economics.py). r6_buyer_scenarios 'pool' (aggregator buys")
    print("  every permit hour, headline loop with cap + band) prints 1.60 at N=6; step 7 is its follow-policy twin.")

    print("\n== Price side (what one sold server-hour fetches, CHF) ==")
    print(f"  basis 1 central: {orm.PRICES_USD_PER_GPU_H['central'][0]} USD/GPU-h x {orm.GPU_PER_SERVER} GPU x {orm.USD} = "
          f"{price1:.3f} CHF per server-h to the client; x {a.platform_share} platform share = {price1*a.platform_share:.3f}"
          " to the operator")
    print("  basis 2: rental anchor 0.48-0.72 USD/GPU-h x 0.80 x 4.19 GPU-h per server-h = 1.35-2.03 CHF to the operator;")
    print("           list value of the work 7.7 / 14.3 / 38.2 CHF (public batch API prices, not an income)")
    print("           (both from r6_buyer_scenarios.py / r4_machine.py)")
    hw_kw1 = capex1 / 1.0
    print(f"\n== Hardware per kW at the wall == basis 1 {hw_kw1:,.0f} CHF per server (1 kW) incl. install; "
          f"basis 2 {inst6/6:,.0f} CHF per kW (house integration, storage and liquid cooling included)")


if __name__ == "__main__":
    main()
