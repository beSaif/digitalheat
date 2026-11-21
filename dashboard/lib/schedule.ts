"use client";

import { useEffect, useRef, useState } from "react";

/* The scheduler's output (python -m scheduler.balance). The dashboard only displays it. */

export type Kind = "house" | "cityhouse" | "hospital" | "spa" | "greenhouse";

export const KIND_LABEL: Record<Kind, string> = {
  house: "House",
  cityhouse: "City house",
  hospital: "Hospital",
  spa: "Spa & pool",
  greenhouse: "Greenhouse",
};
export const KIND_SERVERS: Record<Kind, number> = { house: 4, cityhouse: 6, hospital: 15, spa: 11, greenhouse: 10 };

export type SiteIn = { id: string; kind: Kind; name: string; lat: number; lon: number; servers: number; added?: boolean };

export const DEFAULT_SITES: SiteIn[] = [
  { id: "BS-H1", kind: "hospital", name: "Hospital", lat: 47.5535, lon: 7.5705, servers: 15 },
  { id: "BS-01", kind: "house", name: "House", lat: 47.5695, lon: 7.588, servers: 4 },
  { id: "BS-S1", kind: "spa", name: "Spa & pool", lat: 47.555, lon: 7.6075, servers: 11 },
];

export type YearFig = {
  servers: number;
  demand_kwh: number;
  served_kwh: number;
  coverage: number;
  server_heat_kwh: number;
  dumped_kwh: number;
  run_server_h: number;
  utilisation: number;
  jobs_done: number;
  jobs_missed: number;
  missed_pct: number;
  forced_server_h: number;
  pauses: number;
  checkpoints: number;
  moves_in: number;
  electricity_chf: number;
  heat_value_chf: number;
  hardware_chf: number;
  break_even_chf_per_server_h: number | null;
  price_chf_per_server_h: number | null;
};

export type Series = {
  demand: number[];
  soc: number[];
  served: number[];
  dumped: number[];
  permit: number[];
  reserve_u: number[];
  limit: number[];
  running: number[];
  forced: number[];
  rerank_sh: number[];
  embed_sh: number[];
  paused: number[];
  checkpointed: number[];
  moved_in: number[];
  started: number[];
  finished: number[];
};

export type Schedule = {
  year: number;
  constants: { heat_recovery: number; electricity_chf_kwh: number; heat_value_chf_kwh: number; hardware_chf_per_server: number; hardware_years: number };
  job_types: Record<"embed" | "rerank", { server_h: number; due_h: number; arrival_hours: number[]; backlog: boolean }>;
  sites: (SiteIn & { tank_kwh: number; size: number; label: string; year: YearFig })[];
  fleet: YearFig;
  series: Series[];
  embed_ids: number[];
  /** [id, origin, arrive, due, site, start, finish, status (0 done, 1 missed, 2 open), forced] */
  deadline_jobs: number[][];
};

/** What the scheduler needs to know about a site (no UI flags). */
export const plainSite = (s: SiteIn) => ({ id: s.id, kind: s.kind, name: s.name, lat: s.lat, lon: s.lon, servers: s.servers });

/** Fetch the scheduler's year for these sites; keeps the last result on screen while a new one runs. */
export function useSchedule(sites: SiteIn[], year: number) {
  const [res, setRes] = useState<{ key: string; data: Schedule | null; error: string | null } | null>(null);
  const key = JSON.stringify({ year, sites: sites.map(plainSite) });
  const latest = useRef(key);
  useEffect(() => {
    latest.current = key;
    const t = setTimeout(() => {
      fetch("/api/schedule", { method: "POST", headers: { "content-type": "application/json" }, body: key })
        .then(async (r) => {
          const j = await r.json();
          if (!r.ok) throw new Error(j.error || r.statusText);
          return j as Schedule;
        })
        .then((d) => {
          if (latest.current === key) setRes({ key, data: d, error: null });
        })
        .catch((e) => {
          if (latest.current === key) setRes((r) => ({ key, data: r?.data ?? null, error: String(e.message) }));
        });
    }, 250); // let quick +/- clicks settle
    return () => clearTimeout(t);
  }, [key]);
  return { data: res?.data ?? null, loading: res?.key !== key, error: res?.key === key ? res.error : null };
}
