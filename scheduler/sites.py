"""Site types and their hourly heat demand (kW, = kWh per hour).

Every model uses the case's heating-day rule (a day whose mean temperature is below
12 °C) where space heating is involved, so all sites react to the same weather signal.

    house       the case's reference house: 10 kW x (20 - T) / 25.6 on heating days + 0.5 kW hot water
    cityhouse   real Basel house with 4 apartments, fitted to its gas bills 2021-2025
                (data/city_house_model.json, scripts/calibrate_city_house.py)
    hospital    hospital ward: hot water 2,500 kWh per bed and year, flat over the year
                (hospital DHW study, Applied Thermal Engineering), plus ward heating 1.2 x house
    spa         indoor pool + spa: pool water 600 kWh/m2 a (Passive House pool guide 400-700),
                showers and sauna while open 09-21, hall air kept at 30 °C; 1,800 kWh per m2 of
                water a year on Basel 2025 (published range 1,300-3,100)
    greenhouse  heated vegetable greenhouse held at 18 °C: 300 kWh/m2 a on Basel 2025
                (Dutch sector average 306-334 kWh/m2 a, Wageningen)

Coefficients that depend on the climate are fixed once on Basel 2025, so another year
or place changes the demand through its weather, as in the real building.
"""

import csv
import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
H = 8760

KINDS = {
    "house": {"label": "House", "servers": 4, "tank_kwh": 35, "size": 1.0, "size_unit": "x reference house"},
    "cityhouse": {"label": "City house, 4 flats", "servers": 6, "tank_kwh": 70, "size": 1.0, "size_unit": "x real Basel building"},
    "hospital": {"label": "Hospital", "servers": 15, "tank_kwh": 70, "size": 30, "size_unit": "beds"},
    "spa": {"label": "Spa & pool", "servers": 11, "tank_kwh": 50, "size": 40, "size_unit": "m2 of water"},
    "greenhouse": {"label": "Greenhouse", "servers": 10, "tank_kwh": 70, "size": 300, "size_unit": "m2"},
}

HOSP_DHW_PER_BED = 2500.0  # kWh per bed and year
HOSP_SPACE_SCALE = 1.2
HOSP_SHAPE = [0.45, 0.4, 0.4, 0.4, 0.5, 0.8, 1.4, 1.7, 1.6, 1.4, 1.2, 1.1, 1.2, 1.1, 1, 1, 1.1, 1.3, 1.4, 1.3, 1.1, 0.9, 0.7, 0.55]
POOL_WATER = 600.0  # kWh per m2 of water and year
SPA_DHW_PER_M2 = 450.0  # showers + sauna, kWh per m2 of water and year, open 09-21
SPA_HALL_PER_M2 = 750.0  # hall air at 30 °C, kWh per m2 of water and year on Basel 2025
GREENHOUSE_PER_M2 = 300.0  # kWh per m2 and year on Basel 2025, held at 18 °C


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

    @classmethod
    def from_dict(cls, d):
        k = KINDS[d["kind"]]
        return cls(id=d["id"], kind=d["kind"], name=d.get("name") or k["label"], lat=float(d["lat"]),
                   lon=float(d["lon"]), servers=int(d.get("servers", k["servers"])),
                   tank_kwh=float(d.get("tank_kwh", k["tank_kwh"])), size=float(d.get("size", k["size"])))

    def to_dict(self):
        return asdict(self)


@lru_cache(maxsize=1)
def _basel_2025():
    with open(ROOT / "data" / "reference_house_2025_hourly.csv") as f:
        return [float(r["temperature_2m_c"]) for r in csv.DictReader(f)]


@lru_cache(maxsize=1)
def _climate_coefficients():
    t = _basel_2025()
    hall = sum(max(0.0, 30 - x) for x in t)
    green = sum(max(0.0, 18 - x) for x in t)
    return SPA_HALL_PER_M2 / hall, GREENHOUSE_PER_M2 / green


@lru_cache(maxsize=1)
def _city_house():
    return json.loads((ROOT / "data" / "city_house_model.json").read_text())


def demand(site, temps):
    """Hourly heat demand in kW for one site and 8,760 temperatures."""
    hall_k, green_k = _climate_coefficients()
    ch = _city_house()
    hosp_mean = sum(HOSP_SHAPE) / 24
    out = [0.0] * H
    for d in range(365):
        day = temps[d * 24:(d + 1) * 24]
        heating = sum(day) / 24 < 12
        for h in range(24):
            T = day[h]
            dh = max(0.0, 20 - T) if heating else 0.0  # heating degree-hours, case rule
            if site.kind == "house":
                v = site.size * (10 * dh / 25.6 + 0.5)
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
            else:
                raise ValueError(site.kind)
            out[d * 24 + h] = v
    return out
