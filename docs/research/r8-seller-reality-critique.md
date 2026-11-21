# Critique, round 8: heat-gated hours versus seller reality

Critic for `docs/research/r8-seller-reality.md` and `analysis/r8_draw.py`. Role: a sceptical DigitalHeat founder. Written Sat 21 Nov 2026. This file assesses only. No existing file was changed and git was not touched.

**Currency:** CHF. 1 USD = 0.8392 CHF, re-opened by me: ECB `eurofxref-hist-90d.xml` (<https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml>), 20 Nov 2026, USD 1.099 and CHF 0.9223 per EUR, so 0.9223 / 1.099 = 0.8392.

**Firecrawl calls used: 0.** Temporary files are in the session scratchpad (`r8sellerreality_crit_dl/`, `r8-seller-reality-critic-run.txt`, `r8-seller-reality-critic-seeds3.txt`). None are kept.

## 1. Re-runs

- `python3 analysis/r8_draw.py` (seed 1, 36 s wall, exit 0) prints exactly what the investigator's file shows, in every section.
- `python3 analysis/r8_draw.py --seeds 3` (means of 3 seeds) moves nothing materially:

| Run | Seed 1 | 3-seed mean |
|---|---|---|
| N=6 coverage at d=0.7, headline contract | 52.39% | 52.62% |
| N=8 coverage at d=0.7, headline contract | 61.66% | 61.96% |
| p* at d=0.7, o=0.6 (N=6 / N=8) | 2.60 / 2.62 | 2.60 / 2.62 |
| Dumped at assumed-d 0.7 / 0.5, N=6 | 73 / 471 kWh | 85 / 483 kWh |
| Dumped at assumed-d 0.7 / 0.5, N=8 | 918 / 1,523 kWh | 936 / 1,531 kWh |

- **Patch check.** I checked that the patches really reach the code that runs.
  - `r4_headline.run` reads the module globals `Q1` (tank, dry run, execution) and `P_EL` (electricity).
  - `r3_policy_check.step_permit` reads its own global `Q1`.
  - `r2_deadline_sim.offer_rates` keeps `R.Q1` = 0.8, so the contract stays sized at full draw, as described.
  - Every task resets all four patched attributes, so worker reuse cannot leak state between runs.
  - Operation-only break-even is exactly 0.2261 × d, which shows that both electricity and heat moved with d.
  - Conclusion: the computed numbers are what the code says they are.

## 2. Sources re-opened

- **Azure Retail Prices API**, Switzerland North, filter `contains(armSkuName,'RTXPRO6000')`: Linux consumption prices for NC144lds_xl are 7.865 USD on-demand and 1.453452 USD Spot. NC144ds_xl is 9.123 / 1.68593 and NC288lds_xl is 15.73 / 2.906904. The ratio is 0.185 for all three. **Confirmed.** Microsoft Learn confirms 1 GPU for NC144(l)ds_xl and 2 GPUs for NC288.
- **gcloud-compute.com g4-standard-48**: 4.4999 / 1.7178 (us-central1) and 4.9499 / 2.0496 (europe-west4), 1 × RTX PRO 6000, "Last Update: Wed Nov 18 16:45:26 2026". **Confirmed**, with two limits: it is a third-party aggregator, and the page as fetched does not print a currency. Google's own Spot page exceeded the fetch limit (10 MB).
- **salad.com/pricing**: RTX 4090 at 0.440 (High), 0.347, 0.253 and 0.160 (Lowest, Batch). High is "Still subject to node disconnection". **Confirmed.** These are priority tiers, not on-demand versus spot.
- **runpod.io/gpu-models/rtx-pro-4500-se**: 0.72 USD/h Secure Cloud, 165 W, no spot price listed. **Confirmed.** This price is the input to the "same work 2.53 CHF" figure.
- **POLCA**, par.nsf.gov PDF via pdftotext: Table 4 gives "Peak power utilization" of 97% for training and 79% for inference, for an interactive inference cluster, normalised to provisioned row power. The paper also says "rated power for the DGXA100 machine is 6500W … never exceeded 5700W". **Confirmed**, but both figures are **peaks**, not average draw.
- **Splitwise** (arXiv 2311.18677v2): the quote is exact. **Confirmed.**
- **The 1/W Law** (arXiv 2603.17280v1): the 43% and 86% TDP figures are on the page, attributed to Chung et al. 2026 and tied to the H100-SXM5. The primary was not verified. This **stays unverified**.
- **E2E Networks**, 27 Mar 2026: L4 rated "72W". Whisper-large-v3-turbo fp16/bf16 averages 64.9–72.3 W over batch sizes 1–32. INT8 is **50.9 W at batch size 1 but 61.6 W at batch size 8** (86%). **Confirmed, with a correction**: "INT8 71%" holds only at batch size 1.
- **Weng et al., NSDI '22**: median request 0.5 GPU, median SM usage 0.042 GPU. **Confirmed.** This is utilisation, not power.
- **heata.co/free-hot-water**: both quotes are exact. **Confirmed.**
- **AWS spot.js**: `last-modified: Mon, 13 May 2024 17:03:35 GMT`. **Confirmed.**

## 3. Where the result breaks or overreaches

1. **Transferring the 0.185 ratio to RunPod is not a price.**
   - The Azure ratio is measured against Azure's own on-demand price. Per unit of work, that is 7.865 × 2.383 × 0.8392 = 15.7 CHF, about 6× RunPod's 2.53.
   - Hyperscaler spot for the same work (2.91) lands almost exactly on RunPod on-demand (2.53). The 0.185 discount mostly removes a hyperscaler mark-up that RunPod never had.
   - Applying 0.185 to RunPod gives 0.47 CHF, a price no market we found sells at. Salad's 0.364 is a marketplace's own tier ratio, so it transfers better (0.92). The Google ratio is also a hyperscaler ratio.
   - **Keep the conclusion and drop the number.** The conclusion needs no ratio at all: at o = 0.6, the same work rents *uninterrupted* for 2.53, below p* 2.84 / 3.09.
2. **"Below every price needed" only holds at 60% occupancy.**
   - At o = 1.0, p* is 1.56–1.95. RunPod on-demand (2.53), hyperscaler spot (2.91–4.10) and Exoscale × Google ratio (1.86–2.02) all clear it.
   - The honest form is: "at 60% occupancy of heat-permitted hours, no price-shopping buyer pays enough; only if every permitted hour sells does it clear, and 100% occupancy of hours that disappear for months is not credible."
3. **"Heat problem, not an income problem" is a framing that a founder will push on.**
   - The price needed per sold hour falls only because renters are assumed to pay the full hourly price for a box drawing 50–70%, and because more such hours fit into each kWh of heat.
   - For the homeowner it is a value problem. At d = 0.5, the backup heater supplies 63% of the heat (N=6). If DigitalHeat sells heat (heat as a service), lost heat is lost revenue.
   - The plan should say "lowers coverage roughly in proportion to draw; it does not raise the price needed per sold hour", not "not an income problem".
4. **A power cap does not solve the case that actually happens.**
   - A cap stops overshoot, which is the section-3b failure. Under-draw is the realistic case (serving renters, idle reservations), and it is lost heat that cannot be recovered in cold hours, because all N servers already run.
   - The obvious fix is to top up permitted but unused kWh with the operator's own J1/J2 batch work (GPU sharing) or with "unsold hours as heaters" (+0.15 CHF). Neither is costed.
   - Also, "metered draw" is known only after the hour runs. Admission over a 7-day horizon needs a forecast of draw. The model gives the scheduler the true d for the whole year.
5. **The draw figures are mostly peaks or one card at its limit.**
   - POLCA's 79% and 87.7% are peak figures.
   - The E2E figures come from a 72 W L4 pinned at its power limit, which says little about a 165 W RTX PRO 4500.
   - 43% and 86% are unverified (secondary source, H100).
   - So "offline batch 86–100%" mixes one verified range (90–100%, L4, vendor blog) with an unverified 86%. No source gives an average draw for rented GPUs. The 90/70/50 grid is an assumption.
6. **The 3b stress is crude.**
   - It uses a fixed wrong draw for the whole year, under the plan's own band rule.
   - Its useful message is qualitative: never count permits in server-hours with a guessed draw. The kWh figures are illustrative only.
7. **The positioning sentence says "never"**, but forecast errors can still dump heat (the plan's 0 kWh rests on the 2 K guard). Write "not run with its heat thrown away". The sentence is also about 57 words (about 20–25 s), not about 40 words / 15 s. Shorten it.
8. **Retiring the local-dump option must not hide its number.** The cheaper path (about 1.60 CHF needed, versus 2.15 with RunPod or 2.74 with Swiss cloud fallback) is the price of the principle. The Feasibility criterion rewards stating it. Keep it as "what refusing costs", not as an option.

## 4. Build scope

Nothing here adds build scope if the plan follows the recommendation not to build a draw parameter. Agreed: the case fixes 1 kW per running server.
