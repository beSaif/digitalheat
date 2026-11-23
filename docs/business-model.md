# Business model: what DigitalHeat sells, to whom, at what price

This page answers the team to-do list from the case owner's feedback (21 Nov 2026), section by section. The numbers come from three reproducible scripts. The reference-house key figures (must-have 3) are unchanged by everything here.

| Script | Output | What it computes |
|---|---|---|
| `python3 -m scheduler.balance --scenario services --monthly` | terminal | the services fleet with the new job types, month by month |
| `python3 scripts/site_studies.py` | [`outputs/site_studies.md`](../outputs/site_studies.md), `plots/daily_profiles.png`, `plots/seasonal_capacity.png` | daily curves, household size, summer options, seasons, outages |
| `python3 scripts/business_case.py` | [`outputs/business_case.md`](../outputs/business_case.md), `plots/payback_vs_price.png` | prices, homeowner offer, billing, capex/opex, payback |

The plotting needs matplotlib (`pip install -r requirements.txt`, or `uv run --no-project --with matplotlib python scripts/...`). Prices shared with the balance and the dashboard (exchange rate, AWS spot and on-demand for our reference server, Titan and Cohere service prices, hardware per server) come from [`data/prices_2026.json`](../data/prices_2026.json) through `scheduler/pricing.py`. Every other input, with its source, is in [`data/business_assumptions.json`](../data/business_assumptions.json). The research behind them is in [`research_notes/prices_and_costs.md`](../research_notes/prices_and_costs.md) and [`research_notes/customers.md`](../research_notes/customers.md); every number there has a URL. Anything marked *our assumption* is not sourced.

---

## 1. What customers buy: the service catalogue

DigitalHeat sells **finished results through an API**, not machines. Most companies outsource their IT and cannot run a stack over SSH. They upload data and get back vectors, labels, transcripts or simulation results. The job runs on a server in a Swiss building, and the data never leaves Switzerland.

| Service | Unit sold | Why local matters | Typical buyers (Basel first) |
|---|---|---|---|
| Embeddings / private RAG indexing | 1M tokens | documents under professional secrecy or GMP | hospitals, law firms, insurers, Kanton Basel-Stadt |
| Search reranking | 1,000 queries | second step of the same private search pipeline | same |
| Image tagging | 1,000 images | collection, lab and patient images | museums and archives, pharma lab imaging |
| People counting (video) | video minute | video of people is personal data (nFADP) | BLT, BVB, SBB, venues |
| Transcription | audio minute | patient talks, hearings, bodycam audio | Universitätsspital Basel, courts, canton |
| Simulations (CFD, molecular dynamics, Monte Carlo) | compute-hour | IP-sensitive R&D | pharma and biotech, engineering offices, sciCORE |
| Video compression | output minute | bodycam and CCTV archives | transport operators, broadcasters |

Embeddings and reranking are measured on our own laptops (`docs/workloads.md`). Throughputs for the other five are order-of-magnitude assumptions, marked as such in the JSON. *Optional, not built:* let customers or hosts pick what their server computes (for example "this heater computes weather forecasts" or "sports video"). It changes nothing in the physics but may raise willingness to pay. The scheduler would need only a per-site preference weight in step 4.

## 2. Decision: no raw hardware rental

**Decision:** DigitalHeat does not rent bare servers. If it ever does, it offers that only as a niche tier for a few technical customers, who must accept interruption.

Why:
1. **Most customers can't use it.** Companies that outsource IT have no one to run Linux, drivers and model servers over SSH. A managed API is the product they can buy.
2. **Heat-driven scheduling needs control of the job.** Our scheduler pauses, checkpoints and moves jobs on the heat signal (`scheduler/core.py`). A rented machine belongs to its tenant, so we could not switch it off when the tank is full, and the heat promise to the host would break.
3. **Margin.** Per unit of work, managed-service prices are 3× (simulation) to several hundred times (image tagging) above raw compute (section 3). Bare metal competes on price with Hetzner and AWS spot; services compete on trust.
4. **Downtime.** Renting avoids downtime arguments only by giving up the heat control. With services, an outage costs a restart, or nothing on the twin tier (section 6).

## 3. Price against AWS and Google, plus a premium

The rule: **our price per unit = the AWS list price for the same managed service (Zurich or Frankfurt) × 1.25**, with Google shown alongside. The case owner said we can charge more than Amazon. The 25 % premium buys:
- **local:** data stays in a named Swiss building
- **controlled:** no US CLOUD Act exposure; contracts under Swiss law
- **safe:** fits nFADP Art. 16–17, Art. 321 StGB and GMP Annex 11
- **green:** the heat replaces a boiler or heat pump
- **Swiss**

Full table in [`outputs/business_case.md`](../outputs/business_case.md#1-service-catalogue-and-prices). Three examples:

| Service | AWS (CHF/unit) | Ours (+25 %) | Revenue per server-hour at our price |
|---|---|---|---|
| Embeddings | 0.0168 / 1M tokens (Titan V2) | 0.021 | ~62 CHF |
| Transcription | 0.0050 / min (Transcribe, now USD 0.006, not the old 0.024) | 0.0063 | ~19 CHF |
| Simulation | 9.45 / c7a.48xlarge-hour (same chips as our server) | 11.81 | ~12 CHF |

One server-hour costs 0.33 CHF of electricity. **Price is not the constraint; demand is.** The investor view therefore uses the cheapest honest comparator for interruptible batch work, AWS spot for the same server (c7a.48xlarge): 2.74 CHF/server-hour, **3.42 with our premium (base case)**. On-demand parity is 9.45.

**Reference point from the case owner:** a friend pays USD 12k/yr on AWS for simulations. That is ~1,070 server-hours, 0.15 of one of our servers. At AWS + 25 % he would pay ~12,600 CHF/yr. One reference house (11 servers, 70 % sold) needs about 26 such customers.

## 4. Redundancy tier (RAID across buildings)

A job of the **twin** tier runs as 2–4 copies on different sites. The scheduler never puts two copies in one building (input B, below), and the results are stored on every site that ran a copy.

**Price:** base × (1 + 0.5 × (copies − 1)), so 1.5× for two copies, 2× for three. AWS charges **2×** for a Multi-AZ database, so our two copies cost 25 % less than AWS's redundancy.

**What it costs us:** the extra copies run on server-hours that the heat permit allows anyway. While capacity is unsold, each extra copy-hour is +1.71 CHF of margin. Once the fleet is sold out, it displaces a full-price job (−1.71). So we sell the twin tier while there is spare capacity, and raise the markup once there isn't.

**Does it work?** We ran 100 random 12-hour site outages over 2025 on the services fleet ([outputs/site_studies.md §5](../outputs/site_studies.md)):
- one copy: 16 twin jobs restarted from zero
- two copies: 25 copies were lost, but every job finished from its other copy, with no restart and no missed deadline

## 5. Homeowner offer and billing

**Offer:** heat at a discount to what a heat pump would cost for the same heat, **not free heat**. Free heat costs DigitalHeat 4,153 CHF/yr per reference house in lost heat income. It also invites waste: windows open, 26 °C indoors.

A heat pump's running cost is 0.3325 ÷ 2.5 = **0.133 CHF per kWh of heat**. For the reference house, where server heat covers 31,222 kWh/yr (11 servers):

| Heat price | CHF/kWh | Host pays /yr | Host saves /yr | Host's share of server power | DigitalHeat refunds /yr |
|---|---|---|---|---|---|
| 30 % below heat pump | 0.093 | 2,907 | 1,246 | 22 % | 10,075 |
| 50 % below heat pump | 0.067 | 2,076 | 2,076 | 16 % | 10,906 |

**10-year pitch line** (the case owner's own math): a household paying 1,500 CHF/yr for heating saves **4,500 CHF over 10 years at 30 % off** and **7,500 CHF at 50 % off**. Research puts heat pump running costs at 1,000–1,600 CHF/yr, so 1,500 is realistic. Installing a heat pump costs CHF 45–60k, minus ~10.5k Basel-Stadt subsidy. A DigitalHeat host who already has a heating system avoids that investment for the share the servers cover.

**Conflict to raise with DigitalHeat:** "the host pays at least 50 % of the servers' power" means 0.208 CHF per kWh of heat. That is **1.56× a heat pump's running cost**, so a home would pay more than with a heat pump. At household tariffs the host's share has to follow from the heat discount (16–22 %). 50 % only works for hosts whose alternative heat is expensive, or if it is meant as a share of the *heat value*.

**Billing flow** (the meter belongs to the house):

```
grid ──► host's meter ──► house + server rack (sub-meter S, kWh)
                                   │ heat meter Q (kWh into the tank)
monthly:  DigitalHeat refunds  S × tariff − Q × heat price
          host's net cost  =   Q × heat price            (≤ heat pump cost × (1 − discount))
```

The refund always keeps heating cheaper than a heat pump, because the host only ever pays the agreed heat price for heat actually used. Computing is free to the host.

## 6. Customers who need heat all year, and compute

Summer is the weak point of homes. The best customers need heat at 50–60 °C or below, all year, and ideally also need private compute. Full research, with sources and named sites: [`research_notes/customers.md`](../research_notes/customers.md).

| Segment | Temperature | Year profile | Fit |
|---|---|---|---|
| Pharma/biotech HVAC and cleanroom reheat | **50–60 °C** (Cerbios, Lugano: 45 % of 5.6 GWh/a) | 24/7, all year | excellent |
| Pools, spas, saunas | pool water 28–36 °C | all year | excellent (Hallenbad Allschwil 627 MWh/a ≈ 70 servers) |
| Agriculture: herb, seed and hay drying; greenhouses | 40–55 °C; greenhouse 45 °C supply | drying is a **summer** load | excellent, the mirror image of homes |
| Museum and archive depots | dehumidification reheat 50–60 °C | 24/7; summer dehumidification | excellent (new NMB/Staatsarchiv building, Basel, 2028) |
| Hospitals, hotels, care homes | hot water 60/55 °C (legionella) | 24/7 | heating fits; hot water only as pre-heat |
| Laundries, dairies, breweries | 60–90 °C | shifts | pre-heat only; Feldschlösschen is itself a heat *source* |

**Top 5 "one customer, two needs" pilots:**
1. **Universitätsspital Basel:** 24/7 heat, and already runs local AI on patient data
2. **A mid-size Basel pharma/biotech site** (Bachem, Idorsia, Innovation Park Allschwil): 50–60 °C heat plus GMP- and IP-sensitive simulations
3. **Kanton Basel-Stadt:** keeps AI inputs in the canton, and owns pools and the 2028 archive
4. **Universität Basel / sciCORE+:** sensitive clinical data, plus 24/7 lab ventilation
5. **BLT / BVB / SBB depots:** bodycam video. The FDPIC ruling of 29 Sep 2026 makes local processing a selling point.

## 7. Simulation: business sites, daily curves, families

New site kinds in `scheduler/sites.py`. Daily shapes are the German gas-industry standard profiles (BDEW SigLinDe). The fleet is in `scheduler/balance.py` as `SERVICES`.
- **family:** 4–5 people
- **office:** office hours, lower at weekends
- **pharma:** reheat 24/7, process water Mon–Fri 06–22

**Homes vs businesses** (`plots/daily_profiles.png`):
- Homes and offices both boost at 06–08.
- Homes add an evening peak (17–21 h) while offices are in setback. Offices hold the daytime and drop at weekends.
- On equal energy, mixing homes and offices lowers the January peak-to-mean only a little (1.66 and 1.61 → 1.59). Adding a 24/7 pharma site lowers it to 1.45.
- The bigger complement is seasonal. In summer, pharma (84 % utilisation), spa (82 %) and hospital (77 %) keep their servers busy, while homes (the reference house: 14 %) and offices (31 %) don't.

**Household size:** hot water is a home's only summer heat sink, so size for families. With the same building and 4 servers (the family-home study keeps 4 so only the number of people changes):

| People | Summer heat (kWh, Apr–Sep) | Summer utilisation |
|---|---|---|
| 1 | 3,680 | 23.5 % |
| 5 | 5,876 | 36.0 % |

**Summer fallback, dry cooler:** an outdoor radiator dumps 60 °C water heat to the air, which works because it is never 60 °C outside. We assume 4 kW per site. That costs ~CHF 550/kW installed and 0.02 kW of fan power per kW rejected (Kelvion datasheet). With `--cool-fill`, spare servers keep computing with their heat sent outside:

| Services fleet | Utilisation | Summer utilisation | Heat dumped | Break-even (CHF/server-h) | Payback |
|---|---|---|---|---|---|
| without dry cooler | 76.4 % | 60 % | 0 | 0.226 | 2.8 yr |
| with dry cooler, fill | 93.1 % | 87 % | 74 MWh | 0.246 | 2.2 yr |

It pays wherever the price per server-hour is above about 0.34 CHF (electricity + fan, no heat credit).

## 8. Scheduler: two input signals, seasons, partial power

All new behaviour is in `scheduler/core.py`. It is off by default, so the reference figures stay identical. It is covered by `tests/test_scheduler.py` (13 tests).

- **Input 1, heat:** heat demand from the forecast, tank state, and the **supply temperature the site asks for** (`supply_c`). No heat pump and no booster: a site needing water hotter than the server loop's 60 °C outlet gets no server heat (tested).
- **Input 2, redundancy:** where each job's copies and data are. The hard rule is never two copies on one site. The soft rule is to prefer the site that holds the fewest copies of other jobs, so one building's failure touches as few jobs as possible. Started jobs stay where their data is while that site has heat. `--outage SITE:DAY:HOURS:START` simulates a site failure.
- **Defer non-urgent jobs to winter:** simulation jobs (8 server-hours each, due in 120 days, 100/day) share the earliest-deadline-first queue. Heat-useful capacity falls from 96–97 % of the servers in Dec–Feb to **53–54 % in Jun–Aug**. Deferred work builds to 8,300 server-hours by the end of August, October clears it, and **no deadline is missed** (`plots/seasonal_capacity.png`, `python3 -m scheduler.balance --scenario services --monthly`).
- **24/7 at partial power** (`--partial`): servers run at 30–100 % power instead of on/off. On the reference house, a server is on in **100 % of hours instead of 84 %**, and in summer 100 % instead of 70 %. On/off switching drops from 2,866 switches to 0, with the same heat and coverage. That suits always-on light services (an embeddings API, people counting) that need a server up even when little heat is wanted. Limit: we take throughput as proportional to power; at low power caps the idle share makes this optimistic.

## 9. Investor view

From [`outputs/business_case.md`](../outputs/business_case.md#5-investor-view): capex per server is about **CHF 27,000**.

| Item | CHF | Source |
|---|---|---|
| Server: 2× EPYC 9654, 512 GB DDR5, water cooling | 25,000 | `data/prices_2026.json` (listed server USD 23,028 + ~30 % for 2026 memory and cooling) |
| Site share: tank, plumbing, controls | ~2,000 | research estimates, 16,000 per site |

Opex: maintenance at 10 % of capex per year, plus ops (400) and connectivity (1,200 per site). Life 5 years.

At the base case (3.42 CHF per sold server-hour, 70 % of running hours sold, heat 30 % below a heat pump):

| Fleet | EBITDA per server/yr | Payback | Break-even price |
|---|---|---|---|
| reference house | 3,577 | 7.4 yr | 4.19 CHF/server-h |
| services fleet | 9,531 | 2.8 yr | 2.42 |
| services fleet + dry cooler | 12,163 | 2.2 yr | 2.09 |

A rollout of 1,000 servers in services-type sites costs 26.5 M CHF and earns 9.5 M CHF EBITDA a year. The NPV over 5 years at 8 % is 11.5 M CHF.

**RAM risk:** server DRAM rose ~3× from Q4 2025 to Q4 2026 (TrendForce), so the case owner's "2.5×" is if anything low. The 25,000 CHF server price assumes 2026 contract memory prices. At retail RAM prices (USD 2,561 per 64 GB), payback goes from 2.8 to 3.7 years. At early-2025 prices it would be 1.8 years.

**When it does not pay off:**
- below ~2.4 CHF per sold server-hour (spot parity is 2.74)
- when less than about half of the running hours are sold: at 50 % sold, payback is 4.9 years; at 25 % it never pays back
- single homes alone, without summer sites: 7.4 years with 11 servers sized for all of the heat, longer than the server's 5-year life
- free heat

Demand, not heat or price, is the risk.

## 10. Pitch: business case first, then the technology

Slides follow the team's visual-first rule (pictures, numbers, short titles; sentences in the speaker notes).

1. **Business case:**
   - Who pays: privacy-bound Basel customers buy compute results at AWS + 25 %
   - Who gains: hosts get heat 30–50 % below a heat pump, saving 7,500 CHF over 10 years at 50 % off
   - Payback: 2.8 years on a mixed fleet
2. **Customers:** the top-5 list above, with Basel names. One customer, two needs.
3. **Resilience:** distributed across buildings, so no single outage takes the service down. Examples:
   - CrowdStrike/Microsoft, 19 Jul 2024: ~8.5 M Windows devices down
   - AWS us-east-1, 19–20 Oct 2025: ~14.5 h
   - Azure Front Door, 29–30 Oct 2025: ~8 h

   Then our number: across 100 simulated site outages, twin-tier jobs lost nothing.
4. **The technology meets it:**
   - the reference-house key figures
   - the live demo: January day, July day, interrupted real job
   - the scheduler's two inputs (heat, redundancy)
   - summer: deferral to winter, partial power, dry cooler
5. **Where it stops holding:** RAM price, sold share, household tariffs vs "host pays 50 %", hot water at 60 °C without a booster.
