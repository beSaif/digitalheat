# Docs — DigitalHeat case (sprintd Basel · GreenTech Edition, 20–22 Nov 2026)

| File | What's in it |
|---|---|
| [case-brief.md](case-brief.md) | The full case from the sprintd platform: problem, reference house, data sources, must-haves, pitch format, jury scoring |
| [case-presentation.md](case-presentation.md) | Text of DigitalHeat's slide deck |
| [DigitalHeat-case-presentation.pdf](DigitalHeat-case-presentation.pdf) | The original slide deck (from the case's Dropbox link) |
| [assumption-limits.md](assumption-limits.md) | **Where the case's simplifications stop holding** (tank losses, server heat temperature, hot-water pattern) and how to handle them in the implementation and the pitch |
| [submission.md](submission.md) | What the platform's submission form asks for, and what to fix before submitting |
| [event.md](event.md) | Our team, organizer announcements, where to ask questions, venue basics, schedule, mentors, perks |
| [../data/README.md](../data/README.md) | The input data: reference-house hourly profile, weather, electricity price, MLPerf summary |

## Key deadlines

- **Sat 21 Nov 15:00** — draft submission
- **Sun 22 Nov 08:30** — final submission
- **Sun 22 Nov 09:00–11:30** — DigitalHeat pitches, room 2.22 (5 min + live demo, 3 min Q&A)

## Must-haves at a glance

1. **Workloads** — ≥2 job types with runtime, energy, interruptibility, deadline; ≥1 actually runs and is measured on our machine; scaled to the 1 kW reference server; jobs/day with source.
2. **Scheduling** — follows heat demand with a heat storage tank; the same scheduler that produces the yearly balance pauses/resumes a real running job on the heat signal.
3. **Yearly balance for the reference house** — servers per house, % of heat demand covered, heat dumped, utilisation, % missed deadlines, electricity cost, computing income, break-even CHF per server-hour.

Pitch must open with those key figures, then demo a January day, a July day, and a real job being paused and resumed.

**Must also cover, in implementation and pitch:** where the case's assumptions stop holding (tank losses, server heat too cool for hot water without a booster, hot-water timing). See [assumption-limits.md](assumption-limits.md). This is what the Feasibility criterion (25%) scores.

## Reference numbers (collected, not modelled)

| | Value | Source |
|---|---|---|
| Space heating, reference house, 2025 | 26,851 kWh on 206 heating days | rebuilt profile, [data/README.md](../data/README.md) |
| Hot water | 4,380 kWh/year (12 kWh/day) | case |
| Total heat demand | 31,231 kWh/year | rebuilt profile |
| Electricity price | 33.25 Rp/kWh (0.3325 CHF/kWh) | ElCom 2026, IWB, Basel, H4 |
| Value of heat | 13.30 Rp/kWh of heat (electricity price ÷ 2.5) | case rule |

## Open items

- **Official reference-house CSV:** not linked on the case page, even for signed-in builders. Asked in the case Q&A (20 Nov, 23:27). Until it arrives, `data/reference_house_2025_hourly.csv` is our rebuilt stand-in; it matches the case's coldest hour, 206 heating days and about 27,000 kWh.
- **Repo is private:** must be opened up for the jury before submitting (see [submission.md](submission.md)).
- **Unverified numbers in [assumption-limits.md](assumption-limits.md):** tank losses and server outlet temperatures are general engineering ranges; check them against the sources named there before using them in the pitch.
- **Not collected yet:** cloud on-demand and spot prices; MLPerf power measurements (the summary sheet has throughput only).
