# Pilot estimator for digitalheat.ch/#waerme

A homeowner-facing extension of the DigitalHeat website: **«Spart mein Haus Geld und CO₂?»** opens a calculator under the «Ich brauche Wärme» card. «Pilotstandort werden» stays as the follow-up action. All customer-facing copy is in Swiss Standard German. The calculation runs in the browser, and nothing is sent anywhere.

```bash
python3 scripts/build_estimator_data.py        # rebuild website/rechner/data/ from cached raw files (standard library)
node website/rechner/tests/validate.mjs        # 38 checks; exits non-zero on failure
cd website && python3 -m http.server 8765      # open http://localhost:8765/#rechner (ES modules need http, not file://)
```

## What is in this folder

| Path | Content |
|---|---|
| `index.html`, `styles.css`, `brand.css`, `script.js` | Copy of the live digitalheat.ch page (2026-11-21). The site's CSS and JS are unchanged. In `index.html`: the estimator section `#rechner` sits after `#kunden`, the `#waerme` card has the new entry button, two lines include `rechner/`, and images, video and legal pages point to `https://digitalheat.ch/…`, so DigitalHeat's assets are not copied into this repo |
| `rechner/model.js` | The calculation engine: pure functions, no DOM. The page and the tests import the same file |
| `rechner/app.js` | Page logic: form, postcode search, shared Winter/Sommer toggle, results, chart, economics, CO₂ |
| `rechner/rechner.css` | Styles. Uses the site's tokens (light sections, #101214 ink, 2px corners, teal focus) |
| `rechner/data/` | `points.json` (93 weather points, reference climate, terrain grid), `plz.json` (5,717 postcode rows), `weather/<id>.json` (8,760 hourly temperatures each, loaded on demand) |
| `rechner/tests/validate.mjs` | Validation (see below) |

**To put it on digitalheat.ch:** copy `rechner/` next to the site's `index.html`, paste the `<section id="rechner">` block after `#kunden`, replace the `#waerme` card's button with the `card-actions` block, and add the two `<link>`/`<script type="module">` lines. Bump the `?v=` query when files change, because browsers cache ES modules.

## How it calculates

1. **Location → weather.** Swiss postcode or municipality (swisstopo, Amtliches Ortschaftenverzeichnis), or latitude/longitude. The engine picks the nearest of 93 supported weather points (Open-Meteo, hourly 2025), counting 100 m of height difference like 20 km. If the house's terrain height (Copernicus DEM grid) differs from the point's by ≥ 100 m, temperatures are shifted by 0.65 °C per 100 m. The page always names the weather point and its distance.
2. **Building demand.** This is the case formula, generalised: space heating = UA × max(0, 20 °C − T) in every hour of a heating day (daily mean < 12 °C, the file's 24-row day, as in the reference CSV). UA comes from one of three sources:
   - **Reference house:** 10 kW / 25.6 K = 390.6 W/K.
   - **Area × building class:** typical heating demand per GEAK envelope class (Kanton Solothurn, «Gebäude erneuern – Energieverbrauch halbieren»: A–B ≤ 50, C ≤ 75, D ≤ 100, E ≤ 125, F ≤ 150, G > 150 kWh/m²a). This value applies in the reference climate, the median HGT 20/12 of the 26 Plateau places in 2025 (3,127 Kd), so UA = q × A ÷ (24 × HGT_ref).
   - **Bill calibration:** purchased energy × seasonal efficiency (or useful heat as metered), minus the hot-water estimate if the bill includes it, divided by the location's heating degree-hours.
3. **Hot water.** Residents × 3 kWh/day (the case's 12 kWh/day for four people), flat over 24 hours.
4. **Hourly dispatch over 8,760 h.** Each active server draws 1 kW and delivers 0.8 kW of recoverable heat. Computing is available 95% of each hour (our assumption, editable on the page). Recovered heat meets current demand first; surplus charges the 35 kWh tank; the tank discharges when needed; the existing heater covers the rest. In the default heat-led mode, servers run only as much as demand plus free tank space can absorb, so dumped heat is 0. «Dauerbetrieb» runs all available servers and dumps what a full tank cannot take. Both modes track dumped heat. Servers may run part-hours.
5. **Sizing.** Fleets of 1–20 servers are tested, and the page recommends the smallest one whose annual coverage reaches the chosen target (80% by default, for the demo). If none reaches it, the page shows the best achieved coverage and the backup heat that remains.
6. **Range.** The same fleet is rerun at the low and high end of the building assumptions (class band, or ±10–25% with a bill) and ±25% hot water. The range is widest when everything is a default.
7. **Money.**
   - Server electricity = server-hours × kW × the «Strompreis der Server» slider (default 33.25 Rp./kWh, ElCom 2026 IWB H4).
   - Operator break-even = (electricity − heat revenue) ÷ server-hours, where heat revenue uses the proposed heat price, or the case rule 33.25 ÷ 2.5 = 13.30 Rp./kWh if none is given.
   - Household savings appear only with a heating system, its tariff and a proposed heat price: served heat × (tariff ÷ efficiency − heat price).
8. **CO₂.** This appears only when the heating system is known. Factors are KBOB/ecobau list 2022, V9.0 (`data/raw/kbob/`): oil 0.324, gas 0.230, pellets 0.0277, CH consumer electricity mix 0.125, average Swiss district heating 0.0658 kg CO₂e per kWh of final energy. The user chooses one of two accounting rules, and the page states which one applies:
   - *Elsewhere:* the computing would have run in a data centre anyway, so its electricity is not charged to the house.
   - *Additional:* server electricity × 0.125 is subtracted.

## Validation (`node website/rechner/tests/validate.mjs`)

| Check | Result |
|---|---|
| Basel benchmark: engine vs `data/reference_house_2025_hourly.csv` | all 8,760 hours within 5·10⁻⁵ kWh (CSV rounding); 206 heating days; 26,850.5 / 31,230.5 kWh |
| Cross-check vs `analysis/baseline_sweep.py` (independent Python, whole servers) | coverage and server-hours identical for N = 1…11; dumped kWh identical in always-on mode |
| Tank capacity | state of charge within [0, capacity] in 960 runs (tank 0/10/35/200 kWh, both modes, 1–20 servers, 3 availabilities); the 35 kWh tank reaches exactly 35 |
| Hourly heat balance | direct + discharge + backup = demand and direct + charge + dumped = recovered every hour (error < 10⁻¹⁴ kWh); Winter + Sommer = Jahr |
| Tariff slider | break-even 0.2261 CHF/server-h at 33.25 Rp. (repo figure); cost and break-even are linear in the price; heat credit unaffected |
| Case sanity checks | 10 kW peak ÷ 0.8 = 12.5 → 13 servers; 12 kWh/day = 0.625 servers |
| Sizing rule | smallest fleet ≥ target; at case assumptions 6 servers give 79.6%, so 7 are recommended; an unreachable target reports the best achieved coverage |
| Inputs | bill round trip reproduces the class model's UA; bad bills are rejected; postcode 4051 → Basel, 7500 → St. Moritz |

The page also re-runs the Basel benchmark on load and shows the result under «So wurde gerechnet».

**Reference house at page defaults** (95% availability, target 80%): 7 servers, 84.7% of 31,231 kWh covered, 0 kWh dumped. In winter an average of 6.0 servers run (81.6% coverage); in summer 1.5 run (100%). Server electricity is CHF 10,997 per year.

## Limits (also listed on the page)

- One weather year (2025).
- The building model is linear, with no separate sun, wind or thermal mass.
- The tank has no standby loss.
- Booster and pump electricity are not counted.
- Hot water is spread flat over the day.
- Hardware, installation and maintenance are not in the economics.
- The building-class values are typical figures, not a GEAK assessment.
- The bill year is assumed to be as cold as 2025.
- The compute price of 1.35 CHF/server-hour is a scenario value from `scripts/build_fleet_scenario.py`; no buyer for heat-gated hours has been confirmed.
