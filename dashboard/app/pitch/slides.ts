/*
 * The pitch, slide by slide: what each slide is called, the line that leads to the next one
 * (the "bridge"), and the script to say. The deck (page.tsx) and the printable script
 * (script/page.tsx) both read this list.
 *
 * Story: what it is and the result → we pay for heat twice, so the house decides → why eleven, not thirteen →
 * live demo → summer: an algae farm as a third income → who pays for the work → does it pay, and what has to be true → back to the two problems.
 * Written for the ear: short sentences, the key word last, few numbers, said as words.
 * Numbers are the reference house in Basel, 2025, 11 servers (python3 -m scheduler.balance --servers 11).
 */
/** seconds: a fixed time budget instead of one counted from the words (the live demo). */
export type PitchSlide = { id: string; label: string; bridge: string; note: string; seconds?: number; qa?: boolean };

export const SLIDES: PitchSlide[] = [
  {
    id: "hook",
    label: "Opening",
    bridge: "It starts with two problems.",
    note: "DigitalHeat puts servers in the basement, so their waste heat warms the home. We tested it on a house in Basel, every hour of 2025. Eleven servers. 99.97 percent of the heat. Zero heat thrown away. Zero jobs late. (Press space.) We're team Ctrl+Free.",
  },
  {
    id: "problems",
    label: "Two problems",
    bridge: "So how many did we buy?",
    note: "Today, we pay for heat twice. Data centres pay to get rid of it. Homes pay to make it. This house spends about 4,150 francs a year, even with a heat pump. The catch: a house is a moody customer. On the coldest night, it wants twelve and a half servers. In summer, not even one. So we let the house decide. Every hour, it tells our scheduler how much heat it needs and how much hot water it can still store. That many servers switch on. When the house is warm, the work pauses and waits.",
  },
  {
    id: "figures",
    label: "Result",
    bridge: "Here's what to watch.",
    note: "We bought eleven, not thirteen. The hot-water tank covers the coldest nights, so no server sits waiting for them. Across 2025, they worked 40 percent of the hours. Here's what to watch.",
  },
  {
    id: "console",
    label: "Live demo",
    bridge: "What about summer?",
    seconds: 90,
    note: "(Open the live demo.) A January morning. Every building needs heat, so every rack is working. (Order a job from a phone.) Watch its parts land only on racks whose building needs heat. (Switch to the July afternoon.) Summer. Most buildings are warm, so their racks pause and the work moves to the few that still need heat. (If the demo fails, play the backup recording.) (Back to the slides with: What about summer?)",
  },
  {
    id: "industry",
    label: "Algae case study",
    bridge: "Who pays for the work?",
    note: "What about summer? The house barely needs heat, so the servers sleep. But Windcloud, in Germany, already grows algae with their data centre's heat. A greenhouse next door could take the heat the house doesn't need, so our servers could run every hour. That's a third income, next to computing and heat: up to four times the profit, if every hour sells. (Pause.) Homes take the winter heat. Algae could take spring and autumn.",
  },
  {
    id: "services",
    label: "Paid services",
    bridge: "But does it pay?",
    note: "Who pays for the work? Anyone with work that can wait for heat. Private document search for hospitals and law firms, with data that never leaves Switzerland. That's the job you just saw. Simulations for engineers. And overnight video processing.",
  },
  {
    id: "money",
    label: "Costs",
    bridge: "Back to our two problems.",
    note: "But does it pay? Our servers use the same chips Amazon rents out. All in, one server costs us 1.72 francs an hour. Our work can pause, so we price it like Amazon's spot computing: 2.74. Eleven servers make 40,000 francs a year, and pay for themselves in about three years. What has to be true? Two things. First, the price stays above 1.72. Azure's cheapest is already below that, so we won't win on price alone. We win on computing that stays in Switzerland. Second, the servers work a quarter of the year. Basel gave us 40 percent. Almost double. Every number is in our repository. Rerun it yourselves.",
  },
  {
    id: "close",
    label: "Conclusion",
    bridge: "",
    note: "So: data centres stop paying to throw heat away. Families stop paying to make it. Our ask is one pilot. One building. Eleven servers. One winter. (Pause.) Because the heat was always there. (Pause.) It was just in the wrong building. Thank you.",
  },
];

/** Speaking time in seconds, at a calm pitch pace (140 words a minute), stage directions left out. */
export function seconds(note: string) {
  const words = note.replace(/\([^)]*\)/g, "").split(/\s+/).filter(Boolean).length;
  return Math.round((words / 140) * 60);
}
