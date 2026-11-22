import { beat, checkpoint, conditions, control, done, leave, order, state } from "@/lib/live/coordinator";
import { cleanSites } from "@/lib/server/python";
import { CONDITIONS, type CondKey, type DaySite } from "@/lib/live/shared";

/*
 * Live demo coordinator.
 * GET  → full state for the room screen and the client screen.
 * POST → { op: "beat" | "done" | "checkpoint" | "leave" } from the racks (phones, the operator laptop),
 *        { op: "order", customer, kind, scene, query } from the client screen,
 *        { op: "conditions", key, sites } to let the scheduler decide for a moment (now, January, July),
 *        or a control op ("sites", "fill", "cancel", "forget-offline", "reset") from the room screen.
 */

export async function GET(request: Request) {
  const h = request.headers;
  return Response.json(state(h.get("x-forwarded-host") ?? h.get("host"), h.get("x-forwarded-proto")), { headers: { "cache-control": "no-store" } });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.op !== "string") return Response.json({ error: "bad request" }, { status: 400 });
  const id = typeof body.id === "string" ? body.id.toLowerCase().replace(/[^a-z0-9-]/g, "").slice(0, 32) : undefined;
  switch (body.op) {
    case "beat":
      if (!id) break;
      return Response.json(
        beat({
          id,
          name: typeof body.name === "string" ? body.name : undefined,
          cores: num(body.cores),
          rate: num(body.rate),
          device: typeof body.device === "string" ? body.device : undefined,
          jobId: num(body.jobId),
          chunk: num(body.chunk),
          progress: num(body.progress),
        }),
      );
    case "done":
      if (!id || num(body.jobId) === undefined || num(body.chunk) === undefined) break;
      return Response.json(done({ id, jobId: body.jobId, chunk: body.chunk, ms: num(body.ms) ?? 0, image: typeof body.image === "string" ? body.image : undefined, values: Array.isArray(body.values) ? body.values : undefined }));
    case "checkpoint":
      if (!id || num(body.jobId) === undefined || num(body.chunk) === undefined) break;
      return Response.json(
        checkpoint({ id, jobId: body.jobId, chunk: body.chunk, done: num(body.done), image: typeof body.image === "string" ? body.image : undefined, values: Array.isArray(body.values) ? body.values : undefined }),
      );
    case "fill":
      if (typeof body.site !== "string") break;
      return Response.json(control({ op: "fill", site: body.site.slice(0, 32) }));
    case "leave":
      if (!id) break;
      leave(id);
      return Response.json({ ok: true });
    case "order":
      return Response.json(order({ customer: body.customer, kind: body.kind, scene: body.scene, query: body.query }));
    case "conditions": {
      if (!(body.key in CONDITIONS)) break;
      const sites = body.sites ? cleanSites(body.sites) : null;
      try {
        return Response.json(await conditions({ key: body.key as CondKey, sites: sites ? (sites as unknown as DaySite[]) : undefined }));
      } catch (e) {
        return Response.json({ error: String((e as Error).message) }, { status: 500 });
      }
    }
    case "sites": {
      const sites = cleanSites(body.sites);
      if (!sites) break;
      return Response.json(control({ op: "sites", sites: sites.map((x) => ({ ...x, tank_kwh: 0 })) }));
    }
    case "cancel":
    case "forget-offline":
    case "reset":
      return Response.json(control({ op: body.op, id, jobId: num(body.jobId) }));
  }
  return Response.json({ error: "bad request" }, { status: 400 });
}

function num(v: unknown) {
  return typeof v === "number" && Number.isFinite(v) ? v : undefined;
}
