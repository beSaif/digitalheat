# Round 2 critique: host-side income, hardware cost, mixed fleet

Critic's check of `r2-host-income-hardware.md` and `analysis/r2_fleet_economics.py`, 2026-11-21. Paid Firecrawl calls used: 1 of 1.

## What was checked

- `python3 analysis/r2_fleet_economics.py` re-run: exit 0, every quoted figure in the claims matches the output (break-evens 0.2261 / 0.3325, rank hours, X thresholds, hardware budgets, named scenarios, mixed fleet, section 9).
- Pages opened and confirmed: salad.com/pricing, the Salad demand feed (curl), Salad network-monitor article, Vast.ai earnings article, Vast.ai pricing docs, host optimization guide, host payment page, SPEC result, NVIDIA RTX 5090 page, Dell R760 page, CEC-500-2024-061 (pdftotext, lines 2040 to 2149), startupvalley article, The Register forum, dev.to post, ECB rates, Newegg listing (Firecrawl).
- Not confirmable by me: the pcserverandparts.com R740 listing (HTTP 403 with the free tools, Firecrawl budget spent on Newegg).

## Findings that change the result

1. **Salad uses one GPU per machine and needs Windows.** https://support.salad.com/article/78-is-my-machine-compatible-with-salad says: "Only one GPU is used. A second dedicated card doesn't add earnings and can cause errors", and "Linux is a closed beta for large fleet operators only". The investigator's "2 RTX 4090 per 1 kW machine on Salad" (0.386 CHF average) is therefore not available to one machine. Each paid card needs its own host.
   Computed with `python3 analysis/r2_fleet_economics_critic_check.py` (host power 100 to 200 W and the 2,000 CHF host are assumptions): 1.54 to 1.82 paid cards per kW, Salad average 0.297 to 0.351 CHF per 1-kW-hour, hardware 6,096 to 7,204 CHF per kW, first-server payback 7.5 to 11.2 years. **N* = 0 at the Salad average, not 1.** At the Salad highest rate N* is 1 to 4, not 6.
2. **The "1 server, 4.8 years" result is a knife edge even on the investigator's inputs.** Net after 5-year straight-line hardware is 38 CHF per year. A fixed cost of 100 CHF per year (internet, maintenance; assumption) makes it negative.
3. **"Most interruptible tier" is the customer's priority, not the host's choice.** Salad's tiers say which customer job is preempted by another customer job. A host does not pick the tier. A heat-following host interrupts all tiers alike. So 0.215 CHF is "the lowest rate a job can pay", not "the price of interruptible capacity sold by a heat-following server".
4. **Vast.ai does not fit a server that stops on a heat signal.** Its article says that for on-demand rentals the host "must keep the machine available until the contract ends"; the optimization guide warns of a "negative reliability signal". Listed verified offers have a median reliability of 0.991 (computed from my re-run of the offer query). Rank 6 runs 43% of the year. Vast.ai's interruptible tier means the *renter* is outbid, not that the host may switch off. No Vast.ai figure in the result is an income a heat-following server can count on.
5. **The Vast.ai snapshot is not stable.** My re-run about 70 minutes later: RTX 4090 on-demand median 0.467 USD (44 offers), floor 0.387 to 0.400 USD (40 offers); RTX 5090 on-demand 0.707 USD (33), floor 0.533 USD (28). The 4090 floor moved 12 to 15%, the 5090 on-demand 6%. The inline snippet was not saved, so the stated medians cannot be reproduced.
6. **Break-even at 80% and 50% sold assumes unsold hours still draw 1 kW.** That is resistive heating at 0.3325 CHF per kWh, which no operator would do. If the server stops (or idles) when unsold, the break-even per sold hour stays 0.2261 CHF and coverage falls instead. The script has this variant but the claim and plan change present only the first reading.
7. **H100 results and the one winning mixed fleet are not physical for a house.** 0.784 H100 per kW is a slice of a 10.2 kW, 8-GPU machine. Ranks 1 and 2 would be 1.57 H100s. The income is a vendor claim above a renter price found in round 1, and the 250,000 to 400,000 USD server price has no GPU count on its page (round 1 critique). mix1 also pairs it with the Salad highest rate at 2 cards per kW (finding 1).
8. **"Ranks 7 to 13 never pay" contradicts the script's own output.** Section 7 gives N* = 8 for the H100 high claim, and section 5 shows N* up to 11. True only for the six tested mixed pairs (the claim says seven; the script has six).
9. **Smaller points.** The 21energy prices include 20% VAT (page says so); hardware prices in USD exclude Swiss VAT (8.1%) and shipping. The Salad "average" is while a job runs, not per hour online. Heat per paid hour assumes the rented card runs at full power.

## Consequence

The direction of the investigator's result holds and gets stronger: at sourced consumer-GPU host rates, hardware does not pay back in 5 years for any server count. The honest headline is **N* = 0 by payback; N is a coverage choice**, with "1 server" only as the best case of an optimistic chain (2 cards per kW, every hour sold, no fixed cost, heat credited).

## Critic script output

```
Salad RTX 4090 host rates; one GPU per machine; 450 W card + host W (ASSUMPTION); life 5 y; heat credited; 100% sold
 host W  cards/kW  hw CHF/kW |   rate  CHF/kWh-h  rank1 margin  payback y  N*
    100      1.82      7,204 |    avg      0.351           955        7.5   0
    100      1.82      7,204 |  top25      0.406         1,375        5.2   0
    100      1.82      7,204 |    max      0.537         2,373        3.0   4
    150      1.67      6,603 |    avg      0.322           731        9.0   0
    150      1.67      6,603 |  top25      0.372         1,117        5.9   0
    150      1.67      6,603 |    max      0.492         2,031        3.3   3
    200      1.54      6,096 |    avg      0.297           543       11.2   0
    200      1.54      6,096 |  top25      0.344           898        6.8   0
    200      1.54      6,096 |    max      0.454         1,742        3.5   1

Investigator's own case (2 cards per kW in ONE machine, 5,924 CHF), Salad average, plus a fixed yearly cost per server (ASSUMPTION):
  fixed    0 CHF/yr: rank-1 margin  1,223 CHF/yr, payback   4.8 y, net after 5-y straight-line hardware     38 CHF/yr
  fixed  100 CHF/yr: rank-1 margin  1,123 CHF/yr, payback   5.3 y, net after 5-y straight-line hardware    -62 CHF/yr
  fixed  300 CHF/yr: rank-1 margin    923 CHF/yr, payback   6.4 y, net after 5-y straight-line hardware   -262 CHF/yr
  fixed  600 CHF/yr: rank-1 margin    623 CHF/yr, payback   9.5 y, net after 5-y straight-line hardware   -562 CHF/yr
```
(The column headed "CHF/kWh-h" is CHF per 1-kW-server-hour sold.)
