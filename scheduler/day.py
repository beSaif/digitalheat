"""One day of the scheduler, hour by hour, with every job it touched (the live demo's job board).

    echo '{"year": 2025, "sites": [...], "day": 195, "hour": 6, "hours": 24, "outages": [["P-1", 4690, 24]]}' | python3 -m scheduler.day --stdin
    python3 -m scheduler.day --fleet --day 14          # the dashboard's three sites, 15 January from 06:00

The same Scheduler as the yearly balance (scheduler.balance) and the real-job controller
(scheduler.live) runs from 1 January, so tanks and job queues at the start of the day are exactly
the balance's. Then, for each requested hour, it records:

  sites  what the scheduler computed for every site (heat signal, permit, deadline reserve,
         servers running, heat balance) and every action it took (start, run, resume, moved,
         paused, checkpoint, forced), plus the outside temperature and whether heat is due
         again within 2 h (the pause-or-checkpoint rule)
  jobs   every job that ran this hour, is still open, or finished or missed this hour:
         type, where it came from, where it is, state, work done, deadline

`outages` (site id, first hour of the year, hours) take a site down, as in the balance's --outage.
`sizing: "peak"` gives every site enough servers to cover its highest hour of heat demand in the year
(servers = peak kW / 0.8): all heat from servers, no heat pump and no backup heater.
A site's `x_house` (live demo only) scales its hourly demand so its coldest hour needs x_house times the
house's: the building keeps its own daily and yearly shape, only its size changes.

Nothing here decides anything: it only records the Scheduler's own decisions.
"""

import argparse
import json
import math
import sys
from datetime import date, timedelta

from scheduler.balance import DEFAULT_SITES, REFERENCE
from scheduler.core import REC, Scheduler, job_types
from scheduler.sites import Site, demand
from scheduler.weather import temperatures


def model_date(year, t):
    """Calendar date and hour of model hour t (the model's year has 365 days: 29 February is dropped)."""
    d = t // 24
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    if leap and d >= 59:
        d += 1
    return (date(year, 1, 1) + timedelta(days=d)).isoformat(), t % 24


def job_doc(j, t):
    return {
        "id": j.id, "type": j.type, "origin": j.origin, "site": j.site, "state": j.state,
        "done": round(j.done, 3), "work": j.work, "arrive": j.arrive, "due": j.due,
        "start": j.start, "finish": j.finish, "forced": int(j.forced), "moves": j.moves,
        "ran": int(getattr(j, "_ran", -1) == t),
    }


def run(sites_in, year=2025, day=0, hour=0, hours=24, outages=(), sizing=None):
    sites = [Site.from_dict(s) for s in sites_in]
    temps = [temperatures(s.lat, s.lon, year) for s in sites]
    dem = [demand(s, tt, year) for s, tt in zip(sites, temps)]
    for i, d in enumerate(sites_in):  # live demo: size the building against the house
        x = float(d.get("x_house") or 0)
        if x > 0 and max(dem[i]) > 0:
            house = Site.from_dict({"id": "house", "kind": "house", "lat": sites[i].lat, "lon": sites[i].lon})
            f = x * max(demand(house, temps[i], year)) / max(dem[i])
            dem[i] = [v * f for v in dem[i]]
    if sizing == "peak":  # cover 100 % of heat demand with servers
        for s, d in zip(sites, dem):
            s.servers = math.ceil(max(d) / REC - 1e-9)
    idx = {s.id: i for i, s in enumerate(sites)}
    outs = [(idx[o[0]], int(o[1]), int(o[2])) for o in outages if o[0] in idx and int(o[2]) > 0]
    sch = Scheduler(sites, dem, job_types(), outages=outs)
    H = len(dem[0])
    t0 = max(0, min(H - 1, day * 24 + hour))
    for t in range(t0):  # fast-forward: same scheduler, same state as the balance
        sch.step(t)
    out = []
    for t in range(t0, min(t0 + hours, H)):
        before = list(sch.open)
        n_before = len(sch.jobs)
        step = sch.step(t)
        open_ids = {j.id for j in sch.open}
        seen, jobs = set(), []
        for j in before + sch.jobs[n_before:]:
            if j.id in seen:
                continue
            seen.add(j.id)
            if getattr(j, "_ran", -1) == t or j.id in open_ids or j.finish == t + 1:
                jobs.append(job_doc(j, t))
        d, h = model_date(year, t)
        out.append({
            "t": t, "date": d, "hour": h,
            "sites": [{
                "temp": round(temps[s][t], 1),
                "demand": round(x.demand, 3), "soc0": round(x.soc0, 3), "room": round(x.room, 3),
                "permit": x.permit, "reserve_u": round(x.reserve_u, 3), "limit": x.limit,
                "running": x.running, "forced": x.forced, "served": round(x.served, 3),
                "soc": round(x.soc, 3), "dumped": round(x.dumped, 3),
                "paused": x.paused, "checkpointed": x.checkpointed, "moved_in": x.moved_in,
                "started": x.started, "finished": x.finished,
                "embed_sh": round(x.embed_sh, 3), "rerank_sh": round(x.rerank_sh, 3),
                "heat_soon": bool(sch._will_have_heat(s, t)),
                "down": bool(x.down),
                "actions": [list(a) for a in x.actions],
            } for s, x in enumerate(step)],
            "jobs": jobs,
        })
    return {
        "year": year, "day": day, "hour": hour,
        "sites": [dict(s.to_dict()) for s in sites],
        "job_types": {k: {"server_h": v.sh, "due_h": v.due_h, "arrival_hours": list(v.arrival_hours),
                          "backlog": not v.deadline_job} for k, v in sch.types.items()},
        "hours": out,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--day", type=int, default=195, help="day of the year, 0 = 1 January (195 = 15 July)")
    ap.add_argument("--hour", type=int, default=6)
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--fleet", action="store_true", help="the dashboard's three sites instead of the reference house")
    ap.add_argument("--stdin", action="store_true", help="read {year, sites, day, hour, hours} as JSON from stdin")
    a = ap.parse_args()
    if a.stdin:
        req = json.load(sys.stdin)
        r = run(req["sites"], int(req.get("year", 2025)), int(req.get("day", 195)), int(req.get("hour", 6)),
                int(req.get("hours", 24)), req.get("outages", ()), req.get("sizing"))
    else:
        r = run(DEFAULT_SITES if a.fleet else REFERENCE, a.year, a.day, a.hour, a.hours)
    json.dump(r, sys.stdout, separators=(",", ":"))


if __name__ == "__main__":
    main()
