"""Switzerland-wide point set: locations, coordinates, cached 2025 hourly weather, heat demand.

Pipeline (each step caches its raw download in data/raw/ and never re-downloads):
  1. geocode()          place name -> GeoNames coordinates and elevation (Open-Meteo geocoding API)
  2. download_weather() 2025 hourly temperature_2m from the Open-Meteo archive, several places per request
  3. load_points()      table of locations; load_hourly() hourly demand per location (src.load_data formula)

Basel is taken from the official reference-house weather file (case coordinate 47.56 N, 7.59 E),
and 15 more cities reuse the files already downloaded for the 16-city map (data/raw/swiss_cities/),
so nothing is downloaded twice.
"""

import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from src.cities import CITIES, city_file
from src.load_data import (
    DESIGN_SPREAD_K, INDOOR_C, WEATHER_CSV, ROOT, add_heat_demand, file_time_to_local, read_weather,
)

GEO_DIR = ROOT / "data" / "raw" / "geocoding"
POINT_DIR = ROOT / "data" / "raw" / "swiss_points"

# (name, canton as GeoNames calls it, region, cantonal capital?)
# Regions are OUR grouping (assumption), used only to compare climates in the analysis:
#   Jura, Plateau (incl. Basel and Geneva lowlands), Northern Alps (Prealps and north-side
#   alpine valleys), Inner Alps (Valais, Grisons), South (Ticino and south-side Grisons valleys).
LOCATIONS = [
    # --- 26 cantonal capitals ---
    ("Zürich", "Zurich", "Plateau", True),
    ("Bern", "Bern", "Plateau", True),
    ("Luzern", "Lucerne", "Plateau", True),
    ("Altdorf", "Uri", "Northern Alps", True),
    ("Schwyz", "Schwyz", "Northern Alps", True),
    ("Sarnen", "Obwalden", "Northern Alps", True),
    ("Stans", "Nidwalden", "Northern Alps", True),
    ("Glarus", "Glarus", "Northern Alps", True),
    ("Zug", "Zug", "Plateau", True),
    ("Fribourg", "Fribourg", "Plateau", True),
    ("Solothurn", "Solothurn", "Plateau", True),
    ("Basel", "Basel-City", "Plateau", True),
    ("Liestal", "Basel-Landschaft", "Jura", True),
    ("Schaffhausen", "Schaffhausen", "Plateau", True),
    ("Herisau", "Appenzell Ausserrhoden", "Northern Alps", True),
    ("Appenzell", "Appenzell Innerrhoden", "Northern Alps", True),
    ("St. Gallen", "St. Gallen", "Plateau", True),
    ("Chur", "Grisons", "Inner Alps", True),
    ("Aarau", "Aargau", "Plateau", True),
    ("Frauenfeld", "Thurgau", "Plateau", True),
    ("Bellinzona", "Ticino", "South", True),
    ("Lausanne", "Vaud", "Plateau", True),
    ("Sion", "Valais", "Inner Alps", True),
    ("Neuchâtel", "Neuchâtel", "Jura", True),
    ("Genève", "Geneva", "Plateau", True),
    ("Delémont", "Jura", "Jura", True),
    # --- Plateau ---
    ("Winterthur", "Zurich", "Plateau", False),
    ("Biel", "Bern", "Plateau", False),
    ("Thun", "Bern", "Plateau", False),
    ("Olten", "Solothurn", "Plateau", False),
    ("Baden", "Aargau", "Plateau", False),
    ("Yverdon-les-Bains", "Vaud", "Plateau", False),
    ("Nyon", "Vaud", "Plateau", False),
    ("Montreux", "Vaud", "Plateau", False),
    ("Wil", "St. Gallen", "Plateau", False),
    ("Rapperswil", "St. Gallen", "Plateau", False),
    ("Langenthal", "Bern", "Plateau", False),
    ("Payerne", "Vaud", "Plateau", False),
    ("Kreuzlingen", "Thurgau", "Plateau", False),
    # --- Jura ---
    ("La Chaux-de-Fonds", "Neuchâtel", "Jura", False),
    ("Le Locle", "Neuchâtel", "Jura", False),
    ("La Brévine", "Neuchâtel", "Jura", False),
    ("Sainte-Croix", "Vaud", "Jura", False),
    ("Le Sentier", "Vaud", "Jura", False),
    ("Porrentruy", "Jura", "Jura", False),
    ("Moutier", "Jura", "Jura", False),  # canton Jura since 1 Jan 2026
    ("Saignelégier", "Jura", "Jura", False),
    # --- Northern Alps / Prealps ---
    ("Interlaken", "Bern", "Northern Alps", False),
    ("Meiringen", "Bern", "Northern Alps", False),
    ("Grindelwald", "Bern", "Northern Alps", False),
    ("Adelboden", "Bern", "Northern Alps", False),
    ("Gstaad", "Bern", "Northern Alps", False),
    ("Château-d'Oex", "Vaud", "Northern Alps", False),
    ("Bulle", "Fribourg", "Northern Alps", False),
    ("Engelberg", "Obwalden", "Northern Alps", False),
    ("Einsiedeln", "Schwyz", "Northern Alps", False),
    ("Wildhaus", "St. Gallen", "Northern Alps", False),
    ("Elm", "Glarus", "Northern Alps", False),
    ("Andermatt", "Uri", "Northern Alps", False),
    # --- Inner Alps (Valais, Grisons) ---
    ("Martigny", "Valais", "Inner Alps", False),
    ("Sierre", "Valais", "Inner Alps", False),
    ("Visp", "Valais", "Inner Alps", False),
    ("Brig", "Valais", "Inner Alps", False),
    ("Verbier", "Valais", "Inner Alps", False),
    ("Crans-Montana", "Valais", "Inner Alps", False),
    ("Leukerbad", "Valais", "Inner Alps", False),
    ("Zermatt", "Valais", "Inner Alps", False),
    ("Saas-Fee", "Valais", "Inner Alps", False),
    ("Ulrichen", "Valais", "Inner Alps", False),
    ("Ilanz", "Grisons", "Inner Alps", False),
    ("Disentis", "Grisons", "Inner Alps", False),
    ("Splügen", "Grisons", "Inner Alps", False),
    ("Lenzerheide", "Grisons", "Inner Alps", False),
    ("Arosa", "Grisons", "Inner Alps", False),
    ("Klosters", "Grisons", "Inner Alps", False),
    ("Davos", "Grisons", "Inner Alps", False),
    ("Zernez", "Grisons", "Inner Alps", False),
    ("Scuol", "Grisons", "Inner Alps", False),
    ("Samedan", "Grisons", "Inner Alps", False),
    ("St. Moritz", "Grisons", "Inner Alps", False),
    ("Sils", "Grisons", "Inner Alps", False),
    ("Bivio", "Grisons", "Inner Alps", False),
    ("Juf", "Grisons", "Inner Alps", False),
    # --- South of the Alps ---
    ("Lugano", "Ticino", "South", False),
    ("Locarno", "Ticino", "South", False),
    ("Mendrisio", "Ticino", "South", False),
    ("Chiasso", "Ticino", "South", False),
    ("Biasca", "Ticino", "South", False),
    ("Faido", "Ticino", "South", False),
    ("Airolo", "Ticino", "South", False),
    ("Roveredo", "Grisons", "South", False),
    ("Poschiavo", "Grisons", "South", False),
    ("Vicosoprano", "Grisons", "South", False),
]

# Names whose GeoNames spelling differs from ours.
GEONAMES_QUERY = {"Luzern": "Lucerne", "Genève": "Geneva", "St. Gallen": "St. Gallen", "Biel": "Biel/Bienne",
                  "Sils": "Sils-Segl Maria", "Disentis": "Disentis/Mustér", "Lenzerheide": "Lenzerheide"}


def slug(name):
    table = str.maketrans({"ü": "u", "é": "e", "è": "e", "â": "a", "ô": "o", "ö": "o", "ä": "a", "'": ""})
    return name.lower().translate(table).replace(".", "").replace(" ", "_").replace("-", "_").replace("/", "_")


# ------------------------------------------------------------------ 1. geocoding
def geocode(name, canton, pause_s=0.3):
    """GeoNames hit for a populated place (feature code PPL*) in the given canton. Cached as raw JSON."""
    GEO_DIR.mkdir(parents=True, exist_ok=True)
    path = GEO_DIR / f"geonames_{slug(name)}.json"
    if not path.exists():
        query = GEONAMES_QUERY.get(name, name)
        url = ("https://geocoding-api.open-meteo.com/v1/search?"
               + urllib.parse.urlencode({"name": query, "count": 20, "countryCode": "CH", "format": "json"}))
        with urllib.request.urlopen(url) as r:
            path.write_bytes(r.read())
        time.sleep(pause_s)
    results = json.loads(path.read_text()).get("results", [])
    # Populated places only; skip city districts (PPLX), localities (PPLL) and historical places (PPLH).
    # GeoNames writes cantons as e.g. "Canton of Zurich", so we match the canton name as a substring.
    hits = [r for r in results
            if r.get("feature_code", "").startswith("PPL") and r["feature_code"] not in ("PPLX", "PPLL", "PPLH")
            and canton in (r.get("admin1") or "")]
    if not hits:
        found = [(r["name"], r.get("admin1"), r.get("feature_code")) for r in results]
        raise LookupError(f"No populated place '{name}' in canton {canton}. GeoNames returned: {found}")
    return hits[0]


def km_between(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


def existing_file(name):
    """Weather file that already exists for this place (reference house or 16-city map), else None."""
    if name == "Basel":
        return WEATHER_CSV, (47.56, 7.59), "case coordinate (reference house)"
    if name in CITIES and city_file(name).exists():
        return city_file(name), CITIES[name], "16-city map (rounded city centre)"
    return None


def locations_table():
    """One row per location with the coordinates we request weather for."""
    rows = []
    for name, canton, region, capital in LOCATIONS:
        g = geocode(name, canton)
        row = {"name": name, "canton": canton, "region": region, "capital": capital,
               "geonames_id": g["id"], "geonames_lat": g["latitude"], "geonames_lon": g["longitude"],
               "geonames_elev_m": g.get("elevation")}
        reuse = existing_file(name)
        if reuse:
            _, (lat, lon), why = reuse
            row.update(lat=lat, lon=lon, coord_source=why)
        else:
            row.update(lat=g["latitude"], lon=g["longitude"], coord_source="GeoNames via Open-Meteo geocoding")
        row["km_from_geonames"] = km_between(row["lat"], row["lon"], g["latitude"], g["longitude"])
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 2. weather download
def archive_url(lats, lons):
    q = urllib.parse.urlencode({
        "latitude": ",".join(f"{x:.5f}" for x in lats), "longitude": ",".join(f"{x:.5f}" for x in lons),
        "start_date": "2025-01-01", "end_date": "2025-12-31", "hourly": "temperature_2m",
        "timezone": "Europe/Zurich", "format": "csv",
    })
    return f"https://archive-api.open-meteo.com/v1/archive?{q}"


def batch_index():
    """name -> (batch csv path, location_id) for every location already downloaded in a batch."""
    index = {}
    for req in sorted(POINT_DIR.glob("batch_*.request.json")):
        info = json.loads(req.read_text())
        csv_path = req.with_name(req.name.replace(".request.json", ".csv"))
        if csv_path.exists():
            for i, name in enumerate(info["names"]):
                index[name] = (csv_path, i)
    return index


def download_weather(table, batch_size=8, pause_s=65):
    """Download 2025 hourly temperature for every location without a cached file.

    Open-Meteo's free tier allows 600 calls per minute, and one year of hourly data for one
    place counts as roughly 26 calls (one per 2 weeks). 8 places per request with a one-minute
    pause stays far below the limit.
    """
    POINT_DIR.mkdir(parents=True, exist_ok=True)
    done = batch_index()
    todo = table[[existing_file(n) is None and n not in done for n in table.name]]
    batches = [todo.iloc[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    for k, b in enumerate(batches):
        url = archive_url(b.lat.tolist(), b.lon.tolist())
        tag = hashlib.sha1(url.encode()).hexdigest()[:10]
        print(f"  batch {k + 1}/{len(batches)}: {', '.join(b.name)}")
        with urllib.request.urlopen(url, timeout=120) as r:
            body = r.read()
        (POINT_DIR / f"batch_{tag}.csv").write_bytes(body)
        (POINT_DIR / f"batch_{tag}.request.json").write_text(json.dumps(
            {"url": url, "names": b.name.tolist(), "downloaded": time.strftime("%Y-%m-%d")}, ensure_ascii=False, indent=1))
        if k + 1 < len(batches):
            time.sleep(pause_s)


def read_batch(path, location_id):
    """Read one location out of a multi-location Open-Meteo CSV. Returns (weather, metadata)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    blank = lines.index("")
    meta = pd.read_csv(path, nrows=blank - 1)
    m = meta[meta.location_id == location_id].iloc[0]
    data = pd.read_csv(path, skiprows=blank + 1)
    d = data[data.location_id == location_id].reset_index(drop=True)
    weather = pd.DataFrame({
        "timestamp": file_time_to_local(d["time"], int(m.utc_offset_seconds)),
        "file_time_utc_plus_1": d["time"],
        "temperature_2m": d["temperature_2m (°C)"],
    })
    return weather, {"grid_lat": float(m.latitude), "grid_lon": float(m.longitude), "model_elev_m": float(m.elevation)}


def read_location_weather(name, index=None):
    """(weather, metadata) for one location, from whichever cached file holds it."""
    reuse = existing_file(name)
    if reuse:
        path = reuse[0]
        meta = pd.read_csv(path, nrows=1)
        w = read_weather(path)[["timestamp", "file_time_utc_plus_1", "temperature_2m"]]
        return w, {"grid_lat": float(meta.latitude[0]), "grid_lon": float(meta.longitude[0]),
                   "model_elev_m": float(meta.elevation[0])}
    path, i = (index or batch_index())[name]
    return read_batch(path, i)


# ------------------------------------------------------------------ 3. tables
def load_all(download=True):
    """Return (points, hourly): points = one row per location, hourly = {name: DataFrame}.

    hourly[name] has the load_house() columns for the case constant 25.6, plus
    space_kwh_local / demand_kwh_local for the per-location design spread
    (20 minus that location's own coldest hour).
    """
    table = locations_table()
    if download:
        download_weather(table)
    index = batch_index()
    hourly, metas = {}, []
    for name in table.name:
        weather, meta = read_location_weather(name, index)
        assert len(weather) == 8760 and weather.temperature_2m.notna().all(), f"{name}: incomplete weather"
        df = add_heat_demand(weather)  # case constant 25.6
        local_spread = INDOOR_C - weather.temperature_2m.min()
        local = add_heat_demand(weather, design_spread_k=local_spread)
        df["space_kwh_local"] = local["space_kwh"]
        df["demand_kwh_local"] = local["demand_kwh"]
        hourly[name] = df
        metas.append({**meta, "design_spread_local_k": local_spread})
    points = pd.concat([table, pd.DataFrame(metas)], axis=1)
    points["design_spread_case_k"] = DESIGN_SPREAD_K
    return points, hourly
