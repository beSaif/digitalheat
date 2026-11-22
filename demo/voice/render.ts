/**
 * Resumable render: the video in 20 s chunks (muted), the audio once, then joined and muxed.
 * Each chunk is named after a hash of everything the render reads (src/, cuts, narration, footage, voice),
 * so an interrupted render picks up at the first missing chunk, and any change starts a fresh set.
 *
 *   pnpm render            → out/walkthrough.mp4 + .srt + out/sheet-NN.jpg
 */
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { TOTAL } from '../src/data'
import { FPS } from '../src/theme'

const ROOT = new URL('..', import.meta.url).pathname
const PARTS = join(ROOT, 'out', 'parts')
const OUT = join(ROOT, 'out', 'walkthrough.mp4')
const CHUNK = 20 * FPS

const files = (dir: string): string[] =>
  existsSync(dir) ? readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)])) : []

// big media by size + mtime, code and JSON by content
const h = createHash('sha1')
for (const f of [...files(join(ROOT, 'src')), join(ROOT, 'capture', 'cuts.json'), join(ROOT, 'voice', 'lines.json'), join(ROOT, 'voice', 'manifest.json')].sort())
  h.update(relative(ROOT, f)).update(readFileSync(f))
for (const f of files(join(ROOT, 'public', 'rec')).sort()) {
  const st = statSync(f)
  h.update(`${relative(ROOT, f)}|${st.size}|${st.mtimeMs}`)
}
const hash = h.digest('hex').slice(0, 10)

mkdirSync(PARTS, { recursive: true })
for (const f of readdirSync(PARTS)) if (!f.startsWith(hash)) rmSync(join(PARTS, f)) // an older set

const frames = Math.round(TOTAL * FPS)
const remotion = (...args: string[]) => execFileSync('npx', ['remotion', 'render', 'Walkthrough', ...args], { cwd: ROOT, stdio: ['ignore', 'ignore', 'inherit'] })
const t0 = Date.now()

const parts: string[] = []
for (let a = 0, i = 0; a < frames; a += CHUNK, i++) {
  const b = Math.min(frames, a + CHUNK) - 1
  const file = join(PARTS, `${hash}-${String(i).padStart(2, '0')}.mp4`)
  parts.push(file)
  if (existsSync(file)) {
    console.log(`chunk ${i}: kept`)
    continue
  }
  const tmp = join(PARTS, `tmp-${i}.mp4`)
  console.log(`chunk ${i}: frames ${a}–${b}`)
  remotion(tmp, `--frames=${a}-${b}`, '--muted', '--codec', 'h264', '--crf', '20')
  renameSync(tmp, file) // only a finished chunk gets its real name
}

const audio = join(PARTS, `${hash}-audio.aac`)
if (!existsSync(audio)) {
  console.log('audio')
  const tmp = join(PARTS, 'tmp-audio.aac')
  remotion(tmp, '--codec', 'aac')
  renameSync(tmp, audio)
} else console.log('audio: kept')

const list = join(PARTS, `${hash}-list.txt`)
writeFileSync(list, parts.map((p) => `file '${p}'`).join('\n') + '\n')
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-i', audio, '-map', '0:v', '-map', '1:a', '-c', 'copy', '-shortest', '-movflags', '+faststart', OUT])
console.log(`${relative(ROOT, OUT)}: ${Math.floor(Math.round(TOTAL) / 60)}:${String(Math.round(TOTAL) % 60).padStart(2, '0')}, ${(statSync(OUT).size / 1e6).toFixed(1)} MB, ${((Date.now() - t0) / 1000).toFixed(0)} s`)
