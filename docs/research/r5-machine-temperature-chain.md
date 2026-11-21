# Round 5: one consistent machine, cooling and temperature chain

Investigator file for the round-5 weak point: "layout A assumes a liquid-cooled server delivering about 55 °C, but the reference server (2U, 4 × RTX PRO 4500) is air-cooled, and its installed cost includes no liquid cooling or booster." This round plans and assesses only; nothing here is the team's scheduler. No existing file was changed and git state was not touched. Written Sat 21 Nov 2026.

- **Script:** `analysis/r5_chain.py`, new, standard library only. It imports `baseline_sweep.py`, `r4_tank_layout.py` and `r4_machine.py` without changing them, and writes no bytecode.
- **Command:** `python3 analysis/r5_chain.py` (exit 0, about 3 s). The full output is in section 7.
- **Regression:** the script reproduces `r4_tank_layout.sim` exactly (77.613% / 90.633%, 31,236 / 36,495 h, 0.2293 / 0.2343). It also reproduces the round-4 critic's radiator 55/45 scratch probe (64.3% / 73.0%, 853 blocked hours), so that probe now exists in a committed script.
- **Currency:** CHF. 1 EUR = 0.9223 CHF (ECB, 20 Nov 2026, sourced in round 1 and taken from `r4_machine.py`). Swiss VAT is 8.1% and German VAT 19%, as in `r4_machine.py`. A GBP price is quoted but not converted.
- **Firecrawl:** 2 of 6 calls used. One succeeded (DCD Qarnot page). The second (HPE QuickSpecs) was refused because the account was out of credits.

**Status labels:**
- *sourced*: a URL I opened, with the number read on the page.
- *computed*: produced by `analysis/r5_chain.py`.
- *assumption*: our own choice.
- *unverified*: seen only in a search snippet, or an interpretation.

## 1. Answer in brief

1. **Recommended chain: keep the same four-GPU box and fit it with water cold plates (direct liquid cooling, "DLC").**
   - **Coolant into the server: at most 45 °C** (*assumption*; this is the stated maximum inlet temperature). The flow is set for about 10 K rise, so about 55 °C comes out.
   - **Rack-server GPU blocks are rated to 60 °C maximum operating temperature** (*sourced*, EK and Alphacool). 55 °C leaves 5 K of margin.
   - A small CDU (plate heat exchanger, 5 K approach) feeds a 50 °C top into the 1,000 l buffer. The **house water returning to the CDU must be at most 40 °C.**
   - Hot water: a fresh-water station preheats to 47 °C, and a small electric cylinder tops up to 55 °C.
   - This is layout A with a real machine behind it. The realism column keeps its numbers, so it needs **no new build scope** (section 5).
2. **The realism column on this chain (*computed*, with tank loss 2.80 kWh/day; floor heating, or radiators sized for 50/40):**

   | | N = 6 | N = 8 |
   |---|---|---|
   | Coverage | 77.6% | 90.6% |
   | June–August | 82.2% | 82.2% |
   | Dumped | 0 kWh | 0 kWh |
   | Utilisation | 59.4% | 52.1% |
   | Break-even, case convention | 0.2293 CHF | 0.2293 CHF |
   | Break-even, with circulation pumps at 2% of server power (*assumption*) | 0.2359 CHF | 0.2360 CHF |
   | Break-even, hot-water element also charged to the servers | 0.2409 CHF | 0.2403 CHF |

   The pumps' effect may cancel: a cold-plated box needs less fan power (*unverified*).
3. **Where it stops holding, now from a committed script (*computed*, with tank loss):**
   - **Radiators sized 55/45:** 64.3% / 73.0%. The servers must stop in 853 hours, when the house return is above 40 °C.
   - **Old radiators sized 70/55:** 29.0% / 30.8%; the servers stop in 3,188 hours.
   - **If the box tolerated 50 °C coolant in** (return limit 45 °C; sensitivity DLC50): the 55/45 house gets 77.4% / 90.4%, and the 70/55 house 49.5% / 51.8%. The outlet would then sit at the blocks' 60 °C rating, with no margin left.
4. **Installed cost of the chain (*computed*, central case):**

   | | N = 6 | N = 8 |
   |---|---|---|
   | Per house | **212,574 CHF** | **275,474 CHF** |
   | Per 1 kW server | about 35,400 CHF | about 34,400 CHF |
   | Share of list price needed, 5-year simple payback | **11.2%** | **12.3%** |
   | Share needed, 8 years | 7.7% | 8.3% |
   | Share needed, operation only | 1.7% | 1.7% |

   - Round 4 had 201,914 CHF and 10.7% at N=6.
   - Of the +10,660 CHF per house, only **about 4,600 CHF is liquid cooling**: +250 CHF per box for cold plates over the air coil, plus a 3,000 CHF CDU. The remaining **6,086 CHF** is buffer tank, fresh-water station and hot-water cylinder, which round 4 left out and which **any** chain needs.
   - Range with low / high costs at N=6: 162,250–279,589 CHF, a 9.0–14.3% share over 5 years.
5. **Option (i) availability (*sourced*):**
   - Single-slot rack-server GPU blocks exist:
     - EK-Pro for the RTX PRO 6000 Blackwell **Server Edition**, £412.99 incl. VAT, maximum coolant 60 °C;
     - Alphacool ES for the RTX PRO 6000 **Server Edition**, €399.98 incl. VAT, maximum operating temperature 60 °C, 5 in stock;
     - Alphacool ES for the **RTX PRO 4500 Blackwell**, €399.98, listed for the **workstation** edition (pre-order, October 2026).
   - **I found no block for the RTX PRO 4500 *Server Edition*** that the MLPerf box uses. The DLC box therefore uses either workstation-edition RTX PRO 4500 cards with Alphacool blocks, whose power and throughput are not measured by MLPerf, or RTX PRO 6000 Server Edition cards, which need a different throughput basis. This is the main remaining gap.
6. **Option (ii): products that ship liquid-cooled (*sourced*):**
   - Qarnot's QBx "digital boilers" move "96 percent of the heat produced by the server … by cold plate to a water circulation system", sit "in homes and offices" and have no fans. They are CPU-based (AMD Ryzen, OCP).
   - Heata attaches a server to a vented hot-water cylinder through a thermal bridge, with "up to 4.8 kWh per day" (at least 2.5 contractual). That is about 40% of the case's 12 kWh/day of hot water, and space heating is not served.
   - **Neither opened page states an outlet water temperature or a GPU option.** Qarnot "65 °C" appears only in a search snippet (*unverified*). Thermify's article page is dead; its "~£2,500" and "output temperature between a heat pump and a gas boiler" are from a snippet (*unverified*).
   - There is no product to model, so option (ii) gives no row.
7. **Option (iii): keep the box air-cooled (*computed*, assumptions in section 3):**
   - **Air-cooled with a coil, server inlet air ≤ 30 °C:** water 40 °C at most, returning at ≤ 25 °C. Floor heating covers only 43.1% at N=6, because the floor return is above 25 °C in 2,113 hours. Radiators get under 6%, and hot water 60% direct.
   - **Server inlet air ≤ 35 °C** (water 45 °C, returning at ≤ 30 °C): floor heating 76.5% / 89.3% and hot water 71.1%. Radiators sized 50/40 get only 18.9% / 20.5%.
   - **Heat-pump water heater in the server room** (Buderus COP 3.63 at A20, *sourced*; it accepts air up to 35 °C): 72.5% of hot water is server heat, at 895 kWh/yr of compressor electricity.
   - **Water/water heat pump lifting all heat to 55 °C** (WPZ COP 3.6 at W10/W55, *sourced*, used as a lower bound): every house, old radiators included, gets 67.9% server heat (94.0% including compressor heat). This costs 8,158 kWh/yr of electricity, break-even 0.2893 CHF, and about 16,300 CHF for the heat pump (BFE proxy). With a Carnot-scaled COP of 5.2 (*computed*, *unverified*): 72.2% and 0.2662.
   - **Verdict:** air cooling works only for floor heating, and only if the box runs at about 35 °C inlet air. Heat pumps make radiator houses work, but break-even rises by about 0.04–0.06 CHF per server-hour.
8. **Corrected realism sentence for the pitch** (wording in section 6):
   - The servers carry water cold plates, so the house gets about 50 °C water. That is enough for floor heating and radiators sized for 50 °C, with hot water topped up electrically.
   - Year coverage falls from 79.6% to 77.6% and summer coverage from 100% to 82% at six servers.
   - Radiators that need 55 °C force the servers to stop on cold days (64%); old 70 °C radiator houses are where it stops working (about 30%).

## 2. Sources (opened by me, 21 Nov 2026, unless marked)

| # | Fact | Value read | Status, URL |
|---|---|---|---|
| S1 | EK-Pro GPU WB RTX PRO 6000 SE | "£412.99" "Inc VAT"; "Max. Coolant Operating Temperature" 60 °C; "Compatible with RTX PRO 6000 Blackwell Server Edition and Max-Q Workstation Edition"; "Single-slot design optimised for rackmount and high-density workstation environments" | *sourced*: <https://www.scan.co.uk/products/ek-pro-gpu-wb-rtx-pro-6000-se-water-block-rtx-pro-6000-server-ed-stainless-steel-top-nickel-plated-c> (WebFetch; ekwb.com itself returned 403) |
| S2 | Alphacool ES RTX 6000 Pro Server Edition 1-Slot-Design (art. 19450) | "€399.98", "All prices incl. value added tax"; compatible: RTX PRO 5000 Blackwell, RTX PRO 6000 Blackwell Max-Q Workstation, RTX PRO 6000 Blackwell Server Edition; "Maximum operating temperature" 60 °C (the page does not say block or coolant); recommended working temperature 20 °C; "in stock", 5 available | *sourced*: <https://shop.alphacool.com/en/detail/index/sArticle/22570> (WebFetch) |
| S3 | Alphacool ES 1-slot blocks for RTX Pro 4000 / **4500** / 6000 Workstation and Radeon AI Pro R9700, aimed at "les utilisateurs de serveurs rack" | RTX Pro 4500 and 6000 Workstation blocks **399.98 €**; 4000 and R9700 324.98 €; no server-edition GPU named; no coolant temperature; page modified 2026-10-09 | *sourced*: <https://overclocking.com/?p=257233> (WebFetch). The TechPowerUp launch article (8 Oct 2026, "available for pre-order") returned a bot check: *unverified* |
| S4 | Qarnot QBx digital boiler | "The system recovers 96 percent of the heat produced by the server, transferring it by cold plate to a water circulation system"; "12 or 24 AMD Ryzen processors"; "water-cooled QBx modules sit in homes and offices"; "no fans"; DCD, 25 Mar 2022. **No water temperature on the page** | *sourced*: <https://www.datacenterdynamics.com/en/news/qarnot-upgrades-its-digital-boiler-with-itrenews-refurbished-ocp-hardware/> (Firecrawl scrape, 1 call) |
| S5 | Qarnot boilers (TechCrunch, 9 Jan 2023) | "Up to 95% of computer waste heat is turned into hot water"; modules hold "up to 12 servers", AMD Epyc / Intel Xeon; sites: "social landlords, property developers, local authorities, swimming pools and heating network operators". No temperature, no price | *sourced*: <https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/> (WebFetch). "Water at 65 °C" was seen only in a snippet: *unverified* |
| S6 | Heata (cnx-software, 15 Feb 2023) | "up to 4.8 kWh per day", "at least 2.5 kWh as per contractual obligations"; "attach a thermal bridge to the cylinder"; "only works with vented 425mm to 450mm diameter cylinders"; no temperature in the article; electricity paid by Innovate UK and Heata during the trial | *sourced*: <https://www.cnx-software.com/2023/02/15/install-a-server-in-your-house-get-free-hot-water/> (WebFetch) |
| S7 | Water/water heat pumps, Swiss test centre WPZ (OST), EN 14511, "medium (55 °C)" table | Dolder WP-ZR28-1-R407c.WW: W10/W55 **COP 3.6**, 8.5 kW; WP-ZR48-1: 3.9; Waterkotte EcoTouch 5010.5 Ai: 3.9, 9.2 kW; same units at W10/W30 (part load, A12 column) 6.3–6.7; document dated 28.03.2025 | *sourced*: <https://www.ost.ch/fileadmin/dateiliste/3_forschung_dienstleistung/institute/ies/pdf/projekte_wpz/pruefresultate_sw_28032025.pdf> (curl + pdftotext). W10/W55 means source water 10 °C, flow 55 °C (a lower bound for a 25–40 °C server-heat source) |
| S8 | Heat-pump water heater Buderus BW 270 P.2 (Swiss data sheet) | heat output 1.4 kW; "COP (ohne elektrischen Zuheizer) nach EN 16147, A20/W10-53" **3.63**; "Arbeitsbereich -10 °C bis +35 °C"; max hot water 62 °C without the element, 65 °C with it; 258 l; element 1.5 kW | *sourced*: <https://www.buderus.com/ch/media/country_pool/wissen/documents/fl_bw270p.2_bw400.2_neu.pdf> (curl + pdftotext) |
| S9 | Heat-pump water heater prices in Switzerland (42watt, 2026) | device "ca. CHF 3.300–4.600" (260–300 l); "in der Schweiz typischerweise rund CHF 6.000 inklusive Montage und Entsorgung des alten Boilers"; COP e.g. WWK-I 300 Plus "4,21 (A20)" | *sourced*: <https://42watt.de/magazin/waermepumpenboiler-300-liter> (WebFetch) |
| S10 | A.O. Smith Enevator Aqua Booster (water/water, high temperature) | "produce water up to 78°C (HT version)"; COP 5.48–5.83 (HT) at "user water temperature 30/35°C, source water temperature 10/7°C"; smallest unit 37.6 kW; the operating-limits chart shows source outlet up to 40 °C | *sourced*: <https://www.aosmithme.com/wp-content/uploads/2023/12/Enevator-Aqua-Booster.pdf> (WebFetch, PDF read). Too large for a house (≥ 37.6 kW); used only to show that boosters accept 30–40 °C source water |

Reused from round 4, not searched again:
- NVIDIA blog: coolant "up to 45 degrees Celsius", "entering … at 45 degrees Celsius exits at roughly 55 degrees" (<https://blogs.nvidia.com/blog/liquid-cooling-ai-factories/>).
- Lenovo Gold tier: FWS 40–45 °C, TCS 45–50 °C; the W number is the upper bound of the *inlet* (<https://lenovopress.lenovo.com/lp2018-lenovo-neptune-direct-water-cooling-standards>).
- BFE 2015 heat-pump price study: median 36,000 CHF excl. VAT; heat pump 42%; "Wassererwärmer" 7–8%; storage tank 2–4% (<https://pubdb.bfe.admin.ch/de/publication/download/8157>).
- All machine, price and VAT inputs in `analysis/r4_machine.py`.

Not found or not opened (*unverified*):
- **A water block for the RTX PRO 4500 Blackwell *Server Edition*.** Neither search surfaced one.
- **The HPE DL345 Gen12 QuickSpecs** (inlet-air limit with GPUs; what its "Direct Liquid Cooling" option cools). WebFetch timed out twice, and the Firecrawl call was refused for lack of credits. A search snippet lists "Air cool, Direct Liquid Cooling" as options.
- Comino Grando: "Operating: 3..38ºC" and "2x 18W pumps" appear only in a snippet of a datasheet I did not open.
- Thermify HeatHub: the page redirects to a different site. The price "approximately £2,500" and "output temperature between a heat pump's and a gas boiler's" are from a snippet.
- RTX PRO 4500 Blackwell (workstation) board power: not opened.
- **The GPU's own maximum coolant or junction temperature: not published on any page I opened.** The 60 °C ratings in S1 and S2 are for the block, not for the GPU.

## 3. The chains compared

All chains keep the case's 1 kW server, 80% heat recovery, the follow rule (never dump) and tank loss 2.80 kWh/day. Every chain uses the heating curves and design pairs of `r4_tank_layout.py`.

**"Return limit"** means: in an hour when the heating return is warmer than the limit, the servers cannot be cooled and stop (k = 0). This is the pessimistic bound, the same rule as the round-4 critic's probe.

| Chain | Machine and cooling | House-side top / return limit | Hot water | Status of the temperatures |
|---|---|---|---|---|
| **DLC (recommended)** | same 4-GPU box, GPU and CPU cold plates, small CDU (5 K) | 50 °C / **≤ 40 °C** | fresh-water station 47 °C + element to 55 °C | 45 °C in = NVIDIA, ASHRAE W45 (*sourced*, applied to this box as an *assumption*); 10 K rise is a flow choice (*assumption*); 55 °C < 60 °C block rating (*sourced*); 5 K CDU approach (round 4, our reading) |
| DLC50 | same, if the box tolerates 50 °C coolant in | 50 °C / ≤ 45 °C | same | *assumption*; the outlet then reaches the 60 °C block rating |
| AIR | box unchanged, closed enclosure with an air-to-water coil | 40 °C / ≤ 25 °C | preheat 37 °C + element | inlet air 30 °C, 15 K rise across the box, 5 K coil approach: all *assumptions* |
| AIR35 | same, inlet air 35 °C | 45 °C / ≤ 30 °C | preheat 42 °C + element | 35 °C is the ASHRAE A2 allowable limit (*unverified* for this box; QuickSpecs not read) |
| AIR+HPB | AIR + heat-pump water heater drawing the server-room air | 40 °C / ≤ 25 °C (space heat) | **all** hot water by heat pump, COP 3.63 | COP at A20 (*sourced*) is a lower bound for 25–35 °C room air; air limit 35 °C (*sourced*) |
| AIR+HP | air coil feeding a water/water heat pump to 55 °C for all heat | evaporator side decoupled, no return limit | heat pump | COP 3.6 at W10/W55 (*sourced*, lower bound); COP 5.24 Carnot-scaled to 22 °C source outlet (*computed*, *unverified*) |

**Liquid capture share:** with GPU and CPU on cold plates, liquid takes (627 + 180 W) ÷ 955 W = **84.5%** of wall power on round 4's central power model (*computed*). This is close to the case's 80% recovery, so 80% stays. The rest (PSU loss, RAM, VRMs, fans) warms the basement air.

### 3.1 What each option delivers (N = 6; extra electricity per year; extra installed cost per house, central)

| Option | Outlet to house | Max inlet | Space heat served directly: underfloor 35/28 / radiator 50/40 / 55/45 / 70/55 | Hot water direct | Coverage N=6 (underfloor / rad. 50/40) | Extra electricity, kWh/yr | Extra installed cost vs r4 basis | Break-even case conv. (underfloor) |
|---|---|---|---|---|---|---|---|---|
| (i) DLC | 50 °C | **45 °C coolant**; house return ≤ 40 | 100 / 100 / 73.9 / 22.2% | 82.2% | 77.6% / 77.5% | pumps 625 (*assumption*); element 779 (backup heater, outside the model) | **+10,660** (of which liquid cooling about 4,600) | 0.2293 (0.2359 incl. pumps) |
| (i) DLC50 | 50 °C | 50 °C coolant; return ≤ 45 | 100 / 100 / 97.9 / 46.7% | 82.2% | 77.6% / 77.5% | 625 + 779 | +10,660 | 0.2359 incl. pumps |
| (ii) shipped products | not published | not published | — | Heata: up to 4.8 kWh/day | not modelled | — | Thermify ~£2,500 (*unverified*) | — |
| (iii) AIR | 40 °C | inlet air 30 °C; return ≤ 25 | 43.0 / 0.2 / 0.1 / 0% | 60.0% | 43.1% / 5.1% | element 1,752 | +6,086 | 0.2318 |
| (iii) AIR35 | 45 °C | inlet air 35 °C; return ≤ 30 | 100 / 11.1 / 3.5 / 0.5% | 71.1% | 76.5% / 18.9% | element 1,265 | +6,086 | 0.2294 |
| (iii) AIR+HPB | 40 °C + heat-pump hot water | as AIR | as AIR | 72.5% server heat | 44.2% / 5.9% | heat pump 895 | +7,167 | 0.2414 |
| (iii) AIR+HP, COP 3.6 | 55 °C (lifted) | none on the server side | 72.2 / 72.2 / 72.2 / 57.7% server heat | 72.2% | 67.9% / 67.9% (94.0% incl. compressor heat) | heat pump 8,158 | +20,431 | 0.2893 |
| (iii) AIR+HP, COP 5.2 | 55 °C | none | 80.9 / 80.9 / 80.9 / 64.6% | 80.9% | 72.2% / 72.2% (89.2%) | heat pump 5,320 | +20,431 | 0.2662 |

How to read the table:
- **Coverage** is the case definition: server heat ÷ total demand.
- **Heat-pump chains:** the "direct" share is the server-heat part, (1 − 1/COP) of the demand the heat pump serves.
- **Break-even (case convention)** charges heat-pump electricity to the servers and credits all heat the chain delivers. An element top-up is the backup heater, outside the model.
- **Extra installed cost:** the r4 basis has no buffer tank, fresh-water station or hot-water cylinder. Every chain here adds them: 6,086 CHF per house central (buffer 1,167 and cylinder 2,919 are BFE-share proxies; the fresh-water station at 2,000 is an *assumption*).
- **DLC on top of that:** +250 CHF per box (4 blocks 1,340 + CPU plate 250 + manifold, couplings and leak sensor 800 + assembly 360, against the r4 coil at 2,500) and a 3,000 CHF CDU. All except the blocks are *assumptions*.

### 3.2 Why DLC and not the others

- **DLC against air.** Floor heating at N=6: DLC 77.6% against 76.5% for AIR35, which also needs the box to run at 35 °C inlet air all winter. Radiators sized 50/40, now the Swiss limit for new or replaced emitters: **77.5% against 18.9%**. Hot water 82.2% against 71.1%. DLC costs about 4,600 CHF more per house (about 2% of installed cost), and the 5-year share of list price needed is 11.2% against 11.1%. AIR at 30 °C inlet air is worse on everything (43.1%; 5-year share 18.2%).
- **DLC against heat pumps.** Only a heat pump lifting the server heat serves old 70/55 radiator houses (59.7% server heat at N=6, against 29.0% with DLC). It costs 0.06 CHF more break-even per server-hour (0.2893 against 0.2359), 8,158 kWh/yr of compressor electricity and about 16,300 CHF for the heat pump. That is a different product (a heat-pump house with a server source), so it is a "where it stops holding" line, not the default.
- **DLC against shipped products.** No product page gives a GPU option together with a documented outlet temperature. Qarnot shows that cold plates feeding water in homes and offices are a shipped product: CPU-only, 96% to water. Heata covers at most about 40% of the case's hot water.
- **Build scope.** DLC is the only chain whose realism column already exists as two switches in `baseline_sweep` (`dhw_direct_share=37/45`, `tank_loss_kwh_day=2.80`: 77.72% / 90.74%, within 0.1–0.2 points). The radiator lines are quoted from this script. Nothing new goes into the scheduler.

## 4. Method notes (what the script does)

- `sim(rows, n, chain, house, tank_loss)` is the `r4_tank_layout.sim` balance, generalised to:
  - a house-side top temperature and a return limit (servers stop in hours when the heating return exceeds it);
  - space heat either served directly at that temperature (serial preheat as in r4) or lifted by a heat pump to 55 °C;
  - hot water either preheated (top − 3 K) with an electric element, or made by a heat pump.

  Heat-pump portions need (1 − 1/COP) of their demand as server heat; the compressor electricity is the served amount × 1/(COP − 1). The tank capacity is 1.163 kWh/K × (top − 20 °C). The follow rule takes the largest whole k whose surplus fits, so nothing is dumped.
- **Break-even:** `BEcase` = (server + pump + heat-pump electricity) × 0.3325 − (server heat + compressor heat delivered) × 0.133, divided by server-hours. `BEchg` adds the hot-water element's electricity and credits its heat (the round-2 convention). The element top-up is counted every hour, as in r4.
- **Installed cost:** the r4 central box (4 cards at the post.ch price + 8,000 CHF platform) plus the chain's per-box capture cost, × N ÷ 0.955 kW boxes, plus r4 house integration (14,788 CHF), plus the chain's per-house items. The share needed is (BEchg + installed ÷ (years × server-hours)) ÷ 14.25 CHF list value (r4 central, 50/50 mix, every permit hour sold, simple payback). It uses the chain's own server-hours on the underfloor house.
- **Carnot-scaled COP:** the second-law efficiency of the WPZ W10/W55 point (source out 7 °C, sink 55 °C) is 0.527. Applied to a 22 °C source outlet and a 55 °C sink, it gives 5.24. That is an extrapolation (*unverified*).

## 5. What changes in the plan (no build scope added)

- **Realism column:** no number changes. Relabel the column "reference server with water cold plates (DLC retrofit), coolant ≤ 45 °C in, ~55 °C out, house return ≤ 40 °C". Footnote the pump line: +0.0066 CHF if pumps draw 2% (*assumption*).
- **Maximum inlet temperature, stated in the assumptions list:** "Coolant into the servers ≤ 45 °C (ASHRAE W45 / NVIDIA; applied to this box as an assumption); so house return to the CDU ≤ 40 °C; GPU blocks are rated 60 °C." Sensitivity: at 50 °C in, radiator 55/45 houses recover (77.4% / 90.4%).
- **Installed cost table:** central **212,574 CHF per house at N=6 (275,474 at N=8)**, about 35,000 CHF per 1 kW server. It now includes the buffer, fresh-water station, hot-water cylinder, CDU and cold plates. Share needed: 5 years 11.2% / 12.3%, 8 years 7.7% / 8.3%, operation 1.7%. The 5% interest variants are not recomputed.
- **"Does not pay off" / "where it stops holding":**
  - The 55/45 and 70/55 figures come from `analysis/r5_chain.py` (no longer a critic scratch probe).
  - Add: "Air-cooled box: floor heating only, and only at about 35 °C inlet air (76.5% / 89.3%); radiators below 21%."
  - Add: "Heat-pump lift serves old radiator houses (59.7% server heat) but break-even rises to about 0.29 CHF."
  - Drop the round-2 "air-cooled 70.5% / 81.7%" line. It assumed all space heat usable at air-cooled temperatures, which holds only for floor heating at about 35 °C inlet air.
- **Open risk 5:** replace "the realism column and the installed cost describe different machines" with the remaining gaps:
  - no block found for the RTX PRO 4500 *Server Edition* (the 4500 block is for the workstation card; the RTX PRO 6000 SE has blocks but a different throughput basis);
  - warranty and leak risk of a retrofit (*unverified*);
  - GPU maximum coolant temperature not published;
  - pump power not measured.
- **Question for DigitalHeat (replaces part of question 1):** "Do you cold-plate the GPUs, and what is the maximum coolant inlet temperature you run at: 45 or 50 °C?"

## 6. Realism sentence for the pitch (corrected)

> "Our headline uses the case's simplifications. On the same servers fitted with water cold plates, the house gets about 50 °C water: enough for floor heating and radiators sized for 50 °C, with an electric top-up for hot water, so the year drops from 79.6% to 77.6% and summer from 100% to 82% at six servers. If radiators need 55 °C, the servers must stop on cold days (64%); old 70 °C radiator houses are where it stops working (about 30%)."

Footnote: coolant ≤ 45 °C in (assumption), about 55 °C out, blocks rated 60 °C, 5 K exchanger, tank loss 2.80 kWh/day. Break-even 0.2293 CHF under the case convention (0.2359 with 2% pump power). Installed about 213,000 CHF per house at N=6. `python3 analysis/r5_chain.py`.

## 7. Script output (full)

Command: `python3 analysis/r5_chain.py` (exit 0)

```
r5_chain.py  (CHF; electricity 0.3325 CHF/kWh, heat 0.1330 CHF/kWh; 1 EUR = 0.9223 CHF, ECB 20 Nov 2026)

== 0. Regression checks ==
  A0 vs r4_tank_layout.sim, underfloor + loss, N=6: r4 77.613% 31236 h 0.2293/0.2343 | r5 77.613% 31236 h 0.2293/0.2343 -> OK
  A0 vs r4_tank_layout.sim, underfloor + loss, N=8: r4 90.633% 36495 h 0.2293/0.2336 | r5 90.633% 36495 h 0.2293/0.2336 -> OK
  DLC radiator 55/45 + loss, N=6: 64.3% (round-4 critic probe: 64.3% / 73.0%), blocked 853 h (critic: 853)
  DLC radiator 55/45 + loss, N=8: 73.0% (round-4 critic probe: 64.3% / 73.0%), blocked 853 h (critic: 853)

== 1. Inputs ==
  A0       top   50 C, return limit    -, space heat direct, hot water element, COP sh -, COP dhw -, pump 0.0 kW/srv  | layout A, no return limit (plan, regression)
  DLC      top   50 C, return limit 40.0, space heat direct, hot water element, COP sh -, COP dhw -, pump 0.02 kW/srv  | cold-plate retrofit, inlet <=45 C, return <=40 C
  DLC50    top   50 C, return limit 45.0, space heat direct, hot water element, COP sh -, COP dhw -, pump 0.02 kW/srv  | cold-plate retrofit, inlet <=50 C, return <=45 C
  AIR      top   40 C, return limit 25.0, space heat direct, hot water element, COP sh -, COP dhw -, pump 0.0 kW/srv  | air-cooled + coil, 40 C top, return <=25 C
  AIR35    top   45 C, return limit 30.0, space heat direct, hot water element, COP sh -, COP dhw -, pump 0.0 kW/srv  | air-cooled + coil, 45 C top, return <=30 C
  AIR+HPB  top   40 C, return limit 25.0, space heat direct, hot water hp     , COP sh -, COP dhw 3.63, pump 0.0 kW/srv  | AIR + heat-pump water heater for all DHW
  AIR+HP   top   40 C, return limit    -, space heat hp    , hot water hp     , COP sh 3.6, COP dhw 3.6, pump 0.0 kW/srv  | air + water/water HP to 55 C, COP 3.6
  AIR+HP5  top   40 C, return limit    -, space heat hp    , hot water hp     , COP sh 5.236363636363635, COP dhw 5.236363636363635, pump 0.0 kW/srv  | air + water/water HP to 55 C, COP 5.2
  COP_WW_HIGH = WPZ W10/W55 3.6 -> Carnot efficiency 0.527 -> source 22 C out / sink 55 C: 5.24 (computed extrapolation, unverified)
  GPU block 399.98 EUR incl. 19% DE VAT -> 335 CHF incl. 8.1% CH VAT
  liquid capture share of wall power (central r4 power model): (GPUs 627 + CPU 180 W) / 955 W = 84.5%  (case: 80% recovered)

== 2. Direct shares by chain and house (energy-weighted, before the server count limits it) ==
  chain      underfloor 35/28    radiator 50/40    radiator 55/45    radiator 70/55  hot water
  A0                   100.0%            100.0%             97.9%             55.6%      82.2%
  DLC                  100.0%            100.0%             73.9%             22.2%      82.2%
  DLC50                100.0%            100.0%             97.9%             46.7%      82.2%
  AIR                   43.0%              0.2%              0.1%              0.0%      60.0%
  AIR35                100.0%             11.1%              3.5%              0.5%      71.1%
  AIR+HPB               43.0%              0.2%              0.1%              0.0%      72.5%
  AIR+HP                72.2%             72.2%             72.2%             57.7%      72.2%
  AIR+HP5               80.9%             80.9%             80.9%             64.6%      80.9%
  (heat-pump chains: share of the demand that is SERVER heat, i.e. x (1 - 1/COP); the rest is compressor heat)

== 3. Realism column per chain, tank loss 2.80 kWh/day, follow rule (never dumps) ==
  covSrv = server heat / demand (case definition); covChn = incl. heat-pump compressor heat;
  blkd = hours servers must stop (house return above the chain's limit); HP+pmp, elem = kWh el per year
chain / house                                    N  covSrv  covChn Dec-Feb Jun-Aug dump   util  srv-h  blkd HP+pmp  elem BEcase  BEchg
case assumptions (baseline_sweep)                6   79.6%   79.6%          100.0%    0  59.1%  31067     0      0     0 0.2261 0.2261
A0 | underfloor 35/28                            6   77.6%   77.6%   68.4%   82.2%    0  59.4%  31236     0      0   779 0.2293 0.2343
A0 | radiator 50/40                              6   77.5%   77.5%   68.3%   82.2%    0  59.3%  31189     0      0   779 0.2293 0.2343
A0 | radiator 55/45                              6   77.4%   77.4%   68.3%   82.2%    0  59.3%  31174     0      0   779 0.2294 0.2343
A0 | radiator 70/55                              6   59.2%   59.2%   41.9%   82.2%    0  46.5%  24432     0      0   779 0.2318 0.2382
DLC | underfloor 35/28                           6   77.6%   77.6%   68.4%   82.2%    0  59.4%  31236     0    625   779 0.2359 0.2409
DLC | radiator 50/40                             6   77.5%   77.5%   68.3%   82.2%    0  59.3%  31189     0    624   779 0.2360 0.2410
DLC | radiator 55/45                             6   64.3%   64.3%   47.1%   82.2%    0  49.6%  26056   853    521   779 0.2366 0.2426
DLC | radiator 70/55                             6   29.0%   29.0%    8.2%   82.2%    0  23.3%  12265  3188    245   779 0.2410 0.2537
DLC50 | underfloor 35/28                         6   77.6%   77.6%   68.4%   82.2%    0  59.4%  31236     0    625   779 0.2359 0.2409
DLC50 | radiator 50/40                           6   77.5%   77.5%   68.3%   82.2%    0  59.3%  31189     0    624   779 0.2360 0.2410
DLC50 | radiator 55/45                           6   77.4%   77.4%   68.3%   82.2%    0  59.3%  31174     0    623   779 0.2360 0.2410
DLC50 | radiator 70/55                           6   49.5%   49.5%   28.3%   82.2%    0  38.8%  20374  1762    407   779 0.2382 0.2458
AIR | underfloor 35/28                           6   43.1%   43.1%   22.6%   60.0%    0  33.8%  17758  2113      0  1752 0.2318 0.2515
AIR | radiator 50/40                             6    5.1%    5.1%    0.0%   60.0%    0   5.1%   2659  4884      0  1752 0.2523 0.3838
AIR | radiator 55/45                             6    4.8%    4.8%    0.0%   60.0%    0   4.8%   2530  4909      0  1752 0.2536 0.3918
AIR | radiator 70/55                             6    4.5%    4.5%    0.0%   60.0%    0   4.6%   2410  4929      0  1752 0.2551 0.4001
AIR35 | underfloor 35/28                         6   76.5%   76.5%   68.3%   71.1%    0  58.6%  30819     0      0  1265 0.2294 0.2376
AIR35 | radiator 50/40                           6   18.9%   18.9%    3.3%   71.1%    0  15.7%   8270  3893      0  1265 0.2378 0.2683
AIR35 | radiator 55/45                           6   10.9%   10.9%    0.8%   71.1%    0   9.7%   5076  4500      0  1265 0.2433 0.2930
AIR35 | radiator 70/55                           6    6.4%    6.4%    0.1%   71.1%    0   6.1%   3216  4840      0  1265 0.2495 0.3280
AIR+HPB | underfloor 35/28                       6   44.2%   47.0%   22.7%   72.5%    0  34.6%  18176  2113    895     0 0.2414 0.2414
AIR+HPB | radiator 50/40                         6    5.9%    7.9%    0.0%   72.5%    0   5.6%   2963  4884    611     0 0.2905 0.2905
AIR+HPB | radiator 55/45                         6    5.6%    7.6%    0.0%   72.5%    0   5.4%   2832  4909    609     0 0.2932 0.2932
AIR+HPB | radiator 70/55                         6    5.3%    7.3%    0.0%   72.5%    0   5.2%   2714  4929    611     0 0.2963 0.2963
AIR+HP | underfloor 35/28                        6   67.9%   94.0%   64.9%   72.2%    0  52.5%  27616     0   8158     0 0.2893 0.2893
AIR+HP | radiator 50/40                          6   67.9%   94.0%   64.9%   72.2%    0  52.5%  27616     0   8158     0 0.2893 0.2893
AIR+HP | radiator 55/45                          6   67.9%   94.0%   64.9%   72.2%    0  52.5%  27616     0   8158     0 0.2893 0.2893
AIR+HP | radiator 70/55                          6   59.7%   82.7%   52.2%   72.2%    0  46.8%  24620     0   7174     0 0.2899 0.2899
AIR+HP5 | underfloor 35/28                       6   72.2%   89.2%   66.7%   80.9%    0  55.5%  29194     0   5320     0 0.2662 0.2662
AIR+HP5 | radiator 50/40                         6   72.2%   89.2%   66.7%   80.9%    0  55.5%  29194     0   5320     0 0.2662 0.2662
AIR+HP5 | radiator 55/45                         6   72.2%   89.2%   66.7%   80.9%    0  55.5%  29194     0   5320     0 0.2662 0.2662
AIR+HP5 | radiator 70/55                         6   66.7%   82.5%   58.3%   80.9%    0  52.0%  27341     0   4920     0 0.2670 0.2670

case assumptions (baseline_sweep)                8   92.9%   92.9%          100.0%    0  51.8%  36281     0      0     0 0.2261 0.2261
A0 | underfloor 35/28                            8   90.6%   90.6%   87.2%   82.2%    0  52.1%  36495     0      0   779 0.2293 0.2336
A0 | radiator 50/40                              8   90.5%   90.5%   87.2%   82.2%    0  52.0%  36461     0      0   779 0.2294 0.2337
A0 | radiator 55/45                              8   90.4%   90.4%   87.1%   82.2%    0  52.0%  36443     0      0   779 0.2294 0.2337
A0 | radiator 70/55                              8   59.3%   59.3%   42.1%   82.2%    0  34.9%  24478     0      0   779 0.2318 0.2382
DLC | underfloor 35/28                           8   90.6%   90.6%   87.2%   82.2%    0  52.1%  36495     0    730   779 0.2360 0.2403
DLC | radiator 50/40                             8   90.5%   90.5%   87.2%   82.2%    0  52.0%  36461     0    729   779 0.2360 0.2403
DLC | radiator 55/45                             8   73.0%   73.0%   58.8%   82.2%    0  42.3%  29632   853    593   779 0.2368 0.2421
DLC | radiator 70/55                             8   30.8%   30.8%    9.9%   82.2%    0  18.6%  13067  3188    261   779 0.2412 0.2530
DLC50 | underfloor 35/28                         8   90.6%   90.6%   87.2%   82.2%    0  52.1%  36495     0    730   779 0.2360 0.2403
DLC50 | radiator 50/40                           8   90.5%   90.5%   87.2%   82.2%    0  52.0%  36461     0    729   779 0.2360 0.2403
DLC50 | radiator 55/45                           8   90.4%   90.4%   87.1%   82.2%    0  52.0%  36443     0    729   779 0.2361 0.2403
DLC50 | radiator 70/55                           8   51.8%   51.8%   31.7%   82.2%    0  30.6%  21436  1762    429   779 0.2388 0.2460
AIR | underfloor 35/28                           8   46.5%   46.5%   26.5%   60.0%    0  27.5%  19245  2113      0  1752 0.2321 0.2503
AIR | radiator 50/40                             8    5.3%    5.3%    0.0%   60.0%    0   3.9%   2710  4884      0  1752 0.2520 0.3809
AIR | radiator 55/45                             8    4.9%    4.9%    0.0%   60.0%    0   3.7%   2564  4909      0  1752 0.2534 0.3897
AIR | radiator 70/55                             8    4.5%    4.5%    0.0%   60.0%    0   3.4%   2415  4929      0  1752 0.2550 0.3997
AIR35 | underfloor 35/28                         8   89.3%   89.3%   86.8%   71.1%    0  51.3%  35973     0      0  1265 0.2294 0.2364
AIR35 | radiator 50/40                           8   20.5%   20.5%    4.1%   71.1%    0  12.7%   8935  3893      0  1265 0.2373 0.2656
AIR35 | radiator 55/45                           8   12.0%   12.0%    1.1%   71.1%    0   7.9%   5516  4500      0  1265 0.2423 0.2881
AIR35 | radiator 70/55                           8    6.7%    6.7%    0.1%   71.1%    0   4.7%   3319  4840      0  1265 0.2490 0.3251
AIR+HPB | underfloor 35/28                       8   47.8%   51.1%   26.8%   72.5%    0  28.2%  19752  2113   1019     0 0.2422 0.2422
AIR+HPB | radiator 50/40                         8    6.1%    8.0%    0.0%   72.5%    0   4.3%   3016  4884    615     0 0.2896 0.2896
AIR+HPB | radiator 55/45                         8    5.7%    7.7%    0.0%   72.5%    0   4.1%   2868  4909    612     0 0.2927 0.2927
AIR+HPB | radiator 70/55                         8    5.3%    7.3%    0.0%   72.5%    0   3.9%   2719  4929    611     0 0.2962 0.2962
AIR+HP | underfloor 35/28                        8   72.2%   99.9%   72.1%   72.2%    0  42.0%  29457     0   8671     0 0.2894 0.2894
AIR+HP | radiator 50/40                          8   72.2%   99.9%   72.1%   72.2%    0  42.0%  29457     0   8671     0 0.2894 0.2894
AIR+HP | radiator 55/45                          8   72.2%   99.9%   72.1%   72.2%    0  42.0%  29457     0   8671     0 0.2894 0.2894
AIR+HP | radiator 70/55                          8   59.7%   82.7%   52.2%   72.2%    0  35.1%  24620     0   7174     0 0.2899 0.2899
AIR+HP5 | underfloor 35/28                       8   80.0%   98.8%   79.2%   80.9%    0  46.3%  32439     0   5894     0 0.2664 0.2664
AIR+HP5 | radiator 50/40                         8   80.0%   98.8%   79.2%   80.9%    0  46.3%  32439     0   5894     0 0.2664 0.2664
AIR+HP5 | radiator 55/45                         8   80.0%   98.8%   79.2%   80.9%    0  46.3%  32439     0   5894     0 0.2664 0.2664
AIR+HP5 | radiator 70/55                         8   66.9%   82.7%   58.5%   80.9%    0  39.1%  27422     0   4932     0 0.2670 0.2670

== 4. Installed cost per house and share of list price needed (central costs, central price, every permit hour sold, simple payback) ==
  list value of one server-hour of work (r4, central): 14.25 CHF
  N=6 r4 basis (air coil, no storage/DHW items, case run): 201,914 CHF; operation 0.2261; share needed operation 1.6%, 5 y 10.7%, 8 y 7.3%
    DLC        212,574 CHF (35,429 per 1 kW server; +10,660 vs r4), box 30,026 x 6.28; underfloor run 31,236 h; BEchg 0.2409; share op 1.7%, 5 y 11.2%, 8 y 7.7%
    AIR        208,000 CHF (34,667 per 1 kW server; +6,086 vs r4), box 29,776 x 6.28; underfloor run 17,758 h; BEchg 0.2515; share op 1.8%, 5 y 18.2%, 8 y 12.0%
    AIR35      208,000 CHF (34,667 per 1 kW server; +6,086 vs r4), box 29,776 x 6.28; underfloor run 30,819 h; BEchg 0.2376; share op 1.7%, 5 y 11.1%, 8 y 7.6%
    AIR+HPB    209,081 CHF (34,847 per 1 kW server; +7,167 vs r4), box 29,776 x 6.28; underfloor run 18,176 h; BEchg 0.2414; share op 1.7%, 5 y 17.8%, 8 y 11.8%
    AIR+HP     222,345 CHF (37,057 per 1 kW server; +20,431 vs r4), box 29,776 x 6.28; underfloor run 27,616 h; BEchg 0.2893; share op 2.0%, 5 y 13.3%, 8 y 9.1%
    DLC range low / high: 162,250 / 279,589 CHF; 5 y share 9.0% / 14.3% (low/high costs, central price)
  N=8 r4 basis (air coil, no storage/DHW items, case run): 264,289 CHF; operation 0.2261; share needed operation 1.6%, 5 y 11.8%, 8 y 8.0%
    DLC        275,474 CHF (34,434 per 1 kW server; +11,185 vs r4), box 30,026 x 8.38; underfloor run 36,495 h; BEchg 0.2403; share op 1.7%, 5 y 12.3%, 8 y 8.3%
    AIR        270,375 CHF (33,797 per 1 kW server; +6,086 vs r4), box 29,776 x 8.38; underfloor run 19,245 h; BEchg 0.2503; share op 1.8%, 5 y 21.5%, 8 y 14.1%
    AIR35      270,375 CHF (33,797 per 1 kW server; +6,086 vs r4), box 29,776 x 8.38; underfloor run 35,973 h; BEchg 0.2364; share op 1.7%, 5 y 12.2%, 8 y 8.3%
    AIR+HPB    271,457 CHF (33,932 per 1 kW server; +7,167 vs r4), box 29,776 x 8.38; underfloor run 19,752 h; BEchg 0.2422; share op 1.7%, 5 y 21.0%, 8 y 13.8%
    AIR+HP     284,720 CHF (35,590 per 1 kW server; +20,431 vs r4), box 29,776 x 8.38; underfloor run 29,457 h; BEchg 0.2894; share op 2.0%, 5 y 15.6%, 8 y 10.5%
    DLC range low / high: 210,245 / 360,048 CHF; 5 y share 9.8% / 15.5% (low/high costs, central price)
  DLC per-house items: 1,000 l buffer (BFE 3 % proxy) 1,167; CDU: plate HX + pump group + controls (assumption) 3,000; fresh-water station (assumption) 2,000; small DHW cylinder + element (BFE 7.5 % proxy) 2,919
  DLC per box capture (central): 4 blocks 1,340 + CPU plate 250 + manifold/QDs/tubing/leak sensor 800 + 3 h assembly 360 = 2,750 CHF (r4 air coil: 2,500)

== 5. Pitch lines, recommended chain DLC (N=6 / N=8) ==
  underfloor 35/28   coverage 77.6% / 90.6%; Jun-Aug 82.2%; util 59.4% / 52.1%; BEcase 0.2359 / 0.2360; BEchg 0.2409 / 0.2403; servers stop 0 h
  radiator 50/40     coverage 77.5% / 90.5%; Jun-Aug 82.2%; util 59.3% / 52.0%; BEcase 0.2360 / 0.2360; BEchg 0.2410 / 0.2403; servers stop 0 h
  radiator 55/45     coverage 64.3% / 73.0%; Jun-Aug 82.2%; util 49.6% / 42.3%; BEcase 0.2366 / 0.2368; BEchg 0.2426 / 0.2421; servers stop 853 h
  radiator 70/55     coverage 29.0% / 30.8%; Jun-Aug 82.2%; util 23.3% / 18.6%; BEcase 0.2410 / 0.2412; BEchg 0.2537 / 0.2530; servers stop 3188 h
  case column: 79.6% / 92.9%, util 59.1% / 51.8%, BE 0.2261
  build-scope check N=6: baseline_sweep.simulate(dhw_direct_share=37/45, tank_loss 2.80) = 77.72%, util 59.5%, BE 0.2292
  build-scope check N=8: baseline_sweep.simulate(dhw_direct_share=37/45, tank_loss 2.80) = 90.74%, util 52.1%, BE 0.2293
```

## 8. Limits of this analysis

- The return limit is a pessimistic on/off bound: servers stop for the whole hour when the heating return exceeds the limit. Throttling, or a partial run against a cooler buffer bottom, would land between that bound and the A0 row.
- The 45 °C coolant inlet limit is an *assumption* taken from rack-scale sources. No data sheet for a cold-plated RTX PRO 4500 box states it. The 60 °C ratings belong to the water blocks.
- Cold-plate retrofit costs other than the blocks are *assumptions* (CPU plate, manifold, couplings, leak sensor, labour, CDU). Swiss prices were not checked. The block price is a German MSRP incl. 19% VAT, converted to CHF and Swiss VAT.
- Workstation-edition RTX PRO 4500 cards (the ones with a block) are not the Server Edition measured by MLPerf. Power, price and throughput were kept at the r4 values (*assumption*).
- The air chains rest on an assumed 15 K air rise across the box and a 5 K coil approach. The HPE inlet-air limit for this GPU configuration was not read.
- Heat-pump COPs are test-point values (A20 or W10/W55), used as lower bounds. The Carnot-scaled COP is an extrapolation.
- In the AIR+HPB chain, the hot-water heat pump draws the server-room air. Its own 258 l store and the buffer are lumped into one tank of 1.163 × (40 − 20) kWh, which is conservative for capacity.
- The hot-water cylinder's standby loss is still not modelled (round-4 critic point 1).
- All results use the stand-in reference-house CSV.
