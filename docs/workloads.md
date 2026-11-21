# Workloads: the real jobs, measured

Must-have 1 of the case ([case-brief.md](case-brief.md#must-haves-for-a-valid-submission-all-on-the-reference-house)): at least two job types with runtime, energy, interruptibility and deadline; at least one actually running and measured on our machine; scaled to the 1 kW reference server; jobs per day with a source.

**Both job types run for real on our laptop and were measured.** Code: [`workloads/`](../workloads/). Measurement: [`data/measurements/workloads_2026-11-21_jk_apple-m1.json`](../data/measurements/workloads_2026-11-21_jk_apple-m1.json). Teammates add their own machines with [measure-on-your-machine.md](measure-on-your-machine.md); [`scripts/combine_measurements.py`](../scripts/combine_measurements.py) averages them into `combined.json`, which the scheduler's catalog uses.

## Must-have 1 checklist

| Requirement | Embeddings (`embed`) | Reranking (`rerank`) |
|---|---|---|
| What one item is | One scientific abstract → 384-dim vector | One (query, abstract) pair → relevance score |
| Model | `sentence-transformers/all-MiniLM-L6-v2` @ `1110a24` (Apache-2.0) | `cross-encoder/ms-marco-MiniLM-L6-v2` @ `233902d` (Apache-2.0) |
| Runs on our machine | yes, measured | yes, measured |
| Throughput, measured | 50.96 items/s | 19.50 items/s |
| Energy per item, measured | 0.322 J gross · 0.205 J marginal | 0.654 J gross · 0.348 J marginal |
| Reference server (1 kW), gross basis | 11.2 M items per server-hour | 5.5 M items per server-hour |
| One job | 10 M abstracts = 0.90 server-hours | 5 M pairs = 0.91 server-hours |
| Interruptible | yes: pause instantly, or stop at a checkpoint and resume anywhere | same |
| Deadline | 48 h *(our assumption: batch re-indexing)* | 4 h *(our assumption: same-day evaluation run)* |
| Jobs per day | **open, see [below](#jobs-per-day-open)** | **open** |

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

**Machine:** Apple M1, 8 cores (4 performance), 8 GB, macOS 26.3.1, Python 3.11.14, torch 2.5.1 on CPU (4 threads, torch's default), batch size 32. Measured 2026-11-21 00:10 UTC, on battery.

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
| All heat used (0.3325 − 0.8 × 0.1330) | 0.226 CHF | 0.020 CHF | 0.041 CHF |
| All heat dumped (0.3325) | 0.333 CHF | 0.030 CHF | 0.060 CHF |

(Electricity 0.3325 CHF/kWh and heat value 0.1330 CHF/kWh from [data/README.md](../data/README.md#electricity-price-elcom-2026-iwb-basel-h4), gross basis, factor 1. Hardware cost is excluded, as in the case's formula.) Comparing these with what cloud providers charge for the same output is part of the economics workstream.

## Jobs per day (open)

The case requires the number of jobs arriving per day and its source, or a clear statement that the model assumes unlimited jobs. **This is not decided yet.** One reference server can do about 26 embedding jobs or 26 rerank jobs per day (24 h ÷ 0.9 h), so arrivals are best set relative to fleet capacity. Options:

1. **Unlimited backlog** (always work waiting). Allowed if stated. It makes utilisation purely a heat question, and missed deadlines only come from tight-deadline jobs.
2. **Fixed demand from a sourced trace**, e.g. job arrival rates and durations from the [Alibaba GPU cluster trace 2020](https://github.com/alibaba/clusterdata/tree/master/cluster-trace-gpu-v2020) (several GB, not downloaded) rescaled to our job sizes.
3. **Scenario sweep:** demand at 50%, 100% and 150% of the fleet's winter capacity. That shows where deadlines start to slip in summer, when servers are throttled.

## Limits of these numbers

- **One machine so far, one run of ~3 minutes per job** (more machines: [measure-on-your-machine.md](measure-on-your-machine.md)). The windows vary by up to ±5% for embeddings. One idle window spiked to 8.5 W (median idle 5.70 W): with the median baseline, marginal energy would be 2.6% (embed) and 4.0% (rerank) higher.
- **Thermal drift:** embedding power fell from 17.3 to 15.9 W over the run, likely thermal throttling on a fanless laptop. A long-running steady state may be slightly slower.
- **Whole-system meter:** display, editor and background tasks are inside both idle and load. The gross figure is therefore a little pessimistic, and the marginal figure assumes background load stayed steady.
- **CPU only**, small models (22 M parameters). Larger models (LLM batch inference, transcription) would have very different energy per item but the same heat per server-hour.
- **Reranking pairs are not real top-k retrieval** (see above). This affects relevance, not cost.
