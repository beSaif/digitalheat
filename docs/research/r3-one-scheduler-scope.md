# Round 3: one scheduler, not a script

Weak point: is the adopted policy buildable by four people by the Saturday 21:00 freeze, and does it still hold with deadlines and finite demand? This file plans and assesses. It does not build the scheduler.

**Status labels:** *computed* = printed by a script in `analysis/` (script and command named); *sourced* = number read on a URL that was opened; *assumption* = our own choice or estimate; *unverified* = not checked. **No web sources were used in this round.** Every number here comes from repository inputs or from a script run. Firecrawl calls: 0. Currency: CHF. The electricity price (0.3325 CHF/kWh) and the heat value (price ÷ 2.5) are the repo inputs in `data/README.md`. No currency conversion was needed.

**Files and commands (all run on the stand-in reference house, 2025):**

| File | What | Command | Run time |
|---|---|---|---|
| `analysis/r3_policy_check.py` | Adopted vs minimal policy, every step in between, rule fights, demo days at permit level. Written by the cut-off round-3 run and **not modified here**; re-run, and its output is byte-identical to the earlier file | `python3 analysis/r3_policy_check.py` (3 seeds, multiprocessing) | 47 s wall, 434 s CPU, 228 simulated years |
| `analysis/r3_scope_extra.py` | **New this round.** (A) demo days at job level and on the heat signal under both offer scenarios; (B) restart time as an accounting line; (C) seconds per simulated year | `python3 analysis/r3_scope_extra.py` | 54 s |
| `docs/research/r3-one-scheduler-scope-rerun-output.txt` | Full output of the re-run (same as `r3-one-scheduler-scope-output.txt` from the cut-off run) | | |
| `docs/research/r3-one-scheduler-scope-extra-output.txt` | Full output of `r3_scope_extra.py` | | |

`r3_policy_check.py` imports and regression-checks against `baseline_sweep.simulate()`, `r2_realism.sim()` and `r2_deadline_sim.run()`. All checks print OK (section 0, pasted below).

---

## Bottom line

1. **The minimal scheduler that meets must-haves 2 and 3 word for word has 7 rules and about 80 lines of core code (estimate).** Six rules are must-build: expire, heat permit (never dump), EDF assign-and-pause, pin the real job to a server slot, admission dry run, and the trivial perfect-forecast source. The other two are optional and cheap: cap + band (about 8 lines) and the archived forecast with its guard band (about 25 lines).
2. **The adopted combination holds with deadlines and finite demand. Nothing breaks when the rules run together**, provided **one permit function is called both by the executor and by the admission dry run.** Adopted vs minimal (perfect forecast), N=6 / N=8, saturating offers: coverage 79.2 / 92.9% vs 79.2 / 92.8%; dumped 0 in both; utilisation 58.9 / 51.7% in both; starts 427 / 905 vs 1,788 / 2,223 per year; missed 0.003% / 0.026% vs 0.000%; break-even 0.2269 / 0.2275 vs 0.2261 CHF (the gap is only the 15-minute restart assumption) (*computed*).
3. **The rules fight in two places, and both come from the same mistake: the dry run and the executor disagree.** (i) The band runs in execution but the dry run assumes plain follow: misses rise to 0.59–0.72% (saturating) and 0.23–0.32% (heat-shaped). (ii) Restart time is in execution but not in the dry run: +0.10 to +0.14 points. Plain follow with an unaware dry run reaches 0.87% even with a perfect forecast (*computed*). When the dry run is consistent, the band does **not** push work past deadlines (S3 − S2: −0.002 to +0.004 points, seed noise).
4. **Three round-2 additions move no key figure beyond its rounding: cap + band, the hold rule and restart time inside `decide()`.** Cap + band is worth keeping anyway: 8 lines, starts down by about three quarters, and a calmer July demo. Cut the hold rule. Reduce restart to an accounting line: it reproduces the in-scheduler break-even within 0.0003 CHF (*computed*).
5. **Two additions do move a key figure.** The **2 K guard band** costs 1 line once forecast temperatures exist and removes 0.16 / 0.47 points of misses on the archived forecast. The **archived forecast** removes 2.6 / 3.8 points compared with "tomorrow = today" and adds about 1 coverage point under heat-shaped offers (*computed*).
6. **Missed deadlines under the adopted policy come down to a handful of jobs:** 0 to 12 jobs per year out of 32,000 to 39,000 accepted. One run of twelve gave **exactly 0**. The dashboard must print the count, the accepted share and the forecast source. A percentage alone may read "0.00%" (*computed*).
7. **Demo days.** **At N=6 no January day has a heat pause** under any policy, so the pause and resume must be shown in July. **The adopted 8 kWh band gives only 6 July days with a full pause and resume, and they shift by 3 days between offer scenarios** (saturating 2025-07-19, heat-shaped 2025-07-22; both pause 04:00 and resume 20:00 at N=6). The July day must therefore be read from the final yearly run. A 4 kWh band makes 16 July days robust, a 2 kWh band all 31. At N=8, **2025-01-25** (slot 7, pause 14:00, resume 19:00) is identical in every variant tested.
8. **Recommended build order** (below): permit + tank first; then jobs; then **admission with a perfect forecast before the 14:45 draft** (it is cheap and must give exactly 0 misses, which tests consistency); forecast ingestion and guard band only in the afternoon. Fallback wording for each stage is given verbatim.

---

## (a) Minimal scheduler specification

### What the must-haves demand, word for word (from `docs/case-brief.md`)

| Must-have words | What the core must therefore do | Rule(s) |
|---|---|---|
| MH2 "distribute, pause or reschedule jobs across the servers according to heat demand (winter heating, summer hot water)" | Hourly server count from demand; jobs assigned to servers; jobs without a server pause and wait | R2, R5 |
| MH2 "including a simple heat storage" | Tank state of charge in the permit and in the energy balance | R2, `house_step` |
| MH2 "what happens to a job when its heat is not needed" | Paused with its checkpoint and kept in the queue; missed if its deadline can no longer be met; offers that do not fit are not accepted | R1, R4, R5 |
| MH2 "The same scheduler code that produces the yearly balance must also control at least one real running job: it pauses and resumes it ... based on the heat signal" | One pure core imported by both drivers; the real job is bound to a slot whose run or pause comes from the heat permit | R6, the two drivers, the trace test |
| MH3 servers per house, coverage, dumped, utilisation | Energy accounting of the yearly driver | `house_step`, driver |
| MH3 "missed deadlines in % of jobs" | Jobs with deadlines, counted when they can no longer finish | R1 (+ R4 for a meaningful number) |
| MH3 electricity cost and computing income, break-even | Accounting: run hours, sold hours, heat used, price parameters | driver |
| MH1 "a model that assumes unlimited jobs must say so" | A finite offer generator, or a declared "unlimited" label | driver (offers) |

### State, inputs and outputs

```
state  (carried hour to hour; plain data, copied for the dry run)
  t            hour index 0..8759
  soc_kwh      tank, 0..35
  charging     bool, band state (only if band_kwh > 0)
  jobs         list of Job(id, type, rem_h, deadline_t, real: bool)
  k_prev       permits last hour (for starts and the trace)

decide(state, obs, params) -> (state', out)          # pure: no clock, no I/O, no sim/live flag
  obs      demand_kwh, space_heat_kwh               (this hour, from the CSV)
           forecast_kwh[0..167] or None             (built outside decide; None = admission off)
           offers: list of (type, rem_h, deadline_t)
  params   N, tank_kwh=35, q_kw=0.8, band_kwh (0 = off), cap_when_no_space_heat (bool),
           real_slot s, admission (bool)
  out      k (servers allowed = heat permits), accepted / rejected offers,
           run {slot: job_id}, paused ids, done ids, missed ids,
           real_job_action RUN | PAUSE, heat_kwh, used_kwh, dumped_kwh, one trace line

house_step(soc, heat, demand, tank, loss_per_h=0) -> (soc', used, dumped)   # pure, called by decide
```

The forecast builder (perfect = the CSV's own demand; or archived temperatures → case demand formula with a 12 − guard threshold) lives **outside** `decide()`. It is plain data preparation, so the guard band never touches the core.

### The 7 rules, in the order they run each hour

Conflict rule: **the heat permit beats everything.** No work runs without a permit, and no deadline overrides the heat (the house never dumps to save a job). LOC estimates (*assumption*) are anchored on the non-blank lines of the same logic in the assessment scripts (*computed* by reading them): `step_permit` in `r3_policy_check.py` lines 103–127, 23 lines for follow + band + hold; `forward_fail` in `r2_deadline_sim.py` lines 241–265, 25 lines; admission block lines 315–357, 43 lines; EDF execution lines 389–405, 17 lines; expiry lines 288–298, 11 lines; `read_prev_runs` + `demand_from_temps`, 22 lines.

| # | Rule | LOC (est.) | Serves | Build |
|---|---|---|---|---|
| R1 | **Expire:** a job with `deadline_t − t < ceil(rem_h)` is MISSED and removed | 8 | MH3 missed deadlines | **MUST** |
| R2 | **Heat permit, never dump:** `k = min(N_allowed, floor((demand + tank − soc) / 0.8))`; servers without a permit are off; an unsold permit means the server stays off | 5 | MH2 heat demand + storage; MH3 dumped = 0; jury "coverage at least dumped" | **MUST** |
| R3 | **Anti-flap inside the permit:** at most 1 server when space heating = 0 (cap); after the tank is full, `k = 0` until `soc ≤ tank − band` or `soc < demand` (band). The same function must serve R2 and the R4 dry run | 8 + 1 state var | Starts per year (Q&A on cycling); July demo watchability. No key figure moves at display precision | OPTIONAL, recommended (default on) |
| R4 | **Admission dry run:** add this hour's offers tentatively; roll R2(+R3) forward 168 h on `forecast_kwh` and fill with R5's EDF; take back the newest offers until no accepted job is forecast to fail; the rest are "not accepted (other site)", never "missed" | 35 (one EDF fill function shared with R5) | MH3 missed % that means something (without it: 35–40% missed under saturating offers, 2.6–2.9% under heat-shaped); the working idea "heat is the admission ticket"; jury scheduling quality | **MUST-BUILD**, with a fallback (below) |
| R5 | **Assign EDF and pause the rest:** sort jobs by deadline; the first ones get one server-hour each (a 0.5 h job takes half) up to `k`; every other job is PAUSED (checkpoint kept, stays queued) | 15 | MH2 "distribute, pause or reschedule"; "what happens to a job when its heat is not needed" | **MUST** |
| R6 | **Pin the real job:** the real job is bound to slot `s` and runs iff `k ≥ s`. PAUSE on a falling edge, RESUME on a rising edge. It follows the heat signal, not job priority | 5 | MH2 second sentence ("based on the heat signal") | **MUST** |
| R7 | **Forecast source for R4:** default `perfect` (CSV demand, 3 lines). Optional `ifs025` archived CSV with causal lead `min(7, (L+46)//24)` and guard band (threshold 12 − 2 °C) | 3 / +25 | Core use case "checks the weather forecast"; a non-trivial missed figure | perfect: **MUST**; archived + guard: OPTIONAL (should) |

**Core total: about 80 lines (about 70 must-build).** Around it: `house_step` about 8 lines; yearly driver with offer generator and key figures about 60; live driver about 70 (C); trace-equality test about 25. All *assumption*.

**Not in `decide()` (accounting or parameters of the driver):** restart time as `sold_h − starts × restart_min/60` (2 lines, default 0 in the case column, 15 min in the realistic column); tank loss as `loss_per_h` in `house_step` (1 line); booster as an accounting line (about 5); sold share as the level of the heat-shaped offers (the 12 monthly 2020–24 capacities from `r2_deadline_sim.py` section 1 hard-coded as a table, 2 lines).

### What to cut or reduce (effect *computed* from `r3_policy_check.py` sections 1–3 and `r3_scope_extra.py` section B; 3-seed means)

| Accumulated feature | Effect on key figures when added | Build cost | Verdict |
|---|---|---|---|
| Heat-permit follow | the core | 5 | keep |
| Cap + 8 kWh band (S3 − S2) | coverage −0.06 to +0.00 points, utilisation −0.05 to 0.00, missed −0.002 to +0.004 points, break-even ±0.0000; **starts −1,292 to −1,366 per year** | 8 | keep as a parameter (default on). No key figure moves; it buys Q&A and a calmer demo. Condition: the dry run uses it too |
| Hold rule (H − A) | coverage −0.02 to −0.13 points, missed −0.002 to +0.003, break-even −0.0001 to −0.0004; starts −37 to −284 | 10 + state + its own test | **cut** (rounding-level gain, stateful) |
| Restart 15 min inside execution + aware dry run (A − S3) | break-even +0.0008 to +0.0023 CHF; coverage +0.01 to +0.54 points (restart heat without work); missed +0.001 to +0.005 points | about 30 (executor + dry-run derating) | **reduce to an accounting line**: the line reproduces the in-scheduler break-even within 0.0000–0.0003 CHF. Disclose "restart delay is not in the missed figure" |
| Admission EDF dry run | missed: 35.4 / 39.6% → 0 (saturating, perfect forecast); 2.6 / 2.9% → 0 (heat-shaped) | 35 | **must** |
| 2 K guard band on the archived forecast (S2 − S1) | missed −0.155 / −0.474 points (saturating), −0.000 / −0.017 (shaped); coverage −0.22 / +0.12 points (shaped) | 1 (once temperatures exist) | keep (parameter, default 2 K) |
| Archived forecast instead of persistence (S1 − M2) | missed −2.6 / −3.8 points (saturating), −0.44 / −0.56 (shaped); coverage +1.15 / +1.08 points under shaped offers | 25 + committed CSV | **should**, after the must-haves |
| Sold-share parameter | coverage at 100 / 70 / 40% sold, from round 2 | 2 (offer level) | keep as an offer parameter |
| Tank loss switch | coverage −0.3 points (round 2) | 1 | keep (realistic column) |
| Booster switch | coverage −2.1 / −2.4 points (round 2) | 5 (accounting) | keep (realistic column) |
| Peaked hot water | at most −0.1 points (round 2) | 3 | cut, quote the computed result |
| Two drivers + trace test + process-state check | the must-have itself | about 170 | never cut |

### Build order for role A, Saturday 09:30–21:00

It fits the team table in `docs/overnight.md`: integration at 11:00, lunch 12:15–12:45, draft 14:45, dinner 18:00–18:40, rehearsals with C from 18:40, freeze 21:00. **All feature work ends at 18:00.** Each check is an output that proves the step works, with the expected value from the assessment scripts. These hold only while the team uses the same job definitions (J1 0.5 server-h / 24 h, J2 4 server-h / 168 h, 50/50 by work, Poisson). If the team changes them, the energy checks still hold and the job checks become "0 missed with a perfect forecast".

| Time | Step | Check (what output proves it) |
|---|---|---|
| 09:30–10:15 | `core.py`: R2 permit + `house_step`; yearly driver in "every permit used" mode; key-figure printer | N=6: coverage 79.58%, 31,067 server-h, dumped 0, break-even 0.2261 CHF; N=8: 92.94%, 36,281 server-h (= `python3 analysis/baseline_sweep.py`, follow) |
| 10:15–11:00 | R3 cap + band as parameters (0 = off); R6 real-slot output; trace-line format agreed with C | band off reproduces the line above; cap + 8 kWh: **379 / 891 starts, 79.55 / 92.94%** (`r2_realism.py` section v; `r3_policy_check.py` section 0); trace of a July date shows slot 1 `####................####` (N=6, 2025-07-19, permit level) |
| 11:00–11:20 | **Integration 1** (all four): C's live driver imports `core.py` and pauses B's J1 on R6 | `ps -o state=` shows `T` after PAUSE and not `T` after RESUME |
| 11:20–12:15 | Job queue: offer generator (saturating + heat-shaped table), R5 EDF assign/pause, R1 expire; **no admission yet** | invariants: done + missed + open = accepted; sold h ≤ permit h; dumped 0. Without admission and with heat-shaped offers, missed ≈ 2.6% (N=6) / 2.9% (N=8) (row F) |
| 12:45–13:45 | Second job type; **R4 admission dry run with R7 = perfect** (the CSV's demand), using the same permit function as R2/R3 | **missed exactly 0** at N=6 and N=8, both offer scenarios (rows M1 and X2). A non-zero value here means the dry run and executor disagree (rule fight X1) |
| 13:45–14:45 | Seven key figures from one command; missed line with count, accepted share and forecast label; fallback wording in the README | one command prints N, coverage, dumped, utilisation, missed (x of y accepted, forecast = perfect), electricity cost, income (sold h × price parameter), break-even twice. **Draft saved 14:45** |
| 14:45–15:30 | R7 option `persist` (forecast = last 24 h repeated, about 5 lines, no data); guard band as a parameter | with a 2 K guard, saturating offers: about 0.20% (N=6) / 0.62% (N=8) missed; without the guard 2.8 / 4.3% (rows M3, M2) |
| 15:30–16:30 | R7 option `ifs025`: read `analysis/r2_data/prev_ecmwf_ifs025.csv`, causal lead, guard 2 K | day-1 RMSE 1.16 K, bias +0.29 K (`r2_deadline_sim.py` section 0); missed about 0.002% (N=6) / 0.02% (N=8) saturating (row S2), never quoted as 0 |
| 16:30–17:15 | Accounting lines: restart (`starts × 0.25 h` unsold), tank loss parameter, booster; two-column key figures | restart line, cap + 8 kWh, N=6 saturating: break-even 0.2269 (`r3_scope_extra.py` B); tank loss 2.80 kWh/day: coverage −0.3 points (round 2) |
| 17:15–18:00 | Freeze the yearly configuration; re-run every check above; run a 10-line demo-day finder on the final trace and hand dates and hours to C | finder prints, for the final run, the July days with pause-then-resume on slot 1 and their hours (see (c)) |
| 18:40–21:00 | With C: three timed rehearsals; only demo-blocking fixes | same-decisions test green; SHA-256 of `core.py` identical in both driver headers |

**If behind schedule:** drop 14:45–17:15 in reverse order (accounting lines, then `ifs025`, then `persist`). Never drop 12:45–13:45: the perfect-forecast admission is the cheapest step that turns "missed %" into a scheduler figure.

### Fallback wording (dashboard line and pitch sentence), by how far admission and forecast got

All figures *computed* by `python3 analysis/r3_policy_check.py`. Ranges are 3 seeds × N=6 / N=8. The bracketed numbers are filled from the team's own run.

| Stage reached at 21:00 | Dashboard missed-deadline line | Pitch sentence |
|---|---|---|
| Admission + archived forecast + guard band (the plan) | "Missed deadlines: [x] of [y] accepted jobs ([p]%), forecast = archived ECMWF forecasts, 2 K guard band; accepted [a]% of offered jobs" | "With real archived weather forecasts our scheduler missed [x] of [y] accepted jobs in the year. Forecast error is the only failure we model; server failures and overruns are not in this number." |
| Admission with persistence only | "Missed deadlines: [x] of [y] accepted jobs ([p]%), forecast = 'tomorrow repeats today' (no weather data), 2 K guard band" | "We admit work against a deliberately crude forecast, tomorrow equals today, and still miss only [p]%. A real forecast lowers this further in our analysis script; it is not in the live scheduler yet." Expected: about 0.2% / 0.6% saturating, about 0.00–0.02% heat-shaped |
| Admission with a perfect forecast only | "Missed deadlines: 0 of [y] accepted jobs, **perfect forecast**. This shows only that admission and execution use the same rule; with a real forecast our separate analysis (`analysis/r3_policy_check.py`) gives 0.002–0.03%" | "With perfect foresight nothing is missed, by construction. The honest figure needs a forecast that can be wrong: our analysis script gives three in a hundred thousand to three in ten thousand of accepted jobs, and that part is not yet inside the live scheduler." |
| No admission (every offer accepted) | "Missed deadlines: [p]% of jobs (**no admission control**; every offered job is accepted; offers = heat-shaped contract at 100% of 2020–24 capacity)" | "Without admission control [p]% of jobs miss their deadline (expected about 2.6% / 2.9%). Admission against the forecast brings this near zero in our analysis script (`analysis/r3_policy_check.py`), but that is not yet in the live scheduler." |

In every stage, **never print a bare "0%"**: one adopted run of twelve gave exactly 0 missed jobs (N=8, heat-shaped, seed 3).

---

## (b) Evidence: the adopted policy run together

### Definitions

- **MINIMAL:** plain follow + EDF admission dry run on a perfect forecast (M1) or on persistence (M2; M3 = M2 + 2 K guard).
- **ADOPTED (A):** cap + 8 kWh band, admission dry run that uses the same rule, archived `ifs025` forecast with causal heating-day flag, 2 K guard band, 15 min restart per start, restart-aware dry run.
- **Offers:** `saturating` (N × 24 server-h/day) or `shaped100` (heat-shaped monthly contract at 100% of the 2020–24 mean capacity, which cannot see 2025).
- Jobs as round 2: J1 0.5 server-h / 24 h, J2 4 server-h / 168 h, 50/50 by work, Poisson.
- **Not modelled:** partner site, hardware or network failures, runtime overruns.
- Missed = % of accepted jobs closed in the year (done + missed). "Restart h" = server-hours spent starting (power and heat, no work).

### Section 0 regression checks (pasted)

```
  N=6 follow: baseline_sweep run_h 31067 | this file 31067 -> OK
  N=6 cap + 8 kWh band: r2_realism starts 379, coverage 79.55% | this file starts 379, same hourly server counts: True -> OK
  N=6 hold + cap + 8: r2_realism starts 267, coverage 79.46% | this file starts 267, same hourly server counts: True -> OK
  N=8 follow: baseline_sweep run_h 36281 | this file 36281 -> OK
  N=8 cap + 8 kWh band: r2_realism starts 891, coverage 92.94% | this file starts 891, same hourly server counts: True -> OK
  N=8 hold + cap + 8: r2_realism starts 607, coverage 92.80% | this file starts 607, same hourly server counts: True -> OK
  N=6 follow + adm(ifs025, non-causal flag), saturating, seed 1: r2_deadline_sim accepted 32823, missed 34, coverage 79.130% | this file accepted 32823, missed 34, coverage 79.130% -> OK
  N=8 follow + adm(ifs025, non-causal flag), saturating, seed 1: r2_deadline_sim accepted 39051, missed 109, coverage 92.750% | this file accepted 39051, missed 109, coverage 92.750% -> OK
  all regression checks: OK
```

### Adopted vs minimal: key figures (*computed*, `python3 analysis/r3_policy_check.py` section 1, 3-seed means)

| Policy | N | Offers | Coverage | Dumped kWh | Utilisation | Starts/yr | Accepted jobs / work | Missed % of accepted jobs [seed range] | Break-even CHF/sold h |
|---|---|---|---|---|---|---|---|---|---|
| M1 minimal, perfect | 6 | saturating | 79.2% | 0 | 58.9% | 1,788 | 52.5% / 59.4% | 0.000 [0.000–0.000] | 0.2261 |
| M2 minimal, persistence | 6 | saturating | 79.2% | 0 | 58.9% | 1,791 | 58.4% / 61.1% | 2.773 [2.636–2.883] | 0.2261 |
| M3 = M2 + 2 K guard | 6 | saturating | 79.0% | 0 | 58.7% | 1,822 | 56.1% / 58.9% | 0.195 [0.161–0.253] | 0.2261 |
| **A adopted** | 6 | saturating | **79.2%** | **0** | **58.9%** | **427** | **54.8% / 59.0%** | **0.003 [0.003–0.003]** | **0.2269** |
| F no admission | 6 | saturating | 79.2% | 0 | 58.9% | 1,788 | 100% / 100% | 35.425 | 0.2261 |
| M1 minimal, perfect | 6 | shaped100 | 74.1% | 0 | 55.1% | 2,187 | 95.3% / 97.1% | 0.000 | 0.2261 |
| M2 minimal, persistence | 6 | shaped100 | 72.8% | 0 | 54.1% | 2,293 | 94.2% / 95.6% | 0.444 [0.413–0.475] | 0.2261 |
| **A adopted** | 6 | shaped100 | **74.0%** | **0** | **55.0%** | **756** | **94.6% / 96.4%** | **0.005 [0.003–0.009]** | **0.2276** |
| F no admission | 6 | shaped100 | 74.2% | 0 | 55.1% | 2,182 | 100% / 100% | 2.615 | 0.2261 |
| M1 minimal, perfect | 8 | saturating | 92.8% | 0 | 51.7% | 2,223 | 45.1% / 52.7% | 0.000 | 0.2261 |
| M2 minimal, persistence | 8 | saturating | 92.8% | 0 | 51.7% | 2,223 | 54.1% / 56.5% | 4.298 [4.097–4.436] | 0.2261 |
| M3 = M2 + 2 K guard | 8 | saturating | 92.8% | 0 | 51.7% | 2,223 | 51.1% / 53.0% | 0.615 [0.528–0.688] | 0.2261 |
| **A adopted** | 8 | saturating | **92.9%** | **0** | **51.7%** | **905** | **48.9% / 52.4%** | **0.026 [0.018–0.032]** | **0.2275** |
| F no admission | 8 | saturating | 92.8% | 0 | 51.7% | 2,223 | 100% / 100% | 39.624 | 0.2261 |
| M1 minimal, perfect | 8 | shaped100 | 86.5% | 0 | 48.2% | 2,750 | 94.4% / 96.3% | 0.000 | 0.2261 |
| M2 minimal, persistence | 8 | shaped100 | 85.0% | 0 | 47.3% | 2,920 | 93.6% / 94.7% | 0.577 [0.544–0.609] | 0.2261 |
| **A adopted** | 8 | shaped100 | **86.7%** | **0** | **48.3%** | **1,343** | **93.6% / 95.5%** | **0.005 [0.000–0.008]** | **0.2284** |
| F no admission | 8 | shaped100 | 86.6% | 0 | 48.2% | 2,745 | 100% / 100% | 2.889 | 0.2261 |

Absolute counts for A (*computed*, one-off call of `r3_policy_check.run()`, seeds 1–3): **N=6: 1 missed of about 32,200–32,700 accepted (saturating), 1–3 of about 31,700–32,000 (shaped). N=8: 7–12 of about 38,200–38,900 (saturating), 0–3 of about 36,700–37,100 (shaped).**

A's break-even is above 0.2261 only because of the 15-minute restart assumption. A's coverage under shaped offers (74.0 / 86.7%) is slightly above S3's (73.7 / 86.1%) because restart quarter-hours deliver heat without work. That is an artefact of the restart model, not a gain.

### What each rule buys (*computed*, section 2; differences of 3-seed means; coverage and missed in points)

| Step | N, offers | d coverage | d starts | d accepted work | d missed | d break-even |
|---|---|---|---|---|---|---|
| Archived forecast instead of persistence (S1 − M2) | 6 sat / 6 shp / 8 sat / 8 shp | +0.01 / +1.15 / +0.00 / +1.08 | −3 / −99 / 0 / −132 | −1.43 / +1.29 / −3.15 / +1.15 | **−2.615 / −0.444 / −3.803 / −0.560** | 0 |
| 2 K guard on archived (S2 − S1) | same order | +0.00 / −0.22 / +0.00 / +0.12 | 0 / +26 / 0 / +2 | −0.47 / −0.31 / −0.56 / −0.03 | **−0.155 / 0.000 / −0.474 / −0.017** | 0 |
| Cap + 8 kWh band (S3 − S2) | same order | −0.03 / −0.06 / +0.00 / −0.03 | **−1,353 / −1,366 / −1,317 / −1,292** | −0.03 / −0.07 / +0.01 / −0.04 | −0.002 / 0.000 / +0.004 / 0.000 | 0 |
| Restart 15 min, dry run aware (A − S3) | same order | +0.03 / +0.37 / +0.01 / +0.54 | −8 / −99 / −1 / −154 | −0.17 / −0.12 / −0.31 / −0.24 | +0.003 / +0.005 / +0.001 / +0.005 | +0.0008 / +0.0015 / +0.0014 / +0.0023 |
| Dry run aware of restart (A − A−) | same order | 0 / +0.40 / 0 / +0.45 | 0 / −81 / 0 / −37 | −0.13 / +0.54 / −0.05 / +0.49 | **−0.139 / −0.024 / −0.100 / −0.032** | ≈ 0 |
| Hold instead of band (H − A) | same order | −0.09 / −0.02 / −0.13 / −0.10 | −112 / −37 / −284 / −203 | +0.02 / +0.01 / +0.03 / +0.05 | +0.003 / 0.000 / −0.002 / +0.002 | −0.0002 / −0.0001 / −0.0004 / −0.0003 |
| ADOPTED − MINIMAL perfect (A − M1) | same order | +0.00 / −0.08 / +0.01 / +0.13 | **−1,361 / −1,431 / −1,318 / −1,407** | −0.42 / −0.72 / −0.24 / −0.80 | +0.003 / +0.005 / +0.026 / +0.005 | +0.0008 / +0.0015 / +0.0014 / +0.0023 |

**Reading:** against the perfect-forecast minimal, the adopted policy buys three things: about 1,300–1,430 fewer starts per year; a missed figure that comes from a real forecast instead of being zero by construction; and the "checks the weather forecast" story. It costs at most 0.8 points of accepted work and 0.0023 CHF of break-even, the latter purely from the restart assumption. No coverage, dumped or utilisation figure changes beyond ±0.13 points.

### Where rules fight (*computed*, section 3 and section 1 rows X1–X4, A−, M1r)

| Fight | Mechanism | Size | Fix |
|---|---|---|---|
| **Band in execution, plain follow in the dry run (X1)** | the dry run promises permits the band withholds | missed 0.720 / 0.591% (saturating N=6 / N=8), 0.226 / 0.317% (shaped), against 0.000–0.025% when consistent (S3) | **one permit function, called by both the executor and the dry run** (structural; 0 extra lines) |
| **Restart in execution, not in the dry run (A−)** | each start loses 15 min of work the dry run counted | +0.139 / +0.100 points (saturating), +0.024 / +0.032 (shaped) | derate starting servers in the dry run (about 6 lines) **or** keep restart out of execution (accounting line) |
| **Restart with plain follow and an unaware dry run (M1r)** | 1,780–2,222 starts × 15 min | 0.868 / 0.875% missed with a **perfect** forecast | do not combine; see above |
| Band delaying work past deadlines | the band withholds permits while work waits ("blocked" 13,900–17,100 server-h/yr) | **no measurable effect when the dry run is consistent:** S3 − S2 missed −0.002 to +0.004 points; sold hours −0 to −25 h/yr | none needed; the band lowers the tank, which creates later permits |
| Band without cap (X3) | band alone keeps cycling | 1,526 / 2,398 starts (saturating) vs 435 / 906 with cap | always ship cap and band together |
| Cap alone (X4) | | 1,790 / 2,223 starts: cap alone does nothing at saturating offers | as above |
| Guard band vs coverage (S2 − S1, shaped) | fewer accepted jobs on shoulder days | −0.22 / +0.12 points | accept (noise-level) |

### Restart as an accounting line (*computed*, `python3 analysis/r3_scope_extra.py` section B, seed 1)

```
  N=6 saturating cap + 8 kWh band : no restart BE 0.2261, starts   460, missed 0.000% | restart in scheduler BE 0.2269, missed 0.003%, coverage 79.10% -> 79.15% | accounting line BE 0.2269 (diff +0.0000)
  N=6 saturating plain follow     : no restart BE 0.2261, starts  1813, missed 0.000% | restart in scheduler BE 0.2294, missed 0.009%, coverage 79.13% -> 79.18% | accounting line BE 0.2295 (diff +0.0000)
  N=6 shaped100  cap + 8 kWh band : no restart BE 0.2261, starts   896, missed 0.000% | restart in scheduler BE 0.2277, missed 0.003%, coverage 73.20% -> 73.60% | accounting line BE 0.2279 (diff +0.0002)
  N=6 shaped100  plain follow     : no restart BE 0.2261, starts  2292, missed 0.000% | restart in scheduler BE 0.2305, missed 0.006%, coverage 73.30% -> 73.59% | accounting line BE 0.2307 (diff +0.0002)
  N=8 saturating cap + 8 kWh band : no restart BE 0.2261, starts   921, missed 0.018% | restart in scheduler BE 0.2275, missed 0.029%, coverage 92.75% -> 92.77% | accounting line BE 0.2275 (diff +0.0000)
  N=8 saturating plain follow     : no restart BE 0.2261, starts  2238, missed 0.013% | restart in scheduler BE 0.2296, missed 0.018%, coverage 92.75% -> 92.77% | accounting line BE 0.2296 (diff +0.0000)
  N=8 shaped100  cap + 8 kWh band : no restart BE 0.2261, starts  1527, missed 0.000% | restart in scheduler BE 0.2284, missed 0.008%, coverage 85.73% -> 86.25% | accounting line BE 0.2287 (diff +0.0003)
  N=8 shaped100  plain follow     : no restart BE 0.2261, starts  2866, missed 0.000% | restart in scheduler BE 0.2308, missed 0.003%, coverage 85.69% -> 86.20% | accounting line BE 0.2310 (diff +0.0003)
```

The accounting line is `(electricity − heat value) / (sold h − starts × 0.25 h)` taken from the run without restart. It matches the in-scheduler break-even within 0.0003 CHF. What it leaves out: missed +0.003 to +0.011 points and coverage +0.02 to +0.52 points (unsold restart heat). Restart time itself is an *assumption* (round 2).

### Run time (*computed*, `r3_scope_extra.py` section C, single process)

One simulated year with admission takes **0.7–4.6 s** in plain Python (A: 0.9–1.8 s; M1: 0.7–4.6 s). Without admission it takes 0.1 s. That is fast enough for the yearly driver and for a few dashboard scenarios. The round-2 critic's "about 2.2 s per year" is consistent.

---

## (c) Demo days

### Rules used

The real job follows the **heat signal** of its slot (R6): it runs iff permits ≥ slot. That signal comes from the job-level yearly run, because the live day starts from the yearly state at 00:00 of the demo date. So the pattern depends on the offer scenario of the yearly run. `r3_scope_extra.py` section A scans it for both scenarios. July uses slot 1 (the last server to stop). January uses the highest slot that shows a pause-then-resume.

Seconds per simulated hour (*assumption*, from round 1): January 1.5 s/h (36 s), July 2.5 s/h (60 s), about 130 s live part. Real second = simulated hour × s.

### Days with a full pause and resume of the demo slot (*computed*, `python3 analysis/r3_scope_extra.py`, seed 1)

| Policy | N | January days (heat signal) | July days (heat signal), saturating / shaped / both |
|---|---|---|---|
| Adopted (cap + 8 kWh band) | 6 | **0 of 31**, under both offers (all 6 servers run every January hour) | 6 / 6 / **0** (saturating 07-03, 07-10, 07-12, 07-19, 07-26, 07-28; shaped 07-06, 07-13, 07-15, 07-22, 07-29, 07-31) |
| Adopted | 8 | 6 / 6 / **6** (01-09, 01-25, 01-26, 01-27, 01-28, 01-29) | 6 / 6 / **0** (same dates as N=6) |
| Minimal (plain follow) | 6 | 0 | 31 / 31 / 31 (one-hour flips, 17–18 transitions a day) |
| Minimal | 8 | 6 / 6 / 6 (same dates) | 31 / 31 / 31 |
| Cap + 4 kWh band | 6 / 8 | as above | 23 / 24 / **16** |
| Cap + 2 kWh band | 6 / 8 | as above | 31 / 31 / **31** (two 4 h pauses a day) |

### Recommended picks

| Policy, N | January day | July day | Interrupted job (the pause and resume the audience sees) | Real seconds |
|---|---|---|---|---|
| Adopted, N=6 | **2025-01-13**, coldest day: demand 221.5 kWh, 6 of 6 servers all 24 h, backup 106.3 kWh, **no pause** (message: "in January the heat is always wanted") | from the final yearly run: **2025-07-19** if offers are saturating, **2025-07-22** if heat-shaped | July, slot 1: **PAUSE 04:00, RESUME 20:00** (16 h, tank full) in both | at 2.5 s/h: pause at **10.0 s**, resume at **50.0 s**, 40 s paused of a 60 s day; at 1.5 s/h: 6.0 s / 30.0 s |
| Adopted, N=8 | **2025-01-25**, slot 7: **PAUSE 14:00, RESUME 19:00** (5 h); identical under adopted, minimal, both offers, bands 2/4/8 | 2025-07-19 (saturating: PAUSE 05:00, RESUME 21:00) or 2025-07-22 (shaped: 04:00 / 20:00) | January slot 7 and July slot 1 | January at 1.5 s/h: **21.0 s / 28.5 s** (7.5 s paused); at 1.0 s/h: 14.0 / 19.0 s. July at 2.5 s/h: **12.5 s / 52.5 s** (saturating) or 10.0 / 50.0 s (shaped) |
| Minimal, N=6 or 8 | as above (N=6 no pause; N=8 2025-01-25 slot 7) | any July day, e.g. 2025-07-15 | slot 1 flips hourly: first PAUSE 02:00, RESUME 03:00 (N=8 shaped: 01:00 / 02:00) | at 2.5 s/h: **5.0 s / 7.5 s**, each pause 2.5 s, 17–18 transitions in 60 s |

On the round-1 pitch clock (January from 1:00 at 1.5 s/h, 6 s title card, July from 1:42 at 2.5 s/h; arithmetic only), the July pause and resume fall at **1:52.0 / 2:32.0** (adopted, N=6, either offer scenario). At N=8 they fall at 1:54.5 / 2:34.5 (saturating), with the January pause at 1:21.0 and the resume at 1:28.5.

**Notes for C:**
- With the 8 kWh band the July pause takes 40 of the 60 s. Running July at 1.5 s/h (36 s; pause 6.0 s, resume 30.0 s) frees 24 s of pitch time without losing either event.
- Because the 8 kWh band's July dates move with any change of offers, forecast or N, **pick the date only after the 17:15 freeze, with the finder**.
- Switching to a 4 kWh band makes 16 July days robust. Cost: +102 / +94 starts per year at permit level (481 / 985 vs 379 / 891). Coverage is unchanged at 0.01 points: 79.56 vs 79.55% (`r3_policy_check.py` section 4, band table). The yearly figures must then be rerun with 4 kWh, since demo and balance share the setting.
- In the job-level run (not the heat signal), the 6th server at N=6 sits idle for a few hours on 9 January days because no accepted work is waiting. That is "no work", not "no heat". Do not show it as a heat pause. This is why R6 binds the real job to the permit, not to job availability.

---

## (d) Are the round-2 additions worth their build cost?

| Addition | Worth it? | Why |
|---|---|---|
| Admission as an EDF dry run | **Yes, must-build** | about 35 lines; without it the missed figure is 35–40% (saturating) or 2.6–2.9% (heat-shaped); with a perfect forecast it doubles as the consistency test (exactly 0) |
| Guard band 2 K | **Yes** | 1 line once temperatures exist; −0.16 / −0.47 points of misses on the archived forecast; at most 0.22 coverage points under shaped offers |
| Archived forecast ingestion | **Yes, but after the must-haves (afternoon)** | about 25 lines plus a committed CSV; −2.6 / −3.8 points vs persistence; the only thing that makes "checks the weather forecast" true |
| Cap + 8 kWh band | **Yes, as a cheap parameter**, with two conditions | 8 lines; no key figure moves; starts −75%; it **must** sit in the permit function the dry run uses (else +0.2 to +0.7 points of misses), and the July demo date must be read from the final run (or use 4 kWh) |
| Restart-time parameter inside the scheduler | **No; reduce to an accounting line** | about 30 lines in executor and dry run for break-even +0.0008 to +0.0023 CHF, which the 2-line accounting line reproduces within 0.0003 CHF |
| Hold rule | **No, cut** | rounding-level effect on every key figure; stateful; its own test needed |
| Sold-share parameter | Yes, at the offer level | 2 lines; drives the coverage label "at X% sold" |
| Realism switches | Yes, outside `decide()` | tank loss 1 line in `house_step`; booster as an accounting line; peaked hot water cut (quote the round-2 result) |
| Two drivers + trace test + process-state check | Never cut | the must-have itself |

---

## Limitations of this assessment

- Assessment scripts, not the team's scheduler. LOC figures are estimates anchored on assessment code that also carries statistics; the team's code may be shorter or longer.
- One house, one year (2025), stand-in CSV, 3 seeds; seed ranges are arrival noise only. The job mix, sizes, deadlines and offer levels are round-2 *assumptions*. The archived forecast is from the same model family as the reference weather (round-2 caveat), and its warm bias flatters the miss rate.
- The `causal` flag clamps at a 7-day lead, so targets 145–167 h ahead still use a series up to 23 h fresher than available.
- No partner site, failures or overruns. Work on a job that later misses still counts as sold. Capacity is a pool (a job is not bound to a server except the real one).
- The demo-day scan uses seed 1. A different seed or job definition can shift the job-level July dates. Within the runs tested, the heat-signal patterns at N=8 in January did not change.
- The restart model counts the start quarter-hour as heat without work; the "restart raises coverage" effect is that artefact.
