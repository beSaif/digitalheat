# digitalheat

Team **Ctrl+Free** at sprintd Basel · GreenTech Edition (20–22 Nov 2026), working on the DigitalHeat case:
*Useful Load ⇒ Useful Heat: can your computing power heat a home while doing useful work?*

- [`docs/`](docs/README.md): the case brief, DigitalHeat's slides, submission requirements, event info
- [`data/`](data/README.md): input data for the reference house (hourly heat demand, weather, electricity price)
- [`scripts/`](scripts/): `build_reference_profile.py` rebuilds the hourly profile from Open-Meteo (Python 3, standard library only)

```bash
python3 scripts/build_reference_profile.py            # rebuild data/reference_house_2025_hourly.csv
python3 scripts/build_reference_profile.py --download # re-fetch the weather first
```

## AI tools

Repository set-up, data collection and documentation were done with Claude Code.
