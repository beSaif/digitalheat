# Round 8: team scheduler in the repo, and an independent check of the port

Weak point: "No team scheduler code in the repo yet, and no independent check of the port; every slide figure rests on a printout that does not exist yet" (Transparency 25%; the case requires "code in the repository"; open risks 12 and 15; founder objection 7 of round 7).

Investigator, Sat 21 Nov 2026, about 12:30–13:15. **Planning and assessment only.**
- No git write command was run. Read-only commands only: `git status`, `git ls-files`, `git log`, `git branch -a`, `git diff --stat`, `git show <ref>:<path>`, `git stash list`. No fetch, so the remote branches are as of the last fetch (`.git/FETCH_HEAD`, 11:21).
- No existing file was edited. New files: `analysis/r8_oracle_check.py` and this file.
- No web request was made: 0 WebSearch, 0 WebFetch, 0 Firecrawl. Every number below is *computed* (script and command named), read from a repo file (path named), or an *assumption*.
- Currency: CHF. The only price is the case's electricity price. The script reads it from `data/raw/elcom_iwb_H4_2025_2026.json` (2026, Basel, H4, `total` = 33.25 Rp/kWh = 0.3325 CHF/kWh); the source URL is in `data/README.md` and was not re-opened this round. No conversion is needed.

Status labels as in `docs/overnight.md`: *computed*, *sourced*, *unverified*, *assumption*.

---

## Findings in 10 lines

1. **No team scheduler code exists in the repo or on any fetched branch.** `main` holds 22 tracked files, none of them scheduler code. `analysis/` and `docs/overnight.md` are still untracked at 12:30, so the 11:30 commit decision has not been carried out yet. The only team code outside `main` is on the remote branch `origin/workloads` (fetched 11:21): the real job runner `workloads/` (embed, rerank; SIGSTOP/SIGCONT, SIGTERM → checkpoint → exit 75), a measurement script and an interruption test. It has no scheduler, permit, tank or yearly balance. Code that sits on team laptops and has not been pushed cannot be seen from here.
2. **The plan's job model and the team's job model have split apart (new, high severity).** The plan, the offer CSV and every job-level oracle figure assume J1 = whisper transcription, 0.5 server-h, 24 h deadline, and J2 = LLM generation, 4 server-h, 168 h. The workloads branch defines `embed` (0.90 server-h, 48 h) and `rerank` (0.91 server-h, 4 h), measured on team laptops; its `docs/workloads.md` says "`combined.json`, which the scheduler's catalog uses". If the team scheduler uses that catalog, then 0 of 32,174, 73.53%, 95.6% and the 857 of 33,640 no-admission row do not apply. The same offered work re-sliced into embed/rerank gives about 71.6% / 83.7% coverage and 2,024 / 2,818 misses without admission (illustration, *computed*, section 9 of the script).
3. **Independent check written and run:** `python3 analysis/r8_oracle_check.py`, standard library only, about 10 s wall, exit 0. It imports no analysis module and copies no analysis function. It re-derives the case formulas, the price, the profile, the permit, the tank, EDF, expiry and admission.
4. **Admission-free figures reproduce exactly from first principles.** Matches: total demand 31,231 kWh; 206 heating days; the unlimited-demand balance for N = 1, 6, 8 and 13 (coverage, utilisation, server-hours, electricity, heat value, dumped, break-even 0.2261 / 0.2960); the cap + band starts 379 / 891; and the no-admission row, **857 of 33,640 / 1,307 of 39,222, exactly**.
5. **The check-run row does NOT reproduce from the written spec.** The plan's R4 text ("roll R2(+R3) forward 168 h on the forecast and fill with R5's EDF; take back the newest offers") gives 0 missed, but 0 of **32,272** / 0 of **37,111**, accepted 95.9% / 94.6%, coverage **73.39% / 85.69%**, utilisation 54.51% / 47.73% (reading A). That is −0.14 / −0.41 coverage points and +98 / +88 jobs in the denominator against the oracle.
6. **Cause of the mismatch:** the oracle uses an admission rule the plan never writes down (reading B). It plans the next 168 permits **as if every permitted server ran**, so the tank fills by k × 0.8 kWh whatever the queue holds. It accepts per job type by a deadline-wise slack count, then runs an EDF check on those permits and drops failing new jobs. Re-implemented independently, reading B reproduces the oracle **exactly**: 0 of 32,174 / 0 of 37,023, 95.6% / 94.4%, 73.53% / 86.10%, 54.61% / 47.96%, 0.2261. So the oracle's numbers are internally consistent; the plan's description of the rule is incomplete.
7. **A second unwritten convention:** the band's "after the tank is full" means "once the follow permit has fallen to 0". Read literally (state of charge ≥ 35 kWh), the band gives 1,734 / 2,208 starts instead of 379 / 891. Combined with admission, it gives 33 / 50 missed on the check run (fingerprint table, section (b)).
8. **Three conventions decide "y" in "x of y":** "y" is done + missed in the year (the 36 / 22 jobs still open at year end are excluded), not accepted (32,210 / 37,045). The planned permits wrap to January at year end; without the wrap the run gives 0 of 32,042 / 0 of 36,954 with identical coverage. The oracle has no demo-date pin, while the team's MUST M4 adds one (under 0.06 points, per the plan).
9. **New oracle values for the 14:45 draft stage "no admission yet":** coverage 73.81% / 86.09%, utilisation 54.82% / 47.96%, 28,816 / 33,609 sold server-h, electricity 9,581 / 11,175 CHF, heat value 3,066 / 3,576 CHF, break-even 0.2261, restart line 0.2278 / 0.2286 (*computed*). Check run (reading B): electricity 9,544 / 11,176 CHF, heat value 3,054 / 3,576 CHF, starts 865 / 1,464, restart line 0.2278 / 0.2286.
10. **Build scope:** this file adds none for the team beyond (i) one sentence in the spec (reading B, five lines below) or a tolerance rule, and (ii) the trust checklist in section (c). The juror-runnable draft in section (a) is a subset of the existing MUST and never-cut rows, not new scope. **Flag:** if the team keeps embed/rerank, it needs its own offer file (a generator of about 15 lines, *assumption*), and the J1/J2 oracle table is void for it.

---

## Repo state, read-only (12:30–12:40)

| Command | What it showed |
|---|---|
| `git status --short` | `?? analysis/`, `?? data/raw/basel_wohnviertel.geojson`, `?? docs/overnight.md`, `?? docs/research/`, `?? reports/`, `?? research_notes/`: nothing staged, nothing under `analysis/` tracked |
| `git ls-files` | 22 files: README, `data/` (profile, raw weather, ElCom, city house, MLPerf), `docs/` (case files), `scripts/build_reference_profile.py`. **No scheduler, no driver, no live view** |
| `git branch -a`; `git log --all --oneline` | `main` (HEAD 9c1005e) and `origin/workloads`: 4 commits, the last at 11:19 ("Document Apple M4 battery gauge diagnostic") |
| `git diff --stat main...origin/workloads` | 21 files, +1,273 lines: `workloads/{catalog,jobs,power,run}.py`, `scripts/{measure_workloads,combine_measurements,test_interruption}.py`, `docs/workloads.md`, `data/measurements/*.json`, `data/raw/scifact/*.parquet` (4.5 MB), `requirements-workloads.txt` (torch 2.5.1, sentence-transformers 3.3.1, numpy, pyarrow) |
| `find . -newer docs/case-brief.md -type f` (outside `analysis/`, `docs/research/`) | only `docs/event.md`, `docs/overnight.md`, `data/README.md`, the geojson and `.DS_Store` files; no scheduler file anywhere in the working tree |
| `ls -la analysis/` (newest) | `fleet_scenario.py` (team, 12:20); `r8_guard_heldout.py` and `r8_data/` (parallel round-8 agent); `r8_oracle_check.py` (this round) |

What a juror can run today from a clone of `main`: `python3 scripts/build_reference_profile.py`. Nothing else: no analysis mirror (untracked), no scheduler. From `origin/workloads` (after a venv with torch): the real jobs, the measurement and the interruption test. No yearly balance.

---

## (a) What a juror can clone and run at the 14:45 draft

### Minimum that is honest and runnable

The draft does not need admission. It needs **one stdlib command that prints the seven key figures from the team's own code, with a stage label**, plus the live driver on a stub. Ranked by what is realistic at 14:45 (Saturday table: A has M2 at 11:40–12:15 and M3/M4 plus a started M6 by 14:15; B has K2 v1 and M5):

| Draft level | What runs | Printout must say | Expected seed-1 values (*computed*, `python3 analysis/r8_oracle_check.py`, sections 3 and 5) |
|---|---|---|---|
| **D2 (target)** | yearly driver with offers + EDF + expiry, **no admission yet**; live driver on a stub | "stage: no admission yet (every offered job accepted)" | 857 of 33,640 / 1,307 of 39,222 missed (2.55% / 3.33%); coverage 73.81% / 86.09%; dumped 0; utilisation 54.82% / 47.96%; break-even 0.2261 (restart line 0.2278 / 0.2286) |
| D1 (fallback) | yearly balance with permit + tank + cap/band, **every permit hour sold** | "stage: yearly balance without jobs: unlimited demand, declared; missed deadlines not modelled yet" | coverage 79.55% / 92.94%; dumped 0; 31,055 / 36,281 server-h; utilisation 59.08% / 51.77%; starts 379 / 891; break-even 0.2261 |
| D3 (stretch) | check run with admission | "stage: admission, check run on the recorded 2025 weather (not a forecast)" | 0 of 32,174 / 0 of 37,023 only with reading B; 0 of 32,272 / 0 of 37,111 with the literal R4 text (section (b)) |

Live part at every level: the live driver imports the same core and controls **a stub process** (a stdlib loop that writes an atomic checkpoint) by default, with `--job embed` switching to the real `workloads.run` job when a venv with torch exists. The juror can then run the live demo without installing 4.5 MB of parquet, torch and a 180 MB model download (`docs/workloads.md` on the workloads branch states "Models download from Hugging Face on first run (~180 MB)").

### The one command (names are placeholders for whatever the team calls its files)

```
python3 scheduler/year.py --n 6 --offers data/offers/shaped100_seed1.csv
```

Requirements for it to work in a fresh clone of the **pushed remote**:
- the offer file is committed (today it is the untracked `analysis/r4_offers_shaped100_seed1.csv`; copying it to a tracked path or committing `analysis/` both work);
- only the standard library is needed; the same file runs `--n 8`;
- the header prints the git commit, the SHA-256 of the core file, the offer file, N, stage and pin (on/off).

### README lines for the draft (paste; replace the bracketed parts)

```markdown
## Run it

    python3 scheduler/year.py --n 6     # seven key figures for the reference house, one command, standard library, ~[x] s
    python3 scheduler/live.py --date 2025-07-15 --stub      # same core pauses/resumes a real process (stub job, no install)
    python3 scheduler/live.py --date 2025-07-15 --job embed # same, with the real embedding job (needs the venv in docs/workloads.md)

**State of this draft ([time], Sat 21 Nov):** [stage label exactly as printed, e.g. "no admission yet: every offered job is accepted"].
- Jobs per day come from a contract we sized to the house's expected heat (offer file `[path]`, seed 1), not from a customer.
- [If D1:] Missed deadlines are not modelled yet: this stage assumes unlimited jobs and says so.
- [If D2:] Missed deadlines are shown without admission control; the final version refuses work it has no heat for.
- The live demo controls a stub process unless `--job embed` is given; the stub stands for the work of one server slot, and does not perform it.
- Figures in `analysis/` are separate exploratory scripts used as cross-checks, not this scheduler. `python3 analysis/r8_oracle_check.py` recomputes the key figures without sharing any code with either.
```

Why these limits matter for the jury: the case asks that "a model that assumes unlimited jobs must say so" (must-have 1) and that "the same scheduler code that produces the yearly balance must also control at least one real running job" (must-have 2). The stub line keeps the second claim honest until the real job is wired. The "not this scheduler" line answers round-7 founder objection 7.

---

## (b) Independent oracle check: `analysis/r8_oracle_check.py`

### What is independent and what is not

| Part | Source of the rule | Shares code with `analysis/`? | Result |
|---|---|---|---|
| Price, heat value | ElCom JSON in the repo, case "price ÷ 2.5" | no | 0.3325 / 0.1330 CHF/kWh |
| Demand | case formula applied to the temperatures (not the CSV's demand column), plus the CSV column | no | 26,850.5 kWh on 206 days; CSV identical within 0.00005 kWh per hour (rounding) |
| Permit, tank, unlimited balance | case text + R2 | no | all match |
| Cap + band | R3 text | no | **match only after adopting convention C1 (below)**; literal text gives 1,734 / 2,208 starts |
| EDF, expiry, offer reader | R1, R5 text; CSV header | no | no-admission row matches exactly |
| Admission, reading A | literal R4 text, my own design | no | 0 missed; differs from the oracle (table below) |
| Admission, reading B | **the rule was learned by reading `r7_forecast_paths.run` and `r2_deadline_sim.forward_fail` after reading A failed to match; re-written, not imported or copied** | logic shared, code not | exact match |

So the check is fully independent for everything except the admission rule. For admission it independently confirms that reading B's numbers follow from reading B, and it shows that the written spec does not pin them down.

### Comparison with the plan's oracle table (seed 1, offer CSV, cap + 8 kWh band, restart outside execution)

| Figure | Plan (docs/overnight.md, Key numbers) | Independent, literal R4 (A) | Independent, reading B | Verdict |
|---|---|---|---|---|
| Total demand, heating days | 31,231 kWh, 206 | 31,230.5, 206 | — | match |
| Unlimited N=6: coverage, util, srv-h, elec, heat, BE | 79.6%, 59.1%, 31,067, 10,330, 3,306, 0.2261 | 79.58%, 59.11%, 31,067, 10,330, 3,306, 0.2261 | — | match |
| Unlimited N=8 | 92.9%, 51.8%, 36,281, 12,063, 3,860, 0.2261 | 92.94%, 51.77%, 36,281, 12,063, 3,860, 0.2261 | — | match |
| Unlimited N=1 / N=13 always on | 19.5%, 87.1%, 7,629 / 100%, 59,839 kWh dumped, 0.2960 | 19.54%, 87.09%, 7,629 / 100%, 59,839, 0.2960 | — | match |
| Cap + 8 kWh band, unlimited: starts, coverage | 379 / 891; 79.55% / 92.94% | 379 / 891; 79.55% / 92.94% (with C1) | — | match (C1) |
| Offers in file | 33,676 / 39,244 | 33,676 / 39,244 | — | match |
| No admission: missed of closed | 857 of 33,640 / 1,307 of 39,222 | 857 of 33,640 / 1,307 of 39,222 | — | **exact** |
| Check run: missed of closed | 0 of 32,174 / 0 of 37,023 | 0 of **32,272** / 0 of **37,111** | 0 of 32,174 / 0 of 37,023 | A: DIFF (denominator); B: exact |
| Check run: accepted | 95.6% / 94.4% | **95.9% / 94.6%** | 95.6% / 94.4% | A: DIFF |
| Check run: coverage | 73.53% / 86.10% | **73.39% / 85.69%** | 73.53% / 86.10% | A: DIFF (−0.14 / −0.41 points) |
| Check run: utilisation | 54.61% / 47.96% | **54.51% / 47.73%** | 54.61% / 47.96% | A: DIFF |
| Check run: break-even | 0.2261 | 0.2261 | 0.2261 | match (structural) |

Every DIFF has one cause: the admission rule. Both readings give exactly 0 missed. Reading A accepts more jobs (+98 / +88) but sells fewer server-hours (28,649 vs 28,705 at N=6). My reading of that (*unverified*, not counted per type) is that A's take-back keeps more short J1 jobs and fewer 4 h J2 jobs.

### Unwritten conventions the team needs to hit the oracle exactly

| # | Convention (as the oracle does it) | What the plan text says | Effect if the team does otherwise (*computed*) |
|---|---|---|---|
| C1 | Band: "full" = the follow permit has fallen to 0 (less than 0.8 kWh of room); then k = 0 until soc ≤ 27 kWh or soc < demand | "after the tank is full" | starts 1,734 / 2,208 (unlimited); with admission 33 / 50 missed, because the planner and executor then disagree |
| C2 | Admission plans permits as if all are used (tank charged by k × 0.8), not the queue's own execution | "roll R2(+R3) forward ... and fill with R5's EDF" | reading A row above |
| C3 | Acceptance per job type in the hour's arrival order (the `first` column), k = floor(min slack from the deadline on ÷ job size); then an EDF check on the planned permits drops the first failing new job, or the newest | "take back the newest offers until no accepted job is forecast to fail" | part of reading A |
| C4 | "y" = done + missed in the year; open jobs at year end excluded | "accepted jobs whose deadline fell in the year" | printing accepted gives "of 32,210 / 37,045" |
| C5 | Planned permits wrap to January for targets after 31 Dec, `(h+L) mod 8760` | stated only in r7-scheduler-forecast.md | no wrap: 0 of 32,042 / 0 of 36,954, coverage unchanged |
| C6 | No demo-date pin in the oracle rows | M4 pin is MUST for the team | under 0.06 coverage points (plan, `r4_headline.py` section 5); denominator excludes the pinned job |
| C7 | Expiry before admission; a job may work in hour t only while t < deadline; EDF ties by arrival order | R1, R5 | deadline one hour later or earlier: 858 / 889 no-admission misses at N=6 (fingerprints) |

**Reading B in five spec lines** (for A, if the team wants the exact oracle; *assumption*: about 25 lines in `decide()`, the same size as the slack-plus-EDF-check block it replaces):
1. Planned permits `cf[0..167]`: `cf[0]` = this hour's permit. For L ≥ 1, call the same permit function on `fc_demand[L]` with the band state carried, and charge the planning tank with `cf[L] × 0.8` (as if every permitted server ran), then subtract `min(demand, tank)`.
2. `slack[L]` = Σ `cf[0..L−1]` − remaining work of queued jobs with deadline ≤ h + L.
3. For each job type in the hour's arrival order: accept `k = floor(min(slack[dl:]) / size)` (at most the offered count), then subtract `k × size` from `slack[dl:]`.
4. EDF check on `cf` (each job at most 1 server-hour per hour, and only while hour < deadline). While a job fails, drop the first failing new job, or the newest new job if no failing job is new.
5. Report "x of y" with y = done + missed in the year.

**Recommendation:** either A adopts reading B (exact regression), or the oracle target becomes "0 missed, coverage within 0.5 points, accepted within 0.5 points" for any reading. Decide at the 15:00 slot; do not chase an exact 32,174 with the literal text.

### Fingerprints of likely port slips (section 8 of the script; one convention changed at a time)

| Slip | N | No admission: missed of closed | Check run (B): missed of closed | Accepted | Coverage | Utilisation | BE |
|---|---|---|---|---|---|---|---|
| none (reference) | 6 | 857 of 33,640 | 0 of 32,174 | 95.65% | 73.53% | 54.61% | 0.2261 |
| none (reference) | 8 | 1,307 of 39,222 | 0 of 37,023 | 94.40% | 86.10% | 47.96% | 0.2261 |
| band "full" read as soc ≥ 35 kWh | 6 | 717 of 33,641 | **33** of 32,255 | 95.88% | 73.38% | 54.50% | 0.2261 |
| same | 8 | 1,125 of 39,222 | **50** of 37,137 | 94.69% | 85.92% | 47.86% | 0.2261 |
| unsold permit hours still run | 6 | 1,232 of 33,630 | 0 of 31,707 | 94.29% | 79.55% | 59.08% | **0.2465** |
| same | 8 | 1,432 of 39,211 | 0 of 36,649 | 93.47% | 92.94% | 51.77% | **0.2455** |
| job may still run in its deadline hour (+1 h) | 6 | 858 of 33,640 | 0 of 32,201 | 95.73% | 73.56% | 54.63% | 0.2261 |
| deadline 1 h earlier | 6 | 889 of 33,640 | 0 of 32,095 | 95.41% | 73.56% | 54.64% | 0.2261 |
| FIFO instead of earliest deadline first | 6 | **2,806** of 33,624 | **767** of 31,753 | 94.44% | 70.84% | 52.62% | 0.2261 |
| same | 8 | **3,969** of 39,232 | **1,192** of 37,085 | 94.53% | 83.25% | 46.38% | 0.2261 |

The no-admission row is the sharpest single test: every slip moves it, and it does not depend on the admission reading. Make 857 / 1,307 the first exact regression target. It is reachable at the D2 draft stage, before M6.

### Invariants the team printout must satisfy (any reading, any forecast stage)

Checked here on the independent runs (section 7, all PASS):
- **I1** coverage ≤ the unlimited-demand coverage with the same N and the same cap/band (79.55% / 92.94%).
- **I2** dumped = 0 under the never-dump permit.
- **I3** sold server-h ≤ permit server-h ≤ N × 8,760, and utilisation = sold h ÷ (N × 8,760), because servers are off when unsold.
- **I4** offered = accepted + refused; accepted = done + missed + open; y = done + missed.
- **I5** heat identity: used + dumped + tank at year end = 0.8 × sold h (to 1e-6 kWh). Hence break-even = 0.2261 + 0.1330 × tank_end ÷ sold h, which prints 0.2261 at 4 decimals. Any other break-even under the case column means a slip, such as unsold hours running (0.2465).
- (Plus I6/I7 in the script: on the check run, missed = 0 exactly.)

### Illustration: the team's own job types (section 9; not an oracle)

Same hourly offered server-hours as the shaped100 file, re-sliced 50/50 by work into embed (0.90 h / 48 h) and rerank (0.91 h / 4 h), Poisson, `random.Random(1)` (*computed*; the job sizes and deadlines are the team's *assumptions* in `workloads/catalog.py` on the workloads branch):

| N | Stage | Offered | Accepted | Missed of closed | Coverage | Utilisation |
|---|---|---|---|---|---|---|
| 6 | no admission | 32,927 | 100% | 2,024 of 32,814 | 71.63% | 53.20% |
| 6 | check run (A and B identical here) | 32,927 | 94.2% | 0 of 30,889 | 71.59% | 53.17% |
| 8 | no admission | 38,821 | 100% | 2,818 of 38,806 | 83.77% | 46.67% |
| 8 | check run (A and B identical here) | 38,821 | 93.1% | 0 of 36,129 | 83.73% | 46.64% |

To check a scheduler fed the team's own offers, write them as `hour,server_hours,deadline_h` (one row per offer) and run `python3 analysis/r8_oracle_check.py --offers-long <file> --n 6`. Self-test: the shaped100 CSV converted to this format reproduces section 5 exactly (output pasted below).

---

## (c) Trust checklist: five lines before any number goes on a slide

1. **Provenance:** the printout header shows the git commit (clean for the core file), the SHA-256 of the core, the offer file, seed, N, the stage label and pin on/off. The live driver prints the same SHA-256.
2. **Identities:** dumped = 0; used + dumped + tank_end = 0.8 × sold h; sold h ≤ permit h ≤ N × 8,760; offered = accepted + refused; accepted = done + missed + open. "y" in "x of y" is done + missed, never accepted.
3. **Money:** break-even prints 0.2261 (= 0.3325 − 0.8 × 0.1330, plus 0.1330 × tank_end ÷ sold h). The restart line = (electricity − heat value) ÷ (sold h − 0.25 × starts): 0.2278 / 0.2286 expected. Electricity = sold h × 0.3325; heat value = used × 0.1330.
4. **Regression:** the same code with admission off prints exactly 857 of 33,640 / 1,307 of 39,222 (J1/J2 offers). The check run prints 0 missed and coverage at most 79.55% / 92.94%; its figures equal 0 of 32,174 / 0 of 37,023 and 73.53% / 86.10% exactly with reading B (pin off), or within 0.5 points otherwise.
5. **Independent cross-check:** `python3 analysis/r8_oracle_check.py` ends with "DIFF/FAIL lines counted ...: 0". With the team's own job types, use `--offers-long`. Any mismatch is looked up in the fingerprint table before copying, and a number that is not on the printout does not go on a slide.

---

## Proposed plan changes

1. **Decide the job model now (A + B, 5 minutes at the next sync).** Either the balance uses the plan's J1/J2 (whisper / LLM, offer CSV), and the workloads branch's embed/rerank stay the measured must-have-1 jobs with a stated mapping, or the balance uses embed/rerank and the J1/J2 oracle table is replaced. Then the team needs its own offer file plus `--offers-long` as the cross-check. Today the plan and the team code describe different jobs, and the jury sees both.
2. **Write C1–C5 into the spec** ("Scheduler scope" / "Admission rule"), with reading B in five lines, or change the M6 target to "0 missed; coverage and accepted within 0.5 points of the oracle". The current text cannot reproduce 0 of 32,174.
3. **First exact regression target = the no-admission row** (857 / 1,307). It is available at the D2 draft, independent of the admission reading, and the most sensitive to EDF, expiry and band slips.
4. **14:45 draft = D2** (fallback D1), with the stage label and the README lines in section (a). Make the stub the live driver's default, with `--job embed` as the real job, so a juror can run both commands without torch.
5. **Add the new oracle values** to the Key numbers table: no-admission coverage 73.81% / 86.09%, utilisation 54.82% / 47.96%, electricity 9,581 / 11,175 CHF, heat 3,066 / 3,576 CHF; check-run electricity 9,544 / 11,176 CHF, heat 3,054 / 3,576 CHF, starts 865 / 1,464, restart line 0.2278 / 0.2286 (*computed*, `r8_oracle_check.py` section 5).
6. **Replace the "oracle shares code" caveat** in open risk 15 with: "admission-free figures and the no-admission row are reproduced by an independent script; the check run is reproduced only under the admission rule written in the spec (reading B)".
7. **Carry out the commit**: `analysis/` is still untracked at 12:30. Add `analysis/r8_oracle_check.py` to the commit set; it needs only tracked data plus the offer CSV.
8. **The trust checklist** (section (c)) goes into the 19:00 freeze row: B runs it before D copies numbers.

## Build-scope flags

- No new build scope for the MUST set. Reading B is a specification of M6, not an extra row; whether it is larger than the literal reading is an *assumption* (about the same size).
- Live stub mode: about 10–15 lines in C's live driver (*assumption*). It replaces a torch dependency for the juror; it is cut-safe because the real job stays behind `--job embed`.
- Embed/rerank offer generator, only if the team keeps those job types: about 15 lines (*assumption*). This is new scope created by the split, not by this check.

## Commands run (all from the repo root, macOS, Python 3.13.12)

```
git status --short; git ls-files; git branch -a; git log --all --oneline; git stash list
git log origin/workloads --format='%h %ad %s' --date=iso; git diff --stat main...origin/workloads
git show origin/workloads:docs/workloads.md | head -80     # also workloads/catalog.py, run.py, jobs.py, README.md, combined.json
python3 analysis/r8_oracle_check.py --quick               # sections 1-4, 0.1 s, exit 0
python3 analysis/r8_oracle_check.py                       # all sections, 10.5 s wall (44 s CPU), exit 0
python3 analysis/r8_oracle_check.py --offers-long <scratch>/r8_scheduler_in_repo_offers_long_n6.csv --n 6   # self-test
```

Development note: the first full run used the literal band reading (379 → 1,734 starts, DIFF). The band was then changed to C1 after reading the analysis permit function. Reading B was added after reading A mismatched. Both changes are visible in the script as documented options (`SLIP["band_literal"]`, `reading="A"|"B"`).

## Pasted output (`python3 analysis/r8_oracle_check.py`, Sat 21 Nov ~13:05; MATCH lines of section 2 trimmed)

```
== 1. Inputs re-derived from the case text ==
  price: ElCom 2026 IWB Basel H4 total = 33.25 Rp/kWh = 0.3325 CHF/kWh; heat value = price / 2.5 = 0.1330 CHF/kWh
  space heating from temperatures (case formula): 26,850.5 kWh on 206 heating days; CSV column 26,850.5 kWh; max abs hourly diff 0.00005 (CSV rounded to 4 decimals)
  hot water 4,380 kWh = 12.00 kWh/day; total demand 31,230.5 kWh
  MATCH total demand kWh                                 independent  31,230.5487   plan  31,231.0000   (tol 1)
  MATCH space heating kWh                                independent  26,850.5487   plan  26,851.0000   (tol 1)
  MATCH heating days                                     independent     206.0000   plan     206.0000   (tol 0)
  case cross-check: one server-day = 24 x 1.0 x 0.8 = 19.2 kWh (case: 19.2); coldest-hour servers = 10 / 0.8 = 12.5 (case: 12.5)

== 2. Unlimited demand (every permit hour sold), follow, no cap/band ==
  N   coverage   dumped   util    srv-h    elec CHF  heat CHF  BE CHF/h   used+dump+soc_end-heat
  1     19.54%        0   87.09%     7629       2537       812  0.2261     +3.69e-10
  6     79.58%        0   59.11%    31067      10330      3306  0.2261     -6.55e-10
  8     92.94%        0   51.77%    36281      12063      3860  0.2261     +7.46e-10
  13   100.00%    59839  100.00%   113880      37865      4154  0.2960     +6.98e-09
  (25 MATCH lines against the plan's unlimited table, 0 DIFF)
  break-even identity (never dump, lossless): PRICE - 0.8 x PRICE/2.5 = 0.2261 + 0.1330 x soc_end / sold_h

== 3. Unlimited demand with cap + 8 kWh band ==
  N=6: starts follow 1732, cap+band 379; coverage 79.55%; srv-h 31055
  MATCH N=6 starts cap+band (unlimited)                  independent     379.0000   plan     379.0000   (tol 0)
  MATCH N=6 coverage cap+band (unlimited) %              independent      79.5503   plan      79.5500   (tol 0.005)
  N=8: starts follow 2208, cap+band 891; coverage 92.94%; srv-h 36281
  MATCH N=8 starts cap+band (unlimited)                  independent     891.0000   plan     891.0000   (tol 0)
  MATCH N=8 coverage cap+band (unlimited) %              independent      92.9372   plan      92.9400   (tol 0.005)

== 4. Offer file ==
  N=6: 33,676 offers (29,993 J1, 3,683 J2), offered work 29,728.5 server-h = 56.6% of N x 8760; 92.3 jobs/day
  MATCH N=6 offers in file                               independent  33,676.0000   plan  33,676.0000   (tol 0)
  N=8: 39,244 offers (34,848 J1, 4,396 J2), offered work 35,008.0 server-h = 50.0% of N x 8760; 107.5 jobs/day
  MATCH N=8 offers in file                               independent  39,244.0000   plan  39,244.0000   (tol 0)

== 5. Year with jobs: EDF + expire (+ admission dry run on recorded demand), cap + 8 kWh band ==
  reading A = plan the queue's own execution 168 h ahead (literal R4 text); reading B = plan permits as if all are used, slack count + EDF check
  N rd adm  wrap  offered accepted  acc%   done  missed  open  closed  coverage  util    sold-h  permit-h  elec   heat   BE      BE15    starts
  6 -  no   yes   33,676   33,676 100.0 32,783    857    36  33,640   73.81%  54.82%    28816    31883   9581   3066  0.2261  0.2278    855
  8 -  no   yes   39,244   39,244 100.0 37,915  1,307    22  39,222   86.09%  47.96%    33609    38603  11175   3576  0.2261  0.2286   1462
  6 A  yes  yes   33,676   32,308  95.9 32,272      0    36  32,272   73.39%  54.51%    28649    32006   9526   3048  0.2261  0.2278    879
  8 A  yes  yes   39,244   37,133  94.6 37,111      0    22  37,111   85.69%  47.73%    33452    38825  11123   3559  0.2261  0.2286   1468
  6 B  yes  yes   33,676   32,210  95.6 32,174      0    36  32,174   73.53%  54.61%    28705    31971   9544   3054  0.2261  0.2278    865
  8 B  yes  yes   39,244   37,045  94.4 37,023      0    22  37,023   86.10%  47.96%    33611    38606  11176   3576  0.2261  0.2286   1464
  6 B  yes  no    33,676   32,042  95.1 32,042      0     0  32,042   73.53%  54.61%    28705    31971   9544   3054  0.2261  0.2278    865
  8 B  yes  no    39,244   36,954  94.2 36,954      0     0  36,954   86.10%  47.96%    33611    38606  11176   3576  0.2261  0.2286   1464

== 6. Compare with the plan's oracle table ==
  MATCH N=6 no admission: missed  857 / closed 33,640;  MATCH N=8 no admission: missed 1,307 / closed 39,222
  -- reading A --  (literal R4 text; differences are a different admission rule, not a bug: not counted)
  [reading A lines compressed here; the script prints one MATCH/DIFF line per figure]
  N=6: missed MATCH 0; closed DIFF 32,272 vs 32,174; accepted DIFF 95.94 vs 95.6; coverage DIFF 73.39 vs 73.53; util DIFF 54.51 vs 54.61; BE MATCH 0.2261
  N=8: missed MATCH 0; closed DIFF 37,111 vs 37,023; accepted DIFF 94.62 vs 94.4; coverage DIFF 85.69 vs 86.10; util DIFF 47.73 vs 47.96; BE MATCH 0.2261
  -- reading B --
  MATCH N=6 check run: missed                            independent       0.0000   plan       0.0000   (tol 0)
  MATCH N=6 check run: closed (denominator)              independent  32,174.0000   plan  32,174.0000   (tol 0)
  MATCH N=6 check run: accepted %                        independent      95.6468   plan      95.6000   (tol 0.05)
  MATCH N=6 check run: coverage %                        independent      73.5306   plan      73.5300   (tol 0.005)
  MATCH N=6 check run: utilisation %                     independent      54.6138   plan      54.6100   (tol 0.005)
  MATCH N=6 check run: break-even CHF/h                  independent       0.2261   plan       0.2261   (tol 5e-05)
  MATCH N=8 check run: missed                            independent       0.0000   plan       0.0000   (tol 0)
  MATCH N=8 check run: closed (denominator)              independent  37,023.0000   plan  37,023.0000   (tol 0)
  MATCH N=8 check run: accepted %                        independent      94.3966   plan      94.4000   (tol 0.05)
  MATCH N=8 check run: coverage %                        independent      86.0978   plan      86.1000   (tol 0.005)
  MATCH N=8 check run: utilisation %                     independent      47.9609   plan      47.9600   (tol 0.005)
  MATCH N=8 check run: break-even CHF/h                  independent       0.2261   plan       0.2261   (tol 5e-05)

== 7. Invariants (I1-I7) ==  all PASS for reading A and reading B, N=6 and N=8 (28 lines)

== 8. Fingerprints of likely port slips ==   (table in section (b) above, printed verbatim by the script)

== 9. ILLUSTRATION: embed 0.90 h / 48 h + rerank 0.91 h / 4 h ==  (table in section (b) above)

DIFF/FAIL lines counted (reading B and admission-free rows only): 0
```

Self-test of the team-offers mode (shaped100 N=6 converted to one row per offer):

```
Independent model on .../r8_scheduler_in_repo_offers_long_n6.csv, N=6, cap + 8 kWh band, recorded demand as forecast
  stage                 offered accepted   missed of closed  open  coverage  util   sold-h  dumped  BE      BE15
  no admission           33,676   33,676      857 of  33,640    36   73.81%  54.82%    28816     0.0  0.2261  0.2278
  check run, reading A   33,676   32,308        0 of  32,272    36   73.39%  54.51%    28649     0.0  0.2261  0.2278
  check run, reading B   33,676   32,210        0 of  32,174    36   73.53%  54.61%    28705     0.0  0.2261  0.2278
```
