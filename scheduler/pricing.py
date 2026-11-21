"""Computing income: what one server-hour and one job sell for, from data/prices_2026.json.

The reference server (1 kW) is a dual AMD EPYC 9654 box, the same chips and power as
AWS c7a.48xlarge. So one server-hour sold by DigitalHeat is compared with one hour of
that instance (spot and on-demand), and each job with the managed AWS service doing the
same work (Titan embeddings, Cohere rerank).

    python3 -m scheduler.pricing
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = json.loads((ROOT / "data" / "prices_2026.json").read_text())

FX = P["usd_chf"]["value"]
SPOT_CHF_H = round(P["cloud_same_server"]["spot_usd_h"] * FX, 3)
ON_DEMAND_CHF_H = round(P["cloud_same_server"]["on_demand_usd_h"] * FX, 3)
HW_CHF_PER_SERVER = float(P["hardware"]["chf_per_server"])
HW_YEARS = int(P["hardware"]["years"])
SELL_CHF_H = SPOT_CHF_H  # default selling price, see prices_2026.json "sell_price"


def job_prices(types):
    """Per job type: server-hours, and what the job costs at spot, on-demand and as an AWS managed service (CHF)."""
    from workloads.catalog import JOB_DEFAULTS

    ms = P["managed_services"]
    out = {}
    for k, t in types.items():
        if k not in JOB_DEFAULTS:  # sim, twin: priced per server-hour only, no managed-service equivalent
            out[k] = {"items": None, "server_h": round(t.sh, 4), "spot_chf": round(t.sh * SPOT_CHF_H, 2),
                      "on_demand_chf": round(t.sh * ON_DEMAND_CHF_H, 2), "service_chf": None, "service": None}
            continue
        items = JOB_DEFAULTS[k]["items_per_job"]
        if k == "embed":
            service_usd = items * P["tokens_per_abstract"]["value"] / 1e6 * ms["embed"]["usd"]
        else:
            service_usd = items / P["rerank_docs_per_query"]["value"] / 1000 * ms["rerank"]["usd"]
        out[k] = {
            "items": items,
            "server_h": round(t.sh, 4),
            "spot_chf": round(t.sh * SPOT_CHF_H, 2),
            "on_demand_chf": round(t.sh * ON_DEMAND_CHF_H, 2),
            "service_chf": round(service_usd * FX, 2),
            "service": ms[k]["service"],
        }
    return out


def pays_off(f, elec_price, heat_value, sell=SELL_CHF_H, hw_chf=HW_CHF_PER_SERVER):
    """Where this site or fleet stops paying off, holding everything else as it is.

    profit per year = hours sold x sell price - electricity + heat value - hardware
    """
    h, n = f["run_server_h"], f["servers"]
    if not h or not n:
        return None
    hw = n * hw_chf / HW_YEARS
    profit = h * sell - f["electricity_chf"] + f["heat_value_chf"] - hw
    used = f["served_kwh"] / h  # heat used per server-hour sold (kWh)
    margin = sell - elec_price + used * heat_value  # CHF per server-hour before hardware
    return {
        "sell_chf_per_server_h": sell,
        "income_chf": round(h * sell, 2),
        "profit_chf": round(profit, 2),
        "pays_off": profit > 0,
        # each threshold: the model loses money beyond it
        "min_price_chf_per_server_h": round((f["electricity_chf"] - f["heat_value_chf"] + hw) / h, 3),
        "min_utilisation": round(hw / n / (8760 * margin), 4) if margin > 0 else None,
        # heat value moves with the electricity price (price / 2.5), so solve profit = 0 for the price
        "max_electricity_chf_kwh": round((h * sell - hw) / (h - f["served_kwh"] * heat_value / elec_price), 3),
        "max_hardware_chf_per_server": round((h * margin) * HW_YEARS / n),
    }


if __name__ == "__main__":
    from scheduler.core import job_types

    print(f"1 server-hour: AWS spot CHF {SPOT_CHF_H}, on-demand CHF {ON_DEMAND_CHF_H} (c7a.48xlarge, Frankfurt)")
    print(f"{'job':<8}{'server-h':>9}{'spot':>8}{'on-dem.':>9}{'AWS service':>13}")
    for k, v in job_prices(job_types()).items():
        print(f"{k:<8}{v['server_h']:>9.2f}{v['spot_chf']:>8.2f}{v['on_demand_chf']:>9.2f}{v['service_chf']:>13.2f}")
