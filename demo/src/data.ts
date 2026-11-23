/**
 * Everything that is specific to this video. Times are seconds on the output timeline.
 * Clips come from capture/cuts.json (written by `pnpm record`), voice durations from voice/manifest.json
 * (written by `pnpm voice`), so re-filming or re-voicing re-times the cut by itself.
 */
import cutsJson from '../capture/cuts.json'
import manifestJson from '../voice/manifest.json'
import linesJson from '../voice/lines.json'
import type { Key } from './Camera'
import { C } from './theme'

export const VIDEO = 'rec/screen.mp4'

/** Where the footage sits in the frame; the strip below it carries the tag and subtitles. */
export const SCREEN = { x: 96, y: 14, w: 1728, h: 972 }

// --- end card ---------------------------------------------------------------------------------
export const TITLE = 'DigitalHeat'
export const TAGLINE = 'Computing that heats the building it runs in.'
export const CREDIT = 'sprintd Basel · GreenTech Edition 2026'

/** Tag colour per role passed to roll(); leave `who` empty there to show no tags. */
export const ROLE_COLORS: Record<string, string> = { DigitalHeat: C.rust, Homeowner: C.teal, Customer: C.navy, 'This laptop': C.muted }

// --- clips ------------------------------------------------------------------------------------
export type Cut = { name: string; who: string; from: number; until: number }
export const CUTS = cutsJson as unknown as Cut[]
export const VIDEO_END = CUTS.at(-1)?.until ?? 0

const clip = (name: string) => CUTS.find((c) => c.name === name)

/** `s` seconds after clip `name` starts. */
export function after(name: string, s = 0.3): number {
  const c = clip(name)
  if (!c) throw new Error(`no clip "${name}" in capture/cuts.json`)
  return c.from + s
}

// --- narration --------------------------------------------------------------------------------
type LineSpec = { id: string; clip: string; offset?: number; text: string }
export type Line = { id: string; at: number; seconds: number; text: string }

const voice = manifestJson as unknown as Record<string, { seconds: number }>

export const NARRATION: Line[] = (linesJson as LineSpec[]).flatMap((l) => {
  if (!clip(l.clip)) {
    console.warn(`line ${l.id}: no clip "${l.clip}" (run pnpm record?)`)
    return []
  }
  if (!voice[l.id]) {
    console.warn(`line ${l.id}: no voice clip (run pnpm voice)`)
    return []
  }
  return [{ id: l.id, at: after(l.clip, l.offset ?? 0.3), seconds: voice[l.id].seconds, text: l.text }]
})

NARRATION.forEach((l, i) => {
  const prev = NARRATION[i - 1]
  if (prev && prev.at + prev.seconds > l.at) console.warn(`line ${l.id} starts ${(prev.at + prev.seconds - l.at).toFixed(2)} s before ${prev.id} ends`)
})

/** The footage holds its last frame until the end card, which follows the last line after a breath. */
const lastEnd = NARRATION.reduce((a, l) => Math.max(a, l.at + l.seconds), VIDEO_END)
export const CARD_AT = lastEnd + 1.5
export const TOTAL = CARD_AT + 4.5

// --- camera -----------------------------------------------------------------------------------
/**
 * Points are in 1920×1080 px of the footage; s = 1 shows the whole screen. Stay wide; zoom only where the
 * narration is about text too small to read, at most ~1.25, never framing out what is being clicked.
 */
const WIDE = { x: 960, y: 540, s: 1 }
const k = (t: number, v: { x: number; y: number; s: number }): Key => ({ t, ...v })

/** Jump to `point` at `from` (put it on a cut), stay until `until`, then ease back over `ease` s (0 = jump, for a cut). */
export function zoom(from: number, point: { x: number; y: number; s: number }, until: number, ease = 0.9): Key[] {
  return [k(from, WIDE), k(from, point), k(until, point), k(until + ease, WIDE)]
}

/** Keys must be in time order. Example: ...zoom(after('dials', 0), { x: 768, y: 432, s: 1.25 }, after('reply', 0), 0) */
const endOf = (name: string) => clip(name)?.until ?? 0
/** The customer's page is a 720 px column in a 1440 px window: closer in, for the whole clip (hard cuts in and out). */
/** Just before the frame where a cut lands, so the zoom changes on exactly that frame (camAt gives the earlier key at a tie). */
const onFrame = (t: number) => Math.round(t * 30) / 30 - 0.001
const customer = (name: string, y: number, until = endOf(name)): Key[] => (clip(name) ? zoom(onFrame(clip(name)!.from), { x: 960, y, s: 1.25 }, onFrame(until), 0) : [])
export const CAMERA: Key[] = [k(0, WIDE), ...customer('order', 470), ...customer('summer-order', 470), ...customer('download', 600, TOTAL)]
