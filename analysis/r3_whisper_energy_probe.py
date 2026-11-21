"""Round 3, weak point "machine and income": a FIRST laptop measurement of E,
the gross Wh per audio-hour of J1 (mlx_whisper + whisper-large-v3-turbo).

Exploratory. Not the scheduler, not the demo job. Standard library only; it calls
the already installed `mlx_whisper` CLI and macOS `say` and `ioreg` as subprocesses.
Nothing is downloaded (HF_HUB_OFFLINE=1). No sudo.

    python3 analysis/r3_whisper_energy_probe.py                       # 40 min of audio, 3 back-to-back runs
    python3 analysis/r3_whisper_energy_probe.py --minutes 20 --runs 4 --idle-s 120

Audio: macOS text-to-speech (`say`) reading the repo's own case texts, 16 kHz mono WAV.
Clean synthetic speech, NOT real recordings.

Power: the laptop's battery controller publishes, in `ioreg -c AppleSmartBattery`,
PowerTelemetryData.AccumulatedSystemLoad (sum of mW samples) and
SystemLoadAccumulatorCount (number of samples, about 1 per second). The registry
copy refreshes once per minute (field UpdateTime). The mean system load over one
refresh interval is d(AccumulatedSystemLoad) / d(SystemLoadAccumulatorCount) in mW.
SystemLoad = adapter input + battery discharge, so it stays right when a small
adapter cannot carry the load. Whole device (SoC, display, SSD, and every other
process running at the time), so it is GROSS power. Not checked against a wall
meter; adapter losses are not included. An earlier version of this script read the
instantaneous field SystemPowerIn once per second; that field is the once-a-minute
snapshot and only counts the adapter, so it gave nonsense (kept in the research file).

E_gross = mean system load inside the job windows x total job runtime / audio-hours
E_net   = (job-window mean - idle-window mean) x runtime / audio-hours
Only refresh intervals that lie entirely inside the job span (or entirely inside an
idle phase) are used.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "mlx-community/whisper-large-v3-turbo"
TEXTS = ["docs/case-brief.md", "docs/assumption-limits.md", "docs/event.md"]


def find_exe(name):
    for p in (os.path.expanduser(f"~/miniforge3/bin/{name}"), os.path.expanduser(f"~/.local/bin/{name}")):
        if os.path.exists(p):
            return p
    return name


def snapshot():
    out = subprocess.run(["ioreg", "-rw0", "-c", "AppleSmartBattery"], capture_output=True, text=True).stdout
    g = lambda k: (int(m.group(1)) if (m := re.search(r'"%s"\s*=\s*(\d+)' % k, out)) else None)
    return {"update": g("UpdateTime"), "acc": g("AccumulatedSystemLoad"), "cnt": g("SystemLoadAccumulatorCount"),
            "adapter_w": g("Watts")}


class Poller(threading.Thread):
    """Records every registry refresh as (local time seen, UpdateTime, acc, cnt)."""

    def __init__(self):
        super().__init__(daemon=True)
        self.points, self._stop = [], threading.Event()

    def run(self):
        last = None
        while not self._stop.is_set():
            s = snapshot()
            if s["update"] != last and s["acc"] is not None:
                self.points.append((time.time(), s["update"], s["acc"], s["cnt"]))
                last = s["update"]
            self._stop.wait(1.0)

    def stop(self):
        self._stop.set()
        self.join()

    def intervals(self):
        """(start, end, mean W) per refresh interval, using UpdateTime as the clock."""
        out = []
        for (_, u0, a0, c0), (_, u1, a1, c1) in zip(self.points, self.points[1:]):
            if c1 > c0:
                out.append((u0, u1, (a1 - a0) / (c1 - c0) / 1000.0))
        return out


def clean_text(paths, words_needed):
    words = []
    for p in paths:
        t = (ROOT / p).read_text(encoding="utf-8")
        t = re.sub(r"<[^>]+>", " ", t)
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
        t = re.sub(r"https?://\S+", " ", t)
        t = re.sub(r"[#*|`>_]", " ", t)
        words += t.split()
    out = []
    while len(out) < words_needed:
        out += words
    return " ".join(out[:words_needed])


def mean(x):
    return sum(x) / len(x) if x else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=40.0, help="target audio length per run")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--idle-s", type=float, default=180.0, help="idle phase before and after")
    ap.add_argument("--tmp", default=os.path.join(tempfile.gettempdir(), "r3mi_machine_income_probe"))
    a = ap.parse_args()
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    s = snapshot()
    print(f"telemetry check: UpdateTime={s['update']}, AccumulatedSystemLoad={s['acc']}, count={s['cnt']}, adapter {s['adapter_w']} W")
    if s["acc"] is None:
        sys.exit("no AccumulatedSystemLoad field; cannot measure power on this machine")

    wav, txt = tmp / "r3mi_tts_audio.wav", tmp / "r3mi_tts_text.txt"
    words = int(a.minutes * 162)  # `say` speaks about 162 words per minute (measured: 1,700 words in 628.6 s)
    txt.write_text(clean_text(TEXTS, words), encoding="utf-8")
    t0 = time.time()
    subprocess.run(["say", "-f", str(txt), "-o", str(wav), "--file-format=WAVE", "--data-format=LEI16@16000"], check=True)
    with wave.open(str(wav)) as w:
        audio_s = w.getnframes() / w.getframerate()
    print(f"audio: {audio_s:.1f} s ({audio_s/60:.2f} min) of macOS TTS speech, {words} words; synthesis {time.time()-t0:.1f} s")

    env = dict(os.environ, HF_HUB_OFFLINE="1")
    exe = find_exe("mlx_whisper")
    poll = Poller()
    poll.start()
    time.sleep(a.idle_s)
    idle1 = (time.time() - a.idle_s, time.time())
    job_start = time.time()
    runs = []
    for i in range(1, a.runs + 1):
        t0 = time.time()
        p = subprocess.run([exe, str(wav), "--model", MODEL, "--language", "en", "--output-dir", str(tmp),
                            "--output-name", f"r3mi_run{i}", "--output-format", "txt", "--verbose", "False"],
                           env=env, capture_output=True, text=True)
        dt = time.time() - t0
        if p.returncode != 0:
            print(p.stderr[-2000:])
            sys.exit(f"mlx_whisper failed with exit code {p.returncode}")
        n_out = len((tmp / f"r3mi_run{i}.txt").read_text(encoding="utf-8").split())
        runs.append(dt)
        print(f"run {i}: runtime {dt:.1f} s = {audio_s/dt:.1f} x real time (model load included); transcript {n_out} words vs {words} spoken")
    job_end = time.time()
    t2 = time.time()
    time.sleep(a.idle_s)
    idle2 = (t2, time.time())
    poll.stop()

    iv = poll.intervals()
    inside = lambda lo, hi: [m for u0, u1, m in iv if u0 >= lo - 0.5 and u1 <= hi + 0.5]
    job_w = inside(job_start, job_end)
    idle_w = inside(*idle1) + inside(*idle2)
    print("\nrefresh intervals (UpdateTime start, length s, mean W, phase):")
    for u0, u1, m in iv:
        ph = "job" if (u0 >= job_start - 0.5 and u1 <= job_end + 0.5) else (
            "idle" if (u0 >= idle1[0] - 0.5 and u1 <= idle1[1] + 0.5) or (u0 >= idle2[0] - 0.5 and u1 <= idle2[1] + 0.5) else "mixed")
        print(f"  {u0}  {u1-u0:>3}  {m:7.2f}  {ph}")
    pj, pi = mean(job_w), mean(idle_w)
    rt = sum(runs)
    ah = audio_s * len(runs) / 3600
    eg = pj * rt / 3600 / ah
    en = (pj - pi) * rt / 3600 / ah
    print(f"\njob windows: {len(job_w)}, mean {pj:.2f} W; idle windows: {len(idle_w)}, mean {pi:.2f} W")
    print(f"total runtime {rt:.1f} s for {ah:.3f} audio-hours = {ah*3600/rt:.1f} x real time")
    print(f"E_gross = {eg:.3f} Wh per audio-hour  -> rule (i): {1000/eg:,.0f} audio-hours per 1 kW server-hour")
    print(f"E_net   = {en:.3f} Wh per audio-hour  (job minus idle; idle includes other processes running at the time)")
    print("Status: COMPUTED. One laptop (Apple M3 Pro, 18 GB, 35 W adapter), synthetic TTS audio, battery-controller "
          "telemetry not checked against a wall meter, other processes on the machine included in the gross figure.")


if __name__ == "__main__":
    main()
