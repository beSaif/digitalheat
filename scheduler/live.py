"""Let the scheduler control a real running job on this machine.

    python3 -m scheduler.live                            # reference house, 15 Jul 2025 from 06:00, 24 h
    python3 -m scheduler.live --day 2025-01-15 --seconds-per-hour 3
    python3 -m scheduler.live --fleet --site BS-01       # the dashboard's three sites

The same Scheduler that produces the yearly balance runs hour by hour (sped up: one hour
of the year = --seconds-per-hour real seconds). This machine plays one server of the
chosen site (by default its first one; servers stop from the last one down when heat demand drops). Each hour
the scheduler's decision for that server is applied to a real embedding job
(workloads.run, docs/workloads.md):

    server runs                  -> start the job, SIGCONT a paused job, or restart it from its checkpoint
    no heat, back within 2 h     -> SIGSTOP (paused in memory)
    no heat for longer           -> SIGTERM: the job stops at its next checkpoint (exit 75), resumable anywhere

The heat side (house demand, tank) is the simulated plant of the yearly balance; the job,
its process and its checkpoints are real. Status is written every second to
runs/live/status.json (the dashboard's "Real job" panel reads it).
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

from scheduler.balance import DEFAULT_SITES, REFERENCE
from scheduler.core import Scheduler, job_types
from scheduler.sites import Site, demand
from scheduler.weather import temperatures

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / "runs" / "live"
STATUS = LIVE / "status.json"
EXIT_STOPPED = 75


def worker_python():
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


class RealJob:
    """One real embedding job, driven by signals."""

    def __init__(self, job_dir, items):
        self.dir = Path(job_dir)
        self.items = items
        self.proc = None
        self.state = "not started"  # running, paused, checkpointed, done
        self.log = (self.dir.parent / "job.log")

    def _spawn(self):
        self.dir.parent.mkdir(parents=True, exist_ok=True)
        cmd = [worker_python(), "-m", "workloads.run", "embed", "--job-dir", str(self.dir),
               "--items", str(self.items), "--threads", "2", "--checkpoint-every", "2", "--no-outputs"]
        self.proc = subprocess.Popen(cmd, cwd=ROOT, stdout=open(self.log, "a"), stderr=subprocess.STDOUT)

    def run(self):
        if self.proc and self.proc.poll() is None:
            if self.state == "paused":
                os.kill(self.proc.pid, signal.SIGCONT)
                self.state = "running"
                return "resume (SIGCONT)"
            return None
        code = self.proc.poll() if self.proc else None
        crashed = self.state == "running" and code not in (None, 0, EXIT_STOPPED)
        restart = (self.dir / "state.json").exists()
        self._spawn()
        self.state = "running"
        what = "restart from checkpoint" if restart else "start"
        # a worker that died on its own (not by our SIGTERM) is reported, not silently restarted
        return f"worker crashed (exit {code}, see runs/live/job.log); {what}" if crashed else what

    def pause(self):
        if self.proc and self.proc.poll() is None and self.state == "running":
            os.kill(self.proc.pid, signal.SIGSTOP)
            self.state = "paused"
            return "pause (SIGSTOP)"
        return None

    def checkpoint(self):
        if self.proc and self.proc.poll() is None:
            if self.state == "paused":
                os.kill(self.proc.pid, signal.SIGCONT)
            os.kill(self.proc.pid, signal.SIGTERM)
            try:
                code = self.proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                code = -9
            self.state = "checkpointed" if code == EXIT_STOPPED else "done" if code == 0 else f"exit {code}"
            return f"checkpoint (SIGTERM, exit {code})"
        return None

    def progress(self):
        try:
            s = json.loads((self.dir / "status.json").read_text())
            return {"items_done": s.get("items_done"), "items_total": s.get("total_items", self.items), "items_checkpointed": s.get("items_checkpointed"),
                    "rate": s.get("items_per_s")}
        except (OSError, ValueError):
            return {"items_done": 0, "items_total": self.items, "rate": None}

    def poll_done(self):
        if self.proc and self.proc.poll() == 0:
            self.state = "done"
            return True
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--day", default="2025-07-15", help="first day (YYYY-MM-DD)")
    ap.add_argument("--hour", type=int, default=6)
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--seconds-per-hour", type=float, default=4.0)
    ap.add_argument("--fleet", action="store_true", help="the dashboard's three sites instead of the reference house alone")
    ap.add_argument("--sites-json", help="JSON list of sites (as the dashboard sends)")
    ap.add_argument("--site", default="BS-01", help="site whose server this machine plays")
    ap.add_argument("--server", type=int, default=0, help="server index at that site (0 = first; -1 = last)")
    ap.add_argument("--items", type=int, default=50_000_000, help="size of the real job")
    a = ap.parse_args()

    day = date.fromisoformat(a.day)
    year = day.year
    t0 = (day - date(year, 1, 1)).days
    if year % 4 == 0 and day > date(year, 2, 28):
        t0 -= 1  # the model drops 29 February
    t0 = t0 * 24 + a.hour
    sites_in = json.loads(a.sites_json) if a.sites_json else DEFAULT_SITES if a.fleet else REFERENCE
    sites = [Site.from_dict(s) for s in sites_in]
    si = next((i for i, s in enumerate(sites) if s.id == a.site), 0)
    server = a.server if a.server >= 0 else sites[si].servers - 1
    dem = [demand(s, temperatures(s.lat, s.lon, year)) for s in sites]
    sch = Scheduler(sites, dem, job_types())
    for t in range(t0):  # fast-forward the year to the first live hour: same scheduler, same state
        sch.step(t)

    LIVE.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    job = RealJob(LIVE / f"embed-{run_id}", a.items)
    events, history = [], []
    stop = {"now": False}

    def on_signal(signum, frame):
        stop["now"] = True

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    def write(extra):
        doc = {"pid": os.getpid(), "run_id": run_id, "site": sites[si].to_dict(), "server": server,
               "year": year, "start_t": t0, "hours": a.hours, "seconds_per_hour": a.seconds_per_hour,
               "job": {"dir": str(job.dir.relative_to(ROOT)), "state": job.state,
                       "pid": job.proc.pid if job.proc else None, **job.progress()},
               "events": events[-40:], "history": history, **extra}
        tmp = STATUS.with_suffix(".tmp")
        tmp.write_text(json.dumps(doc))
        tmp.replace(STATUS)

    def event(t, text):
        events.append({"t": t, "at": time.time(), "text": text})
        print(f"[t={t}] {text}", flush=True)

    for t in range(t0, min(t0 + a.hours, len(dem[0]))):
        if stop["now"]:
            break
        h = sch.step(t)[si]
        runs = server < h.running
        if runs:
            act = job.run()
            reason = f"{h.running} of {sites[si].servers} servers have heat"
        elif sch._will_have_heat(si, t):
            act = job.pause()
            reason = "no heat this hour, heat again within 2 h"
        else:
            act = job.checkpoint()
            reason = "no heat for 2 h or more"
        if act:
            event(t, f"{act}: {reason}")
        history.append({"t": t, "demand": round(h.demand, 2), "soc": round(h.soc, 2), "permit": h.permit,
                        "limit": h.limit, "running": h.running, "server_runs": runs})
        calc = {"t": t, "demand": h.demand, "soc0": h.soc0, "room": h.room, "permit": h.permit,
                "reserve_u": h.reserve_u, "limit": h.limit, "running": h.running, "served": h.served,
                "soc": h.soc, "dumped": h.dumped, "server_runs": runs, "decision": act or "no change", "reason": reason}
        end = time.time() + a.seconds_per_hour
        while time.time() < end and not stop["now"]:
            if job.poll_done():
                event(t, "job finished")
            write({"state": "running", "now": calc})
            time.sleep(min(1.0, max(0.0, end - time.time())))
    act = job.checkpoint()
    if act:
        event(t, f"{act}: demo ended")
    write({"state": "finished", "now": calc})


if __name__ == "__main__":
    main()
