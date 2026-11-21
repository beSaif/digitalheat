"use client";

import { useState } from "react";
import Link from "next/link";
import clsx from "clsx";
import { ArrowRight } from "lucide-react";
import { useFleet } from "@/lib/store";
import { useSavedSites, useSchedule, type Schedule, type YearFig } from "@/lib/schedule";
import { Card, Loading, PayChip } from "@/components/ui";

const chf = (x: number) => `CHF ${Math.round(x).toLocaleString("de-CH")}`;

export default function Money() {
  const { year } = useFleet();
  const [sites] = useSavedSites();
  const { data, error } = useSchedule(sites, year);
  const [pick, setPick] = useState<number | "fleet">("fleet");
  if (!data) return error ? <div className="p-6 text-rust-deep">Scheduler error: {error}</div> : <Loading />;

  const i = pick === "fleet" || pick >= data.sites.length ? null : pick;
  const f = i === null ? data.fleet : data.sites[i].year;
  const m = f.money;

  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-display text-[40px] font-semibold leading-none">Does it pay off?</h1>
        <div className="flex flex-wrap gap-1 rounded-full bg-card p-1 ring-1 ring-line/70">
          {[{ k: "fleet" as const, l: "Fleet" }, ...data.sites.map((s, j) => ({ k: j, l: s.name }))].map((o) => (
            <button
              key={o.k}
              onClick={() => setPick(o.k)}
              className={clsx("rounded-full px-3 py-1.5 text-[13px] font-semibold", (i ?? "fleet") === o.k ? "bg-ink text-cream" : "hover:bg-paper")}
            >
              {o.l}
            </button>
          ))}
        </div>
      </div>

      {m ? (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <Stat label="Computing income" value={chf(m.income_chf)} sub={`${Math.round(f.run_server_h).toLocaleString("de-CH")} server-h × CHF ${m.sell_chf_per_server_h.toFixed(2)}`} />
            <Stat
              label="Costs"
              value={chf(f.electricity_chf + f.hardware_chf - f.heat_value_chf)}
              sub={`power ${chf(f.electricity_chf)} · servers ${chf(f.hardware_chf)} · heat −${chf(f.heat_value_chf).slice(4)}`}
            />
            <Card className="bg-ink text-cream ring-0">
              <div className="flex items-center justify-between">
                <h3 className="text-[17px] font-semibold">Profit</h3>
                <PayChip ok={m.pays_off} />
              </div>
              <div className="mt-3 font-display text-[40px] font-semibold leading-none">{chf(m.profit_chf)}</div>
              <div className="mt-3 text-[13px] text-cream/60">per year · {year} weather</div>
            </Card>
          </div>

          <Card className="mt-4">
            <h3 className="text-[17px] font-semibold">Price of one server-hour</h3>
            <Ladder s={data} f={f} />
          </Card>

          <Card className="mt-4">
            <h3 className="text-[17px] font-semibold">Stops paying off when</h3>
            <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Limit label="Price below" value={`CHF ${m.min_price_chf_per_server_h.toFixed(2)}`} unit="/ server-h" />
              <Limit label="Servers busy less than" value={`${Math.round((m.min_utilisation ?? 0) * 100)}%`} unit="of the year" />
              <Limit label="Electricity above" value={`CHF ${m.max_electricity_chf_kwh.toFixed(2)}`} unit="/ kWh" />
              <Limit label="Server costs more than" value={chf(m.max_hardware_chf_per_server)} unit="each" />
            </div>
            <p className="mt-4 text-[13px] text-muted">Income counts every hour a server runs as sold.</p>
          </Card>

          <Card className="mt-4">
            <h3 className="text-[17px] font-semibold">One job</h3>
            <table className="mt-3 w-full text-[14px] tabular-nums">
              <thead className="text-left text-[12px] text-muted">
                <tr>
                  <th className="py-2 font-medium">Job</th>
                  <th className="font-medium">Server-h</th>
                  <th className="font-medium">Our price</th>
                  <th className="font-medium">AWS server</th>
                  <th className="font-medium">AWS service</th>
                </tr>
              </thead>
              <tbody>
                {(["embed", "rerank"] as const).map((k) => {
                  const j = data.job_prices[k];
                  return (
                    <tr key={k} className="border-t border-line/70">
                      <td className="py-2.5 font-semibold">{k === "embed" ? "Embed" : "Rerank"}</td>
                      <td>{j.server_h.toFixed(2)}</td>
                      <td className="font-semibold">CHF {j.spot_chf.toFixed(2)}</td>
                      <td>CHF {j.on_demand_chf.toFixed(2)}</td>
                      <td>CHF {j.service_chf.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          <Link href="/assumptions" className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-semibold text-muted hover:text-ink">
            Sources and assumptions <ArrowRight size={13} />
          </Link>
        </>
      ) : (
        <Card className="mt-6 text-muted">No servers running.</Card>
      )}
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <Card>
      <h3 className="text-[17px] font-semibold">{label}</h3>
      <div className="mt-3 font-display text-[40px] font-semibold leading-none">{value}</div>
      <div className="mt-3 text-[13px] text-muted">{sub}</div>
    </Card>
  );
}

function Limit({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="rounded-2xl bg-paper p-4">
      <div className="text-[13px] text-muted">{label}</div>
      <div className="mt-1 font-display text-[26px] font-semibold leading-tight">{value}</div>
      <div className="text-[12px] text-muted">{unit}</div>
    </div>
  );
}

/** Our break-even, our price (AWS spot) and AWS on-demand on one line. */
function Ladder({ s, f }: { s: Schedule; f: YearFig }) {
  const pts = [
    { v: f.money!.min_price_chf_per_server_h, l: "Our cost", c: "bg-ink" },
    { v: s.constants.aws_spot_chf_h, l: "Our price · AWS spot", c: "bg-rust" },
    { v: s.constants.aws_on_demand_chf_h, l: "AWS on-demand", c: "bg-[#2f6e75]" },
  ];
  const max = Math.max(...pts.map((p) => p.v)) * 1.08;
  return (
    <div className="relative mt-10 mb-12 h-2 rounded-full bg-paper">
      <div className="absolute inset-y-0 left-0 rounded-full bg-amber-soft" style={{ width: `${(pts[0].v / max) * 100}%` }} />
      {pts.map((p, k) => (
        <div key={p.l} className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ left: `${(p.v / max) * 100}%` }}>
          <div className={clsx("size-4 rounded-full ring-4 ring-card", p.c)} />
          <div className={clsx("absolute left-1/2 -translate-x-1/2 whitespace-nowrap text-center", k === 1 ? "bottom-6" : "top-6")}>
            <div className="text-[15px] font-semibold tabular-nums">CHF {p.v.toFixed(2)}</div>
            <div className="text-[12px] text-muted">{p.l}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
