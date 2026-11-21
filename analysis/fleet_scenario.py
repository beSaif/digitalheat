"""Scenario fleet for the operator dashboard design (written 2026-11-21).

NOT the team's scheduler and NOT case data. 24 sites copied from the reference
house, placed in Basel-Stadt by 2024 population per Wohnviertel, with house
size (x0.6-1.5 of the reference house), server count and tank varied.
Physics: the 'follow' rule of analysis/baseline_sweep.py (run as many whole
servers as demand + free tank space absorbs; never dump). Every permitted hour
counts as run and sold: an upper bound with no job model.

    python3 analysis/fleet_scenario.py              # print sites and fleet totals
    python3 analysis/fleet_scenario.py --json OUT   # also write the dashboard inputs
    python3 analysis/fleet_scenario.py --heatmap OUT.svg

Inputs: data/reference_house_2025_hourly.csv; data/raw/basel_wohnviertel.geojson
(data.bs.ch dataset 100042, Geodaten Kanton Basel-Stadt, CC BY 4.0).
Population 2024 per Wohnviertel: data.bs.ch dataset 100060 (copied below).
"""
import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import baseline_sweep as b  # noqa: E402

SEED = 11
POP_2024 = {"01": 2239, "02": 4990, "03": 11476, "04": 9326, "05": 12589, "06": 19224, "07": 9610,
            "08": 13768, "09": 7072, "10": 18044, "11": 19562, "12": 2437, "13": 4410, "14": 5827,
            "15": 9663, "16": 7770, "17": 15168, "18": 7104, "19": 2775, "20": 22645, "30": 1300}
DAYS = {"january": "2025-01-13", "shoulder": "2025-03-21", "tankfull": "2025-04-11", "summer": "2025-07-02"}
LON0, LON1, LAT0, LAT1 = 7.553, 7.695, 47.517, 47.602   # map frame used by the dashboard basemap
Q1 = b.REC * b.P_EL                                    # 0.8 kWh of heat per server-hour


def inside(x, y, ring):
    c = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def build():
    rows = b.load()
    gj = json.load(open(ROOT / "data" / "raw" / "basel_wohnviertel.geojson"))
    polys = {}
    for f in gj["features"]:
        g = f["geometry"]
        rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        polys[f["properties"]["wov_id"]] = (f["properties"]["wov_name"], rings)
    rnd = random.Random(SEED)
    ids = list(POP_2024)
    weights = [POP_2024[i] for i in ids]
    sites, share = [], [0] * len(rows)
    for i in range(24):
        name, rings = polys[rnd.choices(ids, weights)[0]]
        xs = [p[0] for r in rings for p in r]
        ys = [p[1] for r in rings for p in r]
        while True:
            x, y = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
            if any(inside(x, y, r) for r in rings):
                break
        size = rnd.choice([0.6, 0.8, 1.0, 1.0, 1.2, 1.5])
        n = max(3, min(10, round(6 * size) + rnd.choice([-1, 0, 0, 1])))
        tank = rnd.choice([20, 35, 35, 50, 70])
        soc = used = dem = runh = 0.0
        start = {}
        for h, (t, sh, dhw) in enumerate(rows):
            for key, day in DAYS.items():
                if t == day + "T00:00":
                    start[key] = round(soc, 4)
            d = (sh + dhw) * size
            k = min(n, int((d + tank - soc) / Q1 + 1e-9))
            avail = soc + k * Q1
            u = min(d, avail)
            soc = avail - u
            used += u
            dem += d
            runh += k
            share[h] += k
        sites.append({"id": f"BS-{i + 1:02d}", "district": name, "size": size, "n": n, "tank": tank,
                      "coverage": used / dem, "util": runh / (n * 8760), "used": used, "demand": dem,
                      "run_h": runh, "x_pct": round((x - LON0) / (LON1 - LON0) * 100, 2),
                      "y_pct": round((LAT1 - y) / (LAT1 - LAT0) * 100, 2), "start_soc": start})
    total_n = sum(s["n"] for s in sites)
    day_demand = {key: [round(sh + dhw, 4) for t, sh, dhw in rows if t.startswith(day)] for key, day in DAYS.items()}
    return sites, [v / total_n for v in share], day_demand


def heatmap_svg(share):
    ramp = ["#FEE391", "#FEC44F", "#FE9929", "#EC7014", "#CC4C02", "#8C2D04"]
    cw, ch = 3, 4
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {365 * cw} {24 * ch}" '
           f'width="{365 * cw}" height="{24 * ch}" preserveAspectRatio="none" shape-rendering="crispEdges">',
           f'<rect width="{365 * cw}" height="{24 * ch}" fill="#FAFAF9"/>']
    for h in range(24):
        for day in range(365):
            v = share[day * 24 + h]
            if v > 0:
                c = ramp[min(5, int(v * 6 - 1e-9))]
                out.append(f'<rect x="{day * cw}" y="{h * ch}" width="{cw}" height="{ch}" fill="{c}"/>')
    out.append("</svg>")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--heatmap")
    a = ap.parse_args()
    sites, share, day_demand = build()
    used = sum(s["used"] for s in sites)
    dem = sum(s["demand"] for s in sites)
    runh = sum(s["run_h"] for s in sites)
    n = sum(s["n"] for s in sites)
    print(f"{'site':6} {'district':20} size  n tank cover  util")
    for s in sites:
        print(f"{s['id']:6} {s['district']:20} {s['size']:4} {s['n']:2} {s['tank']:4} "
              f"{s['coverage'] * 100:5.1f}% {s['util'] * 100:5.1f}%")
    print(f"fleet: {len(sites)} sites, {n} servers, coverage {used / dem * 100:.1f}% "
          f"({used / 1000:.0f} of {dem / 1000:.0f} MWh), utilisation {runh / (n * 8760) * 100:.1f}%, "
          f"{runh:,.0f} server-h, electricity {runh * b.PRICE:,.0f} CHF, dumped 0 kWh")
    if a.json:
        json.dump({"seed": SEED, "days": DAYS, "day_demand": day_demand, "sites": sites}, open(a.json, "w"))
    if a.heatmap:
        Path(a.heatmap).write_text(heatmap_svg(share))


if __name__ == "__main__":
    main()
