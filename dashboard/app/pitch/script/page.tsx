"use client";

import { Fragment } from "react";
import Link from "next/link";
import { ArrowLeft, Printer } from "lucide-react";
import { SLIDES, seconds } from "../slides";

/* The pitch script: every slide's words in order, with stage directions and timing. Prints cleanly. */

const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

/** Stage directions in brackets, "(Press space.)", become small coral cues. */
function Spoken({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\([^)]*\))/).map((part, i) =>
        part.startsWith("(") ? (
          <span key={i} className="mx-1 rounded-full bg-amber-soft px-2 py-0.5 text-[14px] font-semibold text-rust-deep">
            {part.slice(1, -1)}
          </span>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

export default function Script() {
  const talk = SLIDES.filter((s) => !s.qa);
  const time = (s: (typeof SLIDES)[number]) => s.seconds ?? seconds(s.note);
  const total = talk.reduce((a, s) => a + time(s), 0);
  // when each slide starts and ends, in seconds from the start of the talk
  const times = SLIDES.reduce<[number, number][]>((acc, s) => {
    const start = acc.length ? acc[acc.length - 1][1] : 0;
    return [...acc, [start, start + (s.qa ? 0 : time(s))]];
  }, []);
  return (
    <div className="cosy min-h-dvh bg-paper text-ink print:bg-white">
      <div className="mx-auto max-w-[860px] px-5 py-10 md:py-14">
        <div className="flex flex-wrap items-center gap-3 print:hidden">
          <Link href="/pitch" className="sticker-sm flex items-center gap-1.5 rounded-full bg-card px-4 py-2 text-[14px] font-semibold">
            <ArrowLeft size={15} /> Back to the slides
          </Link>
          <button onClick={() => window.print()} className="press ml-auto flex items-center gap-1.5 rounded-full bg-amber px-4 py-2 text-[14px] font-semibold text-ink">
            <Printer size={15} /> Print
          </button>
        </div>

        <span className="kicker mt-8">DigitalHeat · Team Ctrl+Free</span>
        <h1 className="mt-3 font-display text-[44px] font-semibold leading-none md:text-[60px]">The pitch script</h1>
        <p className="mt-3 text-[17px] text-muted">
          {talk.length} slides · about {mmss(total)} including the live demo · keys: → next, N notes, F full screen
        </p>
        <div className="scarf mt-6" />

        <ol className="mt-8 flex flex-col gap-5">
          {SLIDES.map((s, i) => {
            const [start, end] = times[i];
            return (
              <Fragment key={s.id}>
              <li className="sticker rounded-[22px] bg-card p-5">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="grid size-9 place-items-center rounded-full border-[3px] border-ink bg-amber font-display text-[16px] font-semibold">{i + 1}</span>
                  <span className="font-display text-[24px] font-semibold">{s.label}</span>
                  <span className="ml-auto text-[13px] font-semibold tabular-nums text-muted">
                    {s.qa ? "Q&A only" : `${mmss(start)} – ${mmss(end)}`}
                  </span>
                </div>
                <p className="mt-3 text-[18px] leading-relaxed">
                  <Spoken text={s.note} />
                </p>
                {s.bridge && (
                  <div className="mt-3 border-t-2 border-dashed border-line pt-2 text-[14px] text-muted">
                    Next slide: <b className="text-rust-deep">{s.bridge}</b>
                  </div>
                )}
              </li>
              </Fragment>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
