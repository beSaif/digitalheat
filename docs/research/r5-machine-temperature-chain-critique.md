# Critique, round 5: machine and temperature chain

Critic file for `docs/research/r5-machine-temperature-chain.md` and `analysis/r5_chain.py`. I took the role of a sceptical DigitalHeat founder. I did not change any existing file or touch git state. Written Sat 21 Nov 2026.

## 1. Verdict in brief

- **The numbers reproduce.** `python3 analysis/r5_chain.py` exits 0, and every printed figure matches the investigator's section 7. The regression check against `r4_tank_layout.sim` passes, and the build-scope check gives 77.72% / 90.74%.
- **The recommended DLC chain is still not one consistent machine.** It costs four *server-edition* RTX PRO 4500 cards (passive, 165 W) with four Alphacool blocks made for a different card. I found no block for the server edition either. NVIDIA lists the *workstation* RTX PRO 4500 at "200W", "dual slot", "Active" (<https://www.nvidia.com/en-eu/products/workstations/professional-desktop-gpus/rtx-pro-4500.md>, opened).
  - A box that really takes these blocks needs workstation cards. On r4's central power model it then draws about **1,095 W instead of 955 W (+15%)**.
  - MLPerf did not measure its throughput.
  - "Same box, same numbers" is therefore not true. The weak point is narrowed, not closed.
- **Missed alternative.** NVIDIA's own page for the RTX PRO 6000 Blackwell Server Edition lists an official liquid-cooled variant: "Liquid: Single-Slot, FHXL", "Up to 600W (configurable)" (<https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/>, opened). One such card plus a host is close to the case's 1 kW server, and it is a vendor-made liquid-cooled part, not an enthusiast retrofit. It needs a different throughput basis. The investigator compared only third-party blocks for this card.
- **The realism column is layout A relabelled.** For floor heating and 50/40 radiators, the DLC rows are identical to the A0 rows (coverage, server-hours, starts) because the 40 °C return limit never binds. So the "computed" DLC coverage adds no evidence that the machine delivers 55 °C. The evidence is still the NVIDIA rack-scale blog plus a 10 K-rise flow assumption.
- **Hidden control assumption.** In summer the buffer bottom is at 20 °C, so coolant enters at about 25 °C. A 50 °C top then needs a rise of about 30–35 K on the server side, at about 0.33–0.38 l/min per server (computed below), with outlet-temperature control by a variable-speed pump. Neither the r4 nor the r5 file states this. Without such control the top stays near 35 °C and hot-water direct share falls.
- **Block ratings.** The 60 °C rating is for the blocks, and Alphacool's page also gives a **"recommended working temperature" of 20 °C** (opened). Running at 45–55 °C all year, 5 K below the maximum, is far from what the vendor recommends. That is a five-year reliability question that nobody has costed.
- **Cost framing.** "Only about 4,600 CHF is liquid cooling" is a difference against an *assumed* 2,500 CHF/box air coil. The liquid-cooling hardware itself is about **20,300 CHF per house at N=6** (26,000 at N=8). Every item except the blocks is an assumption.
- **House-side items.** The 6,086 CHF for buffer, fresh-water station and cylinder may already exist in the reference house: the case gives the tank, and a heat-pump house has a cylinder. Without them the total is 206,488 CHF and the share needed 10.97%.
- **The share-needed conclusion is robust.** It stays between 11% and 12.3%, even when retrofit costs rise to 6,000 CHF per box with a 6,000 CHF CDU.
- **One source not confirmed.** I could not open the DCD Qarnot page (HTTP 403 to WebFetch, a Cloudflare page to curl; my single Firecrawl call was refused for lack of credits). TechCrunch, which I did open, supports a weaker version: "Up to 95% of computer waste heat is turned into hot water", AMD Epyc / Intel Xeon, up to 12 servers per module, no temperature.

## 2. Sources re-checked (opened 21 Nov 2026)

| Claim | Result | URL |
|---|---|---|
| c1 EK-Pro RTX PRO 6000 SE | **Confirmed:** £412.99 "Inc VAT"; max coolant operating temperature 60 °C; "RTX PRO 6000 Blackwell Server Edition and Max-Q Workstation Edition"; "Single-slot design optimised for rackmount"; corrosion-inhibiting coolant mandatory | <https://www.scan.co.uk/products/ek-pro-gpu-wb-rtx-pro-6000-se-water-block-rtx-pro-6000-server-ed-stainless-steel-top-nickel-plated-c> |
| c2 Alphacool ES RTX 6000 Pro SE | **Confirmed:** €399.98, "All prices incl. value added tax"; max operating temperature 60 °C (coolant or block not stated); **recommended working temperature 20 °C**; 5 available; max test pressure 4 bar | <https://shop.alphacool.com/en/detail/index/sArticle/22570> |
| c3 Alphacool ES block for the RTX Pro 4500 | **Price confirmed** (€399.98). The page names "RTX Pro 4500 Blackwell" **without an edition**; "workstation" is the investigator's reading (plausible, since no server-edition block exists). No availability date on this page. Modified 2026-10-09 | <https://overclocking.com/?p=257233> |
| c4 no block for the 4500 Server Edition | My own search (`"RTX PRO 4500" "Server Edition" water block`) found none either. It is still an absence claim | search only |
| c5 Qarnot QBx, 96% by cold plate | **Not confirmed:** DCD blocked. TechCrunch (opened) says "up to 95%", AMD Epyc and Intel Xeon, up to 12 servers per module, no temperature, no price | <https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/> |
| c7 Heata | **Confirmed:** "up to 4.8 kWh per day, and at least 2.5 kWh"; thermal bridge; "vented 425mm to 450mm diameter cylinders"; no temperature | <https://www.cnx-software.com/2023/02/15/install-a-server-in-your-house-get-free-hot-water/> |
| c8 WPZ Dolder WP-ZR28-1 | **Confirmed** (curl + pdftotext): "medium (55°C)" table, W10/W55 column (A-10): 8.5 kW, 2.3 kW input, COP 3.6; dated 28.03.2025. The unit's allowed source-water range (can it take 25–40 °C?) is not in this table | <https://www.ost.ch/fileadmin/dateiliste/3_forschung_dienstleistung/institute/ies/pdf/projekte_wpz/pruefresultate_sw_28032025.pdf> |
| c9 Buderus BW 270 P.2 | **Confirmed:** 1.4 kW; COP 3.63 at EN 16147 A20/W10-53; operating range −10 to +35 °C; 62 °C without the element, 65 °C with it | <https://www.buderus.com/ch/media/country_pool/wissen/documents/fl_bw270p.2_bw400.2_neu.pdf> |
| c10 heat-pump water heater, CH price | **Confirmed:** "ca. CHF 3.300–4.600" for 260–300 l; "typischerweise rund CHF 6.000 inklusive Montage und Entsorgung des alten Boilers", which 42watt attributes to Topten.ch (20.08.2026), so it is second-hand | <https://42watt.de/magazin/waermepumpenboiler-300-liter> |
| c26 ECB rate | **Confirmed:** ECB daily XML, 2026-11-20: CHF 0.9223, USD 1.0990 | <https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml> |
| New: workstation RTX PRO 4500 | "200W", "dual slot", "Active", 32 GB | <https://www.nvidia.com/en-eu/products/workstations/professional-desktop-gpus/rtx-pro-4500.md> |
| New: RTX PRO 6000 Server Edition | "Up to 600W (configurable)"; "Air: Dual-Slot, FHFL"; "Liquid: Single-Slot, FHXL"; air-cooled and liquid-cooled variants | <https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/> |

Firecrawl: 1 call, refused (out of credits).

## 3. Re-run and probes

**Re-run.** `python3 analysis/r5_chain.py`, exit 0. The output is identical to the research file section 7 (checked: A0 regression OK; DLC 77.6% / 90.6%; 55/45 64.3% / 73.0% with 853 h; 70/55 29.0% / 30.8%; installed 212,574 / 275,474 CHF; 5-year share 11.2% / 12.3%; build-scope check 77.72% / 90.74%).

**Hand checks:**
- Box cost: 4 × 4,819 + 8,000 + 2,750 = 30,026 CHF.
- Boxes per house: 6 ÷ 0.9547 = 6.2845, so the box total is 188,700 CHF. Adding 14,788 integration and 9,086 house items gives 212,574 CHF.
- Pump break-even: 0.2293 + 0.02 × 0.3325 = 0.2359.
- AIR+HP: (27,616 + 8,158) × 0.3325 − (21,206 + 8,158) × 0.133, divided by 27,616 server-hours, gives 0.2893.
- Hot-water direct share: 37 ÷ 45 = 82.2%.

**Probe.** The script lives in the scratchpad, not the repo, because this critique may add only one file. It imports `baseline_sweep`, `r4_machine` and `r5_chain` read-only:

```
wall W, central model: server edition 955, workstation edition 1095 (+15%)
liquid share with workstation cards: 85.9%
N=6 as r5                  212,574 CHF  5y share 11.24%  BEcase-only share 11.21%
N=6 w/o buffer+FWS+cyl     206,488 CHF  5y share 10.97%  BEcase-only share 10.93%
N=6 stress DLC 6000/box, CDU 6000: 235,999 CHF, liquid cooling total 43,707, 5y share 12.29%
N=6 liquid-cooling hardware total as r5 (not delta vs coil): 20,282 CHF
N=8 as r5                  275,474 CHF  5y share 12.28%  BEcase-only share 12.25%
N=8 w/o buffer+FWS+cyl     269,388 CHF  5y share 12.04%  BEcase-only share 12.01%
N=8 stress DLC 6000/box, CDU 6000: 305,707 CHF, liquid cooling total 56,276, 5y share 13.44%
N=8 liquid-cooling hardware total as r5 (not delta vs coil): 26,043 CHF
N=6: A0 BEcase 0.2293 vs DLC BEcase 0.2359; identical coverage True
N=8: A0 BEcase 0.2293 vs DLC BEcase 0.2360; identical coverage True
server-side rise 10 K -> flow 1.15 l/min per server
server-side rise 30 K -> flow 0.38 l/min per server
server-side rise 35 K -> flow 0.33 l/min per server
```

The 6,000 CHF per box and 6,000 CHF CDU stress values are *assumptions*. The workstation power uses r4's central model with the sourced 200 W.

**Code observations:**
- In `r5_chain.sim`, `"dumped": 0.0` is hard-coded. It is true by construction of the follow rule (the largest k whose surplus fits the tank), but it is not a measured result. Present "0 dumped" as a property of the rule.
- The share-needed line mixes conventions. r4 uses the case break-even (0.2261), while r5 DLC uses BEchg (element and pumps charged). The effect is 0.03 points, which is negligible, but it should be stated.
- Return-limit rule: the servers stop for the whole hour when the return is above the limit. The buffer bottom fed by the fresh-water station's cold return could still cool them, so the radiator lines are lower bounds. The investigator says so; the pitch must too.
- DLC50 keeps the house top at 50 °C, although 50 °C in and 60 °C out would allow about 55 °C. That is conservative and harmless, but the outlet then sits exactly at the block rating.
- The heat-pump chains credit compressor heat at the case's 0.133 CHF/kWh, so a heat pump at COP 3.6 "loses" against the case's COP 2.5 reference on every compressor kWh. That is consistent with the case convention. But in that house, the server-source heat pump *is* the house heat pump, so its 16,300 CHF is partly counterfactual capital the house would spend anyway.

## 4. What should go into the plan

- **Realism column:** keep the numbers, but label them "reference GPU class with water cold plates (DLC). Retrofit costed; no block confirmed for the exact server-edition card; coolant ≤ 45 °C in, about 55 °C out with variable-flow outlet control." Show 0.2293 (case convention) and 0.2359 (with pumps) side by side.
- **Open risk 5:** do not drop it. Reword it to: "the costed DLC retrofit uses blocks for a different edition of the card. Until a server-edition block or a vendor liquid-cooled configuration (for example NVIDIA's liquid RTX PRO 6000 Server Edition) is named, the realism column describes a modified machine whose wall power and throughput are not measured."
- **Realism sentence:** drop "On the same servers". Say "With water cold plates on the GPUs, …", and present 64% (55 °C radiators) as "at least 64%".
- **Installed cost:** list the house-side items (6,086 CHF) separately from liquid cooling (about 20,300 CHF at N=6). Say "liquid cooling is about 20,000 CHF per house, about 10% of installed cost; the share needed stays 11–12%".
