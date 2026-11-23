"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";
import { Minus, Plus } from "lucide-react";
import { useSchedule, type SiteIn } from "@/lib/schedule";
import { CLOUD, COSTS, DEFAULT_PRICE, finance, type Fin, type HoursMode } from "@/lib/finance";

/* The reference house's money: costs, payback, profit, and our price next to AWS and Azure. */

const chf = (x: number) => `${x < 0 ? "−" : ""}CHF ${Math.round(Math.abs(x)).toLocaleString("de-CH")}`;
const num = (x: number) => Math.round(x).toLocaleString("de-CH");

function payback(m: number | null) {
  if (m === null) return "never";
  if (m < 1) return `${Math.max(1, Math.round(m * 30))} days`;
  if (m < 12) return `${m.toFixed(1)} months`;
  return `${(m / 12).toFixed(1)} years`;
}

/** compact: the pitch slide, without the cash chart, so it fits one screen. */
export function Finance({ year = 2025, compact = false, servers = 4 }: { year?: number; compact?: boolean; servers?: number }) {
  const [n, setN] = useState(servers);
  const [mode, setMode] = useState<HoursMode>("heat");
  const [price, setPrice] = useState(DEFAULT_PRICE);
  const sites = useMemo<SiteIn[]>(() => [{ id: "BS-01", kind: "house", name: "Reference house", lat: 47.5695, lon: 7.588, servers: n }], [n]);
  const { data, error, loading } = useSchedule(sites, year);
  const f = useMemo(() => (data ? finance(data, price, mode) : null), [data, price, mode]);

  return (
    <div className="flex flex-col gap-4">
      {/* controls (not in the pitch) */}
      <div className={clsx("flex flex-wrap items-center gap-3", compact && "hidden")}>
        <div className="dh-pill flex items-center gap-1 rounded-full bg-card p-1 ring-1 ring-line/70">
          <span className="px-2 text-[13px] font-semibold text-muted">Servers</span>
          <RoundBtn onClick={() => setN(Math.max(1, n - 1))} label="Fewer servers"><Minus size={14} /></RoundBtn>
          <span className="w-6 text-center font-display text-[18px] font-semibold tabular-nums">{n}</span>
          <RoundBtn onClick={() => setN(Math.min(12, n + 1))} label="More servers"><Plus size={14} /></RoundBtn>
        </div>
        <div className="dh-pill flex gap-1 rounded-full bg-card p-1 ring-1 ring-line/70">
          {([["heat", "Heat-led hours"], ["always", "Always on"]] as const).map(([k, l]) => (
            <button key={k} onClick={() => setMode(k)} className={clsx("rounded-full px-3 py-1.5 text-[13px] font-semibold", mode === k ? "bg-ink text-cream" : "hover:bg-paper")}>
              {l}
            </button>
          ))}
        </div>
        <label className="dh-pill flex min-w-[260px] flex-1 items-center gap-3 rounded-full bg-card px-4 py-1.5 ring-1 ring-line/70">
          <span className="whitespace-nowrap text-[13px] font-semibold text-muted">Our price</span>
          <input type="range" min={0.2} max={10} step={0.05} value={price} onChange={(e) => setPrice(Number(e.target.value))} className="w-full accent-rust" aria-label="Our price per server-hour" />
          <span className="whitespace-nowrap font-display text-[18px] font-semibold tabular-nums">CHF {price.toFixed(2)}</span>
          <span className="whitespace-nowrap text-[12px] text-muted">/ server-h</span>
        </label>
        {loading && <span className="size-2 animate-pulse rounded-full bg-rust" />}
      </div>

      {!f ? (
        <Card className="text-[14px] text-muted">{error ? `Scheduler error: ${error}` : "Running the scheduler for 2025…"}</Card>
      ) : (
        <>
          {/* the three numbers to say out loud */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Card className="bg-ink text-cream ring-0">
              <div className="text-[15px] font-semibold text-cream/70">Pays back in</div>
              <div className="mt-2 font-display text-[44px] font-semibold leading-none">{payback(f.paybackMonths)}</div>
              {!compact && <div className="mt-3 text-[13px] text-cream/55">{chf(f.invest)} invested · from January</div>}
            </Card>
            <Stat label="Profit per year" value={chf(f.profit)} sub={compact ? undefined : `after paying back the investment over ${f.years} years`} bad={f.profit < 0} />
            <Stat
              label="Server-hours sold"
              value={num(f.runH)}
              sub={compact ? undefined : mode === "heat" ? `${Math.round(f.utilisation * 100)}% busy · 0 kWh heat dumped` : `100% busy · ${num(f.dumpedKwh)} kWh heat dumped`}
              bad={mode === "always"}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.15fr]">
            <CostCard f={f} compact={compact} />
            <PriceCard f={f} price={price} compact={compact} />
          </div>

          {!compact && <CashCard f={f} />}
        </>
      )}
    </div>
  );
}

function RoundBtn({ onClick, label, children }: { onClick: () => void; label: string; children: React.ReactNode }) {
  return (
    <button onClick={onClick} aria-label={label} className="grid size-7 place-items-center rounded-full hover:bg-paper">
      {children}
    </button>
  );
}

function Stat({ label, value, sub, bad }: { label: string; value: string; sub?: string; bad?: boolean }) {
  return (
    <Card>
      <div className="text-[15px] font-semibold text-muted">{label}</div>
      <div className={clsx("mt-2 font-display text-[44px] font-semibold leading-none tabular-nums", bad && "text-rust")}>{value}</div>
      {sub && <div className="mt-3 text-[13px] text-muted">{sub}</div>}
    </Card>
  );
}

function Row({ k, v, sub, strong }: { k: string; v: string; sub?: string; strong?: boolean }) {
  return (
    <div className={clsx("flex items-baseline justify-between gap-3 py-1.5", strong && "border-t border-line pt-2.5 font-semibold")}>
      <span>
        {k}
        {sub && <span className="ml-1.5 text-[12px] text-muted">{sub}</span>}
      </span>
      <span className="tabular-nums">{v}</span>
    </div>
  );
}

function CostCard({ f, compact }: { f: Fin; compact?: boolean }) {
  const sub = (x: string) => (compact ? undefined : x); // the pitch shows no small print
  return (
    <Card>
      <h3 className="text-[17px] font-semibold">Costs</h3>
      <div className="mt-3 text-[12px] font-semibold uppercase tracking-[0.12em] text-muted">Once</div>
      <div className="text-[14px]">
        <Row k="Servers" sub={sub(`${f.n} × CHF ${num(f.servers / f.n)}`)} v={chf(f.servers)} />
        <Row k="Installation" sub={sub(`CHF ${num(COSTS.install_site_chf.v)} + ${f.n} × ${COSTS.install_server_chf.v}`)} v={chf(f.install)} />
        <Row k="Investment" v={chf(f.invest)} strong />
      </div>
      <div className="mt-4 text-[12px] font-semibold uppercase tracking-[0.12em] text-muted">Every year</div>
      <div className="text-[14px]">
        <Row k="Electricity" sub={sub(`${num(f.runH)} kWh × CHF 0.33`)} v={chf(f.power)} />
        <Row k="Maintenance" sub={sub(`${f.n} × CHF ${COSTS.maint_server_chf_y.v}`)} v={chf(f.maint)} />
        <Row k="Operation" sub={sub("internet, monitoring")} v={chf(f.ops)} />
        <Row k="Heat the house doesn't buy" v={`+ ${chf(f.heat)}`} />
        <Row k="Running cost" v={chf(f.power + f.maint + f.ops - f.heat)} strong />
      </div>
    </Card>
  );
}

/** Our cost, our price and the four cloud prices for one server-hour, and what a customer pays for the year. */
function PriceCard({ f, price, compact }: { f: Fin; price: number; compact?: boolean }) {
  const rows = [
    { name: "Our cost", chf: f.costPerH, tone: "cost" as const },
    { name: "Us", chf: price, tone: "us" as const },
    ...CLOUD.slice().sort((a, b) => a.chf - b.chf).map((c) => ({ name: c.name, chf: c.chf, tone: "cloud" as const })),
  ];
  const max = Math.max(...rows.map((r) => r.chf));
  const cheapest = Math.min(...CLOUD.map((c) => c.chf));
  // the cheapest cloud we still undercut (or match)
  const beat = CLOUD.filter((c) => c.chf >= price - 0.005).sort((a, b) => a.chf - b.chf)[0];
  const save = beat ? 1 - price / beat.chf : -1;
  const badge = !beat ? "above every cloud" : save < 0.01 ? `same as ${beat.name}` : `${Math.round(save * 100)}% below ${beat.chf === cheapest ? "the cheapest cloud" : beat.name}`;
  return (
    <Card>
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-[17px] font-semibold">One server-hour</h3>
        <span className={clsx("rounded-full px-2 py-0.5 text-[12px] font-semibold", beat ? "bg-teal-soft text-[#2f6e75]" : "bg-amber-soft text-rust-deep")}>
          {badge}
        </span>
      </div>
      <div className="mt-4 flex flex-col gap-2.5">
        {rows.map((r) => (
          <div key={r.name} className="grid grid-cols-[124px_1fr_74px] items-center gap-3 text-[14px]">
            <span className={clsx("whitespace-nowrap", r.tone === "us" && "font-semibold text-rust", r.tone === "cost" && "text-muted")}>{r.name}</span>
            <div className="h-5 rounded-md bg-paper">
              <div
                className={clsx("h-full rounded-md", r.tone === "us" ? "bg-rust" : r.tone === "cost" ? "hatch bg-paper ring-1 ring-line" : "bg-ink/80")}
                style={{ width: `${Math.max(1.5, (r.chf / max) * 100)}%` }}
              />
            </div>
            <span className="text-right font-semibold tabular-nums">CHF {r.chf.toFixed(2)}</span>
          </div>
        ))}
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-paper p-3">
          <div className="text-[12px] text-muted">A customer pays us</div>
          <div className="font-display text-[22px] font-semibold tabular-nums">{chf(f.income)}</div>
        </div>
        <div className="rounded-2xl bg-paper p-3">
          <div className="text-[12px] text-muted">Same hours, AWS on-demand</div>
          <div className="font-display text-[22px] font-semibold tabular-nums">{chf(f.runH * CLOUD[0].chf)}</div>
        </div>
      </div>
      {!compact && <div className="mt-3 text-[12px] text-muted">Per year, for the {num(f.runH)} server-hours. Cloud: 192-core instances, USD × 0.84.</div>}
    </Card>
  );
}

/** Cumulative cash over the server lifetime. */
function CashCard({ f }: { f: Fin }) {
  const W = 1200;
  const H = 180;
  const P = { l: 8, r: 8, t: 14, b: 22 };
  const lo = Math.min(0, ...f.cum);
  const hi = Math.max(0, ...f.cum);
  const X = (i: number) => P.l + (i / (f.cum.length - 1)) * (W - P.l - P.r);
  const Y = (v: number) => P.t + (1 - (v - lo) / (hi - lo || 1)) * (H - P.t - P.b);
  const path = f.cum.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join("");
  const pb = f.paybackMonths;
  return (
    <Card>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h3 className="text-[17px] font-semibold">Cash over {f.years} years</h3>
        <span className="text-[14px] text-muted">
          after {f.years} years <b className={clsx("font-display text-[20px] tabular-nums", f.lifetimeProfit < 0 ? "text-rust" : "text-ink")}>{chf(f.lifetimeProfit)}</b>
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 h-auto w-full" role="img" aria-label="Cumulative cash by month">
        <line x1={P.l} x2={W - P.r} y1={Y(0)} y2={Y(0)} stroke="currentColor" className="text-line" strokeWidth={1.5} />
        {Array.from({ length: f.years + 1 }, (_, y) => (
          <text key={y} x={X(y * 12)} y={H - 4} textAnchor={y === 0 ? "start" : y === f.years ? "end" : "middle"} className="fill-muted text-[12px]">
            {y === 0 ? "start" : `year ${y}`}
          </text>
        ))}
        <path d={path} fill="none" stroke="var(--dh-rust)" strokeWidth={2.5} strokeLinejoin="round" />
        {pb !== null && (
          <g>
            <circle cx={X(pb)} cy={Y(0)} r={5} fill="var(--dh-ink)" />
            <text x={X(pb) + 9} y={Y(0) - 8} className="fill-ink text-[13px] font-semibold">paid back</text>
          </g>
        )}
      </svg>
    </Card>
  );
}

function Card({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement> & { className?: string }) {
  return (
    <div className={clsx("dh-card rounded-[24px] bg-card p-5 ring-1 ring-line/70", className)} {...rest}>
      {children}
    </div>
  );
}
