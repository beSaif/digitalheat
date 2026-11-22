/**
 * The live demo, filmed: Lena joins as a host, the customer orders, the console shows where the work goes,
 * in January and in July, and the customer downloads the result.
 *
 *   REHEARSE=1 pnpm record         dry run, no camera: every selector and state check, ~10 min (July fills tanks)
 *   REHEARSE=1 SCENES=july pnpm record
 *   pnpm record                    film; finished scenes are checkpointed in capture/progress.json and skipped next time
 *   SCENES=july pnpm record        re-film one scene
 *
 * Needs the dashboard running as a production build at DEMO_BASE (cd ../dashboard && pnpm build && pnpm start).
 * Every scene resets the live coordinator and sets itself up off camera, so scenes don't depend on each other.
 */
import 'dotenv/config'
import { chromium, type Browser, type Page } from 'playwright'
import { DPR, SIZE, click, cut, finish, hideCursor, hold, log, moveTo, point, prepare, ready, roll, scene, sleep, type } from './film'
import { NEIGHBOURS, api, closeHosts, joinHost, logState, nodeOf, resetLive, running, settled, siteOf } from './app'
import { BASE, layout, openStage, type Stage } from './stage'

const LENA = 'Lena'
const HOME = 'Homeowner'
const CUSTOMER = 'Customer'
const DH = 'DigitalHeat'

/**
 * Pick a moment on the console (off camera) and wait for the scheduler's decision. The console posts its
 * own "Now" when it first loads, so wait for that first, then check the pick stuck.
 */
async function moment(st: Stage, key: 'january' | 'july', people: number) {
  await ready('console made its first decision', async () => (await api()).conditions && !(await api()).planning, { timeout: 60_000, page: st.page })
  await sleep(1000)
  await st.console.getByRole('button', { name: key === 'january' ? 'January' : 'July' }).click()
  await ready(`${key}: scheduler decided, ${people} racks placed`, settled(key, people), { timeout: 60_000, page: st.page })
  await sleep(2000)
  return ready(`${key} still picked`, settled(key, people), { timeout: 30_000, page: st.page })
}

/** Stage + Lena (already joined) + the neighbours, at a moment. */
async function fleet(browser: Browser, key: 'january' | 'july') {
  await resetLive()
  const st = await openStage(browser, { lena: LENA })
  await ready('console loaded', async () => (await st.console.getByRole('button', { name: 'January' }).count()) > 0, { page: st.page })
  await layout(st, 'split')
  for (const n of NEIGHBOURS) {
    await joinHost(browser, n)
    await sleep(400)
  }
  await moment(st, key, 1 + NEIGHBOURS.length)
  await moveTo(st.page, 1432, 420) // off the map pins (no tooltip)
  await hideCursor(st.page) // nobody clicks in these shots
  return st
}

async function clientPage(browser: Browser) {
  const ctx = await browser.newContext({ viewport: SIZE, deviceScaleFactor: DPR })
  await prepare(ctx)
  const page = await ctx.newPage()
  await page.goto(`${BASE}/client`)
  await page.getByRole('button', { name: /Order ·/ }).waitFor()
  await moveTo(page, 720, 420)
  return page
}

async function main() {
  const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] })
  let st: Stage | null = null
  let client: Page | null = null
  const fresh = async () => {
    await st?.ctx.close()
    await client?.context().close()
    st = null
    client = null
  }

  // 1. Lena joins, her house appears; the neighbours follow -----------------------------------------
  await scene('join', async () => {
    await fresh()
    await resetLive()
    st = await openStage(browser)
    const s = st
    await ready('console loaded', async () => (await s.console.getByRole('button', { name: 'January' }).count()) > 0, { page: s.page })
    await moment(s, 'january', 0)
    await ready('phone asks for a name', async () => (await s.phone.getByPlaceholder('Your first name').count()) > 0, { page: s.page })
    await layout(s, 'split')
    await moveTo(s.page, 1230, 640)

    await roll(s.page, 'join', HOME)
    await hold(1200)
    await type(s.page, s.phone.getByPlaceholder('Your first name'), LENA, { cps: 9, lead: 4 })
    await hold(500)
    await click(s.page, s.phone.getByRole('button', { name: 'Join the fleet' }))
    await ready('Lena on the map', async () => (await s.console.getByText(LENA, { exact: true }).count()) > 0, { page: s.page })
    await hold(2500)
    await cut()

    await layout(s, 'console')
    await roll(s.page, 'fleet', DH)
    await hold(1500)
    for (const n of NEIGHBOURS) {
      await joinHost(browser, n)
      await hold(1600)
    }
    await ready('all six racks placed', settled('january', 6), { page: s.page })
    await hold(1500)
    await cut()
  })

  // 2. January: the customer orders a render, every rack takes part ------------------------------
  await scene('january', async () => {
    await fresh()
    st = await fleet(browser, 'january')
    const s = st
    const all = await api()
    if (!all.hour!.sites.every((x) => x.running > 0)) throw new Error('January: not every building needs heat')
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
    await cut()

    await roll(s.page, 'winter', DH)
    await ready('render started', async () => running(await api()), { page: s.page })
    await hold(1500)
    await cut() // cut() holds until both narration lines have played
    await logState('January after the render')
  })

  // 3. July: tanks full, homes need only hot water, the work goes where heat is still wanted -------
  await scene('july', async () => {
    await fresh()
    st = await fleet(browser, 'july')
    const s = st
    await logState('July, start')
    // fill the tanks off camera: work only makes heat while there is a job, so keep feeding small ones
    let last = 0
    await ready(
      'July tanks full: Lena down to 1 server, greenhouse off',
      async () => {
        const now = await api()
        const lena = siteOf(now, LENA)
        const luca = siteOf(now, 'Luca')
        if (Date.now() - last > 30_000) {
          last = Date.now()
          log(`  Lena ${lena?.on}/${lena?.servers} tank ${Math.round(100 * (lena?.full ?? 0))}% · Luca ${luca?.on}/${luca?.servers} tank ${Math.round(100 * (luca?.full ?? 0))}%`)
        }
        if (lena && luca && lena.on <= 1 && luca.on === 0) return now
        if (!running(now)) await api({ op: 'order', kind: 'embed' })
        return null
      },
      { timeout: 12 * 60_000, every: 1000, page: s.page },
    )
    await ready('filler jobs done', async () => !running(await api()), { timeout: 120_000 })
    await logState('July, tanks full')
    client = await clientPage(browser)
    const c = client

    await roll(c, 'summer-order', CUSTOMER)
    await hold(1000)
    await click(c, c.getByRole('button', { name: 'AI reranking' }))
    await hold(500)
    await click(c, c.getByRole('button', { name: 'Aspirin inhibits the production of PGE2.' }))
    await hold(900)
    await click(c, c.getByRole('button', { name: /Order ·/ }), { settle: 100 })
    await cut()

    await roll(s.page, 'summer', DH)
    await hold(1000)
    const now = await api()
    const lena = siteOf(now, LENA)!
    const luca = siteOf(now, 'Luca')!
    if (lena.on > 1 || luca.on !== 0) throw new Error(`July drifted: Lena ${lena.on}, Luca ${luca.on}`)
    await cut()
  })

  // 4. The customer downloads the result ---------------------------------------------------------
  await scene('result', async () => {
    await fresh()
    st = await fleet(browser, 'january')
    client = await clientPage(browser)
    const c = client
    await click(c, c.getByRole('button', { name: '3D rendering' }))
    await click(c, c.getByRole('button', { name: 'Living room, evening' }))
    await click(c, c.getByRole('button', { name: /Order ·/ }))
    await ready('render done', async () => (await api()).jobs.every((j) => j.doneAt), { timeout: 180_000, page: c })
    await sleep(1500)
    const dl = c.getByRole('button', { name: /Download/ }).first()
    await dl.evaluate((el) => el.scrollIntoView({ block: 'center' }))
    await moveTo(c, 720, 300)

    await roll(c, 'download', CUSTOMER)
    await hold(1500)
    await click(c, dl)
    await hold(2000)
    await cut()
  })

  await closeHosts()
  await browser.close()
  await finish()
}

main().catch(async (e) => {
  console.error(e)
  await closeHosts().catch(() => {})
  process.exit(1)
})
