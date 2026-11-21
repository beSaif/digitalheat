# Round 1, weak point 3: pause/resume demo, "same scheduler code", Saturday split

Investigator output, written Sat 21 Nov 2026 (night). Specification and assessment only: nothing here is the scheduler or the demo. Two exploratory scripts were written and run; both are standard library only.

Status labels: **sourced** = read on the URL given; **computed** = output of a script in `analysis/` on this machine (command given); **unverified** = not checked; **assumption** = our own choice.

Machine used for every *computed* number below: MacBook Pro Mac15,6, Apple M3 Pro (6P+6E), 18 GB, macOS 27.0.1, Python 3.13.12 (`system_profiler SPHardwareDataType`, `sw_vers`, `python3 --version`). Other team laptops were not checked (**unverified** that results carry over).

---

## 0. Findings in short

1. **Mechanism:** use `SIGSTOP`/`SIGCONT` on the job's own process group as the primary pause, with the job writing an atomic checkpoint after every batch in all modes. Fallback, behind one flag: cooperative stop at a batch boundary (`SIGTERM`) and restart from the checkpoint. Both were exercised here: stop takes about 3 ms, zero CPU seconds during 20 one-second stops, no batch repeated or lost; ten hard kills left the checkpoint readable every time (*computed*).
2. **The coldest January day has no pause at all** at 8 servers (13 Jan: 8 servers for 24 h), and **the plain "follow" rule makes the July server flap every hour** (9 pauses a day, each 1 h). Neither gives a watchable interrupted job as the plan stands. A 2 kWh tank hysteresis band with one server in summer gives 2 pauses of 4 h in July and leaves the yearly figures unchanged to four digits (*computed*, illustrative variant, not a decided policy).
3. **Energy without sudo:** `powermetrics` needs root and this account's sudo needs a password; CodeCarbon has no rootless Apple Silicon meter and estimates from CPU load; macmon is rootless but its README warns that macOS 27 (this machine) broke its CPU power source. A rootless whole-machine reading exists in `ioreg` (`PowerTelemetryData.SystemLoad`), but it refreshes only about once a minute, so it is usable for runs of 10 minutes or more, not for the live demo. Units are inferred, the field is undocumented.
4. **"Same code" needs one concrete test:** the live driver starts a day from the yearly run's state snapshot, and its 24 decisions must be byte-identical to the yearly run's rows for that date.
5. **The Saturday split puts the riskiest integration (live driver) after the 15:00 draft, has no freeze, no fallback recording, and leaves the video and the public repo to the last hours.** A corrected table with cut lines is in section 5.

---

## 1. Architecture: what "same scheduler code" means and how to make it auditable

Requirement (docs/case-brief.md, must-have 2): "The same scheduler code that produces the yearly balance must also control at least one real running job: it pauses and resumes it (or stops it at a checkpoint and restarts it) based on the heat signal."

### 1.1 Proposed definition (assumption, to be stated in the README)

> One module contains every decision. It has no clock, no file access, no subprocess call and no "simulation or live" flag. Two entry points import it. Neither entry point contains a threshold or a rule: they only read inputs, call the module, apply its actions and log them.

### 1.2 Interface (specification only, names are suggestions)

```
core.py        (pure, standard library only)
  Observation: hour index, heat demand this hour (kWh), tank state (kWh),
               forecast window (optional), job table (id, type, remaining work,
               deadline, status)
  Action:      RUN(job, server) | PAUSE(job) | RESUME(job, server) |
               MOVE(job) | DROP(job)          # heat is implied by servers running
  decide(obs, sched_state, params) -> (actions, sched_state)

house.py       (pure) tank and demand bookkeeping, used by both drivers
executor.py    interface with two implementations
  SimExecutor      applies actions to the modelled jobs
  ProcessExecutor  applies actions for ONE bound job to a real child process;
                   every other job stays modelled
run_year.py    driver 1: 8,760 steps -> balance + decision trace (JSONL)
run_live.py    driver 2: 24 steps of one date, N real seconds per step,
               starts from the state snapshot run_year.py saved for 00:00 of that date
```

There is no real house, so heat demand and the tank are modelled in both drivers. What is real in the live driver is the process and its progress.

Open design choice for the team (flagged, not decided here): whether the bound job's progress fed back into `decide` is the modelled one (decisions are then identical to the yearly run by construction, and the real process "shadows" a modelled job) or the real one read from the checkpoint file (closed loop; completion hour can shift by one step). Recommendation: modelled progress for the equality test, real progress displayed next to it, closed loop only as a stretch. A founder will ask "is the real job a puppet?"; the honest answer is that the heat side decides, and the real job obeys and reports its real progress.

### 1.3 How a jury can audit it (four checks, all cheap)

| # | Check | How it is shown |
|---|---|---|
| 1 | Both entry points import the same module | `grep -n "import" run_year.py run_live.py` in the README; `core.py` is the only place with rules |
| 2 | Same decisions | a test replays the January and the July demo day through `run_live.py` (dry executor, no sleeping) from the yearly snapshot and asserts the 24 trace lines equal the yearly trace lines for that date, byte for byte |
| 3 | Same decisions with a real process | the same test once more with the real child at about 0.2 s per step; it also asserts `ps -o state=` shows `T` after each PAUSE and not `T` after each RESUME |
| 4 | Same file | both drivers print the SHA-256 of `core.py` and the git commit in their output header; the demo screen shows it |

Check 2 is the one to have by 15:00. `pytest 9.1.1` is installed on this machine (`python3 -m pip list`), but a plain `python3 tests/test_same_decisions.py` with `assert` avoids the dependency for the jury.

---

## 2. Pause mechanism

### 2.1 What the standards and docs say (sourced)

- `SIGSTOP`: "Stop executing (cannot be caught or ignored)", default action "Stop the process". `SIGCONT`: "Continue executing, if stopped". Source: POSIX `<signal.h>`, https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/signal.h.html
- Python: `SIGKILL` "cannot be caught, blocked, or ignored"; "SIGKILL and SIGSTOP cannot be blocked"; "Python signal handlers are always executed in the main Python thread of the main interpreter". Source: https://docs.python.org/3/library/signal.html. Consequence for the cooperative fallback: the `SIGTERM` handler only sets a flag, and the stop happens when the main thread finishes the current batch.
- The case accepts both forms: "it pauses and resumes it (or stops it at a checkpoint and restarts it)" (docs/case-brief.md). DigitalHeat's slide 04 words it as "Pause and resume: save progress. Continue later without repeating completed work." and "Slow down: reduce processing speed or the number of active workers." (docs/case-presentation.md).

### 2.2 What was measured here (computed)

Script: `analysis/pause_resume_probe.py` (dummy job: SHA-256 batches, checkpoint written with temp file + `os.replace` after every batch, child started with `start_new_session=True`).

Command: `python3 analysis/pause_resume_probe.py signals checkpoint throttle`

```
python 3.13.12 on darwin, cpu_count 12

== signals: SIGSTOP / SIGCONT on a child process group ==
batch duration while running: 7.0 ms
stop latency  (signal -> ps state T): n=20 median=3.3 ms min=3.1 max=4.2
resume latency (SIGCONT -> next batch written): n=20 median=7.8 ms min=1.6 max=16.4
batches completed during 20 x 1.0 s stops: 0
CPU seconds consumed during 20 x 1.0 s stops: 0.00
batch sequence contiguous, nothing repeated or lost: True (435 batches)
exit code after SIGTERM: 0

== throttle: number of active workers ('slow down') ==
batches/s with 4 / 2 / 1 active workers: 519.0 / 281.3 / 144.3
ratio vs 4 workers: 1.00 / 0.54 / 0.28  (ideal 1.00 / 0.50 / 0.25)
```

Command: `python3 analysis/pause_resume_probe.py checkpoint` (final version of the script, batches of about 100 ms)

```
== checkpoint: cooperative stop at batch boundary + restart, ~100 ms batches ==
restart latency (spawn -> first new batch): n=10 median=134.6 ms min=129.9 max=136.6
stop latency   (SIGTERM -> process exited): n=10 median=138.8 ms min=10.6 max=148.6
batches finished but missing from checkpoint: 0
sequence contiguous across 10 restarts: True (57 batches)

== checkpoint: hard kill (SIGKILL mid-batch) + restart, ~100 ms batches ==
checkpoint unreadable after SIGKILL: 0 of 10
restarts that began at the surviving checkpoint: 9 of 9
finished batches computed twice: 0; work lost per kill = only the unfinished batch (<= one batch)
```

Note on an earlier run of the same experiment: the first version of the kill test compared the heartbeat log with the checkpoint and printed "contiguous False". That was a flaw in the probe (the checkpoint is written before the log line, so a kill between the two leaves a log gap without any lost work); the test was rewritten to compare restart points with checkpoints. Reported here so nobody trusts the first output.

Command: `python3 analysis/pause_resume_probe.py torch` (PyTorch job in a child, matrix products, cpu and Apple GPU "mps")

```
torch 2.14.0, mps available: True
  cpu: stopped 2 s, batches during stop 0, 3 batches after SIGCONT in 30 ms, alive True
  cpu: stopped 10 s, batches during stop 0, 3 batches after SIGCONT in 41 ms, alive True
  cpu: spawn -> 5th batch (import + first work) 0.54 s; survived: True
  mps: stopped 2 s, batches during stop 0, 3 batches after SIGCONT in 13 ms, alive True
  mps: stopped 10 s, batches during stop 0, 3 batches after SIGCONT in 16 ms, alive True
  mps: spawn -> 5th batch (import + first work) 0.89 s; survived: True
```

Import cost that a restart pays (computed, `time python3 -c "import torch"`: 0.57 s wall; `time python3 -c "import mlx.core, mlx_whisper"`: 0.92 s wall). Model loading time for a real embedding or transcription model was **not** measured (unverified); it is the main cost of the restart path.

Limits of these measurements: one machine; stops of at most 10 s (a pitch pause is 10 to 20 s, so this covers the demo, not a multi-hour stop); a toy matrix job, not the real J1; the stop latency includes one `ps` call.

### 2.3 Comparison

| | A. SIGSTOP / SIGCONT on the process group | B. Cooperative checkpoint and restart | C. Worker-count throttling |
|---|---|---|---|
| Needs the job to cooperate | no | yes (flag check per batch, resume logic) | yes (pool of workers) |
| Stop latency here | 3 ms (computed) | up to one batch plus exit, 139 ms median with 100 ms batches (computed) | same as A per worker |
| Resume latency here | under 20 ms (computed) | process start + imports + model load: 0.13 s for the dummy, 0.5 to 0.9 s for torch/mlx imports alone (computed), model load unverified | same as A |
| Work lost | none (computed) | none on clean stop; at most the batch in progress on a hard kill (computed) | none |
| Survives a crash of the scheduler | no: the child stays stopped until someone sends SIGCONT | yes: nothing is left running | partly |
| Memory while paused | held (process stays resident) | released | held |
| Matches "save progress, continue later" (slide 04) | only if the job also checkpoints | yes | no |
| Matches "move to another site" | no | yes (checkpoint file is the thing that moves) | no |
| Maps onto the case model (whole 1 kW servers on or off) | yes | yes | poorly: the model counts whole servers |
| Live-demo risk | low: no dependence on model loading or network | medium: restart can hit a model download check, a slow load or an import error in front of the jury | medium: more moving parts, nothing extra to see |
| What the audience sees | counter freezes at once, continues at once | counter stops, "restarting", counter continues from the saved number | counter slows |

Failure modes to plan for:

| Failure mode | Applies to | Status | Mitigation |
|---|---|---|---|
| Scheduler dies while child is stopped; orphan stays stopped and holds memory | A, C | reasoning from POSIX semantics (sourced above) | `try/finally` in the executor sends SIGCONT then SIGTERM to the group; README lists `pkill -CONT -f <worker>` as cleanup |
| Stop reaches the shell's job control and the terminal prints "suspended" | A | reasoning; avoided in the probe by `start_new_session=True` | always start the job in its own session and signal the group (`os.killpg`) so child workers stop too |
| GPU / MPS context breaks after a stop | A | survived 2 s and 10 s stops here (computed); longer stops and real models unverified | rehearse with the real J1; if it fails use `--device cpu` or mechanism B |
| Paused process keeps its RAM | A | by definition | irrelevant on an 18 GB laptop for one job; say in the limits that a real fleet would checkpoint and power down for long stops |
| Laptop sleeps or display sleeps mid-demo | all | `caffeinate` creates assertions that prevent sleep; `-d` display, `-i` idle sleep, `-s` system sleep "valid only when system is running on AC power" (sourced: `man caffeinate` on this machine) | run the live driver as `caffeinate -dis python3 run_live.py ...`, on AC power |
| App Nap throttles a background process | all | Apple lists the conditions (not foreground, no recently updated visible window, not audible, no IOKit or NSProcessInfo assertion, not using OpenGL) and the effects (priority reduction, timer throttling, I/O throttling); the page does not mention command-line processes (sourced: https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/AppNap.html). Whether it ever affects a terminal child is unverified | keep the terminal with the demo in the foreground; derive the simulated hour from the step counter, never from wall time |
| Model library checks the network at load and hangs with wifi down | B, and A at first start | "even if the latest version of a file is cached, calling hf_hub_download still triggers a HTTP request"; `HF_HUB_OFFLINE`: "no HTTP calls will be made" (sourced: https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables) | export `HF_HUB_OFFLINE=1` in the demo command; rehearse once with wifi off |
| Half-written checkpoint | B | 0 of 10 unreadable after SIGKILL with temp file + `os.replace` (computed) | keep that write pattern |
| A stopped process on a powered server still draws idle power | A | not measurable here (telemetry too slow, section 3); the case model counts a non-running server as 0 kW | state as a limit: the case has no idle power; a pilot would checkpoint and power down |

### 2.4 Recommendation

- **Primary: A, SIGSTOP/SIGCONT** on the job's process group, with the job writing an atomic checkpoint after every batch regardless of mode. The checkpoint is what makes "saved progress, nothing repeated" true and checkable, and it costs one small file write per batch.
- **Fallback: B, cooperative stop and restart**, selected by one flag on the live driver (`--pause-mode checkpoint`). `core.py` emits the same PAUSE and RESUME actions in both modes; only the executor differs. One optional scene uses B on purpose: kill the job, restart it from the checkpoint, call it "moved to another site".
- **C (throttling): do not build for the demo.** It is first on the cut list. Mention it as slide 04's third lever in the outlook.

---

## 3. Measuring runtime and energy of the real job without sudo, and scaling to 1 kW

Requirement (must-have 1): "At least one job type must actually run on your machine, with measured runtime. Take its energy from a software meter or from runtime x the device's power draw, and state how you scale it to the 1 kW reference server."

### 3.1 Tools checked

| Tool | Installed here | Needs root | Status and source |
|---|---|---|---|
| `powermetrics` | yes (`/usr/bin/powermetrics`) | yes | computed: `powermetrics -n 1` prints "powermetrics must be invoked as the superuser"; `sudo -n true` prints "sudo: a password is required". Usable only if a team member types the password; do not put the password in a script |
| CodeCarbon | no | no, but then it is an estimate | sourced, https://docs.codecarbon.io/latest/explanation/methodology/ : powermetrics on Apple Silicon "requires sudo"; "There is no known way to read Apple Silicon energy without administrative rights."; in a normal install the `cpu_load` mode is chosen first because psutil is a hard dependency; constant mode "applies a flat half of TDP"; energy is power sampled every 15 s by default, times the interval. So on these laptops CodeCarbon is a load-scaled TDP estimate, not a meter |
| macmon | no | no | sourced, https://raw.githubusercontent.com/vladkens/macmon/main/readme.md : "macmon is a sudoless performance monitor for Apple Silicon Macs"; JSON via `macmon pipe` with `cpu_power`, `gpu_power`, `sys_power` in watts; install `brew install macmon`. But: "macOS 27 broke the CPU/ANE power source that macmon previously used without root", "Running macmon with sudo does not grant the same access", with a workaround through the AppleCLPC driver that "depends on undocumented mappings". This machine runs macOS 27.0.1, so macmon here is unverified and risky |
| asitop | no | yes | sourced (same macmon README, list of alternatives): "Written in Python, requires sudo." |
| socpowerbud, NeoAsitop | no | no | sourced (same README): both listed as "sudoless"; not tried |
| `ioreg` battery telemetry | yes (`/usr/sbin/ioreg`) | no | computed, see 3.2 |
| A published device power figure | n/a | n/a | not found. Apple's tech-spec page for this model gives only "72.4-watt-hour lithium-polymer battery" and a "70W" or "96W USB-C Power Adapter" (sourced: https://support.apple.com/117736); the Apple power-consumption page opened (https://support.apple.com/en-us/102839) covers Mac Pro only. Third-party figures disagree and are CPU-only: "maximum power used by all 12 cores in an M3 Pro remains less than 7 W" (https://eclecticlight.co/2024/02/23/apple-silicon-2-power-and-thermal-glory/) against "the M3 Pro with around 23 watts" in Cinebench via powermetrics (https://www.macworld.com/article/2211441/14-inch-m3-pro-macbook-pro-review.html). Neither is a whole-laptop figure |

### 3.2 Rootless reading that works here: `ioreg` `PowerTelemetryData`

`ioreg -rw0 -c AppleSmartBattery` returns, without sudo, a `PowerTelemetryData` dictionary with `SystemLoad`, `AccumulatedSystemLoad` and `SystemLoadAccumulatorCount`. The field is **undocumented**; reading it as milliwatts of whole-machine load is **inferred, not sourced**.

Command: `python3 analysis/pause_resume_probe.py powertrace` (12 SHA-256 workers on 12 cores, external power connected)

```
== powertrace: how often does the ioreg telemetry update, and do the accumulators give a mean? ==
idle                        75 s: counter +114, updates seen 2, median gap 60 s | accumulator mean   7.89 W | SystemLoad values seen (W): [5.2, 5.6, 22.4] | SystemPowerIn last 17.2 W | external Yes
12 workers running         100 s: counter +57, updates seen 1, median gap nan s | accumulator mean  20.82 W | SystemLoad values seen (W): [5.2, 22.8] | SystemPowerIn last 17.2 W | external Yes
12 workers SIGSTOPped       75 s: counter +57, updates seen 1, median gap nan s | accumulator mean  18.96 W | SystemLoad values seen (W): [5.2, 22.8] | SystemPowerIn last 17.2 W | external Yes
accumulator means: load - idle = 12.9 W, stopped - idle = +11.1 W
(each phase mean still contains up to one update interval of the previous phase)
```

Command: `python3 analysis/pause_resume_probe.py power` (same idea, shorter phases; the adapter was plugged in part-way through this run, so the battery V x I column is not usable)

```
idle (probe only)                  SystemLoad mean   2.52 W (min 2.52, max 2.52, 1 distinct of 12 samples)
12 workers running                 SystemLoad mean  16.05 W (min 2.52, max 22.38, 3 distinct of 15 samples)
12 workers SIGSTOPped              SystemLoad mean  22.38 W (min 22.38, max 22.38, 1 distinct of 12 samples)
```

What this does and does not show:

- The value refreshes about once every 60 s (one refresh adds 57 to the sample counter). Phases of 75 to 100 s are therefore dominated by the previous phase. **The "stopped" rows are not evidence that a stopped job draws power**; they are stale readings. The evidence that a stopped job burns nothing is the 0.00 CPU seconds in section 2.2.
- Readings seen: 2.5 to 5.6 "W" idle, 22.4 to 22.8 "W" with all 12 cores busy. Plausible for this laptop, and below the 70 W / 96 W adapter rating (sourced above), but there is no independent meter to confirm the unit. **Unverified.**
- A cross-check against battery voltage x current is possible only on battery power; it was not obtained cleanly (adapter state changed during the run).

### 3.3 Recommended measurement protocol for J1 (role B)

1. On AC power, display on at fixed brightness, other apps closed. Record model, chip, macOS version.
2. Idle reference: wait for one telemetry refresh, read `AccumulatedSystemLoad` and `SystemLoadAccumulatorCount`, wait 5 minutes, read again. Mean = difference of the first divided by difference of the second.
3. Job run: start J1 sized to run **at least 10 minutes** (a one-minute refresh then blurs each edge by at most about 10%), read the same two counters at start and end, and take wall-clock runtime from `time.perf_counter()` inside the job.
4. Energy per job = mean power during the run x runtime. Report it twice: gross (whole machine, conservative) and net (run minus idle). Repeat three times and give the range.
5. Label it in the assumptions list as: "software reading from an undocumented macOS battery-telemetry field, unit inferred, refresh about 60 s; cross-checked against X". Preferred cross-check, if any team member is willing to type their password once: `sudo powermetrics --samplers cpu_power -i 1000` during the same run. Second choice: a plug-in wall meter from the organisers or a mentor (unverified that one is available).
6. Fallback that always satisfies the case wording ("runtime x the device's power draw"): runtime x the adapter rating (70 W or 96 W, sourced) as a stated **upper bound**. It overstates energy several times over and must be labelled as a bound.

Linux laptops (unverified, no Linux machine checked): CodeCarbon's page says RAPL files "on many distributions ... are root-only by default" (https://docs.codecarbon.io/latest/explanation/methodology/), so plan for the runtime x rated power bound there.

### 3.4 Scaling to the 1 kW reference server (assumption, to be written into the assumptions list)

Proposed rule, "same energy per job":

```
E_job  [Wh]            = P_laptop_mean [W] x runtime_laptop [h]        (measured)
server-hours per job   = E_job / 1000 Wh
jobs per server-hour   = 1000 Wh / E_job
```

In words: the reference server is assumed to need the same energy per job as the laptop and to draw 1 kW, so it does 1000 / P_laptop times the laptop's throughput. With the unverified 22.6 W reading above that would be a factor of about 44 (arithmetic example only, not a result).

Where this stops holding (say so in the pitch): a GPU server is likely to need less energy per embedding or per audio minute than a laptop CPU, a CPU-only rack server possibly more. The honest check is one MLPerf Inference result with a power measurement for a comparable task (case resource https://mlcommons.org/benchmarks/inference-datacenter/; not opened in this investigation, so no number is quoted), reported as a sensitivity: "if the server is k times more efficient than our laptop, jobs per server-hour rise k-fold and the break-even price per job falls k-fold; the break-even per server-hour does not change".

---

## 4. Demo script

### 4.1 Which days, and why the current plan does not yet produce an "interrupted job"

Script: `analysis/demo_day_timing.py` (imports `load` and the constants from `analysis/baseline_sweep.py`, replays the `follow` rule hour by hour; "slot j" runs when at least j servers run).

Command: `python3 analysis/demo_day_timing.py` (excerpt; full output is reproducible)

```
January 2025: highest-demand day 2025-01-13 (221.5 kWh), lowest-demand day 2025-01-25 (119.6 kWh)
July 2025: demand per day min 12.0 / max 12.0 kWh (all 31 days identical: True)

== N=8, follow (band 0), as in baseline_sweep.py ==
  year: coverage 92.9%, utilisation 51.8%, server-hours 36281, break-even 0.2261 CHF/server-h
  2025-01-13: demand  221.5 kWh, server-hours 192, unmet (backup)  67.9 kWh, servers per hour: 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8 8
      slot 8: ########################  pauses 0, resumes 0, paused stretches 0-0 h
  2025-01-25: demand  119.6 kWh, server-hours 169, unmet (backup)   0.0 kWh, servers per hour: 8 8 8 8 8 8 8 8 8 8 8 8 8 8 5 3 4 4 6 7 7 7 7 7
      slot 5: ###############...######  pauses 1, resumes 1, paused stretches 3-3 h
      slot 8: ##############..........  pauses 1, resumes 0, paused stretches 10-10 h
  2025-07-15: demand   12.0 kWh, server-hours  15, unmet (backup)   0.0 kWh, servers per hour: 1 1 0 1 1 0 1 0 1 1 0 1 1 0 1 0 1 1 0 1 1 0 1 0
      slot 1: ##.##.#.##.##.#.##.##.#.  pauses 9, resumes 8, paused stretches 1-1 h

== N=8, band 2 kWh + max 1 server when no space heating ==
  year: coverage 92.9%, utilisation 51.8%, server-hours 36281, break-even 0.2261 CHF/server-h
  2025-07-15: demand   12.0 kWh, server-hours  16, unmet (backup)   0.0 kWh, servers per hour: 1 1 1 1 1 0 0 0 0 1 1 1 1 1 1 0 0 0 0 1 1 1 1 1
      slot 1: #####....######....#####  pauses 2, resumes 2, paused stretches 4-4 h
  July: days on which slot 1 is both paused and resumed: 31 of 31; pauses per day min 2 / max 3

== time compression: real seconds per simulated hour ==
s per sim-h  one day  Jan+Jul  1 h pause  4 h pause  8 h pause
        1.0      24s      48s       1.0s       4.0s       8.0s
        1.5      36s      72s       1.5s       6.0s      12.0s
        2.0      48s      96s       2.0s       8.0s      16.0s
        2.5      60s     120s       2.5s      10.0s      20.0s
        3.0      72s     144s       3.0s      12.0s      24.0s
        5.0     120s     240s       5.0s      20.0s      40.0s
```

(Excerpt: the 13 Jan and 25 Jan lines of the second variant are identical to the first and are left out; the band 2 kWh, band 4 kWh and band 4 kWh + cap variants are in the full output.)

Consequences (all computed, stand-in profile, case assumptions, N = 8):

- 13 Jan (highest demand in January): all 8 servers run 24 of 24 hours, 67.9 kWh of 221.5 kWh come from backup. **Zero pauses.** Good for "winter: everything runs and it still is not enough", useless for an interrupted job.
- 25 Jan (lowest demand in January): the eighth server is paused at 14:00 and not resumed that day; the fifth is paused 3 h and resumed.
- July under the plain rule: the single running server alternates on and off, 9 one-hour pauses per day. On screen that is a flicker, and for hardware it is hourly cycling a founder will question.
- A tank band of 2 kWh with at most one server when there is no space heating gives two 4-hour pauses and two resumes on 15 July, with yearly coverage, utilisation, server-hours and break-even unchanged at the printed precision. **This variant is illustrative.** If the team wants this pattern in the demo, the band must be a parameter of `core.py` and be used in the yearly balance too; otherwise the demo would not be the same code with the same settings.

### 4.2 Time compression (assumption)

- January day at 1.5 real seconds per simulated hour: 36 s.
- July day at 2.5 real seconds per simulated hour: 60 s; a 4-hour pause lasts 10 s, long enough to point at.
- J1 batches must be much shorter than one simulated hour so the counter visibly moves: aim for 0.1 to 0.25 s per batch (10 to 25 ticks per July hour). Batch size is a J1 parameter for role B to tune; unverified until J1 exists.
- The compression factor is a flag of the live driver only. `core.py` sees hour indices, so the factor cannot change a decision.

### 4.3 Pitch timeline, 5:00 total

Screen layout for the live part (one terminal window or one local HTML page, no network): left, the house (hour, outdoor temperature, demand, tank level, servers running, backup); right, the real job (PID, state from `ps`, batches done from the checkpoint file, a moving counter); footer, SHA-256 of `core.py` and "decisions identical to yearly run: yes/no".

| Clock | Who | What happens | What the audience sees |
|---|---|---|---|
| 0:00 | D | Key figures for the reference house, the six the brief asks for | one slide with six numbers |
| 0:40 | C | starts `caffeinate -dis python3 run_live.py ...` on the second screen half; job loads | nothing yet |
| 0:50 | D | "now the same scheduler, live" | switch to demo screen |
| 1:00 | C | January day starts, 13 Jan, 1.5 s per hour | 8 of 8 servers on in every hour, tank empty, backup bar filling, job counter running without a break |
| 1:36 | C | January ends; 6 s title card "15 July, hot water only" (auto) | day summary line: demand, server heat, backup |
| 1:42 | C | July day starts, 2.5 s per hour | one server on, tank near full |
| 1:54.5 | – | simulated 05:00: tank full, PAUSE | job state flips to stopped (`T`), counter frozen, "paused by heat signal: tank full" |
| 2:04.5 | – | simulated 09:00: RESUME | counter continues from the same number |
| 2:19.5 | – | simulated 15:00: PAUSE | as above; D says "nothing is dumped, nothing is recomputed" |
| 2:29.5 | – | simulated 19:00: RESUME | |
| 2:42 | C | July ends | summary: batches done, batches repeated 0, decisions identical to yearly run |
| 2:45 | C | optional scene (first thing to cut): kill the job, restart from checkpoint, "moved to another site" | PID changes, counter continues from the saved number |
| 3:10 | D | limits and "when it does not pay off" | one slide |
| 4:15 | D | what DigitalHeat can decide with this, ask | closing slide |
| 5:00 | | stop | |

The pause and resume times in the table are those of the illustrative band variant in 4.1. With whatever policy the team adopts, regenerate them with the yearly trace before rehearsing; they are **not** fixed facts.

Live part: 1:00 to 3:10 = 130 s, of which 96 s is simulated days.

### 4.4 If something fails

| Failure | Response |
|---|---|
| Wifi down | nothing in the demo may need the network: weather is the committed CSV, the model is cached and `HF_HUB_OFFLINE=1` is set, the page uses no CDN. Rehearse once with wifi switched off |
| Projector or adapter problem | demo runs on the laptop; pass the laptop along the jury table; carry an HDMI and a USB-C adapter |
| Job fails to start | driver falls back to `--pause-mode checkpoint` with the dummy CPU job, announced as such |
| Live demo dead | play the pre-recorded run (below) and say it is a recording |
| Laptop asleep or on battery | `caffeinate -dis`, AC power, lid open; checked in the Sunday 07:00 list |

### 4.5 Pre-recorded fallback (also the core of the required video)

- Record Saturday evening, right after the first clean rehearsal: the full 130 s live part, unedited, with a visible wall clock or the terminal's timestamp, plus a second terminal running `ps -o pid,state,time -p <pid>` once a second so the stop is visible independently of our own display.
- Tools present here: `/opt/homebrew/bin/ffmpeg` and `/usr/sbin/screencapture` (computed: `which`). macOS screen recording with Cmd+Shift+5 needs no install.
- Keep the file on two laptops and one USB stick. The submission form asks for a video URL that "must open without a login" (docs/submission.md): test the link in a private browser window. Upload and processing time of the chosen host is unverified; do a test upload on Saturday afternoon.

---

## 5. Review of the Saturday / Sunday split

### 5.1 Problems in the table in docs/overnight.md

| # | Problem | Why it matters |
|---|---|---|
| 1 | The live driver (must-have 2, the part that makes the submission valid) starts at 15:30, after the draft | "a spreadsheet, slides or a simulation alone are not a valid submission" (case brief). The riskiest integration should be the first thing proven, not the last |
| 2 | Checkpointing in J1 is also after 15:00, and J1 is measured before it is interruptible | measuring twice; and the scheduler has nothing real to control until evening |
| 3 | No point where A's core and C's driver are joined before 15:30 | interface mismatches surface late |
| 4 | Dashboard skeleton "on baseline numbers" at 10:00 | Design is 10% of the score; Transparency and Feasibility are 50%. Dashboard work before the numbers exist is the wrong order |
| 5 | Video and pitch script only from 20:00, one person | the video is a required field (docs/submission.md); recording, re-takes, upload and link test need a working demo and about two hours |
| 6 | "repo public" on Sunday 07:00 | the repository URL is a required field and the jury must be able to open it; a first-time public push at the last hour risks leaking something or failing. Note: docs/event.md and docs/submission.md hold names and the repo name; the team should decide what goes public (not changed here) |
| 7 | No feature freeze, no buffer, no fallback recording | any bug found at 23:00 has no slot |
| 8 | Dinner blocks all four for two hours; rehearsal is one person | dinner is served 18:00 to 20:00 (docs/event.md), it does not need two hours; the rehearsal needs presenter and operator together |
| 9 | The same-code test, the assumptions list in the README and the clean-clone check have no owner or slot | these are what the 25% Transparency criterion is scored on |
| 10 | Sunday entrance | "Main entrance ... all of Sunday, it's locked. Use the door phone" (docs/event.md); arriving at 08:15 for an 08:30 deadline is a risk |
| 11 | Mentor windows unused | docs/event.md lists a pitching mentor on site Sat 16:00 to 20:00 and another Sat 11:00 to 16:00; no slot books them |

### 5.2 Minimum viable version of each must-have that must exist by 15:00

| Must-have | Minimum by 15:00 | Not needed by 15:00 |
|---|---|---|
| 1 Workloads | J1 runs on one laptop as a batch loop with a per-batch checkpoint; runtime measured; energy = one 10-minute run with the method in 3.3 (or the adapter-rating bound, labelled); scaling rule of 3.4 written down. J2 as a table row with a source URL for each number. Jobs per day stated, even if it is "assumed, unlimited backlog" said in those words | second measured job, repeat runs, benchmark cross-check |
| 2 Scheduling | `core.py` used by `run_year.py` and `run_live.py`; the live driver pauses and resumes the real J1 on the July day with SIGSTOP/SIGCONT; the same-decisions test (check 2 in 1.3) passes | checkpoint-restart mode, kill-and-move scene, forecast use, throttling, any web UI |
| 3 Balance | one command prints all seven figures for the reference house from the yearly run, including missed deadlines and computing income from the first job model, plus the "does not pay off when" sentence, even if crude | realism switches beyond the two in the baseline, charts |
| Submission | repo openable by the jury, README with setup steps that worked on a second laptop, assumptions list, AI-tool note, a 60 to 90 s unedited screen recording of the July pause uploaded and its link tested | polished video, slides |

Whether "Save draft" on the platform enforces the required fields (repository URL, video URL) is **unverified**; planning for both to exist at 14:45 removes the question.

### 5.3 Corrected table

Roles: A = scheduler core and yearly run; B = workloads and measurement; C = live driver, demo screen, recordings; D = numbers, assumptions, README, pitch and video script.

| Time | A | B | C | D |
|---|---|---|---|---|
| Sat 09:00–09:30 | All four: read the summary in docs/overnight.md, decide idea, servers per house, pause mechanism; write the `decide` signature and the trace line format on one page | | | |
| 09:30–11:00 | `core.py` + `run_year.py` reproducing the baseline (92.9% coverage at 8 servers) as a regression check | J1 as a batch loop with atomic per-batch checkpoint and `--resume`; first runtime number | `run_live.py` against a stub `decide` (alternating run/pause): starts a child in its own session, SIGSTOP/SIGCONT, reads the checkpoint | README skeleton (setup, AI-tool note), assumptions list started from data/README.md and assumption-limits.md; check what must not go public |
| **11:00–11:20** | **Integration 1, all four:** C's driver imports A's core and pauses B's J1 on the July day. This is the walking skeleton | | | |
| 11:20–12:15 | job queue, deadlines, two job types in `core.py` | start the 10-minute energy run; J2 numbers with source URLs | decision trace + same-decisions test | key-figure printer on the yearly output; computing-price research |
| 12:15–12:45 | Lunch (served 12:00–13:00) | | | |
| 12:45–14:15 | seven key figures from one command; "does not pay off when" rule | job arrival number and its source; scaling to 1 kW written up | January and July day in the terminal view; 60–90 s raw recording of the July pause | upload the raw recording, test the link logged out; draft the four-part description |
| **14:15–14:45** | **Freeze for the draft, all four:** fresh clone on a second laptop, follow the README, run the three commands. Fix only what blocks | | | |
| **14:45–15:30** | **Draft submission** saved at 14:45, checked, submitted in the 15:00–15:30 window | | | |
| 15:30–18:00 | realism switches (tank loss, hot-water booster) and the two-column key figures; sensitivity of break-even | repeat measurement (3 runs), measurement notes in the repo; benchmark cross-check for the scaling | one-command demo (`run_live.py` for both days), checkpoint-restart mode behind the flag, wifi-off rehearsal | pitch script to the second (section 4.3); 20 minutes with the pitching mentor (on site 16:00–20:00 per docs/event.md) |
| 18:00–18:40 | Dinner, all four | | | |
| 18:40–21:00 | with C: three timed end-to-end rehearsals; fix only demo-blocking bugs | README check on a clean laptop; list of all assumptions complete, each with status | with A: rehearsals; demo screen readable from the back of a room | slides (four at most), Q&A answers, thumbnail screenshot |
| **21:00** | **Feature freeze.** After this only bug fixes, text and recordings | | | |
| 21:00–23:00 | on call for bugs; write "what is real, what is mocked" | reproducibility pass: every number in the pitch traced to a command or URL | record the fallback run (section 4.5) and the screen part of the video | voice-over and video assembly with C |
| 23:00–24:00 | All four: upload video, test link logged out, fill the final form completely and save it. Then sleep | | | |
| Sun 07:00–08:00 | on site by 07:00 (entrance is locked on Sunday, door phone): fresh clone on the pitch laptop, AC power, wifi-off run, two rehearsals | | | |
| **Sun 08:00** | **Final submission** (30 minutes before the 08:30 deadline) | | | |
| 08:30–09:00 | breakfast; fallback video open in a paused player | | | |

### 5.4 Cut lines: what to drop first when late

Drop in this order, top first:

1. Solar bonus challenge (the brief says to start it only once the three must-haves work).
2. Worker-count throttling ("slow down").
3. Kill-and-restart "moved to another site" scene; multi-site logic stays a sentence in the pitch.
4. Web dashboard: a terminal view plus one static chart is enough for a 10% criterion.
5. Running J2 for real: it stays a benchmark-derived job type with sources.
6. Forecast-based decisions (with a lossless tank the baseline notes greedy filling is already optimal for heat).
7. Peaked hot-water profile comparison.
8. Closed-loop use of the real job's progress in `decide`.
9. Third and second repeat of the energy measurement.

Never cut: one real process paused and resumed by `core.py`; the same-decisions test; the seven key figures from one command; the assumptions list; README setup steps tested on a second laptop; the video link that opens without a login.

Trigger rule (assumption): if Integration 1 has not worked by 12:15, C and A pair on it and C's view work moves after the draft. If the same-decisions test is red at 14:15, the draft says so in "what is real and what is mocked".

---

## 6. What is still unverified

- That the real J1 (embedding or transcription model, possibly on the Apple GPU) survives SIGSTOP for the 10 to 20 s the demo needs; only a toy PyTorch job was tried, for up to 10 s.
- Model load time on restart (the cost of mechanism B) and J1 batch duration.
- The unit and accuracy of `PowerTelemetryData.SystemLoad`; no independent meter was available. Whether the field exists on the other three laptops.
- macmon on macOS 27; not installed, README warns about it.
- Whether App Nap can affect a terminal child process.
- Whether the platform's "Save draft" enforces required fields; upload and processing time of the video host.
- Linux laptops: nothing was checked.
- The band and summer-cap variant in 4.1 is a suggestion from a 60-line replay, not a reviewed policy; its effect on job deadlines is unknown because no job model exists yet.
- No number here uses a currency except the break-even 0.2261 CHF per server-hour reprinted from `analysis/baseline_sweep.py` logic (CHF, no conversion).

## 7. Files and commands

| File | Purpose | Command |
|---|---|---|
| `analysis/pause_resume_probe.py` | mechanism probe (signals, checkpoint, throttle, power, powertrace, torch) | `python3 analysis/pause_resume_probe.py all` (several minutes; `powertrace` alone samples for 250 s) |
| `analysis/demo_day_timing.py` | demo days, pause pattern per server slot, time compression | `python3 analysis/demo_day_timing.py` |

Firecrawl calls used: 0 of 3. All web sources were read with the free fetch tool; the URLs are given where each quote appears.
