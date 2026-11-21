# Workloads: the real jobs, measured

Must-have 1 of the case ([case-brief.md](case-brief.md#must-haves-for-a-valid-submission-all-on-the-reference-house)): at least two job types with runtime, energy, interruptibility and deadline; at least one actually running and measured on our machine; scaled to the 1 kW reference server; jobs per day with a source.

**Both job types run for real and were measured on three team laptops (Apple M1, M3, M4).** Code: [`workloads/`](../workloads/). Measurements: one file per machine in [`data/measurements/`](../data/measurements/), averaged by [`scripts/combine_measurements.py`](../scripts/combine_measurements.py) into [`combined.json`](../data/measurements/combined.json), which the scheduler's catalog ([`workloads/catalog.py`](../workloads/catalog.py)) uses. Teammates add machines with [measure-on-your-machine.md](measure-on-your-machine.md).

## Must-have 1 checklist

| Requirement | Embeddings (`embed`) | Reranking (`rerank`) |
|---|---|---|
| What one item is | One scientific abstract → 384-dim vector | One (query, abstract) pair → relevance score |
| Model | `sentence-transformers/all-MiniLM-L6-v2` @ `1110a24` (Apache-2.0) | `cross-encoder/ms-marco-MiniLM-L6-v2` @ `233902d` (Apache-2.0) |
| Runs on our machine | yes, on 3 laptops | yes, on 3 laptops |
| Throughput, measured | 51–110 items/s (M1 → M4) | 19.5–43 items/s |
| Energy per item, measured (mean of 3, range) | **0.293 J** gross (0.262–0.322) · 0.221 J marginal | **0.660 J** gross (0.623–0.702) · 0.479 J marginal |
| Reference server (1 kW), gross basis | 12.3 M items per server-hour | 5.5 M items per server-hour |
| One job, on one reference server | 10 M abstracts = **0.81 server-hours** | 5 M pairs = **0.92 server-hours** |
| Interruptible | **yes, tested:** pause instantly, or stop at a checkpoint and resume anywhere, with identical output | same |
| Deadline | 48 h after arrival *(our assumption: batch re-indexing)* | 4 h after arrival *(our assumption: same-day evaluation run)* |
| Jobs per day | **unlimited backlog** (stated assumption; see [below](#jobs-per-day)) | **4 per house per day**, at 08, 11, 14 and 17 h *(our assumption, swept 1/4/16)* |

Why these two: DigitalHeat's own slides list "document indexing" and "CLIP embeddings" as flexible jobs ([case-presentation.md](case-presentation.md#03--ideas-for-flexible-computing-jobs)), and the case names embeddings and reranking. Together they make the first two steps of a search/RAG pipeline: index documents, then rank the candidates for a query. They differ in what matters for scheduling: the embedding job tolerates two days of delay, the reranking job only four hours.

## The data the jobs work on

[BEIR SciFact](https://huggingface.co/datasets/BeIR/scifact) (CC BY-SA 4.0), revision `b3b5335`: 5,183 scientific abstracts (median 204 words) and 1,109 claims used as queries. Stored in [`data/raw/scifact/`](../data/raw/scifact/). Abstracts of ~200 words are a typical chunk size for search/RAG indexing, so throughput carries over to real document collections.

A job is "process items 0 … N−1". Item *i* maps onto the corpus deterministically and cycles when N is bigger than the corpus, so any job size runs and repeats exactly:

- `embed`: abstract *i* mod 5,183 (title + text, truncated at 256 tokens)
- `rerank`: query (*i* div 20) mod 1,109 with abstract (7,919·*i* + 13) mod 5,183, truncated at 512 tokens. The pairing is a fixed pseudo-random spread, not real top-k retrieval. Cost depends on text length, not relevance, so throughput is the same.

## How the scheduler controls a job

```bash
.venv/bin/python -m workloads.run embed --job-dir runs/embed-001 --items 20000
```

| Signal | Effect | Lost work |
|---|---|---|
| `SIGSTOP` / `SIGCONT` | freeze / unfreeze instantly (CPU goes to 0%) | none, but the process keeps its memory, and a real server keeps drawing idle power |
| `SIGTERM` / `SIGINT` | finish the current batch, write a checkpoint, exit code **75** | none |
| same command, same `--job-dir` | resume from the checkpoint, on this or any machine holding the job dir | — |
| hard kill (`SIGKILL`, power cut) | — | at most 10 s (checkpoint interval) |
| exit code **0** | job complete | — |

`status.json` in the job dir is rewritten after every batch (state, items done, items checkpointed, items/s); `state.json` is the durable checkpoint.

**Tested (2026-11-21), repeatable with `.venv/bin/python scripts/test_interruption.py`:** a 4,000-item embedding job was paused, resumed, stopped with SIGTERM at item 960 (exit 75), restarted with the same command, and completed. Its output is bit-identical to an uninterrupted run (max abs difference 0.0). So interrupting a job costs no repeated work and changes no results.

## How we measure

**Meter:** the MacBook's battery gauge, read with `ioreg -rn AppleSmartBattery` (no sudo, unlike `powermetrics`). `AccumulatedSystemLoad ÷ SystemLoadAccumulatorCount` between two published snapshots is the exact average whole-system power over that interval, sampled once a second. The gauge publishes every ~40–60 s and measures the load only on battery. Code: [`workloads/power.py`](../workloads/power.py).

**Protocol** ([`scripts/measure_workloads.py`](../scripts/measure_workloads.py)):

1. Idle baseline over 4 publish windows, nothing running.
2. Each job starts as the real `workloads.run` subprocess. Model loading and one full warm-up window are discarded, then power is averaged over 4 windows while counting finished items from `status.json`. The job is stopped with SIGTERM.
3. Gross J/item = load power ÷ items/s. Marginal J/item = (load − idle) ÷ items/s.

**Team results** (all on battery, torch 2.5.1 on CPU, 4 threads, batch size 32, same code and pinned models):

| Machine | Idle W | embed items/s | embed W | embed J/item (gross · marginal) | rerank items/s | rerank W | rerank J/item (gross · marginal) |
|---|---|---|---|---|---|---|---|
| Apple M1, 8 GB, macOS 26.3.1 | 5.97 | 50.96 | 16.42 | 0.322 · 0.205 | 19.50 | 12.75 | 0.654 · 0.348 |
| Apple M3, macOS 15.2 | 3.95 | 73.72 | 21.74 | 0.295 · 0.241 | 32.19 | 20.05 | 0.623 · 0.500 |
| Apple M4, 10 cores, macOS 26.6.2 | 4.86 | 109.55 | 28.67 | 0.262 · 0.217 | 43.12 | 30.29 | 0.702 · 0.590 |
| **Mean** | | | | **0.293** · 0.221 | | | **0.660** · 0.479 |

**Speed doubles from M1 to M4, but gross energy per item stays within ±10%.** That is why the reference server is sized by energy per item, not by laptop speed. Marginal energy varies more between machines (up to ±26% for reranking), which is another reason to use gross as the default.

**Example of one run** (Apple M1, measured 2026-11-21 00:10 UTC):

| | Power (W) per window | Average | Covered |
|---|---|---|---|
| Idle | 5.64 · 5.63 · 8.49 · 5.76 | 5.97 W | 197 s |
| embed | 17.31 · 16.88 · 16.07 · 15.87 | 16.42 W | 148 s, 7,680 items |
| rerank | 12.79 · 12.80 · 12.72 · 12.70 | 12.75 W | 208 s, 4,128 items |

Repeat it: unplug the charger, close other apps, then `.venv/bin/python scripts/measure_workloads.py --label <you>`. That takes ~15 min and writes a new file to `data/measurements/`. On machines without the battery meter, `--no-meter` records speed only.

## Scaling to the 1 kW reference server

```
items per server-hour = 3,600,000 J ÷ (J per item on our machine × efficiency factor)
```

- **Default: gross J/item, efficiency factor 1.** The reference server's 1 kW is its whole draw, including idle, fans and power supply. The comparable figure on our machine is the whole-system draw ÷ throughput, not the marginal one.
- **Optimistic bound:** marginal J/item (counts only the energy above idle).
- **Efficiency factor:** our assumption, not sourced. A 1 kW x86 CPU server may need more energy per item than an M1 (factor > 1). A GPU server, for which these models are built, may need far less (factor < 1). The yearly balance should be run at 0.5×, 1×, 2× and 4×.

**This choice does not change the heat.** One reference server turns 1 kWh of electricity into 0.8 kWh of recoverable heat per hour, whatever it computes. Efficiency only changes how much useful output one server-hour delivers. So the break-even price per server-hour from must-have 3 is the same for any workload. What changes is the price per unit of output a customer would have to pay:

| | Break-even per server-hour | Per 1 M embeddings | Per 1 M rerank pairs |
|---|---|---|---|
| All heat used (0.3325 − 0.8 × 0.1330) | 0.226 CHF | 0.018 CHF | 0.041 CHF |
| All heat dumped (0.3325) | 0.333 CHF | 0.027 CHF | 0.061 CHF |

(Electricity 0.3325 CHF/kWh and heat value 0.1330 CHF/kWh from [data/README.md](../data/README.md#electricity-price-elcom-2026-iwb-basel-h4), team-mean gross basis, factor 1. Hardware cost is excluded, as in the case's formula.) Comparing these with what cloud providers charge for the same output is part of the economics workstream.

## Jobs per day

The case requires the number of jobs arriving per day and where it comes from, and says a model that assumes unlimited jobs must state it. Ours (set in [`workloads/catalog.py`](../workloads/catalog.py), `JOB_DEFAULTS`):

- **Embeddings: unlimited backlog. The model assumes there is always embedding work waiting.** It is the flexible filler: servers run it whenever their heat is useful, and pause it when it is not. Utilisation is therefore limited by heat demand, not by a lack of jobs. In reality, demand for flexible computing is finite. So the yearly utilisation is an upper bound, reached only if DigitalHeat sells enough flexible work.
- **Reranking: a fixed stream of 4 jobs per house per day, every day of the year, arriving at 08:00, 11:00, 14:00 and 17:00 local time, each due 4 h after arrival.** This is our assumption, not taken from a trace. It stands for one customer's evaluation runs spread over a working day. These are the jobs that can be missed, so they are what the "missed deadlines" figure counts.

Why 4 per day: 4 × 0.92 server-hours ≈ 3.7 server-hours ≈ **2.9 kWh of heat per day**, about a quarter of summer hot-water demand (12 kWh/day). In winter the stream is small next to heating demand. In summer it fits the heat demand *only if* the scheduler keeps tank room for it, instead of filling the tank with embedding work. Otherwise the jobs must run anyway and the heat is dumped, or they miss their deadline. So this is the stream that tests the scheduler.

**Sensitivity:** the yearly balance is also run at 1 and 16 rerank jobs per day. At ~16 per day (≈ 11.7 kWh of heat per day), the deadline jobs alone produce all of summer's heat demand, so above that dumping heat is unavoidable in summer.

For scale: one reference server can do ~30 embedding jobs or ~26 rerank jobs per day.

## Limits of these numbers

- **Three laptops, one run of ~2–4 minutes per job each,** all Apple silicon. No x86 or server hardware has been measured. Within a run, the power windows vary by up to ±5% for embeddings. Idle baselines are noisy: the M1 had one 8.5 W spike (median 5.70 W), and the M4's idle drifted from 5.5 to 3.7 W. Marginal figures are therefore less reliable than gross.
- **Thermal drift:** on the M1, embedding power fell from 17.3 to 15.9 W over the run, likely thermal throttling on a fanless laptop. A long-running steady state may be slightly slower.
- **M4 reranking is the outlier:** it costs more energy per item than on the older chips (0.70 vs 0.62–0.65 J), while M4 embedding costs less. We have not investigated why. It is inside the ±6% range we report.
- **Whole-system meter:** display, editor and background tasks are inside both idle and load. The gross figure is therefore a little pessimistic, and the marginal figure assumes background load stayed steady.
- **CPU only**, small models (22 M parameters). Larger models (LLM batch inference, transcription) would have very different energy per item but the same heat per server-hour.
- **Reranking pairs are not real top-k retrieval** (see above). This affects relevance, not cost.

## Optional improvements (not done)

- **Reasoning for the deadlines:** 48 h and 4 h are plausible but unsourced. A sentence from a real use case (e.g. how often a search index is rebuilt, or how fast evaluation results are needed) would back them up.
- **A source for the efficiency factor:** we have not measured or sourced how a 1 kW server's energy per item compares with a laptop's. MLPerf Inference power results ([mlcommons.org](https://mlcommons.org/benchmarks/inference-datacenter/)) are the place to look: they report samples per second per watt for datacenter systems. Until then, the yearly balance is run at efficiency factor 0.5–4×.
- **Arrival rates from a trace:** the 4 rerank jobs per day could be replaced by a rate from the [Alibaba GPU cluster trace 2020](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020) (several GB, not downloaded).

## Apple M4 battery-gauge diagnostic

On 2026-11-21, an Apple M4 MacBook Pro running macOS 26.6.2 started this embedding diagnostic on battery at 92%. All three snapshots showed `ExternalConnected = No`. The diagnostic followed the supplied command below, with a battery-power check before launch and SIGTERM sent directly to the embedding process ID in place of `pkill`. The job checkpointed after 22,624 items and exited with code 75.

```sh
cd digitalheat && (.venv/bin/python -m workloads.run embed --job-dir runs/diag --items 100000000 --no-outputs >/dev/null &) ; sleep 30; for i in 1 2 3; do date +%T; ioreg -rn AppleSmartBattery | grep -oE '"(ExternalConnected|UpdateTime|Voltage|InstantAmperage|Amperage|SystemLoad|AccumulatedSystemLoad|SystemLoadAccumulatorCount|BatteryPower|AccumulatedBatteryPower|BatteryPowerAccumulatorCount)" ?= ?[A-Za-z0-9]+'; sleep 60; done; pkill -f "workloads.run embed --job-dir runs/diag"
```

Raw `ioreg` values are shown below. Each snapshot printed the same `UpdateTime` twice and two `Voltage` values, listed in output order. Times are local to Zurich (CET).

| Field | 11:10:57 | 11:11:57 | 11:12:57 |
|---|---:|---:|---:|
| `ExternalConnected` | No | No | No |
| `UpdateTime` | 1795255842 | 1795255902 | 1795255966 |
| `Voltage` (first) | 12618 | 12255 | 12205 |
| `Voltage` (second) | 12343 | 12257 | 12206 |
| `Amperage` | 18446744073709548773 | 18446744073709548762 | 18446744073709548671 |
| `InstantAmperage` | 18446744073709548773 | 18446744073709548762 | 18446744073709548671 |
| `SystemLoad` | 18446744073709520941 | 18446744073709521447 | 18446744073709522026 |
| `AccumulatedSystemLoad` | 4334438273 | 4332676855 | 4330769464 |
| `SystemLoadAccumulatorCount` | 1733117 | 1733176 | 1733240 |
| `BatteryPower` | 30675 | 30169 | 29590 |
| `AccumulatedBatteryPower` | 674894820 | 676656238 | 678563629 |
| `BatteryPowerAccumulatorCount` | 36989 | 37048 | 37112 |

In all three snapshots, interpreting `SystemLoad` as a signed 64-bit integer gives the exact negative of `BatteryPower`. Dividing the change in each power accumulator by the change in its sample count gives the following interval averages.

| Interval | Samples | System-load average | Battery-power average |
|---|---:|---:|---:|
| 11:10:57 to 11:11:57 | 59 | −29.85454 W | +29.85454 W |
| 11:11:57 to 11:12:57 | 64 | −29.80298 W | +29.80298 W |

The benchmark uses the system-load accumulator. This diagnostic reproduces the negative readings under embedding load and covers no idle or reranking windows. The Apple M4 benchmark entry contains throughput only. [Apple M4 workload measurement](../data/measurements/workloads_2026-11-21_noella_apple-m4.json)

**Fix (2026-11-21):** the sign convention of the system-load samples differs between machines (positive on the M1 / macOS 26.3.1, negative on the M4 / macOS 26.6.2), while the magnitude is the power drawn in both. [`workloads/power.py`](../workloads/power.py) now reads the accumulator change as a signed 64-bit difference and uses its magnitude. Checked against the raw values above: it gives 29.85454 W and 29.80298 W, and the M1 readings are unchanged. As a rough cross-check, 29.85 W ÷ 106.36 items/s ≈ 0.28 J per embedding, in line with the M1 (0.32) and M3 (0.29). This is not used in the average, because the throughput comes from a different run and the diagnostic has no idle baseline. The M4 entry stays throughput-only until it is re-measured with the fixed meter.
