"""Yearly balance: run the scheduler over every hour of a year and report the case's key figures.

    python -m scheduler.balance                        # reference house alone, 2025 (must-have 3)
    python -m scheduler.balance --servers 6 --year 2024
    python -m scheduler.balance --sweep 1-12           # servers per house
    python -m scheduler.balance --config sites.json    # any sites (see DEFAULT_SITES)
    python -m scheduler.balance --stdin --json -       # what the dashboard calls
    python -m scheduler.balance --scenario services --monthly   # business mix: homes, office, pharma, ...
    python -m scheduler.balance --scenario services --partial --drycooler 4 --cool-fill
    python -m scheduler.balance --scenario services --outage BS-P1:20:48:7   # site down day 20 from 07:00, 48 h

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

from scheduler.core import REC, Scheduler, job_types, service_job_types
from scheduler.sites import KINDS, Site, demand
from scheduler.weather import H, temperatures

ROOT = Path(__file__).resolve().parent.parent
ELCOM = ROOT / "data" / "raw" / "elcom_iwb_H4_2025_2026.json"
from scheduler.pricing import HW_CHF_PER_SERVER, HW_YEARS, ON_DEMAND_CHF_H, SELL_CHF_H, SPOT_CHF_H, job_prices, pays_off

DEFAULT_SITES = [
    {"id": "BS-H1", "kind": "hospital", "name": "Hospital", "lat": 47.5535, "lon": 7.5705},
    {"id": "BS-01", "kind": "house", "name": "House", "lat": 47.5695, "lon": 7.588},
    {"id": "BS-S1", "kind": "spa", "name": "Spa & pool", "lat": 47.555, "lon": 7.6075},
]
REFERENCE = [{"id": "BS-01", "kind": "house", "name": "Reference house", "lat": 47.56, "lon": 7.59}]
# The business case's fleet (docs/business-model.md): homes in the evening, businesses by day,
# and sites that need heat in summer. All in Basel, so they share one weather year.
SERVICES = [
    {"id": "BS-01", "kind": "house", "name": "Reference house", "lat": 47.56, "lon": 7.59},
    {"id": "BS-F1", "kind": "family", "name": "Family home (5)", "lat": 47.5695, "lon": 7.588},
    {"id": "BS-H1", "kind": "hospital", "name": "Hospital", "lat": 47.5535, "lon": 7.5705},
    {"id": "BS-S1", "kind": "spa", "name": "Spa & pool", "lat": 47.555, "lon": 7.6075},
    {"id": "BS-O1", "kind": "office", "name": "Office", "lat": 47.5475, "lon": 7.5895},
    {"id": "BS-P1", "kind": "pharma", "name": "Pharma lab", "lat": 47.5705, "lon": 7.5745},
]
SCENARIOS = {"reference": REFERENCE, "fleet": DEFAULT_SITES, "services": SERVICES}
MONTH_START = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]


def electricity_price():
    """ElCom 2026, IWB, Basel, H4, total incl. all fees (CHF/kWh)."""
    obs = json.loads(ELCOM.read_text())["data"]["observations"]
    for o in obs:
        if o["period"] == "2026" and o["municipalityLabel"] == "Basel":
            return o["total"] / 100
    raise LookupError("ElCom 2026 Basel H4 not in " + str(ELCOM))


def run(sites_in, year=2025, pool=True, hw_chf=HW_CHF_PER_SERVER, series=True, sell=SELL_CHF_H, types=None,
        partial=False, cool_fill=False, outages=()):
    """outages: (site id, first day, hours[, start hour]) tuples."""
    t0 = time.time()
    sites = [Site.from_dict(s) for s in sites_in]
    dem = [demand(s, temperatures(s.lat, s.lon, year), year) for s in sites]
    types = types or job_types()
    idx = {s.id: i for i, s in enumerate(sites)}
    outs = [(idx[o[0]], int(o[1]) * 24 + (int(o[3]) if len(o) > 3 else 0), int(o[2])) for o in outages]
    sch = Scheduler(sites, dem, types, pool=pool, partial=partial, cool_fill=cool_fill, outages=outs)
    months = [{"permit_sh": 0.0, "run_sh": 0.0, "heat_sh": 0.0, "cooled_sh": 0.0, "demand": 0.0, "served": 0.0,
               "dumped": 0.0, "queue_sh": 0.0, "queue_jobs": 0, "by_type": {k: 0.0 for k in ("embed", "rerank", "other")}}
              for _ in range(12)]
    keys = ("demand", "soc", "served", "dumped", "permit", "reserve_u", "limit", "running", "forced",
            "rerank_sh", "embed_sh", "paused", "checkpointed", "moved_in", "started", "finished",
            "paused_now", "waiting_now")
    ser = [{k: [0] * H for k in keys} for _ in sites]
    embed_started = [0] * H
    tot = [{"run": 0, "served": 0.0, "demand": 0.0, "dumped": 0.0, "forced": 0, "paused": 0,
            "checkpointed": 0, "moved": 0, "cooled": 0.0, "fan": 0.0, "on_h": 0, "down_h": 0,
            "summer_run": 0.0} for _ in sites]
    for t in range(H):
        m = next(i for i in range(12) if t < MONTH_START[i + 1] * 24)
        mo = months[m]
        step = sch.step(t)
        # jobs standing still at the end of this hour: paused in memory, or saved and waiting
        for j in sch.open:
            if j.site >= 0 and j.state == "paused":
                ser[j.site]["paused_now"][t] += 1
            elif j.site >= 0 and j.state == "checkpointed":
                ser[j.site]["waiting_now"][t] += 1
        for s, h in enumerate(step):
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
            a["cooled"] += h.cooled
            a["fan"] += h.fan_kwh
            a["on_h"] += h.on > 0
            a["down_h"] += h.down
            a["summer_run"] += h.running if 3 <= m <= 8 else 0
            mo["permit_sh"] += h.permit
            mo["run_sh"] += h.running
            mo["heat_sh"] += h.running - h.cooled
            mo["cooled_sh"] += h.cooled
            mo["demand"] += h.demand
            mo["served"] += h.served
            mo["dumped"] += h.dumped
            mo["by_type"]["embed"] += h.embed_sh
            mo["by_type"]["rerank"] += h.rerank_sh
            mo["by_type"]["other"] += h.other_sh
        embed_started[t] = sch.count.get("embed", 0)  # embedding jobs handed out so far
        if t + 1 == MONTH_START[m + 1] * 24:  # deferred work waiting at the end of the month
            q = [j for j in sch.open if j.type not in ("embed", "rerank")]
            mo["queue_sh"] = sum(j.left for j in q)
            mo["queue_jobs"] = len(q)
    # jobs
    jobs = sch.jobs
    per_site_jobs = [{"done": 0, "missed": 0, "open": 0} for _ in sites]
    by_type = {k: {"done": 0, "missed": 0, "open": 0, "lost": 0, "forced": 0, "moves": 0, "pauses": 0,
                   "checkpoints": 0, "restarts": 0} for k in types}
    for j in jobs:
        st = j.state if j.state in ("done", "missed", "lost") else "open"
        by_type[j.type]["restarts"] += j.restarts
        if st == "lost":  # a copy dropped in an outage; its twin carries the job
            by_type[j.type]["lost"] += 1
            continue
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
        cooled = sum(tot[i]["cooled"] for i in idx)
        fan = sum(tot[i]["fan"] for i in idx)
        summer = sum(tot[i]["summer_run"] for i in idx)
        served = sum(tot[i]["served"] for i in idx)
        dem_ = sum(tot[i]["demand"] for i in idx)
        dumped = sum(tot[i]["dumped"] for i in idx)
        done = sum(per_site_jobs[i]["done"] for i in idx)
        missed = sum(per_site_jobs[i]["missed"] for i in idx)
        elec = (run_sh + fan) * price
        hv = served * heat_value
        hw = n * hw_chf / HW_YEARS
        f = {
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
            "cooled_server_h": round(cooled, 1),
            "fan_kwh": round(fan, 1),
            "summer_utilisation": round(summer / (n * 183 * 24), 4) if n else 0,
            "always_on_share": round(sum(tot[i]["on_h"] for i in idx) / (len(list(idx)) * H), 4) if n else 0,
            "down_h": sum(tot[i]["down_h"] for i in idx),
            "electricity_chf": round(elec, 2),
            "heat_value_chf": round(hv, 2),
            "hardware_chf": round(hw, 2),
            "break_even_chf_per_server_h": round((elec - hv) / run_sh, 4) if run_sh else None,
            "price_chf_per_server_h": round((elec - hv + hw) / run_sh, 4) if run_sh else None,
        }
        f["money"] = pays_off(f, price, heat_value, sell, hw_chf)
        return f

    out = {
        "year": year,
        "pool": pool,
        "constants": {"server_kw": 1.0, "heat_recovery": REC, "electricity_chf_kwh": price,
                      "heat_value_chf_kwh": round(heat_value, 4), "hardware_chf_per_server": hw_chf,
                      "hardware_years": HW_YEARS, "sell_chf_per_server_h": sell,
                      "aws_spot_chf_h": SPOT_CHF_H, "aws_on_demand_chf_h": ON_DEMAND_CHF_H},
        "job_prices": job_prices(types),
        "job_types": {k: {"server_h": v.sh, "due_h": v.due_h, "arrival_hours": list(v.arrival_hours),
                          "backlog": not v.deadline_job} for k, v in types.items()},
        "sites": [dict(s.to_dict(), label=KINDS[s.kind]["label"], year=figures([i])) for i, s in enumerate(sites)],
        "fleet": figures(range(len(sites))),
        "jobs_by_type": by_type,
        "lost_server_h": round(sch.lost_sh, 2),
        "options": {"partial": partial, "cool_fill": cool_fill, "outages": [list(o) for o in outages]},
        "monthly": [dict(mo, permit_sh=round(mo["permit_sh"], 1), run_sh=round(mo["run_sh"], 1),
                         heat_sh=round(mo["heat_sh"], 1), cooled_sh=round(mo["cooled_sh"], 1),
                         demand=round(mo["demand"]), served=round(mo["served"]), dumped=round(mo["dumped"], 1),
                         queue_sh=round(mo["queue_sh"], 1),
                         by_type={k: round(v, 1) for k, v in mo["by_type"].items()}) for mo in months],
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
    opts = [k for k, v in r["options"].items() if v]
    print(f"Year {r['year']} · electricity {c['electricity_chf_kwh']:.4f} CHF/kWh · heat {c['heat_value_chf_kwh']:.4f} CHF/kWh"
          f" · {r['seconds']} s" + (f" · options: {', '.join(opts)}" if opts else ""))
    hdr = f"{'':<24}{'servers':>8}{'covered':>9}{'dumped':>9}{'util.':>7}{'summer':>7}{'missed':>8}{'elec CHF':>10}{'heat CHF':>10}{'b-even':>8}{'+hw':>7}"
    print(hdr)
    for name, f in rows:
        print(f"{name[:23]:<24}{f['servers']:>8}{f['coverage'] * 100:>8.1f}%{f['dumped_kwh'] / 1000:>8.1f}M"
              f"{f['utilisation'] * 100:>6.1f}%{f['summer_utilisation'] * 100:>6.1f}%{f['missed_pct']:>7.2f}%{f['electricity_chf']:>10.0f}"
              f"{f['heat_value_chf']:>10.0f}{f['break_even_chf_per_server_h'] or 0:>8.3f}{f['price_chf_per_server_h'] or 0:>7.3f}")
    print("  (dumped in MWh; summer = utilisation April-September)")
    f = r["fleet"]
    if f["cooled_server_h"] or f["fan_kwh"]:
        print(f"  dry cooler: {f['cooled_server_h']:.0f} server-h ran with their heat sent outside, fan {f['fan_kwh']:.0f} kWh")
    if r["options"]["partial"]:
        print(f"  partial power: at least one server on in {f['always_on_share'] * 100:.1f}% of site-hours")
    for k, v in r["jobs_by_type"].items():
        extra = f"  lost copies {v['lost']}" if v["lost"] else ""
        extra += f"  restarted {v['restarts']}" if v["restarts"] else ""
        print(f"  {k:<7} done {v['done']:>6}  missed {v['missed']:>3}  open {v['open']:>4}  forced {v['forced']:>3}"
              f"  paused {v['pauses']:>5}  checkpointed {v['checkpoints']:>5}  moved {v['moves']:>5}{extra}")
    if r["lost_server_h"]:
        print(f"  work lost to outages: {r['lost_server_h']:.1f} server-h")
    for name, f in rows:
        m = f["money"]
        if not m:
            continue
        print(f"{name[:23]:<24}income {m['income_chf']:>9.0f}  hardware {f['hardware_chf']:>7.0f}  profit {m['profit_chf']:>9.0f} CHF/yr"
              f"  at CHF {m['sell_chf_per_server_h']}/server-h  ->  {'pays off' if m['pays_off'] else 'DOES NOT pay off'}")
        print(f"{'':<24}stops paying off below CHF {m['min_price_chf_per_server_h']}/server-h, below "
              f"{(m['min_utilisation'] or 0) * 100:.0f}% utilisation, above CHF {m['max_electricity_chf_kwh']}/kWh or "
              f"above CHF {m['max_hardware_chf_per_server']:,} per server")


def print_monthly(r):
    names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    n = r["fleet"]["servers"]
    print(f"{'month':<6}{'capacity':>10}{'cap %':>7}{'ran':>9}{'cooled':>8}{'embed':>9}{'rerank':>8}{'other':>8}"
          f"{'deferred':>10}{'jobs':>6}{'covered':>9}")
    for i, m in enumerate(r["monthly"]):
        hours = (MONTH_START[i + 1] - MONTH_START[i]) * 24
        cov = m["served"] / m["demand"] if m["demand"] else 0
        print(f"{names[i]:<6}{m['permit_sh']:>10.0f}{100 * m['permit_sh'] / (n * hours):>6.0f}%{m['run_sh']:>9.0f}"
              f"{m['cooled_sh']:>8.0f}{m['by_type']['embed']:>9.0f}{m['by_type']['rerank']:>8.0f}{m['by_type']['other']:>8.0f}"
              f"{m['queue_sh']:>10.0f}{m['queue_jobs']:>6}{cov * 100:>8.1f}%")
    print("  capacity = server-h whose heat the sites can use (heat permit); deferred = sim/twin server-h"
          " waiting at month end")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--servers", type=int, help="servers at every site")
    ap.add_argument("--config", help="JSON list of sites")
    ap.add_argument("--fleet", action="store_true", help="the dashboard's three Basel sites")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), help="reference, fleet, or services (business mix)")
    ap.add_argument("--stdin", action="store_true", help='read {"year", "sites", "pool", "hw_chf"} from stdin')
    ap.add_argument("--no-pool", action="store_true", help="jobs stay at the site they arrived at")
    ap.add_argument("--sweep", help="servers per house, e.g. 1-12")
    ap.add_argument("--services", action="store_true", help="add the sim and twin job types (default with --scenario services)")
    ap.add_argument("--sim-per-day", type=int, default=100, help="simulation jobs per day for the fleet (8 server-h each)")
    ap.add_argument("--twin-per-day", type=int, default=6, help="redundant jobs per day for the fleet")
    ap.add_argument("--replicas", type=int, default=2, help="copies of each redundant job (2-4)")
    ap.add_argument("--partial", action="store_true", help="servers may run at 30-100 %% power")
    ap.add_argument("--drycooler", type=float, help="dry cooler kW at every site")
    ap.add_argument("--cool-fill", action="store_true", help="spare servers run backlog work into the dry cooler")
    ap.add_argument("--outage", action="append", default=[], help="SITE_ID:FIRST_DAY:HOURS[:START_HOUR] (repeatable)")
    ap.add_argument("--monthly", action="store_true", help="print capacity and deferred work per month")
    ap.add_argument("--json", help="write the full result (with hourly series) to this file, - for stdout")
    a = ap.parse_args()

    if a.stdin:
        req = json.load(sys.stdin)
        r = run(req["sites"], int(req.get("year", 2025)), bool(req.get("pool", True)),
                float(req.get("hw_chf", HW_CHF_PER_SERVER)))
        json.dump(r, sys.stdout, separators=(",", ":"))
        return
    scenario = a.scenario or ("fleet" if a.fleet else "reference")
    sites = json.loads(Path(a.config).read_text()) if a.config else SCENARIOS[scenario]
    types = None
    if a.services or scenario == "services":
        types = service_job_types(a.sim_per_day, a.twin_per_day, a.replicas)
    if a.drycooler is not None:
        sites = [dict(s, drycooler_kw=a.drycooler) for s in sites]
    opts = dict(types=types, partial=a.partial, cool_fill=a.cool_fill,
                outages=[tuple(o.split(":")[:1]) + tuple(int(x) for x in o.split(":")[1:]) for o in a.outage])
    if a.sweep:
        lo, hi = (int(x) for x in a.sweep.split("-"))
        print(f"Reference house, {a.year}: servers per house")
        print(f"{'servers':>8}{'covered':>9}{'dumped':>9}{'util.':>8}{'missed':>8}{'b-even':>8}{'+hw':>7}")
        for n in range(lo, hi + 1):
            f = run([dict(REFERENCE[0], servers=n)], a.year, not a.no_pool, series=False, **opts)["fleet"]
            print(f"{n:>8}{f['coverage'] * 100:>8.1f}%{f['dumped_kwh']:>8.0f}k{f['utilisation'] * 100:>7.1f}%"
                  f"{f['missed_pct']:>7.2f}%{f['break_even_chf_per_server_h']:>8.3f}{f['price_chf_per_server_h']:>7.3f}")
        return
    if a.servers is not None:
        sites = [dict(s, servers=a.servers) for s in sites]
    r = run(sites, a.year, not a.no_pool, series=bool(a.json), **opts)
    print_figures(r)
    if a.monthly:
        print_monthly(r)
    if a.json:
        if a.json == "-":
            json.dump(r, sys.stdout, separators=(",", ":"))
        else:
            Path(a.json).write_text(json.dumps(r, separators=(",", ":")))
            print("wrote", a.json)


if __name__ == "__main__":
    main()
