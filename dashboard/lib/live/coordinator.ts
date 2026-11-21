import os from "node:os";
import {
  COLS,
  IMG_H,
  IMG_W,
  LAPTOP_WATTS,
  NODE_COLORS,
  ROWS,
  SIZES,
  TANK,
  TILE_H,
  TILE_W,
  VIEWS,
  houseFor,
  type Assignment,
  type BeatReply,
  type LiveEvent,
  type LiveJob,
  type LiveNode,
  type LiveState,
  type SizeKey,
} from "./shared";

/*
 * In-memory coordinator on the operator's laptop. One Node process, synchronous handlers, so no locking.
 * Kept on globalThis so every route bundle and every dev reload sees the same state.
 */

const OFFLINE_AFTER_MS = 6000;

type NodeRec = LiveNode & { lastSeen: number; abort: boolean };
type Store = {
  nodes: Map<string, NodeRec>;
  jobs: LiveJob[];
  events: LiveEvent[];
  images: Map<string, Buffer>; // `${job}:${tile}` → PNG or JPEG bytes
  imageTypes: Map<string, string>;
  lastTick: number;
  nextJob: number;
};

const g = globalThis as unknown as { __dhLive?: Store };
function store(): Store {
  if (!g.__dhLive)
    g.__dhLive = {
      nodes: new Map(),
      jobs: [],
      events: [],
      images: new Map(),
      imageTypes: new Map(),
      lastTick: Date.now(),
      nextJob: 1,
    };
  return g.__dhLive;
}

function log(s: Store, text: string, tone: LiveEvent["tone"] = "ink") {
  s.events.unshift({ at: Date.now(), text, tone });
  if (s.events.length > 60) s.events.length = 60;
}

const short = (n: NodeRec) => n.city;

/** Hand a node's running tile back to the queue. */
function release(s: Store, n: NodeRec, why: string) {
  if (!n.current) return;
  const job = s.jobs.find((j) => j.id === n.current!.jobId);
  const tile = job?.tiles[n.current.tile];
  if (tile && tile.state === "running" && tile.node === n.id) {
    tile.state = "pending";
    tile.node = null;
    tile.progress = 0;
    tile.restarts++;
    log(s, `Tile ${tile.i + 1} handed back by ${short(n)} (${why}), back in the queue`, "amber");
  }
  n.current = null;
}

/** Advance the tank simulation and liveness checks to now. */
function tick(s: Store) {
  const now = Date.now();
  const dt = Math.min(5, (now - s.lastTick) / 1000);
  s.lastTick = now;
  for (const n of s.nodes.values()) {
    if (n.state === "offline") continue;
    if (now - n.lastSeen > OFFLINE_AFTER_MS) {
      n.state = "offline";
      log(s, `${short(n)} stopped answering`, "alarm");
      release(s, n, "offline");
      continue;
    }
    const computing = n.current !== null;
    if (computing) {
      n.busySec += dt;
      n.heatWh += (LAPTOP_WATTS * dt) / 3600;
    }
    n.tank = Math.max(0, Math.min(100, n.tank + (computing ? TANK.risePerSec : 0) * dt - TANK.drainPerSec * dt));
    if (n.state !== "full" && n.tank >= 100) {
      n.state = "full";
      log(s, `${short(n)}: tank full, server paused`, "teal");
      if (n.current) {
        n.abort = true;
        release(s, n, "tank full");
      }
    } else if (n.state === "full" && n.tank <= TANK.resumeAt) {
      n.state = "idle";
      log(s, `${short(n)}: tank at ${Math.round(n.tank)} %, taking work again`, "rust");
    } else if (n.state !== "full") {
      n.state = n.current ? "running" : "idle";
    }
  }
}

function nextTile(s: Store) {
  for (const job of s.jobs) {
    if (job.doneAt) continue;
    const tile = job.tiles.find((t) => t.state === "pending");
    if (tile) return { job, tile };
  }
  return null;
}

/* ----------------------------------- API ----------------------------------- */

export function beat(input: {
  id: string;
  cores?: number;
  rate?: number;
  jobId?: number;
  tile?: number;
  progress?: number;
}): BeatReply {
  const s = store();
  tick(s);
  const now = Date.now();
  let n = s.nodes.get(input.id);
  if (!n) {
    const h = houseFor(input.id);
    n = {
      id: input.id,
      name: h.name,
      city: h.city,
      color: NODE_COLORS[s.nodes.size % NODE_COLORS.length],
      state: "idle",
      tank: 35 + Math.random() * 20,
      cores: input.cores ?? 0,
      rate: 0,
      busySec: 0,
      heatWh: 0,
      tilesDone: 0,
      current: null,
      lastSeen: now,
      abort: false,
    };
    s.nodes.set(n.id, n);
    log(s, `${n.name} joined the fleet (${n.cores} cores)`, "rust");
  } else if (n.state === "offline") {
    n.state = "idle";
    log(s, `${short(n)} is back online`, "rust");
  }
  n.lastSeen = now;
  if (input.cores) n.cores = input.cores;
  if (input.rate) n.rate = input.rate;

  // The node's view of its work; the coordinator's view wins.
  if (n.current && input.jobId === n.current.jobId && input.tile === n.current.tile) {
    n.current.progress = input.progress ?? n.current.progress;
    const job = s.jobs.find((j) => j.id === n!.current!.jobId);
    if (job) job.tiles[n.current.tile].progress = n.current.progress;
  }
  let abort = n.abort;
  n.abort = false;
  // Node says it is working on something we no longer gave it: stop it.
  if (input.jobId !== undefined && (!n.current || n.current.jobId !== input.jobId || n.current.tile !== input.tile)) abort = true;
  // Node lost its work (reload): free the tile.
  if (input.jobId === undefined && n.current) release(s, n, "restarted");

  let assign: Assignment | null = null;
  if (n.state !== "full" && !n.current) {
    const next = nextTile(s);
    if (next) {
      const { job, tile } = next;
      tile.state = "running";
      tile.node = n.id;
      tile.progress = 0;
      n.current = { jobId: job.id, tile: tile.i, progress: 0, since: now };
      n.state = "running";
      assign = {
        jobId: job.id,
        tile: tile.i,
        x: (tile.i % COLS) * TILE_W,
        y: Math.floor(tile.i / COLS) * TILE_H,
        w: TILE_W,
        h: TILE_H,
        view: job.view,
        budget: SIZES[job.size].giga * 1e9,
      };
      log(s, `Tile ${tile.i + 1} → ${short(n)} (needs heat, tank ${Math.round(n.tank)} %)`, "ink");
    }
  }
  return {
    state: n.state,
    tank: n.tank,
    tilesDone: n.tilesDone,
    heatWh: n.heatWh,
    color: n.color,
    name: n.name,
    assign,
    abort,
  };
}

function decode(dataUrl: string) {
  const m = /^data:(image\/(?:png|jpeg));base64,(.+)$/.exec(dataUrl);
  return m ? { type: m[1], buf: Buffer.from(m[2], "base64") } : null;
}

/** Live preview of a tile in progress. */
export function preview(input: { id: string; jobId: number; tile: number; image: string }) {
  const s = store();
  const n = s.nodes.get(input.id);
  if (!n?.current || n.current.jobId !== input.jobId || n.current.tile !== input.tile) return;
  const img = decode(input.image);
  const job = s.jobs.find((j) => j.id === input.jobId);
  if (!img || !job) return;
  const key = `${job.id}:${input.tile}`;
  s.images.set(key, img.buf);
  s.imageTypes.set(key, img.type);
  job.tiles[input.tile].v++;
}

export function done(input: { id: string; jobId: number; tile: number; image: string; ms: number }) {
  const s = store();
  tick(s);
  const n = s.nodes.get(input.id);
  if (!n?.current || n.current.jobId !== input.jobId || n.current.tile !== input.tile) return { ok: false };
  const job = s.jobs.find((j) => j.id === input.jobId);
  const img = decode(input.image);
  if (!job || !img) return { ok: false };
  const key = `${job.id}:${input.tile}`;
  s.images.set(key, img.buf);
  s.imageTypes.set(key, img.type);
  const tile = job.tiles[input.tile];
  tile.state = "done";
  tile.progress = 1;
  tile.v++;
  n.current = null;
  n.tilesDone++;
  if (n.state === "running") n.state = "idle";
  log(s, `Tile ${tile.i + 1} back from ${short(n)} in ${(input.ms / 1000).toFixed(1)} s`, "rust");
  if (job.tiles.every((t) => t.state === "done")) {
    job.doneAt = Date.now();
    log(s, `Job #${job.id} complete: ${job.tiles.length} tiles in ${((job.doneAt - job.createdAt) / 1000).toFixed(0)} s`, "teal");
  }
  return { ok: true };
}

export function control(input: { op: string; id?: string; size?: SizeKey }) {
  const s = store();
  tick(s);
  const n = input.id ? s.nodes.get(input.id) : undefined;
  switch (input.op) {
    case "submit": {
      const size: SizeKey = input.size && input.size in SIZES ? input.size : "M";
      const id = s.nextJob++;
      const view = VIEWS[(id - 1) % VIEWS.length];
      s.jobs.push({
        id,
        size,
        view,
        createdAt: Date.now(),
        doneAt: null,
        tiles: Array.from({ length: COLS * ROWS }, (_, i) => ({ i, state: "pending", node: null, progress: 0, v: 0, restarts: 0 })),
      });
      // Keep memory small: drop images of all but the last few jobs.
      while (s.jobs.length > 4) {
        const old = s.jobs.shift()!;
        for (let i = 0; i < COLS * ROWS; i++) s.images.delete(`${old.id}:${i}`);
      }
      log(s, `Job #${id} submitted: ${view.name}, ${COLS * ROWS} tiles, ${SIZES[size].label.toLowerCase()}`, "ink");
      break;
    }
    case "full":
      if (n && n.state !== "offline") {
        n.tank = 100;
        tick(s);
      }
      break;
    case "shower":
      if (n && n.state !== "offline") {
        n.tank = Math.max(0, n.tank - TANK.showerDrop);
        log(s, `${short(n)}: hot shower, tank down to ${Math.round(n.tank)} %`, "amber");
        tick(s);
      }
      break;
    case "forget":
      if (n) {
        release(s, n, "removed");
        s.nodes.delete(n.id);
      }
      break;
    case "reset":
      g.__dhLive = undefined;
      break;
  }
  return state(null);
}

export function state(host: string | null): LiveState {
  const s = store();
  tick(s);
  return {
    now: Date.now(),
    nodes: [...s.nodes.values()].map((n) => {
      const { lastSeen, abort, ...pub } = n;
      void lastSeen;
      void abort;
      return pub;
    }),
    jobs: s.jobs,
    events: s.events,
    joinBase: host ? joinBase(host) : null,
  };
}

export function image(jobId: number, tile: number) {
  const s = store();
  const key = `${jobId}:${tile}`;
  const buf = s.images.get(key);
  return buf ? { buf, type: s.imageTypes.get(key) ?? "image/png" } : null;
}

/** The address friends type in: this laptop's LAN IP and the port the dashboard is served on. */
function joinBase(host: string) {
  const port = host.includes(":") ? host.split(":").pop() : "80";
  const ifs = os.networkInterfaces();
  const ips: string[] = [];
  for (const [name, list] of Object.entries(ifs)) {
    for (const a of list ?? []) {
      if (a.family === "IPv4" && !a.internal && !name.startsWith("utun") && !name.startsWith("bridge")) ips.push(a.address);
    }
  }
  const ip = ips.find((a) => a.startsWith("192.168.") || a.startsWith("172.20.10.")) ?? ips[0];
  return ip ? `http://${ip}:${port}` : null;
}

export const GEOMETRY = { IMG_W, IMG_H, COLS, ROWS, TILE_W, TILE_H };
