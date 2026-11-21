# DigitalHeat business case (generated)

`python3 scripts/business_case.py`. Inputs and sources: `data/prices_2026.json` (shared with the balance and the dashboard: exchange rate, AWS server-hour prices, Titan/Cohere, hardware) and `data/business_assumptions.json` (everything else). Physics: the scheduler's yearly balance (Basel 2025). Prices in CHF; USD converted at 0.84 CHF/USD. Every number below is reproducible; the ones marked *assumption* are ours.

## 1. Service catalogue and prices

Our price = the AWS list price for the same managed service × (1 + premium); Google shown for comparison. Revenue per server-hour = our price × units one 1 kW reference server does in an hour.

| Service | Unit | AWS (CHF) | Google (CHF) | Premium | Our price (CHF) | Units per server-h | Revenue per server-h (CHF) |
|---|---|---|---|---|---|---|---|
| Local embeddings / RAG indexing | 1M tokens | 0.0168 | 0.1260 | +25 % | 0.0210 | 2,946 | 61.86 |
| Search reranking | 1,000 queries (100 docs each) | 1.6800 | 0.8400 | +25 % | 2.1000 | 55 | 114.57 |
| Image tagging | 1,000 images | 1.0080 | 1.2600 | +25 % | 1.2600 | 1,000 | 1,260.00 |
| People counting (video) | video minute | 0.1008 | 0.0840 | +25 % | 0.1260 | 6,000 | 756.00 |
| Transcription | audio minute | 0.0050 | 0.0134 | +25 % | 0.0063 | 3,000 | 18.90 |
| Simulations (CFD, molecular dynamics, Monte Carlo) | c7a.48xlarge-hour (same chips as our server) | 9.4450 | – | +25 % | 11.8062 | 1 | 11.81 |
| Video compression (HD) | output minute | 0.0143 | 0.0252 | +25 % | 0.0179 | 600 | 10.71 |

Managed-service prices per unit are far above the cost of the electricity behind them (0.33 CHF per server-hour), so price is not the constraint: how many units customers buy is. The investor view below therefore uses the much lower raw-compute comparator (AWS spot) as its base case.

Raw-compute comparators for one 1 kW reference server (CHF per server-hour): spot parity **2.74**, spot + premium (base case) **3.42**, on-demand parity **9.45**, on-demand + premium **11.81**.

## 2. Redundancy tier

Price of a job run on r sites = base × (1 + 0.5 × (r − 1)), not r ×. AWS charges 2× for a Multi-AZ database, so two copies with us cost 25 % less than AWS's redundancy. Base price 3.42 CHF/server-h. The extra copies run on server-hours the heat permit allows anyway; while capacity is unsold (30 % in the base case, more in winter), they are almost pure margin.

| Copies | Price × | Revenue per job-hour (CHF) | Server-h used | Extra margin, spare capacity | Extra margin, sold out |
|---|---|---|---|---|---|
| 1 | 1.0 | 3.42 | 1 | +0.00 | +0.00 |
| 2 | 1.5 | 5.13 | 2 | +1.71 | -1.71 |
| 3 | 2.0 | 6.84 | 3 | +3.42 | -3.42 |
| 4 | 2.5 | 8.55 | 4 | +5.13 | -5.13 |

So: sell the twin tier while there is spare capacity, and raise the markup (or stop selling it) once the fleet is sold out.


## 3. Homeowner offer (reference house)

Heat pump running cost = electricity ÷ COP = 0.3325 ÷ 2.5 = **0.1330 CHF per kWh of heat**. Server heat used: 18,123 kWh/year; server electricity: 22,654 kWh/year.

| Heat price | CHF/kWh heat | Host pays /yr | Host saves /yr vs heat pump | Host's share of the servers' power | DigitalHeat refunds /yr |
|---|---|---|---|---|---|
| same as heat pump | 0.1330 | 2,410 | 0 | 32 % | 5,122 |
| 30 % below heat pump | 0.0931 | 1,687 | 723 | 22 % | 5,845 |
| 50 % below heat pump | 0.0665 | 1,205 | 1,205 | 16 % | 6,327 |
| free heat | 0.0000 | 0 | 2,410 | 0 % | 7,532 |

Case owner's example, heating bill 1,500 CHF/year: 30 % off saves 450/yr = **4,500 CHF in 10 years**; 50 % off saves 750/yr = **7,500 CHF in 10 years**.

Check of "the host pays at least 50 % of the servers' power": that means 0.208 CHF per kWh of heat, **1.56 × the heat pump's running cost**. A home would pay more than with a heat pump, so at household tariffs the host's share has to follow from the heat discount (16-22 %), not from a fixed 50 %.

## 4. Billing flow

1. The host's own meter pays all electricity, servers included (the meter belongs to the house).
2. A sub-meter on the server rack measures the servers' kWh; a heat meter measures the heat delivered.
3. Monthly, DigitalHeat refunds: server kWh × tariff − heat kWh × agreed heat price.
4. Net for the host: they pay the heat price for the heat they used, nothing for the computing.

## 5. Investor view

Capex per server (CHF):

| Item | CHF |
|---|---|
| server: 2x EPYC 9654, 512 GB DDR5, water cooling (prices_2026.json) | 25,000 |
| site install (tank, plumbing, controls, network) per server | 2,000 |
| **total** | **27,000** |

Annual cash flows per server at the base-case price (3.42 CHF/server-h), 70 % of running server-hours sold, heat 30 % below a heat pump:

| Fleet | Server-h run | Sold | Revenue | Heat income | Electricity | Opex | EBITDA | Payback (yr) | Break-even price CHF/server-h |
|---|---|---|---|---|---|---|---|---|---|
| reference house | 5,664 | 3,964 | 12,203 | 422 | 1,883 | 3,600 | 7,141 | 4.1 | 3.04 |
| services fleet | 7,239 | 5,067 | 15,598 | 539 | 2,407 | 3,200 | 10,530 | 2.5 | 2.28 |
| services fleet + dry cooler | 8,483 | 5,938 | 18,276 | 539 | 2,827 | 3,224 | 12,765 | 2.1 | 2.04 |

Payback (years) by price and share of server-hours sold, services fleet:

| Price CHF/server-h | 25 % sold | 50 % sold | 75 % sold | 100 % sold |
|---|---|---|---|---|
| 0.50 | never | never | never | never |
| 1.00 | never | never | never | 18.5 |
| 1.50 | never | never | 11.8 | 5.7 |
| 2.00 | never | 18.5 | 5.7 | 3.4 |
| 2.74 | never | 6.9 | 3.2 | 2.1 |
| 3.00 | never | 5.7 | 2.8 | 1.9 |
| 3.42 | 53.1 | 4.4 | 2.3 | 1.6 |
| 5.00 | 8.7 | 2.4 | 1.4 | 1.0 |
| 9.45 | 2.6 | 1.0 | 0.7 | 0.5 |
| 11.81 | 1.9 | 0.8 | 0.5 | 0.4 |

RAM price sensitivity (services fleet, base price):

| RAM price | RAM per server (CHF) | Capex per server | Payback (yr) | Break-even CHF/server-h |
|---|---|---|---|---|
| early 2025 | 2,519 | 18,722 | 1.6 | 1.76 |
| 2026 contract (base) | 10,511 | 26,714 | 2.5 | 2.28 |
| retail Nov 2026 | 16,973 | 33,176 | 3.4 | 2.71 |

Case owner's example: a friend pays USD 12,000/yr (CHF 10,080) on AWS for simulations = 1,067 server-hours on our reference server = 0.15 of one server running 80 % of the year. At AWS + 25 % he would pay CHF 12,600/yr; at our base-case rate CHF 3,650/yr. One reference house (4 servers, 70 % sold) needs about 15 such customers.

Rollout of 1,000 servers in services-type sites: capex 26.7 M CHF, revenue 15.6 M CHF/yr, EBITDA 10.5 M CHF/yr, payback 2.5 years, NPV over 5 years at 8 % = 15.3 M CHF.

**When it does not pay off:** below the break-even price per server-hour in the table, or when less than the break-even share of server-hours is sold (demand, not heat, is the risk), or when the heat is given away free (heat income lost, and waste: windows open at 26 °C). RAM at today's prices is the largest single capex item; see the sensitivity in docs/business-model.md.
