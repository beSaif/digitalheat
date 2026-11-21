# Round 8: heat-gated hours versus seller reality

Investigator for round-8 weak point 3: "heat-gated hours versus seller reality: refuse vs dump, renter-controlled draw, interruptible discount" (Feasibility 25%; must-have 3 "computing income" and "when the model does not pay off"; core idea "heat is the admission ticket"; open risk 2; round-7 founder objections 10–12). Written Sat 21 Nov 2026, about 12:20 to 13:20. This file plans and assesses. It builds no scheduler, dashboard or demo, and changes no existing file.

**Status labels** (as in `docs/overnight.md`): *sourced* = number read by me on the page at the URL given; *team-sourced* = from `reports/` or an earlier round, URL not re-opened by me; *computed* = printed by `analysis/r8_draw.py` (command below) or by a one-line `python3 -c` given here; *assumption* = our choice; *unverified* = estimate, search snippet, or attribution I could not check.

**Currency:** CHF. 1 USD = 0.8392 CHF (ECB reference rates of 20 Nov 2026, *team-sourced*: rounds 1 and 6, <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>, not re-opened this round). All interruptible prices below were read in USD. Electricity 0.3325 CHF/kWh, heat valued at price ÷ 2.5 (case).

**Tools:** WebSearch, WebFetch, curl (Azure Retail Prices API, Google GPU pricing page, AWS spot feed, the Alibaba NSDI'22 PDF), `pdftotext`, local Python (`python3 -I` for downloaded data). **Firecrawl calls used: 1 of 5** (one scrape of Google's Spot VM pricing page; it failed with "insufficient credits", no data). No personal, team or repo names in any query.

**Files written this round**

| File | What |
|---|---|
| `analysis/r8_draw.py` | New. Stdlib only. Imports (does not edit) `baseline_sweep`, `r2_deadline_sim`, `r3_policy_check`, `r4_headline`, `r7_payback`. Sets three module attributes at run time in its own process (`r3_policy_check.Q1`, `r4_headline.Q1`, `r4_headline.P_EL`) and wraps `r4_headline.rates_for`, to run the headline loop at a wall draw of d × rated power. 48 yearly runs, about 27 s wall (112 s CPU). Sets `sys.dont_write_bytecode` (checked: `analysis/__pycache__` still 11 files). |
| this file | Findings |

Temporary files (scratchpad, not kept): `.../scratchpad/r8draw_dl/` (`r8draw_polca.pdf/.txt`, `r8draw_weng.pdf/.txt`, `r8draw_gcp_gpu.html/.txt`, `r8draw_aws_spot.js`, `r8draw_az_nc.json`, `r8draw_vast_bid.json`), `.../scratchpad/r8draw_out_*.txt`.

---

## Bottom line

1. **A rented GPU's draw is a heat problem, not an income problem.** At 70% of rated wall power the house gets 30% less heat per server-hour. Under the headline contract (sized in server-hours) coverage falls from **73.2% to 52.4% (N=6)** and from **85.7% to 61.7% (N=8)**; at 50% draw to 37.4% / 44.1% (*computed*). The price needed per sold server-hour moves the other way, slightly: at 60% occupancy it falls from **2.84 to 2.60 CHF (N=6)** and **3.09 to 2.62 (N=8)** at 70% draw, because each hour uses less electricity and the house can host more server-hours per kWh of heat (*computed*). Per kWh at the wall it rises (2.84 → 3.72 CHF at N=6).
2. **What real inference draws, sourced:** saturating offline batch work sits near the rating (Whisper-large-v3-turbo on a 72 W L4: 64.9–72.3 W, i.e. 90–100%); a single interactive request leaves an H100 near 43% of TDP and a large batch near 86% (secondary source); Microsoft's production inference cluster peaks at 79% of provisioned power against 97% for training; a DGX-A100 rated 6,500 W never exceeded 5,700 W (87.7%) across Microsoft's LLM workloads; decode phases run "with almost no latency impact" under a 50% power cap. **J1/J2, which DigitalHeat runs itself as offline batch, sit at the top of that range; a renter's workload can sit anywhere.** In the case's own Alibaba trace, the median task requested 0.5 GPU and used 0.042 GPU of SM capacity (utilisation, not power).
3. **The scheduler must count permits in kWh of heat, not server-hours.** The current band rule recomputes permits every hour from the metered tank, so a renter drawing *less* than assumed is safe: less heat, no dump, no extra misses (naive and kWh permits print the same within 0.1 points, *computed*). The dangerous direction is the opposite: if permits are sized for an assumed 50–70% draw and the renter runs at full power, execution dumps **73–471 kWh (N=6)** and **918–1,523 kWh (N=8)** a year and the "0 kWh dumped" tile breaks (*computed*). Rule: permit kWh = demand forecast + free tank; servers = permit kWh ÷ (0.8 × metered draw); enforce with a GPU power cap. **Build scope: none for the hackathon** (the case's 1 kW per running server keeps d = 1); one line in the assumptions list and one Q&A answer.
4. **Interruptible GPU capacity sells at 18–41% of on-demand** at the providers I opened: Azure Switzerland North, RTX PRO 6000 Blackwell Server Edition VMs, spot/on-demand **0.185** for every 1- and 2-GPU size (*sourced*, Azure's own price API); Google RTX PRO 6000 (g4-standard-48) **0.382** (us-central1) and **0.414** (europe-west4), L4 in Zurich 0.599 (*sourced* from a third-party aggregator of Google prices, labelled); SaladCloud's batch tier is **0.364** of its top tier (*sourced*; tiers, not spot vs on-demand).
5. **Does the house pay off at any sourced interruptible price?** Applied to the cheapest on-demand price for the same work (RunPod, 2.53 CHF per reference server-hour), interruptible is worth **0.47–1.05 CHF**, below every price needed in the grid (lowest 1.56). Applied to Swiss on-demand (Exoscale, 4.88), **0.90–2.02 CHF**: it clears only at 100% occupancy (1.57–1.95 needed). Only hyperscaler spot **list** prices for the same work in their own bundled VMs clear 2.84 CHF: Azure Switzerland North **2.91** (and 3.37 on the larger-RAM size), Google **3.44** (Iowa) / **4.10** (Netherlands) (*computed* from *sourced* prices and the team-sourced MLPerf speed ratios). Those buyers can rent the same work **uninterrupted for 2.53 CHF**. So: **no, not against any buyer who shops on price.** Through a marketplace taking 20%, only Google's Netherlands spot (4.10 × 0.8 = 3.28) clears 2.84.
6. **Refuse, not dump (positioning sentence, section c):** "When the house has no room for heat, the job is refused at the door, not run and its heat thrown away; the January-to-July swing is carried upstream by the aggregator, which sends refused work to cloud capacity it pays for or to a partner site that needs heat all year." The cheapest flat-volume option of round 7 (run the refused 30% in the basement and dump the heat, about 1.60 CHF needed) is therefore **excluded**, not offered as an option: it contradicts the idea and the jury's first scheduling criterion.

---

## (a) Renter-controlled draw

### A1. What GPUs draw during real inference (all opened 21 Nov 2026)

| # | Source | What it says | Share of rating | Status | URL |
|---|---|---|---|---|---|
| 1 | Patel et al., "Characterizing Power Management Opportunities for LLMs in the Cloud" (POLCA), ASPLOS '24, Microsoft Azure | Table 4, "LLM cluster power usage in production": peak power utilisation **Training 97%, Inference 79%** (of provisioned row power; interactive inference cluster). "the rated power for the DGXA100 machine is 6500W [44]. Yet, across all our workloads, the peak power on our machine never exceeded 5700W." Insight 4: "prompt phases are brief and typically reach or exceed GPU TDP, whereas token phases are longer and draw less power." "GPU power constitutes on average 60% of server-level power consumption" | 79% (row peak, inference); 87.7% (DGX-A100 peak / rated, *computed*: 5700/6500) | *sourced* (PDF text via `pdftotext`) | <https://par.nsf.gov/servlets/purl/10505206> |
| 2 | Patel et al., "Splitwise", ISCA 2024 | "the token generation phase incurs almost no latency impact when power capping by over 50% (i.e., 700 to 350W)"; Splitwise-HHcap caps token machines at 70% of rated machine power, each GPU at 50% | decode tolerates a 50% cap | *sourced* | <https://arxiv.org/html/2311.18677v2> |
| 3 | "The 1/W Law" (arXiv 2603.17280, March 2026) | "a GPU serving a single request idles near 43% of its thermal design power (TDP)", "the same GPU running a large batch approaches 86% TDP"; attributed to Chung et al. 2026 (arXiv 2601.22076), tied elsewhere in the paper to H100-SXM5 | 43% (one request), 86% (large batch) | *sourced* on this secondary page; **attribution unverified**: the primary's HTML text (<https://arxiv.org/html/2601.22076v2>) shows power only as a figure axis ("% of GPU TDP"), with no number in the text | <https://arxiv.org/html/2603.17280v1> |
| 4 | E2E Networks blog, 27 Mar 2026, ASR on NVIDIA L4 ("a 72W data-centre efficiency card") | "Avg Power" = "Mean watts during inference run": Whisper-large-v3-turbo fp16 bs 1 **68.6 W**, bs 4 70.3 W, bs 8 68.1 W, bf16 64.9–65.2 W, highest 72.3 W; INT8 bs 1 **50.9 W**; Parakeet-TDT-0.6b 39.0–50.9 W | Whisper fp16/bf16 90–100%; INT8 71%; Parakeet 54–71% (*computed*: W ÷ 72) | *sourced* (vendor blog, one card, method not audited) | <https://e2enetworks.com/blog/benchmarking-asr-models-nvidia-l4-parakeet-whisper-nemotron> |
| 5 | Weng et al., "MLaaS in the Wild", NSDI '22 (the Alibaba GPU trace 2020 the case links) | "the median usage of streaming multiprocessors (SMs) of an instance is 0.042 GPUs"; median request "6 vCPU cores, 0.5 GPUs, and 29 GiB memory" | SM utilisation, **not power**: shows renters use far less than they reserve; an idle reserved GPU still draws idle power | *sourced* (PDF via curl + `pdftotext`) | <https://cse.hkust.edu.hk/~weiwa/papers/weng-nsdi22.pdf> |
| 6 | Repo: MLPerf v5.1 power runs, 8 × B200 | whisper Offline 7,636 W (SR680a V3, air) vs llama3.1-8b Offline 9,436 W (SR780a V3, water) | not a draw share (two different chassis and cooling) | *team-sourced* (`analysis/r3_mlperf_power.py` stored values) | — |
| 7 | Samsi et al., "From Words to Watts" (2023) | A100s capped at 250 / 175 / 150 W; "For a 30% reduction in power from 250W to 175W, the inference time increases by an average of 6.7%" | shows a cap trade-off, not a free-running share | *sourced* | <https://arxiv.org/html/2310.03003v1> |

Tried, no usable number: Tom's Hardware Whisper GPU benchmark (article body truncated by the fetch tool); POLCA on the author's UW page (HTTP 404; the NSF copy was used).

**Reading.** Work that DigitalHeat schedules itself as offline batch (J1 transcription, J2 batch LLM generation) runs near the rating: 86–100% (rows 3 and 4; MLPerf Offline is that regime). A rented GPU runs whatever the renter runs: an interactive endpoint with one request in flight sits near 43%, a reserved but idle GPU lower still (rows 3 and 5; idle level for our card not sourced). The grid 90 / 70 / 50% brackets a busy batch renter, a typical serving renter and a mostly idle renter. It is a grid, not a measured distribution (*assumption*).

### A2. Model

One server-hour at draw d uses d kWh and delivers 0.8·d kWh of heat (case: 1 kW, 80% recovered). Job runtimes stay in server-hours (the renter's hours; a lower draw does not shorten them). Every run uses the round-4 headline loop `r4_headline.run` with policy HEADLINE (cap + 8 kWh band, EDF admission dry run, archived ECMWF ifs025 + 2 K guard), seed 1, the plan's convention for scheduler-comparable figures.

| Variant | Permit count assumes | Tank physics and electricity | Contract |
|---|---|---|---|
| `naive` | 0.8 kWh per server-hour (server-hour permits) | real draw d | headline `shaped100` in server-hours |
| `kwh` | 0.8·d kWh per server-hour (kWh permits at the real draw) | real draw d | headline in server-hours (`h`) or resized ×1/d (`kwh`) |
| `under:x` | 0.8·x (draw assumed lower than real) | real draw 1.0 | headline in server-hours |
| unlimited | as `naive` / `kwh` | real d | every permit hour offered (round-7 F1 spot form) |

p* = (installed/5 + fixed costs + (electricity − heat value)·o·S) / (o·S), the round-7 F1 formula with S = sold server-hours of the run, central costs from `r7_payback.fixed_costs` (installed 212,574 / 275,474 CHF, K 5,903 / 7,161 CHF a year), no interest, heat credited.

### A3. Command and output

```
python3 analysis/r8_draw.py              # seed 1, about 27 s wall on all cores
python3 analysis/r8_draw.py --seeds 3    # seeds 1-3 (means); not run for this file
python3 analysis/r8_draw.py --procs 1    # single process
```

Regression: at d = 1.00 the script reprints the plan's seed-1 HEADLINE values exactly (73.20% / 85.73%, utilisation 54.37% / 47.76%, 0 of 31,908 / 0 of 36,771, break-even 0.2261), and the unlimited rows reprint round 7's F1 p* (2.84 / 1.79 at N=6; 3.09 / 1.95 at N=8; round 7 printed 1.94 as a 3-seed mean). Output of 2026-11-21, exit 0:

```
r8_draw.py. Currency CHF; 1 USD = 0.8392 CHF (ECB 20 Nov 2026, not re-opened). Seeds [1].
Loop: r4_headline.run, policy HEADLINE (cap + 8 kWh band, EDF dry run, archived ifs025 + 2 K guard).
Installed cost and fixed costs: r7_payback.fixed_costs (central). p* = price per sold server-hour needed,
5 y, no interest, heat credited unless marked. Draw d = wall power as share of rated (1 kW per server).

== 0. Regression at d = 1.00 (must equal the plan's seed-1 HEADLINE values) ==
  N=6 shaped100 coverage 73.20% (naive variant 73.20%), util 54.37%, missed 0 of 31,908, BE 0.2261
  N=8 shaped100 coverage 85.73% (naive variant 85.73%), util 47.76%, missed 0 of 36,771, BE 0.2261
  plan, seed 1, archived ECMWF + 2 K: 73.20% / 85.73%, util 54.37% / 47.76%, 0 of 31,908 / 0 of 36,771

== 1. Unlimited demand (every permit hour offered = round-7 F1 spot form); naive vs kWh permits ==
 N     d permits   cover heat MWh   srv-h   util sh/kWh op BE/sh  p* o=.6  p* o=1 p* .6 host p*/kWh .6 cov o=.6
 6  1.00 naive    79.10%    24.70  30,879  58.8%   1.25   0.2261     2.84    1.79       2.95      2.84    47.5%
 6  1.00 kwh      79.10%    24.70  30,879  58.8%   1.25   0.2261     2.84    1.79       2.95      2.84    47.5%
 6  0.90 naive    73.54%    22.97  31,897  60.7%   1.39   0.2035     2.73    1.72       2.83      3.04    44.1%
 6  0.90 kwh      73.55%    22.97  31,901  60.7%   1.39   0.2035     2.73    1.72       2.83      3.04    44.1%
 6  0.70 naive    59.21%    18.49  33,022  62.8%   1.79   0.1583     2.60    1.62       2.68      3.72    35.5%
 6  0.70 kwh      59.21%    18.49  33,022  62.8%   1.79   0.1583     2.60    1.62       2.68      3.72    35.5%
 6  0.50 naive    42.64%    13.32  33,294  63.3%   2.50   0.1131     2.54    1.57       2.59      5.07    25.6%
 6  0.50 kwh      42.64%    13.32  33,294  63.3%   2.50   0.1131     2.54    1.57       2.59      5.07    25.6%
 8  1.00 naive    92.75%    28.97  36,208  51.7%   1.25   0.2261     3.09    1.95       3.20      3.09    55.7%
 8  1.00 kwh      92.75%    28.97  36,208  51.7%   1.25   0.2261     3.09    1.95       3.20      3.09    55.7%
 8  0.90 naive    87.91%    27.45  38,130  54.4%   1.39   0.2035     2.92    1.84       3.02      3.25    52.7%
 8  0.90 kwh      87.92%    27.46  38,134  54.4%   1.39   0.2035     2.92    1.84       3.02      3.25    52.7%
 8  0.70 naive    75.46%    23.57  42,083  60.0%   1.79   0.1583     2.62    1.64       2.70      3.75    45.3%
 8  0.70 kwh      75.49%    23.58  42,102  60.1%   1.79   0.1583     2.62    1.64       2.70      3.75    45.3%
 8  0.50 naive    55.24%    17.25  43,131  61.5%   2.50   0.1131     2.52    1.56       2.57      5.04    33.1%
 8  0.50 kwh      55.24%    17.25  43,131  61.5%   2.50   0.1131     2.52    1.56       2.57      5.04    33.1%
  sh/kWh = server-hours run per kWh of heat used (= 1 / (0.8 d) when nothing is dumped).
  op BE/sh = (electricity - heat value) / sold server-h. p*/kWh .6 = p* (o = 0.6) / d = price per kWh at the wall.
  cov o=.6 = coverage x 0.6: linear estimate if a buyer takes 60 % of permit hours and unsold hours stay off.

== 2. Headline offers (shaped100); contract h = server-hours as sized at full draw, kwh = resized x 1/d ==
 N     d permits contr   cover heat MWh  sold sh   acc%        missed s1   util sh/kWh op BE/sh p* contr  dump
 6  1.00 naive   h      73.20%    22.86   28,575  94.8%     0 of  31,908  54.4%   1.25   0.2261     1.92     0
 6  1.00 kwh     h      73.20%    22.86   28,575  94.8%     0 of  31,908  54.4%   1.25   0.2261     1.92     0
 6  1.00 kwh     kwh    73.20%    22.86   28,575  94.8%     0 of  31,908  54.4%   1.25   0.2261     1.92     0
 6  0.90 naive   h      66.63%    20.81   28,901  96.2%     0 of  32,374  55.0%   1.39   0.2035     1.88     0
 6  0.90 kwh     h      66.63%    20.81   28,903  96.2%     0 of  32,378  55.0%   1.39   0.2035     1.88     0
 6  0.90 kwh     kwh    69.56%    21.72   30,172  90.4%     0 of  33,526  57.4%   1.39   0.2035     1.81     0
 6  0.70 naive   h      52.39%    16.36   29,218  97.7%     0 of  32,868  55.6%   1.79   0.1583     1.82     0
 6  0.70 kwh     h      52.39%    16.36   29,218  97.7%     0 of  32,868  55.6%   1.79   0.1583     1.82     0
 6  0.70 kwh     kwh    56.78%    17.73   31,668  70.7%     0 of  33,572  60.3%   1.79   0.1583     1.69     0
 6  0.50 naive   h      37.42%    11.69   29,218  97.7%     0 of  32,868  55.6%   2.50   0.1131     1.77     0
 6  0.50 kwh     h      37.42%    11.69   29,218  97.7%     0 of  32,868  55.6%   2.50   0.1131     1.77     0
 6  0.50 kwh     kwh    42.40%    13.24   33,108  47.3%     2 of  31,503  63.0%   2.50   0.1131     1.58     0
 8  1.00 naive   h      85.73%    26.77   33,467  93.7%     0 of  36,771  47.8%   1.25   0.2261     2.09     0
 8  1.00 kwh     h      85.73%    26.77   33,467  93.7%     0 of  36,771  47.8%   1.25   0.2261     2.09     0
 8  1.00 kwh     kwh    85.73%    26.77   33,467  93.7%     0 of  36,771  47.8%   1.25   0.2261     2.09     0
 8  0.90 naive   h      78.35%    24.47   33,985  95.7%     0 of  37,533  48.5%   1.39   0.2035     2.04     0
 8  0.90 kwh     h      78.34%    24.47   33,981  95.7%     0 of  37,532  48.5%   1.39   0.2035     2.04     0
 8  0.90 kwh     kwh    83.54%    26.09   36,237  92.2%     1 of  39,945  51.7%   1.39   0.2035     1.92     0
 8  0.70 naive   h      61.66%    19.26   34,388  97.0%     0 of  38,079  49.1%   1.79   0.1583     1.97     0
 8  0.70 kwh     h      61.66%    19.26   34,388  97.0%     0 of  38,079  49.1%   1.79   0.1583     1.97     0
 8  0.70 kwh     kwh    71.27%    22.26   39,744  76.5%     0 of  42,736  56.7%   1.79   0.1583     1.72     0
 8  0.50 naive   h      44.06%    13.76   34,404  97.1%     0 of  38,111  49.1%   2.50   0.1131     1.92     0
 8  0.50 kwh     h      44.06%    13.76   34,404  97.1%     0 of  38,111  49.1%   2.50   0.1131     1.92     0
 8  0.50 kwh     kwh    53.40%    16.68   41,690  53.8%    13 of  41,984  59.5%   2.50   0.1131     1.61     0
  p* contr = price per sold server-hour needed if every accepted contract hour is paid (no occupancy factor).
  acc% = accepted share of offered jobs; missed = seed 1, 'x of y accepted jobs whose deadline fell in the year'.

== 3. Summary: change against d = 1.00 (kWh permits, headline contract in server-hours) ==
  N=6 d=0.90: coverage 73.2% -> 66.6% (contract in server-h), 69.6% (contract resized in kWh, sold 30,172 vs 28,575 sh), naive permits 66.6%; p* contract 1.92 -> 1.88 / 1.81 / 1.88
  N=6 d=0.70: coverage 73.2% -> 52.4% (contract in server-h), 56.8% (contract resized in kWh, sold 31,668 vs 28,575 sh), naive permits 52.4%; p* contract 1.92 -> 1.82 / 1.69 / 1.82
  N=6 d=0.50: coverage 73.2% -> 37.4% (contract in server-h), 42.4% (contract resized in kWh, sold 33,108 vs 28,575 sh), naive permits 37.4%; p* contract 1.92 -> 1.77 / 1.58 / 1.77
  N=8 d=0.90: coverage 85.7% -> 78.3% (contract in server-h), 83.5% (contract resized in kWh, sold 36,237 vs 33,467 sh), naive permits 78.4%; p* contract 2.09 -> 2.04 / 1.92 / 2.04
  N=8 d=0.70: coverage 85.7% -> 61.7% (contract in server-h), 71.3% (contract resized in kWh, sold 39,744 vs 33,467 sh), naive permits 61.7%; p* contract 2.09 -> 1.97 / 1.72 / 1.97
  N=8 d=0.50: coverage 85.7% -> 44.1% (contract in server-h), 53.4% (contract resized in kWh, sold 41,690 vs 33,467 sh), naive permits 44.1%; p* contract 2.09 -> 1.92 / 1.61 / 1.92

== 3b. Stress: permits sized for a LOW assumed draw while the renter runs at full draw (shaped100) ==
  N=6 assumed d=0.7, real 1.0: coverage 72.53% (vs 73.20%), dumped 73 kWh, accepted 95.1%, missed 2 of 32,008, BE 0.2264
  N=6 assumed d=0.5, real 1.0: coverage 72.79% (vs 73.20%), dumped 471 kWh, accepted 96.8%, missed 0 of 32,591, BE 0.2283
  N=8 assumed d=0.7, real 1.0: coverage 83.36% (vs 85.73%), dumped 918 kWh, accepted 94.7%, missed 2 of 37,168, BE 0.2297
  N=8 assumed d=0.5, real 1.0: coverage 82.72% (vs 85.73%), dumped 1,523 kWh, accepted 96.6%, missed 0 of 37,895, BE 0.2320
  Execution trusts the permit count, so heat beyond demand + tank is dumped: a permit counted in server-hours
  with a guessed draw breaks 'nothing is dumped'. Permits must be kWh, checked against metered power.

== 4. Interruptible vs on-demand GPU prices (read 21 Nov 2026) and the price needed ==
  RTX PRO 6000 GPU-h per reference server-hour of work (50/50 J1/J2, r7 MLPerf ratios): 2.383
provider   product                                   region                on-dem   interr  ratio  unit
Azure      NC144lds_xl RTX PRO 6000 BSE v6 (1 GPU)   Switzerland North     7.8650   1.4535  0.185  USD per VM-h  [SOURCED: Azure Retail Prices API (prices.azure.com), Linux consumption meters]
Azure      NC144ds_xl RTX PRO 6000 BSE v6 (1 GPU)    Switzerland North     9.1230   1.6859  0.185  USD per VM-h  [SOURCED: same API]
Azure      NC288lds_xl RTX PRO 6000 BSE v6 (2 GPU)   Switzerland North    15.7300   2.9069  0.185  USD per VM-h  [SOURCED: same API]
Google     g4-standard-48 RTX PRO 6000 (1 GPU)       us-central1           4.4999   1.7178  0.382  USD per VM-h  [SOURCED via third-party aggregator gcloud-compute.com (updated 18 Nov 2026)]
Google     g4-standard-48 RTX PRO 6000 (1 GPU)       europe-west4          4.9499   2.0496  0.414  USD per VM-h  [SOURCED via the same aggregator]
Google     g2-standard-4 L4 (1 GPU)                  europe-west6 Zurich   0.9757   0.5840  0.599  USD per VM-h  [SOURCED via the same aggregator]
SaladCloud RTX 4090, Lowest (batch) vs High tier     community (homes)     0.4400   0.1600  0.364  USD per GPU-h  [SOURCED: salad.com/pricing (tiers, not on-demand vs spot; all tiers can disconnect)]

  A. Interruptible price of the SAME WORK, CHF per reference server-hour of work:
     Azure Switzerland North spot, NC144lds_xl RTX PRO 6000 BSE v6    2.91  (direct spot list x 2.383 GPU-h x 0.8392)
     Azure Switzerland North spot, NC144ds_xl RTX PRO 6000 BSE v6     3.37  (direct spot list x 2.383 GPU-h x 0.8392)
     Google us-central1 spot, g4-standard-48 RTX PRO 6000             3.44  (direct spot list x 2.383 GPU-h x 0.8392)
     Google europe-west4 spot, g4-standard-48 RTX PRO 6000            4.10  (direct spot list x 2.383 GPU-h x 0.8392)
     RunPod RTX PRO 4500 on-demand 2.53 x Azure CH 0.185                     0.47
     RunPod RTX PRO 4500 on-demand 2.53 x Google RTX PRO 6000 0.382-0.414    0.97-1.05
     RunPod RTX PRO 4500 on-demand 2.53 x Salad Lowest/High 0.364            0.92
     Exoscale CH RTX Pro 6000 on-demand 4.88 x Azure CH 0.185                     0.90
     Exoscale CH RTX Pro 6000 on-demand 4.88 x Google RTX PRO 6000 0.382-0.414    1.86-2.02
     Exoscale CH RTX Pro 6000 on-demand 4.88 x Salad Lowest/High 0.364            1.78

  B. Price needed per sold server-hour (unlimited demand, kWh permits) vs those prices.
     direct = DigitalHeat keeps 100 %; mkt = sold through a marketplace, host keeps 80 %.
     candidates (CHF per reference server-hour of work): [0] 2.91; [1] 3.37; [2] 3.44; [3] 4.10; [4] 0.47; [5] 1.05; [6] 0.92; [7] 0.90; [8] 2.02; [9] 1.78
       [0] Azure Switzerland North spot, NC144lds_xl RTX PRO 6000 BSE v6
       [1] Azure Switzerland North spot, NC144ds_xl RTX PRO 6000 BSE v6
       [2] Google us-central1 spot, g4-standard-48 RTX PRO 6000
       [3] Google europe-west4 spot, g4-standard-48 RTX PRO 6000
       [4] RunPod RTX PRO 4500 on-demand x Azure CH 0.185
       [5] RunPod RTX PRO 4500 on-demand x Google ratio
       [6] RunPod RTX PRO 4500 on-demand x Salad Lowest/High 0.364
       [7] Exoscale CH RTX Pro 6000 on-demand x Azure CH 0.185
       [8] Exoscale CH RTX Pro 6000 on-demand x Google ratio
       [9] Exoscale CH RTX Pro 6000 on-demand x Salad Lowest/High 0.364
      N     d    o     p*  clears direct            clears via mkt          
      6  1.00  0.6   2.84  0,1,2,3                  3                       
      6  1.00  1.0   1.79  0,1,2,3,8                0,1,2,3                 
      6  0.90  0.6   2.73  0,1,2,3                  2,3                     
      6  0.90  1.0   1.72  0,1,2,3,8,9              0,1,2,3                 
      6  0.70  0.6   2.60  0,1,2,3                  1,2,3                   
      6  0.70  1.0   1.62  0,1,2,3,8,9              0,1,2,3                 
      6  0.50  0.6   2.54  0,1,2,3                  1,2,3                   
      6  0.50  1.0   1.57  0,1,2,3,8,9              0,1,2,3,8               
      8  1.00  0.6   3.09  1,2,3                    3                       
      8  1.00  1.0   1.95  0,1,2,3,8                0,1,2,3                 
      8  0.90  0.6   2.92  1,2,3                    3                       
      8  0.90  1.0   1.84  0,1,2,3,8                0,1,2,3                 
      8  0.70  0.6   2.62  0,1,2,3                  1,2,3                   
      8  0.70  1.0   1.64  0,1,2,3,8,9              0,1,2,3                 
      8  0.50  0.6   2.52  0,1,2,3                  1,2,3                   
      8  0.50  1.0   1.56  0,1,2,3,8,9              0,1,2,3,8               
     lowest p* in the grid 1.56; highest ratio-based interruptible price 2.02.

  Reading: at o = 0.6 only hyperscaler spot LIST prices for the same work in their own bundled VMs [0]-[3]
  clear p*; at o = 1.0 also Swiss on-demand x the Google or Salad ratio [8], [9]. No ratio applied to the cheapest
  on-demand price of the same work [4]-[6] clears any p*. The same work rents UNINTERRUPTED for 2.53 CHF
  (RunPod on-demand, same card).
```

### A4. Reading the output

**Heat delivered and coverage (section 2, headline contract).** A lower draw removes heat in proportion; the contract in server-hours is still accepted (97–98% of jobs at d ≤ 0.7, because the house can now host more server-hours per kWh), but each sold hour brings 0.8·d kWh:

| N | d | heat used MWh | coverage | server-h per kWh of heat | p* per sold h (contract, all paid) | p* at o = 0.6, unlimited |
|---|---|---|---|---|---|---|
| 6 | 1.00 | 22.86 | 73.20% | 1.25 | 1.92 | 2.84 |
| 6 | 0.90 | 20.81 | 66.63% | 1.39 | 1.88 | 2.73 |
| 6 | 0.70 | 16.36 | 52.39% | 1.79 | 1.82 | 2.60 |
| 6 | 0.50 | 11.69 | 37.42% | 2.50 | 1.77 | 2.54 |
| 8 | 1.00 | 26.77 | 85.73% | 1.25 | 2.09 | 3.09 |
| 8 | 0.90 | 24.47 | 78.34% | 1.39 | 2.04 | 2.92 |
| 8 | 0.70 | 19.26 | 61.66% | 1.79 | 1.97 | 2.62 |
| 8 | 0.50 | 13.76 | 44.06% | 2.50 | 1.92 | 2.52 |

All *computed*, `python3 analysis/r8_draw.py`, sections 1–2, seed 1. Server-hours per kWh of heat permit = 1 ÷ (0.8·d) exactly, because nothing is dumped.

- **Resizing the contract in kWh** (offer 1/d times the server-hours) recovers only part of the heat: 56.8% / 71.3% at d = 0.7, 42.4% / 53.4% at d = 0.5. In cold hours all N servers already run, so a lower draw is like having fewer servers (N=6 at d = 0.5 delivers the heat of about three full-draw servers). Acceptance then falls to 47–54% at d = 0.5 and the first misses appear (2 of 31,503 at N=6; 13 of 41,984 at N=8, seed 1), because the doubled offers saturate the house.
- **Unlimited demand** (section 1): coverage 79.1% → 59.2% (N=6, d = 0.7) and 92.8% → 75.5% (N=8); utilisation rises (58.8% → 62.8%) because more servers run in mild hours.
- **Break-even per sold server-hour falls with draw.** Operation alone: 0.2261 × d (0.2035 / 0.1583 / 0.1131 CHF at 90 / 70 / 50%; 0.3325 × d with the heat to the host). With hardware: the house hosts more server-hours per kWh, so the fixed cost is spread wider; p* at 60% occupancy falls by 0.24 / 0.47 CHF at d = 0.7 (N=6 / N=8). Per kWh at the wall it rises (N=6: 2.84 → 3.04 / 3.72 / 5.07 CHF). A renter who pays per hour and draws little is therefore *not* an income problem for the operator; it is a heat problem for the house.
- **Occupancy and draw compound on coverage.** At o = 0.6 with unsold hours off, the linear estimate gives 47.5% / 55.7% at full draw and 35.5% / 45.3% at d = 0.7 (section 1, last column; linear approximation, not simulated).

**Naive vs kWh permits (sections 1–2).** They differ by at most 0.03 points of coverage. The band rule recomputes the permit count every hour from the metered tank, so when a renter delivers less heat than a permit assumed, the tank stays lower and the next hour issues more permits. Under-drawing is self-correcting under the plan's rule; it costs heat, not deadlines.

**The dangerous direction (section 3b).** If permits are sized for a *lower* draw than the renter actually runs (assumed 0.7 or 0.5, real 1.0), execution trusts the permit count and the tank overflows: **73 / 471 kWh dumped a year at N=6, 918 / 1,523 at N=8**, coverage −0.4 to −3.0 points, 2 misses at d_assumed = 0.7 (seed 1, *computed*). A scheduler that guesses a "typical" renter draw and counts permits in server-hours breaks the "0 kWh dumped" tile.

### A5. How the scheduler should treat draw

1. **The permit is kWh of heat, not server-hours:** permit(h) = forecast demand(h) + free tank space. This is what the plan's permit function already computes before it divides by 0.8.
2. **Convert to servers with the metered draw:** servers(h) = floor(permit kWh ÷ (0.8 × measured kW per server)). In the pilot, the measured kW comes from the box's wall meter or NVML; in the hackathon the case fixes a running server at 1 kW, so d = 1 and nothing changes.
3. **Make the permit physically binding with a power cap** (e.g. `nvidia-smi -pl`, per GPU): a renter can then draw less than the permit (safe, see A4) but never more (the section-3b failure). Splitwise's result (row 2) suggests decode-heavy renters barely notice a 50% cap; prefill-heavy renters would (*unverified* for our card).
4. **Report two units on the dashboard:** heat in kWh (coverage, dumped) and sold server-hours (income, break-even). They separate as soon as d < 1.
5. **Sell work, not hours, where possible:** J1/J2 priced per audio-hour or per token keep the draw in DigitalHeat's hands (offline batch, 86–100% of rating). Hourly GPU rental hands it to the renter.

**Build scope: none for Sunday** (*assumption* on build effort). The case fixes 1 kW per running server, so the team scheduler keeps d = 1. A `draw` argument (default 1.0) in the permit function would be about 2–3 lines (*estimate*), OPTIONAL and cut first; this file recommends **not** building it and stating the rule in the assumptions list and Q&A.

---

## (b) Interruptible discount

### B1. Interruptible vs on-demand GPU prices (read 21 Nov 2026)

| Provider | Product | Region | On-demand | Interruptible | Ratio | Status | URL |
|---|---|---|---|---|---|---|---|
| Azure | Standard_NC144lds_xl_RTXPRO6000BSE_v6 (1 × RTX PRO 6000 BSE, 144 vCPU) | Switzerland North | 7.865 USD/h | 1.453452 USD/h ("Spot" meter) | **0.185** | *sourced*: Azure Retail Prices API, Linux consumption meters, effective dates on-demand 2026-10-01, spot 2026-11-01 | <https://prices.azure.com/api/retail/prices?$filter=serviceName%20eq%20'Virtual%20Machines'%20and%20armRegionName%20eq%20'switzerlandnorth'%20and%20contains(armSkuName,'NC')> |
| Azure | NC144ds_xl (1 GPU, more RAM) | Switzerland North | 9.123 | 1.68593 | 0.185 | *sourced*, same | same |
| Azure | NC288lds_xl (2 GPU) | Switzerland North | 15.73 | 2.906904 | 0.185 | *sourced*, same | same |
| Azure | NC24ads_A100_v4 / NC40ads_H100_v5 | Switzerland North | 5.252 / 9.981 | 0.97057 / 2.325573 | 0.185 / 0.233 | *sourced*, same | same |
| Azure | GPU count per size: NC144lds_xl and NC144ds_xl = 1 GPU, NC288 = 2, NC24/36lds = 1/4 GPU | — | — | — | — | *sourced* | <https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/gpu-accelerated/nc-rtxpro6000-bse-v6-series> |
| Google | g4-standard-48 (1 × RTX PRO 6000) | us-central1 | 4.4999 USD/h | 1.7178 | **0.382** | *sourced* via a **third-party aggregator** of Google SKU prices ("Last Update: Wed Nov 18 16:45:26 2026"); Google's own pages load prices by script and were not readable | <https://gcloud-compute.com/g4-standard-48.html> |
| Google | g4-standard-48 | europe-west4 | 4.9499 | 2.0496 | **0.414** | same | same |
| Google | g2-standard-4 (1 × L4) | europe-west6 Zurich / us-central1 | 0.9757 / 0.7068 | 0.584 / 0.423 | 0.599 / 0.598 | same | <https://gcloud-compute.com/g2-standard-4.html> |
| SaladCloud | RTX 4090, Lowest (batch) vs High tier | community (homes) | 0.440 USD per GPU-h (High) | 0.160 (Lowest) | **0.364** | *sourced*; tiers are priority classes chosen by the renter, and even High is "Still subject to node disconnection" | <https://salad.com/pricing> |
| Google, general | "up to 91% off of the corresponding on-demand price" | — | — | — | ≥ 0.09 | *sourced* (page text; no per-GPU number readable) | <https://cloud.google.com/compute/gpus-pricing> |

Ratios *computed*: `python3 -c "print(1.453452/7.865, 1.7178/4.4999, 2.0496/4.9499, 0.584/0.9757, 0.160/0.440)"` → 0.1848, 0.3817, 0.4141, 0.5985, 0.3636.

Not used: the AWS public spot feed (`https://website.spot.ec2.aws.a2z.com/spot.js`) has `last-modified: Mon, 13 May 2024`, so it is stale; RunPod's pricing page shows no spot price; Vast.ai's offer API returned HTTP 403; Firecrawl (Google Spot VM page) failed for lack of credits.

### B2. Recomputed: price needed vs interruptible price of the same work

The same work in RTX PRO 6000 GPU-hours: 4.19 RTX PRO 4500 GPU-h per reference server-hour ÷ 2.01 (J1) or 1.56 (J2), 50/50 → **2.383 GPU-h** (*computed*; the speed ratios are *team-sourced* from MLPerf v6.1 6.1-0018 vs 6.1-0017 via `r7_payback.py`).

| Interruptible price of one reference server-hour of work | CHF | Clears p* 2.84 (N=6, o = 0.6, d = 1)? |
|---|---|---|
| Azure Switzerland North spot, 1-GPU NC144lds_xl: 1.453452 × 2.383 × 0.8392 | **2.91** | yes, by 0.07, only if sold direct; N=8 (3.09) no |
| Azure Switzerland North spot, NC144ds_xl | 3.37 | yes (direct) |
| Google us-central1 spot (aggregator) | 3.44 | yes (direct), US region |
| Google europe-west4 spot (aggregator) | 4.10 | yes, also via a marketplace (3.28) |
| RunPod on-demand, same card (2.53) × ratio 0.185 / 0.364 / 0.382–0.414 | 0.47 / 0.92 / 0.97–1.05 | **no**, below every p* in the grid (lowest 1.56) |
| Exoscale CH on-demand (4.88) × ratio 0.185 / 0.364 / 0.382–0.414 | 0.90 / 1.78 / 1.86–2.02 | **no** at o = 0.6; only at o = 1.0 with the Google or Salad ratio (1.57–1.95 needed) |

*Computed*, `python3 analysis/r8_draw.py` section 4. With renter-controlled draw the needed price falls (N=6, o = 0.6: 2.73 / 2.60 / 2.54 at d = 0.9 / 0.7 / 0.5), but the ratio-based prices stay far below it, and the coverage falls (A4).

**Answer.** No buyer who shops on price pays enough. Against the price a buyer can actually get for interruptible capacity (any sourced ratio applied to the cheapest on-demand price for the same work), the heat-gated house is worth 0.47–1.05 CHF per server-hour; it needs 2.54–3.09 at 60% occupancy and 1.56–1.95 at 100%. The only interruptible prices that clear 2.84 are hyperscaler spot **list** prices for the same work inside their own bundled VMs (144 vCPU, 264–516 GiB RAM, network and storage included), 2.91–4.10 CHF, and the same buyer can rent the same work **uninterrupted** on RunPod for 2.53. Caveats: the RTX PRO 6000 → 4500 conversion mixes MLPerf hosts; the Google figures come from an aggregator; spot prices change over time and the API shows one current value; a Swiss-residency premium could justify Azure-CH-level prices, but no such buyer was found.

---

## (c) Refuse, not dump: positioning and the updated "does not pay off" statement

**One sentence (pitch and README):**

> "Heat is the admission ticket: when the house has no room for heat, the job is refused at the door, never run with its heat thrown away; the swing between January and July is carried upstream by the aggregator, which sends refused work to cloud capacity it pays for or to a partner site that needs heat all year."

Why this and not "dump": (1) the jury scores "share of heat demand covered at the least heat dumped" first; (2) round 7's cheapest flat-volume option (run the refused 30% in the basement, dump about 7,200 kWh a year, about 1.60 CHF needed, round-7 critic estimate) would turn the headline's 0 kWh into thousands; (3) the precedent operator stops rather than dumps: on Heata's host page, "sometimes the water will be at temperature so the heata unit won't be able to run", and "heata pays for the electricity used by the heata unit" (*sourced*, <https://www.heata.co/free-hot-water>); its SLA backs promises with Cloud Burst Nodes (round 7, *sourced*). Who absorbs the swing, in order: the **aggregator** (DigitalHeat as operator) holds the customer promise; it places refused work on **cloud fallback** (Exoscale CH about 4.88, RunPod 2.53 CHF per server-hour of work, round 7) or a **typed partner site** with year-round heat demand (indoor pool, care home; Leafcloud minimum 500 GJ a year, round 6). The house never carries it.

**Updated "does not pay off when …" (replaces the round-7 critic's wording; numbers rounded for speech):**

> "The model does not cover its running cost when a sold server-hour brings in less than 0.23 francs (0.33 if the homeowner keeps the heat). The servers do not pay back in five years below about 2.80 francs per sold hour at 60% occupancy of heat-permitted hours (1.80 at 100%; about 3.40 with 8% cost of capital), or if GPU-hour prices fall 10% a year. Interruptible GPU capacity sells at 18 to 41% of on-demand, so the same work bought interruptibly costs 0.50 to 2.00 francs: below what the servers need unless buyers take every heat-permitted hour. Only hyperscaler spot list prices (2.90 to 4.10) are higher, and those buyers can rent the same work uninterrupted for 2.50. A rented GPU that draws 70% of its rating lowers the price needed to about 2.60 but delivers 30% less heat, so coverage falls from 73% to 52% at six servers. Refused work goes to the aggregator's cloud fallback (2.70 needed with Swiss cloud) or to a partner site, never to a dry cooler in the basement."

Sources: 0.23 / 0.33 (case formula, plan); 2.80 / 1.80, 2.70 and the 10% decline (`r7_payback.py` sections 4 and 6); 3.40 (round-7 critic probe, *estimate*, not saved); 18–41% (B1, *sourced*); 0.50–2.00 = 0.47–2.02 (B2, *computed*); 2.90–4.10 = 2.91–4.10 (B2); 2.50 = 2.53 (RunPod, round 7); 2.60, 73% → 52% (A4, *computed*, seed 1).

---

## Proposed changes to the plan

1. **Working idea / Run policy:** add "Refused, not dumped" as the one positioning sentence in (c). Retire the round-7 "local dump" option (about 1.60 CHF) from the "when it does not pay off" and open-risk-2 text as an *option*; keep it only as the reason we refuse: "the cheapest way to honour a flat promise dumps about 30% of its heat; we exclude it".
2. **Admission rule (one line):** "A permit is kWh of heat (forecast demand + free tank), converted to servers at the metered draw and enforced with a GPU power cap. Under the case's 1 kW per running server the draw is 1." Build scope: none.
3. **Open risk 2:** replace "A renter, not the scheduler, controls the GPU's draw" with: "Draw: offline batch work runs at 86–100% of rating, interactive serving near 43% (sourced, A1). At 70% draw coverage falls from 73.2% to 52.4% (N=6) / 85.7% to 61.7% (N=8) under the headline contract, while p* falls from 2.84 to 2.60 / 3.09 to 2.62 (`r8_draw.py`). Permits sized for a guessed low draw dump 73–1,523 kWh a year when the renter runs at full power." Replace "Exoscale × 0.36 is about 1.78 CHF, critic estimate" with the sourced ratios: Azure CH RTX PRO 6000 spot 0.185, Google RTX PRO 6000 0.38–0.41 (aggregator), Salad 0.36; interruptible same work 0.47–2.02 CHF; hyperscaler spot list 2.91–4.10.
4. **Q&A 1 / founder objections 10 and 12:** 10 → B2 answer ("no buyer who shops on price; only hyperscaler spot list prices clear it, and the same work rents uninterrupted for 2.53"). 12 → A4/A5 answer ("a heat problem, not an income problem; permits in kWh with a power cap").
5. **"When the model does not pay off":** use the statement in (c).
6. **DigitalHeat question 3:** add "Do you sell work (per audio-hour, per token) or GPU-hours? GPU-hours hand the heat output to the renter."
7. **Pitch:** nothing new on a main slide; the (c) sentence is the only spoken addition (about 40 words, about 15 s).

## Weak points of this work

- The draw grid (90/70/50%) is a bracket, not a measured distribution of renter draw; no source gives the draw distribution of rented GPUs. The 43% / 86% figures come from a secondary paper whose attribution I could not verify in the primary's text.
- Whisper on L4 is a 72 W card that runs into its power limit; a 165 W RTX PRO 4500 may sit lower on the same workload (*unverified*).
- `r8_draw.py` keeps job runtimes fixed when draw falls (renter hours). For DigitalHeat's own batch jobs a power cap would lengthen runtimes (Samsi: −30% power, +6.7% time); not modelled.
- Seed 1 only (the plan's scheduler convention); `--seeds 3` was not run.
- Google prices come from a third-party aggregator; Azure spot prices vary; the RTX PRO 6000 → reference-server conversion uses team-sourced MLPerf ratios from two different hosts; VMs bundle CPU, RAM, network and storage that our box also has, but in different proportions.
- The `under:x` stress is a crude model of a wrong draw estimate (a fixed assumed draw for the whole year).
- No interest, constant prices, central fixed costs, as in round 7.

## Commands and pages

```
python3 analysis/r8_draw.py                                   # full output above (seed 1, ~27 s)
python3 -c "print(5700/6500, 64.9/72, 72.3/72, 50.9/72, 39.0/72)"                              # A1 shares
python3 -c "print(1.453452/7.865, 1.7178/4.4999, 2.0496/4.9499, 0.584/0.9757, 0.160/0.440)"    # B1 ratios
curl -sL -A "Mozilla/5.0" "https://prices.azure.com/api/retail/prices?\$filter=serviceName%20eq%20'Virtual%20Machines'%20and%20armRegionName%20eq%20'switzerlandnorth'%20and%20contains(armSkuName,'NC')"
                                                              # parsed with python3 -I (Linux consumption meters, Spot vs not)
curl -sL -A "Mozilla/5.0" https://cse.hkust.edu.hk/~weiwa/papers/weng-nsdi22.pdf ; pdftotext   # Alibaba NSDI'22
curl -sI https://website.spot.ec2.aws.a2z.com/spot.js         # last-modified 13 May 2024 -> not used
# WebFetch (opened): par.nsf.gov/servlets/purl/10505206 (PDF saved, pdftotext); arxiv.org/html/2311.18677v2;
#   arxiv.org/html/2603.17280v1; arxiv.org/abs/2601.22076; arxiv.org/html/2601.22076v2; arxiv.org/abs/2310.03003;
#   arxiv.org/html/2310.03003v1; e2enetworks.com/blog/benchmarking-asr-models-nvidia-l4-parakeet-whisper-nemotron;
#   learn.microsoft.com/.../nc-rtxpro6000-bse-v6-series; gcloud-compute.com/g4-standard-48.html;
#   gcloud-compute.com/g2-standard-4.html; salad.com/pricing; heata.co/free-hot-water; runpod.io/pricing (no spot)
# Tried, no number: cloud.google.com/compute/gpus-pricing and /spot-vms/pricing (prices loaded by script / too large);
#   tomshardware.com Whisper benchmark (truncated); homes.cs.washington.edu POLCA PDF (404); Vast.ai offers API (403);
#   Firecrawl scrape of cloud.google.com/spot-vms/pricing (insufficient credits)
```
