/*
 * One heat-status vocabulary for the whole dashboard: the live room screen and the map colour a
 * building the same way. Plain module (no "use client"), so server code can import it too.
 */

export type Status = "used" | "dumped" | "short" | "paused" | "idle";

export const STATUS: Record<Status, { label: string; short: string; color: string; text: string }> = {
  used: { label: "Heat used, nothing wasted", short: "heat used", color: "#7bb38a", text: "#2f7a5c" },
  dumped: { label: "Server heat thrown away", short: "heat thrown away", color: "#f2a65a", text: "#a85a12" },
  short: { label: "Heat demand not covered", short: "not covered", color: "#d0533f", text: "#b2402e" },
  paused: { label: "Paused on purpose (tank full)", short: "tank full, paused", color: "#5fa8b0", text: "#2f6e75" },
  idle: { label: "No heat needed", short: "no heat needed", color: "#cfc9bd", text: "#6b675e" },
};

/** The four that carry meaning (idle is the neutral rest state). */
export const STATUS_LEGEND: Status[] = ["used", "dumped", "short", "paused"];

/** Status of a building for one period: heat demand, heat covered by servers, heat thrown away (kWh or kW). */
export function statusOf(demand: number, served: number, dumped: number, paused: number | boolean): Status {
  const p = typeof paused === "boolean" ? paused : paused > 0;
  if (demand <= 0.05 && dumped <= 0.05) return p ? "paused" : "idle";
  if (dumped > 0.05 * Math.max(demand, 1)) return "dumped";
  if (served < 0.9 * demand) return "short";
  if (p) return "paused";
  return "used";
}
