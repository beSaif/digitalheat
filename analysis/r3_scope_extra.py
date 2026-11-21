"""Round 3, weak point 'one scheduler, not a script': three checks r3_policy_check.py leaves open.

ASSESSMENT ONLY. Not the team's scheduler. Standard library only; nothing is edited.
Imports run(), pol(), permit_trace(), slot_pattern(), events() from analysis/r3_policy_check.py.

    python3 analysis/r3_scope_extra.py

A. Demo days at JOB level. r3_policy_check.py picked demo days from the permit pattern
   (every permit used). The live driver starts from the yearly run's state at 00:00 of the
   demo date, so the pattern the audience sees is the job-level one of whatever offer
   scenario the yearly run uses. Which July / January days show a heat pause AND a resume
   on the demo slot under BOTH saturating and heat-shaped (shaped100) offers?
B. Restart time as an accounting line instead of a scheduler rule: does
   (elec - heat value) / (sold h - starts x restart) of the run WITHOUT restart reproduce the
   break-even of the run WITH restart?
C. Cost of one simulated year with admission (single process, wall clock).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r3_policy_check as P  # noqa: E402
import r2_deadline_sim as R  # noqa: E402

NS = (6, 8)
DEMANDS = ("saturating", "shaped100")
BAND = dict(rule="band", band=8.0, cap1=True)
POLS = {
    "ADOPTED (A)": P.pol(fc="ifs025", guard=2.0, restart=15.0, aware=True, **BAND),
    "ADOPTED w/o restart (S3)": P.pol(fc="ifs025", guard=2.0, **BAND),
    "MINIMAL follow+adm(perfect) (M1)": P.pol(),
    "cap + 4 kWh band, ifs025+guard": P.pol(fc="ifs025", guard=2.0, rule="band", band=4.0, cap1=True),
    "cap + 2 kWh band, ifs025+guard": P.pol(fc="ifs025", guard=2.0, rule="band", band=2.0, cap1=True),
}
SPEEDS = (1.0, 1.5, 2.5)


def day_index():
    idx = {}
    for i, (t, _, _) in enumerate(R.base()["rows"]):
        idx.setdefault(t[:10], []).append(i)
    return idx


def pause_resume(pat):
    """First PAUSE followed later by a RESUME inside the day -> (pause_h, resume_h, n_events) or None."""
    ev = P.events(pat)
    for a, b in zip(ev, ev[1:]):
        if a[1] == "PAUSE" and b[1] == "RESUME":
            return a[0], b[0], len(ev)
    return None


def scan(ks, idx, month, slots):
    """-> {date: (slot, pause, resume, n_events, pattern)} for days with pause-then-resume."""
    out = {}
    for dd in sorted(d for d in idx if d[5:7] == month):
        day = [ks[i] for i in idx[dd]]
        for s in slots:
            pat = P.slot_pattern(day, s)
            pr = pause_resume(pat)
            if pr:
                out[dd] = (s, pr[0], pr[1], pr[2], pat)
                break
    return out


def section_a():
    print("== A. Demo days at job level (seed 1): pause AND resume of the demo slot inside one day ==")
    print("  July: demo slot = slot 1 (the last server to stop). January: highest slot with a pause-then-resume.")
    print("  'perm' = permit level of a run where every permit is used; sat / shp = servers WITH WORK in the job-level run,")
    print("  saturating / shaped100 offers (a pause there can mean 'no work', not 'no heat')")
    idx = day_index()
    rows = R.base()["rows"]
    for n in NS:
        for lab, pol in POLS.items():
            res = {dm: P.run(n, pol, dm, 1) for dm in DEMANDS}
            perm = [x[2] for x in P.permit_trace(n, pol["rule"], pol["band"], pol["cap1"])]
            print(f"\n  -- N={n}, {lab} --")
            for month, name, slots in (("01", "January", tuple(range(n, 0, -1))), ("07", "July", (1,))):
                sc = {"perm": scan(perm, idx, month, slots)}
                for dm in DEMANDS:
                    sc[dm] = scan(res[dm]["ks_on"], idx, month, slots)
                    sc["heat_" + dm] = scan(res[dm]["ks_cap"], idx, month, slots)
                hs = sorted(set(sc["heat_saturating"]) & set(sc["heat_shaped100"]))
                print(f"  {name} HEAT SIGNAL (permits of the job-level run, the signal the real job should follow): "
                      f"days with pause-then-resume: sat {len(sc['heat_saturating'])}, shp {len(sc['heat_shaped100'])}, "
                      f"in both: {len(hs)}" + (f" -> {', '.join(hs[:8])}" if hs else ""))
                for dd in hs[:3]:
                    a = sc["heat_saturating"][dd]
                    b = sc["heat_shaped100"][dd]
                    print(f"     {dd} heat sat slot {a[0]} {a[4]} P{a[1]:02d} R{a[2]:02d} ({a[3]} ev) | "
                          f"heat shp slot {b[0]} {b[4]} P{b[1]:02d} R{b[2]:02d} ({b[3]} ev)")
                both = sorted(set(sc["saturating"]) & set(sc["shaped100"]))
                allthree = sorted(set(both) & set(sc["perm"]))
                print(f"  {name}: days with pause-then-resume: perm {len(sc['perm'])}, sat {len(sc['saturating'])}, "
                      f"shp {len(sc['shaped100'])}; in sat AND shp: {len(both)}; in all three: {len(allthree)}")
                for dd in allthree[:6]:
                    tags = []
                    for k in ("perm", "saturating", "shaped100"):
                        s, hp, hr, ne, pat = sc[k][dd]
                        tags.append(f"{k[:4]} slot {s} {pat} P{hp:02d} R{hr:02d} ({ne} ev)")
                    dem = sum(rows[i][1] + rows[i][2] for i in idx[dd])
                    print(f"     {dd} demand {dem:5.1f} kWh | " + " | ".join(tags))
                if not allthree and both:
                    for dd in both[:3]:
                        s, hp, hr, ne, pat = sc["saturating"][dd]
                        s2, hp2, hr2, ne2, pat2 = sc["shaped100"][dd]
                        print(f"     {dd} sat slot {s} {pat} P{hp:02d} R{hr:02d} | shp slot {s2} {pat2} P{hp2:02d} R{hr2:02d}")
    print("\n  real seconds from the start of the day = simulated hour x seconds per simulated hour")
    for hp, hr in ((4, 20), (5, 21), (14, 16), (4, 8), (15, 19)):
        print(f"     PAUSE {hp:02d}:00 RESUME {hr:02d}:00 -> " +
              "; ".join(f"@{s:.1f} s/h: {hp*s:.1f} s / {hr*s:.1f} s, paused {(hr-hp)*s:.1f} s, day {24*s:.0f} s" for s in SPEEDS))


def section_b():
    print("\n== B. Restart 15 min as an accounting line (seed 1, ifs025 + 2 K guard admission) ==")
    print("  approx BE = (elec - heat value) of the run WITHOUT restart / (sold h - starts x 0.25 h)")
    pairs = (("cap + 8 kWh band", P.pol(fc="ifs025", guard=2.0, **BAND),
              P.pol(fc="ifs025", guard=2.0, restart=15.0, aware=True, **BAND)),
             ("plain follow", P.pol(fc="ifs025", guard=2.0),
              P.pol(fc="ifs025", guard=2.0, restart=15.0, aware=True)))
    for n in NS:
        for dm in DEMANDS:
            for lab, p0, p1 in pairs:
                a = P.run(n, p0, dm, 1)
                b = P.run(n, p1, dm, 1)
                approx = (a["elec"] - a["heat_val"]) / (a["sold_h"] - a["starts"] * 0.25)
                print(f"  N={n} {dm:<10} {lab:<17}: no restart BE {a['breakeven']:.4f}, starts {a['starts']:>5}, "
                      f"missed {a['missed']*100:.3f}% | restart in scheduler BE {b['breakeven']:.4f}, missed {b['missed']*100:.3f}%, "
                      f"coverage {a['coverage']*100:.2f}% -> {b['coverage']*100:.2f}% | accounting line BE {approx:.4f} "
                      f"(diff {approx-b['breakeven']:+.4f})")


def section_c():
    print("\n== C. Wall time per simulated year, single process ==")
    for lab in ("ADOPTED (A)", "MINIMAL follow+adm(perfect) (M1)"):
        for n in NS:
            t0 = time.perf_counter()
            P.run(n, POLS[lab], "saturating", 1)
            t1 = time.perf_counter()
            P.run(n, POLS[lab], "shaped100", 1)
            t2 = time.perf_counter()
            print(f"  {lab:<34} N={n}: saturating {t1-t0:.1f} s, shaped100 {t2-t1:.1f} s")
    t0 = time.perf_counter()
    P.run(6, P.pol(adm="all"), "shaped100", 1)
    print(f"  no admission (fallback F), N=6 shaped100: {time.perf_counter()-t0:.1f} s")


if __name__ == "__main__":
    section_a()
    section_b()
    section_c()
