import type { Fleet, JobType, ServiceStats } from "./data";

export const USD_CHF = 0.8392; // ECB 20 Nov 2026, same as analysis/r4_machine.py

/** Per-unit price display: transcription per 1,000 audio-hours, LLM per million output tokens. */
export function unitScale(jt: JobType) {
  return jt.service.unit === "audio-hour"
    ? { per: 1000, label: "1,000 audio-hours" }
    : { per: 1, label: "M output tokens" };
}

export function serviceOf(f: Fleet, id: string): { jt: JobType; st: ServiceStats; index: number } | null {
  const index = f.meta.job_types.findIndex((j) => j.id.toLowerCase() === id.toLowerCase());
  if (index < 0) return null;
  return { jt: f.meta.job_types[index], st: f.services[index], index };
}

/** CHF per display unit, given a price per server-hour. */
export function perUnit(jt: JobType, chfPerServerH: number) {
  return (chfPerServerH / jt.service.unit_per_server_h) * unitScale(jt).per;
}

/** Public list price per display unit, in CHF. */
export function listPerUnit(jt: JobType, k: "low" | "central" | "high") {
  return jt.service.list_usd[k] * USD_CHF * unitScale(jt).per;
}
