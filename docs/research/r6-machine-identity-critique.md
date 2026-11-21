# Round 6 critique: machine identity behind the realism column

Critic file for [r6-machine-identity.md](r6-machine-identity.md) and `analysis/r6_machine.py`. Role: a sceptical DigitalHeat founder. Planning and assessment only. No existing file was changed and git state was not touched. Firecrawl calls used: 0. Written Sat 21 Nov 2026.

## Re-run

- `python3 analysis/r6_machine.py` exits 0 in about 1.7 s. Every computed number in the investigator's claims c5, c15, c16, c18–c22, c25 and c29–c33 is reproduced exactly.
- My probe `probe_r6mi.py` lives in the shared scratchpad and is not saved under `analysis/`. It imports `r6_machine` without editing it. Its output is under Findings 1 and 5.

## Findings, most serious first

### 1. The MTBF was misread. Claim c9 is wrong, and c25 and the Open-risk-3 text inherit the error

The NVIDIA brief (SP-12355-001_v02, PDF opened at <https://www.pny.com/en-eu/file%20library/professional/rtx-pro-6000-server-product-brief.pdf>) prints these two lines:

> Uncontrolled environment:¹ 864,500 hours at 35 °C
> Controlled environment:² 1,062,500 hours at 35 °C

The "1" in front of 864,500 is a footnote marker ("Some environmental stress with limited maintenance (GF35)").
- I checked this with `pdftotext -bbox-layout`. The glyph is 7.2 pt tall against 10.8 pt for the digits beside it, and it sits higher on the line.
- The values also only make sense this way. Read as "1,864,500", the uncontrolled environment would beat the controlled one (1,062,500). That cannot be right.

Consequences:
- The annual failure rate is 8,760 / 864,500 = **1.01%**, not 0.47%. That is 2.16 times higher.
- Self-insurance for years 1–3 becomes about **3,700 CHF** (round-5 machine, N=6) to **6,400 CHF** (RTX PRO 6000, N=8), not 1,700–2,900 CHF.
- The script only counts failures in warranty years 1–3. **Cards also fail in years 4–5, and in 4–8 for the 8-year case, whoever built the machine.** The "vendor DLC, no self-insurance" line leaves these out too.

My probe recomputes the shares with the corrected failure rate (*computed*, critic probe):

| 5-year share incl. maintenance | Investigator | Corrected failure rate, years 1–3 | Corrected, every payback year |
|---|---|---|---|
| Round-5 machine, N=6 / N=8 | 11.6% / 12.7% | 11.7% / 12.8% | **11.8% / 12.9%** |
| RTX PRO 6000 configuration, N=6 / N=8 | 13.1% / 14.2% | 13.2% / 14.4% | **13.4% / 14.6%** |
| RTX PRO 6000 configuration, 8 years | 9.0% / 9.7% | | **9.4% / 10.1%** |

- The effect on the share is small, at +0.2 to +0.4 points. The sourced number itself is wrong, though, and a founder who opens the PDF will spot it.
- The MTBF is also a predicted figure for 35 °C air. Field GPU fault rates run higher. The plan's own Llama-3 derivation gives about 0.5 interruptions per 4-GPU server-year, and not all of those need a card swap. Use 1% as a floor, not a central value.

### 2. One configuration still is not achieved, even for J2: the measured box is not a warm-water box

- The DeepGadget page (opened) says the cooling is "Self-Contained": cooling finishes inside the server, and no extra air-conditioning is needed. It also says the box is designed to run in a 35 °C room.
- That is a closed loop with an internal radiator. Its coolant temperature is not published. Saying the heat goes to room air is an inference, but a safe one.
- So the J2 figure shows that DLC on this card works at 600 W at an unknown, probably cool, coolant temperature. **It says nothing about throughput at a 45–50 °C inlet**, which is what the realism column needs.
- The investigator's section 3 claims DLC "does not throttle" this card. That is true only at the dg5W's own coolant temperature.

### 3. J1 borrow: the host matters more than the cooling, and MLPerf itself shows it

The local file `data/raw/mlperf_inference_v6.1_summary.xlsx` (sheet 1) also lists **6.1-0018**. It is the same Cisco X580P node with the same 4 × RTX PRO 6000 SE at TGP 600 W, but on an Intel Xeon 6747P host. Compared with 6.1-0019 on the AMD EPYC 9845 host:

| Same four cards | llama3.1-8b Offline, tokens/s | whisper Offline, tokens/s |
|---|---|---|
| 6.1-0019, AMD host | 24,913.5 | 9,236.94 |
| 6.1-0018, Intel host | 14,860.7 (−40%) | 7,801.36 (−16%) |

- The dg5W has a 16-core EPYC 9124. The X215c has 160 cores per socket. Matching within 1.6% on llama does not show that whisper transfers. Transcription on the dg5W host is unknown within at least ±15%.
- **Apples to oranges in c16 and in the machine comparison.** The PRO 6000 numbers come from the AMD host (6.1-0019). The PRO 4500 numbers come from the Intel host (6.1-0017, X210 M8).
- On the same Intel host, the PRO 6000 is 2.01 times the 4500 on whisper (7,801 vs 3,878 tokens/s) and 1.56 times on llama (14,861 vs 9,519).
- At 3.66 times the card price (17,621 vs 4,819 CHF), card cost per unit of work is then **1.8 times (J1) and 2.3 times (J2)** the 4500's, not 1.4–1.5 times.
- No 4500 result exists on the AMD host, so neither comparison is like for like.

### 4. N=6 with the RTX PRO 6000 box cannot be built as costed

- Normalising to 1 kW per server gives 2.23 boxes at N=6. The investigator notes this in section 3.4, but the claims (c18, c22) and the proposed table row quote 204,747 CHF and 13.1% without the caveat.
- With whole boxes (*computed*, critic probe):

  | Boxes | Power | Installed | Coverage, case column |
  |---|---|---|---|
  | 2 | 5.39 kW | 186,343 CHF | 73.9% (not 79.6%) |
  | 3 | 8.08 kW | 267,577 CHF | 93.4% |

- Three boxes capped to about 2 kW each would reach 6 kW, but the installed cost would be about 31% higher, which puts the 5-year share near 16%. Throughput at a reduced TGP is unmeasured.
- At N=8, three boxes (8.08 kW) fit well.
- So claim c33 ("coverage is the same on any machine") holds only with roughly 1 kW power steps or power capping, and only for N=8 here.

### 5. Maintenance is anchored on a consumer DIY blog, and the script uses less time than its own anchor

- <https://www.watercoolinguk.co.uk/how-often-should-you-maintain-your-watercooling-loop/> (opened) says "Quick Maintenance (30-60 Minutes)", "Full Maintenance (2-4 Hours)" and "Change your coolant at least once a year". It is written for people building custom loops in their own PCs.
- The script allows 4 h per house-year for 6.3 boxes. That is below one 2–4 h full service per loop.
- With 3 h per box per year, the 5-year share rises to **12.2% / 13.4%** (round-5 machine) and **13.5% / 14.7%** (RTX PRO 6000) (*computed*, critic probe, corrected failure rate over every year).
- 4 h holds only if all boxes hang off one CDU secondary loop with dripless quick-disconnects. Say that, and keep the figure an *assumption*.

### 6. Smaller points

- **c6, c34:** neither page states the country or where the heat goes. "UK" for ThermAI is an inference from the site (IT Brief UK, UK patents, Manchester subsidiary). "Heat to room air" for the dg5W is an inference from "Self-Contained".
- **c11:** the datasheet's thermal curve is for PG25, not water. The rise is about 10 K, which barely matters.
- **c32 / DLC50T:** a 50 °C inlet with a 10 K rise means 60 °C at the plate outlet. That is the Alphacool and EK maximum, so there is **zero margin**. Only the JetCool plate (inlet 18–60 °C) has headroom.
- **c21:** the 1-GPU box carries the full 8,000 CHF platform, which is why it looks worst. At 4,000 CHF it is about 15.5%, still worse than the 4-GPU box, so the conclusion survives.
- **c30:** the budget is for 0.64 of a 9.4 kW machine. It is a thought experiment, not a house price. `GRID_UPGRADE` is left out, but it is 0 in the central case.
- **c14:** the PNY offers page now shows 21.11.2026 11:20. The prices are unchanged.

## Verdict table

| Claim | Verdict | Note |
|---|---|---|
| c1, c2, c3, c4 | survives | MLPerf files re-fetched and match. I did not check fp4 for c2 |
| c5 | survives with caveat | Arithmetic correct; does not show that J1 transfers (Finding 3) |
| c6 | survives with caveat | "Heat to room air" is inferred |
| c7 | survives | Power fields in the system JSON are empty |
| c8 | survives | |
| c9 | **rejected** | 864,500 h, not 1,864,500 h; failure rate 1.01% |
| c10 | survives | |
| c11 | survives with caveat | PG25, about 10 K |
| c12 | survives (as *unverified*) | |
| c13 | survives | |
| c14 | survives | |
| c15 | survives | |
| c16 | downgrade to unverified | Host mismatch; on the same Intel host 1.8× / 2.3× |
| c17 | survives (as *assumption*) | |
| c18 | survives with caveat | Fractional boxes; 13.4% with corrected failures |
| c19 | survives with caveat | 14.6% / 10.1% with corrected failures; 3 boxes fits |
| c20 | survives with caveat | 11.8% / 12.9% corrected |
| c21 | survives with caveat | Platform assumption |
| c22 | survives with caveat | Whole boxes: 186k (5.4 kW) or 268k |
| c23 | survives with caveat (*assumption*) | Consumer anchor; 4 h is below the anchor |
| c24 | survives with caveat | No clause on the page is not permission |
| c25 | **rejected** | ×2.16; years 4–5 missing |
| c26, c27, c28 | survives | |
| c29 | survives with caveat | 85% capture is an assumption |
| c30 | survives with caveat | Fractional machine, not a price |
| c31 | survives | |
| c32 | survives with caveat | Zero margin to the 60 °C block rating |
| c33 | survives with caveat | Only with about 1 kW steps or power capping |
| c34 | survives with caveat | Country is inferred |
| c35, c36 | survives | |
| c37 | survives (as *unverified*) | |
