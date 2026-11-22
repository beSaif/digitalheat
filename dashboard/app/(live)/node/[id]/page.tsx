"use client";

import { use, useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { Briefcase, Building2, Flame, FlaskConical, Hospital, House, Leaf, Moon, MoveRight, Pause, Thermometer, Users, Waves } from "lucide-react";
import { LogoMark } from "@/components/Logo";
import { useServerNode } from "@/lib/live/useServerNode";
import { KIND_NAME, NAME_MAX, TILE_H, TILE_W, cleanName, type Device, type NodeState } from "@/lib/live/shared";

/*
 * Host screen. Phones arrive here from the QR code (/join gives them an id). The person types their
 * first name and becomes a host: their own building with a rack of servers joins the fleet. Whenever
 * the DigitalHeat scheduler says the building needs heat, the page path-traces tiles of a customer's
 * render in Web Workers and sends them back. Hiding the page (locking the phone) takes the rack
 * offline and its tile goes back to the queue.
 */

const NAME_KEY = "dh-live-name";
const SITE_ICON: Record<string, typeof House> = {
  house: House,
  family: Users,
  cityhouse: Building2,
  hospital: Hospital,
  spa: Waves,
  greenhouse: Leaf,
  office: Briefcase,
  pharma: FlaskConical,
};

function detectDevice(): Device {
  if (typeof navigator === "undefined") return "laptop";
  return /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && /Macintosh/.test(navigator.userAgent)) ? "phone" : "laptop";
}

export default function NodePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: rawId } = use(params);
  const id = rawId.toLowerCase();
  const [device, setDevice] = useState<Device | null>(null);
  const [name, setName] = useState<string | null>(null); // null = not read yet, "" = ask
  useEffect(() => {
    Promise.resolve().then(() => {
      setDevice(detectDevice());
      setName(cleanName(localStorage.getItem(NAME_KEY) ?? ""));
    });
  }, []);

  if (device === null || name === null) return <Screen className="bg-cream text-ink" />;
  if (!name)
    return (
      <AskName
        onDone={(n) => {
          localStorage.setItem(NAME_KEY, n);
          setName(n);
        }}
      />
    );
  return <Server id={id} name={name} device={device} />;
}

function Screen({ className, children }: { className: string; children?: React.ReactNode }) {
  return <div className={clsx("fixed inset-0 z-[1000] overflow-y-auto transition-colors duration-700", className)}>{children}</div>;
}

function AskName({ onDone }: { onDone: (name: string) => void }) {
  const [v, setV] = useState("");
  const clean = cleanName(v);
  return (
    <Screen className="bg-cream text-ink">
      <form
        className="mx-auto flex min-h-full max-w-[460px] flex-col justify-center gap-5 px-6 py-10"
        onSubmit={(e) => {
          e.preventDefault();
          if (clean) onDone(clean);
        }}
      >
        <LogoMark size={44} />
        <h1 className="font-display text-[34px] font-semibold leading-tight">Become a DigitalHeat server</h1>
        <input
          autoFocus
          value={v}
          maxLength={NAME_MAX + 4}
          onChange={(e) => setV(e.target.value)}
          placeholder="Your first name"
          autoComplete="given-name"
          className="rounded-2xl bg-card px-4 py-4 text-[20px] font-semibold outline-none ring-1 ring-line focus:ring-2 focus:ring-rust"
        />
        <button disabled={!clean} className="rounded-2xl bg-ink px-5 py-4 text-[18px] font-semibold text-cream disabled:opacity-40">
          Join the fleet
        </button>
      </form>
    </Screen>
  );
}

function Server({ id, name, device }: { id: string; name: string; device: Device }) {
  const { canvas, reply, online, view } = useServerNode(id, { name, device, leaveWhenHidden: true });
  const state: NodeState = !online ? "offline" : (reply?.state ?? "waiting");
  const running = state === "running" && view !== null && !view.loading;
  useWakeLock();
  useBuzzOnStart(state);

  const site = reply?.site;
  const job = reply?.job;
  const SiteIcon = (site && SITE_ICON[site.kind]) || Building2;
  const full = state === "off" && !!reply?.reason.startsWith("Tank full");
  const theme = !online ? "bg-ink text-cream" : state === "running" ? "bg-rust text-cream" : state === "off" ? "bg-teal-soft text-ink" : "bg-cream text-ink";
  const sub = !online ? "text-cream/60" : state === "running" ? "text-cream/75" : "text-muted";
  const panel = state === "running" ? "bg-cream/12" : !online ? "bg-cream/8" : "bg-paper/80 ring-1 ring-line";

  const headline = !online
    ? reply
      ? "Server offline"
      : "Connecting…"
    : state === "running"
      ? running && job
        ? job.kind === "render"
          ? "Rendering"
          : job.kind === "embed"
            ? "Embedding"
            : "Reranking"
        : "Needs heat"
      : state === "off"
        ? full
          ? "Tank full · paused"
          : "Resting"
        : "Getting your rack ready";
  const detail = !online
    ? reply
      ? "Your work moved to another server."
      : ""
    : state === "running" && running && job
      ? `${job.label} for a customer${job.kind === "render" ? "" : ", 8 science abstracts"}. The heat goes into your ${(KIND_NAME[site?.kind ?? ""] ?? "building").toLowerCase()}.`
      : (reply?.reason ?? "");

  return (
    <Screen className={theme}>
      <div className="mx-auto flex min-h-full max-w-[1100px] flex-col px-5 pb-6 pt-5 sm:px-8 sm:pt-7">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <LogoMark size={32} />
            <div className="leading-tight">
              <div className="font-display text-[16px] font-semibold">DigitalHeat server</div>
              <div className={clsx("text-[12px]", sub)}>{reply?.conditions ?? "Live demo"}</div>
            </div>
          </div>
          <span className={clsx("flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] font-semibold", online ? "bg-ink/10" : "bg-alarm text-cream")}>
            <span className={clsx("size-2 rounded-full", online ? "animate-pulse bg-[#3aa35b]" : "bg-cream")} />
            {online ? "Online" : "Offline"}
          </span>
        </div>

        <div className="mt-5 grid flex-1 grid-cols-[minmax(0,1fr)] content-start gap-5 lg:grid-cols-2 lg:gap-10">
          <div className="flex min-w-0 flex-col">
            <div className="flex items-center gap-3">
              <span className="size-5 shrink-0 rounded-full ring-2 ring-cream/70" style={{ background: reply?.color ?? "#9a958a" }} />
              <h1 className="min-w-0 truncate font-display text-[clamp(32px,9vw,64px)] font-semibold leading-[0.95]">{reply?.name ?? name}</h1>
            </div>
            {site && (
              <div className="mt-3 flex items-center gap-2 text-[16px] font-semibold">
                <SiteIcon size={18} className="shrink-0" />
                Your {(KIND_NAME[site.kind] ?? site.kind).toLowerCase()} · {site.servers} servers
              </div>
            )}
            {site && (
              <div className={clsx("mt-1 flex flex-wrap items-center gap-x-3 text-[14px]", sub)}>
                <span className="flex items-center gap-1">
                  <Thermometer size={14} /> {site.temp.toFixed(0)} °C
                </span>
                <span>
                  {site.on}/{site.servers} servers on
                </span>
              </div>
            )}

            <div className={clsx("mt-4 rounded-2xl p-4", panel)}>
              <div className="flex items-center gap-2.5 text-[clamp(19px,5.2vw,26px)] font-semibold leading-tight">
                <span
                  className={clsx(
                    "inline-block size-3.5 shrink-0 rounded-full",
                    state === "running" ? "animate-pulse bg-amber" : state === "off" ? "bg-teal" : online ? "bg-faint" : "bg-alarm",
                  )}
                />
                {headline}
              </div>
              <p className={clsx("mt-1.5 text-[14px] leading-snug", sub)}>{detail}</p>
              {reply?.note && state !== "running" && (
                <p className="mt-2 flex items-center gap-1.5 text-[14px] font-semibold leading-snug">
                  <MoveRight size={15} className="shrink-0" /> {reply.note}
                </p>
              )}
            </div>
          </div>

          <div className="flex min-w-0 flex-col">
            <div className="flex h-[min(30vh,calc(100vw-7.5rem))] justify-between gap-3 lg:h-[min(52vh,520px)]">
              <div className={clsx("relative h-full overflow-hidden rounded-2xl", panel)} style={{ aspectRatio: `${TILE_W} / ${TILE_H}` }}>
                <canvas ref={canvas} className={clsx("absolute inset-2.5 h-[calc(100%-20px)] w-[calc(100%-20px)] rounded-lg shadow-2xl", !running && "invisible")} />
                {!running && (
                  <div className={clsx("absolute inset-0 grid place-items-center px-4 text-center text-[14px]", sub)}>
                    <div>
                      {full ? <Pause size={40} className="mx-auto mb-2 text-teal" /> : state === "off" ? <Moon size={40} className="mx-auto mb-2 text-teal" /> : <Flame size={40} className="mx-auto mb-2 opacity-40" />}
                      {full ? "Tank full: work paused" : state === "off" ? "No heat needed" : state === "running" ? (view?.loading ? "Loading the AI model…" : "Waiting for a job") : online ? "Waiting" : "Offline"}
                    </div>
                  </div>
                )}
              </div>
              <div className="flex w-[64px] shrink-0 flex-col sm:w-[96px]">
                <div className={clsx("relative flex-1 overflow-hidden rounded-2xl", panel)} title="The site's heat tank (the scheduler's)">
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#3f8f9a] to-[#7cc3cb] transition-[height] duration-500" style={{ height: `${site && site.tank ? (100 * site.soc) / site.tank : 0}%` }} />
                  <div className="absolute inset-x-0 top-2 text-center font-display text-[18px] font-semibold tabular-nums sm:text-[24px]">
                    {site && site.tank ? `${Math.round((100 * site.soc) / site.tank)}%` : "–"}
                  </div>
                </div>
                <div className={clsx("mt-1 text-center text-[11px] leading-tight", sub)}>Tank</div>
              </div>
            </div>

            <div className="mt-3">
              <div className={clsx("h-2 overflow-hidden rounded-full", state === "running" ? "bg-cream/20" : "bg-paper")}>
                <div className="h-full rounded-full bg-amber transition-[width] duration-300" style={{ width: `${(view?.progress ?? 0) * 100}%` }} />
              </div>

            </div>

            <div className="mt-4">
              <Stat label="Parts done" value={String(reply?.chunks ?? 0)} sub={sub} />
            </div>
          </div>
        </div>

        <p className={clsx("mt-5 text-[12px]", sub)}>Keep this screen on.</p>
      </div>
    </Screen>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div>
      <div className={clsx("text-[12px]", sub)}>{label}</div>
      <div className="font-display text-[26px] font-semibold tabular-nums">{value}</div>
    </div>
  );
}

/** Keep the screen on while the page is visible, so the phone keeps serving. */
function useWakeLock() {
  useEffect(() => {
    let lock: { release: () => Promise<void> } | null = null;
    const nav = navigator as Navigator & { wakeLock?: { request: (t: "screen") => Promise<{ release: () => Promise<void> }> } };
    const get = () => {
      if (document.visibilityState === "visible" && nav.wakeLock)
        nav.wakeLock
          .request("screen")
          .then((l) => (lock = l))
          .catch(() => {});
    };
    get();
    document.addEventListener("visibilitychange", get);
    return () => {
      document.removeEventListener("visibilitychange", get);
      lock?.release().catch(() => {});
    };
  }, []);
}

/** A short buzz when the scheduler switches this server on. */
function useBuzzOnStart(state: NodeState) {
  const prev = useRef(state);
  useEffect(() => {
    if (prev.current !== "running" && state === "running") navigator.vibrate?.(120);
    prev.current = state;
  }, [state]);
}
