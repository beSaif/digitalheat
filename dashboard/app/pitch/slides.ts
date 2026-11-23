/*
 * The pitch, slide by slide: what each slide is called, the line that leads to the next one
 * (the "bridge"), and the script to say. The deck (page.tsx) and the printable script
 * (script/page.tsx) both read this list.
 *
 * Story: the solution first → the two problems → how it works → result → live demo (the console, slide 5) → money →
 * services → back to the two problems. About 5 minutes; the console is Q&A only.
 * Numbers are the reference house in Basel, 2025, 11 servers (python3 -m scheduler.balance --servers 11): the fewest
 * that cover every hour with its 35 kWh tank, the same rack the live demo gives the house.
 */
/** seconds: a fixed time budget instead of one counted from the words (the live demo). */
export type PitchSlide = { id: string; label: string; bridge: string; note: string; seconds?: number; qa?: boolean };

export const SLIDES: PitchSlide[] = [
  {
    id: "hook",
    label: "Opening",
    bridge: "It starts with two problems.",
    note: "Eleven servers in a basement. For a whole year, they gave a Basel home 99.97% of its heat. Not one kilowatt-hour was wasted, and the servers earned money the entire time. (Press space.) We're team Ctrl+Free, and this is DigitalHeat: servers that heat homes.",
  },
  {
    id: "problems",
    label: "Two problems",
    bridge: "So how many servers does a house need?",
    note: "Today, servers waste heat: data centres pay to cool it away. And homes pay for heat: this house needs 31,231 kilowatt-hours a year, about 4,150 francs even with a heat pump. So why not put servers in basements? Because a house is a moody customer. In the coldest hour it wants twelve and a half servers. On a summer day, less than one. Buy twelve, they idle all summer. Buy one, the house is cold all winter.",
  },
  {
    id: "idea",
    label: "Solution",
    bridge: "We tested it on the reference house, hour by hour, for all of 2025.",
    note: "So we don't fix the number. We let the house decide. Every hour, it tells our scheduler how much heat it needs and how much room is left in its hot-water tank, and only that many servers switch on. When no heat is needed, the work doesn't fail. It pauses, keeps its place, and waits.",
  },
  {
    id: "figures",
    label: "Result",
    bridge: "Now, the live demo.",
    note: "We ran this on the reference house for every hour of 2025. Eleven servers, fewer than the coldest hour asks for: the hot-water tank carries heat into it. 99.97% of the heat covered. Zero heat dumped. Zero missed deadlines. The servers were busy 41% of the year, and that's the point: they only run when the heat is wanted. Let's watch it happen.",
  },
  {
    id: "console",
    label: "Live demo",
    bridge: "Useful heat, useful work. But does it pay?",
    seconds: 90,
    note: "(Click Open the live console.) Show 15 January: every server running. Then 15 July: servers asleep, the work pausing. Then the real job on this laptop pausing and resuming on the heat signal. (Come back to the slides with: Useful heat, useful work. But does it pay?)",
  },
  {
    id: "money",
    label: "Costs",
    bridge: "So who buys all that computing?",
    note: "Useful heat, useful work. But does it pay? Each server is the same machine Amazon rents out by the hour. Eleven, installed, cost 279,000 francs. All in, one server-hour costs us 1.72. We sell it at 2.74, Amazon's own spot price, and less than a third of their on-demand price. That's 40,000 francs profit a year, and the money back in just under three years. Where does it break? Below 1.72 a server-hour, or if servers are busy less than a quarter of the year. And in a real house, the summer tank loses some heat and showers need a small booster. Every number and assumption is in our repository, ready to rerun.",
  },
  {
    id: "services",
    label: "Paid services",
    bridge: "Back to our two problems.",
    note: "So who pays? Work that can wait for heat. Private document search for hospitals and law firms, with data that never leaves Switzerland: that's the job you just saw. Simulations for engineers. And overnight video processing.",
  },
  {
    id: "close",
    label: "Conclusion",
    bridge: "",
    note: "Back to our two problems: zero heat wasted, and a home heated by computing someone else pays for. Our ask: one pilot. One building, eleven servers, one winter. (Pause.) Because the heat was always there. (Pause.) It was just in the wrong building. Thank you.",
  },
];

/** Speaking time in seconds, at a calm pitch pace (140 words a minute), stage directions left out. */
export function seconds(note: string) {
  const words = note.replace(/\([^)]*\)/g, "").split(/\s+/).filter(Boolean).length;
  return Math.round((words / 140) * 60);
}
