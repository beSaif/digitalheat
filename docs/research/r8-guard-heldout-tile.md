# Round 8: held-out check of the 2 K guard, and a missed-deadline tile that can tell inputs apart

Weak point: every guarded planning input prints 0 missed, so tile 5 cannot tell a good forecast from a bad one, and the 2 K guard was chosen and scored on the same 2025 weather (open risk 4, Q&A 5).

**This is planning and assessment only.** Nothing here is the team's scheduler, dashboard or demo. No git state was changed, and no existing file was edited. Firecrawl calls: 0. Web pages opened: none. The only web request was one small data download, with coordinates only (below).

Files written this round:
- `analysis/r8_guard_heldout.py` (standard library only; imports `r2_deadline_sim`, `r3_policy_check`, `r4_headline`, `r5_miss_stress` and `r7_forecast_paths` without editing them)
- `analysis/r8_guard_probe.py` (follow-up probe, imports the script above)
- `analysis/r8_data/prev_ecmwf_ifs025_2024.csv` (473,580 bytes, downloaded in this round)
- `docs/research/r8-guard-heldout-output.txt` (full printout)
- this file

Status labels as in `docs/overnight.md`: *computed* (script and command named), *sourced* (URL opened and read), *unverified*, *assumption*. **Currency: none.** This file has no money figures and does not recompute break-even.

---

## Findings in 10 lines

1. **With the archived ECMWF forecast (O3), 2 K survives the one held-out year we have.** On 2024 weather (archive present from 3 Feb 2024), O3 + 2 K misses **0 at N=6 and at N=8 in all 5 offer seeds**: 0 of 152,405 and 0 of 177,286 accepted jobs closed (*computed*). Picking the guard on 2024 alone and scoring 2025 also gives 2 K and 0.
2. **One caveat for O3.** At N=6, 2025 alone has 0 misses even with no guard, so a guard picked on 2025 would have been 0 K. On 2024 that gives 5 of 30,621 at seed 1 (43 over 5 seeds). The 2 K holds; a "fit on one year" choice would not have found it at N=6.
3. **With persistence (P1), 2 K does not survive out of sample. Nor does any guard from 0 to 6 K.** Under the headline's contract construction, 2025 is the only year of six in which P1 + 2 K gives 0. Seed 1 on 2020–24: **135 / 57 / 10 / 172 / 60 missed at N=6, 199 / 55 / 41 / 372 / 122 at N=8.** Pooled over 5 seeds: **0.318% / 0.427%** of accepted jobs (*computed*).
4. Leave-one-year-out picks 3 K for P1 on every fold, the edge of the grid. 3 K still misses on the held-out year: pooled 0.182% / 0.281% over 2020–24. At 6 K, 2023 still misses 88–109 at N=6 and 194–240 at N=8 (*computed*, probe). So the plan's "persistence + 3 K: 0 in all 10 runs" holds **only on 2025 weather**.
5. **Why it happens.** The misses come in clusters of 10–58 jobs on single days in March, April and November. All are J1 except 8 J2 in 2020. On each of those days the daily mean jumps by about 3–9 K across the case's 12 °C heating-day cliff (e.g. 2023: 5.8 → 14.1 °C). Persistence still plans a heating day, so the actual permits drop to hot water only. A flag guard cannot cover a 9 K jump. A forecast sees the warm spell coming (*computed*, section 5).
6. **A magnitude margin does not fix it either.** Planning as if each persisted hour were 3 K warmer, on top of the 2 K flag guard, cuts pooled misses by only 4% (N=6) and 6% (N=8) (*computed*).
7. **The check run gives 0 in every year and every seed** (0 of 926,500 / 0 of 1,078,254 closed). This confirms that planning equals execution across six weather years (*computed*).
8. **The refused-work line is what separates the stages.** For 2025, seed 1, N=6, all three stages print "0 missed", but refused work differs: **884 server-h (check run), 1,460 (P1 + 2 K), 1,041 (O3 + 2 K)**. At N=8: 1,316 / 2,162 / 1,500. That is +577 / +846 server-h of work turned away by persistence and +158 / +183 by ECMWF (*computed*).
9. **Destination.** The team scheduler routes refused work nowhere. The tile should say "returned to the aggregator, not run here", not "partner site" or "cloud": neither is modelled, and no site is named.
10. Build scope:
    - Line 2 of the tile (refused jobs and server-hours) comes from counters the printer already needs for the accepted share. About 2–3 printer lines (*assumption*).
    - The "vs check run" delta needs a second yearly run. It is **optional, cut first** (flag: small scope addition).

---

## (a) Leave-one-year-out check of the guard

### How each year was built (*computed*, `python3 analysis/r8_guard_heldout.py`)

- **Temperatures.**
  - 2020–2024 come from `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv`. This is the Open-Meteo archive, `models=ecmwf_ifs`, grid cell 47.557 N 7.549 E, UTC+1. It is the same model and cell as the reference house. 29 Feb is dropped by `r2_deadline_sim.read_archive_years()`, so every year has 8,760 h.
  - 2025 is the reference-house CSV.
  - The download URL for the 2020–24 file is in `docs/research/r2-missed-deadlines.md`.
  - The reference weather is a model, not a thermometer, and that holds for all six years.
- **Heat demand of year Y.** We use the case formula unchanged (`r2_deadline_sim.demand_from_temps(T_Y, 12.0)`):
  - space heating = max(0, 10 × (20 − T) / 25.6) kWh on a heating day (day mean < 12 °C), else 0;
  - plus 0.5 kWh hot water every hour.
  - **The constant 25.6 is kept fixed for every year.** It is the case's constant, which makes 2025's coldest hour (−5.6 °C) give 10 kWh. Colder years therefore peak above 10 kWh: 2021 reaches 14.05 kWh/h at −14.7 °C.
  - For 2025 the script uses the CSV values. The formula reproduces them to 0.00005 kWh.
- **Offers of year Y ("scaled to each year's capacity"), main case: the headline construction applied out of sample.**
  - Monthly offer rate = 100% of the mean plain-follow heat-permit capacity of that month over the **other five years** (`r2_deadline_sim.follow_monthly`).
  - Arrivals are Poisson from `r4_headline.offer_stream(rates, seed)`, offer seeds 1–5.
  - For 2025 this equals the headline contract (the 2020–24 normal). The script asserts that seed 1 equals `analysis/r4_offers_shaped100_seed1.csv` byte for byte (section 0: `True` at N=6 and N=8).
- **Offers, sensitivity "own".** Rates = 100% of year Y's own monthly capacity. This contract knows the year's monthly weather, which makes it harsher in cold months.
- **Planning inputs.** Lead K = min(7, ceil((L+23)/24)), the oracle's table.
  - **check run:** actual demand, no guard.
  - **P1:** own[t − 24K], where own is the case formula with heating-day threshold 12 − g. If t − 24K < 0, the value is 0.5. No data from the previous year is used: this is the plan's P1 rule ("t < 0 → 0.5, no wrap"). For 2025 the script uses `r7_forecast_paths.persist_from_csv_columns` itself.
  - **O3:** archived ECMWF IFS 0.25°, `previous_dayK`, threshold 12 − g.
- **Where O3 exists.**
  - 2025: `analysis/r2_data/prev_ecmwf_ifs025.csv`.
  - 2024: new download, `analysis/r8_data/prev_ecmwf_ifs025_2024.csv`. Its first non-NaN `temperature_2m` is 2024-02-03T01:00, and `previous_day7` starts at 2024-02-10T01:00. Hours before that fall back to P1's persisted temperature (labelled in the code).
  - No archived forecast exists for 2020–2023 in the repo, and Open-Meteo's 0.25° IFS archive starts in February 2024 for this point.
- **Run rules.** Cap + 8 kWh band, earliest-deadline-first dry run, restart outside execution, no outages. They are copied from `r7_forecast_paths.run` with demand, forecast and offers as arguments. Section 0 shows **IDENTICAL** results to `r7_forecast_paths.run` for all 12 regression cases: check, O3 + 0/2 K and P1 + 0/1/2 K, at N=6 and N=8. N=8 P1 + 2 K seed 3 reproduces the known 22 of 36,573.
- **Guard selection.** Grid g ∈ {0, 1, 2, 3} K. On the training years (the other five, all 5 seeds), take the smallest g with 0 training misses. If none has 0, take the g with the fewest training misses, ties to the smaller g. Score that g on the held-out year.
- **O3 folds.** With archives for only two years, the O3 "leave-one-out" is train-on-one, test-on-the-other.

Download command (run once, 21 Nov 2026; request contains coordinates only):
```bash
cd analysis/r8_data
V="temperature_2m,temperature_2m_previous_day1,temperature_2m_previous_day2,temperature_2m_previous_day3,temperature_2m_previous_day4,temperature_2m_previous_day5,temperature_2m_previous_day6,temperature_2m_previous_day7"
curl -s -m 60 -o prev_ecmwf_ifs025_2024.csv "https://previous-runs-api.open-meteo.com/v1/forecast?latitude=47.56&longitude=7.59&hourly=$V&start_date=2024-01-01&end_date=2024-12-31&timezone=Europe%2FZurich&format=csv&models=ecmwf_ifs025"
```
The file reports grid point 47.5 N 7.5 E and `utc_offset_seconds` 3600, the same as the 2025 file.

### The six weather years (*computed*, section 1)

```
  year   min T heat days space kWh peak kWh/h Jan cap N6 Jul cap N6 year cap N6 srv-h/d     N8  P1 temp error K1 / K2 (bias/RMSE)
  2020    -4.7       188    24,665      10.15      144.0       15.0                79.9   94.0  -0.01/3.14  -0.01/4.18
  2021   -14.7       221    30,213      14.05      144.0       15.0                91.4  108.8  -0.02/2.80  -0.05/3.71
  2022    -6.8       185    24,636      10.97      143.7       15.0                78.3   91.4  -0.02/2.88  -0.03/3.61
  2023    -6.5       184    24,285      10.85      144.0       15.0                79.1   92.0  +0.02/3.02  +0.03/3.91
  2024    -7.1       189    24,480      11.09      143.9       15.0                80.2   93.4  +0.02/3.04  +0.04/3.91
  2025    -5.6       206    26,851      10.50      144.0       15.0                85.1   99.4  +0.01/2.69  +0.03/3.58
  archived ifs025 day 1: 2024 bias +0.65 RMSE 1.34 K (7,943 of 8,760 hours present) | 2025 bias +0.29 RMSE 1.16 K
  archived ifs025 day 2: 2024 bias +0.69 RMSE 1.44 K (7,919 of 8,760 hours present) | 2025 bias +0.34 RMSE 1.30 K
  archived ifs025 day 7: 2024 bias +0.46 RMSE 2.80 K (7,799 of 8,760 hours present) | 2025 bias +0.19 RMSE 2.85 K
```

Persistence's day-1 error is lowest in 2025 (2.69 K RMSE, against 2.80–3.14 K in 2020–24). The 2024 ECMWF forecast runs warmer against the truth than in 2025 (+0.65 K against +0.29 K on day 1). A warm bias is the cautious direction.

### Result: P1 (persistence), held-out year by year, main contract (*computed*, section 3a)

"seed 1" = one offer seed. "5 seeds" = summed over offer seeds 1–5. Coverage and accepted share are 5-seed means. The check run is the same year, no guard.

| Held out | N | Picked on the other 5 | Held-out misses at the pick, seed 1 (5 seeds) | Fixed 2 K, seed 1 (5 seeds) | Accepted at pick / check | Coverage at pick / check |
|---|---|---|---|---|---|---|
| 2020 | 6 | 3 K | 30 of 29,817 (178 of 148,536) | 135 of 30,006 (641) | 87.2% / 88.2% | 74.40% / 76.20% |
| 2021 | 6 | 3 K | 57 of 31,773 (245) | 57 of 31,773 (249) | 95.7% / 96.7% | 65.65% / 66.40% |
| 2022 | 6 | 3 K | 0 of 29,432 (4) | 10 of 29,449 (175) | 86.4% / 87.9% | 74.05% / 75.06% |
| 2023 | 6 | 3 K | 172 of 29,871 (921) | 172 of 29,889 (930) | 87.9% / 89.9% | 76.14% / 78.01% |
| 2024 | 6 | 3 K | 0 of 30,239 (25) | 60 of 30,308 (413) | 88.9% / 90.0% | 76.33% / 77.99% |
| 2025 | 6 | 3 K | 0 of 31,417 (0) | **0 of 31,471 (0)** | 93.2% / 95.2% | 72.78% / 74.07% |
| 2020 | 8 | 3 K | 88 of 34,385 (364) | 199 of 34,650 (924) | 86.7% / 88.9% | 86.47% / 89.89% |
| 2021 | 8 | 3 K | 53 of 36,908 (310) | 55 of 36,948 (312) | 95.6% / 97.0% | 76.56% / 77.72% |
| 2022 | 8 | 3 K | 19 of 34,096 (43) | 41 of 34,300 (242) | 86.2% / 87.6% | 85.91% / 87.73% |
| 2023 | 8 | 3 K | 383 of 34,550 (1,716) | 372 of 34,637 (1,694) | 87.3% / 89.1% | 88.28% / 90.61% |
| 2024 | 8 | 3 K | 14 of 35,196 (42) | 122 of 35,209 (603) | 88.5% / 88.4% | 89.07% / 90.51% |
| 2025 | 8 | 3 K | 0 of 36,235 (0) | **0 of 36,272 (22)** | 92.6% / 94.3% | 84.68% / 86.48% |

Training misses never reach 0 for P1. For example, with 2025 held out at N=6 the other five years give g0 5,687, g1 3,476, g2 2,408 and g3 1,373 misses, so the rule falls back to "fewest", which is always the largest guard.

Pooled (section 6, *computed*), P1, main contract, 2020–24, 5 seeds:

| Input | N=6 | N=8 |
|---|---|---|
| P1 + 2 K | 2,408 of 757,399 = **0.318%** | 3,775 of 883,783 = **0.427%** |
| P1 + 3 K | 1,373 of 755,961 = 0.182% | 2,475 of 880,174 = 0.281% |

Years with 0 in every seed: 0 of 5 in all four cases.

### Result: O3 (archived ECMWF), train on one year, test on the other (*computed*, section 3a)

| Held out | N | Picked on the other year | Held-out misses at the pick, seed 1 (5 seeds) | Fixed 2 K, seed 1 (5 seeds) | Coverage 2 K / check (5-seed mean) |
|---|---|---|---|---|---|
| 2024 | 6 | **0 K** (2025 has 0 at every g) | 5 of 30,621 (43 of 153,600) | **0 of 30,543 (0 of 152,405)** | 77.17% / 77.99% |
| 2025 | 6 | 2 K | 0 of 31,908 (0 of 159,325) | 0 of 31,908 (0) | 73.76% / 74.07% |
| 2024 | 8 | 2 K | 0 of 35,266 (0 of 177,286) | **0 of 35,266 (0)** | 89.80% / 90.51% |
| 2025 | 8 | 2 K | 0 of 36,771 (0 of 184,726) | 0 of 36,771 (0) | 86.08% / 86.48% |

O3 + 2 K under the "own" contract is also 0 in all seeds for both years and both N (section 2b).

O3's coverage cost against the check run is larger in 2024 than in 2025: 0.82 / 0.71 points against 0.31 / 0.40 (5-seed means).

### Sensitivity: offers sized to the held-out year's own capacity (*computed*, sections 3b and 6)

| P1 + 2 K, "own" contract | N=6 | N=8 |
|---|---|---|
| Pooled 2020–24 | 2,649 of 784,044 = 0.338% | 3,628 of 913,116 = 0.397% |
| 2025 itself, seed 1 | 40 missed | 42 missed |

Under a contract that matches 2025's own capacity, P1 + 2 K misses on 2025 too. The headline's 0 depends on the contract being the 2020–24 normal, which is lighter than 2025's own capacity: 85.1 against 81.8 server-h/day a year at N=6 (mean of the 2020–24 rows in the section 1 table).

### Why persistence misses (*computed*, section 5)

Misses by deadline month, N=6, seed 1:

| Year | Misses | Months |
|---|---|---|
| 2020 | 135 | April 76, November 59 |
| 2021 | 57 | March |
| 2022 | 10 | April |
| 2023 | 172 | March 89, April 34, November 49 |
| 2024 | 60 | April |
| 2025 | 0 | — |

All misses are J1 (24 h deadline) except 8 J2 in 2020.

Days with misses and their daily means (3 days before to 1 day after):

```
    2020 day 107 ( 4):  23 missed | day means   7.5   9.6  13.7  16.2  16.3
    2020 day 306 (11):  58 missed | day means  12.2   9.5  12.1  16.1  11.8
    2021 day  90 ( 3):  57 missed | day means   7.4  10.7  12.2  13.0  14.4
    2023 day  89 ( 3):  34 missed | day means   5.0   5.5  12.1  13.8  11.5
    2023 day 318 (11):  42 missed | day means   6.3   5.8  14.1  12.4   9.6
    2024 day  96 ( 4):  30 missed | day means   9.7  13.0  15.0  16.0  17.5
```

Each cluster follows a jump of the daily mean across the 12 °C cliff:

1. Persistence repeats a day-before-yesterday that was a heating day.
2. The case formula then plans up to 6 servers of space-heating permits.
3. The actual day is not a heating day, so the permits fall to 0.5 kWh/h hot water and one server at most (cap).
4. J1 jobs accepted on those permits cannot finish within 24 h.

The guard only moves the threshold, so it helps only when the persisted day was between 12 − g and 12 °C.

A probe that tries harder (`python3 analysis/r8_guard_probe.py`, seeds 1–3, *computed*) does not rescue P1. These rules were chosen after seeing all six years, so nothing in the probe is held out:

| Rule | Result |
|---|---|
| 4 K guard | 2023: 88–110 (N=6), 223–258 (N=8) |
| 6 K guard | 2023: 88–109 (N=6), 194–240 (N=8); 2022 still 4 at N=6 |
| Lowest of the last 3 persisted days, 2 K | 2023: 138–166 (N=6), 268–317 (N=8) |

Magnitude margin (section 5, *computed*): persisted hourly temperature + 3 K in the space-heating term, flag guard 2 K.

| Pooled 2020–24 misses over 5 seeds | w = 0 | w = 3 K |
|---|---|---|
| N=6 | 2,408 | 2,303 |
| N=8 | 3,775 | 3,550 |

### Verdict on (a)

- **O3 (archived ECMWF) + 2 K survives out of sample.** It gives 0 on held-out 2024 at N=6 and N=8, all 5 seeds, under both contracts.
- The evidence for O3 is one held-out year whose archive starts on 3 Feb. The 2024 truth is the same model family as the forecast, as in 2025. At N=6, picking the guard on 2025 alone would have chosen 0 K and missed 43 over 5 seeds in 2024.
- **P1 (persistence) + 2 K does not survive.** 2025 is the only year of six with 0. On 2020–24 it misses 0.32% / 0.43% of accepted jobs (N=6 / N=8). No guard from 0 to 6 K brings every year to 0.
- If the team ends at P1, its "0 of 31,471 / 0 of 36,272" is a property of the 2025 weather, and must not be presented as robust.

---

## (b) A tile-5 line that discriminates

### What the team scheduler can say about refused work

- Refused at intake = offered − accepted. The team scheduler already counts both for the accepted share.
- Server-hours = refused J1 × 0.5 + refused J2 × 4.
- **Where it goes:** the scheduler does not route it. The only honest destination on the tile is **"returned to the aggregator, not run here"**.
- "Partner site" and "cloud" are not modelled, and no site is named. They belong in Q&A or the README: "in a fleet, the aggregator sends it to a site with heat demand (typed: indoor pool, care home, hospital) or to cloud; we did not model either; nothing is dumped".
- **Do not show "partner site: x server-h"** as a number. There is no partner in the balance, and that would be a claim we cannot back.

### Exact label text, per stage (values: 2025, seed 1 = the offer CSV, *computed*, `python3 analysis/r8_guard_heldout.py` section 4)

The tile layout:
- **Line 1 (big):** the scheduler's own count, as now.
- **Line 2 (new, MUST once admission is in the core):** refused work and where it goes.
- **Line 3:** planning input and contract.
- **Line 4 (optional, cut first):** extra work refused because of the planning input. It needs a second yearly run with the check-run input.
- **Line 5 (analysis-script line, labelled):** the held-out result for the input used.

**Check run (MUST stage)**, N=6 (N=8 in brackets):
> **Missed deadlines: 0 of 32,174 accepted jobs** (0 of 37,023)
> Refused at intake: 1,466 jobs = 884 server-h, 3.0% of offered work (2,199 jobs = 1,316 server-h, 3.8%), returned to the aggregator, not run here
> Planning input: check run on the recorded 2025 weather (planning = execution, not a forecast) · contract shaped100, seed 1
> Analysis script: the same check gives 0 missed on 2020–24 weather too

**P1: persistence + 2 K**, N=6 (N=8):
> **Missed deadlines: 0 of 31,471 accepted jobs** (0 of 36,272)
> Refused at intake: 2,193 jobs = 1,460 server-h, 4.9% of offered work (2,967 jobs = 2,162 server-h, 6.2%), returned to the aggregator, not run here
> Planning input: the house's own measurements from the last one to two days, repeated, + 2 K guard · contract shaped100, seed 1
> *(optional)* Cost of not having a forecast: +577 server-h refused (+846), −1.23 coverage points (−1.99) against the check run
> **Analysis script, same rule on 2020–24 weather: 0.32% of accepted jobs missed (0.43%); 2025 is the only year of six with 0**

**P1 + 3 K** (if the team switches): 0 of 31,417 (0 of 36,235). Refused 2,247 jobs = 1,484 server-h, 5.0% (3,004 = 2,192, 6.3%); +600 (+875) against the check run. Analysis line: 0.18% (0.28%) on 2020–24.

**O3: archived ECMWF + 2 K**, N=6 (N=8):
> **Missed deadlines: 0 of 31,908 accepted jobs** (0 of 36,771)
> Refused at intake: 1,739 jobs = 1,041 server-h, 3.5% of offered work (2,460 jobs = 1,500 server-h, 4.3%), returned to the aggregator, not run here
> Planning input: archived ECMWF weather forecast, only values issued before each decision, + 2 K guard · contract shaped100, seed 1
> *(optional)* Cost of forecast error: +158 server-h refused (+183), −0.33 coverage points (−0.37) against the check run
> **Analysis script: the 2 K guard also gives 0 on 2024 weather it was not tuned on (5 offer seeds)**

Notes for the slide and Q&A (all *computed*, section 4):

- **Season.** June–August refusals are the same for all three stages: 74 server-h at N=6 (0.8/day) and 64–68 at N=8 (0.7/day). The forecast changes nothing in summer.
  - The forecast cost sits in March, April, October and November. At N=6, P1 refuses 68 / 460 / 46 / 134 server-h in those months, against 0 / 236 / 4 / 0 for the check run.
  - Most of the check run's own refusals (April, May, September) come from the 2020–24 contract being larger than 2025's heat in those months. That is contract mismatch, not forecast.
- **Earlier figure.** `r6_buyer_scenarios.py` section 3 gives 1,031 / 1,483 refused server-h. That is a multi-seed mean; seed 1 of the O3 stage is 1,041 / 1,500.
- **What makes the tile discriminate** is line 2 (and line 4 if built). With line 1 alone, all three stages print 0. With line 2, they differ by 158–846 server-h a year.
  - Line 5 is the only line that says whether the 0 holds in another year.
  - It must stay labelled "analysis script", per the plan's rule that stress figures never replace the scheduler's own figure.
- **Build scope.**
  - Line 2: about 2–3 printer lines from existing counters (*assumption*). It belongs in K2.
  - Line 4: a second full-year run inside the printer plus 2 lines (*assumption*). **Flag: small scope addition, cut first.** If cut, quote the delta from this script with the "analysis script" label, or drop it.
  - Line 5: text only (copied from this file's command).

---

## (c) Q&A: "Your guard was tuned on the test year"

**If O3 (archived ECMWF) is the stage in place:**
> "Yes, the 2 K was first picked on 2025, so we re-ran it holding years out. With the archived ECMWF forecast, the same 2 K gives zero missed jobs on 2024 weather it never saw, at six and eight servers and five offer streams. And at six servers, 2025 alone would have suggested no guard, which misses 43 jobs in 2024. That one held-out year is all the archive allows, so we show the planning input and the refused work next to the zero, not just the zero."

**If P1 (persistence) is the stage in place:**
> "Yes, and it matters for persistence. On 2020 to 2024 weather the same rule misses about 0.3% of accepted jobs at six servers and 0.4% at eight, because a 6 to 9 degree warm jump across the case's 12 °C heating-day line wipes out a day's heat permits, and no guard size fixes that. Only a real forecast sees it coming, so our zero is a 2025 result, and the archived ECMWF forecast with the same 2 K guard holds on held-out 2024."

**If only the check run is in place:** "The check run uses the recorded weather by design, so it has no guard to tune. It proves only that planning and execution use the same rule, and it gives 0 in all six years. With persistence + 2 K, the rule misses 0.32% / 0.43% on 2020–24 (analysis script)."

---

## Proposed changes to `docs/overnight.md` (for the rewriter)

1. Open risk 4: replace "the 2 K guard was chosen and scored on the same 2025 weather" with the held-out result:
   - O3 + 2 K gives 0 on held-out 2024 (N=6 and N=8, 5 seeds).
   - P1 + 2 K misses on all five held-out years 2020–24: pooled 0.318% / 0.427%, seed 1 10–172 / 41–372 a year.
   - Cause: warm jumps across the 12 °C cliff.
2. Read-this-first line 4 and Q&A 5: the "persistence + 3 K: 0 in all 10 runs" sentence must say "on 2025 weather only". On 2020–24, P1 + 3 K misses 0.182% / 0.281%.
3. Tile 5:
   - Add line 2: "Refused at intake: X jobs = Y server-h (Z% of offered work), returned to the aggregator, not run here". Expected seed-1 values per stage are in section (b).
   - Add the labelled held-out analysis line for the stage reached.
   - Line 4 (delta against the check run) is optional and cut first (small build-scope addition).
4. Oracle table ("Team-scheduler expected values"): add refused jobs / server-h per stage. Check run 1,466 / 884 (N=6) and 2,199 / 1,316 (N=8); P1 2,193 / 1,460 and 2,967 / 2,162; O3 1,739 / 1,041 and 2,460 / 1,500.
5. Q&A 5: add the (c) answer for the stage reached.
6. 16:30 gate: no change to MUST. But state that O3 is now the only stage whose 0 holds on a held-out year. If O3 is cut, the P1 wording must carry the out-of-sample line.
7. Commit set (11:30 decision): add `analysis/r8_guard_heldout.py`, `analysis/r8_guard_probe.py` and `analysis/r8_data/prev_ecmwf_ifs025_2024.csv` (473,580 bytes) if the held-out claim is quoted.
8. "Still unverified": add that the O3 held-out evidence is one year (2024, archive from 3 Feb, fallback to persistence before 10 Feb for day 7). Also add that the truth for all six years is the same IFS model family as the forecast.

---

## Commands and reproducibility

| What | Command | Time |
|---|---|---|
| Main script, 940 yearly runs | `python3 analysis/r8_guard_heldout.py` (`--seeds 3` for fewer seeds, `--procs 1` for no multiprocessing) | 112 s on 12 cores |
| Full printout | saved as `docs/research/r8-guard-heldout-output.txt` | — |
| Probe | `python3 analysis/r8_guard_probe.py` | 17 s |
| Archive start check | the script prints "2024 previous_day7 first present at hour 961 (day 41 of the year)"; the first non-NaN day-0 value (2024-02-03T01:00) was read with an inline `python3 -I` count over the downloaded CSV during this session | — |

Limits:
- The weather is one model family throughout.
- The offer contract for each held-out year uses the other years' normal, which includes 2025 for 2020–24.
- Outages, overrun and restart are not included here; they are in `r5_miss_stress.py` / `r7_forecast_paths.py`.
- Persistence uses the case formula on model temperatures, not a measured house.
- For check and O3, targets past 31 December wrap to January, as in r5/r7; P1 does not wrap.

### Section 6 output (pooled rates)

```
  normal N=6 P1    g2 years 2020-2024: 2,408 of 757,399 = 0.318% | years with 0 in every seed: 0 of 5 | seed-1 misses by year [135, 57, 10, 172, 60]
  normal N=6 P1    g3 years 2020-2024: 1,373 of 755,961 = 0.182% | years with 0 in every seed: 0 of 5 | seed-1 misses by year [30, 57, 0, 172, 0]
  normal N=6 O3    g2 years 2024-2024: 0 of 152,405 = 0.000% | years with 0 in every seed: 1 of 1 | seed-1 misses by year [0]
  normal N=6 O3    g0 years 2024-2024: 43 of 153,600 = 0.028% | years with 0 in every seed: 0 of 1 | seed-1 misses by year [5]
  normal N=6 check g0 years 2020-2025: 0 of 926,500 = 0.000% | years with 0 in every seed: 6 of 6 | seed-1 misses by year [0, 0, 0, 0, 0, 0]
  normal N=8 P1    g2 years 2020-2024: 3,775 of 883,783 = 0.427% | years with 0 in every seed: 0 of 5 | seed-1 misses by year [199, 55, 41, 372, 122]
  normal N=8 P1    g3 years 2020-2024: 2,475 of 880,174 = 0.281% | years with 0 in every seed: 0 of 5 | seed-1 misses by year [88, 53, 19, 383, 14]
  normal N=8 O3    g2 years 2024-2024: 0 of 177,286 = 0.000% | years with 0 in every seed: 1 of 1 | seed-1 misses by year [0]
  normal N=8 O3    g0 years 2024-2024: 104 of 177,664 = 0.059% | years with 0 in every seed: 0 of 1 | seed-1 misses by year [2]
  normal N=8 check g0 years 2020-2025: 0 of 1,078,254 = 0.000% | years with 0 in every seed: 6 of 6 | seed-1 misses by year [0, 0, 0, 0, 0, 0]
  own    N=6 P1    g2 years 2020-2024: 2,649 of 784,044 = 0.338% | years with 0 in every seed: 0 of 5 | seed-1 misses by year [40, 176, 39, 221, 33]
  own    N=8 P1    g2 years 2020-2024: 3,628 of 913,116 = 0.397% | years with 0 in every seed: 0 of 5 | seed-1 misses by year [122, 161, 58, 278, 111]
  own    N=6 O3    g2 years 2024-2024: 0 of 154,627 = 0.000% | ...      own    N=8 O3    g2 years 2024-2024: 0 of 179,649 = 0.000% | ...
```

### Section 0 output (regression)

All 12 lines read `IDENTICAL` against `r7_forecast_paths.run`. Seed-1 offers equal the offer CSV at N=6 and N=8. See the full printout.
