"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import {
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Clapperboard,
  Flame,
  FlaskConical,
  Maximize,
  Play,
  Receipt,
  Search,
  Sprout,
  Thermometer,
  Waves,
  Coins,
  StickyNote,
  ScrollText,
} from "lucide-react";
import { LogoMark } from "@/components/Logo";
import type { Schedule, SiteIn } from "@/lib/schedule";
import { Finance } from "@/components/Finance";

/*
 * The pitch: a full-screen, keyboard-driven story told with the real scheduler and the real job.
 * Every number on these slides comes from /api/schedule (python -m scheduler.balance) for the reference house.
 * ← → / space / PageUp-Down move, N shows speaker notes, F goes full screen.
 */

const SERVERS = 11; // servers in the reference house's basement (python3 -m scheduler.balance --servers 11)
const HOUSE: SiteIn[] = [{ id: "BS-01", kind: "house", name: "Reference house", lat: 47.5695, lon: 7.588, servers: SERVERS }];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const dayLabel = (d: number) => {
  const x = new Date(Date.UTC(2025, 0, 1 + d));
  return `${x.getUTCDate()} ${MONTHS[x.getUTCMonth()]}`;
};
const pct = (x: number, d = 0) => `${(x * 100).toFixed(d)}%`;
const kwh = (x: number) => `${Math.round(x).toLocaleString("de-CH")} kWh`;

import { SLIDES } from "./slides";

export default function Pitch() {
  const data = useHouse();
  const box = useRef<HTMLDivElement>(null);
  const [cur, setCur] = useState(0);
  const [notes, setNotes] = useState(false);
  const [revealed, setRevealed] = useState(false); // the hook's answer, shown on the first "next"
  const [progress, setProgress] = useState(0);

  const go = useCallback((i: number) => {
    const n = Math.max(0, Math.min(SLIDES.length - 1, i));
    document.getElementById(SLIDES[n].id)?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (es) =>
        es.forEach((e) => {
          if (!e.isIntersecting) return;
          e.target.setAttribute("data-in", ""); // content rises in (pitch.css)
          setCur(SLIDES.findIndex((s) => s.id === e.target.id));
        }),
      { root: el, threshold: 0.55 },
    );
    SLIDES.forEach((s) => {
      const x = document.getElementById(s.id);
      if (x) io.observe(x);
    });
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      if (["ArrowRight", "ArrowDown", "PageDown", " "].includes(e.key)) {
        e.preventDefault();
        if (cur === 0 && !revealed) setRevealed(true);
        else go(cur + 1);
      } else if (["ArrowLeft", "ArrowUp", "PageUp"].includes(e.key)) {
        e.preventDefault();
        go(cur - 1);
      } else if (e.key === "n" || e.key === "N") setNotes((v) => !v);
      else if (e.key === "f" || e.key === "F") fullscreen();
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [cur, go, revealed]);

  return (
    <div
      ref={box}
      onScroll={(e) => {
        const el = e.currentTarget;
        setProgress(el.scrollTop / Math.max(1, el.scrollHeight - el.clientHeight));
      }}
      className="cosy fixed inset-0 snap-y snap-mandatory overflow-y-auto bg-paper text-ink"
    >
      <div className="scarf-bar fixed left-0 top-0 z-30 h-2" style={{ width: `${progress * 100}%` }} />
      <Hook revealed={revealed} reveal={() => setRevealed(true)} />
      <Problems />
      <Figures data={data} />
      <Console />
      <Industry />
      <Services />
      <Money />
      <Close data={data} />

      {/* chapter rail */}
      <nav className="fixed right-4 top-1/2 z-20 hidden -translate-y-1/2 flex-col items-end gap-2 md:flex">
        {SLIDES.map((s, i) => (
          <button key={s.id} onClick={() => go(i)} className="group flex items-center gap-2" aria-label={s.label}>
            <span className={clsx("text-[11px] font-semibold opacity-0 transition-opacity group-hover:opacity-100", i === cur ? "text-rust" : "text-muted")}>{s.label}</span>
            <span className={clsx("h-2 rounded-full transition-all", i === cur ? "w-6 bg-rust" : "w-2 bg-ink/25 group-hover:bg-ink/50")} />
          </button>
        ))}
      </nav>

      <div className="sticker-sm fixed bottom-4 left-4 z-20 flex items-center gap-1 rounded-full bg-card p-1">
        <IconBtn onClick={() => go(cur - 1)} label="Previous"><ChevronUp size={16} /></IconBtn>
        <span className="px-1 text-[12px] font-semibold tabular-nums text-muted">{cur + 1} / {SLIDES.length}</span>
        <IconBtn onClick={() => go(cur + 1)} label="Next"><ChevronDown size={16} /></IconBtn>
        <IconBtn onClick={() => setNotes(!notes)} label="Speaker notes (N)" active={notes}><StickyNote size={15} /></IconBtn>
        <IconBtn onClick={fullscreen} label="Full screen (F)"><Maximize size={15} /></IconBtn>
        <IconBtn onClick={() => window.open("/pitch/script", "_blank")} label="Script (opens in a new tab)"><ScrollText size={15} /></IconBtn>
      </div>

      {notes && (
        <div className="sticker fixed bottom-16 left-4 z-20 max-w-[440px] rounded-[22px] bg-ink p-4 text-[14px] leading-relaxed text-cream">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-amber">Notes · {SLIDES[cur].label}</div>
          {SLIDES[cur].note}
        </div>
      )}
    </div>
  );
}

function fullscreen() {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen?.();
}

function IconBtn({ onClick, label, active, children }: { onClick: () => void; label: string; active?: boolean; children: React.ReactNode }) {
  return (
    <button onClick={onClick} title={label} aria-label={label} className={clsx("grid size-8 place-items-center rounded-full", active ? "bg-rust text-ink" : "hover:bg-amber-soft")}>
      {children}
    </button>
  );
}

function Slide({ id, dark, children, className, bridge = true }: { id: string; dark?: boolean; children: React.ReactNode; className?: string; bridge?: boolean }) {
  const i = SLIDES.findIndex((x) => x.id === id);
  const text = SLIDES[i]?.bridge;
  return (
    <section id={id} className={clsx("relative flex min-h-dvh snap-start flex-col px-5 pb-24 pt-10 md:px-14 md:pt-12", dark ? "grain text-cream" : "bg-paper")}>
      <div className={clsx("flex flex-1 flex-col", className)}>{children}</div>
      {/* the bridge: the question the next slide answers */}
      {text && bridge && (
        <button
          onClick={() => document.getElementById(SLIDES[i + 1].id)?.scrollIntoView({ behavior: "smooth" })}
          className={clsx("press absolute bottom-6 right-14 flex items-center gap-2 rounded-full px-5 py-2 text-right font-display text-[18px] font-semibold md:text-[22px]", dark ? "bg-card text-amber" : "bg-card text-rust-deep")}
        >
          {text} <ArrowRight size={20} />
        </button>
      )}
    </section>
  );
}

function Kicker({ children }: { children: React.ReactNode; dark?: boolean }) {
  return (
    <div>
      <span className="kicker">{children}</span>
    </div>
  );
}

function Waiting({ dark }: { dark?: boolean }) {
  return (
    <div className={clsx("flex items-center gap-3 text-[14px]", dark ? "text-cream/60" : "text-muted")}>
      <span className="size-2 animate-pulse rounded-full bg-rust" /> Running the scheduler for 2025…
    </div>
  );
}

/* ---------- data ---------- */

type Day = { demand: number; running: number; soc: number; served: number; dumped: number; paused: number };

function useHouse() {
  const [s, setS] = useState<Schedule | null>(null);
  useEffect(() => {
    fetch("/api/schedule", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ year: 2025, sites: HOUSE }) })
      .then((r) => (r.ok ? r.json() : null))
      .then(setS)
      .catch(() => {});
  }, []);
  return useMemo(() => {
    if (!s) return null;
    const x = s.series[0];
    const hour = (t: number): Day => ({ demand: x.demand[t], running: x.running[t], soc: x.soc[t], served: x.served[t], dumped: x.dumped[t], paused: x.paused[t] });
    const days: Day[] = [];
    for (let d = 0; d < 365; d++) {
      const a: Day = { demand: 0, running: 0, soc: 0, served: 0, dumped: 0, paused: 0 };
      for (let h = 0; h < 24; h++) {
        const v = hour(d * 24 + h);
        a.demand += v.demand / 24;
        a.running += v.running / 24;
        a.soc += v.soc / 24;
        a.served += v.served / 24;
        a.dumped += v.dumped;
        a.paused += v.paused;
      }
      days.push(a);
    }
    return { s, site: s.sites[0], y: s.sites[0].year, hour, days };
  }, [s]);
}
type House = NonNullable<ReturnType<typeof useHouse>>;

/* ---------- the house, in cross-section ---------- */

function HouseXray({ v, servers, tank, cold, dark }: { v: Day; servers: number; tank: number; cold: boolean; dark?: boolean }) {
  const on = Math.round(v.running);
  const warm = Math.min(1, v.served / Math.max(v.demand, 0.01));
  const fill = Math.max(0, Math.min(1, v.soc / tank));
  const wall = "var(--dh-card)";
  const edge = "var(--dh-line)";
  // servers share the basement left of the tank (x 70–258), however many there are
  const pitch = Math.min(40, 188 / Math.max(1, servers));
  const w = pitch * 0.8;
  return (
    <svg viewBox="0 0 420 380" className="h-full w-full" role="img" aria-label="House cross-section">
      <g opacity={0.9}>
        {cold ? (
          [40, 110, 330, 380, 70, 360].map((x, i) => (
            <text key={i} x={x} y={30 + (i % 3) * 28} fontSize="16" fill={dark ? "var(--dh-cream)" : "var(--dh-faint)"} opacity={0.5}>✳</text>
          ))
        ) : (
          <circle cx="370" cy="40" r="18" fill="var(--dh-amber)" opacity={0.85} />
        )}
      </g>
      <path d="M30 152 L210 46 L390 152 Z" fill="var(--dh-rust)" stroke="var(--bd)" strokeWidth="4" strokeLinejoin="round" />
      <rect x="60" y="152" width="300" height="148" rx="8" fill={wall} stroke="var(--bd)" strokeWidth="4" />
      {/* window, warm when the room is warm */}
      <rect x="250" y="180" width="70" height="56" rx="4" fill="var(--dh-amber)" opacity={0.15 + 0.55 * warm} />
      <path d="M285 180 V236 M250 208 H320" stroke={wall} strokeWidth="4" />
      {/* radiator and rising heat */}
      {Array.from({ length: 7 }, (_, i) => (
        <rect key={i} x={86 + i * 11} y="240" width="7" height="44" rx="3" fill={warm > 0.02 ? "var(--dh-rust)" : edge} opacity={0.35 + 0.65 * warm} />
      ))}
      {warm > 0.02 &&
        [0, 1, 2].map((i) => (
          <path
            key={i}
            d={`M${96 + i * 22} 230 c-6 -8 6 -14 0 -22 s6 -14 0 -22`}
            stroke="var(--dh-amber)"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
            opacity={warm}
            className="steam"
            style={{ animationDelay: `${i * 0.8}s` }}
          />
        ))}
      {/* the backup heater covers what the servers don't */}
      <rect x="180" y="252" width="40" height="32" rx="5" fill="none" stroke={edge} strokeDasharray="3 3" />
      <text x="200" y="272" textAnchor="middle" fontSize="9" fill={dark ? "var(--dh-muted)" : "var(--dh-faint)"}>backup</text>
      <rect x="180" y={284 - 32 * (1 - warm)} width="40" height={32 * (1 - warm)} rx="5" fill="rgba(198,47,47,.22)" />
      {/* ground and basement */}
      <path d="M10 300 H410" stroke="var(--bd)" strokeWidth="2" />
      <rect x="60" y="300" width="300" height="66" rx="8" fill="#4a3428" stroke="var(--bd)" strokeWidth="4" />
      {/* the servers, as little characters: awake and hopping when there is heat to give, asleep when not */}
      {Array.from({ length: servers }, (_, i) => {
        const awake = i < on;
        const ey = 18;
        const er = Math.max(1.1, w * 0.075);
        return (
          <g key={i} transform={`translate(${72 + i * pitch} 312)`}>
            <g className={awake ? "hop" : ""} style={{ animationDelay: `${(i % 4) * 0.15}s` }}>
              <rect width={w} height="44" rx={Math.min(9, w * 0.32)} fill={awake ? "#f7c95c" : "#8a6f5f"} stroke="#2b211c" strokeWidth="2" />
              {awake ? (
                <>
                  <circle cx={w * 0.33} cy={ey} r={er} fill="#4a3428" />
                  <circle cx={w * 0.67} cy={ey} r={er} fill="#4a3428" />
                  <path d={`M${w * 0.36} 26 Q${w * 0.5} ${26 + w * 0.18} ${w * 0.64} 26`} stroke="#4a3428" strokeWidth={Math.max(1.2, w * 0.07)} fill="none" strokeLinecap="round" />
                  {w > 18 && (
                    <>
                      <circle cx={w * 0.18} cy="27" r={w * 0.08} fill="#f6b8c1" />
                      <circle cx={w * 0.82} cy="27" r={w * 0.08} fill="#f6b8c1" />
                    </>
                  )}
                </>
              ) : (
                <path
                  d={`M${w * 0.22} ${ey} Q${w * 0.33} ${ey + 3} ${w * 0.44} ${ey} M${w * 0.56} ${ey} Q${w * 0.67} ${ey + 3} ${w * 0.78} ${ey}`}
                  stroke="#2b211c"
                  strokeWidth={Math.max(1.1, w * 0.065)}
                  fill="none"
                  strokeLinecap="round"
                />
              )}
            </g>
            {/* the first sleeping server snores */}
            {i === on && (
              <g fontFamily="var(--font-fredoka)" fill="#9ccfe6">
                <text className="zz" x={w * 0.7} y="-2" fontSize="10">z</text>
                <text className="zz" x={w * 0.7 + 7} y="-10" fontSize="13" style={{ animationDelay: "1s" }}>Z</text>
              </g>
            )}
          </g>
        );
      })}
      <path d={`M${72 + servers * pitch} 334 H262`} stroke={on ? "var(--dh-rust)" : "rgba(255,255,255,.15)"} strokeWidth="3" strokeDasharray="5 4" className={on ? "move-path" : ""} />
      <path d="M300 310 V292 H130 V284" stroke={warm > 0.02 ? "var(--dh-rust)" : "rgba(107,103,94,.4)"} strokeWidth="3" fill="none" />
      {/* tank */}
      <rect x="266" y="308" width="76" height="50" rx="10" fill="var(--dh-ink-2)" stroke="rgba(246,243,236,.3)" />
      <rect x="268" y={308 + 48 * (1 - fill) + 1} width="72" height={48 * fill} rx="8" fill="var(--dh-amber)" opacity={0.85} />
      <text x="304" y="338" textAnchor="middle" fontSize="11" fontWeight="600" fill="#fbeedd">
        tank
      </text>
    </svg>
  );
}

/* ---------- 0 · opening: the solution first, then the two problems it solves ---------- */

const WARM: Day = { demand: 1, running: 11, soc: 20, served: 1, dumped: 0, paused: 0 }; // a winter hour with every server on

function Hook({ revealed, reveal }: { revealed: boolean; reveal: () => void }) {
  return (
    <Slide id="hook" dark bridge={revealed}>
      <div className="flex items-center gap-3">
        <LogoMark size={34} />
        <span className="font-display text-[19px] font-semibold">DigitalHeat</span>
      </div>
      <div className="grid flex-1 grid-cols-1 items-center gap-8 lg:grid-cols-[1.3fr_1fr]" onClick={reveal}>
        <div>
          <h1 className="max-w-[900px] font-display text-[48px] font-semibold leading-[1.02] md:text-[84px]">
            Servers that
            <br />
            <span className="text-amber">heat homes.</span>
          </h1>
          <div className="scarf mt-8 max-w-[900px]" />
          <div className={clsx("mt-10 transition-all duration-700", revealed ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0")}>
            <div className="text-[20px] font-semibold text-cream/60 md:text-[24px]">One basement, two problems fixed:</div>
            <div className="mt-4 grid max-w-[900px] grid-cols-1 gap-4 md:grid-cols-2">
              <div className="sticker tilt-l rounded-[22px] bg-card px-5 py-4 font-display text-[24px] font-semibold md:text-[28px]">
                <span className="mr-2 text-amber">1</span>Servers waste heat.
              </div>
              <div className="sticker tilt-r rounded-[22px] bg-card px-5 py-4 font-display text-[24px] font-semibold md:text-[28px]">
                <span className="mr-2 text-amber">2</span>Homes pay for heat.
              </div>
            </div>
          </div>
        </div>
        <div className="relative mx-auto aspect-[420/380] w-full max-w-[440px]">
          <HouseXray v={WARM} servers={SERVERS} tank={35} cold dark />
          <div className="sticker-sm absolute left-0 top-0 rounded-full bg-amber px-3 py-1 text-[13px] font-semibold text-ink">A house in Basel</div>
        </div>
      </div>
    </Slide>
  );
}

/* ---------- 1 · problems: one side has too much heat, the other pays for it ---------- */

const HEAT_KWH = 31231; // the reference house, heating + hot water, 2025 (scripts/run_step1.py)
const HEAT_CHF = 0.133; // value of heat, CHF / kWh: electricity ÷ 2.5, a heat pump (case brief)

function Problems() {
  return (
    <Slide id="problems">
      <Kicker>The two problems</Kicker>
      <h2 className="mt-3 font-display text-[36px] font-semibold leading-none md:text-[52px]">Too much heat here. Not enough there.</h2>
      <div className="mt-10 grid flex-1 grid-cols-1 content-center gap-6 lg:grid-cols-2">
        <ProblemCard
          n="1"
          icon={<Flame size={22} className="text-rust" />}
          title="Servers waste heat"
          big="1 kW in"
          unit="≈ 1 kW of heat out"
text="Data centres pay to cool it away."
        />
        <ProblemCard
          n="2"
          warm
          icon={<Receipt size={22} className="text-rust-deep" />}
          title="Homes pay for heat"
          big={`CHF ${(Math.round((HEAT_KWH * HEAT_CHF) / 50) * 50).toLocaleString("en")}`}
          unit="every year"
text="for heating and hot water, even with a heat pump."
        />
      </div>
    </Slide>
  );
}

function ProblemCard({ n, icon, title, big, unit, text, warm }: { n: string; icon: React.ReactNode; title: string; big: string; unit: string; text: string; warm?: boolean }) {
  return (
    <div className={clsx("sticker rounded-[28px] p-6", warm ? "tilt-r bg-amber-soft" : "tilt-l bg-card")}>
      <div className="flex items-center gap-3 text-[17px] font-semibold">
        <span className="grid size-9 place-items-center rounded-full border-[3px] border-ink bg-amber font-display text-[15px] text-ink">{n}</span>
        {icon} {title}
      </div>
      <div className="mt-5 font-display text-[56px] font-semibold leading-none md:text-[64px]">
        {big}
        <span className="ml-3 text-[20px] font-medium text-muted">{unit}</span>
      </div>
      <p className="mt-5 max-w-[480px] text-[17px] leading-snug text-muted">{text}</p>
    </div>
  );
}

/* ---------- 1 · key figures ---------- */

function Figures({ data }: { data: House | null }) {
  const [d, setD] = useState(0);
  useEffect(() => {
    if (!data) return;
    const id = setInterval(() => setD((x) => (x + 1) % 365), 70);
    return () => clearInterval(id);
  }, [data]);
  const y = data?.y;
  const figs = y
    ? [
        [String(y.servers), "servers"],
        [pct(y.coverage, 2), "of its heat"],
        [kwh(y.dumped_kwh), "heat dumped"],
        [pct(y.utilisation, 1), "utilisation"],
        [pct(y.missed_pct / 100, 0), "missed deadlines"],
        [`CHF ${(y.break_even_chf_per_server_h ?? 0).toFixed(3)}`, "break-even"],
      ]
    : [];
  return (
    <Slide id="figures" dark>
      <div className="grid flex-1 grid-cols-1 items-center gap-8 lg:grid-cols-[1fr_1.05fr]">
        <div>
          <Kicker dark>The reference house · Basel, all of 2025</Kicker>
          <h1 className="mt-4 font-display text-[44px] font-semibold leading-[1.02] md:text-[68px]">
            {y ? (
              <>
                {y.servers} servers heat
                <br />
                <span className="text-amber">{pct(y.coverage, 2)}</span> of the home.
              </>
            ) : (
              "The reference house"
            )}
          </h1>
          {data ? (
            <div className="mt-10 grid grid-cols-2 gap-x-6 gap-y-7 md:grid-cols-3">
              {figs.map(([v, k]) => (
                <div key={k} className="sticker rounded-[18px] bg-card px-3 py-2.5">
                  <div className="font-display text-[30px] font-semibold leading-none md:text-[38px]">{v}</div>
                  <div className="mt-1.5 text-[13px] font-semibold text-cream/85">{k}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-10">
              <Waiting dark />
            </div>
          )}
        </div>
        <div className="relative mx-auto aspect-[420/380] w-full max-w-[560px]">
          {data && <HouseXray v={data.days[d]} servers={data.site.servers} tank={data.site.tank_kwh} cold={data.days[d].demand > 1} dark />}
          {data && (
            <div className="sticker-sm absolute left-0 top-0 rounded-full bg-amber px-3 py-1 text-[13px] font-semibold tabular-nums text-ink">
              {dayLabel(d)} · {Math.round(data.days[d].running)} of {data.site.servers} servers on
            </div>
          )}
        </div>
      </div>
    </Slide>
  );
}

function Embedded({ src, title, onClose }: { src: string; title: string; onClose?: () => void }) {
  return (
    <div className="sticker mt-6 flex min-h-[70dvh] flex-1 flex-col overflow-hidden rounded-[28px] bg-ink">
      <div className="flex items-center gap-2 px-4 py-2.5 text-[12px] text-cream/70">
        <span className="size-2.5 rounded-full bg-rust" />
        <span className="size-2.5 rounded-full bg-amber" />
        <span className="size-2.5 rounded-full bg-teal" />
        <span className="ml-2 font-semibold text-cream">{title}</span>
        <a href={src} target="_blank" rel="noreferrer" className="ml-auto hover:text-cream">open in a tab ↗</a>
        {onClose && (
          <button onClick={onClose} className="press ml-3 rounded-full bg-amber px-3 py-1 font-semibold text-ink">
            Back
          </button>
        )}
      </div>
      <iframe src={src} title={title} className="w-full flex-1 bg-paper" />
    </div>
  );
}

/* ---------- 3 · the interrupted real job ---------- */


function Console() {
  const [show, setShow] = useState(false);
  return (
    <Slide id="console">
      <Kicker>Live demo</Kicker>
      <h2 className="mt-3 font-display text-[36px] font-semibold leading-none md:text-[52px]">From one house to a fleet.</h2>
      {show ? (
        <Embedded src="/?t=342" title="DigitalHeat · fleet console" onClose={() => setShow(false)} />
      ) : (
        <button onClick={() => setShow(true)} className="sticker group mt-6 grid min-h-[60dvh] flex-1 place-items-center rounded-[28px] bg-ink text-cream">
          <span className="flex flex-col items-center gap-4">
            <span className="grid size-20 place-items-center rounded-full border-[3px] border-cream bg-rust text-ink transition-transform group-hover:scale-105">
              <Play size={30} fill="currentColor" />
            </span>
            <span className="font-display text-[24px] font-semibold">Open the live console</span>
            <span className="text-[14px] text-cream/50">house · hospital · spa, scheduled hour by hour</span>
          </span>
        </button>
      )}
    </Slide>
  );
}

/* ---------- 5 · who pays: costs, payback, cloud prices ---------- */

function Money() {
  return (
    <Slide id="money">
      <Kicker>Costs & finances</Kicker>
      <h2 className="mt-3 font-display text-[36px] font-semibold leading-none md:text-[52px]">We have the numbers.</h2>
      <div className="mt-6">
        <Finance compact servers={SERVERS} />
      </div>
    </Slide>
  );
}

/* ---------- 5b · paid services: our top 3 (from the service catalogue, docs/todo.csv item 7) ---------- */

const SERVICES = [
  {
    icon: <Search size={26} />,
    t: "Private document search",
    who: "Hospitals, law firms, research labs",
    d: "Search their own files. The data never leaves Switzerland.",
  },
  {
    icon: <FlaskConical size={26} />,
    t: "Simulations",
    who: "Engineers, universities",
    d: "Long calculations that don't mind waiting for the heat.",
  },
  {
    icon: <Clapperboard size={26} />,
    t: "Video & audio processing",
    who: "Media, events, schools",
    d: "Big overnight batches that can pause at any time.",
  },
];

function Services() {
  return (
    <Slide id="services" dark>
      <Kicker dark>Paid services · our top 3</Kicker>
      <h2 className="mt-3 font-display text-[36px] font-semibold leading-none md:text-[52px]">Work that can wait for heat.</h2>
      <div className="mt-10 grid flex-1 grid-cols-1 content-center gap-5 lg:grid-cols-3">
        {SERVICES.map((s, i) => (
          <div key={s.t} className={clsx("sticker flex flex-col rounded-[28px] bg-card p-6", i % 2 ? "tilt-r" : "tilt-l")}>
            <div className="flex items-center gap-3">
              <span className="grid size-12 place-items-center rounded-full border-[3px] border-cream bg-amber text-ink">{s.icon}</span>
              <span className="font-display text-[40px] font-semibold leading-none text-cream/30">{i + 1}</span>
            </div>
            <div className="mt-5 font-display text-[28px] font-semibold leading-tight">{s.t}</div>
            <div className="mt-1 text-[14px] font-semibold text-amber">{s.who}</div>
            <p className="mt-3 text-[17px] leading-snug text-cream/80">{s.d}</p>
          </div>
        ))}
      </div>
    </Slide>
  );
}

/* ---------- 6b · case study: Windcloud 4.0 heats a spirulina farm with data-centre heat (their email to us) ---------- */

const ALGAE = [
  { k: "What", icon: <Sprout size={22} />, d: "A spirulina farm, heated by a data centre's waste heat." },
  { k: "Why", icon: <Thermometer size={22} />, d: "Spirulina grows in water at 15–38 °C. Server heat is exactly that warm." },
  { k: "How", icon: <Waves size={22} />, d: "Warm water from the servers heats the greenhouse, so the growing season lasts longer." },
  { k: "A third income?", icon: <Coins size={22} />, d: "Running every hour would make 46,000 kWh a year more heat than the house needs. If a greenhouse took it, profit could rise from CHF 40,000 to up to 178,000 a year, if every hour sells." },
];

function Industry() {
  return (
    <Slide id="industry" dark>
      <Kicker dark>Case study · Windcloud 4.0, northern Germany</Kicker>
      <h2 className="mt-3 font-display text-[36px] font-semibold leading-none md:text-[52px]">Data-centre heat that grows algae.</h2>
      <div className="mt-10 grid flex-1 grid-cols-1 content-center gap-5 md:grid-cols-2 lg:grid-cols-4">
        {ALGAE.map((x, i) => (
          <div key={x.k} className={clsx("sticker flex flex-col rounded-[28px] p-6", i % 2 ? "tilt-r" : "tilt-l", i === 3 ? "bg-amber-soft" : "bg-card")}>
            <span className="grid size-11 place-items-center rounded-full border-[3px] border-cream bg-amber text-ink">{x.icon}</span>
            <div className="mt-4 font-display text-[28px] font-semibold leading-none">{x.k}</div>
            <p className="mt-3 text-[17px] leading-snug text-cream/85">{x.d}</p>
          </div>
        ))}
      </div>
      <div className="sticker mt-8 self-start rounded-[22px] bg-teal-soft px-6 py-4 font-display text-[22px] font-semibold leading-snug text-cream md:text-[28px]">
        Homes take the winter heat. <span className="text-rust-deep">Algae could take spring and autumn.</span>
      </div>
    </Slide>
  );
}

/* ---------- 7 · close ---------- */

function Close({ data }: { data: House | null }) {
  return (
    <Slide id="close" dark className="items-center justify-center text-center">
      <LogoMark size={56} />
      <div className="mt-10 grid w-full max-w-[900px] grid-cols-1 gap-4 text-left md:grid-cols-2">
        <div className="sticker tilt-l rounded-[22px] bg-card px-5 py-4">
          <div className="font-display text-[26px] font-semibold leading-tight md:text-[30px]">
            <span className="text-amber">{data ? kwh(data.y.dumped_kwh) : "0 kWh"}</span> thrown away.
          </div>
        </div>
        <div className="sticker tilt-r rounded-[22px] bg-card px-5 py-4">
          <div className="font-display text-[26px] font-semibold leading-tight md:text-[30px]">
            <span className="text-amber">{data ? pct(data.y.coverage, 2) : "99.97%"}</span> of its heat from computing.
          </div>
        </div>
      </div>
      <h2 className="mt-12 font-display text-[40px] font-semibold leading-[1.05] md:text-[64px]">
        The heat was always there.
        <br />
        <span className="text-amber">It was just in the wrong building.</span>
      </h2>
      <div className="scarf mt-8 w-full max-w-[640px]" />
    </Slide>
  );
}
