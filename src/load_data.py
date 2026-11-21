"""Shared loaders for the DigitalHeat reference house (Step 1).

Every later script should get its data from here, so the heat demand is
calculated in exactly one place:

    from src.load_data import load_house, load_price
    house = load_house()        # hourly table for 2025, one row per hour
    price = load_price()        # flat electricity price in CHF per kWh

Units: each row is one hour. A constant power of X kW over one hour is X kWh,
so the *_kwh columns can be read as kW (average power in that hour) as well.

All functions are pure: they only read the files you pass in (or the default
files in data/raw/) and return new objects. Nothing in data/ is modified.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
WEATHER_CSV = ROOT / "data" / "raw" / "openmeteo_basel_2025_hourly.csv"
PRICE_JSON = ROOT / "data" / "raw" / "elcom_iwb_H4_2025_2026.json"

# ---- Constants fixed by the DigitalHeat case (do not change) --------------
LOCAL_TZ = "Europe/Zurich"
DESIGN_POWER_KW = 10.0        # heating power at the coldest hour of 2025
INDOOR_C = 20.0               # base temperature in the formula
DESIGN_SPREAD_K = 25.6        # 20 - (-5.6); -5.6 degC is the coldest hour of 2025
HEATING_DAY_LIMIT_C = 12.0    # heating day if the daily mean temperature is below this
HOT_WATER_KWH_PER_DAY = 12.0  # spread flat: 0.5 kWh every hour
HEAT_PUMP_COP = 2.5           # case rule: heat value = electricity price / 2.5


def file_time_to_local(file_times, offset_s):
    """Open-Meteo fixed-offset clock labels -> UTC instants -> Europe/Zurich wall clock."""
    utc = (pd.to_datetime(file_times) - pd.Timedelta(seconds=offset_s)).dt.tz_localize("UTC")
    return utc.dt.tz_convert(LOCAL_TZ)


def read_weather(path=WEATHER_CSV):
    """Read the raw Open-Meteo CSV and return one row per hour.

    The file has 2 metadata lines and a blank line before the real header.
    The metadata says utc_offset_seconds=3600: Open-Meteo wrote every time
    as UTC+1 all year (no summer time). We therefore turn each time into a
    real instant (UTC) first and only then into Swiss wall-clock time.
    """
    path = Path(path)
    meta = pd.read_csv(path, nrows=1)
    offset_s = int(meta.loc[0, "utc_offset_seconds"])

    # Find the real header line ("time,...") instead of trusting a fixed number.
    with open(path, encoding="utf-8") as f:
        header_line = next(i for i, line in enumerate(f) if line.startswith("time,"))
    raw = pd.read_csv(path, skiprows=header_line, encoding="utf-8")

    # Clean column names: "temperature_2m (°C)" -> "temperature_2m", etc.
    raw = raw.rename(columns=lambda c: c.split(" (")[0])

    weather = raw.drop(columns="time")
    weather.insert(0, "timestamp", file_time_to_local(raw["time"], offset_s))
    weather.insert(1, "file_time_utc_plus_1", raw["time"])  # label as written in the file
    return weather


def add_heat_demand(weather, day_definition="wall_clock", design_spread_k=DESIGN_SPREAD_K):
    """Add heating-day flag and hourly demand to a weather table.

    day_definition:
      "wall_clock"  (default, the case rule) - a day is a Europe/Zurich calendar
                    day. On the two clock-change days it has 23 or 25 hours, and
                    the daily mean is taken over the hours that day really has.
      "file_clock"  - a day is a calendar day of the file's UTC+1 clock (always
                    24 hours). Only used to explain differences to the old
                    reference CSV, which was built that way.
    design_spread_k: 20 minus the design (coldest) temperature. Default 25.6 is the
                    case constant (Basel 2025). Other places can pass their own value.
    """
    df = weather.copy()
    if day_definition == "wall_clock":
        df["date"] = df["timestamp"].dt.date
    elif day_definition == "file_clock":
        df["date"] = pd.to_datetime(df["file_time_utc_plus_1"]).dt.date
    else:
        raise ValueError(f"unknown day_definition: {day_definition!r}")

    day = df.groupby("date")["temperature_2m"]
    df["hours_in_day"] = day.transform("size")
    df["day_mean_temperature_2m"] = day.transform("mean")
    df["heating_day"] = df["day_mean_temperature_2m"] < HEATING_DAY_LIMIT_C

    # Space heating: linear in outdoor temperature, only on heating days.
    space = (DESIGN_POWER_KW * (INDOOR_C - df["temperature_2m"]) / design_spread_k).clip(lower=0)
    df["space_kwh"] = space.where(df["heating_day"], 0.0)

    # Hot water: 12 kWh per day, flat over 24 hours = 0.5 kWh every hour.
    df["hot_water_kwh"] = HOT_WATER_KWH_PER_DAY / 24
    df["demand_kwh"] = df["space_kwh"] + df["hot_water_kwh"]
    return df


def load_house(weather_path=WEATHER_CSV, day_definition="wall_clock"):
    """Return the finished hourly table of the reference house, Basel 2025.

    Columns:
      timestamp                start of the hour, tz-aware Europe/Zurich
      file_time_utc_plus_1     the same hour as labelled in the Open-Meteo file
      date                     local calendar day the hour belongs to
      temperature_2m           outdoor temperature, degC
      shortwave_radiation      global horizontal irradiance, W/m2 (solar stretch goal)
      direct_radiation, diffuse_radiation, direct_normal_irradiance   W/m2
      hours_in_day             23, 24 or 25 (clock-change days)
      day_mean_temperature_2m  mean temperature of that local day, degC
      heating_day              True if day mean < 12 degC
      space_kwh                space-heating demand in this hour (= kW)
      hot_water_kwh            hot-water demand in this hour (= kW), always 0.5
      demand_kwh               space_kwh + hot_water_kwh
    """
    return add_heat_demand(read_weather(weather_path), day_definition=day_definition)


def load_price_record(price_path=PRICE_JSON, period="2026", municipality="Basel", category="H4"):
    """Return the one ElCom observation (dict) for IWB, Basel, H4, 2026.

    Values in the file are in Rappen per kWh (Rp/kWh); 100 Rp = 1 CHF.
    """
    with open(price_path, encoding="utf-8") as f:
        observations = json.load(f)["data"]["observations"]
    matches = [
        o for o in observations
        if o["period"] == period and o["municipalityLabel"] == municipality and o["category"] == category
    ]
    if len(matches) != 1:
        raise ValueError(f"expected 1 price record for {period}/{municipality}/{category}, found {len(matches)}")
    return matches[0]


def load_price(price_path=PRICE_JSON):
    """Flat electricity price in CHF per kWh: ElCom 'total' for 2026, IWB, Basel, H4.

    'total' is ElCom's all-in price (grid, metering, energy, public charges,
    federal surcharge). It is given in Rp/kWh, so we divide by 100.
    """
    return load_price_record(price_path)["total"] / 100


def heat_value_chf_per_kwh(price_chf_per_kwh, cop=HEAT_PUMP_COP):
    """Value of 1 kWh of heat: the electricity a heat pump (COP 2.5) would need."""
    return price_chf_per_kwh / cop
