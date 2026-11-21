# Round 6: who buys a heat-shaped contract, what the operator really receives, and where refused work goes

Investigator for weak point 2 of round 6: "who buys a heat-shaped contract and what the operator really receives; refused work goes to an unnamed partner site" (must-have 1 "how many jobs arrive per day and where that number comes from"; must-have 3 "computing income" and break-even; open risks 2, 4 and 11). Written Sat 21 Nov 2026, about 11:00 to 11:40. This file plans and assesses. It builds no scheduler, dashboard or demo.

**Status labels:** *sourced* = number read by me on the page at the URL given (WebFetch summary with quotes, or the PDF page read as an image; re-read by eye before a slide); *team-sourced* = from the team's `reports/` or `research_notes/` with a URL I did **not** re-open (do not quote without opening); *computed* = printed by a script in `analysis/` (script and command named); *assumption* = our own choice; *unverified* = estimate, interpretation or only seen in a search snippet.

**Currency:** CHF. 1 USD = 0.8392 CHF and 1 GBP = 1.1015 CHF, from ECB reference rates of 20 Nov 2026 (EUR/USD 1.0990, EUR/GBP 0.83735, EUR/CHF 0.9223; *sourced*, re-opened this round: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>). Electricity 0.3325 CHF/kWh and heat valued at price ÷ 2.5, from `data/README.md`.

**Tools:** WebSearch, WebFetch, curl (one HTML page and one PDF, text extracted locally), local Python. **Firecrawl calls used: 0 of 6.** No personal or team names in any query.

**Files written this round**

| File | What |
|---|---|
| `analysis/r6_buyer_scenarios.py` | New. Stdlib only. Imports (does not edit) `r4_headline`, `r2_deadline_sim`, `r4_machine`, `r5_chain`, `r3_income`, `baseline_sweep`. Runs the headline yearly loop for six buyer scenarios at N=6 and N=8, prices sold hours with every sourced operator-price anchor, and sizes a typed partner site. About 5 s wall on 8+ cores (38 s CPU). Sets `sys.dont_write_bytecode`. |
| this file | Findings |

Temporary files (scratchpad, not kept): `.../scratchpad/r6buyer_dl/r6buyer_infomaniak.{html,txt}`, `.../scratchpad/r6buyer_dl/r6buyer_bfe9728.{pdf,txt}`, `.../scratchpad/r6buyer_out.txt`.

---

## Bottom line

1. **No buyer we can find defers work by seasons.** Every published deferrable tier we opened tolerates hours to days, not months: OpenAI Batch "completes within 24 hours" at a 50% discount, and the window "can only be set to 24h"; Groq batch 24 h to 7 days at 50%; Google Spot VMs can be reclaimed with 0 or 120 s notice at up to 91% off; Google's own non-urgent work (e.g. YouTube video processing) is paused "for the duration of the grid event" and rescheduled after (*sourced*, table A1). A ~10:1 January/July volume therefore cannot come from one customer's latency tolerance. It can only come from **a pool or aggregator that takes whatever hours the house has**, which is how Heata's SLA works: committed capacity is guaranteed across the network and "Cloud Burst Nodes" (public cloud) fill gaps (*sourced*).
2. **What operators pay the house: the electricity, and the heat is free.** Heata credits the host's energy or bank account from a billing submeter; Leafcloud meters and pays the power and gives "free baseload heat"; Deep Green "covers the electricity and maintenance costs" (all *sourced*). Nobody we found pays the host a share of compute income. So "what the operator receives" means the price DigitalHeat itself gets for a server-hour.
3. **What a server-hour fetches, sourced:** a host on a GPU-rental marketplace gets about **1.15–2.03 CHF per 1 kW server-hour** of our reference box (0.41/0.48/0.72 USD per GPU-hour renter price × 80% host share × 4.19 GPU-hours; prices *sourced*, 4.19 rests on the *assumed* 0.955 kW wall power). These are always-on data-centre prices; no listing pays a server that leaves on its own heat signal. Heata's own published GPU surcharge is £1.19 per GPU-hour (Tier 2, 24–40 GB), i.e. **5.49 CHF per server-hour at list**, but its filed trade debtors were £340 at end-2025 (*team-sourced*), so list ≠ realised.
4. **What it needs** (*computed*, `python3 analysis/r6_buyer_scenarios.py`, cold-plate chain, 5-year simple payback): **1.70 CHF per sold server-hour** under the headline (N=6; 1.87 at N=8), 2.26 with a flat customer, 1.60 if a pool takes every permit hour, and 8.00 for a flat customer sized to July. Against the sourced rental anchors: headline payback **4.1–8.0 years** (N=6), flat customer **5.6–10.9 years**, pool **3.8–7.4 years**, July-sized flat **22–42 years**. The plan's "2.7 years" is the 20%-of-list scenario on the round-4 air-coil cost; on the cold-plate chain the same scenario is **2.9 / 3.2 years** (N=6 / N=8).
5. **Selling hours instead of jobs removes the "19.9 M audio-hours with no buyer" problem**, because a rented hour is priced the same whatever runs in it. Under the 20%-of-list scenario LLM-only work looks hopeless (10–16 years); priced by the hour it pays back like any other hour (LLM-only heat-shaped 4.1–7.9 years, N=6). The 20%-of-list line should no longer lead.
6. **Refused work under our own contract is tiny; under a flat customer it is not.** Headline: about 1,000 server-hours a year refused at N=6 and **0.8 server-hours a day of J1 in summer** per house (about 0.6 kWh of heat a day). Flat customer: about 9,000 server-hours a year and **41 server-hours a day of J1 in summer** (33 kWh of heat a day) per house (*computed*).
7. **Typed partner site: a pool.** Swiss guidance gives **430–480 kWh per m² of water per summer season** (mid-May to mid-September, about 120 days) for an uncovered heated outdoor pool, and a typical indoor pool's monthly heat demand falls from about 71,000 kWh in January to about 24,000 kWh in July (*sourced*, BFE/VHF guideline 2018). Basel's Gartenbad St. Jakob has a heated 50 m pool (*sourced*). With an *assumed* 1,050 m² of water, one such pool absorbs about **157–175 kW all summer, about 200 servers' heat, roughly the refused summer J1 work of 100–130 N=6 houses under a flat customer** (*computed*). The same guideline says outdoor pools may be heated in Switzerland under MuKEn 2008/2014 only with renewable energy or otherwise unusable waste heat ("nicht anders nutzbarer Abwärme"); whether summer server heat counts is our reading (*unverified*).
8. **Build scope: none added.** Everything here is labelling, Q&A text and one comparison table. The team scheduler keeps reading `analysis/r4_offers_shaped100_seed1.csv`.

---

## (a) Evidence: deferrable buyers, contract forms and what operators receive

### A1. How long do real buyers let work wait? (all *sourced*, opened 21 Nov 2026)

| Who | Form | Number on the page | URL |
|---|---|---|---|
| OpenAI Batch API | async batch | "50% cost discount compared to synchronous APIs"; "Each batch completes within 24 hours (and often more quickly)"; "the completion window can only be set to `24h`" | <https://developers.openai.com/api/docs/guides/batch> |
| Groq Batch | async batch | "Pricing is at a 50% cost discount compared to synchronous API pricing"; "We allow for setting a batch window from 24 hours to 7 days"; unfinished jobs become `expired`, billed only for completed requests | <https://console.groq.com/docs/batch> |
| Google Cloud Spot VMs | preemptible capacity | "up to 91% discounts … compared to the on-demand price"; preemption notice 120 s or 0 s (default); for "fault-tolerant workloads, such as batch processing jobs or stateless applications" | <https://docs.cloud.google.com/compute/docs/instances/spot> |
| Google (own data centres) | internal deferrable work | "non-urgent tasks in the background, like YouTube video processing and adding new words to Google Translate"; limited "for the duration of the grid event, and … rescheduled after"; some rerouted to another grid (4 Oct 2023) | <https://cloud.google.com/blog/products/infrastructure/using-demand-response-to-reduce-data-center-power-consumption> |

**Reading.** The longest window any seller of batch work publishes is 7 days, and that is what our J2 deadline (168 h) already uses. Our J1 deadline (24 h) equals OpenAI's only window. Nothing we found tolerates a seasonal shift. A winter-heavy volume is therefore a supply-side property that a **pool** has to absorb (other sites in summer, or a cloud fallback), not a demand-side property of any customer.

### A2. Contract forms of operators that heat buildings with compute

| Operator | Contract form with the compute buyer | What the host gets / pays | Status | URL |
|---|---|---|---|---|
| Heata (UK) | Managed compute with "Committed Capacity of >99.5%" per job cluster; service credits 10/25/100% below 99.5/95/90%; "To guarantee delivery of workloads we may use cloud instances (Cloud Burst Nodes)"; Access Nodes hosted in GCP; worker nodes "one per home, providing free hot water as a byproduct" (SLA "Last Updated: August 2026") | — | *sourced* (PDF read as images) | <https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf> |
| Heata | Price list (GBP, excl. VAT): managed vCPU £0.017 per core-hour, spot £0.010 ("no SLA"); GPU surcharge Tier 1 (16–24 GB, RTX 4090 etc.) £0.89, Tier 2 (24–40 GB) £1.19 per GPU-hour; **no spot price for GPUs**; reserved 30% (1 y) / 55% (3 y) off base compute; no effective date stated | — | *sourced* | <https://docs.heata.co/pricing-billing/> |
| Heata | Render farm for studios (F10 Studios, Eleven Visualisation, Model Works named), "£2 per GPU-hour", RTX 4090 at 450 W; sits in Y Bank, a community building in Caerphilly, whose heat it supplies | building heated | *sourced* | <https://www.heata.co/render/mediacymru> |
| Heata | — | "heata pays for the electricity used by the heata unit"; credit to energy or bank account; "accredited billing submeter"; host saves "£150–350 a year"; "sometimes the water will be at temperature so the heata unit won't be able to run" | *sourced* | <https://www.heata.co/free-hot-water> |
| Leafcloud (NL) | public cloud and GPUs (pricing page not read) | "The power consumed by the servers is metered and paid by Leafcloud"; host gets free baseload heat of 630–3,780 GJ a year; minimum host hot-water demand 500 GJ a year; sized at 5–20% of design thermal load; 20–120 kW IT; 45–65 °C; building types include pools, care homes, hospitals; Zaandam nursing home 5 kW saves €6,000 a year | *sourced* | <https://www.leaf.cloud/leafsites/> |
| Deep Green (UK) | colocation / cloud (not read) | Exmouth Leisure Centre pool: "reduce the pool's energy requirements by 62 percent", "saving them over £20,000 … a year", "a dozen servers"; "installs the kit for free, and also covers the electricity and maintenance costs" (14 Mar 2023) | *sourced* | <https://www.theregister.com/2023/03/14/cloud_startup_waste_heat_dcs/> |
| Qarnot (FR) | banks (BNP Paribas, Société Générale), 3D studio Illumination; revenue €3 M (2024); insolvent May 2026, bought by Scaleway | free heat in housing | *team-sourced*, not re-opened (TechCrunch 2023, Next.ink 2026 in `research_notes/…/comparable_operators.md`) | — |
| Heata finances | trade debtors £340 at 31 Dec 2025, ~80 units installed Aug 2023 | — | *team-sourced* (Companies House, MIT TR), not re-opened | — |

**Answer to "who buys their compute and on what terms":** studios (rendering), one utility's own workloads in a trial, banks (Qarnot, *team-sourced*), and generic cloud users. The terms are either **committed capacity with a cloud fallback** (Heata) or **spot with no SLA** (Heata CPU spot). Nobody publishes a winter-heavy contract. Heata's GPUs have no spot price at all.

### A3. Price anchors: what one of our server-hours could fetch

| Anchor | Per GPU-hour | Per 1 kW server-hour (CHF) | Status |
|---|---|---|---|
| Cheapest listed RTX PRO 4500 rental, renter price | 0.41 USD (GPU.ai, read in round 4 at ~09:50); **0.48 USD (Lium) on re-read at ~11:15 today** | × 4.19 GPU-h × 80% host share × 0.8392 = **1.15 / 1.35** | *sourced* (<https://getdeploying.com/gpus/nvidia-rtx-pro-4500>: "median on-demand price is $0.92 per GPU per hour across 7 providers", as of 21 Nov 2026; no spot prices listed) |
| RunPod Secure Cloud, RTX PRO 4500 SE | 0.72 USD; Community Cloud blank; no spot price | **2.03** | *sourced* (<https://www.runpod.io/gpu-models/rtx-pro-4500-se>) |
| Host share of renter price | about 80% | — | *sourced in round 2* (Salad, Vast.ai), not re-opened |
| Interruptible discount | Vast.ai RTX 4090 interruptible median 0.347 vs on-demand 0.467 USD → 0.74 | 1.35 × 0.74 = **1.00** (hand calculation) → headline N=6 payback **9.5 years** | ratio *team-sourced* (r2 via `analysis/one_rack_model.py`), not re-opened; applying it to this GPU is an *assumption* |
| Heata list, Tier 2 GPU surcharge (direct sale, operator keeps 100%) | £1.19 | × 4.19 × 1.1015 = **5.49** (GPU only, no vCPU/RAM) | *sourced* list price; realised price unknown |
| 20% of US batch list value (plan's scenario) | — | 2.81 (headline mix); 0.96 for LLM-only | 20% is an *assumption* |
| GPU-hours per server-hour | 4 GPUs ÷ 0.955 kW | 4.19 | *assumption* (wall power estimated in round 4) |

**Swiss-resident inference exists at a much higher list price, but not as a batch tier.** Infomaniak AI Services lists Swiss-hosted models in CHF excl. VAT, with no batch or asynchronous discount on the page: Ministral-3-14B CHF 0.30 input / 0.40 output per million tokens, Gemma-4-31B 0.20 / 0.40, Apertus-v1.5-70B 0.70 / 2.50; Whisper V3 "CHF 0.006 / minute", **billed per minute of generation (processing time), not per minute of audio** (*sourced*, <https://www.infomaniak.com/en/hosting/ai-services/prices>, page text extracted with curl). With the plan's 6 input tokens per output token (*assumption*), Ministral-3-14B costs 2.20 CHF per million output tokens, **16 times** the US batch central the plan uses (0.16 USD = 0.134 CHF), Gemma-4-31B 1.60 CHF, 12 times (*computed* by hand). These are larger models than our Llama-3.1-8B row, sold synchronously, and the seller runs its own data centres, so this is evidence that a Swiss data-residency price level exists, not evidence of a buyer for basement capacity. The Whisper price cannot be converted to audio-hours without Infomaniak's throughput (*unverified*).

### A4. What was not found

- Any buyer or contract that accepts a seasonal (months) shift of volume.
- Any transacted price a heat-following operator actually realised per GPU-hour or server-hour (Heata's list exists; its filed debtors suggest little volume, *team-sourced*).
- Any marketplace that pays for capacity that disappears when the tank is full (round 2 and round 4 finding stands). Spot buyers accept interruption by the **seller's** market, so a heat-following host fits the spot model in form; we found no published spot rate for this GPU.

---

## (b) Typed partner site for refused or summer work

The case itself names "hotels, spas, agriculture, businesses" as summer heat sites ([case brief](../case-brief.md#core-use-case)). We type the partner as **a pool**, because the evidence is Swiss and specific:

| Fact | Number | Status / URL |
|---|---|---|
| Heated outdoor pool (Freibad), no cover, Swiss Mittelland, season mid-May to mid-September (~120 operating days), 24 °C | **430–480 kWh per m² of water per season**; with a night cover 215–240 | *sourced*, BFE/VHF "Leitfaden Energie in Hallen- und Freibädern", Version 1, 2018, p. 156 (PDF page read as image): <https://pubdb.bfe.admin.ch/de/publication/download/9728> |
| Outdoor pool heating rule | "Freibäder dürfen gemäss MuKEn 2008/2014 nur mit erneuerbarer Energie oder nicht anders nutzbarer Abwärme aufgeheizt werden" | *sourced*, same PDF p. 155. Whether summer server heat is "nicht anders nutzbare Abwärme" is our reading (*unverified*) |
| Heated outdoor pool kept warm year-round (Warmaussenbecken) | about 7,500–8,500 kWh/m² a year | *sourced*, same PDF p. 155 |
| Typical indoor pool (Hallenbad), monthly heat demand | about 71,000 kWh in January, **about 24,000 kWh in July**, about 18,000 in August | *sourced*, same PDF p. 29, Abb. 1; **read off the bar chart by eye (±2,000 kWh)** |
| Indoor pool specific heat use | 43–52 kWh per m³ of building volume a year | *sourced*, same PDF p. 151 |
| Basel example | Gartenbad St. Jakob: "Beheiztes 50m-Wettkampfbecken mit Beleuchtung"; Sportbad season 25 April to 4 October (2027 table) | *sourced*, <https://www.bs.ch/themen/kultur-sport-und-freizeit/baeder-kunsteisbahnen-sportanlagen-und-raeume/gartenbaeder/gartenbad-st-jakob> |
| Water area of that pool | 50 m × 21 m = 1,050 m² | *assumption* (width not found) |
| Leafcloud's minimum host | 500 GJ/yr of hot-water demand = about 381 kWh a day, about 20 servers' heat | *sourced* threshold, *computed* conversion |

**Order of magnitude** (*computed*, script section 3): one heated 50 m outdoor pool needs 3,760–4,200 kWh a day in season, **157–175 kW average, about 200 servers' recovered heat**. A typical indoor pool in July needs about 774 kWh a day, about 40 servers. Under the headline contract a house refuses about 0.8 server-hours of J1 a day in summer, so the partner site is a footnote. Under a flat customer a house refuses about 41 server-hours of J1 a day in summer; one outdoor pool takes that from about 115–128 houses (N=6), one indoor pool from about 24.

**Wording for the Working idea and open risk 4** (replaces "not named yet"): *"Work a house refuses is never started. In summer it goes to a site that needs heat then, typically a heated outdoor pool (430–480 kWh per m² of water per season in the Swiss Mittelland; Swiss rules allow only renewable heat or otherwise unusable waste heat there) or an indoor pool or spa. That site is outside the reference-house balance and needs its own servers."* Caveat: an outdoor pool's servers sit idle from October to April, so that hardware is a cost the reference house does not carry. An indoor pool runs all year but still swings about 3:1 (January 71,000 vs July 24,000 kWh).

---

## (c) Script and output

`analysis/r6_buyer_scenarios.py` (stdlib only, imports only). Command from the repo root:

```
python3 analysis/r6_buyer_scenarios.py              # seeds 1-3, about 5 s wall, 38 s CPU
python3 analysis/r6_buyer_scenarios.py --seeds 1    # seed 1 only
python3 analysis/r6_buyer_scenarios.py --procs 1    # single process
```

Scenarios: `shaped100` (current headline), `flat` (same yearly volume, flat), `llm_flat` (100% J2, flat), `llm_shaped` (100% J2, heat-shaped), `flat_july` (flat at 15 server-h a day, the July rate), `pool` (saturating offers: an aggregator takes every permit hour). J2-only is done by setting `r2_deadline_sim.WORK_SHARE = (0, 1)` inside the worker before calling `r4_headline.run`; no file is edited. Regression: `shaped100` reproduces the plan's 73.67% / 86.14%, 0 of 31,908 / 36,771, 28,761 / 33,626 sold hours and the 80.9k / 94.0k CHF scenario exactly; `flat` reproduces `r5_pitch_numbers.py` D5 (53.67% / 60.48%).

Output of 2026-11-21, exit 0:

```
r6_buyer_scenarios.py. Currency CHF. 1 USD = 0.8392 CHF, 1 GBP = 1.1015 CHF (ECB 20 Nov 2026).
Policy = r4_headline.HEADLINE; seeds [1, 2, 3]; means over seeds unless marked; missed = seed 1, 'x of y accepted jobs'.
Reference box: 4.19 GPU-h per 1 kW server-h (central wall power, ASSUMPTION). Installed cost (cold-plate chain, central): N=6 212,574, N=8 275,474 CHF.

== 1. Key figures per buyer scenario (computed) ==
scenario    N offer sh/d  Jan/Jul   cover   util  sold sh   J1 sh   J2 sh   acc% sumJ1%    missed (seed 1)      BE  BE+rst starts
shaped100   6       81.8      9.6  73.67%  54.7%   28,761  14,101  14,660  94.7%   89.6      0 of   31,908  0.2261  0.2278    854
shaped100   8       95.9     12.4  86.14%  48.0%   33,626  16,333  17,293  93.8%   90.3      0 of   36,771  0.2261  0.2286  1,497
flat        6       81.8      1.0  53.67%  39.9%   20,952   9,335  11,616  64.1%    0.0      0 of   21,650  0.2261  0.2334  2,632
flat        8       95.9      1.0  60.48%  33.7%   23,612  10,688  12,924  62.4%    0.0      0 of   24,658  0.2261  0.2338  3,102
llm_flat    6       81.8      1.0  53.11%  39.4%   20,733       0  20,733  70.0%    n/a      0 of    5,198  0.2261  0.2315  1,944
llm_flat    8       95.9      1.0  60.86%  33.9%   23,760       0  23,760  68.2%    n/a      0 of    5,913  0.2261  0.2318  2,339
llm_shaped  6       81.8      9.6  74.13%  55.1%   28,940       0  28,940  97.2%    n/a      0 of    7,229  0.2261  0.2274    664
llm_shaped  8       95.9     12.4  86.04%  47.9%   33,588       0  33,588  96.0%    n/a      0 of    8,397  0.2261  0.2283  1,294
flat_july   6       15.0      1.0  14.00%  10.4%    5,467   2,742   2,726 100.0%  100.0      0 of    6,121  0.2261  0.2487  1,984
flat_july   8       15.0      1.0  14.00%   7.8%    5,467   2,742   2,726 100.0%  100.0      0 of    6,121  0.2261  0.2487  1,985
pool        6      144.0      1.0  79.22%  58.8%   30,925  14,135  16,790  54.9%    0.0      0 of   32,487  0.2261  0.2269    435
pool        8      192.0      1.0  92.84%  51.7%   36,242  16,822  19,420  49.2%    0.0      7 of   38,357  0.2261  0.2275    906

== 2. What the operator receives: income, payback and share of list needed vs available (computed) ==
  need = (electricity - heat) + installed / 5 y (simple payback, no interest, cold-plate chain central).
  list = US public batch list value of the sold work (r4_machine central prices); 'avail' = anchor income / list.
scenario    N  need/yr need/sh   list/yr   op%   5y% | anchor      inc/yr  CHF/sh  avail% payback y
shaped100   6    49.0k   1.704    404.7k  1.6% 12.1% | list20       80.9k   2.814   20.0%       2.9
                                                         | rent041      33.2k   1.153    8.2%       8.0
                                                         | rent048      38.8k   1.350    9.6%       6.6
                                                         | rent072      58.2k   2.025   14.4%       4.1
                                                         | heata_t2    157.9k   5.491   39.0%       1.4
shaped100   8    62.7k   1.865    470.2k  1.6% 13.3% | list20       94.0k   2.797   20.0%       3.2
                                                         | rent041      38.8k   1.153    8.2%       8.8
                                                         | rent048      45.4k   1.350    9.7%       7.3
                                                         | rent072      68.1k   2.025   14.5%       4.6
                                                         | heata_t2    184.7k   5.491   39.3%       1.6
flat        6    47.3k   2.255    277.1k  1.7% 17.1% | list20       55.4k   2.645   20.0%       4.2
                                                         | rent041      24.2k   1.153    8.7%      10.9
                                                         | rent048      28.3k   1.350   10.2%       9.0
                                                         | rent072      42.4k   2.025   15.3%       5.6
                                                         | heata_t2    115.1k   5.491   41.5%       1.9
flat        8    60.4k   2.559    315.4k  1.7% 19.2% | list20       63.1k   2.672   20.0%       4.8
                                                         | rent041      27.2k   1.153    8.6%      12.6
                                                         | rent048      31.9k   1.350   10.1%      10.4
                                                         | rent072      47.8k   2.025   15.2%       6.5
                                                         | heata_t2    129.7k   5.491   41.1%       2.2
llm_flat    6    47.2k   2.277     99.9k  4.7% 47.2% | list20       20.0k   0.964   20.0%      13.9
                                                         | rent041      23.9k   1.153   23.9%      11.1
                                                         | rent048      28.0k   1.350   28.0%       9.1
                                                         | rent072      42.0k   2.025   42.0%       5.7
                                                         | heata_t2    113.9k   5.491  113.9%       1.9
                                                         | Swiss list (Ministral-3-14B, J2): 1,637.1k CHF/yr list value; 5-y share needed 2.9% (vs 47.2% of the US batch list)
                                                         | Swiss list (Gemma-4-31B, J2): 1,190.6k CHF/yr list value; 5-y share needed 4.0% (vs 47.2% of the US batch list)
llm_flat    8    60.5k   2.545    114.5k  4.7% 52.8% | list20       22.9k   0.964   20.0%      15.7
                                                         | rent041      27.4k   1.153   23.9%      12.5
                                                         | rent048      32.1k   1.350   28.0%      10.3
                                                         | rent072      48.1k   2.025   42.0%       6.4
                                                         | heata_t2    130.5k   5.491  113.9%       2.2
                                                         | Swiss list (Ministral-3-14B, J2): 1,876.2k CHF/yr list value; 5-y share needed 3.2% (vs 52.8% of the US batch list)
                                                         | Swiss list (Gemma-4-31B, J2): 1,364.5k CHF/yr list value; 5-y share needed 4.4% (vs 52.8% of the US batch list)
llm_shaped  6    49.1k   1.695    139.5k  4.7% 35.2% | list20       27.9k   0.964   20.0%      10.0
                                                         | rent041      33.4k   1.153   23.9%       7.9
                                                         | rent048      39.1k   1.350   28.0%       6.5
                                                         | rent072      58.6k   2.025   42.0%       4.1
                                                         | heata_t2    158.9k   5.491  113.9%       1.4
                                                         | Swiss list (Ministral-3-14B, J2): 2,285.1k CHF/yr list value; 5-y share needed 2.1% (vs 35.2% of the US batch list)
                                                         | Swiss list (Gemma-4-31B, J2): 1,661.9k CHF/yr list value; 5-y share needed 3.0% (vs 35.2% of the US batch list)
llm_shaped  8    62.7k   1.866    161.9k  4.7% 38.7% | list20       32.4k   0.964   20.0%      11.1
                                                         | rent041      38.7k   1.153   23.9%       8.8
                                                         | rent048      45.3k   1.350   28.0%       7.3
                                                         | rent072      68.0k   2.025   42.0%       4.6
                                                         | heata_t2    184.4k   5.491  113.9%       1.6
                                                         | Swiss list (Ministral-3-14B, J2): 2,652.2k CHF/yr list value; 5-y share needed 2.4% (vs 38.7% of the US batch list)
                                                         | Swiss list (Gemma-4-31B, J2): 1,928.9k CHF/yr list value; 5-y share needed 3.3% (vs 38.7% of the US batch list)
flat_july   6    43.8k   8.002     78.1k  1.6% 56.0% | list20       15.6k   2.856   20.0%      14.8
                                                         | rent041       6.3k   1.153    8.1%      41.9
                                                         | rent048       7.4k   1.350    9.5%      34.6
                                                         | rent072      11.1k   2.025   14.2%      21.6
                                                         | heata_t2     30.0k   5.491   38.5%       7.4
flat_july   8    56.3k  10.303     78.1k  1.6% 72.2% | list20       15.6k   2.856   20.0%      19.2
                                                         | rent041       6.3k   1.153    8.1%      54.3
                                                         | rent048       7.4k   1.350    9.5%      44.8
                                                         | rent072      11.1k   2.025   14.2%      28.0
                                                         | heata_t2     30.0k   5.491   38.5%       9.6
pool        6    49.5k   1.601    415.7k  1.7% 11.9% | list20       83.1k   2.689   20.0%       2.8
                                                         | rent041      35.7k   1.153    8.6%       7.4
                                                         | rent048      41.8k   1.350   10.0%       6.1
                                                         | rent072      62.6k   2.025   15.1%       3.8
                                                         | heata_t2    169.8k   5.491   40.9%       1.3
pool        8    63.3k   1.746    492.0k  1.7% 12.9% | list20       98.4k   2.715   20.0%       3.1
                                                         | rent041      41.8k   1.153    8.5%       8.2
                                                         | rent048      48.9k   1.350    9.9%       6.8
                                                         | rent072      73.4k   2.025   14.9%       4.2
                                                         | heata_t2    199.0k   5.491   40.4%       1.4

== 3. Refused work and a typed partner site for it (computed; pool figures SOURCED x area ASSUMPTION) ==
  heated outdoor 50 m pool, 1,050 m2 (ASSUMPTION) x 430-480 kWh/m2 per 120-day season: 3,762-4,200 kWh/day = 157-175 kW average = 196-219 servers' recovered heat (0.8 kW each)
  typical indoor pool, July: 24,000 kWh/month = 774 kWh/day = 40 servers; Leafcloud minimum host: 500 GJ/yr = 381 kWh/day = 20 servers
scenario    N refused sh/yr heat MWh/yr sum J1 ref sh/d heat kWh/d houses per outdoor pool per indoor pool (Jul)
shaped100   6         1,031         0.8             0.8        0.6         6,021-6,722                     1,239
shaped100   8         1,483         1.2             0.7        0.6         6,469-7,221                     1,331
flat        6         8,997         7.2            40.9       32.7           115-128                          24
flat        8        11,367         9.1            48.0       38.4            98-109                          20
llm_flat    6         8,908         7.1     n/a (no J1)
llm_flat    8        11,069         8.9     n/a (no J1)
llm_shaped  6           823         0.7     n/a (no J1)
llm_shaped  8         1,392         1.1     n/a (no J1)
flat_july   6             0         0.0             0.0        0.0          (none refused)                     -
flat_july   8             0         0.0             0.0        0.0          (none refused)                     -
pool        6        21,510        17.2            72.0       57.6            65-73                           13
pool        8        33,121        26.5            96.0       76.8            49-55                           10
```

(Footnote lines of the printout trimmed here; run the command for the full text.)

### Reading

- **Coverage is set by the buyer's shape, not by the job mix.** LLM-only heat-shaped (74.1% / 86.0%) ≈ the 50/50 headline (73.7% / 86.1%); LLM-only flat (53.1% / 60.9%) ≈ the 50/50 flat (53.7% / 60.5%). A flat customer at the same yearly volume loses 20–26 coverage points and refuses 30–38% of its jobs; a flat customer sized so that nothing is ever refused (the July rate) covers **14.0%** and needs 8.00–10.30 CHF per sold hour to pay back in 5 years.
- **"Missed" stays 0 in every buyer scenario at N=6** (seed 1), and 7 of 38,357 only in the N=8 pool case. That is still by construction: admission refuses what it cannot finish. The honest companion number is the **refused share**, which ranges from 3–6% (heat-shaped) to 30–38% (flat).
- **Break-even 0.2261 CHF is the same for every buyer** (never-dump policy); with the 15-minute restart line it rises with the number of starts, worst for the July-sized flat customer (0.2487).
- **Share-of-list framing exaggerates job-mix effects.** At the US batch list, LLM-only needs 35–53% of list and transcription-heavy work 12–19%. Priced per rented hour, the same hours pay back the same; the difference between scenarios is then only sold hours: 28,761 (headline) vs 20,952 (flat) vs 30,925 (pool) at N=6.
- **What would make the 2.7-year line true:** ~2.8 CHF per sold server-hour net to the operator, i.e. 1.4× RunPod's Secure Cloud host share or 2.4× the cheapest listed rental. Only Heata's own **list** price clears that, and Heata's accounts suggest that list is not what it sells at.

---

## (d) Recommendation

**Honest headline buyer framing (two sentences, for the pitch):**

> "Jobs per day is a contract we sized to the house's own heat, not a customer we found: every batch buyer we could find waits hours to a week, none waits a season, so the house sells server-hours into a pool that takes whatever hours its heat allows, the way Heata backs its homes with cloud capacity. At today's GPU-rental host rates that is 1.15 to 2.03 francs per server-hour, which pays the installed servers back in about 4 to 8 years with our contract and 6 to 11 years with a single flat customer; below 1.70 francs per sold hour it does not pay back in five."

**Q&A, "Who actually buys this in July?":**

> "In July the house only has heat room for about 15 server-hours a day, a tenth of January, so there is little to sell: batch buyers whose work can wait 24 hours to 7 days, like OpenAI's or Groq's batch tiers, take what the tank can absorb. Work the house can't take is refused at intake and never started. Under our contract that is under one server-hour a day per house; with a flat customer it is about 41, and that goes to a site that needs heat in summer, for example a heated outdoor pool like St. Jakob's 50 m pool, where one season's heating is about 200 servers' worth, enough for the refused summer work of about a hundred houses. That pool's servers are outside our house balance and sit idle in winter, and we haven't found anyone who buys a season-shaped contract."

---

## Proposed changes to the plan

1. **Computing income (rounds 4–5 section and Key numbers):** keep "share needed" as the lead line, but replace the CHF scenario "80.9k / 94.0k at 20%, 2.7-year payback" with the **sourced rental-anchor line**: "at GPU-rental host rates of 1.15–2.03 CHF per server-hour (0.41/0.48/0.72 USD per GPU-hour × 80%), headline payback 4.1–8.0 years at N=6 (4.6–8.8 at N=8); about 9.5 years if interruptible capacity sells at Vast.ai's 74% ratio" (*computed*, `python3 analysis/r6_buyer_scenarios.py`). Keep 20%-of-list only as a labelled scenario, corrected to the cold-plate chain: **2.9 / 3.2 years**, not 2.7 / 3.1.
2. **Offers label:** relabel `shaped100` from "contract … assumed to follow the weather" to **"work pulled from a pool at the house's expected heat capacity; the pool, not a customer, absorbs the ~10:1 seasonal swing (prior art: Heata's committed capacity with cloud-burst fallback)"**. No change to the CSV or the scheduler.
3. **Comparison lines:** add the `pool` line (79.2% / 92.8%, sold 30,925 / 36,242, payback 3.8–7.4 / 4.2–8.2 years at rental anchors) and the July-sized flat line (14.0%, never pays back in 5 years: 22–42 years) next to the existing flat line, whose payback at rental anchors is 5.6–10.9 / 6.5–12.6 years.
4. **LLM-only:** replace "LLM-only 32–36% of list, 9.5-year payback" with "priced per rented hour, LLM-only pays back like any other hour (heat-shaped 4.1–7.9 years at N=6); 32–36% is an artefact of the cheap US LLM batch list". Note that a Swiss-resident list price exists at 12–16× the US batch price per output token (Infomaniak, synchronous, larger models), with no buyer for basement capacity shown.
5. **Working idea and open risk 4:** replace "That other site … is not named yet" with the typed partner wording in section (b). Open risk 4 keeps: the partner's servers are outside the balance and idle off-season.
6. **"When the model does not pay off" (new bullet):** "below 1.70 CHF per sold server-hour (headline, 5 years, cold-plate chain), 2.26 with a flat customer, 8.00 with a flat customer sized to July; at the cheapest listed GPU-rental host rate (1.15–1.35 CHF) no buyer scenario pays back in 5 years."
7. **Five questions for DigitalHeat:** sharpen the fourth: "Would you sell hours into a pool or marketplace (spot), or finished jobs to named customers, and who holds the cloud fallback when the houses are full?"
8. **Prices are snapshots:** the cheapest RTX PRO 4500 rental on the same page moved from 0.41 USD (round 4, ~09:50) to 0.48 USD (~11:15) today. Quote ranges, not a single price.
9. **Build scope:** none. The scheduler's existing accepted share gives the refused share (1 − accepted); show it beside "missed" as "refused at intake".

## Weak points of this work

- Rental anchors are data-centre, always-on prices; host share (80%) and the 0.74 interruptible ratio were not re-opened this round; the ratio is for an RTX 4090 on another marketplace.
- Heata's prices are list prices with no effective date; Heata's filed figures were not re-opened by me.
- The pool water area (1,050 m²) is assumed; the indoor-pool monthly figures are read from a bar chart by eye; the MuKEn reading for server heat is unverified; Basel's other pools were not checked.
- Summer refused J1 is an expectation (offered rate × refusal share), not counted month by month in the run; J2 summer refusals are not counted.
- The `pool` scenario uses saturating offers, so its "refused" is unlimited backlog, not lost work; its 54.9% / 49.2% accepted share must not be read as refused customer jobs.
- Payback is simple, no interest, 5 years, constant prices, cold-plate chain central (212,574 / 275,474 CHF), as in the plan.
- Infomaniak prices are for different models than our MLPerf row; the 6:1 input ratio is the plan's assumption.

## Commands

```
python3 analysis/r6_buyer_scenarios.py
# web pages opened (WebFetch): developers.openai.com/api/docs/guides/batch; console.groq.com/docs/batch;
#   docs.cloud.google.com/compute/docs/instances/spot; cloud.google.com/blog/products/infrastructure/using-demand-response-...;
#   docs.heata.co/pricing-billing/; heata.co/free-hot-water; heata.co/render/mediacymru; leaf.cloud/leafsites/;
#   theregister.com/2023/03/14/cloud_startup_waste_heat_dcs/; getdeploying.com/gpus/nvidia-rtx-pro-4500;
#   runpod.io/gpu-models/rtx-pro-4500-se; ecb.europa.eu (reference rates); bs.ch (Gartenbad St. Jakob)
# Heata SLA PDF: fetched by WebFetch, pages 1-4 read as images
# Infomaniak: curl -sL -A "Mozilla/5.0" https://www.infomaniak.com/en/hosting/ai-services/prices, tags stripped (python3 -I)
# BFE/VHF Leitfaden: curl -sL https://pubdb.bfe.admin.ch/de/publication/download/9728; pdftotext; pages 29, 151, 155-156 read as images
# hand checks: python3 -c (interruptible ratio 0.74 -> 1.00 CHF/sh, payback 9.5 y; Swiss/US J2 price ratio 16.4 / 11.9)
```
