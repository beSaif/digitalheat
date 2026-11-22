/**
 * Narration: voice/lines.json → public/rec/voice/<id>.mp3 + voice/manifest.json (durations).
 * Only lines whose text, voice or model changed (or whose mp3 is missing) are regenerated; --force redoes all.
 * Lines are voiced TTS_CONCURRENCY at a time (default 3), and the manifest is saved after each one,
 * so an interrupted run picks up where it stopped. It does not depend on the footage, so it can run
 * while `pnpm record` films.
 *
 *   pnpm voice --dry     estimated length per line and in total, no API calls
 *
 * Voice ids are premade, so a key without the voices_read permission still works.
 * Jessica cgSgspJ2msm6clMCkdW9 (default) · Lily pFZP5JQG7iQjIQuC4Bku · Sarah EXAVITQu4vr4xnSDxMaL
 * George JBFqnCBsd6RMkjVDRZzb · Daniel onwK4e9ZLuTAKqWW03F9 · Brian nPczCjzI2devNBz1zQrb
 */
import 'dotenv/config'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const ROOT = new URL('..', import.meta.url).pathname
const OUT = join(ROOT, 'public', 'rec', 'voice')
const MANIFEST = join(ROOT, 'voice', 'manifest.json')
const KEY = process.env.ELEVENLABS_API_KEY ?? ''
const VOICE = process.env.ELEVENLABS_VOICE_ID || 'cgSgspJ2msm6clMCkdW9'
const MODEL = process.env.ELEVENLABS_MODEL || 'eleven_v3'
const CONCURRENCY = Number(process.env.TTS_CONCURRENCY || 3)
const force = process.argv.includes('--force')
const dry = process.argv.includes('--dry')

type LineSpec = { id: string; text: string }
type Entry = { seconds: number; hash: string }
const lines: LineSpec[] = JSON.parse(readFileSync(join(ROOT, 'voice', 'lines.json'), 'utf8'))

// --- budget: about 2.5 words per second, 5–17 s per line, ~2 min in total -------------------------
const estimate = (text: string) => text.split(/\s+/).filter(Boolean).length / 2.5
const est = lines.reduce((a, l) => a + estimate(l.text), 0)
for (const l of lines) {
  const s = estimate(l.text)
  if (dry || s < 5 || s > 17) console.log(`${s < 5 || s > 17 ? '!' : ' '} ${l.id.padEnd(14)} ~${s.toFixed(0)} s`)
}
console.log(`estimate: ${lines.length} lines, ~${Math.floor(est / 60)}:${String(Math.round(est % 60)).padStart(2, '0')} of narration${est > 240 ? '  (long: past ~4 min, cut lines or split into chapters)' : ''}`)
if (dry) process.exit(0)

if (!KEY) {
  console.error('Set ELEVENLABS_API_KEY in demo/.env')
  process.exit(1)
}

const old: Record<string, Entry> = existsSync(MANIFEST) ? JSON.parse(readFileSync(MANIFEST, 'utf8')) : {}
mkdirSync(OUT, { recursive: true })

const duration = (file: string) =>
  Number(String(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file])).trim())

async function speak(text: string, file: string) {
  for (let attempt = 0; ; attempt++) {
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}?output_format=mp3_44100_128`, {
      method: 'POST',
      headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        model_id: MODEL,
        // v3 takes stability 0 (creative), 0.5 (natural) or 1 (robust); v2 models also take similarity_boost/style
        voice_settings: MODEL === 'eleven_v3' ? { stability: 0.5 } : { stability: 0.55, similarity_boost: 0.8, style: 0.15, speed: 1.0 },
      }),
    })
    if (r.ok) return writeFileSync(file, Buffer.from(await r.arrayBuffer()))
    // 429: too many concurrent requests for the plan; back off and retry, as for server errors
    if ((r.status === 429 || r.status >= 500) && attempt < 4) {
      await new Promise((done) => setTimeout(done, 2000 * 2 ** attempt))
      continue
    }
    throw new Error(`tts: ${r.status} ${await r.text()}`)
  }
}

const fileOf = (l: LineSpec) => join(OUT, `${l.id}.mp3`)
const hashOf = (l: LineSpec) => createHash('sha1').update(`${VOICE}|${MODEL}|${l.text}`).digest('hex').slice(0, 12)

const manifest: Record<string, Entry> = {}
for (const l of lines) if (!force && old[l.id]?.hash === hashOf(l) && existsSync(fileOf(l))) manifest[l.id] = old[l.id]
/** In lines.json order; lines that were removed drop out. */
const save = () =>
  writeFileSync(MANIFEST, JSON.stringify(Object.fromEntries(lines.filter((l) => manifest[l.id]).map((l) => [l.id, manifest[l.id]])), null, 2) + '\n')
save()

const todo = lines.filter((l) => !manifest[l.id])
let next = 0
await Promise.all(
  Array.from({ length: Math.min(CONCURRENCY, todo.length) }, async () => {
    while (next < todo.length) {
      const l = todo[next++]
      await speak(l.text, fileOf(l))
      manifest[l.id] = { seconds: +duration(fileOf(l)).toFixed(3), hash: hashOf(l) }
      save()
      console.log(`${l.id} ok (${manifest[l.id].seconds.toFixed(1)} s)`)
    }
  }),
)

const total = Object.values(manifest).reduce((a, m) => a + m.seconds, 0)
console.log(`narration: ${lines.length} lines, ${total.toFixed(1)} s (${todo.length} voiced, ${lines.length - todo.length} kept)`)
