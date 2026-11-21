# Round 1 — critique of the job model (docs/research/r1-job-model.md)

Critic pass, written as a sceptical DigitalHeat founder. Nothing in the investigator's files was changed. Firecrawl calls used: 0.

## What I re-checked and how

| Item | Check | Result |
|---|---|---|
| Alibaba trace numbers (C1–C3) | Downloaded <https://www.usenix.org/system/files/nsdi22-paper-weng.pdf> with curl, `pdftotext -layout`, grep | Confirmed: 6,742 GPUs; "more than 7.5 million instances of 1.2 million tasks submitted by over 1,300 users"; "median run-time (23 minutes) ... 90th percentile (P90) run-time (4.5 hours)"; rough diurnal pattern, weekdays slightly higher, midnight rush hour; "around 65% tasks repeatedly run at least 5 times"; footnote "collected in July and August 2020" |
| Trace README | curl of the raw README on GitHub | Confirmed "over 6,500 GPUs (on ~1800 machines)", July and August 2020 |
| MLPerf row 6.1-0032 (C5) | Parsed `data/raw/mlperf_inference_v6.1_summary.xlsx` (inline strings, no sharedStrings.xml) | Confirmed: Dell, 2x Xeon 6787P, 0 accelerators, llama3.1-8b Offline 1227.99 Tokens/s, whisper Offline 1539.49 with unit row "Samples/s". No power column in any sheet |
| MLPerf whisper definition (C6) | WebFetch of the speech2text README, curl of mlperf.conf | Confirmed model, dataset, "approximately 10 hours", "approaching 30s", `performance_sample_count_override = 1633`, `use_token_latencies = 1` |
| Laptop tooling (C9) | sysctl, find_spec, `command -v`, `ls -laL` of the HF cache | Confirmed. The whisper-large-v3-turbo weights are really there (1.6 GB behind a symlink). Nothing was executed, so "runs without an install" is still untested |
| Battery telemetry (C10) | `ioreg -r -c AppleSmartBattery` | Fields exist, but see bug below |
| All simulation rows (C14–C23) | `python3 analysis/r1_job_sim.py --monthly` | Every quoted figure reproduced exactly |

## Findings

### 1. The 39.0% is arithmetic, not a scheduling result

Identity check (N=8, winter-sized flat demand): work arriving 67,448 server-h; sold here 36,112 + moved 30,746 = 66,858 (the rest is still open on 31 December). Heat-following capacity is 36,281 server-h. So "46% of the work leaves" is `1 − capacity ÷ demand`, with demand chosen by the investigator as a flat line at the winter mean. The queue, EDF and the deadlines contribute almost nothing: the house simply has no summer capacity. The same holds for the dump row: extra hours 30,746 × 0.8 = 24,597 kWh dumped, exactly.

Consequence: the simulation does not test a scheduler. It restates the seasonal capacity curve under a demand shape nobody proposed. That is still a useful warning, but it must not be called a "missed-deadline figure".

### 2. "Missed deadlines" is measured on jobs that a real system would never accept

Summer capacity is known months ahead (hot water, 15 server-h/day, deterministic in this model). A scheduler that admits only what it has permits for misses 0% by construction. A real missed-deadline figure comes from forecast error and from server or network failures after admission, and the script models neither: it has perfect knowledge and greedy filling. So neither 39.0% nor 0% is an honest missed-deadline figure yet. The must-have 3 figure the team needs is "accepted jobs that finished late", under an admission rule and a forecast with error.

### 3. The job-share figure moves with the mix; only the work share is stable

Re-run with the investigator's own functions (monkeypatched `WORK_SHARE`, N=8, winter, nodump):

| J1 share of work | jobs leaving | work leaving (server-h) |
|---|---|---|
| 100% | 46.4% | 31,288 |
| 50% | 39.0% | 30,746 |
| 0% | 49.3% | 30,203 |

39.0% is an artefact of the 50/50 mix and EDF favouring J1. The work share (about 46%) is the robust number.

### 4. Battery-power procedure has a sign bug

While plugged in and not charging I read `InstantAmperage = 18446744073709551126`. That is −490 mA as an unsigned 64-bit value. On battery the current is always negative, so the documented formula `Voltage × InstantAmperage ÷ 10⁶` returns about 2 × 10¹⁴ W. Fix: subtract 2⁶⁴ when the value exceeds 2⁶³ and take the absolute value. The investigator saw a positive 1307 mA only because the battery was charging; that number is charge current, not device power.

The same ioreg class also exposes `SystemPowerIn`, `SystemLoad` and `BatteryPower` under `PowerTelemetryData` (seen: `SystemLoad = 5166`, `BatteryPower = 12019`). They may give wall-side power while plugged in. Units and meaning are unverified; test on Saturday against the battery method.

### 5. Equal-energy scaling makes the laptop measurement irrelevant to the server

"A job that costs E kWh on the laptop costs E kWh on the reference server" assumes a 1 kW rack server is exactly as efficient per unit of work as an M3 Pro running on its GPU. No source supports that. The must-have says "state how you scale", so an assumption is allowed, but the jury can ask why the measured job matters at all if the server-side number is defined rather than derived. A defensible alternative uses the MLPerf row: tokens/s of a named server ÷ its power. That needs the missing power figure.

J1 is also defined backwards (0.5 kWh first, work content later). By the investigator's own estimate one J1 takes the laptop 12–17 hours, so the "measured runtime" in must-have 1 would be of a slice, not of the job type. Define the job by its content (for example N minutes of audio), measure it whole, then scale.

### 6. J2 on a CPU-only server looks uncompetitive on its own numbers

Computed from C5 and the case constants, assuming the Dell system draws 1 kW (unverified): 1,227.99 tokens/s = 4.42 million tokens per server-hour. Net electricity alone is 0.2261 ÷ 4.42 = 0.051 CHF per million tokens heat-matched, 0.075 CHF dumped. I did not open a price list, so no market figure is quoted here, but small-model API prices are of this order (unverified). A founder will ask why the reference J2 is a CPU-only LLM job. Either pick a GPU row from the same spreadsheet or say plainly that the CPU row is the pessimistic case.

"LLM/embedding backlog" also names two different workloads. The MLPerf llama3.1-8b figure is text generation; it says nothing about embeddings.

### 7. The dump rule is right at the margin and silent on the alternative

0.3325 CHF is the correct marginal cost of a dumped server-hour under the case constants. Three gaps:
- It is a household retail tariff. A data centre on an industrial tariff runs the same hour for far less (no number checked), so no customer needs a basement server for work that is dumped.
- The jury ranks "least heat dumped" first within scheduling quality. Dumping 24,597 kWh for income is a scoring loss even when it is profitable.
- Hardware cost is absent. With capex, more sold hours lower the cost per hour, which pushes toward dumping; the rule does not show that tension.

### 8. Smaller points

- "Instances per GPU per day" (17.9) against "jobs per server per day" is apples to oranges: 85% of instances are gang-scheduled parts of one task, GPUs are time-shared in fractions, and the cluster mixes training with inference. Keep the arithmetic, drop it as a plausibility anchor.
- The "22 s per sample" in the unit warning rests on "approximately 10 hours" for 1,633 samples, while the same README says samples approach 30 s (1,633 × 30 s = 13.6 h). The conclusion (tokens/s) is likely right: a search snippet attributes "tokens per second" to MLCommons for whisper, and third-party listings give 350 W TDP for the Xeon 6787P. I opened neither page, so both stay unverified.
- The demo laptop is one machine. Whether the other three laptops have mlx_whisper and the model is unknown.
- Whisper through MLX runs on the laptop GPU. The case allows it, but the "CPU is enough" reading and a CPU-only J2 reference do not match each other.

## What survives

- All sourced trace and MLPerf figures as quoted.
- All script outputs as computed, under the label "flat demand, perfect foresight, zero hand-off time".
- The structural message: one house cannot give high coverage, no dumping and a flat contract at once; the year-round answer needs a second heat sink or a seasonal contract.

## What does not survive

- "39.0% missed" as a key figure or as "the honest missed-deadline figure".
- The battery formula as written.
- J1 sized as 0.5 kWh with unknown content as the measured job.
- 17.9 instances per GPU per day as support for the arrival rate.
