"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

/*
 * "How we computed this": every assumption with its value and source, on the live room screen.
 * The rows come from public/assumptions.json (made by scripts/build_sim2.py, now on the archive/simulation2
 * branch); pass them in, or let the dialog fetch them.
 */

export type Assumption = { label: string; value: string; source: string };

export function useAssumptions(rows?: Assumption[]) {
  const [fetched, setFetched] = useState<Assumption[] | null>(null);
  useEffect(() => {
    if (rows) return;
    let live = true;
    fetch("/assumptions.json")
      .then((r) => r.json())
      .then((d) => live && setFetched(Array.isArray(d) ? d : []))
      .catch(() => live && setFetched([]));
    return () => {
      live = false;
    };
  }, [rows]);
  return rows ?? fetched;
}

export default function SourcesDialog({ rows, onClose, note }: { rows?: Assumption[]; onClose: () => void; note?: string }) {
  const list = useAssumptions(rows);
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return (
    <div className="pointer-events-auto fixed inset-0 z-[2000] grid place-items-center bg-ink/25 p-6 backdrop-blur-[2px]" onClick={onClose}>
      <div className="flex max-h-[80vh] w-[760px] max-w-full flex-col rounded-[20px] border border-line/60 bg-white text-ink shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between px-7 pt-6">
          <div>
            <div className="text-[13px] text-muted">{note ?? "Every number comes from the Python scheduler"}</div>
            <h2 className="font-display text-[24px] font-semibold">How we computed this</h2>
          </div>
          <button onClick={onClose} aria-label="Close" className="grid h-9 w-9 place-items-center rounded-full bg-cream hover:bg-line">
            <X size={16} />
          </button>
        </div>
        <div className="scroll-thin min-h-0 flex-1 overflow-y-auto px-7 pb-7 pt-4">
          {list === null ? (
            <div className="py-6 text-[14px] text-muted">Loading…</div>
          ) : (
            <table className="w-full text-[13.5px]">
              <tbody>
                {list.map((a) => (
                  <tr key={a.label} className="border-t border-line/70 align-top">
                    <td className="py-2 pr-4 text-ink-2">{a.label}</td>
                    <td className="py-2 pr-4 font-semibold tabular-nums">{a.value}</td>
                    <td className="py-2 text-muted">{a.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
