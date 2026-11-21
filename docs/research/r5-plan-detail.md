# Round-5 plan detail (moved out of docs/overnight.md)

Text moved verbatim from `docs/overnight.md` by the round-5 rewriter. Nothing here is new. Links inside moved text are relative to `docs/` (where they were written). Two kinds of content:

- **Section A, still valid, moved for length:** may be quoted with its status label.
- **Section B, superseded round-4 wording:** replaced in round 5 (see the Round 5 entry in `docs/overnight.md` and the r5 research files). Kept for audit only; **do not quote**.

## A. Still valid, moved for length

### A1. Reference server table rows (round 4; *computed*, `python3 analysis/r4_machine.py`, on the round-4 air-coil cost basis)

| Item | Value | Status |
|---|---|---|
| CHF needed per sold server-hour, N=6 | 1.53 (5 y; 1.73 at 5%) / 1.04 (8 y; 1.23) | *computed*, same |
| Payback at operator share 20%, 67% sold, N=6 | 3.9 y central price / 8.1 y low (4.4 / 10.6 at 5%); N=8 low 12.3 y at 5% | *computed*, same |
| Volume at unlimited demand, N=6, half J1 | about 60,000 audio-hours a day per house; 80 Mbit/s average, about 135 Mbit/s at the peak hour (271 if all J1) at an assumed 32 kbit/s codec | *computed*, same, section 3 |

### A2. Realism-column sources (round 4)

- Sources: MuKEn (per suissetec, May 2011): new or replaced floor heating ≤ 35 °C supply, other new or replaced emitters ≤ 50 °C at the lowest outdoor temperature; existing systems not bound (*sourced*: <https://merkblatt.suissetec.ch/de-CH/HEIZ111/file/HEIZ111.pdf>). Radiator design pairs 70/55, 55/45, 35/28 and the EN 442 formula (*sourced*: <https://www.sbz-monteur.de/sites/default/files/sbzm_pdf/file_226319.pdf>). Underfloor exponent 1.1 is an *assumption*. Round-2 booster rows: [r4-plan-detail.md](research/r4-plan-detail.md) section K. Round-1 pause probes (SIGSTOP to state T median 3.3 ms; checkpoint survives 10 SIGKILLs): [r3-plan-detail.md](research/r3-plan-detail.md) section J. Host income (round 2): [r4-plan-detail.md](research/r4-plan-detail.md) section I.


### A1b. Further table rows moved for length (round 4, still valid; status as marked in the source tables)

Servers per house (`docs/overnight.md` table, *computed*):

| | N = 6 | N = 8 |
|---|---|---|
| Run hours of the last server, case assumptions | 3,796 h/yr (6th) | 2,933 h/yr (7th), 2,281 h/yr (8th) |
| Worst case: every paused server left powered at 17.6% idle (break-even) | 0.2659 | 0.2814 |

Headline comparison (*computed*, `python3 analysis/r4_headline.py`, section 4 unless marked):

| Comparison | Coverage N=6 / N=8 | Accepted | Missed |
|---|---|---|---|
| `shaped120` / `shaped150`, seed 1 (inline command, research file section b) | 76.46% / 89.72%; 78.23% / 91.80% | 81.7% / 82.8%; 64.0% / 65.4% | N=8: 12; 13 |
| `shaped50` (half rate) | 37.99% / 44.59% | — | — (3,000–3,400 starts) |

Reference server and installed cost:

| Item | Value | Status |
|---|---|---|
| Throughput | 6.1-0017 (Cisco UCS X210 M8 blade + X580P node, 2 × Xeon 6747P, 4 GPUs): whisper 61.104 samples/s (fp16), llama3.1-8b 9,518.66 output tokens/s (fp4). 6.1-0056 (HPE DL345 Gen12, 2U, 1 × EPYC 9375F, 4 GPUs): whisper 58.08 samples/s, no llama result | *sourced*: MLPerf v6.1 loadgen logs, URLs in the research file section 2.1 |
| Job mix extremes, 5 y, N=6 (round-4 basis) | LLM only 31.7% (35.8% at 5%); transcription only 6.4%. Same basis in round 3: mix 24.0%, J1-only 20% | *computed*, `r4_machine.py`, section 4 |

### A3. Break-even table (round 4, still valid)

*Computed* by `python3 analysis/r2_fleet_economics.py` (sections 1 and 9) unless marked.

| Case | Break-even CHF per sold server-hour |
|---|---|
| Official case formula: heat credited to the operator, every run hour sold (N = 1, 6, 8) | **0.2261** |
| Homeowner gets the heat free | **0.3325** (difference: 3,306 CHF/yr at N=6, 3,860 at N=8 with unlimited demand) |
| 80% / 50% sold, unsold hours still run: [r4-plan-detail.md](research/r4-plan-detail.md) section L | 0.283 / 0.452 (heat credited) |
| 67% sold, unsold hours still run (*computed*, `python3 analysis/r3_income.py`, section 5B; not a headline figure) | 0.3375 (heat credited) |
| Any sold share, **server stops when unsold** (the headline convention) | stays 0.2261 / 0.3325; coverage falls instead |

- Operator-pays-electricity is a real arrangement: one forum post ([r3-plan-detail.md](research/r3-plan-detail.md) section K) and current vendors (creativity research file).

### A4. Demo timing and J1 energy protocol (round 4, still valid)

- **Timing** (*assumption*, to rehearse): 1.5 s per simulated hour, so a pause or resume shows at data-hour × 1.5 s (N=8 January: 21.0 s and 28.5 s); recompute the July seconds from the final date. A shoulder-month day is a Q&A example only. Launch: `caffeinate -dis`, proper charger, `HF_HUB_OFFLINE=1`, one wifi-off rehearsal.
- **Energy for J1:** `analysis/r3_whisper_energy_probe.py` (battery-controller accumulators `AccumulatedSystemLoad` / `SystemLoadAccumulatorCount`), at least 5 minutes, plugged in, fixed brightness, nothing else running, figure integrated over the whole span, gross and net of idle. **Do not use the per-minute `SystemPowerIn` snapshot** (implausibly low readings). Older detail: [r3-plan-detail.md](research/r3-plan-detail.md) section C.

## B. Superseded round-4 wording (do not quote)

### B1. Read this first (round 4)

Realism sentence:

**Realism sentence (after the numbers):** "Our headline uses the case's simplifications. Real servers deliver about 50 °C: enough for floor heating and new radiators, but hot water needs a small electric top-up, so summer coverage drops from 100% to 82% and the year from 79.6% to 77.6% at six servers. Old radiator houses are where it stops working." Footnote: layout A, unlimited-demand line, 50 °C is an estimate, house return at most 40 °C, break-even 0.2293 (case convention).

Q&A 1, 4 and 5:

1. *"What does the operator actually earn?"* Unknown, and we say so. On the reference server, public batch prices of 21 Nov 2026 list one server-hour of work at 7.7 / 14.3 / 38.2 CHF (low / central / high, 50/50 by server-hours; not an achievable income). Electricity minus heat needs 1.6% of that; paying back about 200,000 CHF installed per house needs about 11% over 5 years, 7% over 8 (simple payback; 12% / 9% at 5% interest), 32–36% if all work is LLM generation. Market form: about 1.5 CHF per sold server-hour, about 0.43 USD per GPU-hour net to the operator on every permit hour; data-centre renters pay 0.41–0.92 USD for this GPU, hosts get about 80% (*sourced*), and no buyer was found for capacity that vanishes when the tank is full. All *computed*, `analysis/r4_machine.py` (interest variants by the round-4 critic).
4. *"Hot water must be at 55–60 °C. What temperature is the tank at each end?"* Layout A: server coolant about 55 °C out (vendor blog on rack-scale AI systems), 5 K exchanger → buffer top about 50 °C (estimate), valid only while house water returns at 40 °C or colder. Bottom: 20 °C in summer (34.9 kWh, so the case's 35 kWh holds), heating return in winter (28 °C floor heating). A fresh-water station preheats to 47 °C and a small electric cylinder tops up to 55 °C, so server heat supplies 82.2% of hot water. A 55/45 radiator house returns water above 40 °C in about 850 cold hours (44–45 °C at the design hour), too warm to cool the servers, so the backup heater takes over then. Tank size barely matters (5 kWh usable costs 1.6 points). *Computed*, `analysis/r4_tank_layout.py`.
5. *"Show me missed deadlines with a forecast that can be wrong."* Admission uses archived ECMWF forecasts (day-1 RMSE 1.16 K, day-7 2.85 K), execution the actual weather. Under the headline with the 2 K guard: 0 missed in all 3 seeds; at 120–150% offers 12–13 a year at N=8; at double offers 33 / 11 (seed 1). Without the guard (round 2, saturating) roughly 0.1–0.6% a year. Forecast and truth come from the same model family; failures, overruns and real restart delays are not modelled.

Still unverified (three bullets):

- Reference server: wall power estimated, not measured; the 2U box measured whisper only; platform price likely low; heat-capture cost assumed; air-cooled, so low-temperature water only. Installed cost (~34,000 CHF per server) is an estimate; 5-year life and constant prices assumed.
- Temperatures: server outlet ~55 °C (vendor blog, not a datasheet); the server's maximum inlet temperature (decides the radiator-house figures); SIA 385/1 acceptance of a 47 °C preheat into a 55 °C cylinder; cylinder standby loss; restart time and idle power.
- Missed-deadline figure: forecast error only, assumed job mix, forecast from the same model family as the "truth". Round-4 critic probes (flat customer, fixed contract, radiator lower bound) are scratch scripts, not yet committed.

### B2. Computing income, CHF scenario (round 4, two-machine basis)

- **CHF scenario second, labelled:** 53.6k / 62.6k CHF a year at operator share 20%, central US batch prices, contract = 100% of heat capacity and unlimited willingness to buy (9.4 million audio-hours a year per house, no named buyer). It is on the round-3 two-machine basis (J1 laptop, J2 B200 slice) and **not yet recomputed on the reference server** (*computed*, `analysis/r4_headline.py`, section 3). Sold share comes from the run (~93%, set by the chosen contract). The 0.3375 CHF "at 67% sold" break-even is dropped from the headline (it belongs to the unsold-hours-still-run convention); it stays as one row in the break-even table.

### B3. Reference server and installed cost rows (round 4, air-coil basis)

| Item | Value | Status |
|---|---|---|
| Platform / heat capture per box | 5,000 / 8,000 / 12,000 CHF (likely ≥ 12,000 with this CPU) / 1,000 / 2,500 / 4,000 CHF (air-to-water coil, low-temperature water only, no booster or liquid cooling) | *assumption* |
| Installed cost, central | about 34,000 CHF per 1 kW server; about 200,000 CHF per house at N=6 (GPUs about 121,000 of it), 264,000 at N=8; incl. VAT (10.0% instead of 10.7% share if VAT is reclaimed) | *computed*, `python3 analysis/r4_machine.py`, sections 2–3 (GPU split and ex-VAT by the critic) |
| Share of list needed, N=6, central, all permit hours sold | operation 1.6%; 5-y payback 10.7% (12.1% at 5%); 8-y 7.3% (8.6%); at 67% sold 16.0% / 10.9%. N=8: 1.6% / 11.8% / 8.0% (13.4% / 9.5%). Low–high cost and price range, 5 y: 3.1–25.3% | *computed*, same, section 3 |

### B4. Where it stops holding, temperatures (round 4)

- **Temperatures (where the case assumptions stop holding):** a 55/45 radiator house reaches 64–77% (N=6) and 73–90% (N=8), depending on the servers' maximum inlet temperature (lower bound: servers stop when the return exceeds 40 °C; critic probe). An old 70/55 radiator house reaches at most about 59% for any N, about 30% if the servers need return water at or below 40 °C. A 45 °C loop: summer 71.1%, radiator houses lose at least 10.6 points at N=8 (*computed*, `analysis/r4_tank_layout.py`, section 6). **Air-cooled servers** that cannot serve hot water: 70.5% / 81.7% (*computed*, `analysis/r2_realism.py`); the reference server is air-cooled.

### B5. Realism column, layout A (round 4)

**Layout A** (goes in the assumptions list; detail in [research/r4-tank-temperatures.md](research/r4-tank-temperatures.md) section 3): server coolant about 55 °C out at 45 °C in (*sourced*: <https://blogs.nvidia.com/blog/liquid-cooling-ai-factories/>, about Rubin rack-scale AI systems, not a small-server datasheet) → CDU with a 5 K cold-end approach (read from Lenovo's Gold tier, facility water 40–45 °C vs secondary 45–50 °C; *sourced*: <https://lenovopress.lenovo.com/lp2018-lenovo-neptune-direct-water-cooling-standards>, our interpretation) → 1,000 l stratified heating-water buffer, top about 50 °C (*assumption*), **valid only while water returning to the CDU is at most 40 °C**. Space heating draws through a mixing valve; above 50 °C the buffer preheats the return and the backup heater adds the rest. Hot water: fresh-water station (3 K, inside suissetec's 2–5 K) preheats to 47 °C, a small electric cylinder tops up to 55 °C (SIA 385/1 per suissetec: at least 52 °C without warm-held pipes; *sourced*: <https://merkblatt.suissetec.ch/de-CH/ALLE222/file/ALLE222.pdf>). Cold water 10 °C, tank bottom 20 °C (*assumptions*); cylinder standby loss not modelled. Tank loss 2.80 kWh/day (*sourced*, round 2).

| *Computed*, `python3 analysis/r4_tank_layout.py`, unlimited demand | Coverage N=6 / N=8 | June–August | Utilisation | Break-even CHF |
|---|---|---|---|---|
| **Layout A, floor heating or radiators sized up to 50 °C, + tank loss** | **77.6% / 90.6%** | **82.2%** | 59.4% / 52.1% | **0.2293–0.2294** (top-ups by the backup heater, case convention); about 0.234 if the element's electricity is charged to the servers and its heat credited (excl. cylinder standby) |

### B6. Open risks 3, 4, 5, 8 and 14 (round 4)

3. **Installed cost is an estimate:** about 34,000 CHF per server (~200,000 per house at N=6), about 60% GPUs at sourced Swiss prices; house integration from the BFE 2015 heat-pump study as a proxy (not inflated); platform and heat capture are assumptions, platform probably understated (the box's CPU alone is 4,753 USD at 1kU); no liquid cooling or booster costed, so DigitalHeat's 50–70 °C target is not met; VAT counted as cost; simple payback at constant prices, no insurance, remote hands or failed GPUs.
4. **Missed-deadline figure is narrow** (must-have 3): forecast error only (no failures, overruns, network loss, real restart delays); forecast and truth from the same model family; 2025 with 3 seeds; assumed job mix; partner site unnamed (where the ~5% refused jobs go and who pays for a moved job). The headline's 0 relies on offers equal to expected capacity; at 120–200% offers misses return (11–33 a year). On 2025-01-13 servers holding a permit sit idle for lack of admitted work. The dashboard number must come from the team's own scheduler.
5. **Reference server:** wall power not measured; throughput is ideal offline batching; J1 and J2 were measured together only on a Cisco blade (2 × Xeon, 1 TB RAM), the 2U box measured whisper only. **The box is air-cooled and cannot make 50–70 °C water, while layout A assumes a liquid-cooled ~55 °C server: the realism column and the installed cost describe different machines.** For this box the air-cooled row (70.5% / 81.7%) applies. Note for `docs/assumption-limits.md` section 2 (whoever may edit it): the reference machine is air-cooled, so hot water needs a booster unless DigitalHeat names a liquid-cooled machine. Laptop energy: two synthetic-audio trials, no wall meter.
8. **Tank and temperatures:** usable capacity and winter supply temperature are now modelled (layout A). Still open: a datasheet outlet temperature; **the server's maximum inlet temperature** (sets the 40 vs 45 °C return limit and decides the radiator-house figures); whether SIA 385/1 accepts a 47 °C preheat into a 55 °C cylinder (suissetec says lower station temperatures are "nicht mehr möglich"; a question for a sanitary planner); the cylinder's standby loss; the MuKEn 2014 text. The committed script checks supply temperature only; return-limited server cooling (radiator lower bounds) is a critic scratch check. `docs/assumption-limits.md` should cite the 814/2013 ecodesign limit and 60 °C with warm-held pipes / 55 °C without (whoever may edit it).
14. **6 vs 8 depends on an unknown:** whether demand grows with installed servers. The round-4 critic probes behind this (fixed contract, flat customer) and the radiator lower bounds are scratch scripts listed in the critique files, not committed under `analysis/`; commit them before any of their figures goes on a slide.
