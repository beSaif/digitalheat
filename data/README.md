# Data

Everything here is input data for the reference house defined in the case
([docs/case-brief.md](../docs/case-brief.md#reference-house)). Nothing in this folder is a modelling result.

| File | What | Source |
|---|---|---|
| `reference_house_2025_hourly.csv` | 8,760 hourly rows: weather, heating-day flag, space-heating demand, hot water, total heat demand | Built by `scripts/build_reference_profile.py` from the raw weather below |
| `raw/openmeteo_basel_2025_hourly.csv` | Hourly weather, Basel 2025, Europe/Zurich time: `temperature_2m`, shortwave (global horizontal), direct, diffuse radiation, direct normal irradiance | [Open-Meteo historical archive](https://open-meteo.com/en/docs/historical-weather-api), 47.56 N 7.59 E, downloaded 2026-11-20 |
| `raw/elcom_iwb_H4_2025_2026.json` | IWB electricity tariff, category H4, 2025 and 2026, by component | [ElCom](https://www.strompreis.elcom.admin.ch/operator/624?period=2026&category=H4) GraphQL API, downloaded 2026-11-20 |
| `raw/mlperf_inference_v6.1_summary.xlsx` | MLPerf Inference v6.1 results summary (datacenter + edge, closed + open): throughput per system and benchmark, including whisper and llama3.1-8b | [mlcommons/inference_results_v6.1](https://github.com/mlcommons/inference_results_v6.1) |

Rebuild the profile: `python3 scripts/build_reference_profile.py` (add `--download` to re-fetch the weather). Standard library only.

## Reference house profile

**Status: stand-in.** The case says a ready-made CSV is provided, but it was not linked on the case page. We asked in the case Q&A on 2026-11-20. If DigitalHeat publishes theirs, diff it against this file and switch to theirs.

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

## Not downloaded (linked only)

- **Alibaba GPU cluster trace 2020** — <https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020>. Several GB of job and task tables; the repo holds only headers and a download script (`data/download_data.sh`). The case lists it "as inspiration".
- **MLPerf power measurements** — the summary spreadsheet above has throughput, not power. Power results are in the per-submission folders of the results repo and in the [MLCommons results visualiser](https://mlcommons.org/benchmarks/inference-datacenter/).
- **Cloud on-demand and spot prices** — the case names "public prices of the large cloud providers" but no specific source. Not collected yet.
