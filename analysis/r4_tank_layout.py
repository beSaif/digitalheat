"""Round 4: tank temperatures, summer hot water and winter supply temperature (exploratory, 2026-11-21).

NOT the team's scheduler. A small hourly balance on the stand-in reference house that replaces the
case's "35 kWh usable, all heat usable at any temperature" with ONE stated temperature layout, as a
realism column next to the case-assumption column. Imports the loader, the case constants and
simulate() from analysis/baseline_sweep.py and checks itself against it.

    python3 analysis/r4_tank_layout.py

Standard library only. Sources and status of every input: docs/research/r4-tank-temperatures.md.

Layout A (the one we state)
  server rack, direct liquid cooling: coolant 45 C in -> ~55 C out (vendor blog)
  -> CDU plate heat exchanger, 5 K approach (vendor tier table)  => house side T_TOP = 50 C
  -> 1,000 l stratified BUFFER of heating water (not drinking water; Swiss guidance for waste heat < 50 C)
       space heating: drawn through a mixing valve at the supply temperature of the heating curve;
                      if the curve needs more than T_TOP, the buffer preheats the return water and the
                      house's backup heater lifts the rest (serial / return-boost connection)
       hot water:     fresh-water station from the buffer top, 3 K approach (2-5 K, suissetec) preheats
                      cold water to T_TOP - 3 = 47 C; a small 55 C drinking-water cylinder with an
                      electric element tops up (55 C: storage without warm-held pipes, SIA 385/1)
  Usable buffer energy depends on what the bottom of the tank returns at:
       space heating can draw it down only to the heating return temperature of that hour,
       hot water (fresh-water station returns near cold-water temperature) down to T_FLOOR_DHW = 20 C.

Model (stratified ideal tank, energy above 20 C):
  soc in [0, C*(T_TOP-20)]; space heating may draw from the tank only while soc > C*(T_ret(t)-20);
  live server heat serves demand first, the rest charges the tank; follow rule: largest whole k <= N
  whose surplus fits in the tank (never dumps), as in baseline_sweep 'follow'.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import ROOT, load, simulate, P_EL, REC, TANK, PRICE, HEAT_VALUE  # noqa: E402

Q1 = REC * P_EL
EPS = 1e-9
C_KWH_PER_K = 1000 * 1.163 / 1000      # 1,000 l x 1.163 Wh/(l K) = 1.163 kWh/K

INPUTS = {
    "srv_out_c": 55.0,        # sourced (vendor blog): coolant 45 C in exits at "roughly 55 C"
    "cdu_approach_k": 5.0,    # computed from sourced tier table: TCS 45-50 C vs facility water 40-45 C
    "fws_approach_k": 3.0,    # assumption inside the sourced 2-5 K (fresh-water station primary above DHW)
    "t_cold_c": 10.0,         # assumption (as round 2)
    "t_dhw_set_c": 55.0,      # sourced: storage 55 C without warm-held pipes (SIA 385/1:2020 via BAG/BLV)
    "t_dhw_set_circ_c": 60.0, # sourced: >= 60 C with warm-held pipes (SVGW W3/E3 via BAG/BLV)
    "t_floor_dhw_c": 20.0,    # assumption: tank bottom with only the fresh-water station drawing
    "t_room_c": 20.0,         # case: demand formula uses 20 C
    "loss_kwh_day": 2.80,     # sourced in round 2 (one manufacturer, 934 l, class C)
}
T_TOP = INPUTS["srv_out_c"] - INPUTS["cdu_approach_k"]           # 50 C

# heating systems: design supply / return at the case's design hour (10 kW at -5.6 C), EN 442 exponent n
SYSTEMS = {
    "underfloor 35/28": (35.0, 28.0, 1.1),   # 35 C = MuKEn max for floor heating; 28 C return (suissetec); n=1.1 assumption
    "radiator 55/45":   (55.0, 45.0, 1.3),   # condensing-boiler design pair (SBZ/EN 442); n=1.3 (SBZ example)
    "radiator 50/40":   (50.0, 40.0, 1.3),   # MuKEn max 50 C for new/replaced radiators; 40 C return assumption
    "radiator 70/55":   (70.0, 55.0, 1.3),   # older house, low-temperature boiler pair (SBZ)
}


def curve(phi, sysdef):
    """Supply and return temperature at load fraction phi (0..1), constant flow, arithmetic-mean form
    of the EN 442 characteristic: mean excess ~ phi^(1/n), spread ~ phi."""
    ts, tr, n = sysdef
    tr_room = INPUTS["t_room_c"]
    if phi <= 0:
        return tr_room, tr_room
    dmean = ((ts + tr) / 2 - tr_room) * phi ** (1 / n)
    spread = (ts - tr) * phi
    return tr_room + dmean + spread / 2, tr_room + dmean - spread / 2


def sh_share(t_sup, t_ret, t_top):
    """Share of the hour's space heat the buffer at t_top can deliver (serial preheat of the return)."""
    if t_sup <= t_top + EPS:
        return 1.0
    return max(0.0, min(1.0, (t_top - t_ret) / (t_sup - t_ret)))


def dhw_share(t_top, t_set):
    t_pre = t_top - INPUTS["fws_approach_k"]
    return max(0.0, min(1.0, (t_pre - INPUTS["t_cold_c"]) / (t_set - INPUTS["t_cold_c"])))


def load_temps():
    with open(ROOT / "data" / "reference_house_2025_hourly.csv") as f:
        return [float(r["temperature_2m_c"]) for r in csv.DictReader(f)]


def sim(rows, n, sysdef=None, t_top=T_TOP, t_set=None, tank_loss=0.0, case_mode=False,
        tank_cap=None, floor_mode="return"):
    """case_mode=True: every share 1, floor 0, cap = TANK -> must equal baseline_sweep.simulate()."""
    t_set = INPUTS["t_dhw_set_c"] if t_set is None else t_set
    floor_ref = INPUTS["t_floor_dhw_c"]
    cap = TANK if case_mode else C_KWH_PER_K * (t_top - floor_ref)
    if tank_cap is not None:
        cap = tank_cap
    s_dhw = 1.0 if case_mode else dhw_share(t_top, t_set)
    soc = 0.0
    used = dumped = run_h = dem = lost = 0.0
    boost_el = 0.0                       # electric top-up for hot water (kWh el = kWh heat)
    sh_backup = 0.0                      # space heat the backup heater must add (temperature-limited part)
    seas = {}                            # 'summer' Jun-Aug, 'winter' Dec-Feb
    usable_at_hours = []
    for t, sh, hw in rows:
        dem += sh + hw
        loss = min(soc, tank_loss / 24.0)
        soc -= loss
        lost += loss
        if case_mode:
            s_sh, floor_e = 1.0, 0.0
        else:
            phi = sh / 10.0
            t_sup, t_ret = curve(phi, sysdef)
            s_sh = sh_share(t_sup, t_ret, t_top) if sh > 0 else 1.0
            # stratified ideal: tank drawn down to the return temperature; 'supply' = crude no-stratification
            # case: the tank must stay above the supply temperature (or the return, if it only preheats)
            t_fl = t_ret if (floor_mode == "return" or s_sh < 1.0) else t_sup
            floor_e = C_KWH_PER_K * max(0.0, t_fl - floor_ref) if sh > 0 else 0.0
            if sh > 0:
                usable_at_hours.append(max(0.0, cap - floor_e))
        d_sh, d_hw = sh * s_sh, hw * s_dhw
        sh_backup += sh - d_sh
        boost_el += hw - d_hw

        def step(k, soc0):
            heat = k * Q1
            a = min(d_sh, heat); heat -= a
            b = min(d_hw, heat); heat -= b
            s = soc0
            c = min(d_sh - a, max(0.0, s - floor_e)); s -= c
            e = min(d_hw - b, s); s -= e
            s += heat
            return a + b + c + e, s

        k = 0
        for kk in range(n, -1, -1):
            u, s_after = step(kk, soc)
            if s_after <= cap + EPS:
                k = kk
                break
        u, soc = step(k, soc)
        dump = max(0.0, soc - cap)       # 0 under follow; kept for safety
        soc -= dump
        used += u
        dumped += dump
        run_h += k
        key = "summer" if t[5:7] in ("06", "07", "08") else "winter" if t[5:7] in ("12", "01", "02") else "rest"
        sv = seas.setdefault(key, [0.0, 0.0])
        sv[0] += u
        sv[1] += sh + hw
    elec_srv = run_h * P_EL * PRICE
    heat_val = used * HEAT_VALUE
    be_case = (elec_srv - heat_val) / run_h if run_h else float("nan")
    # round-2 convention: hot-water top-up electricity charged to the servers, its heat credited at price/2.5
    be_charged = (elec_srv + boost_el * PRICE - heat_val - boost_el * HEAT_VALUE) / run_h if run_h else float("nan")
    return {
        "n": n, "coverage": used / dem, "used": used, "dumped": dumped, "lost": lost,
        "util": run_h / (n * 8760), "run_h": run_h, "be_case": be_case, "be_charged": be_charged,
        "boost_el": boost_el, "sh_backup": sh_backup, "cap": cap, "s_dhw": s_dhw,
        "summer": seas["summer"][0] / seas["summer"][1], "winter": seas["winter"][0] / seas["winter"][1],
        "usable_mean_heating_h": (sum(usable_at_hours) / len(usable_at_hours)) if usable_at_hours else cap,
    }


HDR = (f"{'variant':<44}{'N':>2} {'cover':>7} {'Dec-Feb':>7} {'Jun-Aug':>7} {'dump':>5} {'util':>6} "
       f"{'srv-h':>7} {'BEcase':>7} {'BEchg':>7}")


def line(label, r):
    return (f"{label:<44}{r['n']:>2} {r['coverage']*100:>6.1f}% {r['winter']*100:>6.1f}% {r['summer']*100:>6.1f}% "
            f"{r['dumped']:>5.0f} {r['util']*100:>5.1f}% {r['run_h']:>7.0f} {r['be_case']:>7.4f} {r['be_charged']:>7.4f}")


def main():
    rows = load()
    temps = load_temps()
    NS = (6, 8)

    print("== 0. Regression check: case_mode against baseline_sweep.simulate() ==")
    for n in NS:
        a = simulate(rows, n)
        b = sim(rows, n, case_mode=True)
        ok = abs(a["coverage"] - b["coverage"]) < 1e-12 and a["run_h"] == b["run_h"] and abs(a["breakeven"] - b["be_case"]) < 1e-12
        print(f"  N={n}: baseline cov {a['coverage']*100:.3f}% run_h {a['run_h']:.0f} BE {a['breakeven']:.4f} | "
              f"this file {b['coverage']*100:.3f}% {b['run_h']:.0f} {b['be_case']:.4f} -> {'OK' if ok else 'MISMATCH'}")

    print("\n== 1. Inputs ==")
    for k, v in INPUTS.items():
        print(f"  {k:<18} {v}")
    print(f"  T_TOP (house side) = {INPUTS['srv_out_c']} - {INPUTS['cdu_approach_k']} = {T_TOP} C")
    print(f"  tank heat capacity  = 1000 l x 1.163 Wh/(l K) = {C_KWH_PER_K:.3f} kWh/K")

    print("\n== 2. Usable tank energy for 1,000 l (kWh = 1.163 x spread) ==")
    pairs = [("case: 30 K spread (e.g. 60 -> 30 C)", 30.0),
             (f"layout A, hot water only: {T_TOP:.0f} -> {INPUTS['t_floor_dhw_c']:.0f} C", T_TOP - INPUTS["t_floor_dhw_c"])]
    for name, sysdef in SYSTEMS.items():
        _, tr_d = curve(1.0, sysdef)
        pairs.append((f"layout A, {name}, design hour: {T_TOP:.0f} -> {tr_d:.0f} C", max(0.0, T_TOP - tr_d)))
    pairs += [("single combi tank, 60 C top kept for hot water, 50 C loop charges only below", 0.0),
              ("  ... loop zone 50 -> 20 C under a 60 C hot-water zone of 200 l (assumption)", 30.0 * 0.8)]
    for name, spread in pairs:
        print(f"  {name:<78} spread {spread:5.1f} K -> {C_KWH_PER_K*spread:5.1f} kWh")

    print("\n== 3. Heating curve and share of space heat the 50 C buffer serves, by outdoor temperature ==")
    print(f"  {'T out':>6} {'hours':>6} " + " ".join(f"{k:>24}" for k in SYSTEMS))
    print(f"  {'':>6} {'':>6} " + " ".join(f"{'sup/ret  share':>24}" for _ in SYSTEMS))
    bins = [(-6, -2), (-2, 2), (2, 6), (6, 10), (10, 14), (14, 21)]
    for lo, hi in bins:
        hrs = [(r, T) for r, T in zip(rows, temps) if lo <= T < hi and r[1] > 0]
        if not hrs:
            continue
        Tm = (lo + hi) / 2
        phi = max(0.0, min(1.0, (20 - Tm) / 25.6))
        cells = []
        for sysdef in SYSTEMS.values():
            ts, tr = curve(phi, sysdef)
            cells.append(f"{ts:5.1f}/{tr:4.1f}  {sh_share(ts, tr, T_TOP)*100:5.1f}%")
        print(f"  {lo:>3}..{hi:<2} {len(hrs):>6} " + " ".join(f"{c:>24}" for c in cells))
    print("  (T out bin mid-point; heating-day hours only; supply/return from the case load fraction (20-T)/25.6)")

    print("\n== 4. Year totals: space heat the buffer can serve by temperature (energy-weighted) ==")
    sh_tot = sum(r[1] for r in rows)
    for name, sysdef in SYSTEMS.items():
        ok = 0.0
        hrs_lim = 0
        for _, sh, _ in rows:
            if sh <= 0:
                continue
            ts, tr = curve(sh / 10.0, sysdef)
            s = sh_share(ts, tr, T_TOP)
            ok += sh * s
            hrs_lim += s < 1.0
        print(f"  {name:<18} {ok/sh_tot*100:5.1f}% of {sh_tot:,.0f} kWh space heat; hours with supply > {T_TOP:.0f} C: {hrs_lim}")
    for tset in (52.0, INPUTS["t_dhw_set_c"], INPUTS["t_dhw_set_circ_c"]):   # 52 C: fresh-water station outlet without warm-held pipes
        print(f"  hot water, preheat {T_TOP - INPUTS['fws_approach_k']:.0f} C, setpoint {tset:.0f} C: direct share {dhw_share(T_TOP, tset)*100:.1f}% "
              f"(top-up {4380*(1-dhw_share(T_TOP, tset)):,.0f} kWh/yr electric)")

    print("\n== 5. Key figures: case column vs layout A realism column (follow rule, no dumping) ==")
    print("  BEcase = case formula, top-ups by the backup heater outside the model (case convention);")
    print("  BEchg  = hot-water top-up electricity charged to the servers, its heat credited at price/2.5 (round-2 convention)")
    print(HDR)
    out = {}
    for n in NS:
        print(line("case assumptions (35 kWh, all heat usable)", sim(rows, n, case_mode=True)))
        for name, sysdef in SYSTEMS.items():
            r = sim(rows, n, sysdef)
            out[(n, name, 0)] = r
            print(line(f"A, {name}", r))
        for name in ("underfloor 35/28", "radiator 55/45"):
            r = sim(rows, n, SYSTEMS[name], tank_loss=INPUTS["loss_kwh_day"])
            out[(n, name, 1)] = r
            print(line(f"A, {name} + loss 2.80/d", r))
        print()

    print("== 6. Sensitivity (N=6 and 8): loop temperature on the house side and hot-water setpoint ==")
    print(HDR)
    for n in NS:
        for name in ("underfloor 35/28", "radiator 55/45"):
            for tt in (45.0, 50.0, 55.0):
                r = sim(rows, n, SYSTEMS[name], t_top=tt)
                print(line(f"{name}, T_top {tt:.0f} C, set 55", r))
            r = sim(rows, n, SYSTEMS[name], t_set=60.0)
            print(line(f"{name}, T_top 50 C, set 60 (warm-held)", r))
        print()

    print("== 6b. Sensitivity: no stratification (space heating needs the tank above the supply temperature) ==")
    print(HDR)
    for n in NS:
        for name in ("underfloor 35/28", "radiator 55/45"):
            print(line(f"{name}, mixed-tank floor", sim(rows, n, SYSTEMS[name], floor_mode="supply")))
        for tk in (10.0, 5.0):
            print(line(f"underfloor 35/28, usable cap {tk:.0f} kWh", sim(rows, n, SYSTEMS["underfloor 35/28"], tank_cap=tk)))
    print()

    print("== 7. Usable tank energy actually available (mean over heating hours) and stranded share ==")
    for n in NS:
        for name in SYSTEMS:
            r = out[(n, name, 0)]
            print(f"  N={n} {name:<18} cap {r['cap']:.1f} kWh, usable above heating return (mean of heating hours) "
                  f"{r['usable_mean_heating_h']:.1f} kWh; backup adds {r['sh_backup']:,.0f} kWh space heat; "
                  f"hot-water top-up {r['boost_el']:,.0f} kWh el")

    print("\n== 8. Pitch figures (N=6 / N=8) ==")
    for name in ("underfloor 35/28", "radiator 55/45"):
        a6, a8 = sim(rows, 6, case_mode=True), sim(rows, 8, case_mode=True)
        r6, r8 = out[(6, name, 1)], out[(8, name, 1)]
        print(f"  {name} + loss: coverage {a6['coverage']*100:.1f}% -> {r6['coverage']*100:.1f}% (N=6), "
              f"{a8['coverage']*100:.1f}% -> {r8['coverage']*100:.1f}% (N=8); Jun-Aug 100% -> {r6['summer']*100:.1f}%; "
              f"Dec-Feb {a6['winter']*100:.1f}% -> {r6['winter']*100:.1f}% (N=6), {a8['winter']*100:.1f}% -> {r8['winter']*100:.1f}% (N=8); "
              f"util {a6['util']*100:.1f}% -> {r6['util']*100:.1f}% / {a8['util']*100:.1f}% -> {r8['util']*100:.1f}%; "
              f"BE case conv. {r6['be_case']:.4f} / {r8['be_case']:.4f}, charged {r6['be_charged']:.4f} / {r8['be_charged']:.4f}")


if __name__ == "__main__":
    main()
