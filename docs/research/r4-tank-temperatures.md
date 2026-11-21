# Round 4: tank temperatures, summer hot water and winter supply temperature

Investigator file for the round-4 weak point "a 50 °C loop, 55–60 °C storage and 35 kWh from a 30 K spread cannot all hold in one tank; winter radiator supply temperature not modelled". Plan and assessment only. Nothing here is the team's scheduler. No existing file was changed, git state was not touched, and 0 Firecrawl calls were made.

Script: `analysis/r4_tank_layout.py` (standard library only; imports `load`, `simulate` and the case constants from `analysis/baseline_sweep.py` and does not change it). Command: `python3 analysis/r4_tank_layout.py` (exit 0, under 1 s). Its regression check reproduces `baseline_sweep.simulate()` exactly for N=6 and N=8 (79.581% / 92.937%, 31,067 / 36,281 h, 0.2261 CHF).

Currency: CHF. Electricity costs 0.3325 CHF/kWh and heat is valued at 0.133 CHF/kWh, both case constants from `baseline_sweep.py`. No currency conversion was needed.

Status labels: *sourced* means a URL that was opened, with the number read on the page; *computed* means produced by the script above; *assumption* means our own choice; *unverified* means a snippet or an interpretation.

## 1. Findings in brief

1. **The stated layout (A):** a buffer for space heating plus a separate hot-water stage. The server loop, about 55 °C at the chips, passes through the CDU plate heat exchanger (5 K approach), so the house side gets **50 °C** into the top of a **1,000 l stratified buffer of heating water** (not drinking water). Space heating draws from the buffer through a mixing valve. When the heating curve asks for more than 50 °C, the buffer preheats the return water and the house's backup heater adds the rest. Hot water goes through a **fresh-water station** from the buffer top, which preheats drinking water to 47 °C (3 K approach); a **small 55 °C drinking-water cylinder with an electric element** tops it up. The round-2 assumption of a 50 °C loop is now derived from two sources (55 °C outlet − 5 K approach), but the derived value is still an estimate.
2. **Usable buffer energy is not one number.** Energy = 1,000 l × 1.163 Wh/(l K) × spread:
   - hot water only (bottom at about 20 °C): 50 → 20 °C = **34.9 kWh**, so the case's 35 kWh holds in summer;
   - underfloor house at the design hour (return 28 °C): **25.6 kWh**, mean over heating hours 29.5 kWh;
   - radiator house sized 55/45, at the design hour: **5.8 kWh**, mean 16.5 kWh;
   - old radiator house sized 70/55: **0 kWh** at the design hour.
   The case's "60 °C storage plus 30 K spread" (60 → 30 °C) cannot be reached by a 50 °C loop at all (*computed*).
3. **Tank size hardly matters; temperature matters through hot water and old radiators.**
   - **Underfloor house:** all space heat is servable at 50 °C, and the supply never exceeds 34.1 °C in the hour bins.
   - **Radiator 55/45:** 97.9% of space-heating energy is servable directly. The supply is above 50 °C in 339 hours, and on the coldest hour the buffer covers 50% of the load as preheat.
   - **Radiator 70/55:** only 55.6% is servable, with the supply above 50 °C in 2,540 hours.
   - **Hot water:** 82.2% of the energy can come from server heat at a 55 °C setpoint (88.1% at 52 °C, 74.0% at 60 °C), all *computed*.
4. **Key figures, layout A with tank loss 2.80 kWh/day (realism column), against the case column (*computed*):**

| | Case N=6 | A underfloor N=6 | A radiator 55/45 N=6 | Case N=8 | A underfloor N=8 | A radiator 55/45 N=8 |
|---|---|---|---|---|---|---|
| Coverage (year) | 79.6% | 77.6% | 77.4% | 92.9% | 90.6% | 90.4% |
| Coverage Jun–Aug | 100% | 82.2% | 82.2% | 100% | 82.2% | 82.2% |
| Coverage Dec–Feb | 68.7% | 68.4% | 68.3% | 88.1% | 87.2% | 87.1% |
| Dumped | 0 | 0 | 0 | 0 | 0 | 0 |
| Utilisation | 59.1% | 59.4% | 59.3% | 51.8% | 52.1% | 52.0% |
| Break-even, case convention (top-ups by the backup heater, outside the model) | 0.2261 | 0.2293 | 0.2294 | 0.2261 | 0.2293 | 0.2294 |
| Break-even, hot-water top-up charged to the servers, its heat credited (round-2 convention) | 0.2261 | 0.2343 | 0.2343 | 0.2261 | 0.2336 | 0.2337 |

   Without tank loss: underfloor 78.0% / 91.0%, radiator 55/45 77.8% / 90.8%, break-even 0.2261 under the case convention.
   **Old radiator house 70/55: coverage 59.2% at N=6 and 59.3% at N=8**, so more servers do not help; utilisation is 44.1% / 33.1%.
5. **The weak link is the loop temperature, not the tank:**
   - **45 °C on the house side** (the commonly sourced inlet ceiling): Jun–Aug coverage drops to 71.1%, and the radiator-55/45 house at N=8 drops to 80.2%.
   - **55 °C:** Jun–Aug coverage reaches 93.3%.
   - **Tank size:** cutting the usable tank to 10 kWh or 5 kWh costs only 1.0–1.6 points (underfloor; *computed*).
   - **No stratification** (mixed tank): changes coverage by at most 0.2 points.
6. **For the scheduler, one scalar captures almost all of this for underfloor and 55/45 radiator houses.** `baseline_sweep.simulate(rows, n, dhw_direct_share=37/45)` gives 78.04% / 91.02% against 78.0% / 91.0% from the full layout model (*computed*, command in section 6). A temperature-dependent space-heating share is needed only for a house with old high-temperature radiators.

## 2. Sources

### 2.1 Newly opened in round 4

| # | Fact | Value | Status and source |
|---|---|---|---|
| S1 | Swiss limits on supply temperature at the lowest outdoor temperature (per SIA) for new or replaced heat emitters, from the cantonal energy model rules (MuKEn, in force since 4 April 2008) | floor heating max **35 °C**; other emitters such as radiators max **50 °C**; floor-heating return "z. B. 28 °C"; design outdoor temperature "z. B. Region Zürich −8 °C"; at +5 °C outdoor the mean heating-water temperature is "ca. 28 °C" | *sourced*: suissetec info sheet "Fussbodenheizung richtig nutzen", May 2011, <https://merkblatt.suissetec.ch/de-CH/HEIZ111/file/HEIZ111.pdf> (downloaded, read with `pdftotext`). This is MuKEn 2008 as quoted by the trade association; the MuKEn 2014 text itself was not opened |
| S2 | The heating curve defines the supply temperature needed at a given outdoor temperature | definition | *sourced*: same S1 |
| S3 | Fresh-water station outlet temperatures under SIA 385/1:2020 | without warm-held pipes: outlet **≥ 52 °C**; with warm-held pipes: calculated, **58–60 °C**, warm-held pipes ≥ 55 °C, taps ≥ 50 °C after 7 × the flush time; "Legionellenschaltungen" no longer recommended | *sourced*: suissetec Merkblatt "Frischwasserstationen", February 2025, <https://merkblatt.suissetec.ch/de-CH/ALLE222/file/ALLE222.pdf> (downloaded, `pdftotext`) |
| S4 | Fresh-water station: approach between buffer supply and hot water | "sollte die Vorlauftemperatur **2 bis 5 K** über der Warmwassertemperatur liegen"; return to the buffer "möglichst mit tiefer Temperatur"; peak outputs in manufacturer data are usually given at a 70 °C primary supply | *sourced*: same S3 |
| S5 | Fresh-water station advantages | hot water is stored on the heating side, not the drinking-water side, which reduces Legionella risk; "Sämtliche Wärmeangebote (Abwärme, …)" can be used through the buffer | *sourced*: same S3, Tab. 1 |
| S6 | Current fully liquid-cooled AI server coolant temperatures | coolant (75% water, 25% propylene glycol) "up to 45 degrees Celsius"; "the coolant entering a fully liquid-cooled chip at 45 degrees Celsius exits at **roughly 55 degrees**"; waste heat "can be repurposed to heat commercial or residential buildings nearby" | *sourced*: NVIDIA blog, 21 June 2026, <https://blogs.nvidia.com/blog/liquid-cooling-ai-factories/> (downloaded with curl, text extracted). A vendor blog, not a data sheet; "roughly" |
| S7 | One vendor's warmest direct-water-cooling tier | Gold: facility water (FWS) **40–45 °C**, technology cooling system secondary (TCS) **45–50 °C**; the W-class number is the upper bound of the **inlet** temperature; no outlet temperature or ΔT given; "any temperature increases from components such as the CDU must be factored in" | *sourced*: <https://lenovopress.lenovo.com/lp2018-lenovo-neptune-direct-water-cooling-standards> (read through a summarising fetch tool; also read in round 2; re-read by eye before slide use). The **5 K** CDU approach is our reading of TCS minus FWS (*computed* from sourced values; the page does not call it an approach) |
| S8 | EN 442 radiator output formula and design pairs | Φ = Φnorm × (ΔΘln / 49.83)^n with norm 75/65/20; "Der Exponent für den Heizkörper der Normliste beträgt 1,3" (worked example); low-temperature boiler **70/55**, condensing boiler **55/45**, heat-pump new house **35/28**; a 75/65/20 radiator gives 19.95% of its rated output at 35/28/22 | *sourced*: SBZ Monteur 2008/12, <https://www.sbz-monteur.de/sites/default/files/sbzm_pdf/file_226319.pdf> (downloaded, `pdftotext`) |
| S9 | DigitalHeat's own target | "50–70 °C target, system dependent"; "50–70 °C heating and hot water" | *sourced*: case slides, `docs/case-presentation.md` (local copy of the case deck) |

### 2.2 Reused from round 2 (not searched again)

| Fact | Value | Source |
|---|---|---|
| Swiss Legionella guidance, BAG/BLV Modul 11 (version 30.06.2026) | storage ≥ 60 °C with warm-held pipes, **55 °C without**; fresh-water station 52 °C without; waste heat below 50 °C "sollen … in Betriebswasserspeichern gelagert werden" (section 3.13.2); weekly heat-up to 60 °C not accepted as a substitute (5.5) | <https://www.blv.admin.ch/dam/de/sd-web/C3T7bsOJlNIL/legionellen-modul-11-de.pdf> (round 2, confirmed by its critic) |
| Tank standing loss, 934 l stratified buffer, class C | 2.80 kWh/24h (EN 12897:2020) | <https://exhibitorsearch.messefrankfurt.com/images/original/document_downloads/10000006202501/411541/1736956673448_2743857584.pdf> |
| ASHRAE 5th edition | few products operate consistently above 45 °C entering water | <https://www.upsite.com/blog/major-changes-to-ashraes-fifth-edition-of-thermal-guidelines-part-3-liquid-cooling-chapter-updates/> (secondary) |

### 2.3 Not found or not opened (*unverified*)

- A vendor **data sheet** with a server outlet temperature. S6 is a blog ("roughly 55").
- A typical plate heat exchanger approach on a manufacturer page. A search snippet (Wikipedia: "as low as 1 °C" for plate exchangers) was not opened. The 3 K fresh-water-station approach uses S4; the 5 K CDU approach uses S7.
- **Underfloor heating exponent n = 1.1:** seen only in a search snippet of a calculator site (*assumption*). Its effect is negligible, because underfloor supply never comes close to 50 °C.
- **Whether SIA 385/1 accepts a fresh-water-station preheat feeding a 55 °C cylinder** (the potable line between them sits at about 47 °C while water flows). The fallback is an electric in-line heater after the station raising the outlet to 52 °C: direct share 88.1% (*computed*). Ask a sanitary planner.
- The MuKEn 2014 text itself (S1 quotes MuKEn 2008), and Basel's SIA design outdoor temperature. We use the case's −5.6 °C design hour (10 kW). With a colder SIA design point (S1's example is −8 °C for Zurich), the supply temperatures at a given outdoor temperature would be lower, so our choice is on the cautious side.
- NREL test report on heat recovery (fy19osti/73356): the host did not resolve, and only a search snippet was seen. Not used.

## 3. The layout and why it was chosen over a single combi tank

**Layout A: buffer for space heating plus fresh-water station and small hot-water cylinder (chosen)**

```
server rack (DLC)        CDU plate HX          1,000 l buffer (heating water, stratified)
coolant 45 -> ~55 C  ->  5 K approach   ->  top 50 C ---- mixing valve -> heating circuit (curve T_sup)
                         house side 50 C     |            (if T_sup > 50 C: buffer preheats the
                         return <= 45 C <----+ bottom      return; backup heater adds the rest)
                                             |
                                             +-- fresh-water station (3 K) -> drinking water 47 C
                                                    -> small cylinder at 55 C, electric element top-up
```

Why this layout:

- **It follows the Swiss hygiene rule.** Waste heat below 50 °C belongs in non-drinking-water storage (BAG/BLV 3.13.2), and S5 names waste heat explicitly as a use for fresh-water stations.
- **Hot water does not hold the whole buffer at 55–60 °C.** The buffer can be drawn down to 20 °C by the fresh-water station (S4: return "möglichst mit tiefer Temperatur"), so in summer the 30 K spread and 34.9 kWh hold.
- **The house-side return must be ≤ 45 °C** for the server to stay in the warmest sourced cooling tier (S7, FWS 40–45 °C). Underfloor return (≤ 28 °C) and the fresh-water-station return meet this easily. A 55/45 radiator return reaches 44 °C at the design hour (curve, section 4), right at the edge. A 70/55 house returns up to 55 °C, which **cannot cool the servers at all** in cold hours. The model is optimistic for that case: it still lets the servers charge the tank.

**Layout B: one combi tank with stratification (rejected)**

- To serve hot water directly, its top must stay at 55–60 °C, which a 50 °C loop cannot reach. An electric element would have to hold a top zone.
- That zone's volume is lost to the server loop. Illustration (*assumption*): with a 200 l zone, the loop keeps 800 l × 30 K = 27.9 kWh.
- A combi tank keeps drinking water warm inside heating water at loop temperatures, which the BAG rule advises against. It saves one component, but its usable capacity and its hygiene are both worse.

## 4. Method (what the script does)

- **Heating curve** (constant flow, arithmetic-mean form of the EN 442 characteristic; *assumption* on the form, exponent from S8):
  - load fraction φ = space heat ÷ 10 kW, which equals (20 − T) ÷ 25.6 by the case's own formula;
  - mean excess temperature = (design mean − 20) × φ^(1/n);
  - spread = design spread × φ.
  - Design pairs at the case's design hour (−5.6 °C): underfloor 35/28 (S1, MuKEn max), radiator 55/45 (S8), radiator 50/40 (S1 MuKEn max for radiators; 40 °C return is an *assumption*), radiator 70/55 (S8).
  - **Sanity check:** at +5 °C the underfloor mean water temperature comes out at 27.1 °C, against S1's "ca. 28 °C" (S1 uses a −8 °C design point) (*computed*).
- **Share of space heat the buffer serves:** 1 if T_sup ≤ 50 °C, otherwise (50 − T_ret) ÷ (T_sup − T_ret), clipped to [0, 1]. This is a serial preheat of the return; the backup heater adds the rest outside the model, as the case treats its backup heater.
- **Share of hot water the buffer serves:** (47 − 10) ÷ (T_set − 10) = 82.2% at 55 °C. Cold water at 10 °C is an *assumption*, kept from round 2.
- **Tank:** an ideal stratified tank. State = energy above 20 °C, capacity 1.163 × (50 − 20) = 34.9 kWh. Space heating may draw only down to the hour's return temperature; hot water may draw down to 20 °C. Live server heat serves demand first and the surplus charges the tank. The follow rule takes the largest whole number of servers whose surplus fits, so nothing is dumped, as in `baseline_sweep` "follow". Optional tank loss 2.80 kWh/day.
- **Break-even:**
  - *case convention* = (server electricity − value of used server heat) ÷ server-hours. Every top-up (space-heat backup, hot-water element) is the backup heater outside the model.
  - *round-2 convention* = the hot-water element's electricity is charged to the servers and its heat is credited at price ÷ 2.5. The space-heating backup always stays outside the model.
- **Sensitivities:** house-side loop temperature 45 / 50 / 55 °C; hot-water setpoint 60 °C (warm-held pipes); no stratification (space heating needs the tank above the supply temperature); usable tank cut to 10 or 5 kWh.

## 5. Script output (full)

Command: `python3 analysis/r4_tank_layout.py`

```
== 0. Regression check: case_mode against baseline_sweep.simulate() ==
  N=6: baseline cov 79.581% run_h 31067 BE 0.2261 | this file 79.581% 31067 0.2261 -> OK
  N=8: baseline cov 92.937% run_h 36281 BE 0.2261 | this file 92.937% 36281 0.2261 -> OK

== 1. Inputs ==
  srv_out_c          55.0
  cdu_approach_k     5.0
  fws_approach_k     3.0
  t_cold_c           10.0
  t_dhw_set_c        55.0
  t_dhw_set_circ_c   60.0
  t_floor_dhw_c      20.0
  t_room_c           20.0
  loss_kwh_day       2.8
  T_TOP (house side) = 55.0 - 5.0 = 50.0 C
  tank heat capacity  = 1000 l x 1.163 Wh/(l K) = 1.163 kWh/K

== 2. Usable tank energy for 1,000 l (kWh = 1.163 x spread) ==
  case: 30 K spread (e.g. 60 -> 30 C)                                            spread  30.0 K ->  34.9 kWh
  layout A, hot water only: 50 -> 20 C                                           spread  30.0 K ->  34.9 kWh
  layout A, underfloor 35/28, design hour: 50 -> 28 C                            spread  22.0 K ->  25.6 kWh
  layout A, radiator 55/45, design hour: 50 -> 45 C                              spread   5.0 K ->   5.8 kWh
  layout A, radiator 50/40, design hour: 50 -> 40 C                              spread  10.0 K ->  11.6 kWh
  layout A, radiator 70/55, design hour: 50 -> 55 C                              spread   0.0 K ->   0.0 kWh
  single combi tank, 60 C top kept for hot water, 50 C loop charges only below   spread   0.0 K ->   0.0 kWh
    ... loop zone 50 -> 20 C under a 60 C hot-water zone of 200 l (assumption)   spread  24.0 K ->  27.9 kWh

== 3. Heating curve and share of space heat the 50 C buffer serves, by outdoor temperature ==
   T out  hours         underfloor 35/28           radiator 55/45           radiator 50/40           radiator 70/55
                          sup/ret  share           sup/ret  share           sup/ret  share           sup/ret  share
   -6..-2    200        34.1/27.6  100.0%        53.2/43.9   65.5%        48.5/39.1  100.0%        67.5/53.4    0.0%
   -2..2     885        31.9/26.5  100.0%        48.7/40.9  100.0%        44.6/36.8  100.0%        61.0/49.3    6.1%
    2..6    1286        29.7/25.3  100.0%        44.0/37.8  100.0%        40.5/34.3  100.0%        54.3/44.9   54.2%
    6..10   1436        27.4/24.1  100.0%        39.1/34.4  100.0%        36.3/31.6  100.0%        47.2/40.2  100.0%
   10..14    877        25.1/22.9  100.0%        33.8/30.7  100.0%        31.8/28.7  100.0%        39.7/35.0  100.0%
   14..21    258        21.7/21.0  100.0%        25.5/24.5  100.0%        24.7/23.7  100.0%        27.8/26.4  100.0%
  (T out bin mid-point; heating-day hours only; supply/return from the case load fraction (20-T)/25.6)

== 4. Year totals: space heat the buffer can serve by temperature (energy-weighted) ==
  underfloor 35/28   100.0% of 26,851 kWh space heat; hours with supply > 50 C: 0
  radiator 55/45      97.9% of 26,851 kWh space heat; hours with supply > 50 C: 339
  radiator 50/40     100.0% of 26,851 kWh space heat; hours with supply > 50 C: 0
  radiator 70/55      55.6% of 26,851 kWh space heat; hours with supply > 50 C: 2540
  hot water, preheat 47 C, setpoint 52 C: direct share 88.1% (top-up 521 kWh/yr electric)
  hot water, preheat 47 C, setpoint 55 C: direct share 82.2% (top-up 779 kWh/yr electric)
  hot water, preheat 47 C, setpoint 60 C: direct share 74.0% (top-up 1,139 kWh/yr electric)

== 5. Key figures: case column vs layout A realism column (follow rule, no dumping) ==
  BEcase = case formula, top-ups by the backup heater outside the model (case convention);
  BEchg  = hot-water top-up electricity charged to the servers, its heat credited at price/2.5 (round-2 convention)
variant                                      N   cover Dec-Feb Jun-Aug  dump   util   srv-h  BEcase   BEchg
case assumptions (35 kWh, all heat usable)   6   79.6%   68.7%  100.0%     0  59.1%   31067  0.2261  0.2261
A, underfloor 35/28                          6   78.0%   68.7%   82.2%     0  57.9%   30445  0.2261  0.2312
A, radiator 55/45                            6   77.8%   68.7%   82.2%     0  57.8%   30373  0.2261  0.2312
A, radiator 50/40                            6   77.9%   68.7%   82.2%     0  57.8%   30396  0.2261  0.2312
A, radiator 70/55                            6   59.2%   42.0%   82.2%     0  44.1%   23173  0.2263  0.2330
A, underfloor 35/28 + loss 2.80/d            6   77.6%   68.4%   82.2%     0  59.4%   31236  0.2293  0.2343
A, radiator 55/45 + loss 2.80/d              6   77.4%   68.3%   82.2%     0  59.3%   31174  0.2294  0.2343

case assumptions (35 kWh, all heat usable)   8   92.9%   88.1%  100.0%     0  51.8%   36281  0.2261  0.2261
A, underfloor 35/28                          8   91.0%   87.7%   82.2%     0  50.7%   35516  0.2261  0.2305
A, radiator 55/45                            8   90.8%   87.6%   82.2%     0  50.6%   35444  0.2261  0.2305
A, radiator 50/40                            8   90.9%   87.7%   82.2%     0  50.6%   35472  0.2261  0.2305
A, radiator 70/55                            8   59.3%   42.1%   82.2%     0  33.1%   23200  0.2263  0.2330
A, underfloor 35/28 + loss 2.80/d            8   90.6%   87.2%   82.2%     0  52.1%   36495  0.2293  0.2336
A, radiator 55/45 + loss 2.80/d              8   90.4%   87.1%   82.2%     0  52.0%   36443  0.2294  0.2337

== 6. Sensitivity (N=6 and 8): loop temperature on the house side and hot-water setpoint ==
variant                                      N   cover Dec-Feb Jun-Aug  dump   util   srv-h  BEcase   BEchg
underfloor 35/28, T_top 45 C, set 55         6   76.9%   68.6%   71.1%     0  57.1%   30021  0.2261  0.2345
underfloor 35/28, T_top 50 C, set 55         6   78.0%   68.7%   82.2%     0  57.9%   30445  0.2261  0.2312
underfloor 35/28, T_top 55 C, set 55         6   79.1%   68.7%   93.3%     0  58.7%   30861  0.2261  0.2280
underfloor 35/28, T_top 50 C, set 60 (warm-held) 6   77.3%   68.6%   74.0%     0  57.4%   30161  0.2261  0.2336
radiator 55/45, T_top 45 C, set 55           6   74.5%   65.2%   71.1%     0  55.4%   29124  0.2262  0.2349
radiator 55/45, T_top 50 C, set 55           6   77.8%   68.7%   82.2%     0  57.8%   30373  0.2261  0.2312
radiator 55/45, T_top 55 C, set 55           6   78.9%   68.7%   93.3%     0  58.6%   30800  0.2261  0.2280
radiator 55/45, T_top 50 C, set 60 (warm-held) 6   77.1%   68.6%   74.0%     0  57.2%   30084  0.2261  0.2337

underfloor 35/28, T_top 45 C, set 55         8   89.6%   87.2%   71.1%     0  49.9%   34979  0.2261  0.2333
underfloor 35/28, T_top 50 C, set 55         8   91.0%   87.7%   82.2%     0  50.7%   35516  0.2261  0.2305
underfloor 35/28, T_top 55 C, set 55         8   92.3%   88.1%   93.3%     0  51.4%   36039  0.2261  0.2277
underfloor 35/28, T_top 50 C, set 60 (warm-held) 8   90.1%   87.5%   74.0%     0  50.2%   35157  0.2261  0.2326
radiator 55/45, T_top 45 C, set 55           8   80.2%   72.5%   71.1%     0  44.7%   31352  0.2262  0.2343
radiator 55/45, T_top 50 C, set 55           8   90.8%   87.6%   82.2%     0  50.6%   35444  0.2261  0.2305
radiator 55/45, T_top 55 C, set 55           8   92.2%   88.1%   93.3%     0  51.4%   35988  0.2261  0.2277
radiator 55/45, T_top 50 C, set 60 (warm-held) 8   89.8%   87.3%   74.0%     0  50.0%   35075  0.2261  0.2326

== 6b. Sensitivity: no stratification (space heating needs the tank above the supply temperature) ==
variant                                      N   cover Dec-Feb Jun-Aug  dump   util   srv-h  BEcase   BEchg
underfloor 35/28, mixed-tank floor           6   77.9%   68.7%   82.2%     0  57.9%   30418  0.2261  0.2312
radiator 55/45, mixed-tank floor             6   77.6%   68.7%   82.2%     0  57.6%   30288  0.2261  0.2312
underfloor 35/28, usable cap 10 kWh          6   77.0%   68.3%   82.2%     0  57.2%   30061  0.2261  0.2313
underfloor 35/28, usable cap 5 kWh           6   76.4%   68.1%   82.2%     0  56.8%   29844  0.2261  0.2313
underfloor 35/28, mixed-tank floor           8   90.9%   87.7%   82.2%     0  50.6%   35495  0.2261  0.2305
radiator 55/45, mixed-tank floor             8   90.6%   87.5%   82.2%     0  50.5%   35377  0.2261  0.2305
underfloor 35/28, usable cap 10 kWh          8   90.1%   86.7%   82.2%     0  50.2%   35166  0.2261  0.2305
underfloor 35/28, usable cap 5 kWh           8   89.7%   86.3%   82.2%     0  50.0%   35025  0.2261  0.2305

== 7. Usable tank energy actually available (mean over heating hours) and stranded share ==
  N=6 underfloor 35/28   cap 34.9 kWh, usable above heating return (mean of heating hours) 29.5 kWh; backup adds 0 kWh space heat; hot-water top-up 779 kWh el
  N=6 radiator 55/45     cap 34.9 kWh, usable above heating return (mean of heating hours) 16.5 kWh; backup adds 565 kWh space heat; hot-water top-up 779 kWh el
  N=6 radiator 50/40     cap 34.9 kWh, usable above heating return (mean of heating hours) 20.1 kWh; backup adds 0 kWh space heat; hot-water top-up 779 kWh el
  N=6 radiator 70/55     cap 34.9 kWh, usable above heating return (mean of heating hours) 9.2 kWh; backup adds 11,925 kWh space heat; hot-water top-up 779 kWh el
  N=8 underfloor 35/28   cap 34.9 kWh, usable above heating return (mean of heating hours) 29.5 kWh; backup adds 0 kWh space heat; hot-water top-up 779 kWh el
  N=8 radiator 55/45     cap 34.9 kWh, usable above heating return (mean of heating hours) 16.5 kWh; backup adds 565 kWh space heat; hot-water top-up 779 kWh el
  N=8 radiator 50/40     cap 34.9 kWh, usable above heating return (mean of heating hours) 20.1 kWh; backup adds 0 kWh space heat; hot-water top-up 779 kWh el
  N=8 radiator 70/55     cap 34.9 kWh, usable above heating return (mean of heating hours) 9.2 kWh; backup adds 11,925 kWh space heat; hot-water top-up 779 kWh el

== 8. Pitch figures (N=6 / N=8) ==
  underfloor 35/28 + loss: coverage 79.6% -> 77.6% (N=6), 92.9% -> 90.6% (N=8); Jun-Aug 100% -> 82.2%; Dec-Feb 68.7% -> 68.4% (N=6), 88.1% -> 87.2% (N=8); util 59.1% -> 59.4% / 51.8% -> 52.1%; BE case conv. 0.2293 / 0.2293, charged 0.2343 / 0.2336
  radiator 55/45 + loss: coverage 79.6% -> 77.4% (N=6), 92.9% -> 90.4% (N=8); Jun-Aug 100% -> 82.2%; Dec-Feb 68.7% -> 68.3% (N=6), 88.1% -> 87.1% (N=8); util 59.1% -> 59.3% / 51.8% -> 52.0%; BE case conv. 0.2294 / 0.2294, charged 0.2343 / 0.2337
```

Reading the output:

- **Section 3:** the radiator 55/45 house needs more than 50 °C only below −1.1 °C outdoor (339 hours a year). The 70/55 house needs it below +6.5 °C (computed with `curve()`).
- **Section 5:** utilisation in the realism column without tank loss is 1.1–1.3 points below the case column (N=6: 59.1% → 57.9%; N=8: 51.8% → 50.7%), because the hot-water top-up takes some work away from the servers. Adding the tank loss pushes utilisation back up (+1.5 points), because the servers run longer to replace the lost heat. The round-2 critic warned that this should not be read as an improvement.
- **Section 6:** at a 45 °C house-side loop, the radiator 55/45 house at N=8 loses 10.6 points (90.8% → 80.2%), because cold hours become temperature-limited while eight servers would otherwise cover them. At N=6 it loses 3.3 points.
- **Break-even under the case convention stays 0.2261** without tank loss in every row except 70/55 (0.2263; a little heat is left in the tank at year end) and T_top 45 °C (0.2262). Under the follow rule every server-hour's heat is used, so temperatures move coverage and utilisation, not break-even. Tank loss adds +0.003.

## 6. Extra check: the existing baseline switch is enough for the default houses

Command (run in `analysis/`, nothing saved):

`python3 -c "from baseline_sweep import load, simulate; rows=load(); [print(n, simulate(rows,n,dhw_direct_share=37/45,tank=34.9)) for n in (6,8)]"`

(Abridged in this file; the run printed the fields below.)

| `simulate(rows, n, dhw_direct_share=37/45, tank=…)` | Coverage | Utilisation | Server-h | Break-even |
|---|---|---|---|---|
| N=6, tank 35 / 34.9 | 78.04% | 57.97% | 30,467 | 0.2261 |
| N=6, tank 29.5 (mean usable, underfloor) | 77.95% | 57.90% | 30,430 | 0.2261 |
| N=6, tank 34.9 + loss 2.80 | 77.72% | 59.46% | 31,251 | 0.2292 |
| N=8, tank 35 / 34.9 | 91.02% | 50.70% | 35,534 / 35,533 | 0.2261 |
| N=8, tank 34.9 + loss 2.80 | 90.74% | 52.10% | 36,510 | 0.2293 |

These are within 0.1–0.2 points of the full layout model (78.0% / 91.0%; with loss 77.6% / 90.6%). For the underfloor and 55/45 houses, `dhw_direct_share = 0.822` alone reproduces the realism column. The space-heating temperature share matters only for 70/55 radiators, or for a loop below 50 °C feeding radiators.

## 7. Pitch sentence and scheduler parameters

**The one sentence for the pitch (after the key figures):**

> "Our headline uses the case's simplifications. In a real basement the servers' water reaches the house at about 50 °C. That is enough for floor heating and for radiators sized for 55 °C, but hot water needs a small electric top-up to 55 °C, so summer coverage falls from 100% to 82% and the year from 79.6% to 77.4% at six servers. A house with old 70 °C radiators stays below 60% however many servers it gets."

Footnote on the slide: layout A, 1,000 l buffer plus fresh-water station; tank loss 2.80 kWh/day included; 50 °C = 55 °C coolant outlet (vendor blog) − 5 K exchanger approach (vendor tier table), an estimate. Break-even 0.2294 CHF with top-ups paid by the house's backup heater, 0.2343 CHF if the servers pay the hot-water element.

**Parameters the team's scheduler should expose.** The defaults are the case assumptions, so the reference-house key figures do not change. The realism column sets the values shown.

| Parameter | Default (case) | Realism column (layout A) | Build cost |
|---|---|---|---|
| `usable_tank_kwh` | 35 | 34.9 (50 → 20 °C). Leave at 35: the figures move by at most 0.1 point | none, already in `baseline_sweep` (`tank`) |
| `dhw_direct_share` | 1.0 | **0.822** (preheat 47 °C, setpoint 55 °C); 0.881 at 52 °C; 0.740 at 60 °C | none, already in `baseline_sweep` |
| `tank_loss_kwh_day` | 0 | 2.80 | none, already in `baseline_sweep` |
| `loop_temp_c` (house side) | not used | 50 | **optional**, only with the next row |
| `heating_system` = supply/return design pair for a temperature-dependent space-heat share (`sh_direct_share(t_out)`) | None (all space heat servable) | underfloor 35/28 → 1.0 always; radiator 55/45 → 0.979 of the year's energy | **optional, adds scope** (curve plus tank floor, about 40 lines); only needed to show the old-radiator house (70/55) as a "does not pay off / does not cover" case |
| `dhw_topup_charged_to_servers` | False (case convention) | report both | one line in the cost formula |

Recommendation: ship only `dhw_direct_share` (and the existing tank-loss switch) in the realism column, and quote the 70/55 house from this script as a "where it stops holding" line. That adds no build scope.

## 8. Limits of this analysis

- Ideal stratification is optimistic. The crude mixed-tank variant changes coverage by at most 0.2 points, but a real tank mixes at its inlets.
- 50 °C on the house side rests on one vendor blog ("roughly 55 °C" outlet) and a tier table read as a 5 K approach. A 45 °C loop is plausible for many current products (round 2: "few above 45 °C"), and then summer coverage is 71% and a radiator house at N=8 loses 10.6 points.
- In the 70/55 case the servers cannot actually be cooled by 50–55 °C return water. The model still lets them charge the tank, so 59% is an upper bound.
- Return water above 45 °C in the radiator 55/45 house near the design hour is right at the sourced cooling-tier limit.
- Cold water at 10 °C, a fresh-water-station approach of 3 K, a tank floor of 20 °C, underfloor n = 1.1 and the arithmetic-mean heating curve are *assumptions*.
- The serial "buffer preheats the return" connection is assumed to be installed. A simple parallel buffer would give 0% instead of a share whenever T_sup > 50 °C.
- Solar and internal gains, night setback and the slab inertia of underfloor heating are not modelled; the case's demand formula is used as is.
- The stand-in profile, as everywhere in the plan.
