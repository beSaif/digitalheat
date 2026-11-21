"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { geoArea, geoMercator, geoPath, type GeoPermissibleObjects } from "d3-geo";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { ArrowUpRight, ChevronDown, Thermometer, X } from "lucide-react";
import { useFleet } from "@/lib/store";
import { cityTemp, fmtDay, fmtTime, nf, siteNow, type Fleet } from "@/lib/data";
import { Card, Chip, Loading, STATE_LABEL } from "@/components/ui";

type Metric = "demand" | "running" | "coverage";
const METRICS: { id: Metric; label: string }[] = [
  { id: "demand", label: "Heat demand now" },
  { id: "running", label: "Servers running" },
  { id: "coverage", label: "Covered, year to date" },
];

const W = 1000,
  HGT = 600;
// label side per city, so neighbours don't collide
const LABEL_LEFT = new Set(["Zürich", "Genève", "Basel"]);

// warm sequential ramp in brand colours, light to deep rust
const RAMP = ["#f1e6d3", "#f6cf9c", "#f2a65a", "#d97f45", "#c0653a", "#8f4423"];
function ramp(v: number) {
  const x = Math.max(0, Math.min(1, v)) * (RAMP.length - 1);
  const i = Math.floor(x);
  if (i >= RAMP.length - 1) return RAMP[RAMP.length - 1];
  const f = x - i;
  const a = RAMP[i].match(/\w\w/g)!.map((h) => parseInt(h, 16));
  const b = RAMP[i + 1].match(/\w\w/g)!.map((h) => parseInt(h, 16));
  return `rgb(${a.map((c, k) => Math.round(c + (b[k] - c) * f)).join(",")})`;
}

function rewind(fc: FeatureCollection): FeatureCollection {
  // d3-geo wants clockwise exterior rings; flip any feature whose area exceeds a hemisphere
  for (const f of fc.features) {
    if (geoArea(f as GeoPermissibleObjects) > 2 * Math.PI) {
      const g = f.geometry as Geometry & { coordinates: number[][][] | number[][][][] };
      if (g.type === "Polygon") (g.coordinates as number[][][]).forEach((r) => r.reverse());
      if (g.type === "MultiPolygon") (g.coordinates as number[][][][]).forEach((p) => p.forEach((r) => r.reverse()));
    }
  }
  return fc;
}

export default function MapPage() {
  const { fleet, t } = useFleet();
  const [geo, setGeo] = useState<FeatureCollection | null>(null);
  const [metric, setMetric] = useState<Metric>("demand");
  const [city, setCity] = useState<string | null>("Basel");
  useEffect(() => {
    fetch("/data/ch-cantons.geojson")
      .then((r) => r.json())
      .then((g) => setGeo(rewind(g)));
  }, []);
  if (!fleet || !geo) return <Loading />;
  return (
    <div className="relative h-full overflow-hidden">
      <SwissMap fleet={fleet} t={t} geo={geo} metric={metric} city={city} setCity={setCity} />
      <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between p-6">
        <div className="pointer-events-auto">
          <h1 className="font-display text-[40px] font-semibold leading-none">Fleet map</h1>
          <p className="mt-2.5 max-w-[440px] text-[15px] text-muted">
            Heat demand and server allocation across Switzerland, hour by hour. Click a city to see its houses.
          </p>
          <div className="mt-4 flex items-center gap-3 text-[11px] text-muted">
            <span className="uppercase tracking-[0.12em]">{METRICS.find((m) => m.id === metric)!.label}</span>
            <span className="flex items-center gap-1.5">
              {metric === "demand" ? "low" : metric === "running" ? "0%" : "50%"}
              <span className="flex">
                {RAMP.map((c) => (
                  <i key={c} className="h-2 w-5" style={{ background: c }} />
                ))}
              </span>
              {metric === "demand" ? "high, per server" : "100%"}
            </span>
            <span className="flex items-center gap-1.5">
              <i className="hatch h-2 w-4 bg-paper ring-1 ring-line" /> no houses
            </span>
          </div>
        </div>
        <div className="pointer-events-auto flex items-center gap-2">
          <Select value={city ?? ""} onChange={(v) => setCity(v || null)} options={[["", "All cities"], ...fleet.cities.map((c) => [c.name, c.name] as [string, string])]} />
          <div className="flex rounded-full bg-card p-1 ring-1 ring-line">
            {METRICS.map((m) => (
              <button
                key={m.id}
                onClick={() => setMetric(m.id)}
                className={clsx(
                  "rounded-full px-3.5 py-1.5 text-[13px] font-medium",
                  metric === m.id ? "bg-ink text-cream" : "text-muted hover:text-ink",
                )}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      {city && <CityCard fleet={fleet} t={t} city={city} onClose={() => setCity(null)} />}
      <BottomCards fleet={fleet} t={t} />
    </div>
  );
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="relative flex items-center rounded-full bg-card ring-1 ring-line">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none bg-transparent py-2.5 pl-4 pr-9 text-[13px] font-medium outline-none"
      >
        {options.map(([v, l]) => (
          <option key={v} value={v}>
            {l}
          </option>
        ))}
      </select>
      <ChevronDown size={15} className="pointer-events-none absolute right-3 text-muted" />
    </label>
  );
}

function useCityStats(fleet: Fleet, t: number) {
  return useMemo(() => {
    const m = new Map<string, { running: number; servers: number; permit: number; demand: number; served: number; sites: number[]; throttled: number; ytdS: number; ytdD: number }>();
    fleet.sites.forEach((s, i) => {
      const n = siteNow(fleet, i, t);
      const c = m.get(s.city) ?? { running: 0, servers: 0, permit: 0, demand: 0, served: 0, sites: [], throttled: 0, ytdS: 0, ytdD: 0 };
      c.running += n.running;
      c.servers += s.servers;
      c.permit += n.permit;
      c.demand += n.demand;
      c.served += n.served;
      c.sites.push(i);
      if (n.state === "throttled") c.throttled++;
      const h = fleet.hourly[i];
      for (let x = 0; x <= t; x++) {
        c.ytdS += h.served[x];
        c.ytdD += h.demand[x];
      }
      m.set(s.city, c);
    });
    return m;
  }, [fleet, t]);
}

function SwissMap({
  fleet,
  t,
  geo,
  metric,
  city,
  setCity,
}: {
  fleet: Fleet;
  t: number;
  geo: FeatureCollection;
  metric: Metric;
  city: string | null;
  setCity: (c: string | null) => void;
}) {
  const proj = useMemo(() => geoMercator().fitExtent([[20, 30], [W - 20, HGT - 30]], geo as GeoPermissibleObjects), [geo]);
  const path = useMemo(() => geoPath(proj), [proj]);
  const stats = useCityStats(fleet, t);

  const cantonValue = useMemo(() => {
    const v = new Map<string, number>();
    const agg = new Map<string, { d: number; r: number; s: number; ys: number; yd: number; n: number }>();
    for (const [name, c] of stats) {
      const canton = fleet.cities.find((x) => x.name === name)!.canton;
      const a = agg.get(canton) ?? { d: 0, r: 0, s: 0, ys: 0, yd: 0, n: 0 };
      a.d += c.demand;
      a.r += c.running;
      a.s += c.servers;
      a.ys += c.ytdS;
      a.yd += c.ytdD;
      agg.set(canton, a);
    }
    for (const [k, a] of agg) {
      if (metric === "demand") v.set(k, a.d / (a.s * 1.0)); // kWh per installed server, normalises fleet size
      if (metric === "running") v.set(k, a.r / a.s);
      if (metric === "coverage") v.set(k, a.yd ? a.ys / a.yd : 0);
    }
    return v;
  }, [stats, fleet, metric]);

  const norm = (v: number) => (metric === "demand" ? v / 2.2 : metric === "coverage" ? (v - 0.5) / 0.5 : v);
  const selectedCanton = city ? fleet.cities.find((c) => c.name === city)?.canton : null;

  return (
    <svg viewBox={`0 0 ${W} ${HGT}`} className="absolute bottom-[318px] left-6 right-[390px] top-[150px] h-[calc(100%-468px)] w-[calc(100%-414px)]" preserveAspectRatio="xMidYMid meet">
      <defs>
        <filter id="lift" x="-10%" y="-10%" width="120%" height="130%">
          <feDropShadow dx="0" dy="10" stdDeviation="10" floodColor="#5b4630" floodOpacity="0.25" />
        </filter>
        <filter id="liftStrong" x="-20%" y="-20%" width="140%" height="160%">
          <feDropShadow dx="0" dy="12" stdDeviation="8" floodColor="#5b2a12" floodOpacity="0.35" />
        </filter>
        <pattern id="noSites" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="6" height="6" fill="#ebe5d9" />
          <line x1="0" y1="0" x2="0" y2="6" stroke="#cfc6b4" strokeWidth="1.2" />
        </pattern>
      </defs>
      {/* slab thickness under the country */}
      <g transform="translate(0,9)">
        {geo.features.map((f, i) => (
          <path key={i} d={path(f as Feature) ?? ""} fill="#cbbfa8" stroke="#cbbfa8" strokeWidth={2} />
        ))}
      </g>
      <g filter="url(#lift)">
        {geo.features.map((f, i) => {
          const name = (f.properties as { name: string }).name;
          const v = cantonValue.get(name);
          if (name === selectedCanton) return null;
          return (
            <path
              key={i}
              d={path(f as Feature) ?? ""}
              fill={v === undefined ? "url(#noSites)" : ramp(norm(v))}
              stroke="#fbfaf6"
              strokeWidth={1.1}
              className="transition-[fill] duration-300"
            >
              <title>{v === undefined ? `${name}: no DigitalHeat houses` : name}</title>
            </path>
          );
        })}
      </g>
      {/* selected canton lifted, as in the reference's raised region */}
      {selectedCanton &&
        geo.features
          .filter((f) => (f.properties as { name: string }).name === selectedCanton)
          .map((f, i) => {
            const v = cantonValue.get(selectedCanton);
            return (
              <g key={i} transform="translate(0,-7)" filter="url(#liftStrong)">
                <path d={path(f as Feature) ?? ""} fill={v === undefined ? "#e5dccb" : ramp(norm(v))} stroke="#141412" strokeWidth={1.4} />
              </g>
            );
          })}

      {fleet.cities.map((c) => {
        const [x, y] = proj([c.lon, c.lat])!;
        const s = stats.get(c.name)!;
        const active = s.running > 0;
        const sel = city === c.name;
        return (
          <g key={c.name} transform={`translate(${x},${y - (c.canton === selectedCanton ? 7 : 0)})`} className="cursor-pointer" onClick={() => setCity(sel ? null : c.name)}>
            {active && (
              <circle r={14} fill="#f6f3ec" opacity={0.5}>
                <animate attributeName="r" values="16;30;16" dur="2.4s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.6;0;0.6" dur="2.4s" repeatCount="indefinite" />
              </circle>
            )}
            <circle r={sel ? 20 : 16} fill={sel ? "#141412" : "#fbfaf6"} stroke="#141412" strokeWidth={1.5} />
            <text textAnchor="middle" dy="5.5" fontSize="15" fontWeight="700" fill={sel ? "#f2a65a" : "#141412"}>
              {s.sites.length}
            </text>
            <g transform={`translate(${LABEL_LEFT.has(c.name) ? -24 - Math.max(128, c.name.length * 10 + 18) : 24},-2)`}>
              <rect x="-4" y="-16" rx="8" height="38" width={Math.max(128, c.name.length * 10 + 18)} fill="#fbfaf6" opacity={0.92} />
              <text x="4" y="1" fontSize="16" fontWeight="600" fill="#141412">
                {c.name}
              </text>
              <text x="4" y="17" fontSize="12.5" fill="#6b675e">
                {s.running}/{s.servers} servers · {cityTemp(fleet, c.name, t).toFixed(0)}°C
              </text>
            </g>
          </g>
        );
      })}

    </svg>
  );
}

function CityCard({ fleet, t, city, onClose }: { fleet: Fleet; t: number; city: string; onClose: () => void }) {
  const stats = useCityStats(fleet, t).get(city)!;
  const c = fleet.cities.find((x) => x.name === city)!;
  const cover = stats.demand ? stats.served / stats.demand : 0;
  const ytd = stats.ytdD ? stats.ytdS / stats.ytdD : 0;
  return (
    <div className="absolute bottom-[318px] right-6 top-[150px] w-[350px] overflow-auto scroll-thin rounded-[24px] bg-card/95 p-5 shadow-[0_20px_50px_-20px_rgba(60,40,20,0.45)] ring-1 ring-line backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <button onClick={onClose} className="order-last grid size-8 shrink-0 place-items-center rounded-full ring-1 ring-line hover:bg-paper" aria-label="Close">
          <X size={15} />
        </button>
        <div>
          <div className="text-[20px] font-semibold">{city}</div>
          <div className="text-[12px] text-muted">
            Canton {c.canton} · {c.elevation_m} m
          </div>
        </div>
        <div className="text-right">
          <div className="text-[11px] text-muted">Covered this hour</div>
          <div className="font-display text-[24px] font-semibold text-rust">
            {Math.round(cover * 100)}
            <span className="text-[13px] text-muted">%</span>
          </div>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 border-y border-line py-3 text-[12px]">
        <div>
          <div className="font-semibold">
            {stats.running}/{stats.servers}
          </div>
          <div className="text-muted">servers on</div>
        </div>
        <div>
          <div className="flex items-center gap-1 font-semibold">
            <Thermometer size={12} /> {cityTemp(fleet, city, t).toFixed(1)}°C
          </div>
          <div className="text-muted">outside</div>
        </div>
        <div>
          <div className="font-semibold">{Math.round(ytd * 100)}%</div>
          <div className="text-muted">covered YTD</div>
        </div>
      </div>
      <div className="mt-3 flex flex-col">
        {stats.sites.map((i) => {
          const n = siteNow(fleet, i, t);
          const st = STATE_LABEL[n.state];
          return (
            <Link key={i} href={`/sites/${n.site.id}`} className="group flex items-center gap-3 rounded-xl px-1 py-2 hover:bg-paper/60">
              <div className="flex w-[52px] shrink-0 flex-wrap gap-[2px]">
                {Array.from({ length: n.site.servers }, (_, k) => (
                  <i key={k} className={clsx("h-4 w-[3px] rounded-sm", k < n.running ? "bg-rust" : k < n.permit ? "bg-amber-soft" : "bg-line")} />
                ))}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-[13.5px] font-medium">
                  {n.site.id} · {n.site.district}
                </div>
                <div className="text-[11px] text-faint">
                  {n.demand.toFixed(1)} kWh · tank {Math.round(n.socShare * 100)}%
                </div>
              </div>
              <Chip tone={st.tone}>{st.label.split(" ·")[0]}</Chip>
              <ArrowUpRight size={15} className="text-faint group-hover:text-ink" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function BottomCards({ fleet, t }: { fleet: Fleet; t: number }) {
  const stats = useCityStats(fleet, t);
  // last 7 days, hourly, fleet totals
  const hours = useMemo(() => {
    const out: { d: number; s: number; t: number }[] = [];
    for (let x = Math.max(0, t - 167); x <= t; x++) {
      let d = 0,
        s = 0;
      for (const h of fleet.hourly) {
        d += h.demand[x];
        s += h.served[x];
      }
      out.push({ d: d / 10, s: s / 10, t: x });
    }
    return out;
  }, [fleet, t]);
  const maxD = Math.max(...hours.map((h) => h.d));
  const weekServed = hours.reduce((a, h) => a + h.s, 0);
  const weekDemand = hours.reduce((a, h) => a + h.d, 0);
  const daysJ = fleet.daily_jobs;
  const day = Math.floor(t / 24);
  let offered = 0,
    refused = 0;
  for (let d = Math.max(0, day - 6); d <= day; d++) {
    offered += daysJ.offered[d];
    refused += daysJ.refused[d];
  }

  // coverage per day over the year
  const daily = useMemo(() => {
    const out: { cov: number; d: number }[] = [];
    for (let d = 0; d < 365; d++) {
      let dm = 0,
        s = 0;
      for (const h of fleet.hourly)
        for (let x = d * 24; x < d * 24 + 24; x++) {
          dm += h.demand[x];
          s += h.served[x];
        }
      out.push({ cov: s / dm, d: dm });
    }
    return out;
  }, [fleet]);
  const maxDay = Math.max(...daily.map((x) => x.d));
  const cities = [...stats.entries()].sort((a, b) => b[1].ytdS / b[1].ytdD - a[1].ytdS / a[1].ytdD);

  return (
    <div className="absolute inset-x-6 bottom-6 grid grid-cols-12 gap-4">
      <Card className="col-span-5 shadow-[0_20px_50px_-24px_rgba(60,40,20,0.4)]">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[16px] font-semibold">Heat over the last 7 days</div>
            <div className="mt-3 text-[13px] text-muted">Delivered by servers</div>
            <div className="font-display text-[34px] font-semibold leading-none">
              {nf(weekServed / 1000, 1)}
              <span className="text-[15px] text-muted"> MWh</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-x-5 gap-y-2 text-[12px]">
            <div>
              <div className="font-semibold text-rust">{Math.round((weekServed / weekDemand) * 100)}%</div>
              <div className="text-faint">of demand</div>
            </div>
            <div>
              <div className="font-semibold">{nf(offered)}</div>
              <div className="text-faint">jobs offered</div>
            </div>
            <div>
              <div className="font-semibold">{nf(refused)}</div>
              <div className="text-faint">refused at intake</div>
            </div>
            <div>
              <div className="font-semibold">0</div>
              <div className="text-faint">deadlines missed</div>
            </div>
          </div>
        </div>
        <div className="mt-4 flex h-[92px] items-end gap-[1.5px]">
          {hours.map((h) => (
            <div key={h.t} className="relative flex-1" style={{ height: `${(h.d / maxD) * 100}%` }} title={`${fmtDay(h.t)} ${fmtTime(h.t)}: ${nf(h.s)} / ${nf(h.d)} kWh`}>
              <div className="absolute inset-0 rounded-t-sm bg-line" />
              <div className={clsx("absolute inset-x-0 bottom-0 rounded-t-sm", h.t === t ? "bg-ink" : "bg-rust")} style={{ height: `${(h.s / h.d) * 100}%` }} />
            </div>
          ))}
        </div>
        <div className="mt-1 flex justify-between text-[10px] text-faint">
          <span>{fmtDay(hours[0].t)}</span>
          <span>now</span>
        </div>
      </Card>

      <Card className="col-span-3 shadow-[0_20px_50px_-24px_rgba(60,40,20,0.4)]">
        <div className="flex items-center justify-between">
          <div className="text-[16px] font-semibold">Cities</div>
          <div className="text-[11px] text-faint">covered YTD</div>
        </div>
        <div className="mt-2 max-h-[150px] overflow-auto pr-1 scroll-thin">
          {cities.map(([name, c]) => (
            <div key={name} className="flex items-center gap-2 border-b border-line/60 py-[7px] text-[13px] last:border-0">
              <span className="flex-1">{name}</span>
              {c.throttled > 0 ? <Chip tone="amber">Throttled</Chip> : c.running > 0 ? <Chip tone="ink">Running</Chip> : <Chip tone="hatch">Idle</Chip>}
              <span className="w-12 text-right font-semibold">
                {Math.round((c.ytdS / c.ytdD) * 100)}
                <span className="text-[10px] text-faint">%</span>
              </span>
            </div>
          ))}
        </div>
      </Card>

      <Card className="col-span-4 shadow-[0_20px_50px_-24px_rgba(60,40,20,0.4)]">
        <div className="flex items-center justify-between">
          <div className="text-[16px] font-semibold">Coverage trend, all sites</div>
          <span className="rounded-full px-2.5 py-0.5 text-[11px] ring-1 ring-line">2025</span>
        </div>
        <svg viewBox="0 0 365 110" preserveAspectRatio="none" className="mt-3 h-[118px] w-full">
          {daily.map((x, i) => (
            <rect key={i} x={i} width={0.7} y={110 - (x.d / maxDay) * 100} height={(x.d / maxDay) * 100} fill={i === day ? "#141412" : "#e3dccd"} />
          ))}
          <polyline
            fill="none"
            stroke="#c0653a"
            strokeWidth={1.6}
            vectorEffect="non-scaling-stroke"
            points={daily.map((x, i) => `${i},${110 - Math.min(1, x.cov) * 100}`).join(" ")}
          />
          <line x1={day} x2={day} y1={0} y2={110} stroke="#141412" strokeWidth={1} vectorEffect="non-scaling-stroke" strokeDasharray="3 3" />
        </svg>
        <div className="mt-1 flex justify-between text-[10px] text-faint">
          {["Jan", "Mar", "May", "Jul", "Sep", "Nov"].map((m) => (
            <span key={m}>{m}</span>
          ))}
        </div>
        <div className="mt-2 flex gap-4 text-[11px] text-muted">
          <span className="flex items-center gap-1.5">
            <i className="h-0.5 w-3 bg-rust" /> share covered by servers
          </span>
          <span className="flex items-center gap-1.5">
            <i className="size-2 bg-line" /> daily demand
          </span>
        </div>
      </Card>
    </div>
  );
}

