# Round 4 research: one coherent reference machine near 1 kW and its full installed cost

Investigator for weak point "J1 at laptop efficiency and J2 at B200-slice efficiency are different machines". Written Saturday 21 Nov 2026. Read first: `docs/overnight.md` (incl. "Read this first"), `r3-machine-and-income.md` and its critique, `r2-host-income-hardware.md` and its critique. Their searches were not repeated. Paid Firecrawl calls used: **2 of 6** (one gave a captcha page).

Status labels: **sourced** = number read by me on the opened page or file at the URL given; **computed** = produced by `analysis/r4_machine.py` (command below) or by arithmetic shown here; **assumption** = our own choice; **unverified** = seen only in a search snippet, or not confirmed.

Currency: CHF. 1 USD = 0.8392 CHF and 1 EUR = 0.9223 CHF (ECB reference rates of 20 Nov 2026, sourced in round 1: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>). Swiss VAT 8.1% (sourced: <https://www.estv.admin.ch/en/vat-rates-switzerland>, "Normal rate: 8,1 %", read 21 Nov 2026). Provider prices for work are list prices in USD without VAT (r3).

## 1. Short answer

1. **One machine runs both jobs, and MLPerf measured both on the same box.** Reference machine: a **2U single-socket server with 4 × NVIDIA RTX PRO 4500 Blackwell Server Edition** (32 GB, passive, 165 W max each). MLPerf Inference v6.1, ID **6.1-0017** (Cisco UCS X210 M8 node, 4 × RTX PRO 4500 Blackwell): whisper-large-v3 Offline **61.104 samples/s**, llama3.1-8b Offline **9,518.66 output tokens/s** (fp4). Cross-check on a 2U single-socket HPE DL345 Gen12 with the same 4 GPUs (6.1-0056): whisper 58.08 samples/s.
2. **Wall power is not measured** (v6.1 has no power results). Built on sourced maxima (GPU 165 W, CPU EPYC 9375F 320 W TDP): **about 0.95 kW at the wall (range 0.75 to 1.22 kW)** (assumption). It is "near 1 kW", so one case server = about one box.
3. **Work per kWh on this one machine** (central power, computed): J1 **1,411 audio-hours per server-hour (0.71 Wh per audio-hour)**, J2 **35.9 million output tokens per server-hour**. J1 is about 2× the laptop rule (667 to 755) and 0.7× the B200 slice (1,988). J2 is 0.64× the B200 slice (56.07 M).
4. **Installed cost, central: about 33,600 CHF per 1 kW server, 202,000 CHF per house at N = 6 and 264,000 at N = 8** (incl. 8.1% VAT). Of this, 4 GPUs are about 19,300 CHF per box (sourced Swiss prices), platform 8,000 and heat capture 2,500 (assumptions), plus about 14,800 CHF per house for hydraulic and electrical integration (computed from the BFE heat-pump price study). Range 22,700 to 40,400 CHF per kW for the box alone.
5. **Share of list price the operator must capture** (50/50 mix, central price, N = 6, all permit hours sold): **1.6% to cover electricity minus heat; 10.7% to pay back the installed cost in 5 years; 7.3% in 8 years.** At 67% sold (unsold hours still run): 2.4%, 16.0% and 10.9%. N = 8: 11.8% / 8.0% (17.6% / 11.9% at 67% sold). Range over low to high cost and price: **3.1% to 25.3% for 5 years** (N = 6, all sold).
6. **Against r3's line** (laptop J1 + B200-slice J2, laptop-class hardware): operation 2.4% → 1.6%; full cost 20% (30% at 67% sold) → **10.7% (16.0%)**. The coherent machine needs a **smaller** share than r3's reductio, because the J1 list value per kWh roughly doubles while hardware per kW falls from about 52,000 to about 31,000 CHF.
7. **It pays off only if the operator gets more than about a tenth of the list price, and only for transcription-heavy work.** J2 alone (LLM generation) needs **31.7%** of list for a 5-year payback, about 3× J1 alone (6.4%). At the low price the mix needs 19.8% (29.5% at 67% sold). At w = 20% and s = 67% (r3's scenario switches) it pays back in **3.9 years at the central price, 8.1 years at the low price** (N = 6). That is outside a 5-year life, and unlimited demand is assumed.
8. **Renting the box by the hour cross-checks the share.** Renter prices for this GPU (21 Nov 2026) are 0.41 / 0.72 / 0.92 USD per GPU-hour. That is **10% / 18% / 23% of the central list value** of the work the box can do. The 10.7% hurdle sits inside that band. But these are prices for always-available, data-centre-hosted GPUs, and r2 found no market that pays a heat-following host.
9. **New feasibility facts.** One house at N = 6 would transcribe about **60,000 audio-hours a day** (2× the laptop figure), which is about **0.9 TB a day, or 80 Mbit/s sustained**, at 32 kbit/s (assumption). The machine is air-cooled, so heat comes out as air at roughly 35 to 45 °C. Water from an air-to-water coil is then too cold for 60 °C hot water, which strengthens the booster caveat. About 200,000 CHF of GPUs would sit in one basement.

## 2. Why this machine (task a)

Candidates checked in the local MLPerf v6.1 summary (`data/raw/mlperf_inference_v6.1_summary.xlsx`, a copy of <https://github.com/mlcommons/inference_results_v6.1>; parsed with a stdlib xlsx reader in my scratchpad). These are the systems with **both** whisper Offline and llama3.1-8b Offline results on the same box:

| ID | System | GPUs | llama3.1-8b Offline tok/s | whisper Offline tok/s | Status |
|---|---|---|---|---|---|
| 6.1-0017 | Cisco UCS X210 M8 X580P node | 4 × RTX PRO 4500 Blackwell (32 GB) | 9,518.66 | 3,877.67 | sourced (local xlsx) |
| 6.1-0011 | Cisco UCS C240 M8 | 5 × RTX PRO 4500 | 12,017.7 | 4,808.98 | sourced (local xlsx) |
| 6.1-0019 | Cisco UCS X215c M8 X580P node | 4 × RTX PRO 6000 Blackwell Server Edition (96 GB) | 24,913.5 | 9,236.94 | sourced (local xlsx) |
| 6.1-0013 / 6.1-0049 | Cisco C845A / HPE DL380a Gen12 | 8 × RTX PRO 6000 SE | 50,453.7 / 50,965.3 | 18,991.8 / 19,278.3 | sourced (local xlsx); 4.8 kW of GPUs alone, too big for one case server |
| 6.1-0061 / 0090 / 0098 | Intel, Quanta, Supermicro | 4 × Intel Arc Pro B70 | 4,613 to 4,978 | 5,401 to 5,855 | sourced (local xlsx); not pursued (PyTorch stack, no price or power read) |
| 6.1-0032 and other CPU-only rows | 2 × Xeon 6 | none | 853 to 2,069 | 1,100 to 2,971 | sourced (local xlsx); r3's CPU-only comparison |

**Choice: 4 × RTX PRO 4500 Blackwell Server Edition in a 2U single-socket server.**
- The GPUs alone draw 660 W at most, so the box lands near 1 kW. Both job types were measured on **the same MLPerf system** (6.1-0017), so no per-GPU scaling is needed.
- A 2U single-socket server with exactly these 4 GPUs was benchmarked by HPE (DL345 Gen12, 6.1-0056), which shows that the configuration exists as a product.
- The alternative (1 × RTX PRO 6000 Blackwell, 600 W, plus a platform) is in section 7. It is not the reference, because its throughput would have to be scaled from a 4-GPU result and its Swiss price was not confirmed.

### 2.1 Throughput (sourced, MLPerf v6.1 loadgen logs)

| Item | Value | Status | Source |
|---|---|---|---|
| whisper Offline, 6.1-0017 | "Samples per second: 61.104", "Tokens per second: 3877.67", "Result is : VALID" | sourced | <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/Cisco/results/X210M8_X580P_RTXPro4500_32GBx4_TRT/whisper/Offline/performance/run_1/mlperf_log_summary.txt> |
| llama3.1-8b Offline, 6.1-0017 | "Samples per second: 73.7905", "Tokens per second: 9518.66", VALID (129.0 output tokens per sample, computed) | sourced | <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/Cisco/results/X210M8_X580P_RTXPro4500_32GBx4_TRT/llama3.1-8b/Offline/performance/run_1/mlperf_log_summary.txt> |
| Precision | llama "weight_data_types": "fp4"; whisper "fp16" | sourced | `measurements.json` in the same two folders (…/llama3.1-8b/Offline/measurements.json, …/whisper/Offline/measurements.json) |
| Whisper accuracy, 6.1-0017 | "Word Error Rate: 2.1317700353074414%, accuracy=97.86822996469256%" | sourced | …/whisper/Offline/accuracy/accuracy.txt (same base path) |
| System 6.1-0017 | 2 × Xeon 6747P (48 cores), 1 TB RAM, "Air-cooled", "NVIDIA RTX PRO 4500 Blackwell", 4 per node | sourced | <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/Cisco/systems/X210M8_X580P_RTXPro4500_32GBx4_TRT.json> |
| Cross-check 6.1-0056, HPE ProLiant Compute DL345 Gen12 | 1 × AMD EPYC 9375F (32 cores), 384 GB, "Air-cooled", 4 × "NVIDIA RTX PRO 4500 Blackwell Server Edition"; whisper "Samples per second: 58.0816" | sourced | <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/HPE/systems/HPE_PROLIANT_DL345_GEN12_RTX_PRO_4500_PCIE_32GBx4_TRT.json>, <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/HPE/results/HPE_PROLIANT_DL345_GEN12_RTX_PRO_4500_PCIE_32GBx4_TRT/whisper/Offline/performance/run_1/mlperf_log_summary.txt> |
| Audio per whisper sample | 22.05 s ("approximately 10 hours" ÷ 1,633 samples); samples are zero-padded to 30 s, so 30 s is an upper bound | from r3 (sourced there: <https://raw.githubusercontent.com/mlcommons/inference/master/speech2text/README.md>) | — |
| Audio-hours per box-hour | 61.104 × 22.05 = **1,347** (1,833 at 30 s; 1,281 on the HPE box) | computed | — |

Caveats:
- MLPerf runs **whisper-large-v3**, while our laptop J1 runs **large-v3-turbo**. On the same GPU, turbo should be faster (4 decoder layers instead of 32). The speed-up factor was not found (unverified), so the J1 figure here is conservative for turbo work.
- The llama figure counts output tokens only; the input tokens are processed too (as in r3).
- MLPerf Offline is a large batch run with the model loaded. It does not include restarts after a pause.

### 2.2 Wall power (assumption built on sourced maxima)

| Item | Value | Status | Source |
|---|---|---|---|
| RTX PRO 4500 Blackwell Server Edition | "Max power consumption: 165 W"; "32GB GDDR7"; "single slot"; "Thermal: Passive" | sourced | <https://www.nvidia.com/en-eu/data-center/rtx-pro-4500-blackwell-server-edition.md> |
| AMD EPYC 9375F (the CPU in the HPE MLPerf box) | "Default TDP 320W", "cTDP 320-400W", 32 cores, launched 10/10/2024 | sourced | <https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9375f.html> (curl, tags stripped) |
| Wall power of the box | low 0.75 / **central 0.95** / high 1.22 kW = (4 × 165 W × 0.85/0.95/1.00 + CPU 100/180/320 W + RAM, fans, SSD, NIC 60/100/150 W) ÷ PSU efficiency 0.96/0.95/0.93 | **assumption** (formula in the script) | — |
| No measured wall power found for any 4-GPU RTX PRO 4500 box | MLPerf v6.1 has no power rows (r3); no review with a wall meter searched beyond that | — | — |

The share of list value needed for **hardware** does not depend on wall power: cost per kW and work per kWh both scale with 1/P. Only the electricity term and the per-house items move with it (computed; section 4 of the output gives 10.2% to 11.3% across the power range).

### 2.3 Price (task a)

| Item | Price | Status | Source |
|---|---|---|---|
| PNY RTX PRO 4500 (passive, "Ideal for server applications", "0 (Data Center GPU)" outputs), Swiss Post shop | **CHF 4,819.00**, "Delivery within 1-2 working days" for Switzerland; VAT wording not shown (Swiss B2C prices are normally incl. VAT: **unverified**). The page lists both "GDDR6" and "GDDR7" | sourced 21 Nov 2026 (WebFetch) | <https://shop.post.ch/en/electronics/pc-components/graphics-cards/pny-graphics-card-rtx-pro-4500/p/890739> |
| PNY NVIDIA RTX PRO 4500 Blackwell Edition serveur, LDLC Switzerland | **CHF 5,641.95**, "En stock dans + de 15 jours"; VAT wording not found | sourced 21 Nov 2026 (WebFetch, and `"price": "5641.95"`, `priceCurrency "CHF"` in the page source via curl) | <https://www.ldlc.com/fr-ch/fiche/PB00733928.html> |
| Same card, 10 German shops | 4,679.00 EUR (alza.de) to 6,022.69 EUR (geniuzcom.de), galaxus 5,382.96; "Preise inkl. MwSt., zzgl. Versand"; updated "21.11.2026 09:20" | sourced | <https://www.hardwaredealz.com/hardware/gpu/nvidia-rtx-pro-4500-blackwell-32gb/pny-rtx-pro-4500-blackwell-server-edition/preisvergleich.33604> |
| Cheapest German price brought to Swiss VAT | 4,679 ÷ 1.19 × 0.9223 × 1.081 = **CHF 3,920** (import fees and shipping not included) | computed; 19% German VAT is an assumption | — |
| A search snippet showed LDLC.ch at CHF 4,285.95 | the opened page shows 5,641.95 | **unverified**, not used | — |
| Platform: Supermicro AS-2115HE-FTNR (2U, single EPYC 9005/9004, "Up to 4 GPUs", 2 × 2000 W Titanium PSU), Supermicro EU store | WebFetch read "System Starting Price" **€6,924.49**. Firecrawl's page metadata shows prices **2,642.07 / 3,399.80 / 3,850.37 EUR**. VAT status and base contents not stated. The listed GPU options are "1x RTX PRO 6000 Blackwell Server Edition or 3x L40S/RTX Pro 6000 Max-Q", so 4 × RTX PRO 4500 is **not** a listed configuration | sourced (conflicting figures on one page) | <https://store.supermicro.com/nl_en/as-2115he-ftnr.html> |
| HPE DL345 Gen12 (the MLPerf box) | no price found; HPE storefronts show reseller prices only after configuration | — | <https://buy.hpe.com/de/de/compute/rack-servers/proliant-dl300-servers/hpe-proliant-compute-dl345-gen12/p/1014896097> (search result, not opened) |
| **Platform price used** (2U 1P chassis, EPYC CPU, RAM, SSD, redundant PSU) | low 5,000 / **central 8,000** / high 12,000 CHF incl. VAT | **assumption** anchored on the Supermicro page | — |

Box price (computed, `r4_machine.py` section 2): 4 cards + platform + heat capture = **21,681 / 29,776 / 38,568 CHF**, i.e. **22,709 / 31,188 / 40,396 CHF per kW** at 0.955 kW. Compare: r2 consumer rig 6,000 CHF per kW (assumption), r3 laptop-class reductio 52,329 CHF per kW (assumption).

## 3. Installed cost for a water-coupled install (task b)

| Item | Per | Low / central / high, CHF incl. 8.1% VAT | Status | Basis |
|---|---|---|---|---|
| 4 × RTX PRO 4500 Server Edition | box | 15,681 / 19,276 / 22,568 | sourced prices (section 2.3), low computed | Swiss shops / German shop + CH VAT |
| Platform | box | 5,000 / 8,000 / 12,000 | assumption | section 2.3 |
| **Heat capture at the box**: closed enclosure, air-to-water coil, fans, controls | box | 1,000 / 2,500 / 4,000 | **assumption, no price found** | The RTX PRO 4500 Server Edition is passive and the MLPerf boxes are "Air-cooled". Cold plates for this card were not found. Retrofitting liquid coolers is "not an economically viable business model" (CEC-500-2024-061, sourced in r2). Enclosure air/water heat exchangers (Rittal SK series) have no public price list; search snippets showed marketplace listings of €299 to €1,351 for other sizes (**unverified**, not used) |
| **House integration**: hydraulic connection to the tank, pump, valves, pipework, pipe insulation, plumber's labour, electrician, commissioning | house | **10,680 / 14,788 / 20,128** | computed from a sourced proxy | BFE/EnergieSchweiz, "Preise von Luft/Wasser Wärmepumpen" (Ernst Basler + Partner, 16 Dec 2015), 9 kW air/water heat pump in a partly renovated 1950s house. Installed system price: "Medianpreis … rund 36‘000 Franken (exkl. MWSt.)", cheapest 26,000, most expensive 49,000. Component shares: heat pump 42%, labour ("Arbeitsleistungen") 17%, "Wassererwärmer, … weiteres Material, … Demontage und Entsorgung des Öltanks sowie … Elektroarbeiten … jeweils 7 bis 8%", masonry, pipe insulation, storage tank and commissioning "zwischen 2 bis 4%". <https://pubdb.bfe.admin.ch/de/publication/download/8157> (PDF, pdftotext, pages 6 and 26–27). We take labour 17 + other material 7.5 + electrical 7.5 + insulation 3 + commissioning 3 = **38%** of the system price, plus 8.1% VAT (computed). **2015 prices, not inflated**; a heat-pump job is a proxy, not a quote for a server connection |
| Grid connection upgrade for 6 to 8 kW of extra continuous load | house | 0 / 0 / 5,000 | assumption | not searched |
| Tank (35 kWh, 1,000 L) | house | not counted | — | the case gives the tank as part of the reference house |
| Network: business internet line | house, per year | 1,200 CHF/yr (variant line only) | assumption | about 80 to 94 Mbit/s sustained would be needed for J1 audio at 32 kbit/s (computed, assumption on codec) |
| Maintenance and repairs | per year | 2% of box hardware (variant line only) | assumption | — |
| Swiss VAT | all items | 8.1% | sourced | <https://www.estv.admin.ch/en/vat-rates-switzerland> |

**Totals (computed):** N = 6: **201,914 CHF per house** (6.28 boxes, 33,652 CHF per 1 kW server); N = 8: **264,289 CHF** (8.38 boxes, 33,036 per server). Per-house items are only about 6 to 9% of this (computed: 14,788 ÷ 201,914 = 7.3% at N = 6, 5.6% at N = 8, 9.4% in the high case); **the GPUs are about 60%** (6.28 × 19,276 ÷ 201,914).

Not included: interest (simple payback), resale value, insurance against theft and water damage, remote hands, failed-part replacement beyond the 2% variant, whether a 60 °C hot-water booster is needed (`assumption-limits.md` section 2: air-cooled output is too cold for hot water), and noise (a 2U server with chassis fans in a basement; the enclosure may help).

**Compute-heater vendors:** none with a published installed price was found in r2 (Qarnot, Heata, 21energy); not searched again.

## 4. Script and output (task c)

`analysis/r4_machine.py` (new; stdlib only; imports `load`, `simulate`, `PRICE`, `HEAT_VALUE` from `analysis/baseline_sweep.py`, which is unchanged; policy `follow`, case assumptions). Command, from the repo root:

```
python3 analysis/r4_machine.py
# options: --years 5 8   --sold 0.67   --operator-share 0.20
```

Output of 2026-11-21, exit 0:

```
r4_machine.py. Currency CHF; 1 USD = 0.8392 CHF, 1 EUR = 0.9223 CHF (ECB 20 Nov 2026); Swiss VAT 8.1%.
LIST VALUE = what end customers pay a provider at public batch prices, NOT the operator's income.

== 1. Reference machine: 2U 1P server, 4 x RTX PRO 4500 Blackwell Server Edition ==
  wall power low         751 W  = (4 x 165 W x 0.85 + CPU 100 W + rest 60 W) / PSU 0.96   [ASSUMPTION on SOURCED 165 W and 320 W maxima]
  wall power central     955 W  = (4 x 165 W x 0.95 + CPU 180 W + rest 100 W) / PSU 0.95   [ASSUMPTION on SOURCED 165 W and 320 W maxima]
  wall power high       1215 W  = (4 x 165 W x 1.00 + CPU 320 W + rest 150 W) / PSU 0.93   [ASSUMPTION on SOURCED 165 W and 320 W maxima]
  box throughput: whisper-large-v3 61.104 samples/s x 22.05 s = 1,347 audio-h per box-hour (1,833 if every sample were 30 s); HPE DL345 cross-check 1,281
                  llama3.1-8b fp4 9,518.66 output tok/s = 34.27 M per box-hour   [SOURCED, MLPerf v6.1 6.1-0017 / 6.1-0056]
  work per case server-hour (= per kWh at the wall):
  power     audio-h/kWh Wh/audio-h M tok/kWh
  low             1,794      0.557     45.63
  central         1,411      0.709     35.89
  high            1,109      0.902     28.20
  compare: laptop rule (i) 667-755 audio-h/kWh (1.3-1.5 Wh); 8 x B200 slice 1,988 audio-h/kWh (0.50 Wh) and 56.07 M tok/kWh   [r3, COMPUTED]

== 2. Installed cost (CHF incl. 8.1% VAT) ==
  GPU card: low 3,920 (cheapest German offer EUR 4,679.00 incl. 19% VAT -> ex VAT -> CHF + 8.1%), central 4,819 (post.ch), high 5,642 (ldlc.ch)
  low      box: 4 cards  15,681 + platform  5,000 + heat capture 1,000 =  21,681 per box =  22,709 per kW (central power) | house integration 10,680 + grid     0 per house
  central  box: 4 cards  19,276 + platform  8,000 + heat capture 2,500 =  29,776 per box =  31,188 per kW (central power) | house integration 14,788 + grid     0 per house
  high     box: 4 cards  22,568 + platform 12,000 + heat capture 4,000 =  38,568 per box =  40,396 per kW (central power) | house integration 20,128 + grid 5,000 per house
  house integration = 38% of the BFE 2015 heat-pump system price (26,000 / 36,000 / 49,000 excl. VAT) + 8.1% VAT   [COMPUTED from SOURCED shares; 2015 prices]

== 3. N = 6: 31,067 server-h/yr, coverage 79.6%, dumped 0 kWh, electricity - heat = 0.2261 CHF per server-h   [COMPUTED, baseline_sweep.simulate] ==
  work per year if every permit hour is filled (UNLIMITED DEMAND ASSUMED), central power, 50/50:
    J1 21.9 M audio-h/yr (60,058 per day); J2 558 bn output tokens/yr
    audio volume at 32 kbit/s (ASSUMPTION): 0.86 TB per day = 80 Mbit/s sustained into the house
  installed cost per house (central): 201,914 CHF for 6.28 boxes (33,652 per 1 kW server)
  CHF needed per sold server-h (100% sold, no interest): operation 0.2261; + install 5 y 1.526; 8 y 1.039
  list value per server-h (central power):         J1     J2   mix 50/50
    price low                                    14.21   1.20   7.71   (r3 mix: 4.30)
    price central                                23.69   4.82  14.25   (r3 mix: 9.36)
    price high                                   53.29  23.19  38.24   (r3 mix: 30.70)
  SHARE OF LIST PRICE the operator must capture (mix 50/50, central power, 100% of run hours sold; in brackets: 67% sold, unsold hours still run):
    cost caseprice         operation      +install 5 y      +install 8 y       +fixed/yr 5 y
    low      low          2.9% ( 4.4%)      15.2% (22.7%)      10.6% (15.8%)        16.8% (25.1%)
    low      central      1.6% ( 2.4%)       8.2% (12.3%)       5.7% ( 8.6%)         9.1% (13.6%)
    low      high         0.6% ( 0.9%)       3.1% ( 4.6%)       2.1% ( 3.2%)         3.4% ( 5.1%)
    central  low          2.9% ( 4.4%)      19.8% (29.5%)      13.5% (20.1%)        21.9% (32.6%)
    central  central      1.6% ( 2.4%)      10.7% (16.0%)       7.3% (10.9%)        11.8% (17.6%)
    central  high         0.6% ( 0.9%)       4.0% ( 6.0%)       2.7% ( 4.1%)         4.4% ( 6.6%)
    high     low          2.9% ( 4.4%)      25.3% (37.7%)      16.9% (25.2%)        27.8% (41.5%)
    high     central      1.6% ( 2.4%)      13.7% (20.4%)       9.1% (13.6%)        15.0% (22.4%)
    high     high         0.6% ( 0.9%)       5.1% ( 7.6%)       3.4% ( 5.1%)         5.6% ( 8.4%)
  payback at operator share w = 20%, sold s = 67% (case convention: unsold permit hours still run as heaters), central costs, no interest:
    price low      income    32,089 CHF/yr, minus electricity-heat  7,024 =    25,065 CHF/yr -> payback   8.1 y on 201,914 CHF  (does NOT pay back in 8 y)
    price central  income    59,333 CHF/yr, minus electricity-heat  7,024 =    52,309 CHF/yr -> payback   3.9 y on 201,914 CHF
    price high     income   159,205 CHF/yr, minus electricity-heat  7,024 =   152,180 CHF/yr -> payback   1.3 y on 201,914 CHF

== 3. N = 8: 36,281 server-h/yr, coverage 92.9%, dumped 0 kWh, electricity - heat = 0.2261 CHF per server-h   [COMPUTED, baseline_sweep.simulate] ==
  work per year if every permit hour is filled (UNLIMITED DEMAND ASSUMED), central power, 50/50:
    J1 25.6 M audio-h/yr (70,138 per day); J2 651 bn output tokens/yr
    audio volume at 32 kbit/s (ASSUMPTION): 1.01 TB per day = 94 Mbit/s sustained into the house
  installed cost per house (central): 264,289 CHF for 8.38 boxes (33,036 per 1 kW server)
  CHF needed per sold server-h (100% sold, no interest): operation 0.2261; + install 5 y 1.683; 8 y 1.137
  list value per server-h (central power):         J1     J2   mix 50/50
    price low                                    14.21   1.20   7.71   (r3 mix: 4.30)
    price central                                23.69   4.82  14.25   (r3 mix: 9.36)
    price high                                   53.29  23.19  38.24   (r3 mix: 30.70)
  SHARE OF LIST PRICE the operator must capture (mix 50/50, central power, 100% of run hours sold; in brackets: 67% sold, unsold hours still run):
    cost caseprice         operation      +install 5 y      +install 8 y       +fixed/yr 5 y
    low      low          2.9% ( 4.4%)      16.7% (24.9%)      11.5% (17.2%)        18.4% (27.5%)
    low      central      1.6% ( 2.4%)       9.0% (13.5%)       6.2% ( 9.3%)        10.0% (14.9%)
    low      high         0.6% ( 0.9%)       3.4% ( 5.0%)       2.3% ( 3.5%)         3.7% ( 5.5%)
    central  low          2.9% ( 4.4%)      21.8% (32.6%)      14.7% (22.0%)        24.0% (35.9%)
    central  central      1.6% ( 2.4%)      11.8% (17.6%)       8.0% (11.9%)        13.0% (19.4%)
    central  high         0.6% ( 0.9%)       4.4% ( 6.6%)       3.0% ( 4.4%)         4.8% ( 7.2%)
    high     low          2.9% ( 4.4%)      27.8% (41.6%)      18.5% (27.6%)        30.6% (45.6%)
    high     central      1.6% ( 2.4%)      15.1% (22.5%)      10.0% (14.9%)        16.5% (24.7%)
    high     high         0.6% ( 0.9%)       5.6% ( 8.4%)       3.7% ( 5.6%)         6.2% ( 9.2%)
  payback at operator share w = 20%, sold s = 67% (case convention: unsold permit hours still run as heaters), central costs, no interest:
    price low      income    37,475 CHF/yr, minus electricity-heat  8,203 =    29,271 CHF/yr -> payback   9.0 y on 264,289 CHF  (does NOT pay back in 8 y)
    price central  income    69,291 CHF/yr, minus electricity-heat  8,203 =    61,088 CHF/yr -> payback   4.3 y on 264,289 CHF
    price high     income   185,924 CHF/yr, minus electricity-heat  8,203 =   177,721 CHF/yr -> payback   1.5 y on 264,289 CHF

== 4. Sensitivity, N = 6, central price, share needed for 5-y payback (100% sold) ==
  base (central power, cost, price)                      operation   1.6%  5-y  10.7%
  wall power low (0.75 kW per box)                       operation   1.2%  5-y  10.2%
  wall power high (1.22 kW per box)                      operation   2.0%  5-y  11.3%
  cost low                                               operation   1.6%  5-y   8.2%
  cost high                                              operation   1.6%  5-y  13.7%
  30 s of audio per MLPerf sample                        operation   1.2%  5-y   8.2%
  J1 priced as large-v3 batch (0.0555 USD/audio-h)       operation   0.6%  5-y   4.3%
  J1 only (mix 100/0)                                    operation   1.0%  5-y   6.4%
  J2 only (mix 0/100)                                    operation   4.7%  5-y  31.7%

== 5. Cross-check: renting the box by the hour instead of selling work (N = 6, central power and cost) ==
  renter prices per GPU-hour, read 21 Nov 2026 [SOURCED]: GPU.ai 0.41 (cheapest, getdeploying.com), RunPod Secure Cloud 0.72 (runpod.io), median of 7 providers 0.92 (getdeploying.com)
  These are prices for data-centre-hosted, always-available GPUs. A heat-following basement host is not shown to get them (r2: hosts must stay available).
    cheapest 0.41  renter  1.44 CHF per server-h = 10.1% of central list value; host (x0.8) 1.15; net 0.93; payback  7.0 y on 33,652 CHF per server (all 5,178 permit h/yr rented)
    RunPod 0.72    renter  2.53 CHF per server-h = 17.8% of central list value; host (x0.8) 2.03; net 1.80; payback  3.6 y on 33,652 CHF per server (all 5,178 permit h/yr rented)
    median 0.92    renter  3.23 CHF per server-h = 22.7% of central list value; host (x0.8) 2.59; net 2.36; payback  2.8 y on 33,652 CHF per server (all 5,178 permit h/yr rented)

  r3 line for comparison (laptop J1 + B200-slice J2, laptop-class hardware 52,329 CHF/kW, N=6, 5 y, central): operation 2.4%, full 20% (30% at 67% sold)
  NOTE: hardware's share of list value does not depend on wall power (cost per kW and work per kWh both scale with 1/P); only the electricity term and the per-house items do.
```

### 4.1 Reading the output

- **Coverage, dumped heat, utilisation and the 0.2261 CHF break-even do not change.** The machine only changes the work per server-hour, the list value and the installed cost. The break-even is the case formula on electricity and heat, so it is the same for any machine with 1 kW per server.
- **Work per server-hour on one machine** (central power): J1 1,411 audio-hours, J2 35.9 M output tokens. List value at r3's prices: J1 14.21 / 23.69 / 53.29 CHF, J2 1.20 / 4.82 / 23.19 CHF, **mix 7.71 / 14.25 / 38.24 CHF** (low / central / high). r3's incoherent mix was 4.30 / 9.36 / 30.70.
- **Share needed, central cost and price, N = 6:** operation **1.6%**; **10.7%** with a 5-year payback; **7.3%** with 8 years; 11.8% for 5 years with internet and 2% maintenance a year. At 67% sold: 2.4% / 16.0% / 10.9% / 17.6%. N = 8 is about 1 point higher (11.8% / 8.0%), because the 8th server runs fewer hours on the same per-house costs.
- **In CHF per sold server-hour** (N = 6, all sold, no interest): 0.2261 for operation, **1.526** with a 5-year payback, **1.039** with 8 years. N = 8: 1.683 / 1.137. For comparison, r2 had 0.54 to 0.64 net at 6,000 CHF per kW.
- **The cost range matters less than the price and the job mix.** For 5 years at N = 6: cost low → high moves the share from 8.2% to 13.7%. Price high → low moves it from 4.0% to 19.8%. J1 only vs J2 only moves it from **6.4% to 31.7%**.
- **Transcription carries the economics.** On this machine an LLM server-hour is listed at 4.82 CHF (central) and a transcription server-hour at 23.69 CHF. J1 work, however, needs about 60,000 audio-hours a day of demand per house (N = 6), with no buyer named. If paid demand is mostly LLM batch work (a deeper market), the hurdle is about 32% for 5 years and 21% for 8 years (8-year J2-only figure computed by hand: (0.2261 + 201,914 ÷ (8 × 31,067)) ÷ 4.82 = 21.5%).
- **Scenario w = 20%, s = 67%** (r3's switches; unlimited demand; unsold hours still run): payback **3.9 years** (central price), **8.1 years** (low price), 1.3 years (high price), at N = 6 and central cost. N = 8: 4.3 / 9.0 / 1.5 years.
- **Rental cross-check (section 5 of the output):** a renter pays 10.1% / 17.8% / 22.7% of the central list value for this box's hours (cheapest / RunPod / median). Renting all 5,178 permit hours a year at those prices would pay back in 7.0 / 3.6 / 2.8 years. This is an independent sign that 10 to 20% of the list value is what GPU-hours sell for. It is **not** a sign that a heat-following basement host can sell them: r2 found that hosts must stay available, and these are data-centre prices.

### 4.2 Sources for the rental cross-check

| Item | Value | Status | Source |
|---|---|---|---|
| RunPod, RTX PRO 4500 SE | "Secure Cloud $/hr 0.72"; Community Cloud blank; no spot price | sourced 21 Nov 2026 (WebFetch) | <https://www.runpod.io/gpu-models/rtx-pro-4500-se> |
| GetDeploying, RTX PRO 4500 | "As of November 21, 2026, the median on-demand price is $0.92 per GPU per hour across 7 providers"; cheapest "$0.41 /GPU/hr" from GPU.ai | sourced 21 Nov 2026 (WebFetch) | <https://getdeploying.com/gpus/nvidia-rtx-pro-4500> |
| Host share about 80% of the renter price | from r2 (Salad, Vast.ai) | sourced in r2 | r2 file |

## 5. Recommended wording (task d)

**Replace the laptop-efficiency reductio** (plan "The two job types", the "Full cost … laptop-class … a reductio" evidence row, and Q&A answer 1) with this.

Assumptions list, one line:

> **Reference server:** a 2U server with 4 × NVIDIA RTX PRO 4500 Blackwell Server Edition. That is about 0.95 kW at the wall (our estimate from the 165 W GPU and 320 W CPU maxima; not measured). MLPerf v6.1 measured both of our job types on this GPU configuration (ID 6.1-0017): whisper-large-v3 at 61 samples/s and Llama-3.1-8B at 9,519 tokens/s. Per kWh that is about 1,400 audio-hours or 36 million output tokens. Installed in a house: about 34,000 CHF per 1 kW server, or 200,000 CHF for six (Swiss GPU prices, 21 Nov 2026; platform, heat capture and installation are estimates).

Laptop scaling stays as the measured job (must-have 1 needs it). It is no longer the efficiency behind the income line:

> "Our laptop needs 1.3 to 1.5 Wh per audio-hour. The reference server needs about 0.7 Wh (MLPerf throughput, estimated wall power), so a 1 kW server-hour is about 1,400 audio-hours, twice what the laptop rule gives."

The jobs-per-server-hour rule changes from rule (i) (laptop energy) to **MLPerf throughput ÷ estimated wall power**. It moves only job counts and the list value, never heat, coverage, utilisation or the break-even. Keep J1 = 0.5 server-h in the simulation (= about 700 audio-hours per job, computed: 1,411 × 0.5), or keep 333 audio-hours and say "laptop-rule sizing". Either way, no new build scope.

Computing-income tile (replaces the r3 wording; "share needed" first):

> **Needed to pay off:** the operator must receive at least **11% of the list price of the work** for a 5-year payback (7% for 8 years). Electricity after the heat credit alone needs 1.6%. Machine: 4 × RTX PRO 4500 per kW, MLPerf throughput. Prices: Groq/DeepInfra batch, 21 Nov 2026. Assumes every heat-permit hour is filled with paid work, 50/50 transcription/LLM.
> If only 67% of the hours are sold: 16% and 11%. **If the work is LLM generation only: 32% (5 years).**

Pitch, one sentence:

> "On one real server, both our jobs measured by MLPerf, the work a 1 kW server-hour does is listed at about 14 francs, and electricity after the heat credit is 23 centimes. The server costs about 34,000 francs per kilowatt installed, so the operator needs about a tenth of the end-customer price to pay it back in five years, and a third if the work is only LLM generation."

**When the model does not pay off on this machine** (replaces the "fifth to a third, laptop-class" bullet):
- when the operator receives **less than about 11% of the list price** of the work (5-year payback; 7% for 8 years), all permit hours sold, central prices, 50/50 mix (computed);
- **less than 16% / 11% when only 67% of hours are sold** (computed);
- **at the low price (DeepInfra) with 67% sold, below 30% (5 years) / 20% (8 years)** (computed);
- **when the paid work is mostly LLM generation: below about 32% (5 years) / 21% (8 years)** (computed);
- **at r3's scenario (20% of list, 67% sold), at the low price: payback 8.1 years, longer than a 5-year life** (computed);
- **when GPU-hours sell at the cheapest rental rate** (0.41 USD per GPU-hour): payback 7.0 years even with every permit hour rented (computed; data-centre rental price, not a heat-following host);
- and, unchanged, below 0.2261 CHF per sold server-hour on operation alone.

Plainly: **on this machine the model does not pay off at the low price or with LLM-only work. It pays back in 5 years only if at least about a tenth of the transcription-heavy list price reaches the basement**, and nobody has shown that a heat-following host gets that share.

## 6. Weak points of this work

- **Wall power is estimated, not measured.** It only moves the operation share (1.2 to 2.0%) and the 5-year share by ±0.6 points, because hardware per kW and work per kWh scale together.
- **J1 = whisper-large-v3 in MLPerf, priced at large-v3-turbo prices** (r3 central). Turbo is faster on the same GPU (factor not found), so the J1 list value is conservative for turbo work. Priced as large-v3 work (Groq batch 0.0555), the 5-year share falls to 4.3% (computed). Neither is a transacted price.
- **Platform price is an assumption.** The one page read shows conflicting prices (EUR 2,642 to 6,924), unclear contents and VAT. The listed GPU configurations do not include 4 × RTX PRO 4500. No HPE DL345 Gen12 price was found.
- **Heat capture has no price** and is air-to-water: outlet roughly 35 to 45 °C air (`assumption-limits.md`), so the water is colder still (not quantified). Liquid cooling for this card was not found. If DigitalHeat requires 55 to 60 °C water, this machine needs a booster, or a different, liquid-cooled machine with no published price (Comino Grando: quote only, search snippet).
- **House integration is a 2015 heat-pump proxy**, not a quote. A server connection may be simpler than a heat pump (no outdoor unit) or more complex (control integration). Prices are not inflated to 2026.
- **The VAT status of the Swiss GPU prices is not stated on either page.** Inclusion is assumed. If they exclude VAT, the card cost rises 8.1%.
- **Card variant on the Post page is ambiguous** (GDDR6 and GDDR7 both listed). LDLC names the Server Edition explicitly.
- **Unchanged from r3:** operator share and sold share have no source, demand is unlimited, prices are US commodity batch APIs (no Swiss or sovereign price), the 6:1 input-token ratio for J2, and the 50/50 mix.
- **Volume and network** (60,000 audio-hours a day, about 0.9 TB a day at 32 kbit/s) are stated, not costed beyond a 1,200 CHF a year line.
- 200,000 CHF of GPUs per basement raises insurance, theft and the homeowner's consent. None of these is costed.

## 7. Alternative machine, for comparison only (not the reference)

1 × RTX PRO 6000 Blackwell Server Edition (96 GB, "Up to 600W (configurable)", sourced: <https://www.nvidia.com/en-eu/data-center/rtx-pro-6000-blackwell-server-edition.md>) in a platform. Computed by hand (python one-liner, inputs below), throughput = MLPerf 6.1-0019 (4 × RTX PRO 6000 SE: whisper 145.557 samples/s, llama 24,913.5 tok/s, loadgen logs at <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/Cisco/results/X215M8_X580P_RTXPro6000_96GBx4_TRT/>) divided by 4:

| | 4 × RTX PRO 4500 box (reference) | 1 × RTX PRO 6000 box |
|---|---|---|
| Per GPU: whisper samples/s, llama tok/s | 15.3, 2,380 | 36.4, 6,228 (2.4× and 2.6× one RTX PRO 4500 at 3.6× the power) |
| Wall power (assumption) | 0.955 kW | 0.895 kW (600 W × 0.95 + 180 + 100, ÷ 0.95) |
| Audio-h / M tokens per kWh | 1,411 / 35.9 | 897 / 25.1 |
| Central list value per server-h (mix) | 14.25 CHF | 9.21 CHF |
| Hardware per kW | 31,188 CHF | 26,775 CHF (card CHF 13,457 from a MediaMarkt search snippet, **unverified**, + 8,000 platform + 2,500 heat capture) |
| Share needed N = 6: operation / 5 y / 8 y | 1.6% / 10.7% / 7.3% | 2.5% / 14.7% / 10.1% |

The 4 × RTX PRO 4500 box is more efficient per kWh, and on these prices it needs a smaller share. Not pursued further.

## 8. Proposed changes to the plan

1. **Reference server named** (plan line 6, "The two job types", open risk 5): 2U server with 4 × RTX PRO 4500 Blackwell Server Edition, about 0.95 kW (estimate), MLPerf v6.1 6.1-0017 for both J1 and J2. **Delete "J1 (laptop efficiency) and J2 (B200-slice efficiency) are not one machine"**: both job types now come from one machine.
2. **Scaling rule:** keep the laptop measurement as must-have 1's measured job. Base jobs per server-hour and the list value on the reference machine (1,411 audio-h, 35.9 M tokens per server-h). Keep the laptop rule (667 to 755) and the B200 slice (1,988 / 56.07 M) as bracket lines.
3. **Evidence table:** replace the "laptop-class … reductio" row and the "2 × RTX 4090 … coincidence" row with the r4 rows. Installed cost 33,600 CHF per server (202,000 per house at N = 6, 264,000 at N = 8). Share needed 1.6% / 10.7% / 7.3% (operation / 5 y / 8 y; N = 6, central). Cite `python3 analysis/r4_machine.py`.
4. **Computing-income tile and Q&A answer 1:** the section 5 wording. List value per server-hour 7.7 / 14.3 / 38.2 CHF (one machine), replacing 4.3 / 9.4 / 30.7 (two machines).
5. **"When the model does not pay off":** the section 5 bullets, especially "LLM-only work needs about 32%" and "low price at 67% sold needs about 30%".
6. **Open risk 3 (installed cost):** from "no price" to "estimated 34,000 CHF per server, 60% GPUs (sourced Swiss prices), house integration from the BFE heat-pump price study (2015 proxy); heat capture and platform are assumptions; liquid cooling for this card not found". Question 1 for DigitalHeat stays.
7. **`assumption-limits.md` section 2** (whoever may edit it): the reference machine is air-cooled, so the "air-cooled" row applies. A booster for hot water is needed unless DigitalHeat names a liquid-cooled machine.
8. **New question for DigitalHeat:** "Which machine do you install today (GPU, cooling, outlet temperature), and at what installed cost per kW?"
9. **Build scope: none added.** Only the numbers in two tiles and the assumptions list change.

## 9. Commands

```
# MLPerf v6.1 summary (local copy), parsed with a stdlib xlsx reader (scratchpad, not kept)
python3 -I <scratch>/r4mach_xlsx_dump.py data/raw/mlperf_inference_v6.1_summary.xlsx > <scratch>/r4mach_mlperf61.tsv
# loadgen summaries, measurements, systems (curl, raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/...)
#   closed/Cisco/results/X210M8_X580P_RTXPro4500_32GBx4_TRT/{whisper,llama3.1-8b}/Offline/performance/run_1/mlperf_log_summary.txt
#   closed/Cisco/results/X210M8_X580P_RTXPro4500_32GBx4_TRT/{whisper,llama3.1-8b}/Offline/measurements.json
#   closed/Cisco/results/X210M8_X580P_RTXPro4500_32GBx4_TRT/whisper/Offline/accuracy/accuracy.txt
#   closed/Cisco/systems/X210M8_X580P_RTXPro4500_32GBx4_TRT.json
#   closed/HPE/results/HPE_PROLIANT_DL345_GEN12_RTX_PRO_4500_PCIE_32GBx4_TRT/whisper/Offline/performance/run_1/mlperf_log_summary.txt
#   closed/HPE/systems/HPE_PROLIANT_DL345_GEN12_RTX_PRO_4500_PCIE_32GBx4_TRT.json
#   closed/Cisco/results/X215M8_X580P_RTXPro6000_96GBx4_TRT/{whisper,llama3.1-8b}/Offline/... (alternative row)
# BFE heat-pump price study
curl -sL -o <scratch>/r4mach_bfe_8157.pdf https://pubdb.bfe.admin.ch/de/publication/download/8157 && pdftotext -layout ...
# AMD EPYC 9375F and ESTV VAT pages: curl with a browser user agent, tags stripped, grep
# analysis
python3 analysis/r4_machine.py
```

Web pages opened with WebFetch: nvidia.com RTX PRO 4500 SE and RTX PRO 6000 SE (.md), ldlc.com/fr-ch, shop.post.ch, hardwaredealz.com, store.supermicro.com, runpod.io, getdeploying.com. Firecrawl (2 calls): store.supermicro.com (worked; conflicting prices), digitec.ch (captcha, nothing read). Timed out or blocked: digitec.ch and galaxus.de (WebFetch), amd.com (WebFetch; curl worked), mediamarkt.ch (404), shop.post.ch RTX PRO 6000 page (empty).
