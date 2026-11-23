"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { ArrowLeft, Cpu, Droplets, Flame, Laptop, Pause, Power, Smartphone, Thermometer, Zap } from "lucide-react";
import type { Status } from "@/lib/heatStatus";

/*
 * Inside a building: its plant room, drawn in isometric. The rack(s) of DigitalHeat servers stand against the
 * back wall, warm water runs from them into the heat tank, and from the tank out to the building's heating.
 * Every server is clickable and shows what it is doing at this moment.
 */

/** What one server in the rack is doing now. */
export type ServerState = "job" | "ready" | "paused" | "off" | "offline";

/** A building's plant room at this moment (the page that owns the data fills it in). */
export type Inside = {
  name: string;
  kind: string;
  servers: number;
  /** servers the scheduler switched on for heat */
  on: number;
  /** servers working on a customer's part right now (≤ on) */
  used: number;
  /** tank full: the rack is paused */
  paused: boolean;
  /** the device behind a person's rack left */
  offline: boolean;
  demandKw: number;
  /** heat the servers put into the tank now */
  heatKw: number;
  soc: number;
  tankKwh: number;
  status?: Status;
  /** the scheduler's decision for this rack, in words */
  reason?: string;
  /** the customer's part the rack is working on */
  job?: { label: string; part: number; progress: number } | null;
  /** the real device that runs this rack's parts in the demo */
  device?: { name: string; kind: "phone" | "laptop"; cores: number; parts: number; heatWh: number; color: string; watts: number } | null;
  /** what DigitalHeat sells one server-hour for (CHF) */
  sellChfH?: number;
};

/** The case's reference server (data/prices_2026.json) and its warm-water loop (scheduler/core.py). */
const SERVER = { model: "2× AMD EPYC 9654", cores: 192, kw: 1.0, rec: 0.8, outletC: 60 };

const STATE: Record<ServerState, { label: string; led: string; face: string; tone: string; text: string }> = {
  job: { label: "Computing", led: "#f2a65a", face: "#3a2a22", tone: "bg-amber-soft text-rust-deep", text: "Working on a customer's part. Its heat goes into the tank." },
  ready: { label: "On, waiting", led: "#e8d9a8", face: "#33312d", tone: "bg-cream text-ink", text: "Switched on for heat, waiting for the next part. It only heats while it computes." },
  paused: { label: "Paused", led: "#5fa8b0", face: "#2b3436", tone: "bg-teal-soft text-[#2f6e75]", text: "The tank is full, so the rack pauses and its work moves to a building that needs heat." },
  off: { label: "Off", led: "#5a5852", face: "#2a2926", tone: "bg-cream text-muted", text: "Off: the building needs no more heat right now, so this server stays dark." },
  offline: { label: "Offline", led: "#4a4844", face: "#262522", tone: "bg-cream text-faint", text: "The device behind this rack has left the demo." },
};

export function serverState(d: Inside, k: number): ServerState {
  if (d.offline) return "offline";
  if (d.paused) return "paused";
  if (k < d.used) return "job";
  if (k < d.on) return "ready";
  return "off";
}

/* ------------------------------- isometric drawing ------------------------------- */

const U = 34; // px per metre-ish unit
const OX = 270,
  OY = 190;
/** a point of the room (x along the right wall, y along the left wall, z up) on screen */
const P = (x: number, y: number, z: number): [number, number] => [OX + (x - y) * U * 0.866, OY + (x + y) * U * 0.5 - z * U];
const pts = (...ps: [number, number][]) => ps.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" ");
const line = (...ps: [number, number][]) => "M" + ps.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" L");

const ROOM = { x: 12, y: 8, h: 5.2 };
const RACK = { w: 1.5, y0: 0.15, y1: 1.55, base: 0.3, cap: 0.22, gap: 0.3, x: 1.7, room: 4.1 };
const PIPE_Z = 4.85;
/** the tank stands at the front left, clear of the rack row along the back wall */
const TANK = { x: 2, y: 6, r: 1.15, h: 3.6 };
const MAX_RACKS = 5;
const MAX_SLOT = 0.38;

/** Racks and slots for n servers: about 12 a rack (up to 5 racks), at least 4 slots (a small cabinet for a home); slots get thinner past that. */
function layout(n: number) {
  const racks = Math.max(1, Math.min(MAX_RACKS, Math.ceil(n / 12)));
  const per = Math.max(4, Math.ceil(n / racks));
  return { racks, per, slot: Math.min(MAX_SLOT, RACK.room / per), shown: n };
}

function Rack({ r, per, slot, n, d, sel, onPick }: { r: number; per: number; slot: number; n: number; d: Inside; sel: number; onPick: (k: number) => void }) {
  const x0 = RACK.x + r * (RACK.w + RACK.gap),
    x1 = x0 + RACK.w;
  const { y0, y1 } = RACK;
  const h = RACK.base + per * slot + RACK.cap;
  const warm = Array.from({ length: per }, (_, s) => r * per + s).some((k) => k < n && serverState(d, k) === "job");
  return (
    <g>
      {/* shadow on the floor */}
      <polygon points={pts(P(x0 - 0.1, y0, 0), P(x1 + 0.35, y0, 0), P(x1 + 0.35, y1 + 0.35, 0), P(x0 - 0.1, y1 + 0.35, 0))} fill="#141412" opacity={0.08} />
      {/* body: top, side, front */}
      <polygon points={pts(P(x0, y0, h), P(x1, y0, h), P(x1, y1, h), P(x0, y1, h))} fill="#47443e" />
      <polygon points={pts(P(x1, y0, 0), P(x1, y1, 0), P(x1, y1, h), P(x1, y0, h))} fill="#1f1e1b" />
      <polygon points={pts(P(x0, y1, 0), P(x1, y1, 0), P(x1, y1, h), P(x0, y1, h))} fill="#2f2d29" />
      {/* the DigitalHeat mark on the top cap */}
      <polygon points={pts(P(x0 + 0.12, y1, h - 0.05), P(x0 + 0.5, y1, h - 0.05), P(x0 + 0.5, y1, h - RACK.cap + 0.05), P(x0 + 0.12, y1, h - RACK.cap + 0.05))} fill="#c0653a" />
      {/* the servers, from the bottom up */}
      {Array.from({ length: per }, (_, s) => {
        const k = r * per + s;
        const za = RACK.base + s * slot + 0.03,
          zb = za + slot - Math.min(0.06, slot * 0.2),
          zc = (za + zb) / 2;
        const xa = x0 + 0.1,
          xb = x1 - 0.1;
        if (k >= n)
          // a blanking plate: an empty slot
          return <polygon key={s} points={pts(P(xa, y1, za), P(xb, y1, za), P(xb, y1, zb), P(xa, y1, zb))} fill="#262522" />;
        const st = serverState(d, k);
        const S = STATE[st];
        const led = P(xb - 0.16, y1, zc);
        return (
          <g key={s} onClick={() => onPick(k)} className="cursor-pointer [&:hover>polygon]:brightness-150">
            <title>{`Server ${k + 1} · ${S.label}`}</title>
            <polygon points={pts(P(xa, y1, za), P(xb, y1, za), P(xb, y1, zb), P(xa, y1, zb))} fill={S.face} stroke={sel === k ? "#fbfaf6" : "#1a1917"} strokeWidth={sel === k ? 2 : 0.6} />
            {/* vents */}
            {[0.25, 0.42, 0.59].map((v) => (
              <path key={v} d={line(P(xa + v, y1, za + 0.08), P(xa + v, y1, zb - 0.08))} stroke="#141412" strokeWidth={1.4} opacity={0.6} />
            ))}
            {/* load bar: how far into the part the rack is */}
            {st === "job" && <path d={line(P(xa + 0.75, y1, zc), P(xa + 0.75 + 0.55 * Math.max(0.08, d.job?.progress ?? 0.5), y1, zc))} stroke="#c0653a" strokeWidth={2.4} strokeLinecap="round" />}
            {/* the glow: its group holds the faintness, so the blink animation (which sets opacity) cannot override it */}
            {st !== "off" && st !== "offline" && (
              <g opacity={0.28}>
                <circle cx={led[0]} cy={led[1]} r={6} fill={S.led} className={st === "job" ? "led-blink" : undefined} />
              </g>
            )}
            <circle cx={led[0]} cy={led[1]} r={2.4} fill={S.led} className={st === "job" ? "led-blink" : undefined} />
          </g>
        );
      })}
      {/* heat rising off a rack that computes */}
      {warm &&
        [0.25, 0.85, 1.45].map((dx, j) => {
          const [bx, by] = P(x0 + dx, (y0 + y1) / 2, h + 0.05);
          return <path key={j} d={`M${bx},${by} q-5,-10 0,-20 q5,-10 0,-20`} stroke="#f2a65a" strokeWidth={2} fill="none" strokeLinecap="round" className="heat-rise" style={{ animationDelay: `${j * 0.5}s` }} />;
        })}
    </g>
  );
}

/** A vertical tank: glass-like shell, water at its level, a metal cap. */
function Tank({ level, hot, kwh }: { level: number; hot: boolean; kwh: number }) {
  const [cx, by] = P(TANK.x, TANK.y, 0);
  const ty = by - TANK.h * U;
  const rx = TANK.r * U * 1.2247,
    ry = TANK.r * U * 0.7071;
  const wy = by - Math.max(0.02, level) * TANK.h * U;
  const body = (top: number) => `M${cx - rx},${top} L${cx - rx},${by} A${rx},${ry} 0 0 0 ${cx + rx},${by} L${cx + rx},${top} A${rx},${ry} 0 0 1 ${cx - rx},${top} Z`;
  return (
    <g>
      <ellipse cx={cx + 8} cy={by + 6} rx={rx + 10} ry={ry + 5} fill="#141412" opacity={0.08} />
      <path d={body(ty)} fill="#fbfaf6" opacity={0.85} />
      <path d={body(wy)} fill="url(#water)" />
      <ellipse cx={cx} cy={wy} rx={rx} ry={ry} fill="#9ccfd5" opacity={0.9} />
      {hot && (
        <g opacity={0.14}>
          <path d={body(wy)} fill="#f2a65a" className="led-blink" />
        </g>
      )}
      <path d={body(ty)} fill="none" stroke="#b9b2a3" strokeWidth={1.4} />
      <ellipse cx={cx} cy={ty} rx={rx} ry={ry} fill="#e2dccf" stroke="#b9b2a3" strokeWidth={1.4} />
      {/* level marks */}
      {[0.25, 0.5, 0.75].map((f) => (
        <path key={f} d={`M${cx - rx},${by - f * TANK.h * U} l9,4`} stroke="#9a958a" strokeWidth={1} />
      ))}
      <text x={cx} y={by - TANK.h * U * 0.5} textAnchor="middle" className="fill-ink text-[20px] font-semibold" style={{ paintOrder: "stroke", stroke: "#fbfaf6", strokeWidth: 4 }}>
        {Math.round(level * 100)} %
      </text>
      <text x={cx} y={by - TANK.h * U * 0.5 + 18} textAnchor="middle" className="fill-muted text-[12px]" style={{ paintOrder: "stroke", stroke: "#fbfaf6", strokeWidth: 3 }}>
        {kwh > 0 ? `of ${kwh} kWh` : "no tank"}
      </text>
    </g>
  );
}

function Pipe({ d, color, flow, w = 5 }: { d: string; color: string; flow: boolean; w?: number }) {
  return (
    <g>
      <path d={d} stroke="#141412" strokeOpacity={0.18} strokeWidth={w + 2.5} fill="none" strokeLinejoin="round" strokeLinecap="round" />
      <path d={d} stroke={color} strokeWidth={w} fill="none" strokeLinejoin="round" strokeLinecap="round" />
      {flow && <path d={d} stroke="#fff" strokeOpacity={0.75} strokeWidth={1.6} fill="none" strokeDasharray="5 11" strokeLinecap="round" className="pipe-flow" />}
    </g>
  );
}

function Room({ d, sel, onPick }: { d: Inside; sel: number; onPick: (k: number) => void }) {
  const { racks, per, slot, shown } = layout(d.servers);
  const flow = d.used > 0 && !d.paused && !d.offline;
  const toBuilding = d.demandKw > 0.05 && d.soc > 0.05;
  const level = d.tankKwh > 0 ? Math.max(0, Math.min(1, d.soc / d.tankKwh)) : 0;
  const rackX = (r: number) => RACK.x + r * (RACK.w + RACK.gap) + RACK.w / 2;
  const rackTop = RACK.base + per * slot + RACK.cap;
  const last = rackX(racks - 1);
  // flow (warm) and return (cool) headers run above the racks to the left wall, then forward to the tank; they never cross
  const flowPath = [
    ...Array.from({ length: racks }, (_, r) => line(P(rackX(r) - 0.3, 0.75, rackTop), P(rackX(r) - 0.3, 0.75, PIPE_Z))),
    line(P(last - 0.3, 0.75, PIPE_Z), P(0.6, 0.75, PIPE_Z), P(0.6, TANK.y + 0.35, PIPE_Z), P(TANK.x, TANK.y + 0.35, PIPE_Z), P(TANK.x, TANK.y + 0.35, TANK.h)),
  ].join(" ");
  const backPath = [
    ...Array.from({ length: racks }, (_, r) => line(P(rackX(r) + 0.3, 1.1, rackTop), P(rackX(r) + 0.3, 1.1, PIPE_Z + 0.25))),
    line(P(last + 0.3, 1.1, PIPE_Z + 0.25), P(0.95, 1.1, PIPE_Z + 0.25), P(0.95, TANK.y - 0.35, PIPE_Z + 0.25), P(TANK.x, TANK.y - 0.35, PIPE_Z + 0.25), P(TANK.x, TANK.y - 0.35, TANK.h)),
  ].join(" ");
  // out to the building's heating, through the left wall behind the tank
  const outY = TANK.y + 0.7;
  const outPath = line(P(TANK.x - 0.6, outY, 0.55), P(0, outY, 0.55), P(0, outY, 2.3));
  const label = (x: number, y: number, z: number, text: string, anchor: "start" | "middle" | "end" = "middle") => {
    const [sx, sy] = P(x, y, z);
    return (
      <text x={sx} y={sy} textAnchor={anchor} className="fill-muted text-[12.5px] font-semibold" style={{ paintOrder: "stroke", stroke: "#f1ece2", strokeWidth: 4 }}>
        {text}
      </text>
    );
  };
  return (
    <svg viewBox="20 0 620 548" className="h-full w-full" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#7cc3cb" />
          <stop offset="1" stopColor="#3f8f9a" />
        </linearGradient>
        <linearGradient id="wallR" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f6f2ea" />
          <stop offset="1" stopColor="#ece6da" />
        </linearGradient>
        <linearGradient id="wallL" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ebe5d8" />
          <stop offset="1" stopColor="#e0d9ca" />
        </linearGradient>
      </defs>
      {/* floor with tiles */}
      <polygon points={pts(P(0, 0, 0), P(ROOM.x, 0, 0), P(ROOM.x, ROOM.y, 0), P(0, ROOM.y, 0))} fill="#ddd6c6" />
      {Array.from({ length: ROOM.x - 1 }, (_, i) => (
        <path key={`fx${i}`} d={line(P(i + 1, 0, 0), P(i + 1, ROOM.y, 0))} stroke="#cfc7b5" strokeWidth={0.8} />
      ))}
      {Array.from({ length: ROOM.y - 1 }, (_, i) => (
        <path key={`fy${i}`} d={line(P(0, i + 1, 0), P(ROOM.x, i + 1, 0))} stroke="#cfc7b5" strokeWidth={0.8} />
      ))}
      {/* walls, with their top edge */}
      <polygon points={pts(P(0, 0, 0), P(0, ROOM.y, 0), P(0, ROOM.y, ROOM.h), P(0, 0, ROOM.h))} fill="url(#wallL)" />
      <polygon points={pts(P(0, 0, 0), P(ROOM.x, 0, 0), P(ROOM.x, 0, ROOM.h), P(0, 0, ROOM.h))} fill="url(#wallR)" />
      <path d={line(P(0, ROOM.y, ROOM.h), P(0, 0, ROOM.h), P(ROOM.x, 0, ROOM.h))} stroke="#cfc7b5" strokeWidth={2} fill="none" />
      <path d={line(P(0, 0, 0), P(0, 0, ROOM.h))} stroke="#d6cfbf" strokeWidth={1} />
      {/* the heating manifold on the left wall */}
      <polygon points={pts(P(0, outY - 0.55, 2.3), P(0, outY + 0.55, 2.3), P(0, outY + 0.55, 3.1), P(0, outY - 0.55, 3.1))} fill="#d9d2c3" stroke="#bdb5a5" />
      {label(0, outY, 3.45, "To heating")}
      <Pipe d={outPath} color="#f2a65a" flow={toBuilding} />
      {Array.from({ length: racks }, (_, r) => (
        <Rack key={r} r={r} per={per} slot={slot} n={shown} d={d} sel={sel} onPick={onPick} />
      ))}
      {d.tankKwh > 0 && <Tank level={level} hot={flow} kwh={d.tankKwh} />}
      <Pipe d={backPath} color="#5fa8b0" flow={flow} w={4} />
      <Pipe d={flowPath} color="#c0653a" flow={flow} />
      {d.tankKwh > 0 && label(TANK.x + 1.3, TANK.y + 1.3, 0, "Heat tank")}
      {label((rackX(0) + last) / 2, RACK.y1 + 1.1, 0, `${d.servers} server${d.servers === 1 ? "" : "s"} in ${racks} rack${racks === 1 ? "" : "s"}`)}
      {label(0.6, 2.6, PIPE_Z + 0.45, `warm water, up to ${SERVER.outletC} °C`)}
    </svg>
  );
}

/* ------------------------------------ page ------------------------------------ */

export function BuildingInside({ d, onBack, area }: { d: Inside; onBack: () => void; area: { top: number; bottom: number; left: number; right: number } }) {
  // the server shown in the details: the first one computing, until the operator picks one
  const firstBusy = Math.max(0, Array.from({ length: d.servers }, (_, k) => serverState(d, k)).indexOf("job"));
  const [picked, setPicked] = useState<number | null>(null);
  const sel = picked !== null && picked < d.servers ? picked : firstBusy;
  const st = serverState(d, sel);
  const S = STATE[st];
  const level = d.tankKwh > 0 ? Math.max(0, Math.min(1, d.soc / d.tankKwh)) : 0;
  const running = st === "job";
  const DevIcon = d.device?.kind === "phone" ? Smartphone : Laptop;

  // arrow keys step through the servers
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowUp" || e.key === "ArrowRight") setPicked(Math.min(d.servers - 1, sel + 1));
      if (e.key === "ArrowDown" || e.key === "ArrowLeft") setPicked(Math.max(0, sel - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sel, d.servers]);

  return (
    <div className="inside-enter absolute inset-0 bg-[#f1ece2]">
      <div className="absolute flex flex-col gap-3" style={{ top: area.top - 30, bottom: area.bottom, left: area.left, right: area.right }}>
        {/* the building and how its heat stands */}
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="flex shrink-0 items-center gap-1.5 rounded-full border border-line/60 bg-white px-4 py-2 text-[13.5px] font-semibold text-ink shadow-pill hover:bg-cream">
            <ArrowLeft size={14} /> Back outside
          </button>
          <div className="min-w-0">
            <div className="truncate font-display text-[22px] font-semibold leading-tight">Inside {d.name}</div>
            <div className="flex flex-wrap items-center gap-x-2 text-[13.5px] text-muted">
              <span>{d.kind} · plant room</span>
              <span>· needs {d.demandKw.toFixed(1)} kW</span>
              <span>· servers give {d.heatKw.toFixed(1)} kW</span>
              {d.tankKwh > 0 && <span>· tank {Math.round(level * 100)} %</span>}
            </div>
          </div>
        </div>

        <div className="flex min-h-0 flex-1 gap-4">
          <div className="relative min-w-0 flex-1">
            <Room d={d} sel={sel} onPick={setPicked} />
            <div className="pointer-events-none absolute bottom-1 left-1 flex flex-wrap gap-x-3 gap-y-1 text-[12.5px] text-muted">
              {(["job", "ready", "paused", "off"] as ServerState[]).map((k) => (
                <span key={k} className="flex items-center gap-1.5">
                  <span className="size-2.5 rounded-full ring-1 ring-ink/20" style={{ background: STATE[k].led }} /> {STATE[k].label}
                </span>
              ))}
              <span className="text-faint">· click a server</span>
            </div>
          </div>

          {/* the server picked in the rack */}
          <div className="rise w-[290px] shrink-0 self-start rounded-[20px] border border-line/60 bg-white p-4 shadow-pill">
            <div className="flex items-center justify-between gap-2">
              <div className="text-[17px] font-semibold">
                Server {sel + 1} <span className="font-normal text-muted">of {d.servers}</span>
              </div>
              <span className={clsx("flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[12.5px] font-semibold", S.tone)}>
                <span className={clsx("size-2 rounded-full", running && "led-blink")} style={{ background: S.led }} />
                {S.label}
              </span>
            </div>
            <p className="mt-2 text-[13.5px] leading-snug text-muted">{S.text}</p>

            {running && d.job && (
              <div className="mt-3 rounded-xl bg-cream p-2.5 ring-1 ring-line/70">
                <div className="flex justify-between text-[13.5px]">
                  <span className="font-semibold">{d.job.label}</span>
                  <span className="tabular-nums text-muted">part {d.job.part}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-white ring-1 ring-line">
                  <div className="h-full bg-rust transition-[width] duration-500" style={{ width: `${Math.round(d.job.progress * 100)}%` }} />
                </div>
              </div>
            )}

            <div className="mt-3 space-y-1.5 text-[13.5px]">
              <Row icon={<Cpu size={14} />} l="Hardware" v={`${SERVER.model}`} sub={`${SERVER.cores} cores, warm-water cooled`} />
              <Row icon={<Zap size={14} />} l="Power now" v={running ? `${SERVER.kw.toFixed(1)} kW` : "0 kW"} />
              <Row icon={<Flame size={14} />} l="Heat to tank" v={running ? `${(SERVER.kw * SERVER.rec).toFixed(1)} kW` : "0 kW"} sub={`${SERVER.rec * 100} % of its power comes back as heat`} />
              <Row icon={<Thermometer size={14} />} l="Water out" v={running ? `up to ${SERVER.outletC} °C` : "–"} />
              {d.sellChfH !== undefined && <Row icon={<Power size={14} />} l="Earns" v={running ? `CHF ${d.sellChfH.toFixed(2)} / h` : "CHF 0 / h"} />}
            </div>

            {d.reason && (
              <div className="mt-3 flex gap-2 border-t border-line/70 pt-2.5 text-[13px] text-muted">
                {d.paused ? <Pause size={13} className="mt-0.5 shrink-0" /> : <Droplets size={13} className="mt-0.5 shrink-0" />}
                <span>
                  <b className="font-semibold text-ink">Scheduler:</b> {d.reason}
                </span>
              </div>
            )}

            {d.device && (
              <div className="mt-3 border-t border-line/70 pt-2.5">
                <div className="text-[12.5px] font-semibold text-muted">Running the parts in this demo</div>
                <div className="mt-1.5 flex items-center gap-2 text-[13.5px]">
                  <span className="grid size-7 shrink-0 place-items-center rounded-lg text-white" style={{ background: d.device.color }}>
                    <DevIcon size={14} />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate font-semibold">{d.device.name}</span>
                    <span className="block text-[12.5px] text-muted">
                      {d.device.cores} cores · {d.device.parts} parts done · {d.device.heatWh.toFixed(1)} Wh of heat
                    </span>
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ icon, l, v, sub }: { icon: React.ReactNode; l: string; v: string; sub?: string }) {
  return (
    <div className="flex gap-2">
      <span className="mt-0.5 shrink-0 text-faint">{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="flex justify-between gap-2">
          <span className="text-muted">{l}</span>
          <b className="text-right font-semibold tabular-nums">{v}</b>
        </span>
        {sub && <span className="block text-[12px] text-faint">{sub}</span>}
      </span>
    </div>
  );
}
