# Operator dashboard: design research (Sat 21 Nov)

What the fleet-operations design in the Claude Design canvas is based on. Three web-research passes. Firecrawl ran out of credits partway through, so the agents used plain web search and fetch, and some sources are marked unverified.

## What real operator consoles do

- **Gray by default, colour only for abnormal states.** High-performance HMI practice (ISA-101, ASM Consortium). A planned automatic state ("tank full, jobs checkpointed") is drawn in gray, not red. Alarms carry a shape, a priority number and text, so they don't rely on colour alone.
  - Inductive Automation, high-performance HMI: <https://docs.inductiveautomation.com/docs/8.1/ignition-modules/vision/common-tasks-in-vision/high-performance-hmitechniques>
  - ISA blog: <https://blog.isa.org/the-high-performance-hmi>
- **Light, mid-gray backgrounds.** ASM Consortium, "Why gray backgrounds for DCS operating displays" (Honeywell PDF): <https://process.honeywell.com/content/dam/process/en/documents/document-lists/doc_asm-consortium/white-papers/February%2028%202011%20-%20Why%20Gray%20Backgrounds%20for%20DCS%20Operating%20Displays.pdf>
- **Display hierarchy:** fleet, then district, then house, then job and checkpoint log. Level 1 shows everything the operator is responsible for.
  - Nimmo, high-performance HMI best practices: <https://www.controlglobal.com/articles/2012/nimmo-best-practices-high-performance-hmi-design/>
- **Fleet tools open on a dense, filterable list of assets, not charts.** Enphase made its system list the landing page. Nomad's topology view draws each node as a capacity block filled by its allocations, and keeps reserved and used apart (for us: permits granted vs heat absorbed).
  - Nomad topology view: <https://developer.hashicorp.com/nomad/tutorials/web-ui/topology-visualization>
- **Refusal at intake is a first-class event with a stated reason.** Borg and Nomad report placement failures with their cause. Our version: "needs 3.6 h, only 3 permit-hours before due".
  - Borg summary: <https://blog.acolyer.org/2015/05/07/large-scale-cluster-management-at-google-with-borg/>
- No public screenshots of Heata, Qarnot, Deep Green or Thermify operator consoles were found.

## Map and simulation

- **One clock drives every view:** the map, the sites × hours matrix, the detail panel and the year cursor (as in deck.gl's `currentTime`).
- **The year as a 365 × 24 heatmap,** used as the overview and navigator. This is Bret Victor's "ladder of abstraction": step up to the whole year, step down to one hour.
  - <https://worrydream.com/LadderOfAbstraction/>
- **Playback controls:** play/pause, speed, ±1 h steps, and bookmarks for notable days. These come from kepler.gl playback and requests in the Windy community.
  - <https://docs.kepler.gl/docs/user-guides/h-playback>
- **Runs side by side:** A vs B with the difference, plus a "Reproduce" block with the commands, seed and commit.
- **Stack, if the dashboard is coded:** MapLibre GL with a self-hosted Protomaps `.pmtiles` extract (no tile server needed during the demo), and Observable Plot or uPlot for charts. OpenStreetMap attribution must stay visible or one click away.
  - <https://osmfoundation.org/wiki/Licence/Attribution_Guidelines>

## Visual rules (anti "AI slop")

- No rows of identical KPI cards, no dark background with neon accents, no monospace for big numbers.
  - pixelslop catalogue: <https://cdn.jsdelivr.net/npm/pixelslop@0.3.8/dist/skill/resources/ai-slop-patterns.md>
- Separate sections with hairlines instead of cards, use 2 px corner radius, and give sizes a real hierarchy.
- IBM Plex Sans with tabular figures. Units follow the value, smaller and lighter.
- One sequential heat scale (ColorBrewer YlOrBr). Saturated red is kept for alarms. No rainbow.
  - Crameri et al. 2020: <https://pmc.ncbi.nlm.nih.gov/articles/PMC7595127>
- Design empty and normal states: "0 alarms" is a real screen.

## Data behind the canvas

- **Districts:** data.bs.ch dataset 100042 (Geodaten Kanton Basel-Stadt, CC BY 4.0).
- **Population 2024:** data.bs.ch dataset 100060.
- **Rivers:** OpenStreetMap (ODbL), via Overpass.
- **Scenario fleet:** 24 sites placed by population. House size ×0.6–1.5 of the reference house; servers and tank (20–70 kWh) varied. Seed 11.
  - Physics: the follow-heat rule from `analysis/baseline_sweep.py`.
  - Fleet result: 133 servers, 77.7% of heat demand covered, 59.3% utilisation, 0 kWh dumped.
  - Site BS-15 has the reference configuration and reproduces the reference house's trace exactly.
  - The generator is not in the repo yet.
