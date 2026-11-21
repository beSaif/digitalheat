"""Swiss border, lakes and an elevation grid for the heatmap. Raw downloads cached in data/raw/.

Sources
- Border and lakes: Natural Earth 1:10m (public domain), files ne_10m_admin_0_countries and
  ne_10m_lakes and ne_10m_lakes_europe from https://github.com/nvkelso/natural-earth-vector
- Grid elevation: Open-Meteo elevation API (Copernicus DEM GLO-90), https://open-meteo.com/en/docs/elevation-api
"""

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request

from src.load_data import ROOT

NE_DIR = ROOT / "data" / "raw" / "natural_earth"
NE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{}.geojson"
GRID_DIR = ROOT / "data" / "raw" / "swiss_grid"

# Grid over Switzerland: about 3.3 km x 3.4 km cells.
BBOX = {"lat_min": 45.80, "lat_max": 47.83, "lon_min": 5.94, "lon_max": 10.52}
DLAT, DLON = 0.03, 0.045
SIMPLIFY_DEG = 0.002  # about 200 m; enough for a country-scale map


def natural_earth(name):
    """Load a Natural Earth GeoJSON, downloading it once into data/raw/natural_earth/."""
    NE_DIR.mkdir(parents=True, exist_ok=True)
    path = NE_DIR / f"{name}.geojson"
    if not path.exists():
        print(f"  downloading Natural Earth {name} ...")
        urllib.request.urlretrieve(NE_URL.format(name), path)
    return json.loads(path.read_text(encoding="utf-8"))


def rings_of(geometry):
    """All outer rings of a Polygon or MultiPolygon as lists of (lon, lat)."""
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"][0]]
    return [poly[0] for poly in geometry["coordinates"]]


def simplify(points, tol=SIMPLIFY_DEG):
    """Douglas-Peucker line simplification (keeps the shape, drops tiny wiggles)."""
    if len(points) < 3:
        return points
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy) or 1e-12
    dists = [abs(dy * (x - x1) - dx * (y - y1)) / norm for x, y in points[1:-1]]
    i = max(range(len(dists)), key=dists.__getitem__)
    if dists[i] > tol:
        left = simplify(points[: i + 2], tol)
        return left[:-1] + simplify(points[i + 1:], tol)
    return [points[0], points[-1]]


def simplify_ring(ring, tol=SIMPLIFY_DEG):
    """Simplify a closed ring: split it at the point farthest from the start, simplify both halves."""
    x0, y0 = ring[0]
    k = max(range(len(ring)), key=lambda i: (ring[i][0] - x0) ** 2 + (ring[i][1] - y0) ** 2)
    return simplify(ring[: k + 1], tol)[:-1] + simplify(ring[k:], tol)


def point_in_ring(lon, lat, ring):
    """Ray-casting test: is (lon, lat) inside the polygon ring?"""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][:2]
        xj, yj = ring[j][:2]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def swiss_border():
    """Switzerland outline as a list of rings [(lon, lat), ...], simplified."""
    countries = natural_earth("ne_10m_admin_0_countries")
    ch = [f for f in countries["features"] if f["properties"].get("ADM0_A3") == "CHE"]
    assert len(ch) == 1, "Switzerland not found exactly once in Natural Earth countries"
    return [simplify_ring([tuple(p[:2]) for p in ring]) for ring in rings_of(ch[0]["geometry"])]


def swiss_lakes(border):
    """Natural Earth lakes that touch Switzerland, simplified. Returns [(name, ring), ...]."""
    # The big lakes (Léman, Bodensee, Maggiore) are in ne_10m_lakes; smaller ones in the Europe supplement.
    features = natural_earth("ne_10m_lakes")["features"] + natural_earth("ne_10m_lakes_europe")["features"]
    out = []
    for f in features:
        for ring in rings_of(f["geometry"]):
            if any(point_in_ring(x, y, b) for x, y in ring for b in border):
                out.append((f["properties"].get("name") or "", simplify_ring([tuple(p[:2]) for p in ring], 0.001)))
    return out


def grid_cells(border):
    """Grid cells whose centre or any corner lies inside Switzerland. Returns [(row, col, lat, lon)]."""
    nrow = round((BBOX["lat_max"] - BBOX["lat_min"]) / DLAT)
    ncol = round((BBOX["lon_max"] - BBOX["lon_min"]) / DLON)
    cells = []
    for r in range(nrow):
        lat = BBOX["lat_max"] - (r + 0.5) * DLAT          # row 0 = north
        for c in range(ncol):
            lon = BBOX["lon_min"] + (c + 0.5) * DLON
            probes = [(lon, lat)] + [(lon + sx * DLON / 2, lat + sy * DLAT / 2) for sx in (-1, 1) for sy in (-1, 1)]
            if any(point_in_ring(x, y, b) for x, y in probes for b in border):
                cells.append((r, c, round(lat, 5), round(lon, 5)))
    return nrow, ncol, cells


def grid_elevation(cells, batch=100, pause_s=12.0):
    """Elevation (m) of every cell centre, cached in data/raw/swiss_grid/elevation_*.json.

    The free API allows 600 calls per minute and counts every coordinate as a call, so we send
    100 coordinates every 12 s (500 per minute) and wait a minute if the API still says 429.
    """
    GRID_DIR.mkdir(parents=True, exist_ok=True)
    path = GRID_DIR / f"elevation_{DLAT}x{DLON}.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    todo = [(lat, lon) for _, _, lat, lon in cells if f"{lat},{lon}" not in cache]
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        q = urllib.parse.urlencode({"latitude": ",".join(str(a) for a, _ in chunk),
                                    "longitude": ",".join(str(b) for _, b in chunk)})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(f"https://api.open-meteo.com/v1/elevation?{q}", timeout=60) as r:
                    elev = json.load(r)["elevation"]
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 4:
                    raise
                print("  rate limit reached, waiting 65 s ...")
                time.sleep(65)
        cache.update({f"{a},{b}": e for (a, b), e in zip(chunk, elev)})
        path.write_text(json.dumps(cache))
        time.sleep(pause_s)
    return [cache[f"{lat},{lon}"] for _, _, lat, lon in cells]
