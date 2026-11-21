"use client";

import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { StyleSpecification } from "maplibre-gl";
import clsx from "clsx";
import { ArrowDown, ArrowUp, Building2, Hospital, House, Leaf, Minus, Plus, Waves, X } from "lucide-react";
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
          if (zoom < 11)
            return (
              <button
                key={s.id}
                onClick={() => setSelected(i)}
                title={s.name}
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
              </button>
            );
          return (
            <div key={s.id} className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: spots[i].x, top: spots[i].y }}>
              <div
                onClick={() => setSelected(i)}
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
            </div>
          );
        })}

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
