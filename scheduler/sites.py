"""Site types and their hourly heat demand (kW, = kWh per hour).

Every model uses the case's heating-day rule (a day whose mean temperature is below
12 °C) where space heating is involved, so all sites react to the same weather signal.

    house       the case's reference house: 10 kW x (20 - T) / 25.6 on heating days + 0.5 kW hot water
    family      a 4-5 person household in the same building, with BDEW single-family daily curves: space
                heating with a night setback and morning/evening peaks (same daily total as the case
                formula), and hot water 3 kWh per person and day (the case's 12 kWh for four)
    cityhouse   real Basel house with 4 apartments, fitted to its gas bills 2021-2025
                (data/city_house_model.json, scripts/calibrate_city_house.py)
    hospital    hospital ward: hot water 2,500 kWh per bed and year, flat over the year
                (hospital DHW study, Applied Thermal Engineering), plus ward heating 1.2 x house
    spa         indoor pool + spa: pool water 600 kWh/m2 a (Passive House pool guide 400-700),
                showers and sauna while open 09-21, hall air kept at 30 °C; 1,800 kWh per m2 of
                water a year on Basel 2025 (published range 1,300-3,100)
    greenhouse  heated vegetable greenhouse held at 18 °C: 300 kWh/m2 a on Basel 2025
                (Dutch sector average 306-334 kWh/m2 a, Wageningen)
    office      office building, office-hours demand: BDEW office profile (GKO): morning boost 06-09,
                night setback, lower weekends; 60 kWh/m2 a space heat on Basel 2025, 5 kWh/m2 a
                hot water in office hours (our assumptions, see docs/business-model.md)
    pharma      pharma/biotech lab and pilot plant: HVAC reheat 24/7 all year (labs run on 100 %
                outside air), process water (cleaning-in-place, purified water) Mon-Fri 06-22,
                space heat 24/7; 100 + 60 + 50 kWh per m2 of lab a year (our assumptions)

Every site also has a supply temperature it asks for (`supply_c`). Server heat is used only
where that is at most the server loop's outlet (scheduler.core.SERVER_OUTLET_C): DigitalHeat
uses no heat pump and no booster, so a site that needs hotter water cannot take server heat.

Coefficients that depend on the climate are fixed once on Basel 2025, so another year
or place changes the demand through its weather, as in the real building.
"""

import csv
import datetime
import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
H = 8760

KINDS = {
    "house": {"label": "House", "servers": 11, "tank_kwh": 35, "size": 1.0, "size_unit": "x reference house",
              "supply_c": 55},
    "family": {"label": "Family home, 5 people", "servers": 4, "tank_kwh": 35, "size": 5, "size_unit": "people",
               "supply_c": 55},
    "cityhouse": {"label": "City house, 4 flats", "servers": 6, "tank_kwh": 70, "size": 1.0,
                  "size_unit": "x real Basel building", "supply_c": 60},
    "hospital": {"label": "Hospital", "servers": 15, "tank_kwh": 70, "size": 30, "size_unit": "beds", "supply_c": 60},
    "spa": {"label": "Spa & pool", "servers": 11, "tank_kwh": 50, "size": 40, "size_unit": "m2 of water",
            "supply_c": 40},
    "greenhouse": {"label": "Greenhouse", "servers": 10, "tank_kwh": 70, "size": 300, "size_unit": "m2",
                   "supply_c": 40},
    "office": {"label": "Office", "servers": 8, "tank_kwh": 70, "size": 1500, "size_unit": "m2 floor",
               "supply_c": 45},
    "pharma": {"label": "Pharma lab", "servers": 14, "tank_kwh": 70, "size": 500, "size_unit": "m2 of lab",
               "supply_c": 60},
}

HOSP_DHW_PER_BED = 2500.0  # kWh per bed and year
HOSP_SPACE_SCALE = 1.2
HOSP_SHAPE = [0.45, 0.4, 0.4, 0.4, 0.5, 0.8, 1.4, 1.7, 1.6, 1.4, 1.2, 1.1, 1.2, 1.1, 1, 1, 1.1, 1.3, 1.4, 1.3, 1.1, 0.9, 0.7, 0.55]
POOL_WATER = 600.0  # kWh per m2 of water and year
SPA_DHW_PER_M2 = 450.0  # showers + sauna, kWh per m2 of water and year, open 09-21
SPA_HALL_PER_M2 = 750.0  # hall air at 30 °C, kWh per m2 of water and year on Basel 2025
GREENHOUSE_PER_M2 = 300.0  # kWh per m2 and year on Basel 2025, held at 18 °C

# Daily shapes (24 values, mean 1): BDEW/VKU/GEODE standard gas load profiles (SigLinDe), day class 6-10 °C,
# from oemof demandlib's shlp_hour_factors.csv; see research_notes/customers.md, Part 3.
FAMILY_DHW_PER_PERSON = 3.0  # kWh per person and day = the case's 12 kWh/day for four (SIA 385/2: 40-55 l at 60 °C)
FAMILY_HEAT_SHAPE = [0.47, 0.49, 0.51, 0.59, 0.80, 1.18, 1.49, 1.38, 1.26, 1.16, 1.08, 1.04,  # EFH, 6-10 °C
                     1.02, 1.02, 1.05, 1.10, 1.16, 1.23, 1.26, 1.26, 1.20, 1.03, 0.69, 0.52]
FAMILY_DHW_SHAPE = [0.24, 0.24, 0.26, 0.38, 0.72, 1.63, 2.05, 1.77, 1.45, 1.44, 1.19, 1.15,   # EFH, 16-20 °C day
                    1.06, 0.94, 0.89, 0.85, 0.95, 1.01, 1.12, 1.25, 1.26, 1.06, 0.72, 0.37]   # (mostly hot water)
OFFICE_WEEKDAY_SHAPE = [0.70, 0.76, 0.76, 0.87, 1.11, 1.20, 1.49, 1.47, 1.41, 1.28, 1.19, 1.12,  # GKO Mon-Fri
                        1.06, 1.03, 1.01, 0.97, 0.92, 0.93, 0.89, 0.86, 0.84, 0.77, 0.67, 0.69]
OFFICE_SUNDAY_SHAPE = [0.69, 0.84, 0.77, 1.17, 1.52, 1.72, 1.15, 1.15, 1.07, 1.05, 0.99, 0.97,   # GKO Sun (also Sat)
                       0.91, 0.92, 0.92, 0.89, 0.92, 1.06, 0.96, 0.92, 0.98, 0.84, 0.76, 0.81]
OFFICE_DAY_LEVEL = [1.035, 1.052, 1.045, 1.049, 0.988, 0.886, 0.944]  # GKO weekday factors, Mon-Sun
OFFICE_SPACE_PER_M2 = 60.0  # kWh per m2 floor and year on Basel 2025 (our assumption: Swiss stock 120-280,
                            # new SIA 380/1 ~28-35; a renovated mid-age office)
OFFICE_DHW_PER_M2 = 5.0     # kWh per m2 floor and year, Mon-Fri 07-18 (our assumption)
# Pharma lab (our assumption): reheat 24/7, process water Mon-Fri 06-22, space heat 24/7.
PHARMA_REHEAT_PER_M2 = 100.0
PHARMA_PROCESS_PER_M2 = 60.0
PHARMA_SPACE_PER_M2 = 50.0  # on Basel 2025


@dataclass
class Site:
    id: str
    kind: str
    name: str
    lat: float
    lon: float
    servers: int
    tank_kwh: float
    size: float
    supply_c: float = 55.0      # supply temperature the site asks for (°C), heat input of the scheduler
    drycooler_kw: float = 0.0   # outdoor dry cooler: heat it can reject (kW); 0 = none

    @classmethod
    def from_dict(cls, d):
        k = KINDS[d["kind"]]
        return cls(id=d["id"], kind=d["kind"], name=d.get("name") or k["label"], lat=float(d["lat"]),
                   lon=float(d["lon"]), servers=int(d.get("servers", k["servers"])),
                   tank_kwh=float(d.get("tank_kwh", k["tank_kwh"])), size=float(d.get("size", k["size"])),
                   supply_c=float(d.get("supply_c", k["supply_c"])),
                   drycooler_kw=float(d.get("drycooler_kw", 0.0)))

    def to_dict(self):
        return asdict(self)


@lru_cache(maxsize=1)
def _basel_2025():
    with open(ROOT / "data" / "reference_house_2025_hourly.csv") as f:
        return [float(r["temperature_2m_c"]) for r in csv.DictReader(f)]


@lru_cache(maxsize=None)
def weekdays(year):
    """Weekday (Mon = 0) of each of the 365 model days; 29 February is dropped in leap years,
    as in scheduler.weather."""
    d, out = datetime.date(year, 1, 1), []
    while d.year == year:
        if not (d.month == 2 and d.day == 29):
            out.append(d.weekday())
        d += datetime.timedelta(days=1)
    return tuple(out)


def office_schedule(wd, h):
    """Heating profile factor of an office for weekday wd (Mon = 0) and hour h (BDEW GKO)."""
    shape = OFFICE_WEEKDAY_SHAPE if wd < 5 else OFFICE_SUNDAY_SHAPE
    return OFFICE_DAY_LEVEL[wd] * shape[h]


def _heating_hours(temps):
    """Heating degree-hours per hour with the case's heating-day rule."""
    out = [0.0] * H
    for d in range(365):
        day = temps[d * 24:(d + 1) * 24]
        if sum(day) / 24 < 12:
            for h in range(24):
                out[d * 24 + h] = max(0.0, 20 - day[h])
    return out


@lru_cache(maxsize=1)
def _climate_coefficients():
    t = _basel_2025()
    hall = sum(max(0.0, 30 - x) for x in t)
    green = sum(max(0.0, 18 - x) for x in t)
    dh = _heating_hours(t)
    wd = weekdays(2025)
    office = sum(dh[i] * office_schedule(wd[i // 24], i % 24) for i in range(H))
    return SPA_HALL_PER_M2 / hall, GREENHOUSE_PER_M2 / green, OFFICE_SPACE_PER_M2 / office, PHARMA_SPACE_PER_M2 / sum(dh)


@lru_cache(maxsize=1)
def _city_house():
    return json.loads((ROOT / "data" / "city_house_model.json").read_text())


def demand(site, temps, year=2025):
    """Hourly heat demand in kW for one site and 8,760 temperatures of `year`."""
    hall_k, green_k, office_k, pharma_k = _climate_coefficients()
    ch = _city_house()
    wd = weekdays(int(year))
    hosp_mean = sum(HOSP_SHAPE) / 24
    out = [0.0] * H
    for d in range(365):
        day = temps[d * 24:(d + 1) * 24]
        heating = sum(day) / 24 < 12
        workday = wd[d] < 5
        if site.kind == "family" and heating:  # reshape the day, keep the case formula's daily total
            base = [10 * max(0.0, 20 - x) / 25.6 for x in day]
            shaped = sum(b * f for b, f in zip(base, FAMILY_HEAT_SHAPE))
            norm = sum(base) / shaped if shaped > 0 else 0.0
        for h in range(24):
            T = day[h]
            dh = max(0.0, 20 - T) if heating else 0.0  # heating degree-hours, case rule
            if site.kind == "house":
                v = site.size * (10 * dh / 25.6 + 0.5)
            elif site.kind == "family":
                space = 10 * dh / 25.6 * FAMILY_HEAT_SHAPE[h] * norm if heating else 0.0
                v = space + site.size * FAMILY_DHW_PER_PERSON / 24 * FAMILY_DHW_SHAPE[h]
            elif site.kind == "cityhouse":
                v = site.size * (ch["base_kw"] + ch["k_kw_per_K"] * dh)
            elif site.kind == "hospital":
                dhw = site.size * HOSP_DHW_PER_BED / H * HOSP_SHAPE[h] / hosp_mean
                v = dhw + HOSP_SPACE_SCALE * 10 * dh / 25.6 * site.size / 30
            elif site.kind == "spa":
                open_ = 9 <= h < 21
                v = site.size * (POOL_WATER / H + (SPA_DHW_PER_M2 / (365 * 12) if open_ else 0.0)
                                 + hall_k * max(0.0, 30 - T))
            elif site.kind == "greenhouse":
                v = site.size * green_k * max(0.0, 18 - T)
            elif site.kind == "office":
                dhw = OFFICE_DHW_PER_M2 / (261 * 11) if workday and 7 <= h < 18 else 0.0
                v = site.size * (office_k * dh * office_schedule(wd[d], h) + dhw)
            elif site.kind == "pharma":
                process = PHARMA_PROCESS_PER_M2 / (261 * 16) if workday and 6 <= h < 22 else 0.0
                v = site.size * (PHARMA_REHEAT_PER_M2 / H + process + pharma_k * dh)
            else:
                raise ValueError(site.kind)
            out[d * 24 + h] = v
    return out


def size_sites(sites, sites_in, temps, dem, year=2025, sizing=None, rec=0.8):
    """Live-demo sizing, shared by scheduler.day and scheduler.balance so they cannot drift.

    sites: Site objects (servers may be changed in place); sites_in: the request dicts; temps, dem: per site
    8,760 temperatures and hourly demands. Returns the (possibly scaled) demands.
      x_house > 0   scale the site's hourly demand so its coldest hour needs x_house times the house's
                    (same place and weather): the building keeps its own daily and yearly shape.
      sizing="peak" every site gets enough servers for its highest hour: servers = ceil(peak kW / rec).
      sizing="tank" every site gets the fewest servers that, with its tank, cover every hour of the year
                    (tank_servers): the tank carries heat into the cold hours, so fewer servers than "peak".
    Without either, the demands and servers are returned unchanged.
    """
    import math
    dem = list(dem)
    for i, d in enumerate(sites_in):
        x = float(d.get("x_house") or 0)
        if x > 0 and max(dem[i]) > 0:
            house = Site.from_dict({"id": "house", "kind": "house", "lat": sites[i].lat, "lon": sites[i].lon})
            f = x * max(demand(house, temps[i], year)) / max(dem[i])
            dem[i] = [v * f for v in dem[i]]
    if sizing == "peak":
        for s, d in zip(sites, dem):
            s.servers = math.ceil(max(d) / rec - 1e-9)
    elif sizing == "tank":
        for s, d in zip(sites, dem):
            s.servers = tank_servers(d, s.tank_kwh, rec)
    return dem


def tank_servers(dem, tank_kwh, rec=0.8):
    """The fewest servers that cover every hour of `dem` (kW per hour) with a tank of `tank_kwh`.

    Mirrors the scheduler's heat permit (scheduler.core step 2): every hour it runs as many whole servers
    as the demand plus the tank's free room can take, at most n. The tank starts the year at the level it
    ends the year with (a real building's tank isn't empty on New Year's morning). The scheduler itself
    starts from an empty tank, so its first hours of 1 January can fall short by a few kWh (reference house,
    11 servers: 9 kWh, 99.97 % covered). n servers are enough if every hour is served.
    """
    import math
    eps = 1e-9

    def year(n, soc):
        ok = True
        for d in dem:
            on = min(n, math.floor((d + tank_kwh - soc) / rec + eps))
            avail = soc + on * rec
            ok = ok and avail >= d - 1e-6
            soc = min(tank_kwh, max(0.0, avail - d))
        return ok, soc

    def covers(n):
        return year(n, year(n, 0.0)[1])[0]  # second pass from the first year's 31 December level

    lo = max(0, math.ceil(sum(dem) / len(dem) / rec - eps))  # fewer can't keep up over the year
    hi = math.ceil(max(dem) / rec - eps)  # "peak" always covers
    while lo < hi:
        mid = (lo + hi) // 2
        if covers(mid):
            hi = mid
        else:
            lo = mid + 1
    return hi
