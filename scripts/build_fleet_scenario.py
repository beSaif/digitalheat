"""Swiss scenario fleet for the operator dashboard.

    python3 scripts/build_fleet_scenario.py            # uses cached weather
    python3 scripts/build_fleet_scenario.py --download # re-fetch city weather
    python3 scripts/build_fleet_scenario.py --year 2023  # another weather year -> dashboard/public/data/y2023/

A SCENARIO, not measured data. 24 houses in 10 Swiss cities. Each house is the
case's reference house (docs/case-brief.md) scaled ×0.6–1.5 and driven by its
own city's 2025 hourly temperature (Open-Meteo archive, same model and formula
as scripts/build_reference_profile.py). Site BS-01 is the reference house itself
(scale 1, 6 servers, 35 kWh tank, Basel weather from the committed raw CSV).

Physics: case constants (1 kW server, 80 % heat recovered, lossless tank) and the
follow-heat rule from analysis/baseline_sweep.py. The rule gives each hour's
*heat permit*: how many servers the house's demand plus free tank space can absorb.

Jobs: the plan's two types (docs/overnight.md, "The two job types"):
  J1 transcription (whisper large-v3-turbo) 0.5 server-h, due in 24 h
  J2 LLM batch (llama-3.1-8B)                4.0 server-h, due in 168 h
Offers per site and day are sized to that day's permit-hours × a lognormal
factor (σ 0.15), 50/50 by server-hours: a contract sized to the house, not a
customer we found. Admission is an earliest-deadline-first dry run against the
permit plan (perfect forecast); refused work carries its reason. Work is
divisible across servers in half server-hours. Running at most the planned
permit keeps the tank at or below the plan, so admitted work never misses.

Standard library only. Seed 11. Output: dashboard/public/data/
"""
import argparse
import bisect
import csv
import json
import math
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "dashboard" / "public" / "data"
WEATHER_CACHE = ROOT / "data" / "raw" / "openmeteo_swiss_cities_2025_hourly.json"
SEED = 11

P_EL = 1.0
REC = 0.8
Q1 = REC * P_EL
PRICE = 0.3325
HEAT_VALUE = PRICE / 2.5
H = 8760

JOB_TYPES = [
    {"id": "J1", "name": "Transcription", "model": "whisper large-v3-turbo",
     "units": 1, "due_h": 24, "detail": "≈700 audio-hours"},
    {"id": "J2", "name": "LLM batch", "model": "llama-3.1-8B",
     "units": 8, "due_h": 168, "detail": "≈29 M output tokens"},
]  # units = half server-hours

CITIES = {
    "Basel":      {"canton": "Basel-Stadt", "lat": 47.557, "lon": 7.549, "code": "BS"},
    "Zürich":     {"canton": "Zürich", "lat": 47.377, "lon": 8.540, "code": "ZH"},
    "Winterthur": {"canton": "Zürich", "lat": 47.500, "lon": 8.724, "code": "WT"},
    "Bern":       {"canton": "Bern", "lat": 46.948, "lon": 7.447, "code": "BE"},
    "Genève":     {"canton": "Genève", "lat": 46.204, "lon": 6.143, "code": "GE"},
    "Lausanne":   {"canton": "Vaud", "lat": 46.520, "lon": 6.633, "code": "LS"},
    "Luzern":     {"canton": "Luzern", "lat": 47.050, "lon": 8.309, "code": "LU"},
    "St. Gallen": {"canton": "St. Gallen", "lat": 47.424, "lon": 9.377, "code": "SG"},
    "Lugano":     {"canton": "Ticino", "lat": 46.004, "lon": 8.951, "code": "TI"},
    "Chur":       {"canton": "Graubünden", "lat": 46.850, "lon": 9.532, "code": "GR"},
}

# (city, district, lat, lon, building type). Coordinates sit in residential blocks.
SITES = [
    ("Basel", "St. Johann", 47.5668, 7.5778, "Apartment block"),
    ("Basel", "Gundeldingen", 47.5418, 7.5948, "Apartment block"),
    ("Basel", "Matthäus", 47.5671, 7.5948, "Row house"),
    ("Basel", "Bachletten", 47.5497, 7.5722, "Apartment block"),
    ("Basel", "Riehen", 47.5843, 7.6497, "Detached house"),
    ("Zürich", "Wipkingen", 47.3934, 8.5298, "Apartment block"),
    ("Zürich", "Oerlikon", 47.4105, 8.5462, "Apartment block"),
    ("Zürich", "Wiedikon", 47.3698, 8.5185, "Apartment block"),
    ("Zürich", "Hottingen", 47.3707, 8.5615, "Row house"),
    ("Zürich", "Altstetten", 47.3883, 8.4880, "Apartment block"),
    ("Winterthur", "Veltheim", 47.5085, 8.7175, "Detached house"),
    ("Bern", "Länggasse", 46.9562, 7.4286, "Apartment block"),
    ("Bern", "Breitenrain", 46.9598, 7.4562, "Apartment block"),
    ("Bern", "Bümpliz", 46.9450, 7.3905, "Row house"),
    ("Genève", "Plainpalais", 46.1975, 6.1420, "Apartment block"),
    ("Genève", "Eaux-Vives", 46.2010, 6.1625, "Apartment block"),
    ("Lausanne", "Sous-Gare", 46.5135, 6.6305, "Apartment block"),
    ("Lausanne", "Chailly", 46.5305, 6.6500, "Detached house"),
    ("Luzern", "Neustadt", 47.0478, 8.3052, "Apartment block"),
    ("Luzern", "Wesemlin", 47.0598, 8.3168, "Row house"),
    ("St. Gallen", "Rotmonten", 47.4335, 9.3835, "Detached house"),
    ("St. Gallen", "Lachen", 47.4185, 9.3605, "Apartment block"),
    ("Lugano", "Molino Nuovo", 46.0080, 8.9490, "Apartment block"),
    ("Chur", "Lürlibad", 46.8565, 9.5385, "Detached house"),
]


def fetch_weather(city):
    c = CITIES[city]
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={c['lat']}&longitude={c['lon']}&start_date=2025-01-01&end_date=2025-12-31"
           "&hourly=temperature_2m&timezone=Europe%2FZurich")
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    return {"elevation": d["elevation"], "temperature_2m": d["hourly"]["temperature_2m"]}


def load_weather(download):
    if download or not WEATHER_CACHE.exists():
        cache = {"source": "Open-Meteo historical archive, default model, timezone Europe/Zurich",
                 "downloaded": date.today().isoformat(), "cities": {}}
        for city in CITIES:
            if city == "Basel":
                continue
            print("downloading", city)
            cache["cities"][city] = fetch_weather(city)
        WEATHER_CACHE.write_text(json.dumps(cache))
    cache = json.loads(WEATHER_CACHE.read_text())
    temps = {city: v["temperature_2m"] for city, v in cache["cities"].items()}
    elev = {city: v["elevation"] for city, v in cache["cities"].items()}
    with open(ROOT / "data" / "reference_house_2025_hourly.csv") as f:
        temps["Basel"] = [float(r["temperature_2m_c"]) for r in csv.DictReader(f)]
    elev["Basel"] = 247.0
    for city, t in temps.items():
        assert len(t) == H, (city, len(t))
    return temps, elev


def load_weather_year(year):
    """Any other year: Open-Meteo archive per city via scheduler.weather (cached, 29 Feb dropped)."""
    from scheduler.weather import temperatures, CACHE
    temps, elev = {}, {}
    for city, c in CITIES.items():
        temps[city] = temperatures(c["lat"], c["lon"], year)
        doc = json.loads((CACHE / f"{c['lat']:.3f}_{c['lon']:.3f}_{year}.json").read_text())
        elev[city] = doc["elevation"]
    return temps, elev


def demand_profile(temps, scale):
    """Case formula (scripts/build_reference_profile.py), scaled by house size."""
    out = []
    for d in range(365):
        day = temps[d * 24:(d + 1) * 24]
        heating = sum(day) / 24 < 12
        for t in day:
            sh = max(0.0, 10 * (20 - t) / 25.6) if heating else 0.0
            out.append(scale * (sh + 0.5))
    return out


def permit_plan(demand, n, tank):
    """Follow-heat with every allowed server running (analysis/baseline_sweep.py)."""
    soc, plan = 0.0, []
    for d in demand:
        k = min(n, int((d + tank - soc) / Q1 + 1e-9))
        avail = soc + k * Q1
        soc = avail - min(d, avail)
        plan.append(k)
    return plan


def simulate_site(si, site, demand, rng, jobs):
    n, tank = site["servers"], site["tank_kwh"]
    plan = permit_plan(demand, n, tank)
    cap = [2 * k for k in plan]                      # half server-hours per hour
    pre = [0]
    for c in cap:
        pre.append(pre[-1] + c)
    for c in cap[:200]:                              # beyond 31 Dec: January's plan stands in for next winter
        pre.append(pre[-1] + c)

    # offers
    arrivals = [[] for _ in range(H)]
    for d in range(365):
        day_units = sum(cap[d * 24:(d + 1) * 24]) * rng.lognormvariate(0, 0.15)
        for ti, jt in enumerate(JOB_TYPES):
            count = int(round(0.5 * day_units / jt["units"]))
            for _ in range(count):
                arrivals[d * 24 + rng.randrange(24)].append(ti)

    pend_dl, pend = [], []                           # sorted by deadline: [deadline, jid, remaining]
    soc = 0.0
    run_units, soc_arr, served_arr = [], [], []
    slots = []
    prev_slot = [-1] * n
    for t in range(H):
        # admission
        for ti in arrivals[t]:
            jt = JOB_TYPES[ti]
            dl = t + jt["due_h"]
            jid = len(jobs["type"])
            pos = bisect.bisect_right(pend_dl, dl)
            need_before = sum(p[2] for p in pend[:pos])
            ok = need_before + jt["units"] <= pre[dl] - pre[t]
            reason = 0
            if ok:
                cum = need_before + jt["units"]
                for p in pend[pos:]:
                    cum += p[2]
                    if cum > pre[p[0]] - pre[t]:
                        ok, reason = False, 2       # would push an admitted job past its deadline
                        break
            else:
                reason = 1                           # not enough heat before due
            jobs["site"].append(si)
            jobs["type"].append(ti)
            jobs["arrive"].append(t)
            jobs["free"].append(max(0, pre[dl] - pre[t] - need_before))
            jobs["start"].append(-1)
            jobs["finish"].append(-1)
            jobs["status"].append(0 if ok else reason)  # 0 admitted, 1/2 refused, 3 missed
            if ok:
                pend_dl.insert(pos, dl)
                pend.insert(pos, [dl, jid, jt["units"]])
        # execution: earliest deadline first, at most the planned permit
        left = cap[t]
        work = []
        for p in pend:
            if left == 0:
                break
            u = min(p[2], left)
            p[2] -= u
            left -= u
            work.append((p[1], u))
            if jobs["start"][p[1]] < 0:
                jobs["start"][p[1]] = t
        used_units = cap[t] - left
        # server slots, sticky to last hour's server
        need_slots = {}
        for jid, u in work:
            need_slots[jid] = need_slots.get(jid, 0) + u
        slot = [-1] * n
        fill = [0] * n
        for s in range(n):
            j = prev_slot[s]
            if j in need_slots and need_slots[j] > 0:
                take = min(2, need_slots[j])
                slot[s], fill[s] = j, take
                need_slots[j] -= take
        s = 0
        for jid, _ in work:
            while need_slots.get(jid, 0) > 0:
                while s < n and fill[s] >= 2:
                    s += 1
                if s >= n:
                    break
                take = min(2 - fill[s], need_slots[jid])
                if slot[s] < 0:
                    slot[s] = jid
                fill[s] += take
                need_slots[jid] -= take
        slots.append(slot)
        prev_slot = slot
        # heat balance
        heat = used_units * 0.5 * Q1
        avail = soc + heat
        served = min(demand[t], avail)
        soc = avail - served
        assert soc <= tank + 1e-6
        run_units.append(used_units)
        soc_arr.append(soc)
        served_arr.append(served)
        # finish / miss
        keep_dl, keep = [], []
        for p in pend:
            if p[2] == 0:
                jobs["finish"][p[1]] = t + 1
            elif p[0] <= t + 1:
                jobs["status"][p[1]] = 3
                jobs["finish"][p[1]] = t + 1
            else:
                keep_dl.append(p[0])
                keep.append(p)
        pend_dl, pend = keep_dl, keep
    for p in pend:                                   # still running when the replay ends
        jobs["finish"][p[1]] = H
    return plan, run_units, soc_arr, served_arr, slots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--year", type=int, default=2025)
    args = ap.parse_args()
    global OUT
    if args.year == 2025:
        temps, elev = load_weather(args.download)
    else:
        temps, elev = load_weather_year(args.year)
        OUT = OUT / f"y{args.year}"
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sites").mkdir(exist_ok=True)

    sites = []
    counters = {}
    for i, (city, district, lat, lon, btype) in enumerate(SITES):
        code = CITIES[city]["code"]
        counters[code] = counters.get(code, 0) + 1
        if i == 0:
            scale, n, tank = 1.0, 6, 35.0
        else:
            scale = round(rng.uniform(0.6, 1.5), 2)
            n = max(3, min(10, round(scale * 6 + rng.choice([-1, 0, 0, 1]))))
            tank = float(rng.choice([20, 35, 35, 50, 70]))
        sites.append({
            "id": f"{code}-{counters[code]:02d}", "city": city, "district": district,
            "canton": CITIES[city]["canton"], "lat": lat, "lon": lon, "building": btype,
            "scale": scale, "servers": n, "tank_kwh": tank,
            "reference": i == 0, "elevation_m": elev[city],
        })

    jobs = {k: [] for k in ("site", "type", "arrive", "start", "finish", "status", "free")}
    hourly = []
    all_slots = []
    for si, s in enumerate(sites):
        demand = demand_profile(temps[s["city"]], s["scale"])
        plan, run_units, soc, served, slots = simulate_site(si, s, demand, rng, jobs)
        tot_d = sum(demand)
        s["year"] = {
            "demand_kwh": round(tot_d),
            "served_kwh": round(sum(served)),
            "coverage": round(sum(served) / tot_d, 4),
            "permit_server_h": sum(plan),
            "run_server_h": round(sum(run_units) / 2),
            "utilisation": round(sum(run_units) / 2 / (s["servers"] * H), 4),
        }
        hourly.append({
            "demand": [round(d * 10) for d in demand],
            "permit": plan,
            "run": run_units,
            "soc": [round(x * 10) for x in soc],
            "served": [round(x * 10) for x in served],
        })
        all_slots.append(slots)
        print(f"{s['id']:<6} {s['city']:<11} N={s['servers']:>2} tank={s['tank_kwh']:>4.0f} "
              f"scale={s['scale']:.2f} cover={s['year']['coverage']*100:5.1f}% util={s['year']['utilisation']*100:5.1f}%")

    # BS-01 check against analysis/baseline_sweep.py (follow, N=6): its permits are the same plan
    st = jobs["status"]
    totals = {
        "sites": len(sites),
        "servers": sum(s["servers"] for s in sites),
        "demand_kwh": sum(s["year"]["demand_kwh"] for s in sites),
        "served_kwh": sum(s["year"]["served_kwh"] for s in sites),
        "run_server_h": sum(s["year"]["run_server_h"] for s in sites),
        "permit_server_h": sum(s["year"]["permit_server_h"] for s in sites),
        "jobs_offered": len(st),
        "jobs_admitted": sum(1 for x in st if x in (0, 3)),
        "jobs_refused": sum(1 for x in st if x in (1, 2)),
        "jobs_missed": sum(1 for x in st if x == 3),
        "dumped_kwh": 0,
    }
    totals["coverage"] = round(totals["served_kwh"] / totals["demand_kwh"], 4)
    totals["utilisation"] = round(totals["run_server_h"] / (totals["servers"] * H), 4)
    print(totals)

    temps_out = {c: [round(x * 10) for x in temps[c]] for c in CITIES}
    fleet = {
        "meta": {
            "title": "DigitalHeat Swiss scenario fleet",
            "scenario": True,
            "year": args.year,
            "seed": SEED,
            "generator": "scripts/build_fleet_scenario.py",
            "hours": H,
            "start": "2025-01-01T00:00",
            "time_note": "UTC+1 all year (Open-Meteo fixed offset)",
            "constants": {"server_kw": P_EL, "heat_recovery": REC, "price_chf_kwh": PRICE,
                          "heat_value_chf_kwh": round(HEAT_VALUE, 4)},
            "scales": {"demand": 10, "soc": 10, "served": 10, "temp": 10, "run": "half server-hours"},
            "job_types": JOB_TYPES,
            "weather": (f"Open-Meteo archive {args.year}, default model" + ("; Basel from data/raw/openmeteo_basel_2025_hourly.csv" if args.year == 2025 else "; 29 Feb dropped in leap years")),
        },
        "cities": [{"name": c, **{k: v for k, v in CITIES[c].items()}, "elevation_m": elev[c]} for c in CITIES],
        "sites": sites,
        "totals": totals,
        "hourly": hourly,
        "temps": temps_out,
    }
    # jobs in arrival order, in weekly chunks (a job is live at most 168 h after arrival)
    order = sorted(range(len(st)), key=lambda j: (jobs["arrive"][j], jobs["site"][j]))
    newid = [0] * len(order)
    for new, old in enumerate(order):
        newid[old] = new
    (OUT / "jobs").mkdir(exist_ok=True)
    weeks = []
    for w in range((H + 167) // 168):
        ids = [j for j in order if w * 168 <= jobs["arrive"][j] < (w + 1) * 168]
        chunk = {"week": w, "first": newid[ids[0]] if ids else 0, "count": len(ids)}
        for k in jobs:
            chunk[k] = [jobs[k][j] for j in ids]
        (OUT / "jobs" / f"w{w:02d}.json").write_text(json.dumps(chunk, separators=(",", ":")))
        weeks.append({"week": w, "first": chunk["first"], "count": len(ids)})
    for s, slots in zip(sites, all_slots):
        remapped = [[newid[j] if j >= 0 else -1 for j in row] for row in slots]
        (OUT / "sites" / f"{s['id']}.json").write_text(
            json.dumps({"id": s["id"], "slots": remapped}, separators=(",", ":")))
    # fleet-wide daily job counts
    daily = {"offered": [0] * 365, "refused": [0] * 365, "admitted_server_h": [0.0] * 365}
    for j in range(len(st)):
        d = jobs["arrive"][j] // 24
        daily["offered"][d] += 1
        if st[j] in (1, 2):
            daily["refused"][d] += 1
        else:
            daily["admitted_server_h"][d] += JOB_TYPES[jobs["type"][j]]["units"] / 2
    fleet["daily_jobs"] = daily
    fleet["job_weeks"] = weeks
    (OUT / "fleet.json").write_text(json.dumps(fleet, separators=(",", ":"), ensure_ascii=False))
    for p in (OUT / "fleet.json", OUT / "jobs" / "w46.json", OUT / "sites" / "BS-01.json"):
        print(p.relative_to(ROOT), p.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
