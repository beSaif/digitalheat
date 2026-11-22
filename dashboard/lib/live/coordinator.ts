import { readFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { ROOT, runPython } from "@/lib/server/python";
import {
  CONDITIONS,
  COLS,
  DEVICE_WATTS,
  AI_PART,
  EMBED_ITEMS,
  KIND_NAME,
  PARTS,
  PRODUCTS,
  QUALITY,
  RERANK_ITEMS,
  SCENES,
  TANK_RESUME,
  TANK_SPEED,
  TILE_H,
  TILE_W,
  X_HOUSE,
  cleanName,
  baseColorFor,
  colorFor,
  personRack,
  type Assignment,
  type BeatReply,
  type CondKey,
  type Conditions,
  type DayData,
  type DayHour,
  type DaySite,
  type LiveEvent,
  type LiveMove,
  type LiveNode,
  type LiveState,
  type Hit,
  type Job,
  type JobKind,
  type Pricing,
  type SceneKey,
} from "./shared";

/*
 * Live-demo coordinator, in memory on the operator's laptop (one Node process).
 *
 * Roles. Hosts: everyone who joins adds their own building with a rack (a server only runs where its
 * heat is used). Customer: the jury orders every job on /client: a 3D rendering, AI embeddings or AI
 * reranking. DigitalHeat (this file): splits each job into parts and hands them only to racks whose
 * building needs heat. Nothing runs that the customer did not order.
 *
 * Every building has enough servers to cover 100 % of its heat demand (no heat pump, no backup heater):
 * the scheduler sizes each rack from the building's highest hour of the year, with each building type sized
 * against the house (X_HOUSE in shared.ts: a pharma lab is 5 houses, a hospital 4).
 *
 * Which racks have heat is the DigitalHeat scheduler's decision (scheduler/day.py, the yearly balance's
 * code) for one moment: now (today's date and hour with 2025 weather), a January morning or a July
 * afternoon. It is decided again when someone joins or the operator changes the moment; there is no
 * clock running. The operator's own sites have no phones: the operator screen renders their share.
 */

/** Prices from the business case's files: AWS for the same 1 kW server, plus our premium. */
function readPricing(): Pricing {
  try {
    const p = JSON.parse(readFileSync(path.join(ROOT, "data", "prices_2026.json"), "utf8"));
    const b = JSON.parse(readFileSync(path.join(ROOT, "data", "business_assumptions.json"), "utf8"));
    const fx = p.usd_chf.value;
    const spot = p.cloud_same_server.spot_usd_h * fx;
    const premium = b.compute_premium.value;
    return { sellChfH: spot * (1 + premium), spotChfH: spot, onDemandChfH: p.cloud_same_server.on_demand_usd_h * fx, premium, refServer: p.reference_server.value };
  } catch {
    return { sellChfH: 3.42, spotChfH: 2.74, onDemandChfH: 9.45, premium: 0.25, refServer: "2x AMD EPYC 9654 (192 cores)" };
  }
}
const PRICING = readPricing();

/* SciFact (5,183 scientific abstracts, 1,109 claims), the corpus of the measured workloads; exported from data/raw/scifact. */
type Corpus = { docs: [string, string, string][]; queries: string[]; words: Set<string>[]; df: Map<string, number> };
let corpus: Corpus | null = null;
const STOP = new Set("the and for with that this from are was were has have had not but its into than then there their which what when who how does can may also more most such these those been being".split(" "));
const words = (t: string) => t.toLowerCase().match(/[a-z0-9]{3,}/g)?.filter((w) => !STOP.has(w)) ?? [];
function getCorpus(): Corpus {
  if (!corpus) {
    const raw = JSON.parse(readFileSync(path.join(process.cwd(), "data", "scifact.json"), "utf8")) as { docs: [string, string, string][]; queries: string[] };
    const ws = raw.docs.map((d) => new Set(words(`${d[1]} ${d[2]}`)));
    const df = new Map<string, number>();
    for (const w of ws) for (const x of w) df.set(x, (df.get(x) ?? 0) + 1);
    corpus = { ...raw, words: ws, df };
  }
  return corpus;
}
const docText = (c: Corpus, i: number) => `${c.docs[i][1]} ${c.docs[i][2]}`.trim();
/** First stage of a search: the abstracts sharing the most (rare) words with the question; the AI then reranks them. */
function candidates(c: Corpus, query: string, k: number) {
  const q = [...new Set(words(query))];
  const n = c.docs.length;
  const scored = c.words.map((w, i) => ({ i, s: q.reduce((a, x) => a + (w.has(x) ? Math.log(n / (c.df.get(x) ?? n)) : 0), 0) }));
  scored.sort((a, b) => b.s - a.s || a.i - b.i);
  return scored.slice(0, k).map((x) => x.i);
}

const OFFLINE_AFTER_MS = 6000;
const SERVER_KW = 0.8; // heat recovered per running 1 kW server (scheduler.core REC)
const PLAN_DEBOUNCE_MS = 500;
const KEEP_JOBS = 12;
/** A paused part waits this long for its rack's checkpoint, then goes back to the queue without one. */
const SAVE_WAIT_MS = 4000;
const RENDER_SAMPLES = QUALITY.draft.spp * TILE_W * TILE_H;
const pct = (x: number) => `${Math.round(x * 100)} %`;

type NodeRec = LiveNode & {
  lastSeen: number;
  abort: boolean;
  index: number; // join order: the rack's number (people only)
  rackId: string; // a person's rack, or the operator site this base node renders for
  /** a device stands for its whole rack: its servers on as a share of the biggest rack's full size (biggestRack) */
  duty: number;
  restUntil: number;
  /** its rack was switched off mid-part: the next reply asks it to save its progress */
  checkpoint: boolean;
  /** the last time this rack's work moved, in words (shown on the phone) */
  note: string | null;
};
type Store = {
  nodes: Map<string, NodeRec>;
  events: LiveEvent[];
  base: DaySite[]; // the operator's sites
  cond: Conditions | null;
  plan: DayData | null; // one hour: the scheduler's decision for the moment
  planning: boolean;
  planAgain: boolean;
  planTimer: ReturnType<typeof setTimeout> | null;
  jobs: Job[];
  images: Map<string, Buffer>;
  results: Map<string, number[] | number[][]>; // AI parts: vectors or scores
  docs: Map<number, number[]>; // AI jobs: the abstracts (corpus indices) in item order
  tanks: Map<string, number>; // live tank per site id (kWh): starts at the scheduler's level, then follows the jobs
  tankAt: number;
  /** sites whose tank reached 100 %: rack paused until the tank cools to TANK_RESUME */
  full: Set<string>;
  /** saved progress of paused parts, per "job:part": samples traced (render) or the values of the items done (AI) */
  ckpt: Map<string, { done: number; values?: (number[] | number)[] }>;
  moves: LiveMove[];
  nextEmbed: number;
  nextJob: number;
  joined: number;
  totals: { tiles: number; drops: number; moved: number; paused: number; resumed: number };
};

const g = globalThis as unknown as { __dhLive4?: Store };
function fresh(): Store {
  return {
    nodes: new Map(),
    events: [],
    base: [],
    cond: null,
    plan: null,
    planning: false,
    planAgain: false,
    planTimer: null,
    jobs: [],
    images: new Map(),
    results: new Map(),
    docs: new Map(),
    tanks: new Map(),
    tankAt: 0,
    full: new Set(),
    ckpt: new Map(),
    moves: [],
    nextEmbed: 0,
    nextJob: 1,
    joined: 0,
    totals: { tiles: 0, drops: 0, moved: 0, paused: 0, resumed: 0 },
  };
}
function store() {
  const s = (g.__dhLive4 ??= fresh());
  s.tanks ??= new Map(); // a store from before the live tanks (dev reload)
  s.full ??= new Set();
  s.ckpt ??= new Map();
  s.moves ??= [];
  s.totals.paused ??= 0;
  s.totals.resumed ??= 0;
  return s;
}

function log(s: Store, text: string, tone: LiveEvent["tone"] = "ink") {
  s.events.unshift({ at: Date.now(), text, tone });
  if (s.events.length > 80) s.events.length = 80;
}

/** "Hospital", or "Anna's greenhouse" for a person's rack */
const siteName = (x: DaySite | undefined) => (!x ? "?" : x.person ? `${x.person}'s ${(KIND_NAME[x.kind] ?? x.kind).toLowerCase()}` : x.name);

/* --------------------------------- the fleet --------------------------------- */

const people = (s: Store) => [...s.nodes.values()].filter((n) => !n.base).sort((a, b) => a.index - b.index);

/** The operator's sites, then every person's rack. */
function fleet(s: Store): DaySite[] {
  return [...s.base, ...people(s).map((n) => ({ ...personRack(n.index, n.name, n.id), tank_kwh: 0 }))];
}
const sites = (s: Store) => s.plan?.sites ?? fleet(s);
/*
 * The tanks are live. At the chosen moment every tank starts a little below where the scheduler left it
 * in scheduler/day.py (the year run up to that hour): in a real building the tank is rarely full, someone
 * just took a long shower or the heating ran hard. The dip is 0 to TANK_DIP_H hours of the building's own
 * demand, so a house in July is short of a few minutes of hot water while a pharma lab is short of real
 * heat. From then on each building draws its heat demand from its tank, and the
 * tank gets the heat of the servers that run the customer's jobs: no job, no heat. A building switches on
 * as many servers as cover its demand plus refilling its tank within an hour (at most all of them).
 * Demand stays that hour's; the tanks run at TANK_SPEED.
 *
 * A tank that reaches 100 % switches its rack off (a charging band, like a buffer tank's top and bottom
 * sensors) until it has cooled to TANK_RESUME. The part the rack was working on is paused: the device saves
 * its progress (a checkpoint) and the part continues on another rack whose building needs heat, without
 * repeating the work already done.
 */
const wantOn = (site: DaySite, x: DayHour["sites"][number], soc: number) =>
  x.down ? 0 : Math.max(0, Math.min(site.servers, Math.ceil((x.demand + Math.max(0, site.tank_kwh - soc)) / SERVER_KW - 1e-9)));
const plannedHour = (s: Store): DayHour | null => s.plan?.hours[0] ?? null;
/** A tank starts at most this many hours of its building's demand below the scheduler's level. */
const TANK_DIP_H = 2;
/** A site's live tank; the first time, a random start (kept until the operator picks a moment again). */
function tankOf(s: Store, site: DaySite, x: DayHour["sites"][number]) {
  let soc = s.tanks.get(site.id);
  if (soc === undefined) {
    soc = Math.max(0, Math.min(x.soc, site.tank_kwh) - Math.random() * TANK_DIP_H * x.demand);
    s.tanks.set(site.id, soc);
  }
  return soc;
}
/** The moment with live tanks: soc, and the servers each building switches on for it. */
function hour(s: Store): DayHour | null {
  const h = plannedHour(s);
  if (!h) return null;
  const all = sites(s);
  return {
    ...h,
    sites: h.sites.map((x, i) => {
      const site = all[i];
      if (!site) return x;
      const soc = tankOf(s, site, x);
      const on = s.full.has(site.id) ? 0 : wantOn(site, x, soc);
      return { ...x, soc, room: Math.max(0, site.tank_kwh - soc), running: on, permit: on, limit: on };
    }),
  };
}
/** Move the tanks forward to now: heat in from servers running a customer's job, heat out to the building. */
function stepTanks(s: Store) {
  const h = plannedHour(s);
  const now = Date.now();
  const dtH = (Math.min(5000, now - (s.tankAt || now)) / 3_600_000) * TANK_SPEED;
  s.tankAt = now;
  if (!h || dtH <= 0) return;
  const all = sites(s);
  const queued = s.jobs.some((j) => j.tiles.some((t) => t.state === "pending"));
  all.forEach((site, i) => {
    const x = h.sites[i];
    if (!x) return;
    const soc = tankOf(s, site, x);
    const n = s.nodes.get(site.node ?? `base-${site.id.toLowerCase()}`);
    const working = !!n && n.state === "running" && (!!n.current || queued);
    const full = s.full.has(site.id);
    const heatIn = working && !full ? wantOn(site, x, soc) * SERVER_KW : 0;
    const next = Math.max(0, Math.min(site.tank_kwh, soc + (heatIn - x.demand) * dtH));
    s.tanks.set(site.id, next);
    if (site.tank_kwh <= 0) return;
    if (!full && heatIn > 0 && next >= site.tank_kwh - 1e-6) {
      s.full.add(site.id);
      log(s, `${siteName(site)}: tank 100 %, rack paused until it cools to ${pct(TANK_RESUME)}`, "teal");
    } else if (full && next <= TANK_RESUME * site.tank_kwh) {
      s.full.delete(site.id);
      log(s, `${siteName(site)}: tank down to ${pct(TANK_RESUME)}, rack back on`, "rust");
    }
  });
}

/** The moment: day of the year (the model's 365-day year) and hour. "now" is today in Basel. */
function moment(key: CondKey): { day: number; hour: number; label: string } {
  if (key !== "now") {
    const c = CONDITIONS[key];
    return { day: c.day, hour: c.hour, label: c.label };
  }
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Zurich", year: "numeric", month: "numeric", day: "numeric", hour: "numeric", hourCycle: "h23" }).formatToParts(new Date());
  const get = (t: string) => Number(parts.find((p) => p.type === t)?.value);
  const m = get("month"),
    d = get("day");
  const doy = Math.round((Date.UTC(2025, m - 1, d) - Date.UTC(2025, 0, 1)) / 86_400_000); // 2025 has no 29 February
  return { day: Math.min(364, doy), hour: get("hour"), label: "Now" };
}

/* --------------------------------- planning --------------------------------- */

const planCache = new Map<string, Promise<DayData>>();

/** The scheduler's decision for the fleet at the chosen moment (one hour of scheduler/day.py). */
function decide(s: Store, key: CondKey): Promise<DayData> {
  const m = moment(key);
  const req = JSON.stringify({
    year: 2025,
    // no names: they are not the scheduler's business, and a renamed rack then reuses the cached decision
    sites: fleet(s).map(({ id, kind, lat, lon, servers }) => ({ id, kind, name: id, lat, lon, servers, x_house: X_HOUSE[kind] ?? 1 })),
    day: m.day,
    hour: m.hour,
    hours: 1,
    sizing: "peak", // every building has enough servers for 100 % of its heat: no heat pump, no backup heater
  });
  if (!planCache.has(req)) {
    if (planCache.size > 40) planCache.delete(planCache.keys().next().value!);
    const p = runPython("scheduler.day", ["--stdin"], req).then((out) => JSON.parse(out) as DayData);
    p.catch(() => planCache.delete(req));
    planCache.set(req, p);
  }
  return planCache.get(req)!.then((d) => {
    // names and devices are not the scheduler's business: put them back on the racks
    const byId = new Map(fleet(s).map((x) => [x.id, x]));
    return { ...d, sites: d.sites.map((x) => ({ ...x, person: byId.get(x.id)?.person, node: byId.get(x.id)?.node, name: byId.get(x.id)?.name ?? x.name })) };
  });
}

async function setConditions(s: Store, key: CondKey) {
  s.planning = true;
  try {
    const d = await decide(s, key);
    const m = moment(key);
    const before = onSet(s);
    if (s.cond?.key !== key) {
      s.tanks.clear(); // a new moment: tanks start from the scheduler's levels again
      s.full.clear();
      for (const n of s.nodes.values()) n.restUntil = 0; // and no rack keeps resting at the old moment's pace
    }
    s.plan = d;
    s.tankAt = Date.now();
    s.cond = { key, label: m.label, date: d.hours[0].date, hour: d.hours[0].hour };
    reportChanges(s, before);
  } finally {
    s.planning = false;
  }
}

/** Decide again for a changed fleet, in the background (a burst of joins decides once). */
function replan(s: Store) {
  if (!s.cond || s.planTimer) return;
  s.planTimer = setTimeout(async () => {
    s.planTimer = null;
    if (s.planning) {
      s.planAgain = true;
      return;
    }
    const key = s.cond?.key;
    if (!key) return;
    try {
      await setConditions(s, key);
    } catch (e) {
      log(s, `Scheduler failed: ${String((e as Error).message).slice(0, 120)}`, "alarm");
    } finally {
      if (s.planAgain) {
        s.planAgain = false;
        replan(s);
      }
    }
  }, PLAN_DEBOUNCE_MS);
}

/** Servers on per site id, to tell what changed after a new decision. */
function onSet(s: Store) {
  const h = hour(s);
  return new Map(sites(s).map((x, i) => [x.id, h ? Math.ceil(h.sites[i].running - 1e-9) : -1]));
}
function reportChanges(s: Store, before: Map<string, number>) {
  const h = hour(s);
  if (!h) return;
  sites(s).forEach((x, i) => {
    const now = Math.ceil(h.sites[i].running - 1e-9);
    const was = before.get(x.id);
    if (was === undefined || was === -1 || was === now) return;
    if (now === 0) log(s, `${siteName(x)}: no heat needed, rack switched off`, "teal");
    else if (was === 0) log(s, `${siteName(x)}: needs heat, ${now} of ${x.servers} servers on`, "rust");
  });
}

/* --------------------------------- one rack --------------------------------- */

function rackIndex(s: Store, n: NodeRec) {
  return sites(s).findIndex((x) => x.id === n.rackId);
}

/*
 * A device stands for its whole rack, so the work goes out in proportion to servers on, measured against
 * the biggest rack with all its servers on (racks are sized for the coldest hour of the year). On a
 * January morning nearly every server is on and the fleet works almost flat out; in July a pharma lab
 * with 39 of its 66 servers on works 59 % of the time and a house running 1 server for its hot water
 * takes 1 part for every 66, so the same order takes much longer. Less heat needed, less computing.
 */
function biggestRack(s: Store) {
  let top = 0;
  sites(s).forEach((site) => {
    const n = s.nodes.get(site.node ?? `base-${site.id.toLowerCase()}`);
    if (n && n.state !== "offline") top = Math.max(top, site.servers);
  });
  return top;
}

/** What the scheduler decided for this node's rack at the moment (h = hour(s)), in words. */
function placement(s: Store, n: NodeRec, top: number, h: DayHour | null) {
  const site = rackIndex(s, n);
  if (!h) return { site, on: 0, servers: 1, reason: "" };
  if (site < 0) return { site, on: 0, servers: 1, reason: "Adding your rack…" };
  const x = h.sites[site];
  const on = Math.ceil(x.running - 1e-9);
  const servers = sites(s)[site].servers;
  if (s.full.has(sites(s)[site].id)) return { site, on: 0, servers, reason: `Tank full (100 %): rack paused until it cools to ${pct(TANK_RESUME)}` };
  if (on > 0) {
    const what = on >= servers ? `all ${servers} servers on` : `${on} of ${servers} servers on`;
    const share = on < top ? `, so you take ${on} part${on === 1 ? "" : "s"} for every ${top} the biggest rack takes at full power` : "";
    return { site, on, servers, reason: `Needs heat: ${what}${share}` };
  }
  if (x.permit === 0 && x.room < 0.8) return { site, on, servers, reason: "Tank full: no heat needed" };
  if (x.permit === 0) return { site, on, servers, reason: "No heat needed right now" };
  if (x.limit === 0) return { site, on, servers, reason: "Saving tank room for a deadline job" };
  return { site, on, servers, reason: "No heat needed right now" };
}

/* --------------------------------- tiles --------------------------------- */

/**
 * The rack was switched off mid-part (its tank is full, or the moment changed): the part pauses and the
 * device is asked to save its progress; checkpoint() then hands it to the next rack that needs heat.
 */
function pause(s: Store, n: NodeRec) {
  const c = n.current;
  n.current = null;
  n.abort = true;
  if (!c) return;
  const tile = s.jobs.find((j) => j.id === c.jobId)?.tiles[c.chunk];
  if (!tile || tile.state !== "running" || tile.node !== n.id) return;
  tile.state = "paused";
  tile.pausedAt = Date.now();
  tile.from = n.id;
  n.checkpoint = true;
  s.totals.paused++;
}

/** A paused part whose rack never sent its checkpoint (it left): back to the queue, from its last checkpoint if any. */
function unstick(s: Store, now: number) {
  for (const job of s.jobs)
    for (const t of job.tiles)
      if (t.state === "paused" && now - (t.pausedAt ?? 0) > SAVE_WAIT_MS) {
        t.state = "pending";
        t.node = null;
        t.restarts++;
      }
}

const rackSite = (s: Store, n: NodeRec | undefined) => (n ? sites(s).find((x) => x.id === n.rackId) : undefined);

/** Put a node's tile back in the queue (it left, or its rack was switched off). */
function release(s: Store, n: NodeRec, why: string | null) {
  const c = n.current;
  n.current = null;
  if (!c) return;
  const job = s.jobs.find((j) => j.id === c.jobId);
  const tile = job?.tiles[c.chunk];
  if (!tile || tile.state !== "running" || tile.node !== n.id) return;
  tile.state = "pending";
  tile.node = null;
  tile.restarts++;
  s.totals.moved++;
  if (why) log(s, `${n.name} ${why}: part ${tile.i + 1} goes back to the queue`, "amber");
}

function nextTile(s: Store) {
  for (const job of s.jobs) {
    if (job.doneAt) continue;
    const tile = job.tiles.find((t) => t.state === "pending");
    if (tile) return { job, tile };
  }
  return null;
}

function goAway(s: Store, n: NodeRec, why: string) {
  n.state = "offline";
  s.totals.drops++;
  if (!n.base) log(s, `${n.name} ${why}`, "alarm");
  release(s, n, n.base ? null : "left");
}

function tick(s: Store) {
  stepTanks(s);
  const now = Date.now();
  unstick(s, now);
  const top = biggestRack(s);
  // the live hour once per tick: it copies every site, and a tick runs on every beat of every rack
  const h = hour(s);
  for (const n of s.nodes.values()) {
    if (n.state === "offline") continue;
    if (now - n.lastSeen > OFFLINE_AFTER_MS) {
      goAway(s, n, "stopped answering");
      continue;
    }
    const p = placement(s, n, top, h);
    n.site = p.site;
    n.reason = p.reason;
    n.state = !h || p.site < 0 ? "waiting" : p.on > 0 ? "running" : "off";
    n.duty = p.on > 0 ? Math.min(1, p.on / Math.max(p.on, top)) : 0;
    // the rack was switched off: its part pauses, is saved, and continues on a rack that needs heat
    if (n.current && n.state !== "running") pause(s, n);
  }
}

/* ----------------------------------- API ----------------------------------- */

export function beat(input: { id: string; name?: string; cores?: number; rate?: number; device?: string; jobId?: number; chunk?: number; progress?: number }): BeatReply {
  const s = store();
  const now = Date.now();
  const base = input.id.startsWith("base-");
  let n = s.nodes.get(input.id);
  const name = cleanName(input.name);
  if (!n) {
    n = {
      id: input.id,
      name: name || `Guest ${s.joined + 1}`,
      color: base ? baseColorFor([...s.nodes.values()].filter((x) => x.base).length) : colorFor(s.joined),
      device: input.device === "phone" ? "phone" : "laptop",
      state: "waiting",
      site: -1,
      base,
      reason: "",
      cores: input.cores ?? 0,
      rate: 0,
      chunks: 0,
      heatWh: 0,
      current: null,
      lastSeen: now,
      abort: false,
      index: base ? -1 : s.joined,
      rackId: base ? input.id.slice(5).toUpperCase() : `P-${s.joined + 1}`,
      duty: 0,
      restUntil: 0,
      checkpoint: false,
      note: null,
    };
    if (!base) {
      s.joined++;
      log(s, `${n.name} joined with a ${(KIND_NAME[personRack(n.index, n.name, n.id).kind] ?? "").toLowerCase()}`, "rust");
    }
    s.nodes.set(n.id, n);
    if (!base) replan(s);
  } else if (n.state === "offline") {
    n.state = "waiting";
    if (!base) log(s, `${n.name} is back`, "rust");
  }
  if (name && name !== n.name && !base) {
    n.name = name;
    const rack = s.plan?.sites.find((x) => x.id === n!.rackId);
    if (rack) rack.name = rack.person = name;
  }
  n.lastSeen = now;
  if (input.cores) n.cores = input.cores;
  if (input.rate) n.rate = input.rate;
  tick(s);

  // the node's view of its work; the coordinator's view wins
  if (n.current && input.jobId === n.current.jobId && input.chunk === n.current.chunk) n.current.progress = input.progress ?? n.current.progress;
  let abort = n.abort;
  const checkpoint = n.checkpoint;
  n.abort = false;
  n.checkpoint = false;
  if (input.jobId !== undefined && (!n.current || n.current.jobId !== input.jobId || n.current.chunk !== input.chunk)) abort = true;
  if (input.jobId === undefined && n.current) release(s, n, null); // reloaded: the tile goes back

  let assign: Assignment | null = null;
  if (n.state === "running" && !n.current && now >= n.restUntil) {
    const next = nextTile(s);
    if (next) {
      const { job, tile } = next;
      tile.state = "running";
      tile.node = n.id;
      job.startedAt ??= now;
      n.current = { jobId: job.id, chunk: tile.i, progress: 0, since: now };
      assign = {
        jobId: job.id,
        jobType: job.kind,
        chunk: tile.i,
        x: (tile.i % COLS) * TILE_W,
        y: Math.floor(tile.i / COLS) * TILE_H,
        w: TILE_W,
        h: TILE_H,
        scene: job.scene ?? "warm",
        budget: QUALITY.draft.spp * TILE_W * TILE_H,
      };
      const ck = s.ckpt.get(`${job.id}:${tile.i}`);
      const from = tile.from ? s.nodes.get(tile.from) : undefined;
      if (job.kind !== "render") {
        const c = getCorpus();
        const docs = s.docs.get(job.id) ?? [];
        const k = ck?.values?.length ?? 0; // items already done before the pause
        assign.texts = docs.slice(tile.i * AI_PART + k, (tile.i + 1) * AI_PART).map((d) => docText(c, d));
        assign.query = job.query;
        if (k > 0) assign.resume = { done: k, total: AI_PART, v: tile.v };
      } else if (ck && ck.done > 0) {
        assign.budget = Math.max(TILE_W * TILE_H, RENDER_SAMPLES - ck.done);
        assign.resume = { done: ck.done, total: RENDER_SAMPLES, v: tile.v };
      }
      // a paused part continues here: show where it came from
      if (from && from.id !== n.id && tile.saved) {
        const a = rackSite(s, from),
          b = rackSite(s, n);
        if (a && b) {
          s.moves.unshift({ at: now, from: a.id, to: b.id, jobId: job.id, part: tile.i, saved: tile.saved });
          if (s.moves.length > 20) s.moves.length = 20;
          from.note = `Part ${tile.i + 1} moved to ${siteName(b)} at ${pct(tile.saved)}`;
          log(s, `Part ${tile.i + 1} continues at ${pct(tile.saved)} on ${siteName(b)}, moved from ${siteName(a)}`, "amber");
          s.totals.resumed++;
        }
      }
    }
  }

  const h = hour(s);
  const all = sites(s);
  const site = n.site >= 0 ? all[n.site] : null;
  const x = h && n.site >= 0 ? h.sites[n.site] : null;
  const cur = n.current ? s.jobs.find((j) => j.id === n!.current!.jobId) : null;
  return {
    state: n.state,
    name: n.name,
    color: n.color,
    chunks: n.chunks,
    heatWh: n.heatWh,
    site: site && x ? { name: siteName(site), kind: site.kind, servers: site.servers, on: Math.ceil(x.running - 1e-9), tank: site.tank_kwh, soc: x.soc, temp: x.temp, own: !!site.person } : null,
    job: cur ? { id: cur.id, customer: cur.customer, kind: cur.kind, label: PRODUCTS[cur.kind].label } : null,
    reason: n.reason,
    conditions: s.cond ? condLabel(s.cond) : null,
    assign,
    abort,
    checkpoint: abort && checkpoint,
    note: n.note,
  };
}

export function done(input: { id: string; jobId: number; chunk: number; ms: number; image?: string; values?: number[] | number[][] }) {
  const s = store();
  const n = s.nodes.get(input.id);
  const job = s.jobs.find((j) => j.id === input.jobId);
  const tile = job?.tiles[input.chunk];
  // its own part, or the part it finished just as its rack was paused
  const mine = n?.current && n.current.jobId === input.jobId && n.current.chunk === input.chunk;
  const justPaused = tile?.state === "paused" && tile.node === input.id;
  if (!n || !(mine || justPaused)) return { ok: false };
  if (mine) n.current = null;
  if (!job || !tile || tile.node !== n.id) return { ok: false };
  const key = `${job.id}:${tile.i}`;
  const ck = s.ckpt.get(key);
  if (job.kind !== "render") {
    const raw = input.values;
    // a part resumed from a checkpoint brings only the items after it
    const v = Array.isArray(raw) ? [...(ck?.values ?? []), ...raw] : null;
    if (!v || v.length > AI_PART) return { ok: false };
    s.results.set(key, v as number[] | number[][]);
    if (job.kind === "rerank") job.top = topHits(s, job);
    if (job.kind === "embed") job.latest = partTitles(s, job, tile.i).slice(0, 3);
  }
  const img = input.image ? decode(input.image) : null;
  if (img) s.images.set(key, img);
  s.ckpt.delete(key);
  s.images.delete(`${key}:ckpt`);
  tile.state = "done";
  tile.v++;
  n.chunks++;
  // with k servers on and K in the biggest rack, the rack works k/K of the time: rest in proportion to the tile just done
  if (n.duty > 0 && n.duty < 1) n.restUntil = Date.now() + Math.min(120_000, input.ms * (1 / n.duty - 1));
  n.heatWh += (DEVICE_WATTS[n.device] * Math.max(0, Math.min(60_000, input.ms))) / 3_600_000;
  s.totals.tiles++;
  if (job.tiles.every((t) => t.state === "done")) {
    job.doneAt = Date.now();
    const by = new Set(job.tiles.map((t) => t.node)).size;
    log(s, `${PRODUCTS[job.kind].label} done in ${((job.doneAt - (job.startedAt ?? job.createdAt)) / 1000).toFixed(0)} s, by ${by} racks`, "teal");
  }
  return { ok: true };
}

/** The page was closed, hidden or the phone locked: its tile goes back to the queue at once. */
export function leave(id: string) {
  const s = store();
  const n = s.nodes.get(id);
  if (n && n.state !== "offline") goAway(s, n, "left");
}

/**
 * A paused part's progress: render, the tile so far and the samples traced; AI, the values of the items
 * done. The part goes back to the queue and the next rack continues from here.
 */
export function checkpoint(input: { id: string; jobId: number; chunk: number; done?: number; image?: string; values?: (number[] | number)[] }) {
  const s = store();
  const n = s.nodes.get(input.id);
  const job = s.jobs.find((j) => j.id === input.jobId);
  const tile = job?.tiles[input.chunk];
  if (!n || !job || !tile || tile.state !== "paused" || tile.node !== n.id) return { ok: false };
  const key = `${job.id}:${tile.i}`;
  const prev = s.ckpt.get(key);
  if (job.kind === "render") {
    const img = input.image ? decode(input.image) : null;
    const d = Math.max(0, Math.min(RENDER_SAMPLES, input.done ?? 0));
    if (img && d > (prev?.done ?? 0) && d >= 0.02 * RENDER_SAMPLES) {
      s.images.set(`${key}:ckpt`, img);
      s.ckpt.set(key, { done: d });
    }
  } else if (Array.isArray(input.values) && input.values.length) {
    const values = [...(prev?.values ?? []), ...input.values].slice(0, AI_PART - 1);
    s.ckpt.set(key, { done: values.length, values });
  }
  const ck = s.ckpt.get(key);
  const total = job.kind === "render" ? RENDER_SAMPLES : AI_PART;
  tile.saved = ck ? ck.done / total : 0;
  tile.state = "pending";
  tile.node = null;
  tile.pausedAt = undefined;
  tile.v++;
  s.totals.moved++;
  const site = rackSite(s, n);
  n.note = tile.saved ? `Part ${tile.i + 1} saved at ${pct(tile.saved)}, waiting for a rack that needs heat` : null;
  log(s, `${siteName(site)}: part ${tile.i + 1} paused${tile.saved ? `, saved at ${pct(tile.saved)}` : ""}`, "amber");
  return { ok: true };
}

/** A customer orders a job: a 3D rendering of a scene, embeddings of abstracts, or reranking for a question. */
export function order(input: { customer?: string; kind?: string; scene?: string; query?: string }) {
  const s = store();
  const kind = (input.kind && input.kind in PRODUCTS ? input.kind : "render") as JobKind;
  const job: Job = {
    id: s.nextJob++,
    kind,
    customer: cleanName(input.customer) || "a customer",
    createdAt: Date.now(),
    startedAt: null,
    doneAt: null,
    tiles: Array.from({ length: PARTS[kind] }, (_, i) => ({ i, state: "pending", node: null, v: 0, restarts: 0 })),
  };
  if (kind === "render") job.scene = (input.scene && input.scene in SCENES ? input.scene : "warm") as SceneKey;
  if (kind === "embed") {
    const c = getCorpus();
    s.docs.set(job.id, Array.from({ length: EMBED_ITEMS }, (_, k) => (s.nextEmbed + k) % c.docs.length));
    s.nextEmbed = (s.nextEmbed + EMBED_ITEMS) % c.docs.length;
  }
  if (kind === "rerank") {
    const c = getCorpus();
    const q = typeof input.query === "string" ? input.query.replace(/\s+/g, " ").trim().slice(0, 200) : "";
    job.query = q || c.queries[Math.floor(Math.random() * c.queries.length)];
    s.docs.set(job.id, candidates(c, job.query, RERANK_ITEMS));
    job.top = [];
  }
  s.jobs.push(job);
  while (s.jobs.length > KEEP_JOBS) {
    const old = s.jobs.shift()!;
    for (let i = 0; i < old.tiles.length; i++) {
      s.images.delete(`${old.id}:${i}`);
      s.images.delete(`${old.id}:${i}:ckpt`);
      s.results.delete(`${old.id}:${i}`);
      s.ckpt.delete(`${old.id}:${i}`);
    }
    s.docs.delete(old.id);
    for (const n of s.nodes.values())
      if (n.current?.jobId === old.id) {
        n.current = null;
        n.abort = true;
      }
  }
  log(s, `New order: ${PRODUCTS[kind].label}`, "ink");
  return { id: job.id };
}

export function job(id: number) {
  return store().jobs.find((j) => j.id === id) ?? null;
}

export async function conditions(input: { key: CondKey; sites?: DaySite[] }) {
  const s = store();
  s.tanks.clear(); // the operator picked a moment: tanks start from the scheduler's levels
  s.full.clear();
  if (input.sites) s.base = input.sites;
  await setConditions(s, input.key);
  log(s, `${condLabel(s.cond!)}: ${hour(s)!.sites.filter((x) => x.running > 0).length} of ${sites(s).length} buildings need heat`, "ink");
  return state(null);
}

export function control(input: { op: string; id?: string; site?: string; sites?: DaySite[]; jobId?: number }) {
  const s = store();
  switch (input.op) {
    case "fill": {
      // the operator fills a building's tank (someone stopped drawing heat): its rack pauses, its part moves
      stepTanks(s);
      const site = sites(s).find((x) => x.id === input.site);
      if (site && site.tank_kwh > 0) {
        s.tanks.set(site.id, site.tank_kwh);
        if (!s.full.has(site.id)) {
          s.full.add(site.id);
          log(s, `${siteName(site)}: tank 100 %, rack paused until it cools to ${pct(TANK_RESUME)}`, "teal");
        }
        tick(s);
      }
      break;
    }
    case "sites":
      // the operator's sites; a new decision uses them
      if (input.sites && JSON.stringify(input.sites) !== JSON.stringify(s.base)) {
        s.base = input.sites;
        replan(s);
      }
      break;
    case "cancel": {
      const j = s.jobs.find((x) => x.id === input.jobId);
      if (j && !j.doneAt) {
        s.jobs = s.jobs.filter((x) => x !== j);
        for (let i = 0; i < j.tiles.length; i++) s.ckpt.delete(`${j.id}:${i}`);
        for (const n of s.nodes.values())
          if (n.current?.jobId === j.id) {
            n.current = null;
            n.abort = true;
          }
        log(s, `${PRODUCTS[j.kind].label} cancelled`, "ink");
      }
      break;
    }
    case "forget-offline":
      for (const x of [...s.nodes.values()]) if (x.state === "offline") s.nodes.delete(x.id);
      replan(s);
      break;
    case "reset": {
      const { base, cond } = s;
      if (s.planTimer) clearTimeout(s.planTimer);
      g.__dhLive4 = fresh();
      g.__dhLive4.base = base;
      g.__dhLive4.cond = cond;
      if (cond) replan(g.__dhLive4);
      break;
    }
  }
  return state(null);
}

export function state(host: string | null, proto?: string | null): LiveState {
  const s = store();
  tick(s);
  return {
    now: Date.now(),
    conditions: s.cond,
    sites: sites(s),
    hour: hour(s),
    planning: s.planning || !!s.planTimer,
    jobs: s.jobs,
    nodes: [...s.nodes.values()].map((n) => {
      const { lastSeen, abort, index, rackId, checkpoint, note, ...pub } = n;
      void lastSeen;
      void abort;
      void index;
      void rackId;
      void checkpoint;
      void note;
      return pub;
    }),
    events: s.events,
    totals: s.totals,
    full: [...s.full],
    moves: s.moves,
    pricing: PRICING,
    joinBase: host ? joinBase(host, proto) : null,
  };
}

/** Reranking: the best-scoring abstracts among the parts done so far. */
function topHits(s: Store, job: Job): Hit[] {
  const c = getCorpus();
  const docs = s.docs.get(job.id) ?? [];
  const all: { d: number; score: number }[] = [];
  job.tiles.forEach((t) => {
    const v = s.results.get(`${job.id}:${t.i}`) as number[] | undefined;
    v?.forEach((score, k) => all.push({ d: docs[t.i * AI_PART + k], score }));
  });
  all.sort((a, b) => b.score - a.score);
  return all.slice(0, 5).map(({ d, score }) => ({ title: docTitle(c, d), text: c.docs[d][2].slice(0, 260), score: +score.toFixed(2) }));
}

const docTitle = (c: Corpus, d: number) => c.docs[d][1] || c.docs[d][2].slice(0, 90);

/** Embeddings: the titles of one part's abstracts. */
function partTitles(s: Store, job: Job, part: number) {
  const c = getCorpus();
  return (s.docs.get(job.id) ?? []).slice(part * AI_PART, (part + 1) * AI_PART).map((d) => docTitle(c, d));
}

/** An AI job's output, for download: one row per abstract. */
export function result(jobId: number) {
  const s = store();
  const job = s.jobs.find((j) => j.id === jobId);
  if (!job || job.kind === "render") return null;
  const c = getCorpus();
  const docs = s.docs.get(job.id) ?? [];
  const rows = docs.map((d, k) => {
    const v = s.results.get(`${job.id}:${Math.floor(k / AI_PART)}`)?.[k % AI_PART];
    return { id: c.docs[d][0], title: c.docs[d][1], [job.kind === "embed" ? "embedding" : "score"]: v ?? null };
  });
  if (job.kind === "rerank") rows.sort((a, b) => ((b.score as number) ?? -1e9) - ((a.score as number) ?? -1e9));
  return {
    job: job.kind,
    model: job.kind === "embed" ? "sentence-transformers/all-MiniLM-L6-v2" : "cross-encoder/ms-marco-MiniLM-L6-v2",
    dataset: "BEIR SciFact",
    ...(job.query ? { query: job.query } : {}),
    rows,
  };
}

export function image(jobId: number, tile: number, ckpt = false) {
  return store().images.get(`${jobId}:${tile}${ckpt ? ":ckpt" : ""}`) ?? null;
}

function decode(dataUrl: string) {
  const m = /^data:image\/(?:png|jpeg);base64,(.+)$/.exec(dataUrl);
  return m && m[1].length < 400_000 ? Buffer.from(m[1], "base64") : null;
}

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function condLabel(c: Conditions) {
  const [, m, d] = c.date.split("-").map(Number);
  return `${c.label} · ${d} ${MON[m - 1]}, ${String(c.hour).padStart(2, "0")}:00`;
}

/**
 * The address phones open: LIVE_PUBLIC_URL if set (a tunnel such as cloudflared, for venue Wi-Fi that
 * keeps devices apart), else the host the operator screen was opened on if that is not localhost,
 * else this laptop's LAN IP and the port the dashboard is served on.
 */
function joinBase(host: string, proto?: string | null) {
  const pub = process.env.LIVE_PUBLIC_URL?.replace(/\/$/, "");
  if (pub) return pub;
  if (!/^(localhost|127\.0\.0\.1|\[::1\])(:|$)/.test(host)) return `${proto === "https" ? "https" : "http"}://${host}`;
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
