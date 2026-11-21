"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { Droplets, Laptop, Play, RotateCcw, ShowerHead, X } from "lucide-react";
import { Card, CardTitle, Chip } from "@/components/ui";
import {
  COLS,
  HOUSES,
  IMG_H,
  IMG_W,
  ROWS,
  SIZES,
  TANK,
  type LiveJob,
  type LiveNode,
  type LiveState,
  type NodeState,
  type SizeKey,
} from "@/lib/live/shared";

/*
 * Live demo, operator screen. Real laptops open /node/<house> and act as servers;
 * this page submits render jobs and shows where each tile goes and why.
 */

const STATE: Record<NodeState, { label: string; tone: "neutral" | "rust" | "teal" | "ink" }> = {
  running: { label: "Heating · computing", tone: "rust" },
  idle: { label: "Needs heat · waiting", tone: "neutral" },
  full: { label: "Tank full · paused", tone: "teal" },
  offline: { label: "Offline", tone: "ink" },
};

async function send(body: object) {
  const r = await fetch("/api/live", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  return (await r.json()) as LiveState;
}

export default function LivePage() {
  const [s, setS] = useState<LiveState | null>(null);
  const [size, setSize] = useState<SizeKey>("M");

  useEffect(() => {
    let alive = true;
    const pull = async () => {
      try {
        const r = await fetch("/api/live", { cache: "no-store" });
        const next = (await r.json()) as LiveState;
        if (alive) setS(next);
      } catch {}
    };
    pull();
    const t = setInterval(pull, 500);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const act = async (body: object) => setS(await send(body));
  const job = s?.jobs.at(-1);
  const nodes = s?.nodes ?? [];
  const byId = new Map(nodes.map((n) => [n.id, n]));

  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      {/* header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-[40px] font-semibold leading-none">Live demo</h1>
          <p className="mt-2.5 text-[15px] text-muted">
            Real laptops acting as DigitalHeat servers. A job only goes to a house that needs heat; a full tank hands its work on.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex rounded-full bg-paper p-1 ring-1 ring-line">
            {(Object.keys(SIZES) as SizeKey[]).map((k) => (
              <button
                key={k}
                onClick={() => setSize(k)}
                className={clsx(
                  "rounded-full px-3.5 py-1.5 text-[13px] font-medium",
                  size === k ? "bg-ink text-cream" : "text-muted hover:text-ink",
                )}
              >
                {SIZES[k].label}
              </button>
            ))}
          </div>
          <button
            onClick={() => act({ op: "submit", size })}
            className="flex items-center gap-2 rounded-full bg-ink px-5 py-3 text-[15px] font-semibold text-cream hover:bg-ink-2"
          >
            <Play size={17} /> Submit render job
          </button>
          <button
            onClick={() => confirm("Clear all jobs and servers?") && act({ op: "reset" })}
            className="flex items-center gap-2 rounded-full px-5 py-3 text-[15px] font-semibold ring-[1.5px] ring-ink hover:bg-card"
          >
            <RotateCcw size={16} /> Reset
          </button>
        </div>
      </div>

      {/* servers */}
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {nodes.map((n) => (
          <NodeCard key={n.id} n={n} act={act} />
        ))}
        {nodes.length < 3 && (
          <div className="flex min-h-[230px] flex-col justify-center gap-1.5 rounded-[24px] border-2 border-dashed border-line p-5 text-[14px] text-muted">
            <Laptop size={24} className="text-faint" />
            <div className="font-semibold text-ink">Add a laptop</div>
            <div>On the same Wi-Fi, open:</div>
            <code className="break-all rounded-lg bg-paper px-2 py-1 text-[13px] text-ink">
              {s?.joinBase ?? "http://<this-laptop-ip>:3000"}/node/{Object.keys(HOUSES)[nodes.length] ?? "house"}
            </code>
          </div>
        )}
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_380px]">
        <Card>
          <CardTitle right={job && <JobMeta job={job} now={s!.now} />}>
            {job ? `Job #${job.id} · ${job.view.name}` : "No job yet"}
          </CardTitle>
          <div className="mt-4">
            {job ? (
              <Mosaic job={job} byId={byId} />
            ) : (
              <div className="grid aspect-[16/9] place-items-center rounded-2xl bg-paper text-[14px] text-muted">
                Connect the laptops, then press Submit render job.
              </div>
            )}
          </div>
        </Card>

        <div className="flex flex-col gap-4">
          <Card>
            <CardTitle>Join links</CardTitle>
            <ul className="mt-4 space-y-2 text-[13px]">
              {Object.entries(HOUSES)
                .slice(0, 3)
                .map(([id, h]) => (
                  <li key={id} className="flex items-baseline justify-between gap-3">
                    <span className="text-muted">{h.city}</span>
                    <code className="truncate">{(s?.joinBase ?? "") + "/node/" + id}</code>
                  </li>
                ))}
            </ul>
            <p className="mt-3 text-[13px] text-muted">
              No network? Open the same links on this laptop in separate windows; each window acts as a server.
            </p>
          </Card>
          <Card>
            <CardTitle>Scheduler log</CardTitle>
            <ol className="mt-3 max-h-[420px] overflow-auto scroll-thin text-[13px]">
              {(s?.events ?? []).map((e, i) => (
                <li key={e.at + ":" + i} className="flex gap-2 border-b border-line/60 py-1.5 last:border-0">
                  <span className="shrink-0 tabular-nums text-faint">{new Date(e.at).toLocaleTimeString("de-CH")}</span>
                  <span className={clsx(e.tone === "alarm" && "text-[#c62f2f]", e.tone === "teal" && "text-[#2f6e75]", e.tone === "amber" && "text-rust-deep")}>
                    {e.text}
                  </span>
                </li>
              ))}
              {!s?.events.length && <li className="py-2 text-muted">Nothing yet.</li>}
            </ol>
          </Card>
        </div>
      </div>
    </div>
  );
}

function NodeCard({ n, act }: { n: LiveNode; act: (b: object) => void }) {
  const st = STATE[n.state];
  return (
    <Card className="overflow-hidden !p-0">
      <div className="h-2" style={{ background: n.color }} />
      <div className="p-5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="text-[17px] font-semibold tracking-tight">{n.name}</div>
            <div className="mt-1.5">
              <Chip tone={st.tone}>{st.label}</Chip>
            </div>
          </div>
          {n.state === "offline" && (
            <button title="Remove" onClick={() => act({ op: "forget", id: n.id })} className="text-faint hover:text-ink">
              <X size={16} />
            </button>
          )}
        </div>

        <div className="mt-4 flex gap-4">
          <div className="relative h-[92px] w-10 shrink-0 overflow-hidden rounded-xl bg-paper ring-1 ring-line" title="Hot-water tank (simulated)">
            <div className={clsx("absolute inset-x-0 bottom-0 transition-[height] duration-500", n.state === "full" ? "bg-teal" : "bg-amber")} style={{ height: `${n.tank}%` }} />
            <div className="absolute inset-x-0 border-t border-dashed border-ink/40" style={{ bottom: `${TANK.resumeAt}%` }} />
          </div>
          <dl className="grid flex-1 grid-cols-2 gap-x-3 gap-y-2 text-[12.5px]">
            <Fact k="Tank" v={`${Math.round(n.tank)} %`} />
            <Fact k="Tiles done" v={String(n.tilesDone)} />
            <Fact k="Heat" v={`${n.heatWh.toFixed(1)} Wh`} />
            <Fact k="Speed" v={n.rate ? `${(n.rate / 1e9).toFixed(1)} G/s` : "–"} />
          </dl>
        </div>

        <div className="mt-3 h-[34px]">
          {n.current ? (
            <>
              <div className="flex justify-between text-[12.5px]">
                <span>
                  Tile {n.current.tile + 1} · job #{n.current.jobId}
                </span>
                <span className="tabular-nums text-muted">{Math.round(n.current.progress * 100)} %</span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-paper">
                <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${n.current.progress * 100}%`, background: n.color }} />
              </div>
            </>
          ) : (
            <div className="text-[12.5px] text-muted">
              {n.state === "full" ? "No work until the tank drops." : n.state === "offline" ? "Not answering." : "Idle."}
            </div>
          )}
        </div>

        <div className="mt-3 flex gap-2">
          <button
            disabled={n.state === "full" || n.state === "offline"}
            onClick={() => act({ op: "full", id: n.id })}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-full py-2 text-[13px] font-medium ring-1 ring-line hover:bg-paper disabled:opacity-40"
          >
            <Droplets size={14} /> Tank full
          </button>
          <button
            disabled={n.state === "offline"}
            onClick={() => act({ op: "shower", id: n.id })}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-full py-2 text-[13px] font-medium ring-1 ring-line hover:bg-paper disabled:opacity-40"
          >
            <ShowerHead size={14} /> Shower
          </button>
        </div>
      </div>
    </Card>
  );
}

function Fact({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-muted">{k}</dt>
      <dd className="font-semibold tabular-nums">{v}</dd>
    </div>
  );
}

function JobMeta({ job, now }: { job: LiveJob; now: number }) {
  const done = job.tiles.filter((t) => t.state === "done").length;
  const secs = ((job.doneAt ?? now) - job.createdAt) / 1000;
  const moved = job.tiles.reduce((a, t) => a + t.restarts, 0);
  return (
    <div className="flex items-center gap-2 text-[12.5px] text-muted">
      {moved > 0 && <Chip tone="amber">{moved} handed back</Chip>}
      <Chip tone={job.doneAt ? "teal" : "neutral"}>{job.doneAt ? "Complete" : SIZES[job.size].label}</Chip>
      <span className="tabular-nums">
        {done}/{job.tiles.length} tiles · {secs.toFixed(0)} s
      </span>
    </div>
  );
}

function Mosaic({ job, byId }: { job: LiveJob; byId: Map<string, LiveNode> }) {
  return (
    <div
      className="grid overflow-hidden rounded-2xl bg-ink"
      style={{ aspectRatio: `${IMG_W} / ${IMG_H}`, gridTemplateColumns: `repeat(${COLS}, 1fr)`, gridTemplateRows: `repeat(${ROWS}, 1fr)` }}
    >
      {job.tiles.map((t) => {
        const n = t.node ? byId.get(t.node) : undefined;
        return (
          <div key={t.i} className={clsx("relative min-h-0 overflow-hidden", t.state === "pending" && "hatch-light")}>
            {t.v > 0 && t.state !== "pending" && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`/api/live/tile?job=${job.id}&i=${t.i}&v=${t.v}`} alt="" className="absolute inset-0 size-full object-cover" />
            )}
            {t.state === "running" && n && (
              <>
                <div className="absolute inset-0 ring-[3px] ring-inset" style={{ ["--tw-ring-color" as string]: n.color }} />
                <div className="absolute left-1.5 top-1.5 rounded-md px-1.5 py-0.5 text-[11px] font-semibold text-cream" style={{ background: n.color }}>
                  {n.city} · {Math.round(t.progress * 100)} %
                </div>
              </>
            )}
            {t.state === "pending" && <div className="absolute left-1.5 top-1 text-[11px] tabular-nums text-cream/50">{t.i + 1}</div>}
          </div>
        );
      })}
    </div>
  );
}
