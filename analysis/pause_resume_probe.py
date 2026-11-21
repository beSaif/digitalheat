"""Exploratory probe of pause mechanisms for the live demo (round 1, 2026-11-21).

NOT the scheduler and NOT the demo. It answers four narrow questions on the
laptop it runs on, with a dummy CPU job (SHA-256 batches), standard library only:

  signals     SIGSTOP/SIGCONT on a child in its own session: latency, CPU time
              burnt while stopped, work lost.
  checkpoint  cooperative stop (SIGTERM -> finish batch -> state file -> exit)
              and restart; also hard SIGKILL: latency, work lost, file integrity.
  throttle    worker-count throttling ("slow down"): throughput vs active workers.
  power       whole-machine power from `ioreg` (AppleSmartBattery ->
              PowerTelemetryData.SystemLoad, no sudo), idle / loaded / stopped.
              macOS only; the field is undocumented, units inferred as mW.
  powertrace  how often that telemetry updates, and whether its accumulators give
              a usable mean power over a phase (about 4 minutes).
  torch       optional: does a PyTorch job (cpu and mps) survive SIGSTOP/SIGCONT?
              Skipped if torch is not installed. Nothing is installed by this script.

    python3 analysis/pause_resume_probe.py all
    python3 analysis/pause_resume_probe.py signals checkpoint

Scratch files go to a temporary directory that is removed at the end.
"""
import hashlib
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time

ME = os.path.abspath(__file__)
BLOCK = b"\x5a" * (1 << 20)


# ----------------------------------------------------------------- worker ---
def worker(workdir, name, rounds, resume):
    """Dummy interruptible job: each batch hashes `rounds` MiB, then checkpoints."""
    ckpt = os.path.join(workdir, f"{name}.ckpt.json")
    beat = os.path.join(workdir, f"{name}.beat.log")
    batch = 0
    if resume and os.path.exists(ckpt):
        with open(ckpt) as f:
            batch = json.load(f)["batches_done"]
    stop = {"flag": False}
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__("flag", True))
    with open(beat, "a", buffering=1) as hb:
        hb.write(f"start {batch} {time.time():.6f}\n")
        while not stop["flag"]:
            h = hashlib.sha256()
            for _ in range(rounds):
                h.update(BLOCK)
            batch += 1
            tmp = ckpt + ".tmp"
            with open(tmp, "w") as f:
                json.dump({"batches_done": batch, "digest": h.hexdigest()[:8]}, f)
            os.replace(tmp, ckpt)                     # atomic: old or new, never half
            hb.write(f"batch {batch} {time.time():.6f}\n")
        hb.write(f"clean_exit {batch} {time.time():.6f}\n")


def spawn(workdir, name, rounds=20, resume=False):
    cmd = [sys.executable, ME, "--worker", workdir, name, str(rounds), "1" if resume else "0"]
    # own session => own process group: signals reach the job and all its children,
    # and the terminal's job control never sees the stop.
    return subprocess.Popen(cmd, start_new_session=True)


def beats(workdir, name):
    p = os.path.join(workdir, f"{name}.beat.log")
    if not os.path.exists(p):
        return []
    out = []
    with open(p) as f:
        for ln in f:
            parts = ln.split()
            if len(parts) == 3:
                out.append((parts[0], int(parts[1]), float(parts[2])))
    return out


def batches_done(workdir, name):
    b = [x for x in beats(workdir, name) if x[0] == "batch"]
    return b[-1][1] if b else 0


def ckpt_value(workdir, name):
    with open(os.path.join(workdir, f"{name}.ckpt.json")) as f:
        return json.load(f)["batches_done"]


def wait_batches(workdir, name, n, timeout=30):
    t0 = time.time()
    while batches_done(workdir, name) < n:
        if time.time() - t0 > timeout:
            raise RuntimeError("worker did not reach batch %d" % n)
        time.sleep(0.002)


def ps(pid, field):
    r = subprocess.run(["ps", "-o", f"{field}=", "-p", str(pid)], capture_output=True, text=True)
    return r.stdout.strip()


def cpu_seconds(pid):
    t = ps(pid, "time")                 # [[dd-]hh:]mm:ss.cc
    if not t:
        return float("nan")
    parts = t.replace("-", ":").split(":")
    sec = 0.0
    for p in parts:
        sec = sec * 60 + float(p)
    return sec


def stats(xs, unit="ms", k=1000.0):
    xs = [x * k for x in xs]
    return (f"n={len(xs)} median={statistics.median(xs):.1f} {unit} "
            f"min={min(xs):.1f} max={max(xs):.1f}")


# ------------------------------------------------------------ experiments ---
def exp_signals(workdir):
    print("\n== signals: SIGSTOP / SIGCONT on a child process group ==")
    name = "sig"
    p = spawn(workdir, name)
    wait_batches(workdir, name, 5)
    b = [x for x in beats(workdir, name) if x[0] == "batch"]
    per_batch = (b[-1][2] - b[0][2]) / (len(b) - 1)
    print(f"batch duration while running: {per_batch*1000:.1f} ms")
    stop_lat, cont_lat, leaked, cpu_leak = [], [], [], []
    for _ in range(20):
        time.sleep(0.15)
        t0 = time.time()
        os.killpg(p.pid, signal.SIGSTOP)
        while "T" not in ps(p.pid, "state"):
            time.sleep(0.0005)
        stop_lat.append(time.time() - t0)       # includes one `ps` call (~5-10 ms)
        b1, c1 = batches_done(workdir, name), cpu_seconds(p.pid)
        time.sleep(1.0)
        b2, c2 = batches_done(workdir, name), cpu_seconds(p.pid)
        leaked.append(b2 - b1)
        cpu_leak.append(c2 - c1)
        t0 = time.time()
        os.killpg(p.pid, signal.SIGCONT)
        while batches_done(workdir, name) <= b2:
            time.sleep(0.0005)
        cont_lat.append(time.time() - t0)       # up to one full batch by construction
    os.killpg(p.pid, signal.SIGTERM)
    rc = p.wait(timeout=10)
    seq = [x[1] for x in beats(workdir, name) if x[0] == "batch"]
    contiguous = seq == list(range(1, len(seq) + 1))
    print("stop latency  (signal -> ps state T):", stats(stop_lat))
    print("resume latency (SIGCONT -> next batch written):", stats(cont_lat))
    print(f"batches completed during 20 x 1.0 s stops: {sum(leaked)}")
    print(f"CPU seconds consumed during 20 x 1.0 s stops: {sum(cpu_leak):.2f}")
    print(f"batch sequence contiguous, nothing repeated or lost: {contiguous} ({len(seq)} batches)")
    print(f"exit code after SIGTERM: {rc}")


def exp_checkpoint(workdir):
    print("\n== checkpoint: cooperative stop at batch boundary + restart, ~100 ms batches ==")
    name = "ck"
    start_lat, exit_lat, lost = [], [], []
    for i in range(10):
        before = batches_done(workdir, name)
        t0 = time.time()
        p = spawn(workdir, name, rounds=300, resume=True)
        wait_batches(workdir, name, before + 1)
        start_lat.append(time.time() - t0)      # process start + first new batch
        time.sleep(0.4)
        t0 = time.time()
        os.killpg(p.pid, signal.SIGTERM)
        p.wait(timeout=10)
        exit_lat.append(time.time() - t0)
        lost.append(batches_done(workdir, name) - ckpt_value(workdir, name))
    seq = [x[1] for x in beats(workdir, name) if x[0] == "batch"]
    print("restart latency (spawn -> first new batch):", stats(start_lat))
    print("stop latency   (SIGTERM -> process exited):", stats(exit_lat))
    print(f"batches finished but missing from checkpoint: {sum(lost)}")
    print(f"sequence contiguous across 10 restarts: {seq == list(range(1, len(seq)+1))} ({len(seq)} batches)")

    print("\n== checkpoint: hard kill (SIGKILL mid-batch) + restart, ~100 ms batches ==")
    name = "kill"
    corrupt = 0
    resumed_from_ckpt = 0
    for i in range(10):
        p = spawn(workdir, name, rounds=300, resume=True)
        wait_batches(workdir, name, batches_done(workdir, name) + 2)
        time.sleep(0.02 + 0.01 * i)            # land somewhere inside a batch
        os.killpg(p.pid, signal.SIGKILL)
        p.wait(timeout=10)
        try:
            ckpt_value(workdir, name)
        except Exception:
            corrupt += 1
    # every restart must begin exactly at the checkpoint the killed run left behind
    ev = beats(workdir, name)
    starts = [(i, x[1]) for i, x in enumerate(ev) if x[0] == "start"]
    for i, s in starts[1:]:
        last_logged = max([x[1] for x in ev[:i] if x[0] == "batch"], default=0)
        # the checkpoint is written before the log line, so it is last_logged or last_logged+1
        if s in (last_logged, last_logged + 1):
            resumed_from_ckpt += 1
    seq = [x[1] for x in ev if x[0] == "batch"]
    repeated = len(seq) - len(set(seq))
    print(f"checkpoint unreadable after SIGKILL: {corrupt} of 10")
    print(f"restarts that began at the surviving checkpoint: {resumed_from_ckpt} of {len(starts)-1}")
    print(f"finished batches computed twice: {repeated}; work lost per kill = only the unfinished batch (<= one batch)")


def rate(workdir, names, secs):
    a = sum(batches_done(workdir, n) for n in names)
    time.sleep(secs)
    return (sum(batches_done(workdir, n) for n in names) - a) / secs


def exp_throttle(workdir):
    print("\n== throttle: number of active workers ('slow down') ==")
    names = [f"th{i}" for i in range(4)]
    procs = [spawn(workdir, n) for n in names]
    for n in names:
        wait_batches(workdir, n, 3)
    r4 = rate(workdir, names, 3.0)
    for p in procs[2:]:
        os.killpg(p.pid, signal.SIGSTOP)
    time.sleep(0.2)
    r2 = rate(workdir, names, 3.0)
    for p in procs[1:2]:
        os.killpg(p.pid, signal.SIGSTOP)
    time.sleep(0.2)
    r1 = rate(workdir, names, 3.0)
    for p in procs:
        os.killpg(p.pid, signal.SIGCONT)
        os.killpg(p.pid, signal.SIGTERM)
        p.wait(timeout=10)
    print(f"batches/s with 4 / 2 / 1 active workers: {r4:.1f} / {r2:.1f} / {r1:.1f}")
    print(f"ratio vs 4 workers: 1.00 / {r2/r4:.2f} / {r1/r4:.2f}  (ideal 1.00 / 0.50 / 0.25)")


def _signed(x):
    return x - (1 << 64) if x >= (1 << 63) else x


def read_power():
    """(SystemLoad mW?, battery V*I W, external_connected) or None if unavailable."""
    try:
        out = subprocess.run(["ioreg", "-rw0", "-c", "AppleSmartBattery"],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return None
    m = re.search(r'"SystemLoad"=(\d+)', out)
    v = re.search(r'^\s*\|?\s*"Voltage" = (\d+)', out, re.M)
    a = re.search(r'^\s*\|?\s*"InstantAmperage" = (\d+)', out, re.M)
    ext = re.search(r'"ExternalConnected" = (\w+)', out)
    if not (m and v and a):
        return None
    vi = -_signed(int(a.group(1))) * int(v.group(1)) / 1e6
    return int(m.group(1)), vi, ext.group(1) if ext else "?"


def sample_power(label, secs):
    xs = []
    t_end = time.time() + secs
    while time.time() < t_end:
        r = read_power()
        if r:
            xs.append(r)
        time.sleep(1.0)
    if not xs:
        print(f"{label:<34} no reading")
        return None
    sl = [x[0] / 1000 for x in xs]
    vi = [x[1] for x in xs]
    print(f"{label:<34} SystemLoad mean {statistics.mean(sl):6.2f} W (min {min(sl):.2f}, max {max(sl):.2f}, "
          f"{len(set(sl))} distinct of {len(sl)} samples) | battery V*I mean {statistics.mean(vi):6.2f} W")
    return statistics.mean(sl)


def exp_power(workdir):
    print("\n== power: ioreg AppleSmartBattery PowerTelemetryData.SystemLoad (no sudo) ==")
    r = read_power()
    if r is None:
        print("not available on this machine (not macOS, or no battery telemetry)")
        return
    print(f"external power connected: {r[2]}  (battery V*I is only the full machine load when this is 'No')")
    ncpu = os.cpu_count() or 4
    idle = sample_power("idle (probe only)", 12)
    names = [f"pw{i}" for i in range(ncpu)]
    procs = [spawn(workdir, n) for n in names]
    time.sleep(4)                                # let the telemetry catch up
    load = sample_power(f"{ncpu} workers running", 15)
    for p in procs:
        os.killpg(p.pid, signal.SIGSTOP)
    time.sleep(4)
    stopped = sample_power(f"{ncpu} workers SIGSTOPped", 12)
    for p in procs:
        os.killpg(p.pid, signal.SIGCONT)
    time.sleep(4)
    again = sample_power(f"{ncpu} workers resumed", 10)
    for p in procs:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait(timeout=10)
    if idle and load and stopped:
        print(f"load - idle = {load-idle:.1f} W; stopped - idle = {stopped-idle:+.1f} W")


def read_telemetry():
    out = subprocess.run(["ioreg", "-rw0", "-c", "AppleSmartBattery"],
                         capture_output=True, text=True, timeout=5).stdout
    g = lambda k: int(re.search(r'"%s"=(\d+)' % k, out).group(1))
    ext = re.search(r'"ExternalConnected" = (\w+)', out).group(1)
    return {"t": time.time(), "load": g("SystemLoad"), "acc": g("AccumulatedSystemLoad"),
            "cnt": g("SystemLoadAccumulatorCount"), "pin": g("SystemPowerIn"), "ext": ext}


def trace_phase(label, secs):
    rows = []
    t_end = time.time() + secs
    while time.time() < t_end:
        rows.append(read_telemetry())
        time.sleep(1.0)
    changes = [b["t"] - a["t"] for a, b in zip(rows, rows[1:]) if b["cnt"] != a["cnt"]]
    upd = [r for a, r in zip(rows, rows[1:]) if r["cnt"] != a["cnt"]]
    gaps = [b["t"] - a["t"] for a, b in zip(upd, upd[1:])]
    dc = rows[-1]["cnt"] - rows[0]["cnt"]
    da = rows[-1]["acc"] - rows[0]["acc"]
    inst = sorted(set(r["load"] for r in rows))
    print(f"{label:<26} {secs:>3} s: counter +{dc}, updates seen {len(upd)}, "
          f"median gap {statistics.median(gaps) if gaps else float('nan'):.0f} s | "
          f"accumulator mean {da/dc/1000 if dc else float('nan'):6.2f} W | "
          f"SystemLoad values seen (W): {[round(x/1000, 1) for x in inst]} | "
          f"SystemPowerIn last {rows[-1]['pin']/1000:.1f} W | external {rows[-1]['ext']}")
    return da / dc / 1000 if dc else None


def exp_powertrace(workdir):
    print("\n== powertrace: how often does the ioreg telemetry update, and do the accumulators give a mean? ==")
    try:
        read_telemetry()
    except Exception as e:
        print("not available:", e)
        return
    ncpu = os.cpu_count() or 4
    idle = trace_phase("idle", 75)
    procs = [spawn(workdir, f"pt{i}") for i in range(ncpu)]
    load = trace_phase(f"{ncpu} workers running", 100)
    for p in procs:
        os.killpg(p.pid, signal.SIGSTOP)
    stopped = trace_phase(f"{ncpu} workers SIGSTOPped", 75)
    for p in procs:
        os.killpg(p.pid, signal.SIGCONT)
        os.killpg(p.pid, signal.SIGKILL)
        p.wait(timeout=10)
    if idle and load and stopped:
        print(f"accumulator means: load - idle = {load-idle:.1f} W, stopped - idle = {stopped-idle:+.1f} W")
        print("(each phase mean still contains up to one update interval of the previous phase)")


TORCH_CHILD = r"""
import sys, time, torch
dev = sys.argv[1]
x = torch.randn(1500, 1500, device=dev)
n = 0
with open(sys.argv[2], "a", buffering=1) as f:
    while True:
        y = (x @ x).sum().item()      # .item() forces the device to finish
        n += 1
        f.write(f"batch {n} {time.time():.6f}\n")
"""


def exp_torch(workdir):
    print("\n== torch: does a PyTorch job survive SIGSTOP / SIGCONT? ==")
    chk = subprocess.run([sys.executable, "-c",
                          "import torch;print(torch.__version__, torch.backends.mps.is_available())"],
                         capture_output=True, text=True)
    if chk.returncode != 0:
        print("torch not importable here; skipped")
        return
    ver, mps = chk.stdout.split()
    print(f"torch {ver}, mps available: {mps}")
    for dev in (["cpu", "mps"] if mps == "True" else ["cpu"]):
        name = f"torch_{dev}"
        log = os.path.join(workdir, f"{name}.beat.log")
        t0 = time.time()
        p = subprocess.Popen([sys.executable, "-c", TORCH_CHILD, dev, log], start_new_session=True)
        try:
            wait_batches(workdir, name, 5, timeout=60)
            warm = time.time() - t0
            ok = True
            for stop_s in (2.0, 10.0):
                os.killpg(p.pid, signal.SIGSTOP)
                time.sleep(0.3)
                b1 = batches_done(workdir, name)
                time.sleep(stop_s)
                b2 = batches_done(workdir, name)
                t1 = time.time()
                os.killpg(p.pid, signal.SIGCONT)
                wait_batches(workdir, name, b2 + 3, timeout=20)
                lat = time.time() - t1
                alive = p.poll() is None
                ok = ok and alive and b2 == b1
                print(f"  {dev}: stopped {stop_s:.0f} s, batches during stop {b2-b1}, "
                      f"3 batches after SIGCONT in {lat*1000:.0f} ms, alive {alive}")
            print(f"  {dev}: spawn -> 5th batch (import + first work) {warm:.2f} s; survived: {ok}")
        except Exception as e:
            print(f"  {dev}: FAILED: {e}")
        finally:
            try:
                os.killpg(p.pid, signal.SIGCONT)
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait(timeout=10)


EXPS = {"signals": exp_signals, "checkpoint": exp_checkpoint, "throttle": exp_throttle,
        "power": exp_power, "torch": exp_torch, "powertrace": exp_powertrace}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5] == "1")
        sys.exit(0)
    which = sys.argv[1:] or ["all"]
    if which == ["all"]:
        which = list(EXPS)
    print(f"python {sys.version.split()[0]} on {sys.platform}, cpu_count {os.cpu_count()}")
    d = tempfile.mkdtemp(prefix="dh_probe_")
    try:
        for w in which:
            EXPS[w](d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
