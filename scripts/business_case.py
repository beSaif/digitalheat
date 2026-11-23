"""DigitalHeat business case: services, prices, homeowner offer, billing, investor financials.

    python3 scripts/business_case.py     # writes outputs/business_case.md, outputs/business_case.json, plots/payback_vs_price.png

Prices shared with the yearly balance and the dashboard (USD/CHF, AWS spot and on-demand for
the reference server, Titan embeddings and Cohere rerank, hardware per server and its write-off
years) come from data/prices_2026.json via scheduler.pricing, so every page uses one set of
numbers. Everything else lives in data/business_assumptions.json with its source (or "our
assumption").
The physics comes from the scheduler's yearly balance (same code as the key figures):
server-hours, heat used, heat dumped for the reference house and for the services fleet.

Sections of the output, in the order of the team's to-do list:
 1. Service catalogue with AWS / Google prices per unit and our price (premium)
 2. Redundancy tier pricing (2-4 sites) and what it costs us
 3. Homeowner offer: heat at 30 % / 50 % below a heat pump, 10-year savings
 4. Billing flow: host's meter pays, DigitalHeat refunds the servers' share
 5. Investor view: capex, opex, payback as a function of the price per server-hour
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scheduler.balance import REFERENCE, SERVICES, run  # noqa: E402
from scheduler.core import REC, service_job_types  # noqa: E402
from scheduler.pricing import FX, HW_CHF_PER_SERVER, HW_YEARS, ON_DEMAND_CHF_H, P, SPOT_CHF_H  # noqa: E402

A = json.loads((ROOT / "data" / "business_assumptions.json").read_text())
OUT = ROOT / "outputs"
PLOTS = ROOT / "plots"


def v(key):
    """Value of an assumption (each entry is {value, unit, source})."""
    if key == "server_life_years":
        return HW_YEARS
    return A[key]["value"]


def chf(usd):
    return usd * FX


def _measured_units():
    """Embeddings and reranking: prices and units from prices_2026.json and our measurements."""
    from workloads.catalog import reference_job_types
    jt = reference_job_types()
    ms = P["managed_services"]
    return {
        "embed": {"aws_usd_per_unit": ms["embed"]["usd"], "aws_service": ms["embed"]["service"],
                  "units_per_server_h": jt["embed"].items_per_server_hour * P["tokens_per_abstract"]["value"] / 1e6},
        "rerank": {"aws_usd_per_unit": ms["rerank"]["usd"], "aws_service": ms["rerank"]["service"],
                   "units_per_server_h": jt["rerank"].items_per_server_hour / P["rerank_docs_per_query"]["value"] / 1000},
    }


# ---- physics from the scheduler ----------------------------------------------------------------
def physics():
    ref = run(REFERENCE, 2025, series=False)["fleet"]
    svc = run(SERVICES, 2025, series=False, types=service_job_types())["fleet"]
    cool = run([dict(s, drycooler_kw=v("drycooler_kw_per_site")) for s in SERVICES], 2025, series=False,
               types=service_job_types(), cool_fill=True)["fleet"]
    ref["servers_per_site"] = ref["servers"]
    svc["servers_per_site"] = cool["servers_per_site"] = svc["servers"] / len(SERVICES)
    return {"reference house": ref, "services fleet": svc, "services fleet + dry cooler": cool}


# ---- 1. service catalogue -----------------------------------------------------------------------
def catalogue():
    rows = []
    shared = _measured_units()
    for s in A["services"]:
        s = dict(s, **shared.get(s["id"], {}))
        aws = chf(s["aws_usd_per_unit"]) if s.get("aws_usd_per_unit") is not None else None
        gcp = chf(s["gcp_usd_per_unit"]) if s.get("gcp_usd_per_unit") is not None else None
        ref = aws if aws is not None else gcp  # "charge more than Amazon": AWS is the reference
        ours = ref * (1 + s["premium"])
        per_sh = ours * s["units_per_server_h"]
        rows.append(dict(s, aws_chf=aws, gcp_chf=gcp, our_chf=ours, revenue_per_server_h=per_sh))
    return rows


# ---- 2. redundancy tier -------------------------------------------------------------------------
def redundancy(price_sh):
    """Price of an r-site job vs what the same server-hours would earn otherwise. With spare
    capacity (the unsold share), an extra copy uses server-hours that run anyway on the heat
    permit and would earn nothing; when capacity is sold out, it displaces a full-price job."""
    out = []
    aws = v("aws_redundancy_multiplier")
    for r in (1, 2, 3, 4):
        mult = 1 + v("redundancy_markup_per_copy") * (r - 1)
        revenue = price_sh * mult
        out.append({"copies": r, "price_multiplier": round(mult, 2), "aws_multiplier": aws if r == 2 else None,
                    "revenue": round(revenue, 2), "server_h_used": r,
                    "margin_spare_capacity": round(revenue - price_sh, 2),
                    "margin_sold_out": round(revenue - price_sh * r, 2)})
    return out


# ---- 3./4. homeowner offer and billing ----------------------------------------------------------
def homeowner(ref):
    p = v("electricity_household_chf_kwh")
    cop = v("heat_pump_cop")
    hp_kwh = p / cop  # heat pump running cost per kWh of heat (case's heat value)
    served = ref["served_kwh"]
    elec_kwh = ref["run_server_h"]  # 1 kW servers: server-h = kWh
    rows = []
    for d in (0.0, 0.3, 0.5, 1.0):
        heat_price = hp_kwh * (1 - d)
        host_pays = served * heat_price
        rows.append({
            "discount": d, "heat_price_chf_kwh": round(heat_price, 4), "host_pays_chf": round(host_pays),
            "host_saves_chf": round(served * hp_kwh - host_pays),
            "host_share_of_server_power": round(host_pays / (elec_kwh * p), 3),
            "digitalheat_refund_chf": round(elec_kwh * p - host_pays),
        })
    # the case owner's own example: 1,500 CHF heating a year
    bill = v("owner_example_heating_chf_per_year")
    ten = [{"discount": d, "saved_per_year": bill * d, "saved_10y": bill * d * 10} for d in (0.3, 0.5)]
    # "host pays >= 50 % of the servers' power": the heat price that implies
    implied = 0.5 * p * elec_kwh / served
    return {"heat_pump_chf_per_kwh_heat": round(hp_kwh, 4), "served_kwh": served, "server_kwh": elec_kwh,
            "rows": rows, "owner_example": ten, "host_pays_half_heat_price": round(implied, 4),
            "host_pays_half_vs_heat_pump": round(implied / hp_kwh, 2)}


# ---- 5. investor view ---------------------------------------------------------------------------
def capex_per_server(cool=False, per_site=None):
    per_site = per_site or v("servers_per_site_typ")
    parts = {
        "server: 2x EPYC 9654, 512 GB DDR5, water cooling (prices_2026.json)": HW_CHF_PER_SERVER + _ram_delta(),
        "site install (tank, plumbing, controls, network) per server": v("site_install_chf") / per_site,
    }
    if cool:
        parts["dry cooler share"] = v("drycooler_kw_per_site") * v("drycooler_chf_per_kw") / per_site
    return parts


def unit_economics(f, price_sh, discount, sold_share=1.0, cool=False):
    """Annual cash flows per server for a site (or fleet) with yearly figures f."""
    n = f["servers"]
    per_site = f.get("servers_per_site") or v("servers_per_site_typ")
    p_host = v("electricity_household_chf_kwh")
    capex = sum(capex_per_server(cool, per_site).values())
    run_sh = f["run_server_h"] / n
    sold = run_sh * sold_share
    heat_kwh = f["served_kwh"] / n
    elec = (f["run_server_h"] + f.get("fan_kwh", 0)) / n * p_host  # all metered at the host tariff
    heat_income = heat_kwh * p_host / v("heat_pump_cop") * (1 - discount)  # host pays for heat used
    revenue = sold * price_sh * (1 - v("sales_and_payment_fees_share"))
    opex = capex * v("maintenance_share_of_capex") + v("ops_chf_per_server_year") + v("connectivity_chf_per_site_year") / per_site
    ebitda = revenue + heat_income - elec - opex
    payback = capex / ebitda if ebitda > 0 else None
    life = v("server_life_years")
    profit = ebitda - capex / life
    return {"capex": round(capex), "server_h": round(run_sh), "sold_server_h": round(sold), "revenue": round(revenue),
            "heat_income": round(heat_income), "electricity": round(elec), "opex": round(opex),
            "ebitda": round(ebitda), "payback_years": round(payback, 2) if payback else None,
            "profit_after_depreciation": round(profit),
            "break_even_price_sh": round((elec + opex + capex / life - heat_income) / (sold * (1 - v("sales_and_payment_fees_share"))), 3)}


def price_points():
    """Prices per server-hour we test, from the AWS comparators (CHF)."""
    od = ON_DEMAND_CHF_H
    spot = SPOT_CHF_H
    prem = v("compute_premium")
    return {
        "spot parity": round(spot, 2),
        "spot + premium (base case)": round(spot * (1 + prem), 2),
        "on-demand parity": round(od, 2),
        "on-demand + premium": round(od * (1 + prem), 2),
    }


RAM_DELTA = [0.0]  # CHF added to the server price for a RAM price sensitivity


def _ram_delta():
    return RAM_DELTA[0]


def ram_sensitivity(f, price_sh, discount):
    """prices_2026.json prices the server with 2026 memory (~USD 1,600 per 64 GB contract). Retail
    (USD 2,561) and early-2025 (~USD 380) RAM shift the server price by the difference for 512 GB."""
    out = {}
    gb = v("ram_gb_per_server")
    for label, key in (("early 2025", "ram_chf_per_gb_2025"), ("2026 contract (base)", "ram_chf_per_gb"),
                       ("retail Nov 2026", "ram_chf_per_gb_retail")):
        RAM_DELTA[0] = (v(key) - v("ram_chf_per_gb")) * gb
        u = unit_economics(f, price_sh, discount, v("sold_share_base"))
        out[label] = {"ram_chf": round(v(key) * gb), "capex": u["capex"],
                      "payback_years": u["payback_years"], "break_even_price_sh": u["break_even_price_sh"]}
    RAM_DELTA[0] = 0.0
    return out


def friend_example(base_price, house):
    usd = v("friend_aws_simulation_usd_per_year")
    per_sh = ON_DEMAND_CHF_H
    sh = chf(usd) / per_sh
    return {"aws_chf": round(chf(usd)), "server_h": round(sh), "servers_at_80pct": round(sh / (0.8 * 8760), 2),
            "our_price_chf": round(chf(usd) * (1 + v("compute_premium"))),
            "our_price_at_base_rate_chf": round(sh * base_price),
            "customers_per_house": round(house["sold_server_h"] * house_servers() / sh)}


def house_servers():
    from scheduler.sites import KINDS
    return REFERENCE[0].get("servers", KINDS["house"]["servers"])


def rollout(f, price_sh, discount, servers=1000, cool=False):
    u = unit_economics(f, price_sh, discount, v("sold_share_base"), cool)
    life = v("server_life_years")
    r = v("discount_rate")
    capex = u["capex"] * servers
    cash = u["ebitda"] * servers
    npv = -capex + sum(cash / (1 + r) ** (y + 1) for y in range(life))
    return {"servers": servers, "capex_chf": capex, "revenue_chf_y": u["revenue"] * servers,
            "ebitda_chf_y": cash, "payback_years": u["payback_years"], "npv_chf": round(npv),
            "sold_share": v("sold_share_base")}


def plot_payback(phys, discount):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PLOTS.mkdir(exist_ok=True)
    prices = [x / 20 for x in range(4, 201)]  # 0.2 .. 10 CHF per server-hour
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = {"reference house": "#c0653a", "services fleet": "#141412", "services fleet + dry cooler": "#5fa8b0"}
    for name, f in phys.items():
        cool = "dry cooler" in name
        ys = [unit_economics(f, p, discount, v("sold_share_base"), cool)["payback_years"] for p in prices]
        ax.plot(prices, [y if y and y < 10 else None for y in ys], color=colors[name], lw=2, label=name)
    for label, p in price_points().items():
        if p > 10:
            continue
        ax.axvline(p, color="#8a8577", lw=0.8, ls=":")
        ax.text(p, 9.6, label, rotation=90, fontsize=7, va="top", ha="right", color="#5a564c")
    ax.axhline(v("server_life_years"), color="#c0653a", lw=0.8, ls="--")
    ax.text(9.9, v("server_life_years") + 0.1, "server life", fontsize=7, ha="right", color="#c0653a")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xlabel("price per sold server-hour (CHF)")
    ax.set_ylabel("payback (years)")
    ax.set_title(f"Payback per server vs price, {int(v('sold_share_base') * 100)} % of server-hours sold, "
                 f"heat {int(discount * 100)} % below a heat pump", fontsize=10, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "payback_vs_price.png", dpi=150)
    plt.close(fig)


def fmt(x, d=0):
    return f"{x:,.{d}f}" if isinstance(x, (int, float)) else "–"


def report(R):
    L = ["# DigitalHeat business case (generated)", "",
         "`python3 scripts/business_case.py`. Inputs and sources: `data/prices_2026.json` (shared with the balance and "
         "the dashboard: exchange rate, AWS server-hour prices, Titan/Cohere, hardware) and `data/business_assumptions.json` "
         "(everything else). Physics: the "
         "scheduler's yearly balance (Basel 2025). Prices in CHF; USD converted at "
         f"{FX} CHF/USD. Every number below is reproducible; the ones marked *assumption* are ours.", ""]
    L += ["## 1. Service catalogue and prices", "",
          "Our price = the AWS list price for the same managed service × (1 + premium); Google shown for comparison. "
          "Revenue per server-hour = our price × units one 1 kW reference server does in an hour.", "",
          "| Service | Unit | AWS (CHF) | Google (CHF) | Premium | Our price (CHF) | Units per server-h | Revenue per server-h (CHF) |",
          "|---|---|---|---|---|---|---|---|"]
    for s in R["catalogue"]:
        L.append(f"| {s['name']} | {s['unit']} | {fmt(s['aws_chf'], 4) if s['aws_chf'] is not None else '–'} | "
                 f"{fmt(s['gcp_chf'], 4) if s['gcp_chf'] is not None else '–'} | +{int(s['premium'] * 100)} % | "
                 f"{fmt(s['our_chf'], 4)} | {fmt(s['units_per_server_h'])} | {fmt(s['revenue_per_server_h'], 2)} |")
    L += ["", "Managed-service prices per unit are far above the cost of the electricity behind them (0.33 CHF per "
          "server-hour), so price is not the constraint: how many units customers buy is. The investor view "
          "below therefore uses the much lower raw-compute comparator (AWS spot) as its base case.", ""]
    pp = R["price_points"]
    L += ["Raw-compute comparators for one 1 kW reference server (CHF per server-hour): " +
          ", ".join(f"{k} **{x:.2f}**" for k, x in pp.items()) + ".", ""]
    L += ["## 2. Redundancy tier", "",
          f"Price of a job run on r sites = base × (1 + {v('redundancy_markup_per_copy')} × (r − 1)), not r ×. "
          f"AWS charges {v('aws_redundancy_multiplier'):.0f}× for a Multi-AZ database, so two copies with us cost 25 % less than "
          f"AWS's redundancy. Base price {R['base_price']:.2f} CHF/server-h. The extra copies run on server-hours the heat permit "
          "allows anyway; while capacity is unsold (30 % in the base case, more in winter), they are almost pure margin.", "",
          "| Copies | Price × | Revenue per job-hour (CHF) | Server-h used | Extra margin, spare capacity | Extra margin, sold out |",
          "|---|---|---|---|---|---|"]
    for r in R["redundancy"]:
        L.append(f"| {r['copies']} | {r['price_multiplier']} | {r['revenue']:.2f} | {r['server_h_used']} | "
                 f"{r['margin_spare_capacity']:+.2f} | {r['margin_sold_out']:+.2f} |")
    L += ["", "So: sell the twin tier while there is spare capacity, and raise the markup (or stop selling it) once the "
          "fleet is sold out.", ""]
    h = R["homeowner"]
    L += ["", "## 3. Homeowner offer (reference house)", "",
          f"Heat pump running cost = electricity ÷ COP = {v('electricity_household_chf_kwh')} ÷ {v('heat_pump_cop')} = "
          f"**{h['heat_pump_chf_per_kwh_heat']:.4f} CHF per kWh of heat**. Server heat used: {h['served_kwh']:,} kWh/year; "
          f"server electricity: {h['server_kwh']:,} kWh/year.", "",
          "| Heat price | CHF/kWh heat | Host pays /yr | Host saves /yr vs heat pump | Host's share of the servers' power | DigitalHeat refunds /yr |",
          "|---|---|---|---|---|---|"]
    names = {0.0: "same as heat pump", 0.3: "30 % below heat pump", 0.5: "50 % below heat pump", 1.0: "free heat"}
    for r in h["rows"]:
        L.append(f"| {names[r['discount']]} | {r['heat_price_chf_kwh']:.4f} | {r['host_pays_chf']:,} | {r['host_saves_chf']:,} | "
                 f"{r['host_share_of_server_power'] * 100:.0f} % | {r['digitalheat_refund_chf']:,} |")
    L += ["", f"Case owner's example, heating bill {v('owner_example_heating_chf_per_year'):,.0f} CHF/year: " +
          "; ".join(f"{int(e['discount'] * 100)} % off saves {e['saved_per_year']:,.0f}/yr = **{e['saved_10y']:,.0f} CHF in 10 years**"
                    for e in R["homeowner"]["owner_example"]) + ".", "",
          f"Check of \"the host pays at least 50 % of the servers' power\": that means {h['host_pays_half_heat_price']:.3f} CHF per kWh "
          f"of heat, **{h['host_pays_half_vs_heat_pump']:.2f} × the heat pump's running cost**. A home would pay more than with a "
          "heat pump, so at household tariffs the host's share has to follow from the heat discount (16-22 %), not from a fixed 50 %.", ""]
    L += ["## 4. Billing flow", "",
          "1. The host's own meter pays all electricity, servers included (the meter belongs to the house).",
          "2. A sub-meter on the server rack measures the servers' kWh; a heat meter measures the heat delivered.",
          "3. Monthly, DigitalHeat refunds: server kWh × tariff − heat kWh × agreed heat price.",
          "4. Net for the host: they pay the heat price for the heat they used, nothing for the computing.", ""]
    L += ["## 5. Investor view", "", "Capex per server (CHF):", "", "| Item | CHF |", "|---|---|"]
    for k, x in R["capex"].items():
        L.append(f"| {k} | {x:,.0f} |")
    L.append(f"| **total** | **{sum(R['capex'].values()):,.0f}** |")
    L += ["", f"Annual cash flows per server at the base-case price ({R['base_price']:.2f} CHF/server-h), "
          f"{int(v('sold_share_base') * 100)} % of running server-hours sold, heat {int(R['discount'] * 100)} % below a heat pump:", "",
          "| Fleet | Server-h run | Sold | Revenue | Heat income | Electricity | Opex | EBITDA | Payback (yr) | Break-even price CHF/server-h |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, u in R["unit"].items():
        L.append(f"| {k} | {u['server_h']:,} | {u['sold_server_h']:,} | {u['revenue']:,} | {u['heat_income']:,} | {u['electricity']:,} | "
                 f"{u['opex']:,} | {u['ebitda']:,} | {fmt(u['payback_years'], 1)} | {u['break_even_price_sh']:.2f} |")
    L += ["", "Payback (years) by price and share of server-hours sold, services fleet:", "",
          "| Price CHF/server-h | " + " | ".join(f"{int(s * 100)} % sold" for s in R["grid_shares"]) + " |",
          "|---|" + "---|" * len(R["grid_shares"])]
    for p, row in R["grid"].items():
        L.append(f"| {p} | " + " | ".join(fmt(x, 1) if x else "never" for x in row) + " |")
    L += ["", "RAM price sensitivity (services fleet, base price):", "",
          "| RAM price | RAM per server (CHF) | Capex per server | Payback (yr) | Break-even CHF/server-h |", "|---|---|---|---|---|"]
    for k, x in R["ram"].items():
        L.append(f"| {k} | {x['ram_chf']:,} | {x['capex']:,} | {fmt(x['payback_years'], 1)} | {x['break_even_price_sh']:.2f} |")
    fr = R["friend"]
    L += ["", f"Case owner's example: a friend pays USD {v('friend_aws_simulation_usd_per_year'):,.0f}/yr (CHF {fr['aws_chf']:,}) "
          f"on AWS for simulations = {fr['server_h']:,} server-hours on our reference server = {fr['servers_at_80pct']} of one server "
          f"running 80 % of the year. At AWS + {int(v('compute_premium') * 100)} % he would pay CHF {fr['our_price_chf']:,}/yr; at our "
          f"base-case rate CHF {fr['our_price_at_base_rate_chf']:,}/yr. One reference house ({house_servers()} servers, 70 % sold) needs about {fr['customers_per_house']} such customers."]
    ro = R["rollout"]
    L += ["", f"Rollout of {ro['servers']:,} servers in services-type sites: capex {ro['capex_chf'] / 1e6:.1f} M CHF, "
          f"revenue {ro['revenue_chf_y'] / 1e6:.1f} M CHF/yr, EBITDA {ro['ebitda_chf_y'] / 1e6:.1f} M CHF/yr, payback "
          f"{fmt(ro['payback_years'], 1)} years, NPV over {v('server_life_years')} years at {int(v('discount_rate') * 100)} % "
          f"= {ro['npv_chf'] / 1e6:.1f} M CHF.", "",
          "**When it does not pay off:** below the break-even price per server-hour in the table, or when less than "
          "the break-even share of server-hours is sold (demand, not heat, is the risk), or when the heat is given "
          "away free (heat income lost, and waste: windows open at 26 °C). RAM at today's prices is the largest "
          "single capex item; see the sensitivity in docs/business-model.md.", ""]
    return "\n".join(L)


def main():
    phys = physics()
    discount = v("heat_discount_base")
    pp = price_points()
    base = pp["spot + premium (base case)"]
    cat = catalogue()
    unit = {k: unit_economics(f, base, discount, v("sold_share_base"), "dry cooler" in k) for k, f in phys.items()}
    shares = [0.25, 0.5, 0.75, 1.0]
    grid = {f"{p:.2f}": [unit_economics(phys["services fleet"], p, discount, s)["payback_years"] for s in shares]
            for p in sorted(set([0.5, 1.0, 1.5, 2.0, 3.0, 5.0] + [x for x in pp.values()]))}
    R = {"physics": {k: {kk: f[kk] for kk in ("servers", "coverage", "utilisation", "run_server_h", "served_kwh",
                                              "dumped_kwh", "fan_kwh")} for k, f in phys.items()},
         "catalogue": cat, "price_points": pp, "base_price": base, "discount": discount,
         "redundancy": redundancy(base), "homeowner": homeowner(phys["reference house"]),
         "capex": capex_per_server(), "unit": unit, "grid": grid, "grid_shares": shares,
         "rollout": rollout(phys["services fleet"], base, discount),
         "ram": ram_sensitivity(phys["services fleet"], base, discount), "friend": friend_example(base, unit["reference house"])}
    OUT.mkdir(exist_ok=True)
    (OUT / "business_case.json").write_text(json.dumps(R, indent=1, default=str))
    (OUT / "business_case.md").write_text(report(R))
    try:
        plot_payback(phys, discount)
    except ImportError:
        print("matplotlib missing: plot skipped (pip install matplotlib)")
    print(report(R))


if __name__ == "__main__":
    main()
