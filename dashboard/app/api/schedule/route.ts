import { readdirSync, statSync } from "node:fs";
import path from "node:path";
import { ROOT, cleanSites, cleanYear, runPython } from "@/lib/server/python";

/*
 * POST { year, sites } → the scheduler's full year (python -m scheduler.balance --stdin).
 * The dashboard never schedules on its own: this is the same code as the yearly balance and the real-job controller.
 */

const cache = new Map<string, Promise<string>>();

/** Last change to the scheduler code or prices, so an edit never serves an old year from the cache. */
function codeVersion() {
  const dir = path.join(ROOT, "scheduler");
  const files = readdirSync(dir).filter((f) => f.endsWith(".py")).map((f) => path.join(dir, f));
  files.push(path.join(ROOT, "data", "prices_2026.json"));
  return Math.max(...files.map((f) => statSync(f).mtimeMs));
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const sites = cleanSites(body?.sites);
  const year = cleanYear(body?.year ?? 2025);
  if (!sites || !year) return Response.json({ error: "bad request" }, { status: 400 });
  const req = JSON.stringify({ year, sites });
  const key = `${codeVersion()}:${req}`;
  if (!cache.has(key)) {
    if (cache.size > 40) cache.delete(cache.keys().next().value!);
    const p = runPython("scheduler.balance", ["--stdin"], req);
    p.catch(() => cache.delete(key));
    cache.set(key, p);
  }
  try {
    const out = await cache.get(key)!;
    return new Response(out, { headers: { "content-type": "application/json", "cache-control": "no-store" } });
  } catch (e) {
    return Response.json({ error: String((e as Error).message) }, { status: 500 });
  }
}
