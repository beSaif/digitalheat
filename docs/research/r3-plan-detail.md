# Plan detail moved out of overnight.md (round 3 rewrite)

Text below was **moved verbatim** from `docs/overnight.md` (state after round 2) so that the plan itself stays short. Nothing here is new. Where `docs/overnight.md` (after round 3) says something different, **overnight.md wins**; lines superseded in round 3 are marked *[superseded in round 3: ...]*. Status labels as in overnight.md: *computed* (script named), *sourced* (URL opened), *unverified*, *assumption*.

## A. Servers per house — round-2 detail

- Argument for 6 (physical): the sixth server still runs 3,796 h/yr; the seventh and eighth add 7.5 and 5.8 coverage points for fewer hours.
- Argument for 8: the jury scores coverage first; 6 gives up 13 coverage points. The coverage gap (+13.0 to +13.4 points) and the utilisation gap (−7.3 to −7.4 points) are unchanged by the realism switches when paused servers are powered down (*computed*, `analysis/r2_realism.py`).
- **Payback rule, round-2 result:** by 5-year simple payback at sourced consumer-GPU host rates **no server pays back (N\* = 0)**. At Salad RTX 4090 host rates with one paid card per machine (host power and a 2,000 CHF host are *assumptions*), no server pays back in 5 years at the average rate (payback 7.5 to 11.2 years); at the highest rate 1 to 4 servers do, with every hour sold (*computed* by the critic, `python3 analysis/r2_fleet_economics_critic_check.py`).
- **Conditions under which the rule would return 6 or 8** (*computed*, `python3 analysis/r2_fleet_economics.py`, section 6; simple payback, no fixed costs, resale value or interest; hardware 6,000 CHF per kW, 5-year life, heat credited): N\*=1 needs 0.383 to 0.459 CHF net income per run hour, **N\*=6 needs 0.542 to 0.635 CHF, N\*=8 needs 0.752 to 0.998 CHF**.
- With the heat given to the homeowner and 80% of hours sold, no consumer-GPU scenario pays back any server within 5 years (*computed*, same script, section 7).
- **Mixed fleet: dropped as an idea.** No mixed fleet won on inputs a house could have; low-hour ranks are the hardest to pay back. (Do not say "ranks 7 to 13 never pay": at high enough income the single-hardware grid still returns 8 or more servers.)
- **The economics rely on GPU inference being sold.** The live demo job runs on a laptop; the price figures are GPU rental prices. The pitch must say these are different machines.
- Round-1 payback figures (renter price, no fee, two cards per machine) are superseded; they stay in the round-1 research file only.

## B. Run policy — round-2 detail

- **Known defect of the plain rule** (*computed*, `python3 analysis/r2_realism.py`; cause: hourly time step with whole servers): 1,732 (N=6) and 2,208 (N=8) server starts per year; one server slot is started 1,433 / 1,434 times; 1,540 of 1,726 pauses at N=6 last exactly one hour.

| Rule (*computed*, `analysis/r2_realism.py`, section v; unlimited jobs, no deadlines) | Starts/yr N=6 | Starts/yr N=8 | Coverage N=6 / N=8 | One-hour runs left |
|---|---|---|---|---|
| Plain follow | 1,732 | 2,208 | 79.58% / 92.94% | — |
| Cap + 8 kWh band (round-1 band rule) — **adopted** | 379 | 891 | 79.55% / 92.94% | 68 / 266 |
| Cap + 8 kWh band + "running servers keep running" (hold) — **candidate only** | 267 | 607 | 79.46% / 92.80% | 13 / 23 |

- **Hold rule: add only after it passes the deadline simulation.** It is stateful and tested only with unlimited jobs. With it the busiest slot has 90 / 112 starts per year, median pause 16 / 13 hours, summer (June to August) starts fall from 828 to 52. Under 2.80 kWh/day tank loss and peaked hot water it gives 260 / 686 starts.
- **Pause = power down, with a restart time.** Rule: power down when the pause is longer than *restart time ÷ idle fraction* (about 1.4 h with a 15-minute restart and 17.6% idle when idle heat is used; 0.5 h at 5 minutes; when idle heat is dumped the threshold is 1.0 h at the break-even price and longer at higher compute prices). Both inputs are unmeasured for our server. **Restart time is a visible scheduler parameter** (default 15 min, *assumption*; that time is unsold); replace it with role B's measured model-load time. Suspend-to-RAM and one warm standby were not examined.

*[superseded in round 3: the hold rule is cut (rounding-level effect on every key figure, `analysis/r3_policy_check.py` section 2); restart time is an accounting line outside the scheduler, not a scheduler parameter.]*

## C. Pause/resume demo — round-1/2 detail

- **Demo days: choose after N and the run policy are fixed.** The round-1 dates were computed for N=8 with a 2 kWh band (`python3 analysis/demo_day_timing.py`): 2025-01-13 runs all 8 servers 24/24 h with 0 pauses (36 s with no event); 2025-01-25 has a tank-full pause and a resume in winter; 2025-07-15 had 2 pauses of 4 h. **Recompute with the adopted cap + 8 kWh band before choosing**; if the hold rule is added (median run 27 h, pause 16 h) a July day may show one transition or none.

*[superseded in round 3: demo days recomputed for the adopted policy, see overnight.md "Pause/resume demo".]*

- **Timing** (*assumption*): about 130 s live part inside the 5:00 pitch; 2.5 s per simulated hour for July (60 s, a 4 h pause = 10 s); January at 1.0 s per hour or a day with an event. All times to be regenerated from the adopted policy, N and measured model load time.
- **Launch:** `caffeinate -dis`, proper charger (the probe laptop was on a 17 W source and discharged under load), `HF_HUB_OFFLINE=1`, one wifi-off rehearsal.
- **Energy for J1:** run of at least 10 minutes read from `ioreg` `PowerTelemetryData` (rootless; refreshes every 23 to 61 s; unit mW by internal consistency, *unverified* against a meter). Measure with full battery on the proper charger, fixed display brightness, report gross and net of idle, cross-check idle against Apple's published 4.19 W. Cross-check with `sudo powermetrics` if someone types the password. Fallback: runtime × adapter rating (96 W for the 12-core M3 Pro) as a labelled upper bound. Not CodeCarbon or macmon on these laptops. If the battery current is used instead: read `InstantAmperage` as a signed 64-bit value and take the absolute value (the procedure in the job-model research file has this sign bug in step 3a).

*[superseded in round 3 for the energy method: use the battery-controller accumulators in `analysis/r3_whisper_energy_probe.py`, not the per-minute `SystemPowerIn` snapshot.]*

## D. Finite demand with admission control (round 2)

All *computed* by `python3 analysis/r2_deadline_sim.py` (5 seeds, archived `ifs025` forecasts for 2025, no partner site unless stated; raw output in [research/r2-missed-deadlines-output.txt](r2-missed-deadlines-output.txt)). Contract shapes and offer levels are *assumptions*; the heat-shaped contract uses 2020–24 normals.

| Offers | Coverage N=6 / N=8 | Utilisation | Accepted | Missed, % of accepted jobs | Break-even |
|---|---|---|---|---|---|
| Saturating (N × 24 server-h/day) | 79.2% / 92.8% | 58.8% / 51.7% | 55.9% / 49.6% of jobs (59.7% / 53.0% of work); a property of how offers are defined, not of the scheduler | 0.15% / 0.29% in the base run; see range below | 0.2261 |
| Heat-shaped contract, 100% of the 2020–24 monthly mean | 74.1% / 86.1% | — | about 95% of offered jobs; sold share 93.2% / 92.7% | 0.000% / 0.016% (comes from about 7% slack in the contract) | 0.2261 |
| Flat contract at the 2020–24 annual mean (81.8 / 95.9 server-h/day) | 54.0% / 61.1% | — | 70.3% / 68.3% of offered work | 0.002% / 0.006% | 0.2261 |
| Heat-shaped, about 67% sold, unsold hours off | 53.2% / 62.2% | 39.5% / 34.6% | — | — | 0.2261 |
| Heat-shaped, about 38% sold, unsold hours off | 30.7% / 35.7% | 22.8% / 19.9% | — | — | 0.2261 |
| Unsold hours run as unpaid filler (comparison only) | 79.6% / 92.9% | 59.1% / 51.8% | — | — | 0.2449 / 0.2457 at about 92% sold; 0.3413 / 0.3407 at about 66%; 0.5880 / 0.5898 at about 38% |

- Heat-permit capacity by month, 2020–24 mean, N=8: from 15.0 server-h/day (June to August) to 185.3 (January). April varies between 52.8 and 145.7 and October between 24.4 and 110.9 across the five years; 2025 had 92.4 in April and 101.7 in October (*computed*, same script, section 1; data `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv`).
- **Reading (unchanged from round 1):** with finite demand one house cannot have high coverage, no dumping and all offered work hosted at once. The round-1 rows with dumping (for example winter-sized flat demand at N=8: 24,597 kWh dumped, blended break-even 0.2750) remain in [research/r1-job-model.md](r1-job-model.md).

## E. Missed deadlines, round-2 runs — forecast error only

Server failures, network loss, restart cost and runtime overruns are **not** modelled. Job mix is an assumption. *Computed* by `python3 analysis/r2_deadline_sim.py` unless marked; "critic" = *computed* by the round-2 critic in one-off checks described in the [critique file](r2-missed-deadlines-critique.md), to be rerun before quoting.

| Item | N = 6 | N = 8 |
|---|---|---|
| **Figure to use: range per year** (saturating offers, real archived forecasts, no margin, no partner; 2025 and 2024) | **roughly 0.1 to 0.6% of accepted jobs** | same range; N=8 worse in every variant |
| Same, in April, May and October | 0.5 to 1.8% of accepted jobs in those months | |
| Base run 2025 (5 seeds; seed range is arrival noise only) | 0.146% (0.097 to 0.267%) | 0.294% (0.160 to 0.386%) |
| Heating-day flag using only values available at decision time (critic) | 0.153% | 0.511% |
| Forecast mean bias removed (critic) | 0.445% | 0.592% |
| Out-of-sample year 2024 (critic) | 0.146% | 0.151% |
| Among 7-day (J2) jobs | about 0.8 to 1.3% | about 1.3 to 2.2% |
| Missed work, % of accepted work | 0.4 to 0.8% | 0.7 to 1.2% |
| Perfect forecast | 0 | 0 (shows only that admission and execution use the same rule) |
| **With the 2 K guard band** (2025 and 2024, also under causal flag and bias removal: critic) | below 0.02% | below 0.02% |
| Per-job share across other J1/J2 work mixes (critic) | 0.15 to 0.46% | 0.29 to 0.99% |

- **Guard-band cost:** coverage unchanged under saturating offers (79.2% / 92.8%); falls by up to 0.8 points under finite contracts (critic: heat-shaped 74.1 → 73.8% at N=6; flat 54.0 → 53.4% and 61.1 → 60.3%).
- **Cause of the misses:** the case's 12 °C heating-day rule. In 2025 the 7-day-ahead forecast flagged 9 days as heating days that were not (768 kWh of permits promised that never came); the 1-day-ahead forecast did so on 1 day (83 kWh). The figure is driven by a handful of days.
- **Partner site:** with an always-available partner the missed share falls somewhere between zero and the no-partner figure; the size of the reduction is not established (seed ranges overlap). A 0 h hand-off gives zero by construction. Partner refusing 20 / 50 / 100% of hand-offs (1 h delay): 0.125 / 0.165 / 0.222% at N=6 and 0.220 / 0.263 / 0.314% at N=8, ranges overlapping.
- **Sensitivity rows on assumed error models, not sourced bounds** (N=6 / N=8, saturating, no partner): best-match archive 0.075 / 0.266%; synthetic 1 K day-1 RMSE 0.403 / 0.665%; synthetic 2 K 1.022 / 1.057% (0.415 / 0.361% with a 1 h hand-off); synthetic 3 K 1.609 / 1.736%; synthetic 2 K with −1 K bias 2.100 / 2.474%; persistence 1.346 / 3.104%. The bias sign drives misses more than the RMSE.
- About 87% of accepted jobs are the 0.5 server-hour J1 type (N=8, seed 1), so the per-job figure is dominated by short jobs; in June to August all accepted jobs are J2.

**Forecast error used**

| Item | Value | Status |
|---|---|---|
| Archived ECMWF IFS 0.25° forecasts for Basel 2025 against the reference-house temperature, 8,760 h | 1 day ahead: RMSE 1.16 K, MAE 0.87 K, bias +0.29 K; 3 days: RMSE 1.45 K; 7 days: RMSE 2.85 K, MAE 2.19 K. 2024 check (critic): day-1 RMSE 1.34 K, bias +0.65 K; day-7 2.80 K | *computed*, `python3 analysis/r2_deadline_sim.py` section 0; data `analysis/r2_data/prev_ecmwf_ifs025.csv` from the Previous Runs API (query in the research file) |
| Open-Meteo best-match archive, Basel 2025 | day-1 RMSE 1.82 K, bias +1.10 K; day-7 RMSE 3.04 K | *computed*, same section; `analysis/r2_data/prev_runs_basel_2025.csv` |
| Why the measured error flatters us | the 9 km IFS series from the same API is identical to the reference temperature (truth and forecast are the same model family); its lead-time values exist only from 1 Oct 2025. The `ifs025` forecast is biased warm against the reference, which lowers the miss rate; an unbiased or slightly cold forecast gives two to three times more misses | *computed* (identity); the rest is the critic's reading |
| What `_previous_day1` means | value predicted 24 hours before valid time; fixed lead-time offsets of 1 to 7 days; most models archived from January 2024 | *sourced*: <https://open-meteo.com/en/docs/previous-runs-api> (read via a summarising fetch tool) |
| A weather vendor's own verification, worldwide, MAE not RMSE | 1.2 K at 24 h and 2.0 K at 6 days for its post-processed multi-model (2017, more than 11,000 stations); 2.0 to 2.4 K for raw global models against more than 8,000 WMO stations in 2018 (lead time of that table not confirmed) | *sourced*: <https://content.meteoblue.com/en/research-education/weather-data-accuracy/air-temperature/> (same tool) |
| Central-Europe RMSE table from a national weather service | not found in two searches; not evidence that none exists | *unverified* |

## F. Host-side income and renter prices (round 2)

**What a host gets is about 80% of the listed price, and no marketplace was found that pays a server which goes offline on its own heat signal.** Sold share stays an *assumption*: no measured occupancy and no transacted interruptible host rate were found.

| Item | Value | Status and source |
|---|---|---|
| Salad renter prices, USD per GPU-hour (Batch / Low / Medium / High priority) | RTX 5090 0.250 / 0.367 / 0.483 / 0.600; RTX 4090 0.160 / 0.253 / 0.347 / 0.440; RTX 3090 0.090 / 0.127 / 0.163 / 0.200 | *sourced*: <https://salad.com/pricing> |
| Salad host earning rates per GPU-hour **while a container job is running** (not per hour online); lowest / average of all hosts / average of top 25% / highest | RTX 4090 0.128 / 0.2302 / 0.2663 / 0.352; RTX 5090 0.200 / 0.3227 / 0.3867 / 0.480; RTX 3090 0.072 / 0.1029 / 0.1175 / 0.160 | *sourced*: data feed <https://app-api.salad.com/api/v2/demand-monitor/gpu> (21 Nov 2026), field definitions <https://support.salad.com/article/613-network-monitor>. Currency not labelled; **USD is our reading** |
| Host rate ÷ renter price, Salad | 0.80 at both ends of the range for all three cards (inferred ratio, not a published fee) | *computed*, `python3 analysis/r2_fleet_economics.py` section 3 |
| Vast.ai: "Live GPU prices are typically about 25% above what hosts earn" | host share 1 ÷ 1.25 = 0.80 | *sourced*: <https://vast.ai/article/how-much-money-can-you-earn-renting-out-your-gpu-on-vast-ai> (dated 18 May 2026); 0.80 *computed* |
| Vast.ai host payment page | states no fee percentage; 20 USD minimum balance before an invoice is generated | *sourced*: <https://docs.vast.ai/host/payment.md> |
| **Salad pays one GPU per machine** | "Only one GPU is used. A second dedicated card doesn't add earnings" | *sourced* by the critic: <https://support.salad.com/article/78-is-my-machine-compatible-with-salad> |
| **Salad RTX 4090 host rate per 1 kW of wall power**, one paid card per machine, host power 100 to 200 W assumed | average about **0.30 to 0.35 CHF**, highest about 0.45 to 0.54 CHF per sold hour | *unverified* (wall power not measured); arithmetic by `python3 analysis/r2_fleet_economics_critic_check.py` |
| RTX 5090 host income per 1 kW | roughly 0.25 to 0.60 CHF per sold hour on Salad rates; 0.37 to 0.75 CHF on Vast.ai's own statement | *unverified* (cards per kW assumed, not measured) |
| **Lowest rate a Salad job can pay an RTX 4090 host** | at most 0.215 CHF per 1 kW-hour (about 0.17 to 0.20 CHF with one card per machine): **below the 0.2261 CHF break-even**. It is the lowest job rate, not a tier the host chooses | *computed*, `analysis/r2_fleet_economics.py` section 3 and the critic check script |
| Vast.ai's own statement on host earnings | RTX 5090 about 0.30 to 0.60 USD per GPU-hour; for machines kept available ("must keep the machine available until the contract ends"), not measured data and not for a heat-following server. Its "four-GPU 5090 rig at 80% utilization, $700–$1,400 per month" is an illustration (4 × 0.8 × 730 h × 0.30–0.60), not a measured occupancy | *sourced* (same Vast.ai article); vendor statements |
| One Vast.ai host with six consumer cards (RTX 3060 to 3080) | 280 to 340 USD per month before electricity = 0.064 to 0.078 USD per card-hour | *sourced*: <https://dev.to/samhartley_dev/i-expanded-my-gpu-rental-fleet-to-6-cards-heres-what-happened-to-my-earnings-10d5> (single anecdote, year not shown); per card-hour *computed* |
| Vast.ai "interruptible" | saves clients 50 to 80%, hosts earn less per hour on it; it describes renters being outbid by other renters, **not a host that stops its machine**. Host guide: Min Bid Price is "a floor for the bidding system", to be set "close to your cost of power when the GPU is under load" | *sourced*: same article, <https://docs.vast.ai/documentation/instances/pricing>, <https://docs.vast.ai/host/optimization-guide.md> |
| Salad lowest customer-priority tier | 36% (RTX 4090) and 42% (RTX 5090) of the highest tier; chosen by the customer, not the host | *computed* from <https://salad.com/pricing> |
| Vast.ai asking prices, unrented verified single-GPU offers, 21 Nov 2026 | roughly 0.47 USD (RTX 4090) and 0.67 to 0.71 USD (RTX 5090) on demand; interruptible floors roughly 0.35 to 0.40 and 0.53 USD. Asking prices only, not transacted, not stable within an hour. Whether the field is renter-side or host-side is not defined | *unverified* |
| Occupancy / sold share | no figure found; Salad's `utilizationPct` shows values above 100 and cannot be read as a share of hours | *sourced* absence (same Salad feed) |
| CPU-only host income | none found (Vast.ai and Salad pay by GPU; other marketplaces not checked). Salad lists CPU-only renter prices of 0.005 USD per vCPU-hour and 0.001 USD per GB-hour, not converted | *unverified*; renter prices *sourced*: <https://salad.com/pricing> |

**Renter on-demand prices from round 1 (context only; not host income)**

| Hardware per ~1 kW | Renter price CHF per hour | Status and source |
|---|---|---|
| 2 × RTX 4090 (1 kW at the wall is an *assumption*; an upper bound on heat per sold hour) | 0.27 to 1.49 | *computed* (`analysis/r1_servers_choice.py`) from *sourced* prices: <https://computeprices.com/providers/vast/gpus/rtx4090> (third-party tracker, 0.160 to 0.640 USD per GPU-hour across providers), <https://www.runpod.io/pricing> (0.89 USD/h) |
| 96 CPU cores | 0.81 (bare-metal rent incl. power and hosting) to 1.90 (AWS spot snapshot, region not stated) | *computed* from *sourced*: <https://www.hetzner.com/dedicated-rootserver/matrix-ax>, <https://instances.vantage.sh/aws/ec2/c7i.48xlarge>. Mapping to one 1 kW server is by core count only. Host income *unverified* and lower |
| 1 kW share of an 8 × H100 server (fleet-level figure, not house-level) | 1.31 to 3.02 | *computed* from *sourced*: <https://www.runpod.io/pricing>, <https://instances.vantage.sh/aws/ec2/p5.48xlarge>, <https://lambda.com/pricing>; 10.2 kW system power from <https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html> |

## G. When the model does not pay off — round-2 detail

- **Operation only:** below **0.2261 CHF per sold server-hour** (heat credited to the operator, every run hour sold, server off when unsold); below **0.3325 CHF** if the homeowner gets the heat free (*computed*, `analysis/r2_fleet_economics.py`).
- **At the lowest job rate of the one marketplace with published host rates** (at most 0.215 CHF per kW-hour): operation alone is not covered.
- **Including hardware, 5-year simple payback:** at sourced consumer-GPU host rates no server pays back (see "Servers per house"). Six servers need 0.54 to 0.64 CHF net per run hour at 6,000 CHF per kW; eight need 0.75 to 1.00 CHF (*computed*, section 6).
- Hardware budget at 0.386 CHF per run hour, **an optimistic upper reading of the Salad average** (it assumes two paid cards in one machine), 5-year life, all hours sold, heat credited: N\*=1 needs hardware of 4,130 to 6,114 CHF per kW, N\*=6 2,350 to 3,042 CHF, N\*=8 1,246 to 1,828 CHF (*computed*, section 6). At 0.30 to 0.35 CHF the budgets shrink by a quarter to a half (critic).
- The rule behind these: under simple payback with no fixed costs, resale value or interest, N\* depends only on X = (hardware ÷ life) ÷ (income × sold share − break-even): N\*=1 for 5,153 < X ≤ 7,629 h, N\*=6 for 2,933 < X ≤ 3,796 h, N\*=8 for 1,555 < X ≤ 2,281 h, none above 7,629 h (*computed*, section 6).
- Income needed per sold hour with hardware at 5,924 CHF per kW, 5-year life, 80% sold with unsold hours still running, heat credited, no fixed costs: 0.477 CHF for rank 1, 0.673 for rank 6, 0.932 for rank 8 (*computed*, section 9).
- A new dual-RTX-5090 workstation at about 15,700 CHF per kW (*assumption* on wall power) does not pay back at Salad rates; only at Vast.ai's top advertised host figure with every hour sold, which a heat-following server cannot rely on (*computed*, section 7).
- **Worst case, servers left powered while paused** (every paused server at 17.6% idle all year): idle heat alone (20.3 kWh/day for 6 servers, 27.0 for 8) exceeds summer hot water (12 kWh/day), no server sells work from June to August, 1,312 / 2,391 kWh are dumped, break-even 0.2659 (N=6) / 0.2814 (N=8) (*computed*, `python3 analysis/r2_realism.py`, section iv a).
- **Servers that cannot serve hot water at all (for example air-cooled):** coverage falls to 70.5% (N=6) / 81.7% (N=8). Break-even stays 0.2261 if the hot-water heater is outside the model; 0.2578 / 0.2535 if its 4,380 kWh are charged to the servers with the heat credited at price ÷ 2.5; 0.2790 / 0.2718 uncredited (*computed*, same script, section iii; outside and uncredited figures by the critic).
- The last two are not "does not pay off" statements on their own; each must be set against a host income per server-hour.

## H. Realism switches — detail and sources

All *computed* by `python3 analysis/r2_realism.py` (its regression check reproduces `baseline_sweep.simulate()` exactly). Inputs: tank loss 2.80 kWh/day (*sourced*, one manufacturer), storage setpoint 60 °C (*sourced*), server-loop preheat to 50 °C, cold water 10 °C and booster COP 3 (*assumptions*).

| | Coverage N=6 | Coverage N=8 | Break-even N=6 | Break-even N=8 |
|---|---|---|---|---|
| Case assumptions | 79.6% | 92.9% | 0.2261 | 0.2261 |
| Tank loss 2.80 kWh/day only | −0.3 points | −0.3 points | +0.0030 | +0.0031 |
| Loss + electric booster 50 → 60 °C, **booster outside the model** (the case's treatment of the backup heater; critic) | 77.5% | 90.5% | 0.2292 | 0.2293 |
| Loss + electric booster, **electricity charged to the servers, its heat credited at price ÷ 2.5** | 77.5% | 90.5% | 0.2348 | 0.2341 |
| Loss + heat-pump booster at COP 3, charged and credited | 78.7% | 91.9% | 0.2310 | 0.2308 |
| Combined run: loss 2.80, peaked hot water, electric booster charged and credited, power-down, hold + cap + 8 kWh band, 15 min restart | 77.4% (utilisation 59.2%) | 90.3% (51.9%) | 0.2354 | 0.2352 |

- **June to August coverage:** −20.0 points with the electric booster (100% → 80%), by construction from the assumed temperatures: (50 − 10) ÷ (60 − 10). 11 points at a 55 °C setpoint, 30 points at a 45 °C loop. With the heat pump at COP 3: −6.7 points.
- **Break-even rise for loss + electric booster by convention:** +0.003 CHF with the booster outside the model; +0.008 to 0.009 charged and credited (range 0.0076 to 0.0095 at N=6 and 0.0068 to 0.0088 at N=8 across tank losses of 1.68 to 3.57 kWh/day); +0.011 to 0.013 if its heat is not credited.
- Booster alone, charged and credited: electric 876 kWh/yr, yearly coverage −1.7 / −2.2 points, +0.0058 / +0.0049 CHF; heat pump 292 kWh/yr, +0.0019 / +0.0016 CHF.
- Tank loss alone: 720 / 862 kWh per year lost, utilisation +1.5 / +1.4 points, summer coverage stays 100%. At the legal ceiling of 3.57 kWh/day: −0.4 points, +0.0038 / +0.0039 CHF.
- **Restart cost** (servers powered down, follow rule): with 15 minutes unsold per start 1.39% / 1.52% of run hours are unsold and break-even rises by 0.0032 / 0.0035 CHF; at 5 minutes by 0.0011 / 0.0012. With hold + cap + 8 kWh band and 15 minutes: 0.2266 / 0.2271. The 5 and 15 minutes are *assumptions*.
- **Peaked hot water** (45% morning, 10% midday, 45% evening; shape is an *assumption*): at most −0.1 coverage points, break-even unchanged; with a 5 kWh tank 0.39 / 0.29 points.

**Sources behind the switches**

| Item | Value | Status and source |
|---|---|---|
| Tank standing loss, nominally 1,000 l buffer tanks, one manufacturer, per EN 12897:2020 (test temperatures not stated) | 3.38 kWh/24h (887 l, class C), 2.80 kWh/24h (934 l, class C), 1.68 kWh/24h (934 l, double insulation, class A) | *sourced*: <https://exhibitorsearch.messefrankfurt.com/images/original/document_downloads/10000006202501/411541/1736956673448_2743857584.pdf> |
| EU ecodesign ceiling for hot water storage tanks from 26 Sep 2017 | 16.66 + 8.33 × V^0.4 W; at 1,000 l: 148.7 W = 3.57 kWh/day. Class boundaries at 1,000 l: A/B 1.82, B/C 2.54, C/D 3.57 kWh/day | *sourced*: <https://www.legislation.gov.uk/eur/2013/814/pdfs/eur_20130814_adopted_en.pdf>, class formulas <https://www.legislation.gov.uk/eur/2013/812/pdfs/eur_20130812_adopted_en.pdf>; kWh/day *computed* |
| Scope | 814/2013 covers tanks up to 2,000 l; the label regulation 812/2013 only up to 500 l, so a 1,000 l tank is outside the label's scope (manufacturers may still print a class) | *sourced*: <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32013R0814>, <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32013R0812> |
| EN 12897 test temperatures (commonly quoted 65 °C store, 20 °C ambient) | not confirmed | *unverified* |
| Swiss Legionella guidance, BAG/BLV Modul 11 (version 30.06.2026) | with warm-held pipes: storage or fresh-water station at least 60 °C, distribution 55 °C, tap 50 °C; without: storage 55 °C, fresh-water station 52 °C, tap 50 °C; cold water at most 25 °C. A daily or weekly heat-up to 60 °C is no longer considered effective and must not be used to lower operating temperatures; waste heat below 50 °C should be stored in non-drinking-water buffer tanks | *sourced*: <https://www.blv.admin.ch/dam/de/sd-web/C3T7bsOJlNIL/legionellen-modul-11-de.pdf> (sections 3.6, 5.5, 3.13.2) |
| Liquid-cooling classes, ASHRAE 2011, facility supply water | W1 2–17 °C, W2 2–27 °C, W3 2–32 °C, W4 2–45 °C, W5 above 45 °C | *sourced*: <https://datacenters.lbl.gov/sites/default/files/ASHRAE%20Thermal%20Guidelines_%20SVLG%202015.pdf> |
| ASHRAE 5th edition, per a trade blog (the ASHRAE book itself not opened) | classes renamed W17, W27, W32, W40, W45, W+; few products can operate consistently above 45 °C entering water | *sourced* (secondary): <https://www.upsite.com/blog/major-changes-to-ashraes-fifth-edition-of-thermal-guidelines-part-3-liquid-cooling-chapter-updates/> |
| One vendor's warmest direct-water-cooling tier | facility water 40–45 °C, server loop inlet 45–50 °C; 80–85% heat capture without a rear-door heat exchanger, 95–100% with one | *sourced*: <https://lenovopress.lenovo.com/lp2018-lenovo-neptune-direct-water-cooling-standards> |
| Outlet temperature | a 2012 trade-press article quotes a computing centre: inlet up to 40 °C, outlet up to 70 °C. No vendor data sheet with an outlet temperature for a current server found | *sourced* (press quotation only): <https://www.datacenterknowledge.com/cooling/hot-water-cooling-three-projects-making-it-work> |
| Idle power, CPU server (dual Xeon Platinum 8480+, SPECpower_ssj2008, January 2023) | 835 W at 100% load, 147 W active idle = 17.6%. Using this ratio for the 1 kW reference server is our *assumption* and likely a floor | *sourced*: <https://www.spec.org/power_ssj2008/results/res2023q1/power_ssj2008-20221207-01215.html> |
| Idle power, 8 × H100 node | 1.86 kW idle, 8.43 kW at the highest measured load (rated 10.2 kW) = 22.1% | *sourced*: <https://arxiv.org/pdf/2412.08602v2>; ratio *computed* |
| Power cycling, field evidence | only a 2007 blog by a power-management software vendor: 123 servers, 18,826 power cycles in 5 months, no power-supply or disk failure in two years. Old hardware, interested source; **not evidence of safety** | *sourced*: <https://vinaypai.blogspot.com/2007/09/yes-its-still-safe-to-power-off-and.html> |
| Temperature variability | a 2012 field study of air-cooled data centres found high variability in temperature affects node reliability more than average temperature; it does not measure power cycling | *sourced*: <https://www.cs.utoronto.ca/~bianca/papers/temperature_cam.pdf> |
| Published limit on server power cycles per year | none found (short search) | *unverified* |
| Server boot time (roughly 2 minutes at 72–128 GB RAM, 5 minutes or more on larger machines) | search snippet only | *unverified* |

## I. Hardware inputs

| Item | Value | Status |
|---|---|---|
| 2 × RTX 4090 rig | at least about 5,900 CHF, excl. cooling, plumbing, installation. Note: Salad would pay only one of the two cards | *assumption* (2,000 CHF host) on a *sourced* floor price: three cheapest eBay listings averaged 2,338 USD in June 2026, condition not stated (<https://gpupoet.com/gpu/learn/price/june-2026/nvidia-geforce-rtx-4090>) |
| New dual-RTX-5090 workstation (Ryzen 9 9950X, 256 GB, 1600 W supply, 360 mm liquid cooler) | 25,279.00 USD (21,214 CHF), ex sales tax; Swiss VAT and shipping not included | *sourced*: <https://www.newegg.com/gigabyte-gaming-desktop-pcs-dual-gpu-nvidia-geforce-rtx-5090-amd-ryzen-9-9950x-256gb-ddr5-4-tb-ssd-black/p/3D5-0073-00A57>. A 14,649 USD price for the same machine was seen in a search snippet only (*unverified*; the opened page shows 25,279) |
| RTX 5090 power | 575 W Total Graphics Power, 1000 W Required System Power | *sourced*: <https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/> |
| Wall power of that workstation | about 1.35 kW (2 × 575 W plus about 200 W), giving 15,715 CHF per kW | *assumption*, not measured |
| Refurbished Dell R740 (2 × Xeon Gold 6148, 256 GB, no drives) | read by the investigator at 2,196.31 USD; **not re-confirmed by the critic** (page returned 403) | *unverified* |
| Dell R740 power (2 × Xeon Platinum 8180, 192 GB, SPECpower_ssj2008) | 457 W at 100% load, 224 W at 50%, 52.3 W active idle | *sourced*: <https://www.spec.org/power_ssj2008/results/res2017q3/power_ssj2008-20170829-00780.html> |
| Refurbished R740 per kW | about 4,000 CHF per kW | *assumption* built on an unconfirmed price and a power figure from a different CPU configuration |
| New Dell R760, default configuration (one Xeon Gold 6430, 32 cores, 270 W; 64 GB; single 800 W supply) | from 14,239.01 USD (11,950 CHF); no price for a second processor shown | *sourced*: <https://www.dell.com/en-us/shop/productdetailstxn/poweredge-r760> |
| Dual-socket CPU server, 96 to 112 cores | 20,000 CHF | *assumption*, not a price |
| H100 server, per kW | about 20,000 to 33,000 CHF | *unverified* (our reading of a 250,000 to 400,000 USD range with no stated GPU count: <https://intuitionlabs.ai/articles/nvidia-ai-gpu-pricing-guide>); not used in any N result |
| Direct-to-chip liquid cooling, **data-centre scale, rack parts only** | 268,654 USD for 754 servers in 12 racks = 356.31 USD per server, 22,388 USD per rack; 7,339.12 USD per rack distribution unit, 110.67 USD per in-server cooler, 27.68 USD per tube pair, 334.00 USD installation per rack; 470,557.19 USD in total for a 1,200-node cluster incl. facility changes (392 USD per node, *computed*; node count not re-checked) | *sourced*: <https://www.energy.ca.gov/sites/default/files/2024-06/CEC-500-2024-061.pdf> (pp. 49–50) |
| Same report | "The normal life of a server is five years"; retrofitting existing servers with liquid coolers is "not an economically viable business model"; 12-year payback of the liquid cooling from energy savings | *sourced*: same PDF, pp. 47–50 |
| **Water-coupled compute heater installed in a single house, per server or per kW** | **no published price found** (vendors not contacted) | *unverified* absence; first question to DigitalHeat |
| Bitcoin room heaters (21energy Ofen 3) | 1,990 / 2,790 / 2,890 / 3,990 EUR including 20% VAT for 1.0 / 1.1 / 2.0 / 2.2 kW; room heaters, heat medium not stated | *sourced*: <https://startupvalley.news/de/ofen-3-bitcoin-21energy-heizung/> (1 Sep 2026) |
| Bitcoin-mining water heater | a headline names a 2,000 USD product; no power or tank size read, so no cost per kW | *sourced* headline only: <https://www.tomshardware.com/tech-industry/cryptomining/bitcoin-mining-water-heater-firm-says-its-usd2-000-product-can-rake-back-usd1-000-a-year-in-btc-and-claims-it-can-offset-up-to-80-percent-of-electricity-and-water-costs> |
| Service life 5 years, sold share (100 / 80 / 50%), 3,000 CHF installation adder per server | our choices; the five-year life in the CEC report is a data-centre figure and says nothing about resale value or consumer GPUs cycled on and off | *assumption* |

## J. Demo and measurement (round-1 probes)

All *computed* on one M3 Pro laptop with dummy or toy jobs (`python3 analysis/pause_resume_probe.py signals checkpoint throttle`, `... torch`), unless marked.

| Item | Value |
|---|---|
| SIGSTOP to process state T | median 3.3 ms (n=20) |
| Work during 20 stops of 1 s | 0 batches, 0.00 CPU s; batch sequence contiguous |
| Resume after SIGCONT | median about 8 ms to the next 7 ms batch |
| Cooperative stop / restart (dummy job, no model load) | about 140 ms / about 135 ms; 0 finished batches lost |
| Checkpoint after 10 SIGKILLs | readable 10 of 10, no batch computed twice; no fsync, power loss not tested |
| Toy PyTorch loop (cpu, mps) under SIGSTOP | survived 2 s and 10 s; real models and mlx untested |
| Laptop power telemetry | about 2 to 6 W idle, 22.4 to 22.8 W with 12 cores busy (*unverified* against a meter; 17 W power source) |
| Apple-published idle, display on, 230 V | 4.19 W (*sourced*: <https://www.apple.com/environment/pdf/products/notebooks/14-inch_MacBook_Pro_PER_Oct2023.pdf>); no published figure under load found |
| Power drawn by a SIGSTOPped job | not measured (*unverified*) |
| Real model load time on restart | not measured |


## K. Other round-2 plan text condensed in round 3 (verbatim)

### Admission rule (round 2)

- **Admission = dry run of the scheduler's own earliest-deadline-first step on the forecast**, not a capacity sum. A sum of capacity against a sum of work ignores "one server per job" and produced 166 missed jobs at N=8 even with a perfect forecast; the dry run gives 0 (*computed*, `python3 analysis/r2_deadline_sim.py`, reproduced by the critic). Cost: about 2.2 s per simulated year in plain Python (*computed* by the critic).
- **Guard band on the heating-day threshold, as a parameter** (2 K tested: a future day counts as a heating day only if its forecast mean is below 10 °C instead of the case's 12 °C). Checked on two years (2025 and 2024); numbers under "Missed deadlines".
- **Forecast input:** real archived forecasts from the Open-Meteo Previous Runs API (`models=ecmwf_ifs025`), saved as `analysis/r2_data/prev_ecmwf_ifs025.csv`. Conditions from the critic: the heating-day flag may use only values issued by decision time (the research script uses values up to 23 h fresher); state the +0.29 K warm bias; use the committed CSV, no live API call in the demo; do not present it as a house-level forecast error.
- A percentage safety margin on permits is not the tool: 5 to 30% does not reduce misses at N=6 (within seed noise) and cuts them by about two thirds at N=8 only at 30% (*computed*, same script, section 4).

*[superseded in round 3: dry-run run time is now 0.7–5 s per simulated year single-process, `analysis/r3_scope_extra.py` section C.]*

### Servers per house table (round 2)

| | N = 6 | N = 8 |
|---|---|---|
| Coverage (*computed*, `analysis/r1_servers_choice.py`) | 79.6% | 92.9% |
| Dumped | 0 kWh | 0 kWh |
| Utilisation | 59.1% | 51.8% |
| Run hours of the last server, case assumptions | 3,796 h/yr (6th) | 2,933 h/yr (7th), 2,281 h/yr (8th) |
| Run hours of servers 7 and 8, combined realistic run (*computed* by the round-2 critic from `analysis/r2_realism.py`) | | 3,546 and 3,236 h/yr |
| Break-even CHF per server-hour | 0.2261 | 0.2261 (identical for any N by construction while nothing is dumped; it cannot decide between 6 and 8) |
| Missed deadlines, forecast error only (see "Missed deadlines") | both below 1%, near zero with the guard band | N=8 is worse in every variant |
| Server starts per year, plain follow rule (*computed*, `python3 analysis/r2_realism.py`) | 1,732 | 2,208 |
| Server starts per year, cap + 8 kWh band (round-1 band rule) | 379 | 891 |
| Worst case: every paused server left powered all year at 17.6% idle (break-even) | 0.2659 | 0.2814 |

### Run policy (round 2)

- **Follow heat, never dump by default**: each hour run as many whole servers as demand + free tank space can absorb (`follow` in `analysis/baseline_sweep.py`).
- Tank (35 kWh) is charged ahead of cold hours; with a lossless tank greedy filling is already optimal for heat.
- **Dumping threshold, not a default:** under the case constants and with hardware cost excluded, a heat-matched server-hour costs 0.2261 CHF net and a dumped one 0.3325 CHF (*computed*). Dumping covers its own electricity only above 0.3325 CHF per server-hour. Caveats: "least heat dumped" is the jury's first scheduling criterion, and 0.3325 is a household retail tariff, so a data centre runs the same dumped hour cheaper.
- **Adopted as scheduler-core parameters (used by the yearly balance too, never demo-only): at most one server when there is no space heating ("cap") + an 8 kWh tank band.** The cap is the part that does the work: a band without the cap makes cycling worse (2 kWh band: 2,427 / 2,926 starts).
- Summer: ~0.6 server-equivalents for hot water. Work without a permit is not accepted at this house, or goes to a summer heat-sink site (outside the balance, stated as such).

### The two job types (round 2)

Roles swapped in round 1: transcription is the laptop job because `mlx_whisper` and the `whisper-large-v3-turbo` weights are already on one laptop and `sentence_transformers` is not (*computed*, read-only checks; **`mlx_whisper` has not been run, only this one laptop was checked**).

| | J1: transcription of a fixed audio set | J2: offline LLM text generation |
|---|---|---|
| Runs on our laptop | yes, measured whole (uses the laptop GPU; say so) | no, benchmark row |
| Size | defined by content first (N minutes of audio, to be fixed Saturday); runtime and energy measured, then scaled | 4 server-h = 4 kWh (*assumption*) |
| Interruptible | yes, checkpoint per audio file | yes, checkpoint per batch |
| Deadline | 24 h (*assumption*) | 168 h (*assumption*) |
| Source of throughput | own measurement Saturday (placeholder) | MLPerf Inference v6.1, datacenter closed, ID 6.1-0032 (Dell, 2 × Xeon 6787P, no accelerator): llama3.1-8b Offline 1,227.99 tokens/s (*sourced*: local copy `data/raw/mlperf_inference_v6.1_summary.xlsx`; upstream not re-checked) |
| Mix | 50/50 by work (*assumption*) | |

- Job sizes are our assumptions. The Alibaba GPU trace (median instance run-time 23 min, P90 4.5 h; *sourced*: <https://www.usenix.org/system/files/nsdi22-paper-weng.pdf>) is inspiration for "one short, one long" only, not an anchor. Its per-GPU task rate is not comparable with jobs per 1 kW server.
- **Scaling laptop → 1 kW server** (*assumption*, no source): server-hours per job = laptop Wh per job ÷ 1000, stating gross or net-of-idle energy. Error possibly several-fold either way; it fixes heat only and says nothing about compute delivered per server-hour. Cross-check before the draft against the throughput file in `data/raw`.
- If system 6.1-0032 drew exactly 1 kW (*unverified*; no power column in the file), one J2 job would be about 17.7 million output tokens (*computed*).
- **Jobs per day is a contract size we choose, not market data** (*assumption*). Job sizes, deadlines, the 50/50 mix, Poisson arrivals, the offer levels and an always-available partner site are assumptions (the simulation used J1 = 0.5 server-h / 24 h, J2 = 4 server-h / 168 h).
- **Sold share is a visible switch; coverage is always labelled "at X% sold".** Default for an unsold permit hour: the server stays off (break-even stays 0.2261 CHF, coverage falls). Unpaid filler work is one comparison line only: under case prices each filler hour loses 0.2261 CHF.
- **Missed deadlines, dashboard definition:** *accepted jobs not finished by their deadline at any site ÷ accepted jobs whose deadline fell in the year*. Always printed with the accepted share of offers, the forecast source, and beside it the missed share **as % of accepted work** (the per-job share moves 0.15 to 1.0% with the assumed mix), plus a line by job type. Moved share and hand-off delay are shown only if a partner site is built.
- **Never quote 0%.** The dashboard figure must come from the team's own scheduler, not be copied from `analysis/r2_deadline_sim.py`.

*[superseded in round 3: J1 now runs (25–27× real time); scaling rule (i) with measured energy; J2 efficiency from MLPerf v5.1 5.1-0062; the MLPerf whisper unit warning was deleted (settled: the summary column is tokens/s).]*

### Pause/resume demo (round 2)

- **Same code, defined:** one pure decision module (no clock, I/O, subprocess or sim/live flag) imported by a yearly driver and a live driver. The live day starts from the yearly run's state snapshot for 00:00 of that date. A test asserts the live day's 24 decision-trace lines equal the yearly trace for that date; both drivers print the SHA-256 of the core file.
- That test is true by construction while progress is modelled, so the minimum also includes: **a check that the real process is in state T after each PAUSE and running after each RESUME**, and a plain statement of whether the real job's progress ever reaches the scheduler or the balance.
- **Mechanism:** SIGSTOP/SIGCONT on the job's own process group as the live-demo primary; J1 writes an atomic checkpoint (temp file + `os.replace`) after every batch in all modes; cooperative stop + restart from checkpoint behind one flag. Worker-count throttling is dropped (outlook only).
- **SIGSTOP stops the work, not the heat.** The yearly balance counts a paused server as 0 kW; a stopped process on a powered server still draws idle power (17.6% and 22.1% of full power on the two machines we have sources for, see "Realism switches"). Checkpoint-and-restart is the form that matches the heat model, so it must be exercised in a test and shown at least in the recording, and the pitch says: "the laptop freezes the process where a real unit would checkpoint and power down."

### Pitch wording fixed in round 2

- **Break-even is always shown twice, together:** 0.2261 CHF (official case formula, heat value credited to the operator; this stays the reference-house key figure) and 0.3325 CHF (homeowner gets the heat free). The balance gets one parameter "share of heat value paid to the operator" (0 to 1).
- **Realism sentence:** "With tank losses and an electric hot-water booster, June-to-August coverage drops by about 20 points if the server loop reaches 50 °C, and the break-even price rises by under 0.01 CHF per server-hour." Name the cost convention on the slide (see "Realism switches").
- **Host income, not renter price:** a host receives about 80% of the listed price; say "host rates", and say that the lowest job rate on one marketplace is below our break-even.
- **Not in any N result or pitch number:** Vast.ai's advertised H100/H200 host range (vendor's claim, above a renter price found in round 1; an 8-GPU 10.2 kW server is not a house installation).
- **First two questions to DigitalHeat on Saturday:** (1) installed cost per water-coupled server in a house; (2) who is paid for the heat. These move the result more than any further web search. Further questions for the same conversation are listed under open risk 2.
- Before any slide use, re-read by eye the two web pages behind the forecast figures (Open-Meteo Previous Runs docs, the weather vendor's verification page); they were read through a summarising fetch tool, and the lead time of the vendor's 2018 table is not confirmed.

*[superseded in round 3: four questions for DigitalHeat, see overnight.md "Still unverified".]*

### Break-even support (round 2)

- Support for "operator pays, household gets the heat" as a real arrangement: a person signing forum comments as a representative of a UK compute-heating firm writes "We pay for all electricity used by the unit" and that units "put between 180W and 200W into the tank when at full power" (*sourced*: <https://forums.theregister.com/forum/all/2023/01/12/heata_offers_free_hot_water/>; affiliation inferred).
