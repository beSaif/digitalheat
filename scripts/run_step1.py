"""Step 1: build, compare and check the reference-house heat demand; read the price; plot.

Run from the repository root:
    python3 scripts/run_step1.py

Writes (never touches data/):
    outputs/house_2025_hourly.csv   the finished hourly table
    plots/demand_week_january.png   13-19 Jan 2025
    plots/demand_week_july.png      14-20 Jul 2025
Exits with an error if any sanity check fails.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from src.load_data import (
    HEAT_PUMP_COP, LOCAL_TZ, heat_value_chf_per_kwh, load_house, load_price, load_price_record,
)

ANSWER_KEY = ROOT / "data" / "reference_house_2025_hourly.csv"
OUT_CSV = ROOT / "outputs" / "house_2025_hourly.csv"
PLOTS = ROOT / "plots"
TOL = 1e-3  # the answer key is rounded to 4 decimals


def heading(text):
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


# ---------------------------------------------------------------- Part 1
def part1_build():
    heading("PART 1: hourly table from raw Open-Meteo weather")
    house = load_house()
    per_day = house.groupby("date").size()
    print(f"rows: {len(house)}  first: {house.timestamp.iloc[0]}  last: {house.timestamp.iloc[-1]}")
    print(f"hours per local day: {per_day.value_counts().sort_index().to_dict()}")
    for d, n in per_day[per_day != 24].items():
        labels = house.loc[house.date == d, "timestamp"].dt.strftime("%H:%M%z").tolist()
        print(f"  {d}: {n} hours -> {labels[:5]} ...")
    OUT_CSV.parent.mkdir(exist_ok=True)
    out = house.copy()
    out["timestamp"] = out["timestamp"].map(lambda t: t.isoformat())
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV.relative_to(ROOT)}")
    return house


# ---------------------------------------------------------------- Part 2
def part2_compare(house):
    heading("PART 2: compare with data/reference_house_2025_hourly.csv")
    key = pd.read_csv(ANSWER_KEY).add_prefix("key_")
    # The key's time_local is the same UTC+1 label as the weather file, so we join on it.
    m = house.merge(key, left_on="file_time_utc_plus_1", right_on="key_time_local", how="outer", indicator=True)
    print(f"rows ours: {len(house)}, key: {len(key)}, matched one-to-one: {(m._merge == 'both').sum()}")

    pairs = [
        ("temperature_2m", "key_temperature_2m_c"),
        ("shortwave_radiation", "key_shortwave_radiation_w_m2"),
        ("heating_day", "key_heating_day"),
        ("space_kwh", "key_space_heating_kwh"),
        ("hot_water_kwh", "key_hot_water_kwh"),
        ("demand_kwh", "key_total_heat_demand_kwh"),
    ]
    rows = []
    for ours, theirs in pairs:
        o, t = m[ours].astype(float), m[theirs].astype(float)
        d = (o - t).abs()
        rows.append([ours, theirs, d.max(), int((d > TOL).sum()), o.sum(), t.sum(),
                     100 * (o.sum() - t.sum()) / t.sum()])
    table = pd.DataFrame(rows, columns=["ours", "key", "max_abs_diff", "hours_diff",
                                        "sum_ours", "sum_key", "diff_%"])
    print(table.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))

    differing = m[(m.space_kwh - m.key_space_heating_kwh).abs() > TOL]
    if len(differing):
        print("\nHours where space heating differs. Ours: Swiss wall-clock day; key: UTC+1 file day.")
        cols = ["timestamp", "file_time_utc_plus_1", "temperature_2m", "date", "heating_day",
                "key_heating_day", "space_kwh", "key_space_heating_kwh"]
        print(differing[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # Proof of cause: with the key's own day definition we must match exactly.
    same_rule = load_house(day_definition="file_clock")
    d = (same_rule["demand_kwh"].values - key["key_total_heat_demand_kwh"].values).__abs__().max()
    print(f"\nWith UTC+1 file days instead of wall-clock days, max abs diff to key = {d:.5f} kWh "
          f"(key is rounded to 4 decimals)")
    return table


# ---------------------------------------------------------------- Part 3
def part3_checks(house):
    heading("PART 3: sanity checks")
    utc = house["timestamp"].dt.tz_convert("UTC")
    daily = house.groupby("date")["heating_day"].first()
    july = house[house["timestamp"].dt.month == 7]
    space, total = house["space_kwh"].sum(), house["demand_kwh"].sum()
    peak, low = house["demand_kwh"].max(), house["demand_kwh"].min()

    checks = [
        ("8,760 rows", len(house) == 8760, f"{len(house)} rows"),
        ("space heating 27,000 +/- 500 kWh", abs(space - 27000) <= 500, f"{space:,.0f} kWh"),
        ("exactly 206 heating days", daily.sum() == 206, f"{daily.sum()} days"),
        ("total demand ~31,400 kWh (+/- 500)", abs(total - 31400) <= 500, f"{total:,.0f} kWh"),
        ("hot water 4,380 kWh", abs(house["hot_water_kwh"].sum() - 4380) < 1e-6,
         f"{house['hot_water_kwh'].sum():,.0f} kWh"),
        ("peak demand ~10.5 kW (+/- 0.1)", abs(peak - 10.5) <= 0.1, f"{peak:.3f} kW"),
        ("minimum demand 0.5 kW", abs(low - 0.5) < 1e-9, f"{low:.3f} kW"),
        ("no missing values", not house.isna().any().any(), f"{int(house.isna().sum().sum())} missing"),
        ("timestamps sorted", utc.is_monotonic_increasing, "checked in UTC"),
        ("timestamps strictly hourly", (utc.diff().dropna() == pd.Timedelta(hours=1)).all(),
         "every step = 1 h in UTC"),
        ("timestamps in Europe/Zurich", str(house["timestamp"].dt.tz) == LOCAL_TZ, str(house["timestamp"].dt.tz)),
        ("July flat at 0.5 kW", (july["demand_kwh"] == 0.5).all(),
         f"July min {july['demand_kwh'].min()}, max {july['demand_kwh'].max()}"),
    ]
    width = max(len(c[0]) for c in checks)
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    failed = [c[0] for c in checks if not c[1]]
    assert not failed, f"Sanity checks failed: {failed}. Stop and investigate before continuing."
    print("All sanity checks passed.")


# ---------------------------------------------------------------- Part 4
def part4_price():
    heading("PART 4: electricity price (ElCom 2026, IWB, Basel, H4)")
    rec = load_price_record()
    parts = ["gridusage", "energy", "charge", "aidfee"]
    for k in parts + ["total"]:
        print(f"  {k:<10} {rec[k]:>7.3f} Rp/kWh")
    gap = rec["total"] - sum(rec[k] for k in parts)
    print(f"  total - sum of listed parts = {gap:.3f} Rp/kWh (no field in the JSON; the ElCom web page "
          f"lists a metering tariff of 1.20 Rp/kWh, see data/README.md)")
    price = load_price()
    heat = heat_value_chf_per_kwh(price)
    print(f"\n  electricity price: {price:.4f} CHF/kWh")
    print(f"  heat value (/{HEAT_PUMP_COP}): {heat:.4f} CHF per kWh of heat")
    return price, heat


# ---------------------------------------------------------------- Part 5 plots
def plot_week(house, start, end, title, path, ymax):
    week = house[(house["timestamp"] >= pd.Timestamp(start, tz=LOCAL_TZ))
                 & (house["timestamp"] < pd.Timestamp(end, tz=LOCAL_TZ))]
    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    ax.plot(week["timestamp"].dt.tz_localize(None), week["demand_kwh"], color="#2a78d6", linewidth=2)
    ax.set_ylim(0, ymax)
    ax.set_title(title, loc="left", color="#0b0b0b", fontsize=12)
    ax.set_ylabel("Heat demand (kW = kWh per hour)", color="#52514e")
    ax.set_xlabel("Local time, Europe/Zurich", color="#52514e")
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d %b"))
    ax.grid(axis="y", color="#e1e0d9", linewidth=0.8)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#898781")
    ax.tick_params(colors="#52514e", length=0)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  wrote {path.relative_to(ROOT)}: min {week.demand_kwh.min():.2f}, max {week.demand_kwh.max():.2f} kW")


def part5_plots(house):
    heading("PART 5: plots")
    PLOTS.mkdir(exist_ok=True)
    ymax = 11  # same y-axis on both plots
    plot_week(house, "2025-01-13", "2025-01-20",
              "Reference house, hourly heat demand, 13-19 January 2025 (space heating + hot water)",
              PLOTS / "demand_week_january.png", ymax)
    plot_week(house, "2025-07-14", "2025-07-21",
              "Reference house, hourly heat demand, 14-20 July 2025 (hot water only)",
              PLOTS / "demand_week_july.png", ymax)


if __name__ == "__main__":
    house = part1_build()
    part2_compare(house)
    part3_checks(house)
    part4_price()
    part5_plots(house)
