"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import clsx from "clsx";
import { ArrowDown, ArrowUp, Server } from "lucide-react";
import { useFleet } from "@/lib/store";
import { nf, type CostLine, type Fleet } from "@/lib/data";
import { chf, defaults, fleetMoney, hardware, type Assumptions } from "@/lib/money";
import { Card, CardTitle, Chip, Loading } from "@/components/ui";

export default function EconomicsPage() {
  const { fleet } = useFleet();
  if (!fleet) return <Loading />;
  return <Economics fleet={fleet} />;
}

function Economics({ fleet }: { fleet: Fleet }) {
  const e = fleet.meta.economics;
  const [a, setA] = useState<Assumptions>(() => defaults(e));
  const m = useMemo(() => fleetMoney(fleet, a), [fleet, a]);

  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-[40px] font-semibold leading-none">Economics</h1>
          <p className="mt-2.5 text-[15px] text-muted">
            What the fleet costs to build and run, and what each sold server-hour has to earn. Prices in CHF incl. VAT.
          </p>
        </div>
        <Controls a={a} setA={setA} fleet={fleet} />
      </div>

      {/* KPIs */}
      <div className="mt-6 grid grid-cols-2 gap-4 xl:grid-cols-5">
        <Kpi
          label="Installed cost, fleet"
          value={`${nf(m.installed / 1e6, 2)}`}
          unit="M CHF"
          sub={`${fleet.totals.servers} servers in ${fleet.totals.sites} houses · ${nf(m.installed / fleet.totals.servers)} per server`}
        />
        <Kpi
          label="Running cost, per year"
          value={nf((m.cost - m.depreciation) / 1000)}
          unit="k CHF"
          sub={`electricity ${nf(m.electricity / 1000)}k − heat ${nf(m.heat / 1000)}k + fixed ${nf(m.fixed / 1000)}k`}
        />
        <Kpi
          label="Break-even, electricity only"
          value={nf(m.breakeven, 4)}
          unit="CHF/h"
          sub={a.heatShare ? "case formula: power cost minus heat value" : "homeowner keeps the heat"}
        />
        <Kpi
          label="Price needed, incl. hardware"
          value={nf(m.priceNeeded, 2)}
          unit="CHF/h"
          sub={`${a.life}-year write-off, no interest`}
          dark
        />
        <Kpi
          label={`Margin at ${nf(a.price, 2)} CHF / server-h`}
          value={chf(m.margin / 1000)}
          unit="k CHF / yr"
          sub={
            !Number.isFinite(m.payback)
              ? "running costs alone exceed income"
              : m.payback > a.life
                ? `hardware paid back after ${nf(m.payback, 1)} y, beyond the ${a.life}-year life`
                : `hardware paid back in ${nf(m.payback, 1)} years`
          }
          tone={m.margin >= 0 ? "good" : "bad"}
        />
      </div>

      <div className="mt-4 grid grid-cols-12 gap-4">
        <ServerCard fleet={fleet} className="col-span-12 xl:col-span-4" />
        <HouseCost fleet={fleet} className="col-span-12 md:col-span-6 xl:col-span-4" />
        <YearCost m={m} className="col-span-12 md:col-span-6 xl:col-span-4" />
        <PriceLadder fleet={fleet} m={m} a={a} className="col-span-12 xl:col-span-5" />
        <SiteTable fleet={fleet} m={m} className="col-span-12 xl:col-span-7" />
      </div>

      <p className="mt-4 text-[12px] leading-relaxed text-faint">
        Sold server-hours, heat delivered and coverage come from the scenario run. Hardware, maintenance, insurance and
        card failures are estimates and assumptions (docs/overnight.md, Key numbers; analysis/r7_payback.py). Electricity:{" "}
        {e.electricity_source}, {nf(e.electricity_chf_kwh * 100, 2)} Rp/kWh. Heat value = electricity price ÷ heat-pump COP{" "}
        {e.heat_pump_cop}. The selling price is a scenario: {e.compute_price_note}.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ controls */

function Controls({ a, setA, fleet }: { a: Assumptions; setA: (a: Assumptions) => void; fleet: Fleet }) {
  const e = fleet.meta.economics;
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-[20px] bg-card px-4 py-3 ring-1 ring-line/70">
      <label className="flex items-center gap-2 text-[13px] text-muted">
        Selling price
        <input
          type="range"
          min={0.25}
          max={5}
          step={0.05}
          value={a.price}
          onChange={(ev) => setA({ ...a, price: Number(ev.target.value) })}
          className="w-28 accent-[#c0653a]"
        />
        <span className="w-[92px] font-semibold tabular-nums text-ink">{nf(a.price, 2)} CHF/h</span>
      </label>
      <Seg
        value={a.occupancy === null ? "sim" : "60"}
        options={[
          ["sim", "Sold as simulated"],
          ["60", `${Math.round(e.occ_alt * 100)}% sold`],
        ]}
        onChange={(v) => setA({ ...a, occupancy: v === "sim" ? null : e.occ_alt })}
        title={`Share of heat-permitted hours sold. ${Math.round(e.occ_alt * 100)}%: ${e.occ_alt_note}`}
      />
      <Seg
        value={a.heatShare ? "op" : "home"}
        options={[
          ["op", "Heat credited"],
          ["home", "Homeowner keeps heat"],
        ]}
        onChange={(v) => setA({ ...a, heatShare: v === "op" ? 1 : 0 })}
        title="Who is paid for the heat. Credited = case formula (heat valued at electricity ÷ COP 2.5)."
      />
      <Seg
        value={String(a.life)}
        options={[
          ["5", "5 y"],
          ["8", "8 y"],
        ]}
        onChange={(v) => setA({ ...a, life: Number(v) })}
        title="Hardware write-off period"
      />
    </div>
  );
}

function Seg({
  value,
  options,
  onChange,
  title,
}: {
  value: string;
  options: [string, string][];
  onChange: (v: string) => void;
  title?: string;
}) {
  return (
    <div className="flex rounded-full bg-paper p-0.5 text-[12.5px]" title={title}>
      {options.map(([v, l]) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={clsx(
            "rounded-full px-3 py-1.5 font-medium",
            v === value ? "bg-ink text-cream" : "text-muted hover:text-ink",
          )}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

function Kpi({
  label,
  value,
  unit,
  sub,
  dark,
  tone,
}: {
  label: string;
  value: string;
  unit: string;
  sub: string;
  dark?: boolean;
  tone?: "good" | "bad";
}) {
  return (
    <div className={clsx("rounded-[24px] p-5 ring-1", dark ? "bg-ink text-cream ring-ink" : "bg-card ring-line/70")}>
      <div className={clsx("text-[13px]", dark ? "text-cream/70" : "text-muted")}>{label}</div>
      <div
        className={clsx(
          "mt-2 font-display text-[34px] font-semibold leading-none tabular-nums",
          tone === "bad" && "text-alarm",
          tone === "good" && "text-[#2f6e75]",
        )}
      >
        {value}
        <span className={clsx("ml-1.5 font-sans text-[14px] font-medium tracking-normal", dark ? "text-cream/60" : "text-muted")}>{unit}</span>
      </div>
      <div className={clsx("mt-2 text-[12px] leading-snug", dark ? "text-cream/60" : "text-faint")}>{sub}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ server */

const KIND_TONE = { sourced: "teal", computed: "neutral", assumption: "amber" } as const;

function ServerCard({ fleet, className }: { fleet: Fleet; className?: string }) {
  const s = fleet.meta.economics.server;
  const hw = fleet.meta.economics.hardware;
  const box = s.box_lines_chf.reduce((x, l) => x + l.chf, 0);
  return (
    <Card className={className}>
      <CardTitle right={<Chip tone="ink">1 kW unit</Chip>}>Which server</CardTitle>
      <div className="mt-4 flex gap-4">
        <span className="grid size-14 shrink-0 place-items-center rounded-2xl bg-amber-soft text-rust-deep">
          <Server size={28} />
        </span>
        <div>
          <div className="text-[18px] font-semibold leading-tight">{s.gpu}</div>
          <div className="mt-1 text-[13px] text-muted">
            {s.chassis} · {s.cpu} · {s.gpu_count} × {s.gpu_memory_gb} GB · {s.gpu_tdp_w} W per card
          </div>
        </div>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2.5 text-[13px]">
        <Spec k="Wall power" v={`${nf(s.wall_w.central)} W (${nf(s.wall_w.low)}–${nf(s.wall_w.high)}), estimated`} />
        <Spec k="Heat to the house" v={`${Math.round(fleet.meta.constants.heat_recovery * 100)}% of power (case)`} />
        <Spec k="Cooling" v={s.cooling} wide />
        <Spec k="Benchmark" v={s.bench} wide />
      </dl>
      <div className="mt-4 border-t border-line pt-3">
        <div className="flex items-baseline justify-between text-[13px]">
          <span className="font-semibold">One box, installed</span>
          <span className="font-semibold tabular-nums">{nf(box)} CHF</span>
        </div>
        <Lines lines={s.box_lines_chf} />
        <div className="mt-2 text-[12px] text-faint">
          One box draws {nf(s.wall_w.central)} W, so one 1 kW server costs {nf(hw.installed_server_chf)} CHF. {s.status}.
        </div>
      </div>
    </Card>
  );
}

function Spec({ k, v, wide }: { k: string; v: string; wide?: boolean }) {
  return (
    <div className={wide ? "col-span-2" : ""}>
      <dt className="text-[11.5px] uppercase tracking-[0.08em] text-faint">{k}</dt>
      <dd className="mt-0.5 text-ink-2">{v}</dd>
    </div>
  );
}

function Lines({ lines }: { lines: CostLine[] }) {
  return (
    <ul className="mt-2 space-y-1.5">
      {lines.map((l) => (
        <li key={l.label} className="flex items-center gap-2 text-[12.5px]">
          <span className="min-w-0 flex-1 truncate text-muted" title={l.label}>
            {l.label}
          </span>
          <Chip tone={KIND_TONE[l.kind]}>{l.kind}</Chip>
          <span className="w-[64px] text-right tabular-nums">{nf(l.chf)}</span>
        </li>
      ))}
    </ul>
  );
}

/* ------------------------------------------------------------------ one house */

function HouseCost({ fleet, className }: { fleet: Fleet; className?: string }) {
  const e = fleet.meta.economics;
  const ref = fleet.sites.find((s) => s.reference) ?? fleet.sites[0];
  const h = hardware(e, ref.servers);
  return (
    <Card className={className}>
      <CardTitle right={<Chip>{ref.id}</Chip>}>Cost of one house</CardTitle>
      <div className="mt-1 text-[12.5px] text-muted">Reference house, {ref.servers} servers</div>
      <div className="mt-3 font-display text-[34px] font-semibold leading-none tabular-nums">
        {nf(h.installed)}
        <span className="ml-1.5 font-sans text-[14px] font-medium tracking-normal text-muted">CHF</span>
      </div>
      <div className="mt-3 space-y-1.5 text-[12.5px]">
        <Row k={`${ref.servers} × server`} v={nf(e.hardware.installed_server_chf * ref.servers)} />
        <Row k="House side" v={nf(e.hardware.installed_house_chf)} />
      </div>
      <Lines lines={e.server.house_lines_chf} />
      <div className="mt-3 border-t border-line pt-3 text-[12.5px]">
        <div className="mb-1.5 font-semibold">Fixed, per year</div>
        <Row k="Maintenance + leak reserve" v={nf(h.maint)} />
        <Row k="Card failures (1.01 %/yr)" v={nf(h.cards)} />
        <Row k={`Insurance (${e.hardware.insurance_share_yr * 100}% of installed)`} v={nf(h.insurance)} />
        <Row k="Internet uplink" v={nf(h.uplink)} />
      </div>
    </Card>
  );
}

function Row({ k, v, strong }: { k: string; v: string; strong?: boolean }) {
  return (
    <div className={clsx("flex justify-between gap-3", strong && "font-semibold")}>
      <span className="text-muted">{k}</span>
      <span className="tabular-nums">{v}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ year cost */

type FM = ReturnType<typeof fleetMoney>;

function YearCost({ m, className }: { m: FM; className?: string }) {
  const parts = [
    { k: "Electricity", v: m.electricity, c: "#c0653a" },
    { k: "Hardware write-off", v: m.depreciation, c: "#141412" },
    { k: "Insurance", v: m.insurance, c: "#5fa8b0" },
    { k: "Maintenance", v: m.maint, c: "#f2a65a" },
    { k: "Card failures", v: m.cards, c: "#8f4423" },
    { k: "Uplink", v: m.uplink, c: "#9a958a" },
  ];
  const gross = parts.reduce((x, p) => x + p.v, 0);
  return (
    <Card className={className}>
      <CardTitle>Where a year&apos;s cost goes</CardTitle>
      <div className="mt-1 text-[12.5px] text-muted">Whole fleet, {nf(m.sold)} sold server-hours</div>
      <div className="mt-4 flex h-4 overflow-hidden rounded-full">
        {parts.map((p) => (
          <div key={p.k} style={{ width: `${(p.v / gross) * 100}%`, background: p.c }} title={`${p.k}: ${nf(p.v)} CHF`} />
        ))}
      </div>
      <table className="mt-4 w-full text-[12.5px]">
        <thead className="text-faint">
          <tr>
            <th className="pb-1.5 text-left font-medium" />
            <th className="pb-1.5 text-right font-medium">CHF / yr</th>
            <th className="pb-1.5 text-right font-medium">per server-h</th>
          </tr>
        </thead>
        <tbody>
          {parts.map((p) => (
            <tr key={p.k}>
              <td className="py-1">
                <span className="flex items-center gap-2">
                  <i className="size-2.5 rounded-sm" style={{ background: p.c }} />
                  {p.k}
                </span>
              </td>
              <td className="py-1 text-right tabular-nums">{nf(p.v)}</td>
              <td className="py-1 text-right tabular-nums">{nf(p.v / m.sold, 3)}</td>
            </tr>
          ))}
          <tr className="text-[#2f6e75]">
            <td className="py-1">Heat value credited</td>
            <td className="py-1 text-right tabular-nums">{chf(-m.heat)}</td>
            <td className="py-1 text-right tabular-nums">{chf(-m.heat / m.sold, 3)}</td>
          </tr>
          <tr className="border-t border-line font-semibold">
            <td className="pt-2">Total</td>
            <td className="pt-2 text-right tabular-nums">{nf(m.cost)}</td>
            <td className="pt-2 text-right tabular-nums">{nf(m.priceNeeded, 3)}</td>
          </tr>
        </tbody>
      </table>
    </Card>
  );
}

/* ------------------------------------------------------------------ price ladder */

function PriceLadder({ fleet, m, a, className }: { fleet: Fleet; m: FM; a: Assumptions; className?: string }) {
  const refs = fleet.meta.economics.price_refs;
  const max = 5.5;
  const x = (v: number) => `${(Math.min(v, max) / max) * 100}%`;
  const marks = [
    { v: m.breakeven, l: "break-even", c: "#5fa8b0" },
    { v: m.priceNeeded, l: "needed", c: "#c62f2f" },
    { v: a.price, l: "selling", c: "#141412" },
  ];
  return (
    <Card className={className}>
      <CardTitle>Price needed vs what the market pays</CardTitle>
      <div className="mt-1 text-[12.5px] text-muted">CHF per reference server-hour of work</div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[12px]">
        {marks.map((k) => (
          <span key={k.l} className="flex items-center gap-1.5">
            <i className="h-3 w-0.5" style={{ background: k.c }} />
            <span className="text-muted">{k.l}</span>
            <b className="tabular-nums" style={{ color: k.c }}>
              {nf(k.v, 2)}
            </b>
          </span>
        ))}
      </div>
      <div className="relative mt-3">
        {/* marker lines over the bar track: label column 200px + gap 12, value column 68px + gap 12 */}
        <div className="pointer-events-none absolute inset-y-0 left-[212px] right-[80px] z-10">
          {marks.map((k) => (
            <div key={k.l} className="absolute -inset-y-1 w-0.5" style={{ left: x(k.v), background: k.c }} />
          ))}
        </div>
        <ul className="space-y-2.5">
          {refs.map((r) => (
            <li key={r.label} className="flex items-center gap-3" title={r.note}>
              <span className="w-[200px] shrink-0 text-[12.5px] leading-tight text-ink-2">{r.label}</span>
              <div className="relative h-5 flex-1 rounded bg-paper/70">
                <div
                  className={clsx("absolute inset-y-0.5 rounded", r.kind === "sourced" ? "bg-ink-2/80" : "hatch bg-amber-soft")}
                  style={{ left: r.lo === r.hi ? `calc(${x(r.lo)} - 3px)` : x(r.lo), width: r.lo === r.hi ? "6px" : `calc(${x(r.hi)} - ${x(r.lo)})` }}
                />
              </div>
              <span className="w-[68px] shrink-0 text-right text-[12px] tabular-nums text-muted">
                {r.lo === r.hi ? nf(r.lo, 2) : `${nf(r.lo, 2)}–${nf(r.hi, 2)}`}
              </span>
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-4 flex flex-wrap gap-4 text-[11.5px] text-muted">
        <span className="flex items-center gap-1.5">
          <i className="h-2.5 w-4 rounded-sm bg-ink-2/80" /> list price, sourced
        </span>
        <span className="flex items-center gap-1.5">
          <i className="hatch h-2.5 w-4 rounded-sm bg-amber-soft" /> derived, assumption
        </span>
      </div>
      <p className="mt-3 text-[12px] leading-snug text-faint">
        No buyer was found for hours that stop when a house is warm. Interruptible work sells below the price needed;
        uninterrupted rental of the same card sells near it.
      </p>
    </Card>
  );
}

/* ------------------------------------------------------------------ per site */

type SortKey = "id" | "servers" | "installed" | "sold" | "electricity" | "heat" | "priceNeeded" | "margin";

function SiteTable({ fleet, m, className }: { fleet: Fleet; m: FM; className?: string }) {
  const [sort, setSort] = useState<{ k: SortKey; desc: boolean }>({ k: "priceNeeded", desc: false });
  const rows = useMemo(() => {
    const r = fleet.sites.map((s, i) => ({
      s,
      id: s.id,
      servers: s.servers,
      installed: m.rows[i].hw.installed,
      sold: m.rows[i].sold,
      electricity: m.rows[i].electricity,
      heat: m.rows[i].heat,
      priceNeeded: m.rows[i].priceNeeded,
      margin: m.rows[i].margin,
    }));
    r.sort((x, y) => {
      const a = x[sort.k],
        b = y[sort.k];
      const c = typeof a === "string" ? a.localeCompare(b as string) : (a as number) - (b as number);
      return sort.desc ? -c : c;
    });
    return r;
  }, [fleet, m, sort]);
  const cols: [SortKey, string][] = [
    ["id", "Site"],
    ["servers", "Servers"],
    ["installed", "Installed"],
    ["sold", "Sold h"],
    ["electricity", "Electricity"],
    ["heat", "Heat value"],
    ["priceNeeded", "Needed / h"],
    ["margin", "Margin / yr"],
  ];
  return (
    <Card className={clsx("flex flex-col", className)}>
      <CardTitle right={<span className="text-[12px] text-muted">CHF per year unless marked</span>}>By site</CardTitle>
      <div className="mt-3 max-h-[420px] overflow-auto scroll-thin">
        <table className="w-full text-[12.5px]">
          <thead className="sticky top-0 bg-card text-faint">
            <tr>
              {cols.map(([k, l]) => (
                <th
                  key={k}
                  onClick={() => setSort((s) => ({ k, desc: s.k === k ? !s.desc : k !== "id" }))}
                  className={clsx("cursor-pointer select-none pb-2 font-medium hover:text-ink", k === "id" ? "text-left" : "text-right")}
                >
                  <span className="inline-flex items-center gap-0.5">
                    {l}
                    {sort.k === k && (sort.desc ? <ArrowDown size={11} /> : <ArrowUp size={11} />)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-line/70 hover:bg-paper/40">
                <td className="py-1.5">
                  <Link href={`/sites/${r.id}`} className="font-semibold hover:text-rust">
                    {r.id}
                  </Link>{" "}
                  <span className="text-muted">{r.s.city}</span>
                </td>
                <td className="text-right tabular-nums">{r.servers}</td>
                <td className="text-right tabular-nums">{nf(r.installed)}</td>
                <td className="text-right tabular-nums">{nf(r.sold)}</td>
                <td className="text-right tabular-nums">{nf(r.electricity)}</td>
                <td className="text-right tabular-nums">{nf(r.heat)}</td>
                <td className="text-right font-semibold tabular-nums">{nf(r.priceNeeded, 2)}</td>
                <td className={clsx("text-right tabular-nums", r.margin < 0 ? "text-alarm" : "text-[#2f6e75]")}>
                  {chf(r.margin)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
