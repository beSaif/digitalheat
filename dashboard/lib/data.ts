export type JobType = {
  id: string;
  name: string;
  model: string;
  units: number; // half server-hours
  due_h: number;
  detail: string;
};

export type Site = {
  id: string;
  city: string;
  district: string;
  canton: string;
  lat: number;
  lon: number;
  building: string;
  scale: number;
  servers: number;
  tank_kwh: number;
  reference: boolean;
  elevation_m: number;
  year: {
    demand_kwh: number;
    served_kwh: number;
    coverage: number;
    permit_server_h: number;
    run_server_h: number;
    utilisation: number;
  };
};

export type City = {
  name: string;
  canton: string;
  lat: number;
  lon: number;
  code: string;
  elevation_m: number;
};

export type SiteHourly = {
  demand: number[]; // kWh ×10
  permit: number[]; // servers the heat allows
  run: number[]; // half server-hours used
  soc: number[]; // tank kWh ×10, end of hour
  served: number[]; // kWh ×10 delivered from server heat
};

export type Fleet = {
  meta: {
    title: string;
    year: number;
    seed: number;
    generator: string;
    hours: number;
    constants: { server_kw: number; heat_recovery: number; price_chf_kwh: number; heat_value_chf_kwh: number };
    job_types: JobType[];
    weather: string;
    time_note: string;
  };
  cities: City[];
  sites: Site[];
  totals: Record<string, number>;
  hourly: SiteHourly[];
  temps: Record<string, number[]>;
  daily_jobs: { offered: number[]; refused: number[]; admitted_server_h: number[] };
  job_weeks: { week: number; first: number; count: number }[];
};

export type JobChunk = {
  week: number;
  first: number;
  count: number;
  site: number[];
  type: number[];
  arrive: number[];
  start: number[];
  finish: number[];
  status: number[]; // 0 admitted, 1 refused (no heat before due), 2 refused (would push admitted job late), 3 missed
  free: number[]; // half server-hours of permit free before due at arrival
};

export type Job = {
  id: number;
  site: number;
  type: number;
  arrive: number;
  start: number;
  finish: number;
  status: number;
  free: number;
};

export const H = 8760;
export const DEFAULT_T = 324 * 24 + 14; // 21 Nov, 14:00, same date as the event

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** The weather year on screen. Every model year has 365 days: in leap years 29 February is left out. */
let YEAR = 2025;
export function setDataYear(y: number) {
  YEAR = y;
}
export function dataYear() {
  return YEAR;
}
export const isLeap = (y: number) => y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0);
export const YEARS = Array.from({ length: 10 }, (_, i) => 2025 - i);

export function hourDate(t: number) {
  const skip = isLeap(YEAR) && t >= 59 * 24 ? 24 : 0;
  return new Date(Date.UTC(YEAR, 0, 1, 0) + (t + skip) * 3600_000);
}

export function fmtTime(t: number) {
  const d = hourDate(t);
  return `${String(d.getUTCHours()).padStart(2, "0")}:00`;
}

export function fmtDate(t: number, withDay = false) {
  const d = hourDate(t);
  const s = `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
  return withDay ? `${DAYS[d.getUTCDay()]}, ${s}` : s;
}

export function fmtDay(t: number) {
  const d = hourDate(t);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
}

export function dayLetter(day: number) {
  return DAYS[hourDate(day * 24).getUTCDay()][0];
}

export const nf = (v: number, digits = 0) =>
  v.toLocaleString("en-CH", { minimumFractionDigits: digits, maximumFractionDigits: digits }).replace(/,/g, " ");

export type ServerState = "running" | "paused" | "no-heat" | "no-work";

/** What the site is doing in hour t, from the precomputed hourly arrays. */
export function siteNow(f: Fleet, si: number, t: number) {
  const h = f.hourly[si];
  const s = f.sites[si];
  const running = Math.ceil(h.run[t] / 2);
  const permit = h.permit[t];
  const prevRunning = t > 0 ? Math.ceil(h.run[t - 1] / 2) : 0;
  const demand = h.demand[t] / 10;
  const served = h.served[t] / 10;
  const soc = h.soc[t] / 10;
  let state: "running" | "throttled" | "idle-heat" | "idle-work";
  if (running === 0) state = permit === 0 ? "idle-heat" : "idle-work";
  else if (running < prevRunning && permit < prevRunning) state = "throttled";
  else state = "running";
  return {
    site: s,
    running,
    permit,
    prevRunning,
    demand,
    served,
    soc,
    socShare: soc / s.tank_kwh,
    heatKw: (h.run[t] / 2) * f.meta.constants.heat_recovery,
    state,
  };
}

export function fleetNow(f: Fleet, t: number) {
  let running = 0,
    permit = 0,
    demand = 0,
    served = 0,
    heat = 0,
    soc = 0,
    tank = 0;
  f.sites.forEach((s, i) => {
    const h = f.hourly[i];
    running += Math.ceil(h.run[t] / 2);
    permit += h.permit[t];
    demand += h.demand[t] / 10;
    served += h.served[t] / 10;
    heat += (h.run[t] / 2) * f.meta.constants.heat_recovery;
    soc += h.soc[t] / 10;
    tank += s.tank_kwh;
  });
  return { running, permit, demand, served, heat, soc, tank, servers: f.totals.servers };
}

/** Sum over a window [a, b) for all or one site; values in kWh. */
export function windowSum(f: Fleet, key: "demand" | "served", a: number, b: number, si?: number) {
  let s = 0;
  const idx = si === undefined ? f.hourly.map((_, i) => i) : [si];
  for (const i of idx) {
    const arr = f.hourly[i][key];
    for (let t = Math.max(0, a); t < Math.min(H, b); t++) s += arr[t];
  }
  return s / 10;
}

export function cityTemp(f: Fleet, city: string, t: number) {
  return f.temps[city][t] / 10;
}

export function siteIndex(f: Fleet, id: string) {
  return f.sites.findIndex((s) => s.id === id);
}

export function jobProgress(f: Fleet, j: Job, t: number) {
  // work is done EDF at full permit speed; approximate progress linearly between start and finish
  if (j.start < 0 || t < j.start) return 0;
  if (j.finish <= t) return 1;
  return Math.min(0.98, (t - j.start + 0.5) / Math.max(1, j.finish - j.start)); // mid-hour estimate
}
