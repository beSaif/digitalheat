"""Build the data files of the homeowner pilot estimator (website/rechner/data/).

    python3 scripts/build_estimator_data.py

Standard library only. Reads cached raw files, makes no network calls:

  * weather: 93 Swiss places, hourly temperature_2m 2025 (Open-Meteo, UTC+1 file clock).
    Basel is the reference-house weather (data/raw/openmeteo_basel_2025_hourly.csv).
  * place metadata: outputs/swiss_points_2025_stats.csv (names, cantons, regions, coordinates)
  * terrain: data/raw/swiss_grid/elevation_0.03x0.045.json (Copernicus DEM via Open-Meteo)
  * postcodes: data/raw/plz/AMTOVZ_CSV_WGS84/AMTOVZ_CSV_WGS84.csv
    (swisstopo, Amtliches Ortschaftenverzeichnis mit PLZ, WGS84, state 2026-11-01)

Writes:
  website/rechner/data/points.json        places, reference HGT, terrain grid
  website/rechner/data/plz.json           postcode / locality / municipality -> coordinates, terrain height
  website/rechner/data/weather/<id>.json  8,760 hourly temperatures in tenths of a degree

Heating days use the file's own 24-row days, exactly as data/reference_house_2025_hourly.csv
does, so the Basel point reproduces the reference profile hour for hour (checked by
website/rechner/tests/validate.mjs).
"""
import csv
import json
import statistics
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "website" / "rechner" / "data"
STATS = ROOT / "outputs" / "swiss_points_2025_stats.csv"
PLZ_CSV = RAW / "plz" / "AMTOVZ_CSV_WGS84" / "AMTOVZ_CSV_WGS84.csv"
GRID_JSON = RAW / "swiss_grid" / "elevation_0.03x0.045.json"
GRID_DLAT, GRID_DLON = 0.03, 0.045

INDOOR_C = 20.0
HEATING_LIMIT_C = 12.0


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    out = "".join(c if c.isalnum() else "_" for c in s)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


def read_single(path):
    """One-location Open-Meteo CSV -> (temperatures, grid metadata)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    meta = dict(zip(lines[0].split(","), lines[1].split(",")))
    head = lines[3].split(",")
    i_t, i_temp = head.index("time"), head.index("temperature_2m (°C)")
    rows = [ln.split(",") for ln in lines[4:] if ln]
    return [r[i_t] for r in rows], [float(r[i_temp]) for r in rows], meta


def batch_index():
    index = {}
    for req in sorted((RAW / "swiss_points").glob("batch_*.request.json")):
        info = json.loads(req.read_text(encoding="utf-8"))
        for i, name in enumerate(info["names"]):
            index[name] = (req.with_name(req.name.replace(".request.json", ".csv")), i)
    return index


def read_batch(path, location_id):
    lines = path.read_text(encoding="utf-8").splitlines()
    blank = lines.index("")
    mhead = lines[0].split(",")
    meta = None
    for ln in lines[1:blank]:
        rec = dict(zip(mhead, ln.split(",")))
        if int(rec["location_id"]) == location_id:
            meta = rec
    head = lines[blank + 1].split(",")
    i_id, i_t, i_temp = head.index("location_id"), head.index("time"), head.index("temperature_2m (°C)")
    times, temps = [], []
    for ln in lines[blank + 2:]:
        r = ln.split(",")
        if len(r) > i_temp and int(r[i_id]) == location_id:
            times.append(r[i_t])
            temps.append(float(r[i_temp]))
    return times, temps, meta


def weather_for(row, index):
    src = row["coord_source"]
    if src.startswith("case coordinate"):
        return read_single(RAW / "openmeteo_basel_2025_hourly.csv")
    if src.startswith("16-city"):
        return read_single(RAW / "swiss_cities" / f"openmeteo_{slug(row['name'])}_2025_hourly.csv")
    path, i = index[row["name"]]
    return read_batch(path, i)


def heating_stats(temps):
    """HGT 20/12 and heating days on 24-row file days (the reference profile's definition)."""
    hgt, days, dh = 0.0, 0, 0.0
    for d in range(len(temps) // 24):
        block = temps[d * 24:(d + 1) * 24]
        mean = sum(block) / 24
        if mean < HEATING_LIMIT_C:
            days += 1
            hgt += INDOOR_C - mean
            dh += sum(max(0.0, INDOOR_C - t) for t in block)
    return hgt, days, dh


def load_grid():
    raw = json.loads(GRID_JSON.read_text(encoding="utf-8"))
    pts = [(float(k.split(",")[0]), float(k.split(",")[1]), v) for k, v in raw.items()]
    lat0 = min(p[0] for p in pts)
    lon0 = min(p[1] for p in pts)
    nrow = round((max(p[0] for p in pts) - lat0) / GRID_DLAT) + 1
    ncol = round((max(p[1] for p in pts) - lon0) / GRID_DLON) + 1
    cells = [None] * (nrow * ncol)
    for lat, lon, v in pts:
        r, c = round((lat - lat0) / GRID_DLAT), round((lon - lon0) / GRID_DLON)
        cells[r * ncol + c] = None if v is None else round(v)
    return {"lat0": lat0, "lon0": lon0, "dlat": GRID_DLAT, "dlon": GRID_DLON,
            "nrow": nrow, "ncol": ncol, "elev": cells}


def grid_elev(grid, lat, lon):
    """Terrain height of the cell centre nearest to (lat, lon); searches 1 ring if empty."""
    r0 = round((lat - grid["lat0"]) / grid["dlat"])
    c0 = round((lon - grid["lon0"]) / grid["dlon"])
    best = None
    for dr in (0, -1, 1):
        for dc in (0, -1, 1):
            r, c = r0 + dr, c0 + dc
            if 0 <= r < grid["nrow"] and 0 <= c < grid["ncol"]:
                v = grid["elev"][r * grid["ncol"] + c]
                if v is not None:
                    d = (dr * dr + dc * dc)
                    if best is None or d < best[0]:
                        best = (d, v)
        if best and best[0] == 0:
            break
    return None if best is None else best[1]


def main():
    (OUT / "weather").mkdir(parents=True, exist_ok=True)
    index = batch_index()
    with STATS.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    points = []
    for row in rows:
        times, temps, meta = weather_for(row, index)
        assert len(temps) == 8760, f"{row['name']}: {len(temps)} hours"
        assert times[0] == "2025-01-01T00:00" and times[-1] == "2025-12-31T23:00", row["name"]
        hgt, days, dh = heating_stats(temps)
        pid = slug(row["name"])
        tenths = [round(t * 10) for t in temps]
        assert all(abs(t / 10 - x) < 1e-9 for t, x in zip(tenths, temps)), f"{row['name']}: not 0.1 °C"
        (OUT / "weather" / f"{pid}.json").write_text(
            json.dumps({"id": pid, "unit": "0.1 degC", "start": times[0], "clock": "UTC+1 (Open-Meteo file time)",
                        "t": tenths}, separators=(",", ":")), encoding="utf-8")
        points.append({
            "id": pid, "name": row["name"], "canton": row["canton"], "region": row["region"],
            "lat": float(row["lat"]), "lon": float(row["lon"]),
            "elev": round(float(meta["elevation"])),
            "grid_lat": float(meta["latitude"]), "grid_lon": float(meta["longitude"]),
            "hgt": round(hgt, 1), "heating_days": days, "degree_hours": round(dh, 1),
            "min_t": min(temps),
        })

    plateau = [p["hgt"] for p in points if p["region"] == "Plateau"]
    hgt_ref = statistics.median(plateau)
    grid = load_grid()

    (OUT / "points.json").write_text(json.dumps({
        "source": "Open-Meteo historical archive, 2025, hourly temperature_2m, default model; places from outputs/swiss_points_2025_stats.csv",
        "hgt_ref": hgt_ref,
        "hgt_ref_rule": f"median HGT 20/12 of the {len(plateau)} Plateau places, 2025, 24-row file days",
        "points": points,
        "grid": grid,
        "grid_source": "Copernicus DEM GLO-90 via Open-Meteo elevation API, cell centres 0.03 x 0.045 deg",
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    plz = []
    seen = set()
    with PLZ_CSV.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            key = (r["PLZ4"], r["Ortschaftsname"], r["Gemeindename"])
            if key in seen:
                continue
            seen.add(key)
            lat, lon = float(r["N"]), float(r["E"])
            plz.append([int(r["PLZ4"]), r["Ortschaftsname"], r["Gemeindename"], r["Kantonskürzel"],
                        round(lat, 4), round(lon, 4), grid_elev(grid, lat, lon)])
    plz.sort(key=lambda x: (x[0], x[1]))
    (OUT / "plz.json").write_text(json.dumps({
        "source": "swisstopo, Amtliches Ortschaftenverzeichnis mit Postleitzahl und Perimeter (WGS84 CSV), state 2026-11-01",
        "columns": ["plz", "ortschaft", "gemeinde", "kanton", "lat", "lon", "elev_m"],
        "rows": plz,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    basel = next(p for p in points if p["id"] == "basel")
    print(f"{len(points)} weather points, {len(plz)} postcode rows, HGT ref {hgt_ref:.1f} Kd")
    print(f"Basel: HGT {basel['hgt']} Kd, {basel['heating_days']} heating days, min {basel['min_t']} °C, "
          f"space heating at 10 kW / 25.6 K = {basel['degree_hours'] * 10 / 25.6:.1f} kWh")


if __name__ == "__main__":
    main()
