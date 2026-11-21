import { spawn } from "node:child_process";
import { mkdirSync, openSync, readFileSync } from "node:fs";
import path from "node:path";
import { ROOT, cleanSites, cleanYear, python } from "@/lib/server/python";

/*
 * The real job, controlled by the scheduler (python -m scheduler.live).
 * GET  → runs/live/status.json plus whether the controller is still alive
 * POST { op: "start", year, day, hour, site, sites } | { op: "stop" }
 */

const STATUS = path.join(ROOT, "runs", "live", "status.json");

function readStatus() {
  try {
    return JSON.parse(readFileSync(STATUS, "utf8"));
  } catch {
    return null;
  }
}

function alive(pid: number | undefined) {
  if (!pid) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

export async function GET() {
  const s = readStatus();
  return Response.json(s ? { ...s, alive: alive(s.pid) && s.state !== "finished" } : null, {
    headers: { "cache-control": "no-store" },
  });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const cur = readStatus();
  if (body?.op === "stop") {
    if (cur && alive(cur.pid)) process.kill(cur.pid, "SIGTERM");
    return Response.json({ ok: true });
  }
  if (body?.op !== "start") return Response.json({ error: "bad request" }, { status: 400 });
  if (cur && alive(cur.pid) && cur.state !== "finished") return Response.json({ error: "already running" }, { status: 409 });
  const sites = cleanSites(body.sites);
  const year = cleanYear(body.year);
  const day = Number(body.day),
    hour = Number(body.hour);
  if (!sites || !year || !(day >= 0 && day < 365) || !(hour >= 0 && hour < 24)) return Response.json({ error: "bad request" }, { status: 400 });
  const site = sites.find((s) => s.id === body.site)?.id ?? sites[0].id;
  // day index → calendar date (the model's year has no 29 February)
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const date = new Date(Date.UTC(year, 0, 1) + (day + (leap && day >= 59 ? 1 : 0)) * 86_400_000).toISOString().slice(0, 10);
  mkdirSync(path.dirname(STATUS), { recursive: true });
  const log = openSync(path.join(ROOT, "runs", "live", "controller.log"), "a");
  const p = spawn(
    python(),
    ["-m", "scheduler.live", "--day", date, "--hour", String(hour), "--hours", "24", "--seconds-per-hour", "5",
      "--sites-json", JSON.stringify(sites), "--site", site],
    { cwd: ROOT, detached: true, stdio: ["ignore", log, log] },
  );
  p.unref();
  return Response.json({ ok: true, pid: p.pid });
}
