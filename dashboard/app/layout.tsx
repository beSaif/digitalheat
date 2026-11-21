import type { Metadata } from "next";
import { IBM_Plex_Sans, Inter_Tight } from "next/font/google";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";
import { FleetProvider } from "@/lib/store";
import { Shell } from "@/components/Shell";

const plex = IBM_Plex_Sans({
  variable: "--font-plex",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const display = Inter_Tight({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "DigitalHeat · Fleet console",
  description: "Operator console for DigitalHeat's heat-following server fleet (scenario replay).",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plex.variable} ${display.variable} antialiased`}>
      <body>
        <FleetProvider>
          <Shell>{children}</Shell>
        </FleetProvider>
      </body>
    </html>
  );
}
