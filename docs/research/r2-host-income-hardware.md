# Round 2 research: host-side income, full hardware cost, mixed fleet

Investigator for weak point "Host-side income and full hardware cost are unsourced; mixed fleet untested (decides 6 vs 1 vs 8 servers)". Written 2026-11-21. Follows `r1-servers-and-price.md` and its critique. Pages were opened on 2026-11-21. Paid Firecrawl calls used: 3 of 6 (three shop pages that refused the free fetch tool).

Status labels: **sourced** = number read on the opened page at the URL given; **computed** = produced by the script or by arithmetic shown here; **assumption** = our own choice; **unverified** = seen only in a search snippet, or our reading of a field that the source does not define.

Currency: 1 USD = 0.8392 CHF, 1 EUR = 0.9223 CHF (ECB reference rates of 20 November 2026, sourced in round 1: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html). All marketplace prices are in USD without VAT.

## 1. Short answer

1. **What a host receives is about 80% of what the renter pays.** On Salad the host rate is exactly 0.80 of the renter price at both ends of the range for RTX 5090, 4090 and 3090 (computed from two sourced lists). Vast.ai writes "Live GPU prices are typically about 25% above what hosts earn", which is also 80% (sourced).
2. **Host income for consumer GPUs is 0.21 to 0.75 CHF per 1-kW-server-hour sold** (computed from sourced host rates). The average Salad host with RTX 4090 cards gets 0.386 CHF, 1.7 times the operating break-even. The lowest Salad tier, the most interruptible one, pays 0.215 CHF, which is **below** the break-even of 0.2261 CHF.
3. **No measured occupancy figure was found.** Vast.ai's "80% utilization" is an example in a marketing article. Salad's "utilizationPct" field exceeds 100% for some cards, so it is not a plain occupancy share. Sold share stays a parameter.
4. **Full hardware cost is still not sourced.** Sourced: a refurbished dual-socket server at 2,196 USD, a new dual-RTX-5090 workstation at 25,279 USD, direct-to-chip cooling parts at 356 USD per server at data-centre scale, a 1 kW air-heating bitcoin heater at 1,990 EUR. Not found: any price for a water-coupled compute heater installed in a house.
5. **N by payback** (every rank pays back within 5 years, heat credited to the operator): at the sourced consumer-GPU host incomes with a 5,924 CHF rig, the answer is **N = 0 or 1**, not 6. N = 6 needs either the top Salad rate with every run hour sold, or hardware at 2,350 to 3,040 CHF per kW at the average rate. N = 8 needs 1,250 to 1,830 CHF per kW at the average rate. Only the H100 host rates that Vast.ai advertises give N = 5 to 8, and those are a vendor's claim.
6. **Mixed fleet:** a mix beats a uniform fleet in one tested case only (H100 share on ranks 1 and 2, cheap GPU rig on ranks 3 to 6, top Salad rate, all hours sold). With the average rate or 80% sold, the best "mix" is one server or none, and the backup heater takes the peak.
7. **Who receives the heat value** moves the operator's break-even from **0.2261 CHF** (operator credited, the case formula) to **0.3325 CHF** (homeowner gets heat free). One UK operator, Heata, states that it pays all the electricity and the household gets the heat, which is the 0.3325 case.

## 2. Host-side income (task a)

### 2.1 Fee, or host share of the renter price

| Marketplace | Finding | Status | Source |
|---|---|---|---|
| Salad, renter price per GPU-hour, tiers Batch / Low / Medium / High | RTX 5090: 0.250 / 0.367 / 0.483 / 0.600 USD. RTX 4090: 0.160 / 0.253 / 0.347 / 0.440 USD. RTX 3090: 0.090 / 0.127 / 0.163 / 0.200 USD | sourced | https://salad.com/pricing |
| Salad, host earning rate per GPU-hour, lowest to highest | RTX 5090: 0.200 to 0.480. RTX 4090: 0.128 to 0.352. RTX 3090: 0.072 to 0.160 | sourced; the feed gives no currency, USD is our reading | https://app-api.salad.com/api/v2/demand-monitor/gpu (read 2026-11-21 01:11 UTC) |
| Salad host share | 0.200/0.250, 0.480/0.600, 0.128/0.160, 0.352/0.440, 0.072/0.090, 0.160/0.200 are all **0.80** | computed | the two rows above |
| Vast.ai | "Live GPU prices are typically about 25% above what hosts earn." Host share 1 ÷ 1.25 = 0.80 | sourced (vendor article, 18 May 2026); 0.80 computed | https://vast.ai/article/how-much-money-can-you-earn-renting-out-your-gpu-on-vast-ai |
| Vast.ai fee page | No percentage on the payment page or on the host calculator page ("Transparent fees", no rate) | sourced (absence) | https://docs.vast.ai/host/payment.md , https://vast.ai/host/calculator |
| Vast.ai payout threshold | "Your account must accumulate at least $20 USD before an invoice can be generated." | sourced | https://docs.vast.ai/host/payment.md |
| Akash, Salad "20 to 25% fee", Vast "about 15%" | seen in search results only | unverified | — |

The Salad feed is the data behind the public page https://salad.com/earn/demand . That page is a JavaScript shell, so the numbers were read from the feed it loads. The feed address was found by trying it; Salad does not document it. Field meanings come from Salad's support article: earning rate range = "the lowest and highest hourly rate a running container job can pay on that card"; average = "the average across all Chefs with that GPU"; top 25% = "the average for the top quarter of earners with that GPU" (sourced: https://support.salad.com/article/613-network-monitor).

### 2.2 What a host earns per GPU-hour

| Figure | Value, USD per GPU-hour | Status | Source |
|---|---|---|---|
| Salad RTX 4090: lowest / average of all hosts / average of top 25% / highest | 0.128 / 0.2302 / 0.2663 / 0.352 | sourced | Salad feed above |
| Salad RTX 5090: lowest / average / top 25% / highest | 0.200 / 0.3227 / 0.3867 / 0.480 | sourced | Salad feed above |
| Salad RTX 3090: lowest / average / top 25% / highest | 0.072 / 0.1029 / 0.1175 / 0.160 | sourced | Salad feed above |
| Vast.ai, RTX 5090 host | "Consumer GPUs like the RTX 5090 typically earn $0.30-$0.60 per GPU-hour" | sourced (vendor's statement) | Vast.ai article above |
| Vast.ai, H100 and H200 host | "H100s and H200s bring in $2.15-$4.00+ per GPU-hour" | sourced (vendor's statement, not measured data) | Vast.ai article above |
| Vast.ai, four-GPU RTX 5090 rig | "running at 80% utilization can generate $700-$1,400 per month" | sourced (illustration; 4 × 0.8 × 730 h × 0.30 to 0.60 = 701 to 1,402, so it is arithmetic, not a measurement) | Vast.ai article above |
| One host's report: six cards (RTX 3060 to 3080) on Vast.ai | "$280-340/month" before electricity; "Sometimes 4 of my 6 cards are rented simultaneously. Sometimes 1." | sourced (single anecdote; year of the post not shown) | https://dev.to/samhartley_dev/i-expanded-my-gpu-rental-fleet-to-6-cards-heres-what-happened-to-my-earnings-10d5 |
| same, per card-hour | 280 to 340 ÷ (6 × 730 h) = 0.064 to 0.078 USD | computed | row above |

Whether Salad's "average earning rate" counts hours in which a host is online without a job is not stated. If it does, it already contains occupancy; if not, it must be multiplied by a sold share. The script treats it as income per **sold** hour and applies the sold share separately, which is the cautious reading.

### 2.3 The interruptible tier

A server that stops when the tank is full cannot sell on-demand capacity.

| Finding | Status | Source |
|---|---|---|
| Vast.ai: "Interruptible instances appeal to clients who are willing to trade guaranteed uptime for 50-80% cost savings. You'll earn less per hour with interruptible instances vs. on-demand, but they fill gaps in time that would otherwise generate nothing" | sourced | Vast.ai article above |
| Vast.ai docs: "interruptible instances often 50%+ cheaper than on-demand" | sourced | https://docs.vast.ai/documentation/instances/pricing |
| Vast.ai host guide: "The Min Bid Price is a floor for the bidding system, not an on-demand price." "Set your Min Bid Price close to your cost of power when the GPU is under load." "When your machines are idle, you earn nothing." | sourced | https://docs.vast.ai/host/optimization-guide.md |
| Vast.ai: "On-demand rentals always take priority over all interruptible instances regardless of bid price." | sourced | Vast.ai article above |
| Vast.ai public offer list, verified, single GPU, not rented, 2026-11-21 01:13 UTC. RTX 4090: median on-demand asking price 0.467 USD (42 offers), median interruptible floor 0.347 USD (38 offers), ratio 0.74. RTX 5090: 0.667 USD (33 offers) and 0.533 USD (27 offers), ratio 0.80 | computed from a sourced snapshot | https://console.vast.ai/api/v0/bundles/ (query in section 7) |
| Salad: the lowest tier is "the most interruptible"; Low and Medium "can be preempted by higher-priority groups"; charges stop when an instance stops or is preempted | sourced | https://salad.com/pricing |
| Salad lowest tier as a share of the highest tier: RTX 4090 0.160 ÷ 0.440 = 0.36; RTX 5090 0.250 ÷ 0.600 = 0.42 | computed | https://salad.com/pricing |

Limits of the Vast.ai snapshot: the endpoint returns at most 64 offers per query without a login; all of them are **unrented** offers, so these are asking prices and floors, not prices paid; the list does not say whether `dph_base` is the renter's price or the host's. The script treats it as the renter's price and divides by 1.25 (**unverified** reading). The snapshot shows floors only 20 to 26% under the on-demand asks, far less than the "50 to 80%" the vendor names for what clients save. Both can be true (floors of idle machines are not bids), but neither is a transacted interruptible price. **A sourced transacted interruptible host rate was not found.** The nearest sourced figure is Salad's lowest host rate.

### 2.4 Occupancy

No marketplace publishes a measured share of rented hours. Vast.ai says the figure is shown only to registered hosts: "your host dashboard will show detailed market stats with occupancy rates" (sourced, article above). The unauthenticated offer list ignores the `rented` filter and returns unrented offers only, so it cannot be used to count occupancy (computed: 0 of 192 returned offers were marked rented). Salad's feed has `utilizationPct` (RTX 4090: 103, RTX 5090: 99, RTX 3080 Laptop: 200); a value above 100 cannot be a share of hours, so it is not used. **Sold share remains an assumption**; the script shows 100%, 80% and 50%.

### 2.5 Income per 1-kW-server-hour

Conversion: GPUs per kW of wall power × USD per GPU-hour × 0.8392.

| Machine | GPUs per kW | Basis | Status |
|---|---|---|---|
| RTX 4090 rig | 2.00 | 450 W per card (sourced in round 1, https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/) plus about 100 W for the host | card sourced, total assumption |
| RTX 5090 workstation | 1.48 | 2 cards × 575 W "Total Graphics Power" (sourced: https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/ ; same page: "Required System Power" 1000 W for one card) plus about 200 W for CPU and the rest = 1.35 kW | card sourced, total assumption |
| H100 server share | 0.784 | 8 GPUs in 10.2 kW maximum (sourced in round 1) | sourced maximum rating |

The CHF values are in the script output, section 3 below. **No host-side price for CPU-only capacity was found**; Vast.ai and Salad pay by GPU.

## 3. Hardware and heat-recovery cost (task b)

| Item | Price | Wall power | CHF per 1 kW | Status | Source |
|---|---|---|---|---|---|
| Dual-socket CPU server, refurbished: Dell PowerEdge R740, 2 × Xeon Gold 6148 (40 cores), 256 GB, no drives, 90-day warranty, 9 in stock | 2,196.31 USD = 1,843 CHF | 457 W at full load for an R740 with 2 × Xeon Platinum 8180 and 192 GB (224 W at 50%, 52.3 W idle). Different CPU; the 6148 has fewer cores and will draw less | 1,843 ÷ 0.457 = **4,033** | price sourced; power sourced for a sister configuration; transfer is our assumption | price: https://pcserverandparts.com/dell-poweredge-r740-8-bay-sff-server-2x-intel-xeon-gold-6148-2-40-ghz-20c-256gb-ddr4-no-storage-i350-h330-refurbished/ ; power: https://www.spec.org/power_ssj2008/results/res2017q3/power_ssj2008-20170829-00780.html |
| Dual-socket CPU server, new: Dell PowerEdge R760, default configuration with **one** Xeon Gold 6430 (32 cores, 270 W), 64 GB, single 800 W power supply | 14,239.01 USD = 11,950 CHF | not measured; power supply 800 W | **11,950 as a floor** (one CPU only) | sourced; a price for two CPUs is not on the page | https://www.dell.com/en-us/shop/productdetailstxn/poweredge-r760 |
| Dual-GPU machine, new: ArsenalPC MES2X, Ryzen 9 9950X, 2 × RTX 5090, 256 GB, 1600 W power supply, 360 mm liquid cooler for the CPU | 25,279.00 USD = 21,214 CHF | 1,600 W power supply (sourced); about 1.35 kW draw (assumption, see 2.5) | 21,214 ÷ 1.35 = **15,715** | price sourced; draw assumption | https://www.newegg.com/gigabyte-gaming-desktop-pcs-dual-gpu-nvidia-geforce-rtx-5090-amd-ryzen-9-9950x-256gb-ddr5-4-tb-ssd-black/p/3D5-0073-00A57 |
| Used 2 × RTX 4090 rig (round 1) | 3,924 CHF cards (sourced) + 2,000 CHF host (assumption) | about 1 kW (assumption) | **5,924** | as in round 1 | round 1 file |
| H100 server share (round 1) | midpoint of 250,000 to 400,000 USD per server | 10.2 kW maximum | **26,740** | as in round 1 | round 1 file |

A search snippet showed the same dual-RTX-5090 workstation at 14,649 USD; the opened page shows 25,279 USD. The snippet price is **unverified** and not used. A snippet price of 2,734.61 USD for a refurbished R740xd with 2 × Xeon Gold 6140 could not be confirmed (page opened: out of stock, no price).

### Liquid cooling and heat recovery

| Item | Figure | Status | Source |
|---|---|---|---|
| Direct-to-chip liquid cooling, commercial price, 754 servers in 12 racks | "$268,654 ... making the per-server cost $356.31 and the cost per rack $22,388" | sourced | California Energy Commission, "Demonstration of Low-Cost Data Center Liquid Cooling", CEC-500-2024-061, June 2024, pages 49 to 50: https://www.energy.ca.gov/sites/default/files/2024-06/CEC-500-2024-061.pdf |
| same, parts | cooler per server node 110.67 USD, tube pair 27.68 USD, rack distribution unit 7,339.12 USD, hose pair 920.00 USD, installation 334.00 USD per rack | sourced | same |
| same, second cluster of 1,200 nodes including facility changes | 470,557.19 USD in total = 392 USD per node | total sourced, per node computed | same |
| Retrofit | "retrofitting existing servers with aftermarket liquid coolers is not an economically viable business model" | sourced | same |
| Server life | "The normal life of a server is five years." Later: "the useful life of a server is in the range of five to seven years" | sourced; supports the 5-year life used here | same |
| Payback of that liquid cooling from saved cooling energy | "the payback period is 12 years" | sourced | same |
| Compute heater sold to households: 21energy Ofen 3 Base, bitcoin miner as room heater | 1,990 EUR for "bis 1,0 kW"; Pro 2,790 EUR for 1.1 kW; Base XL 2,890 EUR for 2.0 kW; Pro XL 3,990 EUR for 2.2 kW | sourced (article of 1 September 2026); heats room air, not water; mining chips, not general compute | https://startupvalley.news/de/ofen-3-bitcoin-21energy-heizung/ |
| Bitcoin-mining water heater (Superheat) | "$2,000" in the article headline; tank size and power not read | sourced for the headline only | https://www.tomshardware.com/tech-industry/cryptomining/bitcoin-mining-water-heater-firm-says-its-usd2-000-product-can-rake-back-usd1-000-a-year-in-btc-and-claims-it-can-offset-up-to-80-percent-of-electricity-and-water-costs |
| Heata (UK): server on a household hot-water cylinder | units "put between 180W and 200W into the tank when at full power"; "We pay for all electricity used by the unit." No unit cost given | sourced (forum comments of 12 and 13 January 2023 signed by a person other commenters take to be from the company) | https://forums.theregister.com/forum/all/2023/01/12/heata_offers_free_hot_water/ |
| Qarnot digital boiler | "These modules pack up to 12 servers"; "Up to 95% of computer waste heat is turned into hot water"; no price | sourced | https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/amp |

**Not found:** a published price for a liquid-cooled server or "digital boiler" installed in a single house, per server or per kW. The 356 USD per server is a data-centre figure at a scale of 754 servers and covers parts in the rack only. The script therefore shows hardware cost as a grid and one scenario column with 3,000 CHF per server added for plumbing and installation (**assumption**, no source).

**Not included in any hardware figure here:** cold plates or other liquid cooling for the named machines (all three are air-cooled as sold); heat exchanger, pump, pipework and connection to the tank; electrician and a dedicated circuit; internet line; VAT, import and shipping to Switzerland; drives for the refurbished server; maintenance, repairs and replacement of failed parts; resale value; financing cost; remote hands. Whether consumer GPUs may be used in a hosted service under their licence and warranty was not checked.

## 4. Script and output (task c)

Script: `analysis/r2_fleet_economics.py` (new; imports `load`, `simulate`, `PRICE`, `HEAT_VALUE`, `REC` from `analysis/baseline_sweep.py`, which is unchanged). Command, from the repo root:

```
python3 analysis/r2_fleet_economics.py
```

Model: rank k is the k-th server under the follow policy; its run hours and used heat are the difference between the N = k and N = k − 1 simulations. Yearly margin = income per sold hour × sold share × run hours − run hours × 0.3325 + used heat × 0.133 (the last term only when the operator is credited the heat). Payback = hardware cost ÷ margin. N* = the largest N for which every rank 1 to N pays back within the stated life. Unsold run hours still run and heat the house. All output below is **computed**.

### 4.1 Who receives the heat value

```
== 1. Who receives the heat value? Operator break-even both ways ==
FX: 1 USD = 0.8392 CHF, 1 EUR = 0.9223 CHF (ECB reference rates 2026-11-20)
 N   srv-h  elec CHF  heat CHF  official BE (heat credited)  BE if homeowner gets heat free
 1    7629      2537       812                       0.2261                          0.3325
 6   31067     10330      3306                       0.2261                          0.3325
 8   36281     12063      3860                       0.2261                          0.3325
Official formula (unchanged): (electricity cost - value of heat actually used) / server-hours sold.
Both columns assume every run hour is sold. With sold share s the break-even per SOLD hour is the figure / s:
  sold share     100%    90%    80%    70%    50%
  heat credited 0.226  0.251  0.283  0.323  0.452
  heat free     0.333  0.369  0.416  0.475  0.665
If the homeowner pays the operator a share f of the heat value (0.133 CHF/kWh heat), break-even per sold hour at 100% sold:
  f=0.00: 0.3325  f=0.25: 0.3059  f=0.50: 0.2793  f=0.75: 0.2527  f=1.00: 0.2261
Heat value at stake, N=6: 3306 CHF/yr; N=8: 3860 CHF/yr; N=1: 812 CHF/yr.
```

The official figure for the reference house stays **0.2261 CHF** per server-hour sold, from the case formula `(electricity cost − value of the heat actually used) ÷ server-hours sold`. It is the break-even of the house and the operator taken together, or of an operator who is paid the full heat-pump value for the heat. If the homeowner gets the heat free, the operator alone needs **0.3325 CHF**. The 0.1064 CHF difference per run hour is 3,306 CHF per year at N = 6. The case text says the heat "replaces a heat pump" and that homeowners "want lower heating costs", so the homeowner must keep part of it; any split lies between the two figures.

### 4.2 Ranks

```
== 2. Server ranks, follow policy ==
rank  run h/yr  used heat kWh  cover at N=rank  util at N=rank
   1      7629           6103            19.5%           87.1%
   2      5153           4122            32.7%           73.0%
   3      4987           3990            45.5%           67.6%
   4      4885           3908            58.0%           64.7%
   5      4617           3694            69.9%           62.3%
   6      3796           3037            79.6%           59.1%
   7      2933           2346            87.1%           55.4%
   8      2281           1825            92.9%           51.8%
   9      1555           1244            96.9%           48.0%
  10       913            730            99.3%           44.2%
  11       295            223           100.0%           40.5%
  12        32              6           100.0%           37.2%
  13         5              2           100.0%           34.3%
```

### 4.3 Host income in CHF per 1-kW-server-hour sold

```
== 3. Host-side income points, converted to CHF per 1-kW-server-hour SOLD ==
   0.215 CHF   0.95x BE(credited)   0.65x BE(free)  Salad RTX 4090 host rate, lowest (most interruptible tier)
   0.386 CHF   1.71x BE(credited)   1.16x BE(free)  Salad RTX 4090 host rate, average of all hosts
   0.447 CHF   1.98x BE(credited)   1.34x BE(free)  Salad RTX 4090 host rate, average of top 25%
   0.591 CHF   2.61x BE(credited)   1.78x BE(free)  Salad RTX 4090 host rate, highest
   0.249 CHF   1.10x BE(credited)   0.75x BE(free)  Salad RTX 5090 host rate, lowest
   0.401 CHF   1.77x BE(credited)   1.21x BE(free)  Salad RTX 5090 host rate, average of all hosts
   0.597 CHF   2.64x BE(credited)   1.79x BE(free)  Salad RTX 5090 host rate, highest
   0.373 CHF   1.65x BE(credited)   1.12x BE(free)  Vast article, RTX 5090 host, low end
   0.746 CHF   3.30x BE(credited)   2.24x BE(free)  Vast article, RTX 5090 host, high end
   0.466 CHF   2.06x BE(credited)   1.40x BE(free)  Vast offers, RTX 4090 interruptible floor median / 1.25
   0.627 CHF   2.77x BE(credited)   1.89x BE(free)  Vast offers, RTX 4090 on-demand median / 1.25
   0.530 CHF   2.34x BE(credited)   1.59x BE(free)  Vast offers, RTX 5090 interruptible floor median / 1.25
   0.663 CHF   2.93x BE(credited)   2.00x BE(free)  Vast offers, RTX 5090 on-demand median / 1.25
   1.415 CHF   6.26x BE(credited)   4.26x BE(free)  Vast article, H100/H200 host, low end (vendor claim)
   2.633 CHF  11.64x BE(credited)   7.92x BE(free)  Vast article, H100/H200 host, high end (vendor claim)
GPUs per kW: RTX 4090 2.00, RTX 5090 1.48, H100 0.784
Host share on Salad (host rate / renter price): 4090 lowest 0.128/0.160=0.80, 4090 highest 0.352/0.440=0.80, 5090 lowest 0.200/0.250=0.80, 5090 highest 0.480/0.600=0.80
Vast interruptible floor / on-demand asking median: RTX 4090 0.74, RTX 5090 0.80
```

### 4.4 Hardware cost per kW

```
== 4. Hardware cost per 1 kW of wall power (CHF) ==
     4,033  refurb CPU (R740, 2x Gold 6148)
     5,924  used 2x RTX 4090 rig (round 1)
    11,950  new CPU (R760, 1 CPU, floor)
    15,715  new 2x RTX 5090 workstation
    26,740  H100 server share (round 1)
       299  direct-to-chip liquid cooling parts per server, data-centre scale (adder, NOT a house installation)
```

### 4.5 N* over income and hardware cost (three of eight grids; the command prints all)

```
== 5. N* = number of servers such that every rank pays back within the life ==
   rows: host income CHF per SOLD 1-kW-server-hour; unsold run hours still run as heaters

-- life 5 y, sold share 100%, heat value credited to operator --
 income/h |  2,000  3,000  4,000  6,000  8,000 10,000 15,000 20,000 27,000   <- hardware CHF per 1 kW server
     0.15 |      0      0      0      0      0      0      0      0      0
     0.20 |      0      0      0      0      0      0      0      0      0
     0.25 |      0      0      0      0      0      0      0      0      0
     0.30 |      1      0      0      0      0      0      0      0      0
     0.35 |      6      4      1      0      0      0      0      0      0
     0.40 |      7      6      5      1      0      0      0      0      0
     0.50 |      9      8      7      5      1      1      0      0      0
     0.60 |      9      8      8      6      5      1      0      0      0
     0.75 |     10      9      9      7      6      5      1      0      0
     1.00 |     10     10      9      9      8      7      5      1      1
     1.50 |     10     10     10      9      9      8      7      6      5
     2.00 |     11     10     10     10     10      9      8      8      6
     3.00 |     11     11     11     10     10     10      9      9      8

-- life 5 y, sold share 80%, heat value credited to operator --
 income/h |  2,000  3,000  4,000  6,000  8,000 10,000 15,000 20,000 27,000   <- hardware CHF per 1 kW server
     0.15 |      0      0      0      0      0      0      0      0      0
     0.20 |      0      0      0      0      0      0      0      0      0
     0.25 |      0      0      0      0      0      0      0      0      0
     0.30 |      0      0      0      0      0      0      0      0      0
     0.35 |      1      0      0      0      0      0      0      0      0
     0.40 |      5      1      0      0      0      0      0      0      0
     0.50 |      7      6      5      1      0      0      0      0      0
     0.60 |      8      7      6      4      1      0      0      0      0
     0.75 |      9      8      8      6      5      1      0      0      0
     1.00 |     10      9      9      8      7      6      1      1      0
     1.50 |     10     10     10      9      8      8      6      5      1
     2.00 |     11     10     10     10      9      9      8      7      5
     3.00 |     11     11     10     10     10      9      9      8      7

-- life 5 y, sold share 80%, heat value given to homeowner free --
 income/h |  2,000  3,000  4,000  6,000  8,000 10,000 15,000 20,000 27,000   <- hardware CHF per 1 kW server
     0.15 |      0      0      0      0      0      0      0      0      0
     0.20 |      0      0      0      0      0      0      0      0      0
     0.25 |      0      0      0      0      0      0      0      0      0
     0.30 |      0      0      0      0      0      0      0      0      0
     0.35 |      0      0      0      0      0      0      0      0      0
     0.40 |      0      0      0      0      0      0      0      0      0
     0.50 |      1      0      0      0      0      0      0      0      0
     0.60 |      7      5      1      0      0      0      0      0      0
     0.75 |      9      8      6      5      1      1      0      0      0
     1.00 |     10      9      8      7      6      5      1      0      0
     1.50 |     10     10      9      9      8      7      6      5      1
     2.00 |     10     10     10      9      9      8      7      6      5
     3.00 |     11     11     10     10     10      9      9      8      7
```

### 4.6 The ranges in which N = 1, 6 and 8 are right

```
== 6. When are N=1, N=6, N=8 each the right answer? ==
Rank k pays back within L years iff  income x sold share >= BE + (hardware / L) / h_k.
So N* depends only on X = (hardware / L) / (income x sold share - BE), in run hours per year:
  N*=1: 5153 < X <= 7629
  N*=6: 2933 < X <= 3796
  N*=8: 1555 < X <= 2281
  N*=0: X > 7629 or income x sold share <= BE.   BE = 0.2261 (heat credited) or 0.3325 (heat free)

Net income per RUN hour (= income per sold hour x sold share), CHF, heat credited:
 hardware life | N*=0 below |   N*=1 from..to |   N*=6 from..to |   N*=8 from..to | N*>=11 from
    2,000    3 |      0.313 |  0.313..0.355   |  0.402..0.453   |  0.518..0.655   |       2.486
    2,000    5 |      0.279 |  0.279..0.304   |  0.331..0.362   |  0.401..0.483   |       1.582
    2,000    7 |      0.264 |  0.264..0.282   |  0.301..0.324   |  0.351..0.410   |       1.195
    4,000    3 |      0.401 |  0.401..0.485   |  0.577..0.681   |  0.811..1.084   |       4.746
    4,000    5 |      0.331 |  0.331..0.381   |  0.437..0.499   |  0.577..0.741   |       2.938
    4,000    7 |      0.301 |  0.301..0.337   |  0.377..0.421   |  0.477..0.594   |       2.163
    6,000    3 |      0.488 |  0.488..0.614   |  0.753..0.908   |  1.103..1.512   |       7.006
    6,000    5 |      0.383 |  0.383..0.459   |  0.542..0.635   |  0.752..0.998   |       4.294
    6,000    7 |      0.338 |  0.338..0.392   |  0.452..0.518   |  0.602..0.777   |       3.132
    9,000    3 |      0.619 |  0.619..0.808   |  1.016..1.249   |  1.541..2.155   |      10.396
    9,000    5 |      0.462 |  0.462..0.575   |  0.700..0.840   |  1.015..1.384   |       6.328
    9,000    7 |      0.395 |  0.395..0.476   |  0.565..0.664   |  0.790..1.053   |       4.584
   16,000    3 |      0.925 |  0.925..1.261   |  1.631..2.044   |  2.564..3.656   |      18.305
   16,000    5 |      0.646 |  0.646..0.847   |  1.069..1.317   |  1.629..2.284   |      11.074
   16,000    7 |      0.526 |  0.526..0.670   |  0.828..1.005   |  1.228..1.696   |       7.974
   27,000    3 |      1.406 |  1.406..1.973   |  2.597..3.295   |  4.172..6.014   |      30.735
   27,000    5 |      0.934 |  0.934..1.274   |  1.649..2.067   |  2.593..3.699   |      18.531
   27,000    7 |      0.732 |  0.732..0.975   |  1.242..1.541   |  1.917..2.707   |      13.301

Net income per RUN hour (= income per sold hour x sold share), CHF, heat free to homeowner:
 hardware life | N*=0 below |   N*=1 from..to |   N*=6 from..to |   N*=8 from..to | N*>=11 from
    2,000    3 |      0.420 |  0.420..0.462   |  0.508..0.560   |  0.625..0.761   |       2.592
    2,000    5 |      0.385 |  0.385..0.410   |  0.438..0.469   |  0.508..0.590   |       1.688
    2,000    7 |      0.370 |  0.370..0.388   |  0.408..0.430   |  0.458..0.516   |       1.301
    4,000    3 |      0.507 |  0.507..0.591   |  0.684..0.787   |  0.917..1.190   |       4.852
    4,000    5 |      0.437 |  0.437..0.488   |  0.543..0.605   |  0.683..0.847   |       3.044
    4,000    7 |      0.407 |  0.407..0.443   |  0.483..0.527   |  0.583..0.700   |       2.270
    6,000    3 |      0.595 |  0.595..0.721   |  0.859..1.014   |  1.209..1.619   |       7.112
    6,000    5 |      0.490 |  0.490..0.565   |  0.649..0.742   |  0.859..1.104   |       4.400
    6,000    7 |      0.445 |  0.445..0.499   |  0.558..0.625   |  0.708..0.884   |       3.238
    9,000    3 |      0.726 |  0.726..0.915   |  1.123..1.355   |  1.648..2.262   |      10.502
    9,000    5 |      0.568 |  0.568..0.682   |  0.807..0.946   |  1.122..1.490   |       6.434
    9,000    7 |      0.501 |  0.501..0.582   |  0.671..0.771   |  0.896..1.159   |       4.691
   16,000    3 |      1.032 |  1.032..1.367   |  1.737..2.151   |  2.671..3.762   |      18.412
   16,000    5 |      0.752 |  0.752..0.953   |  1.175..1.424   |  1.735..2.390   |      11.180
   16,000    7 |      0.632 |  0.632..0.776   |  0.935..1.112   |  1.335..1.802   |       8.081
   27,000    3 |      1.512 |  1.512..2.079   |  2.703..3.401   |  4.278..6.120   |      30.841
   27,000    5 |      1.040 |  1.040..1.380   |  1.755..2.174   |  2.700..3.805   |      18.638
   27,000    7 |      0.838 |  0.838..1.081   |  1.349..1.648   |  2.023..2.813   |      13.408

Hardware budget (CHF per 1 kW server, life 5 y, 100% sold, heat credited) for which N* is 1, 6, 8 at sourced income points:
 income | N*=0 above |            N*=1 |            N*=6 |            N*=8 | point
  0.215 |        any |               - |               - |               - | Salad 4090 lowest: below break-even, no hardware budget at all
  0.386 |      6,114 |  4,130..6,114   |  2,350..3,042   |  1,246..1,828   | Salad 4090 average
  0.401 |      6,679 |  4,512..6,679   |  2,568..3,324   |  1,361..1,997   | Salad 5090 average
  0.466 |      9,148 |  6,179..9,148   |  3,517..4,552   |  1,865..2,735   | Vast 4090 interruptible floor /1.25
  0.591 |     13,912 |  9,397..13,912  |  5,348..6,922   |  2,836..4,160   | Salad 4090 highest
  0.746 |     19,830 | 13,394..19,830  |  7,624..9,867   |  4,042..5,929   | Vast 5090 host high end
  1.415 |     45,356 | 30,636..45,356  | 17,437..22,568  |  9,245..13,561  | Vast H100 host low end
```

### 4.7 Named scenarios

```
== 7. Named scenarios ==
N* and payback in years of rank 1 / 6 / 8, life 5 y. 'inst' adds 3,000 CHF per server for plumbing and installation (ASSUMPTION).
scenario                                       inc      hw |       sold100 credit |        sold80 credit |  sold80 credit +inst |     sold80 heat free
used 2x4090 rig, Salad lowest                0.215   5,924 | N*=0 never/never/never | N*=0 never/never/never | N*=0 never/never/never | N*=0 never/never/never
used 2x4090 rig, Salad average               0.386   5,924 |    N*=1 4.8/9.7/16.2 |   N*=0 9.4/18.8/31.3 |  N*=0 14.1/28.3/47.1 | N*=0 never/never/never
used 2x4090 rig, Vast interruptible floor    0.466   5,924 |    N*=3 3.2/6.5/10.8 |   N*=0 5.3/10.6/17.7 |   N*=0 8.0/16.0/26.7 |  N*=0 19.3/38.8/64.5
used 2x4090 rig, Salad highest               0.591   5,924 |     N*=6 2.1/4.3/7.1 |    N*=4 3.1/6.3/10.5 |    N*=1 4.7/9.5/15.9 |   N*=0 5.5/11.1/18.5
new 2x5090 workstation, Salad average        0.401  15,715 |  N*=0 11.8/23.6/39.3 |  N*=0 21.7/43.6/72.6 |  N*=0 25.9/52.0/86.5 | N*=0 never/never/never
new 2x5090 workstation, Vast host high end   0.746  15,715 |    N*=1 4.0/8.0/13.3 |   N*=0 5.6/11.2/18.6 |   N*=0 6.6/13.3/22.1 |   N*=0 7.8/15.7/26.1
H100 share, Vast host low end (claim)        1.415  26,740 |     N*=5 2.9/5.9/9.9 |    N*=1 3.9/7.8/12.9 |    N*=1 4.3/8.6/14.4 |    N*=1 4.4/8.8/14.7
H100 share, Vast host high end (claim)       2.633  26,740 |     N*=8 1.5/2.9/4.9 |     N*=7 1.9/3.7/6.2 |     N*=6 2.1/4.2/6.9 |     N*=6 2.0/4.0/6.6
```

### 4.8 Mixed fleet

```
== 8. Mixed fleet: per rank pick the option with the best yearly net = margin - hardware / life ==
Options per rank: A (expensive, high income), B (cheap, low income), or none (backup heater, net 0).

sold 100%, life 5 y, heat credited. A = H100 share at Vast host low end (claim); B = used 2x4090 rig at Salad average
  A: 1.415 CHF/h, 26,740 CHF   B: 0.386 CHF/h, 5,924 CHF
  best mix by rank: AAAAA  -> N=5, coverage 69.9%, net 5,687 CHF/yr after straight-line hardware cost
  all-A fleet: N=5, net 5,687 CHF/yr   all-B fleet: N=1, net 38 CHF/yr
  A beats B on a rank only if it runs more than 4,047 h/yr

sold 100%, life 5 y, heat credited. A = H100 share at Vast host low end (claim); B = used 2x4090 rig at Salad highest
  A: 1.415 CHF/h, 26,740 CHF   B: 0.591 CHF/h, 5,924 CHF
  best mix by rank: AABBBB  -> N=6, coverage 79.6%, net 6,432 CHF/yr after straight-line hardware cost
  all-A fleet: N=5, net 5,687 CHF/yr   all-B fleet: N=6, net 4,221 CHF/yr
  A beats B on a rank only if it runs more than 5,050 h/yr

sold 100%, life 5 y, heat credited. A = H100 share at HALF the Vast low end; B = used 2x4090 rig at Salad average
  A: 0.708 CHF/h, 26,740 CHF   B: 0.386 CHF/h, 5,924 CHF
  best mix by rank: B  -> N=1, coverage 19.5%, net 38 CHF/yr after straight-line hardware cost
  all-A fleet: N=0, net 0 CHF/yr   all-B fleet: N=1, net 38 CHF/yr
  A beats B on a rank only if it runs more than 12,961 h/yr

sold 100%, life 5 y, heat credited. A = new 2x5090 workstation at Vast host high end; B = used 2x4090 rig at Salad average
  A: 0.746 CHF/h, 15,715 CHF   B: 0.386 CHF/h, 5,924 CHF
  best mix by rank: A  -> N=1, coverage 19.5%, net 823 CHF/yr after straight-line hardware cost
  all-A fleet: N=1, net 823 CHF/yr   all-B fleet: N=1, net 38 CHF/yr
  A beats B on a rank only if it runs more than 5,445 h/yr

sold 100%, life 5 y, heat credited. A = used 2x4090 rig at Salad highest; B = refurbished CPU server earning nothing (pure heater)
  A: 0.591 CHF/h, 5,924 CHF   B: 0.000 CHF/h, 4,033 CHF
  best mix by rank: AAAAAA  -> N=6, coverage 79.6%, net 4,221 CHF/yr after straight-line hardware cost
  all-A fleet: N=6, net 4,221 CHF/yr   all-B fleet: N=0, net 0 CHF/yr
  A beats B on a rank only if it runs more than 640 h/yr

sold 100%, life 5 y, heat credited. A = used 2x4090 rig at Salad average; B = refurbished CPU server at 0.30 CHF/h (ASSUMPTION, no source)
  A: 0.386 CHF/h, 5,924 CHF   B: 0.300 CHF/h, 4,033 CHF
  best mix by rank: A  -> N=1, coverage 19.5%, net 38 CHF/yr after straight-line hardware cost
  all-A fleet: N=1, net 38 CHF/yr   all-B fleet: N=0, net 0 CHF/yr
  A beats B on a rank only if it runs more than 4,378 h/yr

sold 80%, life 5 y, heat credited. A = H100 share at Vast host low end (claim); B = used 2x4090 rig at Salad average
  A: 1.415 CHF/h, 26,740 CHF   B: 0.386 CHF/h, 5,924 CHF
  best mix by rank: A  -> N=1, coverage 19.5%, net 1,564 CHF/yr after straight-line hardware cost
  all-A fleet: N=1, net 1,564 CHF/yr   all-B fleet: N=0, net 0 CHF/yr
  A beats B on a rank only if it runs more than 5,058 h/yr

sold 80%, life 5 y, heat credited. A = H100 share at Vast host low end (claim); B = used 2x4090 rig at Salad highest
  A: 1.415 CHF/h, 26,740 CHF   B: 0.591 CHF/h, 5,924 CHF
  best mix by rank: ABBB  -> N=4, coverage 58.0%, net 1,714 CHF/yr after straight-line hardware cost
  all-A fleet: N=1, net 1,564 CHF/yr   all-B fleet: N=4, net 846 CHF/yr
  A beats B on a rank only if it runs more than 6,313 h/yr

sold 80%, life 5 y, heat credited. A = H100 share at HALF the Vast low end; B = used 2x4090 rig at Salad average
  A: 0.708 CHF/h, 26,740 CHF   B: 0.386 CHF/h, 5,924 CHF
  best mix by rank: (no server)  -> N=0, coverage 0.0%, net 0 CHF/yr after straight-line hardware cost
  all-A fleet: N=0, net 0 CHF/yr   all-B fleet: N=0, net 0 CHF/yr
  A beats B on a rank only if it runs more than 16,201 h/yr

sold 80%, life 5 y, heat credited. A = new 2x5090 workstation at Vast host high end; B = used 2x4090 rig at Salad average
  A: 0.746 CHF/h, 15,715 CHF   B: 0.386 CHF/h, 5,924 CHF
  best mix by rank: (no server)  -> N=0, coverage 0.0%, net 0 CHF/yr after straight-line hardware cost
  all-A fleet: N=0, net 0 CHF/yr   all-B fleet: N=0, net 0 CHF/yr
  A beats B on a rank only if it runs more than 6,806 h/yr

sold 80%, life 5 y, heat credited. A = used 2x4090 rig at Salad highest; B = refurbished CPU server earning nothing (pure heater)
  A: 0.591 CHF/h, 5,924 CHF   B: 0.000 CHF/h, 4,033 CHF
  best mix by rank: AAAA  -> N=4, coverage 58.0%, net 846 CHF/yr after straight-line hardware cost
  all-A fleet: N=4, net 846 CHF/yr   all-B fleet: N=0, net 0 CHF/yr
  A beats B on a rank only if it runs more than 800 h/yr

sold 80%, life 5 y, heat credited. A = used 2x4090 rig at Salad average; B = refurbished CPU server at 0.30 CHF/h (ASSUMPTION, no source)
  A: 0.386 CHF/h, 5,924 CHF   B: 0.300 CHF/h, 4,033 CHF
  best mix by rank: (no server)  -> N=0, coverage 0.0%, net 0 CHF/yr after straight-line hardware cost
  all-A fleet: N=0, net 0 CHF/yr   all-B fleet: N=0, net 0 CHF/yr
  A beats B on a rank only if it runs more than 5,473 h/yr
```

### 4.9 Thresholds

```
== 9. When the model does not pay off (computed thresholds) ==
Operation only, every run hour sold: below 0.2261 CHF per sold server-hour (heat credited) / 0.3325 (heat free).
Operation only, 80% of run hours sold: below 0.283 / 0.416 CHF per sold hour.
Operation only, 50% of run hours sold: below 0.452 / 0.665 CHF per sold hour.
With hardware, income per sold hour needed for rank k to pay back (sold 80%, life 5 y):
hardware CHF |   rank 1   rank 2   rank 6   rank 8 | same, heat free:   rank 1   rank 6   rank 8
       2,000 |    0.348    0.380    0.414    0.502 |                     0.481    0.547    0.635
       4,000 |    0.414    0.477    0.546    0.721 |                     0.547    0.679    0.854
       5,924 |    0.477    0.570    0.673    0.932 |                     0.610    0.806    1.065
       8,924 |    0.575    0.716    0.870    1.261 |                     0.708    1.003    1.394
      15,714 |    0.798    1.045    1.318    2.005 |                     0.931    1.451    2.138
      26,740 |    1.159    1.580    2.044    3.213 |                     1.292    2.177    3.346
```

## 5. Reading the result

**N depends on one number.** X = (hardware cost ÷ life) ÷ (income per sold hour × sold share − break-even), in hours per year. N* = 1 for X between 5,153 and 7,629; N* = 6 for X between 2,933 and 3,796; N* = 8 for X between 1,555 and 2,281; no server above 7,629. (computed)

| Answer | Condition, 5-year life, heat credited to the operator | Do sourced figures reach it? |
|---|---|---|
| N = 0 | net income per run hour below 0.2261 + hardware ÷ 38,145 | Yes: Salad's lowest tier (0.215 CHF) at any hardware cost; the Salad average (0.386 CHF) with hardware above 6,114 CHF; the same average at 80% sold with the 5,924 CHF rig |
| N = 1 | hardware 4,130 to 6,114 CHF per kW at 0.386 CHF, all hours sold | Yes: used 2 × RTX 4090 rig (5,924 CHF) at the Salad average, all hours sold. First server pays back in 4.8 years |
| N = 6 | hardware 2,350 to 3,042 CHF at 0.386 CHF; or 5,348 to 6,922 CHF at 0.591 CHF | Only at Salad's highest rate with every run hour sold. No sourced machine costs 2,350 to 3,042 CHF per kW |
| N = 8 | hardware 1,246 to 1,828 CHF at 0.386 CHF; 2,836 to 4,160 CHF at 0.591 CHF; 9,245 to 13,561 CHF at 1.415 CHF | Not with any sourced pair. The H100 share at the top of Vast.ai's claimed range (2.633 CHF) gives N* = 8 with all hours sold |

With the heat given to the homeowner, every income threshold rises by 0.1064 CHF per run hour, and at 80% sold no consumer-GPU scenario pays back any server within 5 years.

**Mixed fleet.** Hardware A beats hardware B on a rank only if that rank runs more than (cost A − cost B) ÷ life ÷ ((income A − income B) × sold share) hours. In one tested case this gives a real mix: H100 share on ranks 1 and 2, used RTX 4090 rig on ranks 3 to 6, net 6,432 CHF per year against 5,687 (all H100, N = 5) and 4,221 (all rigs, N = 6). It needs the top Salad rate, Vast.ai's claimed H100 rate and every hour sold. With the average Salad rate the cheap option pays on rank 1 only, so the "mix" is one to five expensive servers and the backup heater. A refurbished CPU server as a pure heater never pays: it costs 4,033 CHF per kW and each run hour costs 0.2261 CHF more than the heat pump it replaces. In no tested mixed case does any option pay on ranks 7 to 13; they are left to the backup heater.

**When the model does not pay off** (computed):

- Operation only, all run hours sold: below 0.2261 CHF per sold server-hour if the operator is credited the heat, below 0.3325 CHF if the homeowner gets it free.
- Operation only, 80% of run hours sold: below 0.283 and 0.416 CHF. At 50% sold: 0.452 and 0.665 CHF.
- The most interruptible tier on Salad pays a host with RTX 4090 cards 0.215 CHF per 1-kW-server-hour: below break-even before any hardware.
- With hardware at 5,924 CHF per kW, 5 years and 80% sold, the first server needs 0.477 CHF per sold hour, the sixth 0.673 CHF, the eighth 0.932 CHF. The average sourced consumer-GPU host rate is 0.39 to 0.40 CHF.
- A new dual-RTX-5090 workstation (15,715 CHF per kW) does not pay back within 5 years at any sourced consumer-GPU rate except Vast.ai's top figure with all hours sold (rank 1 only, 4.0 years).
- Adding 3,000 CHF per server for installation at 80% sold leaves, among the consumer-GPU scenarios, N* = 1 only at the top Salad rate.

## 6. Weak points of this work

- The Salad feed is undocumented, has no currency label, and is a single snapshot (2026-11-21 01:11 UTC). Rates move.
- Salad pays per GPU of a gaming PC. A host with two cards in one machine, or a rack server, may be paid differently.
- The Vast.ai host figures are the vendor's own advertising. The H100 range in particular (2.15 to 4.00 USD per GPU-hour to the host) is above the RunPod community renter price of 1.99 USD found in round 1, so it is not a safe basis.
- Income is counted per sold hour at 1 kW of draw. A rented GPU does not draw full power all the time (round 1 critique, point 2.6); real heat per sold hour is lower. Not modelled.
- Wall power of the two GPU machines is assumed, not measured. The refurbished server's power is taken from a sister configuration.
- Simple payback: no resale value, repairs, financing or VAT.
- Ranks assume a fixed running order. Rotating servers changes who runs, not the totals; with a mixed fleet the order matters and the expensive machine must always run first.
- No CPU-only host income was found, so the refurbished CPU server has no sourced income at all.
- The "stop when unsold" variant lowers coverage; its coverage was not recomputed.

## 7. Commands

```
python3 analysis/r2_fleet_economics.py
```

Salad feed (saved outside the repo; the script holds the six values used):

```
curl -sL -A "Mozilla/5.0" "https://app-api.salad.com/api/v2/demand-monitor/gpu"
```

Vast.ai offer list, once per GPU model and type (`bid` = interruptible, `on-demand`), with a browser user agent; medians of `dph_base` (on-demand) and `min_bid` (interruptible) computed with an inline `python3` snippet, not saved as a file:

```
curl -s -A "<browser user agent>" -G "https://console.vast.ai/api/v0/bundles/" --data-urlencode 'q={"gpu_name":{"eq":"RTX 4090"},"num_gpus":{"eq":1},"verified":{"eq":true},"rentable":{"eq":true},"type":"bid","order":[["dph_total","asc"]],"limit":64}'
```

CEC report: PDF downloaded by the fetch tool, text extracted with `pdftotext -layout`, cost section read at lines 2020 to 2165 of the text (report pages 47 to 50).

## 8. Proposed changes to the plan

1. Replace "show 6 and 8 side by side, working default 6" with: **N is a coverage choice, not an economic one.** State next to it: by 5-year payback at the average sourced host rate the answer is 1 server (4.8 years) or none; 6 needs 0.54 to 0.64 CHF per run hour at 6,000 CHF hardware, 8 needs 0.75 to 1.00 CHF.
2. Report the break-even twice, always together: 0.2261 CHF (case formula, heat credited) as the official key figure and 0.3325 CHF (homeowner gets heat free) as the operator's own figure. Add a "heat share paid to operator" parameter (0 to 1) to the balance.
3. Add the sold-share parameter to the break-even line: 0.283 CHF at 80% sold, 0.452 CHF at 50% (heat credited).
4. Use host-side income in the pitch: "a host gets about 80% of the listed price; average RTX 4090 host rate on Salad is 0.39 CHF per 1-kW-server-hour, the most interruptible tier 0.215 CHF, below break-even."
5. Drop the mixed fleet as a headline idea. Keep one sentence: expensive hardware only on the ranks that run more than about 5,000 hours (ranks 1 and 2); the peak belongs to the backup heater.
6. Treat hardware cost as open and say so: no published price for a water-coupled compute heater in a house; 356 USD per server is a data-centre figure. Make it the first question to DigitalHeat on Saturday, together with "who is paid for the heat?".
7. Do not quote the Vast.ai H100 host range as income without the words "vendor's claim".
