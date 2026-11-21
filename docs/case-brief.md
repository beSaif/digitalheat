# DigitalHeat case brief

**Useful Load ⇒ Useful Heat: can your computing power heat a home while doing useful work?**

Category: Useful heat from computing · Case partner: DigitalHeat
Event: sprintd Basel · GreenTech Edition, 20–22 November 2026
Source: <https://app.sprintd.org/events/sprintd-basel-greentech/cases/useful-load-useful-heat-can-your-computing-power-heat-a-home> (copied 2026-11-20; re-checked 2026-11-21 10:40: case text unchanged, two resources added, see [Resources](#resources-shared-by-the-case-partner))

---

## The problem today

Servers turn almost all the electricity they use into heat, and that heat is usually cooled away with even more energy. At the same time, homes spend money and energy to produce heat. Which computing workloads fit, how to schedule them against a home's heat demand across the year, and when it pays off is still an open question. Build alternatives to big data centres.

## The expected outcome

A working demonstrator that schedules interruptible computing jobs across distributed servers so that their heat arrives where and when homes need it, over a full year. It shows in transparent, reproducible numbers how much useful heat and useful computing it delivers, and at what cost.

## Who it serves

DigitalHeat, which wants to show that computing can heat homes in a useful way, and homeowners and building operators who want lower heating costs.

## Data

### Starting assumptions (simplified, provided by DigitalHeat)

- One rack server uses 1 kW of electricity and produces about 1 kW of heat.
- 80% of that heat can be recovered into a water-based heating system.
- A typical house needs about 10 kW of heating power on a cold winter day (example value).
- One server running continuously delivers about 19.2 kWh of recoverable heat per day.
- Heating is mainly needed from October to March; hot water is needed all year.
- Simplification: recovered heat can be used for space heating and hot water without a heat pump.

The tension in these numbers is the heart of the case: in the coldest hour a house needs about 12.5 servers (10 kW ÷ 0.8 kW), while summer hot water needs about 0.6 (12 ÷ 19.2 kWh per day). How many servers per house make sense, and what they do from April to September, is for the teams to decide.

### Reference house

The same for every team, so results can be compared.

- **Weather:** Open-Meteo historical archive (<https://open-meteo.com/en/docs/historical-weather-api>), Basel (47.56 N, 7.59 E), 1 January to 31 December 2025, hourly, timezone Europe/Zurich: outdoor temperature and solar irradiance. Free CSV download, no login.
- **Heating demand per hour:** `max(0, 10 kW × (20 − T) ÷ 25.6)`, with T = hourly `temperature_2m` in °C, on heating days only. A heating day is a local calendar day (00:00 to 23:00, Europe/Zurich) whose mean of the 24 hourly values is below 12 °C. 25.6 is a fixed constant (20 minus the coldest hour of 2025, −5.6 °C). This gives about 27,000 kWh of heat per year on 206 heating days.
- The ready hourly profile (weather, heating demand, hot water) is provided as a CSV with the case, so every team starts from the same numbers. *(Still not on the case page. We asked in the case Q&A; the answer on 21 Nov was an upload of real data from a Basel house with four apartments, see [Resources](#resources-shared-by-the-case-partner). That is a different building, not this profile. Our rebuilt profile stays the reference: [data/reference_house_2025_hourly.csv](../data/README.md#reference-house-profile).)*
- **Hot water:** 12 kWh per day, all year (household of four, about 50 litres of hot water per person and day).
- **Heat storage:** one water tank with about 35 kWh usable capacity (1,000 litres, 30 K temperature spread), no losses.
- **Electricity price:** ElCom 2026 (<https://www.strompreis.elcom.admin.ch>), IWB, Basel, category H4, total price per kWh including all fees, as one flat price.
- **Value of the heat:** the heat a server delivers replaces a heat pump. Value it at the electricity price ÷ 2.5 (heat pump efficiency of 2.5).

Teams report their key figures for this reference house. They are free to test other houses, tanks or prices on top.

### Open data for workloads and prices

- Power during AI inference benchmarks: MLPerf Inference results with power measurements (<https://mlcommons.org/benchmarks/inference-datacenter/>).
- Real job durations and resource requests from a large GPU cluster: Alibaba GPU cluster trace 2020 (<https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020>), as inspiration.
- Prices for computing: public on-demand and spot prices of the large cloud providers.
- Teams may also define job types themselves (runtime, power, deadline), naming the source of each number.

## Technology

No hardware and no special access needed. Teams work on their own laptops; any language, framework or AI model is allowed. At least one real workload runs on your own machine (see must-have 1); a CPU is enough, no GPU needed. Measuring more is encouraged.

## Core use case

A cold January day in Basel: a house needs about 10 kW of heat. The system checks the weather forecast, assigns AI jobs such as embeddings, transcription or image recognition to the servers in the basement, and pauses or moves lower-priority jobs once the heat storage is full. In July only hot water is needed: servers run less, jobs move to sites that need heat in summer (hotels, spas, agriculture, businesses), or heat is dumped. A dashboard shows the balance per house and year.

## Must-haves for a valid submission (all on the reference house)

1. **Workloads:** at least two job types (for example AI inference such as embeddings, reranking, image recognition or transcription) with runtime and energy per job (from your own measurements or open benchmarks), whether each can be interrupted, and its deadline. At least one job type must actually run on your machine, with measured runtime. Take its energy from a software meter or from runtime × the device's power draw, and state how you scale it to the 1 kW reference server. State how many jobs arrive per day and where that number comes from; a model that assumes unlimited jobs must say so.
2. **Scheduling:** distribute, pause or reschedule jobs across the servers according to heat demand (winter heating, summer hot water), including a simple heat storage and what happens to a job when its heat is not needed. The same scheduler code that produces the yearly balance must also control at least one real running job: it pauses and resumes it (or stops it at a checkpoint and restarts it) based on the heat signal.
3. **Balance per house and year:**
   - servers per house
   - share of total heat demand (space heating plus hot water) covered by server heat, the rest coming from a backup heater outside the model
   - heat dumped
   - utilisation (server running hours ÷ servers × 8,760)
   - missed deadlines in % of jobs
   - electricity cost and computing income
   - break-even computing price in CHF per server-hour: `(electricity cost − value of the heat actually used) ÷ server-hours sold`

   Every assumption visible, with a clear statement of when the model does not pay off.

## What success looks like for DigitalHeat

A prototype that runs real computing jobs locally and shows, in auditable numbers, that distributed servers can meet a home's heat demand across the year without destroying the profitability of the hardware.

## Business value

Turns a cost (cooling) into a value (heat). Shows how many servers a home needs, which workloads fit which season, and under which electricity and computing prices the model pays off. A basis for DigitalHeat's next conversations and decisions.

## Optional stretch goals

**Bonus Prepper Challenge:** combine solar energy, computing and thermal storage to make a home more self-sufficient. Start it only once the three must-haves work; it is not scored separately.

**Out of scope for this sprint:** feeding heat into the district heating grid. Teams may mention it as an outlook in their pitch.

## Presentation format

5 minutes pitch including a live demo, plus 3 minutes Q&A.

### Key presentation elements

Open with the key figures for the reference house: servers per house, share of heat demand covered, heat dumped, utilisation, missed deadlines and break-even computing price. Then a live demo: one January day, one July day and one interrupted job, shown on a real running process that your scheduler pauses and resumes on the heat signal.

## Prototype requirements

A working demonstrator, a list of all assumptions, and measurements or calculations that others can reproduce (code in the repository; notebooks are fine for analysis). The demonstrator runs at least one real job under the scheduler's control; a spreadsheet, slides or a simulation alone are not a valid submission.

## How the jury scores

| Criterion | Weight | What we reward |
|---|---|---|
| Transparency & reproducibility | 25% | Measurements and calculations can be traced and repeated. Every assumption is visible. |
| Feasibility | 25% | Could DigitalHeat use this as a basis for a pilot decision? The solution knows where its assumptions stop holding and says when the model does not pay off. |
| Scheduling quality & impact | 20% | On the reference house: first the share of heat demand covered at the least heat dumped, then server utilisation and missed deadlines. |
| Creativity & innovation | 20% | A fresh, practical idea for matching computing to heat. |
| Design & usability | 10% | A homeowner or an energy utility understands the result in one minute. |

## Prize

Dinner with the founders and the chance to keep working on the idea with DigitalHeat, for example as project work or an internship.

## Resources (shared by the case partner)

- [MLPerf Inference results with power measurements](https://mlcommons.org/benchmarks/inference-datacenter/)
- [Alibaba GPU cluster trace 2020](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020)
- [PDF of the case presentation](https://www.dropbox.com/scl/fi/6byhvibtqd73fmtkax6b7/DigitalHeat.pdf?rlkey=inpoz7g3kumwogq624yhx5z6y&dl=0) — local copy: [DigitalHeat-case-presentation.pdf](DigitalHeat-case-presentation.pdf), text in [case-presentation.md](case-presentation.md)
- [Bodycams and AI Application](https://www.axon.com/products) (added 21 Nov) — Axon's product page. The case page gives no explanation; we read it as an example of a real AI workload (video and audio from body cameras).
- [Data of a city home, 4 apartments](https://www.dropbox.com/scl/fi/zdz4taiy03zs6r6pf20rz/Housedata.zip?rlkey=1a7i86b1ar9t93drl5a0jmted&dl=0) (added 21 Nov) — anonymised gas and electricity data 2021–2025 and building plans of a real Basel house. Local copy and summary: [data/README.md](../data/README.md#city-house-with-four-apartments-real-data).

## Case Q&A (public thread on the case page)

- **20 Nov, 23:27, us:** Where can we download the reference-house hourly CSV (weather, heating demand, hot water)? The case says it's provided, but the case page doesn't link it.
- **21 Nov, 08:21, case partner:** "I uploaded it. It is a typical Basel City house with 4 appartments."
- **21 Nov, 10:38, us:** Thank you.

What was uploaded is the city-home data above, not the hourly profile of the reference house. See the note under [Reference house](#reference-house).
