# Round 4: plan detail moved out of overnight.md

Text moved **verbatim** out of [../overnight.md](../overnight.md) by the round-4 rewriter so the plan sections stay at about 260 lines. Nothing here is new. Status labels as in overnight.md. Where round 4 superseded a line, the heading says so; the current figures are in overnight.md and the round-4 research files ([tank temperatures](r4-tank-temperatures.md), [demand and headline](r4-demand-headline.md), [reference machine](r4-reference-machine.md)) and their critiques.

## A. Q&A answers as written after round 3 (superseded in round 4 for questions 1, 2, 4 and 5)

**6 hardest Q&A questions**
1. *"What does the operator actually earn?"* Unknown, and we say so. At public batch prices of 21 Nov 2026 the transcription one 1 kW server-hour does is listed at 6.7 / 11.2 / 25.2 CHF (low / central / high, laptop efficiency; *computed*, `analysis/r3_income.py`). Electricity minus heat is 2–5% of that; with hardware about 18–30% (assumed hardware prices). GPU marketplaces pass about 80% of the renter price to hosts (*sourced*), and none was found that pays a server which goes offline on a heat signal. The operator's share is the first question for DigitalHeat.
2. *"Why 6 servers, not 1 or 8?"* Break-even per server-hour is the same for any N, so N trades coverage against utilisation: 8 adds 13 points of coverage for 7 points less utilisation. With hardware at 6,000 CHF/kW and a 5-year life, 6 servers need 0.54–0.64 CHF net per run hour to pay back (*computed*, `analysis/r2_fleet_economics.py`). One vendor sizes at 5–20% of design thermal load (*sourced*; 0.6–2.5 servers for this house per the round-3 critic); at N=1/2 coverage is 19.5% / 32.7% and utilisation 87.1% / 73.0% (*computed*).
3. *"SIGSTOP freezes the job, but the server still makes idle heat."* The balance models power-down; a 15-minute restart (*assumption*) adds 0.0008–0.0023 CHF per server-hour with cap + band (*computed*, `analysis/r3_policy_check.py`). If paused servers stayed on at 17.6% idle, break-even would rise to 0.2659 / 0.2814 and nothing would be sold in summer. That worst case is in our numbers.
4. *"Hot water must be stored at 60 °C. Your loop gives 50 °C."* With tank loss (2.80 kWh/day, *sourced*) and an electric booster, June–August coverage drops about 20 points (loop and setpoint temperatures are *assumptions*). Break-even rises 0.003 to 0.013 CHF depending on who pays for the booster.
5. *"Show me missed deadlines with a forecast that can be wrong."* Admission uses archived ECMWF forecasts (day-1 RMSE 1.16 K, day-7 2.85 K), execution the actual weather: roughly 0.1–0.6% missed a year without a guard band, 0.002–0.026% with the 2 K guard (*computed*). Forecast and truth come from the same model family, so errors are understated; server failures and runtime overruns are not modelled.
6. *"What is new here?"* Heat-following compute, stop-at-full-tank, batch work and per-task reused-heat figures are prior art (2011, 2018 and 2021 papers; current vendors), and so is admission against forecast capacity with deadlines (solar- and carbon-aware scheduling, 2011 and 2021). What we did not find: the house's forecast heat demand plus tank as the capacity curve, refusal at intake, and a published missed-deadline share beside coverage and dumped heat for one reproducible house-year. Be ready for "a virtual capacity curve with heat in place of carbon".

## B. The two job types, round-3 table (superseded: J1/J2 now sized on the round-4 reference server)

### The two job types

| | J1: transcription of a fixed audio set | J2: offline LLM text generation |
|---|---|---|
| Runs on our laptop | yes: `mlx_whisper` large-v3-turbo on the M3 Pro, 25–27× real time on synthetic TTS audio, model load included, two trials (*computed*, `python3 analysis/r3_whisper_energy_probe.py`) | no, benchmark row |
| Energy | 1.3–1.5 Wh per audio-hour gross (two trials, 35–38 W mean whole device, battery-controller accumulators, not checked against a meter; *computed*, same script) | 1 kW slice of MLPerf v5.1 5.1-0062 (8 × B200, fp4): 56.07 million output tokens per kWh (*computed*, `python3 analysis/r3_mlperf_power.py`) |
| Size in the simulation | 0.5 server-h = one 333-audio-hour batch at 1.5 Wh per audio-hour; the demo runs a slice | 4 server-h (*assumption*) |
| Interruptible | yes, checkpoint per audio file | yes, checkpoint per batch |
| Deadline | 24 h (*assumption*) | 168 h (*assumption*) |
| Mix | 50/50 by work (*assumption*) | |

- **Scaling rule** (*assumption*): the 1 kW server uses the same gross energy per audio-hour as our laptop; **J1 jobs per server-hour = 1000 ÷ (P × t)**, P = gross laptop watts, t = laptop hours per J1 job. This implies a rack server as efficient as an Apple laptop GPU (laptop hardware at roughly 52,000 CHF/kW, *assumption*).
- **Check line:** the 8 × B200 MLPerf whisper-large-v3 run uses about 0.37–0.50 Wh per audio-hour on a 1 kW slice of a 7.6 kW machine (*computed*, `r3_mlperf_power.py`). Published machines give an illustrative 150–2,860 audio-hours per kWh (two anecdotal posts and one MLPerf run; not a measured bound).
- Keep J1 = 0.5 server-h in the simulation. Redefining J1 by content multiplies the job count ~33× and changes the missed-deadline %: extra build scope.
- **J1 (laptop efficiency) and J2 (B200-slice efficiency) are not one machine.** Never combine them in a headline without that label. CPU-only comparison: MLPerf v6.1 ID 6.1-0032 (2 × Xeon 6787P), llama3.1-8b Offline 1,227.99 tokens/s (*sourced*: local copy `data/raw/mlperf_inference_v6.1_summary.xlsx`).
- **Jobs per day is a contract size we choose, not market data** (*assumption*; so are Poisson arrivals, offer levels and an always-available partner site). **Sold share is a visible switch; coverage is always labelled "at X% sold".** Default for an unsold permit hour: the server stays off. Unpaid filler work is one comparison line only.
- **Missed deadlines, dashboard line:** *accepted jobs not finished by their deadline ÷ accepted jobs whose deadline fell in the year*, always as "x of y accepted jobs", with the accepted share, the **offer scenario** (saturating vs heat-shaped: the accepted share runs from 49% to 95% between them), the forecast source, and the share of accepted work. **Never a bare 0%.** The figure comes from the team's own scheduler.

## C. Computing income, round-3 wording (superseded: share needed now on the reference server; 0.3375 at 67% sold dropped from the headline)

### Computing income (round 3)

Never a bare number. Wording source: [research/r3-machine-and-income.md](r3-machine-and-income.md) section 8, with the critic's changes below.
- **Lead line, "share needed":** electricity minus heat is 2–5% of the list value of the work at public batch prices before hardware, about 18–30% with hardware at assumed prices. Say "list value of the work", "scenario", "share needed"; avoid "revenue", "earns", "market price of our compute".
- **CHF scenario second**, with two visible switches: **operator share** of list price (default 20%, *assumption*) and **sold share** (default 67%, *assumption*). The tile names the machine efficiencies (J1 laptop, J2 B200 slice), says "assumes every permit hour is filled with paid work (unlimited demand)", and gives provider, tier and date of each price.
- Print the case break-even at the chosen sold share next to 0.2261, with the same s as the income line (0.3375 CHF at 67% sold).

## D. Servers per house: round-2 payback line

- Payback: by 5-year simple payback at sourced consumer-GPU host rates **no server pays back (N\* = 0)**; six servers need 0.54–0.64 CHF net per run hour, eight 0.75–1.00 CHF (*computed*, `python3 analysis/r2_fleet_economics.py`, section 6). Mixed fleet dropped.

## E. Demo days, round-3 adopted policy (superseded: round-4 dates under the shaped100 headline with the demo-day pin)

- **Demo days, adopted policy** (*computed*, `python3 analysis/r3_scope_extra.py`, seed 1 unless stated):
  - **N=6, January:** the heat signal never pauses (permits = 6 every hour in January 2025). At job level, servers with a permit still sit idle for lack of admitted work on 9 January days, including 2025-01-13. The screen shows **job-level** numbers so it matches the yearly balance.
  - **N=6, interrupted job = the July pause of slot 1:** 2025-07-19 (saturating) or 2025-07-22 (heat-shaped), pause at data-hour 04:00 (05:00 CEST), resume 20:00 (21:00 CEST). With the 8 kWh band other seeds give 3–6 days on other dates, so **a demo-day finder reads date and hours from the final run and seed**. With a 4 kWh band, seed 1 has 16 July days common to both offer scenarios.
  - **N=8:** 2025-01-25, slot 7, pause 14:00, resume 19:00 in every variant tested (robust).
- **Timing** (*assumption*, to rehearse): July at 1.5 s per simulated hour (pause at 6.0 s, resume at 30.0 s; frees 24 s against 2.5 s/h). N=8 January at 1.5 s/h: 21.0 s and 28.5 s. A shoulder-month day is a Q&A example only. Launch: `caffeinate -dis`, proper charger, `HF_HUB_OFFLINE=1`, one wifi-off rehearsal.

## F. Adopted policy with deadlines and finite demand (round 3)

*Computed* by `python3 analysis/r3_policy_check.py`, section 1, 3-seed means, 2025. Adopted = cap + 8 kWh band, archived `ifs025` + 2 K guard, restart-aware dry run, 15-min restart inside execution (the plan now moves restart to an accounting line). Offer levels are *assumptions*.

| Policy, offers | Coverage N=6 / N=8 | Dumped | Utilisation | Starts/yr | Accepted jobs | Missed, % of accepted | Break-even CHF |
|---|---|---|---|---|---|---|---|
| Adopted, saturating | 79.2% / 92.9% | 0 | 58.9% / 51.7% | 427 / 905 | 54.8% / 48.9% | 0.003% / 0.026% | 0.2269 / 0.2275 = 0.2261 + assumed restart, no hardware |
| Adopted, heat-shaped (100%) | 74.0% / 86.7% (0.3–0.6 points of it is restart heat without work) | 0 | 55.0% / 48.3% | 756 / 1,343 | 94.6% / 93.6% | 0.005% / 0.005% | 0.2276 / 0.2284 (restart only) |
| Minimal: follow + perfect-forecast admission, saturating | 79.2% / 92.8% | 0 | 58.9% / 51.7% | 1,788 / 2,223 | 52.5% / 45.1% | 0 by construction | 0.2261 (structural) |

- **Absolute:** 0–12 missed jobs a year out of about 31,700–38,900 accepted; one of 12 runs (N=8, heat-shaped, seed 3) had exactly 0 (*computed*, re-run by the critic).
- **Rule fights:** executor with band + dry run assuming plain follow: 0.720% / 0.591% missed (saturating), 0.226% / 0.317% (heat-shaped). Restart in execution with a restart-unaware dry run: 0.868% / 0.875% even with a perfect forecast. A restart-aware dry run lowers misses by 0.139 / 0.100 points (saturating).
- **Cap + 8 kWh band** (consistent dry run): missed −0.002 to +0.004 points, coverage −0.06 to 0.00 points, starts −1,292 to −1,366 a year. Break-even cannot change in this model. **Hold rule:** coverage −0.02 to −0.13 points, missed −0.002 to +0.003, break-even −0.0001 to −0.0004 CHF, 37–284 fewer starts → cut.
- **Forecast:** archived `ifs025` instead of persistence lowers misses by 2.6 / 3.8 points (saturating) and 0.44 / 0.56 (heat-shaped), shaped coverage +1.1 points. A 2 K guard takes misses from 0.158% / 0.495% to 0.002% / 0.021% (saturating). The forecast is from the same model family as the reference weather, so errors are understated. **No admission:** 2.6% / 2.9% missed under heat-shaped offers. (35.4% / 39.6% under saturating offers only reflects offers set to full peak capacity all year.)
- **Restart as an accounting line** reproduces the in-scheduler break-even within 0.0003 CHF (seed 1; *computed*, `python3 analysis/r3_scope_extra.py`, section B); it leaves out +0.003 to +0.011 points of misses and the restart-heat coverage artefact.

## G. Missed deadlines, round-2 runs (no guard band) — summary

*Computed* by `python3 analysis/r2_deadline_sim.py` and round-2 critic checks (full table and forecast-error sources: [r3-plan-detail.md](r3-plan-detail.md) section E). Saturating offers, no guard band: roughly 0.1–0.6% of accepted jobs a year (2025, 2024), 0.5–1.8% in April, May and October (12 °C heating-day rule, a handful of days); with the 2 K guard below 0.02%. Forecast error, archived ECMWF IFS 0.25°, Basel 2025: day-1 RMSE 1.16 K, bias +0.29 K; day-7 RMSE 2.85 K.

## H. Machine, prices and list value of the work (round 3)

Details, commands and price pages: [research/r3-machine-and-income.md](r3-machine-and-income.md); critic's re-checks in [its critique](r3-machine-and-income-critique.md).

| Item | Value | Status |
|---|---|---|
| MLPerf Inference v5.1, 8 × B200: 5.1-0061 whisper Offline; 5.1-0062 llama3.1-8b Offline (fp4) | Power_Result 7,636.49 W; 9,436.05 W and 146,960 tokens/s. Only 24 of 1,448 rows carry power (*computed*) | *sourced*: <https://raw.githubusercontent.com/mlcommons/inference_results_v5.1/main/summary_results.json> |
| Energy on a 1 kW slice of those machines | whisper-large-v3 about 0.37–0.50 Wh per audio-hour; llama 56.07 million output tokens per kWh (input tokens not counted) | *computed*, `python3 analysis/r3_mlperf_power.py` |
| Our laptop (M3 Pro), J1 | 25–27× real time; 35–38 W; idle 2.50 W; 1.3–1.5 Wh per audio-hour gross → about 670–760 audio-hours per 1 kW server-hour | *computed*, `python3 analysis/r3_whisper_energy_probe.py` (two trials, synthetic audio) |
| Transcription, USD per audio-hour (pages opened 21 Nov 2026) | DeepInfra whisper-large-v3-turbo 0.012 (standard, 0.00020 per minute); Groq turbo 0.04, Batch API 50% lower (24 h–7 days) → 0.020; Together Whisper Large v3 0.0015 per minute, batch 0.045 or 0.090 (toggle state unresolved; 24 h best effort) | *sourced*: <https://deepinfra.com/openai/whisper-large-v3-turbo>, <https://console.groq.com/docs/speech-to-text>, <https://console.groq.com/docs/batch>, <https://www.together.ai/pricing>, <https://docs.together.ai/docs/inference/batch/overview> |
| Llama 3.1 8B, USD per million input / output tokens | DeepInfra (Instruct-Turbo) 0.02 / 0.04; Amazon Bedrock US East on demand 0.22 / 0.22, batch 0.11 / 0.11 | *sourced*: <https://deepinfra.com/pricing>, <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json> |
| J2 billed at 6 input tokens per output token | changes J2 central 4× and high 7×; show wherever a J2 price appears | *assumption* |
| **List value per 1 kW server-hour**, low / central / high | J1 alone 6.7 / 11.2 / 25.2 CHF; 50/50 mix 4.3 / 9.4 / 30.7 CHF (J1 laptop efficiency + J2 B200-slice efficiency, not one machine) | *computed*, `python3 analysis/r3_income.py`, section 2 |
| Electricity minus heat as share of list value | 2–5% before hardware; about 18–30% with hardware (assumed hardware prices) | *computed*, same, sections 2 and 7 |
| Full cost (electricity − heat + hardware, 5 years, N=6) as share of J1 central list value | laptop-class (2,000 CHF per 38.22 W laptop = 52,329 CHF/kW, 2.02 CHF per run hour; a reductio, not a design): 20% (30% at 67% sold). 2 × RTX 4090 at 6,000 CHF/kW: 18% (27%), E = 6.7 from mismatched blog runs. The agreement is a coincidence of assumptions | *computed*, same, section 7; prices, life, E *assumption* / *unverified* |
| CPU-only LLM (6.1-0032) at 0.04 USD per million output tokens | 0.148 CHF per server-hour, below the 0.2261 break-even, if the server draws 1 kW (*assumption*) | *computed* (1,227.99 tokens/s × 3,600 × 0.04e-6 × 0.8392) |
| Work if every permit hour were filled (unlimited demand assumed), 50/50 | N=6: 31,067 server-h = 31,067 J1 batches (10.4 million audio-hours, ~28,000 a day) + 3,883 J2 jobs; N=8: 36,281 server-h, 36,281 J1 + 4,535 J2. No buyer named | *computed*, `r3_income.py`, section 5 |
| Share needed (unsold hours still run on filler; 20% of list reaches the operator, *assumption*) | income covers electricity minus heat from about 12% sold (central; 26.3% low, 3.7% high) | *computed*, same, section 5C |
| **Scenario only** (operator share 20%, sold share 67%, unlimited demand, J2 at B200-slice efficiency) | 18k / 39k / 128k CHF a year at N=6; 21k / 46k / 149k at N=8 | *computed*, same, section 5B |

*Round-4 note:* the two-machine list value (J1 laptop + J2 B200 slice) and the laptop-class / 2 × RTX 4090 rows are superseded by the reference-server table in overnight.md; the price sources above are still the ones used by `analysis/r4_machine.py`.

## I. Host income (round 2) — summary

Full tables (Salad and Vast.ai host rates, renter prices, CPU-only): [r3-plan-detail.md](r3-plan-detail.md) section F. A host gets about 80% of the listed price (Salad *computed* from <https://salad.com/pricing> and its data feed; Vast.ai *sourced*). Salad pays one GPU per machine. No marketplace was found that pays a server which goes offline on its own heat signal; no occupancy figure found.
- Salad RTX 4090 host rate per 1 kW of wall power: average about 0.30–0.35 CHF per sold hour (*unverified*, wall power assumed). Lowest job rate at most 0.215 CHF per kW-hour: below 0.2261 (*computed*, `analysis/r2_fleet_economics.py`).

## J. When the model does not pay off

- **Operation only:** below **0.2261 CHF per sold server-hour** (heat credited, every run hour sold, server off when unsold); below **0.3325 CHF** if the homeowner gets the heat free (*computed*).
- **At the lowest job rate of the one marketplace with published host rates** (at most 0.215 CHF per kW-hour), or when the only work is LLM generation on a CPU-only server at the lowest price (0.148 CHF per server-hour).
- **When less than about a fifth to a third of the list price of the work reaches the operator**, with assumed hardware prices, a 5-year life and measured E (*computed*, `analysis/r3_income.py`, section 7); and **when paid demand does not fill the heat-permit hours** (all income figures assume it does).
- **Including hardware, 5-year simple payback:** at sourced consumer-GPU host rates no server pays back; six servers need 0.54–0.64 CHF net per run hour at 6,000 CHF per kW, eight 0.75–1.00 CHF (*computed*, `analysis/r2_fleet_economics.py`, section 6).
- **Worst case, servers left powered while paused:** no summer sales, break-even 0.2659 / 0.2814 (*computed*, `analysis/r2_realism.py`). Air-cooled servers that cannot serve hot water: coverage 70.5% / 81.7%. More conditions: [r3-plan-detail.md](r3-plan-detail.md) section G.

*Round-4 note:* the hardware lines above use round-2/3 hardware assumptions; the current lines use the reference server.

## K. Realism switches — "case assumptions" against "with tank loss and booster"

All *computed* by `python3 analysis/r2_realism.py`. Inputs: tank loss 2.80 kWh/day (*sourced*, one manufacturer), storage setpoint 60 °C (*sourced*), loop preheat to 50 °C, cold water 10 °C and booster COP 3 (*assumptions*). Detail and sources: [r3-plan-detail.md](r3-plan-detail.md) section H.

| | Coverage N=6 | Coverage N=8 | Break-even N=6 | Break-even N=8 |
|---|---|---|---|---|
| Case assumptions | 79.6% | 92.9% | 0.2261 | 0.2261 |
| Tank loss 2.80 kWh/day only | −0.3 points | −0.3 points | +0.0030 | +0.0031 |
| Loss + electric booster 50 → 60 °C, booster outside the model | 77.5% | 90.5% | 0.2292 | 0.2293 |
| Loss + electric booster, charged to the servers, heat credited | 77.5% | 90.5% | 0.2348 | 0.2341 |
| Loss + heat-pump booster at COP 3, charged and credited | 78.7% | 91.9% | 0.2310 | 0.2308 |

- **June to August coverage:** −20.0 points with the electric booster, by construction from the assumed temperatures (11 at a 55 °C setpoint, 30 at a 45 °C loop; −6.7 with the heat pump). **Break-even rise, loss + electric booster:** +0.003 CHF (booster outside), +0.008 to 0.009 (charged and credited), +0.011 to 0.013 (not credited).

*Round-4 note:* the 50 → 60 °C electric-booster rows are replaced by layout A (`analysis/r4_tank_layout.py`); the 60 °C setpoint survives only as the warm-held-pipes sensitivity (74.0% direct hot-water share). The heat-pump booster row uses the round-2 50 → 60 °C layout.

## L. Lines moved in round 4 for length (verbatim)

From "Dashboard and pitch" and "Pitch wording":

- **Not built:** heat-flex tariff (used heat is worth at most 0.1064 CHF per server-hour; *computed*); neighbourhood / partner-site view (one outlook sentence: a partner running flat 24/7 has no idle servers to take moved jobs).
- **Utility line:** by the case constants the servers draw 3.125× the electricity a heat pump would need for the same heat (31,067 vs 9,941 kWh at N=6; *computed*, `analysis/r3_creativity_usability.py`); always add "that electricity also produces the compute being sold".
- **Q&A additions (round 3):** the house's year-round hot water (15.8 GJ/yr) is 3.2% of one vendor's 500 GJ/yr hot-water minimum (*computed* by the round-3 critic); that vendor recommends sizing at 5–20% of design thermal load (*sourced*: <https://leaf.cloud/leafsites/>); a Dutch e-radiator company went bankrupt in 2019 because homes do not need 24×7 heat (*sourced*: <https://web.archive.org/web/20231201233210/https://www.datacenterdynamics.com/en/analysis/making-the-most-of-your-waste-heat/>).

From "Break-even: who gets the heat" (*computed*, `python3 analysis/r2_fleet_economics.py`, sections 1 and 9):

| Case | Break-even CHF per sold server-hour |
|---|---|
| 80% sold, **unsold hours still run at 1 kW** | 0.283 (heat credited) / 0.416 (heat free) |
| 50% sold, unsold hours still run | 0.452 / 0.665 |

From "Yearly balance — unlimited jobs" (*computed*, `python3 analysis/baseline_sweep.py`):

| Servers (follow policy) | Coverage | Dumped | Utilisation | Server-h/yr | Electricity CHF | Heat value CHF | Break-even CHF/server-h |
|---|---|---|---|---|---|---|---|
| 4 | 58.0% | 0 | 64.7% | 22,654 | 7,532 | 2,410 | 0.2261 |
| 10 | 99.3% | 0 | 44.2% | 38,749 | 12,884 | 4,123 | 0.2261 |
