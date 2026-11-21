# Critique: round 6, build-scope audit (what the team scheduler will show at 21:00)

Critic's view of [r6-build-scope-audit.md](r6-build-scope-audit.md), [r6-real-vs-analysis.md](r6-real-vs-analysis.md) and `analysis/r6_build_scope.py`. Assessment only: no existing file was edited, no git state was changed, no web request was made (Firecrawl calls: 0). Probe scripts ran from the session scratchpad and are reproduced below so others can re-run them. Currency: CHF, no conversion needed.

## Bottom line

The numbers reproduce. The conclusions drawn from them go further than the numbers allow.

- **Re-run:** `python3 analysis/r6_build_scope.py --loc-only` and `python3 analysis/r6_build_scope.py` gave exit 0, 9.6 s wall (87 s CPU). Sections 1 to 5 match the pasted output line for line. Git claims re-checked read-only: 22 tracked files, none under `analysis/`.
- **The revised Saturday table does not keep to its own timeline.** By the investigator's own rates, three of its milestones fail.
  1. Role B cannot deliver the key-figure printer (K2) before the 14:45 draft: the work due is 1.95 to 3.70 h (AI-assisted) against 1.56 h of capacity, which fails even at the low estimate.
  2. Role A's admission dry run (M6) needs 2.80 to 6.15 h before the 16:30 gate (midpoint 4.47 h) against 3.06 h of capacity. The gate therefore fails at the midpoint.
  3. At the midpoint, M6 reaches "exactly 0 missed" at about 19:00. That is after the 17:15 configuration freeze and after the slot given to the demo-day finder.

  So the table's "fits at the midpoint" is true only as a sum over the whole day, not as a schedule.
- **The "MUST fits" verdict sits on a 14-minute margin.** It needs the assumed 2× AI speed-up and a focus factor of at least 0.75. At focus 0.70, or at a 1.5× speed-up, role A does not fit.
- **The "current table does not fit" headline is partly a strawman.** It loads every OPTIONAL row onto A, but the current plan already says to drop those in reverse order. With MUST rows only, A's load at AI-assisted rates (midpoint 4.20 h) fits its capacity under the current table's real windows (4.31 h). The real gains in the revision come from moving rehearsals to 19:45 and adding the M4 pin, which no slot of the current table covers.
- **Two of the proposed rewordings introduce new understatements.**
  - **Not-told outage:** the proposal quotes only April (236 / 229 missed). For the same 72 h outage starting on the 15th of a winter month, not told, the misses are 267–307 (N=6) and 317–386 (N=8).
  - **2 K guard:** "the 2 K guard, not the forecast source, removes the misses" is contradicted by the investigator's own row: the archived forecast without the guard already gives 0 / 4.
  - The real-vs-analysis table also still cites the leaky (non-causal) round-2 simulator for "no guard 0.1–0.6%". That figure is at **saturating** offers. At the headline offer level, with the causal flag and no guard, it is 0 / 0.011–0.043% (round-5 reproducibility critique).
- **Hard-coded seed-1 numbers assume the archived-forecast stage.** Plan change 6 puts 73.2% / 85.7% etc. on the slides. Those are the archived + guard stage values, and by the audit's own gate maths that stage is more likely cut than not. At the perfect-forecast stage (the MUST), the scheduler prints coverage 73.13% / 85.85%, utilisation 54.32% / 47.82%, accepted 94.7% / 93.6%, and a restart-line break-even of 0.2279 / 0.2286. Slides must copy the printout, not a number fixed in advance.
- **"Regenerates byte for byte" holds only on this laptop.** `r4_headline.write_offers` needs `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv` (2020–24 weather for the offer rates) and `prev_ecmwf_ifs025.csv`, and `R.base()` reads the latter unconditionally. Both are untracked, as are the three scripts it imports. Plan change 7 lists only the offer CSV and the ifs025 CSV.

## Re-run output (critic, 21 Nov 2026)

Section 4 / 4b / 5 of `python3 analysis/r6_build_scope.py`, identical to the investigator's paste (abridged):

```
S1 perfect        N=6: 0 of 31,859 acc 94.7% cov 73.13% | N=8: 0 of 36,736 acc 93.6% cov 85.85%
S2 persist        N=6: 73 of 31,725                     | N=8: 199 of 36,682
S2g persist+2K    N=6: 0 of 31,471                      | N=8: 0 of 36,272
S3n ifs025 noG    N=6: 0 of 32,122                      | N=8: 4 of 36,905
S3 ifs025+2K      N=6: 0 of 31,908 acc 94.8% cov 73.20% | N=8: 0 of 36,771 acc 93.7% cov 85.73%
S3p +pad 30%      N=6: 0 of 31,896 cov 72.95%           | N=8: 0 of 36,857 cov 85.56%
72 h Apr told     38 of 31,571 / 41 of 36,484 ; NOT told 236 / 229
months told 72 h  N=6 [0,0,0,38,17,2,5,0,11,25,0,0]  N=8 [0,0,0,41,12,7,1,13,9,7,0,0]
4b seed 1         N=6 cov 73.20 util 54.37 BE15 0.2279 elec 9,501 heat 3,040 | N=8 85.73 47.76 0.2287 11,128 3,561
5                 byte-identical: True
```

## Critic probes

Probe 1 (`python3 r6buildscope_crit_probe.py`, under 1 s, imports `analysis/r6_build_scope.py` unchanged):

```
P1 role A, revised (M2 M3 M4 M6 O6): midpoint load vs capacity under focus x AI-speed
  speed x1.0: mid 7.69 | f0.60 cap 4.10 no | f0.65 4.44 no | f0.70 4.78 no | f0.75 5.12 no   | f0.85 5.81 no
  speed x1.5: mid 5.83 | no at every focus factor up to 0.85
  speed x2.0: mid 4.89 | f0.60 no | f0.65 no | f0.70 no | f0.75 FITS | f0.85 FITS
  speed x3.0: mid 3.96 | fits at every focus factor
P2 current table, MUST rows only on A (M2 M5 M3 M6), current windows (rehearse 18:40-21:00)
  speed x1.0: 4.25-9.10 mid 6.68 vs cap 4.31     speed x2.0: 2.60-5.80 mid 4.20 vs cap 4.31
P3 revised table, B work due before the 14:45 draft (M5, K1, K2 + energy run / r3_income), 11:40-12:15 + 12:45-14:15
  speed x1.0: 2.80-5.40 vs cap 1.56              speed x2.0: 1.95-3.70 vs cap 1.56   (fails even at the low estimate)
P4 revised table, A work due before the 16:30 gate (M2 M3 M4 M6), 11:40-12:15, 12:45-14:45, 15:00-16:30
  speed x1.0: 4.50-9.55 vs cap 3.06              speed x2.0: 2.80-6.15 mid 4.47 vs cap 3.06
```

M6 finishing time at the AI-assisted midpoint: 4.47 h effective ÷ 0.75 is about 5.96 h of gross build time from 11:40. Through the revised windows that ends around 19:00, after the 17:15 configuration freeze.

Probe 2 (`python3 r6buildscope_crit_probe2.py`, about 3 s on all cores, imports `r5_miss_stress.py` and `r6_build_scope.py` unchanged):

```
N=6 72 h NOT told, missed Jan/Feb/Mar/Nov/Dec: [274, 277, 307, 289, 267]
N=8 72 h NOT told, missed Jan/Feb/Mar/Nov/Dec: [375, 347, 317, 338, 386]
S1 N=6: coverage 73.13% util 54.32% sold 28,550 elec 9,493 heat 3,038 BE 0.2261 BE15 0.2279 starts 893 accepted 31888 of 33676 (94.69%) missed 0 of 31859
S1 N=8: coverage 85.85% util 47.82% sold 33,512 elec 11,143 heat 3,566 BE 0.2261 BE15 0.2286 starts 1488 accepted 36749 of 39244 (93.64%) missed 0 of 36736
S3 N=6: coverage 73.20% util 54.37% sold 28,575 elec 9,501 heat 3,040 BE 0.2261 BE15 0.2279 starts 896 accepted 31937 of 33676 (94.84%) missed 0 of 31908
S3 N=8: coverage 85.73% util 47.76% sold 33,467 elec 11,128 heat 3,561 BE 0.2261 BE15 0.2287 starts 1527 accepted 36784 of 39244 (93.73%) missed 0 of 36771
```

The not-told winter values match the round-5 critic's probe P4 (r5-missed-deadline-robustness-critique.md), so they were already on record when the investigator wrote "236 / 229 (April)".

<details><summary>Probe sources</summary>

```python
# r6buildscope_crit_probe.py
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/saif/Work/digitalheat/analysis")
import r6_build_scope as B
c = B.census(); R = B.rows(c); byid = {r[0]: r for r in R}
def load(ids, speed):
    lo = hi = 0.0
    for i in ids:
        l, h = B.ph(byid[i][3], byid[i][5], byid[i][6], speed); lo += l; hi += h
    return lo, hi
for speed in (1.0, 1.5, 2.0, 3.0):                       # P1
    lo, hi = load(["M2", "M3", "M4", "M6", "O6"], speed)
    gross = sum(B.hm(b) - B.hm(a) for a, b, k in B.WINDOWS["A"] if k == "build")
    print(speed, (lo+hi)/2, [(f, round(gross*f, 2), (lo+hi)/2 <= gross*f) for f in (0.6, 0.65, 0.7, 0.75, 0.85)])
gross_cur = 0.75 + 2.0 + 3.0                              # P2: 11:30-12:15, 12:45-14:45, 15:00-18:00
for s in (1.0, 2.0): print("P2", s, load(["M2", "M5", "M3", "M6"], s), gross_cur*0.75)
gross_b = (12.25 - 11.667) + 1.5                          # P3
for s in (1.0, 2.0):
    lo, hi = load(["M5", "K1", "K2"], s); print("P3", s, lo+0.5, hi+0.75, gross_b*0.75)
gross_a = (12.25 - 11.667) + 2.0 + 1.5                    # P4
for s in (1.0, 2.0): print("P4", s, load(["M2", "M3", "M4", "M6"], s), gross_a*0.75)
```

```python
# r6buildscope_crit_probe2.py
import sys, multiprocessing as mp
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/saif/Work/digitalheat/analysis")
def task(spec):
    import r5_miss_stress as S, r6_build_scope as B
    lab, n, kw = spec
    if "m" in kw:
        kw = dict(fail_at=(B.day_hour(kw["m"]), n, 72), fail_aware=False)
    return (lab, n), S.run(n, S.cfg(**kw), 1)
if __name__ == "__main__":
    specs = [(f"NT{m:02d}", n, dict(m=m)) for n in (6, 8) for m in (1, 2, 3, 11, 12)]
    specs += [("S1", n, dict(fc="perfect")) for n in (6, 8)] + [("S3", n, dict()) for n in (6, 8)]
    with mp.Pool() as p:
        res = dict(p.map(task, specs, chunksize=1))
    from baseline_sweep import HEAT_VALUE, PRICE
    # prints as shown above: elec = run_h * PRICE, heat = used * HEAT_VALUE,
    # BE15 = (elec - heat) / (sold_h - starts * 0.25)
```
</details>

## Findings in detail

### F1. The revised table is a sum, not a schedule (claims c6, c7; plan changes 1, 4)

Section 3 adds each role's hours over the whole day. It never checks the order of work or what each milestone depends on. Laid against the table's own milestones:

- **14:45 draft.** The "Minimum by 15:00" in docs/overnight.md includes "one command prints the seven key figures". In the revised table, B owns the printer (K2) and must also do M5, K1, the energy run and `r3_income` before 14:15. That is 1.95–3.70 h of work against 1.56 h of capacity. The draft will likely go out with no printer, or with D's half-built one from the old 11:20 slot.
- **16:30 gate.** A's M2–M6 midpoint is 4.47 h against 3.06 h of capacity by 16:30. The gate is set up to fail at the midpoint. The table should say so: "O3 and N1 are expected to be cut; they happen only if A runs fast."
- **17:15 configuration freeze.** At the midpoint, M6 lands around 19:00. The finder (O6) is given 17:15–18:00 and needs the final run with M6 in. As written, the freeze and the finder both come before the core they freeze.
- **Dependencies.** K1 (accumulators) sits in the same yearly loop that A edits, so B and A edit one file at the same time. K5 (trace test, 15:00–16:30) runs while M6 is still changing and must be re-run after it lands. Neither cost is in the hours.

**Fix:** put the printer first in B's queue, before K1 and ahead of the energy run's write-up. Move `r3_income` and the scaling write-up to D, who now writes no code. Move the configuration freeze to 19:00, or keep 17:15 and accept that M6 may miss it, in which case the missed tile uses the fallback wording. Say plainly that O3 and N1 are expected cuts.

### F2. Knife-edge margin (c3–c6)

A's revised load is 4.89 h at the midpoint against 5.12 h of capacity, a margin of 0.23 h. That margin needs both assumptions at once: an AI-assisted speed-up of 2× (not measured) and a focus factor of 0.75. Either one slightly worse breaks the fit (probe P1). The investigator labels the rates as assumptions, but the summary line "No MUST row has to be cut" reads as a finding when it is a coin toss. M6 is also where dry run and executor must agree exactly, and line counts predict debugging time worst there; the investigator notes this.

### F3. The current table is overloaded mainly through rows the plan already lets A drop (c5)

`ASSIGN_CURRENT["A"]` includes O2, O3, O4 and O5. The current plan says "if behind, drop in reverse order". Section 3a also applies the *revised* windows (rehearsals from 19:45) to the *current* table, where A rehearses from 18:40. With A's true current windows (4.31 h effective) and MUST rows only, the AI-assisted midpoint is 4.20 h. The genuine gaps are elsewhere: M4 (demo-date pin) and K1 have no slot in the current table, and B is underused. Those findings stand.

### F4. Outage wording: the correction understates the not-told case (c15, plan change 8)

The revised outage line quotes "Not told, 72 h: 236 / 229 in April". Not told, the cost is highest in winter: 267–307 (N=6) and 317–386 (N=8) for a 72 h outage starting on the 15th of November to March (probe 2; it matches the round-5 critic's P4). The plan's existing line ("up to about 300–390 jobs") was closer to the truth than the proposed correction.

Two more points on this line:
- "Up to 38 / 41" when told is a maximum over 12 sampled start times (00:00 on the 15th), one seed. It is not a worst case.
- "Told" includes knowing the repair time in advance. The investigator notes this caveat.

### F5. The guard sentence and the no-guard line (c11, c12; plan change 9; real-vs-analysis table)

At `shaped100` the archived ECMWF forecast without the guard gives 0 / 4 missed (seed 1). The round-5 reproducibility critic gives 0 / 0.011–0.043% over 5 seeds. The guard matters for persistence (73 / 199 down to 0), not much for the planned forecast. So "the 2 K guard, not the forecast source, removes the misses" is wrong for the archived forecast the plan actually uses.

The bigger problem is in the real-vs-analysis table. Its row "No guard band: roughly 0.1–0.6% … partly `r5_pitch_numbers.py` J2 (2025: 0.097–0.386%)" has three faults:
- J2 runs `r2_deadline_sim.run`, the non-causal simulator the round-5 critic rejected.
- The 0.1–0.6% is at **saturating** offers, not the headline contract.
- Its upper end is reproducible from saved functions (round-5 critique, 2.1), not "a critic probe, not saved".

Pairing that range with the `shaped100` headline in Q&A 5 compares two different offer levels as if they were one.

### F6. Seed-1 slide values depend on the stage reached (c18, plan change 6)

The transparency point (seed 1 against 3-seed means) is valid. Gaps are 0.47 / 0.41 coverage points and 0.35 / 0.22 utilisation points. But plan change 6 fixes the S3 (archived + guard) values in advance. If only the perfect forecast lands, the scheduler prints 73.13% / 85.85%, 54.32% / 47.82%, accepted 94.7% / 93.6%, BE15 0.2279 / 0.2286. The rule must be "copy the scheduler's printout at the freeze", not a number. The c26 mix ("seed-1 counts with 3-seed acceptance") is real but 0.1 points: 31,937 of 33,676 accepted is 94.84%, against a 3-seed 94.7%.

### F7. Reproducibility of the offer CSV (c22, plan change 7)

The byte-identical check passes on this laptop. A fresh clone could regenerate the file only if it also had:
- `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv` (928 KB), behind `offer_rates("shaped100")`;
- `analysis/r2_data/prev_ecmwf_ifs025.csv`, read by `R.base()` on every call;
- `r2_deadline_sim.py`, `r3_policy_check.py`, `r4_headline.py` and `baseline_sweep.py`.

All of these are untracked. `docs/overnight.md` and all of `docs/research/` are untracked too, so the README cannot link the real-vs-analysis table in a clone either. The case requires "code in the repository"; any analysis figure quoted in the pitch needs its script committed.

### F8. Smaller points

- **c23:** "not told is one more line (`n_avail[0] = 0`, future = N)" models a scheduler that sees the present outage but not its length. In `r5_miss_stress.run` the not-told dry run plans with all N servers even at hour 0, so the 236 / 229 values would not be reproduced. The hook itself is sound and cheap; adopt it.
- **c25:** `one_rack_model.py` content verified (`GPU_PER_SERVER = 2`, RTX 4090, `--sold` 0.80). It is labelled "sourced", but it is a repo read, not a web source.
- **K1 overlap:** M1 ("permit + yearly driver reproducing 79.58%, 31,067 server-h") already needs the yearly loop and its coverage accumulators, so K1 is partly double-counted. This overstates B's load slightly.
- **Script docstring:** it says "about 1–2 min"; the actual run takes 9.6 s.
- **Temp files:** section 5 writes its temp file to the system temp directory and deletes it. Harmless, but the loop rule asks for the shared scratchpad.
- **Cutting the dashboard:** cutting the web page (K9) and shrinking the live view to one trace line per hour (K8s) saves real time. But the case's core use case says "a dashboard shows the balance per house and year", and Design & usability (10%) asks that a homeowner understands the result in one minute. A single raw trace line will not do that. Keep a minimal readable live view: state, heat permit, tank, job, three numbers.
- **Perfect forecast as the likely 21:00 stage.** By F1 the scheduler will most likely show perfect-forecast admission. Perfect forecast means admission reads the actual 2025 weather. A founder will call that foresight, and it does not meet "the system checks the weather forecast". That argues for the archived forecast (about 30 driver lines with the hook) ahead of the outage scenario, and ahead of the dashboard page. The investigator's cut order (K9, then N1, then O3) already has this order; the gate maths says even O3 is unlikely.

## Founder objections still open

See the structured result.
