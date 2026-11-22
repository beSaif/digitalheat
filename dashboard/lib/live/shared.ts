/*
 * Live demo: the room's phones as DigitalHeat servers, rendering a customer's image.
 * Shared between the coordinator (route handlers) and the browser pages.
 *
 * Three roles. The room are hosts: everyone who scans the QR code adds their own building with a rack
 * of servers. The jury is DigitalHeat's customer: on /client they order a render job. The big screen
 * is DigitalHeat: it splits each job into tiles and hands them only to racks whose building needs heat,
 * as decided by the DigitalHeat scheduler (scheduler/core.py, the yearly balance's code) for the
 * chosen moment. The phones and the operator laptop path-trace the tiles for real.
 */

export const IMG_W = 960;
export const IMG_H = 540;
export const COLS = 10;
export const ROWS = 6;
export const TILE_W = IMG_W / COLS; // 96
export const TILE_H = IMG_H / ROWS; // 90

/* --------------------------------- render jobs --------------------------------- */

/** What a customer can order: a scene. One quality (samples per pixel) keeps the order page simple. */
export const SCENES = {
  warm: { label: "Living room, evening", note: "warm ceiling light" },
  day: { label: "Living room, daylight", note: "cool, bright" },
  gallery: { label: "Gallery", note: "white walls, mirror spheres" },
} as const;
export type SceneKey = keyof typeof SCENES;
export const QUALITY = {
  draft: { label: "Draft", spp: 64 },
} as const;
export type QualityKey = keyof typeof QUALITY;
export const TILES = COLS * ROWS;

/** Light paths one 1 kW reference server traces per second: measured per core × its cores (an estimate). */
export const PATHS_PER_CORE_S = 1.6e6; // measured: this path tracer on the demo laptop, one core
export const REF_SERVER_CORES = 192; // 2x AMD EPYC 9654, data/prices_2026.json "reference_server"

export type Pricing = {
  sellChfH: number; // DigitalHeat: AWS spot for the same server × (1 + premium)
  spotChfH: number;
  onDemandChfH: number;
  premium: number;
  refServer: string;
};

/*
 * The AI jobs are the two measured workloads (workloads/jobs.py), on BEIR SciFact abstracts, with the
 * same models, run in the browser (public/ai/worker.js). A job is split into parts of AI_PART items.
 */
export const EMBED_ITEMS = 240; // abstracts per embeddings order
export const RERANK_ITEMS = 120; // candidate abstracts scored per reranking order
export const AI_PART = 8;
/** Items one 1 kW reference server does per hour: measured (data/measurements/combined.json, gross), see workloads/catalog.py. */
export const ITEMS_PER_SERVER_H = { embed: 12.29e6, rerank: 5.46e6 } as const;

/** What a customer can order. */
export const PRODUCTS = {
  render: { label: "3D rendering", unit: "image", per: 1_000, perLabel: "1,000 images" },
  embed: { label: "AI embeddings", unit: "abstract", per: 1_000_000, perLabel: "1 million abstracts" },
  rerank: { label: "AI reranking", unit: "pair", per: 1_000_000, perLabel: "1 million pairs" },
} as const;
export type JobKind = keyof typeof PRODUCTS;
export const ITEMS: Record<JobKind, number> = { render: 1, embed: EMBED_ITEMS, rerank: RERANK_ITEMS };
export const PARTS: Record<JobKind, number> = { render: TILES, embed: EMBED_ITEMS / AI_PART, rerank: RERANK_ITEMS / AI_PART };

/** What an order costs: its server time on the reference server, at DigitalHeat's price per server-hour. */
export function quote(kind: JobKind, p: Pricing) {
  const perItemS = kind === "render" ? (QUALITY.draft.spp * IMG_W * IMG_H) / (PATHS_PER_CORE_S * REF_SERVER_CORES) : 3600 / ITEMS_PER_SERVER_H[kind];
  const serverS = perItemS * ITEMS[kind];
  return { serverS, chf: (serverS / 3600) * p.sellChfH, perUnits: (perItemS * PRODUCTS[kind].per * p.sellChfH) / 3600 };
}

/** "paused": its rack was switched off mid-part (tank full) and is saving its progress; then it waits for another rack. */
export type TileState = "pending" | "running" | "paused" | "done";
export type JobPart = {
  i: number;
  state: TileState;
  node: string | null;
  v: number;
  restarts: number;
  /** share of the part already done and saved at a checkpoint (0 = none): the next rack continues from there */
  saved?: number;
  /** the rack that paused it (until it is done) */
  from?: string | null;
  pausedAt?: number;
};
export type Hit = { title: string; text: string; score: number };
export type Job = {
  id: number;
  kind: JobKind;
  customer: string;
  createdAt: number;
  startedAt: number | null;
  doneAt: number | null;
  tiles: JobPart[];
  scene?: SceneKey; // render
  query?: string; // rerank: the customer's question
  top?: Hit[]; // rerank: best abstracts so far
  latest?: string[]; // embed: titles from the part finished last
};

/**
 * A tank that reaches 100 % switches its rack off until it has cooled to TANK_RESUME (a charging band, as a
 * real buffer tank's top and bottom sensors): the part in progress is saved and continues on another rack.
 */
export const TANK_RESUME = 0.9;

/** The tanks run faster than the room: 1 real second is TANK_SPEED seconds of the buildings' heat (1 s = 1 min). */
export const TANK_SPEED = 60;

/** The moments the operator can show. "now" is today's date and hour, with 2025 weather (the data year). */
export const CONDITIONS = {
  now: { label: "Now" },
  january: { label: "January morning", day: 14, hour: 8 },
  july: { label: "July afternoon", day: 195, hour: 14 },
} as const;
export type CondKey = keyof typeof CONDITIONS;

/** Colours: DigitalHeat's first, then evenly spread hues so a room of phones can still find themselves. */
const BRAND = ["#c0653a", "#5fa8b0", "#f2a65a", "#8f4423", "#3f7f87"];
export function colorFor(i: number) {
  if (i < BRAND.length) return BRAND[i];
  const hue = Math.round(((i - BRAND.length) * 137.508 + 20) % 360);
  return `hsl(${hue} 58% 46%)`;
}

/** The operator's own sites (no phones): muted colours of their own, so every building in a job is told apart. */
const BASE_COLORS = ["#6b7a99", "#8a6fa8", "#9c8a3a", "#6f8a5e", "#a0607a", "#4f7d8f"];
export const baseColorFor = (i: number) => BASE_COLORS[i % BASE_COLORS.length];

/** Names shown on the projector: letters, digits, spaces and . - ' & only, at most 18 characters. */
export const NAME_MAX = 18;
export function cleanName(raw: unknown) {
  if (typeof raw !== "string") return "";
  return raw
    .normalize("NFC")
    .replace(/[^\p{L}\p{N} .'&\-]/gu, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, NAME_MAX);
}

/** Nominal draw under full load, for the heat these devices really give off in the room. */
export const DEVICE_WATTS = { phone: 6, laptop: 45 } as const;
export type Device = keyof typeof DEVICE_WATTS;

/* ------------------------- the scheduler's decisions (scheduler/day.py) ------------------------- */

export type JobRec = {
  id: number;
  type: string; // "embed" | "rerank"
  origin: number; // site the job arrived at
  site: number; // site where it runs or is held, -1 = fleet queue
  state: "queued" | "running" | "paused" | "checkpointed" | "done" | "missed" | "lost";
  done: number; // server-hours
  work: number;
  arrive: number;
  due: number;
  start: number;
  finish: number;
  forced: number;
  moves: number;
  ran: number; // 1 if it ran in this hour
};

export type SiteHourRec = {
  temp: number;
  demand: number;
  soc0: number;
  room: number;
  permit: number;
  reserve_u: number;
  limit: number;
  running: number;
  forced: number;
  served: number;
  soc: number;
  dumped: number;
  paused: number;
  checkpointed: number;
  moved_in: number;
  started: number;
  finished: number;
  embed_sh: number;
  rerank_sh: number;
  heat_soon: boolean;
  down: boolean; // the site is out (a person's rack whose phone left)
  actions: [number, string, string][]; // job id, type, action
};

export type DayHour = { t: number; date: string; hour: number; sites: SiteHourRec[]; jobs: JobRec[] };
export type DaySite = {
  id: string;
  kind: string;
  name: string;
  lat: number;
  lon: number;
  servers: number;
  tank_kwh: number;
  /** a person's own rack: their first name and the id of their device */
  person?: string;
  node?: string;
};

/*
 * Every person who joins adds their own building with its own rack to the fleet: a server only runs
 * where its heat is used, so a rack needs a building. Building types take turns between homes (little
 * heat in summer) and sites that need heat all year; all stand in Basel, so they share its weather.
 */
export const PERSON_KINDS = ["house", "pharma", "family", "spa", "office", "greenhouse", "cityhouse"] as const;
export const KIND_NAME: Record<string, string> = {
  house: "House",
  family: "Family home",
  cityhouse: "City house",
  hospital: "Hospital",
  spa: "Spa",
  greenhouse: "Greenhouse",
  office: "Office",
  pharma: "Pharma lab",
};
/*
 * Site types against the house (our assumption): a building of 4x needs 4 times the house's heat in its
 * coldest hour, so it gets about 4 times the house's servers (house: 14). Each keeps its own heat profile:
 * sites with heat all year (pharma, hospital, spa) have the big racks that stay on in summer, while a
 * house in July runs one or two servers for its hot water.
 */
export const X_HOUSE: Record<string, number> = {
  house: 1,
  cityhouse: 1.3,
  family: 1.5,
  office: 3,
  greenhouse: 3,
  spa: 3,
  hospital: 4,
  pharma: 5,
};
export const PERSON_SERVERS = 2;
export function personRack(index: number, name: string, node: string): Omit<DaySite, "tank_kwh"> {
  const kind = PERSON_KINDS[index % PERSON_KINDS.length];
  // spread around the city centre, inside the reference weather cell (±0.02°)
  const a = index * 2.39996;
  const r = 0.006 + 0.0011 * Math.sqrt(index + 1) * 3;
  return {
    id: `P-${index + 1}`,
    kind,
    name,
    lat: +(47.56 + Math.min(0.017, r) * Math.sin(a)).toFixed(4),
    lon: +(7.59 + Math.min(0.017, r * 1.4) * Math.cos(a)).toFixed(4),
    servers: PERSON_SERVERS,
    person: name,
    node,
  };
}
export type DayData = {
  year: number;
  day: number;
  hour: number;
  sites: DaySite[];
  job_types: Record<string, { server_h: number; due_h: number; arrival_hours: number[]; backlog: boolean }>;
  hours: DayHour[];
};

export type NodeState = "running" | "off" | "waiting" | "offline";

export type Assignment = {
  jobId: number;
  jobType: JobKind;
  chunk: number; // part index
  // render: a tile of the image
  x: number;
  y: number;
  w: number;
  h: number;
  scene: SceneKey;
  budget: number; // samples (spp × pixels)
  // embed / rerank: the abstracts (and the question) of this part
  texts?: string[];
  query?: string;
  /** continue from a checkpoint: render, samples already traced (the saved image is /api/live/tile?ckpt=1); AI, items already done */
  resume?: { done: number; total: number; v: number };
};

export type LiveNode = {
  id: string;
  name: string;
  color: string;
  device: Device;
  state: NodeState;
  site: number; // index in the fleet, -1 if not placed yet
  base: boolean; // the operator laptop rendering for one of the operator's sites
  reason: string;
  cores: number;
  rate: number;
  chunks: number; // tiles rendered
  heatWh: number;
  current: { jobId: number; chunk: number; progress: number; since: number } | null;
};

/** Work that moved between racks: a paused part continuing elsewhere (for the map's arrows). */
export type LiveMove = { at: number; from: string; to: string; jobId: number; part: number; saved: number };

export type LiveEvent = { at: number; text: string; tone: "rust" | "teal" | "amber" | "ink" | "alarm" };

export type Conditions = { key: CondKey; label: string; date: string; hour: number };

export type LiveState = {
  now: number;
  conditions: Conditions | null;
  /** the fleet: the operator's sites, then one rack per person */
  sites: DaySite[];
  /** the scheduler's decision for that moment (same shape as one hour of scheduler/day.py) */
  hour: DayHour | null;
  planning: boolean;
  jobs: Job[];
  nodes: LiveNode[];
  events: LiveEvent[];
  totals: { tiles: number; drops: number; moved: number; paused: number; resumed: number };
  /** site ids whose tank is full: their rack is paused until it cools to TANK_RESUME */
  full: string[];
  moves: LiveMove[];
  pricing: Pricing;
  joinBase: string | null;
};

export type BeatReply = {
  state: NodeState;
  name: string;
  color: string;
  chunks: number;
  heatWh: number;
  site: { name: string; kind: string; servers: number; on: number; tank: number; soc: number; temp: number; own: boolean } | null;
  job: { id: number; customer: string; kind: JobKind; label: string } | null;
  reason: string;
  conditions: string | null;
  assign: Assignment | null;
  abort: boolean;
  /** with abort: save the part's progress first (POST op "checkpoint"), it continues on another rack */
  checkpoint: boolean;
  /** the last time this rack's work moved, in words */
  note: string | null;
};

/* ------------------------------- the path tracer ------------------------------- */

/*
 * Worker source (started from a Blob URL). A small path tracer: a room with coloured walls, a ceiling
 * light and three spheres, diffuse and mirror surfaces, up to 5 bounces with Russian roulette.
 * Each worker renders the rows y ≡ k (mod n) of one tile, one sample per pixel per pass, until it has
 * traced its share of the tile's samples; it posts its rows every quarter second.
 */
export const WORKER_SRC = `
const SCENES = {
  warm:    { left: [0.72,0.33,0.18], right: [0.30,0.58,0.62], wall: [0.82,0.78,0.70], light: [9,7.2,5.2],  sky: 0,   s: [[0.85,0.83,0.78,0],[0.95,0.62,0.28,0],[0.9,0.9,0.9,1]] },
  day:     { left: [0.55,0.62,0.70], right: [0.86,0.80,0.66], wall: [0.88,0.88,0.86], light: [7,7.6,8.6],  sky: 1.2, s: [[0.30,0.55,0.62,0],[0.95,0.95,0.95,1],[0.75,0.40,0.22,0]] },
  gallery: { left: [0.90,0.90,0.88], right: [0.90,0.90,0.88], wall: [0.92,0.91,0.88], light: [8,8,8],      sky: 0,   s: [[0.95,0.95,0.95,1],[0.95,0.95,0.95,1],[0.75,0.35,0.20,0]] },
};
const SPH = [[-0.62,0.46,-0.85,0.46],[0.72,0.36,-0.15,0.36],[0.08,0.26,0.62,0.26]];
const X0=-1.5, X1=1.5, Y1=2.4, Z0=-2.0, Z1=4.2;
onmessage = (e) => {
  const { k, n, a, W, H, budget } = e.data;
  const { x: tx, y: ty, w, h } = a;
  const sc = SCENES[a.scene] || SCENES.warm;
  const rows = [];
  for (let r = k; r < h; r += n) rows.push(r);
  const sums = new Float32Array(rows.length * w * 3);
  let seed = ((k + 1) * 2654435761 ^ (tx * 7919 + ty * 104729 + a.jobId * 31)) >>> 0 || 1;
  const rnd = () => { seed ^= seed << 13; seed >>>= 0; seed ^= seed >>> 17; seed ^= seed << 5; seed >>>= 0; return seed / 4294967296; };
  const fov = Math.tan(25 * Math.PI / 180), asp = W / H;
  const camY = 1.15, camZ = 3.6;
  // light reaching (hx,hy,hz) with normal n from one random point of an emitter (rectangle, area A, normal l)
  function occluded(hx, hy, hz, wx, wy, wz, d) {
    for (let i = 0; i < 3; i++) {
      const s = SPH[i];
      const px = hx - s[0], py = hy - s[1], pz = hz - s[2];
      const bb = px * wx + py * wy + pz * wz, c = px * px + py * py + pz * pz - s[3] * s[3];
      const disc = bb * bb - c;
      if (disc > 0) { const tt = -bb - Math.sqrt(disc); if (tt > 1e-4 && tt < d) return true; }
    }
    return false;
  }
  function direct(hx, hy, hz, nx, ny, nz, qx, qy, qz, lnx, lny, lnz, A, out) {
    let wx = qx - hx, wy = qy - hy, wz = qz - hz;
    const d2 = wx * wx + wy * wy + wz * wz, d = Math.sqrt(d2);
    wx /= d; wy /= d; wz /= d;
    const cs = nx * wx + ny * wy + nz * wz, cl = -(lnx * wx + lny * wy + lnz * wz);
    if (cs <= 0 || cl <= 0 || occluded(hx, hy, hz, wx, wy, wz, d - 1e-3)) return 0;
    return (cs * cl * A) / (d2 * Math.PI);
  }
  function trace(ox, oy, oz, dx, dy, dz) {
    let tr = 1, tg = 1, tb = 1, lr = 0, lg = 0, lb = 0, spec = true;
    for (let b = 0; b < 6; b++) {
      let t = 1e9, nx = 0, ny = 0, nz = 0, cr = 0, cg = 0, cb = 0, mir = 0, em = 0;
      for (let i = 0; i < 3; i++) {
        const s = SPH[i];
        const px = ox - s[0], py = oy - s[1], pz = oz - s[2];
        const bb = px * dx + py * dy + pz * dz, c = px * px + py * py + pz * pz - s[3] * s[3];
        const disc = bb * bb - c;
        if (disc > 0) {
          const q = Math.sqrt(disc);
          let tt = -bb - q;
          if (tt < 1e-4) tt = -bb + q;
          if (tt > 1e-4 && tt < t) {
            t = tt;
            nx = (px + dx * tt) / s[3]; ny = (py + dy * tt) / s[3]; nz = (pz + dz * tt) / s[3];
            const m = sc.s[i]; cr = m[0]; cg = m[1]; cb = m[2]; mir = m[3]; em = 0;
          }
        }
      }
      // the room: six axis-aligned walls
      const walls = [[0, X0, 1], [0, X1, -1], [1, 0, 1], [1, Y1, -1], [2, Z0, 1], [2, Z1, -1]];
      for (let i = 0; i < 6; i++) {
        const ax = walls[i][0], v = walls[i][1], sgn = walls[i][2];
        const d = ax === 0 ? dx : ax === 1 ? dy : dz, o = ax === 0 ? ox : ax === 1 ? oy : oz;
        if (Math.abs(d) < 1e-9) continue;
        const tt = (v - o) / d;
        if (tt > 1e-4 && tt < t) {
          t = tt; nx = ax === 0 ? sgn : 0; ny = ax === 1 ? sgn : 0; nz = ax === 2 ? sgn : 0; mir = 0; em = 0;
          const c = i === 0 ? sc.left : i === 1 ? sc.right : sc.wall;
          cr = c[0]; cg = c[1]; cb = c[2];
          if (i === 3) { const hx = ox + dx * tt, hz = oz + dz * tt; if (hx > -0.65 && hx < 0.65 && hz > -1.3 && hz < -0.1) em = 1; }
          if (i === 4 && sc.sky) { const hx = ox + dx * tt, hy = oy + dy * tt; if (hx > -0.9 && hx < 0.9 && hy > 0.9 && hy < 2.0) em = 2; }
        }
      }
      if (t === 1e9) break;
      // emitters seen directly or in a mirror (after a diffuse bounce they were already counted below)
      if (em === 1) { if (spec) { lr += tr * sc.light[0]; lg += tg * sc.light[1]; lb += tb * sc.light[2]; } break; }
      if (em === 2) { if (spec) { lr += tr * 3.2 * sc.sky; lg += tg * 3.8 * sc.sky; lb += tb * 4.6 * sc.sky; } break; }
      ox += dx * t; oy += dy * t; oz += dz * t;
      if (!mir) {
        // next-event estimation: aim one shadow ray at the ceiling light (and the window)
        let f = direct(ox, oy, oz, nx, ny, nz, -0.65 + 1.3 * rnd(), Y1, -1.3 + 1.2 * rnd(), 0, -1, 0, 1.56);
        lr += tr * cr * sc.light[0] * f; lg += tg * cg * sc.light[1] * f; lb += tb * cb * sc.light[2] * f;
        if (sc.sky) {
          f = direct(ox, oy, oz, nx, ny, nz, -0.9 + 1.8 * rnd(), 0.9 + 1.1 * rnd(), Z0, 0, 0, 1, 1.98);
          lr += tr * cr * 3.2 * sc.sky * f; lg += tg * cg * 3.8 * sc.sky * f; lb += tb * cb * 4.6 * sc.sky * f;
        }
      }
      spec = !!mir;
      tr *= cr; tg *= cg; tb *= cb;
      if (mir) {
        const dn = dx * nx + dy * ny + dz * nz;
        dx -= 2 * dn * nx; dy -= 2 * dn * ny; dz -= 2 * dn * nz;
      } else {
        // cosine-weighted direction around the normal
        const r1 = 2 * Math.PI * rnd(), r2 = rnd(), r2s = Math.sqrt(r2);
        const ux = Math.abs(nx) > 0.1 ? 0 : 1, uy = Math.abs(nx) > 0.1 ? 1 : 0;
        let ax = uy * nz, ay = -ux * nz, az = ux * ny - uy * nx;
        const al = Math.hypot(ax, ay, az); ax /= al; ay /= al; az /= al;
        const bx = ny * az - nz * ay, by = nz * ax - nx * az, bz = nx * ay - ny * ax;
        const c1 = Math.cos(r1) * r2s, c2 = Math.sin(r1) * r2s, c3 = Math.sqrt(1 - r2);
        dx = ax * c1 + bx * c2 + nx * c3; dy = ay * c1 + by * c2 + ny * c3; dz = az * c1 + bz * c2 + nz * c3;
      }
      if (b > 2) { const pr = Math.max(tr, tg, tb); if (rnd() > pr) break; tr /= pr; tg /= pr; tb /= pr; }
    }
    return [lr, lg, lb];
  }
  let iters = 0, passes = 0, lastPost = 0;
  const post = (done) => {
    const rgba = new Uint8ClampedArray(rows.length * w * 4);
    for (let p = 0, q = 0; p < rows.length * w; p++, q += 4) {
      for (let c = 0; c < 3; c++) {
        let v = sums[p * 3 + c] / Math.max(1, passes) * 0.9;
        v = v / (1 + v);
        rgba[q + c] = 255 * Math.pow(v, 1 / 2.2);
      }
      rgba[q + 3] = 255;
    }
    postMessage({ k, rows, rgba, iters, passes, done }, [rgba.buffer]);
  };
  while (iters < budget) {
    for (let ri = 0; ri < rows.length; ri++) {
      const py = ty + rows[ri];
      for (let px = 0; px < w; px++) {
        const u = ((tx + px + rnd()) / W * 2 - 1) * fov * asp, v = (1 - (py + rnd()) / H * 2) * fov;
        let dx = u, dy = v - 0.08, dz = -1;
        const l = Math.hypot(dx, dy, dz); dx /= l; dy /= l; dz /= l;
        const c = trace(0, camY, camZ, dx, dy, dz);
        const o = (ri * w + px) * 3;
        sums[o] += c[0]; sums[o + 1] += c[1]; sums[o + 2] += c[2];
      }
    }
    iters += rows.length * w;
    passes++;
    const now = Date.now();
    if (now - lastPost > 250) { lastPost = now; post(false); }
  }
  post(true);
};
`;

