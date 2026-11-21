"""Round 2: physical realism of pause and summer (exploratory, 2026-11-21).

NOT the team's scheduler. A small hourly balance on the stand-in reference
house that adds the switches docs/assumption-limits.md asks for, to see how
they move the key figures and whether they change the choice between 6 and 8
servers. It imports the data loader and the case constants from
analysis/baseline_sweep.py and checks itself against simulate() there.

    python3 analysis/r2_realism.py

Standard library only. Every input that is not a case constant is listed in
INPUTS below with its status (sourced / assumption); URLs are in
docs/research/r2-pause-physics-realism.md.

Switches
  tank_loss      kWh/day taken from the tank while it holds usable heat
  dhw            hourly shape of the 12 kWh/day hot water: flat / peaked / spike
  booster        hot water needs a top-up above the server-loop temperature:
                 none / electric / heat pump (its electricity is counted)
  idle_frac      paused servers stay powered and draw this share of 1 kW
                 (their heat is used if there is demand or tank room, else dumped)
  restart_min    paused servers are powered down; every start costs this many
                 minutes that draw power and give heat but sell no compute
  rule, band     follow (baseline) / r1band (round-1 candidate: stop when the
                 tank is full, restart after it dropped by `band`) / hold
                 (same band, but servers already running keep running and the
                 refill adds one server more than demand needs)
"""
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import load, simulate, P_EL, REC, TANK, PRICE, HEAT_VALUE  # noqa: E402

Q1 = REC * P_EL
EPS = 1e-9

# ---- inputs that are not case constants -----------------------------------
INPUTS = {
    # tank standing loss, kWh/24h (EN 12897 figures from one manufacturer's data sheet,
    # and the EU ecodesign ceiling 16.66 + 8.33 * V^0.4 W for V = 1000 l)
    "loss_classA_934l": 1.68,     # sourced (data sheet, double insulation, class A)
    "loss_classC_934l": 2.80,     # sourced (data sheet, standard insulation, class C)
    "loss_classC_887l": 3.38,     # sourced (data sheet, plain buffer, class C)
    "loss_erp_limit_1000l": (16.66 + 8.33 * 1000 ** 0.4) * 24 / 1000,  # computed from sourced formula
    "t_set_c": 60.0,              # sourced: storage outlet >= 60 C (SVGW W3/E3, warm-held pipes)
    "t_set_nocirc_c": 55.0,       # sourced: 55 C storage without warm-held pipes (SIA 385/1:2020)
    "t_cold_c": 10.0,             # assumption: cold-water inlet temperature
    "t_pre_c": 50.0,              # assumption: temperature the server loop can preheat hot water to
    "cop_booster": 3.0,           # assumption: small heat pump lifting from the tank to t_set
    "idle_cpu": 147.0 / 835.0,    # sourced: SPECpower, active idle / 100 % load, one 2-socket server
    "idle_gpu": 1.86 / 8.43,      # sourced: 8 x H100 node, idle / highest measured load
    "restart_min": (5.0, 15.0),   # assumption: power-on to job running again (POST + OS + model load)
}
LOSS = INPUTS["loss_classC_934l"]   # central tank loss used in the "realistic" columns

DHW_SHAPES = {
    # kWh per hour of day, each sums to 12. 'peaked' and 'spike' are our assumptions.
    "flat": [0.5] * 24,
    "peaked": [1.8 if h in (6, 7, 8) else 0.6 if h in (12, 13) else 1.35 if h in (18, 19, 20, 21) else 0.0
               for h in range(24)],
    "spike": [6.0 if h in (6, 19) else 0.0 for h in range(24)],
}
for _k, _v in DHW_SHAPES.items():
    assert abs(sum(_v) - 12.0) < 1e-9, _k


def booster(kind, t_pre=None, t_set=None, cop=None):
    """Return (share of hot-water energy drawn from server heat,
               booster electricity per kWh hot water,
               booster's own heat per kWh hot water = the part not from server heat)."""
    if kind == "none":
        return 1.0, 0.0, 0.0
    t_pre = INPUTS["t_pre_c"] if t_pre is None else t_pre
    t_set = INPUTS["t_set_c"] if t_set is None else t_set
    cop = INPUTS["cop_booster"] if cop is None else cop
    direct = max(0.0, min(1.0, (t_pre - INPUTS["t_cold_c"]) / (t_set - INPUTS["t_cold_c"])))
    top = 1.0 - direct
    if kind == "electric":
        return direct, top, top
    if kind == "heatpump":            # heat pump takes its source heat from the tank
        return direct + top * (1 - 1 / cop), top / cop, top / cop
    raise ValueError(kind)


def sim(rows, n, tank=TANK, tank_loss=0.0, dhw="flat", boost=("none",), idle_frac=0.0,
        rule="follow", band=0.0, summer_cap=None, restart_min=0.0):
    share, b_el, b_heat = booster(*boost)
    qi = REC * P_EL * idle_frac
    shape = DHW_SHAPES[dhw]
    soc = 0.0
    charging = True
    k_prev = 0
    ks = []
    used = dumped = lost = dem_tot = idle_h = 0.0
    boost_el = boost_heat = 0.0
    seas = {"summer": [0.0, 0.0, 0.0], "rest": [0.0, 0.0, 0.0]}   # used, demand, run_h
    for t, sh, _ in rows:
        hw = shape[int(t[11:13])]
        d = sh + hw * share
        dem_tot += sh + hw
        boost_el += hw * b_el
        boost_heat += hw * b_heat
        loss = min(soc, tank_loss / 24.0)
        soc -= loss
        lost += loss
        cap = n if (summer_cap is None or sh > 0) else min(n, summer_cap)
        room = d + tank - soc
        # largest k whose heat (plus idle heat of the paused servers) fits without dumping
        kmax = 0
        for k in range(cap, -1, -1):
            if k * Q1 + (n - k) * qi <= room + EPS:
                kmax = k
                break
        if rule == "follow":
            k = kmax
        elif rule == "r1band":                     # as analysis/demo_day_timing.py hourly()
            if not charging and (soc <= tank - band + EPS or soc < d):
                charging = True
            k = kmax if charging else 0
            if charging and kmax == 0:
                charging = False
        elif rule == "hold":
            kneed = min(kmax, max(0, math.ceil((d - soc) / Q1 - EPS)))
            if k_prev > kmax:                      # tank cannot absorb: forced shed
                charging = False
            elif soc <= tank - band + EPS:
                charging = True
            keep = min(k_prev, kmax)
            if charging:
                k = max(keep, kneed, min(kmax, math.ceil(d / Q1 - EPS) + 1))
            else:
                k = max(keep, kneed)
        else:
            raise ValueError(rule)
        heat = k * Q1 + (n - k) * qi
        avail = soc + heat
        u = min(d, avail)
        soc = avail - u
        dump = max(0.0, soc - tank)
        soc -= dump
        used += u
        dumped += dump
        idle_h += (n - k) if idle_frac else 0
        ks.append(k)
        k_prev = k
        s = seas["summer" if t[5:7] in ("06", "07", "08") else "rest"]
        s[0] += u
        s[1] += sh + hw
        s[2] += k
    run_h = float(sum(ks))
    # runs per server slot (slot i runs in an hour iff k >= i)
    runs, slot_h = [], []
    for i in range(1, n + 1):
        cur = 0
        slot_h.append(sum(1 for k in ks if k >= i))
        for k in ks:
            if k >= i:
                cur += 1
            elif cur:
                runs.append(cur)
                cur = 0
        if cur:
            runs.append(cur)
    starts = len(runs)
    sold_h = run_h - starts * restart_min / 60.0
    elec_srv = (run_h + idle_h * idle_frac) * P_EL * PRICE
    elec_boost = boost_el * PRICE
    heat_val = used * HEAT_VALUE
    return {
        "n": n, "coverage": used / dem_tot, "used": used, "dumped": dumped, "tank_lost": lost,
        "util": run_h / (n * 8760), "run_h": run_h, "sold_h": sold_h,
        "idle_kwh": idle_h * idle_frac * P_EL, "boost_el": boost_el, "boost_heat": boost_heat,
        "elec": elec_srv + elec_boost, "heat_val": heat_val,
        # case formula with the booster's electricity added to the cost and nothing credited for its heat
        "be_strict": (elec_srv + elec_boost - heat_val) / sold_h if sold_h else float("nan"),
        # same, but the heat the booster adds itself is also valued at price / 2.5
        "be": (elec_srv + elec_boost - heat_val - boost_heat * HEAT_VALUE) / sold_h if sold_h else float("nan"),
        "cov_summer": seas["summer"][0] / seas["summer"][1],
        "cov_rest": seas["rest"][0] / seas["rest"][1],
        "run_summer": seas["summer"][2],
        "starts": starts, "run_min": min(runs) if runs else 0, "run_max": max(runs) if runs else 0,
        "run_med": statistics.median(runs) if runs else 0,
        "runs_le1": sum(1 for r in runs if r <= 1), "runs_le3": sum(1 for r in runs if r <= 3),
        "slot_h": slot_h, "ks": ks,
    }


HDR = (f"{'case':<34}{'N':>2} {'cover':>7} {'summer':>7} {'dump':>6} {'tankloss':>8} {'util':>6} "
       f"{'srv-h':>7} {'boostkWh':>8} {'BE':>7} {'BEstrict':>8}")


def line(label, r):
    return (f"{label:<34}{r['n']:>2} {r['coverage']*100:>6.1f}% {r['cov_summer']*100:>6.1f}% {r['dumped']:>6.0f} "
            f"{r['tank_lost']:>8.0f} {r['util']*100:>5.1f}% {r['run_h']:>7.0f} {r['boost_el']:>8.0f} "
            f"{r['be']:>7.4f} {r['be_strict']:>8.4f}")


def delta(a, b):
    return (f"   -> coverage {(b['coverage']-a['coverage'])*100:+.1f} pts, summer {(b['cov_summer']-a['cov_summer'])*100:+.1f} pts, "
            f"dumped {b['dumped']-a['dumped']:+.0f} kWh, util {(b['util']-a['util'])*100:+.1f} pts, BE {b['be']-a['be']:+.4f} CHF/h")


def main():
    rows = load()
    NS = (6, 8)

    print("== 0. Regression check against analysis/baseline_sweep.py simulate() ==")
    for n in NS:
        for kw_base, kw_mine in (({}, {}), ({"tank_loss_kwh_day": 3.0}, {"tank_loss": 3.0})):
            a = simulate(rows, n, **kw_base)
            b = sim(rows, n, **kw_mine)
            ok = abs(a["coverage"] - b["coverage"]) < 1e-12 and a["run_h"] == b["run_h"] and abs(a["breakeven"] - b["be"]) < 1e-12
            print(f"  N={n} {kw_base or 'case'}: baseline cov {a['coverage']*100:.3f}% run_h {a['run_h']:.0f} BE {a['breakeven']:.4f} | "
                  f"this file cov {b['coverage']*100:.3f}% run_h {b['run_h']:.0f} BE {b['be']:.4f} -> {'OK' if ok else 'MISMATCH'}")
    print("  summer = June to August; BE = break-even CHF per server-hour sold (booster heat valued); "
          "BEstrict = booster electricity charged, its heat not valued")

    print("\n== inputs (status in the research file) ==")
    for k, v in INPUTS.items():
        print(f"  {k:<22} {v if isinstance(v, tuple) else round(v, 4)}")

    base = {n: sim(rows, n) for n in NS}

    print("\n== (i)+(ii) tank standing loss, follow rule ==\n" + HDR)
    for n in NS:
        print(line("case assumptions (no loss)", base[n]))
        for key in ("loss_classA_934l", "loss_classC_934l", "loss_classC_887l", "loss_erp_limit_1000l"):
            r = sim(rows, n, tank_loss=INPUTS[key])
            print(line(f"loss {INPUTS[key]:.2f} kWh/d ({key[5:]})", r))
            print(delta(base[n], r))

    print("\n== (iii) hot-water booster, no tank loss, follow rule ==\n" + HDR)
    variants = [
        ("electric, preheat 50 -> 60 C", ("electric", 50, 60)),
        ("electric, preheat 45 -> 60 C", ("electric", 45, 60)),
        ("electric, preheat 50 -> 55 C", ("electric", 50, 55)),
        ("electric, no direct hot water", ("electric", INPUTS["t_cold_c"], 60)),
        ("heat pump COP 3, 50 -> 60 C", ("heatpump", 50, 60, 3.0)),
        ("heat pump COP 3, 45 -> 60 C", ("heatpump", 45, 60, 3.0)),
        ("heat pump COP 5, 50 -> 60 C", ("heatpump", 50, 60, 5.0)),
        ("heat pump COP 2.5, all hot water", ("heatpump", INPUTS["t_cold_c"], 60, 2.5)),
    ]
    for n in NS:
        print(line("case assumptions (no booster)", base[n]))
        for label, bst in variants:
            r = sim(rows, n, boost=bst)
            print(line(label, r))
            print(delta(base[n], r))

    print("\n== (ii)+(iii) together: 'realistic' = tank loss %.2f kWh/d + booster 50 -> 60 C ==\n" % LOSS + HDR)
    real = {}
    for n in NS:
        print(line("case assumptions", base[n]))
        for label, bst in (("loss + electric booster", ("electric", 50, 60)), ("loss + heat-pump booster COP 3", ("heatpump", 50, 60, 3.0))):
            r = sim(rows, n, tank_loss=LOSS, boost=bst)
            real[(n, bst[0])] = r
            print(line(label, r))
            print(delta(base[n], r))
    print("  sensitivity of the electric-booster pair to the tank loss (N=6 / N=8: summer drop pts, BE rise CHF/h):")
    for key in ("loss_classA_934l", "loss_classC_934l", "loss_classC_887l", "loss_erp_limit_1000l"):
        out = []
        for n in NS:
            r = sim(rows, n, tank_loss=INPUTS[key], boost=("electric", 50, 60))
            out.append(f"N={n}: {(base[n]['cov_summer']-r['cov_summer'])*100:.1f} pts, +{r['be']-base[n]['be']:.4f}")
        print(f"    loss {INPUTS[key]:.2f}: " + " | ".join(out))

    print("\n== (iv) paused servers: powered and idle, or powered down with a restart penalty ==")
    print("  a) paused-but-on all year (SIGSTOP on a real unit). idle heat is used when demand or tank can take it, else dumped")
    print(f"  {'case':<26}{'N':>2} {'cover':>7} {'summer':>7} {'dump':>7} {'util':>6} {'srv-h':>7} {'summer srv-h':>12} {'idle kWh':>9} {'elec CHF':>9} {'BE':>7}")
    for n in NS:
        b = base[n]
        print(f"  {'powered down (case)':<26}{n:>2} {b['coverage']*100:>6.1f}% {b['cov_summer']*100:>6.1f}% {b['dumped']:>7.0f} {b['util']*100:>5.1f}% {b['run_h']:>7.0f} {b['run_summer']:>12.0f} {0:>9.0f} {b['elec']:>9.0f} {b['be']:>7.4f}")
        for label, f in (("idle 17.6 % (CPU server)", INPUTS["idle_cpu"]), ("idle 22.1 % (GPU node)", INPUTS["idle_gpu"]), ("idle 5 %", 0.05)):
            r = sim(rows, n, idle_frac=f)
            print(f"  {label:<26}{n:>2} {r['coverage']*100:>6.1f}% {r['cov_summer']*100:>6.1f}% {r['dumped']:>7.0f} {r['util']*100:>5.1f}% {r['run_h']:>7.0f} {r['run_summer']:>12.0f} {r['idle_kwh']:>9.0f} {r['elec']:>9.0f} {r['be']:>7.4f}")
        f = INPUTS["idle_cpu"]
        print(f"     idle heat of {n} paused servers at 17.6 %: {n*f*REC*24:.1f} kWh/day against 12 kWh/day summer hot water")
    print("  b) powered down; each start costs restart_min of unsold run time (heat still delivered). follow rule, no band")
    for n in NS:
        b = base[n]
        for rm in (0.0,) + INPUTS["restart_min"]:
            r = sim(rows, n, restart_min=rm)
            print(f"     N={n} restart {rm:>4.0f} min: starts {r['starts']:>5}, unsold {r['run_h']-r['sold_h']:>6.0f} h "
                  f"({(r['run_h']-r['sold_h'])/r['run_h']*100:.2f} % of run hours), BE {r['be']:.4f} ({r['be']-b['be']:+.4f})")

    print("\n== (v) hysteresis band sweep (case assumptions, flat hot water) ==")
    hdr = (f"  {'rule':<16}{'band':>5} {'cover':>8} {'srv-h':>7} {'starts':>6} {'run min':>7} {'median':>6} {'max':>6} {'<=1h':>5} {'<=3h':>5} "
           f"{'BE@5min':>8} {'BE@15min':>8} {'summer starts':>13}")
    bands = (0, 1, 2, 4, 8, 12, 16, 24, 32)
    best = {}
    for n in NS:
        print(f"  N={n}\n" + hdr)
        for rule, cap, lab in (("follow", None, "follow"), ("r1band", None, "r1band"), ("r1band", 1, "r1band+cap1"), ("hold", None, "hold"), ("hold", 1, "hold+cap1")):
            for bd in ((0,) if rule == "follow" else bands[1:]):
                r = sim(rows, n, rule=rule, band=bd, summer_cap=cap)
                r5 = sim(rows, n, rule=rule, band=bd, summer_cap=cap, restart_min=5)
                r15 = sim(rows, n, rule=rule, band=bd, summer_cap=cap, restart_min=15)
                ks = r["ks"]
                su = sum(1 for i, (t, _, _) in enumerate(rows) if t[5:7] in ("06", "07", "08") and ks[i] > (ks[i-1] if i else 0))
                print(f"  {lab:<16}{bd:>5} {r['coverage']*100:>7.2f}% {r['run_h']:>7.0f} {r['starts']:>6} {r['run_min']:>7} {r['run_med']:>6.0f} {r['run_max']:>6} "
                      f"{r['runs_le1']:>5} {r['runs_le3']:>5} {r5['be']:>8.4f} {r15['be']:>8.4f} {su:>13}")
                best[(n, lab, bd)] = r

    print("\n  band sweep again with tank loss %.2f kWh/d and peaked hot water (does the recommendation survive?)" % LOSS)
    for n in NS:
        print(f"  N={n}\n" + hdr)
        for rule, cap, lab in (("follow", None, "follow"), ("r1band", 1, "r1band+cap1"), ("hold", 1, "hold+cap1")):
            for bd in ((0,) if rule == "follow" else (2, 4, 8, 12, 16, 24)):
                kw = dict(rule=rule, band=bd, summer_cap=cap, tank_loss=LOSS, dhw="peaked")
                r = sim(rows, n, **kw)
                r5 = sim(rows, n, restart_min=5, **kw)
                r15 = sim(rows, n, restart_min=15, **kw)
                ks = r["ks"]
                su = sum(1 for i, (t, _, _) in enumerate(rows) if t[5:7] in ("06", "07", "08") and ks[i] > (ks[i-1] if i else 0))
                print(f"  {lab:<16}{bd:>5} {r['coverage']*100:>7.2f}% {r['run_h']:>7.0f} {r['starts']:>6} {r['run_min']:>7} {r['run_med']:>6.0f} {r['run_max']:>6} "
                      f"{r['runs_le1']:>5} {r['runs_le3']:>5} {r5['be']:>8.4f} {r15['be']:>8.4f} {su:>13}")

    print("\n  starts per server slot and pause lengths (slot 1 = last server to stop), powered down, case assumptions")
    for n in NS:
        for lab, kw in (("follow", {}), ("r1band+cap1 band 8", dict(rule="r1band", band=8, summer_cap=1)),
                        ("hold+cap1 band 8", dict(rule="hold", band=8, summer_cap=1))):
            ks = sim(rows, n, **kw)["ks"]
            per_slot, gaps = [], []
            for i in range(1, n + 1):
                on = [k >= i for k in ks]
                per_slot.append(sum(1 for j in range(len(on)) if on[j] and (j == 0 or not on[j - 1])))
                cur, seen_run = 0, False
                for x in on:
                    if x:
                        if cur and seen_run:
                            gaps.append(cur)
                        cur, seen_run = 0, True
                    else:
                        cur += 1
            print(f"     N={n} {lab:<20} starts per slot {per_slot}  max {max(per_slot)}/yr; pauses {len(gaps)}, "
                  f"of 1 h: {sum(1 for g in gaps if g == 1)}, of <=3 h: {sum(1 for g in gaps if g <= 3)}, "
                  f"median {statistics.median(gaps):.0f} h, longest {max(gaps)} h")

    print("\n  idle or power down? pause length above which powering down is cheaper (electricity only, no lost sales)")
    net = PRICE - REC * HEAT_VALUE          # CHF per kWh electricity when the heat is used
    for f_lab, f in (("17.6 %", INPUTS["idle_cpu"]), ("22.1 %", INPUTS["idle_gpu"])):
        for rm in INPUTS["restart_min"]:
            boot = rm / 60.0 * P_EL * net   # an unsold start whose heat is still used
            print(f"     idle {f_lab}, restart {rm:.0f} min: start costs {boot:.4f} CHF; idle hour costs "
                  f"{f*P_EL*net:.4f} CHF if its heat is used, {f*P_EL*PRICE:.4f} CHF if dumped -> "
                  f"power down for pauses longer than {boot/(f*P_EL*net):.1f} h (heat used) / {boot/(f*P_EL*PRICE):.1f} h (heat dumped)")

    print("\n== (vi) hot-water shape: flat vs peaked vs two spikes of 6 kWh ==\n" + HDR)
    for n in NS:
        for shape in ("flat", "peaked", "spike"):
            r = sim(rows, n, dhw=shape)
            print(line(f"case, hot water {shape}", r))
            if shape != "flat":
                print(delta(base[n], r))
        for shape in ("flat", "peaked", "spike"):
            r = sim(rows, n, dhw=shape, tank_loss=LOSS, boost=("electric", 50, 60))
            print(line(f"loss+el. booster, {shape}", r))
        for tk in (10.0, 5.0):
            a = sim(rows, n, tank=tk)
            b = sim(rows, n, tank=tk, dhw="peaked")
            print(f"   tank {tk:g} kWh instead of 35: flat {a['coverage']*100:.2f}% -> peaked {b['coverage']*100:.2f}%")

    print("\n== 6 versus 8: case assumptions against the combined realistic run ==")
    print("  realistic = tank loss %.2f kWh/d, hot water peaked, booster 50 -> 60 C, powered down when paused," % LOSS)
    print("  rule hold+cap1 with the recommended band, restart 15 min unsold per start")
    BAND = 8
    print(f"  {'':<34}{'N':>2} {'cover':>7} {'summer':>7} {'dump':>5} {'util':>6} {'srv-h sold':>10} {'starts':>6} {'elec CHF':>9} {'BE':>7}   run h/yr of servers 6, 7, 8")
    for n in NS:
        b = base[n]
        sl = b["slot_h"]
        print(f"  {'case assumptions':<34}{n:>2} {b['coverage']*100:>6.1f}% {b['cov_summer']*100:>6.1f}% {b['dumped']:>5.0f} {b['util']*100:>5.1f}% {b['sold_h']:>10.0f} {b['starts']:>6} {b['elec']:>9.0f} {b['be']:>7.4f}   "
              + ", ".join(str(x) for x in sl[5:]))
        for lab, bst in (("realistic, electric booster", ("electric", 50, 60)), ("realistic, heat-pump booster COP 3", ("heatpump", 50, 60, 3.0))):
            r = sim(rows, n, tank_loss=LOSS, dhw="peaked", boost=bst, rule="hold", band=BAND, summer_cap=1, restart_min=15)
            sl = r["slot_h"]
            print(f"  {lab:<34}{n:>2} {r['coverage']*100:>6.1f}% {r['cov_summer']*100:>6.1f}% {r['dumped']:>5.0f} {r['util']*100:>5.1f}% {r['sold_h']:>10.0f} {r['starts']:>6} {r['elec']:>9.0f} {r['be']:>7.4f}   "
                  + ", ".join(str(x) for x in sl[5:]))
            real[(n, "combined", bst[0])] = r
    for lab in ("electric", "heatpump"):
        a6, a8 = base[6], base[8]
        r6, r8 = real[(6, "combined", lab)], real[(8, "combined", lab)]
        print(f"  gap 8 minus 6, {lab}: coverage case {(a8['coverage']-a6['coverage'])*100:+.1f} pts -> realistic {(r8['coverage']-r6['coverage'])*100:+.1f} pts; "
              f"utilisation case {(a8['util']-a6['util'])*100:+.1f} -> {(r8['util']-r6['util'])*100:+.1f} pts; "
              f"BE case {a8['be']-a6['be']:+.4f} -> {r8['be']-r6['be']:+.4f} CHF/h")

    print("\n== pitch sentence (tank loss %.2f kWh/d sourced; preheat 50 C, cold water 10 C, COP 3 are assumptions; 60 C sourced) ==" % LOSS)
    for n in NS:
        for lab, word in (("electric", "an electric hot-water booster"), ("heatpump", "a small heat-pump booster (COP 3)")):
            r = real[(n, lab)]
            b = base[n]
            print(f"  N={n}: With tank losses and {word}, summer coverage drops by {(b['cov_summer']-r['cov_summer'])*100:.1f} points "
                  f"(from {b['cov_summer']*100:.0f}% to {r['cov_summer']*100:.1f}%, June to August; year: {b['coverage']*100:.1f}% to {r['coverage']*100:.1f}%) "
                  f"and the break-even price rises by {r['be']-b['be']:.4f} CHF per server-hour (from {b['be']:.4f} to {r['be']:.4f}; "
                  f"{r['be_strict']:.4f} if the booster's own heat is not valued).")


if __name__ == "__main__":
    main()
