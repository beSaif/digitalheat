# Round 7: economics with a real seller form

Investigator for weak point 3 of round 7: "every payback rests on always-on rental rates or an assumed list share, with no buyer for heat-gated capacity" (Feasibility 25%; must-have 3 "electricity cost and computing income" and "a clear statement of when the model does not pay off"; open risks 2 and 11; founder objections 6, 7 and 8 of round 6). Written Sat 21 Nov 2026, about 11:40 to 12:30. This file plans and assesses. It builds no scheduler, dashboard or demo.

**Status labels** (as in `docs/overnight.md`): *sourced* = number read by me on the page at the URL given; *team-sourced* = from `reports/` or an earlier round with a URL I did not re-open this round; *computed* = printed by `analysis/r7_payback.py` (command below); *assumption* = our choice; *unverified* = estimate, or read only in a search snippet or a secondary report.

**Currency:** CHF. 1 USD = 0.8392 CHF, 1 GBP = 1.1015 CHF (ECB reference rates of 20 Nov 2026, *sourced* in rounds 1 and 6: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>; not re-opened this round). Electricity 0.3325 CHF/kWh, heat at price ÷ 2.5 (case).

**Tools:** WebSearch, WebFetch, curl (Exoscale page, its price API and the Heata SLA PDF; text extracted locally with `python3 -I` and `pdftotext`), local Python. **Firecrawl calls used: 0 of 6.** No personal or team names in any query.

**Files written this round**

| File | What |
|---|---|
| `analysis/r7_payback.py` | New. Stdlib only. Imports (does not edit) `r6_buyer_scenarios`, `r4_headline`, `r4_machine`, `r5_chain`, `r6_machine`. Runs the yearly loop for three buyer shapes (every permit hour, flat customer, July-sized flat) at N=6 and N=8 and prices them with one payback formula. About 7 s wall, 25 s CPU. Sets `sys.dont_write_bytecode` (checked: `analysis/__pycache__` unchanged). |
| this file | Findings |

Temporary files (scratchpad, not kept): `.../scratchpad/r7seller_dl/r7seller_exo.html`, `r7seller_exo_pricing.js`, `r7seller_exo_oc.json`, `r7seller_heata_sla.{pdf,txt}`, `.../scratchpad/r7seller_out.txt`.

---

## Bottom line

1. **A marketplace that accepts capacity which disappears does exist, and it pays spot prices.** SaladCloud runs on "GPUs that already exist in homes and small businesses"; even its top tier is "still subject to node disconnection; SCE reallocates automatically", and "Owners are paid for idle time" (no rate published). Its RTX 4090 price is 0.160 USD/h at the batch tier ("Lowest") against 0.440 at High, a ratio of **0.36** (*sourced*, salad.com/pricing). The always-on marketplace that the plan's rental anchors come from forbids exactly what a heat-gated host does: on Vast.ai "you cannot take the machine offline until every active rental contract has ended" (*sourced*). **No hyperscaler spot programme that accepts third-party capacity was found** (one search, not exhaustive).
2. **Compute-heating operators back their promises with cloud they pay for.** Heata's SLA: "To guarantee delivery of workloads we may use cloud instances (Cloud Burst Nodes) … This will be recorded"; Cloud Burst is also used "to deal with overcapacity on the network"; and Heata may run its own work on a client's idle allocated capacity "to … ensure reasonable hot water delivery" (*sourced*). The SLA gives no price for the burst, so who pays is our inference: the client pays the SLA price, Heata pays the cloud.
3. **Cloud fallback cost, sourced:** the same work in Swiss cloud costs about **4.9 CHF per reference server-hour** (Exoscale, 4 × RTX Pro 6000, 8.19 CHF/h, Swiss zone, excl. VAT, scaled by the round-6 critic's same-host MLPerf speed ratios 2.01× / 1.56×). On RunPod with the same card it is **2.53 CHF** (0.72 USD per GPU-h × 4.19). Both are above every income anchor a host gets (0.74–2.03 CHF), so **every refused-but-promised hour loses money.**
4. **Occupancy, sourced anchors only from one decentralised marketplace:** Akash reported a "60% average GPU utilization rate" for 2025 (*sourced*, its own blog); Messari put Akash at **33.7% (84 of 334 GPUs) in Q1 2026** (*sourced* from a secondary report, TokenPost, citing Messari's 15 May report; primary not opened). Heata's only published figure is a design floor ">50% on each node in any given month" from a 2024 hackathon (*sourced*), not a fleet figure. **No compute-heating fleet publishes occupancy.**
5. **One payback formula with every cost** (*computed*, `python3 analysis/r7_payback.py`, per server, N=6, 5-year life, central costs, heat credited): installed 35,429 CHF; fixed costs 984 CHF a year (maintenance + leak 225, card failures 205, insurance 354, uplink 200); at 60% occupancy a server sells 3,092 h a year. **Break-even price per sold server-hour: 2.84 CHF** (N=8: 3.09). At 100% occupancy 1.79 (1.94); at Akash's 33.7%, 4.87 (5.32). With the heat given to the host add about 0.10.
6. **Paybacks at the evidenced seller forms** (N=6, heat credited, occupancy 60%): spot at Salad's ratio **never within 50 years** (59.6 y); always-on host rates as an upper bound, **7.7–14.2 years**; committed flat delivery with Swiss fallback at RunPod's renter price **8.7 years**. The only line under 5 years with a sourced fallback uses RunPod as the fallback (US marketplace, regions unnamed), which breaks the Swiss-residency pitch; the only line under 3 years uses Heata's "from" list price, which is not a realised price.
7. **If GPU-hour prices fall 10% a year, the central line never pays back** (5% a year: 11.0 y instead of 7.7). Price decline is an *assumption*, but it dominates every other sensitivity, including the fixed-cost case (7.4–9.0 y).
8. **Decision:** the pitch should **not** present a payback. It presents the **price per sold server-hour needed** (with hardware, for a stated occupancy) next to the case's 0.2261 / 0.3325 and the **share of list price needed**, and compares it with two sourced market prices: what a GPU host gets today (1.35–2.03 CHF, always-on) and what Swiss cloud charges for the same work (about 4.9 CHF). Wording in section (c).
9. **Build scope: none.** One more text line on the printer or slide; the figures come from the analysis script, labelled.

---

## (a) Evidence: how heat-gated capacity can be sold

### A1. Seller forms that exist (all opened 21 Nov 2026 unless marked)

| Form | Who | What the page says | Fits a heat-gated house? | URL |
|---|---|---|---|---|
| Interruptible consumer capacity | SaladCloud | Community Cloud "runs on GPUs that already exist in homes and small businesses worldwide"; High tier "Never preempted by other workloads" but "Still subject to node disconnection; SCE reallocates automatically"; Medium/Low "May be preempted by higher-priority groups", "Minimum run before reallocation is roughly 30 minutes"; Lowest (Batch) "the most interruptible", for "retryable batch work and stateless inference behind a queue"; "Owners are paid for idle time" (no rate). Per GPU-hour, USD: RTX 4090 0.440 / 0.347 / 0.253 / 0.160; RTX 5090 0.600 / 0.483 / 0.367 / 0.250; RTX 3090 0.200 / 0.163 / 0.127 / 0.090. No professional GPU in tier pricing (RTX PRO 6000 only under "Salad Dedicated", quoted per term) | **Yes in form**: the node may leave, the platform reallocates. Price: Lowest/High = 0.36 (4090), 0.42 (5090). Owner pay unknown | <https://salad.com/pricing> |
| Always-on marketplace | Vast.ai | "The offer end date is your commitment to how long you will keep the machine online and fully functional"; "All rental contracts must be honored, you cannot take the machine offline until every active rental contract has ended"; "Restarting during an active rental does cost you reliability"; "Do not take your machine offline"; interruptibles are renter-side bids: "On demand rentals are the highest priority and if met will stop interruptibles" | **No**: the host cannot leave when the tank is full. Interruptible on Vast means the renter is outbid, not that the host leaves | <https://docs.vast.ai/host/hosting-overview> |
| Committed capacity + own cloud burst | Heata (UK) | "Where necessary the Heata Network can also call upon Cloud Burst Nodes to manage peaks in demand and to guarantee service"; "To guarantee delivery of workloads we may use cloud instances (Cloud Burst Nodes) in addition to our distributed Worker Nodes. This will be recorded and we can provide you with this information"; Cloud Burst = "when Heata uses compute capacity based in the cloud to guarantee delivery of workloads to meet the SLA or to deal with overcapacity on the network"; Heata "reserves the right to utilise" a client's idle allocated capacity "to maintain efficient utilisation of the network and ensure reasonable hot water delivery to the household(s)" | **Yes**, at the operator's cost. Burst price not stated; who pays is our inference | <https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf> (curl + `pdftotext`, lines 16–19, 184–201, 259–263) |
| Heata utilisation | Heata blog, 23 Feb 2024 | "we needed to maintain a minimum utilisation of >50% on each node in any given month"; "Heata sends workloads to the cylinders where heat is required"; no cloud fallback in the post | A design constraint in a hackathon, not a fleet occupancy | <https://www.heata.co/content-hub/data-centre-carbon-hackathon-microsoft-azure-centralised-vs-heata-distributed> |
| Hyperscaler spot | Google Spot VMs (round 6) | Google's own capacity, reclaimed with 0 or 120 s notice | No third-party supply route found | round 6 (*sourced* there) |
| Spot/aggregator markets that own no GPUs | SF Compute, Shadeform, Prime Intellect (search snippet only) | aggregate data-centre providers | Suppliers are data centres; *unverified*, not opened | — |

### A2. Occupancy of decentralised GPU fleets

| Figure | Value | Status | URL |
|---|---|---|---|
| Akash 2025, self-reported | "60% average GPU utilization rate"; "a consistent 60% utilization rate for accelerated compute"; "1,000+ GPUs deployed" (published 9 Jan 2026) | *sourced* (operator's own claim) | <https://akash.network/blog/akash-2025-year-in-review/> |
| Akash Q1 2026, Messari | "Average GPU usage dropped 57.4% to 84 units", "available GPU capacity fell 57.5% to 334", "utilization held steady at 33.7%" (article 22 May 2026, citing Messari's 15 May report) | *sourced* from the secondary article; Messari primary not opened | <https://tokenpost.com/news/technology/20776> |
| Heata planning | 80% utilisation in Heata's own cost assumption | *team-sourced* (`reports/Heata business model lessons.md`), not re-opened | — |
| Compute-heating fleets (Heata, Qarnot, Leafcloud, Deep Green) | no published occupancy found | absence after a short search | — |

The Messari figure (33.7%) and the operator's own (60%) bracket the central assumption of **60%**. Note that 84 GPUs in use is a tiny fleet.

### A3. Cloud fallback price (the operator buys the work elsewhere)

| Source | Price read | Per reference server-hour of work | Status |
|---|---|---|---|
| Exoscale, "GPU RTX Pro 6000 Instances": Small 1 GPU / 36 cores / 120 GB; Large 4 GPU / 144 cores / 480 GB; zones "DE-FRA-1, HR-ZAG-1, CH-DK-2, AT-VIE-2"; "All prices exclude any applicable tax"; GPU access only after "a manual screening process" | page table (prices are filled by script); the page's own price API `https://portal.exoscale.com/api/pricing/opencompute` returns `running_gpurtx6000pro_small` 2.15277778 and `running_gpurtx6000pro_large` 8.19444444 per hour | **4.88 CHF** (4-GPU instance), 5.13 (1-GPU) | *sourced* (<https://www.exoscale.com/pricing/>, and the API it calls, both read with curl) ; conversion *computed* |
| RunPod Secure Cloud RTX PRO 4500 SE, re-read this round | "0.72" USD per GPU-hour on-demand; Community Cloud blank; no spot price; regions: "Varies by region" | **2.53 CHF** (× 4.19 GPU-h × 0.8392) | *sourced* (<https://www.runpod.io/gpu-models/rtx-pro-4500-se>) |
| RTX PRO 6000 SE vs RTX PRO 4500 SE per GPU on the same Intel host | whisper 7,801.36 vs 3,878 tok/s → 2.01×; llama3.1-8b 14,860.7 vs 9,518.66 → 1.56× (MLPerf v6.1 6.1-0018 vs 6.1-0017) | 4.19 PRO 4500 GPU-h = 2.08 (J1) / 2.68 (J2) PRO 6000 GPU-h | *team-sourced*: read by the round-6 machine critic from `data/raw/mlperf_inference_v6.1_summary.xlsx`; I did not re-open the xlsx |
| Google Cloud GPU price page | page text truncated by the fetch tool | — | not read (no number) |

Caveats: (i) the Exoscale API returns **the same number under its `chf`, `eur` and `usd` keys**; I read it as CHF (the page lets the viewer pick CHF). If it were EUR or USD, the fallback would be 4.50 or 4.10 CHF (*computed* by hand, `python3 -c`). (ii) "CH-DK-2" is a Swiss zone by its prefix; the city is my reading. (iii) Exoscale is on-demand list; a committed contract could be cheaper. (iv) Exoscale excludes VAT, while our installed cost includes VAT (plan convention).

### A4. Insurance

No published rate for insuring electronics found. Opened: AXA's household electronics form gives premiums "CHF 90 – 130.-" to "CHF 280 – 400.-" by "Wie teuer ist Ihr teuerstes elektronisches Gerät", with no value brackets and for private households only (<https://www.axa.ch/de/formulare/offerte-elektrogeraeteversicherung.html>); a German founders' guide says yearly premiums "starten bei 110 Euro" with no rate (<https://www.fuer-gruender.de/wissen/unternehmen-gruenden/versicherung/elektronikversicherung/>). Insurers' own pages (Allianz, Zurich, in search snippets) say premiums are calculated individually. **Insurance is therefore an assumption: 1.0% of installed cost a year (0.5–2.0%).** Card failures are self-insured separately (round-6 critic: predicted MTBF 864,500 h, 1.01% a year, here applied in every year).

---

## (b) One payback line: formula, script and output

### The formula (per house-year; per server = ÷ N)

```
margin = p_c·V + p_s·o·S − e·(A + o·S) − c_f·(V − A) − K
payback = I / margin                      (simple, no interest, constant prices)
p*      = (I/L + K + e·(A + o·S) + c_f·(V − A)) / (V + o·S)   (one price for every sold hour; payback = life L)
```

| Symbol | Meaning | Value / source |
|---|---|---|
| V | committed flat volume a buyer expects delivered | 0 (F1); flat customer of the house's yearly volume, 29,949 / 34,981 server-h (F2); 15 server-h a day, 5,468 (F3) — *computed* |
| A | part of V the house runs (admission accepts it) | F2 20,952 / 23,612; F3 5,467 (all) — *computed* |
| V − A | committed work refused at intake → bought in cloud | F2 8,998 / 11,369 server-h (30% / 32%) — *computed* |
| S | heat-permitted hours left = P − A, P = every permit hour (30,925 / 36,242) | *computed*; approximation: committed and spot hours do not interact |
| o | occupancy of S by a spot buyer | 0.337 / 0.50 / **0.60** / 0.80 / 1.00 (*assumption*, anchored in A2) |
| p_c, p_s | income per sold server-hour | spot at Salad's ratio 0.74; host rates 1.35 / 2.03; direct sale at RunPod renter price 2.53; Heata "from" list 5.49 (A1, A3; round 6) |
| c_f | cloud fallback per server-hour of work | 2.53 (RunPod, same card) / **4.88** (Exoscale, Swiss) |
| e | operation per hour run in the house | 0.2261 heat credited (case formula) / 0.3325 heat to host (*computed*) |
| K | fixed per house-year: maintenance + leak 1,350 / 1,570 (one CDU loop, round-6 *assumption*; 3 h per box 3,132 / 4,106 as high case), card failures 1,228 / 1,637, insurance 1% of I 2,126 / 2,755, uplink 1,200 (r4 *assumption*) | 5,903 / 7,161 CHF (*computed*) |
| I, L | installed cost (r5 cold-plate chain, central) 212,574 / 275,474 CHF; life 5 or 8 years | round 5 (*computed*, estimate inputs) |

The three seller forms use the same formula: **F1 spot only** (Salad form: no promise, no fallback, paid only when rented), **F2 committed flat** (Heata form: promise flat delivery, buy the refused 30% in cloud, sell the winter surplus spot), **F3 committed floor** (promise only the July rate, which the house can always run, and sell the rest spot).

### Command and output

```
python3 analysis/r7_payback.py              # seeds 1-3 (means), about 7 s wall
python3 analysis/r7_payback.py --seeds 1    # seed 1 only (hours differ by < 1%)
python3 analysis/r7_payback.py --procs 1    # single process
```

Regression: "plan basis (o = 1.00, no K)" prints 3.8 y at N=6 and 4.2 y at N=8, which is round 6's `pool` / `rent072` payback (3.8 / 4.2, `r6_buyer_scenarios.py` section 2). Output of 2026-11-21, exit 0:

```
r7_payback.py. Currency CHF. 1 USD = 0.8392 CHF, 1 GBP = 1.1015 CHF (ECB 20 Nov 2026). Seeds [1, 2, 3] (means).
Policy r4_headline.HEADLINE (cap + 8 kWh band, EDF admission, archived ifs025 + 2 K guard). Simple payback,
no interest, constant prices unless marked. Installed cost: r5 cold-plate chain, central.

== 0. Inputs ==
  income  spot_salad   0.736 CHF per sold server-h   RunPod 0.72 USD x SaladCloud Lowest/High 0.364 x 80% host share (spot host, ASSUMPTION mix)
  income  host048      1.350 CHF per sold server-h   cheapest always-on listing 0.48 USD x 80%
  income  host072      2.025 CHF per sold server-h   RunPod Secure 0.72 USD x 80% (always-on host)
  income  direct072    2.531 CHF per sold server-h   direct sale at RunPod's renter price, operator keeps 100%
  income  heata_list   5.491 CHF per sold server-h   Heata Tier-2 'from' list surcharge, GPU only (list price)
  fallbk  runpod_same  2.531 CHF per server-h of work RunPod RTX PRO 4500, same card, renter price (regions unnamed)
  fallbk  exo_ch_4gpu  4.882 CHF per server-h of work Exoscale RTX Pro 6000 x4, Swiss zone, excl. VAT
  fallbk  exo_ch_1gpu  5.130 CHF per server-h of work Exoscale RTX Pro 6000 x1, Swiss zone, excl. VAT
  RTX PRO 6000 / 4500 per GPU, same host: J1 2.01x, J2 1.56x (MLPerf 6.1-0018 vs 6.1-0017)
  occupancy 0.337  Akash GPUs Q1 2026, 84 of 334 (Messari via TokenPost)
  occupancy 0.500  Heata's own hackathon floor '>50% on each node in any given month'
  occupancy 0.600  Akash 2025 year in review, self-reported average
  occupancy 0.800  Heata's planning assumption (team report, not re-opened)
  occupancy 1.000  plan so far: every permit hour sold
  card failures 1.01 % of cards a year (MTBF 864,500 h), every year; insurance 1.0 % of installed a year (ASSUMPTION, low 0.5 / high 2.0); uplink 1,200 CHF a year (ASSUMPTION)

== 1. Hours per house-year from the yearly loop (computed) ==
 N P permit h   flat V   flat A     V-A  July V  July A e heat cred e heat host
 6     30,925   29,949   20,952   8,998   5,468   5,467      0.2261      0.3325
 8     36,242   34,981   23,612  11,369   5,468   5,467      0.2261      0.3325
  P = every heat-permitted hour run ('pool'); flat = r6 flat customer (same yearly volume); July = 15 server-h a day.
  V = offered work, A = work run in the house (accepted); V-A = refused at intake (-> cloud in form F2).

== 2. Fixed costs per house-year and per server (CHF) ==
  N=6: installed 212,574 (35,429 per server); maintenance + leak 1,350 (3 h per box: 3,132); card failures 1,228; insurance 2,126; uplink 1,200; K = 5,903 a year (984 per server)
  N=8: installed 275,474 (34,434 per server); maintenance + leak 1,570 (3 h per box: 4,106); card failures 1,637; insurance 2,755; uplink 1,200; K = 7,161 a year (895 per server)

== 3. THE LINE, per server (house figures / N). Central: F1 spot only, occupancy 0.60, heat credited ==
  margin = p_c*V + p_s*o*S - e*(A + o*S) - c_f*(V - A) - K ;  payback = I / margin ;
  p* = (I/L + K + e*(A + o*S) + c_f*(V - A)) / (V + o*S)
  N=6 heat credited p= 0.74 (spot_salad) sold  3,092 h/server  income  2,277  op   699  K   984  margin    594 CHF/server-yr  I 35,429  payback   59.6 y   p*(5 y) 2.84  p*(8 y) 1.98
  N=6 heat credited p= 1.35 (host048   ) sold  3,092 h/server  income  4,175  op   699  K   984  margin  2,492 CHF/server-yr  I 35,429  payback   14.2 y   p*(5 y) 2.84  p*(8 y) 1.98
  N=6 heat credited p= 2.03 (host072   ) sold  3,092 h/server  income  6,263  op   699  K   984  margin  4,580 CHF/server-yr  I 35,429  payback    7.7 y   p*(5 y) 2.84  p*(8 y) 1.98
  N=6 heat to host  p= 0.74 (spot_salad) sold  3,092 h/server  income  2,277  op 1,028  K   984  margin    265 CHF/server-yr  I 35,429  payback  never y   p*(5 y) 2.94  p*(8 y) 2.08
  N=6 heat to host  p= 1.35 (host048   ) sold  3,092 h/server  income  4,175  op 1,028  K   984  margin  2,163 CHF/server-yr  I 35,429  payback   16.4 y   p*(5 y) 2.94  p*(8 y) 2.08
  N=6 heat to host  p= 2.03 (host072   ) sold  3,092 h/server  income  6,263  op 1,028  K   984  margin  4,251 CHF/server-yr  I 35,429  payback    8.3 y   p*(5 y) 2.94  p*(8 y) 2.08
  N=8 heat credited p= 0.74 (spot_salad) sold  2,718 h/server  income  2,002  op   615  K   895  margin    492 CHF/server-yr  I 34,434  payback   70.0 y   p*(5 y) 3.09  p*(8 y) 2.14
  N=8 heat credited p= 1.35 (host048   ) sold  2,718 h/server  income  3,670  op   615  K   895  margin  2,160 CHF/server-yr  I 34,434  payback   15.9 y   p*(5 y) 3.09  p*(8 y) 2.14
  N=8 heat credited p= 2.03 (host072   ) sold  2,718 h/server  income  5,505  op   615  K   895  margin  3,995 CHF/server-yr  I 34,434  payback    8.6 y   p*(5 y) 3.09  p*(8 y) 2.14
  N=8 heat to host  p= 0.74 (spot_salad) sold  2,718 h/server  income  2,002  op   904  K   895  margin    203 CHF/server-yr  I 34,434  payback  never y   p*(5 y) 3.20  p*(8 y) 2.25
  N=8 heat to host  p= 1.35 (host048   ) sold  2,718 h/server  income  3,670  op   904  K   895  margin  1,871 CHF/server-yr  I 34,434  payback   18.4 y   p*(5 y) 3.20  p*(8 y) 2.25
  N=8 heat to host  p= 2.03 (host072   ) sold  2,718 h/server  income  5,505  op   904  K   895  margin  3,706 CHF/server-yr  I 34,434  payback    9.3 y   p*(5 y) 3.20  p*(8 y) 2.25

== 4. Break-even price p* per sold server-hour (CHF; one price for every sold hour), central costs ==
  share of list = p* / US batch list value of one server-hour of work (14.25 CHF, r4_machine central)
form                               N conv                  o=0.34         o=0.50         o=0.60         o=0.80         o=1.00
  life 5 y:
  F1 spot only                     6 heat credited   4.87 (34.2%)   3.36 (23.6%)   2.84 (19.9%)   2.18 (15.3%)   1.79 (12.6%)
  F1 spot only                     6 heat to host    4.98 (34.9%)   3.46 (24.3%)   2.94 (20.6%)   2.29 (16.1%)   1.90 (13.3%)
  F1 spot only                     8 heat credited   5.32 (37.4%)   3.66 (25.7%)   3.09 (21.7%)   2.37 (16.7%)   1.94 (13.6%)
  F1 spot only                     8 heat to host    5.43 (38.1%)   3.77 (26.4%)   3.20 (22.4%)   2.48 (17.4%)   2.05 (14.4%)
  F2 flat + cloud fb runpod_same   6 heat credited   2.30 (16.2%)   2.21 (15.5%)   2.15 (15.1%)   2.05 (14.4%)   1.96 (13.7%)
  F2 flat + cloud fb runpod_same   6 heat to host    2.38 (16.7%)   2.28 (16.0%)   2.23 (15.7%)   2.13 (14.9%)   2.04 (14.3%)
  F2 flat + cloud fb runpod_same   8 heat credited   2.48 (17.4%)   2.37 (16.6%)   2.30 (16.2%)   2.19 (15.4%)   2.08 (14.6%)
  F2 flat + cloud fb runpod_same   8 heat to host    2.56 (17.9%)   2.45 (17.2%)   2.38 (16.7%)   2.27 (15.9%)   2.17 (15.2%)
  F2 flat + cloud fb exo_ch_4gpu   6 heat credited   2.94 (20.6%)   2.81 (19.7%)   2.74 (19.2%)   2.61 (18.3%)   2.49 (17.5%)
  F2 flat + cloud fb exo_ch_4gpu   6 heat to host    3.01 (21.2%)   2.89 (20.3%)   2.82 (19.8%)   2.69 (18.9%)   2.57 (18.0%)
  F2 flat + cloud fb exo_ch_4gpu   8 heat credited   3.16 (22.2%)   3.02 (21.2%)   2.93 (20.6%)   2.78 (19.5%)   2.65 (18.6%)
  F2 flat + cloud fb exo_ch_4gpu   8 heat to host    3.24 (22.7%)   3.09 (21.7%)   3.01 (21.1%)   2.86 (20.1%)   2.73 (19.1%)
  F3 July floor + spot             6 heat credited   3.67 (25.8%)   2.89 (20.3%)   2.56 (18.0%)   2.10 (14.7%)   1.79 (12.6%)
  F3 July floor + spot             6 heat to host    3.78 (26.5%)   2.99 (21.0%)   2.67 (18.7%)   2.21 (15.5%)   1.90 (13.3%)
  F3 July floor + spot             8 heat credited   4.16 (29.2%)   3.21 (22.5%)   2.83 (19.8%)   2.30 (16.1%)   1.94 (13.6%)
  F3 July floor + spot             8 heat to host    4.26 (29.9%)   3.32 (23.3%)   2.93 (20.6%)   2.40 (16.9%)   2.05 (14.4%)
  life 8 y:
  F1 spot only                     6 heat credited   3.34 (23.4%)   2.33 (16.3%)   1.98 (13.9%)   1.54 (10.8%)   1.28 ( 9.0%)
  F1 spot only                     6 heat to host    3.45 (24.2%)   2.43 (17.1%)   2.08 (14.6%)   1.65 (11.5%)   1.38 ( 9.7%)
  F1 spot only                     8 heat credited   3.63 (25.5%)   2.52 (17.7%)   2.14 (15.0%)   1.66 (11.7%)   1.37 ( 9.6%)
  F1 spot only                     8 heat to host    3.74 (26.2%)   2.63 (18.4%)   2.25 (15.8%)   1.77 (12.4%)   1.48 (10.4%)
  F2 flat + cloud fb runpod_same   6 heat credited   1.82 (12.8%)   1.75 (12.3%)   1.71 (12.0%)   1.63 (11.4%)   1.56 (10.9%)
  F2 flat + cloud fb runpod_same   6 heat to host    1.90 (13.3%)   1.83 (12.8%)   1.79 (12.5%)   1.71 (12.0%)   1.64 (11.5%)
  F2 flat + cloud fb runpod_same   8 heat credited   1.95 (13.7%)   1.87 (13.1%)   1.82 (12.8%)   1.73 (12.1%)   1.65 (11.6%)
  F2 flat + cloud fb runpod_same   8 heat to host    2.03 (14.2%)   1.95 (13.6%)   1.90 (13.3%)   1.81 (12.7%)   1.73 (12.1%)
  F2 flat + cloud fb exo_ch_4gpu   6 heat credited   2.46 (17.3%)   2.35 (16.5%)   2.30 (16.1%)   2.19 (15.3%)   2.09 (14.7%)
  F2 flat + cloud fb exo_ch_4gpu   6 heat to host    2.54 (17.8%)   2.43 (17.1%)   2.38 (16.7%)   2.27 (15.9%)   2.17 (15.2%)
  F2 flat + cloud fb exo_ch_4gpu   8 heat credited   2.64 (18.5%)   2.52 (17.6%)   2.45 (17.2%)   2.32 (16.3%)   2.21 (15.5%)
  F2 flat + cloud fb exo_ch_4gpu   8 heat to host    2.71 (19.0%)   2.59 (18.2%)   2.53 (17.7%)   2.40 (16.9%)   2.29 (16.1%)
  F3 July floor + spot             6 heat credited   2.54 (17.8%)   2.01 (14.1%)   1.79 (12.6%)   1.48 (10.4%)   1.28 ( 9.0%)
  F3 July floor + spot             6 heat to host    2.64 (18.6%)   2.12 (14.9%)   1.90 (13.3%)   1.59 (11.2%)   1.38 ( 9.7%)
  F3 July floor + spot             8 heat credited   2.85 (20.0%)   2.22 (15.6%)   1.96 (13.8%)   1.61 (11.3%)   1.37 ( 9.6%)
  F3 July floor + spot             8 heat to host    2.96 (20.8%)   2.33 (16.3%)   2.07 (14.5%)   1.71 (12.0%)   1.48 (10.4%)
  F2 o = occupancy of the winter surplus sold spot; the committed volume is always sold. F2 o=0 not shown:
    N=6 F2 runpod_same  surplus idle: p* 2.54 (5 y, heat credited); fallback 8,998 h = 30% of committed work
    N=6 F2 exo_ch_4gpu  surplus idle: p* 3.24 (5 y, heat credited); fallback 8,998 h = 30% of committed work
    N=8 F2 runpod_same  surplus idle: p* 2.76 (5 y, heat credited); fallback 11,369 h = 32% of committed work
    N=8 F2 exo_ch_4gpu  surplus idle: p* 3.52 (5 y, heat credited); fallback 11,369 h = 32% of committed work

== 5. Payback (years) at price anchors, central costs, life-independent ==
form / price                                 N conv           o=0.34  o=0.50  o=0.60  o=0.80  o=1.00
  F1 spot @ spot_salad                       6 heat credited   never   never    59.6    31.6    21.5
  F1 spot @ spot_salad                       6 heat to host    never   never   never    52.0    32.3
  F1 spot @ spot_salad                       8 heat credited   never   never    70.0    36.1    24.3
  F1 spot @ spot_salad                       8 heat to host    never   never   never    60.5    36.8
  F1 spot @ host048                          6 heat credited    36.6    18.5    14.2     9.7     7.4
  F1 spot @ host048                          6 heat to host     45.2    21.6    16.4    11.0     8.3
  F1 spot @ host048                          8 heat credited    41.9    20.9    15.9    10.8     8.2
  F1 spot @ host048                          8 heat to host     52.3    24.4    18.4    12.3     9.3
  F1 spot @ host072                          6 heat credited    16.5     9.7     7.7     5.5     4.3
  F1 spot @ host072                          6 heat to host     18.1    10.5     8.3     5.9     4.6
  F1 spot @ host072                          8 heat credited    18.6    10.8     8.6     6.1     4.7
  F1 spot @ host072                          8 heat to host     20.4    11.7     9.3     6.6     5.1
  F2 commit direct072, fb runpod, spot salad 6 heat credited     4.8     4.7     4.7     4.6     4.5
  F2 commit direct072, fb runpod, spot salad 6 heat to host      5.1     5.0     5.0     4.9     4.8
  F2 commit direct072, fb runpod, spot salad 8 heat credited     5.6     5.5     5.4     5.3     5.1
  F2 commit direct072, fb runpod, spot salad 8 heat to host      5.9     5.8     5.8     5.6     5.5
  F2 commit direct072, fb exo_ch, spot salad 6 heat credited     9.3     8.9     8.7     8.4     8.1
  F2 commit direct072, fb exo_ch, spot salad 6 heat to host     10.4    10.1     9.9     9.6     9.2
  F2 commit direct072, fb exo_ch, spot salad 8 heat credited    12.1    11.6    11.3    10.7    10.2
  F2 commit direct072, fb exo_ch, spot salad 8 heat to host     13.9    13.4    13.1    12.5    11.9
  F2 commit heata_list, fb exo_ch, spot salad 6 heat credited     1.9     1.9     1.9     1.9     1.8
  F2 commit heata_list, fb exo_ch, spot salad 6 heat to host      1.9     1.9     1.9     1.9     1.9
  F2 commit heata_list, fb exo_ch, spot salad 8 heat credited     2.2     2.2     2.2     2.1     2.1
  F2 commit heata_list, fb exo_ch, spot salad 8 heat to host      2.2     2.2     2.2     2.2     2.2
  F3 floor direct072 + spot host048          6 heat credited    13.0    10.1     8.9     7.2     6.0
  F3 floor direct072 + spot host048          6 heat to host     14.3    11.1     9.8     7.9     6.6
  F3 floor direct072 + spot host048          8 heat credited    16.1    12.1    10.5     8.3     6.9
  F3 floor direct072 + spot host048          8 heat to host     17.9    13.4    11.6     9.2     7.6
  F3 floor direct072 + spot salad            6 heat credited    19.2    16.1    14.7    12.4    10.8
  F3 floor direct072 + spot salad            6 heat to host     22.2    18.9    17.3    14.8    13.0
  F3 floor direct072 + spot salad            8 heat credited    25.7    20.7    18.5    15.3    13.0
  F3 floor direct072 + spot salad            8 heat to host     30.4    24.9    22.4    18.6    15.9

== 6. Sensitivity of the central line (F1, o = 0.60, p = host072 2.03, heat credited) ==
  N=6 fixed-cost case low      K   4,840/house-yr  payback    7.4 y  p*(5 y) 2.78
  N=6 fixed-cost case central  K   5,903/house-yr  payback    7.7 y  p*(5 y) 2.84
  N=6 fixed-cost case high     K   9,811/house-yr  payback    9.0 y  p*(5 y) 3.05
  N=6 income falling 5 % a year (ASSUMPTION): payback   11.0 y (constant prices    7.7 y)
  N=6 income falling 10 % a year (ASSUMPTION): payback  never y (constant prices    7.7 y)
  N=6 income falling 20 % a year (ASSUMPTION): payback  never y (constant prices    7.7 y)
  N=6 plan basis (o = 1.00, no K): payback    3.8 y; with K    4.3 y
  N=8 fixed-cost case low      K   5,784/house-yr  payback    8.3 y  p*(5 y) 3.03
  N=8 fixed-cost case central  K   7,161/house-yr  payback    8.6 y  p*(5 y) 3.09
  N=8 fixed-cost case high     K  12,453/house-yr  payback   10.3 y  p*(5 y) 3.33
  N=8 income falling 5 % a year (ASSUMPTION): payback   13.4 y (constant prices    8.6 y)
  N=8 income falling 10 % a year (ASSUMPTION): payback  never y (constant prices    8.6 y)
  N=8 income falling 20 % a year (ASSUMPTION): payback  never y (constant prices    8.6 y)
  N=8 plan basis (o = 1.00, no K): payback    4.2 y; with K    4.7 y

  Reading: payback = I / margin; any 'never' means margin <= 0 or > 99 years. Prices are snapshots of 21 Nov 2026.
```

### Reading

- **Occupancy decides everything in the spot form.** The fixed part (I/L + K = 8,070 CHF per server-year at N=6, 5 y) is spread over the hours actually sold. p* falls from 4.87 at 33.7% to 1.79 at 100% (N=6). The plan has so far shown only the 100% end.
- **The fallback decides the committed form.** F2 is insensitive to spot occupancy (2.49–2.94 at N=6 with Swiss fallback) because 30% of every promised hour is bought at 4.88. With the house's own winter surplus idle, F2 needs 3.24 (Swiss fallback) or 2.54 (RunPod).
- **F3 (promise only the July floor)** has no fallback and is only slightly better than F1 (2.56 vs 2.84 at 60%), because the floor is just 5,468 of 30,925 permit hours.
- **Per server is the same as per house**: payback and p* do not depend on dividing by N. N=8 is worse by about 0.15–0.45 CHF per hour because its extra permit hours are fewer per server.
- **Heat convention adds about 0.10 CHF per sold hour** (0.3325 − 0.2261 = 0.1064 per hour run in the house) and about 1–2 years of payback where margins are thin.
- **Where 4–5 years appears** it needs either 100% occupancy at the RunPod host rate (4.3 y) or a committed buyer paying RunPod's renter price with RunPod as fallback (4.7 y). Neither has a buyer, and the second puts Swiss customers' work on a US marketplace.
- **Price decline**: at 5% a year the central line goes from 7.7 to 11.0 years; at 10% it never pays back, because the yearly margin turns negative before the hardware is paid.

---

## (c) Should the pitch show a payback? Decision and wording

**Decision: no payback in the pitch. The economic result is the price per sold server-hour needed (with hardware, at a stated occupancy) and the share of list price that is, beside the case's break-even 0.2261 / 0.3325 CHF.** Paybacks stay in this file and the backup slide only.

Reasons a sceptical founder would accept:

1. **A payback needs two numbers nobody has measured: the price DigitalHeat would realise and the share of heat-permitted hours a buyer takes.** Across the sourced ranges the same machine pays back in 4.3 years or never (section 5). Picking one figure would be a choice, not a result. The break-even price needs only one of the two.
2. **The prices that give short paybacks belong to a seller form the house cannot use.** Always-on rental requires the host to stay online for the whole contract (Vast.ai). The marketplace that tolerates a node leaving (SaladCloud) prices its batch tier at about a third of its top tier, and at that ratio the servers never pay back.
3. **Promising delivery moves the problem to the cloud bill.** A flat buyer needs 30% of its work run elsewhere; Swiss cloud for that work costs about 4.9 CHF per server-hour, more than any income anchor, so every such hour loses money.
4. **The case asks for a break-even computing price, not a payback.** "Price needed incl. hardware" is the same quantity with installed cost, maintenance, failures and insurance added. The jury can check it against any price list, and the founder can check it against their own.
5. **It turns the missing buyer into a target with a window.** At 60% occupancy a sold server-hour must fetch about 2.8 CHF. That sits between what GPU hosts get today (1.35–2.03 CHF, always-on) and what Swiss cloud charges for the same work (about 4.9 CHF). DigitalHeat's question then becomes: can heat-gated Swiss capacity be sold inside that window? That is a decision a pilot can test.
6. **Feasibility (25%) rewards knowing where assumptions stop holding.** A payback presented as a result would contradict the plan's own "no buyer for heat-gated hours was found".

**Pitch wording (two sentences):**

> "To pay for electricity, maintenance, insurance and the servers themselves within five years, every server-hour DigitalHeat sells must bring in about 2.80 francs if buyers take 60% of the hours the heat allows, or 1.80 francs if they take all of them; that is 13–20% of what the same work costs at public batch prices. GPU hosts get 1.35 to 2.03 francs for an always-on hour today and Swiss cloud charges about 4.90 for the same work, so the model works only if heat-gated Swiss capacity can be sold between those two prices, and we have not found that buyer yet."

**"Does not pay off when …" statement (for the README and the closing slide):**

> "The model does not pay off when a sold server-hour brings in less than 0.23 francs, which covers only electricity minus the heat's value (0.33 if the homeowner keeps the heat). The servers do not pay back in five years when a sold server-hour brings in less than about 2.80 francs at 60% occupancy of heat-permitted hours (1.80 at 100%, 4.90 at the 34% one public GPU marketplace reported for early 2026), when DigitalHeat promises flat delivery and must buy the refused 30% from Swiss cloud and sells below about 2.70 francs, or when GPU-hour prices fall by 10% a year or more."

Sources for each number: 0.2261 / 0.3325 (`r2_fleet_economics.py`, plan); 2.84 / 1.79 / 4.87 and 2.74 (F2, Swiss fallback, o = 0.6) and the 10% decline, `python3 analysis/r7_payback.py` sections 4 and 6; 13–20% = p* ÷ 14.25 CHF list value (`r4_machine.py` central); 1.35 / 2.03 / 4.88 (A3, round 6); 34% (A2). Round "about 2.80" etc. for speech; slides show 2.84 with the label "analysis script, N=6, 5 years, central costs, heat credited".

**Q&A answers this enables** (round-6 founder objections):
- *6 "Who signs for heat-gated hours at always-on prices?"* "Nobody, and we don't assume it. Always-on marketplaces forbid a host from leaving mid-rental; the one that tolerates it, SaladCloud, prices its batch tier at about a third of its top tier. That is why we show the price we need, not a payback."
- *7 "What does the July cloud fallback cost?"* "About 4.9 francs per server-hour in Swiss cloud (Exoscale, RTX Pro 6000), 2.5 on RunPod with the same card. If DigitalHeat promised a flat volume, about 30% of it would run there, and every promised hour would have to fetch about 2.7 francs (Swiss fallback) or 2.2 (RunPod). At 50–60% marketplace occupancy without promises it is 2.8–3.4."
- *8 "Who pays insurance, uplink, maintenance, card failures?"* "They are in the price needed: about 984 francs per server a year (maintenance and leak reserve 225, card failures 205, insurance 354 at 1% a year — an assumption, uplink 200)."

---

## Proposed changes to the plan

1. **Read this first, line 9, and "Computing income":** drop "If heat-gated hours sold at today's always-on GPU-rental host rates, the hardware would pay back in about 4–7 years" and "below about 1.8 CHF per sold server-hour it does not pay back in five". Replace with: "Price per sold server-hour needed incl. hardware, maintenance, card failures, insurance and uplink (5 y, N=6, central): 2.84 CHF at 60% occupancy of heat-permitted hours, 1.79 at 100%, 4.87 at 34%; N=8 3.09 / 1.94 / 5.32; +0.10 with the heat to the host (*computed*, `python3 analysis/r7_payback.py` section 4)." Keep the share of list beside it (19.9% / 12.6% at 60% / 100%).
2. **Pitch wording and buyer framing:** use the two sentences in section (c). No payback figure in the spoken pitch or on a main slide. Section 5 of the script goes to the backup slide with the label "scenarios; no buyer found".
3. **Q&A 1:** replace the rental-anchor payback sentence with the Q&A 6/7/8 answers above. Keep "no buyer for heat-gated capacity at these rates was found".
4. **"When the model does not pay off":** replace the hardware bullet with the statement in section (c), incl. occupancy, the committed-with-fallback case (2.74 Swiss / 2.15 RunPod at o = 0.6) and the 10%-a-year price decline.
5. **Open risk 2:** "Occupancy is not modelled" → "Occupancy is a stated assumption (60%; sourced anchors 33.7% and 60% from one decentralised GPU marketplace; no compute-heating fleet publishes one)". "The cloud fallback … is not costed" → "costed: Exoscale Swiss 4.88 CHF, RunPod 2.53 CHF per server-hour of work; a promised flat volume sends 30% / 32% there". Add: "Vast.ai forbids taking a machine offline during a rental; SaladCloud tolerates node disconnection at spot prices (Lowest/High 0.36); owner pay unpublished."
6. **Open risk 3:** "Insurance, theft, internet uplink … not costed" → "insurance 1% of installed a year and uplink 1,200 CHF a year are costed as assumptions (no published rate found); theft, consent and data protection still not costed".
7. **DigitalHeat question 3, sharpened:** "Would you sell (a) spot capacity that may leave when the house is warm, (b) a promised volume with your own cloud fallback (Swiss? at what price?), or (c) a promised summer floor plus spot? What occupancy do you plan with?"
8. **Retire round 6's rental-anchor numbers (4.1–6.6 y, 1.35–2.03 → payback) as a result.** Keep 1.35–2.03 CHF only as "what a GPU host receives today for an always-on hour".
9. **Build scope: none.** Optional one line on the printer or slide 1 under tile 6: "with hardware: about 2.84 CHF per sold server-hour at 60% occupancy (analysis script)".

## Weak points of this work

- The Salad ratio is for RTX 4090 consumer cards on SaladCloud, applied to RunPod's RTX PRO 4500 price with an 80% host share (round-2 source, not re-opened); Salad's owner pay is unpublished, so the spot income may be lower.
- Occupancy anchors come from one decentralised marketplace (Akash, small fleet); the Messari figure was read in a secondary article.
- The F2 / F3 surplus approximation (S = P − A) ignores that committed and spot hours compete within the same permit hours; the error is small for F3 and moderate for F2 at high occupancy.
- The fallback uses the round-6 critic's same-host MLPerf ratios (not re-opened by me) and Exoscale on-demand list; the API returns one number under three currency keys.
- Insurance and uplink are assumptions; maintenance is round 6's assumption (one CDU loop); card failures use a predicted MTBF in every year.
- No interest; constant prices except the decline sensitivity; renter-controlled draw (a rented but idle GPU makes less heat) is not modelled; no VAT harmonisation between installed cost (incl. VAT) and the Exoscale price (excl. VAT).
- Installed cost (212,574 CHF at N=6) remains a round-5 estimate.

## Commands and pages

```
python3 analysis/r7_payback.py                      # full output above
python3 analysis/r7_payback.py --seeds 1            # seed-1 check: P 30,879 / 36,208, flat V-A 8,856 / 11,346
curl -sL -A "Mozilla/5.0" https://www.exoscale.com/pricing/                       # table, zones, GPU counts
curl -sL -A "Mozilla/5.0" https://portal.exoscale.com/api/pricing/opencompute     # running_gpurtx6000pro_* prices
curl -sL -A "Mozilla/5.0" "https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf"; pdftotext -layout
python3 -c "...8.19444444/4*(4.19/2.0116*0.5+4.19/1.5612*0.5)*0.9223..."         # EUR / USD readings: 4.50 / 4.10
# WebFetch (opened): salad.com/pricing; docs.vast.ai/host/hosting-overview; akash.network/blog/akash-2025-year-in-review/;
#   tokenpost.com/news/technology/20776; runpod.io/gpu-models/rtx-pro-4500-se; heata.co/content-hub/data-centre-carbon-
#   hackathon-microsoft-azure-centralised-vs-heata-distributed; axa.ch/de/formulare/offerte-elektrogeraeteversicherung.html;
#   fuer-gruender.de/.../elektronikversicherung/
# Tried, no number: cloud.google.com/compute/gpus-pricing (truncated); mexc.com/news/1127237 (HTTP 410)
```
