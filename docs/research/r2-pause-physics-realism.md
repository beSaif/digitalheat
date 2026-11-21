# Round 2 — physical realism of pause and summer

Investigator file for weak point 3 of round 2: idle power, restart cost, cycling, sourced tank loss and hot-water booster, and their effect on the 6-vs-8 table. Plan and assessment only; nothing here is the team's scheduler.

**Status labels:** *sourced* = the number was read on the URL given (page or PDF opened in this session) · *computed* = printed by `python3 analysis/r2_realism.py` (stdlib only; imports `load`, `simulate` and the constants from `analysis/baseline_sweep.py`, which was not modified) · *assumption* = our own choice · *unverified* = seen only in a search snippet, or an estimate.

Currency: CHF throughout. No conversion was needed. Paid Firecrawl calls used: 0 of 6.

All yearly figures are on the stand-in profile `data/reference_house_2025_hourly.csv`, with unlimited jobs (every run hour filled and sold) as in the round-1 baseline.

## 1. Short answers

1. **Tank loss is sourced now and it is small.** A 1,000-litre buffer tank loses 1.7 to 3.4 kWh per day on a manufacturer data sheet, and no tank up to 2,000 litres may be sold in the EU above 3.57 kWh per day (at V = 1,000 l). The 2–4 kWh/day in `assumption-limits.md` holds. Effect at 2.80 kWh/day: coverage −0.3 points, break-even +0.003 CHF per server-hour, at N=6 and N=8 alike. Summer coverage does not move, because the server simply runs longer; the loss shows up as 720 to 860 kWh of heat per year that nobody uses.
2. **The hot-water booster is what moves summer.** Swiss guidance wants 60 °C at the storage outlet (55 °C without warm-held pipes). If the server loop preheats to 50 °C (*assumption*), 20% of hot-water energy must come from a booster: 876 kWh of electricity a year with an electric heater, 292 kWh with a small heat pump at COP 3 (*assumption*).
3. **Pitch sentence** (*computed*; inputs labelled in section 4):
   > "These numbers use the case's simplifications. With tank losses and an electric hot-water booster, summer coverage drops by 20 points (100% to 80%) and the break-even price rises by 0.009 CHF per server-hour (0.2261 to 0.2348 at 6 servers; 0.2341 at 8)."

   With a small heat-pump booster instead: summer coverage drops by 6.7 points and the break-even rises by 0.005 CHF. The 20 points follow directly from the assumed 50 °C preheat; with 45 °C it is 30 points, with a 55 °C setpoint 11 points.
4. **A paused server must be powered down, not frozen.** With all servers left on at a sourced idle draw of 17.6% of full power, the idle heat of 6 servers is 20.3 kWh/day against 12 kWh/day of summer hot water. No server would do a single hour of sold work from June to August, 1,312 kWh (N=6) or 2,391 kWh (N=8) would be dumped, and the break-even rises from 0.2261 to 0.2659 (N=6) or 0.2814 (N=8). This is the only switch that separates 6 from 8.
5. **Powering down is cheap if the flapping is fixed.** With the plain follow rule there are 1,732 (N=6) or 2,208 (N=8) starts a year and one server is started 1,433 times. At 15 minutes of unsold time per start (*assumption*) that costs 1.4–1.5% of run hours and +0.003 CHF. With a band, it is below +0.001 CHF.
6. **Band recommendation: 8 kWh, with "one server at most when there is no space heating", and servers that already run keep running** (rule `hold+cap1` in the script). Starts fall from 1,732 to 267 (N=6) and from 2,208 to 607 (N=8); the busiest server goes from 1,433 starts a year to 90–112; no pause is shorter than 2 hours; coverage costs 0.12–0.14 points. If the team will not give up 0.1 points, the round-1 rule with the same 8 kWh band costs 0.03 points or less but leaves 68 (N=6) or 266 (N=8) runs of one hour. Reason for 8 kWh in section 5.
7. **Peaked hot water changes nothing**: at most −0.1 coverage points, break-even unchanged. The check `assumption-limits.md` asks for is done.
8. **6 versus 8 is not changed by any switch as long as paused servers are powered down.** The coverage gap stays at 13.0–13.4 points, the utilisation gap at 7.3 points, the break-even gap below 0.0005 CHF. What the realism does add to the comparison: 8 servers cycle more (607 against 267 starts a year with the band) and lose more if they idle.

## 2. Sources

### 2.1 Tank standing loss

| Fact | Value | Status and source |
|---|---|---|
| EU ecodesign ceiling for hot water storage tanks, from 26 Sept 2017 | S ≤ 16.66 + 8.33 · V^0.4 W (V in litres) | *sourced*: Regulation (EU) 814/2013, Annex II point 2.1, Official Journal PDF <https://www.legislation.gov.uk/eur/2013/814/pdfs/eur_20130814_adopted_en.pdf> (read with `pdftotext`; in the HTML versions the formula is an image) |
| Scope of 814/2013 for tanks | storage volume ≤ 2,000 litres | *sourced*: Article 1(1), <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32013R0814> |
| Benchmark (best available) in 814/2013 | 5 + 4.16 · V^0.4 W | *sourced*: same PDF, Annex VI point 3 |
| Label classes (812/2013, Annex II Table 2) | A+: S < 5.5 + 3.16·V^0.4; A: up to 8.5 + 4.25·V^0.4; B: up to 12 + 5.93·V^0.4; C: up to 16.66 + 8.33·V^0.4; D: up to 21 + 10.33·V^0.4; E: up to 26 + 13.66·V^0.4; F: up to 31 + 16.66·V^0.4; G above | *sourced*: <https://www.legislation.gov.uk/eur/2013/812/pdfs/eur_20130812_adopted_en.pdf> |
| Scope of the label regulation 812/2013 | tanks ≤ 500 litres. **A 1,000-litre tank needs no label**; the class letters on data sheets are the same formula applied voluntarily | *sourced*: Article 1(1), <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32013R0812> |
| Definition of standing loss | "heating power dissipated from a hot water storage tank at given water and ambient temperatures", in W | *sourced*: 814/2013 Article 2(17), same EUR-Lex page |
| The ceiling at V = 1,000 l | 148.7 W = **3.57 kWh/day** (1000^0.4 = 15.849). Class boundaries at 1,000 l: A+/A 55.6 W = 1.33, A/B 75.9 W = 1.82, B/C 106.0 W = 2.54, C/D 148.7 W = 3.57 kWh/day; benchmark 70.9 W = 1.70 kWh/day | *computed* from the sourced formulas (W × 24 ÷ 1000) |
| Data sheet, plain buffer "P8 1000" (nominal 887 l, 100 mm fleece) | 141 W, **3.38 kWh/24h**, class C | *sourced*: Solarbayer product programme PDF, "Bereitschaftswärmeaufwand nach EN 12897:2020", <https://exhibitorsearch.messefrankfurt.com/images/original/document_downloads/10000006202501/411541/1736956673448_2743857584.pdf> |
| Data sheet, stratified buffer "SLS 1000" (nominal 934 l), standard insulation | 117 W, **2.80 kWh/24h**, class C | *sourced*: same PDF |
| Same tank, double insulation ("Plus") | 70 W, **1.68 kWh/24h**, class A | *sourced*: same PDF |
| Other 1,000 l buffers: 104 to 145 W | — | *unverified* (search snippet of a shop; the pages returned HTTP 429) |
| Test temperatures behind these figures (commonly quoted as 65 °C store, 20 °C room) | — | *unverified*: neither regulation text states them in the parts read; the data sheet only names EN 12897:2020 |

Reading: the range in `assumption-limits.md` ("roughly 2–4 kWh per day") is confirmed as 1.7–3.6 kWh/day for a tank that may legally be sold. One manufacturer is not a market survey. The figures are at test conditions; a tank kept at 45–60 °C in a 15 °C cellar has a similar temperature difference, so no rescaling was done (*assumption*). The script uses **2.80 kWh/day** as the central value and the other three as the range.

### 2.2 Hot-water temperatures (Legionella)

Source for all rows: BAG/BLV, "Empfehlungen zu Legionellen und Legionellose, Modul 11, Hausinstallationen: Planung, Bau, Betrieb, Instandhaltung", version of 30.06.2026 (new version after the 2025 total revision), <https://www.blv.admin.ch/dam/de/sd-web/C3T7bsOJlNIL/legionellen-modul-11-de.pdf> (PDF read with `pdftotext`). *Sourced.* The module quotes SIA 385/1:2020 and SVGW W3/E3; the standards themselves were not opened (paywalled).

| Fact | Value |
|---|---|
| Systems with warm-held pipes (Table 1): storage or fresh-water station | SVGW W3/E3: ≥ 60 °C; SIA 385/1:2020: "nach Berechnung" (calculated so that the other temperatures are reached) |
| Distribution system | 55 °C |
| At the tap | 50 °C after seven times the output time |
| Systems without warm-held pipes (Table 2): storage | 55 °C (SIA 385/1:2020 and SVGW); fresh-water station 52 °C (SIA) |
| Cold water | ≤ 25 °C after 30 seconds |
| Critical range | 25 to 50 °C (stated several times, e.g. section 3.16) |
| Above 60 °C | to be avoided (limescale, scalding), chapter 5 |
| Weekly "Legionella cycle" to 60 °C | "aus aktueller Sicht … nicht zielführend"; must not be used to lower normal operating temperatures (section 5.5). **A weekly electric boost is therefore not an accepted substitute for a booster.** |
| Waste heat below 50 °C | "sollen aus hygienischen Gründen in Betriebswasserspeichern gelagert werden" (section 3.13.2): store it in a non-drinking-water buffer. This fits the case's buffer tank; the drinking water is then heated through a fresh-water station or a separate heater that must reach 52–60 °C |

Reading: `assumption-limits.md` says "≥60 °C in storage". Correct for SVGW W3/E3 with circulation; a single-family house without warm-held pipes can run at 55 °C storage. Either way the hot water must leave the heater at 52–60 °C, which is at or above what a warm-water-cooled server loop supplies (next section).

### 2.3 Liquid-cooling classes and server water temperatures

| Fact | Value | Status and source |
|---|---|---|
| ASHRAE 2011 liquid-cooling classes, facility supply water | W1 2–17 °C, W2 2–27 °C, W3 2–32 °C, W4 2–45 °C, W5 > 45 °C; W5 is the class listed with "Building heating system" as main cooling equipment | *sourced*: Lawrence Berkeley National Lab slide deck, <https://datacenters.lbl.gov/sites/default/files/ASHRAE%20Thermal%20Guidelines_%20SVLG%202015.pdf> |
| 5th edition renames by upper limit | W17, W27, W32, new W40, W45, W+ (formerly "over 45 °C"). "several manufacturers are designing liquid cooled solutions that operate around 40°C entering facility water"; "few are capable of operating consistently above 45°C" | *sourced*: <https://www.upsite.com/blog/major-changes-to-ashraes-fifth-edition-of-thermal-guidelines-part-3-liquid-cooling-chapter-updates/> (secondary; the ASHRAE book itself was not opened) |
| The class number | the upper bound of the **inlet** water temperature to the IT equipment, not the outlet | *sourced*: <https://lenovopress.lenovo.com/lp2018-lenovo-neptune-direct-water-cooling-standards> |
| One vendor's warmest tier ("Gold") | facility water 40–45 °C, server loop 45–50 °C inlet | *sourced*: same Lenovo page |
| Share of server heat captured in water | Gold: 80–85% without a rear-door heat exchanger, 95–100% with an insulated rack or rear door; Silver up to 80%; Bronze up to 60%; CPU-only cold plates 70% | *sourced*: same Lenovo page. **The case's 80% recovery matches the warm-water tier without rear door.** |
| Outlet temperature | "the outlet water can be made quite hot (up to 70 degrees Celsius)" with inlet up to 40 °C (LRZ, quoted in the trade press, 2012); IBM coolant "as high as 113 degrees Fahrenheit" (45 °C) | *sourced* as a press quotation: <https://www.datacenterknowledge.com/cooling/hot-water-cooling-three-projects-making-it-work>. Not a vendor data sheet. |
| A 60 °C outlet at 45–50 °C inlet for a current server | — | *unverified*: no vendor document with an outlet figure was found |
| Preheat temperature of 50 °C used in the script | — | *assumption*, placed at the top of the sourced inlet range |

Reading: "50–70 °C without a heat pump" needs class W45/W+ equipment, which the 5th-edition commentary calls rare. Sourced inlet temperatures end at 45–50 °C. Underfloor heating (30–40 °C) is served directly; hot water at 55–60 °C is at the edge. The table in `assumption-limits.md` ("~45–60 °C water") holds for the lower end; the 60 °C end rests on one 2012 press quotation.

### 2.4 Idle power

| Fact | Value | Status and source |
|---|---|---|
| Dual Xeon Platinum 8480+ server (FusionServer 5288 V7), SPECpower_ssj2008 | 835 W at 100% load, 147 W active idle → **17.6%**; 230 W at 10% load | *sourced*: <https://www.spec.org/power_ssj2008/results/res2023q1/power_ssj2008-20221207-01215.html>; ratio *computed* |
| 8 × H100 node (HGX), measured at the wall | idle node 1.86 kW; highest load measured 8.43 kW (rated 10.2 kW) → **22.1%** of the measured maximum, 18.2% of the rating | *sourced*: arXiv 2412.08602v2, table of median task power (row "Idle Node"), <https://arxiv.org/pdf/2412.08602v2>; ratios *computed* |
| Standby draw of a powered-down server (management controller) | a few watts | *unverified*, not searched; set to 0 in the script |

"Active idle" means the operating system is up and no work arrives. A process stopped with SIGSTOP leaves the machine in this state. One CPU server and one GPU node are two data points, not a distribution.

### 2.5 Restart time and cycling wear

| Fact | Value | Status and source |
|---|---|---|
| Field data on daily power cycling | 18,826 power cycles in 5 months on a lab's servers ("an average of once per day per server"), 10 hardware models; no power supply or disk failed in two years. The text says 123 servers in one place and 23 in another | *sourced*, weak: vendor blog, 2007, <https://vinaypai.blogspot.com/2007/09/yes-its-still-safe-to-power-off-and.html> |
| Temperature swings and failures | "high variability in temperature seems to have a stronger effect on node reliability than average temperature" (Observation 10); nodes with a higher coefficient of variation in temperature had significantly more outages (one system at LANL) | *sourced*: El-Sayed et al., SIGMETRICS 2012, <https://www.cs.utoronto.ca/~bianca/papers/temperature_cam.pdf>. About temperature variation, not about power cycles as such |
| A recommended limit on power cycles per year for servers | none found | — |
| Boot time of a rack server (POST and memory check) | about 2 min at 72–128 GB, 5 min and more on larger machines | *unverified*: forum posts seen in search snippets only (the pages did not open) |
| Restart penalty in the script | 5 and 15 minutes from power-on to the job computing again (POST, operating system, model load) | *assumption*. The model-load part is the Saturday measurement already planned for role B |

Reading: there is no published cycle limit to hold our numbers against. The honest statement is: "the only field evidence we found is one small 2007 sample at one cycle per day without failures; a 2012 study links failures to temperature variation, which is what a start/stop does; we therefore keep starts low." With the recommended band the busiest server sees 90–112 starts a year, about a third of one per day.

## 3. The script

`analysis/r2_realism.py` (new this round). Command, run from the repo root:

```
python3 analysis/r2_realism.py
```

It first checks itself against `simulate()` in `analysis/baseline_sweep.py` (case assumptions and a 3 kWh/day loss, N=6 and N=8: identical coverage, run hours and break-even). Full output is in the appendix.

Model choices (all *assumption* unless marked):

- **Tank loss** is taken from the tank every hour while it holds usable heat, as in the baseline. Not credited as room heating in winter (conservative).
- **Booster.** Share of hot-water energy served by server heat = (preheat − cold) ÷ (setpoint − cold), with cold water at 10 °C. Electric: the rest is resistance heat. Heat pump: the rest is delivered at COP 3, taking its source heat from the tank (so that part still counts as server heat). Booster electricity is added to electricity cost. `BE` values the booster's own heat at price ÷ 2.5 like any other heat; `BEstrict` does not.
- **Idle.** Paused servers draw `idle_frac` × 1 kW, 80% of it reaches the water. The rule knows this and runs fewer servers; idle heat that fits neither demand nor tank is dumped. Sold hours are running hours only.
- **Power-down with restart.** A paused server draws nothing. Each start makes `restart_min` minutes of run time unsold; the heat of those minutes is still delivered.
- **Rules.** `follow` is the baseline. `r1band` is the round-1 candidate from `analysis/demo_day_timing.py` (stop when the tank is full, restart when it has dropped by the band). `hold` uses the same band but (a) servers already running are kept until the tank cannot absorb their heat, (b) after such a forced stop no server is added until the tank has dropped by the band, unless demand needs it, (c) while refilling it runs one server more than the demand needs instead of as many as fit. `cap1` = at most one server when there is no space heating.
- **Hot-water shapes.** `flat` 0.5 kWh every hour; `peaked` 1.8 kWh at 06, 07, 08, 0.6 at 12, 13, 1.35 at 18–21 (45% / 10% / 45%); `spike` 6 kWh at 06 and at 19 as a bounding case.
- **Summer** = June to August.
- A start is counted per server slot (slot i runs when at least i servers run), so 3 servers starting in one hour are 3 starts.

Not modelled: the tank's temperature (a booster setpoint above the server-loop temperature also shrinks the usable 30 K spread); circulation losses; radiators needing 55–70 °C; standby draw of a powered-down server; lost work between the last checkpoint and a stop; forecast errors; finite job demand.

## 4. Results (*computed*)

### 4.1 How each switch moves the key figures

Change against case assumptions (N=6: 79.6% coverage, 0 dumped, 59.1% utilisation, 0.2261 CHF; N=8: 92.9%, 0, 51.8%, 0.2261). Follow rule unless stated.

| Switch | N | Coverage | Summer coverage | Dumped | Utilisation | Break-even CHF/server-h |
|---|---|---|---|---|---|---|
| Tank loss 1.68 kWh/d | 6 / 8 | −0.2 / −0.2 pts | 0 | 0 | +0.9 / +0.8 pts | +0.0018 / +0.0019 |
| Tank loss 2.80 kWh/d (central) | 6 / 8 | −0.3 / −0.3 | 0 | 0 | +1.5 / +1.4 | +0.0030 / +0.0031 |
| Tank loss 3.57 kWh/d (legal ceiling) | 6 / 8 | −0.4 / −0.4 | 0 | 0 | +1.9 / +1.7 | +0.0038 / +0.0039 |
| Electric booster, preheat 50 → 60 °C | 6 / 8 | −1.7 / −2.2 | −20.0 | 0 | −1.3 / −1.2 | +0.0058 / +0.0049 |
| Electric booster, 45 → 60 °C | 6 / 8 | −2.6 / −3.3 | −30.0 | 0 | −2.0 / −1.8 | +0.0087 / +0.0075 |
| Electric booster, 50 → 55 °C (no circulation) | 6 / 8 | −1.0 / −1.2 | −11.1 | 0 | −0.7 / −0.7 | +0.0032 / +0.0027 |
| No direct hot water at all (air-cooled case), electric | 6 / 8 | −9.1 / −11.3 | −100 | 0 | −6.7 / −6.3 | +0.0317 / +0.0274 |
| Heat-pump booster COP 3, 50 → 60 °C | 6 / 8 | −0.6 / −0.7 | −6.7 | 0 | −0.4 / −0.4 | +0.0019 / +0.0016 |
| Heat-pump booster COP 5, 50 → 60 °C | 6 / 8 | −0.3 / −0.4 | −4.0 | 0 | −0.3 / −0.2 | +0.0011 / +0.0010 |
| **Tank loss 2.80 + electric booster 50 → 60** | 6 / 8 | −2.1 / −2.4 | −20.0 | 0 | +0.2 / +0.2 | **+0.0087 / +0.0080** |
| **Tank loss 2.80 + heat-pump booster COP 3** | 6 / 8 | −0.9 / −1.0 | −6.7 | 0 | +1.1 / +1.0 | **+0.0049 / +0.0047** |
| Paused servers stay on, idle 17.6% | 6 / 8 | 0 / 0 | 0 | +1,312 / +2,391 kWh | −4.9 / −5.2 | **+0.0398 / +0.0553** |
| Paused servers stay on, idle 22.1% | 6 / 8 | 0 / 0 | 0 | +2,129 / +3,484 kWh | −5.1 / −5.7 | +0.0524 / +0.0727 |
| Powered down, 5 min per start, follow | 6 / 8 | 0 | 0 | 0 | 0 | +0.0011 / +0.0012 |
| Powered down, 15 min per start, follow | 6 / 8 | 0 | 0 | 0 | 0 | +0.0032 / +0.0035 |
| Powered down, 15 min per start, hold+cap1 band 8 | 6 / 8 | −0.12 / −0.14 | 0 | 0 | −0.1 / −0.1 | +0.0005 / +0.0010 |
| Hot water peaked instead of flat | 6 / 8 | −0.0 / −0.1 | 0 | 0 | −0.0 / −0.0 | 0.0000 |
| Hot water as two 6 kWh spikes | 6 / 8 | −0.1 / −0.1 | 0 | 0 | −0.1 / −0.1 | 0.0000 |

Booster electricity: 876 kWh/yr (electric, 50 → 60), 1,314 (45 → 60), 487 (50 → 55), 4,380 (no direct hot water), 292 (heat pump COP 3), 175 (COP 5).

Notes:
- Tank loss raises utilisation because the servers run 2.5% longer to feed the loss (N=6: 31,067 → 31,841 server-hours). More sold hours, but each one costs more: that is the +0.003.
- The summer drop under a booster is by construction the share of hot water the server loop cannot supply. It is a statement about the assumed temperatures, not a simulation result.
- Round 1 quoted "N=8 coverage 92.9% → 81.5%, break-even 0.2261 → 0.2300" for "3 kWh/day tank loss and no direct hot water". That row did not count the booster's electricity. With it counted: 81.7% and 0.2535 (no loss; electric), or 88.6% and 0.2362 with a heat pump at COP 2.5 heating all hot water.

### 4.2 Idle or power down

| | N=6 | N=8 |
|---|---|---|
| Idle heat of all servers at 17.6% | 20.3 kWh/day | 27.0 kWh/day |
| Summer hot-water demand | 12 kWh/day | 12 kWh/day |
| Server-hours sold June–August: powered down / idle 17.6% | 1,380 / **0** | 1,380 / **0** |
| Idle electricity per year at 17.6% | 4,242 kWh | 6,583 kWh |
| Heat dumped per year | 1,312 kWh | 2,391 kWh |
| Break-even | 0.2659 | 0.2814 |

Per pause (electricity only, lost sales not counted): a start costs 0.0188 CHF at 5 minutes and 0.0565 CHF at 15 minutes; an idle hour costs 0.0398 CHF if its heat is used and 0.0585 CHF if it is dumped (17.6% idle). **Power down for any pause longer than about 1 hour (15-minute restart) or about 20–30 minutes (5-minute restart).** Under the plain follow rule 1,540 of 1,726 pauses (N=6) last exactly one hour, so the rule and the pause mechanism have to be chosen together: with the recommended band no pause is shorter than 2 hours and the median pause is 13–16 hours, so power-down is always the right form.

Consequence for the demo wording: SIGSTOP on the laptop stands in for "checkpoint and power down". The balance may only count a paused server as 0 kW if the real unit powers down; that needs the restart time as a visible parameter (default 15 min until the model-load time is measured).

### 4.3 Band sweep

Case assumptions, flat hot water, powered down. Starts per year over all servers; run lengths in hours; break-even with 15 minutes unsold per start.

| Rule | Band kWh | N=6 coverage | N=6 starts | N=6 runs ≤ 1 h | N=6 BE | N=8 coverage | N=8 starts | N=8 runs ≤ 1 h | N=8 BE |
|---|---|---|---|---|---|---|---|---|---|
| follow | 0 | 79.58% | 1,732 | 553 | 0.2293 | 92.94% | 2,208 | 744 | 0.2296 |
| r1band (no cap) | 2 | 79.56% | 2,427 | 1,964 | 0.2306 | 92.94% | 2,926 | 2,161 | 0.2308 |
| r1band (no cap) | 8 | 79.54% | 1,470 | 260 | 0.2288 | 92.94% | 2,383 | 1,249 | 0.2299 |
| r1band+cap1 | 2 | 79.56% | 665 | 81 | 0.2273 | 92.94% | 1,154 | 277 | 0.2279 |
| r1band+cap1 | 4 | 79.56% | 481 | 74 | 0.2270 | 92.94% | 985 | 275 | 0.2276 |
| r1band+cap1 | 8 | 79.55% | 379 | 68 | 0.2268 | 92.94% | 891 | 266 | 0.2275 |
| r1band+cap1 | 16 | 79.51% | 303 | 64 | 0.2267 | 92.94% | 828 | 254 | 0.2274 |
| r1band+cap1 | 32 | 79.26% | 262 | 59 | 0.2266 | 92.94% | 771 | 240 | 0.2273 |
| hold+cap1 | 2 | 79.55% | 594 | 19 | 0.2272 | 92.89% | 1,055 | 104 | 0.2278 |
| hold+cap1 | 4 | 79.51% | 385 | 4 | 0.2268 | 92.88% | 782 | 13 | 0.2273 |
| **hold+cap1** | **8** | **79.46%** | **267** | 13 | **0.2266** | **92.80%** | **607** | 23 | **0.2271** |
| hold+cap1 | 12 | 79.42% | 190 | 0 | 0.2264 | 92.79% | 532 | 13 | 0.2269 |
| hold+cap1 | 16 | 79.37% | 168 | 0 | 0.2264 | 92.65% | 466 | 1 | 0.2268 |
| hold+cap1 | 24 | 79.18% | 139 | 0 | 0.2264 | 92.56% | 313 | 1 | 0.2266 |
| hold+cap1 | 32 | 79.13% | 125 | 0 | 0.2263 | 92.34% | 298 | 0 | 0.2266 |

Longest run: 1,920–1,921 hours (80 days) for follow and r1band; up to 2,255 h (N=6) and 1,942 h (N=8) for hold+cap1 at band 8. Shortest run: 1 hour in every row except a few hold rows (see appendix); the count of one-hour runs is the more useful figure.

Starts per server slot at band 8 (slot 1 = the server that stops last):

| | N=6 | N=8 |
|---|---|---|
| follow | 1433, 17, 28, 60, 96, 98 | 1434, 22, 39, 89, 145, 177, 199, 103 |
| r1band+cap1, 8 kWh | 97, 18, 29, 58, 84, 93 | 98, 22, 39, 89, 144, 178, 204, 117 |
| hold+cap1, 8 kWh | 90, 18, 23, 36, 49, 51 | 92, 21, 31, 60, 91, 105, 112, 95 |

Findings:
- **The band alone, without the cap, makes cycling worse** (2 kWh: 2,427 starts against 1,732 at N=6): when the tank has dropped by the band, as many servers as fit start together for one hour. The round-1 figure of 1,146 starts at N=8 with a 2 kWh band is reproduced with the cap (1,154 here; this script also counts a start in the first hour of the year and counts per slot).
- **The flapping has two sources.** Summer: one server on and off every other hour (828 of the starts). Any band with the cap fixes it: 207 summer starts at 2 kWh, 52 at 8 kWh, 26 at 16 kWh. Heating season: the last server that fits toggles hourly around a full tank; the round-1 rule does not touch that (N=8 stays at about 770–890 starts whatever the band), the hold rule does.
- **Why 8 kWh.** (1) It is the knee: from 0 to 8 kWh starts fall by 85% (N=6) and 73% (N=8); from 8 to 16 kWh they fall by a further 6 percentage points of the original count while the coverage loss doubles (N=8: −0.14 → −0.29 points). (2) In summer the cycle becomes one run of about 27 hours every 43 hours (8 kWh ÷ 0.3 kW net charging; 8 kWh ÷ 0.5 kW draw = 16 h off), so a run is longer than the 24 h job and every pause is far above the 1-hour idle-or-off threshold. (3) 8 kWh is 23% of the tank, so 27 kWh stay in reserve for cold hours; that is why coverage moves by only 0.1 point. (4) The busiest server drops from 1,433 starts a year to about 90, under one start every four days.
- **It survives realism.** With 2.80 kWh/day loss and peaked hot water, hold+cap1 at 8 kWh gives 260 starts (N=6) and 686 (N=8), shortest run 2 h at N=6, coverage −0.09 / −0.12 points against follow under the same switches.
- Limits: the hold rule is a sketch with perfect knowledge of the current hour only and no deadlines. "One server more than demand needs" while refilling is one arbitrary choice among several; the team's scheduler has a forecast and can do better. The numbers show that a band plus "do not stop what runs" is worth about 1,500 starts a year, not that this exact rule is the one to ship.

### 4.4 Hot-water shape

| | N=6 flat | N=6 peaked | N=6 spikes | N=8 flat | N=8 peaked | N=8 spikes |
|---|---|---|---|---|---|---|
| Coverage, case assumptions | 79.58% | 79.5% | 79.5% | 92.94% | 92.9% | 92.8% |
| Break-even | 0.2261 | 0.2261 | 0.2261 | 0.2261 | 0.2261 | 0.2261 |
| Coverage, loss + electric booster | 77.5% | 77.5% | 77.4% | 90.5% | 90.4% | 90.4% |

With a 10 kWh tank instead of 35 the peaked shape costs 0.19 (N=6) and 0.12 (N=8) points; with 5 kWh, 0.39 and 0.29 points. So the statement in `assumption-limits.md` ("because hot water is drawn from the 35 kWh tank, the timing mostly doesn't matter") is confirmed, and the exception it names (cold mornings with an empty tank) is worth at most 0.1 coverage points a year. The flat shape can stay the default; the peaked comparison is one line in the assumptions list and can stay on the cut list.

### 4.5 6 versus 8, case against a combined realistic run

Realistic = tank loss 2.80 kWh/day, hot water peaked, booster 50 → 60 °C, powered down when paused, hold+cap1 with 8 kWh band, 15 minutes unsold per start.

| | N | Coverage | Summer | Dumped | Utilisation | Server-h sold | Starts | Electricity CHF (incl. booster) | Break-even |
|---|---|---|---|---|---|---|---|---|---|
| Case assumptions | 6 | 79.6% | 100% | 0 | 59.1% | 31,067 | 1,732 | 10,330 | 0.2261 |
| Realistic, electric booster | 6 | 77.4% | 80.0% | 0 | 59.2% | 31,056 | 279 | 10,641 | 0.2354 |
| Realistic, heat-pump booster | 6 | 78.5% | 93.3% | 0 | 60.0% | 31,495 | 269 | 10,591 | 0.2315 |
| Case assumptions | 8 | 92.9% | 100% | 0 | 51.8% | 36,281 | 2,208 | 12,063 | 0.2261 |
| Realistic, electric booster | 8 | 90.3% | 80.0% | 0 | 51.9% | 36,192 | 657 | 12,380 | 0.2352 |
| Realistic, heat-pump booster | 8 | 91.7% | 93.3% | 0 | 52.7% | 36,734 | 681 | 12,368 | 0.2319 |

Gap 8 minus 6: coverage +13.4 points (case) → +13.0 (electric) / +13.2 (heat pump); utilisation −7.3 → −7.3 / −7.4 points; break-even 0.0000 → −0.0002 / +0.0004 CHF.

**No realism switch changes the choice between 6 and 8.** Tank loss, booster, hot-water shape and restart cost hit both by the same amount within 0.001 CHF and 0.5 coverage points. Two things do differ and belong next to the table:
- If paused servers are left powered, 8 is hit harder than 6 (break-even 0.2814 against 0.2659; 2,391 against 1,312 kWh dumped). With power-down this disappears.
- 8 servers cycle more: 607 against 267 starts a year with the recommended band; servers 6 to 8 start 105, 112 and 95 times a year at N=8.

Run hours of the top servers in the realistic run (hours in which at least i servers run): server 6 at N=6: 4,562; servers 6, 7, 8 at N=8: 3,899, 3,546, 3,236 (electric booster). These are slot hours inside one configuration and are not the same quantity as the marginal figures in the plan (3,796, 2,933, 2,281 h, which are differences between runs with N−1 and N servers).

## 5. What this means for the plan

1. `assumption-limits.md`: the 2–4 kWh/day and "≥ 60 °C" lines can now carry sources (section 2). The file itself was not edited. Two corrections for whoever does: the EU label stops at 500 litres, so "energy labels for 1,000 L tanks" should read "ecodesign limit (814/2013) and manufacturer data sheets"; and 60 °C applies with warm-held pipes, 55 °C without.
2. The pitch sentence can be said with numbers (section 1, item 3). Say "with our assumption that the server loop reaches 50 °C".
3. Open risk 6 (pause physics) splits into a solved part (idle power is 18–22% of full power; leaving servers on in summer is not an option; a restart costs under 0.004 CHF per server-hour even without a band) and an open part (the restart time is an assumption until the model-load time is measured; no cycling limit exists in the literature we found).
4. The band is no longer "2 kWh, arbitrary". Candidate for adoption: 8 kWh, cap of one server without space heating, and keep running servers running.
5. Founder objections 6 and 7 from round 1 have answers: 6 → "a real unit powers down for any pause over an hour; a start costs 15 minutes of unsold time, about 0.06 CHF; our rule makes no pause shorter than 2 hours"; 7 → "about 270 starts a year for 6 servers, 90 for the busiest; the only field evidence we found is one small sample at one cycle a day without failures".

## 6. What is still weak

- One manufacturer for the tank, one CPU server and one GPU node for idle power, one 2007 blog for cycling. Enough to replace "unverified", not enough for "typical".
- The 50 °C preheat is the input that decides the summer figure and it is an assumption. A vendor outlet-temperature figure for a current warm-water-cooled server was not found.
- Booster COP 3 is an assumption; no data sheet was opened.
- EN 12897 test temperatures not confirmed; the loss was not rescaled to the tank's real temperature.
- Server boot time has no opened source.
- The hold rule is exploratory and was tested only with unlimited jobs. Its interaction with deadlines and with the other investigators' admission rule is untested.
- The booster also raises a question the model does not ask: if the tank must be kept near 60 °C for hot water, the server loop at 45–50 °C cannot charge the top of it, and the usable 35 kWh shrinks.

## Appendix: full output of `python3 analysis/r2_realism.py`

```
== 0. Regression check against analysis/baseline_sweep.py simulate() ==
  N=6 case: baseline cov 79.581% run_h 31067 BE 0.2261 | this file cov 79.581% run_h 31067 BE 0.2261 -> OK
  N=6 {'tank_loss_kwh_day': 3.0}: baseline cov 79.233% run_h 31895 BE 0.2293 | this file cov 79.233% run_h 31895 BE 0.2293 -> OK
  N=8 case: baseline cov 92.937% run_h 36281 BE 0.2261 | this file cov 92.937% run_h 36281 BE 0.2261 -> OK
  N=8 {'tank_loss_kwh_day': 3.0}: baseline cov 92.617% run_h 37309 BE 0.2294 | this file cov 92.617% run_h 37309 BE 0.2294 -> OK
  summer = June to August; BE = break-even CHF per server-hour sold (booster heat valued); BEstrict = booster electricity charged, its heat not valued

== inputs (status in the research file) ==
  loss_classA_934l       1.68
  loss_classC_934l       2.8
  loss_classC_887l       3.38
  loss_erp_limit_1000l   3.5684
  t_set_c                60.0
  t_set_nocirc_c         55.0
  t_cold_c               10.0
  t_pre_c                50.0
  cop_booster            3.0
  idle_cpu               0.176
  idle_gpu               0.2206
  restart_min            (5.0, 15.0)

== (i)+(ii) tank standing loss, follow rule ==
case                               N   cover  summer   dump tankloss   util   srv-h boostkWh      BE BEstrict
case assumptions (no loss)         6   79.6%  100.0%      0        0  59.1%   31067        0  0.2261   0.2261
loss 1.68 kWh/d (classA_934l)      6   79.4%  100.0%      0      434  60.0%   31534        0  0.2279   0.2279
   -> coverage -0.2 pts, summer +0.0 pts, dumped +0 kWh, util +0.9 pts, BE +0.0018 CHF/h
loss 2.80 kWh/d (classC_934l)      6   79.3%  100.0%      0      720  60.6%   31841        0  0.2291   0.2291
   -> coverage -0.3 pts, summer +0.0 pts, dumped +0 kWh, util +1.5 pts, BE +0.0030 CHF/h
loss 3.38 kWh/d (classC_887l)      6   79.2%  100.0%      0      867  60.9%   31999        0  0.2297   0.2297
   -> coverage -0.4 pts, summer +0.0 pts, dumped +0 kWh, util +1.8 pts, BE +0.0036 CHF/h
loss 3.57 kWh/d (erp_limit_1000l)  6   79.2%  100.0%      0      914  61.0%   32049        0  0.2299   0.2299
   -> coverage -0.4 pts, summer +0.0 pts, dumped +0 kWh, util +1.9 pts, BE +0.0038 CHF/h
case assumptions (no loss)         8   92.9%  100.0%      0        0  51.8%   36281        0  0.2261   0.2261
loss 1.68 kWh/d (classA_934l)      8   92.8%  100.0%      0      520  52.6%   36859        0  0.2280   0.2280
   -> coverage -0.2 pts, summer +0.0 pts, dumped +0 kWh, util +0.8 pts, BE +0.0019 CHF/h
loss 2.80 kWh/d (classC_934l)      8   92.6%  100.0%      0      862  53.1%   37243        0  0.2292   0.2292
   -> coverage -0.3 pts, summer +0.0 pts, dumped +0 kWh, util +1.4 pts, BE +0.0031 CHF/h
loss 3.38 kWh/d (classC_887l)      8   92.6%  100.0%      0     1038  53.4%   37441        0  0.2298   0.2298
   -> coverage -0.4 pts, summer +0.0 pts, dumped +0 kWh, util +1.7 pts, BE +0.0037 CHF/h
loss 3.57 kWh/d (erp_limit_1000l)  8   92.6%  100.0%      0     1095  53.5%   37505        0  0.2300   0.2300
   -> coverage -0.4 pts, summer +0.0 pts, dumped +0 kWh, util +1.7 pts, BE +0.0039 CHF/h

== (iii) hot-water booster, no tank loss, follow rule ==
case                               N   cover  summer   dump tankloss   util   srv-h boostkWh      BE BEstrict
case assumptions (no booster)      6   79.6%  100.0%      0        0  59.1%   31067        0  0.2261   0.2261
electric, preheat 50 -> 60 C       6   77.8%   80.0%      0        0  57.8%   30389      876  0.2319   0.2357
   -> coverage -1.7 pts, summer -20.0 pts, dumped +0 kWh, util -1.3 pts, BE +0.0058 CHF/h
electric, preheat 45 -> 60 C       6   76.9%   70.0%      0        0  57.1%   30036     1314  0.2348   0.2406
   -> coverage -2.6 pts, summer -30.0 pts, dumped +0 kWh, util -2.0 pts, BE +0.0087 CHF/h
electric, preheat 50 -> 55 C       6   78.6%   88.9%      0        0  58.4%   30694      487  0.2293   0.2314
   -> coverage -1.0 pts, summer -11.1 pts, dumped +0 kWh, util -0.7 pts, BE +0.0032 CHF/h
electric, no direct hot water      6   70.5%    0.0%      0        0  52.4%   27525     4380  0.2578   0.2790
   -> coverage -9.1 pts, summer -100.0 pts, dumped +0 kWh, util -6.7 pts, BE +0.0317 CHF/h
heat pump COP 3, 50 -> 60 C        6   79.0%   93.3%      0        0  58.7%   30845      292  0.2280   0.2292
   -> coverage -0.6 pts, summer -6.7 pts, dumped +0 kWh, util -0.4 pts, BE +0.0019 CHF/h
heat pump COP 3, 45 -> 60 C        6   78.7%   90.0%      0        0  58.5%   30731      438  0.2289   0.2308
   -> coverage -0.9 pts, summer -10.0 pts, dumped +0 kWh, util -0.6 pts, BE +0.0028 CHF/h
heat pump COP 5, 50 -> 60 C        6   79.2%   96.0%      0        0  58.9%   30933      175  0.2272   0.2280
   -> coverage -0.3 pts, summer -4.0 pts, dumped +0 kWh, util -0.3 pts, BE +0.0011 CHF/h
heat pump COP 2.5, all hot water   6   76.0%   60.0%      0        0  56.5%   29682     1752  0.2379   0.2457
   -> coverage -3.5 pts, summer -40.0 pts, dumped +0 kWh, util -2.6 pts, BE +0.0118 CHF/h
case assumptions (no booster)      8   92.9%  100.0%      0        0  51.8%   36281        0  0.2261   0.2261
electric, preheat 50 -> 60 C       8   90.8%   80.0%      0        0  50.6%   35437      876  0.2310   0.2343
   -> coverage -2.2 pts, summer -20.0 pts, dumped +0 kWh, util -1.2 pts, BE +0.0049 CHF/h
electric, preheat 45 -> 60 C       8   89.7%   70.0%      0        0  49.9%   35004     1314  0.2336   0.2386
   -> coverage -3.3 pts, summer -30.0 pts, dumped +0 kWh, util -1.8 pts, BE +0.0075 CHF/h
electric, preheat 50 -> 55 C       8   91.8%   88.9%      0        0  51.1%   35819      487  0.2288   0.2306
   -> coverage -1.2 pts, summer -11.1 pts, dumped +0 kWh, util -0.7 pts, BE +0.0027 CHF/h
electric, no direct hot water      8   81.7%    0.0%      0        0  45.5%   31886     4380  0.2535   0.2718
   -> coverage -11.3 pts, summer -100.0 pts, dumped +0 kWh, util -6.3 pts, BE +0.0274 CHF/h
heat pump COP 3, 50 -> 60 C        8   92.2%   93.3%      0        0  51.4%   36005      292  0.2277   0.2288
   -> coverage -0.7 pts, summer -6.7 pts, dumped +0 kWh, util -0.4 pts, BE +0.0016 CHF/h
heat pump COP 3, 45 -> 60 C        8   91.9%   90.0%      0        0  51.2%   35866      438  0.2285   0.2302
   -> coverage -1.1 pts, summer -10.0 pts, dumped +0 kWh, util -0.6 pts, BE +0.0024 CHF/h
heat pump COP 5, 50 -> 60 C        8   92.5%   96.0%      0        0  51.5%   36116      175  0.2271   0.2277
   -> coverage -0.4 pts, summer -4.0 pts, dumped +0 kWh, util -0.2 pts, BE +0.0010 CHF/h
heat pump COP 2.5, all hot water   8   88.6%   60.0%      0        0  49.3%   34572     1752  0.2362   0.2430
   -> coverage -4.4 pts, summer -40.0 pts, dumped +0 kWh, util -2.4 pts, BE +0.0101 CHF/h

== (ii)+(iii) together: 'realistic' = tank loss 2.80 kWh/d + booster 50 -> 60 C ==
case                               N   cover  summer   dump tankloss   util   srv-h boostkWh      BE BEstrict
case assumptions                   6   79.6%  100.0%      0        0  59.1%   31067        0  0.2261   0.2261
loss + electric booster            6   77.5%   80.0%      0      729  59.3%   31178      876  0.2348   0.2386
   -> coverage -2.1 pts, summer -20.0 pts, dumped +0 kWh, util +0.2 pts, BE +0.0087 CHF/h
loss + heat-pump booster COP 3     6   78.7%   93.3%      0      723  60.2%   31622      292  0.2310   0.2322
   -> coverage -0.9 pts, summer -6.7 pts, dumped +0 kWh, util +1.1 pts, BE +0.0049 CHF/h
case assumptions                   8   92.9%  100.0%      0        0  51.8%   36281        0  0.2261   0.2261
loss + electric booster            8   90.5%   80.0%      0      872  52.0%   36418      876  0.2341   0.2373
   -> coverage -2.4 pts, summer -20.0 pts, dumped +0 kWh, util +0.2 pts, BE +0.0080 CHF/h
loss + heat-pump booster COP 3     8   91.9%   93.3%      0      865  52.7%   36967      292  0.2308   0.2318
   -> coverage -1.0 pts, summer -6.7 pts, dumped +0 kWh, util +1.0 pts, BE +0.0047 CHF/h
  sensitivity of the electric-booster pair to the tank loss (N=6 / N=8: summer drop pts, BE rise CHF/h):
    loss 1.68: N=6: 20.0 pts, +0.0076 | N=8: 20.0 pts, +0.0068
    loss 2.80: N=6: 20.0 pts, +0.0087 | N=8: 20.0 pts, +0.0080
    loss 3.38: N=6: 20.0 pts, +0.0093 | N=8: 20.0 pts, +0.0086
    loss 3.57: N=6: 20.0 pts, +0.0095 | N=8: 20.0 pts, +0.0088

== (iv) paused servers: powered and idle, or powered down with a restart penalty ==
  a) paused-but-on all year (SIGSTOP on a real unit). idle heat is used when demand or tank can take it, else dumped
  case                       N   cover  summer    dump   util   srv-h summer srv-h  idle kWh  elec CHF      BE
  powered down (case)        6   79.6%  100.0%       0  59.1%   31067         1380         0     10330  0.2261
  idle 17.6 % (CPU server)   6   79.6%  100.0%    1312  54.2%   28467            0      4242     10876  0.2659
  idle 22.1 % (GPU node)     6   79.6%  100.0%    2129  54.0%   28400            0      5331     11215  0.2785
  idle 5 %                   6   79.6%  100.0%       0  57.0%   29937          755      1131     10330  0.2346
     idle heat of 6 paused servers at 17.6 %: 20.3 kWh/day against 12 kWh/day summer hot water
  powered down (case)        8   92.9%  100.0%       0  51.8%   36281         1380         0     12063  0.2261
  idle 17.6 % (CPU server)   8   92.9%  100.0%    2391  46.6%   32687            0      6583     13057  0.2814
  idle 22.1 % (GPU node)     8   92.9%  100.0%    3484  46.1%   32301            0      8336     13512  0.2988
  idle 5 %                   8   92.9%  100.0%       0  49.2%   34502          523      1779     12063  0.2378
     idle heat of 8 paused servers at 17.6 %: 27.0 kWh/day against 12 kWh/day summer hot water
  b) powered down; each start costs restart_min of unsold run time (heat still delivered). follow rule, no band
     N=6 restart    0 min: starts  1732, unsold      0 h (0.00 % of run hours), BE 0.2261 (+0.0000)
     N=6 restart    5 min: starts  1732, unsold    144 h (0.46 % of run hours), BE 0.2272 (+0.0011)
     N=6 restart   15 min: starts  1732, unsold    433 h (1.39 % of run hours), BE 0.2293 (+0.0032)
     N=8 restart    0 min: starts  2208, unsold      0 h (0.00 % of run hours), BE 0.2261 (+0.0000)
     N=8 restart    5 min: starts  2208, unsold    184 h (0.51 % of run hours), BE 0.2273 (+0.0012)
     N=8 restart   15 min: starts  2208, unsold    552 h (1.52 % of run hours), BE 0.2296 (+0.0035)

== (v) hysteresis band sweep (case assumptions, flat hot water) ==
  N=6
  rule             band    cover   srv-h starts run min median    max  <=1h  <=3h  BE@5min BE@15min summer starts
  follow              0   79.58%   31067   1732       1      2   1920   553  1535   0.2272   0.2293           828
  r1band              1   79.58%   31066   1728       1      1   1920  1024  1530   0.2272   0.2293           552
  r1band              2   79.56%   31060   2427       1      1   1920  1964  2232   0.2276   0.2306           414
  r1band              4   79.56%   31060   2060       1      1   1920  1480  1862   0.2274   0.2299           207
  r1band              8   79.54%   31050   1470       1      2   1920   260  1280   0.2270   0.2288           118
  r1band             12   79.51%   31038   1029       1      3   1920    59   784   0.2267   0.2280            78
  r1band             16   79.48%   31028    828       1      4   1920    59   274   0.2266   0.2276            59
  r1band             24   79.33%   30969    599       1      6   1920    49    66   0.2265   0.2272            39
  r1band             32   79.27%   30945    514       1      8   1920    59    87   0.2264   0.2270            31
  r1band+cap1         1   79.58%   31066   1023       1      3   1920    81   591   0.2267   0.2280           414
  r1band+cap1         2   79.56%   31060    665       1      7   1920    81   116   0.2265   0.2273           207
  r1band+cap1         4   79.56%   31060    481       1     13   1920    74   106   0.2264   0.2270           103
  r1band+cap1         8   79.55%   31055    379       1     20   1920    68   104   0.2263   0.2268            52
  r1band+cap1        12   79.53%   31047    340       1     19   1920    70    97   0.2263   0.2267            34
  r1band+cap1        16   79.51%   31040    303       1     19   1920    64    90   0.2263   0.2267            26
  r1band+cap1        24   79.35%   30976    268       1     18   1920    57    79   0.2263   0.2266            18
  r1band+cap1        32   79.26%   30940    262       1     16   1920    59    85   0.2263   0.2266            13
  hold                1   79.56%   31060   1714       1      1   1920  1012  1516   0.2271   0.2293           552
  hold                2   79.54%   31052   1191       1      4   1920   488   529   0.2268   0.2283           276
  hold                4   79.54%   31051    772       2      5   1923     0   304   0.2266   0.2275           166
  hold                8   79.48%   31027    478       1      8   1931     3    21   0.2264   0.2270            92
  hold               12   79.40%   30998    332       3     13   1931     0     1   0.2263   0.2267            62
  hold               16   79.34%   30972    272       1     16   1931     1     2   0.2263   0.2266            46
  hold               24   79.25%   30938    203      12     24   1931     0     0   0.2262   0.2265            31
  hold               32   79.08%   30870    174       2     38   1931     0     1   0.2262   0.2264            23
  hold+cap1           1   79.56%   31060   1003       1      3   1920    68   574   0.2267   0.2279           414
  hold+cap1           2   79.55%   31056    594       1      7   1920    19    49   0.2265   0.2272           207
  hold+cap1           4   79.51%   31041    385       1     14   1933     4    34   0.2263   0.2268           103
  hold+cap1           8   79.46%   31018    267       1     27   2255    13    25   0.2263   0.2266            52
  hold+cap1          12   79.42%   31005    190       2     40   2457     0     2   0.2262   0.2264            34
  hold+cap1          16   79.37%   30986    168       7     54   2457     0     0   0.2262   0.2264            26
  hold+cap1          24   79.18%   30911    139      12     80   2443     0     0   0.2262   0.2264            18
  hold+cap1          32   79.13%   30891    125       5    106   2435     0     0   0.2262   0.2263            13
  N=8
  rule             band    cover   srv-h starts run min median    max  <=1h  <=3h  BE@5min BE@15min summer starts
  follow              0   92.94%   36281   2208       1      2   1921   744  1775   0.2273   0.2296           828
  r1band              1   92.94%   36281   2218       1      1   1921  1225  1786   0.2273   0.2296           552
  r1band              2   92.94%   36281   2926       1      1   1921  2161  2486   0.2276   0.2308           414
  r1band              4   92.94%   36281   2564       1      1   1921  1680  2121   0.2274   0.2302           207
  r1band              8   92.94%   36281   2383       1      1   1921  1249  1932   0.2273   0.2299           118
  r1band             12   92.94%   36281   1859       1      2   1921   254  1402   0.2271   0.2290            83
  r1band             16   92.94%   36281   1585       1      3   1921   253  1083   0.2269   0.2286            62
  r1band             24   92.94%   36281   1291       1      4   1921   244   318   0.2268   0.2281            41
  r1band             32   92.94%   36281   1134       1      5   1921   242   315   0.2267   0.2279            31
  r1band+cap1         1   92.94%   36281   1502       1      3   1921   275   834   0.2269   0.2285           414
  r1band+cap1         2   92.94%   36281   1154       1      7   1921   277   367   0.2267   0.2279           207
  r1band+cap1         4   92.94%   36281    985       1     12   1921   275   368   0.2266   0.2276           103
  r1band+cap1         8   92.94%   36281    891       1      9   1921   266   366   0.2266   0.2275            52
  r1band+cap1        12   92.94%   36281    852       1      9   1921   267   351   0.2265   0.2274            34
  r1band+cap1        16   92.94%   36281    828       1      9   1921   254   337   0.2265   0.2274            26
  r1band+cap1        24   92.94%   36281    796       1     10   1921   245   317   0.2265   0.2273            18
  r1band+cap1        32   92.94%   36281    771       1      9   1921   240   313   0.2265   0.2273            13
  hold                1   92.93%   36277   2229       1      1   1921  1222  1797   0.2273   0.2296           552
  hold                2   92.89%   36262   1647       1      4   1921   565   738   0.2270   0.2287           276
  hold                4   92.88%   36258   1169       1      5   1921    11   410   0.2267   0.2279           166
  hold                8   92.81%   36230    811       1      8   1924     7    49   0.2265   0.2274            92
  hold               12   92.79%   36222    683       1     12   1932     1    10   0.2265   0.2272            62
  hold               16   92.65%   36170    579       2     14   1932     0     1   0.2264   0.2270            46
  hold               24   92.56%   36133    396       1     21   1932     2     6   0.2263   0.2267            31
  hold               32   92.34%   36047    349       2     29   1932     0     1   0.2263   0.2266            23
  hold+cap1           1   92.93%   36277   1520       1      3   1921   278   856   0.2269   0.2285           414
  hold+cap1           2   92.89%   36262   1055       1      7   1921   104   264   0.2266   0.2278           207
  hold+cap1           4   92.88%   36258    782       1     13   1921    13   128   0.2265   0.2273           103
  hold+cap1           8   92.80%   36228    607       1     14   1942    23    50   0.2264   0.2271            52
  hold+cap1          12   92.79%   36222    532       1     13   2416    13    16   0.2264   0.2269            35
  hold+cap1          16   92.65%   36170    466       1     13   2416     1     2   0.2263   0.2268            26
  hold+cap1          24   92.56%   36133    313       1     24   2416     1     3   0.2263   0.2266            17
  hold+cap1          32   92.34%   36047    298       2     30   2471     0     1   0.2263   0.2266            13

  band sweep again with tank loss 2.80 kWh/d and peaked hot water (does the recommendation survive?)
  N=6
  rule             band    cover   srv-h starts run min median    max  <=1h  <=3h  BE@5min BE@15min summer starts
  follow              0   79.18%   31826   1574       1      3   1920   537  1161   0.2301   0.2320           552
  r1band+cap1         2   79.18%   31825    525       1     10   1920    54    74   0.2295   0.2301           138
  r1band+cap1         4   79.18%   31824    454       1     18   1920    53    70   0.2294   0.2300            92
  r1band+cap1         8   79.14%   31808    368       1     20   1920    47    74   0.2294   0.2298            46
  r1band+cap1        12   79.14%   31810    324       1     19   1920    43    66   0.2294   0.2297            30
  r1band+cap1        16   79.09%   31788    277       1     18   1920    41    55   0.2293   0.2297            18
  r1band+cap1        24   78.96%   31732    241       1     20   1920    30    41   0.2293   0.2296            13
  hold+cap1           2   79.16%   31818    459       1     12   1920     4    17   0.2294   0.2300           138
  hold+cap1           4   79.13%   31805    380       1     18   1920     4    11   0.2294   0.2298            92
  hold+cap1           8   79.09%   31788    260       2     37   2224     0    40   0.2293   0.2296            46
  hold+cap1          12   79.05%   31773    207       1     55   2224     7    17   0.2293   0.2295            30
  hold+cap1          16   79.00%   31752    151       1     92   2224     5    10   0.2292   0.2294            19
  hold+cap1          24   78.88%   31698    134      10     95   2224     0     0   0.2292   0.2294            13
  N=8
  rule             band    cover   srv-h starts run min median    max  <=1h  <=3h  BE@5min BE@15min summer starts
  follow              0   92.55%   37220   2275       1      3   1920   736  1393   0.2304   0.2328           506
  r1band+cap1         2   92.55%   37220   1266       1      7   1920   281   448   0.2299   0.2312           138
  r1band+cap1         4   92.55%   37220   1178       1      6   1920   273   444   0.2298   0.2310            92
  r1band+cap1         8   92.55%   37220   1104       1      5   1920   257   442   0.2298   0.2309            46
  r1band+cap1        12   92.55%   37220   1065       1      5   1920   249   427   0.2298   0.2309            30
  r1band+cap1        16   92.55%   37220   1021       1      5   1920   240   392   0.2297   0.2308            18
  r1band+cap1        24   92.55%   37220    973       1      6   1920   216   356   0.2297   0.2307            13
  hold+cap1           2   92.52%   37208   1102       1      8   1920    51   286   0.2298   0.2309           138
  hold+cap1           4   92.48%   37192    946       1     14   1920    19   189   0.2297   0.2307            92
  hold+cap1           8   92.43%   37170    686       1     16   1937     5    74   0.2296   0.2303            46
  hold+cap1          12   92.42%   37167    603       1     15   2223    14    51   0.2295   0.2301            31
  hold+cap1          16   92.31%   37118    517       1     14   2223    26    33   0.2295   0.2300            18
  hold+cap1          24   92.20%   37072    382       2     16   2416     0     4   0.2294   0.2298            13

  starts per server slot and pause lengths (slot 1 = last server to stop), powered down, case assumptions
     N=6 follow               starts per slot [1433, 17, 28, 60, 96, 98]  max 1433/yr; pauses 1726, of 1 h: 1540, of <=3 h: 1585, median 1 h, longest 2916 h
     N=6 r1band+cap1 band 8   starts per slot [97, 18, 29, 58, 84, 93]  max 97/yr; pauses 373, of 1 h: 93, of <=3 h: 137, median 9 h, longest 2893 h
     N=6 hold+cap1 band 8     starts per slot [90, 18, 23, 36, 49, 51]  max 90/yr; pauses 261, of 1 h: 0, of <=3 h: 2, median 16 h, longest 2900 h
     N=8 follow               starts per slot [1434, 22, 39, 89, 145, 177, 199, 103]  max 1434/yr; pauses 2200, of 1 h: 1721, of <=3 h: 1808, median 1 h, longest 3139 h
     N=8 r1band+cap1 band 8   starts per slot [98, 22, 39, 89, 144, 178, 204, 117]  max 204/yr; pauses 883, of 1 h: 281, of <=3 h: 370, median 6 h, longest 2898 h
     N=8 hold+cap1 band 8     starts per slot [92, 21, 31, 60, 91, 105, 112, 95]  max 112/yr; pauses 599, of 1 h: 0, of <=3 h: 0, median 13 h, longest 3021 h

  idle or power down? pause length above which powering down is cheaper (electricity only, no lost sales)
     idle 17.6 %, restart 5 min: start costs 0.0188 CHF; idle hour costs 0.0398 CHF if its heat is used, 0.0585 CHF if dumped -> power down for pauses longer than 0.5 h (heat used) / 0.3 h (heat dumped)
     idle 17.6 %, restart 15 min: start costs 0.0565 CHF; idle hour costs 0.0398 CHF if its heat is used, 0.0585 CHF if dumped -> power down for pauses longer than 1.4 h (heat used) / 1.0 h (heat dumped)
     idle 22.1 %, restart 5 min: start costs 0.0188 CHF; idle hour costs 0.0499 CHF if its heat is used, 0.0734 CHF if dumped -> power down for pauses longer than 0.4 h (heat used) / 0.3 h (heat dumped)
     idle 22.1 %, restart 15 min: start costs 0.0565 CHF; idle hour costs 0.0499 CHF if its heat is used, 0.0734 CHF if dumped -> power down for pauses longer than 1.1 h (heat used) / 0.8 h (heat dumped)

== (vi) hot-water shape: flat vs peaked vs two spikes of 6 kWh ==
case                               N   cover  summer   dump tankloss   util   srv-h boostkWh      BE BEstrict
case, hot water flat               6   79.6%  100.0%      0        0  59.1%   31067        0  0.2261   0.2261
case, hot water peaked             6   79.5%  100.0%      0        0  59.1%   31051        0  0.2261   0.2261
   -> coverage -0.0 pts, summer +0.0 pts, dumped +0 kWh, util -0.0 pts, BE +0.0000 CHF/h
case, hot water spike              6   79.5%  100.0%      0        0  59.0%   31036        0  0.2261   0.2261
   -> coverage -0.1 pts, summer +0.0 pts, dumped +0 kWh, util -0.1 pts, BE -0.0000 CHF/h
loss+el. booster, flat             6   77.5%   80.0%      0      729  59.3%   31178      876  0.2348   0.2386
loss+el. booster, peaked           6   77.5%   80.0%      0      739  59.3%   31166      876  0.2349   0.2386
loss+el. booster, spike            6   77.4%   80.0%      0      743  59.3%   31154      876  0.2349   0.2386
   tank 10 kWh instead of 35: flat 78.78% -> peaked 78.59%
   tank 5 kWh instead of 35: flat 78.06% -> peaked 77.67%
case, hot water flat               8   92.9%  100.0%      0        0  51.8%   36281        0  0.2261   0.2261
case, hot water peaked             8   92.9%  100.0%      0        0  51.7%   36258        0  0.2261   0.2261
   -> coverage -0.1 pts, summer +0.0 pts, dumped +0 kWh, util -0.0 pts, BE +0.0000 CHF/h
case, hot water spike              8   92.8%  100.0%      0        0  51.7%   36240        0  0.2261   0.2261
   -> coverage -0.1 pts, summer +0.0 pts, dumped +0 kWh, util -0.1 pts, BE +0.0000 CHF/h
loss+el. booster, flat             8   90.5%   80.0%      0      872  52.0%   36418      876  0.2341   0.2373
loss+el. booster, peaked           8   90.4%   80.0%      0      880  51.9%   36400      876  0.2341   0.2373
loss+el. booster, spike            8   90.4%   80.0%      0      885  51.9%   36387      876  0.2341   0.2373
   tank 10 kWh instead of 35: flat 92.17% -> peaked 92.05%
   tank 5 kWh instead of 35: flat 91.74% -> peaked 91.45%

== 6 versus 8: case assumptions against the combined realistic run ==
  realistic = tank loss 2.80 kWh/d, hot water peaked, booster 50 -> 60 C, powered down when paused,
  rule hold+cap1 with the recommended band, restart 15 min unsold per start
                                     N   cover  summer  dump   util srv-h sold starts  elec CHF      BE   run h/yr of servers 6, 7, 8
  case assumptions                   6   79.6%  100.0%     0  59.1%      31067   1732     10330  0.2261   4389
  realistic, electric booster        6   77.4%   80.0%     0  59.2%      31056    279     10641  0.2354   4562
  realistic, heat-pump booster COP 3 6   78.5%   93.3%     0  60.0%      31495    269     10591  0.2315   4566
  case assumptions                   8   92.9%  100.0%     0  51.8%      36281   2208     12063  0.2261   3908, 3324, 2807
  realistic, electric booster        8   90.3%   80.0%     0  51.9%      36192    657     12380  0.2352   3899, 3546, 3236
  realistic, heat-pump booster COP 3 8   91.7%   93.3%     0  52.7%      36734    681     12368  0.2319   3935, 3604, 3324
  gap 8 minus 6, electric: coverage case +13.4 pts -> realistic +13.0 pts; utilisation case -7.3 -> -7.3 pts; BE case -0.0000 -> -0.0002 CHF/h
  gap 8 minus 6, heatpump: coverage case +13.4 pts -> realistic +13.2 pts; utilisation case -7.3 -> -7.4 pts; BE case -0.0000 -> +0.0004 CHF/h

== pitch sentence (tank loss 2.80 kWh/d sourced; preheat 50 C, cold water 10 C, COP 3 are assumptions; 60 C sourced) ==
  N=6: With tank losses and an electric hot-water booster, summer coverage drops by 20.0 points (from 100% to 80.0%, June to August; year: 79.6% to 77.5%) and the break-even price rises by 0.0087 CHF per server-hour (from 0.2261 to 0.2348; 0.2386 if the booster's own heat is not valued).
  N=6: With tank losses and a small heat-pump booster (COP 3), summer coverage drops by 6.7 points (from 100% to 93.3%, June to August; year: 79.6% to 78.7%) and the break-even price rises by 0.0049 CHF per server-hour (from 0.2261 to 0.2310; 0.2322 if the booster's own heat is not valued).
  N=8: With tank losses and an electric hot-water booster, summer coverage drops by 20.0 points (from 100% to 80.0%, June to August; year: 92.9% to 90.5%) and the break-even price rises by 0.0080 CHF per server-hour (from 0.2261 to 0.2341; 0.2373 if the booster's own heat is not valued).
  N=8: With tank losses and a small heat-pump booster (COP 3), summer coverage drops by 6.7 points (from 100% to 93.3%, June to August; year: 92.9% to 91.9%) and the break-even price rises by 0.0047 CHF per server-hour (from 0.2261 to 0.2308; 0.2318 if the booster's own heat is not valued).
```
