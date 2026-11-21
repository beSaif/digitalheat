"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { ArrowUpRight } from "lucide-react";
import { Card, Loading } from "@/components/ui";

type Row = { kind: "case" | "measured" | "sourced" | "ours"; name: string; value: string; source: string; url: string | null; file: string | null };

const TABS = [
  { k: "case", l: "Given" },
  { k: "measured", l: "Measured" },
  { k: "sourced", l: "Sourced" },
  { k: "ours", l: "Our choice" },
] as const;

export default function Assumptions() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [tab, setTab] = useState<Row["kind"]>("case");
  useEffect(() => {
    fetch("/api/assumptions")
      .then((r) => r.json())
      .then((d) => Array.isArray(d) && setRows(d));
  }, []);
  if (!rows) return <Loading />;

  return (
    <div className="h-full overflow-auto p-6 scroll-thin">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-display text-[40px] font-semibold leading-none">Assumptions</h1>
        <div className="flex gap-1 rounded-full bg-card p-1 ring-1 ring-line/70">
          {TABS.map((t) => (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              className={clsx("rounded-full px-3 py-1.5 text-[13px] font-semibold", tab === t.k ? "bg-ink text-cream" : "hover:bg-paper")}
            >
              {t.l} <span className="opacity-50">{rows.filter((r) => r.kind === t.k).length}</span>
            </button>
          ))}
        </div>
      </div>

      <Card className="mt-6">
        <table className="w-full text-[14px]">
          <tbody>
            {rows
              .filter((r) => r.kind === tab)
              .map((r) => (
                <tr key={r.name} className="border-t border-line/70 first:border-0">
                  <td className="w-[28%] py-3 pr-4 font-semibold">{r.name}</td>
                  <td className="w-[30%] pr-4 tabular-nums">{r.value}</td>
                  <td className="text-muted">
                    {r.url ? (
                      <a href={r.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-ink">
                        {r.source} <ArrowUpRight size={12} />
                      </a>
                    ) : (
                      r.source
                    )}
                    {r.file && <div className="font-mono text-[11px] opacity-70">{r.file}</div>}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </Card>
      <p className="mt-4 text-[13px] text-muted">
        Same list in the repo: <span className="font-mono">docs/assumptions.md</span>
      </p>
    </div>
  );
}
