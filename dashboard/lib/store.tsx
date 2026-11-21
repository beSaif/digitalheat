"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { DEFAULT_T, H, setDataYear, type Fleet, type Job, type JobChunk } from "./data";

type Ctx = {
  fleet: Fleet | null;
  t: number;
  setT: (t: number | ((t: number) => number)) => void;
  playing: boolean;
  setPlaying: (p: boolean) => void;
  speed: number; // simulated hours per second
  setSpeed: (s: number) => void;
  year: number;
  setYear: (y: number) => void;
  yearLoading: boolean;
};

const FleetCtx = createContext<Ctx | null>(null);

// where the Swiss replay for the current year lives (public/data for 2025, public/data/y<year> otherwise)
let DATA_PATH = "/data";

export function FleetProvider({ children }: { children: React.ReactNode }) {
  const [fleet, setFleet] = useState<Fleet | null>(null);
  const [t, setTRaw] = useState(DEFAULT_T);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(4);
  const [year, setYearRaw] = useState(2025);
  setDataYear(year); // date labels follow the chosen year
  const yearLoading = fleet !== null && fleet.meta.year !== year;

  useEffect(() => {
    // ?t=<hour of year> opens the replay at a given hour, ?year=<year> in another weather year
    const qs = new URLSearchParams(window.location.search);
    const q = Number(qs.get("t"));
    const y = Number(qs.get("year"));
    Promise.resolve().then(() => {
      if (Number.isFinite(q) && q > 0) setTRaw(Math.min(H - 1, Math.round(q)));
      if (y >= 1950 && y <= 2025 && y !== 2025) setYearRaw(y);
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    (year === 2025
      ? Promise.resolve({ path: "/data" })
      : fetch("/api/fleet-year", { method: "POST", body: JSON.stringify({ year }) }).then((r) => r.json())
    )
      .then((r: { path?: string }) => {
        if (!r.path) throw new Error("no data");
        return fetch(`${r.path}/fleet.json`).then((x) => x.json().then((f: Fleet) => ({ f, path: r.path! })));
      })
      .then(({ f, path }) => {
        if (cancelled) return;
        DATA_PATH = path;
        chunkCache.clear();
        setFleet(f);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [year]);

  const setT = useCallback((v: number | ((t: number) => number)) => {
    setTRaw((prev) => {
      const n = typeof v === "function" ? v(prev) : v;
      return Math.max(0, Math.min(H - 1, Math.round(n)));
    });
  }, []);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setT((x) => (x >= H - 1 ? 0 : x + 1)), 1000 / speed);
    return () => clearInterval(id);
  }, [playing, speed, setT]);

  const value = useMemo(
    () => ({ fleet, t, setT, playing, setPlaying, speed, setSpeed, year, setYear: setYearRaw, yearLoading }),
    [fleet, t, setT, playing, speed, year, yearLoading],
  );
  return <FleetCtx.Provider value={value}>{children}</FleetCtx.Provider>;
}

export function useFleet() {
  const c = useContext(FleetCtx);
  if (!c) throw new Error("useFleet outside FleetProvider");
  return c;
}

const chunkCache = new Map<string, Promise<JobChunk>>();
function loadWeek(w: number) {
  const key = `${DATA_PATH}:${w}`;
  if (!chunkCache.has(key)) {
    chunkCache.set(key, fetch(`${DATA_PATH}/jobs/w${String(w).padStart(2, "0")}.json`).then((r) => r.json()));
  }
  return chunkCache.get(key)!;
}

/** Jobs that can be live at hour t: they arrived within the last 168 h (J2 deadline). */
export function useJobsAround(t: number, site?: number) {
  const { fleet } = useFleet();
  const w = Math.floor(t / 168);
  const [state, setState] = useState<{ key: string; jobs: Job[] } | null>(null);
  const key = `${fleet?.meta.year ?? 0}:${w}:${site ?? "all"}`;
  const reqRef = useRef(key);

  useEffect(() => {
    reqRef.current = key;
    const weeks = [w - 1, w].filter((x) => x >= 0 && x <= 52);
    Promise.all(weeks.map(loadWeek)).then((chunks) => {
      if (reqRef.current !== key) return;
      const jobs: Job[] = [];
      for (const c of chunks) {
        for (let i = 0; i < c.count; i++) {
          if (site !== undefined && c.site[i] !== site) continue;
          jobs.push({
            id: c.first + i,
            site: c.site[i],
            type: c.type[i],
            arrive: c.arrive[i],
            start: c.start[i],
            finish: c.finish[i],
            status: c.status[i],
            free: c.free[i],
          });
        }
      }
      setState({ key, jobs });
    });
  }, [key, w, site]);

  return state?.key === key ? state.jobs : null;
}

/** Live queue at t: admitted, arrived, not finished. */
export function liveQueue(jobs: Job[], t: number) {
  return jobs.filter((j) => (j.status === 0 || j.status === 3) && j.arrive <= t && j.finish > t);
}

export function useSiteSlots(id: string | undefined) {
  const { fleet } = useFleet();
  const [slots, setSlots] = useState<{ key: string; slots: number[][] } | null>(null);
  const key = `${fleet?.meta.year ?? 0}:${id}`;
  useEffect(() => {
    if (!id) return;
    fetch(`${DATA_PATH}/sites/${id}.json`)
      .then((r) => r.json())
      .then((d) => setSlots({ key, slots: d.slots }));
  }, [id, key]);
  return slots && slots.key === key ? slots.slots : null;
}
