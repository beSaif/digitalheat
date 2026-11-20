# DigitalHeat case presentation (text of the slides)

Text transcribed from [DigitalHeat-case-presentation.pdf](DigitalHeat-case-presentation.pdf) (6 slides), the deck DigitalHeat shared with the case.

## 01 · Server heat and sovereign AI

**DigitalHeat** — Distributed servers for computing, AI and building heat in Switzerland.

- **5–20 kW** heat per installed unit
- **Switzerland** local data and operations
- **50–70 °C** heating and hot water

(Photo: a server rack in a basement next to a hot-water storage tank.)

## 02 · Solution: computing where buildings need heat

Servers heat buildings. Heat exchangers connect computing to storage, heating and hot water.

- **Building:** heating, hot water and storage
- **Server rack:** CPU and GPU work produces heat, 5–20 kW
- **Useful heat:** 50–70 °C target, system dependent
- **Useful IT power:** up to 40 servers per rack

**Control:** flexible workloads follow heat demand.

## 03 · Ideas for flexible computing jobs

Which useful jobs can follow the heat demand?

- **Local LLMs:** batch inference, document indexing and model evaluation.
- **Images and video:** image tagging, CLIP embeddings, visual search and transcription.
- **Other ideas?** Rendering, simulations, data processing or something completely different.

## 04 · Jobs that can slow down, pause and move

Computing follows heat demand. When a site needs no heat, work moves to another eligible site.

- **Slow down:** reduce processing speed or the number of active workers.
- **Pause and resume:** save progress. Continue later without repeating completed work.
- **Distribute the work:** resume saved work or assign the next batch elsewhere. Respect access and deadlines.

## 05 · Rechnen. Heizen. (German)

*Dezentrale Infrastruktur* — "Ein Digital-Heat-Server im Keller. Rechenleistung wird direkt zu nutzbarer Wärme."
(Decentralised infrastructure — a Digital Heat server in the basement; computing power becomes usable heat directly.)

Diagram: house with server → heat exchanger (Wärmetauscher) → heating loop. A timeline zooms out Haus → Basel → Nordwestschweiz → Schweiz. Map source credit: swissBOUNDARIES3D 2026 · swisstopo.

## 06 · The hackathon: computing, heat and break-even

Build a working scheduler. Test a full year and explore paid services.

- **Run real jobs:** demonstrate useful jobs that slow down, pause and resume across servers.
- **Follow heat demand:** simulate a year with storage and backup heat. Measure useful computing and heat.
- **Paid services:** who pays, and how much? Compare service income and heat value with total costs.
