import { beat, control, done, preview, state } from "@/lib/live/coordinator";

/*
 * Live demo coordinator.
 * GET  → full state for the operator screen.
 * POST → { op: "beat" | "preview" | "done" } from house laptops, or a control op from the operator screen.
 */

export async function GET(request: Request) {
  return Response.json(state(request.headers.get("host")), { headers: { "cache-control": "no-store" } });
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.op !== "string") return Response.json({ error: "bad request" }, { status: 400 });
  const id = typeof body.id === "string" ? body.id.toLowerCase().replace(/[^a-z0-9-]/g, "").slice(0, 32) : undefined;
  switch (body.op) {
    case "beat":
      if (!id) break;
      return Response.json(
        beat({ id, cores: num(body.cores), rate: num(body.rate), jobId: num(body.jobId), tile: num(body.tile), progress: num(body.progress) }),
      );
    case "preview":
      if (!id || typeof body.image !== "string") break;
      preview({ id, jobId: body.jobId, tile: body.tile, image: body.image });
      return Response.json({ ok: true });
    case "done":
      if (!id || typeof body.image !== "string") break;
      return Response.json(done({ id, jobId: body.jobId, tile: body.tile, image: body.image, ms: num(body.ms) ?? 0 }));
    case "submit":
    case "full":
    case "shower":
    case "forget":
    case "reset":
      return Response.json(control({ op: body.op, id, size: body.size }));
  }
  return Response.json({ error: "bad request" }, { status: 400 });
}

function num(v: unknown) {
  return typeof v === "number" && Number.isFinite(v) ? v : undefined;
}
