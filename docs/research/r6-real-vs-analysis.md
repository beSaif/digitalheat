# What is real, what is computed separately, what is assumed

README-ready table for the jury's Transparency criterion (25%). Round 6, written Sat 21 Nov 2026 ~11:30, **before** the team's scheduler exists in the repo. The "Real" column says what the team's own code **will** show **if** the revised Saturday table in [r6-build-scope-audit.md](r6-build-scope-audit.md) lands. At the 21:00 freeze, tick the last column or move the row to "analysis script". Background and evidence: [r6-build-scope-audit.md](r6-build-scope-audit.md).

**Where each kind of figure comes from**

| Label | Meaning | How to repeat it |
|---|---|---|
| **SCHEDULER** | printed by the team's yearly driver, which runs the same `decide()` that controls the live job; one house-year, offers from `analysis/r4_offers_shaped100_seed1.csv` (seed 1 only) | the scheduler's key-figure command (name it in the README) |
| **LIVE** | happens on the demo laptop: a real process paused and resumed by `decide()` | the one-command demo; `ps -o state=` |
| **ANALYSIS** | printed by a separate exploratory script in `analysis/`. It is **not** the scheduler. It re-implements the same rules, and some of its figures average 3 or 5 offer seeds | the command given |
| **MEASURED** | a laptop measurement (battery-controller counters, no wall meter) | the probe script named, on the same laptop |
| **SOURCED** | a number read on a public web page (URL in the research files) | open the URL |
| **ASSUMPTION** | our own choice, listed in the assumptions list | change the parameter |

**Two things to fix before the README goes public (both found this round):**
1. **Seed 1 against 3-seed means.** The scheduler reads one offer file (seed 1), so its own printout gives **73.2% / 85.7%** coverage and **54.4% / 47.8%** utilisation. The pitch's **73.7% / 86.1%** and **54.7% / 48.0%** are 3-seed means from `analysis/r4_headline.py`. The plan rule "the scheduler's printout is the authority" means the slide shows the seed-1 values. Otherwise the 3-seed values carry the label "mean of 3 offer seeds, analysis script" (*computed*, `python3 analysis/r6_build_scope.py`, section 4b).
2. **Nothing under `analysis/` is tracked in git** (`git status`: `?? analysis/`). That includes the offer CSV the scheduler must read and the archived forecast CSV. A fresh clone does not have them. Committing them, or copying them into `data/`, is a team decision. Until then, the README must not call them "committed". The offer CSV is reproducible byte for byte with `python3 analysis/r4_headline.py --write-offers <path>` (*computed*, `r6_build_scope.py` section 5).

## Key figures (the six tiles plus must-have 3)

| # | Figure | Value for the pitch, N=6 / N=8 | Real (SCHEDULER / LIVE) | Separate analysis script | Assumption / measured / sourced inputs | Tick at 21:00 |
|---|---|---|---|---|---|---|
| 1 | Servers per house | 6 and 8 side by side | SCHEDULER parameter N, run twice | — | ASSUMPTION (coverage choice, not an economic result) | [ ] |
| 2 | Heat demand covered, headline contract | **73.2% / 85.7%** (seed 1) | SCHEDULER | 73.7% / 86.1% = 3-seed mean, `python3 analysis/r4_headline.py` s.3 | ASSUMPTION: contract sized to the house's expected heat capacity (`shaped100`) | [ ] |
| 2a | Upper line, unlimited demand | 79.6% / 92.9% | SCHEDULER only if the yearly driver keeps its "every permit used" mode (the 09:30 regression target) | `python3 analysis/baseline_sweep.py` | "unlimited jobs" declared | [ ] |
| 2b | Flat customer, same yearly volume | 53.7% / 60.5% | — | `python3 analysis/r5_pitch_numbers.py` (D5) | ASSUMPTION (flat offer rate) | |
| 3 | Heat dumped | 0 kWh | SCHEDULER (holds by construction of the follow rule) | same in every script | — | [ ] |
| 4 | Utilisation | **54.4% / 47.8%** (seed 1) | SCHEDULER | 54.7% / 48.0% = 3-seed mean, `r4_headline.py` s.3 | — | [ ] |
| 5 | Missed deadlines | "x of y accepted jobs", stage label, accepted share | SCHEDULER, stage reached by 21:00 (expected values in the table below) | stress line: `python3 analysis/r5_miss_stress.py`; outage: `python3 analysis/r6_build_scope.py` s.4 | forecast stage, 2 K guard, job sizes and deadlines are ASSUMPTIONS | [ ] |
| 5a | Accepted share of offers | 94.8% / 93.7% (seed 1) | SCHEDULER (if admission landed) | 94.7% / 93.8% = 3-seed mean | — | [ ] |
| 6 | Break-even, heat credited (case formula) | 0.2261 CHF per sold server-hour | SCHEDULER printer. Structural: 0.3325 − 0.8 × 0.133 whenever nothing is dumped and unsold servers are off, so it is not a scheduling result | `r2_fleet_economics.py`, `baseline_sweep.py` | SOURCED price 0.3325 CHF/kWh (ElCom); case rule heat = price ÷ 2.5 | [ ] |
| 6a | Break-even, homeowner keeps the heat | 0.3325 CHF | SCHEDULER printer (same run, heat credit 0) | `r2_fleet_economics.py` | — | [ ] |
| 6b | Break-even with a 15-min restart line | **0.2279 / 0.2287** (seed 1) | SCHEDULER printer: (elec − heat) ÷ (sold h − starts × 0.25) | 0.2278 / 0.2286 = 3-seed mean, `r4_headline.py` s.3 | ASSUMPTION 15 min (server boot unmeasured) | [ ] |
| 7 | Electricity cost per year | 9,501 / 11,128 CHF (seed 1) | SCHEDULER printer | 9,563 / 11,181 = 3-seed mean | SOURCED price | [ ] |
| 7a | Heat value used per year | 3,040 / 3,561 CHF (seed 1) | SCHEDULER printer | 3,060 / 3,578 = 3-seed mean | case rule | [ ] |
| 7b | Computing income | "share of list price needed": 1.6–1.7% operation; about 11–13% with 5-year payback | — | `python3 analysis/r4_machine.py`, `python3 analysis/r5_chain.py` s.4, `r5_pitch_numbers.py` | SOURCED batch API prices (21 Nov 2026); installed cost, life and operator share are ASSUMPTIONS | |
| 7c | CHF income scenario | 80.9k / 94.0k CHF a year (Key numbers only, never spoken) | — | `r5_pitch_numbers.py` H2 | ASSUMPTION 20% operator share; no buyer named | |

## Expected missed-deadline line from the team's own scheduler, by stage reached at 21:00

Seed 1 (= the offer CSV), cap + 8 kWh band, restart outside execution. The team's run should reproduce these within a few jobs. Larger gaps mean the port differs (*computed*, `python3 analysis/r6_build_scope.py`, section 4).

| Stage reached | Dashboard line (N=6 / N=8) | Say |
|---|---|---|
| No admission | 857 of 33,640 (2.55%) / 1,307 of 39,222 (3.33%), every offer accepted | "without admission control" |
| Admission, perfect forecast (MUST) | 0 of 31,859 / 0 of 36,736; accepted 94.7% / 93.6% | "perfect forecast: shows only that admission and execution use the same rule" |
| Admission, archived ECMWF + 2 K guard (OPTIONAL O3) | 0 of 31,908 / 0 of 36,771; accepted 94.8% / 93.7% | "archived ECMWF forecasts issued before each decision, 2 K guard" |
| Same, house dark 72 h from 15 Apr, scheduler told (PROPOSED N1) | 38 of 31,571 / 41 of 36,484 | "one whole-house outage in April, scheduler told" |

## Live demo

| Claim | Real? | How it is shown / caveat |
|---|---|---|
| The same `decide()` produces the yearly balance and controls a real job | LIVE + SCHEDULER | both drivers print the SHA-256 of the core file; the trace-equality test replays the demo day from the 00:00 snapshot incl. job queue | 
| Real J1 (transcription, `mlx_whisper`) paused and resumed on the heat signal | LIVE | SIGSTOP/SIGCONT on the job's process group; `ps -o state=` shows `T` after PAUSE |
| One checkpoint-restart | LIVE (or in the recording if the live mode is flaky) | atomic checkpoint (temp file + `os.replace`), restart with `--resume` |
| The live process does slot s's work that day | **No** | it stands for 8–19 h of booked 1 kW work and does not perform all of it; the real job is pinned to slot s on the demo date only |
| Demo dates (e.g. N=6 2025-07-15 slot 1, pause 02:00, resume 18:00) | SCHEDULER (demo-day finder on the final run) | dates move with seed, offers and pin; hour labels are UTC+1 all year |
| "SIGSTOP stops the heat" | **No** | the laptop freezes the process where a real unit would checkpoint and power down; the balance models power-down |

## Workloads and scaling (must-have 1)

| Claim | Value | Kind | Command / source |
|---|---|---|---|
| J1 runs on our laptop, runtime measured | 25–27× real time | MEASURED (synthetic audio so far; real audio set run today) | `python3 analysis/r3_whisper_energy_probe.py` |
| J1 energy on the laptop | 1.3–1.5 Wh per audio-hour | MEASURED (battery counters, no wall meter) | same |
| J1 on the 1 kW reference server | ~0.7 Wh per audio-hour, ~1,300–1,400 audio-h per kWh, factor ~2 | ANALYSIS from SOURCED MLPerf v6.1 rows (6.1-0017, 6.1-0056) ÷ ASSUMED wall power 0.95 kW | `python3 analysis/r4_machine.py` s.1 |
| J2 (offline LLM generation) | 4 server-h per job, ~36 M output tokens per kWh | benchmark row, not run; job size ASSUMPTION | `r4_machine.py` s.1 |
| Jobs per day | 92 / 108 on average (Jan 143.9 J1 + 18.0 J2; Jul 15.0 + 1.9 at N=6) | ASSUMPTION: a contract size we chose, not one customer's demand | `python3 analysis/r4_headline.py` s.2; offers = the CSV |
| Deadlines, interruptibility, mix | J1 24 h, J2 168 h, both interruptible, 50/50 by server-hours | ASSUMPTION | — |

## Robustness and realism (all from analysis scripts, none from the scheduler)

| Claim in the pitch | Value | Command |
|---|---|---|
| Archived forecast error (if O3 is not in the scheduler) | day-1 RMSE 1.16 K, day-7 2.85 K, +0.29 K bias | `python3 analysis/r2_deadline_sim.py` s.0 |
| 0 missed in 3 seeds under the headline | 0 of 31,908 / 31,694 / 31,996 (N=6) | `r4_headline.py` s.3 (the scheduler shows seed 1 only) |
| GFS / ICON forecasts, −1 K cold bias, failures up to 1 per server-year, overrun +10% | 0; 0 / ≤ 18 a year; 0; 0.39% / 0.24% unpadded | `python3 analysis/r5_miss_stress.py` (5 seeds) |
| Double offer rate | 33 of 28,928 / 11 of 35,991 (seed 1) | `r4_headline.py` s.4 |
| Whole-house outage, scheduler told, 15th of the month | 0 in Nov–Mar; April 38 / 30–41; October 25 / 7; May–Sep 0–17 | `python3 analysis/r6_build_scope.py` s.4 (seed 1, 24 h and 72 h) |
| Same, scheduler not told, 72 h | 236 / 229 (April), 150 / 173 (October) | same |
| No guard band | roughly 0.1–0.6% a year | partly `r5_pitch_numbers.py` J2 (2025: 0.097–0.386%); the upper end is a critic probe, not saved |
| A server dies on the coldest day | 0 missed; 58–134 kWh to the backup heater | `r5_miss_stress.py` s.4 |
| Realism column (cold plates, ≤ 45 °C inlet, house return ≤ 40 °C) | 77.6% / 90.6% year, 82% summer; 55/45 radiators ≥ 64%; 70/55 about 30%; break-even 0.2293 / 0.2359 CHF | `python3 analysis/r5_chain.py` (inputs mostly ASSUMPTIONS) |
| Paused servers left on at idle (worst case) | break-even 0.2659 / 0.2814 CHF | `python3 analysis/r2_realism.py` |
| N=8 under N=6's contract | 73.9% vs 73.7%, 2,944 vs 854 starts | `r5_pitch_numbers.py` D6 |
| N=1 / N=2 | 19.5% / 32.7% coverage | `baseline_sweep.py` |

## Not reproducible from any script (say so)

- The laptop measurement (hardware; re-run the probe on the same machine).
- The 3.3 ms SIGSTOP latency probe.
- The prior-art gap ("we did not find"), an absence after a short search.
- Failure rate 0.5 per 4-GPU server-year from the Llama 3 paper: our hand derivation, order of magnitude only.
- `analysis/one_rack_model.py` (team-written) prices a **different machine** (2 × RTX 4090, consumer-GPU marketplace prices, 80% sold by default) from the reference server (4 × RTX PRO 4500). Label its figures as a separate scenario, or reconcile them before they reach the README or slides.
