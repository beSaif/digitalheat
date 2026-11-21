# Round 6: build-scope audit. What the team's own scheduler will show at 21:00

Investigator file for round-6 weak point 1 ("build-scope audit: what the team's own scheduler will actually show at 21:00, versus what lives only in analysis scripts"). Written Sat 21 Nov 2026, about 11:00–11:30, while the team builds. Plans and assesses only: no scheduler code was written and no existing file was changed.

**Status labels:** *computed* = printed by `analysis/r6_build_scope.py` or another saved script (command named); *sourced* = read on a URL that was opened (none this round); *assumption* = our own choice or estimate; *unverified* = not checked. **No web sources were used.** Firecrawl calls: 0. Currency: CHF. The only money figures here are seed-1 reprints of the repo's electricity price (0.3325 CHF/kWh) and heat value (price ÷ 2.5) from `data/README.md`. No currency conversion was needed.

**Files written this round**

| File | What |
|---|---|
| `analysis/r6_build_scope.py` | new script, standard library only, imports the analysis scripts without editing them. Sections: 1 line census, 2 person-hours, 3 capacity vs load (current vs revised table), 4 expected missed-deadline line by stage incl. whole-house outages, 4b seed-1 key figures, 5 offer-CSV reproducibility |
| `docs/research/r6-real-vs-analysis.md` | README-ready table: real (scheduler / live) vs analysis script vs assumption, for every figure in "Read this first" |
| this file | findings, commands, pasted output |

**Commands (run on this laptop, 21 Nov 2026):**

```
python3 analysis/r6_build_scope.py --loc-only   # sections 1-3, < 1 s
python3 analysis/r6_build_scope.py              # all sections, 8-10 s wall on all cores (~85 s CPU), exit 0
```

It writes no repository file, no `__pycache__` entry (checked: no `r6` entry in `analysis/__pycache__`), and one temp file (`r6_buildscope_offers_*.csv` in the system temp directory), which it deletes again.

---

## Bottom line

1. **The current Saturday table does not fit.** For the 11:30–21:00 slots in `docs/overnight.md`, role A carries 7.6–15.9 h of work (unassisted rates) or 5.1–10.8 h (AI-assisted). Its effective capacity is about 5.1 h. Role D carries 5.1–8.3 h against 4.4 h; role C 3.3–10.0 h against 4.8 h. Role B carries only 2.3–3.5 h against 5.5 h (*computed*, `r6_build_scope.py` section 3a; rates, focus factor and windows are *assumptions*). The plan puts the whole scheduler core plus every OPTIONAL row on one person, and leaves B mostly idle after the energy run.
2. **The MUST list fits only if three things hold.** The rest of the core (M2–M6) is 4.9–10.4 person-hours unassisted, or 3.0–6.7 with an AI coding assistant. Against A's 5.1 h it fits (i) only with assisted porting from the analysis scripts, (ii) only if A does nothing but M2, M3, M4 and M6, and (iii) only at the midpoint, not the high estimate (midpoint 4.9 h with the demo-day finder; *computed*, section 3b). Unassisted it does not fit one person (midpoint 7.7 h). **No MUST row has to be cut, but the work must be redistributed.** B takes the offer loader, the yearly accumulators and the key-figure printer. If A's admission is not at exactly 0 misses by 16:30, B pairs on it.
3. **Optional rows: what fits and what to cut now.** Fits: cap + band (assumed done at 10:15), the demo-day finder (13 lines; the demo needs it), and the 2-line restart accounting line folded into the printer. **Cut now:** persistence forecast (O2), runtime pad (O4), and the realism column inside the scheduler (O5: quote `r5_chain.py` instead, labelled). Also cut the full terminal layout (K8 shrinks to one formatted trace line per hour), the web dashboard page (K9: tiles on slide 1; revisit at 18:40 only if everything is green), and the 3 repeat measurements. **Stretch, behind a 16:30 gate:** archived forecast + 2 K guard (O3) and the whole-house outage scenario (N1), both on B. B's cumulative midpoint passes capacity at O3 by 0.3 h.
4. **The runtime pad is pure cost inside the team scheduler.** The scheduler has no overrun model, so the pad cannot prevent a miss. With the pad: 0 of 31,896 / 0 of 36,857, coverage 72.95% / 85.56%. Without it: 0 of 31,908 / 0 of 36,771, coverage 73.20% / 85.73% (*computed*, section 4, rows S3p vs S3). Its benefit exists only in `r5_miss_stress.py`.
5. **Smallest change that puts the archived forecast (and an outage) in the dashboard's own figure:** freeze `decide()`'s inputs now with two 168-hour vectors, `fc_demand[0..167]` and `n_avail[0..167]`. Perfect forecast and "all N servers up" are just the default vectors. Then the core diff is 2–3 changed lines inside M6, made today. The archived forecast becomes a driver-side `forecast_vector()` of about 30 lines that both drivers import. The outage becomes a driver-side `--outage` flag of about 8 lines. Retrofitting the outage after the 17:15 freeze costs about 15 core lines plus re-running the trace test and every check (section (b)).
6. **The dashboard's own missed figure reads 0 at every admission stage that has the 2 K guard**: perfect 0 of 31,859 / 0 of 36,736; persistence + guard 0 of 31,471 / 0 of 36,272; archived + guard 0 of 31,908 / 0 of 36,771. Without the guard, persistence gives 73 / 199 and archived 0 / 4. **The guard does the work at this offer level, not the forecast source** (*computed*, section 4). What adds a non-zero, honest line from the team's own code is the outage scenario: house dark 72 h from 15 April, scheduler told, gives **38 of 31,571 / 41 of 36,484**.
7. **Seed 1 against 3-seed means (Transparency).** The scheduler reads one offer file, so its printout will say coverage **73.20% / 85.73%**, utilisation **54.37% / 47.76%**, accepted **94.8% / 93.7%**, and a restart-line break-even of **0.2279 / 0.2287**. The pitch quotes 73.67% / 86.14%, 54.72% / 47.98%, 94.7% / 93.8% and 0.2278 / 0.2286, which are 3-seed means from `r4_headline.py` (*computed*, section 4b). By the plan's own rule ("the scheduler's printout is the authority"), the slide figures change, or carry the label "mean of 3 offer seeds, analysis script". "Read this first" number 4 writes "seed 1; 94.7% / 93.8% accepted", which mixes seed-1 counts with 3-seed acceptance.
8. **Nothing under `analysis/` is in git.** `git status` shows `?? analysis/`, and `git ls-files` lists 22 files, none of them in `analysis/`. The "committed" offer CSV that MUST row M5 reads, and the archived forecast CSV for O3, are not in a fresh clone, so the 14:15 fresh-clone draft check would fail. The offer CSV regenerates byte for byte with `python3 analysis/r4_headline.py --write-offers <path>` (*computed*, section 5). Committing it (310 KB) and `analysis/r2_data/prev_ecmwf_ifs025.csv` (474 KB), or copying them into `data/`, is a team decision and should happen before 14:15.
9. **The outage line in the plan is incomplete.** Seed 1, scheduler told, outage starting on the 15th at 00:00, missed jobs by start month Jan–Dec: N=6, 72 h `[0, 0, 0, 38, 17, 2, 5, 0, 11, 25, 0, 0]`; N=8, 72 h `[0, 0, 0, 41, 12, 7, 1, 13, 9, 7, 0, 0]` (*computed*, section 4). "0 in Nov–Mar" holds. "25–41 in April/October" leaves out N=8 in October (7) and the non-zero May–September values (1–17). Better wording: "0 in November–March, up to 38 / 41 for an outage starting mid-April, 0–25 in other months". The saved script replaces the round-5 critic's unsaved probe, and its April/October values agree with the probe.

---

## (a) Person-hour check

### Method

- **Anchor sizes** are counted, not estimated: code lines (non-blank, not comments, not docstrings) of the function or block in the analysis scripts that implements each rule, found by `ast` and text markers (*computed*, section 1, pasted below). The team's version is assumed to be about the anchor size minus statistics and variant switches, plus a few lines where noted.
- **Rates (assumption):** 40 lines/h when the logic is re-written from an analysis script, 20 lines/h for logic written from a spec. These give the low and high estimates. Each row adds a check time (0.1–1.5 h, *assumption*) for its expected-value check. "AI-assisted" doubles both rates and leaves check time unchanged (*assumption*; the repo's commits carry an AI co-author trailer, so assisted coding is likely but its speed is not measured).
- **Capacity (assumption):** the build windows of each role from 11:30 to 21:00 (lunch 12:15–12:45, dinner 18:00–18:40, draft push 14:45–15:00, C + D draft check 14:15–14:45, D draft submission 14:45–15:30, rehearsals 19:45–21:00 for A, C and D and 20:15–21:00 for B), times a focus factor of 0.75 for interruptions, merges and helping others. Gross / effective: A 6.83 / 5.12 h, B 7.33 / 5.50 h, C 6.33 / 4.75 h, D 5.83 / 4.37 h; all four 19.75 h.
- **Assumed done by 11:30** (the 09:30–11:20 slots of `docs/overnight.md`): M1 permit + tank, O1 cap + band, K3 live driver on a stub with Integration 1, K6 J1 batch loop with checkpoint. If any of these is not green at 11:30, it goes first and the cut line moves up by its hours.

### Rows (section 2 output; "owner" is the owner in the current plan, the revised owners are in (d))

| id | Row | Build class | Anchor (function, code lines) | Team LOC | Person-h unassisted | Person-h AI-assisted | Check (expected value) |
|---|---|---|---|---|---|---|---|
| M1 | R2 heat permit + tank balance | MUST | `r3_policy_check.step_permit` follow part 5 + `run()` tank block 7 | 12 | 0.55–1.10 | 0.40–0.80 | N=6 79.58%, 31,067 server-h |
| M2 | R5 EDF assign, pause the rest, job queue | MUST | `r3_policy_check.run()` EDF execution 18 (+10 queue/trace, *assumption*) | 28 | 0.95–1.90 | 0.60–1.20 | done + missed + open = accepted |
| M3 | R1 expire = missed | MUST | `r3_policy_check.run()` expiry block 10 | 10 | 0.35–0.75 | 0.23–0.50 | no admission: 857 of 33,640 / 1,307 of 39,222 |
| M4 | R6 pin on the demo date, outside the denominator | MUST | `r4_headline.run()` lines with `pin` 13 (+2) | 15 | 0.62–1.25 | 0.44–0.88 | coverage moves < 0.06 points |
| M5 | Offers read from the offer CSV | MUST | `r5_miss_stress.read_offer_csv` 11 | 11 | 0.38–0.80 | 0.24–0.53 | 33,676 / 39,244 offers |
| M6 | R4 admission dry run, perfect forecast | MUST | `r3_policy_check.run()` admission block 75 − statistics 6 − restart-aware 6 − variant switches 7 + `r2_deadline_sim.forward_fail` 22 + 3 + 2 hook lines | 83 | 2.58–5.65 | 1.54–3.58 | exactly 0: 0 of 31,859 / 0 of 36,736 |
| O1 | R3 cap + band | OPTIONAL (default on) | `step_permit` band branch 7 (+2) | 9 | 0.47–0.95 | 0.36–0.72 | 379 / 891 starts (unlimited) |
| O2 | R7 persistence | OPTIONAL, cut-first | `forecast_temps` persist 2 + `demand_from_temps` 8 + lead 3 | 13 | 0.57–1.15 | 0.41–0.82 | 0 of 31,471 / 0 of 36,272 (guard 2 K) |
| O3 | R7 archived ifs025 + 2 K guard, builder outside `decide()` | OPTIONAL, should | `read_prev_runs` 10 + `demand_from_temps` 8 + `fc_demand` 6 + lead 3 + 3 | 30 | 1.25–2.50 | 0.88–1.75 | 0 of 31,908 / 0 of 36,771 |
| O3c | live driver calls the same `forecast_vector()` | OPTIONAL | (*assumption*) | 3 | 0.17–0.40 | 0.14–0.33 | trace test still green |
| O4 | Runtime pad | OPTIONAL, cut-first | `r5_miss_stress.run()` lines with `pad` 1 | 1 | 0.53–1.05 | 0.51–1.02 | re-run every key figure |
| O5 | Accounting lines + two-column printer | accounting | (*assumption* 2 + 1 + 1 + 10) | 14 | 0.60–1.20 | 0.42–0.85 | 0.2279 / 0.2287 (seed 1) |
| O6 | Demo-day finder | (OPTIONAL in the plan; needed for the demo) | `r4_headline.pause_resume_days` 13 | 13 | 0.43–0.90 | 0.26–0.57 | dates from the final run |
| N1 | Whole-house outage, told, driver-side (with the hook) | PROPOSED | `r5_miss_stress.run()` outage block 6 (+2) | 8 | 0.45–0.90 | 0.35–0.70 | 38 of 31,571 / 41 of 36,484 |
| N1x | same, retrofitted into `decide()` without the hook | PROPOSED | outage block 6 + dry-run lines 5 + 4 | 15 | 0.88–1.75 | 0.69–1.38 | plus trace test and all checks again |
| K1 | yearly accumulators + key-figure dict | never cut | `r3_policy_check.run()` return block 17 (+10) | 27 | 0.93–1.85 | 0.59–1.18 | |
| K2 | key-figure printer (7 figures, x of y, BE twice, stage label, restart line) | never cut | (*assumption*) | 30 | 1.00–2.00 | 0.62–1.25 | section 4b values |
| K3 | live driver: own session, SIGSTOP/SIGCONT, `ps` state | never cut | `pause_resume_probe.spawn` 3 + `ps` 3 (+15) | 21 | 1.02–2.05 | 0.76–1.52 | `T` after PAUSE |
| K4 | live replay from the 00:00 snapshot incl. job queue | never cut | (*assumption*; the r3 critic said 30–60 min) | 30 | 1.00–2.00 | 0.62–1.25 | |
| K5 | trace-equality test + SHA-256 | never cut | (*assumption*) | 25 | 0.88–1.75 | 0.56–1.12 | |
| K6 | J1 batch loop, atomic checkpoint, `--resume` | never cut | `pause_resume_probe.worker` 22 (+20) | 42 | 1.30–2.60 | 0.78–1.55 | |
| K7 | checkpoint-restart mode + its test | never cut | `pause_resume_probe.exp_checkpoint` 46 − 9 print lines | 37 | 1.18–2.35 | 0.71–1.43 | |
| K8 / K8s | terminal view of one day / reduced to one trace line per hour | never cut | (*assumption* 40 / 15) | 40 / 15 | 1.25–2.50 / 0.47–1.00 | 0.75–1.50 / 0.29–0.62 | |
| K9 | dashboard page, six tiles from the printer's JSON | OPTIONAL (new row) | (*assumption*) | 40 | 1.25–2.50 | 0.75–1.50 | |

Core `decide()` size from these anchors: **M1–M6 = 159 lines; 198 with cap + band and the archived-forecast builder** (*computed*, section 2). That is above the round-3 critic's 110–150 lines and well above round 3's 80. The admission dry run is 83 of the 159.

### Capacity against load (section 3, pasted in full below)

| Table | Rates | A | B | C | D | All four (capacity 19.75 h) |
|---|---|---|---|---|---|---|
| Current (`docs/overnight.md`) | unassisted | 7.62–15.90 vs 5.12: **no** | 2.25–3.50 vs 5.50: fits | 4.97–10.00 vs 4.75: **no** | 5.50–8.25 vs 4.37: **no** | 20.35–37.65 h |
| Current | AI-assisted | 5.09–10.82: low only | fits | 3.29–6.62: low only | 5.12–7.50: **no** | 15.75–28.45 h |
| Revised (this file) | unassisted | 4.92–10.45: low only | 5.92–11.20: **no** | 5.28–10.60: **no** | 3.25–5.25: midpoint | 19.38–37.50 h |
| Revised | AI-assisted | 3.06–6.73: **midpoint** | 4.56–8.47: midpoint through K2, cut line at O3 | 3.44–6.92: midpoint through K7, cut line at K9 | 3.25–5.25: **midpoint** | 14.31–27.38 h |

Revised rows of the remaining **MUST + never-cut code** (M2–M6, K1, K2, K4, K5, K7, K8s): 10.3–21.3 h unassisted, 6.4–13.5 h AI-assisted (*computed*, section 3 header lines). The revised non-code work of B, C and D is 5.5–9.0 h. That leaves 10.75–14.25 h of the four people's 19.75 h for code. **So the must-build set fits at the AI-assisted midpoint (about 10 h) and does not fit at the unassisted midpoint (about 15.8 h).**

### Verdict

- **MUST list:** keep all six rows. It fits only with the redistribution in (d) and assisted porting from the analysis scripts. Port by reading and re-writing into `decide()`; importing the scripts would make the cross-check circular and break the scripts' own "must not become the scheduler" rule. The scripts are then the regression oracle: section 4 gives the exact counts to hit.
- **If A is behind at 14:15**, the first MUST reduction is R6. The live process follows slot s's heat permit (`k ≥ s`, 5 lines) and is not counted as a job, and the README says "the live process stands for slot s's work; it is not one of the balance's jobs". This saves about 0.3–0.6 h. It re-opens the round-3 critic's objection F3 ("is your live job one of the 32,000?"), so it is a fallback, not the plan.
- **OPTIONAL that fit:** O1 (assumed done), O6 (finder), the restart accounting line inside K2. **Cut now:** O2, O4, O5 inside the scheduler (quote `r5_chain.py`), K8 → K8s, K9 deferred, 3 repeat runs. **Gated:** O3 + O3c + N1 at 16:30.

---

## (b) Smallest change so the dashboard's own missed figure includes the archived forecast (and a whole-house outage)

Diff-sized description. No code.

**Core (`decide(state, obs, params)`, role A, made now inside M6, not later):**
- `obs` carries two lists of length 168 from the first version on:
  - `fc_demand[L]`: demand in kWh the scheduler believes for hour h+L. `fc_demand[0]` is this hour's actual demand. The perfect stage passes the actual demand slice.
  - `n_avail[L]`: servers the scheduler believes are available at hour h+L. The default is `[N] * 168`.
- Execution permit: `step_permit(..., n=obs.n_avail[0], d=obs.fc_demand[0], ...)` instead of `n=N`: **1 changed line**.
- Admission roll-forward: `dF = obs.fc_demand[L]` instead of the actual demand at h+L, and `nav = obs.n_avail[L]` passed as N to the same permit function: **2 changed lines**.
- Nothing else changes in the core. The same-permit-function rule (row X1) is kept automatically.
- **Retrofit cost if the hook is not in now:** about 15 lines in `decide()` (N1x: 0.7–1.8 person-h), plus re-running the trace test and all 17:15 checks.

**Driver side (role B, a data module both drivers import; no core change):**
- `forecast_vector(h, source, guard)` → list of 168 floats, about 30 lines:
  - read `analysis/r2_data/prev_ecmwf_ifs025.csv` (Open-Meteo Previous Runs layout, columns K = 0..7 days before; port of `read_prev_runs`, 10 lines);
  - apply the case formula to each lead series with the heating-day threshold 12 − guard °C (port of `demand_from_temps`, 8 lines), cached per (source, guard);
  - causal lead `min(7, (L + 46) // 24)` and `fc[L] = Fd[lead(L)][(h + L) % 8760]` (3–5 lines). The year-end wrap to January is the same simplification as in the analysis scripts; say so;
  - `source="perfect"` returns the actual demand slice (3 lines).
- Flags `--forecast perfect|ifs025 --guard 2` (2 lines). Printer label (1 line): "forecast = archived ECMWF IFS 0.25° runs (Open-Meteo Previous Runs), issued before each decision, 2 K guard band".
- Live driver: calls the same `forecast_vector(h, ...)` for each demo hour (1–3 lines). The trace test needs no change, because both drivers build identical inputs.
- Outage: `--outage 2025-04-15T00:00,72` builds `n_avail[L] = 0 if start ≤ h+L < start+72 else N` (6 lines). The printer adds a scenario line (2 lines): "scenario: house dark 72 h from 15 Apr, scheduler told: x of y". "Not told" is one more line: `n_avail[0] = 0`, while the future entries stay at N.
- Data: both CSVs must be in the clone (finding 8).

**Expected values to check against** (seed 1, cap + 8 kWh band, restart outside execution; *computed*, section 4):

| Stage | N=6 | N=8 |
|---|---|---|
| Perfect (MUST) | 0 of 31,859; accepted 94.7%; coverage 73.13% | 0 of 36,736; 93.6%; 85.85% |
| Archived ifs025 + 2 K guard | 0 of 31,908; 94.8%; 73.20% | 0 of 36,771; 93.7%; 85.73% |
| + house dark 72 h from 15 Apr, told | 38 of 31,571; 93.8% | 41 of 36,484; 93.0% |
| + house dark 72 h from 15 Apr, not told | 236 of 31,762 | 229 of 36,667 |

**Caveat on "told":** in `r5_miss_stress.run()`, "told" means the scheduler knows the repair end in advance. A real scheduler sees missing heartbeats, not a repair time. Say "scheduler told the outage and its duration", or make the driver assume a fixed 24 h and re-plan (not computed).

**Effort:** the hook costs nothing extra today (counted in M6). O3 + O3c is 1.0–2.1 person-h AI-assisted (1.4–2.9 unassisted), and N1 0.35–0.7 (0.45–0.9).

---

## (c) README table

See [r6-real-vs-analysis.md](r6-real-vs-analysis.md). It covers every key figure and claim in "Read this first": the six tiles and must-have 3, the live demo, workloads and scaling, robustness and realism, and what no script reproduces. Each row says whether it is SCHEDULER, LIVE, ANALYSIS (with command), MEASURED, SOURCED or ASSUMPTION, with a tick column for the 21:00 freeze. It also lists the two fixes from this round (seed-1 values; untracked `analysis/`) and labels the team-written `analysis/one_rack_model.py` as a different machine basis: its header sets `GPU_PER_SERVER = 2` with RTX 4090 cards, consumer-marketplace prices and `--sold 0.80` by default, against the reference server's 4 × RTX PRO 4500.

---

## (d) Revised Saturday table from 11:30 (roles A–D)

A = scheduler core · B = workloads, data inputs and key-figure printer (new) · C = live driver and demo · D = numbers, README, pitch. Draft saved 14:45, submitted 15:00–15:30; feature freeze 21:00; final submission Sun 08:00. Times are *assumptions*; the hours per cell match `r6_build_scope.py` section 3b.

| Time | A | B | C | D |
|---|---|---|---|---|
| **11:30–11:40** | **All four, 10 min:** is Integration 1 green (M1, O1, K3, K6)? **Freeze the `decide()` inputs incl. `fc_demand[0..167]` and `n_avail[0..167]`**, the snapshot format and the printer's JSON keys. Team decision: commit the offer CSV and the ifs025 CSV (or copy them into `data/`) before 14:15 | | | |
| 11:40–12:15 | M2 EDF assign/pause + job queue | M5 offer-CSV loader (shared module); start the J1 energy run (≥ 5 min, plugged) | K8s: one formatted trace line per simulated hour incl. PID state | README skeleton; paste [r6-real-vs-analysis.md](r6-real-vs-analysis.md); use seed-1 values |
| 12:15–12:45 | Lunch | | | |
| 12:45–14:15 | M3 expire, M4 demo-date pin, start M6 admission (perfect) | K1 yearly accumulators + key-figure dict; K2 printer v1 (7 figures, "x of y", stage label, BE twice + restart line); `r3_income.py` with the measured E | K4 live replay from the 00:00 snapshot incl. job queue + offers | assumptions list (edit from `docs/overnight.md`), does-not-pay-off sentences |
| 14:15–14:45 | M6 | scaling write-up (factor ~2, MLPerf rows) | **Draft check, C + D:** fresh clone, README, three commands | |
| **14:45** | **Draft saved.** The printer prints whatever stage is real, with its label ("no admission yet" is fine) | | | |
| 15:00–16:30 | M6 to "exactly 0 missed" (0 of 31,859 / 0 of 36,736) | O3 `forecast_vector()` as a data function, checked alone: day-1 RMSE 1.16 K, bias +0.29 K | K5 trace-equality test + SHA-256, then K7 checkpoint-restart + test | 15:00–15:30 submit the draft; then pitch script |
| **16:30 gate** | **Cut line 1.** M6 not at exactly 0 → B stops O3 and pairs with A until 17:15; O3, O3c and N1 are cut; the missed tile uses the fallback wording for the stage reached. M6 at 0 and K1 + K2 green → B wires O3 (driver only) | | | |
| 16:30–17:15 | consistency checks; snapshot helper for C | O3 wired + O3c (expected 0 of 31,908 / 0 of 36,771); then N1 `--outage` (expected 38 / 41) | K7 | slides draft |
| **17:15** | **Configuration freeze (cut line 2):** no `decide()` edits after this; N1 is cut if not done. A re-runs every check; B prints the final key figures; D copies them (seed 1) into README and slides | | | |
| 17:15–18:00 | O6 demo-day finder on the final run (pin applied), hands date and hours to C | README check on a clean laptop; model-load time; live audio set sized past RESUME | one-command demo for both days | slides |
| 18:00–18:40 | Dinner | | | |
| 18:40–19:45 | demo-blocking fixes only | 60-90 s raw pause recording with C; finish the clean-laptop check | wifi-off run; **cut line 3:** K9 dashboard page only if K5 and K7 are green, otherwise the tiles live on slide 1 | slides, Q&A answers; a pitching mentor if ahead (`docs/event.md` lists pitching mentors on site Sat 11:00–16:00 and 16:00–20:00) |
| 19:45–21:00 | **Three timed rehearsals:** A operator, D presenter, C screen; B joins 20:15 as timer and note-taker | | | |
| **21:00** | **Feature freeze.** Only bug fixes, text (slides may continue until 22:00) and recordings | | | |
| 21:00–24:00 | as in `docs/overnight.md` (fallback recording incl. one checkpoint-restart; voice-over; upload; logged-out link test; final form saved) | | | |
| Sun 07:00–08:00 | on site by 07:00, fresh clone on the pitch laptop, wifi-off run, two rehearsals; **08:00 final submission** | | | |

**Trigger at 11:30:** if Integration 1 (K3 with K6) is not green, A and C pair until it is. O3 and N1 are cut at once, and O6 goes to C. Each hour lost here moves cut line 1 an hour earlier.

**Cut order (new):** K9 dashboard page → N1 outage → O3 archived forecast (+ O3c) → full terminal layout (already K8s) → K7 live (keep it in the recording) → R6 reduced to "follows slot s's permit". Already cut this round: O2 persistence, O4 runtime pad, O5 realism column inside the scheduler, 3 repeat measurements. **Never cut:** M2–M6, K1, K2, K4, K5, one tested checkpoint-restart, O6 (or a hand-picked date from the final trace), the assumptions list, the tested README, the video link.

---

## Pasted output (`python3 analysis/r6_build_scope.py`, 21 Nov 2026)

Section 1 (line census):

```
  permit_follow           5  r3_policy_check.py step_permit() lines 103-109 (cap, kmax, follow)
  permit_band             7  r3_policy_check.py step_permit() lines 110-116 (band branch)
  permit_hold            10  r3_policy_check.py step_permit() lines 117-126 (hold branch, CUT)
  energy                  7  r3_policy_check.py run() lines 329-335 (tank balance, dump)
  expire                 10  r3_policy_check.py run() lines 185-194 (expire = missed)
  adm_block              75  r3_policy_check.py run() lines 201-277 (forecast permits, slack, accept, take-back)
  adm_stats               6  r3_policy_check.py run() lines 201-277 containing summer / mon[m] / off_w (statistics only)
  adm_aware               6  r3_policy_check.py run() lines 220-225 (restart-aware derating, CUT)
  adm_branch              7  r3_policy_check.py run() lines 201-277 containing P["adm"] / arule (variant switches)
  forward_fail           22  r2_deadline_sim.py forward_fail() lines 241-264 (EDF dry run)
  edf_exec               18  r3_policy_check.py run() lines 281-298 (EDF execution, restart 0)
  restart_exec           26  r3_policy_check.py run() lines 299-324 (restart inside execution, CUT)
  pin                    13  r4_headline.py run() lines 103-262 containing 'pin' (R6 demo-date pin)
  offers_csv             11  r5_miss_stress.py read_offer_csv() lines 76-86
  fc_read                10  r2_deadline_sim.py read_prev_runs() lines 92-102
  fc_formula              8  r2_deadline_sim.py demand_from_temps() lines 81-89 (case formula + guard threshold)
  fc_demand               6  r3_policy_check.py fc_demand() lines 148-153
  fc_lead                 3  r3_policy_check.py run() lines containing LEAD / lambda L (causal lead)
  persist                 2  r2_deadline_sim.py forecast_temps() lines 176-177 (persistence)
  pad                     1  r5_miss_stress.py run() lines containing 'pad' (runtime pad)
  outage_exec             6  r5_miss_stress.py run() lines 220-226 (servers up this hour)
  outage_dry              5  r5_miss_stress.py run() lines containing nav / fail_aware (dry run sees the outage)
  outage_gen             17  r5_miss_stress.py outages() lines 161-178 (random failure generator, not needed)
  demo_finder            13  r4_headline.py pause_resume_days() lines 306-319
  run_total             195  r3_policy_check.py run() lines 157-358 (whole yearly loop incl. statistics)
  keyfig                 17  r3_policy_check.py run() lines 342-358 (key-figure dict)
  probe_worker           22  pause_resume_probe.py worker() lines 41-63
  probe_spawn             3  pause_resume_probe.py spawn() lines 66-70
  probe_ps                3  pause_resume_probe.py ps() lines 104-106
  probe_exp_signals      36  pause_resume_probe.py exp_signals() lines 127-162
  probe_exp_checkpoint   46  pause_resume_probe.py exp_checkpoint() lines 165-213
  probe_ckpt_prints       9  pause_resume_probe.py exp_checkpoint() lines containing print(
```

Section 2 totals and section 3 header:

```
  total MUST       159 lines, 5.4-11.4 person-h unassisted, 3.4-7.5 AI-assisted (reduced/alternative rows K8s, N1x not summed)
  total OPTIONAL   123 lines, 5.3-10.7 person-h unassisted, 3.7-7.6 AI-assisted (reduced/alternative rows K8s, N1x not summed)
  total PROPOSED     8 lines, 0.5-0.9 person-h unassisted, 0.3-0.7 AI-assisted (reduced/alternative rows K8s, N1x not summed)
  total NEVER-CUT  252 lines, 8.6-17.1 person-h unassisted, 5.4-10.8 AI-assisted (reduced/alternative rows K8s, N1x not summed)
  core decide() size, MUST rows M1-M6: 159 lines; + cap/band + archived forecast builder: 198

== 3. Saturday from 11:30: capacity vs load per role (FOCUS 0.75 = ASSUMPTION) ==
  already done by 11:30 (ASSUMPTION): M1, O1, K3, K6
  [unassisted] remaining MUST rows M2-M6: 4.88-10.35 h; remaining never-cut code K1, K2, K4, K5, K7, K8s: 5.45-10.95 h
  [AI-assisted] remaining MUST rows M2-M6: 3.04-6.67 h; remaining never-cut code K1, K2, K4, K5, K7, K8s: 3.40-6.85 h
```

Section 3, per-role verdicts:

```
  -- 3a. CURRENT table in docs/overnight.md, unassisted rates --
     role A load 7.62-15.90 h (midpoint 11.76) vs capacity 5.12 h -> does NOT fit
     role B load 2.25-3.50 h (midpoint 2.88) vs capacity 5.50 h -> fits even at the high estimate
     role C load 4.97-10.00 h (midpoint 7.49) vs capacity 4.75 h -> does NOT fit
     role D load 5.50-8.25 h (midpoint 6.88) vs capacity 4.37 h -> does NOT fit
  ALL ROLES: load 20.35-37.65 h vs capacity 19.75 h
  -- 3a. CURRENT table in docs/overnight.md, AI-assisted rates --
     role A load 5.09-10.82 h (midpoint 7.96) vs capacity 5.12 h -> fits at the low estimate only
     role B load 2.25-3.50 h (midpoint 2.88) vs capacity 5.50 h -> fits even at the high estimate
     role C load 3.29-6.62 h (midpoint 4.96) vs capacity 4.75 h -> fits at the low estimate only
     role D load 5.12-7.50 h (midpoint 6.31) vs capacity 4.37 h -> does NOT fit
  ALL ROLES: load 15.75-28.45 h vs capacity 19.75 h
  -- 3b. REVISED table (this round), unassisted rates --
     role A load 4.92-10.45 h (midpoint 7.69) vs capacity 5.12 h -> fits at the low estimate only
     role B load 5.92-11.20 h (midpoint 8.56) vs capacity 5.50 h -> does NOT fit
     role C load 5.28-10.60 h (midpoint 7.94) vs capacity 4.75 h -> does NOT fit
     role D load 3.25-5.25 h (midpoint 4.25) vs capacity 4.37 h -> fits at the midpoint
  ALL ROLES: load 19.38-37.50 h vs capacity 19.75 h
```

Section 3b, AI-assisted, in full:

```
  role A: build windows 6.83 h gross -> 5.12 h effective
     M2 R5 EDF assign, pause the rest (job queue, done/paused ids)       0.60-1.20  cum  0.60-1.20  [MUST]
     M3 R1 expire = missed                                               0.23-0.50  cum  0.82-1.70  [MUST]
     M4 R6 pin on demo date, excluded from denominator                   0.44-0.88  cum  1.26-2.58  [MUST]
     M6 R4 admission dry run, perfect forecast (incl. EDF dry run)       1.54-3.58  cum  2.80-6.15  [MUST]   <-- high estimate passes capacity
     O6 Demo-day finder on the final run (pin applied)                   0.26-0.57  cum  3.06-6.73  [OPTIONAL]
     role A load 3.06-6.73 h (midpoint 4.89) vs capacity 5.12 h -> fits at the midpoint
  role B: build windows 7.33 h gross -> 5.50 h effective
     energy run (>= 5 min, plugged) + r3_income                          0.50-0.75  cum  0.50-0.75  [non-code]
     scaling write-up with MLPerf rows                                   0.50-0.75  cum  1.00-1.50  [non-code]
     model-load time, live audio sizing                                  0.25-0.50  cum  1.25-2.00  [non-code]
     README check on a clean laptop                                      0.50-0.75  cum  1.75-2.75  [non-code]
     M5 Offers read from the offer CSV (both drivers)                    0.24-0.53  cum  1.99-3.27  [MUST]
     K1 Yearly driver accumulators + key-figure dict                     0.59-1.18  cum  2.58-4.45  [NEVER-CUT]
     K2 Key-figure printer (7 figures, x of y, BE twice, label)          0.62-1.25  cum  3.20-5.70  [NEVER-CUT]   <-- high estimate passes capacity
     O3 R7 archived ifs025 + 2 K guard (builder outside decide())        0.88-1.75  cum  4.08-7.45  [OPTIONAL]   <-- midpoint passes capacity (cut line)
     O3c live driver calls the same forecast_vector() (with the hook)    0.14-0.33  cum  4.21-7.78  [OPTIONAL]   <-- midpoint passes capacity (cut line)
     N1 Whole-house outage, scheduler told (driver builds n_avail[0..167])  0.35-0.70  cum  4.56-8.47  [PROPOSED]   <-- midpoint passes capacity (cut line)
     role B load 4.56-8.47 h (midpoint 6.52) vs capacity 5.50 h -> fits at the low estimate only
  role C: build windows 6.33 h gross -> 4.75 h effective
     60-90 s raw pause recording                                         0.25-0.50  cum  0.25-0.50  [non-code]
     wifi-off rehearsal of the one-command demo                          0.25-0.50  cum  0.50-1.00  [non-code]
     K8s reduced: formatted trace line per hour, no layout               0.29-0.62  cum  0.79-1.62  [NEVER-CUT]
     K4 Live replay from 00:00 snapshot incl. job queue + offers         0.62-1.25  cum  1.41-2.88  [NEVER-CUT]
     K5 Trace-equality test + SHA-256 header                             0.56-1.12  cum  1.98-4.00  [NEVER-CUT]
     K7 Checkpoint-restart mode behind a flag + its test                 0.71-1.43  cum  2.69-5.42  [NEVER-CUT]   <-- high estimate passes capacity
     K9 Dashboard page: six tiles from the printer's JSON (static HTML)  0.75-1.50  cum  3.44-6.92  [OPTIONAL]   <-- midpoint passes capacity (cut line)
     role C load 3.44-6.92 h (midpoint 5.18) vs capacity 4.75 h -> fits at the low estimate only
  role D: build windows 5.83 h gross -> 4.37 h effective
     README + real-vs-analysis table (edit r6-real-vs-analysis.md)       0.50-0.75  cum  0.50-0.75  [non-code]
     assumptions list (edit from docs/overnight.md)                      0.50-1.00  cum  1.00-1.75  [non-code]
     does-not-pay-off sentences, description (edit)                      0.25-0.50  cum  1.25-2.25  [non-code]
     pitch script to the second                                          1.00-1.50  cum  2.25-3.75  [non-code]
     slides (4 max; 1 more hour after the freeze if needed)              1.00-1.50  cum  3.25-5.25  [non-code]   <-- high estimate passes capacity
     role D load 3.25-5.25 h (midpoint 4.25) vs capacity 4.37 h -> fits at the midpoint
  ALL ROLES: load 14.31-27.38 h vs capacity 19.75 h
```

Sections 4, 4b and 5:

```
== 4. Expected missed-deadline line of the team scheduler, by stage reached at 21:00 ==
  headline shaped100 offers, seed 1 (= the offer CSV), cap + 8 kWh band, restart outside execution, no pin
  S0 no admission (every offer accepted)               N=6: 857 of 33,640 accepted jobs missed (2.548%), accepted 100.0% of 33,676 offers, coverage 73.81% | N=8: 1307 of 39,222 accepted jobs missed (3.332%), accepted 100.0% of 39,244 offers, coverage 86.09%
  S1 admission, perfect forecast                       N=6:   0 of 31,859 accepted jobs missed (0.000%), accepted 94.7% of 33,676 offers, coverage 73.13% | N=8:   0 of 36,736 accepted jobs missed (0.000%), accepted 93.6% of 39,244 offers, coverage 85.85%
  S2 admission, persistence, no guard                  N=6:  73 of 31,725 accepted jobs missed (0.230%), accepted 94.3% of 33,676 offers, coverage 72.17% | N=8: 199 of 36,682 accepted jobs missed (0.543%), accepted 93.5% of 39,244 offers, coverage 84.45%
  S2g admission, persistence + 2 K guard               N=6:   0 of 31,471 accepted jobs missed (0.000%), accepted 93.5% of 33,676 offers, coverage 72.30% | N=8:   0 of 36,272 accepted jobs missed (0.000%), accepted 92.4% of 39,244 offers, coverage 84.10%
  S3n admission, archived ifs025, no guard             N=6:   0 of 32,122 accepted jobs missed (0.000%), accepted 95.5% of 33,676 offers, coverage 73.54% | N=8:   4 of 36,905 accepted jobs missed (0.011%), accepted 94.1% of 39,244 offers, coverage 85.46%
  S3 admission, archived ifs025 + 2 K guard (plan)     N=6:   0 of 31,908 accepted jobs missed (0.000%), accepted 94.8% of 33,676 offers, coverage 73.20% | N=8:   0 of 36,771 accepted jobs missed (0.000%), accepted 93.7% of 39,244 offers, coverage 85.73%
  S3p S3 + runtime pad 30%, no overrun                 N=6:   0 of 31,896 accepted jobs missed (0.000%), accepted 94.8% of 33,676 offers, coverage 72.95% | N=8:   0 of 36,857 accepted jobs missed (0.000%), accepted 93.9% of 39,244 offers, coverage 85.56%
  S3+H house down 24 h from 15 Jan 00:00, told         N=6:   0 of 31,906 accepted jobs missed (0.000%), accepted 94.8% of 33,676 offers, coverage 73.19% | N=8:   0 of 36,763 accepted jobs missed (0.000%), accepted 93.7% of 39,244 offers, coverage 85.72%
  S3+H house down 72 h from 15 Jan 00:00, told         N=6:   0 of 31,634 accepted jobs missed (0.000%), accepted 94.0% of 33,676 offers, coverage 72.85% | N=8:   0 of 36,396 accepted jobs missed (0.000%), accepted 92.8% of 39,244 offers, coverage 85.25%
  S3+H house down 24 h from 15 Apr 00:00, told         N=6:  38 of 31,886 accepted jobs missed (0.119%), accepted 94.8% of 33,676 offers, coverage 73.16% | N=8:  30 of 36,792 accepted jobs missed (0.082%), accepted 93.8% of 39,244 offers, coverage 85.61%
  S3+H house down 72 h from 15 Apr 00:00, told         N=6:  38 of 31,571 accepted jobs missed (0.120%), accepted 93.8% of 33,676 offers, coverage 72.47% | N=8:  41 of 36,484 accepted jobs missed (0.112%), accepted 93.0% of 39,244 offers, coverage 84.94%
  S3+H house down 24 h from 15 Oct 00:00, told         N=6:  25 of 31,848 accepted jobs missed (0.078%), accepted 94.7% of 33,676 offers, coverage 73.02% | N=8:   7 of 36,672 accepted jobs missed (0.019%), accepted 93.5% of 39,244 offers, coverage 85.54%
  S3+H house down 72 h from 15 Oct 00:00, told         N=6:  25 of 31,775 accepted jobs missed (0.079%), accepted 94.4% of 33,676 offers, coverage 72.92% | N=8:   7 of 36,599 accepted jobs missed (0.019%), accepted 93.3% of 39,244 offers, coverage 85.45%
  S3+H house down 72 h from 15 Apr, NOT told           N=6: 236 of 31,762 accepted jobs missed (0.743%), accepted 94.4% of 33,676 offers, coverage 72.47% | N=8: 229 of 36,667 accepted jobs missed (0.625%), accepted 93.5% of 39,244 offers, coverage 85.07%
  S3+H house down 72 h from 15 Oct, NOT told           N=6: 150 of 31,908 accepted jobs missed (0.470%), accepted 94.8% of 33,676 offers, coverage 73.01% | N=8: 173 of 36,771 accepted jobs missed (0.470%), accepted 93.7% of 39,244 offers, coverage 85.51%

  whole-house outage, told, seed 1, missed jobs by start month (15th, 00:00), Jan..Dec:
    N=6 24 h: [0, 0, 0, 38, 15, 2, 0, 0, 3, 25, 0, 0]  max 38
    N=6 72 h: [0, 0, 0, 38, 17, 2, 5, 0, 11, 25, 0, 0]  max 38
    N=8 24 h: [0, 0, 0, 30, 5, 5, 0, 13, 3, 7, 0, 0]  max 30
    N=8 72 h: [0, 0, 0, 41, 12, 7, 1, 13, 9, 7, 0, 0]  max 41

== 4b. Seed-1 key figures (what a scheduler fed only the seed-1 offer CSV prints) vs the pitch's 3-seed means ==
  N=6 seed 1: coverage 73.20% (pitch 73.67%), utilisation 54.37% (pitch 54.72%), sold 28,575 h (pitch 28,761), electricity 9,501 CHF, heat value 3,040 CHF, break-even 0.2261 CHF (0.2279 with 15-min restart line; pitch 0.2278), accepted 94.8%, starts 896, missed 0 of 31,908
  N=8 seed 1: coverage 85.73% (pitch 86.14%), utilisation 47.76% (pitch 47.98%), sold 33,467 h (pitch 33,626), electricity 11,128 CHF, heat value 3,561 CHF, break-even 0.2261 CHF (0.2287 with 15-min restart line; pitch 0.2286), accepted 93.7%, starts 1,527, missed 0 of 36,771

== 5. Offer CSV reproducibility ==
  r4_headline.write_offers(seed=1) byte-identical to analysis/r4_offers_shaped100_seed1.csv: True
```

Cross-check run (not saved; one-off, `cd analysis && python3 -B -c "import r4_headline as H; ..."`): `r4_headline.run(n, HEADLINE, 'shaped100', s)` per seed gives N=6 coverage 73.198 / 73.864 / 73.963% (mean 73.675%) and N=8 85.729 / 86.463 / 86.216% (mean 86.136%). So the pitch's 73.67% / 86.14% are 3-seed means, and the seed-1 run is the lowest seed for N=6.

Git state check (read-only): `git ls-files | grep -c .` → 22 tracked files, none under `analysis/`; `git status --short` → `?? analysis/`, `?? docs/overnight.md`, `?? docs/research/`, `?? reports/`, `?? research_notes/`.

---

## Limitations

- **No team code was visible.** The repo holds no scheduler yet. "Done by 11:30" is an assumption from the plan's own slots. The person-hour sums are only as good as that assumption and the rates.
- **Rates, check times, the focus factor and the AI-assisted factor are assumptions.** They are anchored on counted lines, not on observed team speed. Lines of code are a weak proxy for debugging time, especially for M6, where the risk is consistency between dry run and executor, not length. The high estimate exists for that reason.
- K2, K4, K5, K8 and K9 have no anchor in the analysis code; their sizes are assumptions.
- Section 4 values hold only if the team uses the same job definitions, the same offer CSV (including its J1/J2 order column), the same permit rule and the same causal lead. Gaps of a few jobs point to a port difference, not necessarily a bug.
- Outage runs: one seed, an outage starting on the 15th at 00:00, 24 or 72 h. "Told" includes knowing the repair time.
- The analysis scripts share code (`step_permit`, `forward_fail`), so their agreement with each other is not independent evidence. Agreement between the team's port and them is evidence for the port only.

## Proposed plan changes (for the rewriter)

See the structured result. Summary: adopt the revised table and cut lines; add the `fc_demand` / `n_avail` input hook to the MUST definition of `decide()`; cut O2, O4 and O5 (in the scheduler) now; gate O3 and N1 at 16:30 on B; move M5, K1 and K2 to B; put seed-1 values on the slides or label the 3-seed means; commit (team decision) the offer and forecast CSVs before 14:15; correct the outage wording; add "the 2 K guard does the work at shaped100" to Q&A 5; label `one_rack_model.py` as a different machine basis.
