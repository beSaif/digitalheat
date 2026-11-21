# Criteria: cold, mild and warm, and how many servers a house can take (Part B)

Status: **proposal for team review.** Every number below comes either from the case formula
(**derived**) or from a choice we made (**assumption**). Nothing here is a building-physics fact.
The numbers are reproduced by `python3 scripts/build_swiss_map.py` and the arithmetic block at the end.

## 1. The two numbers everything follows from (derived)

Case formula, per hour on a heating day: space heating = 10 kW × (20 − T) / 25.6, plus 0.5 kW hot water.
One server gives 0.8 kW of usable heat (case; 0.85 kW in the sensitivity run).

| | Value | How |
|---|---|---|
| Extra heat per degree colder | **0.39 kW per °C** | 10 / 25.6 |
| Temperature step that "adds one server" | **2.05 °C** | 0.8 / 0.390625 |
| Hot water alone | 0.5 kW = **0.63 server** | 12 kWh / 24 h / 0.8 |
| One server running 24 h | **19.2 kWh/day** | 0.8 × 24 (same as the case brief) |
| Tank, 35 kWh | **43.75 server-hours** of heat | 35 / 0.8 |
| Space heating per year vs. heating degree days | **9.375 kWh per Kd** | 24 × 10 / 25.6. Checked on all 93 places: 9.375–9.377 |

**Your starting reference values check out, with one detail:** they are *space heating only*.
With hot water added (+0.5 kW, +0.63 server), the house absorbs:

| Hour temperature | Space heating | + hot water | Servers at 80 % | Servers at 85 % |
|---|---|---|---|---|
| 20 °C | 0 kW | 0.50 kW | 0.63 | 0.59 |
| 12 °C | 3.13 kW (3.9 servers) | 3.63 kW | 4.53 | 4.26 |
| 5 °C | 5.86 kW (7.3 servers) | 6.36 kW | 7.95 | 7.48 |
| 0 °C | 7.81 kW (9.8 servers) | 8.31 kW | 10.39 | 9.78 |
| −5.6 °C | 10.00 kW (12.5 servers) | 10.50 kW | 13.13 | 12.35 |

(On a non-heating day the space-heating part is 0, whatever the hour's temperature.)

## 2. Classes

### 2a. Hourly temperature (on a heating day)

| Class | Range | Heat demand | Servers absorbed (80 %) | Boundary |
|---|---|---|---|---|
| **Warm** | T ≥ 12 °C | 0.5–3.6 kW | 0.6–4.5 | 12 °C: **derived** from the case's heating limit (a daily rule; using it for single hours is an **assumption**). 20 °C, where space heating reaches 0: **derived** |
| **Mild** | 0 °C ≤ T < 12 °C | 3.6–8.3 kW | 4.5–10.4 | 0 °C: **assumption** (a round, easy-to-explain split where demand reaches 78 % of the design power) |
| **Cold** | T < 0 °C | > 8.3 kW | > 10.4 | 0 °C as above |
| ↳ *beyond design* | T < −5.6 °C | > 10.5 kW | > 13.1 | −5.6 °C: **derived** (the case's design hour). Below it, a real 10 kW heating system would already be at its limit |

### 2b. Daily mean temperature

| Class | Range | Heat per day | Server-days absorbed (÷ 19.2 kWh) | Boundary |
|---|---|---|---|---|
| **Warm day** | mean ≥ 12 °C | 12 kWh (hot water only) | 0.63 | **derived** (the case's heating-day rule) |
| **Mild day** | 0 °C ≤ mean < 12 °C | about 87–200 kWh | about 4.5–10.4 | 0 °C: **assumption** (same split as hourly) |
| **Cold day** | mean < 0 °C | more than about 200 kWh | more than about 10.4 | as above |

Daily heat ≈ 9.375 × (20 − mean) + 12 kWh (**derived**; exact unless some hours of a heating day are above 20 °C).

### 2c. Annual climate zone (from heating degree days HGT 20/12)

We use **HGT 20/12**: the sum over days with a mean below 12 °C of (20 °C − daily mean). It uses the same
12 °C limit as the case. Sources: [Canton of Fribourg, definition of Heizgradtage](https://www.fr.ch/de/energie-landwirtschaft-und-umwelt/energie/ueberwachung-des-energieverbrauchs-eines-gebaeudes),
[energiesparhaus.at, HGT 20/12](https://www.energiesparhaus.at/fachbegriffe/hgt.htm). A Basel ordinance refers to
SIA 381/3 "Heizgradtage der Schweiz" ([gesetzessammlung.bs.ch](https://www.gesetzessammlung.bs.ch/frontend/annex_document_dictionaries/190));
we could not read the standard itself. We also report Eurostat's 18/15 convention for comparison
([Eurostat nrg_chdd metadata](https://ec.europa.eu/eurostat/cache/metadata/en/nrg_chdd_esms.htm)).
Our daily mean is the mean of 24 hourly values, which can differ slightly from Tmin/Tmax-based means.

The boundaries are **derived** from "server-years": how many servers' heat a reference house (case sizing)
could absorb over a whole year *if heat could be stored perfectly*. One server = 0.8 × 8,760 = 7,008 kWh/year;
the house needs ≈ 9.375 × HGT + 4,380 kWh. Choosing **whole** server-years (4, 5, 6) as boundaries is an **assumption**.

| Zone | HGT 20/12 (Kd) | Annual heat (case sizing) | Server-years | Places (of 93) | Examples |
|---|---|---|---|---|---|
| **Warm** | < 2,520 | < 28,000 kWh | < 4 | 8 | Locarno, Lugano, Bellinzona, Montreux |
| **Mild** | 2,520–3,270 | 28,000–35,000 kWh | 4–5 | 38 | Basel, Genève, Zürich, Lausanne, Sion, Chur |
| **Cold** | 3,270–4,020 | 35,000–42,000 kWh | 5–6 | 21 | Bern, St. Gallen, Fribourg, La Chaux-de-Fonds |
| **Very cold** | ≥ 4,020 | > 42,000 kWh | > 6 | 26 | Davos, Zermatt, St. Moritz, Juf, La Brévine |

The full list per place is in `outputs/swiss_points_2025_stats.csv` (column `zone`), and in the map ("Whole year 2025" → "Climate zone").

**Warning:** server-years are an upper bound. They assume heat made in July could warm a house in January.
The case tank holds 35 kWh, under 2 days of summer hot water, so in reality the summer limits the year
(see section 3).

## 3. What each class means for servers and scheduling

"N" is the number of servers installed in the house. Choosing N is the team's design decision (case brief);
these rules hold for any N.

| Class | Servers the house can absorb | Risk of dumping heat | Suggested scheduling behaviour |
|---|---|---|---|
| Cold hour / cold day | > 10.4 (> 13.1 beyond design) | **None** if N ≤ 10 | **Run all.** The backup heater covers what the servers can't. Highest-priority jobs first; this is when compute is "free heat" |
| Mild hour / mild day | 4.5–10.4 | **Medium**, if N is above what the hour absorbs | **Run partly:** run ⌊demand / 0.8⌋ servers. Charge the tank ahead of a colder night (up to 43.75 server-hours). Pause or move low-priority jobs once the tank is full |
| Warm hour / warm day | 0.6–4.5 (0.6 above 20 °C or on non-heating days) | **High** | **Pause most servers.** Hot water allows one server for about 15 h a day (12 kWh ÷ 0.8 kW), or that time spread over several servers. Move jobs to sites with summer heat demand (Part C), or dump heat and say so in the balance |

Derived consequences (from the stats file, case sizing, 80 %):

- **In summer (April–September) a Plateau house absorbs about 1.6 servers on average** (Basel 1.5, Zürich 1.7). The minimum is 0.63, hot water only.
  In winter (Oct–Mar) it absorbs about 8.
  So a fleet sized for winter is mostly idle or dumping heat in summer. This holds in every zone except the high Alps.
- **In the very-cold zone the summer is no longer "hot water only".** Mean Apr–Sep absorption reaches about 4.3 servers in Davos and 7.0 in St. Moritz,
  because there are 109 and 175 heating days between April and September.

## 4. Limits (read before using these numbers)

What the case simplifies (fine for comparing places, **not** a building model):

- **Linear formula.** Real heat loss is roughly linear in the indoor–outdoor difference, but the formula ignores
  **sun on windows** (solar gains), **wind**, **thermal mass** (a building reacts hours later), **night setback**
  and **occupancy** (people and appliances heat too).
- **Insulation.** One U-value for every place. "Same as Basel (25.6)" puts a Basel-insulated house in St. Moritz
  (peak 16.2 kW); "sized for local coldest hour" assumes houses everywhere are built to reach exactly 10 kW at their own coldest hour.
  Real Swiss houses lie somewhere between. The two options give annual space heating that differs by a factor of **0.58 to 1.20**
  depending on the place (`outputs/swiss_points_2025_stats.csv`, columns `space_kwh_case` and `space_kwh_local`).
  So the choice matters as much as the climate does.
- **Coldest hour is a fragile design point.** The local variant uses one single hour (e.g. Ilanz −17.2 °C, Lugano −1.3 °C).
  Real design temperatures come from long-term statistics (SIA 2028 climate data), not from one year.
- **Hot water is flat and the same everywhere** (12 kWh/day). In reality it depends on people, habits and the season.
  Altitude does not change the energy needed much (cold water inlet temperature does, slightly). This is **not** modelled.
- **One year (2025).** Another year shifts every number; 2025 is not a long-term mean.
- **One weather grid cell per place** (Open-Meteo's model cell, adjusted for elevation). Valleys with cold-air pools
  (inversions) are smoothed out.

What would need a real building model:
- Hourly *shape* of demand (morning peaks, setback), solar gains, thermal mass, and whether the house's
  radiators work at the low supply temperatures servers can deliver (water-cooled servers typically give 40–60 °C;
  this is an **assumption to be checked in Part C**).

### Bigger buildings: the formula must be scaled

The case formula describes **one single-family house (10 kW peak, 12 kWh hot water/day)**.
For other buildings, keep the shape and scale both parts:

  demand(T) = P_design × (20 − T) / (20 − T_design) + hot water per day / 24

| Building | P_design | Hot water | Source / status |
|---|---|---|---|
| Reference house | 10 kW at −5.6 °C | 12 kWh/day | case |
| City house with 4 apartments (our repo data) | not known | not known | Gas bills show 26,000–66,000 kWh **of gas** per year (`data/README.md`). With an **assumed** 90 % boiler efficiency that is roughly 23,000–60,000 kWh of heat, so up to about 2 reference houses. Peak power cannot be read from monthly bills |
| Hotel, swimming pool, hospital | much higher, and **summer** demand (pools, laundry, kitchens) | much higher | **to be sourced in Part C**; we don't invent values |

A large user with year-round hot-water or pool demand changes the picture more than any climate zone does.
It can take servers in summer, when houses can't. That is why Part C looks for such hosts.

## 5. Reproduce the arithmetic

```bash
python3 -c "
P,S,HW=10,25.6,0.5
for T in [20,12,5,0,-5.6]:
    sp=max(0,P*(20-T)/S); print(T, round(sp,3), round(sp/0.8,3), round(sp+HW,3), round((sp+HW)/0.8,3), round((sp+HW)/0.85,3))
for N in [4,5,6]: print(N, 'server-years -> HGT', round((N*0.8*8760-4380)/(24*P/S)))
"
```
