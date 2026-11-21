# Heat demand of the reference house across Switzerland, 2025 (Part A5)

Data: `outputs/swiss_points_2025_stats.csv` (93 places, rebuilt by `python3 scripts/build_swiss_map.py`).
Unless noted: the same house everywhere (case constant 25.6), 80 % heat recovery, weather 2025.
**Data** = read directly from that file. **Inference** = our interpretation, not shown by the data.
The official key figures stay on the Basel reference house; this is an extension for the pitch.

**1. Highest and lowest (data).** The mildest place is **Locarno** (213 m): 18,316 kWh of space heating, 152 heating days,
HGT 20/12 = 1,953 Kd. The coldest is **Juf** (2,126 m): 64,396 kWh, 347 heating days, 6,869 Kd. That is **3.5 times** as much heat for the same house.
Basel, the reference house (26,851 kWh, 2,864 Kd), ranks **16th mildest of 93**. The case's house therefore sits on the mild side of Switzerland.

**2. Elevation drives most of it (data).** A straight-line fit over all 93 places gives:
**+215 Kd of heating degree days per 100 m** (R² = 0.92), which is **+2,017 kWh of space heating per 100 m** and **+8.8 heating days per 100 m**.
Mean temperature falls by **0.59 °C per 100 m** (R² = 0.93).
Below 800 m, elevation explains only about **half** of the differences (R² = 0.48 for HGT).
At low altitude, *where* a place is matters as much as *how high* it is.

**3. The north–south contrast is largest in the lowlands (data).**
- After removing the elevation trend, places **south of the Alps** need on average **327 Kd less** than their altitude predicts (about 3,070 kWh less).
  **Plateau** places need **256 Kd more**.
- Below 450 m, the 7 southern places have a median of **2,082 Kd / 19,521 kWh**. The 18 Plateau places have **3,111 Kd / 29,163 kWh**, which is **49 % more**.
  Their 138 m higher median elevation explains only about 300 of the 1,029 Kd gap.
- Pairs of places:

  | Pair | Elevation | Space heating | Difference |
  |---|---|---|---|
  | **Lugano** vs **Zürich** | 270 vs 422 m | 18,801 vs 30,243 kWh | **+61 %** for Zürich |
  | Sion (inner-alpine valley) vs Bern | 512 vs 511 m | 26,357 vs 32,125 kWh | +22 % for Bern |
  | Airolo vs Andermatt (across the Gotthard) | 1,174 vs 1,440 m | 41,351 vs 46,683 kWh | +13 % for Andermatt |

  The Gotthard pair's gap (568 Kd) is fully explained by its 266 m difference in elevation. **In the mountains, altitude dominates; in the lowlands, the side of the Alps does.**
- *Inference:* winter fog and cold-air pools on the Plateau and sunnier, more sheltered southern lowlands are plausible reasons. Our data does not test them.

**4. What it means for server counts (data, medians per region; servers whose heat one house could absorb).**

| Region | Places | Median elevation | Winter average (Oct–Mar) | Summer average (Apr–Sep) | Winter ÷ summer |
|---|---|---|---|---|---|
| South | 11 | 306 m | 6.3 | 0.9 | 7× |
| Plateau | 26 | 432 m | 8.0 | 1.6 | 5× |
| Jura | 11 | 924 m | 8.6 | 2.8 | 3× |
| Northern Alps | 19 | 779 m | 8.7 | 2.2 | 4× |
| Inner Alps | 26 | 1,458 m | 10.3 | 3.8 | 2.7× |

- **Peak** demand ranges from 8.8 kW (Lugano, 11 servers) to 17.6 kW (Juf, 22 servers).
- **Summer is the bottleneck almost everywhere.** In a southern or Plateau house, a fleet sized for winter would absorb only one fifth to one seventh as much heat in summer.
- Only in the high Alps does the house keep absorbing several servers in summer.
  St. Moritz averages 7.0 servers April–September because 175 of its 357 heating days fall in those months.
- *Inference:* for keeping servers busy all year, alpine resorts and buildings with year-round hot water (Part C) are more promising hosts than lowland homes.
- **Sensitivity:** at 85 % recovery every server count drops by about 6 % (Basel winter: 7.41 → 6.98).

**5. The house model matters as much as the climate (data).**
- Sizing each house for its own coldest hour (peak 10 kW everywhere) instead of the Basel constant changes annual space heating by a factor of **0.58 (Juf) to 1.20 (Lugano)**.
- The national range shrinks from 18,316–64,396 kWh to **17,097–39,495 kWh**.
- Any statement like "St. Moritz needs 3.5× more heat" must say which house it assumes.

**6. How sure are we?**
- **The dots (computed places):** exactly as certain as the case formula and Open-Meteo's 2025 weather. The Basel dot reproduces the reference house exactly (206 heating days, 26,851 kWh).
- **The colour surface between the dots** is interpolated: elevation trend plus inverse-distance weighting. In a leave-one-out test, each place was predicted from the other 92:

  | Value | Mean error | Worst error |
  |---|---|---|
  | Annual mean temperature | 0.35 °C | 1.9 °C (Zermatt) |
  | Heating degree days | 140 Kd (about 1,300 kWh) | 725 Kd (Vicosoprano) |

  Plain inverse-distance weighting without the elevation trend would be about **4 times worse**.
- **Terrain above 2,126 m** (the highest place) is not estimated.
