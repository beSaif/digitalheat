# digitalheat

Team **Ctrl+Free** at sprintd Basel · GreenTech Edition (20–22 Nov 2026), working on the DigitalHeat case:
*Useful Load ⇒ Useful Heat: can your computing power heat a home while doing useful work?*

- [`docs/`](docs/README.md): the case brief, DigitalHeat's slides, submission requirements, event info
- [`data/`](data/README.md): input data for the reference house (hourly heat demand, weather, electricity price)
- [`scripts/`](scripts/): `build_reference_profile.py` rebuilds the hourly profile from Open-Meteo (Python 3, standard library only); `measure_workloads.py` measures the real jobs' runtime and energy
- [`workloads/`](workloads/): the two real, interruptible jobs (embeddings, reranking) and their scaling to the 1 kW reference server; see [docs/workloads.md](docs/workloads.md)

```bash
python3 scripts/build_reference_profile.py            # rebuild data/reference_house_2025_hourly.csv
python3 scripts/build_reference_profile.py --download # re-fetch the weather first
```

### Real workloads

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements-workloads.txt
.venv/bin/python -m workloads.run embed --job-dir runs/embed-001 --items 20000   # run / resume a real job
.venv/bin/python -m workloads.catalog                                            # job types on the 1 kW reference server
.venv/bin/python scripts/measure_workloads.py --label <you>                      # re-measure (on battery, ~15 min)
.venv/bin/python scripts/test_interruption.py                                    # pause/stop/resume gives identical output
```

Models download from Hugging Face on first run (~180 MB). Measurement uses the macOS battery gauge, so it needs an Apple-silicon laptop on battery; running the jobs works anywhere. To add your machine to the team average, see [docs/measure-on-your-machine.md](docs/measure-on-your-machine.md).

## AI tools

Repository set-up, data collection and documentation were done with Claude Code.
