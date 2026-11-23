import { Fredoka, Nunito } from "next/font/google";
import "./pitch.css";

/* The pitch has its own look (pitch.css): rounded Fredoka headings, Nunito text. */
const fredoka = Fredoka({ variable: "--font-fredoka", subsets: ["latin"], weight: ["500", "600"] });
const nunito = Nunito({ variable: "--font-nunito", subsets: ["latin"], weight: ["400", "600", "700"] });

export default function PitchLayout({ children }: { children: React.ReactNode }) {
  return <div className={`${fredoka.variable} ${nunito.variable}`}>{children}</div>;
}
