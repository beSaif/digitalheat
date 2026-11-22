"use client";

import clsx from "clsx";
import { MoveRight, Pause } from "lucide-react";
import { AI_PART, COLS, IMG_H, IMG_W, ROWS, type Job, type JobPart, type LiveNode } from "@/lib/live/shared";

const EMBED_DIM = 384; // all-MiniLM-L6-v2

type Focus = { focus?: string | null; onFocus?: (id: string | null) => void };

/**
 * What a job looks like while it comes together, and when it is done: one view per kind of job. With
 * `marks` (the room screen) every part carries the colour of the building whose servers ran it, and a
 * legend underneath names them; hovering a name lights up that building's parts (`focus`).
 */
export function JobView({ job, nodes, className, marks = true, text = false, focus = null, onFocus }: { job: Job; nodes: Map<string, LiveNode>; className?: string; marks?: boolean; text?: boolean } & Focus) {
  const f = marks ? focus : null;
  const view =
    job.kind === "embed" ? (
      <EmbedView job={job} nodes={nodes} marks={marks} focus={f} />
    ) : job.kind === "rerank" ? (
      <RerankView job={job} nodes={nodes} marks={marks} text={text} focus={f} />
    ) : (
      <RenderMosaic job={job} nodes={nodes} marks={marks} focus={f} />
    );
  return (
    <div className={className}>
      {view}
      {marks && <Legend job={job} nodes={nodes} focus={f} onFocus={onFocus} />}
    </div>
  );
}

const CUSTOMER = "#c0653a"; // without marks (the customer's view) every part looks the same: no hint of which machine has it
const dim = (t: JobPart, focus: string | null | undefined) => !!focus && t.node !== focus;

/** A part's look: hatched while waiting, pulsing in its rack's colour while running, solid when done; a pause sign while it moves. */
function Part({ t, nodes, marks, focus }: { t: JobPart; nodes: Map<string, LiveNode>; marks: boolean; focus?: string | null }) {
  const n = t.node ? nodes.get(t.node) : undefined;
  const color = marks && n ? n.color : CUSTOMER;
  return (
    <div className={clsx("relative min-h-0 overflow-hidden transition-opacity", t.state === "pending" && "hatch-light", dim(t, focus) && "opacity-25")}>
      {t.state === "pending" && !!t.saved && <div className="absolute inset-y-0 left-0 bg-white/25" style={{ width: `${t.saved * 100}%` }} />}
      {t.state === "running" && n && (
        <>
          <div className="absolute inset-0 animate-pulse opacity-60" style={{ background: color }} />
          <div className="absolute inset-0 ring-2 ring-inset" style={{ ["--tw-ring-color" as string]: color }} />
        </>
      )}
      {t.state === "paused" && <div className="absolute inset-0 ring-2 ring-inset" style={{ ["--tw-ring-color" as string]: color }} />}
      {t.state === "done" && <div className="absolute inset-0" style={{ background: color }} />}
      {marks && (t.state === "paused" || (t.state === "pending" && !!t.saved)) && (
        <span className="absolute inset-0 grid place-items-center text-cream">
          <Pause size={11} fill="currentColor" />
        </span>
      )}
    </div>
  );
}

/** Which buildings ran the job's parts: a colour per building, the parts each did, and the parts that moved mid-way. */
function Legend({ job, nodes, focus, onFocus }: { job: Job; nodes: Map<string, LiveNode> } & Focus) {
  const by = new Map<string, { done: number; running: boolean }>();
  for (const t of job.tiles) {
    if (!t.node || (t.state !== "done" && t.state !== "running")) continue;
    const e = by.get(t.node) ?? { done: 0, running: false };
    if (t.state === "done") e.done++;
    else e.running = true;
    by.set(t.node, e);
  }
  const list = [...by.entries()].map(([id, e]) => ({ id, ...e, n: nodes.get(id) })).sort((a, b) => b.done - a.done);
  const moved = job.tiles.filter((t) => t.from && t.saved).length;
  const paused = job.tiles.filter((t) => t.state === "paused" || (t.state === "pending" && t.saved)).length;
  if (!list.length && !moved) return null;
  return (
    <div className="mt-2 px-1">
      <div className="flex flex-wrap items-center gap-1.5" onMouseLeave={() => onFocus?.(null)}>
        <span className="mr-0.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted">{job.kind === "render" ? "Rendered by" : "Computed by"}</span>
        {list.map(({ id, done, running, n }) => (
          <button
            key={id}
            onMouseEnter={() => onFocus?.(id)}
            onFocus={() => onFocus?.(id)}
            onClick={() => onFocus?.(focus === id ? null : id)}
            className={clsx(
              "flex items-center gap-1.5 rounded-full py-0.5 pl-1 pr-2 text-[12px] ring-1 transition-opacity",
              focus === id ? "bg-ink text-cream ring-ink" : "bg-card ring-line",
              focus && focus !== id && "opacity-50",
            )}
          >
            <span className={clsx("size-3 rounded-full", running && "animate-pulse")} style={{ background: n?.color ?? "#9a958a" }} />
            <span className="max-w-[110px] truncate font-semibold">{n?.name ?? "?"}</span>
            <span className={clsx("tabular-nums", focus === id ? "text-cream/70" : "text-muted")}>{done}</span>
          </button>
        ))}
      </div>
      {(moved > 0 || paused > 0) && (
        <div className="mt-1.5 flex items-center gap-1.5 text-[12px] text-muted">
          <Pause size={11} fill="currentColor" className="text-teal" />
          {paused > 0 ? `${paused} part${paused === 1 ? "" : "s"} paused (tank full), saved, waiting for a rack that needs heat` : ""}
          {paused > 0 && moved > 0 ? " · " : ""}
          {moved > 0 && (
            <span className="flex items-center gap-1">
              <MoveRight size={12} /> {moved} continued on another rack without starting over
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/*
 * A render job as it comes together. A tile in progress glows in the colour of the building rendering it,
 * with its name; a finished tile shows the image that rack sent back, with a corner in its colour. A tile
 * paused because its building's tank is full shows the progress saved so far, until another rack takes over.
 */
export function RenderMosaic({ job, nodes, className, marks = true, focus = null }: { job: Job; nodes: Map<string, LiveNode>; className?: string; marks?: boolean; focus?: string | null }) {
  return (
    <div
      className={clsx("grid overflow-hidden rounded-xl bg-ink", className)}
      style={{ aspectRatio: `${IMG_W} / ${IMG_H}`, gridTemplateColumns: `repeat(${COLS}, 1fr)`, gridTemplateRows: `repeat(${ROWS}, 1fr)` }}
    >
      {job.tiles.map((t) => {
        const n = t.node ? nodes.get(t.node) : undefined;
        const color = n?.color ?? "#9a958a";
        const saved = !!t.saved && t.state !== "done";
        return (
          <div key={t.i} className={clsx("relative min-h-0 overflow-hidden transition-opacity", dim(t, focus) && "opacity-25")}>
            {t.state === "done" ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`/api/live/tile?job=${job.id}&i=${t.i}&v=${t.v}`} alt="" className="absolute inset-0 size-full object-cover" />
            ) : saved ? (
              // the progress saved when its rack paused: the next rack continues from it
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`/api/live/tile?job=${job.id}&i=${t.i}&ckpt=1&v=${t.v}`} alt="" className={clsx("absolute inset-0 size-full object-cover", t.state === "running" ? "opacity-70" : "opacity-45")} />
            ) : (
              <Part t={t} nodes={nodes} marks={marks} />
            )}
            {saved && t.state === "running" && <div className="absolute inset-0 animate-pulse opacity-35" style={{ background: marks ? color : CUSTOMER }} />}
            {saved && t.state === "running" && <div className="absolute inset-0 ring-2 ring-inset" style={{ ["--tw-ring-color" as string]: marks ? color : CUSTOMER }} />}
            {marks && t.state === "done" && n && <div className="absolute left-0 top-0 size-3.5" style={{ background: color, clipPath: "polygon(0 0, 100% 0, 0 100%)" }} />}
            {marks && focus && t.node === focus && t.state === "done" && <div className="absolute inset-0 ring-2 ring-inset" style={{ ["--tw-ring-color" as string]: color }} />}
            {marks && t.state === "running" && n && (
              <span className="absolute bottom-0.5 left-0.5 max-w-[calc(100%-4px)] truncate rounded-[4px] px-1 text-[10px] font-semibold leading-[14px] text-white" style={{ background: color }}>
                {n.name}
              </span>
            )}
            {marks && (t.state === "paused" || (t.state === "pending" && saved)) && (
              <span className="absolute inset-0 grid place-items-center">
                <span className="flex items-center gap-1 rounded-full bg-ink/80 px-1.5 text-[10px] font-semibold leading-[16px] text-cream">
                  <Pause size={9} fill="currentColor" />
                  {t.state === "paused" ? "saving" : `${Math.round((t.saved ?? 0) * 100)} %`}
                </span>
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

const doneItems = (job: Job) => job.tiles.filter((t) => t.state === "done").length * AI_PART;

/*
 * Embeddings: the abstracts go out in parts of AI_PART; each square is one part, coloured by the rack
 * that turned its abstracts into vectors. Underneath: how many are done, and what was just embedded.
 */
function EmbedView({ job, nodes, className, marks, focus }: { job: Job; nodes: Map<string, LiveNode>; className?: string; marks: boolean; focus?: string | null }) {
  const total = job.tiles.length * AI_PART;
  const done = doneItems(job);
  return (
    <div className={className}>
      <div className="grid gap-1 rounded-xl bg-ink p-1" style={{ gridTemplateColumns: "repeat(10, 1fr)" }}>
        {job.tiles.map((t) => (
          <div key={t.i} className="grid aspect-square overflow-hidden rounded-[5px] bg-white/5">
            <Part t={t} nodes={nodes} marks={marks} focus={focus} />
          </div>
        ))}
      </div>
      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-x-3 px-1 text-[13px]">
        <span className="font-semibold tabular-nums">{job.doneAt ? `${total} vectors ready` : `${done} of ${total} abstracts embedded`}</span>
        <span className="text-muted">
          {AI_PART} abstracts per square · {EMBED_DIM} numbers per vector
        </span>
      </div>
      {!job.doneAt && job.latest?.length ? (
        <div className="mt-2 px-1">
          <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted">Just embedded</div>
          <ul className="mt-1 space-y-0.5">
            {job.latest.map((title, k) => (
              <li key={k} className="line-clamp-1 text-[13px] leading-snug">
                {title}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

/*
 * Reranking: the result is the ranking, so that leads. The parts are only a slim strip above it, each
 * segment coloured by the rack that scored those candidates.
 */
function RerankView({ job, nodes, className, marks, text, focus }: { job: Job; nodes: Map<string, LiveNode>; className?: string; marks: boolean; text: boolean; focus?: string | null }) {
  const total = job.tiles.length * AI_PART;
  const done = doneItems(job);
  return (
    <div className={className}>
      <div className="grid h-3 gap-px overflow-hidden rounded-full bg-ink" style={{ gridTemplateColumns: `repeat(${job.tiles.length}, 1fr)` }}>
        {job.tiles.map((t) => (
          <Part key={t.i} t={t} nodes={nodes} marks={marks} focus={focus} />
        ))}
      </div>
      <div className="mt-1.5 px-1 text-[12.5px] tabular-nums text-muted">
        {done} of {total} candidate abstracts scored against the question
      </div>
      <div className="mt-3 px-1">
        <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted">{job.doneAt ? "Best matches" : "Best matches so far"}</div>
        {job.top?.length ? <TopHits job={job} text={text} /> : <div className="text-[13px] text-muted">Scoring the first candidates…</div>}
      </div>
    </div>
  );
}

/** Who rendered a job: tiles per rack, most first. */
export function contributors(job: Job, nodes: Map<string, LiveNode>) {
  const count = new Map<string, number>();
  for (const t of job.tiles) if (t.state === "done" && t.node) count.set(t.node, (count.get(t.node) ?? 0) + 1);
  return [...count.entries()]
    .map(([id, tiles]) => ({ id, tiles, node: nodes.get(id) }))
    .sort((a, b) => b.tiles - a.tiles);
}

export const jobSeconds = (job: Job, now: number) => ((job.doneAt ?? now) - (job.startedAt ?? job.createdAt)) / 1000;

/** Reranking: the best abstracts for the customer's question so far, with the model's score. */
export function TopHits({ job, className, text = false }: { job: Job; className?: string; text?: boolean }) {
  if (!job.top?.length) return null;
  return (
    <ol className={clsx("space-y-1.5", className)}>
      {job.top.map((h, k) => (
        <li key={k} className="flex gap-2 text-[13px] leading-snug">
          <span className="w-4 shrink-0 font-semibold tabular-nums text-muted">{k + 1}</span>
          <span className="min-w-0 flex-1">
            <span className="line-clamp-1 font-semibold">{h.title}</span>
            {text && <span className="line-clamp-2 text-[12px] text-muted">{h.text}</span>}
          </span>
          <span className="shrink-0 tabular-nums text-muted">{h.score.toFixed(1)}</span>
        </li>
      ))}
    </ol>
  );
}
