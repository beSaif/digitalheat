"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import clsx from "clsx";
import {
  Bell,
  BookOpen,
  Building2,
  ChevronLeft,
  ChevronRight,
  Flame,
  LayoutGrid,
  Map as MapIcon,
  Pause,
  Play,
  Search,
  Thermometer,
  X,
  Coins,
  ListChecks,
  Presentation,
  Wallet,
} from "lucide-react";
import { Logo } from "./Logo";
import { useFleet } from "@/lib/store";
import { YEARS, cityTemp, fmtDate, fmtTime, siteNow } from "@/lib/data";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutGrid, match: (p: string) => p === "/" },
  { href: "/replay", label: "Swiss replay", icon: Flame, match: (p: string) => p.startsWith("/replay") },
  { href: "/money", label: "Money", icon: Coins, match: (p: string) => p.startsWith("/money") },
  { href: "/finance", label: "Finance", icon: Wallet, match: (p: string) => p.startsWith("/finance") },
  { href: "/assumptions", label: "Assumptions", icon: ListChecks, match: (p: string) => p.startsWith("/assumptions") },
  { href: "/map", label: "Fleet map", icon: MapIcon, match: (p: string) => p.startsWith("/map") },
  { href: "/sites/BS-01", label: "Sites", icon: Building2, match: (p: string) => p.startsWith("/sites") },
  { href: "/pitch", label: "Pitch", icon: Presentation, match: (p: string) => p.startsWith("/pitch") },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const [method, setMethod] = useState(false);
  const path = usePathname();
  // the pitch is a full-screen presentation: no console chrome around it
  if (path.startsWith("/pitch")) return <>{children}</>;
  return (
    <div className="flex h-dvh gap-3 p-3">
      <Suspense fallback={<aside className="hidden w-[232px] shrink-0 rounded-[28px] bg-cream lg:block" />}>
        <Sidebar onMethod={() => setMethod(true)} />
      </Suspense>
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <Suspense fallback={<header className="h-[76px] shrink-0 rounded-[28px] bg-cream" />}>
          <Topbar />
        </Suspense>
        <main className="min-h-0 flex-1 overflow-hidden rounded-[28px] bg-cream">
          <Suspense>{children}</Suspense>
        </main>
      </div>
      {method && <MethodDialog onClose={() => setMethod(false)} />}
    </div>
  );
}

function Sidebar({ onMethod }: { onMethod: () => void }) {
  const path = usePathname();
  const { fleet } = useFleet();
  return (
    <aside className="hidden w-[232px] shrink-0 flex-col rounded-[28px] bg-cream px-5 py-6 lg:flex">
      <Logo />
      <div className="mt-10 text-[11px] font-medium uppercase tracking-[0.14em] text-faint">Menu</div>
      <nav className="mt-3 flex flex-col gap-1">
        {NAV.map((n) => {
          const active = n.match(path);
          return (
            <Link
              key={n.href}
              href={n.href}
              className={clsx(
                "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] transition-colors",
                active ? "font-semibold text-ink" : "text-muted hover:bg-paper/60 hover:text-ink",
              )}
            >
              {active && <span className="absolute -left-5 top-1.5 h-[calc(100%-12px)] w-1 rounded-r bg-rust" />}
              <n.icon size={19} strokeWidth={active ? 2.4 : 1.8} className={active ? "text-rust" : ""} />
              {n.label}
              {n.label === "Sites" && fleet && (
                <span className="ml-auto rounded-md bg-ink px-1.5 py-0.5 text-[10px] font-semibold text-cream">
                  {fleet.sites.length}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="mt-8 text-[11px] font-medium uppercase tracking-[0.14em] text-faint">General</div>
      <button
        onClick={onMethod}
        className="mt-3 flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[15px] text-muted hover:bg-paper/60 hover:text-ink"
      >
        <BookOpen size={19} strokeWidth={1.8} /> Method & data
      </button>

      <div className="grain relative mt-auto overflow-hidden rounded-2xl p-4 text-cream">
        <div className="text-[11px] uppercase tracking-[0.14em] text-amber">Scenario replay</div>
        <div className="mt-2 font-display text-[19px] font-semibold leading-tight">{fleet?.meta.year ?? 2025} weather, simulated fleet</div>
        <p className="mt-1.5 text-[12px] leading-snug text-cream/65">
          Not live telemetry. Every number comes from one seeded run.
        </p>
        <button
          onClick={onMethod}
          className="mt-4 w-full rounded-full bg-cream py-2 text-[13px] font-semibold text-ink hover:bg-amber"
        >
          How it&apos;s built
        </button>
      </div>
    </aside>
  );
}

function Topbar() {
  const { fleet, t, setT, playing, setPlaying, speed, setSpeed, year, setYear, yearLoading } = useFleet();
  const [q, setQ] = useState("");
  const router = useRouter();
  const matches = useMemo(() => {
    if (!fleet || !q.trim()) return [];
    const s = q.toLowerCase();
    return fleet.sites
      .filter((x) => `${x.id} ${x.city} ${x.district} ${x.canton}`.toLowerCase().includes(s))
      .slice(0, 6);
  }, [fleet, q]);

  const alerts = useMemo(() => {
    if (!fleet) return 0;
    return fleet.sites.filter((_, i) => siteNow(fleet, i, t).state === "throttled").length;
  }, [fleet, t]);

  return (
    <header className="flex h-[76px] shrink-0 items-center gap-4 rounded-[28px] bg-cream px-5">
      <div className="relative w-[340px]">
        <div className="flex items-center gap-2.5 rounded-full bg-card px-4 py-2.5 ring-1 ring-line">
          <Search size={18} className="text-muted" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search site, city or canton"
            className="w-full bg-transparent text-[14px] outline-none placeholder:text-faint"
          />
          <kbd className="rounded-md bg-paper px-1.5 py-0.5 text-[11px] text-muted">⌘K</kbd>
        </div>
        {matches.length > 0 && (
          <div className="absolute left-0 right-0 top-[52px] z-50 overflow-hidden rounded-2xl bg-card shadow-xl ring-1 ring-line">
            {matches.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setQ("");
                  router.push(`/sites/${s.id}`);
                }}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-[14px] hover:bg-paper/60"
              >
                <span className="w-12 font-semibold">{s.id}</span>
                <span className="text-muted">
                  {s.city} · {s.district}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* one clock drives every screen */}
      <div className="ml-auto flex items-center gap-1 rounded-full bg-ink py-1.5 pl-4 pr-1.5 text-cream">
        <label className="relative mr-3 flex items-center gap-1 rounded-full bg-white/10 py-1.5 pl-3 pr-2 text-[14px] font-semibold hover:bg-white/15">
          <span className="sr-only">Weather year</span>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="cursor-pointer appearance-none bg-transparent pr-4 outline-none"
            title="Weather year"
          >
            {YEARS.map((y) => (
              <option key={y} value={y} className="text-ink">
                {y}
              </option>
            ))}
          </select>
          <ChevronRight size={13} className="pointer-events-none absolute right-2 rotate-90 text-cream/70" />
          {yearLoading && <span className="ml-1 size-2 animate-pulse rounded-full bg-amber" title="Loading this year" />}
        </label>
        <div className="mr-2 leading-tight">
          <div className="text-[10px] uppercase tracking-[0.14em] text-amber">Replay</div>
          <div className="text-[14px] font-semibold tabular-nums" suppressHydrationWarning>
            {fmtDate(t)} · {fmtTime(t)}
          </div>
        </div>
        {fleet && (
          <div className="mr-2 flex items-center gap-1 text-[12px] text-cream/70">
            <Thermometer size={14} /> Basel {cityTemp(fleet, "Basel", t).toFixed(1)}°C
          </div>
        )}
        <ClockBtn label="Back 1 h" onClick={() => setT((x) => x - 1)}>
          <ChevronLeft size={16} />
        </ClockBtn>
        <button
          aria-label={playing ? "Pause" : "Play"}
          onClick={() => setPlaying(!playing)}
          className="grid size-9 place-items-center rounded-full bg-amber text-ink hover:bg-cream"
        >
          {playing ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
        </button>
        <ClockBtn label="Forward 1 h" onClick={() => setT((x) => x + 1)}>
          <ChevronRight size={16} />
        </ClockBtn>
        <button
          onClick={() => setSpeed(speed === 1 ? 4 : speed === 4 ? 24 : 1)}
          className="ml-0.5 h-9 rounded-full px-2.5 text-[12px] font-semibold text-cream/80 hover:bg-white/10"
          title="Simulated hours per second"
        >
          {speed}h/s
        </button>
      </div>

      <button className="relative grid size-11 place-items-center rounded-full bg-card ring-1 ring-line" aria-label="Alerts">
        <Bell size={18} />
        {alerts > 0 && (
          <span className="absolute -right-0.5 -top-0.5 grid size-5 place-items-center rounded-full bg-rust text-[10px] font-semibold text-cream">
            {alerts}
          </span>
        )}
      </button>
      <div className="flex items-center gap-3">
        <div className="grid size-11 place-items-center rounded-full bg-amber-soft font-display text-[15px] font-semibold text-rust-deep">
          OP
        </div>
        <div className="hidden leading-tight xl:block">
          <div className="text-[14px] font-semibold">Fleet operator</div>
          <div className="text-[12px] text-muted">Scheduler on duty</div>
        </div>
      </div>
    </header>
  );
}

function ClockBtn({ children, onClick, label }: { children: React.ReactNode; onClick: () => void; label: string }) {
  return (
    <button aria-label={label} onClick={onClick} className="grid size-9 place-items-center rounded-full text-cream/80 hover:bg-white/10">
      {children}
    </button>
  );
}

function MethodDialog({ onClose }: { onClose: () => void }) {
  const { fleet } = useFleet();
  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-ink/40 p-6 backdrop-blur-sm" onClick={onClose}>
      <div
        className="relative max-h-[86vh] w-full max-w-[640px] overflow-auto rounded-[28px] bg-cream p-8 scroll-thin"
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute right-5 top-5 grid size-9 place-items-center rounded-full bg-card ring-1 ring-line" aria-label="Close">
          <X size={16} />
        </button>
        <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.14em] text-rust">
          <span className="h-px w-8 bg-rust" /> Method & data
        </div>
        <h2 className="mt-3 font-display text-[28px] font-semibold leading-tight">A scenario fleet, replayed hour by hour</h2>
        <div className="mt-5 space-y-3 text-[14px] leading-relaxed text-ink-2">
          <p>
            <b>Overview.</b> House (4 servers), hospital (15) and spa (11) in Basel, 2025 weather. Scheduler:{" "}
            <code>scheduler/core.py</code>.
          </p>
          <p>
            <b>Houses.</b> 24 houses in 10 Swiss cities. Each one is the case&apos;s reference house scaled ×0.6–1.5 and driven
            by its own city&apos;s 2025 hourly temperature (Open-Meteo archive). BS-01 is the reference house itself: 6 servers,
            35 kWh tank, Basel weather.
          </p>
          <p>
            <b>Heat permit.</b> Each hour, the scheduler allows only as many 1 kW servers as the house&apos;s heat demand plus
            free tank space can absorb (80% of the power is recovered as heat). Nothing is ever dumped.
          </p>
          <p>
            <b>Jobs.</b> J1 transcription (0.5 server-h, due in 24 h) and J2 LLM batch (4 server-h, due in 168 h), offered
            each day in proportion to the house&apos;s permit-hours. That is a contract sized to the house, not a customer we
            found. Admission is an earliest-deadline-first dry run against the permit plan with a perfect forecast. Work it
            cannot heat-match is refused at intake, with the reason.
          </p>
          <p className="rounded-2xl bg-card p-4 font-mono text-[12.5px] ring-1 ring-line">
            python3 scripts/build_fleet_scenario.py
            <br />
            seed {fleet?.meta.seed ?? 11} · outputs dashboard/public/data/
          </p>
          <p className="text-muted">
            Not live telemetry and not measured data. Cities outside Basel use the same building model with different
            weather. Times are UTC+1 all year. Map tiles © OpenFreeMap, © OpenStreetMap contributors. Canton outlines:
            Code for Germany, click_that_hood.
          </p>
        </div>
      </div>
    </div>
  );
}
