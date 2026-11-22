import { Suspense } from "react";
import type { Metadata, Viewport } from "next";

/** Live demo: phones and laptops as DigitalHeat servers, and the room screen. No console chrome, no fleet replay data. */
export const metadata: Metadata = {
  title: "DigitalHeat · Live",
  description: "Your device is a DigitalHeat server in a Swiss house. Work only goes where heat is needed.",
};

export const viewport: Viewport = { themeColor: "#c0653a" };

// /node/[id] reads its param at request time, so the pages stream inside a Suspense boundary
export default function LiveLayout({ children }: { children: React.ReactNode }) {
  return <Suspense>{children}</Suspense>;
}
