"""Exploratory baseline for the reference house (written overnight 2026-11-21).

NOT the team's scheduler. A minimal hourly energy balance used to ground the
assessment in docs/overnight-assessment.md: how the key figures move with the
number of servers and the run policy, before any job model exists.

    python3 analysis/baseline_sweep.py

Case constants: 1 kW server, 80 % heat recovery, 35 kWh lossless tank,
0.3325 CHF/kWh electricity, heat valued at price / 2.5.
Policies:
  follow    run only as many whole servers as demand + free tank space absorbs
            (never dumps heat; greedy tank filling is optimal for a lossless tank)
  always    all servers run all year; surplus beyond demand + tank is dumped
  floor=k   'follow', but k servers never stop (a contracted compute baseline)
Switches (off by default = case assumptions):
  tank_loss_kwh_day   standby loss taken from the tank every hour
  dhw_direct_share    share of hot-water energy that server heat can deliver;
                      the rest needs a booster outside the model
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICE = 0.3325            # CHF/kWh electricity (ElCom 2026, IWB, H4)
HEAT_VALUE = PRICE / 2.5  # CHF/kWh heat (case rule)
P_EL = 1.0                # kW per server
REC = 0.8                 # recovered heat fraction
TANK = 35.0               # kWh usable


def load():
    with open(ROOT / "data" / "reference_house_2025_hourly.csv") as f:
        return [(r["time_local"], float(r["space_heating_kwh"]), float(r["hot_water_kwh"]))
                for r in csv.DictReader(f)]


def simulate(rows, n, policy="follow", floor=0, tank_loss_kwh_day=0.0,
             dhw_direct_share=1.0, tank=TANK):
    soc = 0.0
    used = dumped = run_h = demand_tot = 0.0
    lost = 0.0
    idle_run = longest_idle = 0          # hours with zero servers running
    monthly = {}
    q1 = REC * P_EL
    for t, sh, dhw in rows:
        d = sh + dhw * dhw_direct_share   # demand server heat may serve
        demand_tot += sh + dhw            # coverage is always vs. full demand
        loss = min(soc, tank_loss_kwh_day / 24.0)
        soc -= loss
        lost += loss
        if policy == "always":
            k = n
        else:
            k = min(n, int((d + tank - soc) / q1 + 1e-9))
            k = max(k, min(floor, n))
        heat = k * q1
        avail = soc + heat
        u = min(d, avail)
        soc = avail - u
        dump = max(0.0, soc - tank)
        soc -= dump
        used += u
        dumped += dump
        run_h += k
        if k == 0:
            idle_run += 1
            longest_idle = max(longest_idle, idle_run)
        else:
            idle_run = 0
        m = monthly.setdefault(t[5:7], [0.0, 0.0, 0.0])
        m[0] += k
        m[1] += u
        m[2] += sh + dhw
    elec = run_h * P_EL * PRICE
    heat_val = used * HEAT_VALUE
    return {
        "n": n, "coverage": used / demand_tot, "used": used, "dumped": dumped,
        "tank_lost": lost, "util": run_h / (n * 8760) if n else 0.0, "run_h": run_h,
        "elec": elec, "heat_val": heat_val,
        "breakeven": (elec - heat_val) / run_h if run_h else float("nan"),
        "longest_idle_h": longest_idle, "monthly": monthly,
    }


def line(r, label=""):
    return (f"{label:<22}{r['n']:>3} {r['coverage']*100:>7.1f}% {r['dumped']:>8.0f} "
            f"{r['util']*100:>6.1f}% {r['run_h']:>8.0f} {r['elec']:>8.0f} {r['heat_val']:>8.0f} "
            f"{r['breakeven']:>7.4f} {r['longest_idle_h']:>6}")


HDR = (f"{'case':<22}{'N':>3} {'cover':>8} {'dump kWh':>8} {'util':>7} {'srv-h':>8} "
       f"{'elec CHF':>8} {'heat CHF':>8} {'BE/h':>7} {'idle h':>6}")

if __name__ == "__main__":
    rows = load()
    print("Total demand kWh:", round(sum(a + b for _, a, b in rows)))
    print("\n== follow (no dumping), case assumptions ==\n" + HDR)
    prev = None
    for n in range(1, 14):
        r = simulate(rows, n)
        extra = ""
        if prev:
            extra = f"   marginal server: +{(r['coverage']-prev['coverage'])*100:.1f} pts, runs {r['run_h']-prev['run_h']:.0f} h/yr"
        print(line(r, "follow") + extra)
        prev = r
    print("\n== always-on (dump surplus) ==\n" + HDR)
    for n in (1, 2, 4, 6, 8, 13):
        print(line(simulate(rows, n, "always"), "always"))
    print("\n== follow with k servers never stopping ==\n" + HDR)
    for n, k in ((4, 1), (6, 1), (6, 2), (8, 2)):
        print(line(simulate(rows, n, floor=k), f"floor={k}"))
    print("\n== realism switches, follow ==\n" + HDR)
    for n in (1, 4, 6, 8):
        print(line(simulate(rows, n, tank_loss_kwh_day=3.0), "tank loss 3/d"))
        print(line(simulate(rows, n, tank_loss_kwh_day=3.0, dhw_direct_share=0.0), "+no direct DHW"))
    print("\n== tank size, N=6, follow ==\n" + HDR)
    for tk in (0.001, 10, 35, 70, 140):
        print(line(simulate(rows, 6, tank=tk), f"tank {tk:g} kWh"))
    print("\n== monthly server-hours and coverage, follow ==")
    for n in (1, 4, 6, 8):
        r = simulate(rows, n)
        print(f"N={n}: " + "  ".join(f"{m}:{v[0]:.0f}h/{(v[1]/v[2]*100 if v[2] else 0):.0f}%"
                                      for m, v in sorted(r["monthly"].items())))
