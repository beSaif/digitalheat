"""Fit a heat-demand model to the real Basel city house (4 apartments, gas bills 2021–2025).

    python3 scripts/calibrate_city_house.py      # writes data/city_house_model.json

Model, per hour (same heating-day rule as the case):
    heat = base_kw + k_kw_per_K × max(0, 20 − T)   on heating days (day mean < 12 °C)
    heat = base_kw                                  otherwise
Fitted by least squares on monthly gas (MESSPUNKT_004) × boiler efficiency, against
Basel's hourly temperature from the Open-Meteo archive for the same months.
Months October 2022 to September 2023 are left out (far below every other year, cause
unknown, see data/README.md). Boiler efficiency 0.90 is our assumption: the data has none.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scheduler.weather import BASEL, temperatures  # noqa: E402

GAS = ROOT / "data" / "raw" / "city_house" / "Data_Gas_2021-2026_anonymisiert.csv"
OUT = ROOT / "data" / "city_house_model.json"
EFFICIENCY = 0.90
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def monthly_gas():
    out = {}
    with open(GAS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["Messpunkt CH"] == "MESSPUNKT_004" and r["Ableseeinheit"] == "KWH":
                ym = r["Zeitraum (KalJahr/Monat)"]
                out[(int(ym[:4]), int(ym[4:]))] = float(r["Verbrauch Medium Einfachtarif (kWh/m3)"])
    return out


def month_features(temps):
    """Hours and heating degree-hours per month (365-day year)."""
    hours, hdh = [0] * 12, [0.0] * 12
    d = 0
    for m, n in enumerate(MONTH_DAYS):
        for _ in range(n):
            day = temps[d * 24:(d + 1) * 24]
            heating = sum(day) / 24 < 12
            hours[m] += 24
            if heating:
                hdh[m] += sum(max(0.0, 20 - t) for t in day)
            d += 1
    return hours, hdh


def main():
    gas = monthly_gas()
    rows = []
    for year in range(2021, 2026):
        hours, hdh = month_features(temperatures(*BASEL, year))
        for m in range(12):
            g = gas.get((year, m + 1))
            if g is None or (2022, 10) <= (year, m + 1) <= (2023, 9):
                continue
            if year % 4 == 0 and m == 1:
                g *= 28 / 29  # our year drops 29 Feb
            rows.append((year, m + 1, hours[m], hdh[m], g * EFFICIENCY))
    # least squares: heat = base * hours + k * hdh
    sxx = sum(h * h for _, _, h, _, _ in rows)
    sxy = sum(h * d for _, _, h, d, _ in rows)
    syy = sum(d * d for _, _, _, d, _ in rows)
    sxz = sum(h * z for _, _, h, _, z in rows)
    syz = sum(d * z for _, _, _, d, z in rows)
    det = sxx * syy - sxy * sxy
    base = (sxz * syy - syz * sxy) / det
    k = (syz * sxx - sxz * sxy) / det
    pred = [base * h + k * d for _, _, h, d, _ in rows]
    obs = [z for *_, z in rows]
    mean = sum(obs) / len(obs)
    r2 = 1 - sum((o - p) ** 2 for o, p in zip(obs, pred)) / sum((o - mean) ** 2 for o in obs)
    model = {
        "what": "Basel city house, 4 apartments: heat = base_kw + k_kw_per_K x max(0, 20 - T) on heating days",
        "base_kw": round(base, 4),
        "k_kw_per_K": round(k, 4),
        "boiler_efficiency": EFFICIENCY,
        "months_used": len(rows),
        "r2_monthly": round(r2, 3),
        "excluded": "2022-10 to 2023-09 (anomalously low, cause unknown)",
        "source": "data/raw/city_house/Data_Gas_2021-2026_anonymisiert.csv (MESSPUNKT_004), Basel Open-Meteo archive",
        "generator": "scripts/calibrate_city_house.py",
    }
    OUT.write_text(json.dumps(model, indent=1) + "\n")
    print(json.dumps(model, indent=1))
    ref_k = 10 / 25.6
    print(f"reference house: base 0.5 kW, k {ref_k:.4f} kW/K  ->  city house = x{k / ref_k:.2f} heating, x{base / 0.5:.1f} hot water")


if __name__ == "__main__":
    main()
