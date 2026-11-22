/**
 * Filming helpers: a visible cursor, human-paced input, and a recorder that films only between
 * roll() and cut(). Frames are high-DPR screenshots (sharper than Playwright's recordVideo, which is
 * soft VP8), each stamped with its time so the clip plays back in real time.
 *
 *   await roll(page, 'start', 'Admin')   ... on camera ...   await cut()
 *   await slowThing()                    // off camera: waits, retries
 *   await roll(page, 'result', 'Admin')  ...                 await cut()
 *   await finish()                       // → public/rec/screen.mp4 + capture/cuts.json
 *
 * Re-film only some clips:  ONLY=result,share pnpm record
 * The other clips keep their file from the last run; their actions still run (so the app ends up in the
 * same state) but without pacing: no holds, instant cursor moves, typing at full speed.
 *
 * Each clip is encoded in the background while filming carries on, and gets a contact sheet
 * (out/clips/<name>.jpg, 20 frames across the clip) so it can be checked in one image.
 *
 * Checkpoints. The story is split into scenes (scene()); each one sets itself up off camera, so it does
 * not depend on the scenes before it. A scene that finishes is written to capture/progress.json with
 * its clips, and the next `pnpm record` skips it. A crash in scene 4 resumes at scene 4.
 *   SCENES=july pnpm record     re-film just these scenes (the others are kept)
 *   FRESH=1 pnpm record         forget progress.json, film everything
 *   REHEARSE=1 pnpm record      run every scene at full speed with no camera: checks every selector and
 *                               every ready() state in a couple of minutes, writes no clips or progress
 *
 * Clip length follows the narration: cut() keeps rolling until the clip's lines (voice/lines.json, real
 * durations from voice/manifest.json, else ~2.5 words/s) have finished, plus a breath.
 */
import { execFile } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { promisify } from 'node:util'
import type { BrowserContext, Locator, Page } from 'playwright'

export const SIZE = { width: 1440, height: 810 }
/** 1.5 keeps text crisp in the 1728 px screen box; drop to 1.25 if clips report < 20 fps. */
export const DPR = 1.5
const QUALITY = 88

const ROOT = new URL('..', import.meta.url).pathname
const CLIPS = join(ROOT, 'out', 'clips')
const SCREEN_OUT = join(ROOT, 'public', 'rec', 'screen.mp4')
const CUTS_OUT = join(ROOT, 'capture', 'cuts.json')

const PROGRESS = join(ROOT, 'capture', 'progress.json')

const run = promisify(execFile)
const list = (v?: string) => new Set((v ?? '').split(',').map((s) => s.trim()).filter(Boolean))
const ONLY = list(process.env.ONLY)
const SCENES = list(process.env.SCENES)
export const REHEARSE = !!process.env.REHEARSE
/** PART=1: film only SCENES and stop (another recorder films the rest at the same time); a plain run joins them. */
const PART = !!process.env.PART
/** True while a clip that is not being re-filmed plays through: same actions, no pacing. */
let fast = false

export const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))
/** A human-paced pause; skipped while a kept clip plays through. */
const pace = (ms: number) => (fast || REHEARSE ? Promise.resolve() : sleep(ms))
/** Hold the current frame for a moment (on camera). */
export const hold = (ms: number) => pace(ms)
export const log = (m: string) => console.log(`${new Date().toISOString().slice(11, 19)} ${m}`)

// --- cursor and input --------------------------------------------------------------------------
const CURSOR_SCRIPT = `
  (() => {
    const make = () => {
      if (document.getElementById('__cur')) return
      if (location.pathname === '/__stage') return // the stage itself: its iframes draw their own
      // a phone screen gets a fingertip, not an arrow
      const touch = window !== window.top && window.innerWidth < 500
      const c = document.createElement('div')
      c.id = '__cur'
      c.style.cssText = touch
        ? 'position:fixed;left:0;top:0;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:rgba(20,20,18,.22);box-shadow:0 0 0 2px rgba(255,255,255,.7);pointer-events:none;z-index:2147483647;transition:opacity .25s;opacity:0'
        : 'position:fixed;left:0;top:0;width:22px;height:30px;pointer-events:none;z-index:2147483647;transform:translate(-3px,-2px);transition:opacity .2s;opacity:0'
      if (!touch) c.innerHTML = '<svg width="22" height="30" viewBox="0 0 22 30"><path d="M2 2 L2 23 L7.5 18 L11 27 L15 25.5 L11.5 16.5 L19 16.5 Z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>'
      document.documentElement.appendChild(c)
      window.addEventListener('mousemove', (e) => { c.style.opacity = touch ? '0.9' : '1'; c.style.transform = 'translate(' + (e.clientX - (touch ? 0 : 3)) + 'px,' + (e.clientY - (touch ? 0 : 2)) + 'px)' }, true)
      // the pointer left this frame (into another iframe): hide, so two cursors never show
      document.documentElement.addEventListener('mouseleave', () => { c.style.opacity = '0' })
      // a finger lifts off the glass: the touch dot fades out shortly after each tap
      const press = (on) => { if (touch) { c.style.background = on ? 'rgba(192,101,58,.45)' : 'rgba(20,20,18,.22)'; if (!on) setTimeout(() => { c.style.opacity = '0' }, 350) } else { c.firstElementChild.style.transform = on ? 'scale(.85)' : ''; c.firstElementChild.style.transformOrigin = '3px 2px' } }
      window.addEventListener('mousedown', () => press(true), true)
      window.addEventListener('mouseup', () => press(false), true)
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', make)
    else make()
  })()
`

/** Hide the cursor in every frame of `page` until the mouse moves again (for shots nobody is clicking in). */
export async function hideCursor(page: Page) {
  await Promise.all(page.frames().map((f) => f.evaluate(`document.getElementById('__cur') && (document.getElementById('__cur').style.opacity = '0')`).catch(() => {})))
}

/** Call once per browser context, before opening pages. */
export async function prepare(ctx: BrowserContext) {
  await ctx.addInitScript(CURSOR_SCRIPT)
}

const mouseAt = new WeakMap<Page, { x: number; y: number }>()

/** Glide the cursor to (x, y), in more steps the further it goes. */
export async function moveTo(page: Page, x: number, y: number) {
  const from = mouseAt.get(page) ?? { x: SIZE.width / 2, y: SIZE.height / 2 }
  const steps = fast || REHEARSE ? 1 : Math.max(8, Math.min(28, Math.round(Math.hypot(x - from.x, y - from.y) / 25)))
  await page.mouse.move(x, y, { steps })
  mouseAt.set(page, { x, y })
}

/** Scroll the element to a comfortable spot and move the cursor onto it, without clicking. */
export async function point(page: Page, target: Locator) {
  await target.first().waitFor({ state: 'visible' })
  await target.first().evaluate((el, behavior) => el.scrollIntoView({ block: 'center', behavior }), (fast || REHEARSE ? 'instant' : 'smooth') as ScrollBehavior)
  await pace(300)
  const box = await target.first().boundingBox()
  if (!box) throw new Error('no box')
  await moveTo(page, box.x + box.width / 2 + (Math.random() * 6 - 3), box.y + box.height / 2 + (Math.random() * 4 - 2))
}

/** Point at the element and click it like a person would. */
export async function click(page: Page, target: Locator, opts: { settle?: number } = {}) {
  await point(page, target)
  await pace(120)
  await page.mouse.down()
  await pace(70)
  await page.mouse.up()
  await pace(opts.settle ?? 250)
}

/**
 * Click the field, then type: the first `lead` characters at a careful pace, the rest at `cps`.
 * Rough speeds: names 14, titles 26, chat 90–110, notes 150, long prose 400+.
 */
export async function type(page: Page, target: Locator, text: string, opts: { cps?: number; lead?: number } = {}) {
  await click(page, target, { settle: 200 })
  if (fast || REHEARSE) {
    await target.first().pressSequentially(text)
    return
  }
  const cps = opts.cps ?? 40
  const lead = Math.min(text.length, opts.lead ?? 12)
  await target.first().pressSequentially(text.slice(0, lead), { delay: 1000 / Math.min(cps, 18) })
  if (text.length > lead) await target.first().pressSequentially(text.slice(lead), { delay: 1000 / cps })
  await sleep(250)
}

/** Ease-in-out scroll of the window by `dy` px. */
export async function smoothScroll(page: Page, dy: number, ms = 1200) {
  if (fast || REHEARSE) return void (await page.evaluate(`window.scrollBy(0, ${dy})`))
  // passed as a string: tsx's keepNames helper (__name) does not exist inside the page
  await page.evaluate(
    `new Promise((done) => {
      const dy = ${dy}, ms = ${ms}, y0 = window.scrollY, t0 = performance.now()
      const tick = () => {
        const p = Math.min(1, (performance.now() - t0) / ms)
        const e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2
        window.scrollTo(0, y0 + dy * e)
        if (p < 1) requestAnimationFrame(tick); else done()
      }
      requestAnimationFrame(tick)
    })`,
  )
}

// --- filming -----------------------------------------------------------------------------------
type Frame = { file: string; t: number }
type Rolling = { name: string; dir: string; file: string; t0: number; frames: Frame[]; stop: { v: boolean }; loop: Promise<void>; needs: number }
type Clip = { name: string; who: string; file: string; done: Promise<void> }

let rolling: Rolling | null = null
const clips: Clip[] = []

/** Start filming `page` as a new clip. `who` is the role tag shown under the screen ('' for none). */
export async function roll(page: Page, name: string, who = '') {
  await cut()
  if (clips.some((c) => c.name === name)) throw new Error(`clip name "${name}" used twice`)
  sceneClips?.push({ name, who })
  if (REHEARSE) {
    clips.push({ name, who, file: '', done: Promise.resolve() })
    log(`(rehearse) ${name}`)
    return
  }
  const file = join(CLIPS, `${name}.mp4`)
  if (ONLY.size && !ONLY.has(name)) {
    if (!existsSync(file)) throw new Error(`clip "${name}" has no file from an earlier run; add it to ONLY`)
    clips.push({ name, who, file, done: Promise.resolve() })
    fast = true
    log(`keep ${name}`)
    return
  }
  fast = false
  const dir = join(CLIPS, name)
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  const frames: Frame[] = []
  const stop = { v: false }
  const t0 = Date.now()
  // Chromium's screencast pushes a JPEG for every painted frame (~60 fps), where screenshot() managed ~8
  const cdp = await page.context().newCDPSession(page)
  cdp.on('Page.screencastFrame', (f: { data: string; sessionId: number }) => {
    if (stop.v) return
    const frame = join(dir, `${String(frames.length).padStart(5, '0')}.jpg`)
    writeFileSync(frame, Buffer.from(f.data, 'base64'))
    frames.push({ file: frame, t: frames.length ? (Date.now() - t0) / 1000 : 0 })
    cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {})
  })
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: QUALITY, maxWidth: Math.round(SIZE.width * DPR), maxHeight: Math.round(SIZE.height * DPR) })
  const loop = (async () => {
    while (!stop.v) await sleep(50)
    await cdp.send('Page.stopScreencast').catch(() => {})
    await cdp.detach().catch(() => {})
  })()
  rolling = { name, dir, file, t0, frames, stop, loop, needs: narrationNeeds(name) }
  clips.push({ name, who, file, done: Promise.resolve() })
  log(`roll ${name}`)
}

/** Encode the frames into the clip and its contact sheet, then drop the frames. */
async function encode(r: Rolling, end: number) {
  // concat list with per-frame durations, so the clip plays in real time
  const list = r.frames.map((f, i) => `file '${f.file}'\nduration ${((r.frames[i + 1]?.t ?? end) - f.t).toFixed(3)}`).join('\n')
  writeFileSync(join(r.dir, 'list.txt'), `${list}\nfile '${r.frames.at(-1)!.file}'\n`)
  // veryfast at CRF 14 is still near-lossless, and the final render re-encodes anyway; 2 threads leave
  // the CPU to the screenshot loop of the clip being filmed meanwhile
  await run('ffmpeg', [
    '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', join(r.dir, 'list.txt'),
    '-vf', `fps=30,scale=${Math.round(SIZE.width * DPR)}:${Math.round(SIZE.height * DPR / 2) * 2},format=yuv420p`,
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-threads', '2', '-movflags', '+faststart', r.file,
  ])
  await run('ffmpeg', [
    '-y', '-loglevel', 'error', '-i', r.file,
    '-vf', `fps=${(20 / Math.max(end, 1)).toFixed(4)},scale=384:-2,tile=5x4`, '-frames:v', '1', '-q:v', '4', r.file.replace(/\.mp4$/, '.jpg'),
  ])
  rmSync(r.dir, { recursive: true, force: true })
}

/** Stop filming; the clip encodes in the background. Everything until the next roll() stays off camera. */
export async function cut() {
  fast = false
  if (!rolling) return
  const r = rolling
  rolling = null
  const short = r.needs - (Date.now() - r.t0) / 1000
  if (short > 0) {
    log(`hold ${r.name} ${short.toFixed(1)} s more for its narration`)
    await sleep(short * 1000)
  }
  r.stop.v = true
  await r.loop
  const end = (Date.now() - r.t0) / 1000
  if (!r.frames.length) throw new Error(`clip ${r.name} has no frames`)
  const clip = clips.find((c) => c.name === r.name)!
  clip.done = encode(r, end)
  clip.done.catch(() => {}) // reported by finish()
  const fps = r.frames.length / end
  log(`cut  ${r.name}: ${end.toFixed(1)} s, ${fps.toFixed(1)} fps captured${fps < 20 ? '  (low: lower DPR or QUALITY in film.ts)' : ''}`)
}

const duration = async (file: string) =>
  Number((await run('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file])).stdout.trim())

/** Wait for the encodes, join all clips into public/rec/screen.mp4 and write their times on the output timeline to capture/cuts.json. */
export async function finish() {
  await cut()
  if (REHEARSE) return log(`rehearsal passed: ${clips.length} clips`)
  if (PART) {
    await Promise.all(clips.map((c) => c.done))
    return log(`part done: ${clips.map((c) => c.name).join(', ')}`)
  }
  if (!clips.length) throw new Error('nothing filmed')
  await Promise.all(clips.map((c) => c.done))
  mkdirSync(join(ROOT, 'public', 'rec'), { recursive: true })
  const list = join(CLIPS, 'clips.txt')
  writeFileSync(list, clips.map((c) => `file '${c.file}'`).join('\n') + '\n')
  await run('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', SCREEN_OUT])
  let at = 0
  const cuts = []
  for (const c of clips) {
    const d = await duration(c.file)
    cuts.push({ name: c.name, who: c.who, from: +at.toFixed(3), until: +(at + d).toFixed(3) })
    at += d
  }
  writeFileSync(CUTS_OUT, JSON.stringify(cuts, null, 2) + '\n')
  log(`screen.mp4: ${clips.length} clips, ${at.toFixed(1)} s → ${SCREEN_OUT}`)
}

// --- narration-driven length -------------------------------------------------------------------
/** Seconds a clip must last so its narration lines finish inside it (plus a breath). */
function narrationNeeds(clip: string) {
  const lines: { id: string; clip: string; offset?: number; text: string }[] = JSON.parse(readFileSync(join(ROOT, 'voice', 'lines.json'), 'utf8'))
  const manifestFile = join(ROOT, 'voice', 'manifest.json')
  const voiced: Record<string, { seconds: number }> = existsSync(manifestFile) ? JSON.parse(readFileSync(manifestFile, 'utf8')) : {}
  return lines
    .filter((l) => l.clip === clip)
    .reduce((a, l) => Math.max(a, (l.offset ?? 0.3) + (voiced[l.id]?.seconds ?? l.text.split(/\s+/).length / 2.5) + 0.8), 0)
}

// --- off-camera waits --------------------------------------------------------------------------
/**
 * Wait (off camera) until `check` returns something truthy, polling every `every` ms. On timeout, save a
 * screenshot of `page` to out/fail-<what>.png and throw with `what`, so a run stops *before* filming
 * a clip whose state is wrong, not after.
 */
export async function ready<T>(what: string, check: () => Promise<T | null | undefined | false>, opts: { timeout?: number; every?: number; page?: Page } = {}): Promise<T> {
  const t0 = Date.now()
  const timeout = opts.timeout ?? 30_000
  let last = 0
  for (;;) {
    const v = await check().catch(() => null)
    if (v) {
      if (Date.now() - t0 > 3000) log(`ready: ${what} (${((Date.now() - t0) / 1000).toFixed(0)} s)`)
      return v
    }
    if (Date.now() - t0 > timeout) {
      const shot = join(ROOT, 'out', `fail-${what.replace(/[^a-z0-9]+/gi, '-').slice(0, 40)}.png`)
      if (opts.page) await opts.page.screenshot({ path: shot }).catch(() => {})
      throw new Error(`not ready after ${timeout / 1000} s: ${what}${opts.page ? ` (see ${shot})` : ''}`)
    }
    if (Date.now() - last > 15_000) {
      last = Date.now()
      if (Date.now() - t0 > 1000) log(`waiting: ${what}…`)
    }
    await sleep(opts.every ?? 500)
  }
}

// --- scenes and checkpoints --------------------------------------------------------------------
type Progress = Record<string, { clips: { name: string; who: string }[]; at: string }>
const progress: Progress = !process.env.FRESH && existsSync(PROGRESS) ? JSON.parse(readFileSync(PROGRESS, 'utf8')) : {}
let sceneClips: { name: string; who: string }[] | null = null

/**
 * One self-contained part of the story. `fn` sets the app up off camera, then films its clips. A scene in
 * capture/progress.json is skipped (its clips are kept), unless SCENES names it; ONLY still works inside.
 */
export async function scene(name: string, fn: () => Promise<void>) {
  if (REHEARSE && SCENES.size && !SCENES.has(name)) return log(`scene ${name}: not rehearsed`)
  const done = progress[name]
  const wanted = SCENES.size ? SCENES.has(name) : !done
  if (!REHEARSE && !wanted && done && done.clips.every((c) => existsSync(join(CLIPS, `${c.name}.mp4`)))) {
    for (const c of done.clips) clips.push({ name: c.name, who: c.who, file: join(CLIPS, `${c.name}.mp4`), done: Promise.resolve() })
    log(`scene ${name}: kept (${done.clips.map((c) => c.name).join(', ')})`)
    return
  }
  if (PART && SCENES.size && !SCENES.has(name)) return log(`scene ${name}: left to the other recorder`)
  if (!REHEARSE && SCENES.size && !SCENES.has(name)) throw new Error(`scene ${name} has no clips from an earlier run; add it to SCENES`)
  log(`scene ${name}${REHEARSE ? ' (rehearse)' : ''}`)
  sceneClips = []
  const t0 = Date.now()
  await fn()
  await cut()
  const mine = sceneClips
  sceneClips = null
  if (REHEARSE) return log(`scene ${name}: ok in ${((Date.now() - t0) / 1000).toFixed(0)} s`)
  // checkpoint only once its clips are encoded
  await Promise.all(clips.filter((c) => mine.some((m) => m.name === c.name)).map((c) => c.done))
  progress[name] = { clips: mine, at: new Date().toISOString() }
  // merge with what other recorders saved meanwhile
  const onDisk: Progress = existsSync(PROGRESS) ? JSON.parse(readFileSync(PROGRESS, 'utf8')) : {}
  writeFileSync(PROGRESS, JSON.stringify({ ...onDisk, [name]: progress[name] }, null, 2) + '\n')
  log(`scene ${name}: saved (${mine.map((c) => c.name).join(', ')})`)
}
