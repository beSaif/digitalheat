# Round 7: the forecast inside the team scheduler (foresight)

Weak point: the 21:00 scheduler most likely admits on a perfect forecast, meaning the actual 2025 weather (open risk 4, founder objections 2 and 3). This file looks for the cheapest honest input for the `fc_demand[0..167]` hook, the stage wording, and a definition of "not told" for the `n_avail[0..167]` hook.

**This is planning and assessment only. Nothing here is the team's scheduler.** One new script: `analysis/r7_forecast_paths.py`, standard library only. It imports `r2_deadline_sim`, `r3_policy_check`, `r5_miss_stress` and `r6_build_scope` without editing them. Command: `python3 analysis/r7_forecast_paths.py` (about 60 s on all cores; `--quick` about 12 s, which skips the outage and seed sections). Currency: CHF. No money figure is new here; break-even is the case formula.

Status labels as in `docs/overnight.md`: *computed* (the script and command are named), *sourced* (I opened the URL), *unverified*, *assumption*.

---

## Findings in 12 lines

1. **The oracle row the plan calls "perfect forecast" is really perfect forecast plus a 2 K guard.** `r6_build_scope.py` S1 calls `r5_miss_stress.cfg(fc="perfect")`, and that config's default is `guard=2.0`. A team scheduler fed the actual weather with no guard prints **0 of 32,174 / 0 of 37,023, accepted 95.6% / 94.4%, coverage 73.53% / 86.10%**. The oracle says 0 of 31,859 / 0 of 36,736, 73.13% / 85.85%. Both are *computed*. If no one notices, A will chase a mismatch that is not a bug.
2. **Perfect-minus-k K is not honest at any k.** Adding k K to the actual temperature still reads the future. Costs: +1 K 0.10 / 0.27 points of coverage, +2 K 0.40 / 0.25, +3 K 0.58 / 0.47. Every one gives 0 missed. Reject it as a "safety version".
3. **Persistence + 2 K guard, built from the reference CSV the driver already reads, is the cheapest honest input.** It needs about 10 driver lines and no new data file. Seed 1: **0 of 31,471 / 0 of 36,272**, accepted 93.5% / 92.4%, coverage **72.30% / 84.10%** (−1.23 / −1.99 points against perfect). In 7 of the 8 runs on offer seeds 2–5 it gives 0; N=8 seed 3 gives 22 of 36,573.
4. **Archived ECMWF + 2 K guard (O3)** needs about 27–30 lines and one more committed CSV (473,508 bytes). Seed 1: 0 of 31,908 / 0 of 36,771, coverage 73.20% / 85.73%. All 8 seed runs give 0. Against persistence it adds +0.90 / +1.63 points of coverage. It is the only candidate that meets "checks the weather forecast".
5. Climatology and trailing means are not cheaper and are worse. 2020–24 climatology + 2 K: 60 / 159 missed. 7-day mean + 2 K: 1 / 59. Persistence/climatology blend + 2 K: 0 / 19.
6. **Look-ahead traps the team must avoid.** (a) A fixed 24 h lag ("yesterday's demand" for every L) reads up to 143 h into the future. The lag must be `K = ceil((L+23)/24)` days. (b) Column `temperature_2m` of the archived CSV is today's run, not a past forecast; never use it for L ≥ 1. (c) The heating-day flag averages the whole target day, which is why K needs the +23.
7. **Small residual look-ahead in the existing analysis lead table, `min(7, ...)`.** For L ≥ 146 the flag uses values issued up to 22 h after decision time. Fixed variants cost at most 0.13 / 0.07 points and still give 0 / 0. ECMWF publication delay is not in the archive. One extra day of lead costs 0.01 / 0.04 points and gives 0 / 0.
8. `fc_demand[0]` = the current hour's actual demand. This is a modelling convention: the house's measured heat draw. Declare it. Strictly, the case's heating-day flag for today needs today's later hours.
9. **Recommended path:** persistence + 2 K guard is the default input of the hook from the first M6 version. Perfect forecast becomes a consistency test only, never the tile. O3 stays the 16:30 upgrade, unchanged.
10. **Dark house, heartbeat rule.** From the second dark hour the scheduler plans `n_avail = 0` for all 168 h until the house reports back. Over 12 sampled starts it gives at most **38 / 29** missed under perfect, **26 / 14** under persistence + 2 K and **38 / 41** under archived. That is close to "told" and far below "not told" (up to 307 / 386).
11. Assuming the house returns 24 h after detection is worse: up to 160 / 190. The heartbeat rule must not assume a repair time.
12. Build-scope flags: about +10 driver lines for B (persistence) and about +3 driver lines for the heartbeat rule. No `decide()` edits (hook already MUST). One correction to the oracle table.

---

## Sources opened (web)

| What | Number or quote used | Status | URL |
|---|---|---|---|
| Meaning of `temperature_2m_previous_dayN` | "Requesting temperature_2m_previous_day1 returns the value predicted 24 hours before valid time"; "_previous_day0 is the current model run (equivalent to the live Forecast API)"; "Data from past model runs is aligned to fixed lead-time offsets of 1–7 days"; "Global models update every 6 hours". The page does not say which run fills an offset, or what the availability delay is. | *sourced* (WebFetch summary of the page, opened 21 Nov 2026) | <https://open-meteo.com/en/docs/previous-runs-api> |
| ECMWF open-data release timing | low-resolution IFS data are released "at the end of the real-time dissemination schedule"; higher-resolution IFS "2h after the low resolution products"; four daily cycles 00/06/12/18 UTC; 06z/18z to step 144. No hours after initialisation are given. | *sourced* (WebFetch summary, opened 21 Nov 2026) | <https://ecmwf.int/en/forecasts/datasets/open-data> |
| ECMWF product schedules page | gives no clock times; it points to the dissemination schedule | *sourced* (nothing usable) | <https://confluence.ecmwf.int/spaces/FUG/pages/673550671/Section+3.1+Product+Schedules> |
| Publication delay in hours | not found | *unverified*; bounded by the "+1 day" variant below | — |

Firecrawl calls used: 0. Re-read the two summarised pages by eye before quoting them on a slide (as the plan's rule for summarising fetch tools requires).

## Local inputs checked

- `analysis/r2_data/prev_ecmwf_ifs025.csv`: 8,764 lines, 473,508 bytes. 3 metadata lines + blank + header, then 8,760 rows. Columns: `time, temperature_2m (°C), temperature_2m_previous_day1 … _day7 (°C)`, UTC+1 fixed (utc_offset_seconds 3600), grid 47.5 N 7.5 E. The `time` column is **identical** to `time_local` of `data/reference_house_2025_hourly.csv` for all 8,760 rows (*computed*, one-liner in the commands section), so the lookup is by row index.
- Lookup for decision hour h, target L: row `h+L`, column `previous_dayK`, `K = min(7, (L+46)//24)` (as `r3_policy_check.run`, `r5_miss_stress.run`). Column `temperature_2m` (day 0) is the current run and must not be used for L ≥ 1.
- `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv`: 2020–24 hourly temperatures. Used here only for climatology and for 14 days of December 2024 (causal persistence in early January; the effect at seed 1 is nil, see "nopad").
- Reference CSV columns used by the persistence builder: `space_heating_kwh`, `day_mean_temperature_c` (both already in the file the driver reads).

---

## (a) Three paths for the `fc_demand` hook

### Results (seed 1 = the offer CSV, headline `shaped100`, cap + 8 kWh band, restart outside execution)

*Computed*, `python3 analysis/r7_forecast_paths.py`, section 1. The script's compact year loop reproduces `r5_miss_stress.run` **identically** (missed, closed, coverage) for perfect, ifs025, ifs025 + 2 K, and the April 72 h outage told / not told (section 0 regression, pasted below).

| Path | Uses future data? | N=6 missed of accepted | acc. | coverage | util. | N=8 missed of accepted | acc. | coverage | util. |
|---|---|---|---|---|---|---|---|---|---|
| perfect, no guard | **yes** | 0 of 32,174 | 95.6% | 73.53% | 54.61% | 0 of 37,023 | 94.4% | 86.10% | 47.96% |
| perfect + 2 K guard (= the plan's "perfect" oracle row) | **yes** | 0 of 31,859 | 94.7% | 73.13% | 54.32% | 0 of 36,736 | 93.6% | 85.85% | 47.82% |
| (iii) perfect temps +1 / +2 / +3 K | **yes** | 0 of 32,042 / 31,857 / 31,747 | 95.2 / 94.7 / 94.4% | 73.43 / 73.13 / 72.95% | | 0 of 36,859 / 36,799 / 36,685 | 94.0 / 93.8 / 93.5% | 85.82 / 85.85 / 85.63% | |
| (i) archived ECMWF, no guard | no | 0 of 32,122 | 95.5% | 73.54% | 54.62% | 4 of 36,905 | 94.1% | 85.46% | 47.60% |
| **(i) archived ECMWF + 2 K (O3)** | no | **0 of 31,908** | 94.8% | **73.20%** | 54.37% | **0 of 36,771** | 93.7% | **85.73%** | 47.76% |
| (i) O3, 7th-day tail fixed (strict) | no | 0 of 31,896 | 94.8% | 73.07% | 54.28% | 0 of 36,764 | 93.7% | 85.66% | 47.72% |
| (i) O3 + 1 day lead (publication delay) | no | 0 of 31,902 | 94.8% | 73.19% | 54.36% | 0 of 36,755 | 93.7% | 85.69% | 47.73% |
| (ii) persistence, no guard | no | 73 of 31,725 | 94.3% | 72.17% | 53.60% | 199 of 36,682 | 93.5% | 84.45% | 47.04% |
| (ii) persistence + 1 K | no | 0 of 31,615 | 94.0% | 72.42% | | 84 of 36,544 | 93.1% | 84.46% | |
| **(ii) persistence + 2 K** | no | **0 of 31,471** | 93.5% | **72.30%** | 53.70% | **0 of 36,272** | 92.4% | **84.10%** | 46.85% |
| (ii) persistence + 2 K, strict (K up to 8) | no | 0 of 31,464 | 93.5% | 72.27% | 53.68% | 0 of 36,275 | 92.4% | 84.06% | 46.83% |
| (ii) persistence + 2 K, CSV only (no Dec 2024) | no | 0 of 31,471 | 93.5% | 72.30% | 53.70% | 0 of 36,272 | 92.4% | 84.10% | 46.85% |
| (ii) persistence + 3 K | no | 0 of 31,417 | 93.3% | 72.24% | | 0 of 36,235 | 92.3% | 84.03% | |
| 7-day same-hour mean + 2 K | no | 1 of 31,699 | 94.2% | 72.52% | | 59 of 36,656 | 93.4% | 84.88% | |
| 2020–24 climatology / + 2 K | no | 121 of 32,116 / 60 of 31,901 | | 72.87 / 72.81% | | 310 of 37,234 / 159 of 36,910 | | 85.20 / 85.32% | |
| (persistence + climatology) / 2 + 2 K | no | 0 of 31,648 | 94.1% | 72.56% | | 19 of 36,605 | 93.3% | 84.88% | |

Break-even is 0.2261 CHF per sold server-hour in every row (case formula, no restart line). Dumped heat is 0 in every row.

**Seed robustness** (offer seeds 2–5 from `r4_headline.offer_stream`; the team scheduler reads seed 1 only), *computed*, section 2b:

| Path | N=6, seeds 2–5 | N=8, seeds 2–5 |
|---|---|---|
| perfect (no guard) | 0, 0, 0, 0; cov 73.55–74.78% | 0, 0, 0, 0; cov 86.33–86.78% |
| persistence + 2 K | 0, 0, 0, 0; cov 72.08–73.63%; acc 92.8–93.5% | 0, **22 of 36,573**, 0, 0; cov 84.59–85.04%; acc 92.4–93.0% |
| archived + 2 K | 0, 0, 0, 0; cov 73.31–74.47% | 0, 0, 0, 0; cov 85.86–86.46% |

### Forecast error against the reference temperature

*Computed*, section 0. Bias and RMSE in K, lead K = 1 / 2 / 7. Heating-day flag errors at K = 2: days wrongly forecast as heating days ("too many") / heating days missed ("too few").

| Source | K1 | K2 | K7 | flag errors K2, guard 0 | guard 2 K |
|---|---|---|---|---|---|
| archived ECMWF | +0.29 / 1.16 | +0.34 / 1.30 | +0.19 / 2.85 | 1 / 9 | 0 / 49 |
| persistence | +0.01 / 2.69 | +0.01 / 3.60 | +0.01 / 4.97 | 21 / 21 | 3 / 46 |
| 7-day mean | +0.01 / 3.48 | +0.01 / 3.83 | +0.01 / 4.31 | 26 / 18 | 5 / 59 |
| climatology | +0.21 / 3.49 | same | same | 14 / 27 | 5 / 47 |

The guard works by removing "too many" days (promised permits that never come). That is what causes misses; "too few" only costs coverage.

### Lines of code, anchored on existing functions

Anchors are *computed* by `r6_build_scope.census()` (printed in section 2). Hour figures use round 6's assumed rates (port 40 lines/h, fresh 20 lines/h, plus check time), so they are *assumptions*.

| Path | What the driver needs | Lines (estimate) | Data to commit | Person-h (assumption) | Honest? |
|---|---|---|---|---|---|
| (i) archived ECMWF + 2 K | `read_prev_runs` 10 + `demand_from_temps` 8 + per-lead cache (`fc_demand`) 6 + `LEAD` 1–3 + per-hour vector 2–3 | **about 27–30** | `analysis/r2_data/prev_ecmwf_ifs025.csv` (473,508 B) | 0.75–1.5 h + 0.5–1.0 check | yes, at the issue time the archive defines; publication delay bounded by "+1 d" (0 / 0) |
| (ii) persistence + 2 K | `persist_from_csv_columns()` in the script = 7 code lines (reads `space_heating_kwh`, `day_mean_temperature_c`; heating day if mean < 10 °C) + `LEAD` 1 + lookup `t = h+L-24*K; own[t] if t >= 0 else 0.5` 2 | **about 10** | none (reads the reference CSV the driver already loads) | 0.25–0.5 h + 0.25–0.5 check | yes, if K = ceil((L+23)/24); checked identical to the temperature-based builder (max diff 0.00005 kWh, CSV rounding) |
| (iii) perfect + k K | `demand_from_temps` 8 + 1 | about 9 (0 for the guard-only version, via the CSV's day-mean column) | none | ~0.5 h | **no**: still reads the actual 2025 weather |

### Look-ahead check, item by item

| Item | Finding | Status |
|---|---|---|
| Issue time vs valid time (archived) | `previous_dayK` = "predicted 24 hours before valid time" (×K). A target value at t from day K was issued at t − 24K. | *sourced* (Open-Meteo page) |
| Heating-day flag built from future hours | The flag averages the target's whole local day, so the last hour of that day (up to t + 23) must also be issued by h. Needs K ≥ (L+23)/24, so `K = ceil((L+23)/24) = (L+46)//24`. The analysis scripts already do this ("causal"). The round-2 simulator's `(L+23)//24` did not. | *computed* reasoning; matches `r3_policy_check.run`, `r5_miss_stress.run` |
| Cap at day 7 | For L ≥ 146 the needed K is 8. `min(7, …)` lets the flag of the 7th-day tail use values issued up to 22 h after h. Fixed: archived "strict" (those hours hot water only) 0 / 0 at 73.07% / 85.66%; persistence "strict" (K = 8 from the past series) 0 / 0 at 72.27% / 84.06%. | *computed* |
| Publication delay (archived) | The archive does not model when a run became public. ECMWF releases IFS open data "at the end of the real-time dissemination schedule" (hours not found). One extra day of lead: 0 / 0 at 73.19% / 85.69%. | delay *unverified*; effect *computed* |
| Day-0 column of the archived CSV | `temperature_2m` = previous_day0 = the current run. Using it for future hours is look-ahead. | *sourced* (same page) |
| Naive persistence "yesterday's demand" | `demand[h+L-24]` for all L reads hours up to h+143 (future) and today's flag. Only `demand[h+L-24K]` with the K above is causal. | reasoning |
| Early January | `r2_deadline_sim.forecast_temps("persist")` wraps to late **December 2025** for the first days (look-ahead). Fixed here with December 2024 from the archive. Setting pre-2025 hours to "no heating" gives the same seed-1 figures. | *computed* |
| End of December | `(h+L) % 8760` makes targets in 2026 read January 2025 values. Not future information, just wrong; it only touches jobs whose deadline falls after 31 Dec, which the missed denominator excludes. | reasoning |
| `fc_demand[0]` | The current hour's actual demand. Physically, this is the house's measured heat draw. In the case formula its heating-day flag uses today's later hours. A declared convention, not a forecast. | reasoning; *assumption* to list |
| Execution | Runs on the actual 2025 permits (the plant). Not a decision input. | as the plan |

---

## (b) Recommendation and stage wording

**Recommend path (ii): persistence + 2 K guard as the hook's default input from the first M6 version.**

- B writes `persist_vector(h)` (about 10 lines, data function, outside `decide()`) next to M5, between 12:45 and 14:15. It checks it alone: the K table, the `t >= 0` branch, and "identical to `demand_from_temps` on shifted temperatures".
- Perfect forecast stays only as a consistency **test**: same code, `fc = actual`, must print 0 missed. It never feeds the tile.
- O3, the archived ECMWF upgrade, keeps its 16:30 gate. It swaps one function, gains +0.90 / +1.63 coverage points and, unlike persistence, "checks the weather forecast".
- Build scope: **+0.5–1 person-h for B** (*assumption*). No change to `decide()`.

**Why not stay with perfect:** it costs nothing in code, but it is the founder's foresight objection. The tile's 0 then proves only that planning and execution share one rule.

**Why not jump straight to archived:** it needs about 3× the lines and a committed CSV, and round 6's gate maths expects O3 to be cut. Persistence lands with M6 by construction.

**Oracle update, needed by any path.** In "Team-scheduler expected values", the "Perfect forecast (MUST)" row is really perfect + 2 K. Either label it so, or add the plain-perfect values 0 of 32,174 / 0 of 37,023, 95.6% / 94.4%, 73.53% / 86.10%, 54.61% / 47.96%. Add a persistence + 2 K row: **0 of 31,471 / 0 of 36,272, 93.5% / 92.4%, 72.30% / 84.10%, 53.70% / 46.85%**.

### Wording by the end state reached at 21:00

Every line names the planning input, the offer scenario ("contract sized to the house's expected heat, `shaped100`, seed 1") and the accepted share. Never print a bare 0%.

| End state | Dashboard missed line (tile 5) | Pitch sentence | Never say |
|---|---|---|---|
| **Archived ECMWF + 2 K** | "Missed: [x] of [y] accepted jobs. Accepted [a]%, refused at intake [100−a]%. Planning input: ECMWF forecasts as issued 1–7 days ahead (archive), 2 K safety margin." | "The scheduler books work only against the weather forecast it would have had that morning, as archived, with a 2-degree safety margin. It missed [x] of [y] accepted jobs. Server failures and overruns are tested only in a separate analysis script." | "real-time forecast", "live weather API" (no live call in the demo) |
| **Persistence + 2 K (recommended default)** | "Missed: [x] of [y] accepted jobs. Accepted [a]%, refused at intake [100−a]%. Planning input: the house's own last full measured day, repeated, with 2 K safety margin (no weather service yet)." | "We have not connected a weather service yet. The scheduler assumes the coming days look like the last day it measured, with a 2-degree margin, and refuses work that would not fit. It missed [x] of [y] accepted jobs. In our analysis script, real archived ECMWF forecasts raise coverage by about one point at six servers." | "forecast" alone without "the house's own last day"; "it checks the weather forecast" |
| **Perfect only** | "Missed: [x] of [y] accepted jobs. Check run: planning used the recorded 2025 weather, so this shows only that planning and execution use the same rule. Decision-time figures from a separate analysis script: persistence 0 of 31,471, archived ECMWF 0 of 31,908 (N=6, seed 1)." | "Our live scheduler still plans on the recorded weather, so its zero only proves that planning and execution agree. That is a check, not a result. With the information a house really has at decision time, its own last day or archived forecasts, our analysis script also gives zero, at about one point less coverage." | "perfect forecast", "foresight", "predicts", "0% missed" |

Q&A 5 sentence, if a judge asks "show me a forecast that can be wrong": "Persistence without a margin misses 73 of 31,725 at six servers and 199 of 36,682 at eight. With a 2-degree margin, 0. In one of eight seed and size runs, at eight servers, it misses 22 of 36,573. Archived ECMWF with the margin gives 0 in all eight." (*computed*, sections 1 and 2b.)

---

## (c) "Not told" / dark house for the `n_avail` hook (5 lines)

1. `n_avail[L]` = servers the scheduler *believes* can run at hour h+L. The driver builds it only from heartbeats received by the start of hour h. No mode ever knows of an outage before it starts.
2. **Dark house (the rule to build):** a house with no heartbeat for one full hour is dark. From the second dark hour on, `n_avail[0..167] = 0`, with no repair time assumed, until a heartbeat returns; then it is N again. In the first dark hour the scheduler still plans with N (a 1 h detection lag).
3. **Missed counting is unchanged.** An accepted job stranded on a dark house that cannot finish by its deadline counts as missed (no hand-off in the team scheduler). Offers arriving while the house is known dark are refused at intake, never counted as missed. The denominator stays "accepted jobs whose deadline fell in the year".
4. Labels for analysis-only bounds: "told" = knows the start and the end (an oracle); "not told" = plans with all N for the whole outage (no detection at all).
5. Numbers, house dark 72 h from the 15th, 12 starts, seed 1 (*computed*, section 3), max over months, N=6 / N=8: heartbeat **38 / 29** (perfect), **26 / 14** (persistence + 2 K), **38 / 41** (archived + 2 K); told 38 / 27, 25 / 13, 38 / 41; not told 307 / 386 under all three; heartbeat with an assumed 24 h repair time 160 / 190.

Build note (*assumption*): with the hook in MUST, the heartbeat rule is about 3 driver lines (`nav = [0]*168 if dark and h > start else [N]*168`). It replaces round 6's N1 "told incl. repair time", which needs the outage end. Only the dark-or-not state is revealed to the scheduler each hour.

---

## Commands run

```
python3 analysis/r7_forecast_paths.py --quick      # sections 0-2, ~12 s
python3 analysis/r7_forecast_paths.py              # all sections, ~60 s, all cores
python3 -c "import csv; ref=[r['time_local'] for r in csv.DictReader(open('data/reference_house_2025_hourly.csv'))]; \
p=[l.split(',')[0] for l in open('analysis/r2_data/prev_ecmwf_ifs025.csv').read().split('\n')[4:] if l]; print(len(ref),len(p),ref==p)"
# -> 8760 8760 True
ls -la analysis/r2_data/    # prev_ecmwf_ifs025.csv 473,508 bytes
```

## Output (relevant parts, pasted from the full run)

```
== 0. Checks ==
  shifted(1) equals actual 24 h earlier for t >= 24: True; first January day reads 2024-12-31 (archive) -4.3 degC, not 2025-12-31 -3.1 degC
  CSV-column persistence (guard 0 K) vs demand_from_temps on the same temperatures: max |diff| 0.00005 kWh
  CSV-column persistence (guard 2 K) vs demand_from_temps on the same temperatures: max |diff| 0.00005 kWh
  forecast temperature error vs the reference temperature (bias, RMSE in K), lead K = 1 / 2 / 7:
    ifs025   K1 +0.29/1.16  K2 +0.34/1.30  K7 +0.19/2.85  heating-day flag wrong at K2: 1 too many / 9 too few days (guard 0); 0 / 49 (guard 2 K)
    persist  K1 +0.01/2.69  K2 +0.01/3.60  K7 +0.01/4.97  heating-day flag wrong at K2: 21 too many / 21 too few days (guard 0); 3 / 46 (guard 2 K)
    trail7   K1 +0.01/3.48  K2 +0.01/3.83  K7 +0.01/4.31  heating-day flag wrong at K2: 26 too many / 18 too few days (guard 0); 5 / 59 (guard 2 K)
    clim     K1 +0.21/3.49  K2 +0.21/3.49  K7 +0.21/3.49  heating-day flag wrong at K2: 14 too many / 27 too few days (guard 0); 5 / 47 (guard 2 K)
    blend    K1 +0.11/2.60  K2 +0.11/3.10  K7 +0.11/3.94  heating-day flag wrong at K2: 16 too many / 20 too few days (guard 0); 3 / 51 (guard 2 K)

  regression: this script's compact run vs r5_miss_stress.run (missed of closed; coverage)
    perfect      N=6: here 0 of 32,174, 73.53% | r5 0 of 32,174, 73.53% -> IDENTICAL
    perfect      N=8: here 0 of 37,023, 86.10% | r5 0 of 37,023, 86.10% -> IDENTICAL
    ifs025+g2    N=6: here 0 of 31,908, 73.20% | r5 0 of 31,908, 73.20% -> IDENTICAL
    ifs025+g2    N=8: here 0 of 36,771, 85.73% | r5 0 of 36,771, 85.73% -> IDENTICAL
    ifs025       N=6: here 0 of 32,122, 73.54% | r5 0 of 32,122, 73.54% -> IDENTICAL
    ifs025       N=8: here 4 of 36,905, 85.46% | r5 4 of 36,905, 85.46% -> IDENTICAL
    Apr told     N=6: here 38 of 31,571, 72.47% | r5 38 of 31,571, 72.47% -> IDENTICAL
    Apr told     N=8: here 41 of 36,484, 84.94% | r5 41 of 36,484, 84.94% -> IDENTICAL
    Apr nottold  N=6: here 236 of 31,762, 72.47% | r5 236 of 31,762, 72.47% -> IDENTICAL
    Apr nottold  N=8: here 229 of 36,667, 85.07% | r5 229 of 36,667, 85.07% -> IDENTICAL

== 1. Forecast candidates for the fc_demand hook (seed 1, headline shaped100) ==
  perfect                0 of  32,174 (0.000%)  95.6%  73.53% 54.61% 0.2261       0 of  37,023 (0.000%)  94.4%  86.10% 47.96%
  perfect+g2             0 of  31,859 (0.000%)  94.7%  73.13% 54.32% 0.2261       0 of  36,736 (0.000%)  93.6%  85.85% 47.82%
  perfect+1K             0 of  32,042 (0.000%)  95.2%  73.43% 54.54% 0.2261       0 of  36,859 (0.000%)  94.0%  85.82% 47.81%
  perfect+2K             0 of  31,857 (0.000%)  94.7%  73.13% 54.32% 0.2261       0 of  36,799 (0.000%)  93.8%  85.85% 47.82%
  perfect+3K             0 of  31,747 (0.000%)  94.4%  72.95% 54.18% 0.2261       0 of  36,685 (0.000%)  93.5%  85.63% 47.70%
  ifs025                 0 of  32,122 (0.000%)  95.5%  73.54% 54.62% 0.2261       4 of  36,905 (0.011%)  94.1%  85.46% 47.60%
  ifs025+g2              0 of  31,908 (0.000%)  94.8%  73.20% 54.37% 0.2261       0 of  36,771 (0.000%)  93.7%  85.73% 47.76%
  ifs025+g2 strict       0 of  31,896 (0.000%)  94.8%  73.07% 54.28% 0.2261       0 of  36,764 (0.000%)  93.7%  85.66% 47.72%
  ifs025+g2 +1d          0 of  31,902 (0.000%)  94.8%  73.19% 54.36% 0.2261       0 of  36,755 (0.000%)  93.7%  85.69% 47.73%
  persist               73 of  31,725 (0.230%)  94.3%  72.17% 53.60% 0.2261     199 of  36,682 (0.543%)  93.5%  84.45% 47.04%
  persist+g1             0 of  31,615 (0.000%)  94.0%  72.42% 53.79% 0.2261      84 of  36,544 (0.230%)  93.1%  84.46% 47.05%
  persist+g2             0 of  31,471 (0.000%)  93.5%  72.30% 53.70% 0.2261       0 of  36,272 (0.000%)  92.4%  84.10% 46.85%
  persist+g2 strict      0 of  31,464 (0.000%)  93.5%  72.27% 53.68% 0.2261       0 of  36,275 (0.000%)  92.4%  84.06% 46.83%
  persist+g3             0 of  31,417 (0.000%)  93.3%  72.24% 53.65% 0.2261       0 of  36,235 (0.000%)  92.3%  84.03% 46.81%
  persist+g2 nopad       0 of  31,471 (0.000%)  93.5%  72.30% 53.70% 0.2261       0 of  36,272 (0.000%)  92.4%  84.10% 46.85%
  trail7+g2              1 of  31,699 (0.003%)  94.2%  72.52% 53.86% 0.2261      59 of  36,656 (0.161%)  93.4%  84.88% 47.28%
  clim                 121 of  32,116 (0.377%)  95.5%  72.87% 54.12% 0.2261     310 of  37,234 (0.833%)  94.9%  85.20% 47.46%
  clim+g2               60 of  31,901 (0.188%)  94.8%  72.81% 54.08% 0.2261     159 of  36,910 (0.431%)  94.1%  85.32% 47.53%
  blend+g2               0 of  31,648 (0.000%)  94.1%  72.56% 53.89% 0.2261      19 of  36,605 (0.052%)  93.3%  84.88% 47.28%

== 2. LOC anchors (r6_build_scope.census(), non-blank non-comment non-docstring lines) ==
  fc_read       10  r2_deadline_sim.py read_prev_runs() lines 92-102
  fc_formula     8  r2_deadline_sim.py demand_from_temps() lines 81-89 (case formula + guard threshold)
  fc_demand      6  r3_policy_check.py fc_demand() lines 148-153
  fc_lead        3  r3_policy_check.py run() lines containing LEAD / lambda L (causal lead)
  persist        2  r2_deadline_sim.py forecast_temps() lines 176-177 (persistence)
  persist_from_csv_columns() in this file: 7 code lines (incl. def and CSV read)

== 2b. Seed robustness (offer seeds 2-5 from r4_headline.offer_stream; the team scheduler reads seed 1 only) ==
  perfect           N=6: missed 0 of 31,892, 0 of 32,167, 0 of 32,007, 0 of 32,075; coverage 73.55-74.78%; accepted 95.0-95.3%
  perfect           N=8: missed 0 of 37,267, 0 of 37,461, 0 of 36,966, 0 of 37,010; coverage 86.33-86.78%; accepted 93.8-94.7%
  persist+g2        N=6: missed 0 of 31,274, 0 of 31,542, 0 of 31,499, 0 of 31,325; coverage 72.08-73.63%; accepted 92.8-93.5%
  persist+g2        N=8: missed 0 of 36,561, 22 of 36,573, 0 of 36,378, 0 of 36,697; coverage 84.59-85.04%; accepted 92.4-93.0%
  ifs025+g2         N=6: missed 0 of 31,694, 0 of 31,996, 0 of 31,857, 0 of 31,870; coverage 73.31-74.47%; accepted 94.5-94.7%
  ifs025+g2         N=8: missed 0 of 36,989, 0 of 37,201, 0 of 36,834, 0 of 36,931; coverage 85.86-86.46%; accepted 93.6-94.0%

== 3. Whole house dark 72 h from the 15th 00:00, by month, seed 1 (n_avail hook modes) ==
  perfect     N=6 told      [0, 0, 0, 38, 17, 2, 5, 0, 11, 25, 0, 0]  max 38
  perfect     N=6 nottold   [274, 277, 307, 236, 78, 21, 34, 24, 23, 150, 289, 267]  max 307
  perfect     N=6 detect    [2, 7, 9, 38, 18, 2, 7, 0, 11, 26, 4, 7]  max 38
  perfect     N=6 detect24  [131, 141, 160, 150, 56, 11, 19, 20, 21, 86, 137, 125]  max 160
  perfect     N=8 told      [0, 0, 0, 27, 12, 5, 3, 3, 10, 7, 0, 0]  max 27
  perfect     N=8 nottold   [375, 347, 317, 195, 55, 20, 25, 33, 32, 173, 338, 386]  max 386
  perfect     N=8 detect    [8, 3, 9, 29, 14, 5, 4, 3, 10, 11, 6, 5]  max 29
  perfect     N=8 detect24  [174, 170, 164, 95, 35, 19, 15, 16, 30, 75, 174, 190]  max 190
  persist+g2  N=6 told      [0, 0, 0, 0, 17, 2, 5, 0, 11, 25, 0, 0]  max 25
  persist+g2  N=6 nottold   [274, 277, 307, 40, 76, 21, 34, 24, 23, 138, 82, 267]  max 307
  persist+g2  N=6 detect    [2, 7, 9, 0, 18, 2, 7, 0, 11, 26, 4, 7]  max 26
  persist+g2  N=6 detect24  [131, 141, 160, 32, 56, 11, 19, 20, 21, 86, 50, 125]  max 160
  persist+g2  N=8 told      [0, 0, 0, 0, 12, 7, 1, 13, 9, 7, 0, 0]  max 13
  persist+g2  N=8 nottold   [375, 347, 317, 41, 55, 31, 24, 43, 27, 135, 0, 386]  max 386
  persist+g2  N=8 detect    [8, 3, 9, 0, 14, 7, 2, 13, 9, 11, 0, 5]  max 14
  persist+g2  N=8 detect24  [174, 170, 164, 32, 35, 21, 13, 26, 27, 75, 0, 190]  max 190
  ifs025+g2   N=6 told      [0, 0, 0, 38, 17, 2, 5, 0, 11, 25, 0, 0]  max 38
  ifs025+g2   N=6 nottold   [274, 277, 307, 236, 76, 21, 34, 24, 23, 150, 289, 267]  max 307
  ifs025+g2   N=6 detect    [2, 7, 9, 38, 18, 2, 7, 0, 11, 26, 4, 7]  max 38
  ifs025+g2   N=6 detect24  [131, 141, 160, 146, 56, 11, 19, 20, 21, 86, 137, 125]  max 160
  ifs025+g2   N=8 told      [0, 0, 0, 41, 12, 7, 1, 13, 9, 7, 0, 0]  max 41
  ifs025+g2   N=8 nottold   [375, 347, 317, 229, 55, 31, 24, 43, 27, 173, 338, 386]  max 386
  ifs025+g2   N=8 detect    [8, 3, 9, 41, 14, 7, 2, 13, 9, 11, 6, 5]  max 41
  ifs025+g2   N=8 detect24  [174, 170, 164, 145, 35, 21, 13, 26, 27, 75, 174, 190]  max 190
```

The ifs025 + 2 K "told" rows reproduce round 6's table exactly ([0,0,0,38,17,2,5,0,11,25,0,0] and [0,0,0,41,12,7,1,13,9,7,0,0]).

## Limits

- One weather year. Seeds 1–5 of one offer generator. Stand-in reference CSV. "Detect" is a model of a heartbeat, not a designed protocol: where the scheduler runs (in the house or at the operator) is open. If it runs in the house, a power cut also stops admission, which behaves like a 0 h detection lag for new offers.
- Persistence + 2 K at N=8 is not 0 in every seed (22 of 36,573, seed 3). The tile prints seed 1 only; say "seed 1" with the number.
- The perfect + 2 K oracle mix-up affects only the label of an expected value, not any slide figure already copied from the freeze printout.
