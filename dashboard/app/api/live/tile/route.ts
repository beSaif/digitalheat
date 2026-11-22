import { image } from "@/lib/live/coordinator";

/** GET /api/live/tile?job=1&i=7&v=1 → a rendered tile; &ckpt=1 → a paused tile's saved progress (v only busts the browser cache). */
export async function GET(request: Request) {
  const q = new URL(request.url).searchParams;
  const buf = image(Number(q.get("job")), Number(q.get("i")), q.get("ckpt") === "1");
  if (!buf) return new Response(null, { status: 404 });
  const png = buf[0] === 0x89 && buf[1] === 0x50;
  return new Response(new Uint8Array(buf), { headers: { "content-type": png ? "image/png" : "image/jpeg", "cache-control": "private, max-age=3600" } });
}
