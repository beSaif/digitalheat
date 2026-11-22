import type { Metadata } from "next";
import { IBM_Plex_Sans, Inter_Tight } from "next/font/google";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

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
  title: "DigitalHeat · Live",
  description: "Your device is a DigitalHeat server in a Swiss house. Work only goes where heat is needed.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plex.variable} ${display.variable} antialiased`}>
      <body>{children}</body>
    </html>
  );
}
