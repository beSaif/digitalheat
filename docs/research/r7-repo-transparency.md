# Round 7: repository reproducibility and the transparency package

Weak point: "Repository reproducibility and the transparency package". Nothing under `analysis/` is tracked, the inputs are untracked, the round-6 real-vs-analysis table has faulty rows, and the repo holds two economics bases (open risk 15). The jury weights Transparency at 25%, and the case requires "code in the repository" that others can repeat.

Investigator, Sat 21 Nov 2026, about 11:45–12:30. **Assessment only.** No git write command was run: only `git status`, `git ls-files`, `git check-ignore` and `git archive HEAD` (which reads the repo and writes a tar file in the scratchpad). No existing file was edited. No web request was made (Firecrawl calls: 0). Currency: CHF. Conversion constants come from `analysis/r4_machine.py` (ECB, 20 Nov 2026, 0.8392 CHF per USD). They were sourced in round 1 and not re-opened this round.

New files this round:
- `analysis/r7_critic_probes.py`: saves the critic probes that "Read this first" quotes.
- `analysis/r7_econ_bridge.py`: bridges the team's economics file to the pitch basis.
- [r7-real-vs-analysis.md](r7-real-vs-analysis.md): the corrected README table.

## 1. Result in brief

1. **Minimal commit set: 26 files, 3.07 MB** (section 2). That is 21 scripts and 5 CSVs. Also commit `analysis/r2_data/prev_runs_basel_2025.csv` (474 KB) if any `r2_deadline_sim.py` figure is quoted, such as "a capacity sum gave 166 missed". None of these files needs the network or holds personal names. The largest is 948 KB.
2. **Verified in a clean copy.** I exported `HEAD` (22 tracked files) into the scratchpad and added only the candidate set. All 16 key commands ran there with exit 0 and no network. Every output matched the run in the repo **byte for byte**, apart from a temp-file name and a timing line. The offer CSV regenerates byte-identical inside the clean copy (`r6_build_scope.py` section 5).
3. **What failed in the clean copy, and why:**
   - With only the tracked files, nothing runs: there is no `analysis/` folder.
   - `r6_build_scope.py --loc-only` needs `pause_resume_probe.py`. It reads that file's source to count lines. That is a dependency the import scan does not show.
   - `r2_deadline_sim.py` needs `prev_runs_basel_2025.csv` (its "bestmatch" rows). With the CSV added it runs, and its output is identical to the repo run.
4. **Critic probes saved.** Several "Read this first" figures could not be reprinted in a fresh clone, because they came from critics' scratch scripts:
   - perfect-stage utilisation 54.32% / 47.82% and its restart-line break-even 0.2279 / 0.2286;
   - "not told" winter outages 267–307 / 317–386;
   - cold bias −3 K 0.107% / 0.234%;
   - no-guard 0.08–0.20% / 0.33–0.56% (saturating offers);
   - corrected failure-rate shares 11.8% / 12.9% and 13.4% / 14.6%;
   - heat-to-host 1.820 / 1.979 CHF.

   `python3 analysis/r7_critic_probes.py` now reprints every one of them exactly (section 4).
5. **`r6_machine.py` on disk still prints the misread MTBF.** Its 5-year share incl. maintenance is 11.6% / 13.1%. The corrected 11.8% / 13.4% exist only in `r7_critic_probes.py` section E. The README must cite that section.
6. **One economics basis: the reference server (r4/r5/r6 scripts).** `one_rack_model.py` becomes a labelled sensitivity. The two files differ mainly in hardware cost per kW (8,924 vs 35,429 CHF, a factor of 4.0). They also differ in the sold-hours convention: one_rack's "case break-even 0.2826" is 0.2261 ÷ 0.80, because unsold hours keep running. The bridge reproduces one_rack's 0.947 CHF exactly and reaches the pitch basis (1.595 CHF) in 7 single-input steps (section 5).
7. **No new build scope.** This round adds two read-only analysis scripts and one table. Committing is a team action of a few minutes (commands in section 6). It is not something this loop may do.

## 2. (a) Minimal commit set

Method:
- Import closure: `modulefinder` run over each key script, in the clean copy.
- Plus every file the scripts read (grep for `open(`, `read_text`, `.csv`).
- Plus an empirical run in a clean copy (section 3).

"Network" = the file needs a download to run or to rebuild. "Untracked dep" = it needs another file that is not yet committed.

| Path | Bytes | Why needed | Network? | Untracked dep? |
|---|---|---|---|---|
| `analysis/baseline_sweep.py` | 5,207 | Upper line (79.6% / 92.9%), N=1, break-even; imported by every script | no | reads tracked `data/reference_house_2025_hourly.csv` only |
| `analysis/r1_job_sim.py` | 9,357 | J1/J2 job types; imported by `r2_deadline_sim.py` | no | baseline_sweep |
| `analysis/r2_deadline_sim.py` | 27,068 | Forecast reader, `base()`, offer rates; imported by all headline scripts | no (reads CSVs) | r1_job_sim, `r2_data/prev_ecmwf_ifs025.csv` (every call), `archive_basel_2020_2024_ecmwf_ifs.csv` (offer rates); `prev_runs_basel_2025.csv` only for its own `main()` |
| `analysis/r2_realism.py` | 22,664 | Idle worst case 0.2659 / 0.2814; imported by r3_policy_check | no | baseline_sweep |
| `analysis/r2_fleet_economics.py` | 18,578 | Break-even 0.2261 / 0.3325; imported by r5_pitch_numbers | no | baseline_sweep |
| `analysis/r3_policy_check.py` | 33,148 | `step_permit`, `pol()`; R2 "same function" row X1 | no | r2_deadline_sim, r2_realism |
| `analysis/r3_income.py` | 13,921 | Job pricing constants; imported by r4_headline | no | baseline_sweep |
| `analysis/r4_headline.py` | 29,201 | 3-seed headline, jobs per day, demo days, `--write-offers` | no | r2/r3 scripts + both r2_data CSVs above |
| `analysis/r4_machine.py` | 16,995 | Reference server, scaling factor about 2, list value, share needed | no | baseline_sweep |
| `analysis/r4_tank_layout.py` | 15,714 | Q&A 4 temperatures; imported by r5_chain | no | baseline_sweep |
| `analysis/r5_chain.py` | 19,514 | Realism column 77.6% / 90.6%, installed cost 212,574 CHF | no | r4_machine, r4_tank_layout |
| `analysis/r5_miss_stress.py` | 26,490 | Stress line (GFS/ICON, failures, overrun, outages) | no | r4_headline, offer CSV, `r5_data/*.csv` |
| `analysis/r5_pitch_numbers.py` | 46,947 | Cross-check of the round-4 figures (154 MATCH, 2 DIFF) | no | r2–r4 scripts, r2_fleet_economics |
| `analysis/r6_build_scope.py` | 28,770 | Team-scheduler regression oracle (stages, outages), offer-CSV check | no | r5_miss_stress, **`pause_resume_probe.py` (reads its source)**, offer CSV |
| `analysis/r6_buyer_scenarios.py` | 16,315 | Price per sold server-hour needed, rental anchors, refused work | no | r4_headline, r5_chain |
| `analysis/r6_machine.py` | 17,190 | Realism machine, coolant variants (section 3) | no | r5_chain. **Its own section 2 still uses the misread MTBF.** |
| `analysis/pause_resume_probe.py` | 17,749 | 3.3 ms pause probe source; read by r6_build_scope | no (the optional torch part needs PyTorch) | none |
| `analysis/one_rack_model.py` | 11,033 | Team's economics file, kept as a labelled sensitivity | no | baseline_sweep |
| `analysis/r7_critic_probes.py` | 9,914 | Reprints the "critic probe" figures (new) | no | r5_miss_stress, r6_build_scope, r4_headline, r6_machine, r5_chain |
| `analysis/r7_econ_bridge.py` | 5,649 | Basis 1 → basis 2 bridge (new) | no | one_rack_model, r5_chain |
| `analysis/r3_whisper_energy_probe.py` | 8,104 | J1 laptop measurement (1.3–1.5 Wh per audio-hour). Code only: it **cannot run stdlib-only**. Needs macOS `say`/`ioreg`, the `mlx_whisper` CLI, and a one-time model download | **yes, model download** (first run) | reads tracked docs (case-brief, assumption-limits, event.md) as TTS text |
| `analysis/r4_offers_shaped100_seed1.csv` | 309,869 | The offer file the team scheduler must read (MUST row) | no; regenerable offline from the two r2_data CSVs | — |
| `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv` | 948,154 | 2020–24 weather behind `offer_rates("shaped100")` | rebuild = Open-Meteo archive API (URL in r2-missed-deadlines.md) | — |
| `analysis/r2_data/prev_ecmwf_ifs025.csv` | 473,508 | Archived ECMWF forecasts; read by `R.base()` on every run | rebuild = Open-Meteo Previous Runs API | — |
| `analysis/r5_data/prev_gfs_seamless.csv` | 471,518 | GFS stress forecasts | rebuild = Open-Meteo Previous Runs API | — |
| `analysis/r5_data/prev_icon_seamless.csv` | 468,484 | ICON stress forecasts | rebuild = Open-Meteo Previous Runs API | — |
| **Total** | **3,071,061** | 26 files | | |

Optional additions:
- `analysis/r2_data/prev_runs_basel_2025.csv` (473,718 B): needed only to run `r2_deadline_sim.py` itself, which is cited for "a capacity sum produced 166 missed jobs".
- `analysis/r3_scope_extra.py` (7,956): "one simulated year takes 0.7–5 s" and "restart line within 0.0003 CHF".
- `analysis/r3_creativity_usability.py` (12,136): heat receipt, 3.20 kWh = 1.07 person-days.
- `analysis/r5_model_load_probe.py` (2,793): about 2 s laptop restart; needs mlx.

All are cited in the plan body, but not in "Read this first". The simplest team action, `git add analysis/` (the whole folder, about 4.2 MB; `__pycache__/` is already ignored by `.gitignore`, checked with `git check-ignore`), is acceptable and avoids forgetting a file.

Not needed:
- `r1_servers_choice.py`, `demo_day_timing.py`, `r2_fleet_economics_critic_check.py`.
- `r3_mlperf_power.py`: downloads about 1.3 MB of MLPerf logs, but has `--offline`.

`analysis/r7_forecast_paths.py` appeared during this round from a parallel agent. I did not test it.

**Docs.** The README can link `docs/research/r7-real-vs-analysis.md` and `docs/overnight.md` only if they are committed.
- `docs/research/` is 1.3 MB.
- `docs/overnight.md` is 146,783 B.
- Four critique files contain the local home path, which includes the account's user name:
  - r4-demand-headline-critique.md, line 83;
  - r4-tank-temperatures-critique.md, lines 61, 95, 194;
  - r5-missed-deadline-robustness-critique.md, lines 81, 106;
  - r6-build-scope-audit-critique.md, scratch-script lines.

  The user name matches the public repo owner name, so the risk is low. Still, it is a team call; `analysis/` contains no such path (grep, case-insensitive).
- `docs/event.md` and `docs/submission.md`, already tracked, contain names (open risk 9).

**Large or personal:** no file is above 1 MB. There are no personal names, e-mail addresses or team names in any candidate script or CSV (grep over `analysis/*.py`, `analysis/*.csv`, `analysis/*/*.csv`).

## 3. Clean-copy test (what was run, what failed)

Commands, all from the session scratchpad. `$S` is the scratchpad; the runner script is `$S/r7repro/r7repro_run.sh`, which sets `PYTHONDONTWRITEBYTECODE=1` and logs exit code, seconds and line count:

```
git archive --format=tar HEAD > $S/r7repro/head.tar            # read-only; 22 tracked files, none in analysis/
tar -xf head.tar -C $S/r7repro/tracked_only                    # clone stand-in A: tracked files only
tar -xf head.tar -C $S/r7repro/cand1 ; cp <26 files above> cand1/analysis/...   # stand-in B: + candidate set
r7repro_run.sh <root> <outdir> "name|analysis/<script>.py [args]" ...           # in cand1, then in the repo
cmp out_cand1/<name>.out out_repo/<name>.out
```

| Command (run in cand1) | Exit | Wall s | Same output as repo run? |
|---|---|---|---|
| `python3 analysis/baseline_sweep.py` | 0 | 0.3 | identical |
| `python3 analysis/one_rack_model.py` | 0 | 0.1 | identical |
| `python3 analysis/r2_fleet_economics.py` | 0 | 0.2 | identical |
| `python3 analysis/r2_realism.py` | 0 | 4.4 | identical |
| `python3 analysis/r4_machine.py` | 0 | 0.1 | identical |
| `python3 analysis/r4_tank_layout.py` | 0 | 1.1 | identical |
| `python3 analysis/r5_chain.py` | 0 | 2.9 | identical |
| `python3 analysis/r6_machine.py` | 0 | 1.7 | identical |
| `python3 analysis/r6_build_scope.py --loc-only` | **1** before adding `pause_resume_probe.py` (`FileNotFoundError` in `src()`), 0 after | 0.1 | identical after the fix |
| `python3 analysis/r4_headline.py` | 0 | 36.1 | identical |
| `python3 analysis/r5_pitch_numbers.py` | 0 | 38.0 | identical (154 MATCH, 2 DIFF I6/I9, as in round 5) |
| `python3 analysis/r6_build_scope.py` | 0 | 9.9 | identical except the temp-file name and "(done in 9.8 s)"; **section 5: offer CSV byte-identical: True** |
| `python3 analysis/r6_buyer_scenarios.py` | 0 | 4.8 | identical |
| `python3 analysis/r5_miss_stress.py` | 0 | 185.7 (machine shared with other agents; 141 s in the repo) | identical |
| `python3 analysis/r3_policy_check.py` | 0 | 71.7 | identical |
| `python3 analysis/r2_deadline_sim.py` | **1** (`FileNotFoundError: analysis/r2_data/prev_runs_basel_2025.csv`, right after section 0's header) | 0.1 | with the CSV added (copy cand2): exit 0, 138 s, identical |
| `python3 analysis/r7_critic_probes.py` | 0 | 9.2 | identical to the repo run |
| `python3 analysis/r7_econ_bridge.py` | 0 | 0.1 | — |
| `python3 analysis/one_rack_model.py --sold 1.0` | 0 | 0.1 | prints "case break-even … 0.2261" |

In the tracked-only copy there is no `analysis/` directory, so none of these commands can start. `scripts/build_reference_profile.py` (tracked) was not re-run; it rebuilds the tracked profile, with `--download` for the network.

Not reproducible in a clone by design: the laptop energy measurement and the 3.3 ms pause latency, which are hardware-specific; the prior-art absence; and the round-6 critic probes listed at the end of r7-real-vs-analysis.md.

## 4. Critic probes now saved: `python3 analysis/r7_critic_probes.py` (17.6 s wall on all cores, exit 0)

```
== A. Team-scheduler stages, seed 1 (offer CSV), cap + 8 kWh band, restart outside execution ==
  S1 perfect    N=6: coverage 73.13% util 54.32% accepted 31888 of 33676 (94.69%) missed 0 of 31,859 | elec 9,493 heat 3,038 BE 0.2261 BE15 0.2279 starts 893
  S1 perfect    N=8: coverage 85.85% util 47.82% accepted 36749 of 39244 (93.64%) missed 0 of 36,736 | elec 11,143 heat 3,566 BE 0.2261 BE15 0.2286 starts 1488
  S3 ifs025+2K  N=6: coverage 73.20% util 54.37% accepted 31937 of 33676 (94.84%) missed 0 of 31,908 | elec 9,501 heat 3,040 BE 0.2261 BE15 0.2279 starts 896
  S3 ifs025+2K  N=8: coverage 85.73% util 47.76% accepted 36784 of 39244 (93.73%) missed 0 of 36,771 | elec 11,128 heat 3,561 BE 0.2261 BE15 0.2287 starts 1527
== B. House dark 72 h from 00:00 on the 15th, scheduler NOT told, seed 1 (missed of closed) ==
  N=6: Jan 274, Feb 277, Mar 307, Nov 289, Dec 267
  N=8: Jan 375, Feb 347, Mar 317, Nov 338, Dec 386
== C. ICON debiased and shifted too cold, 2 K guard, seeds 1-5 (pooled % of accepted jobs) ==
  -2 K N=6: missed per seed [6, 0, 0, 0, 0]  pooled 6/160,018 = 0.004%
  -2 K N=8: missed per seed [0, 3, 14, 5, 2]  pooled 24/185,596 = 0.013%
  -3 K N=6: missed per seed [51, 40, 28, 25, 27]  pooled 171/160,413 = 0.107%
  -3 K N=8: missed per seed [97, 84, 85, 82, 90]  pooled 438/186,883 = 0.234%
== D. No guard, archived ifs025, causal flag, seeds 1-5 (% missed of accepted, per seed) ==
  saturating offers   N=6: mean 0.141%  min 0.079%  max 0.200%  (missed [26, 44, 66, 52, 45])
  saturating offers   N=8: mean 0.470%  min 0.329%  max 0.557%  (missed [220, 128, 196, 160, 219])
  shaped100 headline  N=6: mean 0.000%  min 0.000%  max 0.000%  (missed [0, 0, 0, 0, 0])
  shaped100 headline  N=8: mean 0.027%  min 0.011%  max 0.043%  (missed [4, 9, 9, 12, 16])
== E. Share of list value needed, central, every permit hour sold, incl. maintenance ==
  card failure rate: r6_machine.py on disk 0.47%/yr (misread MTBF 1,864,500 h); corrected 1.01%/yr (864,500 h), self-insured in EVERY payback year
  machine   N  5y+m (r6 file)  5y+m corrected  8y+m corrected
  R5        6           11.6%           11.8%            8.2%   (installed 212,574 CHF, 6.28 boxes, cards fail 1,228 CHF/yr)
  PRO6K4    6           13.1%           13.4%            9.4%   (installed 204,747 CHF, 2.23 boxes, cards fail 1,590 CHF/yr)
  R5        8           12.7%           12.9%            8.9%   (installed 275,474 CHF, 8.38 boxes, cards fail 1,637 CHF/yr)
  PRO6K4    8           14.2%           14.6%           10.1%   (installed 265,038 CHF, 2.97 boxes, cards fail 2,120 CHF/yr)
== F. Price per sold server-hour needed for a 5-year simple payback (cold-plate chain, central), shaped100, seed 1 ==
  N=6: heat credited to the operator 1.714 CHF; heat given free to the host 1.820 CHF (installed 212,574 CHF, sold 28,575 h)
  N=8: heat credited to the operator 1.872 CHF; heat given free to the host 1.979 CHF (installed 275,474 CHF, sold 33,467 h)
```

Every value equals the critics' published probe output:
- A and B: round-6 build-scope critique, probe 2.
- C: round-5 missed-deadline critique, P3.
- D: round-5 reproducibility critique, section 2.1.
- E: round-6 machine critique, finding 1.
- F: round-6 buyer critique, probe 1.

The script imports the saved scripts unchanged. Two runtime-only patches are applied in its own process: an added cold-forecast entry in `r5_miss_stress._C`, and the corrected failure rate computed locally.

## 5. (c) One economics basis

`python3 analysis/one_rack_model.py` (team file, run read-only, defaults) against the r4/r5/r6 machine scripts.

### Where they disagree

| Item | `one_rack_model.py` (team) | r4/r5/r6 scripts (loop) |
|---|---|---|
| Servers per house | 1 | 6 and 8 |
| Machine per 1 kW | 2 × RTX 4090 (450 W) + ~100 W host; total power an assumption | 4 × RTX PRO 4500 Blackwell SE, about 0.95 kW at the wall (assumption on sourced TGP) |
| Throughput / work per kWh | none (no benchmark row) | MLPerf v6.1 6.1-0017 / 6.1-0056: about 1,300–1,400 audio-h and 36 M tokens per kWh. **This carries must-have 1 (scaling to the 1 kW reference server).** |
| Hardware cost | 5,924 CHF used rig + 3,000 install = **8,924 CHF per kW** | cold-plate chain, central: 212,574 CHF per house at N=6 = **35,429 CHF per kW** (incl. house integration, storage, liquid cooling) |
| Opex | 300 CHF/yr per server | none in r6_buyer; maintenance + leak reserve + card failures in r6_machine / r7_critic_probes E |
| Unsold hours | sold 80% of **run** hours; the unsold 20% still run and heat | server **off** when unsold (headline convention) |
| Heat | free to the house (heat fee 0); case break-even line credits it | credited to the operator (case formula), heat-to-host as a variant |
| Price basis | renter price, consumer GPU interruptible: Vast.ai 0.347 USD/GPU-h (central) → 0.582 CHF per server-h; ×0.80 platform share = 0.466 to the operator | (i) list value of the work 7.7 / 14.3 / 38.2 CHF per server-h (batch APIs); (ii) rental anchor RTX PRO 4500 0.48–0.72 USD/GPU-h × 0.80 × 4.19 GPU-h = 1.35–2.03 CHF |
| Output: case break-even | **0.2826** CHF per sold hour (= 0.2261 ÷ 0.80) | **0.2261** for every N and sold share |
| Output: price needed | client 0.947 CHF per sold server-h (0.564 USD/GPU-h) | 1.70 / 1.87 (heat credited), 1.82 / 1.98 (heat to host) per sold server-h, N=6 / N=8 |
| Output: verdict | loss of 1,778 CHF/yr, payback "never" at the central price | share of list needed 1.6% (operation) / about 11–12% (5 y); no buyer found |

### Bridge: `python3 analysis/r7_econ_bridge.py` (exit 0)

```
one_rack_model defaults read from its argparse: sold 0.8, platform 0.8, heat fee 0.0, hardware 5,924 + install 3,000, life 5.0, opex 300.0
basis-2 installed cost per house, cold-plate chain, central, N=6 (r5_chain.installed): 212,574 CHF
  step                                                 need CHF/sold h   sold h coverage
  0 one_rack_model as is (client price, N=1)                     0.947    6,103    19.5%
  1 sold direct (platform share 1.0)                             0.757    6,103    19.5%
  2 server OFF when unsold (basis-2 convention)                  0.674    6,103    19.5%
  3 every run hour sold (sold share 1.0)                         0.606    7,629    19.5%
  4 heat credited to the operator (case rule)                    0.499    7,629    19.5%
  5 N = 6 servers, 6 x one_rack capex and opex                   0.629   31,067    79.6%
  6 basis-2 installed cost (cold-plate chain)                    1.653   31,067    79.6%
  7 no separate opex (r6_buyer_scenarios has none)               1.595   31,067    79.6%
== Price side == basis 1 central: 0.347 USD/GPU-h x 2 GPU x 0.8392 = 0.582 CHF per server-h to the client; x 0.8 = 0.466 to the operator
== Hardware per kW == basis 1 8,924 CHF per server (1 kW) incl. install; basis 2 35,429 CHF per kW
```

How to read it:
- Step 0 reproduces one_rack's printed 0.947.
- Step 7 is the follow-policy twin of r6_buyer_scenarios' "aggregator buys every permit hour", which prints 1.60 at N=6.
- The single biggest move is hardware cost per kW (step 6: 0.629 → 1.653).
- Step 2 is approximate: with the server off when unsold, heat is scaled by the sold share.

### Recommendation

**The README and the pitch cite the reference-server basis** (`r4_machine.py`, `r5_chain.py`, `r6_buyer_scenarios.py`, `r7_critic_probes.py` E/F). Reasons:
- It is the only basis with work per kWh. That work-per-kWh figure is what must-have 1 asks for, and what the J1/J2 sizing uses.
- It uses the same sold-hours convention as the scheduler and the break-even tile (0.2261).
- Its installed cost includes the house side.

`one_rack_model.py` stays in the repo as **a labelled sensitivity**. Suggested wording:
- README row: "`one_rack_model.py`: one-server P&L with a used consumer-GPU rig (2 × RTX 4090, about 8,900 CHF per kW installed) and marketplace prices. A sensitivity, not our basis. Its 'case break-even' assumes unsold hours keep running; `--sold 1.0` gives the case's 0.2261."
- Spoken, only if asked: "With a cheap consumer rig the price needed drops to about 0.6 CHF per sold server-hour at six servers, but a marketplace host gets about 0.47 CHF for an RTX 4090 hour, so even that does not pay back" (*computed*, `r7_econ_bridge.py` steps 5 and price side).

Never put 0.2826 next to 0.2261. Never quote one_rack's "−1,778 CHF/yr" as DigitalHeat's result.

Status of one_rack's inputs: the file labels its prices `[SOURCED]`, citing r2-host-income-hardware.md. They were not re-opened this round, so they are *unverified* here (round-6 critic: "a repo read, not a web source").

## 6. (d) README section text, "How to reproduce every number"

Paste this once the files are committed. The first line is the team's own command, to be filled in at the freeze.

```markdown
## How to reproduce every number

Python 3.10+ (standard library only), no network, from the repo root. Figures on slides come from the scheduler (first line); `analysis/` scripts are separate cross-checks, labelled "analysis script" where quoted.

    python3 <team scheduler key-figure command>        # the seven key figures, seed-1 offer file (authority)
    python3 analysis/baseline_sweep.py                  # upper line, unlimited demand, N = 1/6/8 (1 s)
    python3 analysis/r6_build_scope.py                  # expected scheduler values by stage, outages, offer-file check (10 s)
    python3 analysis/r7_critic_probes.py                # perfect-stage figures, not-told outages, forecast bias, corrected cost shares (20 s)
    python3 analysis/r4_headline.py                     # headline contract, 3-seed means, jobs per day, demo days (40 s)
    python3 analysis/r5_pitch_numbers.py                # cross-check of ~150 plan figures: MATCH/DIFF per line (40 s)
    python3 analysis/r5_miss_stress.py                  # forecast, failure, overrun stress, 5 seeds (2-3 min)
    python3 analysis/r4_machine.py; python3 analysis/r5_chain.py; python3 analysis/r6_buyer_scenarios.py   # scaling, realism column, price needed

The offer file `analysis/r4_offers_shaped100_seed1.csv` can be rebuilt offline with `python3 analysis/r4_headline.py --write-offers <path>` (byte-identical). Weather and forecast inputs in `analysis/r2_data/` and `analysis/r5_data/` were downloaded once from Open-Meteo (URLs in `docs/research/r2-missed-deadlines.md`, `r5-missed-deadline-robustness.md`). Not reproducible from a script: the laptop energy measurement (`analysis/r3_whisper_energy_probe.py`, needs macOS and `mlx_whisper`) and the pause latency (`analysis/pause_resume_probe.py`, machine-dependent).
```

Commit commands for the team (I did **not** run them; adding these files is the team's decision at 11:30):

```
git add analysis/baseline_sweep.py analysis/r1_job_sim.py analysis/r2_deadline_sim.py analysis/r2_realism.py \
  analysis/r2_fleet_economics.py analysis/r3_policy_check.py analysis/r3_income.py analysis/r4_headline.py \
  analysis/r4_machine.py analysis/r4_tank_layout.py analysis/r5_chain.py analysis/r5_miss_stress.py \
  analysis/r5_pitch_numbers.py analysis/r6_build_scope.py analysis/r6_buyer_scenarios.py analysis/r6_machine.py \
  analysis/pause_resume_probe.py analysis/one_rack_model.py analysis/r7_critic_probes.py analysis/r7_econ_bridge.py \
  analysis/r3_whisper_energy_probe.py analysis/r4_offers_shaped100_seed1.csv \
  analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv analysis/r2_data/prev_ecmwf_ifs025.csv \
  analysis/r5_data/prev_gfs_seamless.csv analysis/r5_data/prev_icon_seamless.csv
# optional: analysis/r2_data/prev_runs_basel_2025.csv, docs/research/r7-real-vs-analysis.md, docs/overnight.md
```

Check afterwards (C + D, 14:15 draft check): run `git clone` into a fresh folder, then run the commands above there.

## 7. (b) Corrected real-vs-analysis table

Written to [r7-real-vs-analysis.md](r7-real-vs-analysis.md). Rows fixed relative to round 6:

| Round-6 fault (critic F5–F8 / open risk 15) | Fix |
|---|---|
| Seed-1 tiles hard-coded the archived-forecast stage (73.2% / 85.7% etc.) | Both stages given (perfect 73.13% / 85.85%, util 54.32% / 47.82%, accepted 94.69% / 93.64%, BE15 0.2279 / 0.2286, electricity 9,493 / 11,143, heat 3,038 / 3,566). The rule is "copy the printout". Perfect-stage values now come from a saved command (`r7_critic_probes.py` A) |
| No-guard row cited the non-causal `r5_pitch_numbers.py` J2, mixed offer levels, and called the upper end unsaved | Headline 0% / 0.011–0.043%; saturating only 0.08–0.20% / 0.33–0.56%; causal flag; `r7_critic_probes.py` D |
| Not-told row quoted only April | Winter 267–307 / 317–386 added (`r7_critic_probes.py` B), plus the definition caveat (`n_avail[0] = 0` will not reproduce it) |
| "Regenerates with `--write-offers`" without its inputs | Dependencies named; tested byte-identical in a clean copy |
| `one_rack_model.py` called "sourced" / unlabelled | Labelled as a sensitivity, with the 0.2826 vs 0.2261 explanation and the bridge command |
| Forecast-error row pointed at `r2_deadline_sim.py` s.0 (needs an extra CSV) | Points at `r5_pitch_numbers.py` J1 or `r5_miss_stress.py --quick` |
| Card-failure shares were critic-only, and `r6_machine.py` prints the misread MTBF | `r7_critic_probes.py` E; warning not to quote `r6_machine.py` section 2 |
| "Guard removes the misses" | Stage table says archived without guard is already 0 / 4 |

## 8. Proposed plan changes

1. **11:30 team decision:** commit the 26-file set (or `git add analysis/`). Add `docs/research/r7-real-vs-analysis.md` if the README links it. Open risk 15 then shrinks to "the team scheduler's own command".
2. Replace the README-table pointer to r6-real-vs-analysis.md with [r7-real-vs-analysis.md](r7-real-vs-analysis.md).
3. "Read this first": cite `python3 analysis/r7_critic_probes.py` wherever it now says "critic", for these figures:
   - utilisation 54.32% / 47.82% and BE15 0.2279 / 0.2286;
   - not told 267–307 / 317–386;
   - −3 K 0.11% / 0.23%;
   - no-guard 0.08–0.20% / 0.33–0.56%;
   - 11.8% / 12.9% and 13.4% / 14.6%;
   - 1.82 / 1.98.

   The remaining critic-only figures (12.2% / 13.4% with a 3 h service, 2-box 73.9% / 3-box 93.4%, July-sized flat about 14% / 2.27 CHF, pool 7–8 M CHF) keep the label "estimate" or come off slides.
4. One economics basis: the reference server. `one_rack_model.py` becomes a sensitivity with the wording in section 5; never 0.2826 beside 0.2261.
5. Add the "How to reproduce every number" block (section 6) to D's README skeleton (11:40 slot). The 14:15 fresh-clone check runs exactly these commands.
6. Open risk 15 note: `r6_machine.py` section 2 still prints the misread MTBF (11.6% / 13.1%); quote `r7_critic_probes.py` E instead.
