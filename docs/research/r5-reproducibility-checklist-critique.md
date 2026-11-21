# Round 5 critique: pitch-number reproducibility and the single machine basis for income

Critic role: a sceptical DigitalHeat founder. Under review: `analysis/r5_pitch_numbers.py`, `docs/research/r5-pitch-number-checklist.md` and `docs/research/r5-reproducibility-checklist.md`. I made no edits to existing files and did not touch git. One web fetch (ECB). 0 Firecrawl calls. Scratch files are in the session scratchpad and all start with `r5critic_repro_`.

## 1. Re-runs

| What | Command | Result |
|---|---|---|
| Investigator script | `python3 analysis/r5_pitch_numbers.py --md` | exit 0, 38.8 s wall (the investigator measured 41.6 s), 188 lines: 154 MATCH, 2 DIFF (I6, I9), 32 context. Every value is the same as in the investigator's checklist. |
| Earlier scripts | `python3 analysis/{r4_machine,r4_tank_layout,r2_realism,r2_fleet_economics,r4_headline}.py` | Diffed against the saved scratch outputs `r4mach/r4mach_out.txt`, `r4tank_out.txt`, `r2_realism_out.txt`, `hostincome_fleet_out.txt` and `r4demand_critic_rerun.txt`: identical. Only the `time` line of r4_headline differs. |
| ECB rate | opened <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html> | Reference date 20 November 2026. EUR/USD 1.0990, EUR/CHF 0.9223, so 0.8392 CHF per USD. Confirmed. |
| Rows with no saved command before round 5 | `grep "none saved"` in the checklist | 38 hits. One is the legend line, so 37 rows. Confirmed. |
| Round-4 critic values the script re-implements | compared with r4-tank-temperatures-critique.md (lines 43-55) and r4-demand-headline-critique.md (line 33) | 853 h, 64.3 / 73.0 (with loss), 29.5 / 31.2, 59.2 and 74.99 all match. |

## 2. What breaks

### 2.1 The proposed miss-rate rewording is wrong (claim c12, plan change 2)

The investigator's J2 lines run `r2_deadline_sim.run`. The round-2 critic showed that this simulator uses a **non-causal** heating-day flag: it looks up to 23 h into the future (r2-missed-deadlines-critique.md, finding 2). The adopted policy uses the **causal** flag (`r4_headline.HEADLINE`, `r3_policy_check.pol(causal=True)`).

The investigator's status text says the 0.6% upper end "came from 2024 runs". That is false. The 2024 runs gave 0.146% (N=6) and 0.151% (N=8). The 0.5-0.6% values come from the causal-flag and bias-removed variants for 2025.

I reproduced the no-guard rate with saved functions only, on the current policy: `python3 <scratchpad>/r5critic_repro_noguard.py`. The script calls `r4_headline.run(n, r3_policy_check.pol(fc="ifs025", guard=0.0, rule="band", band=8.0, cap1=True, causal=...), demand, seed)` for seeds 1-5. Results:

| Saturating offers, no guard, seeds 1-5 | N=6 mean (min-max) | N=8 mean (min-max) |
|---|---|---|
| Causal flag (the adopted rule) | 0.141 (0.079-0.200) | **0.470 (0.329-0.557)** |
| Non-causal flag | 0.194 (0.064-0.266) | 0.306 (0.278-0.388) |
| `shaped100` headline offers, causal, no guard | 0.000 | 0.027 (0.011-0.043) |

Conclusions:
- The plan's "roughly 0.1-0.6% without the guard" **stands**, and saved code now reproduces it.
- Changing it to "0.1-0.4%" would quote the leaky simulator and understate N=8 by about a third.
- The 0.6 needs one saved command. Fold this call into `r5_pitch_numbers.py` section J, in place of or beside the r2 run.

### 2.2 The new income figure makes the pitch more optimistic, not more honest (c8, c10, plan change 3)

The 80.9k / 94.0k reproduce. But on the same lines the script also prints H7.6: a margin of 74.4k CHF a year and a **simple payback of 2.7 years** at 20% operator share (3.1 y at N=8). The investigator's summary leaves this out. Moving the scenario to the reference server raises the old basis by half because of the following (computed with `r4_machine.list_value('central','central')` and the headline's sold hours):
- J1 list value is 23.69 CHF per server-hour and J2 only 4.82. The mix is 50/50 by server-hours, yet **82.5% of the list value is transcription**.
- That J1 volume is 19.9 M audio-hours a year per house, about 16 archives the size of SRF's (1.25 M audio-hours) per basement per year. No buyer is named.
- If the work is LLM generation only, the same headline hours at 20% bring 27.7k CHF a year: a margin of 21.2k and a simple payback of 9.5 years, beyond the 5-year life assumed.
- J1 throughput is the Cisco blade (6.1-0017, 1,411 audio-h per kWh) divided by the estimated wall power of a *different* 2U box. The 2U HPE box measured 5% lower (1,341). So "reference-server basis" is a blade on a 2U power budget, about 5% optimistic for J1.

A founder hears "pays back in under 3 years" and asks why every hosting firm isn't doing this. Lead with share needed (1.6% / about 11%). If any CHF figure is shown, put three things next to it: the 82% transcription share, the 19.9 M audio-hours, and the LLM-only payback of 9.5 years.

### 2.3 "154 MATCH" overstates independent reproduction (c1)

- The "plan" strings are hard-coded by the same author who wrote the computation. I checked every MATCH token against `docs/overnight.md`: 11 MATCH rows contain tokens that are not in the plan. J2.6 and J2.8 (0.146 / 0.097 / 0.267, ...) come from the round-2 output. I9b (59.2 / 29.5 / 31.2) comes from the round-4 critic table. 11.0 (G12), 21.5 (G13) and 9518.66 (K5) also appear nowhere in the plan. For these rows, MATCH means "matches earlier research output", not "matches the plan".
- About 12 MATCH rows only echo typed constants or literal arithmetic: A2, A3, G10, G18b (a literal tuple compared with itself), K1, K3, K4, K5, K6, G22, G23, and E1 (equal to the price by construction). They show the constant was typed in. They do not show that a sourced number was re-checked.
- The coverage is still near-complete. One Key-numbers figure is missing: the round-1 pause probe (SIGSTOP to state T, median 3.3 ms; checkpoint survives 10 SIGKILLs). `analysis/pause_resume_probe.py` exists but is not listed.

### 2.4 Minor

- I9 "about 30%" against 29.5%: the plan wrote "about". That is not a rounding slip and needs no edit. "Triples" against 3.4 times is fine as "more than triples".
- I6: the plan's 1.6 came from subtracting rounded table values (78.0 - 76.4). The exact difference is 1.54, so the investigator is right: 1.5. N=8 is 1.3.
- The fixed-contract rows depend on monkeypatching `r2_deadline_sim.offer_rates`. That works now, under spawn and with `--procs 1`, but it breaks quietly if r4_headline stops resolving the function through the module.
- The plan strings describe the round-4 state. Once the plan or the scheduler changes, the DIFF lines will flood. The script is a cross-check of the analysis, not the source of slide numbers.
- During my session, `git status` gained modified tracked files (.gitignore, data/README.md, docs/README.md, docs/case-brief.md, docs/event.md) and `data/raw/city_house/`. Neither I nor the investigator's script caused this: the script only prints. Someone else is editing the repo in parallel.

## 3. Verdict summary

- **Survives:** c2, c4, c5, c6, c7, c9, c11, c13, c14, c15, c16 (URL re-opened), c17, c18.
- **Survives with caveat:** c1 (MATCH inflated by echoes and non-plan strings), c3 (not a slip), c8 and c10 (2.7-year payback hidden, 82.5% J1, Cisco throughput).
- **Rejected:** c12. The 0.6% is reproducible with the causal flag. The attribution to 2024 is wrong.
