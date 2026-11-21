import { image } from "@/lib/live/coordinator";

/** GET /api/live/tile?job=1&i=7&v=3 → the latest image of that tile (v only busts the browser cache). */
export async function GET(request: Request) {
  const q = new URL(request.url).searchParams;
  const img = image(Number(q.get("job")), Number(q.get("i")));
  if (!img) return new Response(null, { status: 404 });
  return new Response(new Uint8Array(img.buf), {
    headers: { "content-type": img.type, "cache-control": "private, max-age=3600" },
  });
}
