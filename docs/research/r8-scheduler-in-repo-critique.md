# Critique of round 8: team scheduler in the repo, independent oracle check

Critic (sceptical DigitalHeat founder), Sat 21 Nov 2026, 12:38–12:55 by the wall clock. Planning and assessment only. No git write command was run, no existing file was edited, and no web request was made (0 WebSearch, 0 WebFetch, 0 Firecrawl). The only file written is this one. Scratch probes are in the session scratchpad and are not team files.

Reviewed: `docs/research/r8-scheduler-in-repo.md`, `analysis/r8_oracle_check.py`, `docs/overnight.md` (Admission rule, Run policy, job types, oracle table), and `origin/workloads` (read with `git show`).

## Verdict in five lines

1. The repo facts hold. At 12:38 there are 22 tracked files and no scheduler. `analysis/` is untracked. `origin/workloads` has the job runner (embed/rerank, SIGSTOP/SIGCONT, exit 75) and no permit, tank or balance code. The job-model split (embed 0.90 h / 48 h and rerank 0.91 h / 4 h against J1 0.5 h / 24 h and J2 4 h / 168 h) is real, and it is the most useful finding.
2. The script re-runs. Exit 0, 13.5 s wall and 50 s CPU here, every printed number the same as in the research file, `DIFF/FAIL ... 0`.
3. **"Independent" is overstated.** The two conventions that decide the job-level figures were not derived from the written spec. Both were learned by reading the analysis code after the first attempt failed to match: band "full" = follow permit at 0 (C1), and admission reading B. So the no-admission row (857 / 1,307) and the check-run row (32,174 / 37,023) are a second port of the analysis code, not an independent derivation. Only demand, the unlimited follow balance and the offer counts reproduce from first principles without help.
4. **The weak point is not fixed.** There is still no team printout. Every comparison is analysis code against analysis code. The round adds instruments: invariants, fingerprints and a checklist. It adds no evidence about the team scheduler.
5. Two fingerprint rows are half-slips: the band read literally with admission (33 / 50 missed), and FIFO with admission (767 / 1,192). The slip changes the executor but not the planner, so these numbers measure a disagreement between planner and executor, not a team that ported the slip consistently.

## Re-run

`python3 analysis/r8_oracle_check.py`: exit 0, 13.46 s wall, 49.9 s user. Sections 1–9 are identical to the pasted output in the research file.

**Timestamps.** The research file says "about 12:30–13:15" and "pasted output ~13:05". Its own mtime is 12:36:13 and the script's is 12:32:54. The stated times are later than the files themselves. That is a small transparency defect, but it is the kind of thing a juror holds against a "reproducible" claim. Fix it to real times.

## Critic probes (scratch `r8_scheduler_in_repo_critic_probe.py`, imports r8_oracle_check, N=6/8, seed-1 profile)

**P1: the band's "full", unlimited demand, cap + 8 kWh band (starts / coverage)**

| Reading of "full" | N=6 | N=8 |
|---|---|---|
| C1: follow permit at 0 (oracle) | 379 / 79.55% | 891 / 92.94% |
| soc ≥ 35 kWh, literal | 1,734 / 79.58% | 2,208 / 92.94% |
| soc ≥ 34.2 kWh (one server of room left) | 502 / 79.43% | **2,270** / 92.74% |
| soc ≥ 34 kWh | 526 / 79.41% | **2,300** / 92.72% |
| soc ≥ 33 kWh | 561 / 79.45% | **2,477** / 92.81% |

- The literal 1,734 / 2,208 is confirmed. It is close to plain follow (1,732 / 2,208) because a never-dump permit almost never lands exactly on 35.000 kWh, so the literal band barely ever triggers. It is an artefact more than a reading.
- More important: at N=8, every reasonable soc-threshold reading gives **more** starts than having no band at all (2,270–2,477 against 2,208). The "band reduces starts" claim at N=8 holds only under C1. Write C1 into the spec, and do not put "891 starts" on a slide without the convention.

**P2: per-type accepted, N=6, check run** (from the queue the executor sees, outside dry runs)

| | J1 accepted | J2 accepted | total | sold h |
|---|---|---|---|---|
| Reading A | 28,698 | 3,610 | 32,308 | 28,649 |
| Reading B | 28,570 | 3,640 | 32,210 | 28,705 |

This confirms c24: A keeps 128 more J1 jobs and 30 fewer J2 jobs. It is now *computed* rather than *unverified*.

## Code review findings in `r8_oracle_check.py`

- **Half-slips.** With `SLIP["band_literal"]`, only `year_with_jobs` sets holding at soc ≥ 35; `planned_permits` uses `permit()`, which then never holds. With `SLIP["fifo"]`, only `edf_fill` uses FIFO; `edf_on_capacity_fails` stays EDF. So the check-run cells of these two fingerprint rows (33 / 50 and 767 / 1,192) mix two rules, and a team that ported the slip in both places would see different numbers. The no-admission cells (717 / 1,125 and 2,806 / 3,969) are clean fingerprints.
- **Break-even is not a test.** It equals 0.3325 − 0.8 × 0.1330 = 0.2261 by construction for any never-dump policy with unsold hours off. Matching it shows nothing about the scheduler. Checklist line 3 ("break-even prints 0.2261") catches one slip class only (unsold hours running).
- **The restart line and starts are single-source.** The script defines `k_run = ceil(work)`, so one 0.5 h J1 job counts as one start. The plan's restart-line oracle values come from analysis scripts for other stages and were never compared with these. Label the new 0.2278 / 0.2286 as single-source.
- **Section 9: readings A and B give identical results in every column for embed/rerank.** This is not explained. It may be genuine, since 4 h rerank deadlines dominate and both rules then reject the same jobs, but it was not investigated. Do not cite it as evidence that the reading does not matter.
- **Tolerances.** The unlimited N = 1, 6, 8 rows compare against the plan's 1-decimal values with a tolerance of 0.05 points, which is loose but adequate. The check-run rows use 0.005 points, which is a real test.

## What is still unanswered (founder view)

See `founder_objections` in the structured result. In short:
- the live job (embed) is not a job type in the yearly balance;
- the check run reaches 0 missed because the dry run sees the true future;
- 891 starts depends on a convention;
- the denominator matches neither the plan's definition nor "accepted";
- at 12:38 there is no pushed team code, while the Saturday table had M2 due at 12:15;
- a 24-site fleet dashboard scenario (`analysis/fleet_scenario.py`, 12:20) is being built before any scheduler exists.
