# Round 8 critique: held-out guard check and the missed-deadline tile

Critic role: a sceptical DigitalHeat founder. I attacked `docs/research/r8-guard-heldout-tile.md`, `analysis/r8_guard_heldout.py` and `analysis/r8_guard_probe.py`.

I changed no git state and edited no existing file. Firecrawl calls: 0. Web requests: none. New files from me:
- `analysis/r8_guard_tile_critic_probe.py` (standard library only; imports the investigator's script without editing it)
- this file

Currency: none. There are no money figures here.

## What I re-ran

| Command | Result |
|---|---|
| `python3 analysis/r8_guard_heldout.py` | 2 min 9 s. Output matches `docs/research/r8-guard-heldout-output.txt` line for line, apart from the timing and run-count lines. All 12 regression lines read IDENTICAL. |
| `python3 analysis/r8_guard_probe.py` | Matches the research file: 6 K guard, 2023: 88–109 missed at N=6 and 194–240 at N=8. |
| `python3 analysis/r8_guard_tile_critic_probe.py` | 20 s. New output, quoted below (*computed*). |
| `python3 -I` count over `analysis/r8_data/prev_ecmwf_ifs025_2024.csv` | First non-NaN values: day 0 at 2024-02-03T01:00, previous_day7 at 2024-02-10T01:00 (row 961). The file uses a fixed GMT+1 offset with no DST jump on 31 Mar or 27 Oct. Grid point 47.5/7.5, the same as the 2025 file. |

The code follows the stated rules:
- The case formula is unchanged and 25.6 stays fixed.
- P1 is causal.
- O3 falls back to persistence before 10 Feb.
- Guard selection is "smallest guard with 0 training misses, else fewest".

I found no arithmetic bug. My objections are about how much the numbers prove and how the tile reads.

## Attack 1: "0 of 152,405" overstates the evidence for O3 + 2 K

The misses come from **cliff days**. On those days the planning input says "heating day" (day mean below 10 °C with the 2 K guard) but the actual day mean is at or above 12 °C. The independent unit of evidence is that day, not the job. Offer seeds vary the jobs and never the weather. Critic probe, section A (*computed*):

| Year | P1 cliff days, lag 1 / lag 2 | ECMWF day-1 / day-2 cliff days |
|---|---|---|
| 2020 | 4 / 7 | no archive |
| 2021 | 3 / 6 | no archive |
| 2022 | 2 / 4 | no archive |
| 2023 | 6 / 13 | no archive |
| 2024 | 2 / 5 | 0 / 0 (324 days from 10 Feb) |
| 2025 | 1 / 3 | 0 / 0 |

So the held-out O3 test rests on about **2–5 dangerous days in 2024**, all of which the forecast saw coming. That counts in O3's favour, but it is a handful of events, not a sample of 150,000.

## Attack 2: the 2 K margin for O3 is one grid step, and it leans on a warm forecast bias

- From the investigator's own output, O3 + **1 K** on 2024 misses **3** jobs at N=6 and **9** at N=8 (5 seeds). On 2025 at N=8 it misses 2.
- The leave-one-year-out rule failed at N=6. Trained on 2025 it picks 0 K, which misses 43 jobs over 5 seeds in 2024.
- At N=8 the rule picks 2 K only because 1 K misses 2 jobs in a single seed of 2025.

The 2024 archived forecast runs **+0.65 K warm** on day 1 against the reference "truth". A warm forecast plans fewer heat permits, so it acts like an extra guard. The critic probe (section B, *computed*, 5 seeds, normal offers) shifts the 2024 forecast colder to remove that bias:

| Forecast shifted by | O3 + 2 K, N=6 | O3 + 2 K, N=8 | O3 + 3 K, N=6 / N=8 |
|---|---|---|---|
| 2024, 0 K (as archived) | 0 of 152,405 | 0 of 177,286 | 0 / 0 |
| 2024, −0.36 K (bias as in 2025) | 0 | 2 | 0 / 0 |
| 2024, −0.65 K (zero bias) | 3 | 16 | 0 / 0 |
| 2024, −1.0 K | 3 | 28 | 0 / 3 |
| 2025, −0.29 K (zero bias) | 0 | 3 | 0 / 0 |

So "2 K survives out of sample" is true as computed, but only just.

The bias is measured against a model "truth" on a different grid cell (47.557/7.549 against 47.5/7.5), so it may be a grid artefact rather than real forecast behaviour. Open risk 4 already lists this as open.

Switching O3 to 3 K now would be tuning on 2024, the only held-out year. **Do not retune.** Report the margin instead.

## Attack 3: line 2 alone does not make the tile discriminate, and its numbers clash with the tile

- **The jury sees one stage.** "1,460 server-h refused" means nothing without a reference. The only discriminating element in the proposal is line 4 (the difference against the check run), which the investigator marks "cut first". A cheaper fix needs no second run: print the check-run reference as fixed, labelled text, e.g. "check run on recorded weather: 884 server-h (analysis script)".
- **Unit clash.** Tile 5 already shows the accepted share in jobs (95.6% at N=6), and the plan defines "refused at intake" as 100% minus that, i.e. 4.4%. The new line 2 says "3.0% of offered work", which is in server-h. Critic probe, section C (*computed*): at N=6 the check run refuses 4.4% of jobs but 3.0% of server-h; P1 refuses 6.5% / 4.9%; O3 5.2% / 3.5%. Two different "refused" percentages on one tile fail the one-minute test. Pick one unit, or label both: "1,466 jobs (4.4%) = 884 server-h (3.0%)".
- **Counts that don't add up on screen.** At N=6: 33,676 offered − 1,466 refused = 32,210 accepted, but line 1 says "0 of 32,174 accepted jobs". The 36-job gap is jobs still open at year end; 32,174 counts closed jobs. Any juror who adds the numbers will see it. Line 1 should say "0 of 32,174 jobs that reached their deadline in 2025", or line 2 should show accepted = 32,210.
- **Destination.** "Returned to the aggregator, not run here" contradicts open risk 4 as currently written ("Refused work goes to a typed year-round heat user that is not named"). The plan also records that no aggregator was found. The rewriter needs one consistent sentence. "Not accepted; the contract we chose would send it back to the work source (not modelled)" is safer.

## Attack 4: smaller points

- **Labels.** "Of accepted jobs" in the pooled rates is really "of closed jobs" (accepted minus open at year end). The difference is small, but the label is wrong.
- **Q&A wording.** The P1 Q&A says "a 6 to 9 degree warm jump". The clusters include a 4.8 K jump (2021, day 87 to day 89) and a 6.6 K one (2020, lag 2). Say "a 3 to 9 degree warm jump", matching the research file.
- **Check run.** Its 0 in six years holds by construction. Jobs whose deadline falls past 31 December are not counted, and check and O3 targets past 31 December wrap to the same year's January.
- **Regression.** The P1 regression reads IDENTICAL even though r8 pads with "hot water only" before 1 January and r7 pads with December 2024 data. At seed 1 the regression cannot tell the two pads apart, so it does not test that path.
- **Probe framing.** With a 6 K guard, P1 reaches 0 in 2020, 2021, 2024 and 2025. The rest is 2023 (88–109) and 2022 (4 in one seed). "No guard fixes it" is correct, but 2023 carries the result.
- **Case formula.** P1's failure is driven by the case's binary 12 °C heating-day rule, which the reference house must use. A real house ramps down gradually, so the size of the P1 penalty may not carry over to a pilot. Say so in Q&A if asked.

## Bottom line

- **P1:** the finding stands. Persistence + 2 K (or 3 K) does not survive out of sample, and the plan must stop presenting P1's 0 as robust.
- **O3:** "2 K survives 2024" stands only with the caveats above: about 5 cliff days of evidence, a one-step margin, and help from a warm forecast bias.
- **Tile:** the proposal needs the unit and arithmetic fixes, plus a fixed check-run reference, before it actually discriminates.
