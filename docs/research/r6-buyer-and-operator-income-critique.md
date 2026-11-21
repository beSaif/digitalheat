# Critique of round 6: who buys a heat-shaped contract, and what the operator receives

Critic for weak point 2 of round 6, written Sat 21 Nov 2026 at about 11:15–11:40. The role is a sceptical DigitalHeat founder. Under review: [r6-buyer-and-operator-income.md](r6-buyer-and-operator-income.md) and `analysis/r6_buyer_scenarios.py`. Nothing was edited. Firecrawl calls used: **0 of 1**. Currency: CHF. The rates are the ECB reference rates of 20 Nov 2026 (re-opened: USD 1.0990, GBP 0.83735, CHF 0.9223 per EUR), so 1 USD = 0.8392 CHF and 1 GBP = 1.1015 CHF.

## Verdict in one paragraph

The sources hold up. Every URL I opened says what the investigator quotes, with three wording fixes: Heata's GPU surcharges are "from" prices on top of vCPU and RAM; getdeploying's 0.41 USD anchor is no longer on the page; and the 0.92 USD median is across 27 configurations, not 7 providers. The script reproduces exactly: `python3 analysis/r6_buyer_scenarios.py` gives byte-identical tables, about 5 s wall. The problems are framing, not arithmetic.

1. **"Pool" is the declared unlimited-jobs case under a new name.** In `r2_deadline_sim`, "saturating" means "the declared 'unlimited jobs' case". No buyer for heat-gated hours at full rental rates was shown. Heata's evidence also points the other way: Heata itself buys cloud capacity (Cloud Burst Nodes) to keep its SLA, and the model does not count that cost.
2. **Paybacks credit the heat to the operator, while the investigator's own evidence says operators give it away.** Heata, Leafcloud and Deep Green all do. With heat given free, every payback gets longer.
3. **The July-sized customer is a strawman.** It is run on 6 servers. On 1 server it needs 2.27 CHF per sold hour, not 8.00.
4. **The typed partner site is a summer-only outdoor pool, which is not the year-round user the task asked for.** Heating it takes about 7 M CHF of servers that sit idle for 8 months.
5. **The proposed Q&A answer calls OpenAI and Groq batch tiers "buyers" of the house's hours.** They are sellers of batch inference and buy no third-party capacity.

## Source checks (all opened by me on 21 Nov 2026)

| Claim | Opened | Result |
|---|---|---|
| c1 OpenAI Batch | developers.openai.com/api/docs/guides/batch | "50% cost discount"; "the completion window can only be set to `24h`". OK |
| c2 Groq | console.groq.com/docs/batch | 50%; "from 24 hours to 7 days"; expired and billed only for completed requests. OK |
| c3 GCP Spot | docs.cloud.google.com/compute/docs/instances/spot | "up to 91%"; 120 s or 0 s (default); "fault-tolerant workloads, such as batch processing". OK |
| c4 Google demand response | cloud.google.com/blog/... | 4 Oct 2023; YouTube processing and Translate; "for the duration of the grid event"; rescheduled afterwards or rerouted. OK |
| c6 Heata SLA | PDF, text extracted with `pdftotext` | "Last Updated: August 2026"; Committed Capacity >99.5%; credits of 10/25/100% below 99.5/95/90%; "we may use cloud instances (Cloud Burst Nodes)"; Access Nodes in GCP. **Also on p. 4: Heata may use a client's idle allocated capacity "to ensure reasonable hot water delivery".** In other words, Heata fills its homes with its own work and backs its clients with cloud. Heata absorbs the swing itself, at its own cost. |
| c7 Heata prices | docs.heata.co/pricing-billing | £0.017 / £0.010 per vCPU-hour; GPU Tier 1 "from £0.89", Tier 2 "from £1.19"; **the surcharge is "billed on top of vCPU and RAM"**; RAM £0.0025 per GB-hour; no GPU spot price; no effective date. The Tier-2 examples are RTX 5090, A100 40 GB and RTX 6000 Ada, all faster than our card. |
| c8 Heata host | heata.co/free-hot-water | Heata pays the electricity through a submeter credit; hosts save £150–350 a year; nothing about a compute-income share. OK |
| c9 Leafcloud | leaf.cloud/leafsites | Leafcloud meters and pays the power; 630–3,780 GJ a year; minimum 500 GJ a year; 5–20% of design load; 20–120 kW; 45–65 °C; hosts: "swimming pools, nursing homes, apartment buildings, hospitals, office complexes". OK |
| c10 Deep Green | theregister.com 2023/03/14 | 62% is *expected*; over £20,000 a year; "a dozen servers"; free installation, and Deep Green pays electricity and maintenance. OK |
| c11 Heata render farm | heata.co/render/mediacymru | £2 per GPU-hour, RTX 4090 at 450 W, Y Bank in Caerphilly. OK |
| c12 getdeploying | getdeploying.com/gpus/nvidia-rtx-pro-4500 | Cheapest today is Lium at 0.48 USD, **a sponsored listing**. GPU.ai now lists 0.54, so **the 0.41 anchor is gone**. The median 0.92 is "across 27 on-demand configs from 7 providers". No spot prices. Which card edition the prices refer to is ambiguous. |
| c13 RunPod | runpod.io/gpu-models/rtx-pro-4500-se | 0.72 USD Secure Cloud; Community Cloud blank; 165 W, passive, data-centre card, which matches the Server Edition. OK |
| c14 ECB | ecb.europa.eu | 20 Nov 2026: 1.0990 / 0.83735 / 0.9223. OK |
| c27 BFE p.156 | pubdb.bfe.admin.ch/.../9728, page image | 430–480 kWh/m² per season, mid-May to mid-September, about 120 days, 24 °C, "nicht windexponierte Lagen"; 215–240 with a cover. OK. **But p.155 says "Ein Grossteil der Wärmeenergie wird für die Erstaufheizung im Frühling benötigt"**: most of the season's heat goes into the spring first heat-up. The 120-day average therefore overstates July demand. |
| c28 MuKEn | same PDF, p.155 image | The quote is exact. The omitted next sentence: "Elektrische Wärmepumpen dürfen eingesetzt werden, wenn eine Abdeckung der Wasserfläche … vorhanden ist". So a covered pool may use a heat pump, which competes with server heat. |
| c29 indoor-pool chart | same PDF, p.29 image | Jan about 71k, Feb about 73k, Jul about 24k, Aug about 18k. The text names closures and revisions as part of the yearly shape, so the summer dip is partly the pool being shut. |
| c30 St. Jakob | bs.ch | "Beheiztes 50m-Wettkampfbecken"; Sportbad 25 April to 4 October; no width; no heat source given. OK |
| c33 Infomaniak | curl of the price page, tags stripped | Ministral-3-14B 0.30 / 0.40, Gemma-4-31B 0.20 / 0.40 CHF per M tokens; Whisper CHF 0.006 per minute "of generation"; "Prices do not include VAT". OK |

## Re-run and critic probe

`python3 analysis/r6_buyer_scenarios.py` matches the investigator's printout exactly. Probe (scratch script, not kept): `python3 <scratchpad>/r6buyer_critic_py/r6buyer_critic_probe.py`. It imports `r6_buyer_scenarios`, `r4_headline` and `r5_chain` read-only, uses seed 1, and the cold-plate chain.

**1. Heat given free to the host (the operator pays all the electricity), as Heata, Leafcloud and Deep Green actually do.** Payback in years, rental anchors 0.41 / 0.48 / 0.72 USD:

| Scenario | N | Need per sold h (heat credited → free) | rent041 | rent048 | rent072 |
|---|---|---|---|---|---|
| shaped100 | 6 | 1.714 → **1.820** | 8.0 → 9.1 | 6.6 → 7.3 | 4.1 → 4.4 |
| shaped100 | 8 | 1.872 → 1.979 | 8.9 → 10.0 | 7.3 → 8.1 | 4.6 → 4.9 |
| flat | 6 | 2.260 → 2.367 | 11.0 → 12.4 | 9.0 → 10.0 | 5.7 → 6.0 |
| pool (= unlimited) | 6 | 1.603 → 1.709 | 7.4 → 8.4 | 6.1 → 6.8 | 3.8 → 4.1 |

The case's break-even formula (electricity − heat value) is a system view and stays on the tile. An *operator* payback has to say who keeps the heat. The plan already prints "0.3325 if the homeowner keeps the heat", and the investigator's paybacks quietly assume the opposite.

**2. July-sized flat customer (15 server-h a day) on fewer servers:**

| N | Coverage | Utilisation | Sold h | Installed CHF | Need per sold h | Payback, rental anchors |
|---|---|---|---|---|---|---|
| 1 | 13.87% | 61.8% | 5,415 | 55,324 | **2.27** | **11.0 / 9.1 / 5.7 y** |
| 2 | 13.87% | 30.9% | 5,416 | 86,774 | 3.43 | 17.3 / 14.3 / 8.9 y |
| 6 | 13.87% | 10.3% | 5,416 | 212,574 | 8.08 | 42.3 / 34.9 / 21.8 y |

Nobody installs 6 servers for a July-sized customer. The fair comparison is N=1: low coverage, but hardware that pays back about as well as the flat customer at N=6.

**3. Partner outdoor pool, capital (heat given free to the pool, which runs 120 days × 24 h at full load):** 157–175 kW is 196–219 boxes × about 35,400 CHF (the N=6 house's installed cost ÷ 6, an *assumption*), so **about 7.0–7.8 M CHF**. Summer-only margin at the rental anchors gives a **7.3–15.0-year payback**. An outdoor pool is a worse site for servers than the house it is meant to relieve. A year-round user does better: an indoor pool, care home or hospital, all of which Leafcloud lists, with a minimum of 500 GJ a year, about 381 kWh a day, about 20 servers.

## Logic problems beyond the probe

- **No evidence the rental price applies.** The rental anchors price always-on data-centre GPUs. A marketplace host who withdraws capacity when a tank fills loses reliability scores and listings. Vast.ai's "interruptible" means the renter can be outbid, not that the host leaves. The investigator says so in A4, then uses those prices as the headline replacement anyway.
- **Rented hours are not heat.** A renter decides what runs on the GPU. A rented but idle 165 W card draws a fraction of that, so the scheduler no longer controls the heat in kWh. The 4.19 GPU-h per server-hour assumes full draw.
- **Occupancy is 100% by assumption.** The "pool" sells every permit hour. Marketplace hosts are paid only when rented, and no occupancy figure was sourced.
- **Prices are held constant for 5 years** on a GPU whose cheapest listed rate moved 17% in one morning. The decline over a GPU's lifetime is not modelled.
- **Heata's £340 trade debtors** (*team-sourced*) do not show "little volume". Year-end receivables can be small when customers prepay. The inference "list ≠ realised" may still be true, but this number does not support it.
- **"Pool" means two things.** It is both the aggregator and the swimming pool in the same Q&A answer. A jury will hear one word for two ideas.
- **The Q&A answer mixes scenarios.** It quotes the flat customer's 41 refused hours a day next to the headline's 0.8. The headline contract does not need a partner at all.

## Founder questions still unanswered

See the structured output. In short: who signs for heat-gated hours at always-on prices, who pays for the cloud burst in July, who keeps the heat, and why build a 7 M CHF server park for a pool that is closed 8 months a year.
