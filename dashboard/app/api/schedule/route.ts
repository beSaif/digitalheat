import { cleanSites, cleanYear, runPython } from "@/lib/server/python";

/*
 * POST { year, sites } → the scheduler's full year (python -m scheduler.balance --stdin).
 * The dashboard never schedules on its own: this is the same code as the yearly balance and the real-job controller.
 */

const cache = new Map<string, Promise<string>>();

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const sites = cleanSites(body?.sites);
  const year = cleanYear(body?.year ?? 2025);
  if (!sites || !year) return Response.json({ error: "bad request" }, { status: 400 });
  const req = JSON.stringify({ year, sites });
  if (!cache.has(req)) {
    if (cache.size > 40) cache.delete(cache.keys().next().value!);
    const p = runPython("scheduler.balance", ["--stdin"], req);
    p.catch(() => cache.delete(req));
    cache.set(req, p);
  }
  try {
    const out = await cache.get(req)!;
    return new Response(out, { headers: { "content-type": "application/json", "cache-control": "no-store" } });
  } catch (e) {
    return Response.json({ error: String((e as Error).message) }, { status: 500 });
  }
}
