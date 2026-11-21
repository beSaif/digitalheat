"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import clsx from "clsx";
import Link from "next/link";
import { ArrowRight, MapPinPlus, Pause, Play, RotateCcw, Snowflake, Square, Sun } from "lucide-react";
import { useFleet } from "@/lib/store";
import { fmtDate, fmtDay, fmtTime, hourDate } from "@/lib/data";
import { DEFAULT_SITES, KIND_LABEL, KIND_SERVERS, plainSite, useSavedSites, useSchedule, type Kind, type Schedule, type SiteIn } from "@/lib/schedule";
import { Card, Loading, PayChip } from "@/components/ui";

const SitesMap = dynamic(() => import("@/components/SitesMap").then((m) => m.SitesMap), { ssr: false });

const WINTER_T = 14 * 24 + 6; // 15 Jan, 06:00
const SUMMER_T = 195 * 24 + 6; // 15 Jul, 06:00

export default function Overview() {
  const { t, setT, playing, setPlaying, speed, year } = useFleet();
  const [sites, save] = useSavedSites();
  const [selected, setSelected] = useState(1);
  const [adding, setAdding] = useState(false);

  const { data, loading, error } = useSchedule(sites, year);
  const base = useSchedule(DEFAULT_SITES, year).data;
  if (!data && !error) return <Loading />;

  const setServers = (i: number, n: number) => save(sites.map((s, j) => (j === i ? { ...s, servers: Math.max(0, Math.min(40, n)) } : s)));
  const addSite = (kind: Kind, lat: number, lon: number) => {
    const k = sites.filter((s) => s.added).length + 1;
    save([...sites, { id: `NEW-${k}`, kind, name: `${KIND_LABEL[kind]} ${k}`, lat: +lat.toFixed(4), lon: +lon.toFixed(4), servers: KIND_SERVERS[kind], added: true }]);
    setAdding(false);
    setSelected(sites.length);
  };
  const removeSite = (i: number) => {
    save(sites.filter((_, j) => j !== i));
    setSelected(1);
  };
  const changed = JSON.stringify(sites) !== JSON.stringify(DEFAULT_SITES);
  const month = hourDate(t).getUTCMonth();
  const winter = month < 3 || month > 9;
  const go = (to: number) => {
    setT(to);
    setPlaying(true);
  };
  const S = data && data.sites.length === sites.length ? data : null;
  const sel = Math.min(selected, sites.length - 1);

  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <h1 className="font-display text-[40px] font-semibold leading-none">Fleet overview</h1>
      {error && <div className="mt-3 rounded-xl bg-amber-soft px-4 py-2 text-[13px] text-rust-deep">Scheduler error: {error}</div>}

      {S && (
        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1fr_1.6fr]">
          <ServersCard s={S} t={t} />
          <PriceCard s={S} base={base} changed={changed} reset={() => save(DEFAULT_SITES)} />
          <JobsCard s={S} t={t} />
        </div>
      )}

      <Card className="mt-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="text-[15px] font-semibold">
            {fmtDate(t)} · {fmtTime(t)}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAdding(!adding)}
              className={clsx(
                "flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-semibold ring-1",
                adding ? "bg-rust text-cream ring-rust" : "ring-ink/30 hover:bg-paper",
              )}
            >
              <MapPinPlus size={15} /> {adding ? "Cancel" : "Add site"}
            </button>
            <Season active={winter} onClick={() => go(WINTER_T)} icon={<Snowflake size={15} />}>
              Winter
            </Season>
            <Season active={!winter} onClick={() => go(SUMMER_T)} icon={<Sun size={15} />}>
              Summer
            </Season>
            <button
              onClick={() => setPlaying(!playing)}
              aria-label={playing ? "Pause" : "Play"}
              className="grid size-10 place-items-center rounded-full bg-ink text-cream hover:bg-ink-2"
            >
              {playing ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
            </button>
          </div>
        </div>
        <SitesMap
          sites={sites}
          schedule={S}
          t={t}
          dur={Math.min(1100, (1000 / speed) * 0.9)}
          selected={sel}
          setSelected={setSelected}
          setServers={setServers}
          adding={adding}
          onAdd={addSite}
          onRemove={removeSite}
          busy={loading}
        />
      </Card>

      {S && (
        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[1.4fr_1fr]">
          <Steps s={S} i={sel} t={t} />
          <RealJob sites={sites} site={sites[sel]} t={t} year={year} />
        </div>
      )}
    </div>
  );
}

function Season({ active, onClick, icon, children }: { active: boolean; onClick: () => void; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={clsx("flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-semibold ring-1", active ? "bg-ink text-cream ring-ink" : "ring-ink/30 hover:bg-paper")}
    >
      {icon} {children}
    </button>
  );
}

/* ---------- cards ---------- */

function ServersCard({ s, t }: { s: Schedule; t: number }) {
  const total = s.sites.reduce((a, x) => a + x.servers, 0);
  const run = s.series.reduce((a, x) => a + x.running[t], 0);
  return (
    <div className="grain flex items-center gap-6 rounded-[24px] p-5 text-cream">
      <div>
        <h3 className="text-[17px] font-semibold">Servers running</h3>
        <div className="mt-3 font-display text-[52px] font-semibold leading-none text-amber">
          {run}
          <span className="text-[24px] text-cream/50"> / {total}</span>
        </div>
      </div>
      <div className="ml-auto flex flex-col gap-1.5">
        {s.sites.map((x, i) => (
          <div key={x.id} className="flex gap-[2px]">
            {Array.from({ length: x.servers }, (_, k) => (
              <i key={k} className={clsx("h-2.5 w-[5px] rounded-[1px]", k < s.series[i].running[t] ? "bg-teal" : "bg-white/15")} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function PriceCard({ s, base, changed, reset }: { s: Schedule; base: Schedule | null; changed: boolean; reset: () => void }) {
  const p = s.fleet.price_chf_per_server_h ?? 0;
  const m = s.fleet.money;
  const d = base?.fleet.price_chf_per_server_h != null ? p - base.fleet.price_chf_per_server_h : 0;
  return (
    <Card>
      <h3 className="text-[17px] font-semibold">Estimated price of compute</h3>
      <div key={p.toFixed(4)} className="mt-3 animate-[pop_0.5s_ease-out] whitespace-nowrap font-display text-[44px] font-semibold leading-none">
        CHF {p.toFixed(2)}
        <span className="ml-1 text-[16px] font-medium text-muted">/ server-h</span>
      </div>
      <Link href="/money" className="mt-3 flex items-center gap-2 text-[13px] text-muted hover:text-ink">
        {m && <PayChip ok={m.pays_off} />}
        AWS CHF {s.constants.aws_spot_chf_h.toFixed(2)}
        <ArrowRight size={13} />
      </Link>
      {changed && (
        <button onClick={reset} className="mt-3 flex items-center gap-1.5 text-[13px] text-muted hover:text-ink">
          <span className={clsx("font-semibold", d > 0 ? "text-rust" : "text-[#2f6e75]")}>
            {d >= 0 ? "+" : "−"}
            {Math.abs(d * 100).toFixed(1)} Rp
          </span>
          <RotateCcw size={13} /> reset
        </button>
      )}
    </Card>
  );
}

function Gauge({ value, max, color }: { value: number; max: number; color: string }) {
  const R = 40;
  const v = max ? Math.min(1, value / max) : 0;
  const pt = (a: number) => `${50 + R * Math.cos(Math.PI * (1 - a))},${48 - R * Math.sin(Math.PI * (1 - a))}`;
  return (
    <svg viewBox="0 0 100 54" className="w-[100px] shrink-0">
      <path d={`M${pt(0)} A${R},${R} 0 0 1 ${pt(1)}`} stroke="#e8e4da" strokeWidth={10} fill="none" strokeLinecap="round" />
      {v > 0 && <path d={`M${pt(0)} A${R},${R} 0 0 1 ${pt(v)}`} stroke={color} strokeWidth={10} fill="none" strokeLinecap="round" />}
      <text x={50} y={46} textAnchor="middle" fontSize="15" fontWeight="600" fill="#141412">
        {value.toFixed(0)} kW
      </text>
    </svg>
  );
}

function JobsCard({ s, t }: { s: Schedule; t: number }) {
  const total = s.sites.reduce((a, x) => a + x.servers, 0);
  const rr = s.series.reduce((a, x) => a + x.rerank_sh[t], 0);
  const em = s.series.reduce((a, x) => a + x.embed_sh[t], 0);
  const open = s.deadline_jobs.filter((j) => j[2] <= t && j[6] > t).sort((a, b) => a[3] - b[3]);
  const cur = open[0];
  const embedDue = t + s.job_types.embed.due_h;
  const rows = [
    { name: "Embed", kw: em, color: "#5fa8b0", job: `#${s.embed_ids[t]}`, due: `${fmtDay(embedDue)}, ${fmtTime(embedDue)}` },
    { name: "Rerank", kw: rr, color: "#f2a65a", job: cur ? `#${cur[0]}` : "–", due: cur ? fmtTime(cur[3]) : "–" },
  ];
  return (
    <Card>
      <h3 className="text-[17px] font-semibold">Job types</h3>
      <div className="mt-2 grid grid-cols-2 gap-4">
        {rows.map((r) => (
          <div key={r.name} className="flex items-center gap-3">
            <Gauge value={r.kw} max={total} color={r.color} />
            <div className="text-[13px] leading-relaxed">
              <div className="text-[15px] font-semibold">{r.name}</div>
              <div className="text-muted">
                Job <b className="text-ink">{r.job}</b>
              </div>
              <div className="text-muted">
                Due <b className="text-ink">{r.due}</b>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ---------- the scheduler's calculation for one site and hour ---------- */

const f1 = (v: number) => v.toFixed(1);

function Steps({ s, i, t }: { s: Schedule; i: number; t: number }) {
  const site = s.sites[i];
  const x = s.series[i];
  const C = site.tank_kwh;
  const N = site.servers;
  const d = x.demand[t];
  const soc0 = t > 0 ? x.soc[t - 1] : 0;
  const room = C - soc0;
  const U = x.reserve_u[t];
  const heat = 0.8 * x.running[t];
  const rr = s.deadline_jobs.filter((j) => j[4] === i && j[5] === t);
  const y = site.year;
  const rows: [string, React.ReactNode][] = [
    ["Heat signal", <>demand {f1(d)} kW · tank {f1(soc0)} of {C} kWh · room {f1(room)} kWh</>],
    ["Heat permit", <>min({N}, ⌊({f1(d)} + {f1(room)}) ÷ 0.8⌋) = <b>{x.permit[t]}</b> servers</>],
    ["Deadline reserve", <>tank ≤ {f1(U)} kWh after this hour → min({x.permit[t]}, ⌊({f1(U)} + {f1(d)} − {f1(soc0)}) ÷ 0.8⌋) = <b>{x.limit[t]}</b></>],
    [
      "Jobs",
      <>
        {rr.length
          ? rr.map((j) => (
              <span key={j[0]} className="mr-2">
                rerank #{j[0]}
                {j[1] !== i ? ` from ${s.sites[j[1]].name}` : ""} due {fmtTime(j[3])}
                {j[8] ? " (forced)" : ""}
              </span>
            ))
          : "no rerank · "}
        embed {x.embed_sh[t].toFixed(2)} server-h · {x.started[t]} started · {x.moved_in[t]} moved in
      </>,
    ],
    ["No heat", <>{x.paused[t]} paused (SIGSTOP) · {x.checkpointed[t]} checkpointed (SIGTERM) · {x.forced[t]} forced</>],
    ["Heat balance", <>0.8 × {x.running[t]} = {f1(heat)} kW · used {f1(x.served[t])} · tank {f1(soc0)} → {f1(x.soc[t])} kWh · dumped {f1(x.dumped[t])}</>],
  ];
  return (
    <Card>
      <h3 className="text-[17px] font-semibold">
        Scheduler · {site.name} · {fmtTime(t)}
      </h3>
      <ol className="mt-3 space-y-2">
        {rows.map(([k, v], n) => (
          <li key={k} className="flex gap-3 text-[13px]">
            <span className="grid size-6 shrink-0 place-items-center rounded-full bg-ink text-[11px] font-semibold text-cream">{n + 1}</span>
            <span className="w-[118px] shrink-0 pt-0.5 font-semibold">{k}</span>
            <span className="pt-0.5 font-mono text-[12.5px] text-ink-2">{v}</span>
          </li>
        ))}
      </ol>
      <div className="mt-4 grid grid-cols-5 gap-2 border-t border-line pt-3 text-center">
        {[
          [`${Math.round(y.coverage * 100)}%`, "heat covered"],
          [`${Math.round(y.dumped_kwh)} kWh`, "dumped"],
          [`${Math.round(y.utilisation * 100)}%`, "utilisation"],
          [`${y.missed_pct.toFixed(1)}%`, "missed"],
          [`${(y.break_even_chf_per_server_h ?? 0).toFixed(3)}`, "break-even CHF/h"],
        ].map(([v, k]) => (
          <div key={k}>
            <div className="font-display text-[18px] font-semibold">{v}</div>
            <div className="text-[11px] text-muted">{k}</div>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ---------- the real job ---------- */

type Live = {
  alive: boolean;
  state: string;
  site: { id: string; name: string };
  start_t: number;
  job: { state: string; items_done: number | null; rate: number | null };
  now?: { t: number; demand: number; soc: number; permit: number; running: number; server_runs: boolean; decision: string; reason: string };
  events: { t: number; text: string }[];
};

function RealJob({ sites, site, t, year }: { sites: SiteIn[]; site: SiteIn; t: number; year: number }) {
  const [live, setLive] = useState<Live | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const poll = () =>
    fetch("/api/realjob")
      .then((r) => r.json())
      .then(setLive)
      .catch(() => {});
  useEffect(() => {
    poll();
    const id = setInterval(poll, 1000);
    return () => clearInterval(id);
  }, []);
  const start = async () => {
    setErr(null);
    const r = await fetch("/api/realjob", {
      method: "POST",
      body: JSON.stringify({ op: "start", year, day: Math.floor(t / 24), hour: t % 24, site: site.id, sites: sites.map(plainSite) }),
    });
    if (!r.ok) setErr((await r.json()).error);
  };
  const stop = () => fetch("/api/realjob", { method: "POST", body: JSON.stringify({ op: "stop" }) });
  const running = live?.alive;
  const st = live?.job.state ?? "not started";
  return (
    <Card>
      <div className="flex items-center justify-between">
        <h3 className="text-[17px] font-semibold">Real job</h3>
        {running ? (
          <button onClick={stop} className="flex items-center gap-1.5 rounded-full bg-ink px-4 py-2 text-[13px] font-semibold text-cream">
            <Square size={13} fill="currentColor" /> Stop
          </button>
        ) : (
          <button onClick={start} className="flex items-center gap-1.5 rounded-full bg-rust px-4 py-2 text-[13px] font-semibold text-cream hover:bg-rust-deep">
            <Play size={13} fill="currentColor" /> Run on {site.name}
          </button>
        )}
      </div>
      {err && <div className="mt-2 text-[12px] text-rust">{err}</div>}
      {live ? (
        <>
          <div className="mt-3 flex items-center gap-3">
            <span
              className={clsx(
                "rounded-full px-3 py-1 text-[13px] font-semibold",
                st === "running" ? "bg-teal text-cream" : st === "paused" ? "bg-amber text-ink" : "bg-paper text-ink ring-1 ring-line",
              )}
            >
              {st}
            </span>
            <span className="text-[13px] text-muted">
              {live.site.name} · {live.now ? `${fmtDay(live.now.t)} ${fmtTime(live.now.t)}` : ""}
            </span>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="font-display text-[20px] font-semibold">{(live.job.items_done ?? 0).toLocaleString("de-CH")}</div>
              <div className="text-[11px] text-muted">abstracts embedded</div>
            </div>
            <div>
              <div className="font-display text-[20px] font-semibold">{live.now ? `${live.now.running}` : "–"}</div>
              <div className="text-[11px] text-muted">servers with heat</div>
            </div>
            <div>
              <div className="font-display text-[20px] font-semibold">{live.now ? f1(live.now.soc) : "–"}</div>
              <div className="text-[11px] text-muted">tank kWh</div>
            </div>
          </div>
          <ul className="mt-3 space-y-1 font-mono text-[12px] text-ink-2">
            {live.events
              .slice(-5)
              .reverse()
              .map((e, k) => (
                <li key={k}>
                  <span className="text-faint">{fmtTime(e.t)}</span> {e.text}
                </li>
              ))}
          </ul>
        </>
      ) : (
        <p className="mt-3 text-[13px] text-muted">Runs a real embedding job on this laptop. The scheduler pauses and resumes it on {site.name}&apos;s heat signal.</p>
      )}
    </Card>
  );
}
