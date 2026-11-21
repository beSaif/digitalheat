"""Every assumption behind the key figures, in one list, built from the live constants.

    python3 -m scheduler.assumptions          # print
    python3 -m scheduler.assumptions --md     # write docs/assumptions.md
    python3 -m scheduler.assumptions --json   # for the dashboard

kind: "case" (given by DigitalHeat), "measured" (by us), "sourced" (public source), "ours" (our choice).
"""

import json
import sys
from pathlib import Path

from scheduler import core, pricing, sites
from scheduler.balance import electricity_price

ROOT = Path(__file__).resolve().parent.parent


def a(kind, name, value, source, url=None, file=None):
    return {"kind": kind, "name": name, "value": value, "source": source, "url": url, "file": file}


def build():
    e = electricity_price()
    P = pricing.P
    m = json.loads((ROOT / "data" / "measurements" / "combined.json").read_text())["jobs"]
    from workloads.catalog import JOB_DEFAULTS
    types = core.job_types()
    city = json.loads((ROOT / "data" / "city_house_model.json").read_text())
    return [
        # given by the case
        a("case", "Server power", "1 kW in, 1 kW heat", "Case brief"),
        a("case", "Heat recovered", f"{core.REC:.0%}", "Case brief"),
        a("case", "Weather", "Basel 47.56 N 7.59 E, 2025, hourly", "Open-Meteo archive",
          "https://open-meteo.com/en/docs/historical-weather-api", "data/reference_house_2025_hourly.csv"),
        a("case", "Heating demand", "10 kW × (20 − T) ÷ 25.6 on days below 12 °C", "Case brief", None,
          "data/reference_house_2025_hourly.csv"),
        a("case", "Hot water", "12 kWh per day, all year", "Case brief"),
        a("case", "Tank", f"{sites.KINDS['house']['tank_kwh']} kWh, no losses", "Case brief"),
        a("case", "Electricity", f"CHF {e:.4f} / kWh", "ElCom 2026, IWB Basel, H4", "https://www.strompreis.elcom.admin.ch",
          "data/raw/elcom_iwb_H4_2025_2026.json"),
        a("case", "Value of heat", f"CHF {e / 2.5:.4f} / kWh", "Electricity ÷ 2.5 (heat pump)"),
        # measured by us
        a("measured", "Embed energy", f"{m['embed']['gross_j_per_item']:.3f} J per abstract",
          "3 laptops (M1, M3, M4), battery gauge", None, "data/measurements/combined.json"),
        a("measured", "Rerank energy", f"{m['rerank']['gross_j_per_item']:.3f} J per pair",
          "3 laptops (M1, M3, M4), battery gauge", None, "data/measurements/combined.json"),
        a("measured", "Embed job", f"{types['embed'].sh:.2f} server-h", "10M abstracts, scaled to 1 kW", None, "workloads/catalog.py"),
        a("measured", "Rerank job", f"{types['rerank'].sh:.2f} server-h", "5M pairs, scaled to 1 kW", None, "workloads/catalog.py"),
        a("measured", "Tokens per abstract", f"{P['tokens_per_abstract']['value']}", "SciFact, MiniLM tokenizer", None,
          "data/prices_2026.json"),
        a("measured", "City house", f"{city['base_kw']:.2f} kW + {city['k_kw_per_K']:.3f} kW/K (R² {city['r2_monthly']:.2f})",
          "Fit to Basel gas bills", None, "scripts/calibrate_city_house.py"),
        # public sources
        a("sourced", "Reference server", P["reference_server"]["value"], "1.0–1.2 kW at the wall, ServeTheHome",
          P["reference_server"]["url"], "data/prices_2026.json"),
        a("sourced", "AWS spot", f"CHF {pricing.SPOT_CHF_H:.2f} / server-h", "c7a.48xlarge, Frankfurt",
          P["cloud_same_server"]["url"], "data/prices_2026.json"),
        a("sourced", "AWS on-demand", f"CHF {pricing.ON_DEMAND_CHF_H:.2f} / server-h", "c7a.48xlarge, Frankfurt",
          P["cloud_same_server"]["url"], "data/prices_2026.json"),
        a("sourced", "AWS embeddings", "USD 0.02 / 1M tokens", "Titan Text Embeddings V2", P["managed_services"]["embed"]["url"]),
        a("sourced", "AWS rerank", "USD 2 / 1,000 queries", "Cohere Rerank 3.5 on Bedrock", P["managed_services"]["rerank"]["url"]),
        a("sourced", "USD → CHF", f"{pricing.FX}", "Mid-market, Nov 2026", P["usd_chf"]["url"]),
        a("sourced", "Hospital hot water", f"{sites.HOSP_DHW_PER_BED:,.0f} kWh per bed and year", "Hospital DHW study", None, "scheduler/sites.py"),
        a("sourced", "Pool water", f"{sites.POOL_WATER:,.0f} kWh per m² and year", "Passive House pool guide (400–700)", None, "scheduler/sites.py"),
        a("sourced", "Greenhouse", f"{sites.GREENHOUSE_PER_M2:,.0f} kWh per m² and year", "Wageningen, Dutch average 306–334",
          "https://edepot.wur.nl/452684", "scheduler/sites.py"),
        # our choices
        a("ours", "Selling price", "AWS spot", "Jobs pause like spot capacity: the cautious price", None, "data/prices_2026.json"),
        a("ours", "Every running hour is sold", "yes", "Embed backlog is unlimited", None, "workloads/catalog.py"),
        a("ours", "Server price", f"CHF {pricing.HW_CHF_PER_SERVER:,.0f}, {pricing.HW_YEARS} years",
          "Listed at CHF 19,300, plus 2026 memory prices and water cooling", P["hardware"]["url"], "data/prices_2026.json"),
        a("ours", "Servers per house", f"{sites.KINDS['house']['servers']}", "From the sweep 1–12", None, "scheduler/balance.py"),
        a("ours", "Embed deadline", f"{JOB_DEFAULTS['embed']['deadline_h']:.0f} h", "Batch indexing", None, "workloads/catalog.py"),
        a("ours", "Rerank deadline", f"{JOB_DEFAULTS['rerank']['deadline_h']:.0f} h", "Same-day evaluation", None, "workloads/catalog.py"),
        a("ours", "Rerank jobs", "4 per day (08, 11, 14, 17 h)", "Our assumption, swept 1 / 4 / 16", None, "workloads/catalog.py"),
        a("ours", "Weather forecast", "perfect", "The real weather is the forecast", None, "scheduler/core.py"),
        a("ours", "Pause or checkpoint", f"pause if heat returns within {core.RESUME_SOON_H} h", "Keeps memory, no lost work",
          None, "scheduler/core.py"),
        a("ours", "Look-ahead", f"{core.HORIZON} h", "Deadline reserve", None, "scheduler/core.py"),
    ]


LABEL = {"case": "Given by the case", "measured": "Measured by us", "sourced": "Public source", "ours": "Our choice"}


def markdown(rows):
    out = ["# Assumptions", "", "Generated by `python3 -m scheduler.assumptions --md`. Do not edit by hand.", ""]
    for k, lab in LABEL.items():
        out += [f"## {lab}", "", "| | Value | Source |", "|---|---|---|"]
        for r in rows:
            if r["kind"] != k:
                continue
            src = f"[{r['source']}]({r['url']})" if r["url"] else r["source"]
            if r["file"]:
                src += f" · [`{r['file']}`](../{r['file']})"
            out.append(f"| {r['name']} | {r['value']} | {src} |")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    rows = build()
    if "--json" in sys.argv:
        print(json.dumps(rows))
    elif "--md" in sys.argv:
        (ROOT / "docs" / "assumptions.md").write_text(markdown(rows))
        print("wrote docs/assumptions.md")
    else:
        for r in rows:
            print(f"{r['kind']:<9}{r['name']:<28}{r['value']}")
