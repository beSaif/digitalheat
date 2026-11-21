# Round 3 critique: creativity (20%) and one-minute usability (10%)

Critic's file for `docs/research/r3-creativity-usability.md` and `analysis/r3_creativity_usability.py`. Role: a sceptical founder. Nothing here is built. Paid web calls: 0 of 1.

Status labels as in `docs/overnight.md`. Currency: CHF. No conversion used. Vendor figures stay in EUR, GBP or USD.

## What I re-ran

- `python3 analysis/r3_creativity_usability.py`: output identical to the research file. The arithmetic is correct. Totals match `analysis/baseline_sweep.py`: N=6 gives 31,067 server-h, 24,854 kWh used and 0 dumped; N=8 gives 36,281, 29,025 and 0.
- Additional one-off numbers (*computed*, inline command run from the repo root):
  ```
  python3 -c "import sys; sys.path.insert(0,'analysis'); from baseline_sweep import load, simulate; rows=load(); [print(n, simulate(rows,n)['coverage'], simulate(rows,n)['util']) for n in (1,2,3)]"
  ```
  N=1: coverage 19.5%, utilisation 87.1%. N=2: 32.7%, 73.0%. N=3: 45.5%, 67.6%.
  Hot water: 4,380 kWh/yr = 15.77 GJ = **3.2%** of 500 GJ (31.7 houses). Total demand: 112.4 GJ = 17.8% of the vendor's smallest model (~630 GJ/yr).
  The median heating hour (5.85 kW) is 58.5% of the 10 kW design load. A heat credit of 0.1064 CHF is 21.3 / 10.6 / 5.3% of illustrative sale prices of 0.5 / 1 / 2 CHF per server-hour (the prices are *assumptions*).
  Tank-loss effect on the receipt: 720 / 24,854 = 2.9% (N=6) and 862 / 29,025 = 3.0% (N=8), loss figures from `docs/overnight.md` (`analysis/r2_realism.py`).

## Sources re-opened

| Claim | What I found | URL actually read |
|---|---|---|
| C1, C2 (2011 data-furnace paper) | Confirmed with `pdftotext`: "40 to 400 CPUs ... primary heat source for a single-family home"; Type A "Low-cost seasonal", "delay-tolerant batch jobs ... opportunistically"; Type C "pumping excess heat directly outside"; overhead "less than $90 per server per year" against "approximately $400"; Table 2 savings 298.1 / 324.4 / 324.3 / 280.4 / 300.9 USD (against 401.6). These are 2011 US figures: residential electricity at 0.10 USD/kWh, server cost excluded | https://classpages.cselabs.umn.edu/Fall-2021/csci8980-ec/papers/EdgeArch/furnace.pdf |
| C3 (2018 computing water heaters) | Confirmed: "if and only if temperature of water is below the target", "stops computing", "non preemptive". The word "deadline" does not appear. "About 60% CPU usage, 10% thermal resistance" is the steady-state result (2 weeks, French household water use, 10 CPUs × 100 W per heater). The 10-heater count is stated for the starvation runs; for the steady state it is implied ("CWH 9") | https://perso.ens-lyon.fr/laurent.lefevre/pdf/CCNC2018_Rais_Caron_Lefevre.pdf |
| C4 (2021 journal paper) | The MDPI URL returns 403 to me. The abstract is confirmed on Europe PMC. **The full text (PMC8073740) has per-task SLA deadlines as a hard constraint**, `t_start + t_execution ≤ t_deadline` (eq. 9), says "delay-tolerant workload" and keeps "task migration ... as low as possible". It does not mention summer, season, weather or priority. One co-author is from the French vendor | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.3390/s21082879&resultType=core&format=json ; https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8073740/fullTextXML |
| C5 | Direct URL returns 403. Confirmed on a Dec 2023 archive snapshot: 10 Nov 2022; "We're stopping doing heaters and going more for boilers"; "social housing ... 24x7 for hot showers"; "you cannot put 500kW of hot water 24x7"; 65 °C. **Also in the article:** "Data centers require 24x7 compute, while people don't require 24x7 heating", and a Dutch e-radiator rival went bankrupt in 2019 over these issues | https://web.archive.org/web/20231201233210/https://www.datacenterdynamics.com/en/analysis/making-the-most-of-your-waste-heat/ |
| C6 | Confirmed: "up to 12 servers", "pilot data center in Finland with 100kW of compute", "We're going to run all year round" | techcrunch URL as cited |
| C7 | Confirmed: "the reuse heat, in W.h", per task and per pool, "Carbon facts prototype" | SDK URL as cited |
| C9 | 4.8 and 2.5 kWh/day confirmed. **"One unit per home" is not on this page.** The Register says "about a hundred units in individual homes" | cnx URL as cited |
| C10 | Confirmed verbatim | theregister URL as cited |
| C11 | Confirmed, with two corrections. (1) The minimum is **"year-round hot water demand (minimum 500 GJ/year)"**, not total heat demand. (2) The page also says **"Recommended sizing is 5-20% of design thermal load"**, which the investigator missed. The 25% at the 5 kW site is labelled three ways: "natural gas use", "Hot Water Coverage" and "a quarter of the facility's heating needs". The page also gives "Heat Output 95%+ of electrical input" | https://leaf.cloud/leafsites/ (raw HTML, curl) |
| C13 | Confirmed but forward-looking: "will reduce ... by 62%", "could save around £20,000". Published 14 Mar 2023. The DCD item (below) calls the 62% "expected heat transfer" | techradar URL as cited |
| C14 | **Now readable** on a Jan 2024 archive snapshot: "installed a 28kW system", "Deep Green pays for the electricity it uses and gives the heat free"; 139,284 kWh/yr "expected", 62% of 222,000 kWh | https://web.archive.org/web/20240115142516/https://www.datacenterdynamics.com/en/news/uk-data-center-startup-offers-to-heat-britains-swimming-pools-with-waste-heat/ |
| C15 | Confirmed: vented in summer; €12,000; 15 years; operator pays internet and electricity; 17 Nov 2014 | itpro URL as cited |
| C16 | Confirmed: "costs 50% less", "processed in less than 24 hours", 8 Oct 2024 | claude.com URL as cited |
| C8 | Archive returns 404. Still snippet-only | — |

## Prior art the investigator missed (it hits the one "new" part)

- **Deadline-constrained, heat-driven scheduling on home servers already exists.** The 2021 paper's full text has hard per-task deadlines (above).
- **Admission against forecast capacity, with deadlines, is established in carbon- and solar-aware scheduling:**
  - GreenSlot (SC 2011): "predicts the amount of solar energy that will be available in the near future" and "schedules the workload to maximize the green energy consumption while meeting the jobs' deadlines". Read on https://scholarship.libraries.rutgers.edu/esploro/outputs/technicalDocumentation/GreenSlot-Scheduling-Energy-Consumption-in-Green/991031550040804646 (abstract via a summarising fetch).
  - Google's carbon-intelligent system (2021): day-ahead "Virtual Capacity Curves ... impose hourly limits on resources available to temporally flexible workloads", with "all such workloads to complete within a day", and "these limits directly impact the real-time admission of flexible workloads". Read with `pdftotext` on https://arxiv.org/pdf/2106.11750.
- A founder will say: "your heat permit is a VCC with heat in place of carbon". What remains not found (*unverified* absence):
  - the weather forecast of one house's heat demand plus its tank used as the capacity curve;
  - an explicit refusal at intake;
  - a published missed-deadline share beside coverage and dumped heat for one reproducible house-year.

## Main problems with the result

1. **C12 compares unlike quantities.** The 500 GJ minimum is on year-round hot-water demand. The house's comparable figure is 15.8 GJ, **3.2%**, not 22.5%. The point gets stronger, but the number is wrong.
2. **Backup angle (median heating hour) goes against the one vendor sizing rule we found.**
   - The vendor recommends 5-20% of design thermal load. For a 10 kW house that is 0.6 to 2.5 servers at 0.8 kW heat each. Utilisation would be 87% at N=1 and 73% at N=2.
   - The median heating hour is 58.5% of design load, 7.3 servers. It is not a fresh idea, and as a "rule" it lands between 6 and 8, so it muddies the N choice.
   - Keep the load-duration chart, which is useful for "why 6". Drop the median rule as a creativity claim, and add the vendor's 5-20% rule to Q&A.
3. **The 32% vs 50% comparison is apples to oranges.**
   - 32% is the heat credit as a share of the *electricity cost* of a 1 kW server-hour. 50% is a discount off the *list price* of an LLM token API.
   - In absolute terms heat funds at most 0.1064 CHF per server-hour. Against any plausible sale price that is 5-21% (prices are *assumptions*).
   - The conclusion (do not build the tariff) holds, and more strongly.
4. **The receipt is not new, and it is a case constant.**
   - Per-task reused W.h exists (C7). "0.8 × hours" is exact only with a lossless tank and zero dumping. With the plan's tank loss it overstates by about 3%.
   - The live laptop job's receipt is modelled, not measured.
5. **Homeowner screen lacks the one number a homeowner reads in a minute: CHF.**
   - The case says the solution serves "homeowners ... who want lower heating costs". Section 5 of the script already prints it: the heat is worth 3,306 CHF/yr at N=6 (3,860 at N=8) at heat-pump cost (*computed*).
   - The screen must say who receives it, which is still open.
   - Two N values per tile, two break-evens, three charts and a switch are too much for one minute. Show one N on the tiles, with N=8 in a single line.
6. **Missed deadlines and refusals.** The low miss rate comes partly from refusing work: 55.9% of jobs are accepted under saturating offers (`docs/overnight.md`). A tile with the miss rate but no accepted share flatters the scheduler. The spec puts a range on tile 5. The plan says the figure must come from the team's own scheduler, so the tile must show the live value plus the accepted share.
7. **Pitch order.** The case says "Open with the key figures ... Then a live demo". A 25 s idea slot between them is a small deviation. Safer: say the idea in one sentence as the January scene starts. The July line "jobs beyond that are refused at intake" is only true if admission is in the core by the freeze (open risk 4).

## Verdict summary

See the structured return. In short:

- **Survive:** C1, C3, C5, C6, C7, C10, C15, C18, C21 (with conditions), C23, C25, C26, C28.
- **Caveats:** C2, C4, C9, C11, C13, C14 (upgraded to sourced via archive), C16, C19, C22, C24, C27, C29, C30.
- **Rejected as worded:** C12 (22.5% should be 3.2%).
- **Unverified:** C8, C17 (narrowed further), C31.
