"""Financial model of ONE installed server: one house, one 1 kW server, one compute client.

    python3 analysis/one_rack_model.py
    python3 analysis/one_rack_model.py --client-price 0.70 --sold 0.6 --heat-fee 0.05

Three views of the same year on the reference house (case assumptions, follow-heat
policy, nothing dumped, server powered off when there is no heat demand or tank space):

  1. House:   heating bill before vs after the server is installed
  2. Company: DigitalHeat's yearly P&L for this one server
  3. Client:  what the compute buyer pays, vs buying the same hours elsewhere

Labels: [SOURCED] number read from a source (URL in docs/research/), [COMPUTED] from the
simulation, [ASSUMPTION] our own choice. Standard library only.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_sweep import load, simulate, PRICE  # noqa: E402

USD = 0.8392            # CHF per USD, ECB 20 Nov 2026 [SOURCED]
COP = 2.5               # heat pump efficiency, case rule [SOURCED: case brief]
GPU_PER_SERVER = 2      # 1 kW server = 2 x RTX 4090 (450 W each) + ~100 W host [card SOURCED, total ASSUMPTION]

# Client-side price per GPU-hour, interruptible / batch tier (USD) [SOURCED, r2-host-income-hardware.md]
PRICES_USD_PER_GPU_H = {
    "low":     (0.160, "Salad RTX 4090 Batch tier (renter price)"),
    "central": (0.347, "Vast.ai RTX 4090 interruptible floor, median of 38 offers"),
    "high":    (0.440, "Salad RTX 4090 High tier (renter price)"),
}
ON_DEMAND_USD_PER_GPU_H = 0.467  # Vast.ai RTX 4090 on-demand ask, median of 42 offers [SOURCED]


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--client-price", type=float, default=None,
                   help="CHF the client pays per server-hour (default: central sourced price)")
    p.add_argument("--sold", type=float, default=0.80,
                   help="share of run hours sold to the client [ASSUMPTION, default 0.80]")
    p.add_argument("--platform-share", type=float, default=0.80,
                   help="share of client price reaching DigitalHeat; 0.80 = via a GPU marketplace "
                        "[SOURCED: Salad, Vast.ai], 1.0 = sold direct")
    p.add_argument("--heat-fee", type=float, default=0.0,
                   help="CHF per kWh of heat the house pays DigitalHeat [ASSUMPTION, default 0 = heat free]")
    p.add_argument("--hardware", type=float, default=5924.0,
                   help="server price CHF [SOURCED: used 2 x RTX 4090 rig, r2 research]")
    p.add_argument("--install", type=float, default=3000.0,
                   help="plumbing + installation CHF [ASSUMPTION, no source found]")
    p.add_argument("--life", type=float, default=5.0, help="years [ASSUMPTION]")
    p.add_argument("--opex", type=float, default=300.0,
                   help="CHF/yr maintenance, connectivity, insurance [ASSUMPTION]")
    return p.parse_args()


def chf(x):
    return f"{x:>10,.0f} CHF"


def main():
    a = args()
    rows = load()
    r = simulate(rows, 1, policy="follow")

    run_h = r["run_h"]                         # server-hours per year [COMPUTED]
    heat_used = r["used"]                      # kWh heat delivered and used [COMPUTED]
    demand = heat_used / r["coverage"]         # kWh total heat demand of the house
    elec_kwh = run_h * 1.0                     # 1 kW server
    sold_h = run_h * a.sold

    price_central = PRICES_USD_PER_GPU_H["central"][0] * GPU_PER_SERVER * USD
    client_price = a.client_price if a.client_price is not None else price_central

    # ---------------------------------------------------------------- 0. the year
    print("ONE SERVER, ONE HOUSE, ONE CLIENT — reference house Basel 2025, case assumptions\n")
    print("== 0. The year (follow-heat policy, 35 kWh tank, nothing dumped) [COMPUTED] ==")
    print(f"  server runs                {run_h:>8,.0f} h/yr  (utilisation {r['util']*100:.1f}%)")
    print(f"  electricity used           {elec_kwh:>8,.0f} kWh  x {PRICE} CHF/kWh = {elec_kwh*PRICE:,.0f} CHF")
    print(f"  heat delivered and used    {heat_used:>8,.0f} kWh  (80% of electricity, case rule)")
    print(f"  house heat demand          {demand:>8,.0f} kWh  -> server covers {r['coverage']*100:.1f}%")
    print(f"  heat dumped                {r['dumped']:>8,.0f} kWh")
    win = sum(v[0] for m, v in r["monthly"].items() if m in ("10", "11", "12", "01", "02", "03"))
    print(f"  run hours Oct–Mar / Apr–Sep {win:>7,.0f} / {run_h - win:,.0f} h")

    # ---------------------------------------------------------------- 1. house
    hp_before = demand / COP * PRICE
    hp_after = (demand - heat_used) / COP * PRICE
    fee = heat_used * a.heat_fee
    house_after = hp_after + fee
    print("\n== 1. HOUSE: heating bill (heat pump COP 2.5 does whatever the server does not) ==")
    print(f"  before: {demand:,.0f} kWh heat / 2.5 = {demand/COP:,.0f} kWh electricity  {chf(hp_before)}")
    print(f"  after:  heat pump for the remaining {demand-heat_used:,.0f} kWh heat        {chf(hp_after)}")
    print(f"          heat fee to DigitalHeat {a.heat_fee:.3f} CHF x {heat_used:,.0f} kWh   {chf(fee)}")
    print(f"          server electricity: paid by DigitalHeat (own meter / refund)  {chf(0)}")
    print(f"  after total                                                {chf(house_after)}")
    print(f"  SAVING                                                     {chf(hp_before-house_after)}"
          f"  ({(hp_before-house_after)/hp_before*100:.1f}% of the heating bill)")

    # ---------------------------------------------------------------- 2. company
    capex = a.hardware + a.install
    dep = capex / a.life
    revenue_compute = sold_h * client_price * a.platform_share
    revenue = revenue_compute + fee
    cost_elec = elec_kwh * PRICE
    costs = cost_elec + dep + a.opex
    profit = revenue - costs
    print("\n== 2. COMPANY (DigitalHeat): yearly P&L of this one server ==")
    print(f"  compute sold   {sold_h:,.0f} h ({a.sold*100:.0f}% of run hours [ASSUMPTION])"
          f" x {client_price:.3f} CHF x {a.platform_share*100:.0f}% kept   {chf(revenue_compute)}")
    print(f"  heat fee from house                                        {chf(fee)}")
    print(f"  REVENUE                                                    {chf(revenue)}")
    print(f"  electricity {elec_kwh:,.0f} kWh x {PRICE}                              {chf(-cost_elec)}")
    print(f"  hardware {a.hardware:,.0f} + install {a.install:,.0f} = {capex:,.0f} CHF over {a.life:.0f} yr     {chf(-dep)}")
    print(f"  maintenance, connectivity, insurance [ASSUMPTION]          {chf(-a.opex)}")
    print(f"  COSTS                                                      {chf(-costs)}")
    print(f"  PROFIT / LOSS per year                                     {chf(profit)}")
    cash = revenue - cost_elec - a.opex
    payback = capex / cash if cash > 0 else float("inf")
    print(f"  cash per year before hardware {cash:,.0f} CHF -> payback "
          + (f"{payback:.1f} years" if payback <= 50 else "never (over 50 years)"))
    print(f"  cost per run hour: electricity {PRICE:.3f} + hardware {dep/run_h:.3f}"
          f" + opex {a.opex/run_h:.3f} = {costs/run_h:.3f} CHF")
    be_client = (costs - fee) / (sold_h * a.platform_share)
    print(f"  client price needed to break even: {be_client:.3f} CHF per server-hour sold"
          f"  (= {be_client/GPU_PER_SERVER/USD:.3f} USD per GPU-hour)")
    be_case = (cost_elec - heat_used * PRICE / COP) / sold_h
    print(f"  case break-even (electricity - heat value, no hardware): {be_case:.4f} CHF per sold hour")

    # ---------------------------------------------------------------- 3. client
    spend = sold_h * client_price
    ondemand = ON_DEMAND_USD_PER_GPU_H * GPU_PER_SERVER * USD
    print("\n== 3. CLIENT: buys interruptible batch GPU time (e.g. archive transcription, embeddings) ==")
    print(f"  server-hours bought        {sold_h:>8,.0f} h/yr  (= {sold_h*GPU_PER_SERVER:,.0f} RTX-4090 GPU-hours)")
    print(f"  price                      {client_price:>8.3f} CHF per server-hour"
          f" (= {client_price/GPU_PER_SERVER/USD:.3f} USD per GPU-hour)")
    print(f"  CLIENT PAYS                                                {chf(spend)}")
    print(f"  same hours on-demand ({ON_DEMAND_USD_PER_GPU_H} USD/GPU-h, Vast.ai median)      {chf(sold_h*ondemand)}")
    print(f"  client saving vs on-demand                                 {chf(sold_h*(ondemand-client_price))}")
    print("  what it gets: hours with a deadline, not a machine — jobs pause when the tank is full,")
    print(f"  {win/run_h*100:.0f}% of the hours fall in Oct–Mar.")

    # ---------------------------------------------------------------- 4. money flow
    print("\n== 4. Where the money goes (per year) ==")
    print(f"  client  -> pays {spend:,.0f} CHF for compute")
    print(f"  market  -> keeps {spend - revenue_compute:,.0f} CHF ({(1-a.platform_share)*100:.0f}% platform fee)")
    print(f"  DigitalHeat -> receives {revenue:,.0f}, pays electricity {cost_elec:,.0f}, hardware {dep:,.0f},"
          f" opex {a.opex:,.0f} -> {profit:+,.0f} CHF")
    print(f"  house   -> saves {hp_before-house_after:,.0f} CHF on heating")

    # ---------------------------------------------------------------- 4b. whole chain
    heat_value = heat_used * PRICE / COP
    system_cost = cost_elec - heat_value + dep + a.opex
    print("\n== 4b. Whole chain, independent of who pays whom ==")
    print(f"  electricity {cost_elec:,.0f} - heat-pump electricity avoided {heat_value:,.0f}"
          f" + hardware {dep:,.0f} + opex {a.opex:,.0f} = {system_cost:,.0f} CHF/yr to cover")
    print(f"  client pays {spend:,.0f} CHF -> chain surplus {spend - system_cost:+,.0f} CHF/yr"
          f" before any platform fee")
    print(f"  client price at which the whole chain breaks even: {system_cost/sold_h:.3f} CHF per sold"
          f" server-hour (= {system_cost/sold_h/GPU_PER_SERVER/USD:.3f} USD per GPU-hour)")

    # ---------------------------------------------------------------- 5. sensitivity
    print("\n== 5. Company profit per year (CHF) by client price and sold share ==")
    shares = [0.5, 0.65, 0.8, 1.0]
    print(f"  {'client price':<52}" + "".join(f"{f'sold {s*100:.0f}%':>11}" for s in shares))
    for k, (usd, src) in PRICES_USD_PER_GPU_H.items():
        p = usd * GPU_PER_SERVER * USD
        cells = "".join(f"{run_h*s*p*a.platform_share + fee - costs:>11,.0f}" for s in shares)
        print(f"  {k:<8}{p:.3f} CHF/server-h  {src[:28]:<28}" + cells)
    print("\n  sold direct (platform share 100%), central price:"
          + "".join(f"{run_h*s*price_central + fee - costs:>11,.0f}" for s in shares))

    print("\nWhen it does not pay: client price below the break-even above, sold share too low,")
    print("or hardware + install much above ~9,000 CHF. The house always saves, because DigitalHeat")
    print("pays the electricity; that cost sits entirely in the company P&L.")


if __name__ == "__main__":
    main()
