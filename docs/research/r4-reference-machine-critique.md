# Round 4 critique: one coherent reference machine near 1 kW and its full installed cost

Critic role: a sceptical DigitalHeat founder. Reviewed `docs/research/r4-reference-machine.md` and `analysis/r4_machine.py` (investigator's files, not modified). Written Sat 21 Nov 2026, about 10:15. Paid Firecrawl calls used by me: **0 of 1**.

Status labels as in the plan: *sourced* = I opened the URL and read the number; *computed* = re-run or one-liner shown below; *assumption*; *unverified*.

## 1. Verdict in five lines

1. **The core result stands.** The script reproduces byte-for-byte (`python3 analysis/r4_machine.py`, exit 0, output identical to section 4 of the research file). Every MLPerf, GPU-price, rental-price, BFE and VAT number I re-opened matches.
2. **One comparison is on the wrong basis.** r3's "20% (30% at 67% sold)" is a share of the **J1-only** list value (11.19 CHF), not of the 50/50 mix. Like for like: r3 J1-only 20% → r4 J1-only **6.4%**; r3 on the mix basis **24.0%** → r4 mix **10.7%** (computed below). r4 still needs less. The sentence "20% → 10.7%" must not go into the plan as written.
3. **"Both jobs measured on the same box" is true only for the Cisco blade** (2 × Xeon 6747P, 1 TB RAM, X-series PCIe node). The 2U single-socket box that the plan names (HPE DL345 Gen12, 6.1-0056) submitted **whisper only**. Its J2 figure is borrowed from the blade.
4. **The machine does not fit DigitalHeat's product.** The case slides target **50–70 °C** heating and hot water (`docs/case-presentation.md` lines 11 and 21). The reference box is air-cooled with passive GPUs. Its cost line has an air-to-water coil but no liquid cooling, and no booster. It is a compute-cost reference, not a heat-quality reference. The plan must say so.
5. **The numbers lean optimistic.** Simple payback has no interest: at 5% the 5-year share rises from 10.7% to 12.1%, and the low-price payback from 8.1 to 10.6 years. Prices are held constant for 5 to 8 years. The platform price is low for the CPU the box is modelled on. "~200,000 CHF of GPUs per basement" is wrong: it is about **121,000 CHF of GPUs** and 202,000 CHF installed.

## 2. Source checks (sourced claims)

| id | What I did | Result |
|---|---|---|
| c1 | curl `…/closed/Cisco/results/X210M8_X580P_RTXPro4500_32GBx4_TRT/whisper/Offline/performance/run_1/mlperf_log_summary.txt` | "Samples per second: 61.104", "Tokens per second: 3877.67", "Result is : VALID". Confirmed |
| c2 | curl the llama3.1-8b summary and both `measurements.json` | "Samples per second: 73.7905", "Tokens per second: 9518.66", VALID. llama `"weight_data_types": "fp4"`, whisper `"fp16"`. Confirmed. System JSON: `"host_processors_per_node": 2`, Xeon 6747P, `"host_memory_capacity": "1 TB"`, accelerator "NVIDIA RTX PRO 4500 Blackwell" (not labelled Server Edition), `"cooling": "Air-cooled"`. So this is a blade node, not the 2U 1P box |
| c3 | curl the HPE summary and system JSON; GitHub API listing of `closed/HPE/results/HPE_PROLIANT_DL345_GEN12_RTX_PRO_4500_PCIE_32GBx4_TRT` | "Samples per second: 58.0816", VALID; 1 × AMD EPYC 9375F, 384 GB, 4 × "RTX PRO 4500 Blackwell Server Edition", Air-cooled. Confirmed. **The folder holds only `whisper`**: no llama3.1-8b result for the 2U box |
| c4 | WebFetch nvidia.com `.md` page | "165 W", "32GB GDDR7", single-slot, passive. No liquid cooling mentioned. Confirmed |
| c5 | curl amd.com, tags stripped | "Default TDP 320W", "cTDP 320-400W", "# of CPU Cores 32". Confirmed. The same page also reads **"1kU Pricing 4753 USD"** (used in section 4) |
| c8 | WebFetch shop.post.ch | CHF 4,819.00; passive; 165 W; "0 (Data Center GPU)" outputs. No VAT wording. GDDR6 and GDDR7 both appear. The page never says "Server Edition", but passive, 165 W and no outputs match the SE. Confirmed with caveat |
| c9 | WebFetch ldlc.com/fr-ch | CHF 5,641.95; "PNY NVIDIA RTX PRO 4500 Blackwell Edition serveur", model TCSRTXPRO4500SE-PB; passive; "En stock dans + de 15 jours"; no TTC/HT wording. Confirmed |
| c10 | WebFetch hardwaredealz | 10 offers from 4,679.00 (alza.de) to 6,022.69 EUR; "Preise inkl. MwSt., zzgl. Versand"; updated 21.11.2026 09:20. Confirmed. Alza is an outlier: the median offer is 5,743 EUR, which is 4,812 CHF at Swiss VAT (computed). That backs post.ch as the central price |
| c11 | WebFetch Supermicro EU store | "System Starting Price €6,924.49"; VAT and base contents not stated; "Up to 4 GPUs", but the listed options are 1 × RTX PRO 6000 SE / H200 or 3 × L40S / RTX PRO 6000 Max-Q; 2 × 2000 W Titanium. Confirmed. The **2,642 / 3,400 / 3,850 EUR** figures came from Firecrawl metadata. I did not re-scrape them, so they are unverified |
| c14 | curl + pdftotext of the BFE PDF | p. 6: "Medianpreis … rund 36‘000 Franken (exkl. MWSt.)", cheapest 26,000, most expensive 49,000; p. 26: heat pump 42%, "Arbeitsleistungen mit 17%", water heater, other material, oil-tank removal and electrical work "jeweils 7 bis 8%", masonry, insulation, storage tank, commissioning "zwischen 2 bis 4%". Confirmed |
| c16 | curl estv.admin.ch | "Normal rate: 8,1 %". Confirmed |
| c25 | WebFetch runpod.io and getdeploying.com | RunPod Secure Cloud $0.72/hr, Community blank. GetDeploying: median $0.92 "as of November 21, 2026" across 7 providers; GPU.ai $0.41 cheapest (others: Lium 0.48, RunPod 0.72, Massed Compute 0.92, AceCloud 0.97, EmpirioLabs 1.00, AWS 2.52). Confirmed |

The MLPerf speech2text README says dev-clean + dev-other are "approximately 10 hours" (curl of `raw.githubusercontent.com/mlcommons/inference/master/speech2text/README.md`, line 148), so 22.05 s per sample is an approximation. If the splits are 10.7 h (my memory of LibriSpeech, *unverified*), a sample averages about 23.6 s and J1 rises about 7%. That direction is conservative.

## 3. Re-run and extra computations

The re-run matches exactly (`diff` of the research file's output block against a fresh run: identical).

Extra checks are one-liners that import `r4_machine` and `baseline_sweep`, run from `analysis/`. The bytecode file they created was removed afterwards. Output:

```
P 0.9547368421052632
6 inst 201914 boxes 6.284 op 0.2261
  i=0.0 y=5 need CHF/srv-h 1.526 share mix 10.7% J1only 6.4% J2only 31.7% | USD per GPU-h to operator 0.434 (at 67% sold 0.648)
  i=0.0 y=8 need CHF/srv-h 1.039 share mix 7.3% J1only 4.4% J2only 21.5% | USD per GPU-h to operator 0.295 (at 67% sold 0.441)
  i=0.05 y=5 need CHF/srv-h 1.727 share mix 12.1% J1only 7.3% J2only 35.8% | USD per GPU-h to operator 0.491 (at 67% sold 0.733)
  i=0.05 y=8 need CHF/srv-h 1.232 share mix 8.6% J1only 5.2% J2only 25.6% | USD per GPU-h to operator 0.350 (at 67% sold 0.523)
  exVAT 5y share 10.0
8 inst 264289 boxes 8.379 op 0.2261
  i=0.0 y=5 need CHF/srv-h 1.683 share mix 11.8% J1only 7.1% J2only 34.9% | USD per GPU-h to operator 0.479 (at 67% sold 0.714)
  i=0.0 y=8 need CHF/srv-h 1.137 share mix 8.0% J1only 4.8% J2only 23.6% | USD per GPU-h to operator 0.323 (at 67% sold 0.483)
  i=0.05 y=5 need CHF/srv-h 1.909 share mix 13.4% J1only 8.1% J2only 39.6% | USD per GPU-h to operator 0.543 (at 67% sold 0.810)
  i=0.05 y=8 need CHF/srv-h 1.353 share mix 9.5% J1only 5.7% J2only 28.1% | USD per GPU-h to operator 0.385 (at 67% sold 0.574)
  exVAT 5y share 11.0
r3 full on mix basis 24.0 r3 J1-only 20.1
peak audio-h per h, half J1 4234 Mbit/s at 32 kbit/s 135.5 all J1 271.0
HPE audio-h/kWh 1341
DE median EUR 5743.0 -> CHF incl CH VAT 4812

N6 central simple 3.86 5% interest 4.4
N6 low simple 8.06 5% interest 10.57
N8 central simple 4.33 5% interest 5.0
N8 low simple 9.03 5% interest 12.31
GPUs per house N6 121139
EPYC 9375F 1kU 4753 USD -> CHF incl VAT 4312
platform +5700 effect on 5y share N6 1.62
```

(The "exVAT" lines take Swiss VAT out of the installed cost: 5-year share 10.0% at N = 6 and 11.0% at N = 8. The 5% interest rate is an *assumption*. The annuity factor is i ÷ (1 − (1+i)^−y).)

Logic checked against the case formulas:
- Break-even is (electricity − heat used) ÷ server-hours = 0.2261, taken unchanged from `baseline_sweep.simulate`. That is correct, and correctly independent of the machine.
- At 67% sold the share is divided by 0.67, consistent with the case convention that unsold hours still run and still earn the heat credit.
- 1 server = 1 kW = 1/P boxes, so 6.28 boxes at N = 6. A real house gets 6 or 7 whole boxes; the per-house cost moves about ±5%.
- The mix is 50/50 **by server-hours**, the same as `r3_income.py` (`J1_SHARE`). The plan's job table says "50/50 by work". This is a pre-existing wording mismatch, not an r4 bug.
- c30 (the hardware share does not depend on P) is algebraically right, given that the box price does not change with P.

## 4. Attacks that do not overturn the numbers but must be in the wording

1. **Wrong comparison basis (c19, plan changes 3 and 4).** r3 section 7: "electricity - heat + hardware = 2.247 = 20% of list value", where the list value is **J1** at 11.19 CHF. Use "r3 24% → r4 10.7% (mix)" or "r3 20% → r4 6.4% (J1 only)". r3's laptop line also counted hardware only. r4 adds heat capture and house integration, so r4 is the fuller number.
2. **Interest and price decay.** Simple payback at constant 21 Nov 2026 prices. At 5% the 5-year share goes from 10.7% to 12.1% and the 8-year share from 7.3% to 8.6%. Payback at the low price goes from 8.1 to 10.6 years. Batch prices for an 8B model are already commodity prices, and an RTX PRO 4500 in 2031 is three generations old. Holding prices flat for 8 years is the optimistic case (*unverified* trend; not quantified).
3. **VAT is applied on costs but not on revenue.** A VAT-registered operator reclaims input VAT. Ex VAT the 5-year share at N = 6 is 10.0% instead of 10.7%. This partly offsets point 2. State which entity owns the hardware.
4. **Platform is underpriced for the box it describes.** The wall power and the 2U cross-check use the EPYC 9375F. Its AMD 1kU price alone is 4,753 USD, which is 4,312 CHF incl. VAT (*computed* from the *sourced* amd.com figure). The barebone that was read starts at 6,924 EUR (VAT unclear). Platform with this CPU and 384 GB RAM is plausibly **at or above the 12,000 CHF "high" case**, not 8,000 central. That adds about 1.6 points to the 5-year share (12.3%). A cheaper 16-core CPU could keep 8,000, but then say so and stop citing the 9375F box.
5. **"Same box" wording (c2).** J1 and J2 come from the Cisco blade together. The 2U single-socket HPE box measured J1 only, 5% lower: 1,341 versus 1,411 audio-h per kWh. Say "MLPerf measured both jobs on this four-GPU set".
6. **GPU value in the basement.** The research file and plan change 9 say "about 200,000 CHF of GPUs". GPUs are **about 121,000 CHF**; 202,000 is the whole installed cost.
7. **Peak network, not average.** 80 Mbit/s is a yearly average. On a cold hour with all 6.28 boxes running and half on J1, the input is about **135 Mbit/s**, and **271 Mbit/s** if all of it is J1 (32 kbit/s codec is an *assumption*). That is a business fibre line, not a home DSL line.
8. **Heat quality.** Passive cards in a 2U chassis use chassis fans; the "rest 100 W" central may be low for fans at full GPU load (*assumption*). A closed enclosure with a coil feeds coil-outlet air back into the server inlet. That ties the water temperature to the GPU inlet-air limit, so 50–70 °C water is out of reach without a heat pump (*unverified* engineering reasoning, consistent with `assumption-limits.md` section 2). The case's "80% recovered, usable without heat pump" is the case's simplification. This machine does not meet it in reality.

## 5. Founder questions still open

See the StructuredOutput list. The sharpest: *your economics hinge on transcription, and one house would need about 60,000 audio-hours of paid transcription a day, every day. Who buys that, and how many houses before you exhaust the market?* For scale only: YouTube uploads are often quoted at about 500 hours per minute, about 720,000 hours a day (*unverified*; the Statista page found masks the number). By that rough measure, about 12 houses at N = 6 would transcribe a volume the size of all YouTube uploads.
