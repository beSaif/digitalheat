"""Hourly outdoor temperature for any place and year, as the case uses it.

Open-Meteo historical archive, hourly temperature_2m, same request as the case's
reference profile (timezone Europe/Zurich, which the archive returns as UTC+1 all year).
Basel 2025 comes from the committed reference profile, so the reference house is exactly
the case's numbers. Other places and years are downloaded once and cached in
data/raw/weather/.

Every year is 365 days (8,760 hours): in leap years 29 February is dropped, so all
years line up hour by hour with the dashboard and the 2025 reference.
"""

import csv
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "raw" / "weather"
REFERENCE_CSV = ROOT / "data" / "reference_house_2025_hourly.csv"
BASEL = (47.56, 7.59)  # the case's reference-house coordinates
H = 8760
FIRST_YEAR, LAST_YEAR = 1950, 2025  # full years only


def _is_basel(lat, lon):
    return abs(lat - BASEL[0]) < 0.02 and abs(lon - BASEL[1]) < 0.02


def _fetch(lat, lon, year):
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lat:.4f}&longitude={lon:.4f}&start_date={year}-01-01&end_date={year}-12-31"
           "&hourly=temperature_2m&timezone=Europe%2FZurich")
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    return {"source": "Open-Meteo historical archive, default model", "latitude": d["latitude"],
            "longitude": d["longitude"], "elevation": d["elevation"], "year": year,
            "temperature_2m": d["hourly"]["temperature_2m"]}


def _fill_gaps(t):
    """Linear fill for the rare missing hour (None) in archive data."""
    out = list(t)
    for i, v in enumerate(out):
        if v is None:
            j = i
            while j < len(out) and out[j] is None:
                j += 1
            a = out[i - 1] if i > 0 else (out[j] if j < len(out) else 10.0)
            b = out[j] if j < len(out) else a
            for k in range(i, j):
                out[k] = a + (b - a) * (k - i + 1) / (j - i + 1)
    return out


def temperatures(lat, lon, year):
    """8,760 hourly temperatures in °C for (lat, lon) and a full calendar year."""
    year = int(year)
    if not FIRST_YEAR <= year <= LAST_YEAR:
        raise ValueError(f"year must be {FIRST_YEAR}–{LAST_YEAR} (full years only)")
    if year == 2025 and _is_basel(lat, lon):
        with open(REFERENCE_CSV) as f:
            return [float(r["temperature_2m_c"]) for r in csv.DictReader(f)]
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{lat:.3f}_{lon:.3f}_{year}.json"
    if not path.exists():
        path.write_text(json.dumps(_fetch(lat, lon, year)))
    t = _fill_gaps(json.loads(path.read_text())["temperature_2m"])
    if len(t) == H + 24:  # leap year: drop 29 February (day index 59)
        del t[59 * 24:60 * 24]
    assert len(t) == H, (lat, lon, year, len(t))
    return t
