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


class ReferenceYear(unittest.TestCase):
    def test_reference_house_2025(self):
        r = run(REFERENCE, 2025, series=False)["fleet"]
        self.assertEqual(r["servers"], 4)
        self.assertEqual(r["jobs_missed"], 0)
        self.assertEqual(r["dumped_kwh"], 0)
        self.assertAlmostEqual(r["break_even_chf_per_server_h"], 0.3325 - REC * 0.3325 / 2.5, places=3)
        self.assertGreater(r["coverage"], 0.5)


if __name__ == "__main__":
    unittest.main()
