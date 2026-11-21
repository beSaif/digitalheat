"""Swiss scenario fleet for the operator dashboard.

    python3 scripts/build_fleet_scenario.py            # uses cached weather
    python3 scripts/build_fleet_scenario.py --download # re-fetch city weather

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
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard" / "public" / "data"
WEATHER_CACHE = ROOT / "data" / "raw" / "openmeteo_swiss_cities_2025_hourly.json"
SEED = 11

P_EL = 1.0
REC = 0.8
Q1 = REC * P_EL
PRICE = 0.3325
HEAT_VALUE = PRICE / 2.5
H = 8760

# ---------------------------------------------------------------- money (dashboard "Money" screen)
# Defaults only; the dashboard recomputes every figure from the hourly arrays with the same formulas
# (dashboard/lib/money.ts) when the operator moves a price.
#   electricity  = sold server-h x 1 kW x PRICE
#   heat value   = heat actually used (served kWh) x PRICE / 2.5                      (case rule)
#   break-even   = (electricity - heat share x heat value) / sold server-h           (case formula at share 1)
#   hardware/yr  = installed / life + maintenance + card failures + insurance + uplink   (no interest)
#   price needed = (hardware/yr + electricity - heat share x heat value) / sold server-h
# Hardware lines are the reference server on the cold-plate chain, central case, linear in servers N;
# coefficients read from analysis/r7_payback.py fixed_costs(n) (N=6: installed 212,574, fixed 5,903 CHF/yr).
# All hardware numbers are ASSUMPTIONS or estimates; see docs/overnight.md "Key numbers".
HW = {
    "installed_house_chf": 23874.2,      # house side: buffer, CDU, fresh-water station, DHW cylinder
    "installed_server_chf": 31449.98,    # per 1 kW reference server (4 x RTX PRO 4500 SE + platform + plates)
    "maint_house_chf_yr": 690.0,         # maintenance + leak reserve, one CDU loop
    "maint_server_chf_yr": 109.99,
    "cards_server_chf_yr": 204.58,       # card failures, 1.01 %/yr (PNY predicted MTBF), self-insured
    "insurance_share_yr": 0.01,          # of installed cost; no published rate found
    "uplink_house_chf_yr": 1200.0,       # internet line
    "life_y": 5,
}
# The 1 kW reference server (analysis/r4_machine.py sections 1-2, analysis/r5_chain.py; docs/overnight.md
# "Reference server, realism machine and installed cost"). Specs sourced, power and platform estimated.
SERVER = {
    "name": "Reference server",
    "chassis": "2U, single socket",
    "gpu": "4 × NVIDIA RTX PRO 4500 Blackwell Server Edition",
    "gpu_tdp_w": 165, "gpu_count": 4, "gpu_memory_gb": 32,
    "cpu": "AMD EPYC 9375F",
    "cooling": "cold plates on each card, warm-water loop to the house buffer (coolant ≤ 45 °C)",
    "wall_w": {"low": 751, "central": 955, "high": 1215},
    "card_chf": {"low": 3920, "central": 4819, "high": 5642},
    # central case, incl. 8.1 % VAT; r4_machine section 2 + r5_chain.installed(n, "DLC"). One box draws 955 W,
    # so one 1 kW server = 1/0.955 box = 31,450 CHF; house side 23,874 CHF per house.
    "box_lines_chf": [
        {"label": "4 GPU cards (post.ch, 4,819 each)", "chf": 19276, "kind": "sourced"},
        {"label": "Platform: chassis, CPU, RAM, PSU", "chf": 8000, "kind": "assumption"},
        {"label": "Cold plates, CPU plate, manifold, leak sensor", "chf": 2750, "kind": "assumption"},
    ],
    "house_lines_chf": [
        {"label": "House integration (38 % of BFE 2015 heat-pump system)", "chf": 14788, "kind": "computed"},
        {"label": "CDU: plate heat exchanger, pump group, controls", "chf": 3000, "kind": "assumption"},
        {"label": "Hot-water cylinder + element", "chf": 2919, "kind": "computed"},
        {"label": "Fresh-water station", "chf": 2000, "kind": "assumption"},
        {"label": "1,000 l buffer", "chf": 1167, "kind": "computed"},
    ],
    "bench": "MLPerf Inference v6.1, results 6.1-0017 (Cisco, same 4 cards) and 6.1-0056 (2U HPE, whisper)",
    "status": "card specs and prices sourced; wall power, platform and cooling parts estimated",
}
COMPUTE_PRICE = 1.35  # CHF per sold server-h, scenario only: always-on GPU host rate today, low end
                       # (0.48 USD/GPU-h x 80 % host share x 4.19 GPU-h x 0.8392 CHF/USD, r7_payback "host048")
OCC_ALT = 0.60         # occupancy of heat-permitted hours: Akash 2025 self-reported average (plan's lead line)
PRICE_REFS = [         # CHF per sold reference server-hour; from docs/overnight.md "Key numbers" / analysis/r7_payback.py, r8_draw.py
    {"label": "Spot host (SaladCloud ratio)", "lo": 0.74, "hi": 0.74, "kind": "assumption",
     "note": "RunPod 0.72 USD × Salad lowest/high 0.364 × 80 % host share"},
    {"label": "Interruptible, same work", "lo": 0.90, "hi": 2.00, "kind": "assumption",
     "note": "spot discount ratios (Azure CH 0.185, Google 0.38–0.41, Salad 0.36) applied to RunPod / Exoscale"},
    {"label": "GPU host, always-on hour", "lo": 1.35, "hi": 2.03, "kind": "sourced",
     "note": "80 % of 0.48–0.72 USD per GPU-h; a seller form a heat-following house cannot use"},
    {"label": "RunPod on-demand, same card", "lo": 2.53, "hi": 2.53, "kind": "sourced",
     "note": "0.72 USD per GPU-h, renter price, operator keeps 100 %"},
    {"label": "Hyperscaler spot list", "lo": 2.91, "hi": 4.10, "kind": "sourced",
     "note": "Azure CH / Google RTX PRO 6000 spot, whole VM; an upper bound"},
    {"label": "Swiss cloud on-demand (Exoscale)", "lo": 4.88, "hi": 4.88, "kind": "sourced",
     "note": "4 × RTX Pro 6000, zone CH-DK-2, excl. VAT"},
]


def hourDate_month(t):
    """Month index (0-11) of hour-of-year t, on the file's UTC+1 clock."""
    return (date(2025, 1, 1) + timedelta(hours=t)).month - 1


def hardware_year(n):
    inst = HW["installed_house_chf"] + HW["installed_server_chf"] * n
    fixed = (HW["maint_house_chf_yr"] + HW["maint_server_chf_yr"] * n + HW["cards_server_chf_yr"] * n
             + HW["insurance_share_yr"] * inst + HW["uplink_house_chf_yr"])
    return inst, fixed, inst / HW["life_y"] + fixed


def money(n, sold_h, served_kwh, permit_h, occ=None):
    """Year economics of one house. occ=None: as simulated; else sold = occ x permit hours, servers off when unsold."""
    f = 1.0 if occ is None else min(1.0, occ * permit_h / sold_h) if sold_h else 0.0
    sold = sold_h * f
    elec = sold * P_EL * PRICE
    heat = served_kwh * f * HEAT_VALUE
    inst, fixed, hw = hardware_year(n)
    return {
        "sold_server_h": round(sold),
        "electricity_chf": round(elec),
        "heat_value_chf": round(heat),
        "income_chf": round(sold * COMPUTE_PRICE),
        "breakeven_case": round((elec - heat) / sold, 4) if sold else None,
        "breakeven_homeowner": round(elec / sold, 4) if sold else None,
        "installed_chf": round(inst),
        "fixed_chf_yr": round(fixed),
        "price_needed": round((hw + elec - heat) / sold, 2) if sold else None,
        "margin_chf": round(sold * COMPUTE_PRICE - (elec - heat) - hw),
    }


# Work per reference server-hour (= per kWh at the wall), central wall power 955 W:
# analysis/r4_machine.py section 1 on MLPerf v6.1 6.1-0017 / 6.1-0056 (sourced throughputs).
# List prices: public US batch APIs, read in round 3 (analysis/r4_machine.py J1_USD_PER_AUDIO_H, J2_USD_PER_M_OUT).
USD_CHF = 0.8392  # ECB 20 Nov 2026
JOB_TYPES = [
    {"id": "J1", "name": "Transcription", "model": "whisper large-v3-turbo",
     "units": 1, "due_h": 24, "detail": "≈700 audio-hours",
     "service": {
         "what": "Speech-to-text for audio archives: broadcasters, courts, call centres, podcasts",
         "unit": "audio-hour", "unit_per_server_h": 1411, "unit_range": [1109, 1794],
         "checkpoint": "per audio file", "input": "audio files (≈0.86 TB a day per full house at 32 kbit/s)",
         "output": "timestamped text", "bench": "MLPerf v6.1 6.1-0017, whisper-large-v3, 61.1 samples/s",
         "list_usd": {"low": 0.012, "central": 0.020, "high": 0.045}, "list_unit": "audio-hour",
         "measured_on_laptop": "mlx_whisper large-v3-turbo, 25–27× real time, 1.3–1.5 Wh per audio-hour"}},
    {"id": "J2", "name": "LLM batch", "model": "llama-3.1-8B",
     "units": 8, "due_h": 168, "detail": "≈144 M output tokens",
     "service": {
         "what": "Offline text generation: summaries, classification, synthetic data, document extraction",
         "unit": "M output tokens", "unit_per_server_h": 35.89, "unit_range": [28.2, 45.63],
         "checkpoint": "per batch", "input": "prompt files (JSONL)", "output": "completions (JSONL)",
         "bench": "MLPerf v6.1 6.1-0017, llama3.1-8b fp4, 9,519 output tokens/s",
         "list_usd": {"low": 0.04, "central": 0.16, "high": 0.77}, "list_unit": "M output tokens",
         "measured_on_laptop": None}},
]  # units = half server-hours

# Real jobs that run and were measured on three team laptops (docs/workloads.md, data/measurements/combined.json).
# Not scheduled in this fleet scenario; shown on the Services screen as measured work.
MEASURED_JOBS = [
    {"id": "embed", "name": "Embeddings", "model": "all-MiniLM-L6-v2",
     "item": "abstract → 384-dim vector", "items_per_s": [51, 110], "j_per_item": 0.293,
     "items_per_server_h": 12.3e6, "items_per_job": 10e6, "server_h_per_job": 0.81, "due_h": 48},
    {"id": "rerank", "name": "Reranking", "model": "ms-marco-MiniLM-L6-v2",
     "item": "(query, abstract) pair → score", "items_per_s": [19.5, 43], "j_per_item": 0.660,
     "items_per_server_h": 5.5e6, "items_per_job": 5e6, "server_h_per_job": 0.92, "due_h": 4},
]

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
    args = ap.parse_args()
    temps, elev = load_weather(args.download)
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
        y = s["year"]
        s["money"] = money(s["servers"], y["run_server_h"], sum(served), y["permit_server_h"])
        s["money_occ60"] = money(s["servers"], y["run_server_h"], sum(served), y["permit_server_h"], OCC_ALT)
        hourly.append({
            "demand": [round(d * 100) for d in demand],
            "permit": plan,
            "run": run_units,
            "soc": [round(x * 10) for x in soc],
            "served": [round(x * 100) for x in served],
        })
        all_slots.append(slots)
        m, m60 = s["money"], s["money_occ60"]
        print(f"{s['id']:<6} {s['city']:<11} N={s['servers']:>2} tank={s['tank_kwh']:>4.0f} "
              f"scale={s['scale']:.2f} cover={s['year']['coverage']*100:5.1f}% util={s['year']['utilisation']*100:5.1f}% "
              f"elec={m['electricity_chf']:>6} heat={m['heat_value_chf']:>5} be={m['breakeven_case']:.4f} "
              f"need={m['price_needed']:.2f} need60={m60['price_needed']:.2f}")

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
    for k in ("electricity_chf", "heat_value_chf", "income_chf", "installed_chf", "fixed_chf_yr", "margin_chf"):
        totals[k] = sum(s["money"][k] for s in sites)
    sold = sum(s["money"]["sold_server_h"] for s in sites)
    hw = sum(hardware_year(s["servers"])[2] for s in sites)
    totals["breakeven_case"] = round((totals["electricity_chf"] - totals["heat_value_chf"]) / sold, 4)
    totals["price_needed"] = round((hw + totals["electricity_chf"] - totals["heat_value_chf"]) / sold, 2)
    print(totals)

    # per service (job type): what the fleet sold, refused and when
    services = []
    for ti, jt in enumerate(JOB_TYPES):
        ids = [j for j in range(len(st)) if jobs["type"][j] == ti]
        done = [j for j in ids if st[j] == 0 and jobs["finish"][j] >= 0]
        monthly = [0.0] * 12
        monthly_refused = [0.0] * 12
        for j in ids:
            m = hourDate_month(jobs["arrive"][j])
            if st[j] in (0, 3):
                monthly[m] += jt["units"] / 2
            elif st[j] in (1, 2):
                monthly_refused[m] += jt["units"] / 2
        per_site = [0.0] * len(sites)
        for j in ids:
            if st[j] in (0, 3):
                per_site[jobs["site"][j]] += jt["units"] / 2
        turn = sorted(jobs["finish"][j] - jobs["arrive"][j] for j in done)
        admitted_h = sum(monthly)
        services.append({
            "id": jt["id"],
            "offered": len(ids),
            "admitted": sum(1 for j in ids if st[j] in (0, 3)),
            "refused_heat": sum(1 for j in ids if st[j] == 1),
            "refused_conflict": sum(1 for j in ids if st[j] == 2),
            "missed": sum(1 for j in ids if st[j] == 3),
            "admitted_server_h": round(admitted_h),
            "refused_server_h": round(sum(monthly_refused)),
            "units_sold": round(admitted_h * jt["service"]["unit_per_server_h"]),
            "monthly_server_h": [round(x) for x in monthly],
            "monthly_refused_server_h": [round(x) for x in monthly_refused],
            "site_server_h": [round(x) for x in per_site],
            "turnaround_h": {"median": turn[len(turn) // 2], "p95": turn[int(len(turn) * 0.95)],
                             "max": turn[-1]} if turn else None,
        })
        print(jt["id"], {k: v for k, v in services[-1].items() if not isinstance(v, list)})

    temps_out = {c: [round(x * 10) for x in temps[c]] for c in CITIES}
    fleet = {
        "meta": {
            "title": "DigitalHeat Swiss scenario fleet",
            "scenario": True,
            "year": 2025,
            "seed": SEED,
            "generator": "scripts/build_fleet_scenario.py",
            "hours": H,
            "start": "2025-01-01T00:00",
            "time_note": "UTC+1 all year (Open-Meteo fixed offset)",
            "constants": {"server_kw": P_EL, "heat_recovery": REC, "price_chf_kwh": PRICE,
                          "heat_value_chf_kwh": round(HEAT_VALUE, 4)},
            "scales": {"demand": 100, "soc": 10, "served": 100, "temp": 10, "run": "half server-hours"},
            "job_types": JOB_TYPES,
            "measured_jobs": MEASURED_JOBS,
            "economics": {
                "electricity_chf_kwh": PRICE, "electricity_source": "ElCom 2026, IWB Basel, H4, total price",
                "heat_pump_cop": 2.5, "compute_price": COMPUTE_PRICE,
                "compute_price_note": "always-on GPU host rate today, low end; no buyer found for heat-gated hours",
                "occ_alt": OCC_ALT, "occ_alt_note": "Akash 2025 self-reported average GPU utilisation",
                "hardware": HW, "price_refs": PRICE_REFS, "server": SERVER,
            },
            "weather": "Open-Meteo archive 2025, default model; Basel from data/raw/openmeteo_basel_2025_hourly.csv",
        },
        "cities": [{"name": c, **{k: v for k, v in CITIES[c].items()}, "elevation_m": elev[c]} for c in CITIES],
        "sites": sites,
        "totals": totals,
        "services": services,
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
