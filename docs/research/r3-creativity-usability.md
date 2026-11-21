# Round 3 — Creativity (20%) and one-minute usability (10%)

Investigator file for the weak point "is the idea fresh, and what does a homeowner see". Plan and assessment only; nothing here is built.

**Status labels:** *sourced* = number read on the URL given (all pages were read through a summarising fetch tool unless marked "text read directly"; re-read by eye before slide use) · *computed* = printed by `python3 analysis/r3_creativity_usability.py` (stand-in profile, case assumptions, plain follow policy, unlimited jobs) or taken from `docs/overnight.md` with its script named · *unverified* = search snippet, estimate or own reading · *assumption* = our choice.

Currency: CHF. No conversion is used in this file. Vendor figures in EUR or GBP are quoted in their own currency and not converted.

Script: `analysis/r3_creativity_usability.py` (standard library, imports `load()` and `simulate()` from `analysis/baseline_sweep.py` unchanged). Command: `python3 analysis/r3_creativity_usability.py`. Paid web calls used: 2 of 6.

---

## Short answer

1. **The core of the working idea is standard practice.** Running servers only when heat is wanted, stopping at a full tank, using delay-tolerant batch work and letting the operator pay the electricity have been described since 2011 and are sold today. "Heat is the admission ticket for compute" is a good sentence for an old rule.
2. **The market has already answered the summer problem, and its answer is not the single-family house.** Vendors moved to year-round heat users (hot water in apartment blocks, pools, care homes, district heating) or vent the heat. One vendor's stated minimum site is 500 GJ per year; the reference house is 112.4 GJ, 22.5% of that (*computed* from a *sourced* threshold).
3. **What was not found in prior art** (about 12 searches, 20 pages; absence is *unverified*, not proof): accepting or refusing a job at intake by a dry run on the weather forecast so that accepted deadlines hold without dumping; a published missed-deadline share next to coverage and dumped heat for one house-year; any published utilisation or compute price from a compute-heating vendor.
4. **Recommended creative core: "heat quote in, heat receipt out".** Every offered job gets a quote before it runs (accepted with a finish time, or refused with the reason "no heat until ...") and a receipt after it ("this job delivered 3.2 kWh = one person's hot water for a day"). The quote is the existing admission dry run shown to the customer; the receipt is one multiplication. **Backup: the sizing rule "size to the median heating hour, not the coldest hour"** with one load-duration chart.
5. **The deadline-priced "heat-flex" tariff is the weakest of the examined angles**, on two computed grounds: heat can fund at most a 32.0% discount, below the 50% that cloud batch tiers already give for a 24-hour window; and a longer deadline does not solve summer, because in June to August the limit is the quantity of heat (15 server-hours a day), not the wait for the next permit.

---

## (a) Prior art

### Companies

| Who | What they do about heat demand and summer | Units per building | Workloads | Published utilisation or price | Status and URL |
|---|---|---|---|---|---|
| French vendor of "digital boilers" (formerly room heaters with servers) | Left room heaters for hot-water boilers because of seasonality: "We're stopping doing heaters and going more for boilers"; "So now we go to social housing [and large apartment blocks], where we can run 24x7 for hot showers"; limit named by the vendor: "you cannot put 500kW of hot water 24x7 in that housing [complex], even if it's a large one". Boilers deliver water at 65 °C by direct water cooling. Target sites of 500 kW to 1 MW for district heating that runs 24x7 | Module of up to 12 servers; pilot site in Finland with 100 kW of compute | Bank risk computation, 3D animation rendering | None found | *sourced*: <https://www.datacenterdynamics.com/en/analysis/making-the-most-of-your-waste-heat/> (10 Nov 2022, paid scrape); <https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/> |
| Same vendor, per-task report | A "Carbon Facts" object per task or pool with `energy_reuse` ("the reuse heat, in W.h"), `energy_it`, carbon saved by the heating part, and site ratios. Module is labelled a prototype | — | — | — | *sourced*: <https://doc.tasq.qarnot.com/documentation/sdk-python/api/compute/carbon_facts.html> |
| Same vendor, "radiators discontinued in 2023 because of lower computing resources in summer" | Search snippet only; the page returned 403 | | | | *unverified* (snippet of <https://eurekanetwork.org/?p=3009>) |
| UK vendor of a server unit clamped to a hot-water cylinder | Sizes the unit for hot water only: "up to 4.8 kWh per day, and at least 2.5 kWh as per contractual obligations"; aims to "match the output power of the CPUs to about 80 percent of what the hot water usage" of a family of four is. What the unit does when the cylinder is hot: not stated on any page read | One unit per home; trial of "about a hundred units" | Batch only: "We're not looking at serving real time workloads"; "Our ideal job is; here's a chunk of data, go and process that for some hours"; Kubernetes, VM clusters, CI runners listed on the site | Household saving "£150–350 a year" (vendor claim); no compute price ("save vs the public cloud") | *sourced*: <https://www.cnx-software.com/2023/02/15/install-a-server-in-your-house-get-free-hot-water/>, <https://www.theregister.com/2023/01/12/heata_offers_free_hot_water/>, <https://www.heata.co/> |
| Dutch vendor placing servers in buildings | Avoids the summer problem by site choice: "All models operate 24/7 with flat heat curve"; eligibility "minimum 500 GJ/year"; sites: apartments, care homes, pools, hospitals, district heating, aquifer storage. Output 45–65 °C. Operator owns the equipment and pays the servers' electricity; heat is free | "modular 20 kW building blocks", 20–120 kW IT load; one 5 kW site "displaced 25% of a care facility's natural gas use" | Cloud (not detailed on the page) | "630 to 3,780 GJ per year, delivered 24/7"; site saving "€6,000 annually" (vendor claims). No utilisation or compute price | *sourced*: <https://leaf.cloud/leafsites/> |
| UK vendor heating swimming pools | Picks a year-round heat user. Pilot cuts the pool's gas use by 62%, saving about £20,000 a year; about 96% of the heat is recycled (vendor claims). What happens when the pool needs no heat: not stated | One immersion unit per pool. "28 kW" and "operator pays the electricity" were seen in a search snippet only | HPC and cloud for a partner cloud provider (snippet) | None | *sourced*: <https://www.techradar.com/news/this-startup-is-recycling-energy-to-heat-swimming-pools-for-free>; the 28 kW figure is *unverified* |
| German vendor (2014 article) | Vents: "In the summer, heat generated from the servers is vented out to stop a building becoming a sauna." Operator pays internet and electricity; heat free for 15 years | Racks in a cabinet, installed for €12,000 | Cloud | Hardware replaced every three years | *sourced*: <https://www.itpro.com/cloud/363061/heat-your-house-with-the-cloud> (17 Nov 2014) |
| UK vendor's forum statement (already in `docs/overnight.md`) | "We pay for all electricity used by the unit"; units "put between 180W and 200W into the tank when at full power" | | | | *sourced* in round 2: <https://forums.theregister.com/forum/all/2023/01/12/heata_offers_free_hot_water/> |

### Research

| Work | What it already contains | Status and URL |
|---|---|---|
| "The Data Furnace: Heating Up with Cloud Computing" (workshop paper, 2011) | Micro-datacentres "on the order of 40 to 400 CPUs, that serve as the primary heat source for a single-family home". Three classes: **Type A "low-cost seasonal"** computes "predominantly when the house needs heating (e.g. at nights or during winters), providing seasonal computing capacity", skewed to "the northern hemisphere's winter months", fit for "delay-tolerant batch jobs ... performed opportunistically"; **Type C** runs "year-round even when heat is not needed in the home by pumping excess heat directly outside", noting "summer operation costs more because higher electricity rates are not compensated by sale of heat". Sizing by the coldest day with 350 W servers. Overhead "less than $90 per server per year" against "approximately $400" in a data centre; savings $280.4 to $324.4 per server per year | *sourced*, text read directly with `pdftotext`: <https://classpages.cselabs.umn.edu/Fall-2021/csci8980-ec/papers/EdgeArch/furnace.pdf> (course mirror of the paper) |
| "Thermal aware scheduling on distributed computing water heaters" (conference paper, 2018, with a French water-heater maker) | The same rule as our heat permit, at tank level: "Availability of a CWH is true if and only if temperature of water is below the target temperature"; "When a CWH reaches its target temperature, it stops computing". Pull-based: the heater asks for exactly the work "needed ... to reach the target temperature". Names "starvation" (not enough work, electric resistance heats instead) and "saturation" (tank hot, no work accepted). **Non-preemptive, no deadlines**; migration listed as future work "implying ... good prediction of water usage". Simulation with 10 heaters of 10 CPUs: "CPU usage of about 60% while minimizing the thermal resistance usage to 10%" | *sourced*, text read directly with `pdftotext`: <https://perso.ens-lyon.fr/laurent.lefevre/pdf/CCNC2018_Rais_Caron_Lefevre.pdf> |
| "Heating Homes with Servers: Workload Scheduling for Heat Reuse in Distributed Data Centers" (journal paper, 20 Apr 2021, with the French vendor) | Constraint-satisfaction model "to optimally allocate workload on servers to reach and maintain the desired home temperature setpoint"; a physical and a machine-learning model link heat demand to workload ("correlation accuracy" 11.98% and 4.74%, as the abstract words it); validated on monitored data of an operating distributed data centre. Deadlines, job flexibility and summer are not mentioned in the abstract; the full text was not read | *sourced* (abstract and metadata, paid scrape): <https://www.mdpi.com/1424-8220/21/8/2879> |
| Conference talk "Scheduling at the edge" (2019) | The vendor's platform of "smart heaters (built upon multi-cores)", a digital twin to test scheduling algorithms, assessed on real logs | *sourced*, abstract read directly: <https://scheduling2019.sciencesconf.org/275794/275794.pdf> |
| An operations-research abstract (2022): "scheduler matching computing and heating needs", "adaptive heat-aware scheduling" | Search snippet only; the page did not open | *unverified* |
| Deadline-dependent pricing across data centres (2012 paper), and a patent with lower charges for looser deadlines | Search snippets only; not opened (certificate error) | *unverified* |
| Cloud batch tiers | One provider's batch API "costs 50% less than standard API calls" and "Each batch is processed in less than 24 hours". Another provider's flex tier gives "lower costs ... in exchange for slower response times and occasional resource unavailability" (no percentage on the page) | *sourced*: <https://claude.com/blog/message-batches-api>, <https://developers.openai.com/docs/guides/flex-processing> |

### Our idea against that, part by part

| Part of the working idea | Verdict | Evidence |
|---|---|---|
| Servers run only when the house or tank can take the heat | **Standard.** Described in 2011 (seasonal class), implemented as "available iff below target temperature" in 2018 | the two papers above |
| Never dump | **Standard for hot-water units** (stop at target temperature). Others vent (2014 article, 2011 Type C) | above |
| Delay-tolerant batch jobs as the workload | **Standard** | 2011 paper; UK vendor's "chunk of data ... for some hours" |
| Work without heat goes to another site with year-round heat demand | **Standard, and it is where the industry went**: apartment blocks, pools, care homes, district heating | three vendors above |
| Operator pays electricity, host gets heat free | **Standard** among the vendors read. It corresponds to our 0.3325 CHF break-even, not 0.2261 | Dutch, German and UK vendors above |
| Per-job statement of reused heat | **Exists** (energy in W.h and carbon per task, labelled prototype) | SDK page above |
| Discount for a longer deadline | **Standard in cloud** (50% for 24 hours), not tied to heat | batch API page above |
| Forecast-based control | Exists for temperature setpoints (2021 paper predicts workload for a setpoint) | abstract above |
| **Admission at intake by a forecast dry run, so that accepted deadlines hold with zero dumping** | **Not found.** The 2018 scheduler has no deadlines and no preemption; the 2021 abstract does not mention deadlines | absence, *unverified* |
| **Missed deadlines, coverage, dumped heat and break-even published together for one house-year, reproducible** | **Not found.** No vendor page read gives utilisation, a compute price or a deadline record | absence, *unverified* |
| **Several servers in a single-family house for space heating, with run hours per server rank** | The 2011 paper sizes to the coldest day and does not rank servers; today's vendors avoid this building type | 2011 paper; the 500 GJ minimum |

**Honest reading for the pitch.** Do not claim that heat-following compute, heat permits or "never dump" are new; the founders know the vendors above. The defensible claims are narrower: (1) we say yes or no to a job before it starts, from the weather forecast, and publish how often that promise fails; (2) we show per server rank how many hours it runs, which turns "how many servers per house" into one chart; (3) every number is reproducible from one command. Say "we did not find" rather than "nobody does".

**Uncomfortable finding for Q&A.** The reference house is 22.5% of one vendor's minimum heat demand for a site, and the vendor that started with room heaters left them for year-round hot water. A founder can ask why a single-family house is the right unit at all. The honest answer on present numbers: for the house alone it does not pay back (N\* = 0 in `docs/overnight.md`); the house model is the building block for a fleet figure, and the summer hours are the reason.

---

## (b) Candidate angles, ranked

Numbers are *computed* by `python3 analysis/r3_creativity_usability.py` unless marked. Relevant output:

```
== 1. Heat receipt: what one server-hour and one job deliver ==
Case hot water: 12.0 kWh/day for 4 x 50 l = 60 Wh per litre -> implied temperature rise 51.6 K (litres x K x 1.163 Wh/(l K))
One person's hot water for one day (case): 3.00 kWh
One shower (assumption: 50 l mixed water, +28 K): 50 x 28 x 1.163 = 1.63 kWh
Reference house space heating at 0 C outdoor: 7.81 kW (case formula)
unit                             heat kWh l hot water person-days  showers  min heating @0C heat value CHF
1 server-hour                        0.80        13.3        0.27     0.49              6.1         0.1064
J1 (0.5 server-h, assumption)        0.40         6.7        0.13     0.25              3.1         0.0532
J2 (4 server-h, assumption)          3.20        53.3        1.07     1.97             24.6         0.4256
J2 per million output tokens (basis 17.7 M tokens per job is UNVERIFIED): 181 Wh heat = 3.0 l of case hot water
Receipt is valid only for hours with zero dumping. Check, follow policy:
  N=6: run hours x 0.8 = 24854 kWh, heat used = 24854 kWh, dumped = 0 kWh, difference (left in tank at year end) = 0.0 kWh
  N=8: run hours x 0.8 = 29025 kWh, heat used = 29025 kWh, dumped = 0 kWh, difference (left in tank at year end) = -0.0 kWh

== 2. Heat-flex tariff: how large a discount the heat can fund ==
Net electricity cost, heat-matched server-hour: 0.2261 CHF
Net electricity cost, server-hour with heat unused: 0.3325 CHF
Difference = heat credit per server-hour: 0.1064 CHF = 32.0 % of the unmatched cost
If the homeowner gets the heat free, the heat funds no discount (0 %).

Permit capacity by month, 2025 stand-in, plain follow (server-hours per day):
month  N=6 srv-h/day  % of Jan  N=8 srv-h/day  % of Jan
01             144.0      100%          185.8      100%
02             144.0      100%          184.3       99%
03             138.1       96%          162.1       87%
04              92.5       64%           92.4       50%
05              42.9       30%           42.9       23%
06              15.0       10%           15.0        8%
07              15.0       10%           15.0        8%
08              15.0       10%           15.0        8%
09              39.2       27%           39.2       21%
10             101.7       71%          101.7       55%
11             133.8       93%          160.5       86%
12             143.9      100%          184.2       99%
N=6: Jun-Aug 1380 server-h (4.4 % of the year), Dec-Feb 12957 server-h (41.7 %), ratio winter/summer 9.4
N=8: Jun-Aug 1380 server-h (3.8 % of the year), Dec-Feb 16631 server-h (45.8 %), ratio winter/summer 12.1

== 2b. Wait for heat, one house, empty queue ==
N=6; a job uses one server; wait = clock hours from arrival to completion
month  job    median h  P90 h  max h
01     J2            4      4      4
04     J2            4      6      7
07     J2            6      7      7
10     J2            4      6      7

== 3. Sizing rule: 'servers follow the Xth percentile hour' ==
Hours in year: 8760; hours with space heating: 4942
  N N x 0.8 kW  hours demand >= that = percentile (all h)  percentile (heating h)  run h of Nth server
  1        0.8                  4936                43.7%                    0.1%                 7629
  4        3.2                  4562                47.9%                    7.7%                 4885
  6        4.8                  3476                60.3%                   29.7%                 3796
  7        5.6                  2729                68.8%                   44.8%                 2933
  8        6.4                  2046                76.6%                   58.6%                 2281
 10        8.0                   776                91.1%                   84.3%                  913
 13       10.4                     2               100.0%                  100.0%                    5
P50 hourly demand: all hours 3.55 kW -> 4.4 servers; heating hours 5.85 kW -> 7.3 servers
P90 hourly demand: all hours 7.84 kW -> 9.8 servers; heating hours 8.51 kW -> 10.6 servers

== 4. Neighbourhood view ==
N=6: idle server-hours per year 21493 (= 17194 kWh heat if run elsewhere); Jun-Aug idle 11868 server-h = 5.38 servers continuously = 4.30 kW of heat, 9494 kWh over the three months
N=8: idle server-hours per year 33799 (= 27039 kWh heat if run elsewhere); Jun-Aug idle 16284 server-h = 7.38 servers continuously = 5.90 kW of heat, 13027 kWh over the three months

== 5b. Prior-art comparisons and the utility's view ==
Reference house total heat demand 31231 kWh = 112.4 GJ per year; one vendor's stated minimum for a site is 500 GJ per year -> the house is 22.5 % of that minimum (4.4 houses per minimum site)
A UK hot-water unit: up to 4.8 kWh/day = 40 % of the case's 12 kWh/day hot water; 4.8 kWh/day = 200 W continuous = 0.25 of one case server's heat
N=6: servers draw 31067 kWh electricity per year for 24854 kWh heat; a heat pump at 2.5 would draw 9941 kWh for the same heat -> ratio 3.125; peak electrical load 6 kW against 1.92 kW for the heat pump at the same heat output
```

(The full output has all 13 rows of section 3, J1 rows of 2b and the monthly figures of section 5.)

### Rank 1 — "Heat quote in, heat receipt out" (recommended creative core)

- **What it is.** Two lines around every job. *Before:* the admission dry run already decides whether a job's deadline can be met with forecast heat; print its answer as a quote: "Accepted. Finishes by Tue 14:00. All of its heat will be used." or "Not at this house: no heat for it before its deadline." *After:* a receipt: "4.0 server-hours · 3.2 kWh of heat delivered · about one person's hot water for a day · 0 kWh thrown away".
- **What is new.** The quote: a yes or no at intake that comes from the weather, with a published failure rate (the missed-deadline range). Not found in the prior art read. The receipt alone is not new (a per-task reused-energy figure exists in one vendor's SDK); the household unit and the pairing with the quote are presentation.
- **Number or screen.** Per server-hour 0.80 kWh = 13.3 litres of hot water at the case's own ratio (12 kWh for 200 litres) = 6.1 minutes of heating the reference house at 0 °C. J2 (4 server-hours, *assumption*) = 3.20 kWh = 1.07 person-days of hot water (case: 3.00 kWh per person and day). J1 (0.5 server-hours, *assumption*) = 0.40 kWh = 6.7 litres. Use "person-days of hot water" (case-derived), not "showers" (our 50-litre shower is an *assumption*).
- **Build work.** Receipt: about 1 person-hour (one multiplication in the trace line and in the job-finished line; role C or D). Quote: about 1 to 2 person-hours **on top of admission being in the core**, which is itself at risk (open risk 4 in `docs/overnight.md`). If admission is not in the core at the 21:00 freeze, show the receipt only and say the quote comes from the separate analysis script.
- **Criterion served.** Creativity (20%), usability (10%), transparency (each job's heat is traceable).
- **Hardest founder objection.** "A per-task heat figure already exists at a competitor, and your receipt is 0.8 kWh times hours: the case's assumption, not a measurement. Your demo job runs on a laptop at about 20 W. What did it really heat?" Answer to prepare: the receipt is valid because dumped heat is 0 kWh in the yearly run (*computed*: run hours × 0.8 equals heat used for N = 6 and 8); for the laptop job it is the scaled, modelled figure and the screen must say "modelled for the 1 kW reference server".

### Rank 2 — Sizing rule "size to the median heating hour, not the coldest hour" (recommended backup)

- **What it is.** One rule a utility can apply to any building's load curve: the number of servers is the heat demand of the median heating hour ÷ 0.8 kW. For the reference house: 5.85 kW ÷ 0.8 = 7.3 servers, against 12.5 for the coldest hour (case text).
- **What is new.** Little as engineering: it restates "run hours of the last server" (already in the plan), and sizing a base-load heat source on a load-duration curve is ordinary heating practice (*unverified*, own knowledge, no source opened). New only against the 2011 paper, which sizes to the coldest day, and against the case's 12.5.
- **Number or screen.** One load-duration chart (see (c), chart 3). N = 6 sits at the 29.7th percentile of heating hours (demand reaches 4.8 kW in 3,476 hours; the sixth server runs 3,796 h/yr with the tank); N = 8 at the 58.6th percentile (2,046 hours; eighth server 2,281 h/yr); the median gives 7.3.
- **Build work.** Under 1 person-hour: numbers exist; the chart is a sorted list. No scheduler change.
- **Criterion served.** Feasibility (a rule DigitalHeat can carry to another building), usability (the 6-versus-8 choice in one picture), some creativity.
- **Hardest founder objection.** "Why the median? Your own payback rule says zero servers. A percentile is a coverage choice dressed as a rule." True; present it as "the percentile is the dial, here is what each setting costs in run hours", not as an optimum. Note it lands between the plan's 6 and 8 and does not settle that choice.

### Rank 3 — Seasonal contract shaped to the heat curve

- **What it is.** Sell capacity by month in the shape of the house's heat demand. Already simulated in round 2 (heat-shaped contract: coverage 74.1% / 86.1%, missed 0.000% / 0.016%, *computed*, `analysis/r2_deadline_sim.py`).
- **What is new.** The 2011 paper already names "seasonal computing capacity ... skewed toward the northern hemisphere's winter months". No vendor read publishes a monthly quantity; a table would be new as a published number, not as an idea.
- **Number or screen.** Monthly permit capacity, 2025 stand-in, N = 6: 144.0 server-hours a day in January, 92.5 in April, 15.0 in June to August, 101.7 in October; June to August hold 4.4% of the year's server-hours and December to February 41.7% (ratio 9.4; 12.1 at N = 8). The plan's 2020–24 means for N = 8 (15.0 to 185.3) agree.
- **Build work.** About 1 person-hour for a table on the screen; nothing if it stays a slide.
- **Criterion served.** Feasibility, scheduling quality (it is what makes misses near zero).
- **Hardest founder objection.** "Who buys compute that shrinks to a tenth in summer? Name the customer." No answer in the plan (open risk 4: no customer type named). April and October vary two- to four-fold between years (52.8 to 145.7 and 24.4 to 110.9 at N = 8 in `docs/overnight.md`), so the shoulder months cannot be contracted firmly.

### Rank 4 — Deadline-priced "heat-flex" tariff

- **What it is.** Jobs with longer deadlines pay less, so that work which can wait takes the heat-matched hours.
- **What is new.** Deadline discounts are standard in cloud (50% for 24 hours, *sourced*). Tying the size of the discount to the heat value would be new: the heat credit is 0.1064 CHF per server-hour, **32.0%** of the 0.3325 CHF an unmatched hour costs (*computed*).
- **Why it ranks low.** (1) 32% is below the 50% the market already gives for a day's delay, and it is 0% if the homeowner gets the heat free. (2) The premise "summer work self-selects through longer deadlines" fails on the numbers: with an empty queue a 4-hour job waits a median of 6 hours in July against 4 in January. Summer is short of quantity (15 server-hours a day for three months), not of timely permits; only a deadline of months would move summer work to autumn. (3) It needs a price per job class, and "computing income" has no defensible value (open risk 11).
- **Number or screen.** Two price floors by class: 0.2261 CHF per server-hour for work that waits for heat, 0.3325 CHF for work that must run now. These are the plan's two existing break-even figures under a different reading, so check the wording with whoever owns the break-even slide.
- **Build work.** About 1 person-hour as a table; more than 2 if prices enter the scheduler. Flag: scope risk.
- **Criterion served.** Creativity, feasibility ("who pays, and how much" from the case deck).
- **Hardest founder objection.** "Batch APIs are already half price with a 24-hour window. Why would a customer take 32% off from you, with jobs refused in summer?"

### Rank 5 — Neighbourhood view: summer work goes to a named year-round heat user

- **What it is.** Show the house next to an apartment block, pool or care home that takes the work the house refuses.
- **What is new.** Nothing: this is the industry's current model (three vendors above). The case itself names it ("hotels, spas, agriculture").
- **Number or screen.** What the partner would have to absorb for one house: 11,868 idle server-hours in June to August at N = 6 = 5.38 servers running continuously = 4.30 kW of heat (N = 8: 16,284 server-hours, 7.38 servers, 5.90 kW). Over the year 21,493 / 33,799 idle server-hours. A flaw to state: a job can only move if the partner site has idle servers; a site that runs "24/7 with flat heat curve" has none, so the partner needs its own extra hardware.
- **Build work.** More than 2 person-hours (a second site in the model). "Kill-and-move scene" is already third on the cut list. **Adds build scope; do not build.** One sentence in the outlook is enough.
- **Criterion served.** Creativity (weakly), business value.
- **Hardest founder objection.** "That is our own slide 4. And if the pool takes the heat all year, why put servers in the house at all?"

### Recommendation

- **Creative core: rank 1, "heat quote in, heat receipt out".** It needs no new mechanism, puts the plan's one part not found in prior art (forecast admission with a published failure rate) in front of the jury in the customer's words, and gives the interrupted-job demo a readable ending.
- **Backup: rank 2, the median-heating-hour sizing rule with the load-duration chart.** It has no dependency on admission being finished and can be shown from numbers that already exist.
- Ranks 3 to 5 are single sentences or one table at most.

---

## (c) The one-minute screen (specification only)

One page, no scrolling on a laptop. Top row: six tiles in the order the case's presentation format gives. Below: charts. A two-way switch "Homeowner | Energy utility" changes the wording under the tiles and swaps the second chart. **Scope flag:** the switch is extra work (about 1 to 2 person-hours); the minimum is one wording (homeowner) with chart 3 shown as a static picture in the slides.

Header line, always visible: "Reference house, Basel, weather of 2025 · 6 servers (8 beside it) · case assumptions · every run hour sold".

### The six tiles, in the required order

Values are for N = 6 with N = 8 in small print beside each; all from `docs/overnight.md`.

| # | Case term | Tile label (plain language) | Value N = 6 (N = 8) | Small print under the tile | Status |
|---|---|---|---|---|---|
| 1 | Servers per house | "Servers in the basement" | **6** (8) | "1 kW each. A choice about coverage, not an economic optimum." | *assumption* (team decides Saturday) |
| 2 | Share of heat demand covered | "Heat that comes from the servers" | **79.6%** (92.9%) | "24,854 of 31,231 kWh a year. The rest, 6,377 kWh, comes from the backup heater. Assumes every run hour is sold." | *computed*, `analysis/baseline_sweep.py`; kWh from `analysis/r3_creativity_usability.py` section 5 |
| 3 | Heat dumped | "Heat thrown away" | **0 kWh** (0 kWh) | "Servers stop when the house and the tank are full." | *computed*, same |
| 4 | Utilisation | "Share of the year the servers run" | **59.1%** (51.8%) | "Hours running ÷ (servers × 8,760 hours)." | *computed*, same |
| 5 | Missed deadlines | "Accepted jobs finished late" | **about 1 to 6 in 1,000** (same range, worse at 8) | "Roughly 0.1 to 0.6% of accepted jobs. Weather-forecast error only; no hardware or network failures. Job mix is our assumption." | *computed* range, `analysis/r2_deadline_sim.py` plus critic checks; never shown as 0%; the live figure must come from the team's own scheduler |
| 6 | Break-even computing price | "What an hour of computing must earn" | **0.2261 CHF per server-hour** (same) | "0.3325 CHF if the homeowner gets the heat for free. Electricity only; no hardware." | *computed*, `analysis/r2_fleet_economics.py` |

Notes:
- Tile 2 under finite saturating offers is 79.2% / 92.8% (*computed*, `analysis/r2_deadline_sim.py`); the tile must name which run it shows ("at X% sold").
- Must-have 3 also asks for electricity cost and computing income; they are not among the six opening figures. Put them in one line under the tiles: "Electricity for the servers: 10,330 CHF a year (12,063). Computing income: scenario only, see assumptions." (*computed* / open risk 11).
- Utility wording for the same tiles: tile 2 "Share of the building's heat supplied by server heat"; tile 4 "Load factor of the installed 6 kW"; tile 6 unchanged. Extra line for the utility: "Electricity drawn: 31,067 kWh a year, peak 6 kW, 41.7% of it in December to February. A heat pump at 2.5 would draw 9,941 kWh for the same heat (3.1 times less)." (*computed*, `analysis/r3_creativity_usability.py` sections 2 and 5b). This line is uncomfortable and should be on the screen: it is the reason the computing has to be worth 0.2261 CHF an hour.

### Charts (three at most)

| # | Shown to | Title | Type | x-axis | y-axis | Series and labels |
|---|---|---|---|---|---|---|
| 1 | both | "Where the heat comes from, month by month" | stacked bars, 12 bars | Month, Jan to Dec | Heat per month, kWh (0 to 5,500) | "From the servers" and "From the backup heater", labelled on the bars, no legend box needed for two series. Values *computed* (section 5): January 3,571 of 5,354 kWh from servers at N = 6; June 360 of 360 |
| 2 | homeowner (and the live demo) | "Today, hour by hour" (the January day or the July day) | step line and filled steps, one axis | Hour of day, 0 to 23 | Heat, kW (0 to 11) | Line "Heat the house needs"; filled steps "Heat from the servers" (steps of 0.8 kW); gap labelled "backup heater". **The tank is not a second axis:** a horizontal gauge beside the chart, "Hot-water tank: 21 of 35 kWh". Under the chart one event row with markers "paused: tank full" and "resumed", and the receipt line of the job that was interrupted |
| 3 | utility (static picture in the slides if the switch is cut) | "How many hours each server runs" | load-duration curve with bands | Hours of the year, sorted from coldest, 0 to 8,760 | Heat demand, kW (0 to 10.5) | Curve "Heat demand"; horizontal bands 0.8 kW high, one per server, each labelled with its hours per year (server 1: 7,629 h … server 6: 3,796 h; server 7: 2,933 h; server 8: 2,281 h); the area above the last band labelled "backup heater"; a marker "median heating hour: 5.85 kW = 7.3 servers". Hours are from the run with the tank, the curve is raw hourly demand, so the band edges and the curve differ slightly (3,796 h against 3,476 h for server 6); say so in the caption |

Demo-day values for chart 2 are not fixed here: the plan requires the January and July days to be recomputed for the adopted policy and N before choosing.

### Five-minute pitch outline

Timing checked by the script (section 6, total 300 s, live part 130 s as the plan allows). Every number below is in `docs/overnight.md` or this file, with its label.

| Time | Part | Content and the only numbers to say |
|---|---|---|
| 0:00–0:40 | **Key figures**, six tiles in order | "6 servers. 79.6% of the house's heat. 0 kWh thrown away. Running 59.1% of the year. About 1 to 6 accepted jobs in 1,000 late, from forecast error alone. Computing must earn 0.2261 CHF per server-hour, 0.3325 if the homeowner gets the heat free." With 8 servers: 92.9% and 51.8%. (*computed*; N is an *assumption*) |
| 0:40–1:05 | **The idea** | "A job is accepted only if the weather forecast says its heat will be wanted: a quote before, a receipt after. A 4-hour job leaves 3.2 kWh in the tank, one person's hot water for a day." (*computed*; job size is an *assumption*). One clause on prior art: "following heat is not new; saying no at intake and publishing the misses is what we add." |
| 1:05–1:45 | **Live: January day** | Chart 2. All servers run, the backup heater fills the gap. January coverage 67% at N = 6, 86% at N = 8 (*computed*, section 5). The scheduler's decision trace scrolls beside it |
| 1:45–2:35 | **Live: July day** | Hot water only: 12 kWh a day, at most one server, 15 server-hours a day (*computed*). Jobs beyond that are refused at intake (the quote), not dumped. Tank gauge fills; "paused: tank full" appears |
| 2:35–3:15 | **Live: the interrupted job** | The real process is paused by the same scheduler code; state check shows it stopped; it resumes from its checkpoint; receipt printed. Say: "the laptop freezes the process where a real unit would checkpoint and power down" (wording fixed in round 2) |
| 3:15–3:50 | **Limits** | "These are the case's simplifications. With tank losses and an electric hot-water booster, June-to-August coverage drops by about 20 points if the server loop reaches 50 °C, and the break-even rises by under 0.01 CHF per server-hour." (*computed* under *assumptions*; convention named on the slide.) "Missed deadlines count forecast error only." "The demo job runs on a laptop; the prices are GPU rental prices: different machines." |
| 3:50–4:35 | **When it does not pay off** | "Below 0.2261 CHF per sold server-hour, or 0.3325 if the heat is given away. The lowest job rate on the one marketplace with published host rates is at most 0.215 CHF per kW-hour: below break-even." (*computed*) "Including hardware at 6,000 CHF per kW over five years, no server pays back at the host rates we could source; six servers need 0.54 to 0.64 CHF net per run hour." (*computed*; hardware cost and life are *assumptions*) "The servers draw 3.1 times the electricity of a heat pump for the same heat, so the computing has to carry it." (*computed*) |
| 4:35–4:50 | **Close** | "What a pilot must measure first: installed cost per server in a basement, and who is paid for the heat." (the two questions fixed in round 2) |
| 4:50–5:00 | Reserve | |

Checks against the plan:
- Order matches the case: key figures first, then January day, July day, interrupted job. Limits and "does not pay off" follow the demo.
- 0% missed deadlines is never said. Coverage is said with "every run hour sold" on the screen header.
- Numbers that must not be said because they did not survive: any payback of "1 server in 4.8 years", "39% moved or missed", H100 figures, 0.15% / 0.29% as single values, "0.009 CHF" as the only booster figure.
- The 0:40–1:05 slot is the only place the creative angle is stated; if the quote is not in the core at the freeze, replace "a quote before" by "the scheduler refuses work it has no heat for" and keep the receipt.
- Risk in the timing: the plan's 130 s live part was an *assumption* with 2.5 s per simulated hour for July (60 s); this outline gives July 50 s, so 2.0 s per hour or a shortened day. To be regenerated with the adopted policy.

---

## Not done, and limits of this file

- Vendor pages are marketing; no vendor figure was checked against a second source. Quotations came through a summarising fetch tool except the two papers read with `pdftotext`.
- Not read: the full text of the 2021 journal paper (abstract only), the 2022 operations-research abstract, the deadline-pricing paper, any Swiss or German-language vendor, patents. "Not found" above means not found in this search.
- Pages that returned 403 or did not open: the eurekanetwork article, two trade-press news items on the pool vendor and on batch processing on hot-water units, a utility's press release on a hot-water trial, the 2012 pricing paper.
- The receipt figures use the case's 80% recovery and the plan's assumed job sizes; none is a measurement.
- The pitch outline was not rehearsed; the timings are a budget, not a measurement.
- Section 2b assumes an empty queue and one server per job; it shows the wait for the next permit, not queueing delay.
