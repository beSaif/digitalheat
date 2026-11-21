"""Round 3, weak point "creativity and one-minute usability": numbers for the
candidate creative angles and for the one-minute screen. Exploratory, standard
library only. NOT the team's scheduler.

    python3 analysis/r3_creativity_usability.py

Imports load() and simulate() from analysis/baseline_sweep.py unchanged
(case assumptions: 1 kW server, 80 % recovery, lossless 35 kWh tank,
0.3325 CHF/kWh, heat valued at price / 2.5, plain 'follow' policy, unlimited
jobs). Every figure printed here is therefore "computed on the stand-in
profile, unlimited jobs", unless the line says "assumption".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import load, simulate, PRICE, HEAT_VALUE, REC, P_EL  # noqa: E402

C_WATER = 1.163  # Wh per litre and kelvin (specific heat of water)

rows = load()
Q1 = REC * P_EL  # kWh recovered heat per server-hour


def section(title):
    print("\n== " + title + " ==")


# ---------------------------------------------------------------- 1
section("1. Heat receipt: what one server-hour and one job deliver")
# Case: hot water 12 kWh/day, household of four, about 50 l per person and day.
dhw_kwh_day, persons, l_per_person = 12.0, 4, 50.0
kwh_per_l_case = dhw_kwh_day / (persons * l_per_person)
dt_case = kwh_per_l_case * 1000 / C_WATER
print(f"Case hot water: {dhw_kwh_day} kWh/day for {persons} x {l_per_person:.0f} l = "
      f"{kwh_per_l_case*1000:.0f} Wh per litre -> implied temperature rise "
      f"{dt_case:.1f} K (litres x K x {C_WATER} Wh/(l K))")
kwh_person_day = dhw_kwh_day / persons
print(f"One person's hot water for one day (case): {kwh_person_day:.2f} kWh")
# Shower, own assumption (NOT from the case): 50 l of mixed water, 10 -> 38 C
shower_l, shower_dt = 50.0, 28.0
shower_kwh = shower_l * shower_dt * C_WATER / 1000
print(f"One shower (assumption: {shower_l:.0f} l mixed water, +{shower_dt:.0f} K): "
      f"{shower_l:.0f} x {shower_dt:.0f} x {C_WATER} = {shower_kwh:.2f} kWh")
# Space heating: reference house at 0 C outdoor
kw_at_0 = 10 * (20 - 0) / 25.6
print(f"Reference house space heating at 0 C outdoor: {kw_at_0:.2f} kW (case formula)")
jobs = (("1 server-hour", 1.0), ("J1 (0.5 server-h, assumption)", 0.5),
        ("J2 (4 server-h, assumption)", 4.0))
print(f"{'unit':<32}{'heat kWh':>9}{'l hot water':>12}{'person-days':>12}"
      f"{'showers':>9}{'min heating @0C':>17}{'heat value CHF':>15}")
for name, sh in jobs:
    h = sh * Q1
    print(f"{name:<32}{h:>9.2f}{h/kwh_per_l_case:>12.1f}{h/kwh_person_day:>12.2f}"
          f"{h/shower_kwh:>9.2f}{h/kw_at_0*60:>17.1f}{h*HEAT_VALUE:>15.4f}")
tok_j2 = 17.7e6  # overnight.md: J2 = about 17.7 M output tokens IF the system drew 1 kW (unverified)
print(f"J2 per million output tokens (basis 17.7 M tokens per job is UNVERIFIED): "
      f"{4*Q1/tok_j2*1e6*1000:.0f} Wh heat = {4*Q1/tok_j2*1e6/kwh_per_l_case:.1f} l of case hot water")
print("Receipt is valid only for hours with zero dumping. Check, follow policy:")
for n in (6, 8):
    r = simulate(rows, n)
    print(f"  N={n}: run hours x 0.8 = {r['run_h']*Q1:.0f} kWh, heat used = {r['used']:.0f} kWh, "
          f"dumped = {r['dumped']:.0f} kWh, difference (left in tank at year end) = "
          f"{r['run_h']*Q1 - r['used']:.1f} kWh")

# ---------------------------------------------------------------- 2
section("2. Heat-flex tariff: how large a discount the heat can fund")
be_heat = PRICE - Q1 * HEAT_VALUE       # net cost of a heat-matched server-hour
be_dump = PRICE                         # server-hour whose heat is not used
print(f"Net electricity cost, heat-matched server-hour: {be_heat:.4f} CHF")
print(f"Net electricity cost, server-hour with heat unused: {be_dump:.4f} CHF")
print(f"Difference = heat credit per server-hour: {be_dump-be_heat:.4f} CHF "
      f"= {(be_dump-be_heat)/be_dump*100:.1f} % of the unmatched cost")
print("Reading: a job that waits for a heat permit can be priced at most "
      f"{(be_dump-be_heat)/be_dump*100:.0f} % below a job that must run now, "
      "if the discount is funded by the heat value alone (operator keeps the heat value).")
print("If the homeowner gets the heat free, the heat funds no discount (0 %).")
print("\nPermit capacity by month, 2025 stand-in, plain follow (server-hours per day):")
days = {"01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
        "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31}
res = {n: simulate(rows, n) for n in (6, 8)}
print("month  " + "  ".join(f"N={n} srv-h/day  % of Jan" for n in (6, 8)))
jan = {n: res[n]["monthly"]["01"][0] / 31 for n in (6, 8)}
for m in sorted(days):
    cells = []
    for n in (6, 8):
        per_day = res[n]["monthly"][m][0] / days[m]
        cells.append(f"{per_day:>13.1f}  {per_day/jan[n]*100:>7.0f}%")
    print(f"{m}     " + "  ".join(cells))
for n in (6, 8):
    mon = res[n]["monthly"]
    summer = sum(mon[m][0] for m in ("06", "07", "08"))
    winter = sum(mon[m][0] for m in ("12", "01", "02"))
    print(f"N={n}: Jun-Aug {summer:.0f} server-h ({summer/res[n]['run_h']*100:.1f} % of the year), "
          f"Dec-Feb {winter:.0f} server-h ({winter/res[n]['run_h']*100:.1f} %), ratio winter/summer {winter/summer:.1f}")

# How long does a job wait for heat if it is alone in the queue?  For each
# start hour: hours until `need` permit-hours (server-hours the follow policy
# would run) have accumulated at this one house.
section("2b. Wait for heat, one house, empty queue (hours until the job's server-hours have been permitted)")


def permit_series(n):
    """Server count per hour under plain follow (re-run of the baseline rule)."""
    soc, out = 0.0, []
    for _, sh, dhw in rows:
        d = sh + dhw
        k = min(n, int((d + 35.0 - soc) / Q1 + 1e-9))
        avail = soc + k * Q1
        u = min(d, avail)
        soc = avail - u
        out.append(k)
    return out


def waits(series, need, month):
    """Elapsed hours to accumulate `need` server-hours, max 1 server per job."""
    out = []
    hrs = len(series)
    for i, (t, _, _) in enumerate(rows):
        if t[5:7] != month:
            continue
        got, j = 0.0, i
        while got < need and j < hrs:
            got += 1.0 if series[j] >= 1 else 0.0
            j += 1
        if got >= need:
            out.append(j - i)
    out.sort()
    return out


for n in (6,):
    s = permit_series(n)
    assert abs(sum(s) - res[n]["run_h"]) < 1e-6, "permit series must reproduce the baseline"
    print(f"N={n}; a job uses one server; wait = clock hours from arrival to completion")
    print(f"{'month':<7}{'job':<6}{'median h':>9}{'P90 h':>7}{'max h':>7}")
    for m in ("01", "04", "07", "10"):
        for name, need in (("J1", 0.5), ("J2", 4.0)):
            w = waits(s, need, m)
            print(f"{m:<7}{name:<6}{w[len(w)//2]:>9}{w[int(len(w)*0.9)]:>7}{w[-1]:>7}")
    print("Reading: with an empty queue the wait is short even in July; in summer the limit is "
          "the QUANTITY of permits per day (table above), not the delay to the next one.")

# ---------------------------------------------------------------- 3
section("3. Sizing rule: 'servers follow the Xth percentile hour'")
dem = sorted(a + b for _, a, b in rows)
heat_hours = sorted(a + b for _, a, b in rows if a > 0)
print(f"Hours in year: {len(dem)}; hours with space heating: {len(heat_hours)}")
print(f"{'N':>3}{'N x 0.8 kW':>11}{'hours demand >= that':>22}{'= percentile (all h)':>21}"
      f"{'percentile (heating h)':>24}{'run h of Nth server':>21}")
prev = 0.0
for n in range(1, 14):
    cap = n * Q1
    ge = sum(1 for x in dem if x >= cap - 1e-9)
    pct_all = (len(dem) - ge) / len(dem) * 100
    ge_h = sum(1 for x in heat_hours if x >= cap - 1e-9)
    pct_h = (len(heat_hours) - ge_h) / len(heat_hours) * 100
    r = simulate(rows, n)
    print(f"{n:>3}{cap:>11.1f}{ge:>22}{pct_all:>20.1f}%{pct_h:>23.1f}%{r['run_h']-prev:>21.0f}")
    prev = r["run_h"]
for q in (50, 75, 90, 95, 99):
    v = dem[int(len(dem) * q / 100) - 1]
    vh = heat_hours[int(len(heat_hours) * q / 100) - 1]
    print(f"P{q} hourly demand: all hours {v:.2f} kW -> {v/Q1:.1f} servers; "
          f"heating hours {vh:.2f} kW -> {vh/Q1:.1f} servers")

# ---------------------------------------------------------------- 4
section("4. Neighbourhood view: summer surplus that a year-round heat user would have to take")
for n in (6, 8):
    r = res[n]
    idle = n * 8760 - r["run_h"]
    mon = r["monthly"]
    s_run = sum(mon[m][0] for m in ("06", "07", "08"))
    s_idle = n * 92 * 24 - s_run
    print(f"N={n}: idle server-hours per year {idle:.0f} (= {idle*Q1:.0f} kWh heat if run elsewhere); "
          f"Jun-Aug idle {s_idle:.0f} server-h = {s_idle/(92*24):.2f} servers continuously "
          f"= {s_idle*Q1/(92*24):.2f} kW of heat, {s_idle*Q1:.0f} kWh over the three months")
    print(f"      electricity for those Jun-Aug hours: {s_idle*PRICE:.0f} CHF; heat value if a "
          f"year-round user pays the case rate: {s_idle*Q1*HEAT_VALUE:.0f} CHF")

# ---------------------------------------------------------------- 5
section("5. Homeowner figures for the one-minute screen (case assumptions, unlimited jobs)")
for n in (6, 8):
    r = res[n]
    total = r["used"] / r["coverage"]
    print(f"N={n}: heat from servers {r['used']:.0f} kWh of {total:.0f} kWh ({r['coverage']*100:.1f} %), "
          f"backup heater {total-r['used']:.0f} kWh, heat value {r['heat_val']:.0f} CHF/yr, "
          f"servers' electricity {r['elec']:.0f} CHF/yr, heat dumped {r['dumped']:.0f} kWh, "
          f"utilisation {r['util']*100:.1f} %")
    mon = r["monthly"]
    print("      coverage by month: " + " ".join(
        f"{m}:{(v[1]/v[2]*100):.0f}%" for m, v in sorted(mon.items())))
    print("      server heat kWh by month: " + " ".join(
        f"{m}:{v[1]:.0f}" for m, v in sorted(mon.items())))
    print("      demand kWh by month:      " + " ".join(
        f"{m}:{v[2]:.0f}" for m, v in sorted(mon.items())))

# ---------------------------------------------------------------- 5b
section("5b. Prior-art comparisons and the utility's view (arithmetic on sourced inputs)")
total_kwh = res[6]["used"] / res[6]["coverage"]
gj = total_kwh * 3.6 / 1000
print(f"Reference house total heat demand {total_kwh:.0f} kWh = {gj:.1f} GJ per year; "
      f"one vendor's stated minimum for a site is 500 GJ per year -> the house is "
      f"{gj/500*100:.1f} % of that minimum ({500/gj:.1f} houses per minimum site)")
print(f"That vendor's 20 kW block, 24/7: 20 x 8760 = {20*8760} kWh = {20*8760*3.6/1000:.1f} GJ "
      f"(its page says 630 GJ per year)")
print(f"A UK hot-water unit: up to 4.8 kWh/day = {4.8/12*100:.0f} % of the case's 12 kWh/day hot water; "
      f"4.8 kWh/day = {4.8/24*1000:.0f} W continuous = {4.8/24/Q1:.2f} of one case server's heat")
for n in (6, 8):
    r = res[n]
    hp = r["used"] / 2.5
    print(f"N={n}: servers draw {r['run_h']*P_EL:.0f} kWh electricity per year for {r['used']:.0f} kWh heat; "
          f"a heat pump at 2.5 would draw {hp:.0f} kWh for the same heat -> ratio {r['run_h']*P_EL/hp:.3f}; "
          f"peak electrical load {n*P_EL:.0f} kW against {min(n*Q1, 10.5)/2.5:.2f} kW for the heat pump at the same heat output")

# ---------------------------------------------------------------- 6
section("6. Pitch outline timing check")
outline = (("Key figures, six in the case order", 40),
           ("The idea in two sentences + the heat receipt", 25),
           ("Live: January day", 40),
           ("Live: July day", 50),
           ("Live: the interrupted job (pause, state check, resume)", 40),
           ("Limits: where the case assumptions stop holding", 35),
           ("When it does not pay off + what a pilot must measure", 45),
           ("Close: one sentence and the two questions to the founders", 15),
           ("Reserve", 10))
t = 0
for name, sec in outline:
    print(f"{t//60}:{t%60:02d}-{(t+sec)//60}:{(t+sec)%60:02d}  {sec:>3} s  {name}")
    t += sec
live = sum(s for nme, s in outline if nme.startswith("Live"))
print(f"Total {t} s = {t//60}:{t%60:02d}; live part {live} s (plan allows about 130 s)")
assert t == 300
