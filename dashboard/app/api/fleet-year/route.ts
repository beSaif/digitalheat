import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { ROOT, cleanYear } from "@/lib/server/python";

/*
 * POST { year } → make sure the Swiss replay for that weather year exists in public/data/y<year>/.
 * Runs scripts/build_fleet_scenario.py --year <year> once (about 20 s with the weather download).
 */

const building = new Map<number, Promise<void>>();

function build(year: number) {
  return new Promise<void>((resolve, reject) => {
    const p = spawn("python3", ["scripts/build_fleet_scenario.py", "--year", String(year)], { cwd: ROOT, stdio: "ignore" });
    p.on("error", reject);
    p.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`generator exit ${code}`))));
  });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const year = cleanYear(body?.year);
  if (!year) return Response.json({ error: "bad request" }, { status: 400 });
  if (year === 2025) return Response.json({ path: "/data" });
  const dir = path.join(ROOT, "dashboard", "public", "data", `y${year}`);
  if (!existsSync(path.join(dir, "fleet.json"))) {
    if (!building.has(year)) {
      const p = build(year).finally(() => building.delete(year));
      building.set(year, p);
    }
    try {
      await building.get(year);
    } catch (e) {
      return Response.json({ error: String((e as Error).message) }, { status: 500 });
    }
  }
  return Response.json({ path: `/data/y${year}` });
}
