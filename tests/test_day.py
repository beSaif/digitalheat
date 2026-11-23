"""The live demo's day recorder replays the yearly balance exactly. Run: python3 -m unittest tests.test_day"""

import math
import unittest

from scheduler.balance import DEFAULT_SITES, run
from scheduler.core import REC
from scheduler.day import run as day
from scheduler.sites import Site, demand, tank_servers
from scheduler.weather import temperatures

SITES = [dict(s, servers={"hospital": 15, "house": 4, "spa": 11}[s["kind"]]) for s in DEFAULT_SITES]
KEYS = ("demand", "soc", "served", "dumped", "permit", "limit", "running", "forced", "paused", "checkpointed", "moved_in", "started", "finished")


class DayMatchesBalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.year = run(SITES, 2025)

    def check(self, d, hour):
        rec = day(SITES, 2025, d, hour, 24)
        self.assertEqual(len(rec["hours"]), 24)
        for h in rec["hours"]:
            for i, x in enumerate(h["sites"]):
                for k in KEYS:
                    self.assertAlmostEqual(x[k], self.year["series"][i][k][h["t"]], places=3, msg=f"t={h['t']} site={i} {k}")
                ran = [j for j in h["jobs"] if j["ran"] and j["site"] == i]
                # every server the scheduler switched on runs a recorded job
                self.assertGreaterEqual(len(ran), round(x["running"] - 1e-9) if x["running"] else 0)
                for a in x["actions"]:
                    self.assertIn(a[2], ("start", "resume", "moved", "paused", "checkpoint", "forced"))

    def test_january_day(self):
        self.check(14, 6)

    def test_july_day(self):
        self.check(195, 6)

    def test_rerank_jobs_recorded(self):
        rec = day(SITES, 2025, 195, 6, 24)
        arrived = {j["id"] for h in rec["hours"] for j in h["jobs"] if j["type"] == "rerank" and j["arrive"] == h["t"]}
        self.assertEqual(len(arrived), 4 * len(SITES))  # 08, 11, 14, 17 h at every site


class Outage(unittest.TestCase):
    def test_site_down_runs_nothing_and_others_take_the_work(self):
        t0 = 14 * 24 + 6
        rec = day(SITES, 2025, 14, 6, 24, outages=[("BS-01", t0 + 3, 5)])
        for h in rec["hours"]:
            house = h["sites"][1]
            down = t0 + 3 <= h["t"] < t0 + 8
            self.assertEqual(house["down"], down)
            if down:
                self.assertEqual(house["running"], 0)
                self.assertFalse([j for j in h["jobs"] if j["ran"] and j["site"] == 1])


if __name__ == "__main__":
    unittest.main()


class SizedAgainstHouse(unittest.TestCase):
    """Live demo: x_house sizes a building against the house; summer heat goes to the year-round sites."""

    def test_racks_scale_with_x_house(self):
        sites = [{"id": k, "kind": k, "lat": 47.56, "lon": 7.59, "x_house": x}
                 for k, x in (("house", 1), ("hospital", 4), ("pharma", 5))]
        rec = day(sites, 2025, 195, 14, 1, sizing="peak")
        servers = {s["kind"]: s["servers"] for s in rec["sites"]}
        house = Site.from_dict({"id": "h", "kind": "house", "lat": 47.56, "lon": 7.59})
        peak = max(demand(house, temperatures(47.56, 7.59, 2025), 2025))  # the house's coldest hour, kW
        for kind, x in (("house", 1), ("hospital", 4), ("pharma", 5)):  # x times the house's peak heat
            self.assertEqual(servers[kind], math.ceil(x * peak / REC - 1e-9), kind)
        on = {s["kind"]: x["running"] for s, x in zip(rec["sites"], rec["hours"][0]["sites"])}
        self.assertLessEqual(on["house"], 2)  # July: hot water only
        self.assertGreater(on["pharma"], 10 * on["house"])

    def test_tank_sizing_covers_the_year_with_fewer_servers(self):
        sites = [dict(s, x_house={"hospital": 4, "house": 1, "spa": 3}[s["kind"]]) for s in DEFAULT_SITES]
        peak = {s["kind"]: s["servers"] for s in day(sites, 2025, 14, 8, 1, sizing="peak")["sites"]}
        tank = {s["kind"]: s["servers"] for s in day(sites, 2025, 14, 8, 1, sizing="tank")["sites"]}
        self.assertEqual(tank["house"], 11)  # the reference house: the pitch, the yearly figures and the demo agree
        for kind in tank:
            self.assertLess(tank[kind], peak[kind], kind)
        year = run(sites, 2025, series=False, sizing="tank")
        for s in year["sites"]:  # every building covered, short only in the first hours of 1 January (empty tank)
            self.assertGreater(s["year"]["coverage"], 0.999, s["kind"])
            self.assertEqual(s["year"]["dumped_kwh"], 0, s["kind"])

    def test_tank_servers_is_the_fewest_that_cover(self):
        house = Site.from_dict({"id": "h", "kind": "house", "lat": 47.56, "lon": 7.59})
        d = demand(house, temperatures(47.56, 7.59, 2025), 2025)
        self.assertEqual(tank_servers(d, 35), 11)
        self.assertEqual(tank_servers(d, 0), math.ceil(max(d) / REC - 1e-9))  # no tank: the peak rule
        self.assertEqual(tank_servers([1.0] * 48, 35), 2)  # 1 kW needs 1.25 servers: 2
