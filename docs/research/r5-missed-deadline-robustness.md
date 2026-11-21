# Round 5: missed-deadline robustness

Weak point: *"0 missed relies on a same-family forecast, restart outside execution, no failures or runtime overruns"* (docs/overnight.md, open risk 4, Q&A 5). Assessment only. No scheduler, dashboard or demo was built. No git state was changed. Firecrawl calls used: 0 of 3.

Status labels: *computed* = printed by the named script and command on the stand-in reference house; *sourced* = number read on the URL given; *assumption* = our choice; *unverified* = not checked. Currency: none needed (no money figures in this file; break-even is not recomputed here).

## Answer in 8 lines

1. **An independent forecast does not break the 0.** The archived NOAA GFS and DWD ICON forecasts (different model families from the ECMWF "truth") give **0 missed in all 5 seeds at N=6 and N=8 with the 2 K guard** (*computed*). Both run warm against the truth (+0.5 to +1.1 K day 1), just like ifs025, so they are cautious too.
2. **A cold forecast is what hurts, and the guard band handles it.** With each forecast's own bias removed and then pushed 1 K too cold, the guard band still holds N=6 at 0 and N=8 at 0 to 18 a year (pooled 0.001–0.023%). Without the guard: 0.10–0.49% at N=6, 0.21–0.66% at N=8 (*computed*).
3. **Server failures barely matter for deadlines.** At a sourced 8%/server-year and a scaled 0.55/server-year (72 h repair), and also at 1.0/server-year: 0 missed at both N, with or without the scheduler being told. Misses only show up at about 4 failures per server-year with 168 h repairs, and then only 0.03–0.09% (*computed*). Failures cost **heat** (0.1–0.5 coverage points), not deadlines.
4. **Runtime overrun is the real risk.** If true runtimes run 10% over nominal on average and admission plans on nominal, misses go to **0.39% (N=6) / 0.24% (N=8)** of accepted jobs, about 100–130 a year. At +30% they reach 2.0% / 1.7% (*computed*; overrun sizes are *assumptions*).
5. **The fix is cheap: admit on padded runtimes.** If admission assumes nominal × 1.3, the combined plausible case (ICON + failures 0.55/yr + overrun +10% + 15-min restart) goes back to **0 missed in all 5 seeds at both N**. The cost: acceptance under that stress falls from 89.7% to 87.8% (N=6) and from 90.1% to 88.6% (N=8); the unstressed headline accepts 94.6% / 93.8% (*computed*). This is one parameter in admission, not a new rule.
6. **Restart inside execution adds a handful a year.** With the dry run aware of start-up time (5, 15 or 30 min, or the 2.1 s measured on the laptop), 0–5 misses a year (0.001–0.004%). If the dry run ignores restart: 6–27 a year (0.03–0.06%) (*computed*). The laptop's cold restart of J1 takes **2.1 s** (*computed*, `analysis/r5_model_load_probe.py`). A server boot is not measured.
7. **Combined, plausible, unpadded:** about **0.4% / 0.25%** of accepted jobs (N=6 / N=8), 76–155 a year. **Combined, harsh** (cold-biased forecast, 1 failure per server-year, +30% overrun, restart ignored): **about 2%**.
8. **Coldest day:** a server that dies on a −2.7 °C day costs 58 kWh of server heat over 72 h (the backup heater takes it) and **0 missed jobs** at N=6 and N=8, told or not told. The reason is that the contract follows the monthly mean, so the coldest days have spare compute (*computed*).

## (a) Independent forecast

### Data (small free download, committed under `analysis/r5_data/`, 0.94 MB; the requests contain coordinates only)

```bash
cd analysis/r5_data
V="temperature_2m,temperature_2m_previous_day1,temperature_2m_previous_day2,temperature_2m_previous_day3,temperature_2m_previous_day4,temperature_2m_previous_day5,temperature_2m_previous_day6,temperature_2m_previous_day7"
for M in gfs_seamless icon_seamless; do
  curl -s -o prev_${M}.csv "https://previous-runs-api.open-meteo.com/v1/forecast?latitude=47.56&longitude=7.59&hourly=$V&start_date=2025-01-01&end_date=2025-12-31&timezone=Europe%2FZurich&format=csv&models=${M}"
done
```

Downloaded 2026-11-21. Both files have 8,760 rows. GFS snaps to the grid cell 47.504 N, 7.617 E. ICON snaps to 47.563 N, 7.590 E. GFS has all 7 lead days. ICON has **no day-7 values (all NaN)**, so the script fills ICON's day 7 from GFS day 7 (labelled in the code).

| Fact | Status | Source |
|---|---|---|
| "`temperature_2m_previous_day1` returns the value predicted 24 hours before valid time"; most models archived from January 2024 (GFS 2 m temperature from March 2021) | *sourced* | <https://open-meteo.com/en/docs/previous-runs-api> (read via a summarising fetch tool; re-read by eye before slide use) |
| "NCEP GFS Seamless" and "DWD ICON Seamless" are selectable; "Seamless combines all models from a given provider" | *sourced* | same URL. The API names `gfs_seamless` / `icon_seamless` are confirmed only by the successful downloads |
| **Round 2's "best match" forecast was already ICON.** Days 0–6 of `analysis/r2_data/prev_runs_basel_2025.csv` are identical to `icon_seamless` in all 8,760 hours; day 7 matches GFS in 6,730 of 8,760 hours | *computed* (inline comparison, session command below) | — |

Comparison command (run from `analysis/`): `python3 -I -c "a=[l.split(',') for l in open('r5_data/prev_icon_seamless.csv').read().split('\n')[4:] if l]; b=[l.split(',') for l in open('r2_data/prev_runs_basel_2025.csv').read().split('\n')[4:] if l]; print([sum(x[k]==y[k] for x,y in zip(a,b)) for k in range(1,9)])"` → `[8760, 8760, 8760, 8760, 8760, 8760, 8760, 0]`.

### Forecast error against the reference-house temperature (*computed*, `python3 analysis/r5_miss_stress.py`, section 1)

```
  ifs025       d1 bias +0.29 RMSE 1.16 | d3 bias +0.33 RMSE 1.45 | d5 bias +0.33 RMSE 2.01 | d7 bias +0.19 RMSE 2.85 | Dec-Feb d1 bias +0.51 RMSE 1.41
  gfs          d1 bias +0.53 RMSE 1.71 | d3 bias +0.59 RMSE 1.92 | d5 bias +0.70 RMSE 2.47 | d7 bias +0.65 RMSE 3.06 | Dec-Feb d1 bias +1.12 RMSE 1.95
  icon         d1 bias +1.10 RMSE 1.82 | d3 bias +0.31 RMSE 1.59 | d5 bias +0.11 RMSE 2.33 | d7 bias +0.65 RMSE 3.06 | Dec-Feb d1 bias +0.59 RMSE 1.66
  gfs_cold     d1 bias -1.00 RMSE 1.91 | d3 bias -1.00 RMSE 2.08 | d5 bias -1.00 RMSE 2.57 | d7 bias -1.00 RMSE 3.15 | Dec-Feb d1 bias -0.41 RMSE 1.64
  icon_cold    d1 bias -1.00 RMSE 1.76 | d3 bias -1.00 RMSE 1.85 | d5 bias -1.00 RMSE 2.53 | d7 bias -1.00 RMSE 3.15 | Dec-Feb d1 bias -1.51 RMSE 2.17
  ifs025_cold  d1 bias -1.00 RMSE 1.51 | d3 bias -1.00 RMSE 1.73 | d5 bias -1.00 RMSE 2.22 | d7 bias -1.00 RMSE 3.01 | Dec-Feb d1 bias -0.78 RMSE 1.53
  icon         day 1: heating-day flag wrong, forecast heating but not:  1 days; forecast no heating but yes: 25 days
  icon_cold    day 1: heating-day flag wrong, forecast heating but not: 11 days; forecast no heating but yes:  0 days
```

- "Cold" variants (*assumption*): each lead's yearly mean bias is removed in-sample (hindsight), then 1 K is subtracted. This is a forecast that promises permits that never come: the dangerous sign. It stands for a system that calibrates its forecast against the house and then meets a cold-biased spell.
- The independent forecasts have about 1.5× ifs025's day-1 RMSE. Their warm bias still protects the figure. A wrong-sign bias does more damage than a larger RMSE (same finding as the round-2 critic).

### Result (headline `shaped100`, 5 seeds; seed 1 = committed CSV offers)

| Forecast | Guard 2 K: N=6 | Guard 2 K: N=8 | Guard 0 K: N=6 | Guard 0 K: N=8 |
|---|---|---|---|---|
| ifs025 (headline) | 0 in all 5 | 0 in all 5 | 0 in all 5 | 4–16 a year (0.027%) |
| GFS (independent) | 0 in all 5 | 0 in all 5 | 0 in all 5 | 0–13 (0.016%) |
| ICON (independent) | 0 in all 5 | 0 in all 5 | 0–6 (0.004%) | 0–11 (0.006%) |
| GFS debiased −1 K | 0 in all 5 | 0–7 (0.007%) | 118–200 (0.49%) | 192–282 (0.66%) |
| ICON debiased −1 K | 0 in all 5 | 0–1 (0.001%) | 24–50 (0.10%) | 65–85 (0.21%) |
| ifs025 debiased −1 K | 0 in all 5 | 0–18 (0.023%) | 41–80 (0.18%) | 105–145 (0.36%) |

Coverage moves by −0.45 to +0.16 points, and accepted share stays at 93–96% (full table below). **The guard band is what keeps the figure at zero.** It must stay in the core (it is a single threshold, 10 °C instead of 12 °C, in the forecast demand).

## (b) Server failures

### Failure rate

| Source | Number read | Status | URL |
|---|---|---|---|
| Microsoft cloud hardware study (SoCC 2010), more than 100,000 servers, 14 months | "9 machine failures in 14 months translates to an annual failure rate (AFR) of around 8%" (normalised per 100 servers); a repaired machine sees on average 2 repairs | *sourced* (PDF text extracted with `pdftotext` and read) | <https://www.microsoft.com/en-us/research/wp-content/uploads/2010/06/socc088-vishwanath.pdf> |
| Llama 3 training (Meta, 2024), up to 16K H100 GPUs | "During a 54-day snapshot period of pre-training, we experienced a total of 466 job interruptions"; 419 unexpected; "Approximately 78% of the unexpected interruptions are attributed to confirmed hardware issues"; Faulty GPU 148, GPU HBM3 memory 72 | *sourced*, read via a summarising fetch tool (the tool's "30.1%" for Faulty GPU does not equal 148/419 = 35.3%; re-read by eye before quoting the percentages) | <https://arxiv.org/html/2407.21783v3> |

Derived rates (*computed*, inline command: `python3 -c "hw=0.78*419; pg=hw/16384*365/54; print(pg, 4*pg)"`, assuming 16K = 16,384 GPUs):
- 0.135 hardware interruptions per GPU-year, so **0.54 per 4-GPU reference server-year** (0.69 counting all unexpected interruptions). That is training at full power and covers interruptions, not necessarily repairs. Used as the high case **0.55**.
- Low case **0.08** per server-year (Microsoft AFR). Stress case **1.0**. Break-point probes **2.0** and **4.0** with 168 h repairs.
- Repair time: **72 h** (*assumption*: technician visit to a house within about 3 days), sensitivity 24 h and 168 h.
- Failure model (*assumption*): Poisson per server while it is up, the failure falls on an hour boundary, and no work is lost (J1 checkpoints per file, J2 per batch). The scheduler knows which servers are down now and their repair end, but not future failures. Variant "NOT told": the scheduler plans with all N.

### Result (guard 2 K, 5 seeds)

| Failures | N=6 missed | N=8 missed | Coverage change |
|---|---|---|---|
| 0.08 / server-year, 72 h | 0 in all 5 | 0 in all 5 | −0.04 / 0.00 points |
| 0.55, 72 h (1–5 outages a year, 72–432 server-h down) | 0 in all 5 | 0 in all 5 | −0.21 / −0.09 |
| 0.55, 24 h / 168 h | 0 / 0 | 0 / 0 | −0.05 to −0.51 |
| 1.0, 72 h | 0 | 0 | −0.20 / −0.09 |
| 0.55, 72 h, scheduler NOT told | 0 | 0 | −0.21 / −0.09 |
| 2.0, 168 h, NOT told | 0–14 (0.009% pooled) | 0 | −0.81 / −0.67 |
| 4.0, 168 h, NOT told | 0–72 (0.09%) | 0–25 (0.03%) | −2.66 / −1.04 |
| Bound: 1 server down all year, NOT told | 93–130 (0.36%) | 8–24 (0.05%) | −8.26 / −3.59 |

Why the failures are harmless for deadlines (*computed*, inline check in this session): **outages bind only when every server holds a permit, and those are the coldest hours.** In those hours the headline contract leaves spare capacity, because it follows the monthly mean. In the headline run, N=6 has 3,198 permit server-hours a year with no admitted work and N=8 has 5,346. The plumbing was checked: a permanent outage the scheduler is not told about does produce misses (bound row).

## (c) Runtime overrun

Model (*assumption*): true runtime = nominal × (1 + U(0, 2o)), so mean overrun o, with a tail up to +2o. Admission and the dry run use nominal (remaining = nominal − done). Mitigation `pad`: admission books nominal × (1 + pad).

| Overrun | Guard 2 K: N=6 | N=8 | Accepted (N=6 / N=8) |
|---|---|---|---|
| none (headline) | 0 | 0 | 94.6% / 93.8% |
| mean +10% (0–20%) | 102–132 a year, **0.39%** of accepted jobs, 0.90% of accepted work | 61–108, **0.24%**, 0.63% | 90.5% / 90.6% |
| mean +30% (0–60%) | 528–631, 2.0%, 7.6% of work | 507–581, 1.7%, 6.2% | 84.6% / 83.4% |
| +30% with a 30% pad | 62–83, 0.26% | 53–65, 0.20% | 77.5% / 77.7% |

- Overrun raises coverage by 1–3.6 points, because the same jobs need more server-hours and so give more heat. If the customer pays per finished job, those extra hours are **unpaid**. The break-even per *paid* server-hour then rises (not recomputed here).
- Plausibility (*unverified*): J1's runtime scales with audio length, which is known at intake. The repeated laptop runs varied by about 1–5% (round-3 files: 70.6–71.4 s; 98.9–104.3 s). J2 (LLM generation) varies with output length, so it is the more likely job to overrun.
- **A pad that covers the tail removes the misses.** Combined plausible (E1) plus a 30% pad (E4) gives 0 in all 5 seeds at both N with the guard on. A pad smaller than the tail (c3) does not.

## (d) Restart inside execution

The plan has **no measured model-load time** (overnight.md: "15 min *assumption* until role B measures model-load time"). Measured here:

```
$ python3 analysis/r5_model_load_probe.py          (computed, M3 Pro laptop, HF_HUB_OFFLINE=1)
import mlx.core + mlx_whisper only: 2.05, 1.03, 1.02 s
run 1: 2.62 s wall for a 3.9 s clip (new process + imports + model load + transcription)
run 2: 2.10 s wall ...
run 3: 1.96 s wall ...
median cold restart of J1 on the laptop: 2.10 s = 0.035 min
```

This is the laptop part only. A powered-down reference server adds firmware POST and OS boot (about 2–5 min in round 2, *unverified*, search snippets only). So we ran 2.1 s, 5, 15 and 30 min.

| Restart in execution | N=6 (5 seeds) | N=8 | Coverage change |
|---|---|---|---|
| 2.1 s, dry run aware | 0–3 a year (0.004%) | 0–2 (0.002%) | ≈0 |
| 5 min, aware | 0–3 (0.004%) | 1–2 (0.004%) | +0.09 / +0.18 |
| 15 min, aware | 0–3 (0.004%) | 0–3 (0.004%) | +0.35 / +0.55 |
| 15 min, dry run NOT aware | 6–13 (0.029%) | 9–23 (0.037%) | 0 / +0.13 |
| 30 min, aware | 0–1 (0.001%) | 0–5 (0.004%) | +0.71 / +1.13 |

The 0–3 a year at 2.1 s equal those at 5–30 min. They are an artefact of whole-hour steps: a job that loses even 2 s on a cold start needs one more hourly slot. **Read the restart effect as "a handful a year", independent of the exact restart time, as long as the dry run derates starting servers.** The perfect-forecast consistency test ("exactly 0 missed") holds only with restart outside execution, as the plan already says.

## Combined

| Scenario (guard 2 K) | N=6 per seed | Pooled | N=8 per seed | Pooled |
|---|---|---|---|---|
| E1 plausible: ICON + failures 0.55/yr 72 h + overrun +10% + restart 15 min aware | 97–155 | **632 / 150,218 = 0.42%** (1.0% of work) | 76–104 | **447 / 176,440 = 0.25%** |
| E2 same with GFS | 88–128 | 0.37% | 51–94 | 0.21% |
| E3 harsh: ICON cold + failures 1.0/yr + overrun +30% + restart 15 min NOT aware | 545–678 | 2.10% (8.1% of work) | 635–765 | 2.06% |
| E4 = E1 + admission pads runtimes 30% | 0 in all 5 | **0 / 147,034** | 0 in all 5 | **0 / 173,616** |
| E4 without the guard band | 0–22 | 0.016% | 0–33 | 0.034% |

E1 misses by month (pooled over 5 seeds, N=6): Jan 17, Feb 73, Mar 26, **Apr 234**, May 36, Jun 24, Jul 14, Aug 16, Sep 45, Oct 65, Nov 0, Dec 82. April (shoulder season, flip-flopping heating days) is the worst month, as in round 2.

## Pitch wording (honest headline)

Tile 5 / spoken line (N=6 shown, N=8 in brackets; seed 1 = the committed offer file):

> "Missed deadlines: **0 of 31,908 accepted jobs** (0 of 36,771), with real archived forecasts from three different weather models and a 2 K safety margin. Stress-tested: server failures at up to one per server per year cost heat, not deadlines (still 0). **If jobs run 10% longer than booked, about 0.4% (0.25%) would miss**, about 100 a year. Booking 30% headroom per job brings that back to 0; we then accept 88% of offered jobs instead of 90%."

Rules:
- Always say "x of y accepted jobs", the offer scenario, and the forecast source. Never a bare 0%.
- Say "forecast error and failures tested; runtime overrun is the risk we manage with headroom".
- Drop "forecast from the same model family" as the main caveat, since it is now tested. Replace it with: "The truth is a weather model, not a thermometer in a real house; forecasts that run too cold are the danger and the 2 K margin covers −1 K of bias."
- If the 30% pad is **not** in the core by the 21:00 freeze, the spoken line must quote the unpadded combined figure (0.4% / 0.25%), not 0.

## Q&A: "What if a server dies on the coldest day?"

> "The house stays warm: every hour the backup heater covers what the servers don't deliver. One server is at most 0.8 kW, so on a −3 °C day it is 9% of the house's heat. We simulated one and two servers dying at midnight on the coldest usable day of 2025 (22 November, −2.7 °C mean, 225 kWh demand), with a 72-hour and a 168-hour repair. Missed deadlines stayed at 0, at six and at eight servers, even when the scheduler was not told about the failure. What we lose is heat: 58 kWh for a 3-day repair, 134 kWh for a week, about 0.2–0.4 points of yearly coverage. Deadlines survive because the coldest days are the days with spare compute: the contract follows the monthly average, so on the coldest days every server holds a heat permit but not all have work. Random failures at published data-centre rates (8% to about 0.5 per server per year) give 0 missed in all our runs. Misses only start at about four week-long failures per server per year."

Footnotes: the coldest day of 2025 (31 Dec, −3.0 °C) is the last simulated day, so a failure there is cut off by the end of the year and was not used. On 13 January (−2.4 °C, the coldest January day) a failure costs 0 kWh and 0 jobs, because those servers were idle for lack of admitted work (known from round 4). *Computed*, `python3 analysis/r5_miss_stress.py`, section 4, seed 1, guard 2 K.

## Commands

```bash
python3 analysis/r5_miss_stress.py            # full run: 560 simulated years, 12 cores, about 2 min 40 s
python3 analysis/r5_miss_stress.py --quick    # regression + forecast error only, about 7 s
python3 analysis/r5_model_load_probe.py       # laptop cold restart of J1, about 15 s
```

Full output: [r5-missed-deadline-robustness-output.txt](r5-missed-deadline-robustness-output.txt). Regression (section 0, all OK): seed-1 offers regenerated by `r4_headline.offer_stream` equal the committed CSV; without stress the loop reproduces `r4_headline.run(HEADLINE)` (accepted 31,937 / 36,784, missed 0 / 0, coverage 73.198% / 85.729%); with a 15-min aware restart it reproduces `r3_policy_check.run(policy A)` (missed 1 / 3, starts 805 / 1,369).

Note that the BASE seed-1 count of closed jobs is 31,908 / 36,771 (the plan's figure). Seed means of coverage over 5 seeds are 73.76% / 86.08%; the plan's 3-seed means are 73.67% / 86.14%.

### Full guard-2 K table (from the output file)

```
  N=6
    scenario                                                                       missed x/y per seed                                          miss%   work%  acc%          cover          util
    BASE headline (ifs025)                                                         0/31,908 0/31,694 0/31,996 0/31,857 0/31,870                0.000%  0.000% 94.6%  73.76% (+0.00)  54.8% (+0.0)
    check: perfect forecast                                                        0/31,859 0/31,655 0/31,954 0/31,773 0/31,802                0.000%  0.000% 94.5%  73.69% (-0.07)  54.7% (-0.1)
    a1 forecast GFS (independent)                                                  0/31,951 0/31,686 0/31,983 0/31,840 0/31,858                0.000%  0.000% 94.6%  73.78% (+0.02)  54.8% (+0.0)
    a2 forecast ICON (independent)                                                 0/31,694 0/31,413 0/31,761 0/31,582 0/31,613                0.000%  0.000% 93.9%  73.31% (-0.45)  54.5% (-0.3)
    a3 GFS debiased -1 K (cold)                                                    0/32,091 0/31,813 0/32,136 0/31,988 0/31,989                0.000%  0.000% 95.1%  73.90% (+0.14)  54.9% (+0.1)
    a4 ICON debiased -1 K (cold)                                                   0/32,031 0/31,769 0/32,069 0/31,934 0/31,933                0.000%  0.000% 94.9%  73.80% (+0.04)  54.8% (+0.0)
    a5 ifs025 debiased -1 K (cold)                                                 0/32,045 0/31,773 0/32,072 0/31,932 0/31,951                0.000%  0.000% 94.9%  73.92% (+0.16)  54.9% (+0.1)
    b1 failures 0.08/srv-yr, 72 h repair                                           0/31,908 0/31,681 0/31,996 0/31,811 0/31,870                0.000%  0.000% 94.6%  73.72% (-0.04)  54.8% (-0.0)
    b2 failures 0.55/srv-yr, 72 h repair                                           0/31,878 0/31,678 0/31,996 0/31,782 0/31,853                0.000%  0.000% 94.6%  73.56% (-0.21)  54.6% (-0.2)
    b4 failures 0.55/srv-yr, 168 h repair                                          0/31,760 0/31,607 0/31,996 0/31,658 0/31,829                0.000%  0.000% 94.5%  73.25% (-0.51)  54.4% (-0.4)
    b5 failures 1.0/srv-yr, 72 h repair                                            0/31,890 0/31,656 0/31,996 0/31,799 0/31,836                0.000%  0.000% 94.6%  73.56% (-0.20)  54.6% (-0.1)
    b8 failures 4.0/srv-yr, 168 h, NOT told (break-point probe)                    30/31,085 0/31,400 72/30,305 6/31,414 34/31,104             0.093%  0.406% 92.8%  71.10% (-2.66)  52.8% (-2.0)
    c1 overrun mean +10%                                                           102/30,371 114/30,213 123/30,593 132/29,831 119/30,582      0.389%  0.899% 90.5%  74.77% (+1.01)  55.5% (+0.7)
    c2 overrun mean +30%                                                           528/28,314 585/28,116 580/28,571 631/28,192 537/28,341      2.022%  7.591% 84.6%  76.05% (+2.29)  56.5% (+1.7)
    d2 restart 15 min in exec, aware                                               1/31,866 1/31,667 3/31,930 0/31,787 1/31,803                0.004%  0.009% 94.5%  74.11% (+0.35)  55.0% (+0.3)
    d3 restart 15 min in exec, NOT aware                                           7/32,008 9/31,723 12/32,058 6/31,932 13/31,928              0.029%  0.102% 94.8%  73.76% (-0.00)  54.8% (-0.0)
    E1 COMBINED plausible: ICON + fail 0.55/72h + overrun 10% + restart 15 aware   132/30,192 155/29,839 97/30,400 137/29,503 111/30,284       0.421%  0.999% 89.7%  74.51% (+0.75)  55.3% (+0.6)
    E3 COMBINED harsh: ICON cold + fail 1.0/72h + overrun 30% + restart 15 NOT awa 567/28,438 571/27,952 608/28,733 678/28,099 545/28,215      2.099%  8.114% 84.6%  75.88% (+2.12)  56.4% (+1.6)
    E4 E1 + admission pads 30%                                                     0/29,460 0/29,180 0/29,849 0/28,957 0/29,588                0.000%  0.000% 87.8%  75.09% (+1.33)  55.8% (+1.0)
  N=8
    BASE headline (ifs025)                                                         0/36,771 0/36,989 0/37,201 0/36,834 0/36,931                0.000%  0.000% 93.8%  86.08% (+0.00)  47.9% (+0.0)
    a1 forecast GFS (independent)                                                  0/36,760 0/36,949 0/37,157 0/36,805 0/36,893                0.000%  0.000% 93.7%  86.02% (-0.06)  47.9% (-0.0)
    a2 forecast ICON (independent)                                                 0/36,556 0/36,735 0/36,949 0/36,608 0/36,669                0.000%  0.000% 93.2%  85.70% (-0.38)  47.7% (-0.2)
    a3 GFS debiased -1 K (cold)                                                    1/36,915 7/37,218 4/37,353 0/36,952 1/37,097                0.007%  0.027% 94.2%  85.91% (-0.17)  47.9% (-0.1)
    a5 ifs025 debiased -1 K (cold)                                                 4/36,819 3/37,114 0/37,282 18/37,011 18/37,170              0.023%  0.102% 94.1%  86.02% (-0.06)  47.9% (-0.0)
    b2 failures 0.55/srv-yr, 72 h repair                                           0/36,771 0/36,989 0/37,193 0/36,816 0/36,913                0.000%  0.000% 93.8%  85.99% (-0.09)  47.9% (-0.1)
    b8 failures 4.0/srv-yr, 168 h, NOT told (break-point probe)                    25/36,048 25/36,655 0/37,205 0/36,757 0/36,798              0.028%  0.120% 93.3%  85.04% (-1.04)  47.4% (-0.6)
    c1 overrun mean +10%                                                           74/35,313 108/35,575 96/35,797 87/35,388 61/35,503          0.240%  0.629% 90.6%  87.97% (+1.89)  49.0% (+1.1)
    d3 restart 15 min in exec, NOT aware                                           10/36,806 23/37,067 9/37,154 11/36,917 15/36,914            0.037%  0.091% 93.9%  86.20% (+0.13)  48.0% (+0.1)
    E1 COMBINED plausible: ICON + fail 0.55/72h + overrun 10% + restart 15 aware   85/35,196 100/35,380 104/35,498 82/35,151 76/35,215         0.253%  0.633% 90.1%  88.11% (+2.03)  49.1% (+1.1)
    E3 COMBINED harsh: ICON cold + fail 1.0/72h + overrun 30% + restart 15 NOT awa 657/32,979 765/33,060 649/33,031 635/32,393 674/32,760      2.058%  7.827% 84.0%  89.26% (+3.18)  49.7% (+1.8)
    E4 E1 + admission pads 30%                                                     0/34,609 0/34,653 0/34,932 0/34,608 0/34,814                0.000%  0.000% 88.6%  88.79% (+2.72)  49.5% (+1.5)
```

(Some rows omitted here for length; all rows, both guard settings and section 3 pooled sums are in the output file.)

## Limitations

- **The truth is still a model.** All "actual" weather is the ECMWF IFS 9 km series. Independence holds only between forecast and truth model families, not against a thermometer in a real house with a thermostat. One weather year (2025).
- The cold variants debias in-sample (hindsight) and shift by a fixed −1 K. A real cold spell may be biased more strongly for a few days.
- Failure rates come from data-centre populations (2010 general servers; 2024 H100 training at full power), not from home-basement GPU servers that power-cycle often. No source was found for failure rates under frequent power cycling (open risk 6 unchanged). Lost work at failure is assumed zero (checkpoints).
- Overrun distribution and pad size are *assumptions*. A real scheduler would learn runtimes per job type. Overrun hours are counted as sold here, but they may be unpaid.
- Restart: the aware-dry-run figures need the core to derate starting servers. That is the round-3 "restart inside the scheduler" item the plan **cut**. With the plan's accounting line, the published number stays the restart-free one, and this file only gives the expected size (a handful a year).
- 5 seeds of offer arrival noise and stress draws. The heat-shaped contract (`shaped100`) is still our own sizing. At 120–200% offers, misses return regardless (round 4).
- Hourly time steps create a floor of 0–3 misses a year whenever restart is inside execution (d0 row).

## Proposed plan changes

1. **Missed-deadline tile wording:** keep "0 of 31,908 / 0 of 36,771 accepted jobs". Change the caveat from "forecast from the same model family" to "tested with three forecast models (ECMWF, GFS, ICON) and server failures at published rates; runtime overrun is the managed risk".
2. **Add one admission parameter, `runtime_pad`** (book nominal × 1.3; one multiplication where admission reads a job's runtime). It is the only change that keeps 0 under the combined stress. Cost under the combined stress: acceptance 89.7% → 87.8% at N=6 and 90.1% → 88.6% at N=8 (94.6% / 93.8% in the unstressed headline; the pad alone without overrun was not run). Build scope: small (*assumption*: under 30 minutes for role A). Decide at 10:15 together with the band size. If it is not in by the freeze, quote 0.4% / 0.25% as the combined figure.
3. **Q&A 5** gets the new numbers: GFS/ICON 0 with the guard; −1 K cold bias 0 / ≤18 a year; failures 0 up to 1 per server-year; overrun +10% about 0.4% / 0.25% without a pad, 0 with it.
4. **New Q&A answer** "server dies on the coldest day" (text above).
5. **Open risk 4** (missed-deadline figure narrow): mark forecast family, failures and restart as tested (with numbers); what stays open is overrun size, a real-house thermometer, failures under power cycling, and the contract size.
6. **Restart:** keep it as an accounting line (no change). Record that the laptop's cold restart of J1 is 2.1 s (role B's model-load measurement can be taken from `analysis/r5_model_load_probe.py`); the server boot time stays unmeasured.
7. **Keep the 2 K guard band in the MUST list.** Without it a −1 K cold bias gives 0.1–0.66% misses.
