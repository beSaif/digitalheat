# Critique: r2 pause physics and realism

Critic pass on `docs/research/r2-pause-physics-realism.md` and `analysis/r2_realism.py`, 2026-11-21. No existing file was changed; git state untouched; 0 Firecrawl calls.

## What was checked

- **Re-run:** `python3 analysis/r2_realism.py` exits 0 and prints every figure quoted in claims C20 to C40. The regression check against `baseline_sweep.simulate()` passes (N=6: 79.581%, 31,067 h, 0.2261; N=8: 92.937%, 36,281 h, 0.2261).
- **Sources:** all 14 cited URLs were downloaded again and the numbers read in the text (PDFs with `pdftotext`). Every sourced figure is on the page it is cited from.
- **Extra check (not saved in the repo):** a few lines importing `sim()` from `r2_realism.py` to recompute the break-even under three ways of charging the booster.

## Sourced claims: all confirmed

| Claim | Read on the page |
|---|---|
| C1 | 814/2013 Annex II: "From 26 September 2017 ... 16,66 + 8,33 · V^0,4 Watts" |
| C2 | 814/2013 Art. 1: tanks ≤ 2 000 litres. 812/2013 Art. 1: tanks ≤ 500 litres |
| C3 | 812/2013 Annex II Table 2, all seven class limits as quoted |
| C5 | Data sheet: 887 l, 141 W, 3.38 kWh/24h, class C; 934 l, 117 W, 2.80, class C; Plus version 70 W, 1.68, class A; "nach EN 12897:2020" |
| C7 | BAG/BLV Modul 11, version 30.06.2026, Tables 1 and 2 as quoted |
| C8 | Sections 5.5 (Legionella cycle "nicht zielführend", must not be used to lower normal temperatures) and 3.13.2 (waste heat below 50 °C into non-drinking-water storage) |
| C9 | W1 2–17, W2 2–27, W3 2–32, W4 2–45, W5 > 45 °C |
| C10 | W17, W27, W32, W40, W45, W+; "few are capable of operating consistently above 45 °C" |
| C11 | Gold tier: FWS 40–45 °C, TCS 45–50 °C; 80–85% without RDHX, 95–100% with |
| C12 | LRZ quote, inlet up to 40 °C, outlet "up to 70 degrees Celsius", article dated 25 June 2012 |
| C13 | 835 W at 100%, 147 W active idle, 2 × Xeon Platinum 8480+, published Jan 2023 |
| C14 | Table: idle node 1.86 kW, GPU burn 8.43 kW, rated 10.2 kW, 8 × H100 |
| C15 | 18,826 cycles in 5 months; "123 servers" and "these 23 servers" both appear. The listed server counts add up to 123, so 23 is a typo |
| C16 | Observation 10, as quoted |

Caveats on what these sources can carry:

- **C2:** "needs no EU energy label" is an inference from the scope article. The data sheet prints a class for the 934 l tank anyway.
- **C13, C14:** two machines, neither the 1 kW reference server. SPECpower results are tuned for low idle. 17.6–22.1% is a floor for well-configured hardware, not a typical value.
- **C15:** the author worked for a vendor of server power-management software, and the hardware is from 2004–2007.
- **C16:** the study is about ambient temperature variation in air-cooled data centres. It says nothing about power cycles of liquid-cooled servers.

## Computed claims: arithmetic holds, three framings do not

### 1. The break-even rise Y is an accounting choice, not a physical result

Under the follow rule nothing is dumped, so every server-hour delivers 0.8 kWh of used heat and the break-even is 0.3325 − 0.8 × 0.133 = 0.2261 CHF for any N. It can only move through (a) heat lost from the tank and (b) whatever booster cost is charged to the servers. Recomputed for 2.80 kWh/day loss and an electric booster 50 → 60 °C:

| How the booster is charged | N=6 | N=8 |
|---|---|---|
| Outside the model, like the case's backup heater | 0.2292 (+0.0031) | 0.2293 (+0.0032) |
| Electricity charged, its heat credited at price ÷ 2.5 (the investigator's headline) | 0.2348 (+0.0087) | 0.2341 (+0.0080) |
| Electricity charged, heat not credited | 0.2386 (+0.0125) | 0.2373 (+0.0112) |

The case formula is `(electricity cost − value of the heat actually used) ÷ server-hours sold` and puts the backup heater "outside the model". The headline 0.009 is the middle of three defensible conventions that span 0.003 to 0.013.

### 2. C41 compares unlike things

Round 1's "0.2300" is 3 kWh/day loss, no direct hot water, booster outside the model. The 0.2535 set against it is no tank loss, booster charged and credited. Like for like (3 kWh/day loss, no direct hot water, N=8): 0.2300 outside, 0.2565 credited, 0.2741 strict. Round 1 did not make an error; it used the case's backup-heater convention.

### 3. "20 points" is an input, not a result

Summer drop = 1 − (50 − 10) ÷ (60 − 10). The investigator says so. With the sourced 55 °C setpoint (no warm-held pipes) it is 11.1 points; with a 45 °C loop it is 30. The 50 °C preheat also assumes no temperature difference across the heat exchanger and a tank that stays at 50 °C while it discharges through a 30 K spread.

### 4. The idle scenario is a strawman

C28 keeps all 6 or 8 paused servers powered all year. No operator would do that. The result (nothing sold June to August, 0.2659 / 0.2814) is correct for that policy and useful as a warning, but it is not "what idle power costs". Suspend-to-RAM and "one warm standby, rest off" were not examined.

### 5. "No realism switch changes 6 vs 8" is true by construction for break-even

Break-even per server-hour does not depend on N when nothing is dumped. The metric cannot separate 6 from 8. What separates them is hardware cost against the hours of servers 7 and 8 (3,546 and 3,236 h a year in the combined run), which this work does not touch.

### Smaller points

- **C35:** "no pause of one hour" is right, but 13 (N=6) and 23 (N=8) runs of one hour remain with the 8 kWh band. Band 12 at N=6 gives 190 starts and none.
- **C32:** the "heat used" threshold (restart time ÷ idle fraction = 1.4 h) holds for any compute price. The "heat dumped" threshold (1.0 h) grows with the compute price; it is only valid at the break-even price.
- **Tank loss raises utilisation** (+1.5 points) and sellable hours. Correct in the model, but it should not be read as an improvement.
- The model takes the tank loss as wasted all year. In winter part of it heats the basement, so the loss figure is on the cautious side.
- With the hold rule a server runs a median 27 h and pauses a median 16 h in the hot-water-only season. A single July demo day may show one transition or none. Demo days must be recomputed before this rule is adopted.

## Verdict summary

- Sourced claims C1–C3, C5, C7–C16: confirmed; caveats above for C2, C13–C16.
- Computed claims: all reproduce. Caveats on C23–C28, C32, C35, C39–C41 for the framings above.
- C6, C17, C18 stay unverified. C19 stays an assumption.
