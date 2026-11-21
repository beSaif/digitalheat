# Round 1 critique: market compute price and servers per house

Critic's review of `docs/research/r1-servers-and-price.md` and `analysis/r1_servers_choice.py`, written 2026-11-21. 0 paid Firecrawl calls. All 15 source URLs were re-opened with the free fetch tool on 2026-11-21.

## 1. What holds

- `python3 analysis/r1_servers_choice.py` re-run: output is identical to the investigator's, line for line. The physical balance (coverage, utilisation, marginal hours) matches `analysis/baseline_sweep.py`.
- The margin formula (income − electricity + value of used heat) and the break-even 0.3325 − 0.8 × 0.133 = 0.2261 CHF agree with the case formula for the follow policy.
- Every sourced price, power figure and exchange rate was found on the page named, with the caveats in section 3.

## 2. What breaks

**2.1 The N = 6 rule does not survive a small haircut on price (computed here).**
The rule uses the renter's on-demand price as host income, with every run hour sold. Re-running the rule with the investigator's own functions:

| Scenario | central | −25% price | −25%, 70% sold | −50% price | −50%, 70% sold |
|---|---|---|---|---|---|
| CPU | 1 | 0 | 0 | 0 | 0 |
| GPU-A (2 × RTX 4090) | 6 | 1 | 0 | 0 | 0 |
| GPU-B (H100 share) | 7 | 6 | 4 | 1 | 0 |

The haircut sizes are my assumptions, not sourced. The point is the cliff: in the scenario the recommendation rests on, a 25% lower income moves N from 6 to 1. Servers 2 to 5 pay back in 3.0 to 3.4 years at the central price, so they all fail together.

**2.2 The price tier is the wrong one for a heat-following server.**
The tracker lists all 11 Vast.ai configurations as on-demand. A server that stops when the tank is full cannot sell on-demand capacity; it sells interruptible capacity. The investigator's own note quotes Vast.ai saying interruptible is "50%+ cheaper". On that tier GPU-A central is about 0.30 CHF, 1.3 times the break-even, and the rule gives N = 0.

**2.3 The rule is also sensitive to the two assumed inputs (computed here, GPU-A, central price).**

| Hardware CHF | life 3 y | life 4 y | life 5 y |
|---|---|---|---|
| 5,924 | 1 | 5 | 6 |
| 8,000 | 1 | 1 | 5 |
| 10,000 | 0 | 1 | 1 |

The hardware figure is a floor: the card price is the average of the three cheapest eBay listings per day (the page does not say used or new), the 2,000 CHF host is assumed, and liquid cooling, plumbing, installation and a network line are not priced.

**2.4 "N = 6" was picked from three answers (1, 6, 7).**
The rule gives a different N per hardware class, and the one closest to the earlier provisional choice was kept. That is not an economic basis for N; it is a conditional statement: "if consumer-GPU hours sell at the on-demand marketplace price, all year, with no fee".

**2.5 The demo workload and the economics are different machines.**
Must-have 1 allows a CPU job on a laptop, and the plan's job types (embeddings, transcription) are measured on a CPU. The economics only work for GPU rental. For CPU-only hardware the rule gives N = 1 at best. The pitch must not show a CPU job and quote GPU income without saying so.

**2.6 Rental price is paid for rented time, not for 1 kW of draw.**
The case counts a running server as 1 kW. A rented GPU on a marketplace draws less than nameplate for much of the rented time, and an unrented one draws near idle. The script ties 1 kW of electricity and 0.8 kW of heat to every sold hour. Real heat per sold hour is lower; the size is unknown.

**2.7 Smaller points.**
- Hetzner: the page shows "from 319 EUR/month" and does not tie the EPYC 9454P to the AX162 explicitly. The rent includes electricity, data-centre space, network and support, so it is not income for bare hardware in a basement. Two 48-core EPYC servers are not shown to draw 1 kW.
- The CPU "low" is half of central by assumption, and the label "low/central/high" suggests a measured spread.
- GPU-B: the "central" (AWS spot, 2.52 CHF) sits above Lambda's single-GPU on-demand price (2.49 CHF). The ordering is arbitrary. The 250,000 to 400,000 USD server range has no GPU count on the page; dividing by 10.2 kW is the investigator's reading.
- RunPod's 0.34 USD community price for the RTX 4090 is in the page's structured data; the visible table shows only 0.89 USD.
- Break-even "independent of N" is true to four decimals up to N = 11 (0.2262 at N = 12, because heat is left in the tank at year end).
- Simple payback ignores resale value, repairs, financing and VAT.
- No mixed fleet was tested (expensive hardware for the servers that run 5,000 to 7,600 h, cheap hardware or the backup heater for the peak).

## 3. Source checks

| Claim | Result |
|---|---|
| fx1 | Confirmed: 20 November 2026, USD 1.0990, CHF 0.9223 |
| map1 | Confirmed: xFusion 5288 V7, 2 × 8480+, 112 cores, 512 GB, 835 / 357 / 147 W |
| map2, cpu1 | Confirmed on aws-pricing.com (third-party mirror) |
| cpu2, cpu3, gpu4 | Confirmed on Vantage; region not stated |
| cpu4 | 319 EUR "from", 304 EUR setup confirmed; CPU-to-model link not explicit on the page |
| gpu1 | Confirmed; all Vast.ai rows are on-demand |
| gpu2 | Confirmed, 0.34 USD only in structured data |
| gpu3 | Confirmed |
| map4 | 450 W confirmed; 850 W is "Required System Power", not "recommended" |
| map6 | Confirmed, 10.2 kW is the maximum rating |
| hw1 | Confirmed |
| hw3 | 2,338 USD is the "lowest average" (three cheapest listings per day); page does not say "used" |
| hw5 | Confirmed; header says updated 15 October 2026, revision note says 10 October 2026 |

Host payout: Vast.ai's June 2024 product update (search result only, page not opened: unverified) says the host fee was replaced by a surcharge on the renter side. Third-party estimates of 10 to 15% were seen in search snippets only (unverified). No occupancy figure found.

## 4. Verdict on the recommendation

- Keep the market-price table as renter prices.
- Do not present N = 6 as the result of an economic rule. Present coverage and payback against N, name the condition under which 6 passes, and say that with a 25% haircut the same rule gives N = 1.
- The honest headline for "when it does not pay off": operation pays above 0.2261 CHF per sold server-hour; hardware payback within 5 years is not shown for any hardware class once fee, interruptible pricing and unsold hours are included.

## 5. Commands used

```
python3 analysis/r1_servers_choice.py
```

Haircut and hardware tables: an inline `python3` snippet importing `marginal`, `margin`, `SCEN`, `LIFE` from `analysis/r1_servers_choice.py`, applying a price factor and sold share to the central price and re-applying the investigator's rule. Not saved as a file.
