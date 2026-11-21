/*
 * Live demo: real laptops as DigitalHeat servers.
 * Shared between the coordinator (route handlers) and the browser pages.
 *
 * The workload is a fractal render split into tiles. Each tile has a fixed compute budget
 * (Mandelbrot iterations); the house laptop refines the tile pass by pass until the budget
 * is spent, so every tile is real CPU work of a known size whatever part of the image it covers.
 */

export const IMG_W = 1536;
export const IMG_H = 864;
export const COLS = 6;
export const ROWS = 4;
export const TILE_W = IMG_W / COLS; // 256
export const TILE_H = IMG_H / ROWS; // 216

/** Job sizes, in giga-iterations per tile. M is about 5 s per tile on a recent 8-core laptop. */
export const SIZES = {
  S: { label: "Small", giga: 4 },
  M: { label: "Medium", giga: 12 },
  L: { label: "Large", giga: 30 },
} as const;
export type SizeKey = keyof typeof SIZES;

export type View = { name: string; cx: number; cy: number; span: number; maxIter: number };
export const VIEWS: View[] = [
  { name: "Seahorse valley", cx: -0.7453, cy: 0.1127, span: 0.012, maxIter: 3000 },
  { name: "Elephant valley", cx: 0.2925, cy: 0.0149, span: 0.012, maxIter: 3000 },
  { name: "Needle tendril", cx: -1.7499, cy: 0.0, span: 0.0012, maxIter: 3000 },
];

/** Houses the friends' laptops play. Any other id works too and gets a generic name. */
export const HOUSES: Record<string, { name: string; city: string }> = {
  basel: { name: "Basel · House 1", city: "Basel" },
  zuerich: { name: "Zürich · House 2", city: "Zürich" },
  bern: { name: "Bern · House 3", city: "Bern" },
  chur: { name: "Chur · House 4", city: "Chur" },
};
export function houseFor(id: string) {
  return HOUSES[id] ?? { name: id.charAt(0).toUpperCase() + id.slice(1), city: id };
}
export const NODE_COLORS = ["#c0653a", "#5fa8b0", "#f2a65a", "#8f4423", "#2a2926"];

/** Simulated hot-water tank, sped up for the demo (percent per second). */
export const TANK = {
  risePerSec: 1.2, // while the laptop computes
  drainPerSec: 0.4, // the household uses hot water all the time
  resumeAt: 85, // a full tank takes work again below this level
  showerDrop: 40,
};
/** Nominal laptop draw under full load, used for the heat estimate. */
export const LAPTOP_WATTS = 45;

export type NodeState = "running" | "idle" | "full" | "offline";

export type Assignment = {
  jobId: number;
  tile: number;
  x: number;
  y: number;
  w: number;
  h: number;
  view: View;
  budget: number; // iterations
};

export type LiveNode = {
  id: string;
  name: string;
  city: string;
  color: string;
  state: NodeState;
  tank: number;
  cores: number;
  rate: number; // iterations per second, last reported
  busySec: number;
  heatWh: number;
  tilesDone: number;
  current: { jobId: number; tile: number; progress: number; since: number } | null;
};

export type TileState = "pending" | "running" | "done";
export type LiveTile = {
  i: number;
  state: TileState;
  node: string | null;
  progress: number;
  v: number; // image version, bumps when a new preview or the final image arrives
  restarts: number;
};

export type LiveJob = {
  id: number;
  size: SizeKey;
  view: View;
  tiles: LiveTile[];
  createdAt: number;
  doneAt: number | null;
};

export type LiveEvent = { at: number; text: string; tone: "rust" | "teal" | "amber" | "ink" | "alarm" };

export type LiveState = {
  now: number;
  nodes: LiveNode[];
  jobs: LiveJob[];
  events: LiveEvent[];
  joinBase: string | null;
};

export type BeatReply = {
  state: NodeState;
  tank: number;
  tilesDone: number;
  heatWh: number;
  color: string;
  name: string;
  assign: Assignment | null;
  abort: boolean;
};

/*
 * Worker source. Kept as a string so the page can start workers from a Blob URL without bundler setup.
 * Each worker renders the rows y ≡ k (mod n) of one tile, one jittered sample per pixel per pass,
 * until it has spent its share of the tile's iteration budget.
 */
export const WORKER_SRC = `
const STOPS = [[20,20,18],[143,68,35],[192,101,58],[242,166,90],[246,243,236],[95,168,176],[20,20,18]];
function palette(t, out, o) {
  t = t - Math.floor(t);
  const f = t * (STOPS.length - 1), i = Math.floor(f), u = f - i;
  const a = STOPS[i], b = STOPS[i + 1];
  out[o] += a[0] + (b[0] - a[0]) * u;
  out[o + 1] += a[1] + (b[1] - a[1]) * u;
  out[o + 2] += a[2] + (b[2] - a[2]) * u;
}
onmessage = (e) => {
  const { k, n, a, W, H, budget, maxPasses } = e.data;
  const { x: tx, y: ty, w, h, view } = a;
  const rows = [];
  for (let r = k; r < h; r += n) rows.push(r);
  const sums = new Float32Array(rows.length * w * 3);
  const spanY = view.span * H / W;
  let seed = (k + 1) * 2654435761 >>> 0;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  let iters = 0, passes = 0, lastPost = 0;
  const post = (done) => {
    const rgba = new Uint8ClampedArray(rows.length * w * 4);
    for (let p = 0, q = 0; p < rows.length * w; p++, q += 4) {
      rgba[q] = sums[p * 3] / passes; rgba[q + 1] = sums[p * 3 + 1] / passes; rgba[q + 2] = sums[p * 3 + 2] / passes; rgba[q + 3] = 255;
    }
    postMessage({ k, rows, rgba, iters, passes, done }, [rgba.buffer]);
  };
  while (iters < budget && passes < maxPasses) {
    for (let ri = 0; ri < rows.length; ri++) {
      const py = ty + rows[ri];
      for (let px = 0; px < w; px++) {
        const cx = view.cx + ((tx + px + rnd()) / W - 0.5) * view.span;
        const cy = view.cy + ((py + rnd()) / H - 0.5) * spanY;
        let x = 0, y = 0, x2 = 0, y2 = 0, i = 0;
        while (x2 + y2 <= 256 && i < view.maxIter) { y = 2 * x * y + cy; x = x2 - y2 + cx; x2 = x * x; y2 = y * y; i++; }
        iters += i;
        const o = (ri * w + px) * 3;
        if (i >= view.maxIter) { sums[o] += 20; sums[o + 1] += 20; sums[o + 2] += 18; }
        else palette(Math.sqrt(i + 1 - Math.log2(Math.log2(x2 + y2) / 2)) * 0.11, sums, o);
      }
    }
    passes++;
    const now = Date.now();
    if (now - lastPost > 250) { lastPost = now; post(false); }
  }
  post(true);
};
`;
