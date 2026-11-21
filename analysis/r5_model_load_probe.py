"""Round 5: how long does a cold restart of the measured job (J1) take on the laptop?

ASSESSMENT ONLY. Standard library only; calls the already installed `mlx_whisper` CLI and
macOS `say` as subprocesses (nothing is installed or downloaded: HF_HUB_OFFLINE=1).

    python3 analysis/r5_model_load_probe.py            # 3 runs
    python3 analysis/r5_model_load_probe.py --runs 5

A restart from checkpoint = new process + imports + model load + the first file. We time
the CLI on a ~3 s clip, so the wall time is almost all restart overhead. This is the LAPTOP
part only: a powered-down reference server adds firmware POST and OS boot (unmeasured).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

MODEL = "mlx-community/whisper-large-v3-turbo"


def main():
    runs = int(sys.argv[sys.argv.index("--runs") + 1]) if "--runs" in sys.argv else 3
    exe = shutil.which("mlx_whisper") or str(Path.home() / "miniforge3/bin/mlx_whisper")
    tmp = Path(tempfile.mkdtemp(prefix="r5_missstress_probe_"))
    wav = tmp / "r5_missstress_clip.wav"
    subprocess.run(["say", "-o", str(wav), "--file-format=WAVE", "--data-format=LEI16@16000",
                    "The server pauses when the tank is full and resumes when the house needs heat."], check=True)
    with wave.open(str(wav)) as w:
        audio_s = w.getnframes() / w.getframerate()
    env = dict(os.environ, HF_HUB_OFFLINE="1")
    py = str(Path(exe).resolve().parent / "python3")
    t = []
    for i in range(runs):
        t0 = time.perf_counter()
        subprocess.run([py, "-c", "import mlx.core, mlx_whisper"], check=True, env=env, capture_output=True)
        t.append(time.perf_counter() - t0)
    print(f"import mlx.core + mlx_whisper only: " + ", ".join(f"{x:.2f}" for x in t) + " s")
    walls = []
    for i in range(runs):
        t0 = time.perf_counter()
        p = subprocess.run([exe, str(wav), "--model", MODEL, "--language", "en", "--output-dir", str(tmp),
                            "--output-name", f"r5_missstress_run{i}", "--output-format", "txt", "--verbose", "False"],
                           env=env, capture_output=True, text=True)
        dt = time.perf_counter() - t0
        if p.returncode != 0:
            print(p.stderr[-1500:])
            sys.exit("mlx_whisper failed")
        walls.append(dt)
        txt = (tmp / f"r5_missstress_run{i}.txt").read_text().strip()
        print(f"run {i+1}: {dt:.2f} s wall for a {audio_s:.1f} s clip (new process + imports + model load + transcription): '{txt[:60]}'")
    walls.sort()
    print(f"median cold restart of J1 on the laptop: {walls[len(walls)//2]:.2f} s = {walls[len(walls)//2]/60:.3f} min")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
