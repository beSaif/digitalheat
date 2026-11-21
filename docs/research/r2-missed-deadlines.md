# Round 2 — missed deadlines on accepted jobs (must-have 3)

Investigator pass for weak point 2 of round 2. Assessment only: the script is exploratory and is **not** the team's scheduler. Nothing outside `analysis/` and `docs/research/` was touched; no git state changed. Firecrawl calls used: 0 of 3.

Status labels: *computed* = printed by the named script and command; *sourced* = number read on the URL given; *assumption* = our choice; *unverified* = not checked.

Currency: CHF throughout. No conversion is used in this file. Electricity 0.3325 CHF/kWh and heat value 0.1330 CHF/kWh are the case constants already in `analysis/baseline_sweep.py`.

## 1. Short answer

**Headline (all *computed*, `python3 analysis/r2_deadline_sim.py`, 5 seeds, stand-in reference house, case assumptions):**

| | N = 6 | N = 8 |
|---|---|---|
| Coverage / dumped / utilisation (saturating offers, unsold hours idle) | 79.2% / 0 kWh / 58.8% | 92.8% / 0 kWh / 51.7% |
| Accepted share of offered jobs (offers = N × 24 server-h/day, declared) | 55.9% (59.7% of offered work) | 49.6% (53.0% of offered work) |
| **Missed deadlines, % of accepted jobs — no partner site** | **0.15%** (seeds 0.10 to 0.27%) | **0.29%** (seeds 0.16 to 0.39%) |
| same, 7-day jobs only (J2) | 0.76% | 1.34% |
| same, % of accepted work | 0.39% | 0.70% |
| With a partner site, hand-off delay 1 h: moved / missed | 0.09% / 0.07% | 0.16% / 0.13% |
| Hand-off delay 4 h: moved / missed | 0.09% / 0.10% | 0.17% / 0.17% |
| Hand-off delay 0 h: moved / missed | 0.15% / 0.000% (zero by construction) | 0.30% / 0.000% (zero by construction) |
| Break-even per sold server-hour | 0.2261 CHF | 0.2261 CHF |

Conditions under which this holds:

1. **Admission control is on.** A job is accepted only if the forecast heat permits before its deadline can fit it on top of the work already accepted. About half of the saturating offers are *not accepted* and go elsewhere; they are not misses.
2. **The forecast is the real archived 1 to 7 day forecast for Basel 2025** (ECMWF IFS 0.25°, Open-Meteo Previous Runs API), not a made-up error. Its measured error against the reference-house temperature is 1.16 K RMSE one day ahead and 2.85 K seven days ahead (section 2). The reference weather is itself an IFS product, so this error is on the low side of what a house with a real thermometer would see.
3. **No safety margin, no guard band, never dump.** Dumped heat is 0 kWh in every row.
4. **Job types of round 1**: J1 0.5 server-h / 24 h deadline, J2 4 server-h / 168 h deadline, half of the offered work each (*assumption*). About 87% of accepted jobs are J1 (seed 1, N=8), so the per-job figure is dominated by J1. Most misses are J2 jobs in April, May and October.
5. **Not modelled:** server or network failure, restart overhead after a pause, uncertain job runtimes, a partner that needs more than the stated delay. These would add misses. The figure is a *forecast-error-only* missed-deadline rate.

How far the figure moves (all *computed*, saturating offers, no partner):

| Forecast seen by the admission rule | Day-1 RMSE | Missed, N = 6 | Missed, N = 8 |
|---|---|---|---|
| Perfect | 0 K | 0.000% | 0.000% |
| Real archive, Open-Meteo best match | 1.82 K (bias +1.10 K, warm = cautious) | 0.08% | 0.27% |
| **Real archive, ECMWF IFS 0.25°** | **1.16 K** | **0.15%** | **0.29%** |
| Synthetic, unbiased | 1 K | 0.40% | 0.67% |
| Synthetic, unbiased (closest to published station-level error, section 2) | 2 K | 1.02% | 1.06% |
| Synthetic, unbiased | 3 K | 1.61% | 1.74% |
| Synthetic 2 K with a −1 K bias (forecast too cold) | 2 K | 2.10% | 2.47% |
| Persistence (worst case: next 7 days = last 24 h) | 2.70 K | 1.35% | 3.10% |

With a seasonal (heat-shaped) contract instead of saturating offers the figure is 0.000% (N=6) and 0.016% (N=8); with a flat contract 0.002% and 0.006%. These contracts leave slack, so forecast errors are absorbed.

**The cause is the case's heating-day rule, not ordinary temperature noise.** Space heating switches on only if the day's mean is below 12 °C. A forecast just below 12 °C against an actual just above it promises about 80 kWh of permits that never come. In 2025 the 7-day-ahead forecast did that on 9 days (768 kWh), the 1-day-ahead forecast on 1 day (83 kWh). A percentage safety margin does not help reliably (N=6: 0.15% becomes 0.18 to 0.28% with 5 to 30% margin, inside seed noise; N=8: 0.29% falls to 0.10% only at a 30% margin). A **guard band** does: counting a future day as a heating day only if its forecast mean is below 10 °C cuts misses to 0.003% (N=6) and 0.010% (N=8) with no loss of coverage or sold hours.

**Recommended dashboard wording (must-have 3):**

> **Missed deadlines: X% of accepted jobs** (accepted jobs not finished by their deadline at any site ÷ accepted jobs whose deadline fell in the year). Next to it, always: **accepted Y% of offered jobs · moved to a partner site Z% · forecast used · hand-off delay**. Second line: by job type and as % of accepted work.

Never print the missed figure without the accepted share and the moved share. "0% missed" with instant hand-off is true by construction and says nothing.

## 2. Forecast error: what was sourced and what was measured

### Sources opened

| What | Value | Status | URL actually read |
|---|---|---|---|
| Open-Meteo Previous Runs API: meaning of `temperature_2m_previous_dayN` | "_previous_day1 returns the value predicted 24 hours before valid time"; fixed lead-time offsets of 1 to 7 days; most models archived from January 2024; the page itself proposes comparing the offsets with observations or reanalysis to measure skill | *sourced* | <https://open-meteo.com/en/docs/previous-runs-api> |
| Published 2 m temperature forecast error, hourly, more than 11,000 stations worldwide, 2017 | MAE 1.2 K at 24 h and 2.0 K at 6 days for the vendor's post-processed multi-model; raw models 1.7 to 2.2 K | *sourced* (vendor's own verification; worldwide, not central Europe) | <https://content.meteoblue.com/en/research-education/weather-data-accuracy/air-temperature/> |
| Same page, 24 h forecasts of 2018 against more than 8,000 WMO stations | raw global models MAE 2.0 K (ICON) to 2.4 K (GEM) | *sourced* | same URL |
| Same page, provider comparison 2021, 475 METAR stations | MAE 1.26 to 2.03 °C for 12 to 35 h, 1.43 to 2.29 °C for 48 to 71 h | *sourced* | same URL |
| A published day-ahead and 3 to 7 day RMSE specifically for central Europe from a national weather service | **not found.** ECMWF and MeteoSwiss material located by search gives charts or CRPS, no table values. The MeteoSwiss/ECMWF 2024 report was downloaded and searched with `pdftotext`; it has no 2 m temperature error numbers | not sourced | <https://www.ecmwf.int/sites/default/files/elibrary/092024/81589-application-and-verification-of-ecmwf-products-2024-switzerland.pdf> |

The pages were read through a fetch tool that summarises; the quoted figures should be re-read by eye before they go on a slide.

### Data downloaded (three small CSV files in `analysis/r2_data/`, 1.9 MB together; requests contain coordinates only)

```bash
V="temperature_2m,temperature_2m_previous_day1,temperature_2m_previous_day2,temperature_2m_previous_day3,temperature_2m_previous_day4,temperature_2m_previous_day5,temperature_2m_previous_day6,temperature_2m_previous_day7"
# real archived forecasts, ECMWF IFS 0.25 deg  -> prev_ecmwf_ifs025.csv
curl -o prev_ecmwf_ifs025.csv "https://previous-runs-api.open-meteo.com/v1/forecast?latitude=47.56&longitude=7.59&hourly=$V&start_date=2025-01-01&end_date=2025-12-31&timezone=Europe%2FZurich&format=csv&models=ecmwf_ifs025"
# real archived forecasts, default 'best match' model mix -> prev_runs_basel_2025.csv
curl -o prev_runs_basel_2025.csv "https://previous-runs-api.open-meteo.com/v1/forecast?latitude=47.56&longitude=7.59&hourly=$V&start_date=2025-01-01&end_date=2025-12-31&timezone=Europe%2FZurich&format=csv"
# 2020-2024 hourly temperature, same model as the reference house, for the contract's climate normal
curl -o archive_basel_2020_2024_ecmwf_ifs.csv "https://archive-api.open-meteo.com/v1/archive?latitude=47.56&longitude=7.59&start_date=2020-01-01&end_date=2024-12-31&hourly=temperature_2m&timezone=Europe%2FZurich&models=ecmwf_ifs&format=csv"
```

Downloaded 2026-11-21. Check done while downloading: the same Previous Runs request with `models=ecmwf_ifs` returns a `temperature_2m` column identical to the reference-house temperature for all 8,760 hours (bias 0.00, RMSE 0.00) but no previous-day values (all NaN), so the 9 km model has no archived lead-time series; the 0.25° version of the same model does. That file was deleted again.

### Measured error (forecast minus reference-house temperature, 8,760 hours of 2025) — *computed*

```text
== 0. Forecast error against the reference-house temperature (2025, 8,760 h, kelvin) ==
   forecast - actual; 'day K' = value issued K days before the valid hour
   ECMWF IFS 0.25 (ifs025)
     day 1: bias +0.29  MAE 0.87  RMSE 1.16  lag-1h autocorr 0.844
     day 2: bias +0.34  MAE 0.98  RMSE 1.30  lag-1h autocorr 0.866
     day 3: bias +0.33  MAE 1.09  RMSE 1.45  lag-1h autocorr 0.881
     day 4: bias +0.30  MAE 1.28  RMSE 1.67  lag-1h autocorr 0.903
     day 5: bias +0.33  MAE 1.54  RMSE 2.01  lag-1h autocorr 0.924
     day 6: bias +0.24  MAE 1.94  RMSE 2.52  lag-1h autocorr 0.949
     day 7: bias +0.19  MAE 2.19  RMSE 2.85  lag-1h autocorr 0.956
   Open-Meteo best match (bestmatch)
     day 1: bias +1.10  MAE 1.48  RMSE 1.82  lag-1h autocorr 0.857
     day 2: bias +0.28  MAE 1.10  RMSE 1.42  lag-1h autocorr 0.856
     day 3: bias +0.31  MAE 1.23  RMSE 1.59  lag-1h autocorr 0.871
     day 4: bias +0.30  MAE 1.45  RMSE 1.87  lag-1h autocorr 0.886
     day 5: bias +0.11  MAE 1.80  RMSE 2.33  lag-1h autocorr 0.919
     day 6: bias +0.15  MAE 2.07  RMSE 2.69  lag-1h autocorr 0.927
     day 7: bias +0.37  MAE 2.30  RMSE 3.04  lag-1h autocorr 0.918
   persistence (persist)
     day 1: bias +0.00  MAE 2.07  RMSE 2.70  lag-1h autocorr 0.949
     day 2: bias +0.00  MAE 2.78  RMSE 3.61  lag-1h autocorr 0.969
     day 3: bias -0.00  MAE 3.17  RMSE 4.06  lag-1h autocorr 0.975
     day 4: bias +0.00  MAE 3.52  RMSE 4.41  lag-1h autocorr 0.978
     day 5: bias +0.00  MAE 3.77  RMSE 4.75  lag-1h autocorr 0.980
     day 6: bias +0.00  MAE 3.93  RMSE 4.96  lag-1h autocorr 0.982
     day 7: bias -0.00  MAE 3.93  RMSE 4.97  lag-1h autocorr 0.982
   synthetic 2 K, seed 1 (syn2)
     day 1: bias +0.03  MAE 1.60  RMSE 2.00  lag-1h autocorr 0.850
     day 2: bias +0.01  MAE 1.81  RMSE 2.26  lag-1h autocorr 0.852
     day 3: bias +0.06  MAE 2.02  RMSE 2.53  lag-1h autocorr 0.852
     day 4: bias +0.14  MAE 2.29  RMSE 2.85  lag-1h autocorr 0.845
     day 5: bias +0.12  MAE 2.74  RMSE 3.43  lag-1h autocorr 0.846
     day 6: bias +0.18  MAE 3.47  RMSE 4.36  lag-1h autocorr 0.848
     day 7: bias +0.23  MAE 3.83  RMSE 4.85  lag-1h autocorr 0.842
   synthetic model uses rho = 0.844 and RMSE growth day1..7 = 1.00, 1.12, 1.25, 1.44, 1.73, 2.17, 2.45
   ifs025 day 1, Dec-Feb only: bias +0.51  RMSE 1.41
   ifs025 day 3, Dec-Feb only: bias +0.51  RMSE 1.70
   ifs025 day 7, Dec-Feb only: bias +0.17  RMSE 3.19
```

Reading:

- Our measured IFS error (MAE 0.87 K one day ahead, 2.19 K seven days ahead) is **below** the published station-level range (MAE 1.2 to 2.4 K at 24 h). Expected: the "truth" here is an IFS product, not a thermometer. The synthetic 2 K row (day-1 MAE 1.60 K, day-7 MAE 3.83 K) is the one that matches published station-level error at 24 h, and it is the prudent upper reading.
- Both real forecasts are biased warm (+0.1 to +1.1 K). A warm forecast promises fewer permits, so it is cautious. The −1 K "cold" synthetic row shows what the opposite sign costs.
- The simulation uses the day-1 value for every lead from 1 to 24 hours, the day-2 value for 25 to 48 hours and so on. A real system would have fresher short-range forecasts, so this is conservative for the hand-off decision.

### The heating-day cliff — *computed*

```text
== 0b. The heating-day cliff: days of 2025 whose forecast heating-day flag is wrong ==
   (case rule: space heating only if the day's mean temperature is below 12 degC)
   ifs025    day 1: forecast 'heating' but actually not:  1 days (   83 kWh of permits promised that never came); forecast 'no heating' but actually yes:  7 days; daily demand error RMSE 13.0 kWh/day
   ifs025    day 3: forecast 'heating' but actually not:  3 days (  237 kWh of permits promised that never came); forecast 'no heating' but actually yes: 11 days; daily demand error RMSE 16.9 kWh/day
   ifs025    day 5: forecast 'heating' but actually not:  4 days (  323 kWh of permits promised that never came); forecast 'no heating' but actually yes: 15 days; daily demand error RMSE 20.8 kWh/day
   ifs025    day 7: forecast 'heating' but actually not:  9 days (  768 kWh of permits promised that never came); forecast 'no heating' but actually yes: 18 days; daily demand error RMSE 27.7 kWh/day
   bestmatch day 1: forecast 'heating' but actually not:  1 days (   77 kWh of permits promised that never came); forecast 'no heating' but actually yes: 25 days; daily demand error RMSE 23.0 kWh/day
   bestmatch day 3: forecast 'heating' but actually not:  2 days (  156 kWh of permits promised that never came); forecast 'no heating' but actually yes: 17 days; daily demand error RMSE 19.2 kWh/day
   bestmatch day 5: forecast 'heating' but actually not:  5 days (  403 kWh of permits promised that never came); forecast 'no heating' but actually yes: 17 days; daily demand error RMSE 23.1 kWh/day
   bestmatch day 7: forecast 'heating' but actually not:  6 days (  560 kWh of permits promised that never came); forecast 'no heating' but actually yes: 12 days; daily demand error RMSE 24.2 kWh/day
   persist   day 1: forecast 'heating' but actually not: 13 days ( 1079 kWh of permits promised that never came); forecast 'no heating' but actually yes: 13 days; daily demand error RMSE 26.4 kWh/day
   persist   day 3: forecast 'heating' but actually not: 26 days ( 2333 kWh of permits promised that never came); forecast 'no heating' but actually yes: 26 days; daily demand error RMSE 41.5 kWh/day
   persist   day 5: forecast 'heating' but actually not: 29 days ( 2769 kWh of permits promised that never came); forecast 'no heating' but actually yes: 29 days; daily demand error RMSE 46.9 kWh/day
   persist   day 7: forecast 'heating' but actually not: 30 days ( 2826 kWh of permits promised that never came); forecast 'no heating' but actually yes: 30 days; daily demand error RMSE 48.1 kWh/day
```

## 3. What the script does

`analysis/r2_deadline_sim.py` (standard library; imports `load()`, the constants and `simulate` from `baseline_sweep.py` and the job types from `r1_job_sim.py`; neither file was edited). 680 simulated years in about 2 minutes 15 seconds on 12 cores.

| Element | Rule | Status |
|---|---|---|
| Heat permits | plain `follow` rule: each hour as many whole servers as demand + free tank space absorbs; never dumps | case constants |
| Admission | accept an offer only if (1 − margin) × forecast permits before each later deadline ≥ work already accepted up to that deadline + the new job; then an earliest-deadline-first dry run on the forecast with "one server per job"; the hour's acceptances are taken back until no accepted job is forecast to fail. Rejected = "not accepted", never "missed" | our rule |
| Forecast | admission and hand-off see the forecast issued ⌈lead ÷ 24 h⌉ days earlier; execution sees the actual 2025 weather | real data or labelled synthetic |
| Synthetic error | actual + AR(1) noise, hourly autocorrelation 0.844 and growth with lead (1.00 … 2.45) both measured from the IFS archive; forecast revisions between lead days independent; seeded | *assumption* in shape, measured in parameters |
| Execution | earliest deadline first, one server per job per hour; a job that can no longer finish is removed and counted missed | our rule |
| Hand-off | at a job's last safe moment (deadline − now − remaining runtime = delay) a dry run on the forecast decides: forecast says it fails → moved (finishes on time at the partner, counted "moved"); forecast says it fits → kept; if the weather then turns out warmer, it is too late to move → missed. "none" = no partner | our rule; partner capacity is an *assumption* (section 4.5 varies it) |
| Offers | Poisson, seeded. *saturating* = N × 24 server-h/day (the declared "unlimited" case); *flat* = 2020–24 mean follow capacity, flat (81.8 server-h/day at N=6, 95.9 at N=8); *shapedXX* = XX% of the 2020–24 mean capacity of each month | *assumption* (contract sizes we choose) |
| Sold share | realised: paid server-hours ÷ follow permit hours of 2025 (31,067 at N=6, 36,281 at N=8) | computed |
| Unsold permit hour | *idle*: server off, backup heater covers the heat; *filler*: server runs unpaid work, hour counts as run, not as sold | our two rules |
| Break-even | (electricity cost − value of heat actually used) ÷ server-hours **sold** | case formula |
| Missed % | missed ÷ (completed here + moved + missed); jobs still open on 31 December are left out | our definition |

Sanity checks (*computed*): with a perfect forecast there are 0 misses in every row of section 4.2, so every miss in the tables is caused by forecast error. Before the dry-run re-check was added, the perfect forecast still produced 166 misses at N=8 (seed 1, all 7-day jobs in transition months) because an aggregate capacity test ignores "one server per job"; a team that implements only the aggregate test will see that artefact. The demand rebuilt from the temperature column matches the reference CSV (assert in the script).

### Contract sizes: 2020–24 climate normal against 2025 — *computed*

```text
== 1. Heat-permit capacity by month, follow rule, server-h/day ==
   N=6   follow permit hours 2025 = 31067
     month           1      2      3      4      5      6      7      8      9     10     11     12   year
     2020-24 avg 143.9  141.8  133.2   99.4   44.6   15.0   15.0   15.0   30.6   66.8  138.0  142.4   81.8
     min of 5 yr 143.7  133.3  123.7   49.0   21.4   15.0   15.0   15.0   15.0   24.5  132.2  137.1
     max of 5 yr 144.0  144.0  137.5  125.7   91.3   15.0   15.0   15.0   43.4  108.6  143.7  144.0
     2025 actual 144.0  144.0  138.1   92.5   42.9   15.0   15.0   15.0   39.2  101.7  133.8  143.9   85.1
   N=8   follow permit hours 2025 = 36281
     month           1      2      3      4      5      6      7      8      9     10     11     12   year
     2020-24 avg 185.3  171.5  155.2  111.0   44.7   15.0   15.0   15.0   30.6   68.0  163.0  181.7   95.9
     min of 5 yr 177.3  158.9  141.3   52.8   21.4   15.0   15.0   15.0   15.0   24.4  152.7  169.5
     max of 5 yr 189.4  183.2  168.2  145.7   91.7   15.0   15.0   15.0   43.5  110.9  184.2  191.8
     2025 actual 185.8  184.3  162.1   92.4   42.9   15.0   15.0   15.0   39.2  101.7  160.5  184.2   99.4
```

The shoulder months vary most between years (April at N=8: 52.8 to 145.7 server-h/day; October: 24.4 to 110.9). October 2025 was far colder than the five-year mean (101.7 against 68.0), April milder (92.4 against 111.0). A monthly contract sized on a normal therefore under-sells cold shoulder months and over-offers mild ones; with arrival randomness this is why "shaped100" reaches only 93% sold share and rejects about 5% of offers.

## 4. Results

Column key: `cover` = share of total heat demand covered; `dump` = kWh dumped; `util` = server running hours ÷ (N × 8,760); `sold h` = paid server-hours hosted; `sold%` = sold h ÷ follow permit hours; `acc%job` / `acc%wrk` = accepted share of offered jobs / work; `done%`, `moved%`, `MISSED%` = share of accepted (closed) jobs, mean of 5 seeds with the lowest and highest seed; `BE/sold h` = break-even in CHF per sold server-hour; `mJ1%`, `mJ2%` = missed share within each job type; `mWork%` = missed work ÷ accepted work.

### 4.1 Main table: three demand scenarios × four hand-off settings

```text
== 2. Main: real archived forecast (ifs025), no safety margin, unsold hours idle ==
 N demand     forecast  marg hand unsold  cover  dump   util  sold h  sold% acc%job acc%wrk  done% moved%   MISSED% mean [min-max] BE/sold h   mJ1%   mJ2% mWork%
 6 saturating ifs025      0% none idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.9%  0.00%    0.146 [0.097-0.267]    0.2261  0.058  0.762  0.393
 6 saturating ifs025      0%   0h idle    79.2%     0  58.8%   30931  99.6%   55.9%   59.7%  99.8%  0.15%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.070 [0.024-0.155]    0.2261  0.076  0.029  0.049
 6 saturating ifs025      0%   4h idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.100 [0.033-0.191]    0.2261  0.097  0.125  0.110

 6 flat       ifs025      0% none idle    54.0%     0  40.1%   21081  67.9%   64.4%   70.3% 100.0%  0.00%    0.002 [0.000-0.009]    0.2261  0.000  0.014  0.006
 6 flat       ifs025      0%   0h idle    54.0%     0  40.1%   21081  67.9%   64.4%   70.3% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 flat       ifs025      0%   1h idle    54.0%     0  40.1%   21081  67.9%   64.4%   70.3% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 flat       ifs025      0%   4h idle    54.0%     0  40.1%   21081  67.9%   64.4%   70.3% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000

 6 shaped100  ifs025      0% none idle    74.1%     0  55.1%   28947  93.2%   95.2%   97.0% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 shaped100  ifs025      0%   0h idle    74.1%     0  55.1%   28947  93.2%   95.2%   97.0% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 shaped100  ifs025      0%   1h idle    74.1%     0  55.1%   28947  93.2%   95.2%   97.0% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 shaped100  ifs025      0%   4h idle    74.1%     0  55.1%   28947  93.2%   95.2%   97.0% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000

 8 saturating ifs025      0% none idle    92.8%     0  51.7%   36222  99.8%   49.6%   53.0%  99.7%  0.00%    0.294 [0.160-0.386]    0.2261  0.144  1.337  0.697
 8 saturating ifs025      0%   0h idle    92.8%     0  51.7%   36222  99.8%   49.6%   53.0%  99.7%  0.30%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.7%   53.1%  99.7%  0.16%    0.126 [0.008-0.233]    0.2261  0.122  0.147  0.130
 8 saturating ifs025      0%   4h idle    92.8%     0  51.7%   36222  99.8%   49.6%   53.1%  99.7%  0.17%    0.174 [0.056-0.306]    0.2261  0.166  0.234  0.187

 8 flat       ifs025      0% none idle    61.1%     0  34.0%   23848  65.7%   63.0%   68.3% 100.0%  0.00%    0.006 [0.000-0.012]    0.2261  0.001  0.043  0.018
 8 flat       ifs025      0%   0h idle    61.1%     0  34.0%   23847  65.7%   63.0%   68.3% 100.0%  0.01%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 flat       ifs025      0%   1h idle    61.1%     0  34.0%   23847  65.7%   63.0%   68.3% 100.0%  0.00%    0.002 [0.000-0.008]    0.2261  0.001  0.006  0.004
 8 flat       ifs025      0%   4h idle    61.1%     0  34.0%   23847  65.7%   63.0%   68.3% 100.0%  0.00%    0.002 [0.000-0.008]    0.2261  0.001  0.006  0.004

 8 shaped100  ifs025      0% none idle    86.1%     0  48.0%   33627  92.7%   94.5%   95.9% 100.0%  0.00%    0.016 [0.005-0.030]    0.2261  0.000  0.135  0.058
 8 shaped100  ifs025      0%   0h idle    86.1%     0  48.0%   33621  92.7%   94.5%   95.9% 100.0%  0.01%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 shaped100  ifs025      0%   1h idle    86.2%     0  48.0%   33642  92.7%   94.5%   95.9% 100.0%  0.01%    0.001 [0.000-0.005]    0.2261  0.000  0.009  0.004
 8 shaped100  ifs025      0%   4h idle    86.2%     0  48.0%   33645  92.7%   94.5%   96.0% 100.0%  0.01%    0.002 [0.000-0.011]    0.2261  0.000  0.018  0.009
```

- Saturating offers: coverage 79.2% / 92.8% against 79.6% / 92.9% with every permit sold. A few permits stay unused (99.6% / 99.8% sold).
- Flat contract: about 30% of the offered work is rejected (summer has no permits), coverage falls to 54.0% / 61.1%, misses practically vanish. This is round 1's finding restated with admission: the flat contract costs coverage, not deadlines.
- Heat-shaped contract at 100% of the normal: 74.1% / 86.1% coverage, 95% of offers accepted, misses 0.000% / 0.016%.
- Hand-off with a delay roughly halves the misses on average but not in every seed (seed 1, N=6, 4 h delay: 46 misses in one October event against 34 without a partner). With 0 h delay everything that would miss is moved, so "missed" is 0 by construction.

### 4.2 Forecast-error sensitivity (saturating offers)

```text
== 3. Forecast-error sensitivity, saturating offers, no margin ==
 N demand     forecast  marg hand unsold  cover  dump   util  sold h  sold% acc%job acc%wrk  done% moved%   MISSED% mean [min-max] BE/sold h   mJ1%   mJ2% mWork%
 6 saturating perfect     0% none idle    79.2%     0  58.8%   30930  99.6%   52.7%   59.6% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 saturating perfect     0%   1h idle    79.2%     0  58.8%   30930  99.6%   52.7%   59.6% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 saturating perfect     0%   4h idle    79.2%     0  58.8%   30930  99.6%   52.7%   59.6% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 saturating ifs025      0% none idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.9%  0.00%    0.146 [0.097-0.267]    0.2261  0.058  0.762  0.393
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.070 [0.024-0.155]    0.2261  0.076  0.029  0.049
 6 saturating ifs025      0%   4h idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.100 [0.033-0.191]    0.2261  0.097  0.125  0.110
 6 saturating bestmatch   0% none idle    79.2%     0  58.8%   30930  99.6%   55.4%   59.5%  99.9%  0.00%    0.075 [0.034-0.171]    0.2261  0.036  0.340  0.174
 6 saturating bestmatch   0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.5%   59.6%  99.9%  0.05%    0.028 [0.000-0.141]    0.2261  0.032  0.000  0.015
 6 saturating bestmatch   0%   4h idle    79.2%     0  58.8%   30930  99.6%   55.5%   59.6%  99.9%  0.06%    0.040 [0.000-0.198]    0.2261  0.046  0.000  0.021
 6 saturating syn1        0% none idle    79.2%     0  58.8%   30930  99.6%   56.3%   60.1%  99.6%  0.00%    0.403 [0.201-0.615]    0.2261  0.206  1.769  0.926
 6 saturating syn1        0%   1h idle    79.2%     0  58.8%   30930  99.6%   56.1%   60.1%  99.6%  0.23%    0.193 [0.061-0.275]    0.2261  0.140  0.556  0.327
 6 saturating syn1        0%   4h idle    79.2%     0  58.8%   30930  99.6%   56.3%   60.1%  99.5%  0.21%    0.311 [0.076-0.496]    0.2261  0.259  0.674  0.440
 6 saturating syn2        0% none idle    79.2%     0  58.8%   30930  99.6%   57.3%   60.9%  99.0%  0.00%    1.022 [0.488-1.320]    0.2261  0.542  4.398  2.315
 6 saturating syn2        0%   1h idle    79.2%     0  58.8%   30930  99.6%   57.3%   60.9%  99.1%  0.53%    0.415 [0.099-0.618]    0.2261  0.403  0.492  0.429
 6 saturating syn2        0%   4h idle    79.2%     0  58.8%   30930  99.6%   57.3%   60.9%  99.0%  0.48%    0.484 [0.102-0.683]    0.2261  0.450  0.720  0.558
 6 saturating syn3        0% none idle    79.2%     0  58.8%   30930  99.6%   58.4%   61.9%  98.4%  0.00%    1.609 [0.850-1.922]    0.2261  0.753  7.651  3.901
 6 saturating syn3        0%   1h idle    79.2%     0  58.8%   30930  99.6%   58.4%   61.9%  98.4%  0.95%    0.610 [0.227-0.938]    0.2261  0.605  0.646  0.571
 6 saturating syn3        0%   4h idle    79.2%     0  58.8%   30930  99.6%   58.3%   62.0%  98.4%  0.88%    0.722 [0.377-1.042]    0.2261  0.657  1.180  0.868
 6 saturating syn2cold    0% none idle    79.2%     0  58.8%   30930  99.6%   58.8%   62.2%  97.9%  0.00%    2.100 [1.320-2.661]    0.2261  1.261  8.061  4.306
 6 saturating syn2cold    0%   1h idle    79.2%     0  58.8%   30930  99.6%   58.8%   62.2%  98.0%  1.01%    1.011 [0.723-1.221]    0.2261  0.991  1.160  0.976
 6 saturating syn2cold    0%   4h idle    79.2%     0  58.8%   30930  99.6%   58.8%   62.3%  97.9%  0.89%    1.229 [0.815-1.594]    0.2261  1.158  1.739  1.352
 6 saturating persist     0% none idle    79.2%     0  58.8%   30930  99.6%   58.2%   61.0%  98.7%  0.00%    1.346 [1.238-1.526]    0.2261  0.835  5.038  2.706
 6 saturating persist     0%   1h idle    79.2%     0  58.8%   30930  99.6%   58.3%   61.0%  98.7%  1.20%    0.112 [0.000-0.238]    0.2261  0.124  0.024  0.070
 6 saturating persist     0%   4h idle    79.2%     0  58.8%   30930  99.6%   58.3%   61.1%  98.7%  1.22%    0.126 [0.000-0.270]    0.2261  0.139  0.034  0.083
 8 saturating perfect     0% none idle    92.8%     0  51.7%   36222  99.8%   45.3%   52.7% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 saturating perfect     0%   1h idle    92.8%     0  51.7%   36222  99.8%   45.3%   52.7% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 saturating perfect     0%   4h idle    92.8%     0  51.7%   36222  99.8%   45.3%   52.7% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 saturating ifs025      0% none idle    92.8%     0  51.7%   36222  99.8%   49.6%   53.0%  99.7%  0.00%    0.294 [0.160-0.386]    0.2261  0.144  1.337  0.697
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.7%   53.1%  99.7%  0.16%    0.126 [0.008-0.233]    0.2261  0.122  0.147  0.130
 8 saturating ifs025      0%   4h idle    92.8%     0  51.7%   36222  99.8%   49.6%   53.1%  99.7%  0.17%    0.174 [0.056-0.306]    0.2261  0.166  0.234  0.187
 8 saturating bestmatch   0% none idle    92.8%     0  51.7%   36222  99.8%   49.3%   52.9%  99.7%  0.00%    0.266 [0.028-0.346]    0.2261  0.239  0.452  0.322
 8 saturating bestmatch   0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.4%   52.9%  99.7%  0.12%    0.143 [0.000-0.209]    0.2261  0.164  0.000  0.075
 8 saturating bestmatch   0%   4h idle    92.8%     0  51.7%   36222  99.8%   49.3%   53.0%  99.8%  0.12%    0.130 [0.000-0.219]    0.2261  0.147  0.012  0.073
 8 saturating syn1        0% none idle    92.8%     0  51.7%   36222  99.8%   49.9%   53.5%  99.3%  0.00%    0.665 [0.276-1.074]    0.2261  0.367  2.737  1.461
 8 saturating syn1        0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.9%   53.5%  99.4%  0.31%    0.268 [0.015-0.585]    0.2261  0.249  0.398  0.294
 8 saturating syn1        0%   4h idle    92.8%     0  51.7%   36222  99.8%   49.9%   53.5%  99.3%  0.30%    0.372 [0.023-0.617]    0.2261  0.340  0.594  0.435
 8 saturating syn2        0% none idle    92.8%     0  51.7%   36222  99.8%   51.0%   54.2%  98.9%  0.00%    1.057 [0.645-1.381]    0.2261  0.421  5.585  2.851
 8 saturating syn2        0%   1h idle    92.8%     0  51.7%   36222  99.8%   51.0%   54.2%  99.0%  0.59%    0.361 [0.108-0.680]    0.2261  0.280  0.931  0.563
 8 saturating syn2        0%   4h idle    92.8%     0  51.7%   36222  99.8%   51.1%   54.3%  99.0%  0.57%    0.438 [0.156-0.776]    0.2261  0.330  1.196  0.720
 8 saturating syn3        0% none idle    92.8%     0  51.7%   36222  99.8%   52.1%   55.2%  98.3%  0.00%    1.736 [1.233-2.013]    0.2261  0.676  9.289  4.679
 8 saturating syn3        0%   1h idle    92.8%     0  51.7%   36222  99.8%   52.1%   55.3%  98.4%  1.04%    0.564 [0.266-0.817]    0.2261  0.411  1.646  0.948
 8 saturating syn3        0%   4h idle    92.8%     0  51.7%   36222  99.8%   52.2%   55.4%  98.2%  1.03%    0.752 [0.401-0.975]    0.2261  0.601  1.820  1.129
 8 saturating syn2cold    0% none idle    92.8%     0  51.7%   36222  99.8%   52.7%   55.8%  97.5%  0.00%    2.474 [1.773-3.240]    0.2261  1.356 10.466  5.580
 8 saturating syn2cold    0%   1h idle    92.8%     0  51.7%   36222  99.8%   52.8%   55.8%  97.7%  1.11%    1.211 [0.655-1.673]    0.2261  1.029  2.502  1.631
 8 saturating syn2cold    0%   4h idle    92.8%     0  51.7%   36222  99.8%   52.8%   55.9%  97.6%  1.06%    1.324 [0.806-1.857]    0.2261  1.123  2.747  1.822
 8 saturating persist     0% none idle    92.8%     0  51.7%   36222  99.8%   53.8%   56.1%  96.9%  0.00%    3.104 [2.909-3.415]    0.2261  2.035 11.061  6.078
 8 saturating persist     0%   1h idle    92.8%     0  51.7%   36222  99.8%   53.9%   56.2%  96.9%  1.86%    1.220 [1.088-1.469]    0.2261  1.224  1.190  1.112
 8 saturating persist     0%   4h idle    92.8%     0  51.7%   36222  99.8%   54.1%   56.4%  96.8%  1.70%    1.525 [1.447-1.669]    0.2261  1.519  1.568  1.443
```

### 4.3 Guard band on the heating-day threshold

```text
== 4b. Guard band on the heating-day threshold in the forecast, saturating, no margin ==
 N demand     forecast  marg hand unsold  cover  dump   util  sold h  sold% acc%job acc%wrk  done% moved%   MISSED% mean [min-max] BE/sold h   mJ1%   mJ2% mWork%
 6 saturating ifs025      0% none idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.9%  0.00%    0.146 [0.097-0.267]    0.2261  0.058  0.762  0.393
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.070 [0.024-0.155]    0.2261  0.076  0.029  0.049
 6 saturating ifs025g1    0% none idle    79.2%     0  58.8%   30930  99.6%   54.9%   59.5% 100.0%  0.00%    0.018 [0.009-0.028]    0.2261  0.000  0.138  0.062
 6 saturating ifs025g1    0%   1h idle    79.2%     0  58.8%   30930  99.6%   54.9%   59.5% 100.0%  0.02%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 saturating ifs025g2    0% none idle    79.2%     0  58.8%   30930  99.6%   55.3%   59.4% 100.0%  0.00%    0.003 [0.000-0.009]    0.2261  0.000  0.024  0.012
 6 saturating ifs025g2    0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.3%   59.4% 100.0%  0.00%    0.001 [0.000-0.003]    0.2261  0.000  0.005  0.002
 6 saturating ifs025g3    0% none idle    79.2%     0  58.8%   30930  99.6%   55.6%   59.3% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 saturating ifs025g3    0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.6%   59.3% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000

 8 saturating ifs025      0% none idle    92.8%     0  51.7%   36222  99.8%   49.6%   53.0%  99.7%  0.00%    0.294 [0.160-0.386]    0.2261  0.144  1.337  0.697
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.7%   53.1%  99.7%  0.16%    0.126 [0.008-0.233]    0.2261  0.122  0.147  0.130
 8 saturating ifs025g1    0% none idle    92.8%     0  51.7%   36222  99.8%   48.8%   52.8%  99.9%  0.00%    0.051 [0.042-0.068]    0.2261  0.004  0.375  0.188
 8 saturating ifs025g1    0%   1h idle    92.8%     0  51.7%   36222  99.8%   48.8%   52.8%  99.9%  0.05%    0.002 [0.000-0.005]    0.2261  0.000  0.012  0.006
 8 saturating ifs025g2    0% none idle    92.8%     0  51.7%   36222  99.8%   49.4%   52.7% 100.0%  0.00%    0.010 [0.005-0.015]    0.2261  0.001  0.075  0.039
 8 saturating ifs025g2    0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.4%   52.7% 100.0%  0.01%    0.002 [0.000-0.005]    0.2261  0.000  0.012  0.007
 8 saturating ifs025g3    0% none idle    92.8%     0  51.7%   36222  99.8%   50.2%   52.7% 100.0%  0.00%    0.008 [0.005-0.013]    0.2261  0.001  0.063  0.033
 8 saturating ifs025g3    0%   1h idle    92.8%     0  51.7%   36222  99.8%   50.1%   52.7% 100.0%  0.01%    0.002 [0.000-0.003]    0.2261  0.000  0.013  0.006
```

`ifs025gX` = a future day counts as a heating day only if its forecast mean is below (12 − X) °C. The percentage-margin sweep (section 4 of the raw output) and "bad forecast plus margin" (section 7) are in [r2-missed-deadlines-output.txt](r2-missed-deadlines-output.txt). Margins of 5 to 30% do not reduce misses reliably; sold hours do not fall with the margin either (99.6% / 99.8% in every row), which suggests the held-back capacity is sold later to short jobs (interpretation, not tested separately).

### 4.4 Sold share and what an unsold permit hour does

```text
== 5. Sold share and the unsold-hour rule, ifs025, hand-off 1 h, no margin ==
 N demand     forecast  marg hand unsold  cover  dump   util  sold h  sold% acc%job acc%wrk  done% moved%   MISSED% mean [min-max] BE/sold h   mJ1%   mJ2% mWork%
 6 shaped100  ifs025      0%   1h idle    74.1%     0  55.1%   28947  93.2%   95.2%   97.0% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 shaped100  ifs025      0%   1h filler  79.6%     0  59.1%   28685  92.3%   94.2%   96.3% 100.0%  0.00%    0.000 [0.000-0.000]    0.2449  0.000  0.000  0.000
 6 shaped70   ifs025      0%   1h idle    53.2%     0  39.5%   20782  66.9%   98.6%   99.2% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 shaped70   ifs025      0%   1h filler  79.6%     0  59.1%   20584  66.3%   97.0%   98.2% 100.0%  0.00%    0.000 [0.000-0.000]    0.3413  0.000  0.000  0.000
 6 shaped40   ifs025      0%   1h idle    30.7%     0  22.8%   11969  38.5%  100.0%  100.0% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 6 shaped40   ifs025      0%   1h filler  79.6%     0  59.1%   11947  38.5%   99.7%   99.8% 100.0%  0.00%    0.000 [0.000-0.000]    0.5880  0.000  0.000  0.000
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.070 [0.024-0.155]    0.2261  0.076  0.029  0.049
 6 saturating ifs025      0%   1h filler  79.6%     0  59.1%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.070 [0.024-0.155]    0.2271  0.076  0.029  0.049
 8 shaped100  ifs025      0%   1h idle    86.2%     0  48.0%   33642  92.7%   94.5%   95.9% 100.0%  0.01%    0.001 [0.000-0.005]    0.2261  0.000  0.009  0.004
 8 shaped100  ifs025      0%   1h filler  92.9%     0  51.8%   33394  92.0%   93.7%   95.4% 100.0%  0.02%    0.000 [0.000-0.000]    0.2457  0.000  0.000  0.000
 8 shaped70   ifs025      0%   1h idle    62.2%     0  34.6%   24272  66.9%   98.4%   99.1% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 shaped70   ifs025      0%   1h filler  92.9%     0  51.8%   24081  66.4%   97.1%   98.3% 100.0%  0.00%    0.000 [0.000-0.000]    0.3407  0.000  0.000  0.000
 8 shaped40   ifs025      0%   1h idle    35.7%     0  19.9%   13932  38.4%   99.9%   99.9% 100.0%  0.00%    0.000 [0.000-0.000]    0.2261  0.000  0.000  0.000
 8 shaped40   ifs025      0%   1h filler  92.9%     0  51.8%   13908  38.3%   99.6%   99.8% 100.0%  0.00%    0.000 [0.000-0.000]    0.5898  0.000  0.000  0.000
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.7%   53.1%  99.7%  0.16%    0.126 [0.008-0.233]    0.2261  0.122  0.147  0.130
 8 saturating ifs025      0%   1h filler  92.9%     0  51.8%   36215  99.8%   49.7%   53.0%  99.7%  0.16%    0.126 [0.008-0.233]    0.2265  0.122  0.147  0.130
```

| Sold share (realised) | Unsold hour | Coverage N=6 / N=8 | Utilisation N=6 / N=8 | Break-even CHF per sold server-hour N=6 / N=8 |
|---|---|---|---|---|
| 99.6% / 99.8% (saturating) | idle | 79.2% / 92.8% | 58.8% / 51.7% | 0.2261 / 0.2261 |
| 93% (shaped100) | idle | 74.1% / 86.2% | 55.1% / 48.0% | 0.2261 / 0.2261 |
| 92% (shaped100) | filler | 79.6% / 92.9% | 59.1% / 51.8% | 0.2449 / 0.2457 |
| 67% (shaped70) | idle | 53.2% / 62.2% | 39.5% / 34.6% | 0.2261 / 0.2261 |
| 66% (shaped70) | filler | 79.6% / 92.9% | 59.1% / 51.8% | 0.3413 / 0.3407 |
| 38% (shaped40) | idle | 30.7% / 35.7% | 22.8% / 19.9% | 0.2261 / 0.2261 |
| 38% (shaped40) | filler | 79.6% / 92.9% | 59.1% / 51.8% | 0.5880 / 0.5898 |

- **Idle rule:** every running hour is sold and its heat is used, so the break-even stays at 0.2261 CHF. Coverage and utilisation fall in proportion to the sold share. The backup heater (outside the model) covers the rest.
- **Filler rule:** coverage and utilisation stay at the follow values, and the break-even becomes 0.2261 ÷ sold share (0.2261 ÷ 0.385 = 0.587). Each unpaid filler hour costs 0.3325 CHF of electricity and returns 0.1064 CHF of heat value (0.8 kWh × 0.1330), a net loss of 0.2261 CHF under the case formula. The filler rule buys coverage points with money; it is a server used as a resistance heater.
- The dashboard must state which rule is on. Coverage "92.9%" at a 38% sold share is only true with filler at 0.59 CHF per sold hour.

### 4.5 Partner site that is sometimes full (hand-off delay 1 h)

```text
== 6. Partner site refuses a share of hand-offs, saturating, ifs025, hand-off 1 h ==
 N demand     forecast  marg hand unsold  cover  dump   util  sold h  sold% acc%job acc%wrk  done% moved%   MISSED% mean [min-max] BE/sold h   mJ1%   mJ2% mWork%
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   55.9%   59.7%  99.8%  0.09%    0.070 [0.024-0.155]    0.2261  0.076  0.029  0.049
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   56.0%   59.7%  99.8%  0.08%    0.125 [0.028-0.318]    0.2261  0.116  0.183  0.136   partner refuses 20%
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   56.0%   59.7%  99.8%  0.05%    0.165 [0.052-0.343]    0.2261  0.132  0.395  0.250   partner refuses 50%
 6 saturating ifs025      0%   1h idle    79.2%     0  58.8%   30930  99.6%   56.0%   59.7%  99.8%  0.00%    0.222 [0.088-0.394]    0.2261  0.139  0.797  0.447   partner refuses 100%
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.7%   53.1%  99.7%  0.16%    0.126 [0.008-0.233]    0.2261  0.122  0.147  0.130
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.5%   53.1%  99.6%  0.15%    0.220 [0.085-0.340]    0.2261  0.193  0.413  0.280   partner refuses 20%
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.5%   53.1%  99.6%  0.10%    0.263 [0.146-0.345]    0.2261  0.183  0.823  0.472   partner refuses 50%
 8 saturating ifs025      0%   1h idle    92.8%     0  51.7%   36222  99.8%   49.6%   53.0%  99.7%  0.00%    0.314 [0.203-0.474]    0.2261  0.155  1.421  0.746   partner refuses 100%
```

### 4.6 Where and when the misses happen (seed 1)

```text
== 8. Detail: saturating offers, ifs025, no margin, seed 1 ==
   N=6 hand-off none: accepted 32823, completed here 32732, moved 0, missed 34; missed J1 0.014% / J2 0.719% of accepted jobs of that type; missed work 0.338% of accepted work
     month        1      2      3      4      5      6      7      8      9     10     11     12
     acc       4993   4428   5029   2849   1223    120    116    116    993   3456   4456   5044
     done      4979   4433   4971   2894   1174    144    116    116    866   3487   4478   5074
     moved        0      0      0      0      0      0      0      0      0      0      0      0
     missed       0      0      0      9     12      0      0      0      1     12      0      0
   N=6 hand-off 4 h: accepted 32742, completed here 32611, moved 31, missed 46; missed J1 0.147% / J2 0.095% of accepted jobs of that type; missed work 0.118% of accepted work
     month        1      2      3      4      5      6      7      8      9     10     11     12
     acc       4993   4428   5029   2839   1175    116    116    117    967   3488   4430   5044
     done      4979   4433   4971   2884   1125    142    116    116    847   3474   4450   5074
     moved        0      0      0      7     13      0      0      0      0     11      0      0
     missed       0      0      0      0      0      0      0      0      0     46      0      0
   N=8 hand-off none: accepted 39051, completed here 38792, moved 0, missed 109; missed J1 0.012% / J2 2.145% of accepted jobs of that type; missed work 1.030% of accepted work
     month        1      2      3      4      5      6      7      8      9     10     11     12
     acc       6647   6008   5848   2716   1252    113    116    116    937   3207   5392   6699
     done      6608   5946   5805   2790   1197    138    117    116    728   3342   5375   6630
     moved        0      0      0      0      0      0      0      0      0      0      0      0
     missed       0      0      4     51     18      0      0      0      2     32      2      0
   N=8 hand-off 4 h: accepted 38993, completed here 38723, moved 81, missed 48; missed J1 0.091% / J2 0.347% of accepted jobs of that type; missed work 0.196% of accepted work
     month        1      2      3      4      5      6      7      8      9     10     11     12
     acc       6647   6008   5831   2726   1232    112    116    117   1013   3161   5331   6699
     done      6608   5946   5785   2801   1191    126    116    117    808   3269   5326   6630
     moved        0      0      5     57     10      0      0      0      2      6      1      0
     missed       0      0      0      1      0      0      0      0      3     43      1      0
```

Misses sit in March to May and September to November; none in January, February or June to August in these four runs.

### 4.7 Consistency check against the round-1 baseline

```text
== 9. Check: follow rule with every permit sold (baseline_sweep.simulate) ==
   N=6: coverage 79.6%, dumped 0 kWh, utilisation 59.1%, 31067 server-h, break-even 0.2261 CHF/server-h
   N=8: coverage 92.9%, dumped 0 kWh, utilisation 51.8%, 36281 server-h, break-even 0.2261 CHF/server-h
```

## 5. Limits (what a critic should attack)

1. **Truth and forecast come from the same model family.** The measured 1.16 K day-1 RMSE understates the error against a real house. The synthetic 2 K row is the prudent reading: about 1.0 to 1.1% missed without a partner, 0.4% with a 1 h hand-off.
2. **One weather year, five arrival seeds.** The seed spread (for example 0.16 to 0.39% at N=8) is arrival randomness only; the forecast errors of 2025 are one realisation. Another year can have more or fewer threshold days.
3. **Misses come from very few events** (seed 1, N=8: 109 missed jobs, 51 of them in April). Small-number statistics; quote one decimal at most.
4. **The per-job percentage hides the job type.** About 87% of accepted jobs are 0.5 h jobs with a 24 h deadline. Per 7-day job the figure is 0.8% / 1.3%, with persistence 5% / 11%.
5. **Forecast-error only.** No hardware or network failure, no restart cost, exact runtimes, checkpointing free. Real missed deadlines will be higher.
6. **The partner site is unnamed and assumed to have room.** Section 4.5 shows the figure returning to the no-partner level as the partner refuses more.
7. **Synthetic error model**: independent revisions between lead days and a single autocorrelation are *assumptions*. The real 1.16 K forecast gives 0.15 to 0.29%, the synthetic 1 K one 0.40 to 0.67%; the warm bias of the real forecast is one likely reason (not isolated).
8. **Admission order and mix are ours**: random order between the two types each hour; 50/50 work mix. Not tested with other mixes.
9. **The heating-day rule is a case simplification.** A real house has no 12 °C cliff, so real permit errors would be smoother. On the case's reference house the cliff is real and the scheduler must handle it.
10. **Year boundary:** forecasts beyond 31 December wrap to January 2025; jobs open at year end are left out of the percentages.
11. Stand-in reference profile, as in every other file. The plain follow rule is used; the hysteresis band from round 1 is not.

## 6. Recommendations for the plan

1. Report **missed deadlines in % of accepted jobs** with the definition in section 1, always together with accepted share, moved share, forecast source and hand-off delay; add the per-type line.
2. Quote the headline as "about 0.2 to 0.3% of accepted jobs (forecast error only, real archived forecasts, no partner site); about 1% with station-level forecast error; 1 to 3% with a persistence forecast". Do not quote 0%.
3. Put a **guard band on the heating-day threshold** into the admission rule (parameter; 2 K tested) and show it as a scheduling idea that follows from the case's own rule: about 30 to 50 times fewer misses at no cost in coverage in this test.
4. Implement the admission check as a dry run of the scheduler's own earliest-deadline-first step on the forecast, not as a capacity sum, or the one-server-per-job limit produces misses even with a perfect forecast.
5. Use real archived forecasts (the two commands above; no key, 0.5 MB each) in the yearly run. It makes "the system checks the weather forecast" from the core use case reproducible.
6. Make sold share and the unsold-hour rule two visible switches; default *idle*, and print the break-even as 0.2261 ÷ sold share when *filler* is on.
7. For N: missed deadlines do not separate 6 from 8 (0.15% against 0.29%); coverage does.

## 7. Commands run

```bash
python3 analysis/r2_deadline_sim.py > docs/research/r2-missed-deadlines-output.txt   # 680 simulated years, 5 seeds, about 2 min 15 s on 12 cores
python3 analysis/r2_deadline_sim.py --seeds 3     # quicker (not run)
python3 analysis/r2_deadline_sim.py --procs 1     # single process (not run)
```

Plus the three `curl` downloads in section 2, one `curl` with `models=ecmwf_ifs` (identity check, file deleted), and `pdftotext` on the downloaded ECMWF/MeteoSwiss report. Two full runs gave identical figures for the rows present in both.

Files written: `analysis/r2_deadline_sim.py`, `analysis/r2_data/prev_ecmwf_ifs025.csv`, `analysis/r2_data/prev_runs_basel_2025.csv`, `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv`, `docs/research/r2-missed-deadlines.md`, `docs/research/r2-missed-deadlines-output.txt`.
