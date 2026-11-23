"""Scheduler checks. Run: python3 -m unittest tests.test_scheduler"""

import math
import unittest

from scheduler.balance import REFERENCE, run
from scheduler.core import REC, JobType, Scheduler
from scheduler.sites import Site

TYPES = {
    "embed": JobType("embed", 0.81, 48, (), False),
    "rerank": JobType("rerank", 0.92, 4, (8, 11, 14, 17), True),
}


def site(id_, servers=4, tank=35.0):
    return Site(id=id_, kind="house", name=id_, lat=47.56, lon=7.59, servers=servers, tank_kwh=tank, size=1.0)


class HourRules(unittest.TestCase):
    def test_permit_and_energy_balance(self):
        demand = [[(h % 24) / 3 for h in range(96)]]  # 0..7.7 kW, every day
        sch = Scheduler([site("A")], demand, TYPES)
        soc = 0.0
        for t in range(96):
            h = sch.step(t)[0]
            self.assertEqual(h.permit, min(4, math.floor((h.demand + 35 - soc) / REC + 1e-9)))
            self.assertLessEqual(h.limit, h.permit)
            self.assertEqual(h.running, h.limit + h.forced)
            self.assertAlmostEqual(soc + h.heat, h.served + h.soc + h.dumped, places=9)
            self.assertLessEqual(h.soc, 35 + 1e-9)
            soc = h.soc

    def test_pause_when_heat_returns_soon(self):
        # heat every other hour: an embedding job is paused (SIGSTOP), never checkpointed
        demand = [[0.8 if t % 2 == 0 else 0.0 for t in range(48)]]
        sch = Scheduler([site("A", servers=1, tank=0.0)], demand, {"embed": TYPES["embed"]})
        acts = [a for t in range(48) for a in sch.step(t)[0].actions]
        self.assertIn("paused", [a[2] for a in acts])
        self.assertNotIn("checkpoint", [a[2] for a in acts])

    def test_checkpoint_and_move_when_heat_stays_away(self):
        # site A loses its heat for good after hour 2; site B has heat from hour 6: the job moves
        a = [1.0] * 2 + [0.0] * 46
        b = [0.0] * 6 + [1.0] * 42
        sch = Scheduler([site("A", 1, 0.0), site("B", 1, 0.0)], [a, b], {"embed": JobType("embed", 3.0, 48, (), False)})
        acts = []
        for t in range(48):
            for s, h in enumerate(sch.step(t)):
                acts += [(s, x[2]) for x in h.actions]
        self.assertIn((0, "checkpoint"), acts)
        self.assertIn((1, "moved"), acts)

    def test_deadline_job_runs_anyway_in_its_last_hour(self):
        # no heat at all: the rerank job is forced in its last possible hour, its heat dumped
        sch = Scheduler([site("A", 2, 0.0)], [[0.0] * 24], {"rerank": TYPES["rerank"]})
        hs = [sch.step(t)[0] for t in range(13)]
        self.assertEqual(hs[11].forced, 1)  # arrives 08:00, due 12:00, last start 11:00
        self.assertAlmostEqual(hs[11].dumped, REC)
        self.assertFalse(any(j.state == "missed" for j in sch.jobs))

    def test_rerank_goes_to_the_site_with_heat(self):
        a = [0.0] * 24  # origin site: no heat
        b = [5.0] * 24
        sch = Scheduler([site("A", 4, 0.0), site("B", 4, 0.0)], [a, b], {"rerank": TYPES["rerank"]})
        for t in range(9):
            sch.step(t)
        first = [j for j in sch.jobs if j.origin == 0][0]
        self.assertEqual(first.site, 1)
        self.assertFalse(first.forced)


class NewRules(unittest.TestCase):
    def test_replicas_never_share_a_site(self):
        twin = JobType("twin", 2.0, 24, (6,), True, replicas=2, per_site=False, count=3)
        sites = [site(x, 4, 0.0) for x in "ABC"]
        sch = Scheduler(sites, [[3.0] * 72] * 3, {"twin": twin, "embed": TYPES["embed"]})
        for t in range(72):
            sch.step(t)
            for g in sch.groups.values():
                placed = [j.site for j in g if j.site >= 0]
                self.assertEqual(len(placed), len(set(placed)))
        self.assertTrue(all(j.state == "done" for j in sch.jobs if j.type == "twin"))

    def test_replica_survives_outage(self):
        twin = JobType("twin", 3.0, 24, (0,), True, replicas=2, per_site=False, count=1)
        sites = [site("A", 2, 0.0), site("B", 2, 0.0)]
        sch = Scheduler(sites, [[2.0] * 24] * 2, {"twin": twin}, outages=[(0, 1, 5)])
        for t in range(24):
            sch.step(t)
        states = sorted(j.state for j in sch.jobs)
        self.assertEqual(states, ["done", "lost"])
        self.assertEqual(sum(j.restarts for j in sch.jobs), 0)

    def test_single_job_restarts_after_outage(self):
        sim = JobType("sim", 3.0, 24, (0,), True, per_site=False, count=1)
        sch = Scheduler([site("A", 1, 0.0), site("B", 1, 0.0)], [[2.0] * 24] * 2, {"sim": sim},
                        outages=[(0, 2, 3)])
        for t in range(24):
            sch.step(t)
        self.assertEqual(sch.jobs[0].restarts, 1)
        self.assertAlmostEqual(sch.lost_sh, 2.0)
        self.assertEqual(sch.jobs[0].state, "done")

    def test_hot_supply_gets_no_server_heat(self):
        hot = site("A")
        hot.supply_c = 70.0  # radiators that need 70 °C: no heat pump, so no server heat
        h = Scheduler([hot], [[5.0] * 24], TYPES).step(0)[0]
        self.assertEqual(h.permit, 0)
        self.assertEqual(h.running, 0)

    def test_partial_power_runs_part_load(self):
        demand = [[0.5] * 48]  # summer hot water only: one server at 0.5 / 0.8 = 62.5 % once the tank is full
        sch = Scheduler([site("A", 4, 0.0)], demand, {"embed": TYPES["embed"]}, partial=True)
        hs = [sch.step(t)[0] for t in range(48)]
        self.assertTrue(all(abs(h.running - 0.625) < 1e-9 for h in hs))
        self.assertTrue(all(h.on == 1 for h in hs))
        self.assertTrue(all(h.dumped < 1e-9 for h in hs))

    def test_dry_cooler_fill(self):
        s = site("A", 4, 0.0)
        s.drycooler_kw = 4.0
        sch = Scheduler([s], [[0.8] * 24], {"embed": TYPES["embed"]}, cool_fill=True)
        h = sch.step(0)[0]
        self.assertEqual(h.running, 4)  # 1 server for the house, 3 into the cooler (4 kW / 0.8 = 5 > 3 spare)
        self.assertEqual(h.cooled, 3)
        self.assertAlmostEqual(h.dumped, 3 * REC)
        self.assertAlmostEqual(h.fan_kwh, 0.02 * 3 * REC)

    def test_batch_waits_for_heat(self):
        # 10 batch jobs of 1 server-h, due in 10 days; no heat for 3 days, then plenty: none missed
        sim = JobType("sim", 1.0, 240, (0,), True, per_site=False, count=10)
        demand = [[0.0] * 72 + [3.2] * 200]
        sch = Scheduler([site("A", 4, 0.0)], demand, {"sim": sim})
        for t in range(24):
            sch.step(t)
        self.assertEqual(sum(j.state == "queued" for j in sch.jobs), 10)
        for t in range(24, 272):
            sch.step(t)
        self.assertFalse(any(j.state == "missed" for j in sch.jobs))
        self.assertGreater(max(j.finish for j in sch.jobs), 72)


class ReferenceYear(unittest.TestCase):
    def test_reference_house_2025(self):
        r = run(REFERENCE, 2025, series=False)["fleet"]
        self.assertEqual(r["servers"], 11)
        self.assertEqual(r["jobs_missed"], 0)
        self.assertEqual(r["dumped_kwh"], 0)
        self.assertAlmostEqual(r["break_even_chf_per_server_h"], 0.3325 - REC * 0.3325 / 2.5, places=3)
        self.assertGreater(r["coverage"], 0.999)  # short only in the first hours of 1 January (empty tank)

    def test_pay_off_thresholds_are_break_even_points(self):
        from scheduler.balance import electricity_price
        from scheduler.pricing import pays_off

        f = run(REFERENCE, 2025, series=False)["fleet"]
        m, e = f["money"], electricity_price()
        # selling exactly at the minimum price gives zero profit (up to its rounding to 0.001 CHF per server-hour)
        self.assertAlmostEqual(pays_off(f, e, e / 2.5, sell=m["min_price_chf_per_server_h"])["profit_chf"], 0,
                               delta=0.0005 * f["run_server_h"] + 1)
        # at the maximum electricity price, profit is zero too
        e2 = m["max_electricity_chf_kwh"]
        h = f["run_server_h"]
        g = dict(f, electricity_chf=h * e2, heat_value_chf=f["served_kwh"] * e2 / 2.5)
        self.assertAlmostEqual(pays_off(g, e2, e2 / 2.5)["profit_chf"], 0, delta=50)


if __name__ == "__main__":
    unittest.main()
