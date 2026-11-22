"use client";

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { Box, Check, Download, ListOrdered, Rows3, Send } from "lucide-react";
import { LogoMark } from "@/components/Logo";
import { JobView, jobSeconds } from "@/components/RenderMosaic";
import { COLS, IMG_H, IMG_W, ITEMS, PRODUCTS, SCENES, TILE_H, TILE_W, quote, type Job, type JobKind, type LiveState, type SceneKey } from "@/lib/live/shared";

/*
 * Client screen, for the jury: DigitalHeat's customer. It reads like a cloud order page: pick a job
 * (a 3D rendering, AI embeddings or AI reranking of science abstracts), see the price, order, and get
 * the output. Every job in the demo comes from here. Prices: the job's server time on the 1 kW
 * reference server (AI: measured, workloads/catalog.py; rendering: estimated) at DigitalHeat's price
 * per server-hour (data/prices_2026.json, data/business_assumptions.json).
 */

const KEY = "dh-client-jobs";
const DL = "ml-auto flex items-center gap-1.5 rounded-full bg-ink px-4 py-2 text-[14px] font-semibold text-cream";
const SWATCH: Record<SceneKey, string> = {
  warm: "linear-gradient(90deg,#b8542e 0 30%,#e8dfd0 30% 70%,#4f9aa1 70%)",
  day: "linear-gradient(90deg,#8ea1b3 0 30%,#eef0ef 30% 70%,#dccfb0 70%)",
  gallery: "linear-gradient(90deg,#e9e8e4 0 45%,#c0653a 45% 55%,#e9e8e4 55%)",
};
const ICON: Record<JobKind, typeof Box> = { render: Box, embed: Rows3, rerank: ListOrdered };
const WHAT: Record<JobKind, string> = {
  render: `${IMG_W} × ${IMG_H} px image`,
  embed: `${ITEMS.embed} science abstracts`,
  rerank: `${ITEMS.rerank} science abstracts ranked for your question`,
};
const QUESTIONS = ["The risk of cancer rises with level of alcohol consumption.", "Aspirin inhibits the production of PGE2.", "Medications to treat obesity are highly effective."];

/** CHF with enough decimals to show small amounts */
function chf(v: number) {
  if (v >= 1) return `CHF ${v.toFixed(2)}`;
  if (v >= 0.01) return `CHF ${v.toFixed(3)}`;
  return `CHF ${v.toFixed(4)}`;
}

export default function ClientPage() {
  const [s, setS] = useState<LiveState | null>(null);
  const [kind, setKind] = useState<JobKind>("render");
  const [scene, setScene] = useState<SceneKey>("warm");
  const [question, setQuestion] = useState("");
  const [mine, setMine] = useState<number[]>([]);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    Promise.resolve().then(() => {
      try {
        setMine(JSON.parse(localStorage.getItem(KEY) ?? "[]"));
      } catch {}
    });
    let alive = true;
    const pull = () =>
      fetch("/api/live", { cache: "no-store" })
        .then((r) => r.json())
        .then((d) => alive && setS(d))
        .catch(() => {});
    pull();
    const id = setInterval(pull, 700);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const send = async () => {
    setSending(true);
    try {
      const r = await fetch("/api/live", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ op: "order", kind, scene, query: question.trim() || QUESTIONS[0] }),
      });
      const { id } = await r.json();
      const next = [...mine, id];
      setMine(next);
      localStorage.setItem(KEY, JSON.stringify(next));
      setTimeout(() => document.getElementById(`job-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" }), 900);
    } finally {
      setSending(false);
    }
  };

  const nodes = useMemo(() => new Map((s?.nodes ?? []).map((n) => [n.id, n])), [s]);
  const jobs = (s?.jobs ?? []).filter((j) => mine.includes(j.id)); // oldest first: a new order goes to the end
  const q = s?.pricing ? quote(kind, s.pricing) : null;

  return (
    <div className="fixed inset-0 z-[1000] overflow-y-auto bg-cream text-ink">
      <div className="mx-auto max-w-[720px] px-4 py-5 sm:px-6 sm:py-8">
        {/* header */}
        <div className="flex items-center gap-3">
          <LogoMark size={32} />
          <div className="min-w-0 leading-tight">
            <div className="font-display text-[19px] font-semibold sm:text-[22px]">DigitalHeat Cloud</div>
            <div className="text-[13px] text-muted">Pick a service, pay per job</div>
          </div>
        </div>

        {/* order */}
        <div className="mt-5 rounded-[22px] bg-card p-4 ring-1 ring-line sm:p-5">
          <div className="grid grid-cols-3 gap-2">
            {(Object.keys(PRODUCTS) as JobKind[]).map((k) => {
              const Icon = ICON[k];
              return (
                <button
                  key={k}
                  onClick={() => setKind(k)}
                  className={clsx(
                    "flex flex-col items-center gap-1.5 rounded-xl px-2 py-3 text-center text-[13.5px] font-semibold leading-tight ring-1",
                    kind === k ? "bg-ink text-cream ring-ink" : "ring-line hover:bg-cream",
                  )}
                >
                  <Icon size={20} />
                  {PRODUCTS[k].label}
                </button>
              );
            })}
          </div>

          <div className="mt-4 text-[13px] text-muted">{WHAT[kind]}</div>

          {kind === "render" && (
            <div className="mt-2 grid gap-2 sm:grid-cols-3">
              {(Object.keys(SCENES) as SceneKey[]).map((k) => (
                <button
                  key={k}
                  onClick={() => setScene(k)}
                  className={clsx("flex items-center gap-3 rounded-xl p-2 text-left ring-1 sm:block", scene === k ? "bg-cream ring-2 ring-rust" : "ring-line hover:bg-cream")}
                >
                  <div className="h-10 w-16 shrink-0 rounded-md sm:h-8 sm:w-auto" style={{ background: SWATCH[k] }} />
                  <div className="text-[14px] font-semibold sm:mt-1.5 sm:text-[13px]">{SCENES[k].label}</div>
                </button>
              ))}
            </div>
          )}

          {kind === "rerank" && (
            <div className="mt-2">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={QUESTIONS[0]}
                maxLength={200}
                className="w-full rounded-xl bg-cream px-3 py-2.5 text-[15px] outline-none ring-1 ring-line placeholder:text-faint focus:ring-2 focus:ring-rust"
              />
              <div className="mt-2 flex flex-wrap gap-1.5">
                {QUESTIONS.map((x) => (
                  <button key={x} onClick={() => setQuestion(x)} className="rounded-full px-2.5 py-1 text-left text-[12px] ring-1 ring-line hover:bg-cream">
                    {x}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* quote */}
          {q && (
            <div className="mt-4 rounded-2xl bg-cream p-4 ring-1 ring-line">
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-[13px] text-muted">Price per {PRODUCTS[kind].perLabel}</span>
                <span className="font-display text-[28px] font-semibold tabular-nums">{chf(q.perUnits)}</span>
              </div>
              <button
                onClick={send}
                disabled={sending}
                className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-rust px-5 py-3 text-[16px] font-semibold text-cream hover:bg-rust-deep disabled:opacity-50"
              >
                <Send size={17} /> Order · {chf(q.chf)}
              </button>
            </div>
          )}
        </div>

        {/* orders */}
        <div className="mt-5 space-y-5">
          {s &&
            jobs.map((j) => (
              <Order key={j.id} j={j} s={s} nodes={nodes} />
            ))}
        </div>
      </div>
    </div>
  );
}

function Order({ j, s, nodes }: { j: Job; s: LiveState; nodes: Map<string, LiveState["nodes"][number]> }) {
  const done = j.tiles.filter((t) => t.state === "done").length;
  const jq = quote(j.kind, s.pricing);
  return (
    <div id={`job-${j.id}`} className="scroll-mt-4 rounded-[22px] bg-card p-4 ring-1 ring-line sm:p-5">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <div className="text-[17px] font-semibold">
          {PRODUCTS[j.kind].label}
          {j.scene && <span className="font-normal text-muted"> · {SCENES[j.scene].label}</span>}
        </div>
        <div className="text-[13.5px] tabular-nums text-muted">
          {new Date(j.createdAt).toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" })} ·{" "}
          {j.doneAt ? `Ready in ${jobSeconds(j, s.now).toFixed(0)} s` : j.startedAt ? `Running · ${Math.round((100 * done) / j.tiles.length)}%` : "In the queue"}
        </div>
        {j.doneAt &&
          (j.kind === "render" ? (
            <button onClick={() => downloadImage(j.id, j.scene ?? "render")} className={DL}>
              <Download size={15} /> Download
            </button>
          ) : (
            <a href={`/api/live/result?job=${j.id}`} download className={DL}>
              <Download size={15} /> Download JSON
            </a>
          ))}
      </div>
      {j.query && <div className="mt-1 text-[14px] italic">“{j.query}”</div>}
      <JobView job={j} nodes={nodes} className="mt-3" marks={false} text />
      {j.doneAt && (
        <div className="mt-3 flex items-center gap-1.5 text-[13.5px] font-semibold">
          <Check size={15} className="text-[#3aa35b]" /> Charged {chf(jq.chf)}
        </div>
      )}
    </div>
  );
}

/** Put the tiles together into one image and save it. */
async function downloadImage(jobId: number, scene: string) {
  const c = document.createElement("canvas");
  c.width = IMG_W;
  c.height = IMG_H;
  const ctx = c.getContext("2d")!;
  const tiles = (IMG_W / TILE_W) * (IMG_H / TILE_H);
  await Promise.all(
    Array.from({ length: tiles }, (_, i) =>
      new Promise<void>((ok) => {
        const img = new Image();
        img.onload = () => {
          ctx.drawImage(img, (i % COLS) * TILE_W, Math.floor(i / COLS) * TILE_H);
          ok();
        };
        img.onerror = () => ok();
        img.src = `/api/live/tile?job=${jobId}&i=${i}`;
      }),
    ),
  );
  const a = document.createElement("a");
  a.href = c.toDataURL("image/png");
  a.download = `digitalheat-render-${jobId}-${scene}.png`;
  a.click();
}
