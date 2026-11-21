"use client";

import Link from "next/link";
import { useMemo } from "react";
import { FlaskConical } from "lucide-react";
import { useFleet } from "@/lib/store";
import { nf, type Fleet } from "@/lib/data";
import { defaults, fleetMoney } from "@/lib/money";
import { listPerUnit, perUnit, unitScale } from "@/lib/services";
import { ArrowBadge, Card, CardTitle, Chip, JobIcon, Loading } from "@/components/ui";

export default function ServicesPage() {
  const { fleet } = useFleet();
  if (!fleet) return <Loading />;
  return <Services fleet={fleet} />;
}

function Services({ fleet }: { fleet: Fleet }) {
  const m = useMemo(() => fleetMoney(fleet, defaults(fleet.meta.economics)), [fleet]);
  const totalH = fleet.services.reduce((x, s) => x + s.admitted_server_h, 0);
  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <h1 className="font-display text-[40px] font-semibold leading-none">Services</h1>
      <p className="mt-2.5 max-w-[760px] text-[15px] text-muted">
        What the fleet sells: batch work with a deadline that can pause when a house is warm and resume later. Customers
        buy finished work (audio transcribed, tokens generated), not GPU-hours, so the scheduler keeps control of when the
        servers run and where the heat goes.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
        {fleet.meta.job_types.map((jt, i) => {
          const st = fleet.services[i];
          const u = unitScale(jt);
          return (
            <Link key={jt.id} href={`/services/${jt.id.toLowerCase()}`} className="group">
              <Card className="h-full transition-shadow group-hover:shadow-lg">
                <div className="flex items-start gap-4">
                  <JobIcon type={i} size={52} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h2 className="text-[22px] font-semibold leading-tight">{jt.name}</h2>
                      <Chip>{jt.id}</Chip>
                    </div>
                    <div className="mt-1 text-[13px] text-muted">
                      {jt.model} · {jt.service.what}
                    </div>
                  </div>
                  <ArrowBadge />
                </div>
                <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <Stat k="One job" v={`${jt.units / 2} server-h`} s={jt.detail} />
                  <Stat k="Deadline" v={`${jt.due_h} h`} s={`checkpoint ${jt.service.checkpoint}`} />
                  <Stat
                    k="Sold, 2025"
                    v={`${nf(st.admitted_server_h / 1000)}k server-h`}
                    s={`${Math.round((st.admitted_server_h / totalH) * 100)}% of fleet work`}
                  />
                  <Stat
                    k="Cost floor"
                    v={`${nf(perUnit(jt, m.priceNeeded), perUnit(jt, m.priceNeeded) < 1 ? 3 : 2)} CHF`}
                    s={`per ${u.label} · list ${nf(listPerUnit(jt, "low"), 2)}–${nf(listPerUnit(jt, "high"), 2)}`}
                  />
                </div>
              </Card>
            </Link>
          );
        })}
      </div>

      <Card className="mt-4">
        <CardTitle right={<Chip tone="teal">measured</Chip>}>
          <span className="flex items-center gap-2">
            <FlaskConical size={18} /> Running on our own machines
          </span>
        </CardTitle>
        <p className="mt-1 text-[13px] text-muted">
          Two real, interruptible jobs measured on three team laptops (Apple M1, M3, M4) and scaled to the 1 kW reference
          server. Not scheduled in the fleet scenario. Code in <code>workloads/</code>, method in docs/workloads.md.
        </p>
        <table className="mt-4 w-full text-[13px]">
          <thead className="text-faint">
            <tr>
              <th className="pb-2 text-left font-medium">Job</th>
              <th className="pb-2 text-left font-medium">One item</th>
              <th className="pb-2 text-right font-medium">Laptop</th>
              <th className="pb-2 text-right font-medium">Energy / item</th>
              <th className="pb-2 text-right font-medium">Per server-h</th>
              <th className="pb-2 text-right font-medium">One job</th>
              <th className="pb-2 text-right font-medium">Deadline</th>
            </tr>
          </thead>
          <tbody>
            {fleet.meta.measured_jobs.map((j) => (
              <tr key={j.id} className="border-t border-line/70">
                <td className="py-2">
                  <div className="font-semibold">{j.name}</div>
                  <div className="text-[12px] text-muted">{j.model}</div>
                </td>
                <td className="py-2 text-muted">{j.item}</td>
                <td className="py-2 text-right tabular-nums">
                  {j.items_per_s[0]}–{j.items_per_s[1]} /s
                </td>
                <td className="py-2 text-right tabular-nums">{j.j_per_item.toFixed(3)} J</td>
                <td className="py-2 text-right tabular-nums">{nf(j.items_per_server_h / 1e6, 1)} M</td>
                <td className="py-2 text-right tabular-nums">
                  {nf(j.items_per_job / 1e6)} M = {j.server_h_per_job} server-h
                </td>
                <td className="py-2 text-right tabular-nums">{j.due_h} h</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function Stat({ k, v, s }: { k: string; v: string; s: string }) {
  return (
    <div>
      <div className="text-[11.5px] uppercase tracking-[0.08em] text-faint">{k}</div>
      <div className="mt-1 text-[17px] font-semibold tabular-nums">{v}</div>
      <div className="mt-0.5 text-[12px] text-muted">{s}</div>
    </div>
  );
}
