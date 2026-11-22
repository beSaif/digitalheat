/** Talking to the live demo off camera: its API, the other hosts' phones, and the state checks scenes wait on. */
import type { Browser, BrowserContext } from 'playwright'
import { BASE, CORES } from './stage'
import { log, sleep } from './film'

export type Site = { id: string; name: string; person?: string; kind: string; servers: number; tank_kwh: number }
export type SiteHour = { demand: number; soc: number; running: number }
export type Node = { id: string; name: string; state: string; base: boolean; site: number; current: { jobId: number; chunk: number } | null }
export type Tile = { state: string; node: string | null; restarts: number }
export type Job = { id: number; kind: string; tiles: Tile[]; doneAt: number | null }
export type State = {
  conditions: { key: string } | null
  sites: Site[]
  hour: { sites: SiteHour[] } | null
  planning: boolean
  jobs: Job[]
  nodes: Node[]
  events: { text: string }[]
}

export async function api(body?: object): Promise<State> {
  const r = await fetch(`${BASE}/api/live`, body ? { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) } : { cache: 'no-store' })
  if (!r.ok) throw new Error(`api ${r.status}: ${await r.text()}`)
  return r.json()
}

/** The neighbours who join after Lena, in join order (the app gives them a pharma lab, family home, spa, office, greenhouse). */
export const NEIGHBOURS = ['Marco', 'Aisha', 'Jonas', 'Nora', 'Luca']

const hosts: BrowserContext[] = []

/** Each neighbour is a phone-sized page of its own (own storage = own device id). */
export async function joinHost(browser: Browser, name: string) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true })
  await ctx.addInitScript(CORES)
  await ctx.addInitScript(`localStorage.setItem('dh-live-name', ${JSON.stringify(name)})`)
  const p = await ctx.newPage()
  await p.goto(`${BASE}/join`)
  hosts.push(ctx)
  return ctx
}

export async function closeHosts() {
  await Promise.all(hosts.splice(0).map((c) => c.close().catch(() => {})))
}

/** A clean slate: every phone closed, then the coordinator forgets them and all jobs. */
export async function resetLive() {
  await closeHosts()
  await sleep(500)
  await api({ op: 'reset' })
}

// --- reading the state ---------------------------------------------------------------------------
export const siteIndex = (s: State, person: string) => s.sites.findIndex((x) => x.person === person)
export function siteOf(s: State, person: string) {
  const i = siteIndex(s, person)
  if (i < 0 || !s.hour?.sites[i]) return null
  const x = s.sites[i]
  const h = s.hour.sites[i]
  return { ...x, ...h, on: Math.ceil(h.running - 1e-9), full: h.soc / Math.max(1e-9, x.tank_kwh) }
}
export const nodeOf = (s: State, name: string) => s.nodes.find((n) => !n.base && n.name === name)
export const running = (s: State) => s.jobs.some((j) => !j.doneAt)

/** Racks placed and the scheduler's decision in, for this moment. */
export const settled = (key: string, people: number) => async () => {
  const s = await api()
  const placed = s.nodes.filter((n) => !n.base && n.site >= 0 && n.state !== 'offline' && n.state !== 'waiting').length
  return !s.planning && s.conditions?.key === key && s.hour && placed >= people ? s : null
}

export function describe(s: State) {
  return s.sites
    .map((x, i) => {
      const h = s.hour?.sites[i]
      return `${(x.person ?? x.name).padEnd(12)} ${h ? Math.ceil(h.running - 1e-9) : '-'}/${x.servers} on, ${h?.demand.toFixed(1)} kW, tank ${h ? Math.round((100 * h.soc) / x.tank_kwh) : '-'}%`
    })
    .join('\n  ')
}
export const logState = async (label: string) => log(`${label}\n  ${describe(await api())}`)
