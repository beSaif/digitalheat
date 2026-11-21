# digitalheat

Team **Ctrl+Free** at sprintd Basel · GreenTech Edition (20–22 Nov 2026), working on the DigitalHeat case:
*Useful Load ⇒ Useful Heat: can your computing power heat a home while doing useful work?*

- [`docs/`](docs/README.md): the case brief, DigitalHeat's slides, submission requirements, event info
- [`data/`](data/README.md): input data for the reference house (hourly heat demand, weather, electricity price)
- [`scripts/`](scripts/): `build_reference_profile.py` rebuilds the hourly profile from Open-Meteo (Python 3, standard library only); `measure_workloads.py` measures the real jobs' runtime and energy
- [`workloads/`](workloads/): the two real, interruptible jobs (embeddings, reranking) and their scaling to the 1 kW reference server; see [docs/workloads.md](docs/workloads.md)

```bash
python3 scripts/build_reference_profile.py            # rebuild data/reference_house_2025_hourly.csv
python3 scripts/build_reference_profile.py --download # re-fetch the weather first
```

### Real workloads

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements-workloads.txt
.venv/bin/python -m workloads.run embed --job-dir runs/embed-001 --items 20000   # run / resume a real job
.venv/bin/python -m workloads.catalog                                            # job types on the 1 kW reference server
.venv/bin/python scripts/measure_workloads.py --label <you>                      # re-measure (on battery, ~15 min)
.venv/bin/python scripts/test_interruption.py                                    # pause/stop/resume gives identical output
```

Models download from Hugging Face on first run (~180 MB). Measurement uses the macOS battery gauge, so it needs an Apple-silicon laptop on battery; running the jobs works anywhere. To add your machine to the team average, see [docs/measure-on-your-machine.md](docs/measure-on-your-machine.md).

### Operator dashboard

A Next.js fleet console in [`dashboard/`](dashboard/README.md): live KPIs, a Swiss fleet map and a 3D view of each site with its servers, replaying a simulated fleet of 24 houses in 10 Swiss cities over the 2025 weather. **Scenario data, not telemetry.**

```bash
python3 scripts/build_fleet_scenario.py   # regenerate dashboard/public/data (standard library, seed 11)
cd dashboard && pnpm install && pnpm dev  # http://localhost:3000
```

## AI tools

Repository set-up, data collection, analysis scripts, the dashboard and documentation were done with Claude Code. The dashboard started from the `create-next-app` template (Next.js, Tailwind).

## Step 1: House data

One command regenerates the table, the comparison, the sanity checks, the price and the plots:

```bash
pip install -r requirements.txt     # pandas, matplotlib (tested: Python 3.13, pandas 3.0.1, matplotlib 3.10.8)
python3 scripts/run_step1.py        # exits with an error if any sanity check fails
```

Every later script gets its numbers from [`src/load_data.py`](src/load_data.py), so demand is computed in one place:

```python
from src.load_data import load_house, load_price, heat_value_chf_per_kwh
house = load_house()   # 8,760 rows, one per hour, Europe/Zurich
price = load_price()   # 0.3325 CHF/kWh
```

Outputs (nothing in `data/` is modified): `outputs/house_2025_hourly.csv`, `plots/demand_week_january.png`, `plots/demand_week_july.png`.

### Assumptions and sources

| Item | Value / rule | Source |
|---|---|---|
| Weather | Open-Meteo historical archive, `latitude=47.56&longitude=7.59&start_date=2025-01-01&end_date=2025-12-31&hourly=temperature_2m,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance&timezone=Europe/Zurich&format=csv`, default model (`best_match`). Open-Meteo snaps to grid cell 47.557 N, 7.549 E, 247 m | `data/raw/openmeteo_basel_2025_hourly.csv`, downloaded 2026-11-20 (URL in `scripts/build_reference_profile.py`) |
| File time | The file header says `utc_offset_seconds=3600, GMT+1`: Open-Meteo wrote **UTC+1 all year, without summer time** (every day has 24 rows; 30 March has a `02:00` row that doesn't exist on the Swiss wall clock) | Inspected in the file |
| Timezone handling | File time − 1 h = UTC, then converted to `Europe/Zurich`. All 8,760 rows are kept; none dropped or filled. In absolute time the rows are strictly hourly | `read_weather()` |
| Local day | Swiss wall-clock calendar day. 30 Mar 2025 has 23 hours, 26 Oct 2025 has 25 hours (02:00 appears twice, +02:00 then +01:00); all other 363 days have 24 | Case brief; `add_heat_demand()` |
| Heating day | Daily mean of `temperature_2m` < 12 °C. On the two clock-change days the mean is taken over the 23 or 25 hours that day has | Case brief |
| Space heating | `max(0, 10 × (20 − T) / 25.6)` kWh per hour on heating days, else 0. 25.6 = 20 − (−5.6), coldest hour (31 Dec 2025 23:00) | Case brief |
| Hot water | 12 kWh/day spread flat: 0.5 kWh every hour (so 11.5 / 12.5 kWh on the 23- / 25-hour days; 4,380 kWh per year). The case gives no hourly shape; flat is our choice | Case brief |
| Units | One row = one hour, so a value in kWh per hour equals the average kW in that hour | — |
| Electricity price | **33.25 Rp/kWh = 0.3325 CHF/kWh**: ElCom field `total`, period 2026, operator IWB (624), municipality Basel (2701), category H4. Whether VAT is included isn't stated in the file | `data/raw/elcom_iwb_H4_2025_2026.json`, ElCom GraphQL API, downloaded 2026-11-20 |
| Heat value | 0.3325 / 2.5 = **0.1330 CHF per kWh of heat** (heat pump COP 2.5) | Case brief |

Price note: the JSON lists `gridusage` 11.414 + `energy` 10.892 + `charge` 7.443 + `aidfee` 2.300 = 32.049 Rp/kWh, which is 1.201 Rp below `total`. The ElCom web page shows a metering tariff (Messtarif) of 1.20 Rp/kWh that has no field in the API. In 2025 the listed parts do add up to `total` (33.856). We use `total`, the all-in price the case asks for.

### Results (`python3 scripts/run_step1.py`)

| Check | Result | Status |
|---|---|---|
| Rows | 8,760 | PASS |
| Space heating | 26,851 kWh (target 27,000 ± 500) | PASS |
| Heating days | 206 | PASS |
| Total demand | 31,231 kWh (target ≈ 31,400) | PASS |
| Hot water | 4,380 kWh | PASS |
| Peak / minimum | 10.50 kW (31 Dec 23:00) / 0.50 kW | PASS |
| Missing values, sorting, strictly hourly, Europe/Zurich | none / yes / yes / yes | PASS |
| July | flat 0.5 kW | PASS |

The "about 31,400 kWh" total in our task list is 27,000 + 4,380. With the exact 26,851 kWh it is 31,231 kWh.

**Comparison with `data/reference_house_2025_hourly.csv`.** This file isn't an independent answer key. The case never published its profile, so we built that file earlier with `scripts/build_reference_profile.py` from the same weather. Temperature, irradiance and hot water match on all 8,760 hours. Space heating differs on 20 hours (max 4.30 kWh in one hour; annual difference +0.47 kWh = 0.002 %). Cause: the old script defined days on the file's UTC+1 clock. From April to October that day runs 01:00 to 00:00 Swiss summer time, so the midnight hour belongs to the previous day. On 20 days near the 12 °C limit, that one hour lands in a day with a different heating flag. Recomputed with the old day definition, our code matches the file to within 0.00005 kWh (rounding). The number of heating days is 206 either way. We follow the case rule (Swiss wall-clock days).

**Plots.** Both plots use the same 0 to 11 kW axis. 13 to 19 January 2025 varies between 6.3 and 10.4 kW, highest at night and lowest in the afternoon. 14 to 20 July 2025 is flat at 0.5 kW (hot water only, no heating days in July).

## Extension: heat demand across Switzerland (map, zones, criteria)

An extension for the pitch. **The official key figures stay on the Basel reference house** (Step 1). This part never changes those numbers; the build script checks that its Basel point is identical to `load_house()`.

```bash
python3 scripts/build_swiss_map.py     # one command: downloads only what is not cached, then builds everything
open outputs/swiss_heat_map.html       # single file, works offline, makes no network calls
```

Outputs:

| File | Content |
|---|---|
| `outputs/swiss_heat_map.html` | Map: hourly, monthly or annual values, interpolated surface, climate-zone map, click panel, table of all places, dark/light mode, phone layout |
| `outputs/swiss_points_2025_stats.csv` | One row per place: location, sources, all annual numbers (A2) for both house sizings and both recovery rates |
| `outputs/swiss_points_2025_monthly.csv` | One row per place and month: mean and coldest temperature, heating days, HGT, space heating, total demand, average and peak kW, servers (average and "every day of the month"). The build checks that the 12 months add up to the annual numbers |
| `outputs/interpolation_check.csv` | Leave-one-out test of the surface method |
| [`docs/swiss_heat_analysis.md`](docs/swiss_heat_analysis.md) | One-page analysis (A5) |
| [`docs/criteria.md`](docs/criteria.md) | Cold / mild / warm classes, server rules, zones, limits (Part B) |

Code: [`src/swiss_points.py`](src/swiss_points.py) (places, geocoding, weather), [`src/swiss_stats.py`](src/swiss_stats.py) (annual numbers, zones), [`src/swiss_geo.py`](src/swiss_geo.py) (border, lakes, grid), [`scripts/build_swiss_map.py`](scripts/build_swiss_map.py) (checks, interpolation, HTML), [`scripts/swiss_map_template.html`](scripts/swiss_map_template.html) (the page). Heat demand is computed only by `add_heat_demand()` in `src/load_data.py`. The page recomputes it in the browser and checks it against the Python totals on every load; the footer shows the result.

### Assumptions and sources

| Item | Value / rule | Label | Source |
|---|---|---|---|
| Places | 93: all 26 cantonal capitals, Plateau, Jura, northern and inner Alps, Ticino and south-Grisons valleys; 206–2,114 m (GeoNames), 213–2,126 m (weather model) | our choice | list in `src/swiss_points.py` |
| Coordinates | GeoNames populated place (feature code PPL*) matched by name and canton | data | [Open-Meteo geocoding API](https://open-meteo.com/en/docs/geocoding-api), raw answers cached in `data/raw/geocoding/`, 2026-11-21 |
| Reused points | Basel = case coordinate 47.56 N 7.59 E (reference file); 15 cities reuse the 16-city map files (rounded centres, ≤ 1.4 km from GeoNames) | — | `data/raw/openmeteo_basel_2025_hourly.csv`, `data/raw/swiss_cities/` |
| Moutier | canton Jura (changed canton on 1 Jan 2026; GeoNames already lists it there) | data | GeoNames |
| Weather | Open-Meteo archive, 2025, hourly `temperature_2m`, `timezone=Europe/Zurich`, default model; 8 places per request, one-minute pauses (free tier: 600 calls/min) | data | [Open-Meteo historical API](https://open-meteo.com/en/docs/historical-weather-api), raw CSVs + request URL in `data/raw/swiss_points/`, 2026-11-21 |
| Elevation of a place | the elevation Open-Meteo used to adjust temperature (its terrain model at the point); GeoNames elevation also stored | data | both in the stats CSV |
| Heat demand | case formula, local days, heating day < 12 °C, 0.5 kWh/h hot water | case | `src/load_data.py` |
| House sizing | "case": 25.6 everywhere. "local": 20 − own coldest hour of 2025 (21.3–43.9 K) | case / our variant | brief |
| Heat recovery | 0.8 kW per server; sensitivity 0.85 kW | case | brief |
| Heating degree days | **HGT 20/12** (main): Σ (20 − daily mean) over days with mean < 12 °C. Eurostat 18/15 shown for comparison | convention | [Canton FR](https://www.fr.ch/de/energie-landwirtschaft-und-umwelt/energie/ueberwachung-des-energieverbrauchs-eines-gebaeudes), [Eurostat nrg_chdd](https://ec.europa.eu/eurostat/cache/metadata/en/nrg_chdd_esms.htm) |
| Seasons | winter = Jan–Mar + Oct–Dec 2025; summer = Apr–Sep; "every day" winter servers use Dec–Feb only | our choice | `src/swiss_stats.py` |
| Months | a day counts in the month of its local (Europe/Zurich) date; monthly map colours use one scale for all 12 months so months can be compared | our choice | `monthly_stats()` in `src/swiss_stats.py` |
| Server counts | average = mean demand ÷ recovery (needs storage within the day); "every day" = lowest daily mean ÷ recovery | derived | `src/swiss_stats.py` |
| Zones | HGT 20/12 boundaries 2,520 / 3,270 / 4,020 Kd = 4 / 5 / 6 server-years (whole numbers: our choice) | derived + assumption | [`docs/criteria.md`](docs/criteria.md) |
| Border, lakes | Natural Earth 1:10m admin-0 countries and lakes (+ Europe supplement), simplified to ~200 m | **public domain** | [naturalearthdata.com](https://www.naturalearthdata.com/about/terms-of-use/), files from [github.com/nvkelso/natural-earth-vector](https://github.com/nvkelso/natural-earth-vector), cached in `data/raw/natural_earth/` (not in git, 19 MB; re-downloaded automatically) |
| Grid | 3,879 cells of 0.03° × 0.045° (≈ 3.3 × 3.4 km) touching Switzerland | our choice | `src/swiss_geo.py` |
| Grid terrain | elevation of each cell centre | data | [Open-Meteo elevation API](https://open-meteo.com/en/docs/elevation-api) (Copernicus DEM GLO-90), cached in `data/raw/swiss_grid/` |
| Surface method | per value: least-squares line against elevation over all places + inverse-distance weighting (power 2, 8 nearest places) of the residuals; clamped to the range of the places; terrain above the highest place (2,126 m) not estimated | our choice | `interpolate()` in the build script, same code in the page |
| Surface accuracy | leave-one-out: annual mean temperature ±0.35 °C (worst 1.9 °C), HGT ±140 Kd (worst 725 Kd); plain IDW is about 4× worse | data | `outputs/interpolation_check.csv` |

Known limits: one weather year; one model grid cell per place (inversions, slopes and valley floors are smoothed); the house formula is linear and ignores sun, wind, thermal mass and occupancy; both house sizings are simplifications ([`docs/criteria.md`](docs/criteria.md#4-limits-read-before-using-these-numbers)). The 16 raw files in `data/raw/swiss_cities/` (with irradiance) come from the earlier 16-city map and are reused.

## Step 2: Scheduler

One scheduler (`scheduler/core.py`) makes the yearly balance, controls the real job and feeds the dashboard. Each hour, for each site:

1. **Heat signal:** room in the tank = capacity − charge.
2. **Heat permit:** servers = min(N, ⌊(demand + room) ÷ 0.8⌋).
3. **Deadline reserve:** looks 24 h ahead and keeps tank room for the rerank jobs that will be due.
4. **Jobs:** rerank jobs go earliest-deadline-first to the site with the most free heat; embed jobs fill the rest. A job that would miss its deadline runs anyway, and its heat is dumped.
5. **No heat:** if heat returns within 2 h, the job pauses (SIGSTOP). Otherwise it is checkpointed (SIGTERM, exit 75) and goes back to the queue, maybe to another site.
6. **Heat balance:** heat = 0.8 kW per running server. The tank serves demand first; any heat above capacity is dumped.

```bash
python3 -m scheduler.balance                 # reference house, 2025
python3 -m scheduler.balance --fleet         # house + hospital + spa
python3 -m scheduler.balance --year 2023     # any year 1950–2025 (Open-Meteo weather)
python3 -m scheduler.balance --sweep 1-12    # servers vs coverage and price
python3 -m scheduler.live --fleet            # the scheduler runs a real embed job: pause/resume/checkpoint
python3 -m scheduler.pricing                 # price of one server-hour and one job vs AWS
python3 -m scheduler.assumptions --md        # regenerate docs/assumptions.md
python3 -m unittest tests.test_scheduler
```

The balance also prints computing income, profit, and where the model stops paying off (price, utilisation, electricity, server cost). Prices and their sources: [`data/prices_2026.json`](data/prices_2026.json). Every assumption: [`docs/assumptions.md`](docs/assumptions.md).

Data: workload catalog (embed 0.81 server-h, due 48 h; rerank 0.92 server-h, due 4 h), reference house 2025, Basel city-house gas bills (`scripts/calibrate_city_house.py`, R² 0.93), ElCom 2026 price 0.3325 CHF/kWh, and Open-Meteo hourly weather.

**Beyond the reference house** (all off by default; the key figures above do not change):

- Two input signals: heat (demand, tank, and the site's supply temperature: above the 60 °C server outlet, no server heat) and redundancy (copies of a job never share a site).
- New sites: family home (4–5 people), office (office hours), pharma lab (24/7 reheat + shifts), with BDEW daily profiles.
- New jobs: `sim` (simulations, due in 120 days, wait for winter) and `twin` (redundancy tier, 2–4 copies on different sites).
- Options: `--partial` (servers at 30–100 % power, on 24/7), `--drycooler KW --cool-fill` (outdoor dry cooler, with its fan power), `--outage SITE:DAY:HOURS:START`.

```bash
python3 -m scheduler.balance --scenario services --monthly              # homes, office, pharma, hospital, spa
python3 -m scheduler.balance --scenario services --drycooler 4 --cool-fill
python3 scripts/site_studies.py      # daily curves, household size, summer options, seasons, outages
python3 scripts/business_case.py     # service prices vs AWS/Google, homeowner offer, billing, capex/opex, payback
```

Write-up: [docs/business-model.md](docs/business-model.md) (services, no hardware rental, pricing, redundancy tier, homeowner offer, billing, customers, investor view, pitch order). Sources: [research_notes/](research_notes/), inputs: [data/business_assumptions.json](data/business_assumptions.json).
