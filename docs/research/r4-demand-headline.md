# Round 4: demand side and the headline run

Investigator for the weak point "which offer scenario, customer type and arrival source the key figures are computed under" (must-have 1: "State how many jobs arrive per day and where that number comes from; a model that assumes unlimited jobs must say so"; must-have 3: missed deadlines, computing income, break-even). Written Sat 21 Nov 2026, about 09:50 to 10:30. This file plans and assesses. It does not build the scheduler.

**Status labels:** *sourced* = number read by me on the page at the URL given (opened with WebFetch, which returns a summary plus quotes: re-read by eye before a slide); *computed* = printed by a script in `analysis/` (script and command named); *assumption* = our own choice; *unverified* = not checked or only seen in a search snippet.

**Currency:** CHF. 1 USD = 0.8392 CHF (ECB reference rates of 20 Nov 2026, sourced in round 1, re-confirmed by the round-3 critic: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>). Electricity 0.3325 CHF/kWh and heat value = price ÷ 2.5, from `data/README.md`.

**Tools:** WebSearch and WebFetch only. **Firecrawl calls used: 0 of 3.**

**Files written this round**

| File | What |
|---|---|
| `analysis/r4_headline.py` | New. Stdlib only. Imports (does not edit) `baseline_sweep`, `r2_deadline_sim`, `r3_policy_check`, `r3_income`. Yearly loop = `r3_policy_check.run()` without restart in execution, plus custom offer rates, sold hours per job type and an optional pinned real job. Section 0 checks it reproduces `r3_policy_check.run()` exactly. |
| `analysis/r4_offers_shaped100_seed1.csv` | New. The headline offer stream for N=6 and N=8 (per hour: J1 offers, J2 offers, which type is admitted first), 8,760 rows, 310 kB. Written by `python3 analysis/r4_headline.py --write-offers analysis/r4_offers_shaped100_seed1.csv`. Its totals equal the run's offered jobs (checked: N=6 33,676, N=8 39,244). |
| this file | Findings |

---

## Bottom line

1. **Headline offer scenario: `shaped100`, a heat-shaped monthly contract equal to 100% of the house's normal heat-permit capacity (2020–24 weather), Poisson arrivals, seed 1.** On average 81.8 J1 + 10.2 J2 jobs a day at N=6 (143.9 + 18.0 in January, 15.0 + 1.9 in July), 95.9 + 12.0 at N=8. The number comes from five past years of Basel weather and the case's own demand formula, so it is reproducible and cannot see 2025. Nobody named sends it: it is a contract size we choose, filled through an aggregator (*assumption*).
2. **Why not saturating:** the must-have says "missed deadlines in % of jobs". Under saturating offers 45–51% of offered jobs are turned away and 0.0% of summer J1 is accepted (*computed*). A juror who reads "% of jobs" as offered jobs sees half the work refused. Under `shaped100` 94–95% are accepted, 90% of summer J1, and missed + refused stays at 5–6% under either reading.
3. **Headline key figures** (*computed*, `python3 analysis/r4_headline.py`, seeds 1–3, archived ECMWF forecast + 2 K guard, cap + 8 kWh band):

   | | N = 6 | N = 8 |
   |---|---|---|
   | Coverage | **73.7%** (73.2–74.0) | **86.1%** (85.7–86.5) |
   | Heat dumped | 0 kWh | 0 kWh |
   | Utilisation | 54.7% | 48.0% |
   | Jobs offered per day / accepted | 92.2 / 94.7% | 108.0 / 93.8% |
   | Missed deadlines | **0 of 31,908** accepted jobs (seed 1; 0 in all 3 seeds) | **0 of 36,771** (0 in all 3 seeds) |
   | Server-hours sold | 28,761 (92.6% of the unlimited-demand permit hours) | 33,626 (92.7%) |
   | Electricity / heat value used | 9,563 / 3,060 CHF | 11,181 / 3,578 CHF |
   | Break-even per sold server-hour | 0.2261 (0.2278 with the 15-min restart line) | 0.2261 (0.2286) |
   | Share of list value needed (central) | 2.4% | 2.4% |
   | Computing income, scenario (operator share 20%, central prices) | 53,631 CHF/yr | 62,589 CHF/yr |

   Coverage is 5.9 / 6.8 points below the unlimited-demand figures (79.6% / 92.9%) because unsold permit hours leave the server off.
4. **Missed is now 0 in every seed.** It was 1–12 a year in round 3 only because restart sat inside execution; the plan has since moved restart to an accounting line. The dashboard must therefore print "0 of 31,908 accepted jobs, forecast error only" and show the stress line next to it: at double the offer rate, 33 of 28,928 (N=6) and 11 of 35,991 (N=8) (*computed*). Never a bare 0%.
5. **Named Swiss customers are tiny against one house.** SRF's spoken-word archive (about 1.25 million audio-hours, *sourced*) is 1,875 server-hours at laptop efficiency: 6% of one N=6 house-year, or about 13 days of January permits. Swiss hospitals' 1.5 million inpatient stays a year (*sourced*) and Suva's 2.7 million invoices a year (*sourced*) are 0.1–2.5% of one house-year at an assumed 10 summarisation calls per document. So **demand, not heat, binds once there is more than one house**, and "jobs per day" can only be a contract size filled from many customers. A "named customer only" run gives **4.8% coverage**.
6. **Pinned real job (R6): refuted as specified, confirmed in a narrower form.** Pinned to slot 1 **all year**, the "always-ready" job is an unlimited backlog: 7,532 h a year, 25.8% of sold hours at N=6, summer J1 acceptance falls from 89.6% to **0.0%**, accepted jobs from 94.7% to 73.0%. That reintroduces exactly the inconsistency R6 was meant to fix. **Pinned on the demo day only**, it changes coverage by less than 0.06 points, keeps the pause pattern of the no-pin run (N=6 2025-07-15 slot 1 PAUSE 02:00 RESUME 18:00; N=8 2025-01-25 slot 7 PAUSE 14:00 RESUME 19:00), and its hours are counted as sold J1 work. Recommended form below.
7. **Recommend N = 8 under the headline scenario:** +12.5 coverage points (the jury's first scheduling criterion) at 0 dumped, 0 missed and identical break-even, and its January demo day pauses on the heat signal, which N=6 never does in January. Cost: worse hardware payback (8 servers need 0.75–1.00 CHF net per run hour against 0.54–0.64 for 6, round 2) and 643 more starts a year.

---

## (a) Customer types and their volumes

### Three customer types who could send deferrable, data-resident batch work

| Type | Work | Volume found | Status | Source (opened) |
|---|---|---|---|---|
| **A. Swiss public broadcaster archive** (SRF) | J1: transcribe the spoken archive for search and subtitles, deadline-free backlog | "gut eineinviertel Millionen Stunden gesprochene Inhalte" digitised = **about 1.25 million audio-hours**; 500 hours used to train one Swiss-German ASR system | sourced (article dated 22 Jan 2023) | <https://www.srf.ch/news/automatische-spracherkennung-computer-schryb-aues-mit-won-ig-hie-saege> |
| | same archive | "Über eine Million Stunden Audio- und rund 250'000 Stunden Videomaterial lagern im Keller des SRF in Zürich" | sourced (27 Mar 2024) | <https://www.srf.ch/radio-srf-musikwelle/audio-und-videomaterial-der-schatz-des-srf-im-archiv-roboter> |
| **B. Swiss hospitals / clinical research group** | J2: summarise or code discharge documents; patient data must stay in Switzerland | "2023 wurden in den Schweizer Spitälern 1,5 Millionen stationäre Aufenthalte" and 23.9 million outpatient consultations | sourced (BFS release, 26 Nov 2024) | <https://www.admin.ch/gov/de/start/dokumentation/medienmitteilungen.msg-id-103286.html> |
| **C. Swiss accident insurer** (Suva), data-residency document processing | J2: extract and check medical invoices | "2,7 Millionen Arzt- und Spitalrechnungen hat die Suva im letzten Jahr erhalten und geprüft" (2024) | sourced (page dated 24 Sep 2025) | <https://www.suva.ch/de-ch/ueber-uns/magazin-und-medien/medien/heilkosten> |

Not used: a search snippet attributing "130 million invoices a year" to a Swiss insurers' association. The Beobachter article I opened does not contain that sentence, so it is *unverified*. The SRG archive factsheet PDF returned HTTP 403. Federal Supreme Court (about 7,000–8,000 judgments a year, search snippet only, *unverified*) is too small to matter. No published core-hour usage was found for ETH's Euler cluster (search only).

### Converted to 1 kW server-hours (*computed*, `python3 analysis/r4_headline.py`, section 1)

Conversion factors (round 3): J1 667 audio-hours per server-hour (laptop rule, E = 1.5 Wh per audio-hour), 149 at E = 6.7 (2 × RTX 4090, *unverified*). J2 438,026 MLPerf summarisation samples per server-hour on a B200 slice (from 1,148.12 samples/s at 9,436.05 W, MLPerf v5.1 5.1-0062, sourced in round 3), 34,537 on 2 × Xeon 6787P if it draws 1 kW (*assumption*). **10 samples per document is an assumption.**

| Customer | Server-hours | Share of ONE N=6 house-year (31,067 permit server-h) |
|---|---|---|
| A, 1.25 M audio-h (one-off stock) | 1,875 to 8,389 | 6.0% to 27.0% |
| A, 1.0 M audio-h | 1,500 to 6,711 | 4.8% to 21.6% |
| B, 1.5 M stays a year | 34 to 434 per year | 0.11% to 1.4% |
| C, 2.7 M invoices a year | 62 to 782 per year | 0.20% to 2.5% |

**Reading.** At any of these efficiencies, one house at N=6 does more transcription and summarisation in a year than these Swiss customers need. One house could transcribe SRF's entire spoken archive in about 1,875 server-hours, which is 13 days of January permits at 144 server-hours a day (*computed* from the figures above). This is the honest answer to the round-3 founder question "who buys 28,000 audio-hours a day from one house": nobody we can name. A real fleet would need many customers per house, or heavier work per job (larger models, video, simulation) than the two job types in the plan. The flip side: transcription is cheap per audio-hour, which is why the list value per server-hour is high.

### Jobs per day for one reference house from a stated customer volume (*assumption*, labelled)

- Customer A's archive (1.25 million audio-hours), transcribed within **1 year** by **1 house** (both *assumption*):
  1,250,000 ÷ 333 audio-hours per J1 job ÷ 365 = **10.3 J1 jobs a day = 5.1 server-hours a day** (*computed*).
- Against the `shaped100` contract (81.8 server-hours a day at N=6, 95.9 at N=8) that fills **6.3% / 5.4%**. One such archive keeps 0.06 houses busy for a year.
- As a run ("named customer only", flat 5.1 server-hours a day): **coverage 4.78%, utilisation 3.6%** at N=6 (*computed*, section 4).

So the per-house jobs-per-day figure in the headline has to be a **contract size**, not one customer's volume. The pitch should say it that way (wording in (b)).

---

## (b) Headline offer scenario

### Choice: `shaped100`

**Definition.** Each month m the house is offered work equal to the **mean heat-permit server-hours per day of month m under plain heat-following in 2020–24** (Open-Meteo archive, ECMWF IFS, Basel; `analysis/r2_data/archive_basel_2020_2024_ecmwf_ifs.csv`; computed by `r2_deadline_sim.normal_capacity`). Half the offered work is J1, half J2.

**Defence against the must-have wording.**

| Must-have words | `shaped100` | `saturating` (old headline) |
|---|---|---|
| "how many jobs arrive per day" | a table of 12 monthly rates per N (below), mean 92.2 / 108.0 jobs a day | N × 24 server-hours a day: 288 J1 + 36 J2 a day at N=6 |
| "where that number comes from" | five past years of the reference location's weather through the case's demand formula; a contract a seller could sign before the year starts | "as much work as the servers could ever take": a capacity, not an arrival source |
| "a model that assumes unlimited jobs must say so" | finite. The unlimited case stays as one comparison line (79.6% / 92.9%) | it is the unlimited case in disguise and has to be labelled that way |
| "missed deadlines in % of jobs" | 0 missed; 5.3% / 6.2% of offered jobs not accepted | 0 / 0.025% missed of accepted jobs, but 45% / 51% of offered jobs refused |
| live job is one of the balance's jobs | summer J1 accepted 89.6% / 90.3% | summer J1 accepted 0.0% |
| jury: coverage first | 73.7% / 86.1% | 79.2% / 92.8% |

The coverage loss (5.6 / 6.7 points against saturating) is the price of a finite, sourced arrival number. The case allows a declared unlimited model, so the team could pick saturating, but then it carries the two problems in rows 4 and 5. **Intermediate levels** (seed 1, *computed* by the inline command at the end of this section): 120% gives 76.5% / 89.7% coverage at 81.7% / 82.8% accepted; 150% gives 78.2% / 91.8% at 64.0% / 65.4%. Over-offering needs its own justification ("we sell 20% more than the normal"), so 100% stays the default.

### Exactly how the team's scheduler should generate offers

1. **Rate table** (server-hours offered per day, by month; *computed*, `analysis/r4_headline.py` section 2, = `r2_deadline_sim.offer_rates("shaped100", n)`):

   | Month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | Year |
   |---|---|---|---|---|---|---|---|---|---|---|---|---|---|
   | N=6 | 143.9 | 141.8 | 133.2 | 99.4 | 44.6 | 15.0 | 15.0 | 15.0 | 30.6 | 66.8 | 138.0 | 142.4 | 81.8 |
   | N=8 | 185.3 | 171.5 | 155.2 | 111.0 | 44.7 | 15.0 | 15.0 | 15.0 | 30.6 | 68.0 | 163.0 | 181.7 | 95.9 |

2. **Per type:** J1 jobs per day = rate × 0.5 ÷ 0.5 h; J2 jobs per day = rate × 0.5 ÷ 4 h. At N=6: January 143.9 J1 + 17.99 J2, July 15.0 J1 + 1.88 J2, year 81.8 + 10.22. At N=8: January 185.3 + 23.17, July 15.0 + 1.88, year 95.9 + 11.99.
3. **Arrival distribution:** Poisson per hour with λ = jobs per day ÷ 24, independent for J1 and J2 (*assumption*). Within an hour with arrivals, the type admitted first is drawn 50/50.
4. **Seed:** `random.Random(1)` for the headline; seeds 2 and 3 for the spread shown in Q&A.
5. **Deadlines:** J1 24 h, J2 168 h after arrival (*assumption*, matching the two ends of Groq's batch window, round 3). Sizes 0.5 and 4 server-hours (*assumption*).
6. **Simplest build: read the offer stream from the committed file** `analysis/r4_offers_shaped100_seed1.csv` (or a copy under `data/` if the team prefers; a team decision) instead of writing a generator. That also answers the round-3 critic's question "who stores the day's offers for the live replay": the yearly driver and the live driver both read the same file. This removes build scope rather than adding it. The `first` column is drawn every hour with arrivals, even when only one type arrived, so it can be ignored then.
7. **Policy for the key figures:** cap + 8 kWh band; one permit function for executor and dry run; EDF admission dry run on archived `ifs025` with the causal flag and a 2 K guard; restart as an accounting line (0 in the case column, 15 min in the realistic column).

### Wording

- **Dashboard line under the tiles:** "Offers: heat-shaped contract, 100% of the house's normal heat capacity (Basel 2020–24), 92 jobs a day on average (144 J1 + 18 J2 a day in January, 15 + 2 in July), Poisson, seed 1. Accepted 94.7%. Missed: 0 of 31,908 accepted jobs (archived ECMWF forecast, 2 K guard; forecast error only). Unlimited demand would cover 79.6%."
- **Pitch sentence:** "We do not assume unlimited work. The house is offered a monthly contract equal to its normal heat capacity, about 90 jobs a day, and turns away the 5% it has no heat for. The number is a contract size we chose; filling it needs many customers, because SRF's whole spoken archive would keep one house busy for only two winter weeks."

Inline probe command for the intermediate levels (not a lasting script):

```
python3 -B -c "import sys; sys.dont_write_bytecode=True; sys.path.insert(0,'analysis'); import r4_headline as H
for n in (6,8):
  for dm in ('shaped120','shaped150'):
    r=H.run(n,H.HEADLINE,dm,1); print(n,dm,r['coverage'],r['acc_jobs'],r['acc_j1_summer'],r['missed_n'],r['closed_n'])"
```

Output (seed 1): N=6 120%: 76.46%, 81.7% accepted, summer J1 64.9%, 0 of 32,586 missed; 150%: 78.23%, 64.0%, 23.0%, 0 of 31,876. N=8 120%: 89.72%, 82.8%, 57.9%, 12 of 38,748; 150%: 91.80%, 65.4%, 25.8%, 13 of 38,325.

### A limitation the headline keeps: idle servers on cold days

On the coldest day (2025-01-13, seed 1) the headline run has permits for all servers all day, but working servers per hour are `666666666656365265544245` at N=6 (22 server-hours idle while holding a permit) and `688788888888855778885688` at N=8 (16). That is about 13–18 kWh more backup heat that day (*computed*, inline call of `r4_headline.run`, command below). Saturating offers have the same at N=6 (16 h) and none at N=8. A contract sized to the monthly normal runs short in a cold spell. Show the job-level count on the January screen (as the plan already says), not the permit count.

```
python3 -B -c "import sys; sys.dont_write_bytecode=True; sys.path.insert(0,'analysis'); import r4_headline as H
di=H.day_index('2025-01-13')
for n in (6,8):
  for dm in ('shaped100','saturating'):
    r=H.run(n,H.HEADLINE,dm,1); c=r['ks_cap'][di*24:di*24+24]; o=r['ks_on'][di*24:di*24+24]; print(n,dm,''.join(map(str,o)),sum(a-b for a,b in zip(c,o)))"
```

---

## (c) Script and output

Command: `python3 analysis/r4_headline.py` (seeds 1–3, multiprocessing; 36 s wall, 183 s CPU on this laptop). Output of 2026-11-21, exit 0, pasted in full:

```
r4_headline.py. Currency CHF; 1 USD = 0.8392 CHF (ECB 20 Nov 2026, sourced in round 1). Stand-in reference house, 2025.
Headline policy: cap + 8 kWh band; EDF admission dry run with the same permit function; archived ECMWF ifs025 forecast,
causal heating-day flag, 2 K guard band; restart NOT in execution (accounting line, 15 min ASSUMPTION).
Jobs: J1 0.5 server-h / 24 h, J2 4 server-h / 168 h, 50/50 by work, Poisson (ASSUMPTIONS, round 1-3). No partner site,
no failures or overruns. Forecast and 'actual' weather come from the same model family (errors understated).

== 0. Regression: this loop without a pin = r3_policy_check.run() ==
  N=6 shaped100  seed 1: r3 accepted 31937, missed 0, starts 896, coverage 73.198% | r4 31937, 0, 896, 73.198% -> OK
  N=6 saturating seed 1: r3 accepted 32539, missed 0, starts 460, coverage 79.099% | r4 32539, 0, 460, 79.099% -> OK
  N=6 unlimited reference (baseline_sweep follow): coverage 79.58%, 31067 server-h
  N=8 shaped100  seed 1: r3 accepted 36784, missed 0, starts 1527, coverage 85.729% | r4 36784, 0, 1527, 85.729% -> OK
  N=8 saturating seed 1: r3 accepted 38563, missed 7, starts 921, coverage 92.750% | r4 38563, 7, 921, 92.750% -> OK
  N=8 unlimited reference (baseline_sweep follow): coverage 92.94%, 36281 server-h
  all regression checks: OK

== 1. Customer volumes in 1 kW server-hours (scaling rules of round 3) ==
  J1 transcription: 667 audio-h per server-h (laptop rule, E = 1.5 Wh/audio-h, COMPUTED r3); 149 at E = 6.7 (2 x RTX 4090, UNVERIFIED)
  J2 summarisation: 438,026 MLPerf samples per server-h (B200 slice, COMPUTED from SOURCED); 34,537 (2 x Xeon, 1 kW ASSUMPTION); 10 samples per document ASSUMPTION
  A Swiss public broadcaster archive (SRF), spoken audio digitised: 1,250,000 audio-hours (stock, one-off) [SOURCED]
      = 1,875 to 8,389 server-h = 6.04% to 27.0% of ONE N=6 house-year (31,067 permit server-h)   src https://www.srf.ch/news/automatische-spracherkennung-computer-schryb-aues-mit-won-ig-hie-saege (22 Jan 2023)
    same archive, audio material in the basement: 1,000,000 audio-hours (stock; 'ueber eine Million') [SOURCED]
      = 1,500 to 6,711 server-h = 4.83% to 21.6% of ONE N=6 house-year (31,067 permit server-h)   src https://www.srf.ch/radio-srf-musikwelle/audio-und-videomaterial-der-schatz-des-srf-im-archiv-roboter (27 Mar 2024)
  B Swiss hospitals, inpatient stays per year (discharge documents): 1,500,000 stays per year (2023) [SOURCED]
      = 34 to 434 server-h = 0.11% to 1.4% of ONE N=6 house-year (31,067 permit server-h)   src https://www.admin.ch/gov/de/start/dokumentation/medienmitteilungen.msg-id-103286.html (26 Nov 2024)
  C Swiss accident insurer (Suva), doctor and hospital invoices checked: 2,700,000 invoices per year (2024) [SOURCED]
      = 62 to 782 server-h = 0.20% to 2.5% of ONE N=6 house-year (31,067 permit server-h)   src https://www.suva.ch/de-ch/ueber-uns/magazin-und-medien/medien/heilkosten (24 Sep 2025)
  Derivation (ASSUMPTION: archive A transcribed in 1 year by 1 house): 1,250,000 audio-h / 333 audio-h per J1 / 365 = 10.3 J1 jobs per day = 5.1 server-h/day per house
     against the shaped100 contract at N=6: 81.8 server-h/day yearly mean -> the archive fills 6.3% of it; houses one such archive keeps busy for a year: 0.063
     against the shaped100 contract at N=8: 95.9 server-h/day yearly mean -> the archive fills 5.4% of it; houses one such archive keeps busy for a year: 0.054

== 2. Headline offer generator: shaped100, jobs offered per day by month (expected values) ==
  rate_m = 1.00 x mean heat-permit server-h/day of month m under plain follow, 2020-24 Open-Meteo archive (cannot see 2025)
  lambda_J1 per hour = rate_m x 0.5 / 0.5 / 24;  lambda_J2 per hour = rate_m x 0.5 / 4 / 24;  Poisson, random.Random(seed)
  N=6  month          1      2      3      4      5      6      7      8      9     10     11     12   year
        server-h/d  143.9  141.8  133.2   99.4   44.6   15.0   15.0   15.0   30.6   66.8  138.0  142.4   81.8
        J1 jobs/d   143.9  141.8  133.2   99.4   44.6   15.0   15.0   15.0   30.6   66.8  138.0  142.4   81.8
        J2 jobs/d   17.99  17.72  16.65  12.42   5.58   1.88   1.88   1.88   3.82   8.35  17.25  17.81  10.22
        J1 audio-h/d at 333 per job: Jan 47,924, Jul 4,995, year mean 27,230
  N=8  month          1      2      3      4      5      6      7      8      9     10     11     12   year
        server-h/d  185.3  171.5  155.2  111.0   44.7   15.0   15.0   15.0   30.6   68.0  163.0  181.7   95.9
        J1 jobs/d   185.3  171.5  155.2  111.0   44.7   15.0   15.0   15.0   30.6   68.0  163.0  181.7   95.9
        J2 jobs/d   23.17  21.44  19.40  13.88   5.59   1.88   1.88   1.88   3.82   8.50  20.38  22.72  11.99
        J1 audio-h/d at 333 per job: Jan 61,719, Jul 4,995, year mean 31,938

(42 simulated years, seeds [1, 2, 3])

== 3. HEADLINE key figures: shaped100 offers, headline policy, archived forecast + 2 K guard (seed mean [min-max]) ==
  N=6
    coverage 73.67% [73.20-73.96]   dumped 0 kWh   utilisation 54.72%   starts/yr 854
    offered jobs 33,664/yr (92.2/day); accepted 94.7% of jobs, 96.5% of work; summer (Jun-Aug) J1 accepted 89.6% of offers
    missed deadlines: 0 of 31908, 0 of 31694, 0 of 31996 accepted jobs closed in 2025 (seeds [1, 2, 3]) = 0.0000% [0.0000-0.0000]; not accepted (sent elsewhere): 5.3% of offered jobs
    server-hours sold 28,761 (J1 14,101, J2 14,660) = 92.6% of the unlimited-demand permit hours
    electricity 9,563 CHF; heat value used 3,060 CHF; electricity - heat 6,503 CHF
    break-even per sold server-hour: 0.2261 CHF (case formula; 0.3325 if the homeowner keeps the heat); with the 15-min restart accounting line 0.2278
    list value of the sold work (J1 laptop efficiency, J2 B200 slice: NOT one machine), CHF/yr: low 122,262 / central 268,154 / high 886,171
    share of list value needed to cover electricity - heat: low 5.3% / central 2.4% / high 0.7%
    SCENARIO computing income at operator share 20% (ASSUMPTION), sold share = computed above: low 24,452 / central 53,631 / high 177,234 CHF/yr; if every sold hour were J1 (one machine, laptop efficiency): 38,618 / 64,364 / 144,819
  N=8
    coverage 86.14% [85.73-86.46]   dumped 0 kWh   utilisation 47.98%   starts/yr 1497
    offered jobs 39,433/yr (108.0/day); accepted 93.8% of jobs, 95.8% of work; summer (Jun-Aug) J1 accepted 90.3% of offers
    missed deadlines: 0 of 36771, 0 of 36989, 0 of 37201 accepted jobs closed in 2025 (seeds [1, 2, 3]) = 0.0000% [0.0000-0.0000]; not accepted (sent elsewhere): 6.2% of offered jobs
    server-hours sold 33,626 (J1 16,333, J2 17,293) = 92.7% of the unlimited-demand permit hours
    electricity 11,181 CHF; heat value used 3,578 CHF; electricity - heat 7,603 CHF
    break-even per sold server-hour: 0.2261 CHF (case formula; 0.3325 if the homeowner keeps the heat); with the 15-min restart accounting line 0.2286
    list value of the sold work (J1 laptop efficiency, J2 B200 slice: NOT one machine), CHF/yr: low 142,200 / central 312,946 / high 1,037,747
    share of list value needed to cover electricity - heat: low 5.3% / central 2.4% / high 0.7%
    SCENARIO computing income at operator share 20% (ASSUMPTION), sold share = computed above: low 28,440 / central 62,589 / high 207,549 CHF/yr; if every sold hour were J1 (one machine, laptop efficiency): 45,150 / 75,250 / 169,313

== 4. Sensitivity and comparison rows (seed means) ==
  row                                          N   cover  dump   util acc%job sumJ1% missed x of y (seed 1)  missed%  sold h      BE  BE+rst  income c  need c starts
  HEADLINE shaped100, archived + 2 K           6  73.67%     0  54.7%   94.7%  89.6%            0 of 31,908   0.0000  28,761  0.2261  0.2278    53,631    2.4%    854
  check: shaped100, perfect forecast           6  74.01%     0  55.0%   95.4%  89.9%            0 of 32,174   0.0000  28,892  0.2261  0.2277    53,902    2.4%    820
  sensitivity: half rate (shaped50)            6  37.99%     0  28.2%   99.7% 100.0%            0 of 16,672   0.0000  14,831  0.2261  0.2382    27,783    2.4%   3021
  sensitivity: double rate (shaped200)         6  78.96%     0  58.6%   44.1%   6.4%           33 of 28,928   0.0841  30,824  0.2261  0.2268    55,468    2.5%    398
  reference: saturating (N x 24 h/day)         6  79.22%     0  58.8%   54.9%   0.0%            0 of 32,487   0.0000  30,925  0.2261  0.2269    56,913    2.5%    435
  named customer only (5.1 srv-h/d flat)       6   4.78%     0   3.6%  100.0% 100.0%             0 of 2,106   0.0000   1,867  0.2261  0.2810     3,501    2.4%   1459
  shaped100 + real job pinned slot 1, all year 6  74.86%     0  55.6%   73.0%   0.0%            0 of 24,376   0.0000  29,223  0.2261  0.2273    57,434    2.3%    619
  shaped100 + real job pinned, demo day only   6  73.67%     0  54.7%   94.7%  88.8%            0 of 31,892   0.0000  28,760  0.2261  0.2278    53,632    2.4%    846

  HEADLINE shaped100, archived + 2 K           8  86.14%     0  48.0%   93.8%  90.3%            0 of 36,771   0.0000  33,626  0.2261  0.2286    62,589    2.4%   1497
  check: shaped100, perfect forecast           8  86.55%     0  48.2%   94.5%  90.3%            0 of 37,023   0.0000  33,788  0.2261  0.2285    62,926    2.4%   1449
  sensitivity: half rate (shaped50)            8  44.59%     0  24.8%   99.7% 100.0%            0 of 19,686   0.0000  17,408  0.2261  0.2376    32,620    2.4%   3367
  sensitivity: double rate (shaped200)         8  92.25%     0  51.4%   46.3%   7.9%           11 of 35,991   0.0514  36,011  0.2261  0.2276    65,611    2.5%    929
  reference: saturating (N x 24 h/day)         8  92.84%     0  51.7%   49.2%   0.0%            7 of 38,357   0.0251  36,242  0.2261  0.2275    66,887    2.5%    906
  named customer only (5.1 srv-h/d flat)       8   4.78%     0   2.7%  100.0% 100.0%             0 of 2,106   0.0000   1,867  0.2261  0.2810     3,501    2.4%   1459
  shaped100 + real job pinned slot 1, all year 8  88.51%     0  49.3%   78.0%   0.0%           16 of 30,488   0.0524  34,554  0.2261  0.2279    67,504    2.3%   1076
  shaped100 + real job pinned, demo day only   8  86.19%     0  48.0%   93.8%  90.3%            0 of 36,771   0.0000  33,646  0.2261  0.2286    62,634    2.4%   1490

  income c = scenario income, central prices, operator share 20% (ASSUMPTION); need c = share of list value needed (central)

== 5. The pinned real job (R6) in the yearly balance ==
  N=6: all-year pin on slot 1: pinned hours 7,532/yr = 25.8% of sold hours; coverage 73.67% -> 74.86%; accepted jobs 94.7% -> 73.0%; summer J1 accepted 89.6% -> 0.0%; missed 0.0000% -> 0.0000%
  N=6: demo-day pin on 2025-07-15 slot 1 (chosen from the no-pin seed-1 run, pattern there ##................######, pause 02:00 resume 18:00)
        with the pin, seed 1: pinned job ran 8 h that day; its pattern ##................######; events PAUSE 02:00, RESUME 18:00
        yearly figures with vs without the demo-day pin (seed means): coverage 73.675% -> 73.673%, sold h 28,761 -> 28,760, accepted 94.73% -> 94.69%, missed 0.0000% -> 0.0000%
  N=6: demo candidates in the no-pin run (seed 1), slot 1, month 07: 07-06 P04 R20, 07-15 P02 R18, 07-22 P04 R20, 07-31 P02 R18
  N=8: all-year pin on slot 1: pinned hours 7,531/yr = 21.8% of sold hours; coverage 86.14% -> 88.51%; accepted jobs 93.8% -> 78.0%; summer J1 accepted 90.3% -> 0.0%; missed 0.0000% -> 0.0524%
  N=8: demo-day pin on 2025-01-25 slot 7 (chosen from the no-pin seed-1 run, pattern there ##############.....#####, pause 14:00 resume 19:00)
        with the pin, seed 1: pinned job ran 19 h that day; its pattern ##############.....#####; events PAUSE 14:00, RESUME 19:00
        yearly figures with vs without the demo-day pin (seed means): coverage 86.136% -> 86.187%, sold h 33,626 -> 33,646, accepted 93.84% -> 93.84%, missed 0.0000% -> 0.0000%
  N=8: demo candidates in the no-pin run (seed 1), slot 7, month 01: 01-09 P09 R17, 01-25 P14 R19, 01-26 P12 R18, 01-27 P02 R03, 01-28 P11 R12, 01-29 P10 R11
```

### Reading the output

- **Section 0:** without a pin, the r4 loop gives the same accepted jobs, missed jobs, starts, coverage and sold hours as `r3_policy_check.run()` for both N and both offer scenarios. The figures therefore inherit every round-3 check.
- **Perfect-forecast check:** 0 missed at both N (must be exactly 0; it is). The archived forecast costs 0.3 / 0.4 coverage points and 0.7 points of accepted jobs against perfect foresight.
- **Half rate (`shaped50`):** coverage halves (38.0% / 44.6%) and starts rise to about 3,000 a year (servers stop for lack of work, not heat). The restart line lifts break-even to 0.238. **Double rate (`shaped200`):** coverage 79.0% / 92.3%, close to unlimited, but only 44–46% of offers are accepted, summer J1 6–8%, and misses appear: 0.084% / 0.051%.
- **Break-even** is 0.2261 CHF per sold server-hour in every row: nothing is dumped and the server is off when unsold, so it is structural (round-3 critic F1). Only the restart line moves it (0.2268 to 0.2382, worst at half rate).
- **Income** (`r3_income.py` prices and labels, w = 20% *assumption*): central 53.6k / 62.6k CHF a year. That is higher than round 3's 39k / 46k because round 3 assumed 67% sold, while here the sold share comes out of the run at 92.6% / 92.7% of the permit hours. That share is set by the contract level we chose; it is **not evidence of demand**. The list value still mixes J1 at laptop efficiency with J2 at B200-slice efficiency (not one machine). If every sold hour were J1 on one machine, the central scenario is 64.4k / 75.3k. The share needed (2.4% central, before hardware) does not move with the scenario.
- **Break-even at the chosen sold share:** round 3's "0.3375 at 67% sold" assumes unsold permit hours still run. Under the headline (server off when unsold) break-even stays 0.2261 and coverage falls instead, to 73.7% / 86.1%. Print the one that matches the run.

---

## (d) Is the pinned real job counted in the yearly balance consistently?

**Model used** (`r4_headline.run(..., pin=...)`): the real job is bound to slot s and runs in an hour iff permits k ≥ s. While it runs it takes one of the k permitted servers and the EDF pool gets k − 1. The admission dry run subtracts it from the forecast permits in the same way (same permit function). It has no deadline (a backlog item), so its hours count as **sold J1 work** and it is **excluded from the missed-deadline denominator**.

### Variant 1, as the plan words R6 ("always-ready queue job on slot s"): refuted

*Computed*, section 5, seed means, slot 1:

| | N = 6 | N = 8 |
|---|---|---|
| Pinned hours per year | 7,532 = **25.8% of sold hours** | 7,531 = 21.8% |
| Coverage | 73.67% → 74.86% | 86.14% → 88.51% |
| Accepted jobs | 94.7% → **73.0%** | 93.8% → 78.0% |
| Summer J1 accepted | 89.6% → **0.0%** | 90.3% → 0.0% |
| Missed | 0 → 0 | 0 → 0.052% |

Its hours are counted, but it is an **unlimited backlog on slot 1**: a quarter of the sold work comes from a job with no arrival rate, which must-have 1 would require us to declare. In summer it takes the single permitted server, so every offered J1 is refused again. This is the 0% the pin was meant to remove. Not consistent with a finite-demand headline.

### Variant 2, pinned on the demo day only: confirmed

The demo job is one extra backlog job that exists only on the demo date. It is pinned to the demo slot, counted as sold J1 work, and known to admission from the start of the year (it is a scheduled event).

| | N = 6 | N = 8 |
|---|---|---|
| Demo date and slot (from the no-pin run, seed 1) | 2025-07-15, slot 1 | 2025-01-25, slot 7 |
| Pattern without pin | `##................######` P 02:00, R 18:00 | `##############.....#####` P 14:00, R 19:00 |
| Pattern of the pinned job, with pin | **identical**, 8 h run | **identical**, 19 h run |
| Yearly effect (seed means) | coverage 73.675 → 73.673%, sold h 28,761 → 28,760, missed 0 → 0 | coverage 86.136 → 86.187%, sold h 33,626 → 33,646, missed 0 → 0 |

Other July candidates at N=6, seed 1: 07-06 (P04 R20), 07-22 (P04 R20), 07-31 (P02 R18). Hour labels are UTC+1 all year, so July 02:00 / 18:00 is 03:00 / 19:00 CEST (`data/README.md`). The N=6 July date differs from round 3 (07-22) because restart left execution, which again shows that **the date must come from the final run**. N=8 2025-01-25 is unchanged.

**How to count it, in one line for the README:** "The live job is backlog job #D (one archive batch, no deadline) that exists only on the demo date. In the yearly run it is pinned to slot s on that date and its run hours (8 h at N=6, 19 h at N=8) are counted as sold J1 server-hours. It is excluded from the missed-deadline count because it has no deadline. The live driver replays that day from the 00:00 snapshot, with the same offer file, and the trace test compares the 24 lines."

Build cost: the pin is one condition in the permit split (`pool = k − [pin active and k ≥ s]`), applied in the executor and in the dry run. That is the same few lines R6 already budgets, plus a date parameter. Procedure: (1) run the year without the pin; (2) the demo-day finder picks date and slot; (3) re-run with the pin on that date; (4) check that the pattern still shows pause then resume (it did for both N here).

---

## Recommendation: N = 6 or 8 under the headline

**N = 8.** One line: *under `shaped100` it covers 86.1% against 73.7% (+12.5 points) with 0 kWh dumped, 0 missed and the same 0.2261 CHF break-even, and its January demo day pauses on the heat signal, which N=6 never does in January.*

Against it, to say in Q&A: utilisation 48.0% vs 54.7%; 1,497 vs 854 starts a year; two more servers whose 7th and 8th run 2,933 h and 2,281 h a year (round 1); a hardware payback threshold of 0.75–1.00 CHF net per run hour vs 0.54–0.64 (round 2, `analysis/r2_fleet_economics.py`). At sourced host rates neither N pays back hardware, so hardware does not separate them.

---

## Limitations

- Assessment script, not the team's scheduler. One weather year (2025), stand-in CSV, 3 arrival seeds. Job sizes, deadlines, mix and Poisson arrivals are assumptions from rounds 1–3.
- Forecast error is the only failure modelled; the archived forecast and the "actual" weather come from the same model family (errors understated). No partner site, no server failures, no runtime overruns. Work on a job that later misses would still count as sold (no case arose here).
- `shaped100` is sized on the 2020–24 normal, but the house still sees one realisation (2025). In a colder or milder year the accepted share moves.
- Customer volumes are order-of-magnitude anchors read through WebFetch summaries with direct quotes. They are stocks or national totals, not purchase volumes. "10 samples per document" and "one archive per house per year" are assumptions.
- Income keeps every round-3 caveat: the J1/J2 machine mix, US commodity batch prices, unsourced operator share, no Swiss or data-resident price level.

## Proposed changes to the plan (`docs/overnight.md`)

1. **Headline offer scenario = `shaped100`** (heat-shaped contract at 100% of the 2020–24 normal, Poisson, seed 1, J1 24 h / J2 168 h). Replace the "decide saturating or heat-shaped at 09:00" item with this default. Keep saturating and unlimited as labelled comparison lines.
2. **Replace the 5 opening numbers** with the `shaped100` values: coverage 73.7% / 86.1%, dumped 0, utilisation 54.7% / 48.0%, missed "0 of 31,908 / 0 of 36,771 accepted jobs" with the double-rate stress line (33 of 28,928 / 11 of 35,991), break-even 0.2261 (0.2278 / 0.2286 with restart). Unlimited demand (79.6% / 92.9%) becomes the upper line.
3. **Committed offer file** `analysis/r4_offers_shaped100_seed1.csv` (or a copy under `data/`), read by both drivers. This replaces a generator and answers who stores the live-replay offers.
4. **R6 reworded:** "the real job is a backlog job pinned to slot s **on the demo date only**, counted as sold J1 hours, excluded from the missed denominator". Drop "always ready all year": that would make 22–26% of sold hours an undeclared unlimited backlog and bring back 0% summer J1.
5. **Jobs-per-day sentence for must-have 1:** "a contract size we choose (100% of normal heat capacity), not one customer's demand; named Swiss customers are far smaller than one house (SRF's spoken archive = 6% of one N=6 house-year at laptop efficiency; a 'named customer only' run covers 4.8%)". Add it to open risk 11 and the "does not pay off when" block: "when paid demand per house falls below the contract: at half the rate coverage halves to 38% / 45%".
6. **Servers: N = 8 as the working default** under the headline scenario (reason above); the 09:00 decision stays with the team.
7. **Income line:** sold share now comes from the run (92.6% / 92.7%), not the 67% assumption. Lead with "2.4% of list value needed", then the scenario 53.6k / 62.6k CHF a year (w = 20%, J1 laptop + J2 B200 slice, not one machine). Remove the "0.3375 at 67% sold" line from the headline: it belongs to the unsold-hours-still-run convention, which the headline does not use.
8. **Demo dates:** N=6 July shaped100 seed 1 is now 2025-07-15 (P 02:00, R 18:00 data time); N=8 2025-01-25 slot 7 holds. Dates are read from the final run with the pin applied.
9. **Questions for DigitalHeat, added:** "Do you have a buyer or aggregator for deferrable batch work, and at what monthly volume per site?"

## Commands

```
python3 analysis/r4_headline.py                                                     # all sections, 36 s
python3 analysis/r4_headline.py --write-offers analysis/r4_offers_shaped100_seed1.csv
# web: WebSearch (SRF archive hours, Swiss sound archive, Euler core-hours, Federal Supreme Court, BFS hospital stays,
#      insurer invoices); WebFetch of the four source URLs in section (a). The SRG factsheet PDF returned 403.
```
