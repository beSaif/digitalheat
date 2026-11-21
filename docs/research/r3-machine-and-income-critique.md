# Critique, round 3: which machine, sold where, for what income

Critic for `r3-machine-and-income.md` (founder's view: servers, heating, compute markets). Written 2026-11-21. Paid Firecrawl calls used: **0**. Every page below was opened again by me with curl (text checked with grep) unless marked otherwise. Temp files went to my scratchpad with prefix `r3mi_crit_`.

## 1. Verdict in short

- **The sourcing holds.** Every price and every MLPerf number I re-opened matches: DeepInfra whisper turbo, Groq whisper turbo and the Groq batch terms, Together, DeepInfra Llama-3.1-8B, MLPerf v5.1 power rows, the Tom's Hardware post, and the ECB rates of 20 Nov 2026. Bedrock is now confirmed without Firecrawl, from AWS's public price-list file (section 3).
- **The scripts reproduce.** `python3 analysis/r3_income.py` gives the same numbers as the research file; only the source notes are shortened there. `python3 analysis/r3_mlperf_power.py --offline` gives 0.503 Wh per audio-hour and 56.07 million tokens per kWh. I checked the case formulas against the code: the break-even is 0.2261 per run hour and 0.3375 per sold hour at 67% sold. Both are right.
- **I reran the laptop probe once** (section 4). It gives **E = 1.32 Wh per audio-hour** (755 audio-hours per server-hour), against 1.50. Integrated over the whole span, the two trials give 1.38 and 1.52, so state 1.3 to 1.5.
- **Where it breaks is the meaning, not the arithmetic.**
  1. **The headline CHF 9.36 per server-hour (CHF 39,000 a year) mixes two machines that do not exist together.** J1 runs at laptop efficiency and J2 at the efficiency of a 9.4 kW, 8 × B200 machine with fp4 weights. The hardware check in section 7 then prices only the laptop-class J1. A laptop-class machine running Llama-8B gets nowhere near 15.6 tokens per joule. My order-of-magnitude guess is about 1 token per joule (*unverified*). At that rate J2 is worth about 0.5 CHF per server-hour, not 7.5, and the 50/50 central value drops to about 6 CHF.
  2. **Every permit hour is filled with paid-for work, so demand is unlimited.** Must-have 1 says such a model "must say so". The script does not. One house would transcribe 28,000 audio-hours a day, with no buyer named. That also contradicts the plan's finite-arrival deadline simulation, which accepts fewer jobs than it is offered.
  3. **The 0.35 to 6.7 Wh bracket rests on anecdotes.** The low end is a tweet with no stated power method (probably chip power only). The high end takes the 8-second run from the blog and the "+242 W" delta that the same page measured on a different, slow run, then assumes 1 kW for two cards. Keep it as an illustration, not as a measured range.
  4. **The pitch sentence "the work one server-hour does is listed at about 9 francs" is chosen to impress.** That 9 francs needs laptop-grade efficiency, which section 7 prices at 52,000 CHF per kW. For a 6,000 CHF per kW GPU rig the same calculation gives 2.5 CHF. A founder will ask "on which machine?" in the Q&A.
  5. **The price benchmark is US commodity APIs** (Groq, DeepInfra, Bedrock us-east-1). DigitalHeat's own slides sell "Switzerland, local data and operations" and "sovereign AI". No Swiss or data-residency price was checked, so the premium could go either way.

## 2. Claim verdicts

| ID | Verdict | Reason |
|---|---|---|
| c1 | survives | v5.1 `summary_results.json` downloaded and parsed: 5.1-0061 whisper Offline, Power_Result 7636.4895833333 W, 43698.6 "Samples/s", fp16, note "B200 TGP 1000W". |
| c2 | survives | 5.1-0062 llama3.1-8b Offline, 9436.05296875 W, 146960.0 Tokens/s, fp4. Server scenario 9011.07 W, 128,689 tokens/s. |
| c3 | survives | 1,448 rows, 24 with has_power. For whisper and llama3.1-8b the only power rows are the two Lenovo 8 × B200 systems; the others are Lenovo LLM/rgat/SDXL rows and a Ryzen mini PC running resnet. |
| c4 | survives with caveat | Loadgen summary re-read: "Samples per second: 688.623", "Tokens per second: 43698.6". mlperf.conf: 1,633 samples. README: dev-clean + dev-other "approximately 10 hours", repackaged into "samples approaching 30s" and **zero-padded to 30 s**. So 0.37 to 0.50 Wh per audio-hour, and the model is large-v3, not turbo. |
| c5 | survives with caveat | Arithmetic right. It is a 1 kW slice of a 9.4 kW machine with fp4 weights. Tokens counted are output only; the machine also processes the (unknown) input. |
| c6 | survives with caveat | Arithmetic checked: 3 × 2,566.9 s ÷ 302.2 s = 25.5. My rerun gives 26.7 × real time on 31.6 min of TTS audio (section 4). Synthetic audio, other agents running. |
| c7 | survives with caveat | The method is sound and consistent with my integration over the full span. The unit (mW) has never been checked against a wall meter, and the 45.7 W window includes other agents' work. |
| c8 | survives with caveat | 1.50 holds for that trial (1.52 when integrated over the whole span, computed by hand from the printed windows). My rerun gives 1.32 (755 audio-h per server-h). Safe wording: "E = 1.3 to 1.5 Wh per audio-hour gross, two TTS trials, display off, 670 to 760 audio-hours per server-hour". |
| c9 | survives with caveat | The 60-s refresh is consistent with the probe's own refresh log. That the low reading came from excluding battery discharge is an interpretation, and the first-version output was not kept. Keep only "do not use SystemPowerIn". |
| c10 | survives with caveat | The rule is honest, one sentence, and satisfies must-have 1's "state how you scale it". It must also say what it implies: a rack server **as efficient as an Apple laptop GPU**, which costs about 52,000 CHF per kW in laptop hardware (assumption). The claim that it "moves only jobs and income" is not quite true: if J1 is defined by content, server-hours per job move with E, and so do the missed-deadline % and the job counts. |
| c11 | survives with caveat | Arithmetic right (667 ÷ 149 = 4.5, 2,857 ÷ 667 = 4.3). Both ends are anecdotal. 0.35 is one tweet, power method not stated, probably chip only. 6.7 pairs a throughput from one run on the blog page ("8 Seconds", insanely-fast-whisper) with a power delta measured on another ("+242 W", the slow 186-s run), plus 1 kW assumed for two cards. Call it an illustrative range. |
| c12 | survives | Re-opened. The quoted tweet reads "179:23 audio using Whisper V3 Turbo in just 2:29 with MLX with a mere 25W". It names the comparison card "RTX 5000" while the headline says A5000. |
| c13 | survives | "$0.00020 / minute" on the page today. This is the standard rate, not batch. |
| c14 | survives | Table header "Cost Per Hour", turbo "$0.04". Batch page: "50% lower cost", "24-hour to 7 day processing window", whisper-large-v3-turbo listed under Audio Transcriptions. |
| c15 | survives with caveat | "$0.0015" sits under a "Batch API price" toggle. The HTML's `data-batch` attributes are all empty, so the toggle state cannot be read from the page source. Together's batch window "defaults to 24h and cannot be changed" (best effort). The high price is 0.045 **or 0.090** USD per audio-hour. |
| c16 | survives | "Meta-Llama-3.1-8B-Instruct-Turbo 128k $0.02 $0.04" on deepinfra.com/pricing today. |
| c17 | survives with caveat | Confirmed for **us-east-1** in AWS's public price-list file (publication 2026-11-11): batch "$0.00011 per 1K input tokens" and the same for output; on-demand $0.00022 per 1K. <https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json>. Name the region. |
| c18 | survives | Correctly labelled assumption. It moves J2 central 4× and J2 high 7×, so the dashboard must show the input ratio wherever a J2 price appears. |
| c19 | survives with caveat | Reproduced: 11.189 + 7.529 → 9.359 central. But this is the **incoherent machine mix** (laptop J1, B200 J2). Label it, or replace J2 with a coherent machine (section 1, point 1). |
| c20 | survives with caveat | Reproduced (2.42%, 5.26%, 0.74%). On the same incoherent mix, and before hardware, which is the real hurdle. |
| c21 | survives with caveat | Reproduced. Assumes **unlimited demand** (every permit hour filled with paid work), which must-have 1 says must be declared. 28,372 audio-hours a day per house has no named buyer. Inconsistent with the plan's finite-arrival deadline sim. |
| c22 | survives with caveat | Same as c21, N = 8. |
| c23 | survives with caveat | Reproduced (290,755 × 0.2 × 0.67 = 38,961). Product of two unsourced haircuts, the incoherent mix and unlimited demand. A scenario, never "income". |
| c24 | survives with caveat | Reproduced. It assumes unsold hours still draw 1 kW (filler work, unpaid) so the heat is kept. Say so. It also rests on w = 20%, which has no source. |
| c25 | survives | 7,024 ÷ 20,815 = 0.3375. It follows the case formula literally. |
| c26 | survives with caveat | Reproduced: 52,329 CHF/kW, 2.021 CHF per run hour, 20% / 30%. The laptop price is an assumption, and nobody builds 1 kW out of 26 laptops. Read it as a reductio, not a design. |
| c27 | survives with caveat | Reproduced (18% / 27%). E = 6.7 is built as described under c11 and is probably pessimistic. At, say, 0.7 kW wall power for two cards E would be about 4.7 (assumption), so "both classes agree" is a coincidence of assumptions. |
| c28 | survives with caveat | 6.1-0032 llama3.1-8b Offline = 1227.99 tokens/s, confirmed in `data/raw/mlperf_inference_v6.1_summary.xlsx` (column llama3.1-8b Offline). 1227.99 × 3600 × 0.04e-6 × 0.8392 = 0.148 CHF. The 1 kW is an assumption, and output-only billing is the low case. |
| c29 | survives | ECB page re-opened today: 20 November 2026, USD 1.0990, CHF 0.9223 → 0.8392 CHF per USD. |

## 3. Bedrock without Firecrawl

```
curl -sL https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json  # 1.49 MB, publicationDate 2026-11-11
USE1-Llama3-1-8B-input-tokens-batch   0.00011 USD per 1K  "for Llama 3.1 8B in US East (N. Virginia) for Batch"
USE1-Llama3-1-8B-output-tokens-batch  0.00011 USD per 1K
USE1-Llama3-1-8B-input-tokens         0.00022 USD per 1K (on demand)
USE1-Llama3-1-8B-output-tokens        0.00022 USD per 1K (on demand)
```

## 4. Laptop probe rerun

Command: `python3 analysis/r3_whisper_energy_probe.py --minutes 30 --runs 3 --idle-s 120 --tmp <scratchpad>/r3mi_crit_probe`, which is shorter than the original. Output:

```
audio: 1894.7 s (31.58 min) of macOS TTS speech, 4860 words; synthesis 29.9 s
run 1: runtime 70.8 s = 26.8 x real time (model load included); transcript 4929 words vs 4860 spoken
run 2: runtime 70.6 s = 26.8 x real time (model load included)
run 3: runtime 71.4 s = 26.5 x real time (model load included)
refresh intervals: 6.94 mixed | 1.19 idle | 11.75 mixed | 34.02 job | 35.97 job | 36.12 job | 15.32 mixed | 1.61 idle
job windows: 3, mean 35.37 W; idle windows: 2, mean 1.40 W
total runtime 212.7 s for 1.579 audio-hours = 26.7 x real time
E_gross = 1.324 Wh per audio-hour  -> rule (i): 755 audio-hours per 1 kW server-hour
E_net   = 1.271 Wh per audio-hour
```

Reading (computed):
- **The second trial gives E = 1.32, against the investigator's 1.50.** Rule (i) then gives 755 audio-hours per server-hour instead of 667. That is 12% apart on the same laptop, model and kind of audio, within one hour.
- **The windows-only method reads slightly low.** It drops the mixed windows that hold model load and the tail of the run. Integrating the accumulator over the whole span and taking out idle for the non-job seconds only gives 1.38 Wh here and 1.52 in the original trial. So the method is 1 to 4% low.
- **A fair statement today: E = 1.3 to 1.5 Wh per audio-hour gross, from two TTS trials** (computed). It moves J1 income by ±7% around the stated figure, small next to the price and share assumptions.
- Saturday's measurement should report the integrated figure, not only the full windows.

## 5. Plan-change verdicts

| # | Change | Verdict | Why |
|---|---|---|---|
| 1 | Rule (i), E = 1.5 measured, range 150 to 2,860, MLPerf check line | accept, modified | Keep the rule and the check line. Call the range "illustrative, from two anecdotal posts and one MLPerf run". Say "one trial, TTS audio, display off", and that Saturday's measurement replaces it. |
| 2 | J1 jobs per server-hour = 1000 ÷ (P × t); J1 = 333 audio-h or content-defined | accept, modified | The formula is right. Choose the simplest option: keep 0.5 server-h in the simulation, say "one simulated J1 = a 333-audio-hour batch, the demo runs a slice", and leave the deadline sim alone. Redefining J1 by content (0.015 server-h) multiplies the job count by about 33 and changes missed-deadline % (build scope plus a re-run). |
| 3 | J2 row = MLPerf 5.1-0062 | accept, modified | Keep it as the sourced efficiency bound of a datacenter GPU machine. Do **not** combine it with laptop-class J1 in a headline figure. Either use a coherent machine for both types or label the mix "J1 at laptop efficiency, J2 at B200-slice efficiency". |
| 4 | Delete the whisper unit warning | accept | Verified: the summary's "Samples/s" 43,698.6 equals the loadgen "Tokens per second: 43698.6". Samples per second are 688.623. |
| 5 | Scenario wording for computing income, plus an operator-share switch | accept, modified | Lead with the "share needed" wording (the investigator's fallback) and keep the CHF scenario as the second line. A bold "CHF 39,000" gets quoted as income whatever caveat follows it. The tile must also name the machine efficiency and say "assumes every permit hour is filled with paid work (unlimited demand)". The switch is one extra input. |
| 6 | Show the break-even at the chosen sold share (0.3375 at 67%) | accept | The case formula divides by hours sold. It is one printed number, and it must use the same s as the income line. |
| 7 | "Does not pay off when < ~30% of list reaches the operator" | accept, modified | Word it as "about a fifth to a third of the list price, with assumed hardware prices, 5-year life and the measured E". Add "or when paid demand does not fill the heat-permit hours". The 30% rests on two assumed hardware prices and an unverified E. |
| 8 | Open risk 11 reworded | accept, modified | The list value of the work is defensible; income still is not. Add the incoherent J1/J2 machine mix, the unchecked Swiss or sovereign price level, and the buyer for ~28,000 audio-hours a day per house. |
| 9 | Saturday role B reruns the probe with real audio | accept | Already in the plan's 11:20 slot. Plugged in, display at fixed brightness, nothing else running (other agents contaminated both runs). |
| 10 | Question for DigitalHeat: hours or jobs, owner's share | accept | Faster than any search. Add: "what do your customers pay for Swiss-resident inference?" |

## 6. Founder questions still unanswered

1. "Which machine do I put in the basement? Your 9 francs per server-hour assumes laptop-grade efficiency for transcription and B200 efficiency for LLMs. Give me one machine, its price, and both numbers on it."
2. "Who buys 28,000 audio-hours of transcription a day from one house, and 10 million a year? What share of Groq's or DeepInfra's volume is that?"
3. "You benchmark against US commodity batch APIs. My pitch is sovereign Swiss compute. What is the Swiss price, and are you underselling or overselling?"
4. "Where does the 20% operator share come from? A ratio of Salad renter prices to API list prices is two different markets."
5. "Unsold hours still run at 1 kW to keep the heat. Doing what, and who pays for that wear?"
6. "28,000 audio-hours a day is about 0.4 to 3 TB of audio a day into a residential connection, depending on codec (my estimate, unverified). Is that in your model?"
7. "Your laptop energy came from battery telemetry with the display off and other processes running. Why should I trust 1.5 Wh and not 1.2 or 2.0?"
8. "If J1 is defined by content, your missed-deadline % changes. Which number goes on the slide?"
