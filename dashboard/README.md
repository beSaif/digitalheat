# DigitalHeat live demo

The room runs a customer's jobs: phones and laptops are DigitalHeat servers in Swiss buildings, and work only goes where heat is needed.

## Run

```bash
pnpm install
pnpm dev        # or, for the event: pnpm build && pnpm start
```

Open `/` on the projector. Map tiles load from tiles.openfreemap.org, so the map needs internet.

## How it works

| Screen | Route | Who | What it is |
|---|---|---|---|
| Room screen | `/` | everyone (projector) | DigitalHeat's view: map of the buildings, which need heat at the chosen moment, the jobs, and the job being run |
| Client | `/client` | the jury | DigitalHeat's customer: orders every job (3D rendering, AI embeddings, AI reranking), watches it, downloads the output |
| Join | `/join` | the room | the QR code's target: gives the device an id and opens the host screen |
| Host | `/node/[id]` | the room | asks for a first name; the phone is that person's rack and runs parts of jobs while their building needs heat |

**Roles.** People in the room are **hosts**: each one adds their own building (house, pharma lab, family home, spa, office, greenhouse or city house, in turn) with a rack of servers. The jury is the **customer**. The room screen is **DigitalHeat**.

**Sizing.** Every building has enough servers for 100 % of its heat demand, no heat pump and no backup heater: servers = the building's highest hour of heat demand in 2025 ÷ 0.8 kW (house 14, hospital 33, office 67, …).

**No clock.** The operator picks a moment: *Now* (today's date and hour, 2025 weather), *January* (15 Jan, 08:00) or *July* (15 Jul, 14:00). `python3 -m scheduler.day` runs the DigitalHeat scheduler (the yearly balance's code, fast-forwarded from 1 January, `sizing: "peak"`) for the whole fleet and returns that hour's decision: for each building its heat demand, tank and how many servers it switches on. It decides again when someone joins or the moment changes.

**Live tanks.** At the chosen moment every tank starts at a random level between 20 % and 90 % (never above the scheduler's level): a real tank is rarely full, someone just took a long shower. From then on each building draws its heat demand (that hour's) from its tank, and the tank gets 0.8 kW per server running a customer's job: no job, no heat, and the tank drains. A building switches on as many servers as cover its demand plus refilling its tank within an hour, at most all of them; its device works that share of the time. The tanks run 60 times faster than real time (1 s = 1 min, `TANK_SPEED` in `lib/live/shared.ts`), so a job's heat shows. Picking a moment again restarts them from the scheduler.

**Tank full: pause, save, move.** A tank that reaches 100 % switches its rack off until it has cooled to 90 % (`TANK_RESUME`), like a buffer tank's top and bottom sensors. The part that rack was working on pauses: the device saves a checkpoint (a render tile: the image so far and the samples traced; an AI part: the items already done) and the part goes to the next rack whose building needs heat. That rack continues from the checkpoint and does not repeat the work: a tile starts from the saved image and averages its new samples with the saved ones, and an AI part runs only the items that are left. On the room screen the paused part shows its saved percentage, a dashed arrow on the map goes from the paused building to the one that takes over, and the host's phone says where its part went. For a demo, hover a building on the map and press **Fill tank** while its card says "Working on part …".

**Who did which part.** On the room screen each building has a colour. A part in progress glows in that colour with the building's name, a finished tile keeps a corner in it, and the **Rendered by** row under the job lists every building with its part count. Hover a name there, or a building in the list on the left, to light up its parts.

**3D view.** Hover a building on the map and press **3D view** on its card: the map flies into its block in 3D with the building in rust. **Back to map** (or Escape) returns.

**Every job comes from the client screen**, and nothing else runs. Three products:

- **3D rendering.** A 960 × 540 path-traced image (a room with a ceiling light, three spheres; diffuse and mirror surfaces, direct light sampling), split into 60 tiles. Tiles go only to racks whose building needs heat. A device stands for its whole rack: with k of N servers on it renders k/N of the time, so on a July afternoon homes (hot water only) barely render and the pharma lab, spa and hospital do most of the image. The overview's own sites have no phones; the room screen renders their share in background workers. A host who leaves (page hidden, phone locked, 6 s silent) hands their part back to the queue.
- **AI embeddings.** 240 BEIR SciFact abstracts embedded with `all-MiniLM-L6-v2` (max 256 tokens), 30 parts of 8. Output: one 384-number vector per abstract, as JSON.
- **AI reranking.** The customer's question (or a SciFact claim); a keyword first stage picks 120 candidate abstracts, `ms-marco-MiniLM-L6-v2` (max 512 tokens) scores each (question, abstract) pair, 15 parts of 8. Output: the top 5 abstracts, and all scores as JSON.

The AI jobs use the same models and data as the measured workloads (`workloads/jobs.py`), run in the browser with transformers.js (ONNX, 8-bit quantized, one thread). The models (23 MB each), the runtime (`public/ai/`, 27 MB of WASM) and SciFact (`data/scifact.json`, exported from `data/raw/scifact`) are served by the operator laptop, so no internet is needed; each device downloads a model the first time it gets that kind of job. Prices: a job's server time on the 1 kW reference server (AI from the measured items per server-hour, rendering estimated) at DigitalHeat's price per server-hour.

For the event, run a production build (`pnpm build && pnpm start`), which handles a room of phones better than `pnpm dev`. Phones must reach the operator laptop. On Wi-Fi that keeps devices apart, use a tunnel, e.g. `cloudflared tunnel --url http://localhost:3000`, then either open `/` through the tunnel URL, start with `LIVE_PUBLIC_URL=https://….trycloudflare.com`, or add `?join=https://….trycloudflare.com` to `/`. The QR code follows.

Old `/live` links redirect to `/` (query string kept).
