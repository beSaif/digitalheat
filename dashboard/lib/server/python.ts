import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

/** Repository root (the dashboard runs from dashboard/). */
export const ROOT = path.resolve(process.cwd(), "..");

export function python() {
  const venv = path.join(ROOT, ".venv", "bin", "python");
  return existsSync(venv) ? venv : "python3";
}

/** Run `python -m <module> <args>` in the repo root, feeding stdin; resolves with stdout. */
export function runPython(module: string, args: string[], stdin?: string, timeoutMs = 120_000): Promise<string> {
  return new Promise((resolve, reject) => {
    const p = spawn(python(), ["-m", module, ...args], { cwd: ROOT });
    const out: Buffer[] = [];
    const err: Buffer[] = [];
    const timer = setTimeout(() => p.kill("SIGKILL"), timeoutMs);
    p.stdout.on("data", (d) => out.push(d));
    p.stderr.on("data", (d) => err.push(d));
    p.on("error", reject);
    p.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) resolve(Buffer.concat(out).toString());
      else reject(new Error(Buffer.concat(err).toString().split("\n").filter(Boolean).slice(-3).join("\n") || `exit ${code}`));
    });
    if (stdin !== undefined) p.stdin.end(stdin);
  });
}

export const KINDS = ["house", "cityhouse", "hospital", "spa", "greenhouse"] as const;

export type SiteIn = {
  id: string;
  kind: (typeof KINDS)[number];
  name: string;
  lat: number;
  lon: number;
  servers: number;
};

/** Accept only sites inside Switzerland with sane sizes; returns null when the input is bad. */
export function cleanSites(raw: unknown): SiteIn[] | null {
  if (!Array.isArray(raw) || raw.length === 0 || raw.length > 20) return null;
  const out: SiteIn[] = [];
  for (const s of raw) {
    if (!s || typeof s !== "object") return null;
    const r = s as Record<string, unknown>;
    const lat = Number(r.lat),
      lon = Number(r.lon),
      servers = Number(r.servers);
    if (!KINDS.includes(r.kind as SiteIn["kind"])) return null;
    if (!(lat >= 45.8 && lat <= 47.9 && lon >= 5.9 && lon <= 10.6)) return null;
    if (!Number.isInteger(servers) || servers < 0 || servers > 40) return null;
    out.push({
      id: String(r.id ?? "").replace(/[^A-Za-z0-9-]/g, "").slice(0, 12) || `S${out.length + 1}`,
      kind: r.kind as SiteIn["kind"],
      name: String(r.name ?? "").slice(0, 40),
      lat,
      lon,
      servers,
    });
  }
  return out;
}

export function cleanYear(raw: unknown) {
  const y = Number(raw);
  return Number.isInteger(y) && y >= 1950 && y <= 2025 ? y : null;
}
