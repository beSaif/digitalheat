"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useFleet } from "@/lib/store";
import { Finance } from "@/components/Finance";
import { CLOUD, COSTS } from "@/lib/finance";

export default function FinancePage() {
  const { year } = useFleet();
  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <h1 className="font-display text-[40px] font-semibold leading-none">When does it pay back?</h1>
      <p className="mt-2 text-[14px] text-muted">Reference house, Basel, {year} weather.</p>
      <div className="mt-6">
        <Finance year={year} />
      </div>

      <details className="mt-4 rounded-[24px] bg-card p-5 text-[13px] ring-1 ring-line/70">
        <summary className="cursor-pointer text-[15px] font-semibold">Where the numbers come from</summary>
        <table className="mt-3 w-full">
          <tbody>
            {Object.values(COSTS).map((c) => (
              <tr key={c.label} className="border-t border-line/70">
                <td className="py-2 font-semibold">{c.label}</td>
                <td className="tabular-nums">
                  {c.v.toLocaleString("de-CH")} {c.unit}
                </td>
                <td className="text-muted">{c.src}</td>
              </tr>
            ))}
            {CLOUD.map((c) => (
              <tr key={c.id} className="border-t border-line/70">
                <td className="py-2 font-semibold">{c.name}</td>
                <td className="tabular-nums">USD {c.usd.toFixed(2)} / h</td>
                <td className="text-muted">{c.src}</td>
              </tr>
            ))}
            <tr className="border-t border-line/70">
              <td className="py-2 font-semibold">Server-hours, electricity, heat</td>
              <td>scheduler</td>
              <td className="text-muted">python -m scheduler.balance · CHF 0.3325 / kWh (ElCom 2026) · heat at price ÷ 2.5</td>
            </tr>
          </tbody>
        </table>
      </details>

      <Link href="/assumptions" className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-semibold text-muted hover:text-ink">
        All assumptions <ArrowRight size={13} />
      </Link>
    </div>
  );
}
