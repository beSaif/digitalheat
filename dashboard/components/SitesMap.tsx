"use client";

import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { StyleSpecification } from "maplibre-gl";
import clsx from "clsx";
import { ArrowDown, ArrowUp, Building2, Hospital, House, Leaf, Minus, Pause, Plus, Save, Waves, X } from "lucide-react";
import { KIND_LABEL, KIND_SERVERS, type Kind, type Schedule, type SiteIn } from "@/lib/schedule";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

const ICON: Record<Kind, typeof House> = { house: House, cityhouse: Building2, hospital: Hospital, spa: Waves, greenhouse: Leaf };
const SWISS: [[number, number], [number, number]] = [
  [5.95, 45.82],
  [10.49, 47.81],
];
const PAD = { top: 110, bottom: 70, left: 170, right: 170 };

async function style(): Promise<StyleSpecification> {
  const s: StyleSpecification = await fetch("https://tiles.openfreemap.org/styles/positron").then((r) => r.json());
  s.layers = s.layers.filter((l) => !l.id.includes("shield"));
  for (const l of s.layers) {
    const p = l as { paint?: Record<string, unknown> };
    if (l.id === "background") p.paint = { "background-color": "#ece8de" };
    if (l.id === "water") p.paint = { "fill-color": "#cfdedd" };
  }
  return s;
}

function boundsOf(sites: SiteIn[]): [[number, number], [number, number]] {
  const lons = sites.map((s) => s.lon),
    lats = sites.map((s) => s.lat);
  const pad = 0.012;
  return [
    [Math.min(...lons) - pad, Math.min(...lats) - pad],
    [Math.max(...lons) + pad, Math.max(...lats) + pad],
  ];
}

type Props = {
  sites: SiteIn[];
  schedule: Schedule | null;
  t: number;
  dur: number;
  selected: number;
  setSelected: (i: number) => void;
  setServers: (i: number, n: number) => void;
  adding: boolean;
  onAdd: (kind: Kind, lat: number, lon: number) => void;
  onRemove: (i: number) => void;
  busy: boolean;
};

export function SitesMap({ sites, schedule, t, dur, selected, setSelected, setServers, adding, onAdd, onRemove, busy }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [pts, setPts] = useState<{ x: number; y: number }[] | null>(null);
  const [zoom, setZoom] = useState(13);
  const [hover, setHover] = useState<number | null>(null);
  const [pinned, setPinned] = useState<number | null>(null);
  const card = hover ?? pinned;
  const [pick, setPick] = useState<{ lat: number; lon: number; x: number; y: number } | null>(null);
  const sitesRef = useRef(sites);
  const addingRef = useRef(adding);
  useEffect(() => {
    sitesRef.current = sites;
    addingRef.current = adding;
  });

  useEffect(() => {
    let m: maplibregl.Map | null = null;
    let cancelled = false;
    style().then((st) => {
      if (cancelled || !el.current) return;
      m = new maplibregl.Map({ container: el.current, style: st, center: [7.589, 47.561], zoom: 13, scrollZoom: false, attributionControl: { compact: true } });
      map.current = m;
      m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
      const place = () => {
        if (!m) return;
        setPts(sitesRef.current.map((s) => m!.project([s.lon, s.lat])));
        setZoom(m.getZoom());
      };
      m.on("load", () => {
        m?.resize();
        m?.fitBounds(boundsOf(sitesRef.current), { padding: PAD, duration: 0 });
        place();
      });
      m.on("move", place);
      m.on("resize", place);
      m.on("click", (e) => {
        if (!addingRef.current) return;
        const { lng, lat } = e.lngLat;
        if (lat < 45.8 || lat > 47.9 || lng < 5.9 || lng > 10.6) return;
        setPick({ lat, lon: lng, x: e.point.x, y: e.point.y });
      });
      const ro = new ResizeObserver(() => m?.resize());
      ro.observe(el.current);
      m.once("remove", () => ro.disconnect());
    });
    return () => {
      cancelled = true;
      m?.remove();
      map.current = null;
    };
  }, []);

  // re-place markers and refit when sites are added or removed
  const shape = sites.map((s) => `${s.id}:${s.lat}:${s.lon}`).join("|");
  const spots = pts && spread(pts, zoom < 11 ? 84 : 230, zoom < 11 ? 36 : 120);
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    m.fitBounds(boundsOf(sitesRef.current), { padding: PAD, maxZoom: 14, duration: 600 });
    Promise.resolve().then(() => setPts(sitesRef.current.map((s) => m.project([s.lon, s.lat]))));
  }, [shape]);

  useEffect(() => {
    if (map.current) map.current.getCanvas().style.cursor = adding ? "crosshair" : "";
  }, [adding]);

  const S = schedule && schedule.sites.length === sites.length ? schedule : null;
  const showPick = adding && pick;

  return (
    <div className="relative h-[560px] overflow-hidden rounded-[20px] ring-1 ring-line">
      <div ref={el} className="h-full w-full" />

      <div className="pointer-events-none absolute left-1/2 top-4 -translate-x-1/2 rounded-full bg-ink px-4 py-2 text-[13px] font-semibold text-cream shadow">
        Job queue
      </div>
      <button
        onClick={() => map.current?.fitBounds(SWISS, { padding: 30 })}
        className="absolute right-3 top-3 rounded-full bg-card px-3 py-1.5 text-[12px] font-semibold ring-1 ring-line hover:bg-paper"
      >
        Switzerland
      </button>
      {adding && !showPick && (
        <div className="pointer-events-none absolute left-1/2 top-16 -translate-x-1/2 rounded-full bg-rust px-4 py-1.5 text-[13px] font-semibold text-cream">
          Click on the map to place the new site
        </div>
      )}
      {busy && (
        <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-2 rounded-full bg-card px-3 py-1.5 text-[12px] ring-1 ring-line">
          <span className="size-2 animate-pulse rounded-full bg-rust" /> Scheduler running…
        </div>
      )}

      {spots && S && (
        <div key={t} className="pointer-events-none absolute inset-0">
          {sites.flatMap((_, i) => {
            if (!spots[i]) return [];
            const x = S.series[i];
            const rr = S.deadline_jobs.filter((j) => j[4] === i && j[5] === t).length;
            const em = Math.max(0, Math.min(6, Math.ceil(x.embed_sh[t] / 3)));
            const dots = [
              ...Array.from({ length: rr }, (_, k) => ({ c: "bg-amber", d: k * 90 })),
              ...Array.from({ length: em }, (_, k) => ({ c: "bg-teal", d: 60 + k * 70 })),
            ];
            return dots.map((dot, k) => (
              <span
                key={`${i}-${k}`}
                className={clsx("token absolute size-3 rounded-full ring-2 ring-white", dot.c)}
                style={{ "--x": `${spots[i].x}px`, "--y": `${spots[i].y}px`, "--d": `${dur}ms`, "--delay": `${Math.min(dot.d, dur * 0.4)}ms` } as React.CSSProperties}
              />
            ));
          })}
        </div>
      )}

      {spots &&
        sites.map((s, i) => {
          if (!spots[i]) return null;
          const x = S?.series[i];
          const n = s.servers;
          const run = x ? x.running[t] : 0;
          const rr = x ? Math.ceil(x.rerank_sh[t] - 1e-9) : 0;
          const d = x ? x.demand[t] : 0;
          const prev = x && t > 0 ? x.demand[t - 1] : d;
          const up = d - prev > 0.05;
          const down = prev - d > 0.05;
          const Icon = ICON[s.kind];
          const paused = x ? x.paused_now[t] : 0;
          const waiting = x ? x.waiting_now[t] : 0;
          const movedIn = S ? S.deadline_jobs.filter((j) => j[4] === i && j[5] === t && j[1] !== i).length + (x?.moved_in[t] ?? 0) : 0;
          if (zoom < 11)
            return (
              <button
                key={s.id}
                onClick={() => {
                  setSelected(i);
                  setPinned(pinned === i ? null : i);
                }}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
                className={clsx(
                  "absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-1 rounded-full bg-card py-1 pl-1 pr-2 text-[12px] font-semibold shadow",
                  selected === i ? "ring-2 ring-rust" : "ring-1 ring-line",
                )}
                style={{ left: spots[i].x, top: spots[i].y }}
              >
                <span className="grid size-6 place-items-center rounded-full bg-amber-soft text-rust-deep">
                  <Icon size={13} />
                </span>
                {run}/{n}
                {paused > 0 && <Pause size={11} className="text-rust" fill="currentColor" />}
              </button>
            );
          return (
            <div key={s.id} className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: spots[i].x, top: spots[i].y }}>
              <div
                onClick={() => {
                  setSelected(i);
                  setPinned(pinned === i ? null : i);
                }}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
                className={clsx(
                  "relative flex cursor-pointer items-center gap-3 rounded-2xl bg-card px-3 py-2.5 shadow-lg",
                  selected === i ? "ring-2 ring-rust" : "ring-1 ring-line",
                )}
              >
                <span className={clsx("relative grid size-11 place-items-center rounded-xl", s.kind === "spa" ? "bg-teal-soft text-[#2f6e75]" : "bg-amber-soft text-rust-deep")}>
                  <Icon size={22} />
                  {(up || down) && (
                    <span className={clsx("absolute -right-2 -top-2 grid size-5 place-items-center rounded-full text-cream", up ? "bg-rust" : "bg-teal")}>
                      {up ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                    </span>
                  )}
                </span>
                <div>
                  <div className="text-[14px] font-semibold leading-tight">
                    {s.name} {s.kind === "house" && <span className="font-normal text-muted">{s.id}</span>}
                  </div>
                  <div className="text-[13px] text-muted">
                    <b className="text-ink">{run}</b> / {n} servers
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setServers(i, n + 1);
                    }}
                    aria-label={`Add a server at ${s.name}`}
                    className="grid size-6 place-items-center rounded-full bg-ink text-cream hover:bg-ink-2"
                  >
                    <Plus size={12} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setServers(i, n - 1);
                    }}
                    disabled={n === 0}
                    aria-label={`Remove a server at ${s.name}`}
                    className="grid size-6 place-items-center rounded-full bg-paper ring-1 ring-line hover:bg-cream disabled:opacity-40"
                  >
                    <Minus size={12} />
                  </button>
                </div>
                {s.added && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemove(i);
                    }}
                    aria-label={`Remove ${s.name}`}
                    className="absolute -right-2 -top-2 grid size-5 place-items-center rounded-full bg-ink text-cream"
                  >
                    <X size={11} />
                  </button>
                )}
              </div>
              <div className="mx-auto mt-1.5 flex w-fit max-w-[180px] flex-wrap justify-center gap-[3px] rounded-lg bg-card/90 p-1.5 ring-1 ring-line">
                {Array.from({ length: n }, (_, k) => (
                  <i key={k} className={clsx("h-3 w-2 rounded-[2px]", k < rr ? "bg-amber" : k < run ? "bg-teal" : "bg-line")} />
                ))}
              </div>
              {(paused > 0 || waiting > 0 || movedIn > 0) && (
                <div className="mx-auto mt-1 flex w-fit gap-1 text-[11px] font-semibold">
                  {paused > 0 && (
                    <span className="flex items-center gap-1 rounded-full bg-ink px-2 py-0.5 text-cream">
                      <Pause size={10} fill="currentColor" /> {paused} paused
                    </span>
                  )}
                  {waiting > 0 && (
                    <span className="flex items-center gap-1 rounded-full bg-ink px-2 py-0.5 text-cream">
                      <Save size={10} /> {waiting} saved
                    </span>
                  )}
                  {movedIn > 0 && <span className="rounded-full bg-amber px-2 py-0.5 text-ink">{movedIn} moved in</span>}
                </div>
              )}
            </div>
          );
        })}

      {spots && S && (
        <svg key={`mv${t}`} className="pointer-events-none absolute inset-0 h-full w-full overflow-visible">
          <defs>
            <marker id="mv-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" fill="#f2a65a" />
            </marker>
          </defs>
          {[...new Set(S.deadline_jobs.filter((j) => j[5] === t && j[1] !== j[4] && j[4] >= 0).map((j) => `${j[1]}-${j[4]}`))].map((k) => {
            const [a, b] = k.split("-").map(Number);
            if (!spots[a] || !spots[b]) return null;
            // start and end at the card edges, not under the cards
            const r = zoom < 11 ? 22 : 70;
            const dx = spots[b].x - spots[a].x,
              dy = spots[b].y - spots[a].y,
              len = Math.hypot(dx, dy);
            if (len < 2 * r + 10) return null;
            const A = { x: spots[a].x + (dx / len) * r, y: spots[a].y + (dy / len) * r },
              B = { x: spots[b].x - (dx / len) * r, y: spots[b].y - (dy / len) * r };
            const mx = (A.x + B.x) / 2 - (B.y - A.y) * 0.25,
              my = (A.y + B.y) / 2 + (B.x - A.x) * 0.25;
            return (
              <path
                key={k}
                d={`M${A.x},${A.y} Q${mx},${my} ${B.x},${B.y}`}
                className="move-path"
                stroke="#f2a65a"
                strokeWidth={3}
                fill="none"
                strokeDasharray="8 6"
                markerEnd="url(#mv-head)"
              />
            );
          })}
        </svg>
      )}

      {spots && S && card !== null && card < sites.length && spots[card] && (
        <SiteHour
          x={spots[card].x}
          y={spots[card].y}
          name={sites[card].name}
          demand={S.series[card].demand[t]}
          heat={S.series[card].running[t] * S.constants.heat_recovery}
          served={S.series[card].served[t]}
          soc={S.series[card].soc[t]}
          tank={S.sites[card].tank_kwh}
          high={zoom >= 11}
        />
      )}

      {showPick && (
        <div className="absolute z-10 w-[230px] -translate-x-1/2 rounded-2xl bg-card p-3 shadow-xl ring-1 ring-line" style={{ left: Math.max(pick.x, 125), top: Math.min(pick.y + 14, 300) }}>
          <div className="mb-2 flex items-center justify-between text-[13px] font-semibold">
            New site
            <button onClick={() => setPick(null)} aria-label="Cancel" className="text-muted hover:text-ink">
              <X size={14} />
            </button>
          </div>
          <div className="grid grid-cols-1 gap-1">
            {(Object.keys(KIND_LABEL) as Kind[]).map((k) => {
              const Icon = ICON[k];
              return (
                <button
                  key={k}
                  onClick={() => {
                    onAdd(k, pick.lat, pick.lon);
                    setPick(null);
                  }}
                  className="flex items-center gap-2 rounded-xl px-2 py-1.5 text-left text-[13px] hover:bg-paper"
                >
                  <Icon size={16} className="text-rust-deep" /> {KIND_LABEL[k]}
                  <span className="ml-auto text-[11px] text-faint">{KIND_SERVERS[k]} servers</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="pointer-events-none absolute bottom-3 left-3 flex gap-3 rounded-full bg-card/90 px-3 py-1.5 text-[12px] ring-1 ring-line">
        <span className="flex items-center gap-1.5">
          <i className="size-2.5 rounded-full bg-teal" /> Embed
        </span>
        <span className="flex items-center gap-1.5">
          <i className="size-2.5 rounded-full bg-amber" /> Rerank
        </span>
        <span className="flex items-center gap-1.5">
          <ArrowUp size={12} className="text-rust" /> heat demand rising
        </span>
        <span className="flex items-center gap-1.5">
          <Pause size={11} fill="currentColor" /> no heat: paused
        </span>
        <span className="flex items-center gap-1.5">
          <i className="h-0 w-4 border-t-2 border-dashed border-amber" /> moved to heat
        </span>
      </div>
    </div>
  );
}

/** Push pins that would sit on top of each other downwards, so close sites stay readable. */
function spread(pts: { x: number; y: number }[], w: number, h: number) {
  const out: { x: number; y: number }[] = [];
  for (const p of pts) {
    if (!p) {
      out.push(p);
      continue;
    }
    const q = { x: p.x, y: p.y };
    while (out.some((o) => o && Math.abs(o.x - q.x) < w && Math.abs(o.y - q.y) < h)) q.y += h;
    out.push(q);
  }
  return out;
}

/** What a site needs this hour, and where the heat comes from. */
function SiteHour(p: { x: number; y: number; name: string; demand: number; heat: number; served: number; soc: number; tank: number; high: boolean }) {
  const backup = Math.max(0, p.demand - p.served);
  const rows = [
    { l: "Needs", v: `${p.demand.toFixed(1)} kW` },
    { l: "Servers give", v: `${p.heat.toFixed(1)} kW` },
    { l: "Backup heater", v: `${backup.toFixed(1)} kW`, hot: backup > 0.05 },
  ];
  return (
    <div
      className="pointer-events-none absolute z-20 w-[210px] -translate-x-1/2 rounded-2xl bg-ink p-3.5 text-cream shadow-xl"
      style={{ left: p.x, top: p.y - (p.high ? 58 : 22), transform: "translate(-50%, -100%)" }}
    >
      <div className="text-[13px] font-semibold">{p.name}</div>
      <div className="mt-2 space-y-1 text-[13px]">
        {rows.map((r) => (
          <div key={r.l} className="flex justify-between">
            <span className="text-cream/60">{r.l}</span>
            <b className={clsx("tabular-nums", r.hot && "text-amber")}>{r.v}</b>
          </div>
        ))}
      </div>
      <div className="mt-2.5 flex justify-between text-[13px]">
        <span className="text-cream/60">Tank</span>
        <b className="tabular-nums">
          {p.soc.toFixed(0)} / {p.tank} kWh
        </b>
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-cream/15">
        <div className="h-full rounded-full bg-amber" style={{ width: `${Math.min(100, (p.soc / p.tank) * 100)}%` }} />
      </div>
    </div>
  );
}
