# Round 7 critique: economics with a real seller form

Critic for `docs/research/r7-seller-form-economics.md` and `analysis/r7_payback.py`. Written Sat 21 Nov 2026. I edited nothing. My probes ran from a scratch file outside the repo that imports `r7_payback`, `r6_buyer_scenarios`, `r4_headline` and `baseline_sweep` read-only; the probe code and its full output are reproduced below. **Firecrawl calls: 0.** No personal or team names in any request.

Currency: CHF, at the investigator's rates (1 USD = 0.8392 CHF, ECB 20 Nov 2026, not re-opened).

## What holds

- **Re-run:** `python3 analysis/r7_payback.py` (3 seeds, 3 s wall) prints every number in the research file, byte for byte in the tables I compared (sections 0–6).
- **Regression check:** the "plan basis" figures (3.8 / 4.2 y) match round 6's `pool` / `rent072` rows (`docs/research/r6-buyer-and-operator-income.md` lines 205 and 210).
- **Formula:** p* = (I/L + K + e·(A+oS) + c_f·(V−A)) / (V+oS) is algebraically right for straight-line capital recovery, and margin = 0 at p* for L-year payback.
- **Web sources, all opened by me on 21 Nov 2026:**
  - salad.com/pricing: RTX 4090 at 0.440 / 0.347 / 0.253 / 0.160 USD; High tier "Still subject to node disconnection; SCE reallocates automatically"; "Owners are paid for idle time"; homes and small businesses.
  - docs.vast.ai/host/hosting-overview: "you cannot take the machine offline until every active rental contract has ended".
  - Heata SLA PDF (curl + pdftotext): lines 18–19, 185–187, 197–201 and 261–263 as quoted. No burst price; the only cost row reads "Included / Request a Quote".
  - Heata blog, 23 Feb 2024: ">50% on each node in any given month".
  - Akash blog, 9 Jan 2026: "60% average GPU utilization rate". The post does not define utilisation.
  - TokenPost, 22 May 2026, Q1 2026, citing Messari of 15 May: 33.7%.
  - RunPod RTX PRO 4500 SE: 0.72 USD Secure on-demand.
  - Exoscale price API: `chf/eur/usd running_gpurtx6000pro_large` = 8.19444444 under all three keys. The page lists Large as 4 GPU / 144 cores / 480 GB, and the zone footnote for the RTX Pro 6000 block includes CH-DK-2.
- **Decision (c):** showing no payback, and instead the price needed per sold hour at a stated occupancy, is the right call. I accept the reasoning.

## What breaks or needs a caveat

### 1. The cloud fallback is a dominated option, so F2's conclusion is wrong as stated (biggest flaw)

The plan already prices the alternative. Under "Run policy", a dumped server-hour costs **0.3325 CHF** (electricity, no heat credit). Work refused for lack of heat in summer can run on the house's own idle servers with the heat dumped, at 0.33 CHF/h. RunPod costs 2.53 and Exoscale 4.88. The servers are free in summer: about 0.6 server-equivalents carry the hot-water load out of N = 6.

Probe output (*computed*, scratch probe below, central costs, 5 y, heat credited):

| F2 committed flat | N=6, o=0 | N=6, o=0.6 | N=8, o=0.6 |
|---|---|---|---|
| fallback Exoscale (investigator) | 3.24 | 2.74 | 2.93 |
| fallback RunPod (investigator) | 2.54 | 2.15 | 2.30 |
| **run in house, dump heat (0.3325/h)** | **1.87** | **1.60** | **1.72** |

At RunPod's renter price (2.53) with the dump fallback and Salad-ratio spot on the surplus, payback is **3.3 y (N=6) / 3.6 y (N=8)**. The investigator's Swiss-fallback line gives 8.7 / 11.3 y.

So these statements are false as written: "every refused-but-promised hour loses money" and "promising delivery moves the problem to the cloud bill". The true trade-off is different. A promised flat volume costs either dumped heat or cloud money. Dumping breaks the plan's "heat dumped 0 kWh" headline and its "heat is the admission ticket" idea, and the jury scores dumped heat first.

The honest statement: "a promised flat volume needs about 1.6 CHF per sold hour if refused work runs in the basement with the heat dumped (about 30% of the volume, about 7,200 kWh dumped a year at N=6), or 2.7 if it is bought from Swiss cloud."

The 7,200 kWh is my estimate: 8,998 refused server-h × 0.8 kWh recovered heat each. The dry cooler a dump needs is not costed. As an *assumption*, even 5,000 CHF per house adds only about 0.02 CHF per sold hour.

### 2. Occupancy below 100% silently contradicts the coverage headline

The plan says "an unsold permit hour: the server stays off". At 60% occupancy the house then gets roughly 60% of the server heat.

Pool coverage is 79.2% (N=6) and 92.8% (N=8) when every permit hour runs (*computed*). At o = 0.6 that drops to roughly **47.5% / 55.7%**, and at o = 0.337 to about 27% / 31%. This is a linear approximation, not simulated.

So the payback line and the coverage tile describe two different houses. The other option is to run unsold permit hours as plain heaters to keep coverage. With the heat credited that costs e·(1−o)/o per sold hour: **+0.15 CHF at o = 0.6** and +0.44 at o = 0.337. That makes the central p* about **2.99, not 2.84** (N=6).

The research file mentions neither. Either way, the pitch must say which house it is.

### 3. No cost of capital

p* uses I/L. A founder will discount. At N=6, o = 0.6, 5 years, p* is **3.19 at 5%** and **3.41 at 8%**, against 2.84 with no interest. At N=8 it is 3.48 / 3.73 against 3.09. All *computed* with the capital recovery factor (scratch probe below). The round-4 plan had 5%-interest variants; this line dropped them.

In the other direction, a VAT-registered operator would reclaim input VAT. Taking 8.1% out of I gives p* 2.66 / 2.89. This is a sensitivity; I did not check whether I includes VAT.

### 4. The Salad tier is mapped wrongly onto the host

Salad's tier is chosen by the **renter** ("Choose the priority tier per container group"), not set by the node. Even High tolerates node disconnection. A heat-gated Salad node would therefore serve High-, Medium-, Low- and Lowest-tier renters, not only Lowest.

"Spot host income = RunPod Secure × Lowest/High × 80%" (0.74 CHF) is a constructed price, not "Salad's ratio applied to a host". As an *assumption* (4090 price on a PRO 4500 box, 80% share not re-opened), Salad's own 4090 prices give 1.24 / 0.98 / 0.71 / 0.45 CHF per server-h by tier. Owner pay is unpublished.

The "59.6 years" line therefore rests on an assumption mix and should not be quoted as "Salad's spot price".

### 5. The "window" in the pitch sentence compares interruptible supply with an on-demand ceiling

4.88 CHF is Exoscale **on-demand** list. A buyer of capacity that leaves when the house is warm compares it with interruptible prices. Applying the same Salad Lowest/High ratio to 4.88 gives about **1.78 CHF**, below the 2.84 needed. This is an illustration, not a sourced price.

"Between 2.03 and 4.90" overstates the room. A sceptical founder reads the honest version as: the price needed sits above what interruptible GPU capacity fetches today.

### 6. "13–20% of what the same work costs at public batch prices" collides with "Swiss cloud charges about 4.90 for the same work"

The 14.25 CHF is the US token-API batch list value (`r4_machine.list_value`). Renting the GPUs for the same work costs 2.53 (RunPod) or 4.88 (Exoscale). In one breath the pitch would give three "costs of the same work". Keep share-of-list on a slide with its label ("of US batch API list prices"), and drop it from the spoken sentence.

The proposed two sentences are about 95 words, roughly 35–40 s of a 5-minute pitch. Too long.

### 7. Smaller points

- **Akash figure:** the TokenPost article's own averages, 84 used of 334 available, give **25.1%**, not 33.7%. The article does not define the 33.7%. The claim's parenthesis "(84 of 334 GPUs in use)" implies an identity that does not hold.
- **Comparability of the anchors:** both occupancy anchors are always-on leasing on one decentralised marketplace, with utilisation undefined. Neither is the occupancy of a node that is available only when a house wants heat. Expect worse, not better.
- **Card failures:** the PRO 6000 MTBF is applied to boxes priced with PRO 4500 cards (`CARD` central). Disclosed, but it is a mixed basis.
- **Payback beyond life:** every payback above the 5-year life means "does not pay back". The 7.7, 14.2 and 59.6 y figures should never be shown as if meaningful. The decline sensitivity (c21) is then moot for the central line.
- **Installed cost:** it includes a house-integration proxy taken from a 9 kW heat-pump installation (26,000–49,000 CHF). Avoided boiler or heat-pump capex is not credited. The house still needs its backup heater for 20–50% of demand. A founder will ask.

## Probe

Scratch script, kept outside the repo. Imports only, edits nothing. Run with `python3 r7sellercritic_probe.py` from the scratch directory, about 3 s. The essential lines:

```
F2: P.p_star(I, 5, K, e, V, A, S, o, c_f) with c_f in {4.882 exo, 2.531 runpod, 0.3325 dump}
interest: (I*crf + K + e*0.6*P) / (0.6*P), crf = r/(1-(1+r)**-5)
coverage: o x pool coverage (approximation)
```

Output (excerpt):

```
N=6: pool coverage 79.2% (all permit hours run)
  F2 o=0.6 fallback exo 2.74 | runpod 2.15 | dump 1.60     (o=0: 3.24 | 2.54 | 1.87)
  F1 o=0.6 5% interest p* 3.19 ; 8% 3.41 ; no interest 2.84 ; I excl. 8.1% VAT 2.66
  F2 direct072 + dump fallback + spot salad o=0.6: payback 3.3 y
N=8: pool coverage 92.8%
  F2 o=0.6 exo 2.93 | runpod 2.30 | dump 1.72 ; 5% 3.48 ; 8% 3.73 ; VAT-excl 2.89 ; dump payback 3.6 y
Salad 4090 tiers at 80% share as CHF per server-h: 1.24 / 0.98 / 0.71 / 0.45 ; Exoscale x 0.364 = 1.78 ; 84/334 = 25.1%
```

## Wording I would accept

**Pitch, spoken (one sentence plus one):**

> "Including the servers, maintenance and insurance over five years, every hour we sell must bring in about 2.80 francs if buyers take 60% of the hours the heat allows, and 1.80 if they take them all. GPU hosts get 1.35 to 2.03 francs for an always-on hour today, and we have not found a buyer for hours that come and go with the heat."

**Does not pay off when …:**

> "The model does not cover its running cost when a sold server-hour brings in less than 0.23 francs (0.33 if the homeowner keeps the heat). The servers do not pay back in five years below about 2.80 francs per sold hour at 60% occupancy of heat-permitted hours (1.80 at 100%; about 3.40 with 8% cost of capital), or if GPU-hour prices fall 10% a year. A promised flat volume needs about 1.60 francs if the refused 30% runs in the basement with its heat dumped, or 2.70 if it is bought from Swiss cloud. At 60% occupancy, with unsold hours left off, the servers cover only about half the heat demand instead of about four fifths."
