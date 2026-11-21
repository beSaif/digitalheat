# Round 1 critique: pause/resume demo, "same scheduler code", Saturday split

Critic's review of `docs/research/r1-demo-and-timeline.md`, `analysis/pause_resume_probe.py` and `analysis/demo_day_timing.py`, written 2026-11-21 (night). 0 paid Firecrawl calls. No file other than this one was written; git state untouched.

Status labels: **sourced** = read on the URL given; **computed** = re-run here (command given); **unverified** = not checked; **assumption** = a choice.

## 1. What holds

- All three probe commands were re-run on the same machine and reproduce within run-to-run noise (stop latency median 3.3 ms, 0 batches and 0.00 CPU s during stops, checkpoint readable 10 of 10 after SIGKILL, toy torch job on cpu and mps survives 2 s and 10 s stops). `python3 analysis/demo_day_timing.py` reproduces line for line.
- Every sourced quote (POSIX signal.h, Python signal docs, CodeCarbon methodology, macmon README, Apple tech specs 117736, Mac Pro page 102839, eclecticlight, Macworld, App Nap, Hugging Face environment variables, `man caffeinate`) was re-opened and is on the page as quoted.
- The demo timeline arithmetic (pause at 1:54.5, 2:04.5, 2:19.5, 2:29.5; 130 s live part) follows from the 15 July pattern of the band variant.
- The diagnosis of the Saturday table (live driver after the draft, no freeze, no recording) is correct against `docs/overnight.md`.

## 2. What breaks or needs a caveat

**2.1 "No published whole-laptop power figure" is wrong for idle (sourced here).**
Apple's Product Environmental Report for this model has a power table: 14-inch MacBook Pro with M3 Pro, "Idle—Display On" 4.03 W (100 V), 4.07 W (115 V), 4.19 W (230 V); Sleep 0.26 / 0.26 / 0.30 W; Off 0.13 / 0.13 / 0.16 W; tested with a fully charged battery on the 70 W adapter, at the wall. Source: https://www.apple.com/environment/pdf/products/notebooks/14-inch_MacBook_Pro_PER_Oct2023.pdf (read with `pdftotext`; the free fetch tool refused the 32 MB file). No published figure under load was found, so the gap remains for the number that matters, but the idle reference exists and should be used as a cross-check.

**2.2 The ioreg field is a difference of two other fields (computed here).**
Five samples over 215 s: `SystemLoad` = `SystemPowerIn` − `BatteryPower` exactly (17181 − 14337 = 2844; 17183 − 14103 = 3080; 17174 − 15234 = 1940; 17179 − 14461 = 2718; 17176 − 15336 = 1840). `BatteryPower` equals battery voltage × current (11.711 V × 1.284 A = 15.04 W against 15036). So the milliwatt reading is internally consistent, and the idle value (1.8 to 3.1 W here, 2.5 to 5.6 W in the investigator's run) sits near Apple's 4.19 W wall figure. This supports the unit; it is still not an independent meter.
Consequences nobody wrote down:
- While the battery charges (15 W here), the job's power is a small difference of two large numbers. Measure with a full battery.
- This laptop was fed 17.2 W (19.8 V × 0.87 A) in every sample, in the investigator's run too. The investigator's 22.4 to 22.8 W load reading is above that, so under full load the battery was discharging. "On AC power" was true only in name. Check which charger is used before the measurement and before the pitch.
- Idle was read with the display probably dim or off (night run). Net-of-idle energy depends on that.

**2.3 Refresh interval is not a clean 60 s (computed here).**
Gaps between refreshes in my 215 s sample: 24.1 s, 59.7 s, 60.6 s, 23.0 s; the sample counter rises about one per second (33, 57, 57, 22). The investigator's "median gap 60 s" came from a single gap. "About once a minute, sometimes sooner" is safe; the 10-minute run advice stands.

**2.4 The "stopped rows are stale" statement is an inference, not a measurement.**
It is the likely explanation, but power in the stopped state was never measured. What a SIGSTOPped job costs in watts is unverified.

**2.5 SIGSTOP stops the work, not the heat.**
The yearly balance counts a paused server as 0 kW. A stopped process on a powered server still draws idle power, and for a rack server that is a large share of 1 kW (the sibling critique confirmed a sourced example: 147 W idle against 835 W at full load for one server model). The form of pause that matches the heat model is "stop at a checkpoint and restart", which the investigator makes the fallback and puts the visible restart scene third on the cut list. A founder will see this at once. The restart path should be exercised in a test and shown at least in the recording, and the pitch should say that the laptop demo freezes the process while a real unit would checkpoint and power down.

**2.6 The same-decisions test proves less than it sounds.**
With modelled progress fed back into `decide`, both drivers call one pure function with the same inputs, so identical traces are true by construction. The test catches a driver that feeds different inputs; it does not show that the real job matters to the scheduler. The honest claim is "same decisions, real process obeys". The test in check 3 (process state `T` after each PAUSE) is the one that proves control and should be part of the 15:00 minimum, not check 2 alone. Whether the real job's progress, completion and deadline ever reach the balance is undecided.

**2.7 The band variant: figures hold, the choice of 2 kWh does not (computed here).**
Re-run with the investigator's `hourly()` and a cap of one server when there is no space heating:

| N | band kWh | coverage | server-hours | server starts per year | pauses in July | longest July pause |
|---|---|---|---|---|---|---|
| 8 | 0 | 92.937% | 36,281 | 2,200 | 279 | 1 h |
| 8 | 2 | 92.937% | 36,281 | 1,146 | 69 | 4 h |
| 8 | 4 | 92.937% | 36,281 | 977 | 35 | 8 h |
| 8 | 16 | 92.937% | 36,281 | 820 | 9 | 24 h |
| 6 | 0 | 79.581% | 31,067 | 1,728 | 279 | 1 h |
| 6 | 2 | 79.563% | 31,060 | 659 | 69 | 4 h |
| 6 | 16 | 79.512% | 31,040 | 297 | 9 | 24 h |

(Command: inline `python3` importing `hourly`, `year_figures`, `transitions` from `analysis/demo_day_timing.py`; "server starts" = sum of hour-to-hour increases in servers running.)
- At N = 8 the yearly figures are unchanged to six digits; at N = 6 coverage falls by 0.02 points. The claim survives.
- 2 kWh was picked because it gives a 10-second pause on screen. On the same model a larger band gives fewer starts at no cost at N = 8. A band chosen for the camera is a demo setting, even if it is a core parameter. Choose it from a sweep like the one above and say why.
- July has 4 different daily patterns under this variant; the script's times hold for 15 July only.
- The cap is switched on the current hour's space heating being zero, which also happens on 3,818 hours inside and around the heating season. Untested against deadlines and tank loss.

**2.8 The January day shows nothing for 36 seconds.**
On 13 January all 8 servers run all 24 hours. That is 12% of the pitch with no event. The day is also tied to N = 8, which the sibling critique on servers and price puts in doubt. 25 January at N = 8 has a tank-full pause and a resume in winter (computed, reproduced). Pick the days after N is decided, and run January at 1.0 s per hour at most.

**2.9 Scaling rule: stated, but the error could be large in either direction.**
"Same energy per job" makes the 1 kW server about 44 times the laptop. Apple Silicon is efficient per watt against CPU rack servers and weak against GPU servers, so jobs per server-hour could be off several-fold up or down. The brief only asks that the scaling be stated, so the rule is admissible as an assumption, but the cross-check should not wait until after the draft, and gross against net-of-idle energy (a 10 to 25% difference on the readings above) must be fixed in the rule.

**2.10 Adapter bound.**
Apple's spec page gives the 96 W adapter for the 12-core M3 Pro, which is this machine; 70 W is for the 11-core model. The battery is "72.4-watt-hour" with a footnote "Actual rating of 69.6 watt-hours (14-inch model)". An adapter rating bounds average wall power, not peaks (the battery can add to it).

**2.11 Timeline.**
- Direction is right: walking skeleton at 11:00, freeze, recording, early form.
- Role A at 11:20 to 12:15 has "job queue, deadlines, two job types in core.py" in 55 minutes, then all seven figures including missed deadlines and computing income by 14:15. That is the least realistic cell in the table and everything after it depends on it.
- All four are held from 14:15 to 15:30 for a draft the organisers call "rough is fine": about 5 person-hours. Two people can do the clean-clone check and the form.
- The byte-identical test is written at 11:20 against a trace format that role A changes at 11:20 and again at 12:45. Expect it to be red at 14:15.
- No slot for: the team's own idea (still a placeholder), the decision on N after the price critique, diffing the official profile if it is published, reading the case Q&A, checking the other three laptops (telemetry field, MPS, mlx).
- Breakfast is 09:00 to 10:00; the table starts an all-hands at 09:00.
- Two hours for a voiced video including assembly, upload and link test is tight for people who have not chosen a host.
- Cut list item 6 drops forecast use, but the working idea says permits come "from the weather forecast" and the core use case says the system "checks the weather forecast". Cutting it changes the pitch, not only the code. Item 4 drops the dashboard that the core use case names.

**2.12 Smaller points.**
- Kill test: the restart check accepts either of two start values, kills are timed to land inside a batch, and the checkpoint is not fsynced. It shows safety against a process kill, not against power loss.
- Cooperative stop and restart were timed on a dummy with no model. Model load time, the real cost, is unmeasured (the investigator says so).
- `import mlx.core, mlx_whisper` took 1.24 s here against the 0.92 s reported; `import torch` 0.57 s, as reported.
- The toy torch test is a matrix product. mlx, which is what the installed transcription library uses, was not tested under SIGSTOP.
- At 2.5 s per simulated hour the real job does 2.5 s of work per "server-hour". The real counter and the modelled job progress are different quantities and the screen must label them so.

## 3. Source and re-run checks

| Claim | Result |
|---|---|
| C1 to C7 | Reproduced; values move a few percent between runs (for example 421 batches against 435) |
| C8 | torch 0.57 s reproduced; mlx 1.24 s here |
| C9, C10, C12, C13, C14, C21, C23, C24, C25 | Quotes found on the pages named |
| C11, C15, C16 | Reproduced |
| C17 | Gaps of 23 to 61 s seen; see 2.3 |
| C18 | Unit supported by internal consistency and Apple's idle figure; still no meter; see 2.2 |
| C19 | Inference; see 2.4 |
| C20 | Confirmed, with the 69.6 Wh footnote and the adapter split by chip variant |
| C22 | Incomplete: an idle figure is published; see 2.1 |
| C26 to C30 | Reproduced; C29 extended in 2.7 |
| C33 to C35 | Match the local copies |

## 4. Housekeeping

A 32 MB PDF (the Apple report) was downloaded to the session scratchpad, outside the repo, to read one table, and deleted afterwards.
