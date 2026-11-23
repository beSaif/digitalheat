"use client";

import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { StyleSpecification } from "maplibre-gl";
import clsx from "clsx";
import { ArrowDown, ArrowLeft, ArrowUp, Box, Briefcase, DoorOpen, Building2, FlaskConical, Hospital, Map as MapIcon, House, Leaf, Minus, Pause, Plus, Save, Users, Waves, X } from "lucide-react";
import { KIND_LABEL, KIND_SERVERS, type Kind, type Schedule, type SiteIn } from "@/lib/schedule";
import { STATUS, type Status } from "@/lib/heatStatus";
import { BuildingInside, type Inside } from "@/components/BuildingInside";
import chCoarse from "@/lib/switzerland-coarse.json";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

const ICON: Record<Kind, typeof House> = {
  house: House,
  family: Users,
  cityhouse: Building2,
  hospital: Hospital,
  spa: Waves,
  greenhouse: Leaf,
  office: Briefcase,
  pharma: FlaskConical,
};
const SWISS: [[number, number], [number, number]] = [
  [5.95, 45.82],
  [10.49, 47.81],
];
const PAD = { top: 110, bottom: 70, left: 170, right: 170 };

/** Base-map labels a quiet map keeps: cities and towns. Villages, hamlets, districts, roads, rivers and the airport go. */
const MAIN_LABELS = new Set(["label_city", "label_city_capital", "label_town", "label_state", "label_country_1", "label_country_2", "label_country_3"]);

/** Line layers a quiet map drops: paths, minor streets, piers, rail, tunnels and the airport. Main roads and motorways stay. */
const QUIET_DROP = /^(highway_path|highway_minor|road_pier|road_area_pier|railway|tunnel_|aeroway)/;

/**
 * A quiet map (the live room screen) is a pale paper backdrop, so the heat-status colours on the pins are the only
 * strong colour: land, parks and buildings close to the paper tone, main roads a faint warm line, town names faded.
 */
function quieten(l: StyleSpecification["layers"][number]) {
  const p = l as { paint?: Record<string, unknown> };
  const id = l.id;
  if (id === "background") p.paint = { "background-color": "#f1eee6" };
  else if (id === "water") p.paint = { "fill-color": "#dce6e4" };
  else if (id === "waterway") p.paint = { ...p.paint, "line-color": "#d6e1df" };
  else if (id === "building") p.paint = { ...p.paint, "fill-color": "#ebe7de", "fill-outline-color": "#e4dfd4" };
  else if (l.type === "fill" && id !== "buildings-3d") p.paint = { ...p.paint, "fill-color": "#ece8df" };
  else if (id.includes("casing")) p.paint = { ...p.paint, "line-color": "#e3ded2" };
  else if (id.startsWith("highway_")) p.paint = { ...p.paint, "line-color": "#f8f6f0" };
  else if (id.startsWith("boundary")) p.paint = { ...p.paint, "line-color": "#cdc7ba", "line-opacity": 0.55 };
  else if (l.type === "symbol") p.paint = { ...p.paint, "text-color": "#8a857a", "text-halo-color": "#f1eee6", "text-halo-width": 1.2, "text-halo-blur": 0, "text-opacity": 0.85 };
}

async function style(quiet: boolean): Promise<StyleSpecification> {
  // the border is drawn from the fine outline; labels are tested against a ~1 km coarse one, which is far cheaper
  const [s, ch]: [StyleSpecification, GeoJSON.Feature<GeoJSON.Polygon>] = await Promise.all([
    fetch("https://tiles.openfreemap.org/styles/positron").then((r) => r.json()),
    fetch("/switzerland.geojson").then((r) => r.json()),
  ]);
  s.layers = s.layers.filter((l) => !l.id.includes("shield") && (!quiet || ((l.type !== "symbol" || MAIN_LABELS.has(l.id)) && !QUIET_DROP.test(l.id))));
  for (const l of s.layers) {
    const p = l as { paint?: Record<string, unknown> };
    if (quiet) quieten(l);
    else if (l.id === "background") p.paint = { "background-color": "#ece8de" };
    else if (l.id === "water") p.paint = { "fill-color": "#cfdedd" };
    // place names only inside Switzerland: towns across the border are noise
    if (l.type === "symbol") {
      const f = (l as { filter?: unknown[] }).filter;
      (l as { filter?: unknown }).filter = f ? ["all", f, ["within", chCoarse]] : ["within", chCoarse];
    }
  }
  // Switzerland's border, drawn strong over the roads and under the labels
  s.sources.ch = { type: "geojson", data: ch };
  const top = s.layers.findIndex((l) => l.type === "symbol");
  s.layers.splice(
    top < 0 ? s.layers.length : top,
    0,
    { id: "ch-halo", type: "line", source: "ch", layout: { "line-join": "round" }, paint: { "line-color": "#ffffff", "line-opacity": 0.8, "line-width": ["interpolate", ["linear"], ["zoom"], 6, 6, 12, 10] } },
    { id: "ch-border", type: "line", source: "ch", layout: { "line-join": "round" }, paint: { "line-color": "#5b5348", "line-width": ["interpolate", ["linear"], ["zoom"], 6, 2.2, 12, 3.5] } },
  );
  // 3D buildings, only close up (a building's 3D view): the city map further out stays flat
  const at = s.layers.findIndex((l) => l.type === "symbol");
  s.layers.splice(at < 0 ? s.layers.length : at, 0, {
    id: "buildings-3d",
    type: "fill-extrusion",
    source: "openmaptiles",
    "source-layer": "building",
    minzoom: 15,
    paint: {
      "fill-extrusion-color": "#fbfaf6",
      "fill-extrusion-height": ["coalesce", ["get", "render_height"], 9],
      "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
      "fill-extrusion-opacity": ["interpolate", ["linear"], ["zoom"], 15, 0, 16, 0.92],
      "fill-extrusion-vertical-gradient": true,
    },
  });
  return { ...s, light: { anchor: "viewport", color: "#ffffff", intensity: 0.3 } };
}

/** The building of the site in 3D view, in DigitalHeat's colour. */
function paintBuilding(m: maplibregl.Map, x: SiteIn | undefined) {
  if (!x) return;
  if (!m.getSource("site-bldg")) {
    m.addSource("site-bldg", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    m.addLayer({ id: "site-bldg", type: "fill-extrusion", source: "site-bldg", paint: { "fill-extrusion-color": "#c0653a", "fill-extrusion-height": ["get", "h"], "fill-extrusion-base": 0, "fill-extrusion-opacity": 0.96 } });
  }
  (m.getSource("site-bldg") as maplibregl.GeoJSONSource).setData(footprintAt(m, x.lat, x.lon, "buildings-3d"));
}

/** A building's 3D view: close up, tilted, turned a little. */
const VIEW_3D = { zoom: 17.2, pitch: 62, bearing: -28 };

/** Below this zoom the sites are one marker: they would all sit on the same spot. */
const FAR_ZOOM = 8;

/** Room around Switzerland when the whole country is shown: the side panels' room, little at top and bottom. */
const swissPad = (p: { top: number; bottom: number; left: number; right: number }) => ({ top: Math.min(p.top, 120), bottom: 90, left: p.left, right: p.right });

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
  /** Tailwind height class; the overview uses the default 560 px */
  height?: string;
  /** room around the sites when the map fits them (smaller for a smaller map) */
  pad?: { top: number; bottom: number; left: number; right: number };
  /** small pin markers at every zoom (for a small map; the details live elsewhere on the page) */
  compact?: boolean;
  /** full-bleed map under floating panels: no frame, legend, zoom or server buttons, and only the main place names */
  bare?: boolean;
  /** sites from this index on are small pins labelled with their name (people's racks in the live demo) */
  pinFrom?: number;
  /** extra controls in a building's card (the live demo: fill its tank) */
  cardExtra?: (i: number) => React.ReactNode;
  /** heat status of a building (lib/heatStatus.ts): its pin's dot and label, and a ring around its icon */
  statusAt?: (i: number) => Status | undefined;
  /** open on the whole of Switzerland and fly into the sites; adds a "Switzerland" / "Back to Basel" button */
  fromSwiss?: boolean;
  /** where that button sits (Tailwind position classes) */
  swissBtnAt?: string;
  /** a building's plant room and servers: adds "Go inside" to its 3D view */
  insideOf?: (i: number) => Inside | null;
};

export function SitesMap({ sites, schedule, t, dur, selected, setSelected, setServers, adding, onAdd, onRemove, busy, height = "h-[560px]", pad = PAD, compact = false, bare = false, pinFrom, cardExtra, statusAt, fromSwiss = false, swissBtnAt = "right-3 top-3", insideOf }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [pts, setPts] = useState<{ x: number; y: number }[] | null>(null);
  const [zoom, setZoom] = useState(13);
  const small = compact || zoom < 11;
  const far = zoom < FAR_ZOOM;
  // the whole country is shown (or the opening flight is under way): no automatic refits onto the sites meanwhile
  const [swiss, setSwiss] = useState(fromSwiss);
  const holdRef = useRef(fromSwiss);
  const isPin = (i: number) => small || (pinFrom !== undefined && i >= pinFrom);
  const named = (i: number) => pinFrom !== undefined && i >= pinFrom;
  const [hover, setHoverNow] = useState<number | null>(null);
  const [pinned, setPinned] = useState<number | null>(null);
  // a building's 3D view: the map flies into its block, tilted, with the building in DigitalHeat's colour
  const [view3d, setView3d] = useState<number | null>(null);
  const view3dRef = useRef<number | null>(null);
  // inside a building (from its 3D view): its plant room and servers cover the map
  const [inside, setInside] = useState<number | null>(null);
  const insideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const card = inside !== null ? null : (hover ?? pinned ?? view3d);
  // leaving a pin closes its card a moment later, so the pointer can move onto the card and use its buttons
  const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const setHover = (i: number | null) => {
    if (hoverTimer.current) clearTimeout(hoverTimer.current);
    hoverTimer.current = null;
    if (i !== null) setHoverNow(i);
    else hoverTimer.current = setTimeout(() => setHoverNow(null), 280);
  };
  const keepCard = () => {
    if (hoverTimer.current) clearTimeout(hoverTimer.current);
    hoverTimer.current = null;
  };
  // Escape closes a building's card
  useEffect(() => {
    if (pinned === null) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setPinned(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pinned]);
  const [pick, setPick] = useState<{ lat: number; lon: number; x: number; y: number } | null>(null);
  const sitesRef = useRef(sites);
  const addingRef = useRef(adding);
  const padRef = useRef(pad);
  const bareRef = useRef(bare);
  const fromSwissRef = useRef(fromSwiss);
  useEffect(() => {
    sitesRef.current = sites;
    addingRef.current = adding;
    padRef.current = pad;
  });

  useEffect(() => {
    let m: maplibregl.Map | null = null;
    let cancelled = false;
    style(bareRef.current).then((st) => {
      if (cancelled || !el.current) return;
      const intro = fromSwissRef.current;
      m = new maplibregl.Map({
        container: el.current,
        style: st,
        // the opening shot is the whole of Switzerland
        ...(intro ? { bounds: SWISS, fitBoundsOptions: { padding: swissPad(padRef.current) } } : { center: [7.589, 47.561] as [number, number], zoom: 13 }),
        scrollZoom: false,
        attributionControl: { compact: true },
      });
      map.current = m;
      if (!bareRef.current) m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
      const place = () => {
        if (!m) return;
        setPts(sitesRef.current.map((s) => m!.project([s.lon, s.lat])));
        setZoom(m.getZoom());
      };
      m.on("load", () => {
        m?.resize();
        if (intro) setTimeout(() => flyIn(1), 900);
        else m?.fitBounds(boundsOf(sitesRef.current), { padding: padRef.current, duration: 0 });
        place();
      });
      m.on("move", place);
      m.on("resize", place);
      m.on("click", (e) => {
        setPinned(null); // a click on the map closes a building's card
        if (!addingRef.current) return;
        const { lng, lat } = e.lngLat;
        if (lat < 45.8 || lat > 47.9 || lng < 5.9 || lng > 10.6) return;
        setPick({ lat, lon: lng, x: e.point.x, y: e.point.y });
      });
      m.on("idle", () => {
        const i = view3dRef.current;
        if (m && i !== null) paintBuilding(m, sitesRef.current[i]);
      });
      // a map in a flexible box gets its final size after load: refit the sites when the box changes
      const ro = new ResizeObserver(() => {
        m?.resize();
        if (m?.loaded() && view3dRef.current === null && !holdRef.current) m.fitBounds(boundsOf(sitesRef.current), { padding: padRef.current, maxZoom: 14, duration: 0 });
      });
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
  const spots = pts && spread(pts, (i) => (named(i) ? [170, 48] : isPin(i) ? [84, 36] : [230, 120]));
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    if (view3dRef.current === null && !holdRef.current) m.fitBounds(boundsOf(sitesRef.current), { padding: padRef.current, maxZoom: 14, duration: 600 });
    Promise.resolve().then(() => setPts(sitesRef.current.map((s) => m.project([s.lon, s.lat]))));
  }, [shape]);

  useEffect(() => {
    if (map.current) map.current.getCanvas().style.cursor = adding ? "crosshair" : "";
  }, [adding]);

  const open3d = (i: number) => {
    const m = map.current;
    if (!m) return;
    view3dRef.current = i;
    setView3d(i);
    setPinned(i);
    setSelected(i);
    (m.getSource("site-bldg") as maplibregl.GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features: [] });
    const x = sitesRef.current[i];
    m.flyTo({ center: [x.lon, x.lat], ...VIEW_3D, padding: padRef.current, duration: 2200, essential: true });
  };
  const close3d = () => {
    const m = map.current;
    leaveInside(false);
    view3dRef.current = null;
    setView3d(null);
    setPinned(null);
    if (!m) return;
    (m.getSource("site-bldg") as maplibregl.GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features: [] });
    // level the camera and drop the 3D view's padding (flyTo keeps it on the map, and fitBounds adds its own on top)
    m.easeTo({ pitch: 0, bearing: 0, padding: { top: 0, bottom: 0, left: 0, right: 0 }, duration: 700 });
    m.once("moveend", () => {
      if (view3dRef.current === null && !holdRef.current) m.fitBounds(boundsOf(sitesRef.current), { padding: padRef.current, maxZoom: 14, duration: 1100 });
    });
  };

  /** Step into the building: the camera dollies up to its wall, then the plant room fades in. */
  const goInside = (i: number) => {
    const m = map.current;
    if (!m) return;
    setPinned(null);
    setHoverNow(null);
    m.easeTo({ zoom: 19.3, pitch: 74, duration: 900, essential: true });
    if (insideTimer.current) clearTimeout(insideTimer.current);
    insideTimer.current = setTimeout(() => setInside(i), 600);
  };
  /** Leave the plant room; `back` returns the camera to the building's 3D view. */
  function leaveInside(back = true) {
    if (insideTimer.current) clearTimeout(insideTimer.current);
    insideTimer.current = null;
    setInside(null);
    if (back && view3dRef.current !== null) {
      setPinned(view3dRef.current);
      map.current?.easeTo({ zoom: VIEW_3D.zoom, pitch: VIEW_3D.pitch, duration: 1000, essential: true });
    }
  }
  useEffect(() => () => {
    if (insideTimer.current) clearTimeout(insideTimer.current);
  }, []);

  /** Fly from wherever the map is into the sites (the opening shot, or back from the whole map). */
  function flyIn(slow = 0) {
    const m = map.current;
    if (!m) return;
    holdRef.current = true;
    setSwiss(false);
    m.fitBounds(boundsOf(sitesRef.current), { padding: padRef.current, maxZoom: 14, pitch: 0, bearing: 0, duration: slow ? 4800 : 3000, essential: true });
    m.once("moveend", () => {
      holdRef.current = false;
    });
  }
  /** Zoom out to the whole of Switzerland. */
  const flyOut = () => {
    const m = map.current;
    if (!m) return;
    holdRef.current = true;
    setSwiss(true);
    setPinned(null);
    setHoverNow(null);
    leaveInside(false);
    if (view3dRef.current !== null) {
      view3dRef.current = null;
      setView3d(null);
      (m.getSource("site-bldg") as maplibregl.GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features: [] });
    }
    m.fitBounds(SWISS, { padding: swissPad(padRef.current), pitch: 0, bearing: 0, duration: 2600, essential: true });
  };
  // Escape steps back out: from inside the building to its 3D view, from the 3D view to the map
  useEffect(() => {
    if (view3d === null) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && (inside !== null ? leaveInside() : close3d());
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const S = schedule && schedule.sites.length === sites.length ? schedule : null;
  const showPick = adding && pick;

  return (
    <div className={clsx("relative overflow-hidden", !bare && "rounded-[20px] ring-1 ring-line", height)}>
      <div ref={el} className="h-full w-full" />

      {!bare && (
        <div className="pointer-events-none absolute left-1/2 top-4 -translate-x-1/2 rounded-full bg-ink px-4 py-2 text-[13px] font-semibold text-cream shadow">
          Job queue
        </div>
      )}
      {!bare && (
        <button
          onClick={() => map.current?.fitBounds(SWISS, { padding: 30 })}
          className="absolute right-3 top-3 rounded-full bg-card px-3 py-1.5 text-[12px] font-semibold ring-1 ring-line hover:bg-paper"
        >
          Switzerland
        </button>
      )}
      {adding && !showPick && (
        <div className="pointer-events-none absolute left-1/2 top-16 -translate-x-1/2 rounded-full bg-rust px-4 py-1.5 text-[13px] font-semibold text-cream">
          Click on the map to place the new site
        </div>
      )}
      {busy && !bare && (
        <div className="pointer-events-none absolute left-3 top-3 flex items-center gap-2 rounded-full bg-card px-3 py-1.5 text-[12px] ring-1 ring-line">
          <span className="size-2 animate-pulse rounded-full bg-rust" /> Scheduler running…
        </div>
      )}

      {spots && S && !far && (
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
        !far &&
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
          if (isPin(i)) {
            const st = statusAt?.(i);
            return (
              <button
                key={s.id}
                onClick={() => {
                  setSelected(i);
                  setPinned(pinned === i ? null : i);
                }}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover(null)}
                title={st ? STATUS[st].label : KIND_LABEL[s.kind]}
                className={clsx(
                  "absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-2 rounded-xl border bg-white py-1.5 pl-1.5 pr-2.5 text-left leading-tight shadow-pill transition-colors",
                  selected === i ? "border-ink ring-1 ring-ink" : "border-line/60 hover:border-faint",
                )}
                style={{ left: spots[i].x, top: spots[i].y }}
              >
                {/* the kind of building */}
                <span className={clsx("grid size-7 shrink-0 place-items-center rounded-lg", s.kind === "spa" ? "bg-teal-soft text-[#2f6e75]" : "bg-amber-soft text-rust-deep")}>
                  <Icon size={15} />
                </span>
                <span className="min-w-0">
                  <span className="flex items-center gap-1.5 whitespace-nowrap">
                    {/* the heat status, the same colours as the servers panel */}
                    <span className="size-2.5 shrink-0 rounded-full transition-colors duration-500" style={{ background: st ? STATUS[st].color : STATUS.idle.color }} />
                    {named(i) && <span className="max-w-[110px] truncate text-[13.5px] font-semibold">{s.name}</span>}
                    <span className={clsx("text-[13px] tabular-nums", named(i) ? "text-muted" : "font-semibold")}>
                      {run}/{n}
                    </span>
                    {paused > 0 && <Pause size={11} className="shrink-0 text-[#2f6e75]" fill="currentColor" />}
                  </span>
                  {named(i) && st && st !== "idle" && st !== "used" && (
                    <span className="mt-0.5 block whitespace-nowrap pl-4 text-[12.5px] font-semibold" style={{ color: STATUS[st].text }}>
                      {STATUS[st].short}
                    </span>
                  )}
                </span>
              </button>
            );
          }
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
                <span
                  className={clsx("relative grid size-11 place-items-center rounded-xl transition-shadow duration-500", s.kind === "spa" ? "bg-teal-soft text-[#2f6e75]" : "bg-amber-soft text-rust-deep")}
                  style={statusAt?.(i) && statusAt(i) !== "idle" ? { boxShadow: `0 0 0 3px ${STATUS[statusAt(i)!].color}` } : undefined}
                >
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
                {!bare && <div className="flex flex-col gap-1">
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
                </div>}
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

      {spots && S && !far && (
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
            const ra = isPin(a) ? 22 : 70,
              rb = isPin(b) ? 22 : 70;
            const dx = spots[b].x - spots[a].x,
              dy = spots[b].y - spots[a].y,
              len = Math.hypot(dx, dy);
            if (len < ra + rb + 10) return null;
            const A = { x: spots[a].x + (dx / len) * ra, y: spots[a].y + (dy / len) * ra },
              B = { x: spots[b].x - (dx / len) * rb, y: spots[b].y - (dy / len) * rb };
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

      {spots && S && !far && card !== null && card < sites.length && spots[card] && (
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
          live={bare}
          onEnter={keepCard}
          onLeave={() => setHover(null)}
          actions={
            <>
              {view3d === card ? (
                <>
                  {insideOf?.(card) && (
                    <CardBtn onClick={() => goInside(card)} title="Step into the plant room and see its servers">
                      <DoorOpen size={13} /> Go inside
                    </CardBtn>
                  )}
                  <CardBtn onClick={close3d}>
                    <ArrowLeft size={13} /> Back to map
                  </CardBtn>
                </>
              ) : (
                <CardBtn onClick={() => open3d(card)}>
                  <Box size={13} /> 3D view
                </CardBtn>
              )}
              {cardExtra?.(card)}
            </>
          }
        />
      )}

      {/* far out: the sites are one marker, a click flies back in */}
      {pts && far && pts.length > 0 && (
        <button
          onClick={() => flyIn()}
          title="Fly back to the sites"
          className="absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-2 rounded-full border border-line/60 bg-white py-1.5 pl-1.5 pr-3.5 text-[14px] font-semibold shadow-pill hover:bg-cream"
          style={{ left: pts.reduce((a, p) => a + p.x, 0) / pts.length, top: pts.reduce((a, p) => a + p.y, 0) / pts.length }}
        >
          <span className="relative grid size-6 place-items-center">
            <span className="absolute inset-0 animate-ping rounded-full bg-rust/40" />
            <span className="size-3 rounded-full bg-rust ring-2 ring-white" />
          </span>
          Basel <span className="font-normal text-muted">· {sites.length} buildings</span>
        </button>
      )}

      {fromSwiss && view3d === null && (
        <button
          onClick={() => (swiss ? flyIn() : flyOut())}
          className={clsx("absolute z-10 flex items-center gap-1.5 rounded-full border border-line/60 bg-white px-3.5 py-2 text-[13.5px] font-semibold text-ink shadow-pill hover:bg-cream", swissBtnAt)}
        >
          {swiss ? (
            <>
              <ArrowLeft size={14} /> Back to Basel
            </>
          ) : (
            <>
              <MapIcon size={14} /> Switzerland
            </>
          )}
        </button>
      )}

      {view3d !== null && inside === null && sites[view3d] && (
        <button
          onClick={close3d}
          className="absolute left-1/2 top-4 z-20 flex -translate-x-1/2 items-center gap-1.5 rounded-full border border-line/60 bg-white px-4 py-2 text-[13.5px] font-semibold text-ink shadow-pill hover:bg-cream"
        >
          <ArrowLeft size={14} /> Back to the map · {sites[view3d].name} in 3D
        </button>
      )}

      {inside !== null && sites[inside] && (() => {
        const d = insideOf?.(inside);
        return d ? <BuildingInside key={sites[inside].id} d={d} onBack={() => leaveInside()} area={{ top: pad.top, bottom: Math.min(pad.bottom, 96), left: pad.left, right: pad.right }} /> : null;
      })()}

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

      {!bare && <div className="pointer-events-none absolute bottom-3 left-3 flex gap-3 rounded-full bg-card/90 px-3 py-1.5 text-[12px] ring-1 ring-line">
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
      </div>}
    </div>
  );
}

/** Push pins that would sit on top of each other downwards, so close sites stay readable. */
function spread(pts: { x: number; y: number }[], size: (i: number) => [number, number]) {
  const out: { x: number; y: number }[] = [];
  pts.forEach((p, i) => {
    if (!p) {
      out.push(p);
      return;
    }
    const [w, h] = size(i);
    const q = { x: p.x, y: p.y };
    // two boxes overlap when their centres are closer than half of both widths (heights)
    while (out.some((o, k) => o && Math.abs(o.x - q.x) < (w + size(k)[0]) / 2 && Math.abs(o.y - q.y) < (h + size(k)[1]) / 2)) q.y += h;
    out.push(q);
  });
  return out;
}

/** What a site needs this hour, and where the heat comes from. */
/** A building's hour. `live`: the live demo, where servers cover all heat through the tank (no backup heater). */
function SiteHour(p: {
  x: number;
  y: number;
  name: string;
  demand: number;
  heat: number;
  served: number;
  soc: number;
  tank: number;
  high: boolean;
  live?: boolean;
  actions?: React.ReactNode;
  onEnter?: () => void;
  onLeave?: () => void;
}) {
  const backup = Math.max(0, p.demand - p.served);
  const rows = [
    { l: "Needs", v: `${p.demand.toFixed(1)} kW` },
    { l: "Servers give", v: `${p.heat.toFixed(1)} kW` },
    // the live demo has no backup heater: what the servers do not give right now comes out of the tank, while it holds any
    ...(p.live
      ? p.soc > 0.05
        ? [{ l: "From tank", v: `${Math.max(0, p.demand - p.heat).toFixed(1)} kW` }]
        : [{ l: "Not covered", v: `${Math.max(0, p.demand - p.heat).toFixed(1)} kW`, hot: p.demand - p.heat > 0.05 }]
      : [{ l: "Backup heater", v: `${backup.toFixed(1)} kW`, hot: backup > 0.05 }]),
  ];
  const level = p.tank > 0 ? Math.max(0, Math.min(1, p.soc / p.tank)) : 0;
  // no room above the pin (a building's 3D view puts it near the top): open the card below it
  const below = p.y < 380;
  return (
    <div
      onMouseEnter={p.onEnter}
      onMouseLeave={p.onLeave}
      onClick={(e) => e.stopPropagation()}
      className="rise absolute z-20 w-[230px] rounded-2xl border border-line/60 bg-white p-3.5 text-ink shadow-pill"
      style={below ? { left: p.x, top: p.y + 22, transform: "translate(-50%, 0)" } : { left: p.x, top: p.y - (p.high ? 58 : 22), transform: "translate(-50%, -100%)" }}
    >
      {/* a bridge over the gap to the pin, so moving onto the card keeps it open */}
      <div className={clsx("absolute inset-x-0", below ? "bottom-full" : "top-full")} style={{ height: below ? 14 : p.high ? 46 : 14 }} />
      <div className="text-[14px] font-semibold">{p.name}</div>
      <div className="mt-2 space-y-1 text-[13.5px]">
        {rows.map((r) => (
          <div key={r.l} className="flex justify-between">
            <span className="text-muted">{r.l}</span>
            <b className={clsx("font-semibold tabular-nums", r.hot && "text-[#a85a12]")}>{r.v}</b>
          </div>
        ))}
      </div>
      <div className="mt-2.5 flex justify-between text-[13.5px]">
        <span className="text-muted">Tank</span>
        <b className="font-semibold tabular-nums">
          {p.live ? `${Math.round(level * 100)} % · ` : ""}
          {p.soc.toFixed(0)} / {p.tank} kWh
        </b>
      </div>
      <div className={clsx("mt-1.5 overflow-hidden rounded-full bg-cream ring-1 ring-line/70", p.live ? "h-2.5" : "h-1.5")}>
        <div className={clsx("h-full rounded-full", p.live ? "bg-gradient-to-r from-[#3f8f9a] to-[#7cc3cb]" : "bg-amber")} style={{ width: `${level * 100}%` }} />
      </div>
      {p.actions && <div className="mt-3 flex flex-wrap gap-1.5">{p.actions}</div>}
    </div>
  );
}

export function CardBtn({ onClick, children, title }: { onClick: () => void; children: React.ReactNode; title?: string }) {
  return (
    <button
      title={title}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className="flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-[12.5px] font-semibold text-ink ring-1 ring-line hover:bg-cream"
    >
      {children}
    </button>
  );
}

/**
 * The building at a point, as a polygon to extrude in DigitalHeat's colour: the house-sized footprint of
 * `layer` (rendered buildings) under or nearest to the point, or a 16 m block when none is mapped there.
 */
export function footprintAt(m: maplibregl.Map, lat: number, lon: number, layer: string): GeoJSON.FeatureCollection {
  const p = m.project([lon, lat]);
  const box: [maplibregl.PointLike, maplibregl.PointLike] = [
    [p.x - 40, p.y - 40],
    [p.x + 40, p.y + 40],
  ];
  const feats = m.getLayer(layer) ? m.queryRenderedFeatures(box, { layers: [layer] }) : [];
  // tiles merge neighbouring buildings into one multipolygon: pick the single polygon at the site
  const inside = (ring: number[][]) => {
    let c = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i],
        [xj, yj] = ring[j];
      if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) c = !c;
    }
    return c;
  };
  let best: { ring: number[][]; h: number } | null = null;
  let bestD = Infinity;
  for (const f of feats) {
    const g = f.geometry;
    if (g.type !== "Polygon" && g.type !== "MultiPolygon") continue;
    const polys = (g.type === "Polygon" ? [g.coordinates] : g.coordinates) as number[][][][];
    for (const poly of polys) {
      const ring = poly[0];
      // house-sized footprints only (7–80 m across): skips station halls, malls and sheds
      const xs = ring.map((c) => c[0]),
        ys = ring.map((c) => c[1]);
      const spanM = Math.max((Math.max(...xs) - Math.min(...xs)) * 111320 * Math.cos((lat * Math.PI) / 180), (Math.max(...ys) - Math.min(...ys)) * 110540);
      if (spanM > 80 || spanM < 7) continue;
      let d = inside(ring) ? 0 : Infinity;
      if (d) for (const c of ring) d = Math.min(d, (c[0] - lon) ** 2 + (c[1] - lat) ** 2);
      if (d < bestD) {
        bestD = d;
        best = { ring, h: Number(f.properties?.render_height ?? 12) };
      }
    }
  }
  if (best) {
    // grow the footprint 4 % so its walls sit just outside the white extrusion (no z-fighting)
    const n = best.ring.length;
    const cx = best.ring.reduce((a, c) => a + c[0], 0) / n,
      cy = best.ring.reduce((a, c) => a + c[1], 0) / n;
    const ring = best.ring.map(([x, y]) => [cx + (x - cx) * 1.04, cy + (y - cy) * 1.04]);
    return { type: "FeatureCollection", features: [{ type: "Feature", properties: { h: best.h + 1 }, geometry: { type: "Polygon", coordinates: [ring] } }] };
  }
  // no mapped building at the point: draw a 16 m block so the site is still visible
  const dx = 8 / (111320 * Math.cos((lat * Math.PI) / 180)),
    dy = 8 / 110540;
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { h: 14 },
        geometry: { type: "Polygon", coordinates: [[[lon - dx, lat - dy], [lon + dx, lat - dy], [lon + dx, lat + dy], [lon - dx, lat + dy], [lon - dx, lat - dy]]] },
      },
    ],
  };
}
