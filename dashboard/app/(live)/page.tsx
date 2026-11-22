"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import clsx from "clsx";
import QRCode from "qrcode";
import { Briefcase, Building2, Droplets, FlaskConical, GripVertical, Hospital, House, Leaf, Maximize2, Minimize2, Pause, QrCode, RotateCcw, Snowflake, Sun, Timer, Trash2, Users, Waves, X } from "lucide-react";
import { LogoMark } from "@/components/Logo";
import { JobView, jobSeconds } from "@/components/RenderMosaic";
import { useServerNode } from "@/lib/live/useServerNode";
import { plainSite, useSavedSites, type Kind, type Schedule, type SiteIn } from "@/lib/schedule";
import { CardBtn } from "@/components/SitesMap";
import { CONDITIONS, KIND_NAME, PRODUCTS, TANK_RESUME, TANK_SPEED, type CondKey, type DayHour, type DaySite, type Job, type LiveNode, type LiveState } from "@/lib/live/shared";

/*
 * Live demo, room screen (projector). A full-screen map of the fleet with floating panels.
 *
 * The fleet is the overview's sites plus one building per person who scanned the QR code, each with
 * enough servers for 100 % of its heat. The operator picks a moment (now, a January morning, a July
 * afternoon); the DigitalHeat scheduler decides which buildings need heat then. The jury orders every
 * job on /client (3D rendering, AI embeddings, AI reranking); its parts go only to racks whose building
 * needs heat and the output assembles here. This screen also runs parts, in background workers, for
 * the overview's sites (they have no phones).
 */

const SitesMap = dynamic(() => import("@/components/SitesMap").then((m) => m.SitesMap), { ssr: false });

const ICON: Record<string, typeof House> = { house: House, family: Users, cityhouse: Building2, hospital: Hospital, spa: Waves, greenhouse: Leaf, office: Briefcase, pharma: FlaskConical };
const COND_ICON: Record<CondKey, typeof Sun> = { now: Timer, january: Snowflake, july: Sun };
const PANEL = "rounded-[22px] bg-cream/95 shadow-xl ring-1 ring-line/80 backdrop-blur";

const post = async (body: object) => {
  const r = await fetch("/api/live", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
};

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const fmtIso = (iso: string) => {
  const [, m, d] = iso.split("-").map(Number);
  return `${d} ${MON[m - 1]}`;
};
const onOf = (x: DayHour["sites"][number] | undefined) => (x ? Math.ceil(x.running - 1e-9) : 0);
/** A building's rack: the person's phone, or the background worker this screen runs for an overview site. */
const nodeOf = (site: DaySite, nodes: Map<string, LiveNode>) => nodes.get(site.node ?? `base-${site.id.toLowerCase()}`);
/**
 * Servers in use: the ones on for heat, while the rack is working on a customer's job: it holds a part,
 * or parts are still waiting for it (between two parts it is only fetching the next one). Otherwise none.
 */
const usedOf = (n: LiveNode | undefined, x: DayHour["sites"][number] | undefined, queued: boolean) => (n && n.state === "running" && (n.current || queued) ? onOf(x) : 0);
const hasQueue = (s: LiveState | null) => !!s?.jobs.some((j) => j.tiles.some((t) => t.state === "pending"));

/** How long the map shows a part that moved between racks. */
const MOVE_SHOW_MS = 6000;

/**
 * The scheduler's decision in the shape the map reads (it was made for the yearly balance). Buildings with
 * a full tank show as paused; parts that just moved from a paused rack to another show as arrows.
 */
function hourSchedule(sites: DaySite[], h: DayHour, full: string[] = [], moves: LiveState["moves"] = [], now = 0): Schedule {
  const idx = new Map(sites.map((x, i) => [x.id, i]));
  const arrows = moves
    .filter((m) => now - m.at < MOVE_SHOW_MS && idx.has(m.from) && idx.has(m.to))
    .map((m, k) => [k, idx.get(m.from)!, 0, 0, idx.get(m.to)!, h.t]);
  const at = (v: number) => {
    const a: number[] = [];
    a[h.t] = v;
    return a;
  };
  return {
    constants: { heat_recovery: 0.8 },
    sites: sites.map((x) => ({ ...x, kind: x.kind as Kind })),
    series: h.sites.map((x, i) => ({
      demand: at(x.demand),
      running: at(x.running),
      served: at(x.served),
      soc: at(x.soc),
      rerank_sh: at(0),
      embed_sh: at(0),
      moved_in: at(0),
      paused_now: at(full.includes(sites[i]?.id) ? 1 : 0),
      waiting_now: at(0),
    })),
    deadline_jobs: arrows,
  } as unknown as Schedule;
}

export default function LivePage() {
  const [s, setS] = useState<LiveState | null>(null);
  const [sites] = useSavedSites();
  const [selected, setSelected] = useState(-1);
  const [busy, setBusy] = useState<CondKey | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [joinOverride, setJoinOverride] = useState<string | null>(null);
  const [qrOpen, setQrOpen] = useState(false);
  const [viewing, setViewing] = useState<number | null>(null); // a job clicked in the list; null = follow the one running
  const [focus, setFocus] = useState<string | null>(null); // a rack whose parts light up in the job view

  useEffect(() => {
    Promise.resolve().then(() => setJoinOverride(new URLSearchParams(window.location.search).get("join")));
    let alive = true;
    const pull = async () => {
      try {
        const r = await fetch("/api/live", { cache: "no-store" });
        const next = (await r.json()) as LiveState;
        if (alive) setS(next);
      } catch {}
    };
    pull();
    const id = setInterval(pull, 500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const choose = async (key: CondKey) => {
    setBusy(key);
    setErr(null);
    try {
      const st = await post({ op: "conditions", key, sites: sites.map(plainSite) });
      if (st.error) throw new Error(st.error);
      setS(st);
    } catch (e) {
      setErr(String((e as Error).message));
    } finally {
      setBusy(null);
    }
  };

  // the overview's sites; the first time, let the scheduler decide for now
  const siteKey = JSON.stringify(sites.map(plainSite));
  const ready = s !== null;
  const hasCond = !!s?.conditions;
  useEffect(() => {
    if (!ready) return;
    if (!hasCond) post({ op: "conditions", key: "now", sites: JSON.parse(siteKey) }).catch(() => {});
    else post({ op: "sites", sites: JSON.parse(siteKey) }).catch(() => {});
  }, [siteKey, ready, hasCond]);

  const hour = s?.hour ?? null;
  const fleet: DaySite[] = s?.sites ?? [];
  const mapSites: SiteIn[] = fleet.map((x) => ({ id: x.id, kind: x.kind as Kind, name: x.person ?? x.name, lat: x.lat, lon: x.lon, servers: x.servers }));
  const nodes = useMemo(() => new Map((s?.nodes ?? []).map((n) => [n.id, n])), [s]);
  // the map's pins count servers in use, like the buildings panel
  const S =
    hour && fleet.length
      ? hourSchedule(fleet, { ...hour, sites: hour.sites.map((x, i) => ({ ...x, running: usedOf(nodeOf(fleet[i], nodes), x, hasQueue(s)) })) }, s?.full, s?.moves, s?.now)
      : null;
  const fill = async (i: number) => {
    const site = fleet[i];
    if (site) setS(await post({ op: "fill", site: site.id }));
  };
  const joinUrl = (joinOverride ?? s?.joinBase ?? "") + "/join";
  const clientUrl = (joinOverride ?? s?.joinBase ?? "") + "/client";
  const people = (s?.nodes ?? []).filter((n) => !n.base && n.state !== "offline").length;
  const jobs = s?.jobs ?? [];
  const current = jobs.find((j) => j.id === viewing) ?? jobs.find((j) => !j.doneAt) ?? jobs.at(-1) ?? null;
  const baseSites = fleet.filter((x) => !x.person);

  return (
    <div className="fixed inset-0 z-[1000] overflow-hidden bg-paper text-ink">
      <div className="absolute inset-0">
        {mapSites.length > 0 && (
          <SitesMap
            sites={mapSites}
            schedule={S}
            t={hour?.t ?? 0}
            dur={900}
            selected={selected}
            setSelected={setSelected}
            setServers={() => {}}
            adding={false}
            onAdd={() => {}}
            onRemove={() => {}}
            busy={false}
            height="h-full"
            pad={{ top: 90, bottom: 470, left: 340, right: 440 }}
            bare
            pinFrom={0}
            cardExtra={(i) =>
              fleet[i] && !s?.full.includes(fleet[i].id) ? (
                <>
                  <CardBtn onClick={() => fill(i)} title="Someone stops drawing heat: the tank tops up to 100 %, the rack pauses and its work moves on">
                    <Droplets size={13} /> Fill tank
                  </CardBtn>
                  {/* the operator fills a tank while its rack holds a part, so the pause shows */}
                  <span className="w-full px-1 text-[11.5px] text-cream/60">
                    {nodeOf(fleet[i], nodes)?.current ? `Working on part ${nodeOf(fleet[i], nodes)!.current!.chunk + 1} now` : "Between parts"}
                  </span>
                </>
              ) : fleet[i] ? (
                <span className="flex items-center gap-1 px-1 text-[12px] font-semibold text-[#7cc3cb]">
                  <Pause size={11} fill="currentColor" /> Tank full: paused to {Math.round(TANK_RESUME * 100)} %
                </span>
              ) : null
            }
          />
        )}
      </div>

      {/* the operator laptop renders for the overview's sites (they have no phones) */}
      {baseSites.map((x) => (
        <BaseRack key={x.id} site={x} />
      ))}

      {/* left: the moment and the racks */}
      <div className="pointer-events-none absolute bottom-4 left-4 top-4 flex w-[300px] flex-col gap-2.5">
        <div className={clsx(PANEL, "pointer-events-auto px-4 py-3")}>
          <div className="flex items-center gap-2">
            <LogoMark size={22} />
            <span className="font-display text-[14px] font-semibold">DigitalHeat · Live</span>
            <button
              onClick={() => setQrOpen(true)}
              title="Show the join code"
              className="ml-auto flex items-center gap-1 rounded-full py-1 pl-2 pr-2.5 text-[12px] font-semibold ring-1 ring-ink/25 hover:bg-card"
            >
              <QrCode size={13} /> Join
              <span className="flex items-center gap-0.5 font-normal text-muted">
                · <Users size={11} /> {people}
              </span>
            </button>
          </div>
          <div className="mt-2.5 flex gap-1">
            {(Object.keys(CONDITIONS) as CondKey[]).map((k) => {
              const Icon = COND_ICON[k];
              const on = s?.conditions?.key === k;
              return (
                <button
                  key={k}
                  disabled={busy !== null}
                  onClick={() => choose(k)}
                  className={clsx(
                    "flex flex-1 items-center justify-center gap-1 rounded-full py-1.5 text-[12.5px] font-semibold ring-1 disabled:opacity-60",
                    on ? "bg-ink text-cream ring-ink" : "ring-ink/25 hover:bg-card",
                  )}
                >
                  <Icon size={13} /> {k === "now" ? "Now" : k === "january" ? "January" : "July"}
                </button>
              );
            })}
          </div>
          {s?.conditions && hour && (
            <div className="mt-2.5 leading-tight">
              <div className="flex items-baseline gap-2">
                <span className="font-display text-[26px] font-semibold tabular-nums">{String(s.conditions.hour).padStart(2, "0")}:00</span>
                <span className="text-[14px] font-semibold">{fmtIso(s.conditions.date)}</span>
                <span className="text-[14px] text-muted">{hour.sites[0]?.temp.toFixed(0)} °C</span>
              </div>
              <div className="mt-0.5 text-[12.5px] text-muted">
                {hour.sites.filter((x) => x.running > 0).length} of {fleet.length} buildings need heat{s.planning ? " · deciding…" : ""}
                <span className="ml-1 text-faint" title="The tanks run 60 times faster than real time, so the jobs' heat shows">· tanks 1 s = {TANK_SPEED / 60} min</span>
              </div>
            </div>
          )}
        </div>
        <Racks s={s} hour={hour} nodes={nodes} selected={selected} onSelect={setSelected} onFocus={setFocus} />
      </div>

      {/* right: jobs from customers */}
      <div className="pointer-events-none absolute bottom-4 right-4 top-4 flex w-[400px] flex-col gap-2.5">
        {err && <div className={clsx(PANEL, "pointer-events-auto px-4 py-2 text-[13px] text-alarm")}>{err}</div>}
        <Jobs
          jobs={jobs}
          now={s?.now ?? 0}
          shown={current?.id ?? null}
          onShow={(id) => setViewing((v) => (v === id ? null : id))}
          actions={
            <>
              <IconBtn title="Remove offline phones" onClick={async () => setS(await post({ op: "forget-offline" }))}>
                <Trash2 size={13} />
              </IconBtn>
              <IconBtn title="Reset" onClick={async () => confirm("Clear all phones and jobs?") && setS(await post({ op: "reset" }))}>
                <RotateCcw size={13} />
              </IconBtn>
            </>
          }
        />
      </div>

      {/* centre: the job being rendered; the operator can drag it out of the way or make it compact */}
      <JobPanel>
        {(compact, bar) =>
          current ? (
            <>
              <div className="mb-2 flex items-center justify-between gap-3 px-1">
                {bar}
                <div className={clsx("min-w-0 flex-1 truncate font-semibold", compact ? "text-[13px]" : "text-[15px]")}>
                  {PRODUCTS[current.kind].label}
                  {current.query && <span className="font-normal text-muted"> · “{current.query}”</span>}
                </div>
                <div className={clsx("shrink-0 tabular-nums text-muted", compact ? "text-[12px]" : "text-[13px]")}>
                  {current.tiles.filter((t) => t.state === "done").length}/{current.tiles.length} parts · {jobSeconds(current, s!.now).toFixed(0)} s
                  {current.doneAt ? " · done" : ""}
                </div>
              </div>
              <JobView job={current} nodes={nodes} focus={focus} onFocus={setFocus} />
            </>
          ) : compact ? (
            <div className="flex items-center gap-3 px-1">
              {bar}
              <div className="min-w-0 flex-1 truncate text-[14px] font-semibold">
                Waiting for a customer&apos;s job <span className="font-normal text-muted">· {clientUrl.replace(/^https?:\/\//, "")}</span>
              </div>
            </div>
          ) : (
            <>
              <div className="px-1">{bar}</div>
              <div className="grid aspect-[16/6] place-items-center text-center">
                <div>
                  <div className="font-display text-[24px] font-semibold">Waiting for a customer&apos;s job</div>
                  <div className="mt-1 text-[14px] text-muted">Order at {clientUrl.replace(/^https?:\/\//, "")}</div>
                </div>
              </div>
            </>
          )
        }
      </JobPanel>

      {/* the join code in the middle: click the small one; click anywhere to close */}
      {qrOpen && (
        <div onClick={() => setQrOpen(false)} className="absolute inset-0 z-20 grid cursor-pointer place-items-center bg-ink/30 backdrop-blur-[2px]">
          <div className={clsx(PANEL, "flex flex-col items-center gap-3 px-10 py-8")}>
            <QR url={joinUrl} size={420} />
            <div className="font-display text-[34px] font-semibold">Scan to become a server</div>
            <div className="text-[16px] text-muted">{people === 1 ? "1 person has" : `${people} people have`} joined</div>
          </div>
        </div>
      )}
    </div>
  );
}

/* --------------------------------- pieces --------------------------------- */

const PANEL_KEY = "dh-live-job-panel";

/**
 * The job panel floats over the map: drag it by its handle to uncover a building, or make it compact.
 * Where it is and how big are kept in this browser; double-click the handle to put it back.
 */
function JobPanel({ children }: { children: (compact: boolean, bar: React.ReactNode) => React.ReactNode }) {
  const [compact, setCompact] = useState(false);
  const [off, setOff] = useState({ x: 0, y: 0 });
  const box = useRef<HTMLDivElement>(null);
  const drag = useRef<{ px: number; py: number; x: number; y: number } | null>(null);
  useEffect(() => {
    try {
      const v = JSON.parse(localStorage.getItem(PANEL_KEY) || "null");
      if (v && typeof v.x === "number" && typeof v.y === "number")
        Promise.resolve().then(() => {
          setOff({ x: v.x, y: v.y });
          setCompact(!!v.compact);
        });
    } catch {}
  }, []);
  const save = (o: { x: number; y: number }, c: boolean) => localStorage.setItem(PANEL_KEY, JSON.stringify({ ...o, compact: c }));
  const bar = (
    <span className="flex shrink-0 items-center gap-0.5">
      <span
        title="Drag to move · double-click to put back"
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId);
          drag.current = { px: e.clientX, py: e.clientY, x: off.x, y: off.y };
        }}
        onPointerMove={(e) => {
          const d = drag.current;
          const r = box.current?.getBoundingClientRect();
          if (!d || !r) return;
          let x = d.x + e.clientX - d.px,
            y = d.y + e.clientY - d.py;
          // keep at least 80 px of the panel on screen
          const dx = x - off.x,
            dy = y - off.y;
          if (r.left + dx > window.innerWidth - 80) x -= r.left + dx - (window.innerWidth - 80);
          if (r.right + dx < 80) x += 80 - (r.right + dx);
          if (r.top + dy < 0) y -= r.top + dy;
          if (r.top + dy > window.innerHeight - 40) y -= r.top + dy - (window.innerHeight - 40);
          setOff({ x, y });
        }}
        onPointerUp={() => {
          drag.current = null;
          save(off, compact);
        }}
        onDoubleClick={() => {
          setOff({ x: 0, y: 0 });
          save({ x: 0, y: 0 }, compact);
        }}
        className="grid size-7 cursor-grab touch-none place-items-center rounded-full text-muted hover:bg-card hover:text-ink active:cursor-grabbing"
      >
        <GripVertical size={15} />
      </span>
      <button
        title={compact ? "Make it bigger" : "Make it compact"}
        onClick={() => {
          setCompact(!compact);
          save(off, !compact);
        }}
        className="grid size-7 place-items-center rounded-full text-muted hover:bg-card hover:text-ink"
      >
        {compact ? <Maximize2 size={13} /> : <Minimize2 size={13} />}
      </button>
    </span>
  );
  return (
    <div className="pointer-events-none absolute bottom-4 left-[332px] right-[432px] flex flex-col items-center gap-2">
      <div
        ref={box}
        className={clsx(PANEL, "pointer-events-auto w-full", compact ? "max-w-[420px] p-2.5" : "max-w-[820px] p-3")}
        style={{ transform: `translate(${off.x}px, ${off.y}px)` }}
      >
        {children(compact, bar)}
      </div>
    </div>
  );
}

function IconBtn({ title, onClick, children }: { title: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button title={title} onClick={onClick} className="grid size-7 place-items-center rounded-full ring-1 ring-line hover:bg-card">
      {children}
    </button>
  );
}

/** Renders the share of one of the overview's sites in this browser, while the scheduler keeps it on. */
function BaseRack({ site }: { site: DaySite }) {
  const { canvas } = useServerNode(`base-${site.id.toLowerCase()}`, { name: site.name, workers: 2, device: "laptop" });
  return <canvas ref={canvas} className="hidden" />;
}


/** The live tank's level, and the building's heat demand. */
function tankState(x: DayHour["sites"][number], tank: number) {
  const full = tank > 0 ? Math.max(0, Math.min(1, x.soc / tank)) : 0;
  const kw = x.demand < 10 ? x.demand.toFixed(1) : String(Math.round(x.demand));
  return { full, need: x.demand > 0.05 ? `needs ${kw} kW` : "no heat needed" };
}

function Racks({
  s,
  hour,
  nodes,
  selected,
  onSelect,
  onFocus,
}: {
  s: LiveState | null;
  hour: DayHour | null;
  nodes: Map<string, LiveNode>;
  selected: number;
  onSelect: (i: number) => void;
  onFocus: (id: string | null) => void;
}) {
  const sites = s?.sites ?? [];
  const queued = hasQueue(s);
  return (
    <div className={clsx(PANEL, "pointer-events-auto min-h-0 shrink overflow-auto p-3 scroll-thin")}>
      <div className="px-1 text-[11.5px] font-semibold uppercase tracking-[0.12em] text-muted">Servers</div>
      <div className="mt-1 space-y-0.5" onMouseLeave={() => onFocus(null)}>
        {sites.map((site, i) => {
          const n = nodeOf(site, nodes);
          return (
            <Rack
              key={site.id}
              site={site}
              n={n}
              x={hour?.sites[i]}
              queued={queued}
              full={!!s?.full.includes(site.id)}
              selected={i === selected}
              onClick={() => onSelect(i)}
              onHover={() => onFocus(n?.id ?? null)}
            />
          );
        })}
      </div>
    </div>
  );
}

function Rack({
  site,
  n,
  x,
  queued,
  full,
  selected,
  onClick,
  onHover,
}: {
  site: DaySite;
  n?: LiveNode;
  x?: DayHour["sites"][number];
  queued: boolean;
  full: boolean;
  selected: boolean;
  onClick: () => void;
  onHover: () => void;
}) {
  const on = usedOf(n, x, queued);
  const Icon = ICON[site.kind] ?? Building2;
  const off = !!site.person && (!n || n.state === "offline");
  const tk = x ? tankState(x, site.tank_kwh) : null;
  return (
    <button
      onClick={onClick}
      onMouseEnter={onHover}
      title="Hover to see this building's parts in the job"
      className={clsx("flex w-full items-center gap-2.5 rounded-xl px-2 py-1.5 text-left", selected ? "bg-paper" : "hover:bg-paper/60", off && "opacity-45")}
    >
      {/* the tank, with its level */}
      <span className="relative grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-[7px] bg-card ring-1 ring-line" title={tk ? `Tank ${Math.round(tk.full * 100)} % of ${site.tank_kwh} kWh` : undefined}>
        <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#3f8f9a] to-[#7cc3cb] transition-[height] duration-700" style={{ height: `${(tk?.full ?? 0) * 100}%` }} />
        <span className="relative text-[10.5px] font-semibold tabular-nums text-ink [text-shadow:0_0_3px_rgba(255,255,255,0.8)]">{tk ? `${Math.round(tk.full * 100)}%` : ""}</span>
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5">
          {/* the rack's colour: its parts in the job carry the same */}
          <span className="size-3 shrink-0 rounded-full ring-2 ring-white" style={{ background: n?.color ?? "#9a958a" }} />
          <span className="truncate text-[13.5px] font-semibold">{site.person ?? site.name}</span>
          <span title={KIND_NAME[site.kind] ?? site.kind} className="shrink-0 text-muted">
            <Icon size={12} />
          </span>
        </span>
        <span className="mt-0.5 block truncate text-[11.5px] text-muted">
          {off ? (
            "offline"
          ) : full ? (
            <span className="flex items-center gap-1 font-semibold text-[#2f6e75]">
              <Pause size={10} fill="currentColor" /> tank full · paused to {Math.round(TANK_RESUME * 100)} %
            </span>
          ) : (
            tk?.need
          )}
        </span>
      </span>
      {x && !off && (
        <span className="shrink-0 text-right leading-tight" title={`${on} of ${site.servers} servers running a customer's job`}>
          <span className={clsx("flex items-center justify-end gap-1 text-[14px] font-semibold tabular-nums", on > 0 ? "text-ink" : "text-faint")}>
            {on > 0 && <span className="size-1.5 animate-pulse rounded-full bg-rust" />}
            <span>
              {on}
              <span className="font-normal text-muted">/{site.servers}</span>
            </span>
          </span>
          <span className="text-[10.5px] text-muted">servers</span>
        </span>
      )}
    </button>
  );
}

/** Wall-clock time of an order, e.g. 09:04:12 */
const clock = (ms: number) => new Date(ms).toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

function Jobs({
  jobs,
  now,
  shown,
  onShow,
  actions,
}: {
  jobs: Job[];
  now: number;
  shown: number | null;
  onShow: (id: number) => void;
  actions: React.ReactNode;
}) {
  // in the order they came in: a new order joins the end of the queue
  const list = jobs;
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    box.current?.scrollTo({ top: box.current.scrollHeight, behavior: "smooth" });
  }, [list.length]);
  return (
    <div ref={box} className={clsx(PANEL, "pointer-events-auto min-h-0 shrink overflow-auto px-3 pb-3 scroll-thin")}>
      <div className="sticky top-0 z-10 -mx-3 mb-1 flex items-center gap-1.5 bg-cream/95 px-3 pb-1.5 pt-2.5 backdrop-blur">
        <span className="px-1 text-[11.5px] font-semibold uppercase tracking-[0.12em] text-muted">Jobs</span>
        <span className="ml-auto" />
        {actions}
      </div>
      {list.length === 0 && <div className="px-1 py-1 text-[13px] text-muted">No orders yet</div>}
      <div className="space-y-2">
        {list.map((j) => {
          const done = j.tiles.filter((t) => t.state === "done").length;
          const running = j.tiles.filter((t) => t.state === "running").length;
          return (
            <div
              key={j.id}
              role="button"
              tabIndex={0}
              onClick={() => onShow(j.id)}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onShow(j.id)}
              title="Show this job below"
              className={clsx("cursor-pointer rounded-xl px-1.5 py-1", j.id === shown ? "bg-paper ring-1 ring-line" : "hover:bg-paper/60")}
            >
              <div className="flex items-baseline gap-2">
                <span className="truncate text-[14px] font-semibold">{PRODUCTS[j.kind].label}</span>
                <span className="shrink-0 text-[11.5px] tabular-nums text-muted">{clock(j.createdAt)}</span>
                <span
                  className={clsx(
                    "ml-auto shrink-0 rounded px-1.5 py-[1px] text-[11px] font-semibold",
                    j.doneAt ? "bg-ink/10" : running ? "bg-rust text-cream" : "bg-paper text-muted ring-1 ring-line",
                  )}
                >
                  {j.doneAt ? `Done · ${jobSeconds(j, now).toFixed(0)} s` : running ? `Running on ${running}` : "Queued"}
                </span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-paper ring-1 ring-line">
                <div className="h-full bg-rust transition-[width] duration-500" style={{ width: `${(100 * done) / j.tiles.length}%` }} />
              </div>
              {!j.doneAt && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    post({ op: "cancel", jobId: j.id });
                  }} className="mt-0.5 flex items-center gap-1 text-[11px] text-faint hover:text-ink">
                  <X size={11} /> cancel
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function QR({ url, size }: { url: string; size: number }) {
  const [svg, setSvg] = useState("");
  useEffect(() => {
    if (!url || url.startsWith("/")) return;
    QRCode.toString(url, { type: "svg", margin: 1, errorCorrectionLevel: "M", color: { dark: "#141412ff", light: "#fbfaf6ff" } })
      .then(setSvg)
      .catch(() => {});
  }, [url]);
  return <div className="shrink-0 overflow-hidden rounded-xl bg-card ring-1 ring-line [&>svg]:size-full" style={{ width: size, height: size }} dangerouslySetInnerHTML={{ __html: svg }} />;
}
