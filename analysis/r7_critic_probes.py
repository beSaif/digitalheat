"""Round 7: save the critic probes that "Read this first" quotes, so a fresh clone can reprint them.

ASSESSMENT ONLY. Not the team's scheduler. Standard library only. Imports the saved analysis
scripts read-only (nothing on disk is changed; monkeypatches are runtime-only, in this process).

    python3 analysis/r7_critic_probes.py            # all sections, all CPU cores (about 10-40 s)
    python3 analysis/r7_critic_probes.py --procs 1  # no multiprocessing

Why: several figures in docs/overnight.md "Read this first" are labelled "critic probe". The
critics ran them from scratch scripts in a temporary directory that a fresh clone does not have.
This file re-implements those probes with the same calls, so each figure has one saved command.

Sections (source of the original probe in brackets)
  A  Team-scheduler stages, seed 1: perfect forecast (S1) and archived ifs025 + 2 K guard (S3):
     coverage, utilisation, accepted share, missed, break-even with a 15-min restart line
     [round-6 build-scope critique, probe 2]
  B  Whole-house outage 72 h from 00:00 on the 15th, scheduler NOT told, winter months, seed 1
     [round-6 build-scope critique, probe 2; round-5 missed-deadline critique P4]
  C  ICON forecast debiased then shifted -2 K / -3 K (too cold), 2 K guard, seeds 1-5
     [round-5 missed-deadline critique P3]
  D  No guard band, archived ifs025, causal heating-day flag, SATURATING offers, seeds 1-5
     (and shaped100 for contrast) [round-5 reproducibility critique, section 2.1]
  E  Share of list value needed incl. maintenance with the corrected card failure rate
     (MTBF 864,500 h -> 1.01 %/yr, failures in every payback year) [round-6 machine critique, finding 1]
  F  Price per sold server-hour needed, heat credited vs heat given free to the host, seed 1
     [round-6 buyer critique, probe 1]

Currency CHF throughout (conversion constants live in r4_machine.py: ECB 20 Nov 2026).
"""
import argparse
import multiprocessing as mp
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

SEEDS5 = (1, 2, 3, 4, 5)
WINTER = (1, 2, 3, 11, 12)
RESTART_H = 0.25                       # 15-min restart line (ASSUMPTION, plan)


# ---------------------------------------------------------------- workers (top level for spawn)
def add_cold(S, shift):
    """Round-5 critic P3: per-lead yearly bias removed, then shifted `shift` K too cold."""
    name = f"icon_cold{shift:g}"
    key = ("ft", name)
    if key not in S._C:
        ft = S.fc_temps("icon")
        act = ft[0]
        new = [act]
        for k in range(1, 8):
            bias, _ = S.stats(ft[k], act)
            new.append([t - bias - shift for t in ft[k]])
        S._C[key] = new
    return name


def task(spec):
    kind, label, n, seed, kw = spec
    if kind == "S":                                   # r5_miss_stress.run (team-scheduler mirror)
        import r5_miss_stress as S
        import r6_build_scope as B
        kw = dict(kw)
        if "outage_month" in kw:
            m = kw.pop("outage_month")
            kw.update(fail_at=(B.day_hour(m), n, 72), fail_aware=False)
        if "cold" in kw:
            kw["fc"] = add_cold(S, kw.pop("cold"))
        r = S.run(n, S.cfg(**kw), seed)
        keep = ("coverage", "util", "run_h", "sold_h", "starts", "offered", "accepted", "acc_jobs",
                "missed_n", "closed_n", "used", "breakeven")
        return (label, n, seed), {k: r[k] for k in keep}
    if kind == "H":                                   # r4_headline.run (round-4 headline loop)
        import r3_policy_check as P3
        import r4_headline as H
        demand = kw.pop("demand")
        r = H.run(n, P3.pol(**kw) if kw else H.HEADLINE, demand, seed)
        keep = ("missed_n", "closed_n", "acc_jobs", "sold_h", "sold_t", "elec", "heat_val", "coverage")
        return (label, n, seed), {k: r[k] for k in keep}
    raise ValueError(kind)


def specs():
    out = []
    for n in (6, 8):
        out.append(("S", "S1 perfect", n, 1, dict(fc="perfect")))
        out.append(("S", "S3 ifs025+2K", n, 1, dict()))
        for m in WINTER:
            out.append(("S", f"NT{m:02d}", n, 1, dict(outage_month=m)))
        for sh in (2, 3):
            for s in SEEDS5:
                out.append(("S", f"cold{sh}", n, s, dict(cold=sh)))
        for s in SEEDS5:
            out.append(("H", "noguard_sat", n, s, dict(demand="saturating", fc="ifs025", guard=0.0,
                                                         rule="band", band=8.0, cap1=True, causal=True)))
            out.append(("H", "noguard_shaped", n, s, dict(demand="shaped100", fc="ifs025", guard=0.0,
                                                            rule="band", band=8.0, cap1=True, causal=True)))
        out.append(("H", "headline", n, 1, dict(demand="shaped100")))
    return out


# ---------------------------------------------------------------- section E (no simulation of jobs)
def section_e():
    import baseline_sweep as bs
    import r5_chain as rc
    import r6_machine as M6
    afr_old = M6.AFR
    afr = 8760.0 / 864500.0            # SOURCED by the round-6 critic: PNY RTX PRO 6000 SE brief, 864,500 h
    rows = bs.load()
    print("\n== E. Share of list value needed, central, every permit hour sold, incl. maintenance ==")
    print(f"  card failure rate: r6_machine.py on disk {afr_old*100:.2f}%/yr (misread MTBF 1,864,500 h); "
          f"corrected {afr*100:.2f}%/yr (864,500 h), self-insured in EVERY payback year")
    print(f"  {'machine':<8}{'N':>3}{'5y+m (r6 file)':>16}{'5y+m corrected':>16}{'8y+m corrected':>16}")
    for n in (6, 8):
        r = rc.sim(rows, n, "DLC", "underfloor 35/28", tank_loss=rc.LOSS)
        op, run_h = r["be_chg"], r["run_h"]
        for m in ("R5", "PRO6K4"):
            inst, boxes, _ = M6.installed(m, n)
            maint, warr3 = M6.yearly_cost(m, n, retrofit=True)
            a, t = M6.work_per_kwh(m)
            mix = M6.list_value(a, t)[2]
            n_gpu, card = M6.MACHINES[m][0], M6.MACHINES[m][4]
            fail_y = afr * boxes * n_gpu * card["central"]          # CHF of cards per year, corrected
            s5_file = M6.share(op, inst, run_h, 5, mix, maint, warr3)
            s5 = M6.share(op, inst, run_h, 5, mix, maint, fail_y * 5)
            s8 = M6.share(op, inst, run_h, 8, mix, maint, fail_y * 8)
            print(f"  {m:<8}{n:>3}{s5_file*100:>15.1f}%{s5*100:>15.1f}%{s8*100:>15.1f}%"
                  f"   (installed {inst:,.0f} CHF, {boxes:.2f} boxes, cards fail {fail_y:,.0f} CHF/yr)")
    print("  R5 = reference server on the cold-plate chain; PRO6K4 = realism machine (4 x RTX PRO 6000 SE),"
          " N normalised to kW (2.23 boxes at N=6: not buildable)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=0)
    a = ap.parse_args()
    sp = specs()
    if a.procs == 1:
        res = dict(task(s) for s in sp)
    else:
        with mp.get_context("spawn").Pool(a.procs or None) as p:
            res = dict(p.map(task, sp, chunksize=1))
    from baseline_sweep import HEAT_VALUE, PRICE, P_EL
    import r5_chain as rc

    print("r7_critic_probes.py  (assessment only; not the team scheduler; stand-in reference house 2025; CHF)")
    print("\n== A. Team-scheduler stages, seed 1 (offer CSV), cap + 8 kWh band, restart outside execution ==")
    for lab in ("S1 perfect", "S3 ifs025+2K"):
        for n in (6, 8):
            r = res[(lab, n, 1)]
            elec = r["run_h"] * P_EL * PRICE
            heat = r["used"] * HEAT_VALUE
            be15 = (elec - heat) / (r["sold_h"] - r["starts"] * RESTART_H)
            print(f"  {lab:<13} N={n}: coverage {r['coverage']*100:.2f}% util {r['util']*100:.2f}% "
                  f"accepted {r['accepted']} of {r['offered']} ({r['acc_jobs']*100:.2f}%) "
                  f"missed {r['missed_n']} of {r['closed_n']:,} | elec {elec:,.0f} heat {heat:,.0f} "
                  f"BE {r['breakeven']:.4f} BE15 {be15:.4f} starts {r['starts']}")

    print("\n== B. House dark 72 h from 00:00 on the 15th, scheduler NOT told, seed 1 (missed of closed) ==")
    for n in (6, 8):
        cells = [f"{['Jan','Feb','Mar','','','','','','','','Nov','Dec'][m-1]} {res[(f'NT{m:02d}', n, 1)]['missed_n']}"
                 for m in WINTER]
        print(f"  N={n}: " + ", ".join(cells))

    print("\n== C. ICON debiased and shifted too cold, 2 K guard, seeds 1-5 (pooled % of accepted jobs) ==")
    for sh in (2, 3):
        for n in (6, 8):
            rs = [res[(f"cold{sh}", n, s)] for s in SEEDS5]
            x, y = sum(r["missed_n"] for r in rs), sum(r["closed_n"] for r in rs)
            print(f"  -{sh} K N={n}: missed per seed {[r['missed_n'] for r in rs]}  pooled {x}/{y:,} = {x/y*100:.3f}%")

    print("\n== D. No guard, archived ifs025, causal flag, seeds 1-5 (% missed of accepted, per seed) ==")
    for lab, txt in (("noguard_sat", "saturating offers"), ("noguard_shaped", "shaped100 headline")):
        for n in (6, 8):
            v = [res[(lab, n, s)]["missed_n"] / max(1, res[(lab, n, s)]["closed_n"]) * 100 for s in SEEDS5]
            print(f"  {txt:<19} N={n}: mean {sum(v)/5:.3f}%  min {min(v):.3f}%  max {max(v):.3f}%  "
                  f"(missed {[res[(lab, n, s)]['missed_n'] for s in SEEDS5]})")

    section_e()

    print("\n== F. Price per sold server-hour needed for a 5-year simple payback (cold-plate chain, central),"
          " shaped100, seed 1 ==")
    for n in (6, 8):
        r = res[("headline", n, 1)]
        inst = rc.installed(n, "DLC")[0]
        cred = (r["elec"] - r["heat_val"] + inst / 5.0) / r["sold_h"]
        free = (r["elec"] + inst / 5.0) / r["sold_h"]
        print(f"  N={n}: heat credited to the operator {cred:.3f} CHF; heat given free to the host {free:.3f} CHF "
              f"(installed {inst:,.0f} CHF, sold {r['sold_h']:,.0f} h)")


if __name__ == "__main__":
    main()
