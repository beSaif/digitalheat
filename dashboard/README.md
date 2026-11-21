# DigitalHeat fleet console

Operator dashboard for a scenario fleet of heat-following servers: 24 houses in 10 Swiss cities, replayed hour by hour over 2025 weather.

| Screen | Route | What it shows |
|---|---|---|
| Overview | `/` | Live operator KPIs (servers running vs heat permit, heat delivered, job queue, refusals), week of heat, jobs due next, site states, year-to-date coverage, year replay |
| Fleet map | `/map` | Swiss cantons coloured by heat demand / servers running / coverage, city pins, city detail card, 7-day heat, coverage trend |
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
