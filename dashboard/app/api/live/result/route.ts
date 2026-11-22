import { result } from "@/lib/live/coordinator";

/** GET /api/live/result?job=3 → an AI job's output as JSON: embeddings or reranking scores per abstract. */
export async function GET(request: Request) {
  const id = Number(new URL(request.url).searchParams.get("job"));
  const r = result(id);
  if (!r) return new Response(null, { status: 404 });
  return new Response(JSON.stringify(r), {
    headers: { "content-type": "application/json", "content-disposition": `attachment; filename="digitalheat-${r.job}-${id}.json"` },
  });
}
