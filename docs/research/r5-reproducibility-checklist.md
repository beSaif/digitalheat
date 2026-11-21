# Round 5: every pitch number reproducible from one saved script; income on one machine basis

Investigator for weak point 2 of round 5: "Headline and comparison figures are not all reproducible from saved scripts; income sits on two machine bases" (Transparency & reproducibility 25%; must-have 3 "computing income"). Written Sat 21 Nov 2026. Plans and assesses only: no git operation, no existing file edited, nothing of the scheduler, dashboard or demo built.

**Deliverables (new files only):**
- `analysis/r5_pitch_numbers.py`: one command that prints every number in "Read this first" and "Key numbers" of `docs/overnight.md` with a label, the plan's value, a status and MATCH / DIFF.
- [r5-pitch-number-checklist.md](r5-pitch-number-checklist.md): the table number → label → value → earlier command → status → matches plan.
- This file: method, commands, findings, the income recomputation, plan changes, and the script output.

**Web:** none used this round. No search or fetch was needed: every input is already a constant in a saved script, with its URL from an earlier round. Sourced constants are marked "sourced (URL), not re-opened this round". **Firecrawl calls used: 0 of 0.**

Currency CHF. 1 USD = 0.8392 CHF, from ECB reference rates of 20 Nov 2026 (EUR/CHF 0.9223 ÷ EUR/USD 1.0990; *sourced* in round 1: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>).

## 1. Result

| | |
|---|---|
| Command | `python3 analysis/r5_pitch_numbers.py` (add `--md` for table rows, `--procs 1` without multiprocessing, `--skip-r2` to leave out the 10 round-2 years) |
| Run | 21 Nov 2026, exit 0, 41.6 s wall, 274 s CPU on this laptop; seeds 1–3 (headline), 1–5 (round-2 rows) |
| Lines | **188: 154 MATCH, 2 DIFF, 32 context** |
| DIFF | I6 "5 kWh usable costs 1.6 points" → **1.5**; I9 70/55 lower bound "about 30%" → **29.5%** (rounds to 29) |
| Before this round without a saved command | **37 checklist rows** (two of them, G13 and G15, partly; flat customer, fixed contract, radiator lower bounds, 5% interest, ex-VAT, GPU value, peak bandwidth, USD per GPU-hour, shaped120/150, 2025-01-13 idle permits, 0.148 CHF, 0.6–2.5 servers, 9.4 M audio-hours, `dhw_direct_share` 37/45 proxy). All 37 now reproduce in the saved script, at the values the critics printed |
| Still not reproducible from a saved script | (a) the 0.6% upper end of "roughly 0.1–0.6%" no-guard misses (2024 runs by the round-2 critic); (b) the laptop measurement 1.3–1.5 Wh per audio-hour and 25–27× real time (hardware, `analysis/r3_whisper_energy_probe.py`, not re-run); (c) "core size 110–150 lines" (a critic's reading) |

## 2. Method

1. Read `docs/case-brief.md`, `docs/assumption-limits.md`, `docs/overnight.md` (all of it), `data/README.md`, `analysis/baseline_sweep.py`, and the scripts and critique files that the plan cites.
2. Listed every number in "Read this first" and "Key numbers" that is used in the pitch or Q&A. Matched each to the saved script that prints it, or found that none does.
3. Re-ran every saved script the plan cites and compared the output with the outputs saved by earlier rounds (section 3).
4. Wrote `analysis/r5_pitch_numbers.py`. It imports the existing scripts unchanged. Where a number came from a critic's scratch file, it re-implements the same logic:
   - fixed contract: monkeypatches `r2_deadline_sim.offer_rates` with `fix6_` / `fix8_` prefixes, as the critic's `r4demand_critic_probe.py` did;
   - radiator lower bound: a copy of the critic's `sim_ret()`;
   - interest: annuity factor i ÷ (1 − (1+i)^−y);
   - payback at interest: y = −ln(1 − inst·i ÷ margin) ÷ ln(1+i).
5. Each figure is printed next to the plan's figure. MATCH means the value, rounded to the last digit the plan shows, equals it. Where the plan says "about X", the script prints the exact value on one line and the value rounded to X's precision on the next.
6. The income scenario was recomputed on the reference server (section 5).

Limits of the check: the "plan" strings in the script were typed by me from `docs/overnight.md`. A typo there would show as a false DIFF, never as a false MATCH, because both sides are printed. Numbers outside "Read this first" and "Key numbers" were not checked; section 6 lists the ones I saw.

## 3. Commands run and whether earlier outputs reproduce

| Command | Wall time | Result |
|---|---|---|
| `python3 -B analysis/baseline_sweep.py` | 0.2 s | exit 0; every Key-numbers row (N=1/6/8/13, tank 10/140, N=2) as in the plan |
| `python3 -B analysis/r4_machine.py` | 0.05 s | exit 0; **byte-identical** to the investigator's saved output (scratchpad `r4mach/r4mach_out.txt`) and the critic's run (`r4refmach_crit_run.txt`) |
| `python3 -B analysis/r4_tank_layout.py` | 1.0 s | exit 0; **identical** to the saved `r4tank_out.txt` |
| `python3 -B analysis/r2_fleet_economics.py` | 0.1 s | exit 0; **identical** to the saved `hostincome_fleet_out.txt` |
| `python3 -B analysis/r2_realism.py` | 4.2 s | exit 0; **identical** to the saved `r2_realism_out.txt` |
| `python3 -B analysis/r3_income.py` | 0.05 s | exit 0; 0.3375 (section 5B) and the 4.298 / 9.359 / 30.704 list values as cited |
| `python3 -B analysis/r3_creativity_usability.py` | 0.1 s | exit 0; heat receipt 3.20 kWh = 1.07 person-days |
| `python3 -B analysis/r4_headline.py` | 36.2 s | exit 0; **identical** line for line to the round-4 critic's rerun (`r4demand_critic_rerun.txt`); only the appended timing line differs |
| `python3 analysis/r5_pitch_numbers.py --md` | 41.6 s | exit 0; output in section 8 |
| Not run: `r2_deadline_sim.py` in full (several minutes) | — | its section 0 (RMSE, bias) and the section 2 no-guard rows are recomputed directly by `r5_pitch_numbers.py` (J1, J1b, J2) and match the saved `r2-missed-deadlines-output.txt` |
| Not run: `r3_whisper_energy_probe.py` | — | a laptop measurement that loads whisper; its 1.5 Wh value is a constant (`r3_income.E_PROBE`), echoed as K3 with status *measured, not re-run* |

Temporary outputs are in the scratchpad with the prefix `r5repro_`. Nothing was written to the repo except the three new files.

## 4. "Read this first", item by item (IDs refer to the checklist and the script output)

| Plan item | Numbers | IDs | Status |
|---|---|---|---|
| 10-line plan, 2 (6 vs 8) | +12.5 points; +0.2 under one contract; "triples starts" | C12, D6b, D6g | computed; **"triples" is 3.4×** |
| 10-line plan, 5–6 (machine) | 0.95 kW; HPE 5% lower; 1.3–1.5 Wh laptop; 0.7 Wh; factor about 2; 1,300–1,400 audio-h/kWh | G1, G4, K3, G3, G5/G5b, G2/G2b | assumption / computed / measured (not re-run) / computed |
| 10-line plan, 9 (break-even, income) | 0.2261; 0.3325; 1.6%; about 11% | C10, E1, G11, G11g | computed |
| 5 opening numbers | 73.7 / 86.1; 79.6 / 92.9; 53.7 / 60.5; 0 kWh; 54.7 / 48.0; 0 of 31,908 / 0 of 36,771; 94.7 / 93.8; 33 of 28,928 / 11 of 35,991; 0.2261 (0.2278 / 0.2286); 0.3325 | C1b, B4.6/B4.8, D5b, C2, C3b, C6, C4, D2d, C10, C11, E1 | all computed, all MATCH; the flat-customer line (D5b) was a critic probe until now |
| Realism sentence | 100% → 82%; 79.6% → 77.6%; 50 °C; return ≤ 40 °C; 0.2293 | I1b, B4.6, I1, I13, I1d | computed; 40 °C is the critic's reading of the CDU approach (interpretation) |
| Q&A 1 (income) | 7.7 / 14.3 / 38.2; 1.6%; 200,000 CHF; 11% / 7% (12% / 9% at 5%); 32–36% LLM only; 1.5 CHF; 0.43 USD per GPU-h; 0.41–0.92 USD; 80% host share | G9, G11, G7d, G11g, G13b, G21, G16, G18b, K6 | computed; renter prices and host share sourced earlier; the 5% rows were critic one-liners until now |
| Q&A 2 (why 6) | 13 points for 7 points; 12.5; 17%; 73.9 vs 73.7; 41.2%; 2,944 vs 854; 0.6–2.5 servers; 19.5% / 32.7%, 87.1% / 73.0% | B13, C12, C13, D6c, D6e, D6f, K1, B4.1, B10 | computed (K1 from the sourced 5–20% rule) |
| Q&A 3 (idle heat) | 0.2278 / 0.2286; 0.2659 / 0.2814; nothing sold in summer | C11, F1, F1b | computed; 15 min and 17.6% transfer are assumptions |
| Q&A 4 (temperatures) | 55 → 50 °C; 34.9 kWh; 47 / 55 °C; 82.2%; about 850 h; 44–45 °C; 5 kWh costs 1.6 points | I13, I4, I13, I5, I8a, I8b, I6 | computed; **I6 is 1.5 points** |
| Q&A 5 (forecast) | RMSE 1.16 / 2.85 K; 0 missed in 3 seeds; 12–13 at 120–150%; 33 / 11 at 200%; 0.1–0.6% without guard | J1, C6, D3d, D2d, J2 | computed; **2025 runs give 0.10–0.39%; the 0.6% came from unsaved 2024 runs** |
| Still unverified | SRF archive = 6% of a house-year; 34,000 CHF per server; 6 input per output token | H8b, G7a, K4 | computed / computed / assumption |

All Key-numbers tables (unlimited demand, headline, comparison rows, break-even, reference server, "does not pay off", realism column) are covered row by row in the checklist (sections B–K of the script).

## 5. Computing income on one machine basis (new)

**Problem.** The plan leads with the "share of list value needed", computed on the reference server (`r4_machine.py`: J1 at 1,411 audio-hours per kWh and J2 at 35.89 M tokens per kWh, central wall power 0.955 kW). The CHF scenario beside it (53.6k / 62.6k CHF a year) came from `r4_headline.money()`, which prices J1 at laptop efficiency (667 audio-h per kWh) and J2 at the B200-slice efficiency (56.07 M tokens per kWh). These are two machines.

**Fix.** `r5_pitch_numbers.py` section H prices the headline run's sold hours per job type with `r4_machine.list_value("central", price)`. Prices, operator share (20%, *assumption*) and sold hours stay the same; only the machine changes. *Computed*, `python3 analysis/r5_pitch_numbers.py`, section H, seed means 1–3:

| Headline `shaped100`, operator share 20% (*assumption*), CHF a year | N = 6 | N = 8 |
|---|---|---|
| Sold J1 / J2 server-hours (headline run) | 14,101 / 14,660 | 16,333 / 17,293 |
| **Old, two machines** (laptop J1, B200-slice J2): low / central / high | 24.5k / **53.6k** / 177.2k | 28.4k / **62.6k** / 207.5k |
| **New, reference server**: low / central / high | 43.6k / **80.9k** / 218.3k | 50.6k / **94.0k** / 254.3k |
| New: list value of the sold work, central | 404.7k | 470.2k |
| New: share needed under the headline, operation / + install 5 y / 8 y / 5 y at 5% | 1.6% / 11.6% / 7.8% / 13.1% | 1.6% / 12.9% / 8.6% / 14.6% |
| New: margin after electricity minus heat, central; payback simple / at 5% | 74.4k; 2.7 / 3.0 years | 86.4k; 3.1 / 3.4 years |
| Audio-hours a year implied by the sold J1 work: old (laptop) / new (reference server) | 9.4 M / **19.9 M** | 10.9 M / **23.0 M** |
| Same machine, the exact share-needed basis (every permit hour sold, 50/50, unlimited demand), low / central / high | 47.9k / 88.6k / 237.6k | 55.9k / 103.4k / 277.5k |
| Same, 67% sold (the `r4_machine.py` payback convention), central | 59.3k | 69.3k |

Reading:
- On one basis, the share needed under the headline is **11.6%** (5 y), against 10.7% when every permit hour is sold. The headline sells 92.6% of permit hours, and the installed cost is spread over fewer hours. The pitch should name its basis. Suggestion: keep 10.7% / "about 11%" as the round figure. Both round to 11%.
- The CHF figure rises by half (53.6k → 80.9k) only because the faster machine does twice the J1 work per kWh. That doubles the implied transcription volume to **19.9 million audio-hours a year from one house**, about 16 times SRF's spoken archive of 1.25 million hours (*sourced* in round 4: <https://www.srf.ch/news/automatische-spracherkennung-computer-schryb-aues-mit-won-ig-hie-saege>). No named buyer comes near this. **A higher CHF number makes the demand problem worse, not better**, so it should stay a labelled scenario behind the share-needed line, as the plan already says.
- The 2.7-year payback assumes unlimited willingness to buy at central US batch prices and a 20% operator share. It is not a pitch figure.
- Market form, unchanged: about 1.53 CHF per sold server-hour (5 y), about 0.43 USD per GPU-hour net to the operator on every permit hour (G15, G16).

## 6. Numbers outside the two sections (seen, not all checked)

These are cited in other plan sections and come from saved scripts I did not re-run this round:
- `analysis/r3_policy_check.py` row X1 (misses 0.59–0.72% if executor and dry run differ);
- `analysis/r3_policy_check.py` (1,292–1,366 starts cut by cap + band);
- `analysis/r2_deadline_sim.py` (166 missed with a capacity sum);
- `analysis/r3_scope_extra.py` (0.7–5 s per year; restart within 0.0003 CHF);
- the round-1 pause probes (`analysis/pause_resume_probe.py`: 3.3 ms to state T, 10 SIGKILLs);
- the dashboard's "3.125× a heat pump's electricity" (`r4-plan-detail.md` section L);
- the January coverage 67% / 86% (plain follow).

None of them is among the five opening numbers. Role D should add them to the checklist only if they reach a slide.

## 7. Proposed plan changes

1. **"Still unverified" and open risks 8 and 14:** replace "Round-4 critic probes (flat customer, fixed contract, radiator lower bound) are scratch scripts, not yet committed" with "reproduced by `python3 analysis/r5_pitch_numbers.py` (IDs D5, D6, I7b, I8, I9b); checklist in `docs/research/r5-pitch-number-checklist.md`". (Here "committed" means saved in the repo folder; whether to `git add` stays the team's call.)
2. **Fix three wordings:** "5 kWh usable costs 1.6 points" → **1.5**, and "1.0–1.6" → "1.0–1.5". "triples starts" → "3.4 times the starts". "roughly 0.1–0.6% without the guard" → "0.1–0.4% in 2025 (seeds 1–5)", unless the 2024 runs are saved.
3. **Computing income, Q&A 1 and "Computing income (round 4)":** replace "53.6k / 62.6k … not yet recomputed on the reference server" with "on the reference server: 80.9k / 94.0k CHF a year at 20% operator share, central prices, headline sold hours, implying 19.9 M / 23.0 M audio-hours a year per house (no named buyer); scenario only". Keep the share needed as the lead. Say once that it is 11.6% under the headline and 10.7% with every permit hour sold.
4. **Role D, 21:00–23:00 "every pitch number traced to a command or URL":** this is done for the analysis figures. At the freeze, run `python3 analysis/r5_pitch_numbers.py` once (1 minute) and replace the C-section figures with the team scheduler's own printout. Label any figure that still comes from this script "from the analysis script". No new build scope; the script is an assessment tool, not part of the demonstrator.
5. **README for the jury:** list the one command (`python3 analysis/r5_pitch_numbers.py`) beside the scheduler's key-figure command, so a reviewer can trace every slide number in about 40 seconds. Transparency is 25% of the score.

## 8. Script output (`python3 analysis/r5_pitch_numbers.py`, 21 Nov 2026, exit 0)

The `--md` table rows are omitted here; they are in the checklist file.

```
r5_pitch_numbers.py. Currency CHF. Stand-in reference house 2025. Seeds [1, 2, 3]
Statuses: computed = this script (function named); sourced = constant read from the URL named in the plan;
assumption = our choice; measured = laptop measurement, NOT re-run here; critic probe = round-4 scratch logic, now here.

== A. Inputs and conversions ==
  [A1] CHF per USD (ECB 20 Nov 2026: EUR/CHF 0.9223 / EUR/USD 1.0990) = 0.8392 | plan: 0.8392 | computed from sourced https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html | MATCH
  [A2] Swiss VAT % = 8.1 | plan: 8.1 | sourced https://www.estv.admin.ch/en/vat-rates-switzerland | MATCH
  [A3] electricity CHF/kWh (ElCom 2026 IWB H4) = 0.3325 | plan: 0.3325 | sourced https://www.strompreis.elcom.admin.ch/operator/624?period=2026&category=H4 (data/README.md) | MATCH
  [A4] heat value CHF/kWh (price / 2.5, case rule) = 0.1330 | computed (case rule) | context

== B. Yearly balance, unlimited demand (baseline_sweep.simulate, follow) ==
  [B1] total heat demand kWh/yr = 31,231 | plan: 31,231 | computed | MATCH
  [B2] space heating kWh/yr = 26,851 | plan: 26,851 | computed | MATCH
  [B3] hot water kWh/yr = 4,380 | plan: 4,380 | computed | MATCH
  [B4.1] N=1 coverage % / dumped kWh / utilisation % = 19.5 / 0.0 / 87.1 | plan: 19.5 / 0.0 / 87.1 | computed | MATCH
  [B5.1] N=1 server-h / electricity CHF / heat value CHF = 7,629 / 2,537 / 812 | plan: 7,629 / 2,537 / 812 | computed | MATCH
  [B6.1] N=1 break-even CHF/server-h = 0.2261 | plan: 0.2261 | computed | MATCH
  [B4.6] N=6 coverage % / dumped kWh / utilisation % = 79.6 / 0.0 / 59.1 | plan: 79.6 / 0.0 / 59.1 | computed | MATCH
  [B5.6] N=6 server-h / electricity CHF / heat value CHF = 31,067 / 10,330 / 3,306 | plan: 31,067 / 10,330 / 3,306 | computed | MATCH
  [B6.6] N=6 break-even CHF/server-h = 0.2261 | plan: 0.2261 | computed | MATCH
  [B4.8] N=8 coverage % / dumped kWh / utilisation % = 92.9 / 0.0 / 51.8 | plan: 92.9 / 0.0 / 51.8 | computed | MATCH
  [B5.8] N=8 server-h / electricity CHF / heat value CHF = 36,281 / 12,063 / 3,860 | plan: 36,281 / 12,063 / 3,860 | computed | MATCH
  [B6.8] N=8 break-even CHF/server-h = 0.2261 | plan: 0.2261 | computed | MATCH
  [B7] N=13 always-on: coverage % / utilisation % = 100 / 100 | plan: 100 / 100 | computed | MATCH
  [B8] N=13 always-on: dumped kWh / server-h / elec CHF / heat CHF = 59,839 / 113,880 / 37,865 / 4,154 | plan: 59,839 / 113,880 / 37,865 / 4,154 | computed | MATCH
  [B9] N=13 always-on break-even = 0.2960 | plan: 0.2960 | computed | MATCH
  [B10] N=2 coverage % / utilisation % = 32.7 / 73.0 | plan: 32.7 / 73.0 | computed | MATCH
  [B11] N=6 tank 10 kWh / 140 kWh coverage % = 78.8 / 80.3 | plan: 78.8 / 80.3 | computed | MATCH
  [B12] run h/yr of the 6th / 7th / 8th server = 3,796 / 2,933 / 2,281 | plan: 3,796 / 2,933 / 2,281 | computed | MATCH
  [B13] unlimited: N=8 minus N=6 coverage pts / utilisation pts (Q&A 2 '13 points for 7 points') = 13 / 7 | plan: 13 / 7 | computed | MATCH

(running 58 simulated years with r4_headline.run ...)

== C. Headline run, shaped100, archived ifs025 + 2 K guard, cap + 8 kWh band (r4_headline.run, seed means) ==
  [C1] coverage % N=6 / N=8 (2 decimals) = 73.67 / 86.14 | plan: 73.67 / 86.14 | computed | MATCH
  [C1b] coverage % N=6 / N=8 (pitch, 1 decimal) = 73.7 / 86.1 | plan: 73.7 / 86.1 | computed | MATCH
  [C2] heat dumped kWh N=6 / N=8 = 0 / 0 | plan: 0 / 0 | computed | MATCH
  [C3] utilisation % N=6 / N=8 = 54.72 / 47.98 | plan: 54.72 / 47.98 | computed | MATCH
  [C3b] utilisation % (pitch) = 54.7 / 48.0 | plan: 54.7 / 48.0 | computed | MATCH
  [C4] offers accepted % N=6 / N=8 = 94.7 / 93.8 | plan: 94.7 / 93.8 | computed | MATCH
  [C5] summer (Jun-Aug) J1 accepted % N=6 / N=8 = 89.6 / 90.3 | plan: 89.6 / 90.3 | computed | MATCH
  [C6.6] N=6 missed x of y accepted jobs, seeds [1, 2, 3] = 0 of 31,908 / 0 of 31,694 / 0 of 31,996 | plan: 0 of 31,908 / 0 of 31,694 / 0 of 31,996 | computed | MATCH
  [C6.8] N=8 missed x of y accepted jobs, seeds [1, 2, 3] = 0 of 36,771 / 0 of 36,989 / 0 of 37,201 | plan: 0 of 36,771 / 0 of 36,989 / 0 of 37,201 | computed | MATCH
  [C7] server-hours sold N=6 / N=8 = 28,761 / 33,626 | plan: 28,761 / 33,626 | computed | MATCH
  [C8] electricity CHF/yr N=6 / N=8 = 9,563 / 11,181 | plan: 9,563 / 11,181 | computed | MATCH
  [C9] heat value used CHF/yr N=6 / N=8 (dashboard 'heat worth') = 3,060 / 3,578 | plan: 3,060 / 3,578 | computed | MATCH
  [C10] break-even CHF per sold server-h N=6 / N=8 = 0.2261 / 0.2261 | plan: 0.2261 / 0.2261 | computed | MATCH
  [C11] break-even with 15-min restart line N=6 / N=8 = 0.2278 / 0.2286 | plan: 0.2278 / 0.2286 | computed; 15 min is an assumption | MATCH
  [C12] N=8 extra coverage points under the headline = 12.5 | plan: 12.5 | computed | MATCH
  [C13] N=8 contract larger than N=6's, % (yearly mean offer rate) = 17 | plan: 17 | computed | MATCH
  [C14] jobs offered per day N=6 / N=8 (expected) = 92 / 108 | plan: 92 / 108 | computed | MATCH
  [C15] N=6 January J1 / J2 jobs per day; July J1 / J2 = 143.9 / 18.0 / 15.0 / 1.9 | plan: 143.9 / 18.0 / 15.0 / 1.9 | computed | MATCH
  [C16] sold share of unlimited-demand permit hours % N=6 / N=8 = 93 / 93 | plan: 93 / 93 | computed (plan: 'about 93%') | MATCH
  [C17] starts per year N=6 / N=8 (headline) = 854 / 1,497 | computed | context
  [C18] perfect-forecast check: missed jobs, all seeds, N=6 + N=8 = 0 | plan: 0 | computed | MATCH

== D. Comparison and sensitivity rows (r4_headline.run; critic probes re-implemented) ==
  [D1] saturating: accepted % N=6 / N=8 = 54.9 / 49.2 | plan: 54.9 / 49.2 | computed | MATCH
  [D1b] saturating: summer J1 accepted % = 0.0 / 0.0 | plan: 0.0 / 0.0 | computed | MATCH
  [D2] shaped200: coverage % = 78.96 / 92.25 | plan: 78.96 / 92.25 | computed | MATCH
  [D2b] shaped200: accepted % = 44.1 / 46.3 | plan: 44.1 / 46.3 | computed | MATCH
  [D2c] shaped200: mean missed % = 0.084 / 0.051 | plan: 0.084 / 0.051 | computed | MATCH
  [D2d] shaped200 seed 1: missed x of y N=6 / N=8 = 33 of 28,928 / 11 of 35,991 | plan: 33 of 28,928 / 11 of 35,991 | computed | MATCH
  [D3] shaped120 seed 1: coverage % N=6 / N=8 = 76.46 / 89.72 | plan: 76.46 / 89.72 | computed (was inline command) | MATCH
  [D3b] shaped150 seed 1: coverage % N=6 / N=8 = 78.23 / 91.80 | plan: 78.23 / 91.80 | computed (was inline command) | MATCH
  [D3c] shaped120 / shaped150 seed 1: accepted % N=6 / N=8 / N=6 / N=8 = 81.7 / 82.8 / 64.0 / 65.4 | plan: 81.7 / 82.8 / 64.0 / 65.4 | computed (was inline command) | MATCH
  [D3d] N=8 missed at shaped120 / shaped150, seed 1 = 12 / 13 | plan: 12 / 13 | computed (was inline command) | MATCH
  [D4] shaped50: coverage % = 37.99 / 44.59 | plan: 37.99 / 44.59 | computed | MATCH
  [D4b] shaped50: starts per year (plan '3,000-3,400') = 3,021 / 3,367 | computed | context
  [D5] flat customer, same yearly volume: coverage % (2 dec.) = 53.67 / 60.48 | plan: 53.67 / 60.48 | computed (critic probe, now here) | MATCH
  [D5b] flat customer: coverage % (pitch) = 53.7 / 60.5 | plan: 53.7 / 60.5 | computed (critic probe, now here) | MATCH
  [D5c] flat customer: accepted % / summer J1 % = 64.1 / 62.4 / 0.0 / 0.0 | plan: 64.1 / 62.4 / 0.0 / 0.0 | computed (critic probe, now here) | MATCH
  [D5d] flat customer: missed jobs, all seeds N=6 + N=8 = 0 | plan: 0 | computed (critic probe, now here) | MATCH
  [D6] fixed contract (N=6's offers): coverage % N=6 / N=8 = 73.67 / 73.88 | plan: 73.67 / 73.88 | computed (critic probe, now here) | MATCH
  [D6b] fixed contract: N=8 gain in coverage points (Read-this-first '0.2') = 0.2 | plan: 0.2 | computed (critic probe, now here) | MATCH
  [D6c] fixed contract: coverage % N=6 / N=8 (Q&A '73.7 against 73.9') = 73.7 / 73.9 | plan: 73.7 / 73.9 | computed (critic probe, now here) | MATCH
  [D6d] fixed contract: accepted % N=6 / N=8 = 94.7 / 94.7 | plan: 94.7 / 94.7 | computed (critic probe, now here) | MATCH
  [D6e] fixed contract: N=8 utilisation % = 41.2 | plan: 41.2 | computed (critic probe, now here) | MATCH
  [D6f] fixed contract: starts per year N=6 / N=8 = 854 / 2,944 | plan: 854 / 2,944 | computed (critic probe, now here) | MATCH
  [D6g] fixed contract: starts ratio N=8 / N=6 (plan says 'triples') = 3.4 | computed | context
  [D6h] fixed contract: restart break-even N=6 / N=8 = 0.2278 / 0.2320 | plan: 0.2278 / 0.2320 | computed (critic probe, now here) | MATCH
  [D6i] context: N=6 on N=8's contract, coverage % = 74.99 | computed (critic probe) | context
  [D7] named customer only (SRF-size archive, flat): coverage % = 4.8 | plan: 4.8 | computed | MATCH
  [D8] all-year pin, N=6: pinned h/yr / share of sold h % = 7,531.7 / 25.8 | computed | context
  [D8b] all-year pin, N=6: pinned h/yr = 7,532 | plan: 7,532 | computed | MATCH
  [D8c] all-year pin, N=6: share of sold hours % = 25.8 | plan: 25.8 | computed | MATCH
  [D8d] all-year pin, N=6: summer J1 accepted % (from 89.6) = 0.0 | plan: 0.0 | computed | MATCH
  [D9] demo-day pin: coverage % N=6 without -> with = 73.675 / 73.673 | plan: 73.675 / 73.673 | computed | MATCH
  [D9b] demo-day pin: coverage % N=8 without -> with = 86.136 / 86.187 | plan: 86.136 / 86.187 | computed | MATCH
  [D10.6] demo day N=6: date, slot, pause, resume, hours run (seed 1) = 2025-07-15 slot 1 P02 R18 8 h | plan: 2025-07-15 slot 1 P02 R18 8 h | computed | MATCH
  [D10.8] demo day N=8: date, slot, pause, resume, hours run (seed 1) = 2025-01-25 slot 7 P14 R19 19 h | plan: 2025-01-25 slot 7 P14 R19 19 h | computed | MATCH
  [D11] 2025-01-13 permit-holding idle server-hours N=6 / N=8 (seed 1) = 22 / 16 | plan: 22 / 16 | computed (was inline command) | MATCH

== E. Break-even: who gets the heat, sold share (case formula) ==
  [E1] homeowner gets heat free: electricity per server-h = 0.3325 | plan: 0.3325 | computed | MATCH
  [E2] heat value at stake CHF/yr N=6 / N=8 (unlimited) = 3,306 / 3,860 | plan: 3,306 / 3,860 | computed | MATCH
  [E3] 80% / 50% sold, unsold still run: break-even = 0.283 / 0.452 | plan: 0.283 / 0.452 | computed (r2_fleet_economics formula) | MATCH
  [E4] 67% sold, unsold still run: break-even = 0.3375 | plan: 0.3375 | computed (r3_income 5B formula) | MATCH

== F. Pause physics (r2_realism.sim, unlimited demand) ==
  [F1] paused servers powered at 17.6% idle: break-even N=6 / N=8 = 0.2659 / 0.2814 | plan: 0.2659 / 0.2814 | computed; idle share sourced (SPECpower), applying it to this server is an assumption | MATCH
  [F1b] same: summer server-hours sold N=6 / N=8 ('nothing sold in summer') = 0 / 0 | plan: 0 / 0 | computed | MATCH
  [F2] starts/yr plain follow / cap + 8 kWh band, N=6 then N=8 = 1,732 / 379 / 2,208 / 891 | plan: 1,732 / 379 / 2,208 / 891 | computed | MATCH

== G. Reference server and installed cost (r4_machine; critic extras re-implemented) ==
  [G1] wall power kW central (low-high) = 0.95 / 0.75 / 1.22 | plan: 0.95 / 0.75 / 1.22 | assumption built on sourced 165 W / 320 W maxima | MATCH
  [G2] audio-h per kWh: Cisco 6.1-0017 / HPE 6.1-0056 (plan 'about 1,300-1,400') = 1,411 / 1,341 | computed | context
  [G2b] same, rounded to hundreds = 1,300 / 1,400 | plan: 1,300 / 1,400 | computed | MATCH
  [G3] Wh per audio-hour, reference server = 0.7 | plan: 0.7 | computed | MATCH
  [G4] HPE 2U box lower than Cisco blade, % = 5 | plan: 5 | computed from sourced MLPerf rows | MATCH
  [G5] laptop / reference Wh per audio-h factor (1.3 and 1.5 Wh) = 1.8 / 2.1 | computed | context
  [G5b] factor, rounded = 2 | plan: 2 | computed (plan 'about 2') | MATCH
  [G6] million output tokens per kWh = 36 | plan: 36 | computed | MATCH
  [G7] installed CHF per 1 kW server (central), exact / to 1,000 = 33,652 / 34,000 | computed | context
  [G7a] installed CHF per 1 kW server, rounded to 1,000 (plan 'about 34,000') = 34,000 | plan: 34,000 | computed | MATCH
  [G7b] installed CHF per house N=6, exact / to 10,000 (plan 'about 200,000') = 201,914 / 200,000 | computed | context
  [G7d] installed CHF per house N=6 to 10,000 / N=8 to 1,000 = 200,000 / 264,000 | plan: 200,000 / 264,000 | computed | MATCH
  [G7c] GPU value per house N=6, CHF to 1,000 (plan 'about 121,000') = 121,000 | plan: 121,000 | computed (critic extra, now here) | MATCH
  [G8] house integration CHF low / central / high, hundreds = 10,700 / 14,800 / 20,100 | plan: 10,700 / 14,800 / 20,100 | computed from a proxy (BFE 2015) + assumption | MATCH
  [G9] list value of one server-hour, mix 50/50, low / central / high CHF = 7.7 / 14.3 / 38.2 | plan: 7.7 / 14.3 / 38.2 | computed (prices sourced in round 3) | MATCH
  [G10] round-3 two-machine list value = 4.3 / 9.4 / 30.7 | plan: 4.3 / 9.4 / 30.7 | computed in round 3 (constant echoed by r4_machine) | MATCH
  [G11] share of list needed N=6 central: operation % = 1.6 | plan: 1.6 | computed | MATCH
  [G11b] N=6 5-y / 8-y payback share % (simple) = 10.7 / 7.3 | plan: 10.7 / 7.3 | computed | MATCH
  [G11c] N=6 5-y / 8-y share % at 5% interest = 12.1 / 8.6 | plan: 12.1 / 8.6 | computed (critic probe, now here); 5% is an assumption | MATCH
  [G11d] N=6 5-y / 8-y share % at 67% sold = 16.0 / 10.9 | plan: 16.0 / 10.9 | computed | MATCH
  [G11e] N=8 operation / 5-y / 8-y share % = 1.6 / 11.8 / 8.0 | plan: 1.6 / 11.8 / 8.0 | computed | MATCH
  [G11f] N=8 5-y / 8-y share % at 5% interest = 13.4 / 9.5 | plan: 13.4 / 9.5 | computed (critic probe, now here) | MATCH
  [G11g] pitch rounding: 5-y / 8-y share; at 5% interest = 11 / 7 / 12 / 9 | plan: 11 / 7 / 12 / 9 | computed | MATCH
  [G11h] 5-y share range, low cost + high price .. high cost + low price % = 3.1 / 25.3 | plan: 3.1 / 25.3 | computed | MATCH
  [G11i] 5-y / 8-y share at LOW price, central cost, 67% sold % = 30 / 20 | plan: 30 / 20 | computed | MATCH
  [G12] 5-y share ex VAT N=6 / N=8 % = 10.0 / 11.0 | plan: 10.0 / 11.0 | computed (critic extra, now here) | MATCH
  [G13] LLM only: 5-y / 8-y share %; at 5% = 31.7 / 21.5 / 35.8 / 25.6 | plan: 31.7 / 21.5 / 35.8 / 25.6 | computed (8-y and 5% by critic probe, now here) | MATCH
  [G13b] LLM only, pitch rounding (Q&A '32-36%') = 32 / 36 | plan: 32 / 36 | computed | MATCH
  [G13c] transcription only: 5-y share % = 6.4 | plan: 6.4 | computed | MATCH
  [G14] round 3 like-for-like: share on the mix basis % = 24.0 | plan: 24.0 | computed (critic extra, now here) | MATCH
  [G14b] round 3 share on the J1-only basis % = 20 | plan: 20 | computed (r3_income section 7) | MATCH
  [G15] CHF needed per sold server-h N=6: 5 y / 5 y at 5% / 8 y / 8 y at 5% = 1.53 / 1.73 / 1.04 / 1.23 | plan: 1.53 / 1.73 / 1.04 / 1.23 | computed (5% by critic probe, now here) | MATCH
  [G16] USD per GPU-hour the operator needs: 5 y / 8 y / 5 y at 67% sold = 0.43 / 0.30 / 0.65 | plan: 0.43 / 0.30 / 0.65 | computed (critic extra, now here) | MATCH
  [G17] payback y at 20% share, 67% sold, N=6 central / low (simple) = 3.9 / 8.1 | plan: 3.9 / 8.1 | computed | MATCH
  [G17b] same at 5% interest, N=6 central / low; N=8 low = 4.4 / 10.6 / 12.3 | plan: 4.4 / 10.6 / 12.3 | computed (critic probe, now here) | MATCH
  [G18] cheapest rental 0.41 USD/GPU-h: payback y per server, all permit h rented = 7.0 | plan: 7.0 | computed; 0.41 USD sourced (getdeploying.com), 80% host share sourced (round 2) | MATCH
  [G18b] renter prices USD/GPU-h cheapest / RunPod / median (echo) = 0.41 / 0.72 / 0.92 | plan: 0.41 / 0.72 / 0.92 | sourced https://getdeploying.com/gpus/nvidia-rtx-pro-4500 and https://www.runpod.io/gpu-models/rtx-pro-4500-se | MATCH
  [G19] unlimited demand, half J1: audio-h per day per house, to 1,000 (plan 'about 60,000') = 60,000 | plan: 60,000 | computed | MATCH
  [G19b] average Mbit/s at 32 kbit/s = 80 | plan: 80 | computed; codec rate assumption | MATCH
  [G19c] peak-hour Mbit/s half J1 / all J1 = 135 / 271 | plan: 135 / 271 | computed (critic extra, now here) | MATCH
  [G20] 5-y hardware share across wall power low / high % = 10.2 / 11.3 | plan: 10.2 / 11.3 | computed | MATCH
  [G21] market form: CHF per sold server-h (5 y), rounded = 1.5 | plan: 1.5 | computed | MATCH
  [G22] CPU-only LLM (6.1-0032) at the low price, CHF per server-h = 0.148 | plan: 0.148 | computed; 1 kW is an assumption; 1,227.99 tok/s sourced (MLPerf v6.1 summary) | MATCH
  [G23] lowest marketplace host rate, CHF per kW-h (Salad 4090 min x 2 GPU/kW) = 0.215 | plan: 0.215 | computed; host rate sourced in round 2, 2 GPU per kW assumption | MATCH

== H. Computing income scenario: two-machine basis (old) vs reference-server basis (new), headline run ==
  [H1.6] N=6 OLD two-machine basis (laptop J1, B200-slice J2), income at 20%, central, k CHF/yr = 53.6 | plan: 53.6 | computed (r4_headline.money); scenario, not income | MATCH
  [H1b.6] N=6 OLD two-machine basis, low / high, k CHF/yr = 24.5 / 177.2 | computed (r4_headline.money) | context
  [H2.6] N=6 NEW reference-server income at 20%, low / central / high, k CHF/yr = 43.6 / 80.9 / 218.3 | computed (NEW: r4_machine.list_value x headline sold hours per job type); scenario, not income | context
  [H3.6] N=6 sold J1 / J2 server-h (headline) = 14,101 / 14,660 | computed | context
  [H4.6] N=6 list value of sold work, reference server, central, k CHF/yr = 404.7 | computed (NEW) | context
  [H5.6] N=6 share needed under the headline: operation / + install 5 y / 8 y / 5 y at 5% (central) = 1.6 / 11.6 / 7.8 / 13.1 | computed (NEW; same basis as the share-needed line, but headline sold hours instead of every permit hour) | context
  [H6.6] N=6 audio-hours per year implied by sold J1: two-machine (laptop) / reference server, millions = 9.4 / 19.9 | computed (NEW) | context
  [H7.6] N=6 NEW basis: margin after electricity-heat, k CHF/yr; payback y simple / at 5% (central) = 74.4 / 2.7 / 3.0 | computed (NEW) | context
  [H1.8] N=8 OLD two-machine basis (laptop J1, B200-slice J2), income at 20%, central, k CHF/yr = 62.6 | plan: 62.6 | computed (r4_headline.money); scenario, not income | MATCH
  [H1b.8] N=8 OLD two-machine basis, low / high, k CHF/yr = 28.4 / 207.5 | computed (r4_headline.money) | context
  [H2.8] N=8 NEW reference-server income at 20%, low / central / high, k CHF/yr = 50.6 / 94.0 / 254.3 | computed (NEW: r4_machine.list_value x headline sold hours per job type); scenario, not income | context
  [H3.8] N=8 sold J1 / J2 server-h (headline) = 16,333 / 17,293 | computed | context
  [H4.8] N=8 list value of sold work, reference server, central, k CHF/yr = 470.2 | computed (NEW) | context
  [H5.8] N=8 share needed under the headline: operation / + install 5 y / 8 y / 5 y at 5% (central) = 1.6 / 12.9 / 8.6 / 14.6 | computed (NEW; same basis as the share-needed line, but headline sold hours instead of every permit hour) | context
  [H6.8] N=8 audio-hours per year implied by sold J1: two-machine (laptop) / reference server, millions = 10.9 / 23.0 | computed (NEW) | context
  [H7.8] N=8 NEW basis: margin after electricity-heat, k CHF/yr; payback y simple / at 5% (central) = 86.4 / 3.1 / 3.4 | computed (NEW) | context
  [H9.6] N=6 NEW, exact share-needed basis (every permit hour sold, 50/50 mix, unlimited demand), income at 20%, low / central / high, k CHF/yr = 47.9 / 88.6 / 237.6 | computed (NEW; r4_machine.list_value x baseline run hours) | context
  [H9b.6] N=6 same at 67% sold (r4_machine section 3 convention), central, k CHF/yr = 59.3 | computed (equals r4_machine 'income' line) | context
  [H9.8] N=8 NEW, exact share-needed basis (every permit hour sold, 50/50 mix, unlimited demand), income at 20%, low / central / high, k CHF/yr = 55.9 / 103.4 / 277.5 | computed (NEW; r4_machine.list_value x baseline run hours) | context
  [H9b.8] N=8 same at 67% sold (r4_machine section 3 convention), central, k CHF/yr = 69.3 | computed (equals r4_machine 'income' line) | context
  [H8] SRF-size archive (1.25 M audio-h) in server-h: laptop rule / reference server = 1,875 / 886 | computed; 1.25 M sourced (srf.ch, URL in plan) | context
  [H8b] SRF archive at laptop rule: server-h / % of one N=6 house-year = 1,875 / 6 | plan: 1,875 / 6 | computed | MATCH
  [H8c] two-machine basis: audio-h/yr in the N=6 income line, millions = 9.4 | plan: 9.4 | computed | MATCH

== I. Realism column, layout A, and radiator houses (r4_tank_layout.sim; critic return-limit probe) ==
  [I1] layout A, underfloor + loss 2.80: coverage % N=6 / N=8 = 77.6 / 90.6 | plan: 77.6 / 90.6 | computed | MATCH
  [I1b] June-August coverage % (layout A) = 82.2 | plan: 82.2 | computed | MATCH
  [I1c] utilisation % N=6 / N=8 (layout A) = 59.4 / 52.1 | plan: 59.4 / 52.1 | computed | MATCH
  [I1d] break-even, case convention: underfloor N=6 / radiator 55/45 N=6 = 0.2293 / 0.2294 | plan: 0.2293 / 0.2294 | computed | MATCH
  [I1e] break-even, top-up charged to servers N=6 / N=8 = 0.234 / 0.234 | plan: 0.234 / 0.234 | computed (plan 'about 0.234') | MATCH
  [I2] tank loss only: coverage change pts N=6 / N=8 = -0.3 / -0.3 | plan: -0.3 / -0.3 | computed | MATCH
  [I2b] tank loss only: break-even rise N=6 / N=8 = 0.0030 / 0.0031 | plan: 0.0030 / 0.0031 | computed | MATCH
  [I3] no-build-scope proxy: dhw_direct_share=37/45 + loss: coverage % N=6 / N=8 = 77.72 / 90.74 | plan: 77.72 / 90.74 | computed | MATCH
  [I4] usable buffer kWh: summer / floor 35/28 / 50/40 / 55/45 / 70/55 design hour = 34.9 / 25.6 / 11.6 / 5.8 / 0.0 | plan: 34.9 / 25.6 / 11.6 / 5.8 / 0.0 | computed | MATCH
  [I5] hot-water direct share % at 55 / 52 / 60 C setpoint = 82.2 / 88.1 / 74.0 | plan: 82.2 / 88.1 / 74.0 | computed | MATCH
  [I5b] electric top-up kWh/yr at 55 C = 779 | plan: 779 | computed | MATCH
  [I6] usable tank 10 / 5 kWh costs coverage pts (floor heating, N=6) = 1.0 / 1.5 | plan: 1.0 / 1.6 | computed | DIFF
  [I7] radiator 55/45 + loss, upper bound (servers keep running): coverage % N=6 / N=8 = 77 / 90 | plan: 77 / 90 | computed | MATCH
  [I7b] radiator 55/45 + loss, LOWER bound (servers stop if return > 40 C): coverage % N=6 / N=8 = 64 / 73 | plan: 64 / 73 | computed (critic probe, now here) | MATCH
  [I7c] same, one decimal = 64.3 / 73.0 | plan: 64.3 / 73.0 | computed (critic probe, now here) | MATCH
  [I8] radiator 55/45: heating hours with return > 40 C (exact) = 853 | computed (critic probe, now here) | context
  [I8a] same, to 10 h (plan Q&A 'about 850') = 850 | plan: 850 | computed (critic probe, now here) | MATCH
  [I8b] radiator 55/45 return temperature at the design hour, C = 45 | plan: 45 | computed (plan '44-45') | MATCH
  [I9] radiator 70/55: upper bound N=6 / lower bound (ret <= 40 C) N=6 / N=8 % = 59 / 29 / 31 | plan: 59 / 30 / 31 | computed (lower bounds: critic probe, now here); plan words 'at most about 59%', 'about 30%' | DIFF
  [I9b] same, one decimal (round-4 critic table: 59.2 / 29.5 / 31.2) = 59.2 / 29.5 / 31.2 | plan: 59.2 / 29.5 / 31.2 | computed (critic probe, now here) | MATCH
  [I10] 45 C loop: June-August % / radiator 55/45 N=8 loss in pts = 71.1 / 10.6 | plan: 71.1 / 10.6 | computed | MATCH
  [I12] higher space-heating draw floor (mixed tank): largest coverage loss, pts = 0.2 | computed (plan '<= 0.2 points') | context
  [I13] layout A temperatures: buffer top C / fresh-water preheat C = 50 / 47 | plan: 50 / 47 | computed from sourced 55 C outlet (NVIDIA blog) and 5 K / 3 K approaches (Lenovo / suissetec; interpretation) | MATCH
  [I11] air-cooled, no direct hot water: coverage % N=6 / N=8 = 70.5 / 81.7 | plan: 70.5 / 81.7 | computed | MATCH

== J. Forecast error and round-2 no-guard miss rate (r2_deadline_sim) ==
  [J1] ECMWF ifs025 RMSE K, day 1 / day 7 = 1.16 / 2.85 | plan: 1.16 / 2.85 | computed from archived forecasts (analysis/r2_data/prev_ecmwf_ifs025.csv) | MATCH
  [J1b] ifs025 day-1 bias K = +0.29 | plan: +0.29 | computed | MATCH
  [J2.6] N=6 saturating, ifs025, NO guard, no partner, 2025, seeds 1-5: missed % mean / min / max = 0.146 / 0.097 / 0.267 | plan: 0.146 / 0.097 / 0.267 | computed (round-2 run); plan's '0.1-0.6%' upper end came from 2024 runs by the round-2 critic, not in a script | MATCH
  [J2.8] N=8 saturating, ifs025, NO guard, no partner, 2025, seeds 1-5: missed % mean / min / max = 0.294 / 0.160 / 0.386 | plan: 0.294 / 0.160 / 0.386 | computed (round-2 run); plan's '0.1-0.6%' upper end came from 2024 runs by the round-2 critic, not in a script | MATCH
  [J3] named-customer volume vs shaped100 contract N=6 % = 6.3 | computed | context

== K. Small derived Q&A numbers ==
  [K1] vendor sizing 5-20% of design load = servers (10 kW design / 0.8 kW per server) = 0.6 / 2.5 | plan: 0.6 / 2.5 | computed from sourced 5-20% (URL in r4-plan-detail.md section L) | MATCH
  [K2] heat receipt: J2 (4 server-h) heat kWh / person-days of case hot water = 3.20 / 1.07 | plan: 3.20 / 1.07 | computed; job size assumption | MATCH
  [K3] laptop J1 energy Wh per audio-hour used downstream (r3_income.E_PROBE) = 1.5 | plan: 1.5 | measured 2026-11-21 by r3_whisper_energy_probe.py, NOT re-run here (plan range 1.3-1.5) | MATCH
  [K4] J2 input tokens billed per output token = 6 | plan: 6 | assumption (r3_income.IN_PER_OUT) | MATCH
  [K6] marketplace host share (Salad 4090 host rate / renter price, lowest tier) = 0.80 | plan: 0.80 | computed from rates sourced in round 2 (r2-host-income-hardware.md) | MATCH
  [K5] MLPerf throughput: whisper Cisco / HPE samples/s; llama tok/s = 61.10 / 58.08 / 9518.66 | plan: 61.10 / 58.08 / 9518.66 | sourced (MLPerf v6.1 loadgen logs, URLs in r4-reference-machine.md section 2.1) | MATCH

== Summary ==
  188 lines: 154 MATCH, 2 DIFF, 32 context (not quoted in the plan or quoted only in words)
  DIFF [I6] usable tank 10 / 5 kWh costs coverage pts (floor heating, N=6): script 1.0 / 1.5 vs plan 1.0 / 1.6
  DIFF [I9] radiator 70/55: upper bound N=6 / lower bound (ret <= 40 C) N=6 / N=8 %: script 59 / 29 / 31 vs plan 59 / 30 / 31
```
