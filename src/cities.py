"""Hourly weather and heat demand of the reference house in several Swiss cities, 2025.

Idea: take the SAME reference house (same insulation, same formula as Basel)
and place it in different cities. Only the weather changes. This shows how
strongly heat demand depends on the local climate.

    from src.cities import load_cities
    df = load_cities()   # one row per city and hour

The demand itself is computed by src.load_data.add_heat_demand(), so the
formula lives in exactly one place. Note: the constant 25.6 (Basel's coldest
hour) is kept on purpose - the house is the same everywhere. In colder places
the demand therefore goes above 10 kW, which is what a real house would need.
"""

import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from src.load_data import ROOT, add_heat_demand, read_weather

CITY_DIR = ROOT / "data" / "raw" / "swiss_cities"

# name -> (latitude, longitude). City-centre coordinates, rounded to 2 decimals
# like the case's Basel point. Mix of lowland, lake, south and mountain climates.
CITIES = {
    "Basel": (47.56, 7.59),
    "Zürich": (47.37, 8.54),
    "Genève": (46.20, 6.14),
    "Bern": (46.95, 7.45),
    "Lausanne": (46.52, 6.63),
    "Luzern": (47.05, 8.31),
    "St. Gallen": (47.42, 9.37),
    "Winterthur": (47.50, 8.72),
    "Neuchâtel": (46.99, 6.93),
    "Fribourg": (46.81, 7.15),
    "La Chaux-de-Fonds": (47.10, 6.83),
    "Sion": (46.23, 7.36),
    "Lugano": (46.00, 8.95),
    "Chur": (46.85, 9.53),
    "Davos": (46.80, 9.84),
    "St. Moritz": (46.50, 9.84),
}

HOURLY_VARS = "temperature_2m,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance"


def city_file(name):
    """Path of the raw weather CSV of one city, e.g. data/raw/swiss_cities/openmeteo_st_gallen_2025_hourly.csv."""
    slug = (name.lower().replace("ü", "u").replace("è", "e").replace("â", "a")
            .replace(".", "").replace(" ", "_").replace("-", "_"))
    return CITY_DIR / f"openmeteo_{slug}_2025_hourly.csv"


def openmeteo_url(lat, lon):
    """Same request as the Basel reference file, only the coordinates change."""
    query = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "start_date": "2025-01-01", "end_date": "2025-12-31",
        "hourly": HOURLY_VARS, "timezone": "Europe/Zurich", "format": "csv",
    })
    return f"https://archive-api.open-meteo.com/v1/archive?{query}"


def download_cities(cities=CITIES, overwrite=False, pause_s=1.0):
    """Download the raw weather of every city that is not on disk yet."""
    CITY_DIR.mkdir(parents=True, exist_ok=True)
    for name, (lat, lon) in cities.items():
        path = city_file(name)
        if path.exists() and not overwrite:
            continue
        print(f"  downloading {name} ...")
        urllib.request.urlretrieve(openmeteo_url(lat, lon), path)
        time.sleep(pause_s)  # be polite to the free API


def read_city_meta(path):
    """Grid point that Open-Meteo actually used (it snaps to its model grid)."""
    meta = pd.read_csv(path, nrows=1)
    return {"grid_lat": float(meta.latitude[0]), "grid_lon": float(meta.longitude[0]),
            "elevation_m": float(meta.elevation[0])}


def load_cities(cities=CITIES):
    """Hourly table for all cities: the load_house() columns plus 'city'."""
    frames = []
    for name in cities:
        df = add_heat_demand(read_weather(city_file(name)))
        df.insert(0, "city", name)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def city_summary(df, cities=CITIES):
    """One row per city: location, coldest hour, heating days, annual and peak demand."""
    rows = []
    for name, d in df.groupby("city", sort=False):
        coldest = d.loc[d.temperature_2m.idxmin()]
        rows.append({
            "city": name,
            "lat": cities[name][0], "lon": cities[name][1],
            **read_city_meta(city_file(name)),
            "mean_temp_c": d.temperature_2m.mean(),
            "coldest_c": coldest.temperature_2m,
            "coldest_time": coldest.timestamp.strftime("%Y-%m-%d %H:%M"),
            "heating_days": int(d.groupby("date").heating_day.first().sum()),
            "space_kwh": d.space_kwh.sum(),
            "hot_water_kwh": d.hot_water_kwh.sum(),
            "demand_kwh": d.demand_kwh.sum(),
            "peak_kw": d.demand_kwh.max(),
        })
    return pd.DataFrame(rows)
