"""Rebuild the DigitalHeat reference-house hourly profile from Open-Meteo weather.

Stand-in for the "ready hourly profile" CSV the case says is provided but which
was not linked on the case page (asked in the case Q&A, 2026-11-20). Only the
case's own definitions are applied here; see docs/case-brief.md#reference-house.

Usage:
    python3 scripts/build_reference_profile.py            # uses data/raw/ copy
    python3 scripts/build_reference_profile.py --download # re-fetch weather first
"""

import argparse
import csv
import urllib.request
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "openmeteo_basel_2025_hourly.csv"
OUT = ROOT / "data" / "reference_house_2025_hourly.csv"

OPEN_METEO_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=47.56&longitude=7.59&start_date=2025-01-01&end_date=2025-12-31"
    "&hourly=temperature_2m,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance"
    "&timezone=Europe%2FZurich&format=csv"
)

# Case constants
DESIGN_POWER_KW = 10.0      # heating power on the coldest hour
INDOOR_C = 20.0             # base temperature in the formula
DESIGN_SPREAD_K = 25.6      # 20 - (-5.6), coldest hour of 2025
HEATING_DAY_MEAN_C = 12.0   # day is a heating day if its 24h mean is below this
HOT_WATER_KWH_PER_DAY = 12.0


def load_weather(path):
    with open(path, newline="") as f:
        lines = list(csv.reader(f))
    # Open-Meteo CSV: 2 metadata lines, a blank line, then the hourly header.
    header_idx = next(i for i, r in enumerate(lines) if r and r[0] == "time")
    return lines[header_idx + 1 :]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="re-fetch weather from Open-Meteo")
    args = ap.parse_args()

    if args.download:
        RAW.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(OPEN_METEO_URL, RAW)

    rows = [r for r in load_weather(RAW) if r]
    temps = [float(r[1]) for r in rows]

    by_day = OrderedDict()
    for r, t in zip(rows, temps):
        by_day.setdefault(r[0][:10], []).append(t)
    day_mean = {d: sum(v) / len(v) for d, v in by_day.items()}

    hot_water_kwh_per_hour = HOT_WATER_KWH_PER_DAY / 24

    out_rows = []
    for r, t in zip(rows, temps):
        day = r[0][:10]
        heating_day = day_mean[day] < HEATING_DAY_MEAN_C
        space = max(0.0, DESIGN_POWER_KW * (INDOOR_C - t) / DESIGN_SPREAD_K) if heating_day else 0.0
        out_rows.append([
            r[0], t, r[2], r[3], r[4], r[5],
            round(day_mean[day], 3), int(heating_day),
            round(space, 4), round(hot_water_kwh_per_hour, 4),
            round(space + hot_water_kwh_per_hour, 4),
        ])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "time_local", "temperature_2m_c", "shortwave_radiation_w_m2",
            "direct_radiation_w_m2", "diffuse_radiation_w_m2", "direct_normal_irradiance_w_m2",
            "day_mean_temperature_c", "heating_day",
            "space_heating_kwh", "hot_water_kwh", "total_heat_demand_kwh",
        ])
        w.writerows(out_rows)

    space_total = sum(r[8] for r in out_rows)
    hw_total = sum(r[9] for r in out_rows)
    n_heat_days = sum(1 for m in day_mean.values() if m < HEATING_DAY_MEAN_C)
    coldest = min(temps)
    print(f"hours:              {len(out_rows)}")
    print(f"coldest hour:       {coldest} °C (case: -5.6)")
    print(f"heating days:       {n_heat_days} (case: 206)")
    print(f"space heating:      {space_total:,.0f} kWh (case: about 27,000)")
    print(f"hot water:          {hw_total:,.0f} kWh")
    print(f"total heat demand:  {space_total + hw_total:,.0f} kWh")
    print(f"peak hourly demand: {max(r[10] for r in out_rows):.2f} kWh")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
