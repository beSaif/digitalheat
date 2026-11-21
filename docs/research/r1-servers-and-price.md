# Round 1 research: market compute price and servers per house

Investigator for weak point 1 ("servers per house has no economic basis; no market compute price to hold against the break-even of 0.2261 CHF per 1-kW-server-hour"). Written 2026-11-21. Web pages were opened on 2026-11-21 with the free fetch tool; 0 paid Firecrawl calls used.

Status labels: **sourced** = number read on the page at the URL given; **computed** = produced by a script or by arithmetic shown here from sourced numbers; **assumption** = our own choice; **unverified** = seen only in a search snippet or remembered, not read on an opened page.

## 1. Short answer

- Every public price we found for hardware that draws about 1 kW is above the operating break-even of 0.2261 CHF per server-hour. The lowest is 0.27 CHF (two RTX 4090 at the cheapest tracked marketplace price), the highest hyperscaler on-demand figures are 7 to 9 CHF. *(computed from sourced prices)*
- These are prices that **customers pay**. What a host in a basement would receive is lower (platform fee, unsold hours, no SLA). We found no sourced figure for that gap; it is the biggest weakness of the comparison.
- The break-even price does not choose N, but hardware payback does. With the rule "add servers while the marginal server pays back within 5 years at the central price", N is **6** for a cheap consumer-GPU rig, **7** for a share of an H100 server, and **1** for a new CPU-only server. *(computed; the 5 years and two of the three hardware prices are assumptions)*
- Recommendation: **N = 6** (79.6% coverage, 0 dumped, 59.1% utilisation), not 8. Servers 7 and 8 raise coverage to 92.9% but each pays back in more than 5 years in two of the three scenarios.
- The model does not pay off at all below **0.2261 CHF per server-hour sold** (operation only). Including hardware over 5 years, even the first, best-used server needs 0.38 CHF (consumer GPU rig), 0.75 CHF (CPU server) or 0.93 CHF (H100 share).

## 2. Currency

| Rate | Value | Status | Source |
|---|---|---|---|
| EUR/USD | 1.0990 | sourced | https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html (reference rates of 20 November 2026) |
| EUR/CHF | 0.9223 | sourced | same page |
| CHF per USD | 0.8392 | computed | 0.9223 ÷ 1.0990 |

All cloud prices are listed in USD or EUR excluding VAT. CHF values below use these rates.

## 3. Mapping the "1 kW rack server" to named hardware

The case's server is abstract: 1 kW of electricity, no hardware named. Three concrete stand-ins:

| Stand-in | What it is | Evidence that it is about 1 kW | Status |
|---|---|---|---|
| **CPU** | One dual-socket Xeon server, mapped to one AWS `c7i.48xlarge` (192 vCPU = 96 physical cores, Sapphire Rapids) | A published SPECpower result for a dual Xeon Platinum 8480+ server (2 chips, 112 cores, 512 GB) shows 835 W average at 100% load, 357 W at 50%, 147 W at idle: https://www.spec.org/power_ssj2008/results/res2023q1/power_ssj2008-20221207-01215.html . Core count of c7i.48xlarge (96 cores, 2 threads per core): https://aws-pricing.com/c7i.48xlarge.html | power sourced for a similar server, not for the AWS host itself |
| **GPU-A** | A rig with two RTX 4090 | Card power 450 W each ("Total Graphics Power"), recommended system power for one card 850 W: https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/ . Two cards = 900 W; that the rest of the host adds only about 100 W under GPU load is an **assumption** | card power sourced, system total assumption |
| **GPU-B** | A 1 kW share of an 8-GPU H100 server = 8 ÷ 10.2 = 0.784 H100 | DGX H100: 8 × H100, 2 × Xeon 8480C, "10.2 kW max": https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html | sourced (maximum rating, not typical draw) |

Weaknesses of the mapping, stated plainly:

1. **CPU:** the SPEC server has 112 cores at 835 W, which is 134 cores per kW. Mapping 1 kW to a 96-core instance therefore understates the compute per kW by up to 1.40× (134 ÷ 96). We keep 1:1 because it is the conservative direction. SPECpower runs a Java workload; a different workload draws different power.
2. **GPU-A:** real 4090 hosts on marketplaces differ (1 to 8 cards, various CPUs). A 4090 is consumer hardware; its licence and warranty position in a hosted service was not checked (**unverified**).
3. **GPU-B:** 10.2 kW is the maximum rating, so real draw is lower and a 1 kW share holds more than 0.784 GPU. Conservative direction. One cannot buy 0.78 of a GPU; it only works as a share of a fleet.
4. **Cooling:** none of the three is sold with liquid cooling that delivers 50 to 70 °C water. That hardware costs more (not priced here).
5. **Price is not income.** All figures below are what a renter pays. A host receives less: marketplace commission (not sourced), unsold hours, and a discount for a server that stops when the house is warm.
6. **Dates differ.** Listed prices are November 2026 snapshots; GPU prices have moved fast in both directions.

## 4. Market prices, per 1-kW-server-hour

### CPU-only

| Offer | Listed price | Per 1-kW server-hour | CHF | Status | Source |
|---|---|---|---|---|---|
| AWS c7i.48xlarge on-demand, us-east-1 | 8.568 USD/h | 8.568 USD | 7.19 | sourced | https://aws-pricing.com/c7i.48xlarge.html and https://instances.vantage.sh/aws/ec2/c7i.48xlarge |
| same, eu-central-1 (Frankfurt) | 9.7776 USD/h | 9.778 USD | 8.21 | sourced | https://aws-pricing.com/c7i.48xlarge.html |
| same, eu-central-2 (Zurich) | 10.7558 USD/h | 10.756 USD | 9.03 | sourced | https://aws-pricing.com/c7i.48xlarge.html |
| same, 3-year reserved | 3.772 USD/h | 3.772 USD | 3.17 | sourced (region not stated on page) | https://instances.vantage.sh/aws/ec2/c7i.48xlarge |
| same, spot | 2.259 USD/h | 2.259 USD | 1.90 | sourced (region not stated on page; spot moves hourly) | https://instances.vantage.sh/aws/ec2/c7i.48xlarge |
| AWS c7a.48xlarge (AMD EPYC 9R14, 192 vCPU) on-demand / spot | 9.853 / 2.441 USD/h | same | 8.27 / 2.05 | sourced (region not stated) | https://instances.vantage.sh/aws/ec2/c7a.48xlarge |
| Hetzner AX162 dedicated server (EPYC 9454P, 48 cores), from 319 EUR/month plus 304 EUR setup | 2 servers for 96 cores = 638 EUR/month ÷ 730 h = 0.874 EUR/h | 0.874 EUR | 0.81 | price sourced; 96-core scaling and 730 h/month computed; setup fee ignored | https://www.hetzner.com/dedicated-rootserver/matrix-ax |

Both AWS pages are third-party mirrors of AWS's price list, not aws.amazon.com itself. The us-east-1 on-demand figure matches on both.

**CPU income per 1-kW-server-hour used in the script:** low **0.40 CHF**, central **0.81 CHF**, high **1.90 CHF**.
- High = AWS spot, assuming a host could sell at the cheapest hyperscaler tier and keep all of it.
- Central = rented bare metal with the same core count.
- Low = half of central. The 50% haircut for an interruptible, residential, no-SLA host is an **assumption**, not a sourced number.

### GPU

| Offer | Listed price per GPU-hour | Per 1-kW server-hour | CHF | Status | Source |
|---|---|---|---|---|---|
| RTX 4090, cheapest of 23 tracked providers (Salad) | 0.160 USD | ×2 = 0.320 USD | 0.27 | sourced (tracker, "last updated November 20, 2026") | https://computeprices.com/providers/vast/gpus/rtx4090 |
| RTX 4090, Vast.ai, lowest of 11 tracked configurations | 0.361 USD | ×2 = 0.722 USD | 0.61 | sourced (same tracker) | same |
| RTX 4090, Vast.ai, highest tracked | 0.627 USD | ×2 = 1.254 USD | 1.05 | sourced (same tracker) | same |
| RTX 4090, RunPod Community Cloud ("from") | 0.34 USD | ×2 = 0.68 USD | 0.57 | sourced | https://www.runpod.io/pricing |
| RTX 4090, RunPod Secure Cloud | 0.89 USD | ×2 = 1.78 USD | 1.49 | sourced | https://www.runpod.io/pricing |
| H100 PCIe, RunPod Community / Secure | 1.99 / 2.89 USD | ×0.784 = 1.56 / 2.27 USD | 1.31 / 1.90 | sourced | https://www.runpod.io/pricing |
| H100, Lambda, 8-GPU instance on-demand | 4.59 USD | ×0.784 = 3.60 USD | 3.02 | sourced | https://lambda.com/pricing |
| H100 PCIe, Lambda, single GPU | 3.79 USD | ×0.784 = 2.97 USD | 2.49 | sourced | https://lambda.com/pricing |
| AWS p5.48xlarge (8 × H100) spot | 30.584 USD per instance | ÷10.2 = 3.00 USD | 2.52 | sourced (region not stated) | https://instances.vantage.sh/aws/ec2/p5.48xlarge |
| AWS p5.48xlarge on-demand | 55.040 USD per instance | ÷10.2 = 5.40 USD | 4.53 | sourced (region not stated) | https://instances.vantage.sh/aws/ec2/p5.48xlarge |
| AWS g6e.xlarge (1 × L40S) on-demand / spot | 1.861 / 1.666 USD | not mapped to 1 kW (no sourced system power) | — | sourced, reference only | https://instances.vantage.sh/aws/ec2/g6e.xlarge |

Vast.ai's own pricing page showed no numbers to the fetch tool (prices load dynamically); it states only that interruptible instances are "50%+ cheaper" than on-demand (https://vast.ai/pricing). The Vast.ai figures above therefore come from a third-party tracker.

**GPU income per 1-kW-server-hour used in the script:**

| | low | central | high |
|---|---|---|---|
| GPU-A (2 × RTX 4090) | 0.27 CHF | 0.61 CHF | 1.49 CHF |
| GPU-B (0.784 H100) | 1.31 CHF | 2.52 CHF | 3.02 CHF |

GPU-A is the most relevant comparison for DigitalHeat: it is a marketplace where small hosts with no SLA already sell compute, which is close to a server in a basement. Its low end (0.27 CHF) is only 1.2× the break-even.

## 5. Hardware purchase price for a 1 kW server

| Stand-in | Price | CHF per 1 kW server | Status | Source |
|---|---|---|---|---|
| CPU: Dell PowerEdge R760, default configuration, **one** Xeon Gold 6430 (32 cores), 64 GB | 14,239.01 USD | 11,950 | sourced, but single CPU and well below the 96-core target | https://www.dell.com/en-us/shop/ipovw/poweredge-r760 |
| CPU: dual-socket server with about 96 to 112 cores | no price found on an opened page | **20,000 (assumption)**, plausible range 12,000 to 30,000 | assumption | — (a reseller page for two 8480+ processors alone at about 27,000 USD was seen only in a search snippet: unverified) |
| GPU-A: two used RTX 4090 | 2 × 2,338 USD (lowest average of eBay listings, June 2026; range 2,241 to 2,470) | 3,924 for the cards | sourced | https://gpupoet.com/gpu/learn/price/june-2026/nvidia-geforce-rtx-4090 |
| GPU-A: host around the cards | — | 2,000 (assumption) | assumption | — |
| GPU-A total | | **5,924** | computed from the two rows above | |
| GPU-B: complete H100 server | 250,000 to 400,000 USD per server "depending on GPU count and configuration"; single H100 27,000 to 40,000 USD | 20,570 to 32,910, midpoint **26,740** (÷ 10.2 kW, × 0.8392) | sourced range (industry guide, updated 15 October 2026); taking it as an 8-GPU, 10.2 kW server is our reading | https://intuitionlabs.ai/articles/nvidia-ai-gpu-pricing-guide |

None of these includes the heat-recovery plumbing, installation in a house, or a network line. Service life of **5 years is an assumption**.

## 6. Script and output

Script: `analysis/r1_servers_choice.py` (new; imports `load`, `simulate`, `PRICE`, `HEAT_VALUE` from `analysis/baseline_sweep.py`, which is unchanged). Command, run from the repo root:

```
python3 analysis/r1_servers_choice.py
```

Marginal server = the N-th server under the follow policy: its run hours and used heat are the difference between the N and N−1 simulations. Yearly margin = run hours × price − run hours × 0.3325 + used heat × 0.133. Payback = hardware price ÷ yearly margin. All hours are assumed sold unless stated.

Full output (status: computed):

```
FX: 1 USD = 0.8392 CHF, 1 EUR = 0.9223 CHF (ECB 2026-11-20). Service life 5 y (assumption).
Operating break-even (case formula, follow policy): 0.2261 CHF per server-hour sold

== Physical balance, follow policy ==
 N   cover   util  dump marg h/yr marg heat kWh marg cover pts
 1   19.5%  87.1%     0      7629          6103           19.5
 2   32.7%  73.0%     0      5153          4122           13.2
 3   45.5%  67.6%     0      4987          3990           12.8
 4   58.0%  64.7%     0      4885          3908           12.5
 5   69.9%  62.3%     0      4617          3694           11.8
 6   79.6%  59.1%     0      3796          3037            9.7
 7   87.1%  55.4%     0      2933          2346            7.5
 8   92.9%  51.8%     0      2281          1825            5.8
 9   96.9%  48.0%     0      1555          1244            4.0
10   99.3%  44.2%     0       913           730            2.3
11  100.0%  40.5%     0       295           223            0.7
12  100.0%  37.2%     0        32             6            0.0
13  100.0%  34.3%     0         5             2            0.0

== CPU  (96-core dual-socket): income low/central/high = 0.403/0.806/1.896 CHF per server-h; hardware 20,000 CHF (hardware 20,000 CHF = assumption) ==
 N  marg h | margin CHF/yr  low  central     high | payback y  low  central     high | fleet payback central
 1    7629 |               1350     4425    12738 |           14.8      4.5      1.6 |                   4.5
 2    5153 |                912     2989     8604 |           21.9      6.7      2.3 |                   5.4
 3    4987 |                882     2892     8327 |           22.7      6.9      2.4 |                   5.8
 4    4885 |                864     2833     8156 |           23.1      7.1      2.5 |                   6.1
 5    4617 |                817     2678     7709 |           24.5      7.5      2.6 |                   6.3
 6    3796 |                672     2202     6338 |           29.8      9.1      3.2 |                   6.7
 7    2933 |                519     1701     4897 |           38.5     11.8      4.1 |                   7.1
 8    2281 |                404     1323     3809 |           49.6     15.1      5.3 |                   7.6
 9    1555 |                275      902     2596 |           72.7     22.2      7.7 |                   8.2
10     913 |                162      530     1524 |          123.8     37.8     13.1 |                   8.9
11     295 |                 50      169      491 |          396.5    118.1     40.7 |                   9.7
12      32 |                  3       16       51 |         6439.3   1249.8    393.1 |                  10.6
13       5 |                  1        3        8 |        31512.8   7547.7   2469.6 |                  11.5
Rule 'add servers while the marginal server pays back within 5 y': N = 0 (low) / 1 (central) / 7 (high)
Compute price (CHF/server-h sold) at which the N-th server pays back in 5 y:  N=1:0.75  N=2:1.00  N=4:1.04  N=6:1.28  N=8:1.98  N=10:4.61
Share of run hours that must be sold at the central price just to cover operation: 28%

== GPU-A (2x RTX 4090 rig): income low/central/high = 0.269/0.606/1.494 CHF per server-h; hardware 5,924 CHF (hardware = 2 used cards + 2,000 CHF host (assumption)) ==
 N  marg h | margin CHF/yr  low  central     high | payback y  low  central     high | fleet payback central
 1    7629 |                324     2898     9671 |           18.3      2.0      0.6 |                   2.0
 2    5153 |                219     1957     6532 |           27.1      3.0      0.9 |                   2.4
 3    4987 |                212     1894     6322 |           28.0      3.1      0.9 |                   2.6
 4    4885 |                207     1855     6193 |           28.6      3.2      1.0 |                   2.8
 5    4617 |                196     1754     5853 |           30.2      3.4      1.0 |                   2.9
 6    3796 |                161     1442     4812 |           36.8      4.1      1.2 |                   3.0
 7    2933 |                125     1114     3718 |           47.6      5.3      1.6 |                   3.2
 8    2281 |                 97      866     2892 |           61.2      6.8      2.0 |                   3.4
 9    1555 |                 66      591     1971 |           89.7     10.0      3.0 |                   3.7
10     913 |                 39      347     1157 |          152.9     17.1      5.1 |                   4.0
11     295 |                 11      110      372 |          549.9     53.7     15.9 |                   4.4
12      32 |                 -1       10       38 |          never    617.2    155.9 |                   4.8
13       5 |                 -0        2        6 |          never   3592.4    973.0 |                   5.2
Rule 'add servers while the marginal server pays back within 5 y': N = 0 (low) / 6 (central) / 9 (high)
Compute price (CHF/server-h sold) at which the N-th server pays back in 5 y:  N=1:0.38  N=2:0.46  N=4:0.47  N=6:0.54  N=8:0.75  N=10:1.52
Share of run hours that must be sold at the central price just to cover operation: 37%

== GPU-B (0.78 H100, DGX share): income low/central/high = 1.310/2.516/3.021 CHF per server-h; hardware 26,740 CHF (hardware = mid of 250k-400k USD per 10.2 kW server) ==
 N  marg h | margin CHF/yr  low  central     high | payback y  low  central     high | fleet payback central
 1    7629 |               8268    17472    21324 |            3.2      1.5      1.3 |                   1.5
 2    5153 |               5584    11802    14403 |            4.8      2.3      1.9 |                   1.8
 3    4987 |               5405    11421    13939 |            4.9      2.3      1.9 |                   2.0
 4    4885 |               5294    11188    13654 |            5.1      2.4      2.0 |                   2.1
 5    4617 |               5004    10574    12905 |            5.3      2.5      2.1 |                   2.1
 6    3796 |               4114     8694    10610 |            6.5      3.1      2.5 |                   2.3
 7    2933 |               3179     6717     8198 |            8.4      4.0      3.3 |                   2.4
 8    2281 |               2472     5224     6376 |           10.8      5.1      4.2 |                   2.6
 9    1555 |               1685     3561     4346 |           15.9      7.5      6.2 |                   2.8
10     913 |                989     2091     2552 |           27.0     12.8     10.5 |                   3.0
11     295 |                318      674      823 |           84.1     39.7     32.5 |                   3.3
12      32 |                 32       71       87 |          832.4    378.0    307.8 |                   3.6
13       5 |                  5       11       14 |         5173.4   2387.2   1948.2 |                   3.9
Rule 'add servers while the marginal server pays back within 5 y': N = 3 (low) / 7 (central) / 8 (high)
Compute price (CHF/server-h sold) at which the N-th server pays back in 5 y:  N=1:0.93  N=2:1.26  N=4:1.32  N=6:1.63  N=8:2.57  N=10:6.08
Share of run hours that must be sold at the central price just to cover operation: 9%

== Sold-share sensitivity (unsold run hours still heat the house), central prices, N-th server margin CHF/yr ==
scenario                       sold     N=1     N=4     N=6     N=8
CPU  (96-core dual-socket)     100%    4425    2833    2202    1323
CPU  (96-core dual-socket)      70%    2580    1652    1284     771
CPU  (96-core dual-socket)      50%    1350     864     672     404
GPU-A (2x RTX 4090 rig)        100%    2898    1855    1442     866
GPU-A (2x RTX 4090 rig)         70%    1511     967     752     452
GPU-A (2x RTX 4090 rig)         50%     586     375     292     175
GPU-B (0.78 H100, DGX share)   100%   17472   11188    8694    5224
GPU-B (0.78 H100, DGX share)    70%   11713    7500    5828    3502
GPU-B (0.78 H100, DGX share)    50%    7874    5042    3918    2354
```

## 7. Recommendation for N

**Rule:** add servers while the marginal server still pays back its hardware within 5 years at the central price, with every run hour sold and never dumping heat.

| Scenario | N at low price | N at central price | N at high price |
|---|---|---|---|
| CPU server, 20,000 CHF | 0 | 1 | 7 |
| GPU-A rig, 5,924 CHF | 0 | 6 | 9 |
| GPU-B H100 share, 26,740 CHF | 3 | 7 | 8 |

**Recommend N = 6** for the reference house: 79.6% of heat demand covered, 0 kWh dumped, 59.1% utilisation, sixth server runs 3,796 h/yr. It is the largest N that passes the rule in the consumer-GPU scenario, and one below the result for the H100 scenario.

Why not 8 (the provisional choice in the plan): servers 7 and 8 add 7.5 and 5.8 coverage points but run only 2,933 and 2,281 h/yr. In the GPU-A scenario they pay back in 5.3 and 6.8 years, in the CPU scenario in 11.8 and 15.1 years. The jury ranks coverage first, so N = 8 (92.9%) remains a defensible "coverage variant" to show next to N = 6, with its payback stated.

What a sceptic can fairly say against N = 6:

- With new CPU-only servers the same rule gives N = 1 (19.5% coverage). The recommendation depends on GPU workloads being sold.
- At the low price the rule gives N = 0 in two of three scenarios. The result is sensitive to price, and the central prices are renter prices, not host income.
- If only 50% of run hours are sold at the central price, the sixth GPU-A server earns 292 CHF/yr (payback about 20 years) and the sixth CPU server 672 CHF/yr.
- The 5-year life, the 20,000 CHF CPU server and the 2,000 CHF host are assumptions. Change them and N moves.
- The marginal view assumes a fixed running order. Rotating servers changes who runs, not the totals; the fleet payback column shows the average (CPU 6.7 years, GPU-A 3.0, GPU-B 2.3 at N = 6).

## 8. When the model does not pay off

- **Operation only (the case's official figure):** below 0.2261 CHF per server-hour sold, every run hour loses money compared with a heat pump. Unchanged by N under the follow policy.
- **Unsold hours:** a server that runs without a paying job is an electric heater. The share of run hours that must be sold just to cover operation is 28% at 0.81 CHF, 37% at 0.61 CHF, 9% at 2.52 CHF.
- **Including hardware over 5 years**, the price at which the N-th server pays back:

| | N=1 | N=2 | N=4 | N=6 | N=8 | N=10 |
|---|---|---|---|---|---|---|
| CPU, 20,000 CHF | 0.75 | 1.00 | 1.04 | 1.28 | 1.98 | 4.61 |
| GPU-A, 5,924 CHF | 0.38 | 0.46 | 0.47 | 0.54 | 0.75 | 1.52 |
| GPU-B, 26,740 CHF | 0.93 | 1.26 | 1.32 | 1.63 | 2.57 | 6.08 |

  (CHF per server-hour sold; computed.)

## 9. Not done / still open

- No sourced figure for what a marketplace host actually receives (commission, occupancy). This is the number a DigitalHeat founder will ask for first.
- No sourced price for a dual-socket 96 to 112 core server; no price for liquid-cooled variants.
- AWS prices come from two third-party mirrors, not from aws.amazon.com; three of them have no region stated on the page.
- Azure and Google Cloud were not checked.
- Hetzner's hourly billing and the power draw of the AX162 were not checked; the scaling is by core count only.
