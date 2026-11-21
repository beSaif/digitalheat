# Data

Everything here is input data for the reference house defined in the case
([docs/case-brief.md](../docs/case-brief.md#reference-house)). Nothing in this folder is a modelling result.

| File | What | Source |
|---|---|---|
| `reference_house_2025_hourly.csv` | 8,760 hourly rows: weather, heating-day flag, space-heating demand, hot water, total heat demand | Built by `scripts/build_reference_profile.py` from the raw weather below |
| `raw/openmeteo_basel_2025_hourly.csv` | Hourly weather, Basel 2025, Europe/Zurich time: `temperature_2m`, shortwave (global horizontal), direct, diffuse radiation, direct normal irradiance | [Open-Meteo historical archive](https://open-meteo.com/en/docs/historical-weather-api), 47.56 N 7.59 E, downloaded 2026-11-20 |
| `raw/openmeteo_swiss_cities_2025_hourly.json` | Hourly 2025 temperature for the 9 non-Basel cities of the dashboard's scenario fleet (Zürich, Winterthur, Bern, Genève, Lausanne, Luzern, St. Gallen, Lugano, Chur), Europe/Zurich time, default model | [Open-Meteo historical archive](https://open-meteo.com/en/docs/historical-weather-api), fetched by `scripts/build_fleet_scenario.py --download`, 2026-11-21 |
| `raw/elcom_iwb_H4_2025_2026.json` | IWB electricity tariff, category H4, 2025 and 2026, by component | [ElCom](https://www.strompreis.elcom.admin.ch/operator/624?period=2026&category=H4) GraphQL API, downloaded 2026-11-20 |
| `raw/city_house/*.csv` | Real, anonymised gas (monthly, 2021–2026) and electricity (15-minute, 2021–2025) data of a Basel house with four apartments. See [below](#city-house-with-four-apartments-real-data) | Case resource "Data of a city home, 4 apartments", downloaded 2026-11-21 |
| `raw/mlperf_inference_v6.1_summary.xlsx` | MLPerf Inference v6.1 results summary (datacenter + edge, closed + open): throughput per system and benchmark, including whisper and llama3.1-8b | [mlcommons/inference_results_v6.1](https://github.com/mlcommons/inference_results_v6.1) |

Rebuild the profile: `python3 scripts/build_reference_profile.py` (add `--download` to re-fetch the weather). Standard library only.

## Reference house profile

**Status: rebuilt from the case's formula; no official file exists.** The case says a ready-made CSV is provided, but it is not on the case page. We asked in the case Q&A on 2026-11-20. The answer on 2026-11-21 was an upload of real data from a different building (the [city house](#city-house-with-four-apartments-real-data)), so there is nothing to diff this file against.

Check against the figures the case states:

| | Ours | Case |
|---|---|---|
| Coldest hour | −5.6 °C (2025-12-31 23:00) | −5.6 °C |
| Heating days | 206 | 206 |
| Space heating per year | 26,851 kWh | about 27,000 kWh |
| Hot water per year | 4,380 kWh | 12 kWh/day |
| Total heat demand | 31,231 kWh | — |
| Peak hourly demand | 10.5 kWh (10 heating + 0.5 hot water) | about 10 kW heating |

Columns (one row per local hour):

| Column | Meaning |
|---|---|
| `time_local` | Start of hour, Europe/Zurich |
| `temperature_2m_c` | Outdoor temperature, °C |
| `shortwave_radiation_w_m2` | Global horizontal irradiance, W/m² (the case's "solar irradiance") |
| `direct_radiation_w_m2`, `diffuse_radiation_w_m2`, `direct_normal_irradiance_w_m2` | Irradiance components, W/m² (only needed for the solar stretch goal) |
| `day_mean_temperature_c` | Mean of the 24 hourly temperatures of that local day |
| `heating_day` | 1 if `day_mean_temperature_c` < 12 °C |
| `space_heating_kwh` | `max(0, 10 × (20 − T) / 25.6)` on heating days, else 0 |
| `hot_water_kwh` | 0.5 every hour (see notes) |
| `total_heat_demand_kwh` | Space heating + hot water |

Notes:

- **Hot water is spread flat over 24 hours.** The case only gives 12 kWh per day, not an hourly shape. Flat is the neutral choice; it can be changed in the script.
- **Timestamps are UTC+1 all year, not Swiss wall-clock time.** With `timezone=Europe/Zurich`, Open-Meteo applies a fixed +1 h offset and ignores daylight saving: every day has 24 rows (8,760 in total), 30 March has a "02:00" row that doesn't exist on the wall clock, and from April to October a row labelled 12:00 is 13:00 on the wall clock. Recomputed on true wall-clock days (with the 23- and 25-hour days) the result is the same: 206 heating days, 26,842 kWh. Totals are unaffected; only summer hour-of-day labels are shifted by one hour.
- **Weather model:** Open-Meteo's default (`best_match`), which for this location and year is identical to `ecmwf_ifs`. It is the only model that reproduces the case's −5.6 °C and 206 heating days (ERA5: −7.5 °C, 186 days, 23,625 kWh; ERA5-Land: −6.0 °C, 201 days, 26,476 kWh). The default could point to a different model in future, so treat the committed raw file (downloaded 2026-11-20) as the source of truth and use `--download` only to check.
- Open-Meteo snaps the coordinates to its nearest grid cell (47.557 N, 7.549 E, 247 m).

## Electricity price (ElCom 2026, IWB, Basel, H4)

**33.25 Rp/kWh = 0.3325 CHF/kWh**, the "total" the case asks for.

| Component | Rp/kWh |
|---|---|
| Network usage (Netznutzung) | 11.41 |
| Metering (Messtarif) | 1.20 |
| Energy (Energie) | 10.89 |
| Public charges (Abgaben an Gemeinwesen) | 7.44 |
| Federal grid surcharge (35 EnG) | 2.30 |
| **Total** | **33.25** |

The same price applies in Basel, Riehen and Bettingen. For comparison, 2025 was 33.856 Rp/kWh. The ElCom page does not say whether VAT is included.

Derived from the case's rule (heat valued at electricity price ÷ 2.5): **13.30 Rp per kWh of heat**.

## City house with four apartments (real data)

Added to the case resources by DigitalHeat on 2026-11-21 as "Data of a city home, 4 apartments"; in the case Q&A they call it "a typical Basel City house with 4 appartments". Source: [Housedata.zip on Dropbox](https://www.dropbox.com/scl/fi/zdz4taiy03zs6r6pf20rz/Housedata.zip?rlkey=1a7i86b1ar9t93drl5a0jmted&dl=0), downloaded 2026-11-21. Names, addresses, contract and meter numbers are replaced by placeholders (`PERSON_001`, `OBJEKT_001`, …) in the files as delivered.

**This is not the reference house.** The reference house is one household defined by a formula; this is a real building with four households. The key figures for the jury stay on the reference house. This data is for checking assumptions against reality and for the optional "other houses" test. Nothing in the repo uses it yet.

| File in `raw/city_house/` | Content |
|---|---|
| `Data_Gas_2021-2026_anonymisiert.csv` | Monthly gas bills for three metering points, January 2021 onwards: energy in kWh and cost in CHF (energy, network, charges, total). Semicolon-separated, UTF-8 with BOM, German headers |
| `Data_Strom_<year>_anonymisiert.csv` (2021–2025) | One electricity metering point, kWh per 15 minutes. Six header lines of metadata, then `Datum;Zeit;Energie;Einheit` (date `YYYYMMDD`, time `HH-MM-SS`) |
| `plans/Grund_und_Aufriss_anonymisiert.pdf`, `plans/Dachstock_anonymisiert.pdf` | Scanned building plans, 4 pages each: floor plans and elevations ("Grund und Aufriss"), and the attic ("Dachstock"). **Not in git** (20 MB, listed in `.gitignore`); get them from the Dropbox link |

### Gas

| Metering point | What the data shows | Period |
|---|---|---|
| `MESSPUNKT_004` | The building's main gas supply: 26,000 to 66,000 kWh per year, strongly seasonal, with a monthly capacity charge (rows with unit `KW`) | 2021-01 to 2025-09 |
| `MESSPUNKT_002`, `MESSPUNKT_003` | Two small supplies of 10 to 25 kWh per month plus a base fee of CHF 3.75. Too small for heating; probably gas cookers (our guess, not stated in the data) | 2021-01 to 2026-05 |

`MESSPUNKT_004`, gas in kWh:

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Jan | 9,175 | 9,655 | 2,843 | 7,019 | 7,418 |
| Feb | 7,151 | 7,216 | 2,424 | 5,069 | 6,407 |
| Mar | 7,040 | 6,966 | 2,009 | 4,744 | 5,524 |
| Apr | 5,799 | 5,239 | 1,785 | 3,774 | 3,400 |
| May | 4,095 | 2,212 | 746 | 1,490 | 2,043 |
| Jun | 1,698 | 1,793 | 569 | 1,354 | 1,439 |
| Jul | 2,863 | 1,853 | 588 | 1,399 | 1,487 |
| Aug | 2,863 | 1,853 | 588 | 1,399 | 1,487 |
| Sep | 2,966 | 2,861 | 569 | 2,077 | 2,070 |
| Oct | 5,430 | 668 | 2,408 | 2,513 | — |
| Nov | 8,426 | 2,118 | 5,370 | 6,154 | — |
| Dec | 8,811 | 2,834 | 6,292 | 7,472 | — |
| **Year** | **66,317** | **45,268** | **26,191** | **44,464** | 31,275 (9 months) |
| Total cost, CHF | 6,095 | 5,649 | 4,628 | 7,145 | 4,591 |
| Rp per kWh of gas, all in | 9.2 | 12.5 | 17.7 | 16.1 | 14.7 |

Things to know before using it:

- **These are kWh of gas, not of heat.** Heat delivered is lower by the boiler's efficiency, which the data does not give.
- **July and August are identical in every year,** so at least the summer values are meter readings split evenly over two months, not separate measurements. Treat monthly values as billing figures.
- **October 2022 to September 2023 is far below the other years** (about 17,700 kWh in those twelve months, against 44,000 to 66,000 kWh in the calendar years around it). The files do not say why. Do not average over this period without asking DigitalHeat.
- **The four apartments are not metered separately** for heat; the plans show one gas heating room in the basement.
- Summer gas use (June to August, no space heating) is about 45 to 50 kWh per day in 2024 and 2025, 60 to 80 kWh in 2021 and 2022. The case's hot-water figure for four households would be 48 kWh per day (4 × 12). The two are not directly comparable (gas in versus heat out, losses, unknown number of residents), but they are the same order of magnitude.

### Electricity

One metering point (`MESSPUNKT_001`), on the same contract account as the main gas supply:

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| kWh per year | 2,087 | 1,975 | 1,833 | 1,711 | 1,600 |
| Highest 15-minute value, kWh | 1.21 | 1.15 | 1.15 | 1.06 | 0.68 |

- **This is not the electricity of four apartments.** 1,600 to 2,100 kWh per year is less than one typical household uses. The data does not say what the meter supplies. It is roughly twice as high in winter (160 to 280 kWh per month, December to February) as in summer (65 to 170 kWh, June to August).
- **Timestamps are Swiss wall-clock time.** The day of the spring clock change has 92 rows (02:00 to 02:45 missing); the day of the autumn change has 96, not 100. Every other day has 96 rows, with no empty values. This differs from the reference-house profile, which is UTC+1 all year.
- April 2021 is unusually low (46 kWh, against 156 to 210 kWh in the neighbouring months and in other Aprils).

### Building plans

Terraced house, 8.60 m wide and 12.00 m deep, with a narrower rear wing of 8.00 m. Basement with a gas heating room ("Heizung Gas"), cellars and a laundry; the drainage note lists 4 showers, 4 WCs, 8 washbasins and 4 kitchens. Ground floor apartment: living room, two bedrooms, kitchen, bathroom. The attic plan shows a 55 m² work room. We only skimmed the scans at low resolution; heated floor area and construction year were not extracted.

## Not downloaded (linked only)

- **Alibaba GPU cluster trace 2020** — <https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020>. Several GB of job and task tables; the repo holds only headers and a download script (`data/download_data.sh`). The case lists it "as inspiration".
- **MLPerf power measurements** — the summary spreadsheet above has throughput, not power. Power results are in the per-submission folders of the results repo and in the [MLCommons results visualiser](https://mlcommons.org/benchmarks/inference-datacenter/).
- **Axon products** — <https://www.axon.com/products>, added to the case resources on 2026-11-21 as "Bodycams and AI Application". A vendor product page, no data.
- **Cloud on-demand and spot prices** — the case names "public prices of the large cloud providers" but no specific source. Not collected yet.
