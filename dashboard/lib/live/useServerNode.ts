"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { IMG_H, IMG_W, WORKER_SRC, type Assignment, type BeatReply, type Device } from "./shared";

/*
 * Turns the current browser tab into a DigitalHeat server: asks the coordinator for work every
 * half second and runs the part it is given: a render tile path-traced in Web Workers, or AI
 * embeddings / reranking of a few abstracts in the AI worker (public/ai/worker.js, which keeps its
 * model loaded). Progress is drawn into the returned `canvas` (attach it to a <canvas> that stays
 * mounted) and the finished part goes back with its image and, for AI, its values.
 *
 * When the scheduler switches the rack off mid-part (its tank is full), the server saves its progress
 * (a checkpoint: the tile so far and the samples traced, or the AI items done) before it stops, and a
 * part resumed from a checkpoint continues where the other rack stopped: a render tile starts from the
 * saved image and averages its new samples with the saved ones, an AI part does only the items left.
 *
 * With `leaveWhenHidden` the server says goodbye when the page is hidden (phone locked, tab switched):
 * the coordinator hands its chunk on at once, and the server rejoins in the same slot when it comes back.
 */

type Work = {
  a: Assignment;
  workers: Worker[];
  iters: number[];
  doneCount: number;
  started: number;
  progress: number;
  rate: number;
  result: { ms: number; image: string; values?: number[] | number[][] } | null;
  /** render resumed from a checkpoint: the saved image in linear light, its samples per pixel and in all */
  base?: { v: Float32Array; spp: number; samples: number } | null;
  /** AI: the values of the items done so far, for a checkpoint */
  partial?: (number[] | number)[];
};

/* The path tracer's tone curve (WORKER_SRC: v/(1+v), gamma 2.2) and its inverse, to average saved and new samples in linear light. */
const DEC = Float32Array.from({ length: 256 }, (_, c) => {
  const g = Math.min(0.9995, Math.pow(c / 255, 2.2));
  return g / (1 - g);
});
const enc = (v: number) => 255 * Math.pow(v / (1 + v), 1 / 2.2);

async function loadBase(a: Assignment) {
  if (!a.resume) return null;
  try {
    const blob = await fetch(`/api/live/tile?job=${a.jobId}&i=${a.chunk}&ckpt=1&v=${a.resume.v}`).then((r) => (r.ok ? r.blob() : Promise.reject()));
    const bmp = await createImageBitmap(blob);
    const c = document.createElement("canvas");
    c.width = a.w;
    c.height = a.h;
    const ctx = c.getContext("2d")!;
    ctx.drawImage(bmp, 0, 0, a.w, a.h);
    const px = ctx.getImageData(0, 0, a.w, a.h);
    const v = new Float32Array(a.w * a.h * 3);
    for (let p = 0; p < a.w * a.h; p++) for (let k = 0; k < 3; k++) v[p * 3 + k] = DEC[px.data[p * 4 + k]];
    return { v, spp: a.resume.done / (a.w * a.h), samples: a.resume.done, px };
  } catch {
    return null;
  }
}

export type ServerView = { a: Assignment; progress: number; rate: number; workers: number; loading?: boolean };

/** AI part canvas: one row per abstract (embed: its 384 numbers as colours; rerank: its score as a bar). */
const AI_W = 384;
const AI_H = 360;
function drawAiRow(ctx: CanvasRenderingContext2D, kind: string, i: number, n: number, values: number[] | number) {
  const h = AI_H / n;
  const y = Math.round(i * h);
  const hh = Math.round((i + 1) * h) - y;
  if (kind === "embed" && Array.isArray(values)) {
    for (let d = 0; d < values.length && d < AI_W; d++) {
      const v = Math.max(-1, Math.min(1, values[d] * 9));
      ctx.fillStyle = v >= 0 ? `rgb(${Math.round(20 + 172 * v)},${Math.round(20 + 81 * v)},${Math.round(18 + 40 * v)})` : `rgb(${Math.round(20 + 75 * -v)},${Math.round(20 + 148 * -v)},${Math.round(18 + 158 * -v)})`;
      ctx.fillRect(d, y, 1, hh);
    }
  } else if (typeof values === "number") {
    const p = Math.max(0, Math.min(1, (values + 11.5) / 14)); // the model's scores run from about -11 (unrelated) to +3 (a match)
    ctx.fillStyle = "#26241f";
    ctx.fillRect(0, y, AI_W, hh);
    ctx.fillStyle = values > 0 ? "#f2a65a" : "#c0653a";
    ctx.fillRect(0, y + 3, Math.max(4, Math.round(AI_W * p)), hh - 6);
  }
}
let aiTask = 0;

const BEAT_MS = 500;
let blobUrl: string | null = null;
const workerUrl = () => (blobUrl ??= URL.createObjectURL(new Blob([WORKER_SRC], { type: "text/javascript" })));

const post = (body: object) =>
  fetch("/api/live", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });

export function useServerNode(
  id: string | null,
  opts: { name?: string; workers?: number; device?: Device; leaveWhenHidden?: boolean; enabled?: boolean } = {},
) {
  const { name, workers: workerCount, device = "laptop", leaveWhenHidden = false, enabled = true } = opts;
  const [reply, setReply] = useState<BeatReply | null>(null);
  const [online, setOnline] = useState(true);
  const [hidden, setHidden] = useState(false);
  const [view, setView] = useState<ServerView | null>(null);
  const [lastRate, setLastRate] = useState(0);
  const work = useRef<Work | null>(null);
  const aiWorker = useRef<Worker | null>(null); // one per server, created on its first AI part, keeps its models loaded
  const cores = useRef(1);
  const canvas = useRef<HTMLCanvasElement>(null);
  const nameRef = useRef(name);
  useEffect(() => {
    nameRef.current = name;
  }, [name]);

  const stop = useCallback(() => {
    work.current?.workers.forEach((w) => w.terminate());
    work.current = null;
    setView(null);
  }, []);

  const startAi = useCallback(
    (a: Assignment) => {
      const c = canvas.current;
      if (!c) return;
      const texts = a.texts ?? [];
      c.width = AI_W;
      c.height = AI_H;
      const ctx = c.getContext("2d")!;
      ctx.fillStyle = "#141412";
      ctx.fillRect(0, 0, AI_W, AI_H);
      const task = ++aiTask;
      const w: Work = { a, workers: [], iters: [], doneCount: 0, started: performance.now(), progress: 0, rate: 0, result: null, partial: [] };
      const ai = (aiWorker.current ??= new Worker("/ai/worker.js", { type: "module" }));
      const onMsg = (e: MessageEvent<{ task: number; type: string; i?: number; values?: number[] | number | (number[] | number)[]; ms?: number; message?: string }>) => {
        const m = e.data;
        if (m.task !== task) return;
        if (work.current !== w) {
          ai.removeEventListener("message", onMsg);
          return;
        }
        if (m.type === "loading") setView({ a, progress: 0, rate: 0, workers: 1, loading: true });
        if (m.type === "item" && m.i !== undefined && m.values !== undefined) {
          drawAiRow(ctx, a.jobType, m.i, texts.length, m.values as number[] | number);
          w.partial![m.i] = m.values as number[] | number;
          w.doneCount = m.i + 1;
          w.progress = Math.min(0.99, w.doneCount / texts.length);
          w.rate = w.doneCount / Math.max(0.001, (performance.now() - w.started) / 1000);
          setView({ a, progress: w.progress, rate: w.rate, workers: 1 });
        }
        if (m.type === "done") {
          ai.removeEventListener("message", onMsg);
          w.result = { ms: m.ms ?? performance.now() - w.started, image: c.toDataURL("image/jpeg", 0.85), values: m.values as number[] | number[][] };
          w.progress = 1;
          setView({ a, progress: 1, rate: w.rate, workers: 1 });
          setLastRate(w.rate);
        }
        if (m.type === "error") {
          ai.removeEventListener("message", onMsg);
          console.error("AI worker:", m.message);
        }
      };
      ai.addEventListener("message", onMsg);
      ai.postMessage({ task, kind: a.jobType, texts, query: a.query });
      work.current = w;
      setView({ a, progress: 0, rate: 0, workers: 1 });
    },
    [canvas],
  );

  const start = useCallback(
    (a: Assignment) => {
      stop();
      if (a.jobType !== "render") return startAi(a);
      const c = canvas.current;
      if (!c) return;
      const n = cores.current;
      const url = workerUrl();
      c.width = a.w;
      c.height = a.h;
      const ctx = c.getContext("2d")!;
      ctx.fillStyle = "#141412";
      ctx.fillRect(0, 0, a.w, a.h);
      const img = ctx.createImageData(a.w, a.h);
      const w: Work = { a, workers: [], iters: new Array(n).fill(0), doneCount: 0, started: performance.now(), progress: 0, rate: 0, result: null, base: null };
      const spawn = (k: number) => {
        const worker = new Worker(url);
        worker.onmessage = (e: MessageEvent<{ k: number; rows: number[]; rgba: Uint8ClampedArray; iters: number; passes: number; done: boolean }>) => {
          if (work.current !== w) return;
          const { rows, rgba, iters, passes, done } = e.data;
          const b = w.base;
          for (let ri = 0; ri < rows.length; ri++) {
            if (!b) {
              img.data.set(rgba.subarray(ri * a.w * 4, (ri + 1) * a.w * 4), rows[ri] * a.w * 4);
              continue;
            }
            // resumed: average the saved samples and this rack's new ones, weighted by their counts
            const wb = b.spp / (b.spp + Math.max(1, passes));
            for (let x = 0; x < a.w; x++) {
              const o = rows[ri] * a.w + x,
                q = (ri * a.w + x) * 4;
              for (let c = 0; c < 3; c++) img.data[o * 4 + c] = enc(wb * b.v[o * 3 + c] + (1 - wb) * DEC[rgba[q + c]]);
              img.data[o * 4 + 3] = 255;
            }
          }
          ctx.putImageData(img, 0, 0);
          w.iters[e.data.k] = iters;
          const total = w.iters.reduce((s, v) => s + v, 0);
          const secs = (performance.now() - w.started) / 1000;
          w.rate = total / Math.max(0.001, secs);
          if (done) w.doneCount++;
          const saved = w.base?.samples ?? 0;
          w.progress = w.doneCount === n ? 1 : Math.min(0.99, (saved + total) / (saved + a.budget));
          setView({ a, progress: w.progress, rate: w.rate, workers: n });
          if (w.doneCount === n) {
            w.result = { ms: performance.now() - w.started, image: c.toDataURL("image/jpeg", 0.88) };
            w.workers.forEach((x) => x.terminate());
            setLastRate(w.rate);
          }
        };
        worker.postMessage({ k, n, a, W: IMG_W, H: IMG_H, budget: a.budget / n });
        w.workers.push(worker);
      };
      work.current = w;
      setView({ a, progress: 0, rate: 0, workers: n });
      if (!a.resume) for (let k = 0; k < n; k++) spawn(k);
      else
        loadBase(a).then((b) => {
          if (work.current !== w) return;
          if (b) {
            w.base = b;
            img.data.set(b.px.data);
            ctx.putImageData(img, 0, 0);
          }
          for (let k = 0; k < n; k++) spawn(k);
        });
    },
    [canvas, stop, startAi],
  );

  // Phones: leave when the page is hidden, come back when it is shown again.
  useEffect(() => {
    if (!id || !enabled || !leaveWhenHidden) return;
    const onHide = () => {
      if (document.visibilityState !== "hidden") return;
      stop();
      setHidden(true);
      navigator.sendBeacon?.("/api/live", new Blob([JSON.stringify({ op: "leave", id })], { type: "application/json" }));
    };
    const onShow = () => document.visibilityState === "visible" && setHidden(false);
    document.addEventListener("visibilitychange", onHide);
    document.addEventListener("visibilitychange", onShow);
    window.addEventListener("pagehide", onHide);
    return () => {
      document.removeEventListener("visibilitychange", onHide);
      document.removeEventListener("visibilitychange", onShow);
      window.removeEventListener("pagehide", onHide);
    };
  }, [id, enabled, leaveWhenHidden, stop]);

  useEffect(() => {
    if (!id || !enabled || hidden) return;
    const hc = navigator.hardwareConcurrency || 4;
    cores.current = Math.max(1, Math.min(workerCount ?? hc - 1, hc - 1));
    let alive = true;
    const send = (body: object) => post({ id, ...body });

    (async () => {
      while (alive) {
        let ok = false;
        try {
          const w = work.current;
          if (w?.result) {
            await send({ op: "done", jobId: w.a.jobId, chunk: w.a.chunk, ms: w.result.ms, image: w.result.image, values: w.result.values });
            if (work.current === w) {
              work.current = null;
              setView(null);
            }
          }
          const cur = work.current;
          const res = await send({
            op: "beat",
            name: nameRef.current,
            cores: cores.current,
            device,
            rate: cur?.rate || undefined,
            jobId: cur?.a.jobId,
            chunk: cur?.a.chunk,
            progress: cur?.progress,
          });
          if (!res.ok) throw new Error(String(res.status));
          const r: BeatReply = await res.json();
          if (!alive) break;
          setReply(r);
          setOnline(true);
          ok = true;
          if (r.abort) {
            const cur = work.current;
            const snap = r.checkpoint && cur && !cur.result ? snapshot(cur, canvas.current) : null;
            stop();
            if (cur && snap) await send({ op: "checkpoint", jobId: cur.a.jobId, chunk: cur.a.chunk, ...snap }).catch(() => {});
          }
          if (r.assign) start(r.assign);
        } catch {
          if (alive) setOnline(false);
        }
        // finished tiles go back at once; otherwise wait for the next beat
        await new Promise((go) => setTimeout(go, ok && work.current?.result ? 30 : BEAT_MS));
      }
    })();
    return () => {
      alive = false;
      stop();
      aiWorker.current?.terminate();
      aiWorker.current = null;
    };
  }, [id, enabled, hidden, workerCount, device, canvas, start, stop]);

  return { canvas, reply, online: online && !hidden, hidden, view, lastRate };
}

/** A part's progress when its rack is paused: render, the tile so far and the samples traced (with the saved ones); AI, the items done. */
function snapshot(w: Work, c: HTMLCanvasElement | null) {
  if (w.a.jobType === "render") {
    const done = (w.base?.samples ?? 0) + w.iters.reduce((s, v) => s + v, 0);
    return c ? { done, image: c.toDataURL("image/png") } : null;
  }
  const values: (number[] | number)[] = [];
  for (const v of w.partial ?? []) {
    if (v === undefined) break;
    values.push(v);
  }
  return values.length ? { values } : null;
}
