/**
 * The stage: one page that holds the live console (/live) and Lena's phone (/join → /node/<id>) as two
 * iframes, so a single screenshot loop films both, and the layout switches between
 *   'console'  the console full frame (phone parked off screen, still running)
 *   'split'    the console full frame with Lena's phone standing over the jobs panel on the right
 * Only one room screen (/) ever runs: it also renders the overview's own sites (base racks), and two of them
 * would fight over those racks.
 */
import type { Browser, BrowserContext, FrameLocator, Page } from 'playwright'
import { DPR, SIZE, prepare } from './film'

export const BASE = process.env.DEMO_BASE ?? 'http://localhost:3000'

/** Phone screen in CSS px, and how much it is scaled down on the stage. */
const PHONE = { w: 390, h: 844, s: 0.86 }
const BEZEL = 11

/** Cap every page's workers: seven pages × (cores − 1) workers would starve the screenshot loop. */
export const CORES = `Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 3 })`

const HTML = (phoneSrc: string) => `<!doctype html><html><head><style>
  html, body { margin: 0; width: ${SIZE.width}px; height: ${SIZE.height}px; overflow: hidden; background: #e8e4da; }
  #console { position: absolute; left: 0; top: 0; width: ${SIZE.width}px; height: ${SIZE.height}px; border: 0; }
  #phone-wrap { position: absolute; top: ${Math.round((SIZE.height - PHONE.h * PHONE.s) / 2 - BEZEL)}px; right: 26px;
    width: ${Math.round(PHONE.w * PHONE.s)}px; height: ${Math.round(PHONE.h * PHONE.s)}px; padding: ${BEZEL}px;
    background: #141412; border-radius: 46px; box-shadow: 0 24px 60px rgba(20,20,18,.35), 0 0 0 1.5px #3a3833 inset; }
  #phone-wrap.parked { left: 3000px; right: auto; }
  #screen { position: relative; width: 100%; height: 100%; border-radius: 36px; overflow: hidden; background: #f6f3ec; }
  #phone { width: ${PHONE.w}px; height: ${PHONE.h}px; border: 0; transform: scale(${PHONE.s}); transform-origin: 0 0; }
  #lock { position: absolute; inset: 0; background: linear-gradient(#1c1b19, #0b0b0a); color: #f6f3ec; display: none;
    flex-direction: column; align-items: center; padding-top: 90px; font: 600 64px/1 system-ui, sans-serif; letter-spacing: -1px; }
  #lock small { font: 500 15px system-ui, sans-serif; opacity: .7; margin-top: 10px; letter-spacing: 0; }
  #lock.on { display: flex; }
  #notch { position: absolute; top: 9px; left: 50%; width: 96px; height: 26px; margin-left: -48px; background: #141412; border-radius: 14px; z-index: 2; }
</style></head><body>
  <iframe id="console" src="${BASE}/?join=http://localhost:3000"></iframe>
  <div id="phone-wrap" class="parked"><div id="screen">
    <div id="notch"></div>
    <iframe id="phone" src="${phoneSrc}"></iframe>
    <div id="lock"><span id="clock">08:01</span><small>Locked</small></div>
  </div></div>
</body></html>`

export type Stage = { ctx: BrowserContext; page: Page; console: FrameLocator; phone: FrameLocator }

/**
 * A fresh stage. With `lena` set, her phone has already joined under that name (no form);
 * without it the phone opens /join and asks for a name.
 */
export async function openStage(browser: Browser, opts: { lena?: string } = {}): Promise<Stage> {
  const ctx = await browser.newContext({ viewport: SIZE, deviceScaleFactor: DPR })
  await ctx.addInitScript(CORES)
  if (opts.lena) await ctx.addInitScript(`localStorage.setItem('dh-live-name', ${JSON.stringify(opts.lena)})`)
  await prepare(ctx)
  // the stage lives on the app's own origin, so the iframes share its storage like a real browser would
  await ctx.route(`${BASE}/__stage`, (r) => r.fulfill({ contentType: 'text/html', body: HTML(`${BASE}/join`) }))
  const page = await ctx.newPage()
  page.on('dialog', (d) => d.accept())
  await page.goto(`${BASE}/__stage`)
  return { ctx, page, console: page.frameLocator('#console'), phone: page.frameLocator('#phone') }
}

export async function layout(st: Stage, mode: 'console' | 'split') {
  await st.page.evaluate(`document.getElementById('phone-wrap').classList.toggle('parked', ${mode === 'console'})`)
}

/** The phone's own frame, for evaluate(). */
const phoneFrame = (st: Stage) => st.page.frames().find((f) => f.url().includes('/node/') || f.url().includes('/join'))!

/** Lock the phone: the lock screen shows, and the page is told it is hidden (as iOS does). */
export async function lockPhone(st: Stage, clock: string) {
  await st.page.evaluate(`document.getElementById('clock').textContent = ${JSON.stringify(clock)}; document.getElementById('lock').classList.add('on')`)
  await phoneFrame(st).evaluate(`
    Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
    document.dispatchEvent(new Event('visibilitychange'))`)
}

/** Unlock: the lock screen goes, but the page stays hidden until showPhone() (so its offline screen shows). */
export async function unlockPhone(st: Stage) {
  await st.page.evaluate(`document.getElementById('lock').classList.remove('on')`)
}

/** The page is visible again: the server comes back in the same slot. */
export async function showPhone(st: Stage) {
  await phoneFrame(st).evaluate(`
    Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
    document.dispatchEvent(new Event('visibilitychange'))`)
}
