"""Yearly balance: run the scheduler over every hour of a year and report the case's key figures.

    python -m scheduler.balance                        # reference house alone, 2025 (must-have 3)
    python -m scheduler.balance --servers 6 --year 2024
    python -m scheduler.balance --sweep 1-12           # servers per house
    python -m scheduler.balance --config sites.json    # any sites (see DEFAULT_SITES)
    python -m scheduler.balance --stdin --json -       # what the dashboard calls

Key figures per site and for the fleet (case, must-have 3): servers, share of heat demand
covered, heat dumped, utilisation (server running hours / servers x 8,760), missed deadlines
in % of jobs, electricity cost, value of the heat used, break-even computing price
(electricity cost - value of the heat used) / server-hours sold. On top: the same price with
a hardware write-off (our assumption, CHF per server and year), which the dashboard shows.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from scheduler.core import REC, Scheduler, job_types
from scheduler.sites import KINDS, Site, demand
from scheduler.weather import H, temperatures

ROOT = Path(__file__).resolve().parent.parent
ELCOM = ROOT / "data" / "raw" / "elcom_iwb_H4_2025_2026.json"
HW_CHF_PER_SERVER = 4000.0  # our assumption, not sourced; written off over HW_YEARS
HW_YEARS = 5

DEFAULT_SITES = [
    {"id": "BS-H1", "kind": "hospital", "name": "Hospital", "lat": 47.5535, "lon": 7.5705},
    {"id": "BS-01", "kind": "house", "name": "House", "lat": 47.5695, "lon": 7.588},
    {"id": "BS-S1", "kind": "spa", "name": "Spa & pool", "lat": 47.555, "lon": 7.6075},
]
REFERENCE = [{"id": "BS-01", "kind": "house", "name": "Reference house", "lat": 47.56, "lon": 7.59}]


def electricity_price():
    """ElCom 2026, IWB, Basel, H4, total incl. all fees (CHF/kWh)."""
    obs = json.loads(ELCOM.read_text())["data"]["observations"]
    for o in obs:
        if o["period"] == "2026" and o["municipalityLabel"] == "Basel":
            return o["total"] / 100
    raise LookupError("ElCom 2026 Basel H4 not in " + str(ELCOM))


def run(sites_in, year=2025, pool=True, hw_chf=HW_CHF_PER_SERVER, series=True):
    t0 = time.time()
    sites = [Site.from_dict(s) for s in sites_in]
    dem = [demand(s, temperatures(s.lat, s.lon, year)) for s in sites]
    types = job_types()
    sch = Scheduler(sites, dem, types, pool=pool)
    keys = ("demand", "soc", "served", "dumped", "permit", "reserve_u", "limit", "running", "forced",
            "rerank_sh", "embed_sh", "paused", "checkpointed", "moved_in", "started", "finished")
    ser = [{k: [0] * H for k in keys} for _ in sites]
    embed_started = [0] * H
    tot = [{"run": 0, "served": 0.0, "demand": 0.0, "dumped": 0.0, "forced": 0, "paused": 0,
            "checkpointed": 0, "moved": 0} for _ in sites]
    for t in range(H):
        for s, h in enumerate(sch.step(t)):
            x, a = ser[s], tot[s]
            x["demand"][t] = round(h.demand, 3)
            x["soc"][t] = round(h.soc, 3)
            x["served"][t] = round(h.served, 3)
            x["dumped"][t] = round(h.dumped, 3)
            x["permit"][t] = h.permit
            x["reserve_u"][t] = round(h.reserve_u, 3)
            x["limit"][t] = h.limit
            x["running"][t] = h.running
            x["forced"][t] = h.forced
            x["rerank_sh"][t] = round(h.rerank_sh, 3)
            x["embed_sh"][t] = round(h.embed_sh, 3)
            x["paused"][t] = h.paused
            x["checkpointed"][t] = h.checkpointed
            x["moved_in"][t] = h.moved_in
            x["started"][t] = h.started
            x["finished"][t] = h.finished
            a["run"] += h.running
            a["served"] += h.served
            a["demand"] += h.demand
            a["dumped"] += h.dumped
            a["forced"] += h.forced
            a["paused"] += h.paused
            a["checkpointed"] += h.checkpointed
            a["moved"] += h.moved_in
        embed_started[t] = sch.count.get("embed", 0)  # embedding jobs handed out so far
    # jobs
    jobs = sch.jobs
    per_site_jobs = [{"done": 0, "missed": 0, "open": 0} for _ in sites]
    by_type = {k: {"done": 0, "missed": 0, "open": 0, "forced": 0, "moves": 0, "pauses": 0, "checkpoints": 0}
               for k in types}
    for j in jobs:
        st = "done" if j.state == "done" else "missed" if j.state == "missed" else "open"
        by_type[j.type][st] += 1
        by_type[j.type]["forced"] += j.forced
        by_type[j.type]["moves"] += j.moves
        by_type[j.type]["pauses"] += j.pauses
        by_type[j.type]["checkpoints"] += j.checkpoints
        per_site_jobs[j.origin][st] += 1
    price = electricity_price()
    heat_value = price / 2.5

    def figures(idx):
        n = sum(sites[i].servers for i in idx)
        run_sh = sum(tot[i]["run"] for i in idx)
        served = sum(tot[i]["served"] for i in idx)
        dem_ = sum(tot[i]["demand"] for i in idx)
        dumped = sum(tot[i]["dumped"] for i in idx)
        done = sum(per_site_jobs[i]["done"] for i in idx)
        missed = sum(per_site_jobs[i]["missed"] for i in idx)
        elec = run_sh * price
        hv = served * heat_value
        hw = n * hw_chf / HW_YEARS
        return {
            "servers": n,
            "demand_kwh": round(dem_),
            "served_kwh": round(served),
            "coverage": round(served / dem_, 4) if dem_ else 0,
            "server_heat_kwh": round(run_sh * REC),
            "dumped_kwh": round(dumped, 1),
            "run_server_h": run_sh,
            "utilisation": round(run_sh / (n * H), 4) if n else 0,
            "jobs_done": done,
            "jobs_missed": missed,
            "missed_pct": round(100 * missed / (done + missed), 3) if done + missed else 0,
            "forced_server_h": sum(tot[i]["forced"] for i in idx),
            "pauses": sum(tot[i]["paused"] for i in idx),
            "checkpoints": sum(tot[i]["checkpointed"] for i in idx),
            "moves_in": sum(tot[i]["moved"] for i in idx),
            "electricity_chf": round(elec, 2),
            "heat_value_chf": round(hv, 2),
            "hardware_chf": round(hw, 2),
            "break_even_chf_per_server_h": round((elec - hv) / run_sh, 4) if run_sh else None,
            "price_chf_per_server_h": round((elec - hv + hw) / run_sh, 4) if run_sh else None,
        }

    out = {
        "year": year,
        "pool": pool,
        "constants": {"server_kw": 1.0, "heat_recovery": REC, "electricity_chf_kwh": price,
                      "heat_value_chf_kwh": round(heat_value, 4), "hardware_chf_per_server": hw_chf,
                      "hardware_years": HW_YEARS},
        "job_types": {k: {"server_h": v.sh, "due_h": v.due_h, "arrival_hours": list(v.arrival_hours),
                          "backlog": not v.deadline_job} for k, v in types.items()},
        "sites": [dict(s.to_dict(), label=KINDS[s.kind]["label"], year=figures([i])) for i, s in enumerate(sites)],
        "fleet": figures(range(len(sites))),
        "jobs_by_type": by_type,
        "seconds": round(time.time() - t0, 2),
    }
    if series:
        out["series"] = ser
        out["embed_ids"] = embed_started
        out["deadline_jobs"] = [[j.id, j.origin, j.arrive, j.due, j.site, j.start, j.finish,
                                 {"done": 0, "missed": 1}.get(j.state, 2), int(j.forced)]
                                for j in jobs if j.type != "embed"]
    return out


def print_figures(r):
    rows = [(s["id"] + " " + s["name"], s["year"]) for s in r["sites"]]
    if len(rows) > 1:
        rows.append(("Fleet", r["fleet"]))
    c = r["constants"]
    print(f"Year {r['year']} · electricity {c['electricity_chf_kwh']:.4f} CHF/kWh · heat {c['heat_value_chf_kwh']:.4f} CHF/kWh"
          f" · {r['seconds']} s")
    hdr = f"{'':<24}{'servers':>8}{'covered':>9}{'dumped':>9}{'util.':>7}{'missed':>8}{'elec CHF':>10}{'heat CHF':>10}{'b-even':>8}{'+hw':>7}"
    print(hdr)
    for name, f in rows:
        print(f"{name[:23]:<24}{f['servers']:>8}{f['coverage'] * 100:>8.1f}%{f['dumped_kwh']:>8.0f}k"
              f"{f['utilisation'] * 100:>6.1f}%{f['missed_pct']:>7.2f}%{f['electricity_chf']:>10.0f}"
              f"{f['heat_value_chf']:>10.0f}{f['break_even_chf_per_server_h'] or 0:>8.3f}{f['price_chf_per_server_h'] or 0:>7.3f}")
    for k, v in r["jobs_by_type"].items():
        print(f"  {k:<7} done {v['done']:>6}  missed {v['missed']:>3}  open {v['open']:>3}  forced {v['forced']:>3}"
              f"  paused {v['pauses']:>5}  checkpointed {v['checkpoints']:>5}  moved {v['moves']:>5}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--servers", type=int, help="servers at the reference house")
    ap.add_argument("--config", help="JSON list of sites")
    ap.add_argument("--fleet", action="store_true", help="the dashboard's three Basel sites")
    ap.add_argument("--stdin", action="store_true", help='read {"year", "sites", "pool", "hw_chf"} from stdin')
    ap.add_argument("--no-pool", action="store_true", help="jobs stay at the site they arrived at")
    ap.add_argument("--sweep", help="servers per house, e.g. 1-12")
    ap.add_argument("--json", help="write the full result (with hourly series) to this file, - for stdout")
    a = ap.parse_args()

    if a.stdin:
        req = json.load(sys.stdin)
        r = run(req["sites"], int(req.get("year", 2025)), bool(req.get("pool", True)),
                float(req.get("hw_chf", HW_CHF_PER_SERVER)))
        json.dump(r, sys.stdout, separators=(",", ":"))
        return
    sites = json.loads(Path(a.config).read_text()) if a.config else DEFAULT_SITES if a.fleet else REFERENCE
    if a.sweep:
        lo, hi = (int(x) for x in a.sweep.split("-"))
        print(f"Reference house, {a.year}: servers per house")
        print(f"{'servers':>8}{'covered':>9}{'dumped':>9}{'util.':>8}{'missed':>8}{'b-even':>8}{'+hw':>7}")
        for n in range(lo, hi + 1):
            f = run([dict(REFERENCE[0], servers=n)], a.year, not a.no_pool, series=False)["fleet"]
            print(f"{n:>8}{f['coverage'] * 100:>8.1f}%{f['dumped_kwh']:>8.0f}k{f['utilisation'] * 100:>7.1f}%"
                  f"{f['missed_pct']:>7.2f}%{f['break_even_chf_per_server_h']:>8.3f}{f['price_chf_per_server_h']:>7.3f}")
        return
    if a.servers is not None:
        sites = [dict(s, servers=a.servers) for s in sites]
    r = run(sites, a.year, not a.no_pool, series=bool(a.json))
    print_figures(r)
    if a.json:
        if a.json == "-":
            json.dump(r, sys.stdout, separators=(",", ":"))
        else:
            Path(a.json).write_text(json.dumps(r, separators=(",", ":")))
            print("wrote", a.json)


if __name__ == "__main__":
    main()
