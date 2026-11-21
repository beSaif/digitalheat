"""Measure runtime and energy per item of the real jobs on this machine.

Protocol (docs/workloads.md#how-we-measure):
  1. Idle baseline: average whole-system power over `--windows` battery-gauge
     publish windows (~45-60 s each) with nothing running.
  2. For each job type: start the real job (workloads.run) as a subprocess, skip
     model loading and one full warm-up window, then average power over
     `--windows` windows while counting items finished (from status.json).
     Stop the job with SIGTERM (it checkpoints and exits 75).
  3. Energy per item, gross    = load power / items per second
     Energy per item, marginal = (load power - idle power) / items per second

Energy needs an Apple-silicon laptop on battery (the gauge only measures the
load then). Keep the machine otherwise quiet and the display brightness constant.
On any other machine use --no-meter: it records throughput only (items/s).

    .venv/bin/python scripts/measure_workloads.py --label alex               # both jobs, energy + speed
    .venv/bin/python scripts/measure_workloads.py --label alex --no-meter    # speed only, any machine
"""

import argparse
import json
import os
import platform
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from workloads import power  # noqa: E402
from workloads.jobs import EXIT_STOPPED, JOB_TYPES  # noqa: E402

OUT_DIR = ROOT / "data" / "measurements"


def sysctl(name):
    return subprocess.run(["sysctl", "-n", name], capture_output=True, text=True).stdout.strip()


def cpu_name():
    if sys.platform == "darwin":
        return sysctl("machdep.cpu.brand_string")
    if sys.platform.startswith("linux"):
        m = re.search(r"model name\s*:\s*(.+)", Path("/proc/cpuinfo").read_text())
        if m:
            return m.group(1).strip()
    return platform.processor() or platform.machine()


def git_commit():
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() or None


def stop_job(proc):
    proc.send_signal(signal.SIGTERM)  # on Windows this is a hard terminate, no checkpoint
    code = proc.wait()
    if os.name != "nt" and code != EXIT_STOPPED:
        raise RuntimeError(f"job exited with {code}, expected {EXIT_STOPPED}")


def windows(n, label):
    """Average power over n publish windows, starting at the next publish. Returns (W, s, per-window W)."""
    a = power.wait_for_publish()
    first, per = a, []
    for _ in range(n):
        b = power.wait_for_publish(a)
        w, _ = power.average_w(a, b)
        per.append(round(w, 3))
        print(f"  {label}: window {len(per)}/{n}: {w:.2f} W", flush=True)
        a = b
    w, secs = power.average_w(first, a)
    return w, secs, per, first, a


def read_status(job_dir):
    return json.loads((job_dir / "status.json").read_text())


def start_job(job_type, threads, run_dir):
    job_dir = run_dir / job_type
    cmd = [sys.executable, "-m", "workloads.run", job_type, "--job-dir", str(job_dir),
           "--items", "100000000", "--no-outputs"]
    if threads:
        cmd += ["--threads", str(threads)]
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL)
    while not (job_dir / "status.json").exists():  # model loading
        if proc.poll() is not None:
            raise RuntimeError(f"{job_type} exited early with code {proc.returncode}")
        time.sleep(0.5)
    print(f"{job_type}: running, warm-up", flush=True)
    return proc, job_dir


def measure_speed_only(job_type, seconds, threads, run_dir):
    proc, job_dir = start_job(job_type, threads, run_dir)
    try:
        time.sleep(45)  # warm-up, comparable to one gauge window
        s_a = read_status(job_dir)
        time.sleep(seconds)
        s_b = read_status(job_dir)
    finally:
        stop_job(proc)
    items, wall = s_b["items_done"] - s_a["items_done"], s_b["updated_at"] - s_a["updated_at"]
    print(f"  {job_type}: {items / wall:.2f} items/s over {wall:.0f} s", flush=True)
    return {"items": items, "wall_seconds": wall, "items_per_s": items / wall}


def measure_job(job_type, n_windows, threads, run_dir):
    proc, job_dir = start_job(job_type, threads, run_dir)
    try:
        power.wait_for_publish()  # discard the window that contains start-up

        a = power.wait_for_publish()
        s_a = read_status(job_dir)
        per, cur = [], a
        for _ in range(n_windows):
            b = power.wait_for_publish(cur)
            per.append(round(power.average_w(cur, b)[0], 3))
            print(f"  {job_type}: window {len(per)}/{n_windows}: {per[-1]:.2f} W", flush=True)
            cur = b
        s_b = read_status(job_dir)
        load_w, secs = power.average_w(a, cur)
    finally:
        stop_job(proc)

    items = s_b["items_done"] - s_a["items_done"]
    wall = s_b["updated_at"] - s_a["updated_at"]
    return {"load_w": load_w, "gauge_seconds": secs, "window_w": per, "items": items,
            "wall_seconds": wall, "items_per_s": items / wall}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", nargs="+", default=sorted(JOB_TYPES), choices=sorted(JOB_TYPES))
    ap.add_argument("--windows", type=int, default=4, help="gauge publish windows per measurement")
    ap.add_argument("--threads", type=int, help="torch CPU threads (default: torch's choice)")
    ap.add_argument("--label", required=True, help="short name for whoever runs this, used in the file name")
    ap.add_argument("--no-meter", action="store_true", help="measure throughput only (any machine)")
    a = ap.parse_args()
    label = re.sub(r"[^a-z0-9-]+", "-", a.label.lower()).strip("-")

    if not a.no_meter:
        try:
            snap = power.read()
        except Exception:
            sys.exit("No battery power meter on this machine (needs an Apple-silicon laptop). "
                     "Run again with --no-meter to measure throughput only.")
        if not snap.on_battery:
            sys.exit("Unplug the charger: the battery gauge only measures the load while on battery.")

    import torch

    started = datetime.now(timezone.utc)
    run_dir = ROOT / "runs" / f"measure-{started:%Y%m%dT%H%M%S}"
    idle = None
    if not a.no_meter:
        print(f"idle baseline ({a.windows} windows, keep the machine quiet)", flush=True)
        idle_w, idle_s, idle_per, _, _ = windows(a.windows, "idle")
        idle = {"w": idle_w, "gauge_seconds": idle_s, "window_w": idle_per}

    results = {}
    for jt in a.jobs:
        if a.no_meter:
            r = measure_speed_only(jt, a.windows * 50, a.threads, run_dir)
            r.update(load_w=None, marginal_w=None, gross_j_per_item=None, marginal_j_per_item=None)
        else:
            r = measure_job(jt, a.windows, a.threads, run_dir)
            r["marginal_w"] = r["load_w"] - idle_w
            r["gross_j_per_item"] = r["load_w"] / r["items_per_s"]
            r["marginal_j_per_item"] = r["marginal_w"] / r["items_per_s"]
        spec = JOB_TYPES[jt]
        r.update(model=spec.model, revision=spec.revision, batch_size=spec.batch_size,
                 max_tokens=spec.max_tokens, item=spec.item)
        results[jt] = r

    report = {
        "measured_at_utc": started.isoformat(timespec="seconds"),
        "label": label,
        "git_commit": git_commit(),
        "machine": {
            "cpu": cpu_name(),
            "cores": os.cpu_count(),
            "arch": platform.machine(),
            "os": f"macOS {platform.mac_ver()[0]}" if sys.platform == "darwin" else platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "torch_threads": a.threads or torch.get_num_threads(),
        },
        "meter": None if a.no_meter else
            "macOS battery gauge, AccumulatedSystemLoad / SystemLoadAccumulatorCount (whole system, on battery)",
        "idle": idle,
        "jobs": results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cpu_slug = re.sub(r"[^a-z0-9]+", "-", report["machine"]["cpu"].lower()).strip("-")
    out = OUT_DIR / f"workloads_{started:%Y-%m-%d}_{label}_{cpu_slug}.json"
    out.write_text(json.dumps(report, indent=1))

    f = lambda v, p: "-" if v is None else f"{v:.{p}f}"  # noqa: E731
    if idle:
        print(f"\nidle {idle['w']:.2f} W over {idle['gauge_seconds']} s")
    print(f"{'job':8} {'items/s':>8} {'load W':>7} {'marg. W':>7} {'J/item gross':>13} {'J/item marg.':>13}")
    for jt, r in results.items():
        print(f"{jt:8} {r['items_per_s']:8.2f} {f(r['load_w'], 2):>7} {f(r['marginal_w'], 2):>7} "
              f"{f(r['gross_j_per_item'], 4):>13} {f(r['marginal_j_per_item'], 4):>13}")
    print(f"\nwritten {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
