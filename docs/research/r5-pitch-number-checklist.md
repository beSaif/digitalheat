# Round 5: pitch-number checklist (number → command → status)

Investigator file for weak point 2 of round 5 ("headline and comparison figures not all reproducible; income on two machine bases"). Written Sat 21 Nov 2026. Plans and assesses only. Full findings: [r5-reproducibility-checklist.md](r5-reproducibility-checklist.md).

**One command reproduces every number below:**

```
python3 analysis/r5_pitch_numbers.py          # ~40 s wall on this laptop (all cores), ~275 s CPU; exit 0
python3 analysis/r5_pitch_numbers.py --md     # same, plus this table's rows (without the "earlier command" column)
```

Standard library only. It imports `baseline_sweep`, `r2_deadline_sim`, `r2_realism`, `r2_fleet_economics`, `r3_income`, `r4_headline`, `r4_machine` and `r4_tank_layout` without editing them. It writes no files and no `__pycache__` (checked: no `r5_*` entry appeared in `analysis/__pycache__`). Currency CHF; 1 USD = 0.8392 CHF (ECB reference rates 20 Nov 2026, EUR/CHF 0.9223 ÷ EUR/USD 1.0990, *sourced*: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>, inherited from round 1).

## Result in five lines

1. **188 lines printed: 154 match the plan to its last shown digit, 2 do not, 32 are context lines** (the plan quotes them only in words, or they are new). Run of 21 Nov 2026.
2. **The 2 mismatches are rounding slips in the plan, not model errors.** "5 kWh usable costs 1.6 points" is really **1.5** (77.99 − 76.45; the plan subtracted two rounded table values). The 70/55 radiator lower bound "about 30%" is **29.5%**, which rounds to 29.
3. **37 rows had no saved command before this round** (two of them, G13 and G15, only partly). They existed only as round-4 critic scratch scripts (flat customer, fixed contract, radiator lower bounds), critic one-liners (5% interest, ex-VAT, GPU value per house, peak bandwidth, USD per GPU-hour), inline `python3 -c` calls (shaped120/150, idle permits on 2025-01-13), or hand formulas (0.148 CHF, 0.6–2.5 servers). They are now all in `analysis/r5_pitch_numbers.py`, and every one reproduces the critic's value.
4. **Not reproducible from any saved script:** the upper end of "roughly 0.1–0.6%" no-guard misses (it came from 2024 runs by the round-2 critic; the saved 2025 runs give 0.097–0.386%); the laptop measurement (1.3–1.5 Wh per audio-hour, 25–27× real time; it is a hardware measurement, not re-run here); "core size 110–150 lines" (a critic's reading, not a count).
5. **Income now on one machine basis (new):** on the reference server, the headline's computing-income scenario at 20% operator share is **80.9k / 94.0k CHF a year** (N=6 / N=8, central prices), not 53.6k / 62.6k (two-machine basis). The rise comes only from the faster machine. It implies **19.9 million audio-hours a year** from one N=6 house (twice the 9.4 million of the old line, about 16 times the SRF archive of 1.25 million hours). The share needed under the headline is 1.6% for operation and 11.6% with 5-year simple payback (13.1% at 5% interest). Every permit hour sold, as in the existing share-needed line, gives 10.7%.

## How to read the table

- **value (r5 script)**: printed by `python3 analysis/r5_pitch_numbers.py` on 21 Nov 2026.
- **plan**: the figure as written in `docs/overnight.md` ("Read this first" and "Key numbers", state after round 4). Where the plan says "about X", the script prints the value rounded to X's precision. The exact value is on the line before it (for example G7, G7b, I8).
- **earlier command**: what printed the number before round 5. "none saved" = it lived only in a scratchpad file, a critique file or an inline call.
- **status**: *computed* = this script (the function used is named in the script's section header); *sourced* = an input constant read on the URL given (opened in earlier rounds; I did not re-open the URLs this round); *assumption* = our choice; *measured* = laptop measurement, not re-run; "critic probe, now here" = logic from a round-4 critic scratch file, now in the saved script.
- **matches plan**: yes / **no** / n/a (context line).

## Mismatches and wording to fix in the plan

| id | Plan says | Script prints | Fix |
|---|---|---|---|
| I6 | "Tank size barely matters (5 kWh usable costs 1.6 points)"; "10 / 5 kWh usable costs 1.0–1.6 points" | 1.0 / **1.5** points (77.99% → 76.45%) | write "1.0–1.5 points" |
| I9 | 70/55 house "about 30%" if servers need return ≤ 40 °C | **29.5%** (N=6), 31.2% (N=8) | "about 30%" is fine as words; in a table write 29.5% |
| D6g | "triples starts" (fixed contract) | 2,944 ÷ 854 = **3.4×** | "more than triples" or "3.4 times" |
| G2 | "about 1,300–1,400 audio-hours per kWh" | 1,341 (2U HPE) / **1,411** (Cisco blade) | "about 1,340–1,410" or keep "about 1,300–1,400" |
| J2 | "roughly 0.1–0.6% a year without the guard" | 2025, seeds 1–5: N=6 0.097–0.267%, N=8 0.160–0.386% | say "0.1–0.4% in 2025" unless the 2024 runs are saved too |
| G14b | "Same basis in round 3: … J1-only 20%" | 20.1% | fine |
| Q&A 1 | CHF scenario "not yet recomputed on the reference server" | now H2: 80.9k / 94.0k CHF (central) | replace the line; see the research file, section 5 |

## Table

| id | number | value (r5 script) | plan | earlier command | status | matches plan |
|---|---|---|---|---|---|---|
| A1 | CHF per USD (ECB 20 Nov 2026: EUR/CHF 0.9223 / EUR/USD 1.0990) | 0.8392 | 0.8392 | `python3 analysis/r4_machine.py` header (constant) | computed from sourced https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html | yes |
| A2 | Swiss VAT % | 8.1 | 8.1 | `python3 analysis/r4_machine.py` header | sourced https://www.estv.admin.ch/en/vat-rates-switzerland | yes |
| A3 | electricity CHF/kWh (ElCom 2026 IWB H4) | 0.3325 | 0.3325 | constant in baseline_sweep.py (data/README.md) | sourced https://www.strompreis.elcom.admin.ch/operator/624?period=2026&category=H4 (data/README.md) | yes |
| A4 | heat value CHF/kWh (price / 2.5, case rule) | 0.1330 | - | constant in baseline_sweep.py | computed (case rule) | n/a (not a plan figure) |
| B1 | total heat demand kWh/yr | 31,231 | 31,231 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B2 | space heating kWh/yr | 26,851 | 26,851 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B3 | hot water kWh/yr | 4,380 | 4,380 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B4.1 | N=1 coverage % / dumped kWh / utilisation % | 19.5 / 0.0 / 87.1 | 19.5 / 0.0 / 87.1 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B5.1 | N=1 server-h / electricity CHF / heat value CHF | 7,629 / 2,537 / 812 | 7,629 / 2,537 / 812 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B6.1 | N=1 break-even CHF/server-h | 0.2261 | 0.2261 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B4.6 | N=6 coverage % / dumped kWh / utilisation % | 79.6 / 0.0 / 59.1 | 79.6 / 0.0 / 59.1 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B5.6 | N=6 server-h / electricity CHF / heat value CHF | 31,067 / 10,330 / 3,306 | 31,067 / 10,330 / 3,306 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B6.6 | N=6 break-even CHF/server-h | 0.2261 | 0.2261 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B4.8 | N=8 coverage % / dumped kWh / utilisation % | 92.9 / 0.0 / 51.8 | 92.9 / 0.0 / 51.8 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B5.8 | N=8 server-h / electricity CHF / heat value CHF | 36,281 / 12,063 / 3,860 | 36,281 / 12,063 / 3,860 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B6.8 | N=8 break-even CHF/server-h | 0.2261 | 0.2261 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B7 | N=13 always-on: coverage % / utilisation % | 100 / 100 | 100 / 100 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B8 | N=13 always-on: dumped kWh / server-h / elec CHF / heat CHF | 59,839 / 113,880 / 37,865 / 4,154 | 59,839 / 113,880 / 37,865 / 4,154 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B9 | N=13 always-on break-even | 0.2960 | 0.2960 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B10 | N=2 coverage % / utilisation % | 32.7 / 73.0 | 32.7 / 73.0 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B11 | N=6 tank 10 kWh / 140 kWh coverage % | 78.8 / 80.3 | 78.8 / 80.3 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B12 | run h/yr of the 6th / 7th / 8th server | 3,796 / 2,933 / 2,281 | 3,796 / 2,933 / 2,281 | `python3 analysis/baseline_sweep.py` | computed | yes |
| B13 | unlimited: N=8 minus N=6 coverage pts / utilisation pts (Q&A 2 '13 points for 7 points') | 13 / 7 | 13 / 7 | `python3 analysis/baseline_sweep.py` (difference read by hand) | computed | yes |
| C1 | coverage % N=6 / N=8 (2 decimals) | 73.67 / 86.14 | 73.67 / 86.14 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C1b | coverage % N=6 / N=8 (pitch, 1 decimal) | 73.7 / 86.1 | 73.7 / 86.1 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C2 | heat dumped kWh N=6 / N=8 | 0 / 0 | 0 / 0 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C3 | utilisation % N=6 / N=8 | 54.72 / 47.98 | 54.72 / 47.98 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C3b | utilisation % (pitch) | 54.7 / 48.0 | 54.7 / 48.0 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C4 | offers accepted % N=6 / N=8 | 94.7 / 93.8 | 94.7 / 93.8 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C5 | summer (Jun-Aug) J1 accepted % N=6 / N=8 | 89.6 / 90.3 | 89.6 / 90.3 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C6.6 | N=6 missed x of y accepted jobs, seeds [1, 2, 3] | 0 of 31,908 / 0 of 31,694 / 0 of 31,996 | 0 of 31,908 / 0 of 31,694 / 0 of 31,996 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C6.8 | N=8 missed x of y accepted jobs, seeds [1, 2, 3] | 0 of 36,771 / 0 of 36,989 / 0 of 37,201 | 0 of 36,771 / 0 of 36,989 / 0 of 37,201 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C7 | server-hours sold N=6 / N=8 | 28,761 / 33,626 | 28,761 / 33,626 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C8 | electricity CHF/yr N=6 / N=8 | 9,563 / 11,181 | 9,563 / 11,181 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C9 | heat value used CHF/yr N=6 / N=8 (dashboard 'heat worth') | 3,060 / 3,578 | 3,060 / 3,578 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C10 | break-even CHF per sold server-h N=6 / N=8 | 0.2261 / 0.2261 | 0.2261 / 0.2261 | `python3 analysis/r4_headline.py` s.3 | computed | yes |
| C11 | break-even with 15-min restart line N=6 / N=8 | 0.2278 / 0.2286 | 0.2278 / 0.2286 | `python3 analysis/r4_headline.py` s.3 | computed; 15 min is an assumption | yes |
| C12 | N=8 extra coverage points under the headline | 12.5 | 12.5 | `python3 analysis/r4_headline.py` s.3 (difference by hand) | computed | yes |
| C13 | N=8 contract larger than N=6's, % (yearly mean offer rate) | 17 | 17 | `python3 analysis/r4_headline.py` s.2 (ratio by hand) | computed | yes |
| C14 | jobs offered per day N=6 / N=8 (expected) | 92 / 108 | 92 / 108 | `python3 analysis/r4_headline.py` s.2 | computed | yes |
| C15 | N=6 January J1 / J2 jobs per day; July J1 / J2 | 143.9 / 18.0 / 15.0 / 1.9 | 143.9 / 18.0 / 15.0 / 1.9 | `python3 analysis/r4_headline.py` s.2 | computed | yes |
| C16 | sold share of unlimited-demand permit hours % N=6 / N=8 | 93 / 93 | 93 / 93 | `python3 analysis/r4_headline.py` s.3 | computed (plan: 'about 93%') | yes |
| C17 | starts per year N=6 / N=8 (headline) | 854 / 1,497 | - | `python3 analysis/r4_headline.py` s.3 | computed | n/a (not a plan figure) |
| C18 | perfect-forecast check: missed jobs, all seeds, N=6 + N=8 | 0 | 0 | `python3 analysis/r4_headline.py` s.4 'check' row | computed | yes |
| D1 | saturating: accepted % N=6 / N=8 | 54.9 / 49.2 | 54.9 / 49.2 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D1b | saturating: summer J1 accepted % | 0.0 / 0.0 | 0.0 / 0.0 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D2 | shaped200: coverage % | 78.96 / 92.25 | 78.96 / 92.25 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D2b | shaped200: accepted % | 44.1 / 46.3 | 44.1 / 46.3 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D2c | shaped200: mean missed % | 0.084 / 0.051 | 0.084 / 0.051 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D2d | shaped200 seed 1: missed x of y N=6 / N=8 | 33 of 28,928 / 11 of 35,991 | 33 of 28,928 / 11 of 35,991 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D3 | shaped120 seed 1: coverage % N=6 / N=8 | 76.46 / 89.72 | 76.46 / 89.72 | none saved: inline `python3 -c` in r4-demand-headline.md s.(b) | computed (was inline command) | yes |
| D3b | shaped150 seed 1: coverage % N=6 / N=8 | 78.23 / 91.80 | 78.23 / 91.80 | none saved: inline `python3 -c` in r4-demand-headline.md s.(b) | computed (was inline command) | yes |
| D3c | shaped120 / shaped150 seed 1: accepted % N=6 / N=8 / N=6 / N=8 | 81.7 / 82.8 / 64.0 / 65.4 | 81.7 / 82.8 / 64.0 / 65.4 | none saved: inline `python3 -c` in r4-demand-headline.md s.(b) | computed (was inline command) | yes |
| D3d | N=8 missed at shaped120 / shaped150, seed 1 | 12 / 13 | 12 / 13 | none saved: inline `python3 -c` in r4-demand-headline.md s.(b) | computed (was inline command) | yes |
| D4 | shaped50: coverage % | 37.99 / 44.59 | 37.99 / 44.59 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D4b | shaped50: starts per year (plan '3,000-3,400') | 3,021 / 3,367 | - | `python3 analysis/r4_headline.py` s.4 | computed | n/a (not a plan figure) |
| D5 | flat customer, same yearly volume: coverage % (2 dec.) | 53.67 / 60.48 | 53.67 / 60.48 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D5b | flat customer: coverage % (pitch) | 53.7 / 60.5 | 53.7 / 60.5 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D5c | flat customer: accepted % / summer J1 % | 64.1 / 62.4 / 0.0 / 0.0 | 64.1 / 62.4 / 0.0 / 0.0 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D5d | flat customer: missed jobs, all seeds N=6 + N=8 | 0 | 0 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6 | fixed contract (N=6's offers): coverage % N=6 / N=8 | 73.67 / 73.88 | 73.67 / 73.88 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6b | fixed contract: N=8 gain in coverage points (Read-this-first '0.2') | 0.2 | 0.2 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6c | fixed contract: coverage % N=6 / N=8 (Q&A '73.7 against 73.9') | 73.7 / 73.9 | 73.7 / 73.9 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6d | fixed contract: accepted % N=6 / N=8 | 94.7 / 94.7 | 94.7 / 94.7 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6e | fixed contract: N=8 utilisation % | 41.2 | 41.2 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6f | fixed contract: starts per year N=6 / N=8 | 854 / 2,944 | 854 / 2,944 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6g | fixed contract: starts ratio N=8 / N=6 (plan says 'triples') | 3.4 | - | new | computed | n/a (not a plan figure) |
| D6h | fixed contract: restart break-even N=6 / N=8 | 0.2278 / 0.2320 | 0.2278 / 0.2320 | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe, now here) | yes |
| D6i | context: N=6 on N=8's contract, coverage % | 74.99 | - | none saved: round-4 critic scratch `r4demand_critic_probe.py` (scratchpad) | computed (critic probe) | n/a (not a plan figure) |
| D7 | named customer only (SRF-size archive, flat): coverage % | 4.8 | 4.8 | `python3 analysis/r4_headline.py` s.4 | computed | yes |
| D8 | all-year pin, N=6: pinned h/yr / share of sold h % | 7,531.7 / 25.8 | - | `python3 analysis/r4_headline.py` s.5 | computed | n/a (not a plan figure) |
| D8b | all-year pin, N=6: pinned h/yr | 7,532 | 7,532 | `python3 analysis/r4_headline.py` s.5 | computed | yes |
| D8c | all-year pin, N=6: share of sold hours % | 25.8 | 25.8 | `python3 analysis/r4_headline.py` s.5 | computed | yes |
| D8d | all-year pin, N=6: summer J1 accepted % (from 89.6) | 0.0 | 0.0 | `python3 analysis/r4_headline.py` s.5 | computed | yes |
| D9 | demo-day pin: coverage % N=6 without -> with | 73.675 / 73.673 | 73.675 / 73.673 | `python3 analysis/r4_headline.py` s.5 | computed | yes |
| D9b | demo-day pin: coverage % N=8 without -> with | 86.136 / 86.187 | 86.136 / 86.187 | `python3 analysis/r4_headline.py` s.5 | computed | yes |
| D10.6 | demo day N=6: date, slot, pause, resume, hours run (seed 1) | 2025-07-15 slot 1 P02 R18 8 h | 2025-07-15 slot 1 P02 R18 8 h | `python3 analysis/r4_headline.py` s.5 | computed | yes |
| D10.8 | demo day N=8: date, slot, pause, resume, hours run (seed 1) | 2025-01-25 slot 7 P14 R19 19 h | 2025-01-25 slot 7 P14 R19 19 h | `python3 analysis/r4_headline.py` s.5 | computed | yes |
| D11 | 2025-01-13 permit-holding idle server-hours N=6 / N=8 (seed 1) | 22 / 16 | 22 / 16 | none saved: inline `python3 -c` in r4-demand-headline.md s.(b) | computed (was inline command) | yes |
| E1 | homeowner gets heat free: electricity per server-h | 0.3325 | 0.3325 | `python3 analysis/r2_fleet_economics.py` s.1 | computed | yes |
| E2 | heat value at stake CHF/yr N=6 / N=8 (unlimited) | 3,306 / 3,860 | 3,306 / 3,860 | `python3 analysis/r2_fleet_economics.py` s.1 | computed | yes |
| E3 | 80% / 50% sold, unsold still run: break-even | 0.283 / 0.452 | 0.283 / 0.452 | `python3 analysis/r2_fleet_economics.py` s.1 | computed (r2_fleet_economics formula) | yes |
| E4 | 67% sold, unsold still run: break-even | 0.3375 | 0.3375 | `python3 analysis/r3_income.py` s.5B | computed (r3_income 5B formula) | yes |
| F1 | paused servers powered at 17.6% idle: break-even N=6 / N=8 | 0.2659 / 0.2814 | 0.2659 / 0.2814 | `python3 analysis/r2_realism.py` (iv a) | computed; idle share sourced (SPECpower), applying it to this server is an assumption | yes |
| F1b | same: summer server-hours sold N=6 / N=8 ('nothing sold in summer') | 0 / 0 | 0 / 0 | `python3 analysis/r2_realism.py` (iv a) | computed | yes |
| F2 | starts/yr plain follow / cap + 8 kWh band, N=6 then N=8 | 1,732 / 379 / 2,208 / 891 | 1,732 / 379 / 2,208 / 891 | `python3 analysis/r2_realism.py` (v) | computed | yes |
| G1 | wall power kW central (low-high) | 0.95 / 0.75 / 1.22 | 0.95 / 0.75 / 1.22 | `python3 analysis/r4_machine.py` | assumption built on sourced 165 W / 320 W maxima | yes |
| G2 | audio-h per kWh: Cisco 6.1-0017 / HPE 6.1-0056 (plan 'about 1,300-1,400') | 1,411 / 1,341 | - | `python3 analysis/r4_machine.py` | computed | n/a (not a plan figure) |
| G2b | same, rounded to hundreds | 1,300 / 1,400 | 1,300 / 1,400 | `python3 analysis/r4_machine.py` | computed | yes |
| G3 | Wh per audio-hour, reference server | 0.7 | 0.7 | `python3 analysis/r4_machine.py` | computed | yes |
| G4 | HPE 2U box lower than Cisco blade, % | 5 | 5 | `python3 analysis/r4_machine.py` | computed from sourced MLPerf rows | yes |
| G5 | laptop / reference Wh per audio-h factor (1.3 and 1.5 Wh) | 1.8 / 2.1 | - | `python3 analysis/r4_machine.py` | computed | n/a (not a plan figure) |
| G5b | factor, rounded | 2 | 2 | `python3 analysis/r4_machine.py` | computed (plan 'about 2') | yes |
| G6 | million output tokens per kWh | 36 | 36 | `python3 analysis/r4_machine.py` | computed | yes |
| G7 | installed CHF per 1 kW server (central), exact / to 1,000 | 33,652 / 34,000 | - | `python3 analysis/r4_machine.py` | computed | n/a (not a plan figure) |
| G7a | installed CHF per 1 kW server, rounded to 1,000 (plan 'about 34,000') | 34,000 | 34,000 | `python3 analysis/r4_machine.py` | computed | yes |
| G7b | installed CHF per house N=6, exact / to 10,000 (plan 'about 200,000') | 201,914 / 200,000 | - | `python3 analysis/r4_machine.py` | computed | n/a (not a plan figure) |
| G7d | installed CHF per house N=6 to 10,000 / N=8 to 1,000 | 200,000 / 264,000 | 200,000 / 264,000 | `python3 analysis/r4_machine.py` | computed | yes |
| G7c | GPU value per house N=6, CHF to 1,000 (plan 'about 121,000') | 121,000 | 121,000 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic extra, now here) | yes |
| G8 | house integration CHF low / central / high, hundreds | 10,700 / 14,800 / 20,100 | 10,700 / 14,800 / 20,100 | `python3 analysis/r4_machine.py` | computed from a proxy (BFE 2015) + assumption | yes |
| G9 | list value of one server-hour, mix 50/50, low / central / high CHF | 7.7 / 14.3 / 38.2 | 7.7 / 14.3 / 38.2 | `python3 analysis/r4_machine.py` | computed (prices sourced in round 3) | yes |
| G10 | round-3 two-machine list value | 4.3 / 9.4 / 30.7 | 4.3 / 9.4 / 30.7 | `python3 analysis/r3_income.py` s.2 | computed in round 3 (constant echoed by r4_machine) | yes |
| G11 | share of list needed N=6 central: operation % | 1.6 | 1.6 | `python3 analysis/r4_machine.py` | computed | yes |
| G11b | N=6 5-y / 8-y payback share % (simple) | 10.7 / 7.3 | 10.7 / 7.3 | `python3 analysis/r4_machine.py` | computed | yes |
| G11c | N=6 5-y / 8-y share % at 5% interest | 12.1 / 8.6 | 12.1 / 8.6 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic probe, now here); 5% is an assumption | yes |
| G11d | N=6 5-y / 8-y share % at 67% sold | 16.0 / 10.9 | 16.0 / 10.9 | `python3 analysis/r4_machine.py` | computed | yes |
| G11e | N=8 operation / 5-y / 8-y share % | 1.6 / 11.8 / 8.0 | 1.6 / 11.8 / 8.0 | `python3 analysis/r4_machine.py` | computed | yes |
| G11f | N=8 5-y / 8-y share % at 5% interest | 13.4 / 9.5 | 13.4 / 9.5 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic probe, now here) | yes |
| G11g | pitch rounding: 5-y / 8-y share; at 5% interest | 11 / 7 / 12 / 9 | 11 / 7 / 12 / 9 | `python3 analysis/r4_machine.py` | computed | yes |
| G11h | 5-y share range, low cost + high price .. high cost + low price % | 3.1 / 25.3 | 3.1 / 25.3 | `python3 analysis/r4_machine.py` | computed | yes |
| G11i | 5-y / 8-y share at LOW price, central cost, 67% sold % | 30 / 20 | 30 / 20 | `python3 analysis/r4_machine.py` | computed | yes |
| G12 | 5-y share ex VAT N=6 / N=8 % | 10.0 / 11.0 | 10.0 / 11.0 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic extra, now here) | yes |
| G13 | LLM only: 5-y / 8-y share %; at 5% | 31.7 / 21.5 / 35.8 / 25.6 | 31.7 / 21.5 / 35.8 / 25.6 | `python3 analysis/r4_machine.py` s.4 (5 y only); 8 y and 5%: none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (8-y and 5% by critic probe, now here) | yes |
| G13b | LLM only, pitch rounding (Q&A '32-36%') | 32 / 36 | 32 / 36 | `python3 analysis/r4_machine.py` | computed | yes |
| G13c | transcription only: 5-y share % | 6.4 | 6.4 | `python3 analysis/r4_machine.py` | computed | yes |
| G14 | round 3 like-for-like: share on the mix basis % | 24.0 | 24.0 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic extra, now here) | yes |
| G14b | round 3 share on the J1-only basis % | 20 | 20 | `python3 analysis/r3_income.py` s.7 | computed (r3_income section 7) | yes |
| G15 | CHF needed per sold server-h N=6: 5 y / 5 y at 5% / 8 y / 8 y at 5% | 1.53 / 1.73 / 1.04 / 1.23 | 1.53 / 1.73 / 1.04 / 1.23 | `python3 analysis/r4_machine.py` s.3 (simple); 5%: none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (5% by critic probe, now here) | yes |
| G16 | USD per GPU-hour the operator needs: 5 y / 8 y / 5 y at 67% sold | 0.43 / 0.30 / 0.65 | 0.43 / 0.30 / 0.65 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic extra, now here) | yes |
| G17 | payback y at 20% share, 67% sold, N=6 central / low (simple) | 3.9 / 8.1 | 3.9 / 8.1 | `python3 analysis/r4_machine.py` | computed | yes |
| G17b | same at 5% interest, N=6 central / low; N=8 low | 4.4 / 10.6 / 12.3 | 4.4 / 10.6 / 12.3 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic probe, now here) | yes |
| G18 | cheapest rental 0.41 USD/GPU-h: payback y per server, all permit h rented | 7.0 | 7.0 | `python3 analysis/r4_machine.py` | computed; 0.41 USD sourced (getdeploying.com), 80% host share sourced (round 2) | yes |
| G18b | renter prices USD/GPU-h cheapest / RunPod / median (echo) | 0.41 / 0.72 / 0.92 | 0.41 / 0.72 / 0.92 | `python3 analysis/r4_machine.py` s.5 (echo) | sourced https://getdeploying.com/gpus/nvidia-rtx-pro-4500 and https://www.runpod.io/gpu-models/rtx-pro-4500-se | yes |
| G19 | unlimited demand, half J1: audio-h per day per house, to 1,000 (plan 'about 60,000') | 60,000 | 60,000 | `python3 analysis/r4_machine.py` | computed | yes |
| G19b | average Mbit/s at 32 kbit/s | 80 | 80 | `python3 analysis/r4_machine.py` | computed; codec rate assumption | yes |
| G19c | peak-hour Mbit/s half J1 / all J1 | 135 / 271 | 135 / 271 | none saved: round-4 critic one-liners (output in r4-reference-machine-critique.md s.3) | computed (critic extra, now here) | yes |
| G20 | 5-y hardware share across wall power low / high % | 10.2 / 11.3 | 10.2 / 11.3 | `python3 analysis/r4_machine.py` | computed | yes |
| G21 | market form: CHF per sold server-h (5 y), rounded | 1.5 | 1.5 | `python3 analysis/r4_machine.py` | computed | yes |
| G22 | CPU-only LLM (6.1-0032) at the low price, CHF per server-h | 0.148 | 0.148 | none saved: hand formula in r3-machine-and-income.md | computed; 1 kW is an assumption; 1,227.99 tok/s sourced (MLPerf v6.1 summary) | yes |
| G23 | lowest marketplace host rate, CHF per kW-h (Salad 4090 min x 2 GPU/kW) | 0.215 | 0.215 | `python3 analysis/r2_fleet_economics.py` s.3 | computed; host rate sourced in round 2, 2 GPU per kW assumption | yes |
| H1.6 | N=6 OLD two-machine basis (laptop J1, B200-slice J2), income at 20%, central, k CHF/yr | 53.6 | 53.6 | `python3 analysis/r4_headline.py` s.3 | computed (r4_headline.money); scenario, not income | yes |
| H1b.6 | N=6 OLD two-machine basis, low / high, k CHF/yr | 24.5 / 177.2 | - | `python3 analysis/r4_headline.py` s.3 | computed (r4_headline.money) | n/a (not a plan figure) |
| H2.6 | N=6 NEW reference-server income at 20%, low / central / high, k CHF/yr | 43.6 / 80.9 / 218.3 | - | none: new in round 5 | computed (NEW: r4_machine.list_value x headline sold hours per job type); scenario, not income | n/a (not a plan figure) |
| H3.6 | N=6 sold J1 / J2 server-h (headline) | 14,101 / 14,660 | - | none: new in round 5 | computed | n/a (not a plan figure) |
| H4.6 | N=6 list value of sold work, reference server, central, k CHF/yr | 404.7 | - | none: new in round 5 | computed (NEW) | n/a (not a plan figure) |
| H5.6 | N=6 share needed under the headline: operation / + install 5 y / 8 y / 5 y at 5% (central) | 1.6 / 11.6 / 7.8 / 13.1 | - | none: new in round 5 | computed (NEW; same basis as the share-needed line, but headline sold hours instead of every permit hour) | n/a (not a plan figure) |
| H6.6 | N=6 audio-hours per year implied by sold J1: two-machine (laptop) / reference server, millions | 9.4 / 19.9 | - | none: new in round 5 | computed (NEW) | n/a (not a plan figure) |
| H7.6 | N=6 NEW basis: margin after electricity-heat, k CHF/yr; payback y simple / at 5% (central) | 74.4 / 2.7 / 3.0 | - | none: new in round 5 | computed (NEW) | n/a (not a plan figure) |
| H1.8 | N=8 OLD two-machine basis (laptop J1, B200-slice J2), income at 20%, central, k CHF/yr | 62.6 | 62.6 | `python3 analysis/r4_headline.py` s.3 | computed (r4_headline.money); scenario, not income | yes |
| H1b.8 | N=8 OLD two-machine basis, low / high, k CHF/yr | 28.4 / 207.5 | - | `python3 analysis/r4_headline.py` s.3 | computed (r4_headline.money) | n/a (not a plan figure) |
| H2.8 | N=8 NEW reference-server income at 20%, low / central / high, k CHF/yr | 50.6 / 94.0 / 254.3 | - | none: new in round 5 | computed (NEW: r4_machine.list_value x headline sold hours per job type); scenario, not income | n/a (not a plan figure) |
| H3.8 | N=8 sold J1 / J2 server-h (headline) | 16,333 / 17,293 | - | none: new in round 5 | computed | n/a (not a plan figure) |
| H4.8 | N=8 list value of sold work, reference server, central, k CHF/yr | 470.2 | - | none: new in round 5 | computed (NEW) | n/a (not a plan figure) |
| H5.8 | N=8 share needed under the headline: operation / + install 5 y / 8 y / 5 y at 5% (central) | 1.6 / 12.9 / 8.6 / 14.6 | - | none: new in round 5 | computed (NEW; same basis as the share-needed line, but headline sold hours instead of every permit hour) | n/a (not a plan figure) |
| H6.8 | N=8 audio-hours per year implied by sold J1: two-machine (laptop) / reference server, millions | 10.9 / 23.0 | - | none: new in round 5 | computed (NEW) | n/a (not a plan figure) |
| H7.8 | N=8 NEW basis: margin after electricity-heat, k CHF/yr; payback y simple / at 5% (central) | 86.4 / 3.1 / 3.4 | - | none: new in round 5 | computed (NEW) | n/a (not a plan figure) |
| H9.6 | N=6 NEW, exact share-needed basis (every permit hour sold, 50/50 mix, unlimited demand), income at 20%, low / central / high, k CHF/yr | 47.9 / 88.6 / 237.6 | - | none: new in round 5 | computed (NEW; r4_machine.list_value x baseline run hours) | n/a (not a plan figure) |
| H9b.6 | N=6 same at 67% sold (r4_machine section 3 convention), central, k CHF/yr | 59.3 | - | `python3 analysis/r4_machine.py` s.3 payback block | computed (equals r4_machine 'income' line) | n/a (not a plan figure) |
| H9.8 | N=8 NEW, exact share-needed basis (every permit hour sold, 50/50 mix, unlimited demand), income at 20%, low / central / high, k CHF/yr | 55.9 / 103.4 / 277.5 | - | none: new in round 5 | computed (NEW; r4_machine.list_value x baseline run hours) | n/a (not a plan figure) |
| H9b.8 | N=8 same at 67% sold (r4_machine section 3 convention), central, k CHF/yr | 69.3 | - | `python3 analysis/r4_machine.py` s.3 payback block | computed (equals r4_machine 'income' line) | n/a (not a plan figure) |
| H8 | SRF-size archive (1.25 M audio-h) in server-h: laptop rule / reference server | 1,875 / 886 | - | none: new in round 5 | computed; 1.25 M sourced (srf.ch, URL in plan) | n/a (not a plan figure) |
| H8b | SRF archive at laptop rule: server-h / % of one N=6 house-year | 1,875 / 6 | 1,875 / 6 | `python3 analysis/r4_headline.py` s.1 | computed | yes |
| H8c | two-machine basis: audio-h/yr in the N=6 income line, millions | 9.4 | 9.4 | none saved: critic hand calc (14,101 x 667) | computed | yes |
| I1 | layout A, underfloor + loss 2.80: coverage % N=6 / N=8 | 77.6 / 90.6 | 77.6 / 90.6 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I1b | June-August coverage % (layout A) | 82.2 | 82.2 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I1c | utilisation % N=6 / N=8 (layout A) | 59.4 / 52.1 | 59.4 / 52.1 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I1d | break-even, case convention: underfloor N=6 / radiator 55/45 N=6 | 0.2293 / 0.2294 | 0.2293 / 0.2294 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I1e | break-even, top-up charged to servers N=6 / N=8 | 0.234 / 0.234 | 0.234 / 0.234 | `python3 analysis/r4_tank_layout.py` | computed (plan 'about 0.234') | yes |
| I2 | tank loss only: coverage change pts N=6 / N=8 | -0.3 / -0.3 | -0.3 / -0.3 | `python3 analysis/r2_realism.py` (i) 2.80 row | computed | yes |
| I2b | tank loss only: break-even rise N=6 / N=8 | 0.0030 / 0.0031 | 0.0030 / 0.0031 | `python3 analysis/r2_realism.py` (i) 2.80 row | computed | yes |
| I3 | no-build-scope proxy: dhw_direct_share=37/45 + loss: coverage % N=6 / N=8 | 77.72 / 90.74 | 77.72 / 90.74 | none saved: one-liner in r4-tank-temperatures-critique.md (C25) | computed | yes |
| I4 | usable buffer kWh: summer / floor 35/28 / 50/40 / 55/45 / 70/55 design hour | 34.9 / 25.6 / 11.6 / 5.8 / 0.0 | 34.9 / 25.6 / 11.6 / 5.8 / 0.0 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I5 | hot-water direct share % at 55 / 52 / 60 C setpoint | 82.2 / 88.1 / 74.0 | 82.2 / 88.1 / 74.0 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I5b | electric top-up kWh/yr at 55 C | 779 | 779 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I6 | usable tank 10 / 5 kWh costs coverage pts (floor heating, N=6) | 1.0 / 1.5 | 1.0 / 1.6 | `python3 analysis/r4_tank_layout.py` | computed | **no** |
| I7 | radiator 55/45 + loss, upper bound (servers keep running): coverage % N=6 / N=8 | 77 / 90 | 77 / 90 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I7b | radiator 55/45 + loss, LOWER bound (servers stop if return > 40 C): coverage % N=6 / N=8 | 64 / 73 | 64 / 73 | none saved: round-4 critic scratch `r4tankcrit_check.py` (scratchpad) | computed (critic probe, now here) | yes |
| I7c | same, one decimal | 64.3 / 73.0 | 64.3 / 73.0 | none saved: round-4 critic scratch `r4tankcrit_check.py` (scratchpad) | computed (critic probe, now here) | yes |
| I8 | radiator 55/45: heating hours with return > 40 C (exact) | 853 | - | none saved: round-4 critic scratch `r4tankcrit_check.py` (scratchpad) | computed (critic probe, now here) | n/a (not a plan figure) |
| I8a | same, to 10 h (plan Q&A 'about 850') | 850 | 850 | none saved: round-4 critic scratch `r4tankcrit_check.py` (scratchpad) | computed (critic probe, now here) | yes |
| I8b | radiator 55/45 return temperature at the design hour, C | 45 | 45 | `python3 analysis/r4_tank_layout.py` s.3 (bin value only) | computed (plan '44-45') | yes |
| I9 | radiator 70/55: upper bound N=6 / lower bound (ret <= 40 C) N=6 / N=8 % | 59 / 29 / 31 | 59 / 30 / 31 | `python3 analysis/r4_tank_layout.py` s.5 (upper); lower: none saved: round-4 critic scratch `r4tankcrit_check.py` (scratchpad) | computed (lower bounds: critic probe, now here); plan words 'at most about 59%', 'about 30%' | **no** |
| I9b | same, one decimal (round-4 critic table: 59.2 / 29.5 / 31.2) | 59.2 / 29.5 / 31.2 | 59.2 / 29.5 / 31.2 | `python3 analysis/r4_tank_layout.py` s.5 (upper); lower: none saved: round-4 critic scratch `r4tankcrit_check.py` (scratchpad) | computed (critic probe, now here) | yes |
| I10 | 45 C loop: June-August % / radiator 55/45 N=8 loss in pts | 71.1 / 10.6 | 71.1 / 10.6 | `python3 analysis/r4_tank_layout.py` | computed | yes |
| I12 | higher space-heating draw floor (mixed tank): largest coverage loss, pts | 0.2 | - | `python3 analysis/r4_tank_layout.py` s.6b | computed (plan '<= 0.2 points') | n/a (not a plan figure) |
| I13 | layout A temperatures: buffer top C / fresh-water preheat C | 50 / 47 | 50 / 47 | `python3 analysis/r4_tank_layout.py` s.1 | computed from sourced 55 C outlet (NVIDIA blog) and 5 K / 3 K approaches (Lenovo / suissetec; interpretation) | yes |
| I11 | air-cooled, no direct hot water: coverage % N=6 / N=8 | 70.5 / 81.7 | 70.5 / 81.7 | `python3 analysis/r2_realism.py` (iii) | computed | yes |
| J1 | ECMWF ifs025 RMSE K, day 1 / day 7 | 1.16 / 2.85 | 1.16 / 2.85 | `python3 analysis/r2_deadline_sim.py` s.0 (full run, minutes) | computed from archived forecasts (analysis/r2_data/prev_ecmwf_ifs025.csv) | yes |
| J1b | ifs025 day-1 bias K | +0.29 | +0.29 | `python3 analysis/r2_deadline_sim.py` s.0 | computed | yes |
| J2.6 | N=6 saturating, ifs025, NO guard, no partner, 2025, seeds 1-5: missed % mean / min / max | 0.146 / 0.097 / 0.267 | 0.146 / 0.097 / 0.267 | `python3 analysis/r2_deadline_sim.py` s.2 | computed (round-2 run); plan's '0.1-0.6%' upper end came from 2024 runs by the round-2 critic, not in a script | yes |
| J2.8 | N=8 saturating, ifs025, NO guard, no partner, 2025, seeds 1-5: missed % mean / min / max | 0.294 / 0.160 / 0.386 | 0.294 / 0.160 / 0.386 | `python3 analysis/r2_deadline_sim.py` s.2 | computed (round-2 run); plan's '0.1-0.6%' upper end came from 2024 runs by the round-2 critic, not in a script | yes |
| J3 | named-customer volume vs shaped100 contract N=6 % | 6.3 | - | `python3 analysis/r4_headline.py` s.1 | computed | n/a (not a plan figure) |
| K1 | vendor sizing 5-20% of design load = servers (10 kW design / 0.8 kW per server) | 0.6 / 2.5 | 0.6 / 2.5 | none saved: hand arithmetic | computed from sourced 5-20% (URL in r4-plan-detail.md section L) | yes |
| K2 | heat receipt: J2 (4 server-h) heat kWh / person-days of case hot water | 3.20 / 1.07 | 3.20 / 1.07 | `python3 analysis/r3_creativity_usability.py` s.1 | computed; job size assumption | yes |
| K3 | laptop J1 energy Wh per audio-hour used downstream (r3_income.E_PROBE) | 1.5 | 1.5 | `python3 analysis/r3_whisper_energy_probe.py` (laptop measurement) | measured 2026-11-21 by r3_whisper_energy_probe.py, NOT re-run here (plan range 1.3-1.5) | yes |
| K4 | J2 input tokens billed per output token | 6 | 6 | `python3 analysis/r3_income.py` s.1 | assumption (r3_income.IN_PER_OUT) | yes |
| K6 | marketplace host share (Salad 4090 host rate / renter price, lowest tier) | 0.80 | 0.80 | `python3 analysis/r2_fleet_economics.py` s.3 host-share line | computed from rates sourced in round 2 (r2-host-income-hardware.md) | yes |
| K5 | MLPerf throughput: whisper Cisco / HPE samples/s; llama tok/s | 61.10 / 58.08 / 9518.66 | 61.10 / 58.08 / 9518.66 | `python3 analysis/r4_machine.py` s.1 | sourced (MLPerf v6.1 loadgen logs, URLs in r4-reference-machine.md section 2.1) | yes |

IDs: A inputs · B unlimited-demand balance · C headline run · D comparison rows · E break-even table · F pause physics · G reference server and installed cost · H computing income on two bases · I temperatures and realism column · J forecast and misses · K small derived numbers.
