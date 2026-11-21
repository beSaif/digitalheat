"use client";

import { use, useCallback, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { Droplets, Expand, Flame, Gauge, ShowerHead } from "lucide-react";
import { LogoMark } from "@/components/Logo";
import { IMG_H, IMG_W, TANK, WORKER_SRC, houseFor, type Assignment, type BeatReply, type NodeState } from "@/lib/live/shared";

/*
 * House screen: open on a friend's laptop at http://<operator-ip>:3000/node/basel.
 * The page itself is the server: it asks the coordinator for work, renders the tile in Web Workers
 * on every core but one, and sends the image back. Keep the page visible; hidden tabs get throttled.
 */

type Work = {
  a: Assignment;
  workers: Worker[];
  iters: number[];
  doneCount: number;
  started: number;
  progress: number;
  rate: number;
  result: { image: string; ms: number } | null;
};

const BEAT_MS = 500;
let blobUrl: string | null = null;
const workerUrl = () => (blobUrl ??= URL.createObjectURL(new Blob([WORKER_SRC], { type: "text/javascript" })));
const PREVIEW_MS = 1200;

export default function NodePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: rawId } = use(params);
  const id = rawId.toLowerCase();
  const house = houseFor(id);

  const [reply, setReply] = useState<BeatReply | null>(null);
  const [online, setOnline] = useState(true);
  const [view, setView] = useState<{ a: Assignment; progress: number; rate: number; workers: number } | null>(null);
  const [lastRate, setLastRate] = useState(0);
  const canvas = useRef<HTMLCanvasElement>(null);
  const work = useRef<Work | null>(null);
  const cores = useRef(1);

  const stop = useCallback(() => {
    work.current?.workers.forEach((w) => w.terminate());
    work.current = null;
    setView(null);
  }, []);

  const start = useCallback(
    (a: Assignment) => {
      stop();
      const n = cores.current;
      const url = workerUrl();
      const c = canvas.current!;
      c.width = a.w;
      c.height = a.h;
      const ctx = c.getContext("2d")!;
      ctx.fillStyle = "#141412";
      ctx.fillRect(0, 0, a.w, a.h);
      const img = ctx.createImageData(a.w, a.h);
      const w: Work = { a, workers: [], iters: new Array(n).fill(0), doneCount: 0, started: performance.now(), progress: 0, rate: 0, result: null };
      for (let k = 0; k < n; k++) {
        const worker = new Worker(url);
        worker.onmessage = (e: MessageEvent<{ k: number; rows: number[]; rgba: Uint8ClampedArray; iters: number; done: boolean }>) => {
          if (work.current !== w) return;
          const { rows, rgba, iters, done } = e.data;
          for (let ri = 0; ri < rows.length; ri++) img.data.set(rgba.subarray(ri * a.w * 4, (ri + 1) * a.w * 4), rows[ri] * a.w * 4);
          ctx.putImageData(img, 0, 0);
          w.iters[e.data.k] = iters;
          const total = w.iters.reduce((s, v) => s + v, 0);
          const secs = (performance.now() - w.started) / 1000;
          w.rate = total / Math.max(0.001, secs);
          if (done) w.doneCount++;
          w.progress = w.doneCount === n ? 1 : Math.min(0.99, total / a.budget);
          setView({ a, progress: w.progress, rate: w.rate, workers: n });
          if (w.doneCount === n) {
            w.result = { image: c.toDataURL("image/png"), ms: performance.now() - w.started };
            w.workers.forEach((x) => x.terminate());
            setLastRate(w.rate);
          }
        };
        worker.postMessage({ k, n, a, W: IMG_W, H: IMG_H, budget: a.budget / n, maxPasses: 4096 });
        w.workers.push(worker);
      }
      work.current = w;
      setView({ a, progress: 0, rate: 0, workers: n });
    },
    [stop],
  );

  useEffect(() => {
    cores.current = Math.max(1, (navigator.hardwareConcurrency || 4) - 1);
    let alive = true;
    let lastPreview = 0;
    const post = (body: object) =>
      fetch("/api/live", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ id, ...body }) });

    (async () => {
      while (alive) {
        try {
          const w = work.current;
          if (w?.result) {
            await post({ op: "done", jobId: w.a.jobId, tile: w.a.tile, image: w.result.image, ms: w.result.ms });
            work.current = null;
            setView(null);
          } else if (w && performance.now() - lastPreview > PREVIEW_MS && canvas.current) {
            lastPreview = performance.now();
            await post({ op: "preview", jobId: w.a.jobId, tile: w.a.tile, image: canvas.current.toDataURL("image/jpeg", 0.7) });
          }
          const cur = work.current;
          const res = await post({
            op: "beat",
            cores: cores.current,
            rate: cur?.rate || undefined,
            jobId: cur?.a.jobId,
            tile: cur?.a.tile,
            progress: cur?.progress,
          });
          if (!res.ok) throw new Error(String(res.status));
          const r: BeatReply = await res.json();
          if (!alive) break;
          setReply(r);
          setOnline(true);
          if (r.abort) stop();
          if (r.assign) start(r.assign);
        } catch {
          setOnline(false);
        }
        await new Promise((ok) => setTimeout(ok, BEAT_MS));
      }
    })();
    return () => {
      alive = false;
      stop();
    };
  }, [id, start, stop]);

  const control = (op: "full" | "shower") =>
    fetch("/api/live", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op, id }) });

  const state: NodeState = !online ? "offline" : (reply?.state ?? "idle");
  const running = state === "running" && view !== null;
  const tank = reply?.tank ?? 0;
  const theme = !online
    ? "bg-ink text-cream"
    : running
      ? "bg-rust text-cream"
      : state === "full"
        ? "bg-teal-soft text-ink"
        : "bg-cream text-ink";
  const sub = !online ? "text-cream/60" : running ? "text-cream/75" : "text-muted";

  const headline = !online
    ? "Can't reach the coordinator"
    : running
      ? "Heating the house"
      : state === "full"
        ? "Tank full · server paused"
        : "Waiting for work";
  const detail = !online
    ? "Check that this laptop is on the same Wi-Fi as the operator laptop."
    : running
      ? `Computing tile ${view!.a.tile + 1} of job #${view!.a.jobId} · ${view!.a.view.name}`
      : state === "full"
        ? `The house has all the heat it needs. Work goes to another house until the tank drops below ${TANK.resumeAt} %.`
        : "Ready. Heat is needed, so this server takes the next job that comes in.";

  return (
    <div className={clsx("fixed inset-0 z-[1000] flex flex-col overflow-hidden transition-colors duration-700", theme)}>
      {/* top bar */}
      <div className="flex items-center justify-between px-10 pt-8">
        <div className="flex items-center gap-3">
          <LogoMark size={40} />
          <div className="leading-tight">
            <div className="font-display text-[18px] font-semibold">DigitalHeat server</div>
            <div className={clsx("text-[13px]", sub)}>Live demo · this laptop is one of the fleet</div>
          </div>
        </div>
        <button
          onClick={() => document.documentElement.requestFullscreen?.()}
          className={clsx("flex items-center gap-2 rounded-md px-3 py-2 text-[13px] font-medium ring-1", running ? "ring-cream/40 hover:bg-cream/10" : "ring-line hover:bg-paper/60")}
        >
          <Expand size={15} /> Full screen
        </button>
      </div>

      {/* house + state */}
      <div className="px-10 pt-8">
        <h1 className="font-display text-[clamp(44px,7vw,96px)] font-semibold leading-[0.95]">{reply?.name ?? house.name}</h1>
        <div className="mt-4 flex items-center gap-3 text-[clamp(20px,2.2vw,30px)] font-semibold">
          <span className={clsx("inline-block size-4 rounded-full", running ? "animate-pulse bg-amber" : state === "full" ? "bg-teal" : online ? "bg-faint" : "bg-alarm")} />
          {headline}
        </div>
        <p className={clsx("mt-1 max-w-[60ch] text-[16px]", sub)}>{detail}</p>
      </div>

      {/* work + tank */}
      <div className="flex min-h-0 flex-1 items-stretch gap-10 px-10 py-8">
        <div className="flex min-w-0 flex-1 flex-col">
          <div className={clsx("relative flex min-h-0 flex-1 items-center justify-center overflow-hidden rounded-2xl", running ? "bg-rust-deep/40" : "bg-paper/70 ring-1 ring-line")}>
            <canvas ref={canvas} className={clsx("max-h-full max-w-full rounded-lg shadow-2xl", !running && "hidden")} style={{ aspectRatio: "256 / 216", height: "100%" }} />
            {!running && (
              <div className={clsx("text-center text-[18px]", sub)}>
                {state === "full" ? <Droplets size={56} className="mx-auto mb-3 text-teal" /> : <Flame size={56} className="mx-auto mb-3 opacity-40" />}
                {state === "full" ? "No work while the tank is full" : online ? "No tile right now" : "Offline"}
              </div>
            )}
          </div>
          <div className="mt-4">
            <div className={clsx("h-3 overflow-hidden rounded-full", running ? "bg-cream/20" : "bg-paper")}>
              <div className="h-full rounded-full bg-amber transition-[width] duration-300" style={{ width: `${(view?.progress ?? 0) * 100}%` }} />
            </div>
            <div className={clsx("mt-2 flex justify-between text-[15px] tabular-nums", sub)}>
              <span>{view ? `${Math.round(view.progress * 100)} %` : "–"}</span>
              <span className="flex items-center gap-1.5">
                <Gauge size={16} />
                {((view?.rate || lastRate) / 1e9).toFixed(2)} G iterations/s{view ? ` · ${view.workers} workers` : ""}
              </span>
            </div>
          </div>
        </div>

        {/* tank */}
        <div className="flex w-[clamp(200px,20vw,300px)] shrink-0 flex-col">
          <div className={clsx("text-[14px] font-semibold uppercase tracking-wide", sub)}>Hot-water tank</div>
          <div className={clsx("relative mt-3 flex-1 overflow-hidden rounded-2xl", running ? "bg-cream/15" : "bg-paper ring-1 ring-line")}>
            <div
              className={clsx("absolute inset-x-0 bottom-0 transition-[height] duration-500", state === "full" ? "bg-teal" : "bg-amber")}
              style={{ height: `${tank}%` }}
            />
            <div className="absolute inset-x-0 top-4 text-center font-display text-[56px] font-semibold tabular-nums">{Math.round(tank)}%</div>
            <div className="absolute inset-x-0 border-t-2 border-dashed border-ink/30" style={{ bottom: `${TANK.resumeAt}%` }} />
          </div>
          <div className={clsx("mt-2 text-[12px]", sub)}>Simulated and sped up for the demo</div>
          <div className="mt-5 grid grid-cols-2 gap-4">
            <Stat label="Heat delivered" value={`${(reply?.heatWh ?? 0).toFixed(1)} Wh`} sub={sub} />
            <Stat label="Tiles done" value={String(reply?.tilesDone ?? 0)} sub={sub} />
          </div>
        </div>
      </div>

      {/* controls */}
      <div className="flex items-center gap-3 px-10 pb-8">
        <button
          onClick={() => control("full")}
          disabled={!online || state === "full"}
          className="flex items-center gap-2 rounded-lg bg-teal px-5 py-3 text-[16px] font-semibold text-ink disabled:opacity-40"
        >
          <Droplets size={18} /> Tank full
        </button>
        <button
          onClick={() => control("shower")}
          disabled={!online}
          className={clsx("flex items-center gap-2 rounded-lg px-5 py-3 text-[16px] font-semibold ring-1 disabled:opacity-40", running ? "ring-cream/50 hover:bg-cream/10" : "ring-ink/20 hover:bg-paper")}
        >
          <ShowerHead size={18} /> Someone takes a hot shower
        </button>
        <span className={clsx("ml-auto text-[12px]", sub)}>Heat estimate assumes about 45 W while computing</span>
      </div>
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div>
      <div className={clsx("text-[12px]", sub)}>{label}</div>
      <div className="font-display text-[28px] font-semibold tabular-nums">{value}</div>
    </div>
  );
}
