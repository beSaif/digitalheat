"""Build the offline Switzerland heat map (Part A + zones of Part B).

Run from the repository root (one command, downloads only what is not cached in data/raw/):
    python3 scripts/build_swiss_map.py

Writes:
    outputs/swiss_points_2025_stats.csv    one row per location, all annual numbers (Part A2)
    outputs/swiss_points_2025_monthly.csv  one row per location and month
    outputs/interpolation_check.csv        leave-one-out test of the interpolation
    outputs/swiss_heat_map.html            single file, works offline, no network calls
"""

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.load_data import DESIGN_POWER_KW, HOT_WATER_KWH_PER_DAY, INDOOR_C, load_house  # noqa: E402
from src.swiss_geo import BBOX, DLAT, DLON, grid_cells, grid_elevation, swiss_border, swiss_lakes  # noqa: E402
from src.swiss_points import load_all  # noqa: E402
from src.swiss_stats import RECOVERY, ZONES, all_monthly, all_stats, check_hot_water, check_monthly  # noqa: E402

TEMPLATE = ROOT / "scripts" / "swiss_map_template.html"
OUT = ROOT / "outputs"

# Interpolation settings (must match the JavaScript in the template)
IDW_POWER = 2
IDW_NEIGHBOURS = 8


# ---------------------------------------------------------------- checks
def check_basel(stats, hourly):
    ref = load_house()
    b = stats.set_index("name").loc["Basel"]
    assert b.heating_days == 206, f"Basel heating days {b.heating_days} != 206"
    assert abs(b.space_kwh_case - ref.space_kwh.sum()) < 1e-6, "Basel space heating differs from reference house"
    assert (hourly["Basel"].demand_kwh.values == ref.demand_kwh.values).all(), "Basel hourly demand differs"
    print(f"  PASS  Basel = reference house: 206 heating days, {b.space_kwh_case:,.0f} kWh space heating")


def check_hgt_relation(stats):
    """Derived rule of thumb: space heating ~= 24 h x 10 kW / 25.6 K x HGT = 9.375 x HGT (case sizing)."""
    ratio = stats.space_kwh_case / stats.hgt_20_12
    print(f"  INFO  space heating / HGT 20/12 = {ratio.min():.3f} .. {ratio.max():.3f} kWh per Kd "
          f"(theory 9.375; lower where some heating-day hours are above 20 degC)")
    return ratio


# ---------------------------------------------------------------- interpolation
def km_xy(lat, lon):
    """Simple local projection in km (good enough inside Switzerland)."""
    return np.c_[np.asarray(lon) * 111.32 * np.cos(np.radians(46.8)), np.asarray(lat) * 110.57]


def interpolate(st_xy, st_z, st_v, q_xy, q_z, detrend=True):
    """Elevation-detrended inverse-distance weighting.

    1. fit value = a + b * elevation over all stations (least squares)
    2. interpolate the residuals with IDW (power 2, 8 nearest stations)
    3. add the trend back at the target elevation, clamp to the station range
    """
    if detrend:
        b, a = np.polyfit(st_z, st_v, 1)
    else:
        a, b = st_v.mean(), 0.0
    resid = st_v - (a + b * st_z)
    d = np.sqrt(((q_xy[:, None, :] - st_xy[None, :, :]) ** 2).sum(-1))
    idx = np.argsort(d, axis=1)[:, :IDW_NEIGHBOURS]
    dn = np.take_along_axis(d, idx, 1)
    w = 1 / np.maximum(dn, 0.5) ** IDW_POWER
    r = (w * resid[idx]).sum(1) / w.sum(1)
    return np.clip(a + b * q_z + r, st_v.min(), st_v.max())


def leave_one_out(stats, metrics):
    """Predict each station from the others; compare plain IDW with elevation-detrended IDW."""
    xy, z = km_xy(stats.lat, stats.lon), stats.model_elev_m.values
    rows = []
    for m in metrics:
        v = stats[m].values.astype(float)
        for detrend in (False, True):
            err = []
            for i in range(len(v)):
                keep = np.arange(len(v)) != i
                p = interpolate(xy[keep], z[keep], v[keep], xy[i:i + 1], z[i:i + 1], detrend)[0]
                err.append(p - v[i])
            err = np.array(err)
            rows.append({"metric": m, "method": "IDW + elevation trend" if detrend else "plain IDW",
                         "mean_abs_error": np.abs(err).mean(), "max_abs_error": np.abs(err).max(),
                         "worst_station": stats.name.iloc[np.abs(err).argmax()],
                         "r2_elevation": np.corrcoef(z, v)[0, 1] ** 2})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- payload
def b64_int16(values):
    return base64.b64encode(np.asarray(values, dtype="<i2").tobytes()).decode()


def rnd(x, n=2):
    return None if pd.isna(x) else round(float(x), n)


def build_payload(points, hourly, stats, monthly, border, lakes, grid, loo):
    nrow, ncol, cells, elev = grid
    first = hourly[points.name.iloc[0]]
    times = [t.isoformat(timespec="minutes") for t in first.timestamp]
    dates = [str(d) for d in first.date.drop_duplicates()]
    date_start = first.reset_index(drop=True).groupby("date").head(1).index.tolist()

    stat_cols = [c for c in stats.columns if c not in points.columns or c == "name"]
    month_cols = [c for c in monthly.columns if c not in ("name", "month")]
    by_name = {n: g.sort_values("month") for n, g in monthly.groupby("name")}
    stations = []
    for _, s in stats.iterrows():
        df = hourly[s["name"]]
        assert [t.isoformat(timespec="minutes") for t in df.timestamp] == times, f"{s['name']}: times differ"
        heat = df.groupby("date").heating_day.first().astype(int)
        stations.append({
            "name": s["name"], "canton": s.canton, "region": s.region, "capital": bool(s.capital),
            "lat": rnd(s.lat, 5), "lon": rnd(s.lon, 5), "elev": rnd(s.model_elev_m, 0),
            "geoElev": rnd(s.geonames_elev_m, 0), "coordSource": s.coord_source,
            "spreadLocal": rnd(s.design_spread_local_k, 3),
            "t": b64_int16(np.round(df.temperature_2m.values * 10)),
            "heat": "".join(map(str, heat.tolist())),
            "s": {c: (s[c] if isinstance(s[c], str) else rnd(s[c], 3)) for c in stat_cols if c != "name"},
            "m": {c: [rnd(v, 3) for v in by_name[s["name"]][c]] for c in month_cols},
        })
    mask = np.zeros((nrow, ncol), dtype=int)
    for r, c, _, _ in cells:
        mask[r, c] = 1
    return {
        "times": times, "dates": dates, "dateStart": date_start,
        "case": {"designPowerKw": DESIGN_POWER_KW, "indoorC": INDOOR_C, "spreadCase": 25.6,
                 "hotWaterKw": HOT_WATER_KWH_PER_DAY / 24, "recovery": RECOVERY, "heatingLimitC": 12},
        "zones": [[n, (u if np.isfinite(u) else None)] for n, u in ZONES],
        "idw": {"power": IDW_POWER, "neighbours": IDW_NEIGHBOURS},
        "stations": stations,
        "grid": {"nrow": nrow, "ncol": ncol, "bbox": BBOX, "dlat": DLAT, "dlon": DLON,
                 "mask": "".join(map(str, mask.ravel().tolist())), "elev": b64_int16(np.round(elev)),
                 "maxStationElev": float(points.model_elev_m.max())},
        "border": [[[round(x, 4), round(y, 4)] for x, y in ring] for ring in border],
        "lakes": [[[round(x, 4), round(y, 4)] for x, y in ring] for _, ring in lakes],
        "loo": loo.round(3).to_dict(orient="records"),
    }


def main():
    print("1. Locations and weather")
    points, hourly = load_all(download=True)
    print(f"  {len(points)} locations, {points.capital.sum()} cantonal capitals, "
          f"model elevation {points.model_elev_m.min():.0f}-{points.model_elev_m.max():.0f} m")

    print("2. Annual statistics")
    stats = all_stats(points, hourly)
    check_basel(stats, hourly)
    check_hot_water(stats)
    check_hgt_relation(stats)
    OUT.mkdir(exist_ok=True)
    stats.round(3).to_csv(OUT / "swiss_points_2025_stats.csv", index=False)
    monthly = all_monthly(points, hourly)
    check_monthly(monthly, stats)
    monthly.round(3).to_csv(OUT / "swiss_points_2025_monthly.csv", index=False)
    print(f"  PASS  monthly numbers add up to the annual numbers ({len(monthly)} rows)")

    print("3. Border, lakes, grid")
    border = swiss_border()
    lakes = swiss_lakes(border)
    nrow, ncol, cells = grid_cells(border)
    elev = grid_elevation(cells)
    print(f"  border {sum(len(r) for r in border)} points, {len(lakes)} lakes, {len(cells)} grid cells")

    print("4. Interpolation check (leave one out)")
    loo = leave_one_out(stats, ["mean_temp_c", "winter_mean_temp_c", "hgt_20_12", "heating_days",
                                "space_kwh_case", "peak_kw_case", "summer_mean_kw_case"])
    loo.round(3).to_csv(OUT / "interpolation_check.csv", index=False)
    print(loo.round(2).to_string(index=False))

    print("5. HTML")
    payload = build_payload(points, hourly, stats, monthly, border, lakes, (nrow, ncol, cells, elev), loo)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", data)
    (OUT / "swiss_heat_map.html").write_text(html, encoding="utf-8")
    print(f"  wrote outputs/swiss_heat_map.html ({len(html.encode()) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
