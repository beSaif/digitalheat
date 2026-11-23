"use client";

import clsx from "clsx";
import { Flower2, Leaf, Snowflake, Sun } from "lucide-react";

/*
 * The season of the moment the operator picked, as a light tint over the whole screen: a cold blue frame and
 * falling snow in winter, a warm frame and a sun glow in summer, softer tints in between. It never takes clicks.
 *
 * Seasons follow heating, not the calendar: November to March is winter (the heating season in Basel),
 * June to August is summer, April–May and September–October are in between.
 */

export type Season = "winter" | "spring" | "summer" | "autumn";

/** Season of an ISO date (YYYY-MM-DD). */
export function seasonOf(iso: string | undefined): Season | null {
  const m = iso ? Number(iso.split("-")[1]) : NaN;
  if (!m) return null;
  if (m >= 11 || m <= 3) return "winter";
  if (m <= 5) return "spring";
  if (m <= 8) return "summer";
  return "autumn";
}

export const SEASON = {
  winter: { label: "Winter", icon: Snowflake, fg: "#3d6f8f", bg: "#e4eef5", edge: "rgba(110, 160, 200, 0.26)" },
  spring: { label: "Spring", icon: Flower2, fg: "#4f7a45", bg: "#e8f0e2", edge: "rgba(130, 175, 110, 0.20)" },
  summer: { label: "Summer", icon: Sun, fg: "#a35a1c", bg: "#fbecd9", edge: "rgba(242, 166, 90, 0.30)" },
  autumn: { label: "Autumn", icon: Leaf, fg: "#8f4423", bg: "#f5e6dc", edge: "rgba(192, 101, 58, 0.22)" },
} as const;

/* deterministic flakes, so server and browser agree and they do not jump on re-render */
const FLAKES = Array.from({ length: 64 }, (_, i) => {
  const r = (k: number) => {
    const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453;
    return x - Math.floor(x);
  };
  return { left: r(1) * 100, size: 4 + r(2) * 6, dur: 10 + r(3) * 12, delay: -r(4) * 22, sway: 12 + r(5) * 28, top: r(7) * 100, o: 0.55 + r(6) * 0.4 };
});

export default function SeasonOverlay({ season }: { season: Season | null }) {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-[5] overflow-hidden">
      {(Object.keys(SEASON) as Season[]).map((k) => (
        <div
          key={k}
          className={clsx("absolute inset-0 transition-opacity duration-[1400ms] ease-out", season === k ? "opacity-100" : "opacity-0")}
          style={{ background: `radial-gradient(ellipse 75% 70% at 50% 50%, transparent 55%, ${SEASON[k].edge} 100%)` }}
        />
      ))}

      {/* summer: a sun glow from the top right corner */}
      <div
        className={clsx("season-sun absolute -right-[12vw] -top-[18vw] size-[46vw] rounded-full transition-opacity duration-[1400ms]", season === "summer" ? "opacity-100" : "opacity-0")}
        style={{ background: "radial-gradient(circle, rgba(255, 205, 120, 0.55) 0%, rgba(255, 190, 100, 0.22) 38%, transparent 68%)" }}
      />

      {/* winter: frost along the top edge and falling snow */}
      <div
        className={clsx("absolute inset-x-0 top-0 h-[22vh] transition-opacity duration-[1400ms]", season === "winter" ? "opacity-100" : "opacity-0")}
        style={{ background: "linear-gradient(to bottom, rgba(190, 215, 235, 0.22), transparent)" }}
      />
      {season === "winter" && (
        <div className="season-snow absolute inset-0">
          {FLAKES.map((f, i) => (
            <span
              key={i}
              className="season-flake absolute rounded-full"
              style={
                {
                  left: `${f.left}%`,
                  top: `${f.top}%`,
                  width: f.size,
                  height: f.size,
                  opacity: f.o,
                  background: "radial-gradient(circle, #ffffff 35%, #dcebf6 100%)",
                  boxShadow: "0 0 0 1px rgba(90, 140, 180, 0.28), 0 1px 4px rgba(60, 110, 150, 0.35)",
                  animationDuration: `${f.dur}s`,
                  animationDelay: `${f.delay}s`,
                  "--sway": `${f.sway}px`,
                } as React.CSSProperties
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
