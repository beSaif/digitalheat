# Docs — DigitalHeat case (sprintd Basel · GreenTech Edition, 20–22 Nov 2026)

| File | What's in it |
|---|---|
| [case-brief.md](case-brief.md) | The full case from the sprintd platform: problem, reference house, data sources, must-haves, pitch format, jury scoring |
| [case-presentation.md](case-presentation.md) | Text of DigitalHeat's slide deck |
| [DigitalHeat-case-presentation.pdf](DigitalHeat-case-presentation.pdf) | The original slide deck (from the case's Dropbox link) |
| [event.md](event.md) | Event logistics: schedule with our deadlines and pitch room, relevant mentors, perks |

## Key deadlines

- **Sat 21 Nov 15:00** — draft submission
- **Sun 22 Nov 08:30** — final submission
- **Sun 22 Nov 09:00–11:30** — DigitalHeat pitches, room 2.22 (5 min + live demo, 3 min Q&A)

## Must-haves at a glance

1. **Workloads** — ≥2 job types with runtime, energy, interruptibility, deadline; ≥1 actually runs and is measured on our machine; scaled to the 1 kW reference server; jobs/day with source.
2. **Scheduling** — follows heat demand with a heat storage tank; the same scheduler that produces the yearly balance pauses/resumes a real running job on the heat signal.
3. **Yearly balance for the reference house** — servers per house, % of heat demand covered, heat dumped, utilisation, % missed deadlines, electricity cost, computing income, break-even CHF per server-hour.

Pitch must open with those key figures, then demo a January day, a July day, and a real job being paused and resumed.

## Missing

The case says a ready hourly profile CSV (weather, heating demand, hot water) for the reference house is "provided with the case", but the public case page does not link it. It is probably visible only to signed-in/accepted builders on the platform, or handed out at the deep dive. It can be rebuilt from the Open-Meteo 2025 Basel archive with the formula in [case-brief.md](case-brief.md#reference-house); check the result against ~27,000 kWh/year over 206 heating days.
