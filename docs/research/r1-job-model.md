# Round 1 — job model and the never-dump vs. deadline trade-off

Investigator output for weak point 2 ("no job model"). Assessment only: `analysis/r1_job_sim.py` is an exploratory script, not the team's scheduler.

Status labels: **sourced** (URL opened and number read there), **computed** (script + command), **assumption** (our design choice), **unverified** (estimate, not checked), **placeholder** (team must measure on Saturday).

## 1. Short answer

1. Two job types, both sized in reference-server hours so energy is `runtime × 1 kW`: **J1 transcription batch** (0.5 server-h, 0.5 kWh, 24 h deadline, measured on the laptop) and **J2 LLM/embedding backlog** (4 server-h, 4 kWh, 7-day deadline, from MLPerf). Sizes follow the Alibaba trace's median (23 min) and P90 (4.5 h) instance run-time (sourced).
2. With **unlimited jobs** the model reproduces the baseline exactly (N=8: 92.9% coverage, 0 dumped, 51.8% utilisation) and "missed deadlines" is undefined. That is the number in the plan today and it must be declared as an unlimited-backlog result.
3. With a **finite flat demand** there is no free lunch at a single house (N=8, computed):
   - sized to winter (185 server-h/day): coverage 92.5%, but **39.0% of jobs (46% of the work) cannot run at the house** between April and October. They are moved if a summer site exists, missed if not.
   - same demand, dump heat to keep deadlines: 0% missed, but **24,597 kWh dumped** (79% of the house's annual heat demand) and break-even rises from 0.2261 to **0.2750 CHF/server-h**.
   - sized to summer (15 server-h/day): 0% missed, 0 dumped, but coverage **14.0%** and utilisation **7.8%**.
4. Longer deadlines do not solve it: even 7 days / 90 days leaves 22.2% of jobs without a permit (N=8, annual-mean demand). Deadlines buffer weather, not seasons.
5. Deadline rule that follows from the case constants: a dumped server-hour costs the full electricity price, **0.3325 CHF**, a heat-matched one **0.2261 CHF**. So: dump only for jobs that pay more than 0.3325 CHF/server-h; move everything else.

## 2. The two job types (proposal)

| | J1: transcription batch | J2: LLM / embedding backlog |
|---|---|---|
| What | speech-to-text on an audio archive (Whisper) | offline text generation or embedding of a document backlog (llama3.1-8b class) |
| Runs on our laptop | **yes**, this is the measured one | optional second measurement |
| Runtime on 1 kW reference server | 0.5 h (assumption, anchored on trace median 23 min) | 4 h (assumption, anchored on trace P90 4.5 h) |
| Energy per job | 0.5 kWh (= runtime × 1 kW, case rule) | 4.0 kWh |
| Interruptible | yes | yes |
| Checkpoint granularity | one audio file (≤ 30 s chunk inside Whisper); state = list of finished files | one batch of prompts/documents; state = index of last finished batch |
| Deadline | 24 h after arrival (assumption) | 168 h after arrival (assumption) |
| Work content of one job | placeholder: `0.5 kWh ÷ measured Wh per audio-hour` | 17.7 million output tokens = 4 h × 1,227.99 tokens/s (computed from MLPerf row below; power of that system unverified) |
| Share of arriving work | 50% (assumption) | 50% (assumption) |

Why these sizes. The Alibaba GPU trace paper reports: "The median run-time (23 minutes) … 90th percentile (P90) run-time (4.5 hours)", run-time "spreading four orders of magnitude" (**sourced**: <https://www.usenix.org/system/files/nsdi22-paper-weng.pdf>, section on instance run-time, read via one Firecrawl PDF scrape, pages 1–8 of 17). We take one short and one long type at roughly those two points instead of a full distribution. This is "inspiration", as the case says; it is not a fit.

### Sources read for workload numbers

| Number | Value | Status | Source |
|---|---|---|---|
| Trace size | 6,742 GPUs, "more than 7.5 million instances of 1.2 million tasks submitted by over 1,300 users", two months | sourced | <https://www.usenix.org/system/files/nsdi22-paper-weng.pdf> |
| Trace period, machines | July and August 2020, "over 6,500 GPUs (on ~1800 machines)" | sourced | <https://github.com/alibaba/clusterdata/blob/master/cluster-trace-gpu-v2020/README.md> |
| Instance run-time | median 23 min, P90 4.5 h | sourced | NSDI paper, same URL |
| Arrival shape | "rough diurnal patterns", weekdays slightly higher than weekends, "midnight is also a rush hour" | sourced | NSDI paper, same URL |
| Recurrence | "65% of tasks repeatedly executed at least 5 times" | sourced | NSDI paper, same URL |
| Tasks per GPU per day | 2.9 (= 1.2 M ÷ 62 days ÷ 6,742) | computed from sourced numbers; 62 days is our reading of "July and August" | — |
| Instances per GPU per day | 17.9 (= 7.5 M ÷ 62 ÷ 6,742) | computed, same caveat | — |
| MLPerf v6.1 whisper, Offline, CPU-only 2× Xeon 6787P (Dell R770, ID 6.1-0032) | 1,539.49 (spreadsheet header says "Samples/s") | sourced, local file `data/raw/mlperf_inference_v6.1_summary.xlsx`, sheet "datacenter - closed" | <https://github.com/mlcommons/inference_results_v6.1> (as named in data/README.md; I read the local copy only) |
| Same system, llama3.1-8b Offline | 1,227.99 tokens/s | sourced, same local file | same |
| Other CPU-only 2-socket rows, whisper | 1,477.4 (Supermicro 6.1-0096), 1,548.1 (QCT 6.1-0089), 2,275.93 (Dell 2× 6980P, 6.1-0031) | sourced, same local file | same |
| MLPerf whisper benchmark definition | whisper-large-v3; LibriSpeech dev-clean + dev-other, "approximately 10 hours", repackaged "into samples approaching 30s" | sourced | <https://raw.githubusercontent.com/mlcommons/inference/master/speech2text/README.md> |
| MLPerf whisper sample count and metric | `whisper.*.performance_sample_count_override = 1633`; `whisper.*.use_token_latencies = 1` | sourced | <https://raw.githubusercontent.com/mlcommons/inference/master/loadgen/mlperf.conf> |
| mlx_whisper vs whisper.cpp, large-v3-turbo | 13.135 s vs 26.704 s on one file; chip and audio length not stated, so no real-time factor can be derived | sourced but not usable for sizing | <https://notes.billmill.org/dev_blog/2026/01/updated_my_mlx_whisper_vs._whisper.cpp_benchmark.html> |

**Unit warning (unverified).** The summary spreadsheet labels the whisper column "Samples/s". 1,633 samples over about 10 hours is about 22 s of audio per sample, so 1,539 samples/s on a CPU-only server would be about 9 audio-hours per second, which is not plausible. The loadgen config sets `use_token_latencies = 1` for whisper, so the figure is most likely **tokens/s**. Do not convert the MLPerf whisper number into audio-hours in the pitch until someone checks one submission's detail log. If it is tokens/s, one J1 job is 0.5 h × 1,539.49 = 2.77 million tokens on that system (computed).

**Not found.** No power figure for these MLPerf systems (the summary has throughput only, as data/README.md already says). "A CPU-only 2-socket Xeon server draws about 1 kW" is **unverified**; I could not open a spec page for the CPU's TDP. No published sentences-per-second figure for an embedding model on Apple silicon was found (sbert.net pages opened, the speed table was not in the fetched text). No Apple power figure for the M3 Pro laptop (Apple's page <https://support.apple.com/en-us/102839> covers Mac Pro only).

### What is already on the laptop (read-only checks, nothing installed)

Machine: Apple M3 Pro, 12 cores, 18 GB (`sysctl`). Python 3.13.12.

| Present | Missing |
|---|---|
| `mlx_whisper` module, `torch` 2.14.0, `psutil`, `numpy`, `sklearn` | `sentence_transformers`, `transformers`, `faster_whisper`, `openai-whisper`, `onnxruntime`, `codecarbon` |
| `ffmpeg` 9.0.2, `ollama` (models: qwen2.5:7b, gemma3:4b, qwen2.5vl:7b, dolphin-mixtral), `powermetrics` (needs sudo) | `whisper-cpp` / `whisper-cli` binary, `macmon`, `asitop` |
| Hugging Face cache: `mlx-community/whisper-large-v3-turbo`, `BAAI/bge-m3`, `BAAI/bge-reranker-v2-m3`, `ggerganov/whisper.cpp` | — |

Consequence: **transcription with `mlx_whisper` + cached `whisper-large-v3-turbo` can run on Saturday without installing anything**, and it is the same benchmark family as MLPerf whisper (which uses large-v3, not turbo: say so). It runs on the M3's GPU through Metal, not on the CPU alone. The case says "a CPU is enough", it does not forbid a GPU. If the team wants a strict CPU job, the shortest routes each need one install on Saturday: `sentence-transformers` on `device="cpu"` with the cached bge-m3, or a `whisper-cpp` binary with the cached ggml model. An embeddings job as J1 (as in the current plan) is therefore not runnable today without an install.

### Saturday measurement procedure for J1 (placeholders to fill)

1. Audio set: about 30 minutes of public-domain speech split into files of 20–30 s (LibriSpeech dev-clean from <http://www.openslr.org/12/> is the set MLPerf uses; the URL is quoted in the MLPerf README, I did not open it). Record total audio seconds with `ffprobe`.
2. Run the files one by one, append each finished file name to a `done.txt` (this is the checkpoint), and time the whole run with `time.perf_counter()`. Repeat three times, report mean and spread. First run includes model load: report it separately as the resume overhead.
3. Power, two options. (a) No sudo: unplug the charger and sample `ioreg -r -c AppleSmartBattery` every 5 s; power in W = `Voltage` (mV) × `InstantAmperage` (mA) ÷ 10⁶. Both fields exist on this machine (checked while plugged in). Take an idle sample for 2 minutes first. (b) With sudo, run by a team member: `sudo powermetrics --samplers cpu_power -i 1000`, which reports CPU + GPU package power. State which one was used; (a) is whole-device power including the screen, which is what the case's "runtime × the device's power draw" asks for.
4. Report: runtime per audio-hour, Wh per audio-hour (gross, and net of idle), tokens per audio-second (to compare with MLPerf if the unit question is settled).
5. Scaling to the reference server (assumption A1, must be stated in the pitch): **equal energy per unit of work**. A job that costs E kWh on the laptop costs E kWh on the reference server and takes `E ÷ 1 kW` hours there. One J1 job is then "0.5 kWh of transcription" = `0.5 kWh ÷ (measured Wh per audio-hour)` audio-hours. The laptop demo runs a slice of one job, not a whole one: at an unverified 30–40 W, 0.5 kWh would take the laptop 12–17 hours.
6. Where A1 stops holding: a GPU server is far more efficient per token than a laptop and a CPU server probably less; A1 only fixes the heat side (1 kWh of electricity is 0.8 kWh of heat whatever the chip does). It says nothing reliable about how much compute a customer gets per server-hour, so computing income per server-hour must come from market prices per server-hour, not from our laptop throughput.

### Jobs per day: where the number comes from

There is no public figure for how many jobs a 4–10 server basement site would receive. The honest statement is: **arrivals are a contract size we choose (assumption), not market data.** The simulation therefore uses a flat, deterministic stream of R server-hours per day, half of the work in each type, which gives `R` J1 jobs and `R ÷ 8` J2 jobs per day. For N=8: winter sizing R = 184.8 → 207.9 jobs/day; annual-mean sizing R = 99.4 → 111.8 jobs/day; summer sizing R = 15.0 → 16.9 jobs/day (computed).

Plausibility anchor only: winter sizing is 26 jobs per server per day and annual sizing 14, against 17.9 instances per GPU per day in the Alibaba trace (computed above). Equating one 1 kW server with one GPU is an assumption.

## 3. Simulation

Script: `analysis/r1_job_sim.py` (standard library; imports `load()` and the case constants from `analysis/baseline_sweep.py`).

Command: `python3 analysis/r1_job_sim.py` (add `--monthly` for the month tables). Runs in about 7 s.

Model in one paragraph: hourly, heat-following permits identical to `follow` in the baseline (a permit is one server-hour whose 0.8 kWh fits demand plus free tank space). Jobs are filled into permits earliest-deadline-first; a job uses one server at a time. A job is urgent when it must run in every remaining hour to finish. An urgent job without a permit either leaves the house (`nodump`) or runs anyway and its heat is dumped (`dump`, up to N servers).

Column meaning: `left%` = jobs that left under `nodump`. **This is the missed-deadline figure if there is no second site, and the moved figure if there is one.** They are never counted as completed here. `miss%` = jobs that could not run even with dumping. `moved h` = server-hours of work that left. `BE` = `(electricity − value of heat used) ÷ server-hours sold`.

Output (computed, pasted unchanged):

```
 N demand    policy  srv-h/d jobs/d  cover dump kWh   util  sold h  done%  left%  miss% moved h BE CHF/h
 4 unlimited -           inf    inf  58.0%        0  64.7%   22654    n/a    n/a    n/a     n/a   0.2261
 4 winter    nodump     96.0  108.0  58.0%        0  64.6%   22650  70.4%  29.6%   0.0%   12016   0.2261
 4 winter    dump       96.0  108.0  58.0%     9604  98.9%   34662 100.0%   0.0%   0.0%       0   0.2630
 4 annual    nodump     62.1   69.8  42.7%        0  47.5%   16658  79.3%  20.7%   0.0%    5992   0.2261
 4 annual    dump       62.1   69.8  42.7%     4788  64.6%   22650 100.0%   0.0%   0.0%       0   0.2542
 4 summer    nodump     15.0   16.9  14.0%        0  15.6%    5474 100.0%   0.0%   0.0%       0   0.2261
 4 summer    dump       15.0   16.9  14.0%        0  15.6%    5474 100.0%   0.0%   0.0%       0   0.2261

 6 unlimited -           inf    inf  79.6%        0  59.1%   31067    n/a    n/a    n/a     n/a   0.2261
 6 winter    nodump    144.0  162.0  79.6%        0  59.1%   31058  64.6%  35.4%   0.0%   20925   0.2261
 6 winter    dump      144.0  162.0  79.6%    16737  98.9%   51982 100.0%   0.0%   0.0%       0   0.2689
 6 annual    nodump     85.1   95.8  55.8%        0  41.4%   21784  74.0%  26.0%   0.0%    9278   0.2261
 6 annual    dump       85.1   95.8  55.8%     7417  59.1%   31062 100.0%   0.0%   0.0%       0   0.2579
 6 summer    nodump     15.0   16.9  14.0%        0  10.4%    5474 100.0%   0.0%   0.0%       0   0.2261
 6 summer    dump       15.0   16.9  14.0%        0  10.4%    5474 100.0%   0.0%   0.0%       0   0.2261

 8 unlimited -           inf    inf  92.9%        0  51.8%   36281    n/a    n/a    n/a     n/a   0.2261
 8 winter    nodump    184.8  207.9  92.5%        0  51.5%   36112  61.0%  39.0%   0.0%   30746   0.2261
 8 winter    dump      184.8  207.9  92.5%    24597  95.4%   66858 100.0%   0.0%   0.0%       0   0.2750
 8 annual    nodump     99.4  111.8  63.3%        0  35.3%   24708  71.6%  28.4%   0.0%   11568   0.2261
 8 annual    dump       99.4  111.8  63.3%     9250  51.8%   36276 100.0%   0.0%   0.0%       0   0.2600
 8 summer    nodump     15.0   16.9  14.0%        0   7.8%    5474 100.0%   0.0%   0.0%       0   0.2261
 8 summer    dump       15.0   16.9  14.0%        0   7.8%    5474 100.0%   0.0%   0.0%       0   0.2261

10 unlimited -           inf    inf  99.3%        0  44.2%   38749    n/a    n/a    n/a     n/a   0.2261
10 winter    nodump    206.8  232.7  98.0%        0  43.7%   38274  59.2%  40.8%   0.0%   36698   0.2261
10 winter    dump      206.8  232.7  98.0%    29355  85.6%   74968 100.0%   0.0%   0.0%       0   0.2782
10 annual    nodump    106.2  119.4  66.4%        0  29.6%   25914  70.4%  29.6%   0.0%   12829   0.2261
10 annual    dump      106.2  119.4  66.4%    10260  44.2%   38744 100.0%   0.0%   0.0%       0   0.2613
10 summer    nodump     15.0   16.9  14.0%        0   6.2%    5474 100.0%   0.0%   0.0%       0   0.2261
10 summer    dump       15.0   16.9  14.0%        0   6.2%    5474 100.0%   0.0%   0.0%       0   0.2261

== sensitivity, N=8, annual-mean rate: do longer deadlines remove the problem? ==
 8 24h/168h  nodump     99.4  111.8  63.3%        0  35.3%   24708  71.6%  28.4%   0.0%   11568   0.2261
 8 24h/168h  dump       99.4  111.8  63.3%     9250  51.8%   36276 100.0%   0.0%   0.0%       0   0.2600
 8 72h/720h  nodump     99.4  111.8  66.6%        0  37.1%   26000  74.3%  25.7%   0.0%   10276   0.2261
 8 72h/720h  dump       99.4  111.8  66.6%     8217  51.8%   36276 100.0%   0.0%   0.0%       0   0.2562
 8 168h/2160hnodump     99.4  111.8  74.6%        0  41.6%   29141  77.8%  22.2%   0.0%    7093   0.2261
 8 168h/2160hdump       99.4  111.8  74.6%     5672  51.7%   36231 100.0%   0.0%   0.0%       0   0.2469

== sensitivity, N=8, nodump: flat rate between summer and winter sizing ==
 8 flat 15   nodump     15.0   16.9  14.0%        0   7.8%    5474 100.0%   0.0%   0.0%       0   0.2261
 8 flat 30   nodump     30.0   33.8  23.8%        0  13.2%    9283  95.3%   4.7%   0.0%    1664   0.2261
 8 flat 50   nodump     50.0   56.2  35.9%        0  20.0%   13996  83.7%  16.3%   0.0%    4250   0.2261
 8 flat 75   nodump     75.0   84.4  50.3%        0  28.0%   19618  76.1%  23.9%   0.0%    7752   0.2261
 8 flat 100  nodump    100.0  112.5  63.6%        0  35.4%   24824  71.5%  28.5%   0.0%   11670   0.2261
 8 flat 125  nodump    125.0  140.6  74.4%        0  41.4%   29030  67.4%  32.6%   0.0%   16590   0.2261
 8 flat 150  nodump    150.0  168.8  83.4%        0  46.5%   32558  64.3%  35.7%   0.0%   22184   0.2261
 8 flat 190  nodump    190.0  213.8  92.9%        0  51.7%   36262  60.5%  39.5%   0.0%   32381   0.2261
```

Month view, N=8, annual-mean demand, `python3 analysis/r1_job_sim.py --monthly` (computed):

```
never dump                                           dump to keep deadlines
month  arrived    done    left  sold h               done   sold h dump kWh
01        3466    3464       0    3076               3464     3076        0
04        3355    2883     332    2591               3216     2758      132
05        3466    1745    1683    1331               3426     2919     1270
06        3354     900    2455     450               3355     2982     2026
07        3467     930    2536     465               3465     3081     2093
08        3467     930    2536     465               3467     3081     2093
09        3355    1588    1767    1175               3355     2983     1447
10        3466    3344     281    3153               3626     3390      191
```

(Rows for Feb, Mar, Nov, Dec omitted: nothing left, nothing dumped. Layout rearranged side by side; numbers unchanged.)

### What the numbers say

- **Check:** "unlimited" reproduces `baseline_sweep.py` exactly (N=8: 92.9%, 36,281 server-h, 0.2261). Every figure in the current plan is an unlimited-jobs figure.
- **Coverage is bought with demand, not with servers.** At N=8, coverage climbs from 14.0% (15 server-h/day) to 92.9% (190 server-h/day) only if that much work arrives every day. Each step up in flat demand raises the share that has no permit in summer: 4.7% at 30, 28.5% at 100, 39.5% at 190.
- **Never dump at winter-sized demand, N=8:** 39.0% of jobs leave, carrying 30,746 server-h, 46% of the arriving work (30,746 ÷ (36,112 + 30,746)). Averaged over the year that is 84 server-h/day (30,746 ÷ 365), but it falls almost entirely between May and September: in June to August about 170 of the 185 server-h/day leave, which is 136 kWh of heat per day at 80% recovery, the hot-water demand of about eleven reference households (12 kWh/day each).
- **Dump to keep deadlines, same demand:** utilisation 95.4% and 66,858 server-h sold, but 24,597 kWh dumped (79% of the 31,231 kWh annual heat demand). Break-even 0.2750 CHF/server-h instead of 0.2261.
- **The marginal rule.** From the case constants alone: a heat-matched server-hour costs 0.3325 − 0.8 × 0.3325 ÷ 2.5 = 0.2261 CHF net; a dumped one costs 0.3325 CHF. Dumping is rational only for work priced above 0.3325 CHF/server-h. Between 0.2261 and 0.3325 only heat-matched hours pay; below 0.2261 nothing pays.
- **Deadlines are a weather buffer, not a season buffer.** Tripling them (72 h / 30 days) moves `left%` from 28.4% to 25.7%; a 90-day deadline for J2 still leaves 22.2%.
- **Summer sizing is the only flat demand with 0% missed and 0 dumped**, and it wastes the hardware (7.8% utilisation at N=8) and covers 14.0% of the heat.

### Limits of this script (what a critic should attack)

1. A moved job leaves at its last possible moment with zero hand-off time, and the partner site is assumed to have a free server instantly. A real hand-off needs margin and the scheduler should move earlier (at admission, from the seasonal forecast). The moved share is probably not sensitive to this; the missed share is: with any transfer delay, late hand-offs become misses.
2. Arrivals are flat and deterministic. No bursts, no diurnal shape, no weekday effect. With deadlines of 24 h and more, an hourly shape should matter little; not tested.
3. Pausing costs nothing. Real resume cost (model reload, tens of seconds, unverified) is small against a one-hour step but not zero for a 0.5 h job.
4. Plain EDF favours J1 (earlier deadlines), so in summer J2 jobs wait the full 7 days and then leave. The split of `left%` by type is not reported.
5. The 50/50 work mix, both deadlines and both runtimes are assumptions. Only the run-time anchors are sourced.
6. Servers are counted per hour of work, so a half-used server-hour counts as half an hour running (sub-hour on/off).
7. Jobs still open on 31 December are excluded from the percentages.
8. Stand-in profile, lossless tank, direct hot water: the case assumptions, same as the baseline.

## 4. Recommendation

**Job mix.** J1 = transcription batch, measured on the laptop with `mlx_whisper` and the already cached `whisper-large-v3-turbo` (no install needed; say plainly that it uses the laptop GPU and that MLPerf uses large-v3). J2 = LLM/embedding backlog with numbers from MLPerf v6.1 llama3.1-8b Offline on a CPU-only server. This swaps the current plan's roles (embeddings measured, transcription from benchmark) because embeddings cannot run on the laptop today without installing a package.

**Arrival model.** Present three rows side by side and say which is which, never the unlimited row alone:
1. *Unlimited (declared)*: the upper bound, today's key numbers.
2. *Flat contract sized to winter*: the stress case, with both policies.
3. *Heat-shaped contract*: DigitalHeat sells each house's capacity as a seasonal profile and routes the rest to summer sites at admission. In this single-house model that is numerically the `nodump` row with `left%` read as "placed elsewhere at admission". It needs the multi-site assumption stated.

**Deadline rule.** Never dump by default. Move a job as soon as the forecast shows no permit before its deadline. Dump only for a job whose price is above the electricity price, 0.3325 CHF per server-hour. This gives the jury a rule with a number instead of a slogan.

**The honest missed-deadline figure.** There is no single one; it depends on a demand assumption nobody has data for. What can be said without bending anything (N=8, case assumptions, stand-in profile, our job mix):

- "With unlimited jobs, missed deadlines are not defined."
- "With a flat demand sized to winter and no dumping, **39.0% of jobs cannot be finished at the house in time**. With a summer partner site they are moved and 0% are missed; without one, 39.0% is the missed-deadline figure."
- "Dumping instead brings missed deadlines to 0% and costs 24,597 kWh of dumped heat and 0.049 CHF more per server-hour."
- "A single house on its own stays below 5% missed without dumping only up to about 30 server-hours of work per day, which covers 23.8% of its heat."

Do not open the pitch with "0% missed deadlines" unless the moved share stands next to it.

## 5. Commands run

```
python3 analysis/r1_job_sim.py
python3 analysis/r1_job_sim.py --monthly
python3 --version; sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize
command -v ffmpeg ollama whisper whisper-cpp whisper-cli powermetrics; ollama list
python3 -c "import importlib.util ..."           # find_spec for torch, mlx_whisper, sentence_transformers, ...
ls ~/.cache/huggingface/hub
ioreg -r -c AppleSmartBattery | grep -E 'InstantAmperage|Voltage'
python3 (zipfile + xml.etree) on data/raw/mlperf_inference_v6.1_summary.xlsx   # whisper and llama3.1-8b columns
curl https://raw.githubusercontent.com/mlcommons/inference/master/loadgen/mlperf.conf   # grep whisper
curl https://raw.githubusercontent.com/mlcommons/inference/master/speech2text/README.md
```

Web: free fetch/search for everything except one paid Firecrawl scrape (the NSDI paper PDF, too large for the free fetcher). Firecrawl calls used: 1 of 5.
