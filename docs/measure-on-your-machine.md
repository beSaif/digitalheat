# Measure the workloads on your machine

We average the energy and speed of our two real jobs over several team laptops, so the numbers don't rest on one machine. Paste the prompt below into Claude Code (or follow it by hand). It takes about 25 minutes, most of it waiting.

**Before you start:**
- **Apple-silicon Mac laptop (M1–M4):** you can measure energy, the number we need most. Charge to at least 40%, then run it **unplugged**.
- **Any other machine:** you can measure speed only. That's still useful.
- You need access to the GitHub repo `beSaif/digitalheat`.

---

```text
I'm helping my hackathon team (DigitalHeat case, team Ctrl+Free) measure how fast and how
energy-efficiently two real AI jobs run on my computer. The team will average results from
several laptops. Please do this end to end, and explain each step to me briefly as you go.

1. Get the code
   - Clone https://github.com/beSaif/digitalheat (or `git pull` if I already have it) and check
     out the branch `workloads`.
   - Read docs/workloads.md (the method) and scripts/measure_workloads.py before running anything.

2. Set up Python
   - Install uv if it's missing (https://docs.astral.sh/uv/), then:
       uv venv --python 3.11 .venv
       uv pip install --python .venv/bin/python -r requirements-workloads.txt
   - On Linux (x86), get the CPU-only PyTorch so it doesn't pull ~2.5 GB of CUDA:
       add `--index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple`
   - On Windows, the interpreter is .venv\Scripts\python instead of .venv/bin/python.

3. Smoke test: run both real jobs once (first run downloads two models, ~180 MB):
       .venv/bin/python -m workloads.run embed  --job-dir runs/smoke-embed  --items 640
       .venv/bin/python -m workloads.run rerank --job-dir runs/smoke-rerank --items 640
   Both must end with "done at item 640 of 640".

4. Interruption test (macOS/Linux only; skip on Windows):
       .venv/bin/python scripts/test_interruption.py
   It must print PASS. This shows a job can be paused, stopped and resumed with identical output.

5. Measure. Pick a short label for me (first name or initials, lowercase, no spaces).
   - Apple-silicon Mac LAPTOP: ask me to unplug the charger, close other apps, keep screen
     brightness unchanged and not touch the computer for ~15 minutes. Then run:
         .venv/bin/python scripts/measure_workloads.py --label <label>
   - Any other machine (Intel Mac, Windows, Linux, desktop):
         .venv/bin/python scripts/measure_workloads.py --label <label> --no-meter
   Run it in the foreground and don't run other heavy commands while it measures: the power
   meter reads the whole machine, so any other work would distort the numbers.

6. Share the result
   - It writes exactly one new file: data/measurements/workloads_<date>_<label>_<cpu>.json
   - Commit ONLY that file to the `workloads` branch (`git pull --rebase` first) and push.
     If I can't push, tell me to send the file to the team chat instead.
   - Don't run scripts/combine_measurements.py and don't commit data/measurements/combined.json;
     one teammate combines everyone's files.

Rules:
- Don't change the code in workloads/ or scripts/. All machines must use the same jobs, models and
  method, or the results can't be averaged. Fixing my environment (installing Python, uv,
  packages) is fine.
- If something fails, stop and tell me the exact error. Don't work around the measurement logic.

At the end, show me a short summary: my CPU, items/s for embed and rerank, J/item (if measured),
whether the interruption test passed, and whether the file was pushed or needs sending.
```

---

## For whoever combines the results

```bash
git pull
python3 scripts/combine_measurements.py   # prints every machine, writes data/measurements/combined.json
.venv/bin/python -m workloads.catalog     # reference-server job types, now from the team average
```

Energy per item is averaged over metered machines only. Speed is averaged over all of them, but it's for comparison only, because the reference server's throughput comes from energy per item ([workloads.md](workloads.md#scaling-to-the-1-kw-reference-server)). Report the spread (min–max) next to the mean in the pitch: it shows how much the numbers depend on the hardware.
