# DigitalHeat fleet console

Operator dashboard for a scenario fleet of heat-following servers: 24 houses in 10 Swiss cities, replayed hour by hour over 2025 weather.

| Screen | Route | What it shows |
|---|---|---|
| Overview | `/` | Live operator KPIs (servers running vs heat permit, heat delivered, job queue, refusals), week of heat, jobs due next, site states, year-to-date coverage, year replay |
| Fleet map | `/map` | Swiss cantons coloured by heat demand / servers running / coverage, city pins, city detail card, 7-day heat, coverage trend |
| Services | `/services`, `/services/[id]` | What the fleet sells (J1 transcription, J2 LLM batch): job size, deadline, throughput on the reference server, volume sold and refused per month and site, cost floor per audio-hour / per M tokens against public list prices; plus the two jobs measured on team laptops |
| Economics | `/economics` | The reference server (4 × RTX PRO 4500 Blackwell SE, ≈1 kW) and its installed cost, cost of one house, yearly cost breakdown, break-even and price needed per sold server-hour against market prices, per-site table. Selling price, occupancy, who keeps the heat and write-off period are adjustable (`lib/money.ts`, same formulas as the generator) |
| Site | `/sites/[id]` | 3D city block (MapLibre + OpenFreeMap) with the house highlighted, the rack with each server's state and job, tank, ±24 h heat permit, per-server detail |

One clock (top bar) drives every screen. `?t=<hour of year>` opens at a given hour, e.g. `/?t=2533` (16 Apr 13:00, tanks full, servers throttled).

## Run

```bash
pnpm install
pnpm data      # regenerate public/data from ../scripts/build_fleet_scenario.py (stdlib Python, seed 11)
pnpm dev
```

Map tiles load from tiles.openfreemap.org, so the site view needs internet. Everything else is served from `public/data`.

## Data

Not live telemetry. See the generator's docstring (`../scripts/build_fleet_scenario.py`) and the "Method & data" dialog in the app.
