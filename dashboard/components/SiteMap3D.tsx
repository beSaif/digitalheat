"use client";

import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import type { StyleSpecification, LayerSpecification } from "maplibre-gl";
import type { Fleet } from "@/lib/data";
import { siteNow } from "@/lib/data";

const STYLE_URL = "https://tiles.openfreemap.org/styles/positron";
// Turbopack can't bundle MapLibre's worker; serve the prebuilt one from public/ (copied by predev/prebuild)
maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

async function brandStyle(): Promise<StyleSpecification> {
  const s: StyleSpecification = await fetch(STYLE_URL).then((r) => r.json());
  const layers: LayerSpecification[] = [];
  for (const l of s.layers) {
    if (l.id === "building" || l.id.includes("shield")) continue;
    if (l.id === "background") (l as { paint: Record<string, unknown> }).paint = { "background-color": "#ece8de" };
    if (l.id === "water") (l as { paint: Record<string, unknown> }).paint = { "fill-color": "#cfdedd" };
    if (l.id === "park" || l.id === "landcover_wood")
      (l as { paint: Record<string, unknown> }).paint = { "fill-color": "#dfe3cf", "fill-opacity": 0.7 };
    if (l.id === "landuse_residential") (l as { paint: Record<string, unknown> }).paint = { "fill-color": "#e6e1d5", "fill-opacity": 0.6 };
    layers.push(l);
    if (l.id === "aeroway-area") {
      layers.push({
        id: "buildings-3d",
        type: "fill-extrusion",
        source: "openmaptiles",
        "source-layer": "building",
        minzoom: 13,
        paint: {
          "fill-extrusion-color": "#fbfaf6",
          "fill-extrusion-height": ["coalesce", ["get", "render_height"], 9],
          "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
          "fill-extrusion-opacity": 0.92,
          "fill-extrusion-vertical-gradient": true,
        },
      } as LayerSpecification);
    }
  }
  return { ...s, layers, light: { anchor: "viewport", color: "#ffffff", intensity: 0.3 } };
}

type Props = { fleet: Fleet; si: number; t: number; onSite: (id: string) => void; padLeft: number };

export function SiteMap3D({ fleet, si, t, onSite, padLeft }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef<Map<number, { m: maplibregl.Marker; el: HTMLDivElement }>>(new Map());
  const siteRef = useRef(si);
  siteRef.current = si;
  const onSiteRef = useRef(onSite);
  onSiteRef.current = onSite;
  const tRef = useRef(t);
  tRef.current = t;
  const done = useRef(-1); // site whose building is highlighted

  // create once
  useEffect(() => {
    let cancelled = false;
    const mk = markers.current;
    const s = fleet.sites[si];
    brandStyle().then((style) => {
      if (cancelled || !el.current) return;
      const m = new maplibregl.Map({
        container: el.current,
        style,
        center: [s.lon, s.lat],
        zoom: 17.2,
        pitch: 62,
        bearing: -28,
        attributionControl: { compact: true },
        canvasContextAttributes: { antialias: true },
      });
      m.setPadding({ left: padLeft, top: 0, right: 0, bottom: 0 });
      map.current = m;
      // the container can be 0×0 when the map is created (Suspense reveal, layout); keep the canvas in sync
      const ro = new ResizeObserver(() => m.resize());
      ro.observe(el.current);
      m.once("remove", () => ro.disconnect());
      m.on("load", () => {
        m.addSource("site-bldg", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
        m.addLayer({
          id: "site-bldg",
          type: "fill-extrusion",
          source: "site-bldg",
          paint: {
            "fill-extrusion-color": "#c0653a",
            "fill-extrusion-height": ["get", "h"],
            "fill-extrusion-base": 0,
            "fill-extrusion-opacity": 0.96,
          },
        });
      });
      m.on("idle", () => {
        if (done.current !== siteRef.current) highlight();
      });
      // markers for every fleet site (visible when near)
      fleet.sites.forEach((x, i) => {
        const div = document.createElement("div");
        div.style.cursor = "pointer";
        div.addEventListener("click", () => onSiteRef.current(x.id));
        const mk = new maplibregl.Marker({ element: div, anchor: "bottom" }).setLngLat([x.lon, x.lat]).addTo(m);
        markers.current.set(i, { m: mk, el: div });
      });
      paintMarkers();
    });
    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
      mk.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function highlight() {
    const m = map.current;
    if (!m || !m.getSource("site-bldg")) return;
    const s = fleet.sites[siteRef.current];
    const p = m.project([s.lon, s.lat]);
    const box: [maplibregl.PointLike, maplibregl.PointLike] = [
      [p.x - 40, p.y - 40],
      [p.x + 40, p.y + 40],
    ];
    const feats = m.queryRenderedFeatures(box, { layers: ["buildings-3d"] });
    // tiles merge neighbouring buildings into one multipolygon: pick the single polygon at the site
    const inside = (ring: number[][]) => {
      let c = false;
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const [xi, yi] = ring[i],
          [xj, yj] = ring[j];
        if (yi > s.lat !== yj > s.lat && s.lon < ((xj - xi) * (s.lat - yi)) / (yj - yi) + xi) c = !c;
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
        const spanM = Math.max((Math.max(...xs) - Math.min(...xs)) * 111320 * Math.cos((s.lat * Math.PI) / 180), (Math.max(...ys) - Math.min(...ys)) * 110540);
        if (spanM > 80 || spanM < 7) continue;
        let d = inside(ring) ? 0 : Infinity;
        if (d) for (const c of ring) d = Math.min(d, (c[0] - s.lon) ** 2 + (c[1] - s.lat) ** 2);
        if (d < bestD) {
          bestD = d;
          best = { ring, h: Number(f.properties?.render_height ?? 12) };
        }
      }
    }
    const src = m.getSource("site-bldg") as maplibregl.GeoJSONSource;
    done.current = siteRef.current;
    if (best) {
      // grow the footprint 4 % so its walls sit just outside the white extrusion (no z-fighting)
      const n = best.ring.length;
      const cx = best.ring.reduce((a, c) => a + c[0], 0) / n,
        cy = best.ring.reduce((a, c) => a + c[1], 0) / n;
      const ring = best.ring.map(([x, y]) => [cx + (x - cx) * 1.04, cy + (y - cy) * 1.04]);
      src.setData({
        type: "FeatureCollection",
        features: [{ type: "Feature", properties: { h: best.h + 1 }, geometry: { type: "Polygon", coordinates: [ring] } }],
      });
    } else {
      // no mapped building at the point: draw a 16 m block so the site is still visible
      const dx = 8 / (111320 * Math.cos((s.lat * Math.PI) / 180)),
        dy = 8 / 110540;
      src.setData({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: { h: 14 },
            geometry: {
              type: "Polygon",
              coordinates: [[[s.lon - dx, s.lat - dy], [s.lon + dx, s.lat - dy], [s.lon + dx, s.lat + dy], [s.lon - dx, s.lat + dy], [s.lon - dx, s.lat - dy]]],
            },
          },
        ],
      });
    }
  }

  function paintMarkers() {
    markers.current.forEach(({ el }, i) => {
      const n = siteNow(fleet, i, tRef.current);
      const sel = i === siteRef.current;
      el.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;transform:translateY(${sel ? -64 : -28}px)">
          <div style="display:flex;align-items:center;gap:6px;padding:${sel ? "6px 10px 6px 6px" : "4px 8px 4px 4px"};border-radius:999px;background:${sel ? "#141412" : "#fbfaf6"};color:${sel ? "#f6f3ec" : "#141412"};box-shadow:0 8px 20px -8px rgba(40,25,10,.55);font:600 ${sel ? 13 : 11}px var(--font-plex),system-ui;white-space:nowrap;border:1px solid ${sel ? "#141412" : "#ddd7ca"}">
            <span style="display:grid;place-items:center;width:${sel ? 26 : 20}px;height:${sel ? 26 : 20}px;border-radius:999px;background:${n.running ? "#f2a65a" : "#ddd7ca"};color:#141412;font-size:${sel ? 11 : 10}px">${n.running}</span>
            ${fleet.sites[i].id}${sel ? `<span style="opacity:.6;font-weight:500">· ${n.running}/${fleet.sites[i].servers} on</span>` : ""}
          </div>
          <div style="width:2px;height:${sel ? 40 : 14}px;background:${sel ? "#141412" : "#9a958a"}"></div>
        </div>`;
    });
  }

  useEffect(() => {
    paintMarkers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t, si]);

  // fly when the site changes
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    const s = fleet.sites[si];
    done.current = -1;
    m.flyTo({ center: [s.lon, s.lat], zoom: 17.2, pitch: 62, bearing: -28, duration: 2200, essential: true });
  }, [si, fleet]);

  return (
    <div className="absolute inset-0">
      <div ref={el} className="h-full w-full" />
      <div className="absolute bottom-6 right-6 flex flex-col overflow-hidden rounded-2xl bg-card shadow-lg ring-1 ring-line">
        <button className="grid size-11 place-items-center text-[22px] hover:bg-paper" onClick={() => map.current?.zoomIn()} aria-label="Zoom in">
          +
        </button>
        <div className="mx-2 h-px bg-line" />
        <button className="grid size-11 place-items-center text-[22px] hover:bg-paper" onClick={() => map.current?.zoomOut()} aria-label="Zoom out">
          −
        </button>
        <div className="mx-2 h-px bg-line" />
        <button
          className="grid size-11 place-items-center text-[12px] font-semibold hover:bg-paper"
          onClick={() => map.current?.easeTo({ bearing: (map.current.getBearing() + 90) % 360, duration: 900 })}
          aria-label="Rotate"
        >
          ⟳
        </button>
      </div>
    </div>
  );
}
