# Round 3 research: which machine, sold where, for what income

Investigator for weak point "reference-server identity, laptop-to-1 kW scaling rule, and a defensible 'computing income' key figure". Rerun of round 3, written 2026-11-21 (Saturday, 09:05 to 09:30). It replaces the uncritiqued draft that the cut-off run left in this file; that draft's figures were re-checked, and the ones kept are marked. The searches of `r2-host-income-hardware.md`, `r1-job-model.md` and the earlier draft were not repeated. Paid Firecrawl calls used: **1 of 6** (Amazon Bedrock pricing page, which loads its prices by script).

Status labels: **sourced** = number read by me on the opened page or file at the URL given; **computed** = produced by a script in `analysis/` (command named) or by arithmetic shown here; **assumption** = our own choice; **unverified** = not confirmed, or read only through a summary.

Currency: CHF. 1 USD = 0.8392 CHF (ECB reference rates of 20 November 2026, sourced in round 1: <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>). Provider prices are list prices in USD, no VAT.

## 1. Short answer

1. **The laptop job has now been measured once.** `mlx_whisper` with the cached `whisper-large-v3-turbo` on the team's M3 Pro: 3 × 42.8 minutes of synthetic speech in 302 s (**25.5 × real time**, model load included) at **38.2 W** mean whole-device power. That gives **E = 1.50 Wh per audio-hour gross** (1.40 net of idle). Computed, `python3 analysis/r3_whisper_energy_probe.py`. Caveats: one trial, text-to-speech audio, battery-controller telemetry not checked against a wall meter, other processes on the machine included.
2. **MLPerf power is now sourced, not my own average.** The v5.1 summary file carries the official `Power_Result`: **7,636.49 W** for whisper (ID 5.1-0061) and **9,436.05 W** for llama3.1-8b (ID 5.1-0062), both Lenovo servers with 8 × B200. They match the draft's own averages of the analyser logs to the watt. v6.0 and v6.1 have no power results at all.
3. **Recommended scaling rule: equal energy per unit of work, gross laptop energy.** One sentence: *"We assume the 1 kW reference server needs the same electricity per audio-hour as our laptop: 1.5 Wh, so one server-hour transcribes about 670 audio-hours."* Formula: **J1 jobs per server-hour = 1000 ÷ (P × t)**, with P the laptop's mean watts and t its hours for one J1 job. Real machines span 0.35 to 6.7 Wh per audio-hour, so the result can be about 4× too low or 4.5× too high. The rule moves only jobs and income, never heat, coverage, utilisation or the break-even.
4. **Prices per unit of work are public and fit a heat-following server.** Batch tiers sell a result within 24 h to 7 days (Groq), not an hour of a machine. Transcription: 0.012 / 0.020 / 0.045 USD per audio-hour (low / central / high). Llama-3.1-8B: 0.04 to 0.77 USD per million output tokens, depending on provider and on how many input tokens are billed (sourced prices; input ratio is an assumption).
5. **The list value of one server-hour's work is 4.3 / 9.4 / 30.7 CHF** (50/50 mix), against an electricity-minus-heat cost of 0.2261 CHF. Only **2.4% of the list value** (central) has to reach the operator to cover electricity net of heat (computed, `python3 analysis/r3_income.py`). This is not income.
6. **What does decide it: hardware.** Efficiency per joule is bought with hardware cost per kW. Laptop-class efficiency costs about 52,000 CHF per kW (26 laptops; price is an assumption) = 2.02 CHF per run hour over 5 years at N=6. Electricity net of heat plus hardware then needs **about 20% of the list value**, and **30% if only 67% of hours are sold**. A consumer-GPU rig lands at the same place (18% / 27%). So the operator needs roughly a fifth to a third of what end customers pay, and no source for that share was found.
7. **Sold share at which income equals electricity minus heat value** (case convention: all permit hours run, a share is sold): **12.1%** at the central price if the operator gets 20% of list (26.3% low, 3.7% high). Identical for N=6 and N=8.
8. **Dashboard wording:** a scenario line with its two switches and its price source, never a bare income (section 8).

## 2. What changed against the cut-off draft

| Draft said | Now | Why |
|---|---|---|
| E = 1.5 Wh per audio-hour, "placeholder, not measured" | 1.50 measured (one trial) | probe run on the laptop (section 3.3). That the two agree is a coincidence |
| MLPerf power = "my window average, not the official metric" | official `Power_Result` read, same values | v5.1 `summary_results.json` |
| J2 price central 0.04 USD (output only), one provider | central 0.16 (input billed at 6:1), high 0.77 (Amazon Bedrock batch), two providers | input tokens are work too. Bedrock was read through Firecrawl |
| scenario B with the server off when unsold | B = case convention (all permit hours run, a share is sold), D = plan default | the case formula divides by hours **sold**, which only makes sense if unsold hours still run |
| no hardware in the income line | section 7 of the script: hardware per run hour for two machine classes | efficiency and hardware price go together |

## 3. Scaling rule (task a)

### 3.1 MLPerf results with power

| Finding | Value | Status | Source |
|---|---|---|---|
| v6.1 / v6.0 rows with power | 0 of 492 / 0 of 520 | computed from sourced files (draft; not re-run) | <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/summary.csv>, <https://raw.githubusercontent.com/mlcommons/inference_results_v6.0/main/summary_results.json> |
| v5.1 rows with power | 24 of 1,448. Two 8 × B200 Lenovo systems (llama2-70b, llama3.1-405b, llama3.1-8b, rgat, stable-diffusion-xl, whisper) and four edge resnet runs on one Ryzen mini PC (27.5 to 34.2 W) | computed, re-run today | <https://raw.githubusercontent.com/mlcommons/inference_results_v5.1/main/summary_results.json> |
| Whisper, ID 5.1-0061, ThinkSystem SR680a V3, 8 × B200-SXM-180GB, Offline | `Power_Result` 7636.4895833333 W; `Performance_Result` 43698.6, `Performance_Units` "Samples/s" (it is tokens/s, see 3.2); accuracy 97.78; weights fp16; note "B200 TGP 1000W" | sourced | same file |
| llama3.1-8b, ID 5.1-0062, SR780a V3, 8 × B200, Offline | `Power_Result` 9436.05296875 W; 146,960 tokens/s; **weights fp4**. Server scenario: 9,011.07 W, 128,689 tokens/s | sourced | same file |
| Loadgen samples per second | whisper 688.623; llama3.1-8b 1,148.12 (128.0 output tokens per sample) | sourced (draft), re-read by the script today | `mlperf_log_summary.txt` under <https://github.com/mlcommons/inference_results_v5.1/tree/main/closed/Lenovo/results/SR680a_V3_B200SXMx8_TRT/whisper/Offline/performance/run_1/> and the SR780a llama3.1-8b folder |
| Whisper energy | 11.09 J per sample; with 22.05 s of audio per sample: **0.503 Wh per audio-hour = 1,988 audio-hours per kWh** (0.370 if all samples were 30 s) | computed, `python3 analysis/r3_mlperf_power.py` | 22.05 s = "approximately 10 hours" ÷ 1,633 samples: <https://raw.githubusercontent.com/mlcommons/inference/master/speech2text/README.md> |
| llama3.1-8b energy | **15.57 output tokens per J = 56.07 million output tokens per kWh** | computed, same command | — |

Both figures describe a **1 kW slice of a 7.6 to 9.4 kW machine**. Use them as a measured efficiency bound, not as the reference server.

### 3.2 The MLPerf whisper column is tokens per second (settled)

The summary column "Samples/s" holds tokens/s. The loadgen logs print both: ID 6.1-0032 (Dell, 2 × Xeon 6787P, no GPU) "Samples per second: 20.3947" and "Tokens per second: 1539.49" (sourced in the draft: <https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/closed/Dell/results/1-node-2S-GNR_86C/whisper/Offline/performance/run_1/mlperf_log_summary.txt>). The v5.1 row above repeats the pattern: 43,698.6 "Samples/s" against 688.623 samples per second in the log. Computed from this: the CPU-only server transcribes about **450 × real time**, which is 2.22 Wh per audio-hour **if** it draws 1 kW (assumption; no power figure exists for it).

### 3.3 Laptop measurement (new)

`python3 analysis/r3_whisper_energy_probe.py` (stdlib; calls the installed `mlx_whisper`, macOS `say` and `ioreg`; `HF_HUB_OFFLINE=1`, nothing downloaded):

- Audio: macOS text-to-speech reading the repo's case texts, 42.78 minutes, 6,480 words, 16 kHz mono. Transcripts had 6,584 words, so the model transcribed everything (the extra words are numbers and symbols spoken out).
- Power: the battery controller's `PowerTelemetryData.AccumulatedSystemLoad` ÷ `SystemLoadAccumulatorCount`, one mean per 60-second registry refresh. SystemLoad = adapter input + battery discharge, whole device. The machine has a 35 W adapter, and under load the battery supplied the rest, so SystemLoad (not SystemPowerIn) is the right field.
- A first attempt read the instantaneous `SystemPowerIn` once per second. That field only refreshes once a minute and leaves out the battery, so it gave 1.16 W in one run and 16.7 W in the other. **Discarded.** Lesson for role B on Saturday: use the accumulators, run at least 4 to 5 minutes, and keep the laptop plugged in with a full battery.

Output (2026-11-21, 09:12 to 09:22, exit 0):

```
telemetry check: UpdateTime=1795248650, AccumulatedSystemLoad=502275880, count=140436, adapter 34 W
audio: 2566.9 s (42.78 min) of macOS TTS speech, 6480 words; synthesis 40.6 s
run 1: runtime 99.0 s = 25.9 x real time (model load included); transcript 6584 words vs 6480 spoken
run 2: runtime 98.9 s = 25.9 x real time (model load included); transcript 6584 words vs 6480 spoken
run 3: runtime 104.3 s = 24.6 x real time (model load included); transcript 6584 words vs 6480 spoken
refresh intervals (UpdateTime start, length s, mean W, phase):
  1795248770   60     3.96  idle
  1795248830   60     1.57  idle
  1795248890   60    30.19  mixed
  1795248950   60    34.31  job
  1795249010   60    36.49  job
  1795249070   60    36.44  job
  1795249130   60    45.65  job
  1795249190   60    14.13  mixed
  1795249250   60     3.22  idle
  1795249310   60     1.24  idle
job windows: 4, mean 38.22 W; idle windows: 4, mean 2.50 W
total runtime 302.2 s for 2.139 audio-hours = 25.5 x real time
E_gross = 1.500 Wh per audio-hour  -> rule (i): 667 audio-hours per 1 kW server-hour
E_net   = 1.402 Wh per audio-hour  (job minus idle; idle includes other processes running at the time)
```

Reading: the four job windows range from 34.3 to 45.7 W, so E is 1.35 to 1.79 within this one trial. Other agents were running on the same laptop (load average about 2 before and after), and the 45.7 W window probably includes some of their work. The idle level (1.2 to 4.0 W) suggests the display was off. With the display on, gross E rises by display watts × 0.039 h per audio-hour (assumption; not measured).

Plausibility (computed): the M4 Max post in 3.4 gives 72 × real time at 25 W. That is 2.8 times faster than our 25.5 ×, on a chip with more than twice the GPU cores, at a power that was probably chip-only.

### 3.4 Published whisper throughput and power outside MLPerf (from the draft, one re-checked)

| Machine | Figure | Wh per audio-hour | Status | Source |
|---|---|---|---|---|
| Apple M4 Max, Whisper V3 Turbo, MLX | "transcribed a 179:23 audio using Whisper V3 Turbo in just 2:29 with MLX with a mere 25W power draw" | 0.35 (computed) | figures sourced, **re-opened today**; one user's post, measurement method not stated | <https://www.tomshardware.com/pc-components/cpus/apple-m4-max-cpu-transcribes-audio-twice-as-fast-as-the-rtx-a5000-gpu-in-user-test-m4-max-pulls-just-25w-compared-to-the-rtx-a5000s-190w> (13 Nov 2024) |
| RTX A5000, same file | 4:33 at 190 W | 4.8 GPU only | same | same |
| RTX 4090, large-v3, 10 min of audio | 8 s, "+242 W" | 6.7 if two cards make a 1 kW rig | unverified (draft read it through a summary) | <https://owehrens.com/whisper-nvidia-rtx-4090-vs-m1pro-with-mlx/> |
| Groq hosted whisper | real-time speed factor 189 (large-v3) and 216 (turbo); no power | — | sourced, re-read today | <https://console.groq.com/docs/speech-to-text> |

### 3.5 The three candidate rules

| Rule | Needs | Gives | Verdict |
|---|---|---|---|
| (i) **Equal energy per unit of work**: the laptop's Wh per audio-hour applies unchanged | the laptop measurement only (now done once) | audio-hours per server-hour = 1000 ÷ E = 667 | **recommended.** It is what must-have 1 asks for ("state how you scale it"), it is one sentence, and the laptop number drives it |
| (ii) Throughput ratio from a benchmark | the MLPerf whisper harness run on the laptop (large-v3, 1,633 samples) plus a named server with a power figure | a named machine | rejected: no v6.x system has power, and running the harness is build scope |
| (iii) Samples per joule from MLPerf power | nothing from the laptop | 1,988 audio-hours per server-hour, measured | used as the **check line**, not the rule: one machine type (8 × B200, 7.6 kW), a different model (large-v3), and the laptop measurement would no longer matter |

### 3.6 Recommendation

- **Sentence for the assumptions list and pitch:** *"We assume the 1 kW reference server needs the same electricity per audio-hour as our laptop. We measured 1.5 Wh, so one server-hour transcribes about 670 audio-hours."*
- **Formula** (P = mean laptop watts during the job, gross; t = laptop hours for one J1 job; A = audio-hours in one J1 job):
  - E = P × t ÷ A (Wh per audio-hour)
  - **J1 jobs per server-hour = 1000 ÷ (P × t)** = 1000 ÷ (E × A)
  - server-hours per J1 job = P × t ÷ 1000 (the plan's existing rule "laptop Wh per job ÷ 1000", unchanged)
- With the plan's J1 size of 0.5 server-hours, one J1 job = **333 audio-hours** (computed). That is 13 hours of laptop time, so the demo transcribes a slice of a job, as round 1 already said. Alternatively, define J1 by content (for example 10 audio-hours = 0.015 server-h at E = 1.5). If the team keeps 0.5 server-h, say "one J1 job = a 333-hour transcription batch".
- **Gross, not net:** gross E gives fewer jobs per server-hour (the cautious side), and a server has its own overhead.
- **Check line beside it:** "MLPerf v5.1 measured 0.50 Wh per audio-hour on an 8-GPU server (whisper-large-v3, 7,636 W); our laptop needs 1.5, three times more."
- **How wrong it could be:** machines with figures span 0.35 Wh (M4 Max, chip power) to 6.7 Wh (two RTX 4090 in an assumed 1 kW rig). So 1 kW does **150 to 2,860 audio-hours per hour, against 667 from the rule**: about 4.5× fewer to 4.3× more. Within our own trial: 560 to 740.
- **What the error touches:** J1 job count and income. **What it does not touch:** server-hours, coverage, dumped heat, utilisation, electricity, heat value, break-even.
- **J2:** no laptop measurement. Use **MLPerf v5.1 ID 5.1-0062: 56.07 million output tokens per kWh** (official power, fp4 weights, a 1 kW slice of 9.4 kW). Keep ID 6.1-0032 (4.42 million per hour, 1 kW assumed) as the CPU-only comparison.
- **Reference-server identity, said plainly:** the reference server is **1 kW of wall power, not a named product**. Work per kWh comes from a named source for each job type. No named 1 kW machine with both a measured power figure and a benchmark result was found.

## 4. Why a price per job (task b, framing)

Round 2 found that GPU marketplaces rent hours of machines that stay available, and that a host which switches off on a heat signal breaks that deal. A price per finished job does not have this problem, because batch tiers promise a result inside a window, not a machine:

| Provider | Window | Status | Source |
|---|---|---|---|
| Groq Batch | "24-hour to 7 day processing window"; "50% lower cost"; covers "audio transcription" with whisper-large-v3 and whisper-large-v3-turbo, and lists llama-3.1-8b-instant | sourced, re-read today | <https://console.groq.com/docs/batch> |
| OpenAI Batch | "Each batch completes within 24 hours (and often more quickly)" | sourced (draft, not re-read) | <https://developers.openai.com/api/docs/guides/batch> |
| Amazon Bedrock | "batch inference at a 50% lower price compared to on-demand inference pricing" | sourced (curl, today) | <https://aws.amazon.com/bedrock/pricing/> |

The plan's deadlines (J1 24 h, J2 168 h, both assumptions) match the two ends of Groq's window. The catch: the market sells these windows **to end customers**. DigitalHeat would have to be the provider, or a subcontractor to one. No provider was found that buys capacity this way.

## 5. Prices per unit of work (task b)

All read on 2026-11-21. None of the pages shows a "last updated" date, except Bedrock's `og:updated_time` 2026-11-20.

### 5.1 Transcription (USD per audio-hour)

| Provider, model | As written | List | Batch | Status | Source |
|---|---|---|---|---|---|
| DeepInfra, openai/whisper-large-v3-turbo | "$0.00020 / minute" | 0.012 | none read | sourced, re-read today; ×60 computed | <https://deepinfra.com/openai/whisper-large-v3-turbo> |
| Groq, whisper-large-v3-turbo | "$0.04" cost per hour | 0.040 | 50%: **0.020** | sourced, re-read today | <https://console.groq.com/docs/speech-to-text>, <https://console.groq.com/docs/batch> |
| Groq, whisper-large-v3 | "$0.111" | 0.111 | 0.0555 | sourced, re-read today | same |
| Together AI, Whisper Large v3 | "$0.0015" in the table "Price per audio minute", which has a "Batch API price" toggle | 0.090 | "Selected serverless models run at 50% off batch rates: openai/whisper-large-v3" → 0.045 | sourced, re-read today. **Unverified which toggle state the $0.0015 is**: if it is already the batch price, batch = 0.090 | <https://www.together.ai/pricing>, <https://docs.together.ai/docs/inference/batch/overview> |
| OpenAI, whisper-1 | "$0.006" per minute | 0.36 | not read | sourced (draft); outlier | <https://developers.openai.com/api/docs/models/whisper-1> |

Used: **low 0.012, central 0.020, high 0.045.** Groq bills at least 10 s per request (sourced, same page).

### 5.2 Llama-3.1-8B, the MLPerf model (USD per million tokens)

| Provider | Input | Output | Batch / async | Status | Source |
|---|---|---|---|---|---|
| DeepInfra, Meta-Llama-3.1-8B-Instruct-Turbo | 0.02 | 0.04 | "Flex ... 0.8x base price", availability per model not stated | sourced, re-read today | <https://deepinfra.com/pricing> |
| Amazon Bedrock, Llama 3.1 Instruct (8B) | 0.22 | 0.22 | **batch 0.11 / 0.11** | sourced through Firecrawl (rendered page, cached 2026-11-21 03:41 UTC, direct quote). Region is the page default, not stated in the quote | <https://aws.amazon.com/bedrock/pricing/> |
| Groq, llama-3.1-8b-instant | "Contact Sales" (Enterprise) | | in the batch model list | sourced, re-read today | <https://console.groq.com/docs/models> |

The MLPerf task summarises news articles into 128 output tokens, so input tokens dominate. The input length was not found (the llama3.1-8b README gives 13,368 samples but no token lengths: <https://raw.githubusercontent.com/mlcommons/inference/master/language/llama3.1-8b/README.md>). **Assumption: 6 input tokens billed per output token.** Expressed per million output tokens:

- **low 0.04** (DeepInfra, output only)
- **central 0.16** (DeepInfra, output + 6 × input)
- **high 0.77** (Bedrock batch, output + 6 × input)

## 6. Script and output (task c)

`python3 analysis/r3_income.py` (stdlib; imports `load` and `simulate` from `analysis/baseline_sweep.py` unchanged, policy `follow`, case assumptions). Options: `--wh-per-audio-hour`, `--wholesale`, `--sold`. Output of 2026-11-21, exit 0. The long source notes on the price lines are shortened here; they are the URLs of section 5.

```
r3_income.py. Currency CHF; 1 USD = 0.8392 CHF (ECB, 20 Nov 2026). LIST PRICES ARE WHAT END CUSTOMERS PAY A PROVIDER,
not DigitalHeat's income. Break-even = case formula, heat credited at electricity price / 2.5.

== 1. Inputs ==
J1 scaling rule (i): audio-h per server-h = 1000 / E = 667, E = 1.5 Wh per audio-hour [r3_whisper_energy_probe.py, COMPUTED]
J2: 56.07 million output tokens per server-h [COMPUTED, MLPerf 5.1-0062, 1 kW slice of a 9.4 kW machine]
Job sizes [ASSUMPTION]: J1 = 0.5 server-h = 333 audio-h; J2 = 4 server-h = 224 million output tokens
Mix [ASSUMPTION]: 50% of server-hours to J1, 50% to J2
J1 low      0.012 USD/audio-h =   3.36 CHF per J1 job  [DeepInfra ... SOURCED]
J1 central  0.020 USD/audio-h =   5.59 CHF per J1 job  [Groq turbo, batch 50% ... SOURCED]
J1 high     0.045 USD/audio-h =  12.59 CHF per J1 job  [Together large-v3, batch 50% ... SOURCED; toggle UNVERIFIED]
J2 low      0.040 USD/M out-tok =   7.53 CHF per J2 job  [DeepInfra output only. SOURCED]
J2 central  0.160 USD/M out-tok =  30.11 CHF per J2 job  [DeepInfra output + 6 x input; ratio 6 ASSUMPTION]
J2 high     0.770 USD/M out-tok = 144.93 CHF per J2 job  [Bedrock batch 0.11/0.11; ratio 6 ASSUMPTION]
Wholesale share w = 20% [ASSUMPTION]; sold share s = 67% [ASSUMPTION]

== 2. Gross list value of the work in one 1 kW server-hour (CHF) ==
                                                   low   central      high
J1, rule (i), E = 1.5                            6.714    11.189    25.176
J2, B200 slice                                   1.882     7.529    36.232
mix 50/50 (the main case)                        4.298     9.359    30.704
break-even (electricity - heat value)           0.2261   (0.3325 without the heat credit)
share of list value needed to cover electricity minus heat value (= break-even / gross value):
  J1                                              3.4%      2.0%      0.9%
  J2, B200 slice                                 12.0%      3.0%      0.6%
  mix 50/50                                       5.3%      2.4%      0.7%

== 3. Same, for three coherent machines (one efficiency for both job types) ==
  laptop-class (rule i) J1 + B200 J2             4.298     9.359    30.704   needs 2.4% of list (central)  [the main case]
  8 x B200, 1 kW slice                          10.951    20.448    55.653   needs 1.1% of list (central)  [power SOURCED (MLPerf official)]
  2 x Xeon 6787P, no GPU                         2.339     4.071     9.920   needs 5.6% of list (central)  [1 kW ASSUMPTION]

== 4. J1 over the scaling bracket, central price ==
  E =   1.5 ->    667 audio-h per server-h ->  11.19 CHF -> needs  2.0%   [laptop, this run; COMPUTED]
  E =  0.35 ->  2,857 audio-h per server-h ->  47.95 CHF -> needs  0.5%   [Apple M4 Max ...]
  E = 0.503 ->  1,988 audio-h per server-h ->  33.37 CHF -> needs  0.7%   [8 x B200, MLPerf 5.1-0061 ...]
  E =  2.22 ->    450 audio-h per server-h ->   7.56 CHF -> needs  3.0%   [2 x Xeon 6787P; 1 kW ASSUMPTION]
  E =   6.7 ->    149 audio-h per server-h ->   2.51 CHF -> needs  9.0%   [2 x RTX 4090; UNVERIFIED]

== 5. Year on the reference house, follow policy, every permit hour filled with work ==

N = 6: server-hours run 31,067; coverage 79.6%; dumped 0 kWh  [COMPUTED, baseline_sweep.simulate]
  J1: 15,534 server-h = 31,067 jobs = 10.36 million audio-h (28,372 per day)
  J2: 15,534 server-h = 3,883 jobs = 871 billion output tokens
  electricity 10,330 CHF; heat value 3,306 CHF; electricity - heat 7,024 CHF = 0.2261 per server-h
                                                     low     central        high
  A. gross LIST value of the work, CHF/yr        133,522     290,755     953,874
     per server-hour                               4.298       9.359      30.704
     margin over 0.2261 per server-hour            4.072       9.133      30.478
  B. scenario w = 20%, s = 67%; all permit hours run (heat kept), unsold hours unpaid  [case convention]
     server-hours sold                            20,815
     computing income, CHF/yr                     17,892      38,961     127,819
     electricity / heat value, CHF/yr             10,330       3,306
     income per sold server-hour                   0.860       1.872       6.141
     case break-even per sold hour                0.3375
     margin per sold server-hour                   0.522       1.534       5.803
     yearly margin before hardware, CHF           10,868      31,937     120,795
  C. sold share at which income = electricity - heat value, s* = (elec - heat) / (gross x w):
     w = 5%                                       105.2%       48.3%       14.7%   (>100% = cannot break even)
     w = 10%                                       52.6%       24.2%        7.4%
     w = 20%                                       26.3%       12.1%        3.7%
     w = 50%                                       10.5%        4.8%        1.5%
     w = 100%                                       5.3%        2.4%        0.7%
  D. plan default (server OFF when unsold): margin = s x run-h x (w x gross/h - 0.2261); sign set by w alone:
     w needed                                       5.3%        2.4%        0.7%   (coverage then falls with s)

N = 8: server-hours run 36,281; coverage 92.9%; dumped 0 kWh  [COMPUTED, baseline_sweep.simulate]
  J1: 18,140 server-h = 36,281 jobs = 12.09 million audio-h (33,133 per day)
  J2: 18,140 server-h = 4,535 jobs = 1,017 billion output tokens
  electricity 12,063 CHF; heat value 3,860 CHF; electricity - heat 8,203 CHF = 0.2261 per server-h
                                                     low     central        high
  A. gross LIST value of the work, CHF/yr        155,931     339,553   1,113,963
     per server-hour                               4.298       9.359      30.704
     margin over 0.2261 per server-hour            4.072       9.133      30.478
  B. scenario w = 20%, s = 67%; all permit hours run (heat kept), unsold hours unpaid  [case convention]
     server-hours sold                            24,308
     computing income, CHF/yr                     20,895      45,500     149,271
     electricity / heat value, CHF/yr             12,063       3,860
     income per sold server-hour                   0.860       1.872       6.141
     case break-even per sold hour                0.3375
     margin per sold server-hour                   0.522       1.534       5.803
     yearly margin before hardware, CHF           12,692      37,297     141,068
  C. sold share at which income = electricity - heat value, s* = (elec - heat) / (gross x w):
     w = 5%                                       105.2%       48.3%       14.7%   (>100% = cannot break even)
     w = 10%                                       52.6%       24.2%        7.4%
     w = 20%                                       26.3%       12.1%        3.7%
     w = 50%                                       10.5%        4.8%        1.5%
     w = 100%                                       5.3%        2.4%        0.7%
  D. plan default (server OFF when unsold): margin = s x run-h x (w x gross/h - 0.2261); sign set by w alone:
     w needed                                       5.3%        2.4%        0.7%   (coverage then falls with s)

== 6. Cross-check of the wholesale share (not a source for it) ==
  RTX 4090 at 75 x real time: list value 0.90 USD per GPU-hour (low); Salad renter price 0.160-0.440 USD/h = 18%-49% of it
  RTX 4090 at 75 x real time: list value 1.50 USD per GPU-hour (central); Salad renter price 0.160-0.440 USD/h = 11%-29% of it
  RTX 4090 at 75 x real time: list value 3.38 USD per GPU-hour (high); Salad renter price 0.160-0.440 USD/h = 5%-13% of it
  A provider renting that GPU and keeping it busy would hand the machine owner about this share (after the ~20% marketplace fee: x0.8).

== 7. Efficiency is bought with hardware: J1 list value vs hardware cost per run hour (N = 6, central price) ==
  laptop-class (M3 Pro), this run: hardware 52,329 CHF/kW / (5 yr x 5,178 h) = 2.021 CHF per run hour; J1 list value 11.19; electricity - heat + hardware = 2.247 = 20% of list value (at s = 67%: w needed 30%)  [2,000 CHF per laptop ASSUMPTION (price not read), 38.22 W per laptop COMPUTED by the probe]
  2 x RTX 4090 rig: hardware 6,000 CHF/kW / (5 yr x 5,178 h) = 0.232 CHF per run hour; J1 list value 2.51; electricity - heat + hardware = 0.458 = 18% of list value (at s = 67%: w needed 27%)  [6,000 CHF per kW = round-2 ASSUMPTION on a SOURCED card floor price; E UNVERIFIED]
  No hardware price was read for the 8 x B200 server; its row is left out on purpose.
```

Sensitivity to the probe's window spread (computed, `python3 analysis/r3_income.py --wh-per-audio-hour 1.79` and `1.35`): the central 50/50 list value per server-hour moves from 9.36 to 8.45 and 9.98 CHF.

### Reading the output

- **The sold share asked for in the task (section C).** Under the case convention (servers run every permit hour for heat, a share s is sold), income equals electricity minus heat value at **s\* = 12.1%** (central) when the operator receives 20% of list, and at 26.3% / 3.7% (low / high). The same holds for N=6 and N=8, because both sides scale with server-hours. At w = 5% and the low price it cannot break even (105%). Under the plan's default (server off when unsold, section D) no sold share breaks even on its own. The condition becomes w ≥ 2.4% (central), and coverage falls with s.
- **The case's own break-even moves with the sold share.** 0.2261 CHF per server-hour assumes every run hour is sold. At s = 67% the case formula gives **0.3375 CHF per sold hour** (computed, section B). The pitch must use the same s as the income line.
- **Electricity is not the hurdle; hardware and the operator's share are.** Electricity net of heat is 2 to 5% of the list value. With hardware at 5 years and N=6 run hours, the full-cost hurdle is about **18 to 20% of the list value at 100% sold, and 27 to 30% at 67% sold**, for both machine classes (section 7). The two classes agree because hardware cost per kW and work per kWh rise together. Round 2 reached the same point from the host side: the needed 0.54 to 0.64 CHF net per run hour against Salad's 0.30 to 0.35.
- **The wholesale share has no source.** The 4090 cross-check (section 6) puts a renter-paid GPU-hour at 11 to 29% of the list value of the work it could do, at the central price and full utilisation. After the marketplace's ~20% fee that is about 9 to 23% for the machine owner. The full-cost hurdle of 27 to 30% (at 67% sold) is above that range. Read this as "probably does not pay with consumer or laptop-class hardware at today's batch prices", not as a proof.
- **J2 on a CPU-only server does not cover its electricity at the low price.** 4.42 million tokens × 0.04 USD = 0.148 CHF per server-hour, against 0.2261 (computed from the inputs above). It does at the central price (0.59 CHF) only if at least 38% of list reaches the operator.
- **Volume.** At N=6 one house would transcribe **28,372 audio-hours a day** and generate 871 billion tokens a year. No buyer for that volume from one site is named. With finite demand the sold share binds, and it has no source.
- **The heat credit is small against the work.** 0.1064 CHF per server-hour is 1.1% of the central list value. It decides whether a basement is cheaper than a data centre, not whether the work is worth doing.

## 7. Weak points of this work

- **One laptop trial**, synthetic TTS audio, 4 one-minute power windows, other agents running on the same machine, display probably off, battery telemetry never checked against a wall meter. E could reasonably be 1.2 to 2.0 on a clean rerun (unverified). Role B should repeat it on Saturday with real audio (procedure in section 9).
- 22.05 s of audio per MLPerf whisper sample rests on "approximately 10 hours". The error is at most +36%.
- The J2 central and high prices depend on the assumed 6:1 input ratio. With output-only billing they are 0.04 and 0.11 USD.
- The Together toggle (list or batch) is unresolved. Bedrock was read only through Firecrawl's rendered and cached copy, with the region not shown in the quote.
- **Both haircuts are assumptions:** wholesale share (20%) and sold share (67%). The 2,000 CHF laptop price and the 6,000 CHF per kW rig are assumptions. No B200 server price was read.
- The mix is by server-hours, and J1 and J2 come from different machines (laptop-class and a B200 slice). Section 3 of the output gives coherent single-machine rows for comparison.
- Not counted: network and storage to move about 28,000 audio-hours a day into a basement, restart time, data-protection terms, provider minimum volumes.

## 8. Recommended wording (task d)

**Never show a bare "computing income" number.** Figures are from this run. After role B's own measurement, rerun `python3 analysis/r3_income.py --wh-per-audio-hour <E>`.

Dashboard key-figure tile (N=6):

> **Computing income (scenario, not a forecast): CHF 39,000 per year**
> = 20% of the list value of the work done × 67% of heat-permit hours sold. Both percentages are our assumptions; change them here: [operator share] [sold share].
> List value of the work: CHF 291,000 per year. Prices: Groq whisper-large-v3-turbo batch, 0.020 USD per audio-hour; DeepInfra Llama-3.1-8B, 0.04 / 0.02 USD per million output / input tokens. Both read on 21 Nov 2026.
> Electricity CHF 10,330 · heat value CHF 3,306 · **income covers electricity minus heat from 12% sold.** Hardware is not included: with it, about 30% of list must reach the operator.

Fallback if the team wants no scenario figure:

> **Computing income: not known. Needed: CHF 7,024 per year (N=6) to cover electricity minus heat, which is 2.4% of the list value of the work at public batch prices (Groq, DeepInfra, 21 Nov 2026), and about 30% with hardware.**

Pitch, one sentence:

> "At today's public batch prices the work one server-hour does is listed at about 9 francs, and electricity after the heat credit is 23 centimes. Electricity is not the problem. The question for a pilot is what share of that price a basement operator gets: with hardware we need about a third."

Words to avoid: "revenue", "earns", "market price of our compute". Words to use: "list value of the work", "scenario", "share needed".

Assumptions list, one line each: scaling rule, measured E and its 0.35 to 6.7 range; J2 source "1 kW slice of a 9.4 kW machine, fp4"; the prices with provider, tier and date; FX rate; 6:1 input ratio; wholesale share; sold share; 50/50 mix; hardware price and life in the full-cost line.

## 9. Commands

```
# MLPerf
curl -sL https://raw.githubusercontent.com/mlcommons/inference_results_v5.1/main/summary_results.json   # Power_Result per row
python3 analysis/r3_mlperf_power.py            # downloads ~1.3 MB of v5.1 logs; prints energy per sample/token
# laptop probe (about 12 minutes; plugged in, battery full; nothing downloaded)
python3 analysis/r3_whisper_energy_probe.py --tmp <scratch dir>
#   Saturday, real audio: replace the WAV with a fixed audio set, keep the accumulator method, run >= 5 minutes
# income
python3 analysis/r3_income.py
python3 analysis/r3_income.py --wh-per-audio-hour 1.79
python3 analysis/r3_income.py --wh-per-audio-hour 1.35
# price pages re-read today with curl (browser user agent, tags stripped, grep for the model names):
#   deepinfra.com/openai/whisper-large-v3-turbo, deepinfra.com/pricing, console.groq.com/docs/speech-to-text,
#   console.groq.com/docs/batch, console.groq.com/docs/models, console.groq.com/docs/model/llama-3.1-8b-instant,
#   www.together.ai/pricing, docs.together.ai/docs/inference/batch/overview, aws.amazon.com/bedrock/pricing (prices
#   are script-filled; read with one Firecrawl scrape, query mode), tomshardware M4 Max article,
#   raw.githubusercontent.com/mlcommons/inference/master/language/llama3.1-8b/README.md
```

Pages that did not give what was asked: `groq.com/pricing` (947 characters, no prices); the Bedrock page through curl (price placeholders only); the llama3.1-8b README (no token lengths).

## 10. Proposed changes to the plan

1. **Scaling rule (plan line 6 and "The two job types"):** replace "*assumption*, no source, possibly several-fold" with: rule (i), gross laptop energy, **measured E = 1.5 Wh per audio-hour (one trial)**, 667 audio-hours per server-hour, range 150 to 2,860 from published machines, check line MLPerf 0.50 Wh (official power 7,636 W).
2. **J1 size:** state "one J1 job = 0.5 server-h = 333 audio-hours", or redefine J1 by content (for example 10 audio-hours = 0.015 server-h). Either way, J1 jobs per server-hour = 1000 ÷ (P × t).
3. **J2 reference row:** MLPerf v5.1 ID 5.1-0062, 56.07 million output tokens per kWh, official power 9,436 W, fp4, labelled "1 kW slice of a 9.4 kW machine". 6.1-0032 is kept as the CPU comparison.
4. **Delete the whisper-unit warning:** the column is tokens/s, and samples/s comes from the loadgen logs.
5. **Computing-income line:** the section 8 wording, with an operator-share switch next to the existing sold-share switch (one extra input, no new build scope).
6. **Break-even display:** next to 0.2261, show the case break-even at the chosen sold share (0.3375 at 67%).
7. **"Does not pay off when":** add "when less than about 30% of the list price of the work reaches the operator once hardware is counted (central prices, 67% sold), or when the only work is LLM generation on a CPU-only server at the lowest price".
8. **Open risk 11:** from "no defensible value" to "defensible as list value plus required shares; operator share, sold share and the buyer of 28,000 audio-hours a day per house remain unsourced".
9. **Saturday, role B:** repeat the probe with the real audio set (accumulator method, ≥ 5 minutes, plugged in), then rerun `r3_income.py --wh-per-audio-hour <E>`. Watch for the `SystemPowerIn` trap.
10. **Question for DigitalHeat:** "Do you sell hours or finished jobs, and what share of the end-customer price reaches the machine owner?"
