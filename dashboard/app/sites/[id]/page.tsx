"use client";

import Link from "next/link";
import { use, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import clsx from "clsx";
import { ChevronDown, ChevronLeft, ChevronRight, Info, Thermometer, X } from "lucide-react";
import { useFleet, useJobsAround, useSiteSlots } from "@/lib/store";
import { H, cityTemp, fmtDay, fmtTime, jobProgress, nf, siteIndex, siteNow, type Fleet, type Job } from "@/lib/data";
import { Chip, JobIcon, Loading, STATE_LABEL } from "@/components/ui";
import { SiteMap3D } from "@/components/SiteMap3D";

type SlotState = { kind: "running" | "paused" | "ready" | "off"; job: Job | null; jobId: number };

export default function SitePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { fleet, t } = useFleet();
  const router = useRouter();
  if (!fleet) return <Loading />;
  const si = siteIndex(fleet, id);
  if (si < 0)
    return (
      <div className="grid h-full place-items-center text-muted">
        Unknown site {id}.{" "}
        <Link className="underline" href="/sites/BS-01">
          Open BS-01
        </Link>
      </div>
    );
  return (
    <div className="relative h-full overflow-hidden">
      <SiteMap3D fleet={fleet} si={si} t={t} padLeft={470} onSite={(x) => router.push(`/sites/${x}`)} />
      <SitePanel fleet={fleet} si={si} t={t} />
    </div>
  );
}

function SitePanel({ fleet, si, t }: { fleet: Fleet; si: number; t: number }) {
  const router = useRouter();
  const site = fleet.sites[si];
  const now = siteNow(fleet, si, t);
  const slots = useSiteSlots(site.id);
  const jobs = useJobsAround(t, si);
  const [sel, setSel] = useState<number | null>(null);
  const [showInfo, setShowInfo] = useState(false);

  const jobById = useMemo(() => {
    const m = new Map<number, Job>();
    jobs?.forEach((j) => m.set(j.id, j));
    return m;
  }, [jobs]);

  const slotStates: SlotState[] = useMemo(() => {
    const out: SlotState[] = [];
    if (!slots) return out;
    const row = slots[t] ?? [];
    const prev = t > 0 ? slots[t - 1] : [];
    let readyLeft = Math.max(0, now.permit - now.running);
    for (let k = 0; k < site.servers; k++) {
      const j = row[k] ?? -1;
      if (j >= 0) {
        out.push({ kind: "running", job: jobById.get(j) ?? null, jobId: j });
        continue;
      }
      const pj = prev[k] ?? -1;
      const pjob = pj >= 0 ? jobById.get(pj) : undefined;
      if (pjob && pjob.finish > t) out.push({ kind: "paused", job: pjob, jobId: pj });
      else if (readyLeft > 0) {
        readyLeft--;
        out.push({ kind: "ready", job: null, jobId: -1 });
      } else out.push({ kind: "off", job: null, jobId: -1 });
    }
    return out;
  }, [slots, t, jobById, site.servers, now.permit, now.running]);

  const siteIds = fleet.sites.map((s) => s.id);
  const go = (d: number) => router.push(`/sites/${siteIds[(si + d + siteIds.length) % siteIds.length]}`);
  const st = STATE_LABEL[now.state];

  return (
    <>
      <div className="absolute bottom-5 left-5 top-5 flex w-[440px] flex-col overflow-hidden rounded-[26px] bg-card/97 shadow-[0_24px_60px_-28px_rgba(50,30,10,0.55)] ring-1 ring-line backdrop-blur">
        <div className="overflow-auto p-6 scroll-thin">
          {/* header */}
          <div className="flex items-start justify-between">
            <div>
              <div className="text-[12px] uppercase tracking-[0.14em] text-rust">{site.reference ? "Reference house" : site.building}</div>
              <h1 className="mt-1 font-display text-[30px] font-semibold leading-none">
                {site.id} · {site.district}
              </h1>
              <div className="mt-2 text-[13px] text-muted">
                {site.city}, {site.canton} · {site.servers} servers · {site.tank_kwh} kWh tank
              </div>
            </div>
            <div className="flex gap-1.5">
              <button onClick={() => go(-1)} aria-label="Previous site" className="grid size-9 place-items-center rounded-full ring-1 ring-line hover:bg-paper">
                <ChevronLeft size={17} />
              </button>
              <button onClick={() => go(1)} aria-label="Next site" className="grid size-9 place-items-center rounded-full ring-1 ring-line hover:bg-paper">
                <ChevronRight size={17} />
              </button>
            </div>
          </div>

          <div className="mt-5 flex items-center gap-3 rounded-2xl bg-paper/70 p-3.5">
            <span className="grid size-10 place-items-center rounded-xl bg-card ring-1 ring-line">
              <Thermometer size={18} />
            </span>
            <div className="flex-1 text-[14px] leading-snug">
              <b className="font-semibold">
                {now.running} of {site.servers} servers on
              </b>{" "}
              <span className="text-muted">
                · {cityTemp(fleet, site.city, t).toFixed(1)}°C outside, house needs {now.demand.toFixed(1)} kWh this hour
              </span>
            </div>
            <Chip tone={st.tone}>{st.label.split(" ·")[0]}</Chip>
          </div>

          {/* rack */}
          <div className="mt-6 flex items-center justify-between">
            <h2 className="text-[16px] font-semibold">Servers</h2>
            <div className="flex items-center gap-3 text-[11px] text-muted">
              <Legend c="bg-amber" l="running" />
              <Legend c="bg-teal" l="paused" />
              <Legend c="bg-cream/40" l="ready" />
              <Legend c="bg-white/10" l="off" />
            </div>
          </div>
          {slots && jobs ? (
            <Rack states={slotStates} n={site.servers} sel={sel} setSel={setSel} fleet={fleet} />
          ) : (
            <div className="mt-3 grid place-items-center rounded-[18px] bg-[#141412] text-[12px] text-cream/50" style={{ height: site.servers * 44 + 14 }}>
              Reading the rack…
            </div>
          )}

          {/* tank + heat */}
          <div className="mt-6 grid grid-cols-[96px_1fr] gap-4">
            <Tank share={now.socShare} kwh={now.soc} cap={site.tank_kwh} />
            <div className="flex flex-col justify-center gap-3 text-[13px]">
              <Row k="Heat from servers" v={`${nf(now.heatKw, 1)} kW`} />
              <Row k="Delivered to house" v={`${nf(now.served, 1)} kWh`} />
              <Row k="Backup heater" v={`${nf(Math.max(0, now.demand - now.served), 1)} kWh`} />
              <Row k="Heat permit" v={`${now.permit} of ${site.servers} servers`} />
            </div>
          </div>

          {/* permit window */}
          <PermitWindow fleet={fleet} si={si} t={t} />

          {/* year */}
          <div className="mt-6 grid grid-cols-3 gap-2 border-t border-line pt-4 text-[12px]">
            <Stat v={`${Math.round(site.year.coverage * 100)}%`} k={`heat covered, ${fleet.meta.year}`} />
            <Stat v={`${Math.round(site.year.utilisation * 100)}%`} k="server utilisation" />
            <Stat v={nf(site.year.run_server_h)} k="server-h of work" />
          </div>
          <button onClick={() => setShowInfo(!showInfo)} className="mt-4 flex items-center gap-1.5 text-[12px] text-muted hover:text-ink">
            <Info size={13} /> How this site is modelled <ChevronDown size={13} className={clsx(showInfo && "rotate-180")} />
          </button>
          {showInfo && (
            <p className="mt-2 text-[12px] leading-relaxed text-muted">
              Reference house ×{site.scale.toFixed(2)} on {site.city}&apos;s {fleet.meta.year} hourly temperature.{" "}
              {site.reference ? "This is the case's reference house unchanged. " : ""}
              The building is the closest OpenStreetMap footprint to a representative address in {site.district}. It is not a real
              customer.
            </p>
          )}
        </div>
      </div>
      {sel !== null && slotStates[sel] && (
        <ServerCard fleet={fleet} site={si} k={sel} s={slotStates[sel]} t={t} slots={slots} onClose={() => setSel(null)} />
      )}
    </>
  );
}

function Legend({ c, l }: { c: string; l: string }) {
  return (
    <span className="flex items-center gap-1">
      <i className={clsx("size-2 rounded-full ring-1 ring-ink/20", c === "bg-cream/40" || c === "bg-white/10" ? "bg-line" : c)} />
      {l}
    </span>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between border-b border-dashed border-line pb-1.5">
      <span className="text-muted">{k}</span>
      <span className="font-semibold">{v}</span>
    </div>
  );
}

function Stat({ v, k }: { v: string; k: string }) {
  return (
    <div>
      <div className="font-display text-[20px] font-semibold">{v}</div>
      <div className="text-faint">{k}</div>
    </div>
  );
}

/** Front of the rack, one unit per server, like the case photo. */
function Rack({
  states,
  n,
  sel,
  setSel,
  fleet,
}: {
  states: SlotState[];
  n: number;
  sel: number | null;
  setSel: (k: number | null) => void;
  fleet: Fleet;
}) {
  return (
    <div className="mt-3 rounded-[18px] bg-[#141412] p-2.5 shadow-inner">
      <div className="flex flex-col gap-1.5">
        {Array.from({ length: n }, (_, k) => {
          const s = states[k];
          const kind = s?.kind ?? "off";
          const jt = s?.job ? fleet.meta.job_types[s.job.type] : null;
          return (
            <button
              key={k}
              onClick={() => setSel(sel === k ? null : k)}
              className={clsx(
                "group flex h-[38px] items-center gap-3 rounded-[10px] px-3 text-left transition",
                sel === k ? "bg-[#2e2c28] ring-2 ring-amber" : "bg-[#1f1e1b] hover:bg-[#2a2925]",
              )}
            >
              <span className="w-7 text-[11px] font-semibold text-cream/50">S{k + 1}</span>
              <span className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <i
                    key={i}
                    className={clsx(
                      "size-1.5 rounded-full",
                      kind === "running" && (i === 0 ? "bg-amber" : "bg-amber/60 animate-pulse"),
                      kind === "paused" && (i === 0 ? "bg-teal" : "bg-teal/30"),
                      kind === "ready" && (i === 0 ? "bg-cream/60" : "bg-cream/15"),
                      kind === "off" && "bg-white/10",
                    )}
                    style={kind === "running" ? { animationDelay: `${(k * 0.27 + i * 0.4) % 1.2}s` } : undefined}
                  />
                ))}
              </span>
              {/* vent grille */}
              <span className="flex flex-1 gap-[3px] opacity-25">
                {Array.from({ length: 14 }, (_, i) => (
                  <i key={i} className="h-3.5 w-[2px] rounded bg-cream" />
                ))}
              </span>
              <span className={clsx("w-[132px] truncate text-right text-[11.5px]", kind === "running" ? "text-amber" : kind === "paused" ? "text-teal" : "text-cream/40")}>
                {kind === "running" && (jt ? `${jt.id} ${jt.name}` : "running")}
                {kind === "paused" && "paused · checkpointed"}
                {kind === "ready" && "ready · no work"}
                {kind === "off" && "off · no heat permit"}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Tank({ share, kwh, cap }: { share: number; kwh: number; cap: number }) {
  return (
    <div className="flex flex-col items-center">
      <div className="relative h-[124px] w-[64px] overflow-hidden rounded-[22px] bg-paper ring-1 ring-line">
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-rust to-amber transition-[height] duration-500" style={{ height: `${Math.min(1, share) * 100}%` }} />
        <div className="absolute inset-0 grid place-items-center font-display text-[15px] font-semibold text-ink mix-blend-multiply">{Math.round(share * 100)}%</div>
      </div>
      <div className="mt-1.5 text-center text-[11px] leading-tight text-muted">
        Tank {nf(kwh, 1)}
        <br />
        of {cap} kWh
      </div>
    </div>
  );
}

function PermitWindow({ fleet, si, t }: { fleet: Fleet; si: number; t: number }) {
  const h = fleet.hourly[si];
  const n = fleet.sites[si].servers;
  const from = Math.max(0, t - 24),
    to = Math.min(H, t + 25);
  const hours = [];
  for (let x = from; x < to; x++) hours.push(x);
  return (
    <div className="mt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-[16px] font-semibold">Heat permit, ±24 h</h2>
        <div className="flex gap-3 text-[11px] text-muted">
          <span className="flex items-center gap-1">
            <i className="size-2 rounded-sm bg-rust" /> ran
          </span>
          <span className="flex items-center gap-1">
            <i className="hatch size-2 rounded-sm bg-paper ring-1 ring-line" /> allowed
          </span>
        </div>
      </div>
      <div className="mt-3 flex h-[70px] items-end gap-[2px]">
        {hours.map((x) => (
          <div key={x} className="relative flex-1" style={{ height: `${(h.permit[x] / n) * 100}%` }} title={`${fmtDay(x)} ${fmtTime(x)}: ${Math.ceil(h.run[x] / 2)} ran, ${h.permit[x]} allowed`}>
            <div className={clsx("hatch absolute inset-0 rounded-t-[2px] bg-paper", x === t && "ring-1 ring-ink")} />
            {x <= t && <div className={clsx("absolute inset-x-0 bottom-0 rounded-t-[2px]", x === t ? "bg-ink" : "bg-rust")} style={{ height: `${h.permit[x] ? (h.run[x] / 2 / h.permit[x]) * 100 : 0}%` }} />}
          </div>
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-faint">
        <span>−24 h</span>
        <span>now</span>
        <span>+24 h (forecast)</span>
      </div>
    </div>
  );
}

function ServerCard({
  fleet,
  site,
  k,
  s,
  t,
  slots,
  onClose,
}: {
  fleet: Fleet;
  site: number;
  k: number;
  s: SlotState;
  t: number;
  slots: number[][] | null;
  onClose: () => void;
}) {
  const sObj = fleet.sites[site];
  const jt = s.job ? fleet.meta.job_types[s.job.type] : null;
  const p = s.job ? jobProgress(fleet, s.job, t) : 0;
  const hist = useMemo(() => {
    if (!slots) return [];
    const out: number[] = [];
    for (let x = Math.max(0, t - 47); x <= t; x++) out.push(slots[x]?.[k] ?? -1);
    return out;
  }, [slots, t, k]);
  const onHours = hist.filter((x) => x >= 0).length;
  const jobsDone = new Set(hist.filter((x) => x >= 0)).size;
  const kindLabel = { running: "Running", paused: "Paused · checkpointed", ready: "Ready · no work", off: "Off · no heat permit" }[s.kind];
  return (
    <div className="absolute bottom-6 right-24 w-[360px] rounded-[24px] bg-card/97 p-5 shadow-[0_24px_60px_-28px_rgba(50,30,10,0.55)] ring-1 ring-line backdrop-blur">
      <button onClick={onClose} className="absolute right-4 top-4 grid size-8 place-items-center rounded-full ring-1 ring-line hover:bg-paper" aria-label="Close">
        <X size={15} />
      </button>
      <div className="text-[12px] uppercase tracking-[0.14em] text-rust">
        {sObj.id} · server S{k + 1}
      </div>
      <div className="mt-1 font-display text-[24px] font-semibold">{kindLabel}</div>
      <div className="mt-1 text-[12.5px] text-muted">1 kW reference server · {s.kind === "running" ? "0.8 kW heat to the tank" : "0 kW, no heat"}</div>

      {s.job && jt ? (
        <div className="mt-4 rounded-2xl bg-paper/70 p-3.5">
          <div className="flex items-center gap-3">
            <JobIcon type={s.job.type} />
            <div className="min-w-0 flex-1">
              <div className="text-[14px] font-semibold">
                {jt.id} {jt.name} · #{s.job.id}
              </div>
              <div className="text-[11.5px] text-muted">
                {jt.model} · {jt.detail}
              </div>
            </div>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-line">
            <div className="h-full rounded-full bg-rust" style={{ width: `${p * 100}%` }} />
          </div>
          <div className="mt-1.5 flex justify-between text-[11.5px] text-muted">
            <span>{Math.round(p * 100)}% done</span>
            <span>
              due {fmtDay(s.job.arrive + jt.due_h)} {fmtTime(s.job.arrive + jt.due_h)} · in {s.job.arrive + jt.due_h - t} h
            </span>
          </div>
          {s.kind === "paused" && (
            <div className="mt-2 text-[11.5px] leading-snug text-ink-2">
              The tank is full or the house needs less heat, so the job was checkpointed. It resumes when the heat permit comes
              back, still ahead of its deadline.
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4 rounded-2xl bg-paper/70 p-3.5 text-[12.5px] leading-snug text-muted">
          {s.kind === "ready"
            ? "The house could take this server's heat, but no admitted job is waiting at this site."
            : "The house has no use for more heat this hour, so this server stays off. Nothing is dumped."}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-[12px]">
        <span className="font-semibold">Last 48 h</span>
        <span className="text-muted">
          {onHours} h on · {jobsDone} job{jobsDone === 1 ? "" : "s"}
        </span>
      </div>
      <div className="mt-2 flex h-6 gap-[2px]">
        {hist.map((x, i) => (
          <i key={i} className={clsx("flex-1 rounded-[2px]", x >= 0 ? (i === hist.length - 1 ? "bg-ink" : "bg-rust") : "bg-line")} />
        ))}
      </div>
    </div>
  );
}
