"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { DEFAULT_T, H, type Fleet, type Job, type JobChunk } from "./data";

type Ctx = {
  fleet: Fleet | null;
  t: number;
  setT: (t: number | ((t: number) => number)) => void;
  playing: boolean;
  setPlaying: (p: boolean) => void;
  speed: number; // simulated hours per second
  setSpeed: (s: number) => void;
};

const FleetCtx = createContext<Ctx | null>(null);

export function FleetProvider({ children }: { children: React.ReactNode }) {
  const [fleet, setFleet] = useState<Fleet | null>(null);
  const [t, setTRaw] = useState(DEFAULT_T);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(4);

  useEffect(() => {
    // ?t=<hour of year> opens the replay at a given hour (e.g. for a demo link)
    const q = Number(new URLSearchParams(window.location.search).get("t"));
    fetch("/data/fleet.json")
      .then((r) => r.json())
      .then((f: Fleet) => {
        // screens read demand/served as kWh ×10; the file may store them ×100 for the money figures
        for (const key of ["demand", "served"] as const) {
          const k = (f.meta.scales?.[key] ?? 10) / 10;
          if (k !== 1) for (const h of f.hourly) h[key] = h[key].map((v) => v / k);
        }
        if (Number.isFinite(q) && q > 0) setTRaw(Math.min(H - 1, Math.round(q)));
        setFleet(f);
      });
  }, []);

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
    () => ({ fleet, t, setT, playing, setPlaying, speed, setSpeed }),
    [fleet, t, setT, playing, speed],
  );
  return <FleetCtx.Provider value={value}>{children}</FleetCtx.Provider>;
}

export function useFleet() {
  const c = useContext(FleetCtx);
  if (!c) throw new Error("useFleet outside FleetProvider");
  return c;
}

const chunkCache = new Map<number, Promise<JobChunk>>();
function loadWeek(w: number) {
  if (!chunkCache.has(w)) {
    chunkCache.set(
      w,
      fetch(`/data/jobs/w${String(w).padStart(2, "0")}.json`).then((r) => r.json()),
    );
  }
  return chunkCache.get(w)!;
}

/** Jobs that can be live at hour t: they arrived within the last 168 h (J2 deadline). */
export function useJobsAround(t: number, site?: number) {
  const w = Math.floor(t / 168);
  const [state, setState] = useState<{ key: string; jobs: Job[] } | null>(null);
  const key = `${w}:${site ?? "all"}`;
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
  const [slots, setSlots] = useState<{ id: string; slots: number[][] } | null>(null);
  useEffect(() => {
    if (!id) return;
    fetch(`/data/sites/${id}.json`)
      .then((r) => r.json())
      .then(setSlots);
  }, [id]);
  return slots && slots.id === id ? slots.slots : null;
}
