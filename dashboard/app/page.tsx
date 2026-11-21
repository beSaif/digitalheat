"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import clsx from "clsx";
import { Map as MapIcon, Pause, Play, RotateCcw, Terminal, TrendingDown, TrendingUp } from "lucide-react";
import { useFleet, useJobsAround, liveQueue } from "@/lib/store";
import {
  DEFAULT_T,
  H,
  dayLetter,
  fleetNow,
  fmtDate,
  fmtDay,
  fmtTime,
  jobProgress,
  nf,
  siteNow,
  type Fleet,
  type Job,
} from "@/lib/data";
import { ArrowBadge, Card, CardTitle, Chip, JobIcon, Loading, STATE_LABEL, Unit } from "@/components/ui";

export default function Overview() {
  const { fleet, t } = useFleet();
  const jobs = useJobsAround(t);
  if (!fleet) return <Loading />;
  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <Header fleet={fleet} />
      <Kpis fleet={fleet} t={t} jobs={jobs} />
      <div className="mt-4 grid grid-cols-12 gap-4">
        <HeatWeek fleet={fleet} t={t} className="col-span-12 xl:col-span-6" />
        <LatestDecision fleet={fleet} t={t} jobs={jobs} className="col-span-6 xl:col-span-3" />
        <DueNext fleet={fleet} t={t} jobs={jobs} className="col-span-6 xl:col-span-3 xl:row-span-1" />
        <SitesNow fleet={fleet} t={t} jobs={jobs} className="col-span-12 xl:col-span-5" />
        <Coverage fleet={fleet} t={t} className="col-span-6 xl:col-span-4" />
        <YearReplay fleet={fleet} className="col-span-6 xl:col-span-3" />
      </div>
    </div>
  );
}

function Header({ fleet }: { fleet: Fleet }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-[40px] font-semibold leading-none">Fleet overview</h1>
        <p className="mt-2.5 text-[15px] text-muted">
          {fleet.totals.sites} houses · {fleet.totals.servers} servers · 10 Swiss cities. Servers run only when a house can
          use the heat.
        </p>
      </div>
      <div className="flex gap-3">
        <Link
          href="/map"
          className="flex items-center gap-2 rounded-full bg-ink px-5 py-3 text-[15px] font-semibold text-cream hover:bg-ink-2"
        >
          <MapIcon size={18} /> Open fleet map
        </Link>
        <button
          onClick={() => {
            navigator.clipboard?.writeText("python3 scripts/build_fleet_scenario.py");
            setCopied(true);
            setTimeout(() => setCopied(false), 1600);
          }}
          className="flex items-center gap-2 rounded-full px-5 py-3 text-[15px] font-semibold ring-[1.5px] ring-ink hover:bg-card"
        >
          <Terminal size={17} /> {copied ? "Command copied" : "Reproduce run"}
        </button>
      </div>
    </div>
  );
}

function Delta({ v, unit = "", invert = false, dark = false }: { v: number; unit?: string; invert?: boolean; dark?: boolean }) {
  const up = v > 0;
  const good = invert ? !up : up;
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-semibold ring-1",
        dark ? "text-amber ring-amber/50" : good ? "text-ink ring-ink/30" : "text-rust ring-rust/40",
      )}
    >
      {v === 0 ? "±0" : `${up ? "+" : "−"}${nf(Math.abs(v), unit === "kWh" ? 1 : 0)}`}
      {up ? <TrendingUp size={12} /> : v < 0 ? <TrendingDown size={12} /> : null}
    </span>
  );
}

function Kpis({ fleet, t, jobs }: { fleet: Fleet; t: number; jobs: Job[] | null }) {
  const now = fleetNow(fleet, t);
  const prev = fleetNow(fleet, Math.max(0, t - 1));
  const q = jobs ? liveQueue(jobs, t) : null;
  const qPrev = jobs ? liveQueue(jobs, t - 1) : null;
  const qHours = q ? q.reduce((s, j) => s + fleet.meta.job_types[j.type].units / 2 * (1 - jobProgress(fleet, j, t)), 0) : 0;
  const dayStart = Math.floor(t / 24) * 24;
  const refusedToday = jobs ? jobs.filter((j) => (j.status === 1 || j.status === 2) && j.arrive >= dayStart && j.arrive <= t).length : null;
  const refusedYday = jobs
    ? jobs.filter((j) => (j.status === 1 || j.status === 2) && j.arrive >= dayStart - 24 && j.arrive <= t - 24).length
    : 0;
  const cover = now.demand ? now.served / now.demand : 0;

  return (
    <div className="mt-6 grid grid-cols-2 gap-4 xl:grid-cols-4">
      <div className="grain relative overflow-hidden rounded-[24px] p-5 text-cream">
        <div className="flex items-center justify-between">
          <h3 className="text-[17px] font-semibold">Servers running</h3>
          <ArrowBadge dark />
        </div>
        <div className="mt-3 font-display text-[52px] font-semibold leading-none text-amber">
          {now.running}
          <span className="text-[24px] text-cream/50"> / {now.servers}</span>
        </div>
        <div className="mt-4 flex items-center gap-2 text-[12.5px] text-cream/75">
          <Delta v={now.running - prev.running} dark /> heat permit allows {now.permit}
        </div>
      </div>

      <Card>
        <CardTitle right={<ArrowBadge />}>Heat delivered</CardTitle>
        <div className="mt-3 font-display text-[52px] font-semibold leading-none">
          {nf(now.served, 1)}
          <Unit>kWh</Unit>
        </div>
        <div className="mt-4 flex items-center gap-2 text-[12.5px] text-muted">
          <Delta v={now.served - prev.served} unit="kWh" /> this hour · {Math.round(cover * 100)}% of {nf(now.demand)} kWh demand
        </div>
      </Card>

      <Card>
        <CardTitle right={<ArrowBadge />}>Job queue</CardTitle>
        <div className="mt-3 font-display text-[52px] font-semibold leading-none">
          {q ? nf(q.length) : "…"}
          <Unit>jobs</Unit>
        </div>
        <div className="mt-4 flex items-center gap-2 text-[12.5px] text-muted">
          {q && qPrev && <Delta v={q.length - qPrev.length} />} {nf(qHours)} server-h left · 0 missed
        </div>
      </Card>

      <Card>
        <CardTitle right={<ArrowBadge />}>Refused today</CardTitle>
        <div className="mt-3 font-display text-[52px] font-semibold leading-none">
          {refusedToday ?? "…"}
          <Unit>jobs</Unit>
        </div>
        <div className="mt-4 flex items-center gap-2 text-[12.5px] text-muted">
          <Delta v={(refusedToday ?? 0) - refusedYday} invert /> not enough heat before due
        </div>
      </Card>
    </div>
  );
}

function HeatWeek({ fleet, t, className }: { fleet: Fleet; t: number; className?: string }) {
  const today = Math.floor(t / 24);
  const days = Array.from({ length: 7 }, (_, i) => today - 3 + i).filter((d) => d >= 0 && d < 365);
  const data = days.map((d) => {
    let demand = 0,
      served = 0,
      demandSoFar = 0;
    const end = d === today ? t + 1 : (d + 1) * 24;
    for (let i = 0; i < fleet.sites.length; i++) {
      const h = fleet.hourly[i];
      for (let x = d * 24; x < (d + 1) * 24; x++) demand += h.demand[x];
      for (let x = d * 24; x < end; x++) {
        served += h.served[x];
        demandSoFar += h.demand[x];
      }
    }
    // share covered so far; for today the bar fills only the hours already played
    return { d, demand: demand / 10, served: served / 10, share: demandSoFar ? served / demandSoFar : 0, played: (end - d * 24) / 24 };
  });
  const max = Math.max(...data.map((x) => x.demand)) * 1.05;
  return (
    <Card className={className}>
      <CardTitle
        right={
          <div className="flex items-center gap-4 text-[12px] text-muted">
            <span className="flex items-center gap-1.5">
              <i className="size-2.5 rounded-full bg-rust" /> Server heat
            </span>
            <span className="flex items-center gap-1.5">
              <i className="hatch size-2.5 rounded-full bg-paper ring-1 ring-line" /> Backup heater / ahead
            </span>
          </div>
        }
      >
        Heat this week
      </CardTitle>
      <div className="mt-5 flex h-[196px] items-end justify-between gap-3 px-2">
        {data.map((x) => {
          const hDemand = (x.demand / max) * 170;
          const share = x.share;
          const future = x.d > today;
          const isToday = x.d === today;
          return (
            <div key={x.d} className="group relative flex flex-1 flex-col items-center gap-2">
              {isToday && (
                <div className="absolute -top-1 z-10 rounded-md bg-card px-1.5 py-0.5 text-[10px] font-semibold ring-1 ring-line"
                  style={{ bottom: hDemand + 30 }}>
                  {Math.round(share * 100)}%
                </div>
              )}
              <div
                className={clsx("relative w-full max-w-[58px] overflow-hidden rounded-full", future ? "hatch bg-paper ring-1 ring-line" : "hatch bg-paper")}
                style={{ height: Math.max(18, hDemand) }}
                title={`${fmtDay(x.d * 24)}: ${nf(x.served)} of ${nf(x.demand)} kWh from servers`}
              >
                {!future && (
                  <div
                    className={clsx("absolute inset-x-0 bottom-0 rounded-full", isToday ? "bg-amber" : x.d === today - 1 ? "bg-rust-deep" : "bg-rust")}
                    style={{ height: `${Math.min(1, share) * x.played * 100}%` }}
                  />
                )}
              </div>
              <div className={clsx("text-[12px]", isToday ? "font-semibold text-ink" : "text-muted")}>{dayLetter(x.d)}</div>
            </div>
          );
        })}
      </div>
      <div className="mt-2 text-[12px] text-faint">
        Fleet heat demand per day. Today counts up to {fmtTime(t)}, and the days ahead show the forecast demand.
      </div>
    </Card>
  );
}

const REASON = ["", "not enough heat before due", "would push an admitted job late"];

function LatestDecision({ fleet, t, jobs, className }: { fleet: Fleet; t: number; jobs: Job[] | null; className?: string }) {
  const latest = useMemo(() => {
    if (!jobs) return null;
    let best: Job | null = null;
    for (const j of jobs) if ((j.status === 1 || j.status === 2) && j.arrive <= t && (!best || j.arrive >= best.arrive)) best = j;
    return best;
  }, [jobs, t]);
  const { setT } = useFleet();
  if (!latest) {
    const today = Math.floor(t / 24);
    let last = -1;
    for (let d = today - 1; d >= 0; d--)
      if (fleet.daily_jobs.refused[d] > 0) {
        last = d;
        break;
      }
    return (
      <Card className={clsx("flex flex-col", className)}>
        <CardTitle>Latest refusal</CardTitle>
        <div className="mt-4 font-display text-[24px] font-semibold leading-[1.15]">Nothing refused this week</div>
        <div className="mt-2 text-[13.5px] leading-snug text-muted">
          {jobs ? "Every house can take all the heat its servers make, so all offered work fits before its deadline." : "Loading…"}
          {last >= 0 && ` Last refusals: ${fmtDay(last * 24)}, ${nf(fleet.daily_jobs.refused[last])} jobs.`}
        </div>
        {last >= 0 && (
          <button
            onClick={() => setT(last * 24 + 12)}
            className="mt-auto flex items-center justify-center gap-2 rounded-full bg-ink py-3 text-[14px] font-semibold text-cream hover:bg-ink-2"
          >
            Jump to {fmtDay(last * 24)}
          </button>
        )}
      </Card>
    );
  }
  const jt = fleet.meta.job_types[latest.type];
  const site = fleet.sites[latest.site];
  return (
    <Card className={clsx("flex flex-col", className)}>
      <CardTitle>Latest refusal</CardTitle>
      <div className="mt-4 font-display text-[24px] font-semibold leading-[1.15] text-rust-deep">
        {jt.id} {jt.name} for {site.id}
      </div>
      <div className="mt-2 text-[13.5px] leading-snug text-muted">
        {fmtDay(latest.arrive)}, {fmtTime(latest.arrive)} · needs {nf(jt.units / 2, 1)} server-h before due, only{" "}
        {nf(latest.free / 2, 1)} free. Reason: {REASON[latest.status]}.
      </div>
      <Link
        href={`/sites/${site.id}`}
        className="mt-auto flex items-center justify-center gap-2 rounded-full bg-ink py-3 text-[14px] font-semibold text-cream hover:bg-ink-2"
      >
        Open {site.id} · {site.city}
      </Link>
    </Card>
  );
}

function DueNext({ fleet, t, jobs, className }: { fleet: Fleet; t: number; jobs: Job[] | null; className?: string }) {
  const [type, setType] = useState<number | null>(null);
  const list = useMemo(() => {
    if (!jobs) return [];
    return liveQueue(jobs, t)
      .filter((j) => type === null || j.type === type)
      .sort((a, b) => a.arrive + fleet.meta.job_types[a.type].due_h - (b.arrive + fleet.meta.job_types[b.type].due_h))
      .slice(0, 5);
  }, [jobs, t, type, fleet]);
  return (
    <Card className={className}>
      <CardTitle
        right={
          <button
            onClick={() => setType(type === null ? 1 : type === 1 ? 0 : null)}
            className="rounded-full px-3 py-1 text-[12.5px] font-medium ring-1 ring-ink/70 hover:bg-paper"
          >
            {type === null ? "All types" : fleet.meta.job_types[type].id}
          </button>
        }
      >
        Due next
      </CardTitle>
      <div className="mt-3 flex flex-col gap-3">
        {list.map((j) => {
          const jt = fleet.meta.job_types[j.type];
          const due = j.arrive + jt.due_h;
          const p = jobProgress(fleet, j, t);
          return (
            <Link key={j.id} href={`/sites/${fleet.sites[j.site].id}`} className="flex items-center gap-3 rounded-xl hover:bg-paper/50">
              <JobIcon type={j.type} />
              <div className="min-w-0 flex-1">
                <div className="truncate text-[14px] font-medium">
                  {jt.name} · {fleet.sites[j.site].id}
                </div>
                <div className="text-[11.5px] text-faint">
                  due in {due - t} h · {p > 0 ? `${Math.round(p * 100)}% done` : "queued"}
                </div>
              </div>
            </Link>
          );
        })}
        {!jobs && <div className="text-[13px] text-muted">Loading queue…</div>}
      </div>
    </Card>
  );
}

function SitesNow({ fleet, t, jobs, className }: { fleet: Fleet; t: number; jobs: Job[] | null; className?: string }) {
  const rows = useMemo(() => {
    const r = fleet.sites.map((_, i) => siteNow(fleet, i, t));
    const order = { throttled: 0, running: 1, "idle-work": 2, "idle-heat": 3 };
    return r.sort((a, b) => order[a.state] - order[b.state] || b.running - a.running);
  }, [fleet, t]);
  const mainJob = (si: number) => {
    if (!jobs) return null;
    const q = liveQueue(jobs, t).filter((j) => j.site === si && j.start >= 0 && j.start <= t);
    if (!q.length) return null;
    const j2 = q.filter((j) => j.type === 1).length;
    return j2 >= q.length / 2 ? 1 : 0;
  };
  return (
    <Card className={className}>
      <CardTitle
        right={
          <Link href="/map" className="rounded-full px-3 py-1 text-[12.5px] font-medium ring-1 ring-ink/70 hover:bg-paper">
            All sites on map
          </Link>
        }
      >
        Sites right now
      </CardTitle>
      <div className="mt-3 max-h-[262px] overflow-auto pr-1 scroll-thin">
        {rows.map((r) => {
          const si = fleet.sites.indexOf(r.site);
          const mj = mainJob(si);
          const st = STATE_LABEL[r.state];
          return (
            <Link
              key={r.site.id}
              href={`/sites/${r.site.id}`}
              className="flex items-center gap-3 border-b border-line/60 py-2.5 last:border-0 hover:bg-paper/40"
            >
              <span
                className={clsx(
                  "grid size-10 shrink-0 place-items-center rounded-full font-display text-[12px] font-semibold",
                  r.running ? "bg-ink text-amber" : "bg-paper text-muted ring-1 ring-line",
                )}
              >
                {r.site.id.slice(0, 2)}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-[14.5px] font-medium">
                  {r.site.id} · {r.site.city} {r.site.district}
                </div>
                <div className="truncate text-[12px] text-faint">
                  {r.running > 0 ? (
                    <>
                      {r.running} of {r.site.servers} servers on{" "}
                      <b className="font-medium text-ink-2">{mj === null ? "queued work" : fleet.meta.job_types[mj].name}</b>
                    </>
                  ) : r.state === "idle-heat" ? (
                    "House needs no heat and the tank is full"
                  ) : (
                    `Heat for ${r.permit} servers, no admitted work`
                  )}
                </div>
              </div>
              <Chip tone={st.tone}>{st.label}</Chip>
            </Link>
          );
        })}
      </div>
    </Card>
  );
}

function Coverage({ fleet, t, className }: { fleet: Fleet; t: number; className?: string }) {
  const { served, demand } = useMemo(() => {
    let s = 0,
      d = 0;
    for (const h of fleet.hourly) {
      for (let x = 0; x <= t; x++) {
        s += h.served[x];
        d += h.demand[x];
      }
    }
    return { served: s / 10, demand: d / 10 };
  }, [fleet, t]);
  const share = served / demand;
  // semicircle gauge
  const R = 92,
    W = 26,
    cx = 130,
    cy = 120;
  const arc = (a0: number, a1: number) => {
    const p = (a: number) => [cx + R * Math.cos(Math.PI * (1 - a)), cy - R * Math.sin(Math.PI * (1 - a))];
    const [x0, y0] = p(a0);
    const [x1, y1] = p(a1);
    return `M${x0},${y0} A${R},${R} 0 0 1 ${x1},${y1}`;
  };
  return (
    <Card className={className}>
      <CardTitle>Heat covered, year to date</CardTitle>
      <svg viewBox="0 0 260 140" className="mx-auto mt-2 w-full max-w-[300px]">
        <defs>
          <pattern id="hatchG" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="7" height="7" fill="#efebe2" />
            <line x1="0" y1="0" x2="0" y2="7" stroke="#141412" strokeOpacity="0.35" strokeWidth="2.5" />
          </pattern>
        </defs>
        <path d={arc(0, 1)} stroke="url(#hatchG)" strokeWidth={W} fill="none" strokeLinecap="round" />
        <path d={arc(0, share)} stroke="#c0653a" strokeWidth={W} fill="none" strokeLinecap="round" />
        <text x={cx} y={cy - 12} textAnchor="middle" className="font-display" fontSize="44" fontWeight="600" fill="#141412">
          {Math.round(share * 100)}%
        </text>
        <text x={cx} y={cy + 10} textAnchor="middle" fontSize="12" fill="#6b675e">
          from server heat
        </text>
      </svg>
      <div className="mt-1 flex justify-center gap-5 text-[12.5px] text-muted">
        <span className="flex items-center gap-1.5">
          <i className="size-3 rounded-full bg-rust" /> Servers {nf(served / 1000)} MWh
        </span>
        <span className="flex items-center gap-1.5">
          <i className="hatch size-3 rounded-full bg-paper ring-1 ring-line" /> Backup {nf((demand - served) / 1000)} MWh
        </span>
      </div>
      <div className="mt-2 text-center text-[12px] text-faint">0 kWh dumped · 0 deadlines missed</div>
    </Card>
  );
}

function YearReplay({ fleet, className }: { fleet: Fleet; className?: string }) {
  const { t, setT, playing, setPlaying } = useFleet();
  const daily = useMemo(() => {
    const out = new Array(365).fill(0);
    for (const h of fleet.hourly) for (let x = 0; x < H; x++) out[Math.floor(x / 24)] += h.demand[x];
    const m = Math.max(...out);
    return out.map((v) => v / m);
  }, [fleet]);
  const day = Math.floor(t / 24);
  return (
    <div className={clsx("grain relative flex flex-col overflow-hidden rounded-[24px] p-5 text-cream", className)}>
      <h3 className="text-[17px] font-semibold">Year replay</h3>
      <div className="mt-3 font-display text-[52px] font-semibold leading-none tabular-nums">{fmtTime(t)}</div>
      <div className="mt-1 text-[13px] text-cream/60">{fmtDate(t, true)}</div>
      {/* 365 days of fleet heat demand: click to jump */}
      <div
        className="relative mt-4 flex h-[56px] cursor-pointer items-end gap-px"
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          setT(Math.floor(((e.clientX - r.left) / r.width) * 365) * 24 + (t % 24));
        }}
        title="Fleet heat demand per day, 2025. Click to jump."
      >
        {daily.map((v, i) => (
          <div key={i} className="flex-1 rounded-t-[1px]" style={{ height: `${8 + v * 92}%`, background: i === day ? "#f6f3ec" : i < day ? "#c0653a" : "rgba(242,166,90,0.35)" }} />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-cream/45">
        <span>Jan</span>
        <span>Apr</span>
        <span>Jul</span>
        <span>Oct</span>
        <span>Dec</span>
      </div>
      <div className="mt-auto flex items-center justify-center gap-3 pt-4">
        <button
          onClick={() => setPlaying(!playing)}
          aria-label={playing ? "Pause replay" : "Play replay"}
          className="grid size-12 place-items-center rounded-full bg-cream text-ink hover:bg-amber"
        >
          {playing ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" />}
        </button>
        <button
          onClick={() => {
            setPlaying(false);
            setT(DEFAULT_T);
          }}
          aria-label="Back to 21 Nov"
          className="grid size-12 place-items-center rounded-full bg-rust text-cream hover:bg-rust-deep"
        >
          <RotateCcw size={19} />
        </button>
      </div>
    </div>
  );
}
