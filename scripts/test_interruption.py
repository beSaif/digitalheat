"""Check that a real job survives pause, stop and resume without losing or changing work.

Runs the same embedding job twice: once straight through, once paused (SIGSTOP),
unpaused (SIGCONT), stopped at a checkpoint (SIGTERM, expects exit 75) and resumed.
Passes if both outputs are identical. macOS / Linux only (Windows has no SIGSTOP).

    .venv/bin/python scripts/test_interruption.py
"""

import json
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workloads.jobs import EXIT_STOPPED  # noqa: E402

ITEMS = 4000


def cmd(job_dir):
    return [sys.executable, "-m", "workloads.run", "embed", "--job-dir", str(job_dir),
            "--items", str(ITEMS), "--checkpoint-every", "3"]


def status(job_dir):
    return json.loads((job_dir / "status.json").read_text())


def load(job_dir):
    import numpy as np
    return np.concatenate([np.load(f) for f in sorted((job_dir / "out").glob("*.npy"))])


def main():
    if not hasattr(signal, "SIGSTOP"):
        sys.exit("SIGSTOP is not available on this OS; skip this test.")
    base = ROOT / "runs" / "test-interruption"
    shutil.rmtree(base, ignore_errors=True)
    ref, intr = base / "reference", base / "interrupted"

    print("1/3 reference run, straight through", flush=True)
    subprocess.run(cmd(ref), cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    print("2/3 interrupted run: pause, unpause, stop", flush=True)
    p = subprocess.Popen(cmd(intr), cwd=ROOT, stdout=subprocess.DEVNULL)
    while not (intr / "status.json").exists():
        time.sleep(0.5)
    time.sleep(5)
    p.send_signal(signal.SIGSTOP)
    time.sleep(1)
    frozen = status(intr)["items_done"]
    time.sleep(4)
    assert status(intr)["items_done"] == frozen, "job kept working while paused"
    print(f"    paused at item {frozen}: no progress for 4 s", flush=True)
    p.send_signal(signal.SIGCONT)
    time.sleep(4)
    p.send_signal(signal.SIGTERM)
    code = p.wait()
    s = status(intr)
    assert code == EXIT_STOPPED, f"expected exit {EXIT_STOPPED}, got {code}"
    assert s["state"] == "stopped" and s["items_checkpointed"] == s["items_done"] < ITEMS
    print(f"    stopped at checkpoint, item {s['items_done']}, exit {code}", flush=True)

    print("3/3 resume with the same command", flush=True)
    subprocess.run(cmd(intr), cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    a, b = load(ref), load(intr)
    diff = float(abs(a - b).max())
    assert a.shape == b.shape == (ITEMS, 384), (a.shape, b.shape)
    print(f"PASS: {ITEMS} items, outputs identical (max abs diff {diff})" if diff == 0
          else f"outputs differ: max abs diff {diff}")
    sys.exit(0 if diff == 0 else 1)


if __name__ == "__main__":
    main()
