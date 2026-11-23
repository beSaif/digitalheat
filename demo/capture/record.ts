/**
 * The live demo, filmed the way docs/demo-script.md presents it: from the house out to the fleet.
 *
 *   order    the customer orders a 3D render                                   (Customer)
 *   house    January, 08:00, -2 °C: the reference house in 3D, 11 of 11 servers (DigitalHeat)
 *   fleet    back to the map: the hospital and the spa render their share     (DigitalHeat)
 *   fill     Fill tank on the house: its part pauses, saves and moves on      (DigitalHeat)  case: the interrupted job
 *   summer   July, 14:00, 25 °C: the house down to 1 server, the spa busy      (DigitalHeat)  case: the July day
 *   realjob  the same scheduler pausing and resuming a real AI job (scheduler.live) on this laptop (This laptop)
 *
 *   REHEARSE=1 pnpm record          dry run, no camera: every selector and state check
 *   REHEARSE=1 SCENES=july pnpm record
 *   pnpm record                     film; finished scenes are checkpointed in capture/progress.json and skipped next time
 *   SCENES=july pnpm record         re-film one scene
 *
 * Needs the dashboard running as a production build at DEMO_BASE (cd ../dashboard && pnpm build && pnpm start)
 * and the repo's .venv with requirements-workloads.txt (the real job). No phones join: the fleet is the
 * overview's three sites, whose racks run on the room screen itself.
 * The previous video's story (Lena's phone, six buildings) is in git history.
 */
import 'dotenv/config'
import { spawn, type ChildProcess } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { chromium, type Browser, type Page } from 'playwright'
import { DPR, SIZE, click, cut, finish, hideCursor, hold, log, moveTo, point, prepare, ready, roll, scene, sleep } from './film'
import { api, logState, resetLive, running, settled, type State } from './app'
import { BASE, layout, openStage, type Stage } from './stage'

const CUSTOMER = 'Customer'
const DH = 'DigitalHeat'
const LAPTOP = 'This laptop'

const REPO = new URL('../..', import.meta.url).pathname
const HOUSE_ID = 'BS-01'
const HOUSE_NODE = 'base-bs-01'

/** The house in the scheduler's current hour: servers on, of how many. */
function house(s: State) {
  const i = s.sites.findIndex((x) => x.id === HOUSE_ID)
  const h = s.hour?.sites[i]
  return i < 0 || !h ? null : { on: Math.ceil(h.running - 1e-9), servers: s.sites[i].servers, demand: h.demand }
}

/** Pick a moment on the console (off camera) and wait for the scheduler's decision. */
async function moment(st: Stage, key: 'january' | 'july') {
  await ready('console made its first decision', async () => (await api()).conditions && !(await api()).planning, { timeout: 60_000, page: st.page })
  await sleep(1000)
  await st.console.getByRole('button', { name: key === 'january' ? 'January' : 'July' }).click()
  await ready(`${key}: scheduler decided`, settled(key, 0), { timeout: 60_000, page: st.page })
  await sleep(2000)
  return ready(`${key} still picked`, settled(key, 0), { timeout: 30_000, page: st.page })
}

/** A fresh room screen (no phones) at a moment, cursor parked off the pins. */
async function room(browser: Browser, key: 'january' | 'july') {
  await resetLive()
  const st = await openStage(browser)
  await layout(st, 'console')
  await ready('console loaded', async () => (await st.console.getByRole('button', { name: 'January' }).count()) > 0, { page: st.page })
  await moment(st, key)
  await moveTo(st.page, 720, 120)
  return st
}

/** The house's pin on the map (the racks panel has a "House" row too, but it isn't an absolutely placed button). */
const housePin = (st: Stage) => st.console.locator('button.absolute', { hasText: 'House' }).first()

async function clientPage(browser: Browser) {
  const ctx = await browser.newContext({ viewport: SIZE, deviceScaleFactor: DPR })
  await prepare(ctx)
  const page = await ctx.newPage()
  await page.goto(`${BASE}/client`)
  await page.getByRole('button', { name: /Order ·/ }).waitFor()
  await moveTo(page, 720, 420)
  return page
}

// --- the terminal: scheduler.live's real output, shown as it arrives ---------------------------------
const CMD = `.venv/bin/python -m scheduler.live --seconds-per-hour 5`
const SITE = [{ id: 'BS-01', kind: 'house', name: 'Reference house', lat: 47.56, lon: 7.59, servers: 11 }]

const TERMINAL = `<!doctype html><html><head><meta charset="utf-8"><style>
  html, body { margin: 0; width: ${SIZE.width}px; height: ${SIZE.height}px; overflow: hidden; background: #e8e4da; }
  .win { position: absolute; inset: 36px 60px; border-radius: 14px; background: #161512; box-shadow: 0 24px 60px rgba(20,20,18,.3);
    font: 400 21px/1.55 'IBM Plex Mono', ui-monospace, Menlo, monospace; color: #e9e4d8; overflow: hidden; }
  .bar { height: 40px; display: flex; align-items: center; gap: 8px; padding: 0 16px; background: #24221e; color: #9a958a; font-size: 14px; }
  .dot { width: 12px; height: 12px; border-radius: 50%; background: #4a4740; }
  .bar span { margin-left: 12px; }
  .body { padding: 22px 28px; }
  .cmd { color: #9a958a; white-space: pre-wrap; } .cmd b { color: #e9e4d8; font-weight: 500; }
  #lines div { white-space: pre; } .t { color: #6b675e; }
  .start, .resume { color: #8fd0d6; } .pause { color: #f2a65a; } .checkpoint { color: #f6c48b; }
  #job { position: absolute; left: 28px; right: 28px; bottom: 24px; padding: 16px 20px; border-radius: 10px; background: #211f1b;
    display: flex; justify-content: space-between; align-items: baseline; font-size: 20px; }
  #state { font-weight: 600; } #state.running { color: #8fd0d6; } #state.paused { color: #f2a65a; }
  #items { font-size: 26px; font-weight: 600; color: #f6f3ec; font-variant-numeric: tabular-nums; }
</style></head><body><div class="win">
  <div class="bar"><i class="dot"></i><i class="dot"></i><i class="dot"></i><span>digitalheat — scheduler.live — one server of the reference house, 15 July 2025</span></div>
  <div class="body">
    <div class="cmd">~/digitalheat $ <b>${CMD}</b></div>
    <div id="lines"></div>
  </div>
  <div id="job"><span>real AI job (text embeddings) · pid <span id="pid">–</span> · <span id="state">starting</span></span><span><span id="items">0</span> <span style="color:#9a958a">abstracts embedded</span></span></div>
</div></body></html>`

/** "[t=4687] pause (SIGSTOP): no heat this hour…" → hour of day and a colour class */
function termLine(raw: string) {
  const m = raw.match(/^\[t=(\d+)\] (.*)$/)
  if (!m) return null
  const hh = String(Number(m[1]) % 24).padStart(2, '0')
  const kind = /^pause/.test(m[2]) ? 'pause' : /^resume/.test(m[2]) ? 'resume' : /^start/.test(m[2]) ? 'start' : /^checkpoint/.test(m[2]) ? 'checkpoint' : ''
  return { html: `<span class="t">${hh}:00</span>  <span class="${kind}">${m[2].replace(/&/g, '&amp;').replace(/</g, '&lt;')}</span>`, kind }
}

type Status = { job?: { state: string; pid: number | null; items_done: number | null } }
const status = (): Status | null => {
  try {
    return JSON.parse(readFileSync(`${REPO}/runs/live/status.json`, 'utf8'))
  } catch {
    return null
  }
}

async function main() {
  const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] })
  let st: Stage | null = null
  let client: Page | null = null
  let proc: ChildProcess | null = null
  const fresh = async () => {
    await st?.ctx.close()
    await client?.context().close()
    st = null
    client = null
  }

  // 1. January: the customer orders, the house in 3D, then the fleet ---------------------------------
  await scene('january', async () => {
    await fresh()
    st = await room(browser, 'january')
    const s = st
    await logState('January')
    client = await clientPage(browser)
    const c = client

    await roll(c, 'order', CUSTOMER)
    await hold(1200)
    await click(c, c.getByRole('button', { name: '3D rendering' }))
    await hold(400)
    await click(c, c.getByRole('button', { name: 'Living room, evening' }))
    await hold(500)
    await point(c, c.getByText(/Price per/))
    await hold(900)
    await click(c, c.getByRole('button', { name: /Order ·/ }), { settle: 100 })
    await hold(1500)
    await cut()

    // off camera: the parts reach the racks, the house is running its share
    await ready('house busy with the render', async () => {
      const now = await api()
      const h = house(now)
      return running(now) && h && h.on > 0 && now.nodes.find((n) => n.id === HOUSE_NODE)?.current ? now : null
    }, { timeout: 60_000, page: s.page })
    await logState('January, rendering')
    // one render takes ~17 s; a second customer's order keeps the racks on through the house clip
    // (the narration says all eleven are on), instead of the house dropping to 0/11 halfway
    await api({ op: 'order', customer: 'a customer', kind: 'render', scene: 'day' })

    await roll(s.page, 'house', DH)
    await hold(800)
    await click(s.page, housePin(s))
    await hold(900)
    await click(s.page, s.console.getByRole('button', { name: '3D view' }))
    await hold(4000)
    await cut()

    // off camera: a fresh order, so the fleet clip shows an image being cut up and filled in by every building
    await ready('earlier renders done', async () => ((await api()).jobs.every((j) => j.doneAt) ? true : null), { timeout: 60_000, page: s.page })
    await api({ op: 'order', customer: 'a customer', kind: 'render', scene: 'gallery' })
    await ready('fresh render started', async () => {
      const now = await api()
      const j = now.jobs.at(-1)
      return j && j.tiles.some((t) => t.state !== 'pending') && j.tiles.filter((t) => t.state === 'done').length <= 3 ? true : null
    }, { timeout: 30_000, every: 100, page: s.page })

    await roll(s.page, 'fleet', DH)
    await click(s.page, s.console.getByRole('button', { name: 'Back to map' }))
    await moveTo(s.page, 720, 120)
    await hold(3000)
    await cut()
  })

  // 2. The interrupted job: fill the house's tank while it holds a part -------------------------------
  await scene('fill', async () => {
    await fresh()
    st = await room(browser, 'january')
    const s = st
    await api({ op: 'order', kind: 'render' })
    await ready('house holds a part', async () => {
      const now = await api()
      const n = now.nodes.find((x) => x.id === HOUSE_NODE)
      return n?.current && n.current.chunk >= 0 ? now : null
    }, { timeout: 90_000, page: s.page })
    await sleep(1500)

    await roll(s.page, 'fill', DH)
    await hold(800)
    await click(s.page, housePin(s))
    await ready('card says "Working on part"', async () => (await s.console.getByText(/Working on part \d+ now/).count()) > 0, { timeout: 20_000, page: s.page })
    await hold(1200)
    await click(s.page, s.console.getByRole('button', { name: 'Fill tank' }))
    await moveTo(s.page, 720, 120)
    await hold(6000)
    await cut()
  })

  // 3. July: the house down to hot water, the spa still busy --------------------------------------------
  await scene('july', async () => {
    await fresh()
    st = await room(browser, 'july')
    const s = st
    let last = 0
    await ready('July: house down to 1 server, a job running', async () => {
      const now = await api()
      const h = house(now)
      if (Date.now() - last > 30_000) {
        last = Date.now()
        log(`  house ${h?.on}/${h?.servers}, ${h?.demand.toFixed(2)} kW`)
      }
      if (!running(now)) await api({ op: 'order', kind: 'embed' })
      return h && h.on <= 1 && running(now) ? now : null
    }, { timeout: 10 * 60_000, every: 1000, page: s.page })
    await sleep(2000)
    await logState('July')

    await roll(s.page, 'summer', DH)
    await hold(1500)
    await moveTo(s.page, 720, 120)
    await hold(4000)
    const h = house(await api())
    if (!h || h.on > 1) throw new Error(`July drifted: house ${h?.on}`)
    await cut()
    await hideCursor(s.page)
  })

  // 4. The real job on this laptop ----------------------------------------------------------------------
  await scene('realjob', async () => {
    await fresh()
    await resetLive()
    const ctx = await browser.newContext({ viewport: SIZE, deviceScaleFactor: DPR })
    await prepare(ctx)
    await ctx.route(`${BASE}/__terminal`, (r) => r.fulfill({ contentType: 'text/html', body: TERMINAL }))
    const page = await ctx.newPage()
    await page.goto(`${BASE}/__terminal`)
    await hideCursor(page)

    const seen: string[] = []
    proc = spawn(`${REPO}/.venv/bin/python`, ['-m', 'scheduler.live', '--seconds-per-hour', '5', '--hours', '18', '--sites-json', JSON.stringify(SITE)], { cwd: REPO, stdio: ['ignore', 'pipe', 'pipe'] })
    let buf = ''
    proc.stdout!.on('data', (d: Buffer) => {
      buf += d.toString()
      const parts = buf.split('\n')
      buf = parts.pop()!
      for (const raw of parts) {
        const l = termLine(raw.trim())
        if (!l) continue
        seen.push(raw.trim())
        page.evaluate(`(() => { const d = document.createElement('div'); d.innerHTML = ${JSON.stringify(l.html)}; document.getElementById('lines').appendChild(d) })()`).catch(() => {})
      }
    })
    proc.stderr!.on('data', () => {})
    const poll = setInterval(() => {
      const st = status() as (Status & { pid?: number }) | null
      const j = st && st.pid === proc?.pid ? st.job : null
      if (!j) return
      page
        .evaluate(`(() => { const s = document.getElementById('state'); s.textContent = ${JSON.stringify(j.state === 'running' ? 'running' : j.state === 'paused' ? 'paused (SIGSTOP)' : j.state)}; s.className = ${JSON.stringify(j.state)};
          document.getElementById('pid').textContent = ${JSON.stringify(String(j.pid ?? '–'))};
          document.getElementById('items').textContent = ${JSON.stringify((j.items_done ?? 0).toLocaleString('en-US'))} })()`)
        .catch(() => {})
    }, 400)

    // off camera: the model loads (~20 s of running time); film once the job is embedding
    // status.json is shared with earlier runs: only trust it once it is this process's
    const mine = () => {
      const st = status() as (Status & { pid?: number }) | null
      return st && st.pid === proc?.pid ? st : null
    }
    await ready('real job embedding', async () => ((mine()?.job?.items_done ?? 0) > 0 ? true : null), { timeout: 150_000, page })
    log(`  terminal so far: ${seen.join(' | ')}`)

    const before = seen.length
    await roll(page, 'realjob', LAPTOP)
    await hold(24_000)
    // on camera: at least one pause and one resume (a rehearsal skips the hold, so wait for them)
    await ready('real job paused and resumed on camera', async () => {
      const k = seen.slice(before).map((x) => termLine(x)?.kind)
      return k.includes('pause') && k.includes('resume') ? true : null
    }, { timeout: 60_000, page })
    await hold(2000)
    await cut()
    clearInterval(poll)
    proc.kill('SIGINT')
    await new Promise((r) => proc!.once('exit', r))
    proc = null
    log(`  terminal: ${seen.slice(-8).join(' | ')}`)
    await ctx.close()
  })

  await browser.close()
  await finish()
  ;(proc as ChildProcess | null)?.kill("SIGINT")
}

main().catch(async (e) => {
  console.error(e)
  process.exit(1)
})
