"use client";

import { useEffect, useState } from "react";

/* The scheduler's output (python -m scheduler.balance). The dashboard only displays it. */

export type Kind = "house" | "family" | "cityhouse" | "hospital" | "spa" | "greenhouse" | "office" | "pharma";

export const KIND_LABEL: Record<Kind, string> = {
  house: "House",
  family: "Family home",
  cityhouse: "City house",
  hospital: "Hospital",
  spa: "Spa & pool",
  greenhouse: "Greenhouse",
  office: "Office",
  pharma: "Pharma lab",
};
export const KIND_SERVERS: Record<Kind, number> = { house: 4, family: 4, cityhouse: 6, hospital: 15, spa: 11, greenhouse: 10, office: 8, pharma: 14 };

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
  money: Money | null;
};

/** Computing income and where the model stops paying off (scheduler/pricing.py). */
export type Money = {
  sell_chf_per_server_h: number;
  income_chf: number;
  profit_chf: number;
  pays_off: boolean;
  min_price_chf_per_server_h: number;
  min_utilisation: number | null;
  max_electricity_chf_kwh: number;
  max_hardware_chf_per_server: number;
};

export type JobPrice = { items: number; server_h: number; spot_chf: number; on_demand_chf: number; service_chf: number; service: string };

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
  /** jobs paused in memory at this site at the end of the hour */
  paused_now: number[];
  /** jobs saved at a checkpoint, waiting for heat */
  waiting_now: number[];
};

export type Schedule = {
  year: number;
  constants: {
    heat_recovery: number;
    electricity_chf_kwh: number;
    heat_value_chf_kwh: number;
    hardware_chf_per_server: number;
    hardware_years: number;
    sell_chf_per_server_h: number;
    aws_spot_chf_h: number;
    aws_on_demand_chf_h: number;
  };
  job_prices: Record<"embed" | "rerank", JobPrice>;
  job_types: Record<"embed" | "rerank", { server_h: number; due_h: number; arrival_hours: number[]; backlog: boolean }>;
  sites: (SiteIn & { tank_kwh: number; size: number; label: string; year: YearFig })[];
  fleet: YearFig;
  series: Series[];
  embed_ids: number[];
  /** [id, origin, arrive, due, site, start, finish, status (0 done, 1 missed, 2 open), forced] */
  deadline_jobs: number[][];
};

const STORE = "dh.sites.v1";

/** The sites the operator set up (kept in this browser). */
export function useSavedSites() {
  const [sites, setSites] = useState<SiteIn[]>(DEFAULT_SITES);
  useEffect(() => {
    let saved: SiteIn[] | null = null;
    try {
      saved = JSON.parse(localStorage.getItem(STORE) || "null");
    } catch {}
    if (Array.isArray(saved) && saved.length) Promise.resolve(saved).then(setSites);
  }, []);
  const save = (next: SiteIn[]) => {
    setSites(next);
    try {
      localStorage.setItem(STORE, JSON.stringify(next));
    } catch {}
  };
  return [sites, save] as const;
}

/** What the scheduler needs to know about a site (no UI flags). */
export const plainSite = (s: SiteIn) => ({ id: s.id, kind: s.kind, name: s.name, lat: s.lat, lon: s.lon, servers: s.servers });
