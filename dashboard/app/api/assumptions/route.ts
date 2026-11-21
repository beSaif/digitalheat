import { runPython } from "@/lib/server/python";

/* GET → every assumption with its value and source (python -m scheduler.assumptions --json). */
export async function GET() {
  try {
    return new Response(await runPython("scheduler.assumptions", ["--json"]), { headers: { "content-type": "application/json" } });
  } catch (e) {
    return Response.json({ error: String((e as Error).message) }, { status: 500 });
  }
}
