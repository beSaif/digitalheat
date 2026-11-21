# Round 6: machine identity behind the realism column

Investigator file for the round-6 weak point: "costed water blocks fit a different card edition; throughput, power and price must come from one liquid-cooled configuration." This round plans and assesses only. No existing file was changed and git state was not touched. Written Sat 21 Nov 2026.

- **Script:** `analysis/r6_machine.py`, new, standard library only. It imports `baseline_sweep.py`, `r4_machine.py` and `r5_chain.py` without editing them and writes no bytecode. It adds four temperature chains to `r5_chain.CHAINS` **at runtime only**; the file on disk is unchanged.
- **Command:** `python3 analysis/r6_machine.py` (exit 0, about 1.5 s). The output is in section 7.
- **Regression:** the script reproduces r5's installed cost exactly (212,574 CHF at N=6), the list value (14.2526 CHF) and the 5-year share (11.24%).
- **Currency:** CHF. 1 EUR = 0.9223 CHF and 1 USD = 0.8392 CHF (ECB, 20 Nov 2026; sourced in round 1, re-confirmed by the r5 critic, taken from `r4_machine.py`). VAT: CH 8.1% (sourced, r4), DE 19% (as r4), AT 20% (*assumption*: standard rate). A GBP price is quoted but not converted.
- **Firecrawl:** 1 of 6 calls used (digitec.ch). It was refused: the account is out of credits. Free WebSearch and WebFetch, plus curl to raw.githubusercontent.com and a vendor PDF, did the rest.

**Status labels:**
- *sourced*: a URL I opened, with the number read on the page.
- *computed*: produced by `python3 analysis/r6_machine.py`.
- *assumption*: our own choice.
- *unverified*: seen only in a search snippet, read off a chart, or an interpretation.

## 1. Answer in brief

1. **No single machine has a sourced price, wall power and both throughputs from one liquid-cooled configuration.** I checked three candidates. Each one is missing at least one leg:

   | Candidate | Liquid-cooled | J1 whisper | J2 llama3.1-8b | Wall power | Price | Usable for house water |
   |---|---|---|---|---|---|---|
   | **A. 4 × RTX PRO 6000 Blackwell Server Edition + cold plates made for that exact edition** (recommended realism machine) | blocks for this card (*sourced*: Alphacool, EK, JetCool) | measured on an **air-cooled** Cisco X215c with the same 4 cards at the same 600 W TGP (6.1-0019) | measured on a **vendor direct-liquid-cooled** box with the same 4 cards (ManyCoreSoft DeepGadget dg5W, 6.1-0102). Within 1.6% of the Cisco box | **estimated**, about 2.7 kW per box (TGP sourced) | cards *sourced* (DE shops, 21 Nov 2026); platform and liquid parts are *assumptions* | yes: the plates take facility water, JetCool rated to 60 °C inlet |
   | B. Lenovo ThinkSystem SR780a V3, 8 × B200, Neptune water-cooled | yes, by the vendor ("Water-cooled", W45) | measured, same system (5.1-0062) | measured, same system, **with measured wall power 9,436 W** | J2 run measured; J1 power only on the air twin | **none found** | yes (45 °C inlet, 12 l/min) but 9.4 kW and about 0.64 boxes per house: not a house machine |
   | C. Plan as of round 5: 4 × RTX PRO 4500 Server Edition + Alphacool blocks | blocks fit the **workstation** card, not the measured one | measured, air (6.1-0017) | measured, air (6.1-0017) | estimated | cards *sourced*, blocks for another edition | only with a different card |

2. **Recommended:** relabel the realism machine as candidate A. Its blocks fit the card that MLPerf measured, and J2 was measured on a liquid-cooled box. Two gaps remain, and the pitch must name both:
   - wall power is estimated, not measured;
   - J1 is borrowed from the air-cooled twin.

   Exact wording is in section 6.
3. **Share of list price needed** (*computed*; central costs and prices; every permit hour sold; simple payback; maintenance, leak reserve and warranty self-insurance included as labelled *assumptions*):

   | | N=6: op / 5 y / 8 y | N=8: op / 5 y / 8 y | LLM-only, 5 y (N=6 / N=8) |
   |---|---|---|---|
   | Plan (C), round 5 as published, without maintenance | 1.7% / 11.2% / 7.7% | 1.7% / 12.3% / 8.3% | — |
   | Plan (C) + maintenance + warranty self-insurance | 1.7% / **11.6%** / 8.0% | 1.7% / **12.7%** / 8.7% | 34.4% / 37.5% |
   | **A: 4 × RTX PRO 6000 SE, cold plates** | 2.0% / **13.1%** / 9.0% | 2.0% / **14.2%** / 9.7% | 36.3% / 39.5% |
   | A as a vendor DLC system (no warranty self-insurance) | 2.0% / 13.0% / 8.9% | 2.0% / 14.1% / 9.6% | — |
   | A, low / high costs | 5 y 12.1% / 17.6% | 5 y 13.2% / 19.2% | — |
   | 1 × RTX PRO 6000 SE box near 1 kW (throughput ÷ 4, *assumption*) | 2.6% / 17.4% / 12.0% | 2.6% / 18.9% / 13.0% | 48.3% / 52.5% |
   | 4 × RTX PRO 4500 **workstation** (the edition the costed blocks fit; throughput *assumed* equal) | 1.9% / 12.0% / 8.4% | 1.9% / 13.1% / 9.0% | — |

   - The consistent machine needs about **1.5 points more** than the published 11.2% (13.1% against 11.6% on like-for-like rules).
   - The reason: the RTX PRO 6000 SE costs about 3.7 times the RTX PRO 4500 (17,621 against 4,819 CHF) for 2.4 to 2.6 times the throughput. Per unit of work its card cost is 1.4 to 1.5 times higher.
   - A one-GPU box "near 1 kW" is worse (17.4%), because the platform cost is spread over one card instead of four.
4. **Does it matter for "Read this first"?**
   - **No change** to coverage, dumped heat, utilisation, missed deadlines, or any break-even (0.2261 / 0.3325 / 0.2293 / 0.2359). All of these are per kW and do not depend on the machine.
   - **No change** to the realism column's coverage. The DLC45 rows are identical on any machine.
   - **Wording changes:**
     - Plan line 5 and the realism footnote ("no block confirmed for the exact card") go.
     - Plan line 9's "about 11–13%" holds. Q&A 1's "about 11–12% over 5 years ... 7.7% over 8" becomes "about 12–14% over 5 years, 8–10% over 8, on a liquid-cooled configuration incl. maintenance". 11.6% is the RTX PRO 4500 basis, 14.2% the RTX PRO 6000 at N=8.
     - If the team switches the throughput reference to the RTX PRO 6000 (not recommended: churn, section 5), the scaling line also changes: 1,191 instead of about 1,400 audio-hours per kWh, factor about 1.7 instead of about 2.
5. **Outlet temperature (realism column, *computed*, `r5_chain.sim` with tank loss 2.80):**
   - **Coolant inlet ≤ 40 °C:** floor heating 76.5% / 89.3%, summer 71.1%. 55/45 radiators fall to 32.8% / 34.6%.
   - **≤ 45 °C (plan):** unchanged, 77.6% / 90.6%, summer 82.2%, 55/45 at least 64.3% / 73.0%.
   - **≤ 50 °C** with a 55 °C house-side top (new DLC50T): 78.7% / 92.0%, summer 93.3%. 55/45 radiators reach 78.5% / 91.8%, and 70/55 at least 51.3% / 56.2%.
     - A 50 °C inlet sits within JetCool's sourced 18–60 °C plate rating.
     - With the Alphacool or EK blocks it leaves zero margin to their 60 °C maximum.
     - The GPU itself may need power capping (section 4, *unverified*).
   - **≤ 55 °C** with a 60 °C top: 79.3% / 92.8%, summer 100%. The outlet would be about 65 °C, above every block rating found, so this is a sensitivity only.
6. **Warranty, leaks, maintenance:**
   - PNY gives professional cards **3 years**, "when used normally" (*sourced*). I found no published clause on cooler removal (*unverified* absence), so treat the card warranty as at risk with a retrofit.
   - Self-insuring card failures in years 1–3 at the NVIDIA MTBF (1,864,500 h, *sourced*; 0.47% a year, *computed*) costs about 1,700 / 2,200 CHF per house (C / A, N=6).
   - Maintenance, spares and leak reserve come to about 900–1,400 CHF per house-year (*assumption*, anchored on sourced service times).
   - Together they add **about 0.4 points** to the 5-year share.
   - A vendor-integrated DLC box removes the warranty question. DeepGadget gives 3 years (*sourced*), but the dg5W rejects its heat to room air, so it does not make house water.
7. **Build scope: none added.** The scheduler is unaffected. Only text and the cost lines change, and the script already prints them.

## 2. Sources (opened by me, 21 Nov 2026, unless marked)

| # | Fact | Value read | Status, URL |
|---|---|---|---|
| S1 | MLPerf v6.1 summary (local copy), all RTX PRO rows | 6.1-0102 "ManyCoreSoft DeepGadget dg5W (4x NVIDIA RTX PRO 6000 Blackwell 96GB, TensorRT)", accelerator "NVIDIA RTX PRO 6000 Blackwell Server Edition", **llama3.1-8b only** (Offline 24,511.8, Server 24,510.5 tok/s), notes "(TGP 600W each); direct liquid cooling (DLC)". 6.1-0019 Cisco X215c 4 × RTX PRO 6000 SE "TGP 600W": llama3.1-8b Offline 24,913.5, whisper present | *sourced*: `data/raw/mlperf_inference_v6.1_summary.xlsx` (copy of <https://github.com/mlcommons/inference_results_v6.1>), parsed with a stdlib reader in my scratchpad |
| S2 | DeepGadget dg5W system description | `"cooling": "Direct Liquid Cooling"`, AMD EPYC 9124 (16 cores), 512 GB, `"power_supply_quantity_and_rating_watts": ""` (empty) | *sourced*: <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/TTA/systems/DeepGadget_dg5W_RTXPro6000_96GBx4_TRT.json> (curl) |
| S3 | dg5W llama3.1-8b loadgen summary | "Samples per second: 191.499", "Tokens per second: 24511.8", "Result is : VALID"; weights fp4. The results folder holds only `llama3.1-8b` (GitHub API listing) | *sourced*: `.../closed/TTA/results/DeepGadget_dg5W_RTXPro6000_96GBx4_TRT/llama3.1-8b/Offline/performance/run_1/mlperf_log_summary.txt` and `measurements.json` (curl) |
| S4 | Cisco X215c 4 × RTX PRO 6000 SE whisper | "Samples per second: 145.557", "Tokens per second: 9236.94", VALID; system JSON `"cooling": "Air-cooled"`, EPYC 9845, 1.5 TB, hw_notes "TGP 600W" | *sourced*: `.../closed/Cisco/results/X215M8_X580P_RTXPro6000_96GBx4_TRT/whisper/Offline/performance/run_1/mlperf_log_summary.txt`, `.../closed/Cisco/systems/X215M8_X580P_RTXPro6000_96GBx4_TRT.json` (curl) |
| S5 | dg5W press article (Korean) | 6.1-0102; Offline "초당 2만4511.8토큰"; versus the Cisco 4-GPU server Offline "1.61% 낮다"; "dg5W의 전력 수치는 이번 공식 결과에 포함되지 않았다" (no power in the official result); comparison servers "모두 공랭식" (all air-cooled); dated 2026-09-23 | *sourced*: <https://www.specialtimes.co.kr/news/articleView.html?idxno=466559> (WebFetch) |
| S6 | DeepGadget dg5R / dg5W launch post | dg5W: up to 6 water-cooled GPUs (RTX PRO 6000 SE among them); PSU "1,300W 플래티넘 x4 또는 3,200W 티타늄 x4, N+1"; "Self-Contained 방식이라 별도 공조 설비가 필요 없다" (cooling ends inside the server); full-load GPU peak "54~67℃"; noise 20–53 dB; "보증은 3년" (3-year warranty); price "GPU 구성에 따라 달라진다" (no price); the dg5R powers down on a detected leak; 1 Jun 2026 | *sourced*: <https://www.deepgadget.com/blog/dg5r-dg5w-liquid-cooling-ai-server-launch/> (WebFetch) |
| S7 | NVIDIA RTX PRO 6000 Blackwell Server Edition product brief SP-12355-001_v02 (June 2025) | "capable of 600 W maximum board power"; total board power 600 W max (default), **300 W minimum** (programmable); thermal solution "Passive"; thermal qualification "TAVG < 80 °C"; "The partner thermal solution should be designed and validated…"; **MTBF "Uncontrolled environment: 1 864,500 hours at 35 °C"** | *sourced*: <https://www.pny.com/en-eu/file%20library/professional/rtx-pro-6000-server-product-brief.pdf> (WebFetch saved the PDF; pdftotext) |
| S8 | NVIDIA RTX PRO 6000 SE page | "Up to 600W (configurable)"; "Air: Dual-Slot, FHFL"; "Liquid: Single-Slot, FHXL"; no liquid partner named | *sourced*: <https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/> (WebFetch; also opened by the r5 critic) |
| S9 | JetCool SmartPlate cold plate for RTX PRO 6000 Server Edition (a Flex company) | "Engineered for 600W TDP … warm inlets up to 60°C"; "Fluid Inlet Temp. 18ºC to 60ºC"; "Design Fluid Flow Rate 0.9 LPM"; operating pressure 72 psi, burst 216 psi; thermal-resistance chart (junction to fluid, PG25, 40 °C inlet) with an axis of 0.040–0.058 °C/W over 0.6–1.8 LPM (curve value not readable from the text: *unverified*); no price | *sourced*: <https://info.jetcool.com/hubfs/Marketing%20Resources%202026/NVIDIA%20RTX%20PRO%206000%20SmartPlate%20Cold%20Plate%20Datasheet.pdf> (curl + pdftotext) |
| S10 | RTX PRO 6000 SE price, DE shops | PNY RTX PRO 6000 Blackwell Server Edition, "Passivkühlung": electronis.de 20,322.99 €, HEINZSOFT 20,323.00 €, Mindfactory 21,740.79 €, JB-Computer 21,740.84 €; "Preise inkl. MwSt."; timestamp 21.11.2026 10:20 | *sourced*: <https://www.hardwaredealz.com/hardware/gpu/nvidia-rtx-pro-6000-blackwell-96gb/pny-rtx-pro-6000-blackwell-server-edition/preisvergleich.72743> (WebFetch) |
| S11 | RTX PRO 6000 SE price, AT shops | NVIDIA-branded listing: DiTech.at and e-tec.at 21,999.00 € each; PNY listing: both 29,169.00 €; incl. VAT; 21.11.2026 10:20 | *sourced*: <https://www.hardwaredealz.com/hardware/gpu/nvidia-rtx-pro-6000-blackwell-server-edition/preisvergleich.67250>, <https://www.hardwaredealz.com/hardware/gpu/nvidia-rtx-pro-6000-blackwell-96gb/pny-rtx-pro-6000-blackwell-server-edition/preisvergleich.67884> (WebFetch) |
| S12 | Lenovo SR780a V3 MLPerf v5.1 (5.1-0062) | system JSON `"cooling": "Water-cooled"`, "B200 TGP 1000W"; llama3.1-8b Offline "Tokens per second: 146960", VALID; whisper Offline "Samples per second: 699.136"; summary JSON `Power_Result` 9,436.05 W (llama Offline), none for whisper. Air twin SR680a V3 (5.1-0061) whisper power 7,636.49 W | *sourced*: <https://raw.githubusercontent.com/mlcommons/inference_results_v5.1/main/closed/Lenovo/systems/SR780a_V3_B200SXMx8_TRT.json>, `.../results/SR780a_V3_B200SXMx8_TRT/{llama3.1-8b,whisper}/Offline/performance/run_1/mlperf_log_summary.txt`, <https://raw.githubusercontent.com/mlcommons/inference_results_v5.1/main/summary_results.json> (curl) |
| S13 | Lenovo SR780a V3 environmental specification | "ASHRAE class W45: up to 45°C (113°F) inlet temperature to the rack"; B200: "Minimum water flow rate … at 45°C … 12.0 liters per minute per Chassis"; "Maximum pressure: 4.4 bars" | *sourced*: <https://pubs.lenovo.com/sr780a-v3/server_specifications_environmental> (WebFetch) |
| S14 | PNY EMEA warranty | "Professional Graphic Cards : 3 years"; "free from defects in material and manufacture, when used normally"; no clause on modification or cooler removal on the page | *sourced*: <https://www.pny.com/en-eu/legal/warranty-emea> (WebFetch) |
| S15 | Custom-loop maintenance (enthusiast retailer) | "Change your coolant at least once a year"; quick service "every 6-12 months", 30–60 minutes; full teardown "Annually", 2–4 hours; leak test "12-24 hours before powering on" after full maintenance; check fittings "for tightness, corrosion, or signs of weeping" | *sourced*: <https://www.watercoolinguk.co.uk/how-often-should-you-maintain-your-watercooling-loop/> (WebFetch, second half of the page) |
| S16 | Puget Systems part | "NVIDIA RTX PRO 6000 Blackwell Server Edition with Comino Liquid Cooling" (GPU008-KIT01); the Comino block "is designed for the Comino Grando server" and the card "cannot be used in any other type of system"; no price, wattage or warranty on the page | *sourced*: <https://www.pugetsystems.com/parts/Accelerators/NVIDIA-RTX-PRO-6000-Blackwell-Server-Edition-with-Comino-Liquid-Cooling-16860/> (WebFetch) |
| S17 | ThermAI (UK) home-heating node | "six-GPU ThermAI Node" with "NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs"; built by "2CRSi"; spray cooling with a non-conductive fluid "inside a sealed cassette"; "Outlet water temperatures can reach up to 60C"; Sunamp heat batteries; pilots "to lead to 100 homes in 2027"; households get heat "free of charge"; no node power, price or throughput; 18 Nov 2026 | *sourced*: <https://itbrief.co.uk/story/thermai-turns-gpu-server-waste-heat-into-home-heating> (WebFetch). The DCD article returned 403 |
| S18 | Renda Nova8 | 8 × RTX PRO 6000 at "full 600W", jet-impingement DLC; no price, system power or water temperature; 18 Nov 2026 | *sourced*: <https://aecmag.com/workstations/renda-and-nexalus-launch-liquid-cooled-ai-server/> (WebFetch) |

Reused without re-searching (round 5, confirmed by its critic):
- Alphacool ES RTX 6000 Pro **Server Edition** block: €399.98 incl. VAT; maximum 60 °C; recommended 20 °C; maximum test pressure 4 bar (<https://shop.alphacool.com/en/detail/index/sArticle/22570>).
- EK-Pro RTX PRO 6000 SE block: £412.99 incl. VAT; maximum coolant 60 °C; corrosion-inhibiting coolant mandatory (<https://www.scan.co.uk/products/ek-pro-gpu-wb-rtx-pro-6000-se-water-block-rtx-pro-6000-server-ed-stainless-steel-top-nickel-plated-c>).
- RTX PRO 4500 workstation: 200 W, dual slot, active (<https://www.nvidia.com/en-eu/products/workstations/professional-desktop-gpus/rtx-pro-4500.md>).
- All r4 machine, price and VAT inputs.

Not found or not usable (*unverified*):
- **Any price for a vendor liquid-cooled RTX PRO 6000 SE system** (DeepGadget, Comino/Puget, Renda, ThermAI, NVIDIA MGX 6U liquid version). Searches returned none, and DeepGadget says the price "varies with GPU configuration".
- **Any wall-power measurement of an RTX PRO 6000 or RTX PRO 4500 box.** MLPerf v6.0 and v6.1 contain no power rows (`has_power` false for all 520 v6.0 rows; v6.1 summary JSON returned 404). In v5.1 only the 8 × B200 Lenovo systems have power for whisper or llama3.1-8b.
- **A Swiss price for the RTX PRO 6000 SE.** digitec.ch and galaxus returned 403 to curl and timed out in WebFetch; the Firecrawl call was refused for lack of credits.
- **A price for the SR780a V3.** A search snippet shows Newegg at 320,169.50 USD for model 7DJ51000NA with an unknown configuration; I did not open it (403).
- PNY's policy on cooler removal for professional cards: no clause found. Forum posts only.
- JetCool plate price; ThermAI node power and price; Comino Grando coolant temperatures. The Grando review gives a 6.5 kW cooling capacity at "20°C intake air", so it rejects heat to air.

## 3. Why candidate A, and what is still inconsistent

**What A fixes compared with the round-5 plan:**
- The cold plates are made for the same card edition that MLPerf measured. There are three of them: Alphacool ES and EK-Pro are named for the "RTX PRO 6000 Blackwell Server Edition", and JetCool for the "RTX PRO 6000 Server Edition".
- NVIDIA itself lists a liquid single-slot variant (S8).
- One of the two throughput figures (J2) was measured on a box whose GPUs are on direct liquid cooling (S2, S3). This shows that DLC on this card does not throttle llama3.1-8b at 600 W TGP: 98.4% of the air-cooled Cisco result (*computed*).

**What remains:**
1. **J1 is borrowed.** The DLC box submitted llama3.1-8b only. Whisper comes from the Cisco X215c (air-cooled, same four cards, same TGP).
   - Bridge: the two boxes agree within 1.6% on llama3.1-8b.
   - The host CPUs differ: a 16-core EPYC 9124 against a dual-socket server CPU, with 512 GB against 1.5 TB of RAM. Whisper preprocessing may load the CPU more than llama does (*unverified*).
2. **Wall power is estimated.** (4 × 600 W × 0.95 + 180 + 100) ÷ 0.95 = 2.69 kW, range 2.29–3.09 kW (r4 power model, *assumption*). The DeepGadget PSUs (4 × 1,300 W N+1, so 3,900 W usable) bracket it from above.
   - The share needed hardly depends on this: hardware per kW and work per kWh scale together (r4).
   - The list value per server-hour moves with 1/P.
3. **Price legs are not one quote.** The cards come from German shops on 21 Nov 2026 (*sourced*). Platform (8,000 CHF), manifold, CPU plate, assembly, CDU and house items are r4/r5 *assumptions*.
   - A 4 × 600 W box needs about 2.7 kW of PSU and probably a larger chassis than r4's 2U assumption, so 8,000 CHF is likely low (*unverified*).
4. **Box granularity.** 6 kW ÷ 2.69 kW = 2.23 boxes. A real house gets 2 boxes (5.4 kW) or 3 (8.1 kW).
   - The r4/r5 normalisation (1 server = 1 kW = 1/P boxes) hides this, as it already did for the 4500 box (6.28 boxes).
   - Alternative: cap each card at 300–450 W (sourced range, S7). The throughput at reduced TGP is unmeasured.

**Why not B (Lenovo SR780a V3):**
- It is the only fully measured liquid-cooled configuration: J1 and J2 on the same water-cooled system, J2 with measured wall power, a vendor-stated 45 °C inlet and 12 l/min. At 85% capture (*assumption*) that gives about **9.6 K rise, so 45 → 55 °C** (*computed*), which supports the plan's 45/55 assumption with a vendor flow figure.
- But it is a 9.4 kW, 8 × B200 machine with no public price: 0.64 boxes at N=6.
- It would need the same 5-year share as A only if one unit cost at most about 564,000 CHF incl. VAT (*computed* threshold, N=6).
- Keep it as the "B200 slice" bracket line, now labelled "water-cooled, measured power". Do not use it as the house machine.

**Why not keep C:** the costed blocks fit the 200 W workstation RTX PRO 4500. Re-based on that card (R5WS), the box draws about 1.09 kW and its throughput is unmeasured. The share needed would be 12.0% only if the workstation card matched the server card's throughput (*assumption*).

**Why not a GPU heater product:**
- ThermAI (UK, S17) is the closest real product: six RTX PRO 6000 SE, outlet water up to 60 °C, homes. It publishes no power, price or throughput.
- It is also **prior art** for the creativity Q&A: a GPU node heating homes, announced 18 Nov 2026, the same GPU, 60 °C water. The plan's novelty claim (refusal at intake against the forecast heat and tank) is unaffected, but "we did not find" must not cover "GPU servers heating homes with water".

## 4. Temperatures, warranty, leaks, maintenance

**GPU and plate limits:**
- The block ratings stay 60 °C maximum (Alphacool, EK). JetCool rates fluid **inlet** up to 60 °C at 0.9 l/min design flow (S9).
- At 600 W and 0.9 l/min, the coolant rise is 600 ÷ (0.015 kg/s × 4,186) = **9.6 K** (*computed* by hand; about 10 K with PG25). That matches the plan's 10 K.
- NVIDIA qualifies the card at TAVG < 80 °C (S7).
- The JetCool junction-to-fluid resistance axis spans 0.040–0.058 °C/W. At 600 W that puts the GPU about 24–35 K above the fluid (*unverified*: curve value not readable, and junction is not TAVG). At 45 °C inlet that is roughly 69–80 °C, at 50 °C roughly 74–85 °C.
- So **50 °C inlet at full 600 W may need a power cap** (programmable down to 300 W, S7). The DLC50T rows are a sensitivity, not the plan.
- DeepGadget reports a full-load GPU peak of 54–67 °C in its self-contained loop (S6). No coolant temperature is given.

**Warranty implications of a retrofit:**
- PNY: 3 years for professional cards, "when used normally" (S14). No clause on cooler removal found. The NVIDIA brief leaves the thermal solution to the "partner", validated against TAVG < 80 °C.
- Treat the card warranty as **lost** with a third-party block. The server-platform warranty is also likely affected (*unverified*).
- Cost as self-insurance: annual failure rate = 8,760 ÷ 1,864,500 = **0.47% per card-year** (*computed* from S7; applied to the RTX PRO 4500 too, *assumption*). Over the 3 warranty years:
  - 1,707 CHF per house (C, N=6);
  - 2,212 CHF (A, N=6);
  - 2,949 CHF (A, N=8).
- This is small because the MTBF is high. A worse real failure rate (round 5 derived about 0.5 repairs per 4-GPU server-year from Llama 3 training, order of magnitude only) would raise it about tenfold, to about 0.5–1 point of share (*unverified*).
- A vendor-integrated DLC system avoids the question:
  - DeepGadget offers 3 years (S6), but its loop is self-contained and rejects heat to room air.
  - The Puget/Comino liquid card is tied to the Comino Grando chassis, which also rejects heat to air (6.5 kW at 20 °C intake air, review snippet, *unverified*).
  - **No vendor warm-water version with a warranty and a price was found.**

**Leak-risk mitigation (no build scope; assumptions list and Q&A only):**
- The CDU plate exchanger keeps the server loop separate from the house heating water (already in the chain).
- Inhibited coolant is mandatory (EK, sourced r5).
- Pressure-test before commissioning: 4 bar maximum test pressure for Alphacool (sourced r5); JetCool runs 72 psi continuous and withstands 216 psi burst (S9). Leak-test 12–24 h after any full service (S15).
- Use dripless quick disconnects and a drip tray under each box (*assumption*).
- Fit a leak sensor per box that **cuts power on detection**: DeepGadget does this on the dg5R (S6).
- For the scheduler, a leak shutdown is a server failure. The `r5_miss_stress.py` failure stress already covers 1 failure per server-year with 0 missed jobs. **Nothing to build.**

**Annual maintenance (*assumption*, anchored on S15):**
- Per house: 4 technician-hours at 120 CHF, plus 150 CHF of coolant, plus 2% of the liquid-cooling hardware a year in spares (pumps, QDs, O-rings), plus a 50 CHF per box-year leak reserve.
- That gives **1,350 CHF** (C, N=6), **924 CHF** (A, N=6), 1,570 / 1,002 at N=8.
- A has fewer boxes, so fewer loops and less hardware.
- The enthusiast guidance (coolant at least yearly, 30–60 min quick service, 2–4 h annual teardown) is for desktop loops. A sealed server loop with PG25 may need less (*unverified*).

## 5. What changes in the plan (no build scope added)

1. **Realism machine label:**
   - Old: "this GPU class with water cold plates (no block confirmed for the exact card)".
   - New: "4 × RTX PRO 6000 Blackwell Server Edition with cold plates made for that card (Alphacool / EK / JetCool); LLM throughput measured on a vendor direct-liquid-cooled box (MLPerf v6.1-0102), transcription on the air-cooled twin (6.1-0019, LLM within 1.6%); wall power estimated (~2.7 kW per box)".
2. **Keep the RTX PRO 4500 as the throughput and price reference** for lines 5–6, the job table and Key numbers.
   - Switching would change J1's size (0.5 server-h is about 700 audio-hours at 1,411 per kWh; it would be about 600 at 1,191), the list value (14.25 → 12.19 CHF per server-hour), the scaling factor (about 2 → about 1.7) and the r4/r5 income rows. Only text changes, but many numbers move one day before the pitch.
   - Instead, show the liquid-cooled configuration as the **upper end of the share range**.
   - If the critic insists on one machine everywhere, switch to A and accept the churn. The scheduler does not depend on it.
3. **Installed cost and share needed (table "Reference server and installed cost"):** add a row "liquid-cooled configuration (4 × RTX PRO 6000 SE + cold plates), incl. maintenance and warranty self-insurance".
   - Installed about 205,000 / 265,000 CHF (N=6 / N=8).
   - Share needed: 5 years 13.1% / 14.2%; 8 years 9.0% / 9.7%; operation 2.0%; LLM-only 36–40%.
   - Add "maintenance + warranty self-insurance add about 0.4 points" to the C row: 11.6% / 12.7%.
4. **Open risk 3:** replace "retrofit warranty … leak risk and coolant maintenance not costed" with:
   - "costed as assumptions: about 900–1,400 CHF per house-year maintenance and leak reserve;
   - about 1,700–2,900 CHF self-insured card failures in years 1–3 (NVIDIA MTBF);
   - +0.4 points".
5. **Open risk 5:** replace the round-5 sentence with:
   - "Realism machine: 4 × RTX PRO 6000 SE with cold plates for that card. J2 measured with DLC, J1 borrowed from the air-cooled twin, wall power estimated, platform price assumed. No vendor warm-water system with a published price was found.
   - Lenovo SR780a V3 (8 × B200, W45) is fully measured (J1, J2, wall power on J2) but has no price and is 9.4 kW."
6. **Realism footnote:** change "blocks rated 60 °C (GPU limit unpublished; no block confirmed for the exact card)" to:
   - "plates for this card rated 60 °C (Alphacool, EK) or 18–60 °C inlet (JetCool);
   - GPU qualified at TAVG < 80 °C;
   - a 50 °C inlet may need a power cap".
   - Optional sensitivity line: "at 50 °C inlet with a 55 °C top: 78.7% / 92.0%, summer 93.3%, 55/45 radiators 78.5%" (`r6_machine.py` section 3).
7. **Q&A 1 wording:** "about 12–14% over 5 years, 8–10% over 8, on a liquid-cooled configuration incl. maintenance (11.6% on the cheaper RTX PRO 4500 basis)."
8. **Q&A 6 (prior art):** add ThermAI (UK, Nov 2026): six RTX PRO 6000 SE per node, water up to 60 °C, homes, pilots towards 100 homes in 2027.
9. **B200 slice bracket line:** label it "Lenovo SR780a V3, water-cooled (W45, 12 l/min), measured wall power".
10. **DigitalHeat question 1:** add "do you buy a vendor liquid-cooled system or retrofit plates, and who carries the GPU warranty?"

## 6. Exact pitch wording (no single consistent configuration)

> "Our reference compute is a GPU server with water cold plates: four NVIDIA RTX PRO 6000 Server Edition cards, with cold plates made for that card. MLPerf measured the LLM job on a direct-liquid-cooled box with these four cards, and transcription on the air-cooled version of the same four cards. Wall power is our estimate, about 2.7 kW per box. Card prices are from German shops today; platform, plumbing and installation are our assumptions. Price, power and throughput are not from one quote, and we say so."

Footnote, one line: "Fully measured liquid-cooled reference: Lenovo SR780a V3 (8 × B200, 45 °C water in, about 55 °C out): throughput and wall power measured, no public price. Share needed 11.6–13.1% (5 y, N=6, incl. maintenance); coverage and break-even do not depend on the machine. `python3 analysis/r6_machine.py`."

If the team keeps the RTX PRO 4500 everywhere instead, the minimum honest wording is: "GPU-class server; throughput from MLPerf system 6.1-0017 (air-cooled), power estimated from component maxima, price from Swiss and German shops; the liquid-cooled version would use a different card edition; consistency not verified."

## 7. Script output

Command: `python3 analysis/r6_machine.py` (exit 0)

```
r6_machine.py  (CHF; 1 USD = 0.8392 CHF, 1 EUR = 0.9223 CHF, ECB 20 Nov 2026; CH VAT 8.1%, DE 19%, AT 20%)
LIST VALUE = public batch prices for the work, NOT operator income. Shares: every permit hour sold, simple payback.

== 0. Regression: R5 machine on this script's rules vs r5_chain section 4 ==
  r5_chain installed N=6 212,574 CHF | r6 212,574 CHF -> OK
  r5 list value 14.2526 | r6 14.2526; 5-y share r6 11.24% (plan: 11.2%)

== 1. Machines: wall power (r4 power model, ASSUMPTION on SOURCED TGP), work per kWh, list value ==
  machine    P low/cen/high kW audio-h/kWh M tok/kWh list CHF/srv-h  note
  R5        0.75/0.95/1.22         1,411     35.89          14.25  4x RTX PRO 4500 SE (MLPerf 6.1-0017, air) + blocks for another edition
  R5WS      0.88/1.09/1.37         1,231     31.30          12.43  4x RTX PRO 4500 workstation 200 W + its blocks; throughput ASSUMED = server card
  PRO6K4    2.29/2.69/3.09         1,191     32.75          12.19  4x RTX PRO 6000 SE DLC: J2 DeepGadget dg5W DLC 6.1-0102, J1 Cisco X215c 6.1-0019
  PRO6K1    0.70/0.89/1.15           897     24.66           9.18  1x RTX PRO 6000 SE: 4-GPU results / 4 (ASSUMPTION)
  J1 borrow check: DLC dg5W llama 24,511.8 vs air Cisco X215c 24,913.5 tok/s -> ratio 0.9839
  B200LC  measured 9.44 kW (J2 run)       2,019     56.07          20.71  SR780a V3 water-cooled; J1 power from the air twin SR680a (5.1-0061)
  B200LC water rise at 12.0 l/min, 85% capture (ASSUMPTION): 9.6 K -> 45 C in, ~55 C out
  card prices CHF incl. CH VAT: RTX PRO 6000 SE low 17,027 / central 17,621 / high 24,235 (AT max); RTX PRO 4500 central 4,819
  CHF of card per (audio-h per h): PRO 6000 22.0, PRO 4500 14.3; per (k tok/s): PRO 6000 2,876, PRO 4500 2,025

== 2. Installed cost and share of list price needed, N = 6 and N = 8 (central costs and prices) ==
  op = BEchg of the r5 DLC chain (machine-independent per kWh); maint = service + coolant + spares + leak reserve;
  warranty = self-insured card failures in years 1-3 if the retrofit voids the card warranty (AFR from MTBF)

  N=6: 31,236 server-h/yr, BEchg 0.2409 CHF/server-h
  machine  boxes   box CHF  house CHF  liquid maint/yr  warr.    op     5y   5y+m     8y   8y+m 5y+m LLM
  R5        6.28    30,026    212,574  20,285    1,350  1,707  1.7%  11.2%  11.6%   7.7%   8.0%    34.4%
  R5WS      5.48    30,026    188,442  18,075    1,266  1,489  1.9%  11.6%  12.0%   8.0%   8.4%    35.6%
  PRO6K4    2.23    81,234    204,747   9,124      924  2,212  2.0%  12.7%  13.1%   8.7%   9.0%    36.3%
  PRO6K1    6.71    26,906    204,303  11,618    1,198  1,666  2.6%  16.9%  17.4%  11.5%  12.0%    48.3%
  PRO6K4 as vendor DLC (no warranty self-insurance): 5y+m 13.0%, 8y+m 8.9%
  PRO6K4 cost low    :   186,012 CHF, 5y+m 12.1%
  PRO6K4 cost high   :   289,325 CHF, 5y+m 17.6%
  PRO6K4 price low   : 5y+m 24.4%
  PRO6K4 price high  : 5y+m 4.8%
  B200LC: 0.64 boxes per house; it matches PRO6K4's 5y+m share only if one SR780a V3 costs <= 563,818 CHF incl. VAT (no public price found)

  N=8: 36,495 server-h/yr, BEchg 0.2403 CHF/server-h
  machine  boxes   box CHF  house CHF  liquid maint/yr  warr.    op     5y   5y+m     8y   8y+m 5y+m LLM
  R5        8.38    30,026    275,474  26,047    1,570  2,277  1.7%  12.3%  12.7%   8.3%   8.7%    37.5%
  R5WS      7.31    30,026    243,298  23,099    1,457  1,985  1.9%  12.7%  13.1%   8.6%   9.0%    38.6%
  PRO6K4    2.97    81,234    265,038  11,165    1,002  2,949  2.0%  13.9%  14.2%   9.4%   9.7%    39.5%
  PRO6K1    8.94    26,906    264,446  14,490    1,367  2,221  2.6%  18.4%  18.9%  12.5%  13.0%    52.5%
  PRO6K4 as vendor DLC (no warranty self-insurance): 5y+m 14.1%, 8y+m 9.6%
  PRO6K4 cost low    :   241,928 CHF, 5y+m 13.2%
  PRO6K4 cost high   :   373,028 CHF, 5y+m 19.2%
  PRO6K4 price low   : 5y+m 26.5%
  PRO6K4 price high  : 5y+m 5.3%
  B200LC: 0.85 boxes per house; it matches PRO6K4's 5y+m share only if one SR780a V3 costs <= 550,991 CHF incl. VAT (no public price found)

== 3. Realism column if the outlet temperature differs (r5_chain.sim, tank loss 2.80, N=6 / N=8) ==
  inlet limit -> house top / return limit: 40 C -> 45/35; 45 C -> 50/40 (plan); 50 C -> 55/45 (DLC50T; r5's DLC50 keeps a 50 C top); 55 C -> 60/50 (outlet ~65 C, above the 60 C block ratings: JetCool-class plates only)
  chain  house              cov N=6 cov N=8 Jun-Aug  util6 stop h  BEcase   BEchg
  DLC40  underfloor 35/28     76.5%   89.3%   71.1%  58.6%      0  0.2360  0.2442
  DLC40  radiator 50/40       54.9%   60.8%   71.1%  42.6%   1394  0.2373  0.2486
  DLC40  radiator 55/45       32.8%   34.6%   71.1%  26.2%   2864  0.2402  0.2585
  DLC40  radiator 70/55       12.3%   13.1%   71.1%  10.8%   4355  0.2490  0.2936
  DLC45  underfloor 35/28     77.6%   90.6%   82.2%  59.4%      0  0.2359  0.2409
  DLC45  radiator 50/40       77.5%   90.5%   82.2%  59.3%      0  0.2360  0.2410
  DLC45  radiator 55/45       64.3%   73.0%   82.2%  49.6%    853  0.2366  0.2426
  DLC45  radiator 70/55       29.0%   30.8%   82.2%  23.3%   3188  0.2410  0.2537
  DLC50  underfloor 35/28     77.6%   90.6%   82.2%  59.4%      0  0.2359  0.2409
  DLC50  radiator 50/40       77.5%   90.5%   82.2%  59.3%      0  0.2360  0.2410
  DLC50  radiator 55/45       77.4%   90.4%   82.2%  59.3%      0  0.2360  0.2410
  DLC50  radiator 70/55       49.5%   51.8%   82.2%  38.8%   1762  0.2382  0.2458
  DLC50T underfloor 35/28     78.7%   92.0%   93.3%  60.2%      0  0.2359  0.2377
  DLC50T radiator 50/40       78.5%   91.9%   93.3%  60.1%      0  0.2359  0.2378
  DLC50T radiator 55/45       78.5%   91.8%   93.3%  60.1%      0  0.2359  0.2378
  DLC50T radiator 70/55       51.3%   56.2%   93.3%  39.9%   1762  0.2376  0.2403
  DLC55  underfloor 35/28     79.3%   92.8%  100.0%  60.7%      0  0.2358  0.2358
  DLC55  radiator 50/40       79.2%   92.7%  100.0%  60.6%      0  0.2359  0.2359
  DLC55  radiator 55/45       79.2%   92.6%  100.0%  60.6%      0  0.2359  0.2359
  DLC55  radiator 70/55       72.1%   83.3%  100.0%  55.4%    452  0.2362  0.2362
  case column (baseline_sweep): 79.6% / 92.9%
```

**Method notes and caveats:**
- **Operation cost** is r5's `BEchg` on the DLC chain (pumps and hot-water element charged). It is the same per kWh for every machine.
- **Shares** are (operation + installed ÷ (years × server-h) + maintenance per year ÷ server-h + warranty total ÷ (years × server-h)) ÷ list value per server-h, with every permit hour sold. The "LLM" column uses the J2 list value only.
- **R5WS** uses the server-edition card price (4,819 CHF) because no workstation-card price was read, and assumes the server card's throughput. Both are *assumptions*.
- **High card price** uses the highest AT offer (29,169 €, PNY listing) at an assumed 20% AT VAT. The low and central prices come from the 4 German offers.
- **B200LC J1 per kWh** uses the air twin's whisper power (7,636 W). Its llama figure (56.07 M tokens/kWh) equals the r3 "B200 slice".
- **The DLC50T and DLC55 chains** keep r5's 10 K server rise and 5 K CDU approach. The return limit is the inlet limit minus 5 K, and the house-side top is the inlet + 10 − 5. The hot-water direct share follows `r5_chain.dhw_direct_share`: 93.3% at a 55 °C top, 100% at 60 °C.

## 8. Commands

```
# MLPerf v6.1 local summary, real column positions (scratchpad, not kept)
python3 -I <scratch>/r6machid/r6machid_xlsx2.py data/raw/mlperf_inference_v6.1_summary.xlsx > <scratch>/r6machid/r6machid_dc.txt
# MLPerf system JSON and loadgen summaries (curl, raw.githubusercontent.com/mlcommons/...)
#   inference_results_v6.1/main/closed/TTA/systems/DeepGadget_dg5W_RTXPro6000_96GBx4_TRT.json
#   inference_results_v6.1/main/closed/TTA/results/DeepGadget_dg5W_RTXPro6000_96GBx4_TRT/llama3.1-8b/Offline/{performance/run_1/mlperf_log_summary.txt,measurements.json}
#   api.github.com/repos/mlcommons/inference_results_v6.1/contents/closed/TTA/results/DeepGadget_dg5W_RTXPro6000_96GBx4_TRT
#   inference_results_v6.1/main/closed/Cisco/results/X215M8_X580P_RTXPro6000_96GBx4_TRT/whisper/Offline/performance/run_1/mlperf_log_summary.txt
#   inference_results_v6.1/main/closed/Cisco/systems/X215M8_X580P_RTXPro6000_96GBx4_TRT.json
#   inference_results_v5.1/main/closed/Lenovo/systems/SR780a_V3_B200SXMx8_TRT.json
#   inference_results_v5.1/main/closed/Lenovo/results/SR780a_V3_B200SXMx8_TRT/{llama3.1-8b,whisper}/Offline/performance/run_1/mlperf_log_summary.txt
#   inference_results_v{5.1,6.0}/main/summary_results.json  (power rows filtered with a python one-off)
# JetCool datasheet
curl -sL -A "Mozilla/5.0" -o <scratch>/r6machid/r6machid_jetcool.pdf "https://info.jetcool.com/hubfs/Marketing%20Resources%202026/NVIDIA%20RTX%20PRO%206000%20SmartPlate%20Cold%20Plate%20Datasheet.pdf" && pdftotext -layout ...
# NVIDIA RTX PRO 6000 SE brief (saved by WebFetch) -> pdftotext -layout
# analysis
python3 analysis/r6_machine.py
```

Web pages opened with WebFetch: specialtimes.co.kr (dg5W), deepgadget.com launch post, inblog.ai/deepgadget (index), nvidia.com RTX PRO 6000 SE, pny.com product brief, pugetsystems.com part, itbrief.co.uk (ThermAI), aecmag.com (Renda), hardwaredealz.com (3 price pages), pny.com EMEA warranty, watercoolinguk.co.uk, pubs.lenovo.com SR780a V3 environmental.

Failed: galaxus.de and digitec.ch (timeout, 403 to curl), datacenterdynamics.com (403), newegg.com (403), Firecrawl (refused, out of credits).
