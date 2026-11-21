# What is real, what is computed separately, what is assumed

Round 7 (Sat 21 Nov 2026, written around 12:00). This replaces [r6-real-vs-analysis.md](r6-real-vs-analysis.md) and fixes the rows the round-6 critic flagged ([r6-build-scope-audit-critique.md](r6-build-scope-audit-critique.md), F5–F8). It is written so it can be pasted into the README. Background, commands and test runs are in [r7-repo-transparency.md](r7-repo-transparency.md).

**Before pasting:** the README can only link these commands if the files listed in "How to reproduce every number" are committed. Until the team decides, do not call anything under `analysis/` "committed". At the 19:00 configuration freeze, copy the scheduler's printout into the SCHEDULER rows and tick them. Do not use a number that was fixed in advance.

## Labels

| Label | Meaning | How to repeat it |
|---|---|---|
| **SCHEDULER** | Printed by the team's yearly driver, which runs the same `decide()` that controls the live job. One house-year, offers from `analysis/r4_offers_shaped100_seed1.csv` (seed 1 only). | The team's key-figure command (name it here at the freeze). |
| **LIVE** | Happens on the demo laptop: a real process paused and resumed by `decide()`. | The one-command demo; `ps -o state=` shows `T` after PAUSE. |
| **ANALYSIS** | Printed by a separate exploratory script in `analysis/`. It re-implements the same rules but is **not** the scheduler. Some of its figures average 3 or 5 offer seeds. | The command shown (Python 3, standard library, no network). |
| **MEASURED** | A laptop measurement: battery-controller counters, no wall meter. | The probe script on the same laptop (needs `mlx_whisper`, macOS). |
| **SOURCED** | A number read on a public web page. | Open the URL (listed in `docs/research/`). |
| **ASSUMPTION** | Our own choice, listed in the assumptions list. | Change the parameter. |

**The stage decides the seed-1 values.** The scheduler's figures depend on which admission stage lands by the freeze. The plan expects the perfect-forecast stage (MUST); the archived-forecast stage (O3) is an expected cut. Both columns are given below as the regression oracle. **The slide copies whatever the printout says.** The 3-seed means (73.7% / 86.1% etc.) may appear only with the label "mean of 3 offer seeds, analysis script".

## Key figures (the six tiles plus must-have 3)

N=6 / N=8. "Oracle" = what the team's scheduler should print if its port matches. Each oracle value is ANALYSIS, from the command named. All oracle values reprinted in a clean copy of the candidate commit set ([r7-repo-transparency.md](r7-repo-transparency.md), section 3).

| # | Claim / figure | Value, N=6 / N=8 | Where it comes from | Status |
|---|---|---|---|---|
| 1 | Servers per house | 6 and 8 side by side | Scheduler parameter N, run twice | ASSUMPTION (a coverage choice, not an economic result) |
| 2 | Heat demand covered, headline contract | Perfect-forecast stage: **73.13% / 85.85%**. Archived ECMWF + 2 K stage: 73.20% / 85.73% | SCHEDULER at the freeze. Oracle: `python3 analysis/r6_build_scope.py` (section 4, S1 and S3) | SCHEDULER [ ]; oracle ANALYSIS |
| 2m | Same, mean of 3 offer seeds | 73.67% / 86.14% | `python3 analysis/r4_headline.py`, section 3 | ANALYSIS (label it so) |
| 2a | Upper line, unlimited demand | 79.6% / 92.9% | `python3 analysis/baseline_sweep.py` | ANALYSIS; "unlimited jobs" declared |
| 2b | Flat customer, same yearly volume | 53.7% / 60.5% | `python3 analysis/r5_pitch_numbers.py` (line D5) | ANALYSIS; flat offer rate is an ASSUMPTION |
| 3 | Heat dumped | 0 kWh | SCHEDULER (holds by construction of the follow rule); same in every script | SCHEDULER [ ] |
| 4 | Utilisation | Perfect stage: **54.32% / 47.82%**. Archived stage: 54.37% / 47.76%. 3-seed mean: 54.72% / 47.98% | SCHEDULER. Oracle: `python3 analysis/r7_critic_probes.py` section A (perfect) and `r6_build_scope.py` section 4b (archived). Mean: `r4_headline.py` section 3 | SCHEDULER [ ]; oracle ANALYSIS |
| 5 | Missed deadlines | "x of y accepted jobs" + stage + accepted share + "refused at intake". Perfect: **0 of 31,859 / 0 of 36,736**. Archived + 2 K: 0 of 31,908 / 0 of 36,771. No admission: 857 of 33,640 / 1,307 of 39,222 | SCHEDULER. Oracle: `r6_build_scope.py` section 4 | SCHEDULER [ ]; job sizes, deadlines, guard and contract are ASSUMPTIONS |
| 5a | Accepted share of offers | Perfect: 94.69% / 93.64%. Archived: 94.84% / 93.73% | SCHEDULER. Oracle: `r7_critic_probes.py` section A | SCHEDULER [ ] |
| 6 | Break-even, heat credited (case formula) | 0.2261 CHF per sold server-hour | SCHEDULER printer; also `python3 analysis/r2_fleet_economics.py`. It is structural (0.3325 − 0.8 × 0.3325 ÷ 2.5) whenever nothing is dumped and unsold servers are off, so it is not a scheduling result | SCHEDULER [ ]; price SOURCED (ElCom, `data/raw/elcom_iwb_H4_2025_2026.json`); heat = price ÷ 2.5 is the case rule |
| 6a | Break-even, homeowner keeps the heat | 0.3325 CHF | Same run, heat credit 0 | SCHEDULER [ ] |
| 6b | Break-even with a 15-min restart line | Perfect: **0.2279 / 0.2286**. Archived: 0.2279 / 0.2287. 3-seed mean: 0.2278 / 0.2286 | SCHEDULER printer: (electricity − heat) ÷ (sold h − starts × 0.25). Oracle: `r7_critic_probes.py` A; `r6_build_scope.py` 4b; `r4_headline.py` s.3 | SCHEDULER [ ]; 15 min is an ASSUMPTION (server boot not measured) |
| 7 | Electricity cost per year | Perfect: 9,493 / 11,143 CHF. Archived: 9,501 / 11,128. Mean: 9,563 / 11,181 | SCHEDULER printer. Oracle: `r7_critic_probes.py` A; `r6_build_scope.py` 4b | SCHEDULER [ ] |
| 7a | Heat value used per year | Perfect: 3,038 / 3,566 CHF. Archived: 3,040 / 3,561. Mean: 3,060 / 3,578 | Same | SCHEDULER [ ] |
| 7b | Computing income, lead line | Share of list price needed: operation 1.6% (1.7% on the cold-plate chain); 5-year payback about 11–12% on the reference server | `python3 analysis/r4_machine.py` s.3, `python3 analysis/r5_chain.py` s.4, `r5_pitch_numbers.py` H5.6 | ANALYSIS; batch API prices SOURCED (21 Nov 2026); installed cost, life and operator share are ASSUMPTIONS |
| 7c | Same, incl. maintenance and card failures | Reference server 11.8% / 12.9% (12.2% / 13.4% with a 3 h service per box); realism machine 13.4% / 14.6% (8 years 9.4% / 10.1%) | `python3 analysis/r7_critic_probes.py` section E (corrected failure rate 1.01%/yr). The 3 h-service variant stays a round-6 critic probe | ANALYSIS; MTBF SOURCED; maintenance inputs ASSUMPTIONS. **Do not quote `r6_machine.py`'s own 11.6% / 13.1%: that file still uses the misread MTBF.** |
| 7d | Price per sold server-hour needed (5 y, cold-plate chain) | Heat credited 1.70 / 1.87 (3-seed), 1.714 / 1.872 (seed 1). Heat free to the host 1.820 / 1.979 (seed 1) | `python3 analysis/r6_buyer_scenarios.py` s.2; heat-to-host: `r7_critic_probes.py` section F | ANALYSIS; conditional, **no buyer of heat-gated hours found** |
| 7e | CHF income scenario at 20% of list | 80.9k / 94.0k CHF a year | `r5_pitch_numbers.py` H2 | ANALYSIS; 20% share is an ASSUMPTION; Key numbers only, never spoken |

## Expected missed-deadline line from the team's scheduler, by stage reached at the freeze

Seed 1 (= the offer CSV), cap + 8 kWh band, restart outside execution. The team's run should match within a few jobs; a larger gap means the port differs. *Computed*, `python3 analysis/r6_build_scope.py` section 4.

| Stage reached | Dashboard line (N=6 / N=8) | Say |
|---|---|---|
| No admission | 857 of 33,640 (2.55%) / 1,307 of 39,222 (3.33%); every offer accepted | "without admission control" |
| Admission, perfect forecast (MUST) | 0 of 31,859 / 0 of 36,736; accepted 94.7% / 93.6% | "admission reads the actual 2025 weather; this shows only that admission and execution use the same rule, not forecast skill" |
| Admission, archived ECMWF + 2 K guard (O3, expected cut) | 0 of 31,908 / 0 of 36,771; accepted 94.8% / 93.7% | "archived ECMWF forecasts issued before each decision, 2 K guard". Without the guard the same forecast gives 0 / 4, so do not say the guard alone removes the misses |
| Same, house dark 72 h from 15 April, scheduler told incl. the repair time (N1) | 38 of 31,571 / 41 of 36,484 | "one sampled whole-house outage in April, scheduler told" (the highest of 12 sampled start dates, one seed; not a worst case) |

## Live demo

| Claim | Where it comes from | Status / caveat |
|---|---|---|
| The same `decide()` produces the yearly balance and controls a real job | Both drivers print the SHA-256 of the core file; the trace-equality test replays the demo day from the 00:00 snapshot incl. job queue | LIVE + SCHEDULER [ ] |
| Real J1 (transcription, `mlx_whisper`) paused and resumed on the heat signal | SIGSTOP/SIGCONT on the job's process group; `ps -o state=` shows `T` after PAUSE | LIVE [ ] |
| One checkpoint-restart | Atomic checkpoint (temp file + `os.replace`), restart with `--resume` | LIVE, or in the recording [ ] |
| The live process does slot s's work that day | It stands for 8–19 h of booked 1 kW work and does not do all of it; the real job is pinned to slot s on the demo date only | **No**, say so |
| Demo dates (e.g. N=6 2025-07-15 slot 1, pause 02:00, resume 18:00) | Demo-day finder on the final run with the pin; the example is from `r4_headline.py` s.5 (seed 1) | SCHEDULER [ ]; dates move with seed, offers and pin; hour labels UTC+1 all year |
| "SIGSTOP stops the heat" | The laptop freezes the process where a real unit would checkpoint and power down; the balance models power-down | **No**, say so |
| SIGSTOP reaches state T in about 3.3 ms (median) | `python3 analysis/pause_resume_probe.py` | MEASURED on one laptop; hardware-dependent, not a figure a clone reprints exactly |

## Workloads and scaling (must-have 1)

| Claim | Value | Where it comes from | Status |
|---|---|---|---|
| J1 runs on our laptop, runtime | 25–27× real time | `python3 analysis/r3_whisper_energy_probe.py` (needs macOS, `say`, `ioreg`, the `mlx_whisper` CLI and its model, which is downloaded once) | MEASURED, synthetic audio so far |
| J1 energy on the laptop | 1.3–1.5 Wh per audio-hour | Same | MEASURED (battery counters, no wall meter) |
| J1 on the 1 kW reference server | About 0.7 Wh per audio-hour, about 1,300–1,400 audio-hours per kWh, factor about 2 | `python3 analysis/r4_machine.py` s.1, from MLPerf v6.1 rows 6.1-0017 / 6.1-0056 ÷ wall power | ANALYSIS; MLPerf SOURCED (`data/raw/mlperf_inference_v6.1_summary.xlsx`); 0.95 kW wall power is an ASSUMPTION |
| J2 (offline LLM generation) | 4 server-h per job; about 36 M output tokens per kWh | `r4_machine.py` s.1 | Benchmark row, not run by us; job size ASSUMPTION |
| Jobs per day | 92 / 108 on average (N=6 January 143.9 J1 + 18.0 J2, July 15.0 + 1.9) | `python3 analysis/r4_headline.py` s.2; the offers are the CSV | ASSUMPTION: "a contract size we chose (100% of the house's normal heat capacity), not one customer's demand" |
| Deadlines, interruptibility, mix | J1 24 h, J2 168 h, both interruptible, 50/50 by server-hours | Plan | ASSUMPTION |

## Robustness and realism (all from analysis scripts, none from the scheduler)

| Claim in the pitch | Value | Command | Status |
|---|---|---|---|
| Archived forecast error | Day-1 RMSE 1.16 K, day-7 2.85 K, +0.29 K warm bias | `python3 analysis/r5_pitch_numbers.py` (line J1) or `python3 analysis/r5_miss_stress.py --quick` | ANALYSIS. *Fixed:* round 6 cited `r2_deadline_sim.py` s.0, whose full run also needs the uncommitted `prev_runs_basel_2025.csv` |
| 0 missed in 3 seeds under the headline (archived + 2 K) | 0 of 31,908 / 31,694 / 31,996 (N=6); 0 of 36,771 / 36,989 / 37,201 (N=8) | `r4_headline.py` s.3 | ANALYSIS; the scheduler shows seed 1 only |
| GFS / ICON forecasts, failures up to 1 per server-year, overrun +10% unpadded | 0; 0; 0.39% / 0.24% | `python3 analysis/r5_miss_stress.py` (5 seeds) | ANALYSIS; overrun shape ASSUMPTION; the team scheduler has no overrun model |
| −1 K cold bias with guard | 0 / at most 18 a year | `r5_miss_stress.py` | ANALYSIS |
| −2 K / −3 K cold bias with guard | 0.004% / 0.013%; 0.107% / 0.234% | `python3 analysis/r7_critic_probes.py` section C | ANALYSIS. *Fixed:* was "critic probe, not saved" |
| **No guard band** | **Headline contract:** 0% / 0.011–0.043% (5 seeds). **Saturating offers only:** 0.08–0.20% / 0.33–0.56% | `r7_critic_probes.py` section D (causal heating-day flag, archived ifs025) | ANALYSIS. *Fixed:* round 6 cited `r5_pitch_numbers.py` J2, which runs the non-causal round-2 simulator, and put a saturating-offer range next to the headline contract. Never quote "0.1–0.6%" for the headline |
| Double offer rate | 33 of 28,928 / 11 of 35,991 (seed 1) | `r4_headline.py` s.4 | ANALYSIS |
| Whole-house outage 72 h from the 15th, scheduler told incl. repair time | 0 in Nov–Mar; April 38 / 41; October 25 / 7; May–Sep 0–17 (12 sampled starts, seed 1) | `python3 analysis/r6_build_scope.py` s.4 | ANALYSIS; not a worst case |
| **Same, scheduler NOT told** | **Winter (Nov–Mar) 267–307 / 317–386**; April 236 / 229; October 150 / 173 | Winter: `r7_critic_probes.py` section B. April and October: `r6_build_scope.py` s.4 | ANALYSIS. *Fixed:* round 6 quoted only April. "Not told" here = the dry run plans with all N servers even at hour 0; a scheduler that sees the present outage but not its length (`n_avail[0] = 0`) is a different definition and will not reproduce these values |
| A server dies on the coldest day | 0 missed; 58–134 kWh to the backup heater | `r5_miss_stress.py` s.4 | ANALYSIS |
| Realism column (cold plates, ≤ 45 °C inlet, house return ≤ 40 °C) | 77.6% / 90.6% year, 82% summer; 55/45 radiators ≥ 64.3% / 73.0%; 70/55 about 30%; break-even 0.2293 (0.2359 with pumps) | `python3 analysis/r5_chain.py` | ANALYSIS; inputs mostly ASSUMPTIONS; plate ratings SOURCED |
| Paused servers left on at idle (worst case) | Break-even 0.2659 / 0.2814 CHF | `python3 analysis/r2_realism.py` | ANALYSIS; idle fraction ASSUMPTION |
| N=8 under N=6's contract | 73.9% vs 73.7%, 2,944 vs 854 starts | `r5_pitch_numbers.py` D6 | ANALYSIS |
| N=1 / N=2 | 19.5% / 32.7% coverage | `baseline_sweep.py` (N=1); `r5_pitch_numbers.py` (N=2) | ANALYSIS |

## Second economics basis in the repo

| File | What it models | Status |
|---|---|---|
| `analysis/one_rack_model.py` (written by the team) | One house, **one** 1 kW server as 2 × RTX 4090 (used rig, 5,924 + 3,000 CHF), consumer-GPU marketplace prices (Vast.ai / Salad), 80% of run hours sold while the unsold 20% still run, 80% platform share, heat free to the house | ANALYSIS, **sensitivity only, not the pitch basis.** Its "case break-even 0.2826" is 0.2261 ÷ 0.80 because unsold hours still run; `python3 analysis/one_rack_model.py --sold 1.0` prints the case's 0.2261. Its inputs are labelled `[SOURCED]` in the file but were read from the team's research notes, not re-opened this round. Bridge to the pitch basis: `python3 analysis/r7_econ_bridge.py` |

## Not reproducible from any script (say so)

- The laptop energy and runtime measurement: hardware, on the same laptop only.
- The 3.3 ms SIGSTOP latency: a script exists (`pause_resume_probe.py`), but the value depends on the machine.
- The prior-art gap ("we did not find"): an absence after a short search.
- Failure rate 0.5 per 4-GPU server-year, derived by hand from the Llama 3 paper: order of magnitude only.
- The 3 h-service maintenance variant (12.2% / 13.4%), the box-granularity coverage (2 boxes 73.9%, 3 boxes 93.4%), the July-sized flat customer on one server (about 14%, 2.27 CHF) and the outdoor-pool sizing (7–8 M CHF): round-6 critic probes, not saved under `analysis/`. Either label them "estimate" or keep them off slides.
- The offer CSV regenerates byte for byte with `python3 analysis/r4_headline.py --write-offers <path>` **only if** `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv` and `prev_ecmwf_ifs025.csv` are present. Tested in a clean copy of the candidate commit set: byte-identical (`r6_build_scope.py` section 5). Without those two CSVs it would need a network download from Open-Meteo.
