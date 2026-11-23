"use client";

import clsx from "clsx";
/* Shared building blocks of the floating cards on the live room screen: white, rounded, one soft layered shadow. */

/* number formatting, Swiss style: 12'400 */
const fmt = (n: number, d = 0) =>
  n.toLocaleString("de-CH", { minimumFractionDigits: d, maximumFractionDigits: d }).replace(/’/g, "'");

export const GOOD = "#2f7a5c";
export const BAD = "#c62f2f";

export function Card({ className, children, style }: { className?: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div className={clsx("rise pointer-events-auto rounded-[20px] border border-line/60 bg-white shadow-pill", className)} style={style}>
      {children}
    </div>
  );
}

export function Pill({ className, children, onClick, active, title }: { className?: string; children: React.ReactNode; onClick?: () => void; active?: boolean; title?: string }) {
  return (
    <button
      title={title}
      onClick={onClick}
      className={clsx(
        "rise pointer-events-auto flex items-center gap-2 rounded-full border border-line/60 bg-white px-5 py-3 text-[15px] shadow-pill transition-colors hover:bg-cream",
        active && "font-semibold",
        className,
      )}
    >
      {children}
    </button>
  );
}

/** Switch like Vampère's "Show proposed measures" toggle. */
export function Switch({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label?: string }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      aria-label={label}
      onClick={(e) => {
        e.stopPropagation();
        onChange(!on);
      }}
      className={clsx("relative h-7 w-12 shrink-0 rounded-full transition-colors", on ? "bg-[#2f7a5c]" : "bg-line")}
    >
      <span className={clsx("absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-all", on ? "left-[22px]" : "left-0.5")} />
    </button>
  );
}

/** Segmented control (Local grid | Market-based style). */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  disabled,
}: {
  value: T;
  options: { v: T; label: React.ReactNode }[];
  onChange: (v: T) => void;
  disabled?: boolean;
}) {
  return (
    <div className="inline-flex rounded-full bg-cream p-1">
      {options.map((o) => (
        <button
          key={o.v}
          disabled={disabled}
          onClick={() => onChange(o.v)}
          className={clsx(
            "rounded-full px-3.5 py-1.5 text-[13.5px] transition-all disabled:opacity-60",
            value === o.v ? "bg-white font-semibold shadow-pill" : "text-muted hover:text-ink",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Change in %, green when it goes the good way. lower = lower values are better. */
export function Delta({ before, after, lower = true, className }: { before: number; after: number; lower?: boolean; className?: string }) {
  if (Math.abs(after - before) < 1e-9) return null;
  if (!before) {
    // from nothing: a percentage means nothing, say it is new
    const good = lower ? after < 0 : after > 0;
    return (
      <span className={clsx("text-[13px] font-semibold", className)} style={{ color: good ? GOOD : BAD }}>
        new
      </span>
    );
  }
  const d = (after - before) / Math.abs(before);
  if (Math.abs(d) < 0.005) return null;
  const good = lower ? d < 0 : d > 0;
  return (
    <span className={clsx("text-[13px] font-semibold tabular-nums", className)} style={{ color: good ? GOOD : BAD }}>
      {d > 0 ? "+" : "−"}
      {fmt(Math.abs(d) * 100)}%
    </span>
  );
}

export function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div>
      <div className="text-[13px] text-muted">{label}</div>
      <div className="mt-0.5 flex items-baseline gap-1.5 text-[21px] font-semibold leading-tight tabular-nums">
        {value}
        {sub}
      </div>
    </div>
  );
}

export type ChipTone = "plain" | "good" | "warn" | "bad" | "info" | "rust";

export function Chip({
  children,
  tone = "plain",
  size = "md",
  className,
  title,
}: {
  children: React.ReactNode;
  tone?: ChipTone;
  /** sm: for list rows (less padding, same 12.5 px text) */
  size?: "md" | "sm";
  className?: string;
  title?: string;
}) {
  const t = {
    plain: "bg-cream text-ink-2",
    good: "bg-[#e6f1ea] text-[#2f7a5c]",
    warn: "bg-[#fbeee0] text-[#a85a12]",
    bad: "bg-[#f8e3df] text-[#b2402e]",
    info: "bg-teal-soft text-[#2f6f77]",
    rust: "bg-amber-soft text-rust-deep",
  }[tone];
  return (
    <span title={title} className={clsx("inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full font-medium", size === "sm" ? "px-2 py-0.5 text-[12.5px]" : "px-2.5 py-1 text-[12.5px]", t, className)}>
      {children}
    </span>
  );
}

export function Swatch({ color }: { color: string }) {
  return <span className="inline-block h-3 w-3 shrink-0 rounded-[3px]" style={{ background: color }} />;
}
