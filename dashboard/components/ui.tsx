import clsx from "clsx";
import { ArrowUpRight, AudioLines, Cpu } from "lucide-react";

export function Card({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement> & { className?: string }) {
  return (
    <div className={clsx("rounded-[24px] bg-card p-5 ring-1 ring-line/70", className)} {...rest}>
      {children}
    </div>
  );
}

export function CardTitle({ children, right }: { children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <h3 className="text-[17px] font-semibold tracking-tight">{children}</h3>
      {right}
    </div>
  );
}

export function ArrowBadge({ dark = false }: { dark?: boolean }) {
  return (
    <span
      className={clsx(
        "grid size-9 place-items-center rounded-full",
        dark ? "bg-cream text-ink" : "ring-1 ring-ink/70 text-ink",
      )}
    >
      <ArrowUpRight size={17} />
    </span>
  );
}

export function Unit({ children }: { children: React.ReactNode }) {
  return <span className="ml-1 text-[0.42em] font-medium tracking-normal opacity-60">{children}</span>;
}

export function Chip({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "ink" | "amber" | "teal" | "rust" | "hatch";
  children: React.ReactNode;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-md px-1.5 py-0.5 text-[11px] font-medium",
        tone === "neutral" && "bg-paper text-muted ring-1 ring-line",
        tone === "ink" && "bg-ink text-cream",
        tone === "amber" && "bg-amber-soft text-rust-deep",
        tone === "teal" && "bg-teal-soft text-[#2f6e75]",
        tone === "rust" && "bg-rust text-cream",
        tone === "hatch" && "hatch bg-paper text-ink-2 ring-1 ring-line",
      )}
    >
      {children}
    </span>
  );
}

export function JobIcon({ type, size = 34 }: { type: number; size?: number }) {
  return (
    <span
      className={clsx(
        "grid shrink-0 place-items-center rounded-xl",
        type === 0 ? "bg-teal-soft text-[#2f6e75]" : "bg-amber-soft text-rust-deep",
      )}
      style={{ width: size, height: size }}
    >
      {type === 0 ? <AudioLines size={size * 0.5} /> : <Cpu size={size * 0.5} />}
    </span>
  );
}

export function Loading() {
  return (
    <div className="grid h-full place-items-center text-[14px] text-muted">
      <div className="flex items-center gap-3">
        <span className="size-2 animate-pulse rounded-full bg-rust" /> Loading the fleet replay…
      </div>
    </div>
  );
}

export const STATE_LABEL = {
  running: { label: "Running", tone: "ink" as const },
  throttled: { label: "Throttled · tank full", tone: "amber" as const },
  "idle-heat": { label: "Idle · no heat", tone: "hatch" as const },
  "idle-work": { label: "Idle · no work", tone: "neutral" as const },
};

export function PayChip({ ok }: { ok: boolean }) {
  return (
    <span className={clsx("rounded-full px-2 py-0.5 text-[12px] font-semibold", ok ? "bg-[#dcebe9] text-[#2f6e75]" : "bg-amber-soft text-rust-deep")}>
      {ok ? "Pays off" : "Loses money"}
    </span>
  );
}
