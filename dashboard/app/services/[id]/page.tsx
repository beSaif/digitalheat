"use client";

import Link from "next/link";
import { use, useMemo, useState } from "react";
import clsx from "clsx";
import { ArrowLeft } from "lucide-react";
import { useFleet } from "@/lib/store";
import { hourDate, nf, type Fleet } from "@/lib/data";
import { defaults, fleetMoney } from "@/lib/money";
import { listPerUnit, perUnit, serviceOf, unitScale, USD_CHF } from "@/lib/services";
import { Card, CardTitle, Chip, JobIcon, Loading } from "@/components/ui";

const MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

export default function ServicePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { fleet } = useFleet();
  if (!fleet) return <Loading />;
  const svc = serviceOf(fleet, id);
  if (!svc)
    return (
      <div className="grid h-full place-items-center text-[14px] text-muted">
        <div>
          No service “{id}”.{" "}
          <Link href="/services" className="font-semibold text-rust">
            All services
          </Link>
        </div>
      </div>
    );
  return <Service fleet={fleet} {...svc} />;
}

function Service({ fleet, jt, st, index }: { fleet: Fleet } & NonNullable<ReturnType<typeof serviceOf>>) {
  const e = fleet.meta.economics;
  const m = useMemo(() => fleetMoney(fleet, defaults(e)), [fleet, e]);
  const [occ, setOcc] = useState<"sim" | "60">("sim");
  const m60 = useMemo(() => fleetMoney(fleet, { ...defaults(e), occupancy: e.occ_alt }), [fleet, e]);
  const needed = occ === "sim" ? m.priceNeeded : m60.priceNeeded;
  const u = unitScale(jt);
  const sv = jt.service;
  const closed = st.admitted;

  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <Link href="/services" className="inline-flex items-center gap-1.5 text-[13px] text-muted hover:text-ink">
        <ArrowLeft size={15} /> Services
      </Link>
      <div className="mt-3 flex flex-wrap items-center gap-4">
        <JobIcon type={index} size={56} />
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-[40px] font-semibold leading-none">{jt.name}</h1>
            <Chip>{jt.id}</Chip>
          </div>
          <p className="mt-2 text-[15px] text-muted">{sv.what}</p>
        </div>
        <div className="ml-auto flex gap-2">
          {fleet.meta.job_types.map((o, i) => (
            <Link
              key={o.id}
              href={`/services/${o.id.toLowerCase()}`}
              className={clsx(
                "rounded-full px-4 py-2 text-[13px] font-semibold ring-1",
                i === index ? "bg-ink text-cream ring-ink" : "ring-line hover:bg-card",
              )}
            >
              {o.name}
            </Link>
          ))}
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 xl:grid-cols-5">
        <Tile label="Sold in 2025" value={nf(st.admitted_server_h / 1000)} unit="k server-h" sub={sv.unit === "audio-hour" ? `${nf(st.units_sold / 1e6, 1)} M audio-hours` : `${nf(st.units_sold / 1e6, 1)} trillion output tokens`} />
        <Tile label="Jobs closed" value={nf(closed)} unit="jobs" sub={`${st.missed} missed the deadline`} />
        <Tile
          label="Refused at intake"
          value={nf(st.refused_heat + st.refused_conflict)}
          unit="jobs"
          sub={`${((100 * (st.refused_heat + st.refused_conflict)) / st.offered).toFixed(1)}% of offered · ${nf(st.refused_server_h)} server-h`}
        />
        <Tile
          label="Turnaround"
          value={st.turnaround_h ? String(st.turnaround_h.median) : "–"}
          unit="h median"
          sub={st.turnaround_h ? `95% within ${st.turnaround_h.p95} h · deadline ${jt.due_h} h` : ""}
        />
        <Tile label={`Cost floor / ${u.label}`} value={nf(perUnit(jt, needed), perUnit(jt, needed) < 1 ? 3 : 2)} unit="CHF" sub={`at ${nf(needed, 2)} CHF per server-h`} dark />
      </div>

      <div className="mt-4 grid grid-cols-12 gap-4">
        <Card className="col-span-12 xl:col-span-4">
          <CardTitle>What the customer buys</CardTitle>
          <dl className="mt-3 space-y-2.5 text-[13px]">
            <Spec k="Unit sold" v={sv.unit === "audio-hour" ? "Audio-hours transcribed" : "Million output tokens generated"} />
            <Spec k="One job" v={`${jt.units / 2} server-h on the reference server (${jt.detail})`} />
            <Spec k="Deadline" v={`${jt.due_h} h after the job is accepted`} />
            <Spec k="Model" v={jt.model} />
            <Spec k="Input → output" v={`${sv.input} → ${sv.output}`} />
            <Spec k="Interruptible" v={`Yes: pauses when the house is warm, checkpoint ${sv.checkpoint}`} />
            <Spec
              k="Throughput, 1 kW server"
              v={`${nf(sv.unit_per_server_h, sv.unit_per_server_h < 100 ? 1 : 0)} ${sv.unit === "audio-hour" ? "audio-hours" : "M tokens"} per server-h (${nf(sv.unit_range[0], sv.unit_range[0] < 100 ? 1 : 0)}–${nf(sv.unit_range[1], sv.unit_range[1] < 100 ? 1 : 0)})`}
            />
            <Spec k="Source" v={sv.bench} />
            {sv.measured_on_laptop && <Spec k="Measured on our laptop" v={sv.measured_on_laptop} />}
          </dl>
        </Card>

        <Card className="col-span-12 md:col-span-6 xl:col-span-4">
          <CardTitle
            right={
              <div className="flex rounded-full bg-paper p-0.5 text-[12px]">
                {(["sim", "60"] as const).map((v) => (
                  <button
                    key={v}
                    onClick={() => setOcc(v)}
                    className={clsx("whitespace-nowrap rounded-full px-2.5 py-1 font-medium", occ === v ? "bg-ink text-cream" : "text-muted")}
                  >
                    {v === "sim" ? "as simulated" : `${Math.round(e.occ_alt * 100)}% sold`}
                  </button>
                ))}
              </div>
            }
          >
            Price per unit
          </CardTitle>
          <div className="mt-1 text-[12.5px] text-muted">CHF per {u.label}</div>
          <PriceBars
            rows={[
              { l: "Break-even, electricity", v: perUnit(jt, (occ === "sim" ? m : m60).breakeven), c: "#5fa8b0" },
              { l: "Cost floor, incl. hardware", v: perUnit(jt, needed), c: "#c62f2f" },
              { l: "List price, low", v: listPerUnit(jt, "low"), c: "#2a2926" },
              { l: "List price, central", v: listPerUnit(jt, "central"), c: "#2a2926" },
              { l: "List price, high", v: listPerUnit(jt, "high"), c: "#2a2926" },
            ]}
          />
          <p className="mt-4 text-[12px] leading-snug text-faint">
            List prices: public US batch APIs, {nf(sv.list_usd.low, 3)}–{nf(sv.list_usd.high, 3)} USD per {sv.list_unit},
            at {USD_CHF} CHF/USD. The cost floor is the fleet&apos;s price needed per server-hour divided by the work one
            server-hour does. Cost floor below list price does not mean there is a buyer for heat-gated work at that volume.
          </p>
        </Card>

        <Monthly st={st} className="col-span-12 md:col-span-6 xl:col-span-4" />

        <BySite fleet={fleet} st={st} className="col-span-12" />
      </div>
    </div>
  );
}

function Tile({ label, value, unit, sub, dark }: { label: string; value: string; unit: string; sub: string; dark?: boolean }) {
  return (
    <div className={clsx("rounded-[24px] p-5 ring-1", dark ? "bg-ink text-cream ring-ink" : "bg-card ring-line/70")}>
      <div className={clsx("text-[13px]", dark ? "text-cream/70" : "text-muted")}>{label}</div>
      <div className="mt-2 font-display text-[32px] font-semibold leading-none tabular-nums">
        {value}
        <span className={clsx("ml-1.5 font-sans text-[14px] font-medium tracking-normal", dark ? "text-cream/60" : "text-muted")}>{unit}</span>
      </div>
      <div className={clsx("mt-2 text-[12px]", dark ? "text-cream/60" : "text-faint")}>{sub}</div>
    </div>
  );
}

function Spec({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-[11.5px] uppercase tracking-[0.08em] text-faint">{k}</dt>
      <dd className="mt-0.5 text-ink-2">{v}</dd>
    </div>
  );
}

function PriceBars({ rows }: { rows: { l: string; v: number; c: string }[] }) {
  const max = Math.max(...rows.map((r) => r.v)) * 1.08;
  return (
    <ul className="mt-4 space-y-3">
      {rows.map((r) => (
        <li key={r.l}>
          <div className="flex justify-between text-[12.5px]">
            <span className="text-muted">{r.l}</span>
            <span className="font-semibold tabular-nums">{nf(r.v, r.v < 1 ? 3 : 2)} CHF</span>
          </div>
          <div className="mt-1 h-2.5 rounded-full bg-paper">
            <div className="h-full rounded-full" style={{ width: `${Math.max(1, (r.v / max) * 100)}%`, background: r.c }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function Monthly({ st, className }: { st: NonNullable<ReturnType<typeof serviceOf>>["st"]; className?: string }) {
  const max = Math.max(...st.monthly_server_h.map((v, i) => v + st.monthly_refused_server_h[i]));
  const [hover, setHover] = useState<number | null>(null);
  const { t } = useFleet();
  const hi = hover ?? hourDate(t).getUTCMonth();
  return (
    <Card className={className}>
      <CardTitle>Work sold by month</CardTitle>
      <div className="mt-1 text-[12.5px] text-muted">
        {["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][hi]}:{" "}
        <b className="text-ink">{nf(st.monthly_server_h[hi])}</b> server-h sold
        {st.monthly_refused_server_h[hi] > 0 && <>, {nf(st.monthly_refused_server_h[hi])} refused</>}
      </div>
      <div className="mt-4 flex h-[180px] items-end gap-1.5">
        {st.monthly_server_h.map((v, i) => (
          <div
            key={i}
            className="flex h-full flex-1 cursor-default flex-col justify-end"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          >
            <div className="hatch rounded-t-sm bg-paper" style={{ height: `${(st.monthly_refused_server_h[i] / max) * 100}%` }} />
            <div className={clsx("rounded-b-sm", i === hi ? "bg-rust" : "bg-ink-2/80")} style={{ height: `${(v / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="mt-1.5 flex gap-1.5 text-center text-[10.5px] text-faint">
        {MONTHS.map((l, i) => (
          <span key={i} className="flex-1">
            {l}
          </span>
        ))}
      </div>
      <p className="mt-3 text-[12px] leading-snug text-faint">
        Work follows heat demand: winter months sell several times the summer volume. Hatched: refused at intake, returned
        to the customer.
      </p>
    </Card>
  );
}

function BySite({ fleet, st, className }: { fleet: Fleet; st: NonNullable<ReturnType<typeof serviceOf>>["st"]; className?: string }) {
  const rows = fleet.sites.map((s, i) => ({ s, h: st.site_server_h[i] })).sort((a, b) => b.h - a.h);
  const max = rows[0]?.h ?? 1;
  return (
    <Card className={className}>
      <CardTitle right={<span className="text-[12px] text-muted">server-h sold in 2025</span>}>By site</CardTitle>
      <div className="mt-4 grid grid-cols-1 gap-x-8 gap-y-2 md:grid-cols-2 xl:grid-cols-3">
        {rows.map(({ s, h }) => (
          <Link key={s.id} href={`/sites/${s.id}`} className="group flex items-center gap-3 text-[12.5px]">
            <span className="w-12 font-semibold group-hover:text-rust">{s.id}</span>
            <span className="w-20 truncate text-muted">{s.city}</span>
            <div className="h-2 flex-1 rounded-full bg-paper">
              <div className="h-full rounded-full bg-rust/80" style={{ width: `${(h / max) * 100}%` }} />
            </div>
            <span className="w-14 text-right tabular-nums">{nf(h)}</span>
          </Link>
        ))}
      </div>
    </Card>
  );
}
