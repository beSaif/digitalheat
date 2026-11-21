"""Round 5: one consistent machine + cooling + temperature chain (exploratory, 2026-11-21).

NOT the team's scheduler. Compares cooling chains for the reference server (2U, 4 x RTX PRO 4500 Blackwell
class) on the stand-in reference house, recomputes the realism column (coverage, dumped, utilisation,
break-even) and the installed cost / share-of-list-price-needed lines for N=6 and N=8.

    python3 analysis/r5_chain.py

Standard library only. Imports (never edits) analysis/baseline_sweep.py, analysis/r4_tank_layout.py and
analysis/r4_machine.py. Sources and status of every input: docs/research/r5-machine-temperature-chain.md.

Chains (all keep the case's 1 kW server and 80 % recovery, follow rule, never dump):
  A0   layout A as in the plan (DLC ~55 C out, 5 K CDU -> 50 C house side), NO return limit  [regression]
  DLC  same box retrofitted with GPU + CPU cold plates; coolant into the box <= 45 C, so the house water
       returning to the CDU must be <= 40 C; servers stop in hours when the heating return is warmer
       (pessimistic bound, as the round-4 critic). Hot water: fresh-water station to 47 C + electric top-up
       to 55 C.  -> the RECOMMENDED chain
  DLC50 sensitivity: coolant into the box <= 50 C (return <= 45 C, house side still 50 C because blocks
       are rated 60 C max: outlet 55-60 C)
  AIR  box stays air-cooled in a closed enclosure with an air-to-water coil; server inlet air <= 30 C,
       exhaust ~45 C (15 K rise, assumption), 5 K coil approach -> water 40 C top, return <= 25 C.
       Hot water: preheat 37 C + electric top-up.
  AIR35 sensitivity: inlet air <= 35 C (ASHRAE A2 upper limit, assumption), water 45 C top, return <= 30 C
  AIR+HPB air-cooled; space heat from coil water as AIR; ALL hot water from a heat-pump water heater that
       draws the server room air (COP 3.63 at A20, sourced lower bound; air limit 35 C, sourced)
  AIR+HP  air-cooled; a water-to-water heat pump lifts coil water to 55 C for space heat AND hot water;
       COP 3.6 (WPZ W10/W55, sourced lower bound) and a Carnot-scaled 5.2 (computed, unverified)

Conventions (as the plan / r4_tank_layout):
  coverage_srv = server heat used / total demand (case definition, "share covered by server heat")
  coverage_chain = (server heat + heat-pump compressor heat delivered) / total demand
  BEcase = (server electricity + heat-pump electricity - value of heat the chain delivered) / server-hours;
           electric top-ups (hot-water element, space-heat backup) are the backup heater outside the model
  BEchg  = BEcase with the hot-water element's electricity charged to the servers and its heat credited
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_sweep as bs          # noqa: E402
import r4_tank_layout as tl          # noqa: E402
import r4_machine as mc              # noqa: E402

PRICE, HEAT_VALUE, Q1 = bs.PRICE, bs.HEAT_VALUE, bs.REC * bs.P_EL
C = tl.C_KWH_PER_K                   # 1.163 kWh/K for 1,000 l
EPS = 1e-9
LOSS = 2.80                          # kWh/day, sourced in round 2 (realism column)
T_COLD, T_DHW, FWS_K = 10.0, 55.0, 3.0
HOUSES = ["underfloor 35/28", "radiator 50/40", "radiator 55/45", "radiator 70/55"]

# ---------------------------------------------------------------- heat-pump COPs
COP_HPB = 3.63       # SOURCED: Buderus BW 270 P.2, EN 16147 A20/W10-53 (air range -10..35 C, max 62 C w/o element)
COP_WW_LOW = 3.6     # SOURCED: WPZ test results 28.03.2025, water/water, Dolder WP-ZR28-1 (8.5 kW), W10/W55


def carnot_scaled(cop_ref, src_out_ref, sink_ref, src_out, sink):
    """Keep the measured Carnot (second-law) efficiency, change the lift. Temperatures in C."""
    eta = cop_ref / ((sink_ref + 273.15) / (sink_ref - src_out_ref))
    return eta * (sink + 273.15) / (sink - src_out), eta


COP_WW_HIGH, ETA_WW = carnot_scaled(COP_WW_LOW, 7.0, 55.0, 22.0, 55.0)  # source 25 C in / 22 C out (coil loop)

CHAINS = {
    #          t_top  ret_max  sh_mode   dhw_mode   cop_sh        cop_dhw   pump kW per running server
    "A0":      (50.0, None,  "direct", "element", None,         None,     0.0),
    "DLC":     (50.0, 40.0,  "direct", "element", None,         None,     0.02),
    "DLC50":   (50.0, 45.0,  "direct", "element", None,         None,     0.02),
    "AIR":     (40.0, 25.0,  "direct", "element", None,         None,     0.0),
    "AIR35":   (45.0, 30.0,  "direct", "element", None,         None,     0.0),
    "AIR+HPB": (40.0, 25.0,  "direct", "hp",      None,         COP_HPB,  0.0),
    "AIR+HP":  (40.0, None,  "hp",     "hp",      COP_WW_LOW,   COP_WW_LOW, 0.0),
    "AIR+HP5": (40.0, None,  "hp",     "hp",      COP_WW_HIGH,  COP_WW_HIGH, 0.0),
}
LABEL = {
    "A0": "layout A, no return limit (plan, regression)",
    "DLC": "cold-plate retrofit, inlet <=45 C, return <=40 C",
    "DLC50": "cold-plate retrofit, inlet <=50 C, return <=45 C",
    "AIR": "air-cooled + coil, 40 C top, return <=25 C",
    "AIR35": "air-cooled + coil, 45 C top, return <=30 C",
    "AIR+HPB": "AIR + heat-pump water heater for all DHW",
    "AIR+HP": "air + water/water HP to 55 C, COP 3.6",
    "AIR+HP5": "air + water/water HP to 55 C, COP %.1f" % COP_WW_HIGH,
}


def dhw_direct_share(t_top):
    return max(0.0, min(1.0, (t_top - FWS_K - T_COLD) / (T_DHW - T_COLD)))


def sim(rows, n, chain, house, tank_loss=0.0, t_hp_out=55.0):
    t_top, ret_max, sh_mode, dhw_mode, cop_sh, cop_dhw, pump_kw = CHAINS[chain]
    sysdef = tl.SYSTEMS[house]
    cap = C * (t_top - 20.0)
    s_dhw = dhw_direct_share(t_top)
    soc = 0.0
    q_srv = q_hp_el = el_elem = run_h = dem = 0.0
    blocked_h = 0
    seas = {}
    for t, sh, hw in rows:
        dem += sh + hw
        soc -= min(soc, tank_loss / 24.0)
        nmax = n
        portions = []                      # (server heat needed, tank floor energy, cop or None)
        if sh > 0:
            ts, tr = tl.curve(sh / 10.0, sysdef)
            if sh_mode == "direct":
                share = tl.sh_share(ts, tr, t_top)
                portions.append((sh * share, C * max(0.0, tr - 20.0), None))
                if ret_max is not None and tr > ret_max + EPS:
                    nmax = 0
                    blocked_h += 1
            else:
                share = tl.sh_share(ts, tr, t_hp_out)
                portions.append((sh * share * (1 - 1 / cop_sh), 0.0, cop_sh))
        if dhw_mode == "element":
            portions.append((hw * s_dhw, 0.0, None))
            el_elem_h = hw * (1 - s_dhw)
        else:
            portions.append((hw * (1 - 1 / cop_dhw), 0.0, cop_dhw))
            el_elem_h = 0.0

        def step(k, s0):
            heat = k * Q1
            left = [p[0] for p in portions]
            for i in range(len(portions)):
                x = min(left[i], heat)
                heat -= x
                left[i] -= x
            s = s0
            for i, (_, floor_e, _) in enumerate(portions):
                x = min(left[i], max(0.0, s - floor_e))
                s -= x
                left[i] -= x
            served = [portions[i][0] - left[i] for i in range(len(portions))]
            return served, s + heat

        k = 0
        for kk in range(nmax, -1, -1):
            if step(kk, soc)[1] <= cap + EPS:
                k = kk
                break
        served, soc = step(k, soc)
        u_srv = sum(served)
        hp_el = sum(x / (p[2] - 1) for x, p in zip(served, portions) if p[2])   # compressor electricity
        # element top-up = the part above the preheat temperature, every hour (same convention as r4_tank_layout)
        q_srv += u_srv
        q_hp_el += hp_el
        el_elem += el_elem_h
        run_h += k
        key = "summer" if t[5:7] in ("06", "07", "08") else "winter" if t[5:7] in ("12", "01", "02") else "rest"
        sv = seas.setdefault(key, [0.0, 0.0])
        sv[0] += u_srv
        sv[1] += sh + hw
    e_srv = run_h * bs.P_EL
    e_pump = run_h * pump_kw
    delivered = q_srv + q_hp_el
    be_case = ((e_srv + e_pump + q_hp_el) * PRICE - delivered * HEAT_VALUE) / run_h if run_h else float("nan")
    be_chg = be_case + (el_elem * PRICE - el_elem * HEAT_VALUE) / run_h if run_h else float("nan")
    return {"n": n, "cov_srv": q_srv / dem, "cov_chain": delivered / dem, "util": run_h / (n * 8760),
            "run_h": run_h, "dumped": 0.0, "be_case": be_case, "be_chg": be_chg, "hp_el": q_hp_el,
            "el_elem": el_elem, "e_pump": e_pump, "blocked_h": blocked_h, "cap": cap,
            "summer": seas["summer"][0] / seas["summer"][1], "winter": seas["winter"][0] / seas["winter"][1]}


def direct_shares(rows, chain, house):
    """Energy-weighted share of the year's space heat and hot water the chain's server heat serves
    (before the server count limits it): temperature-limited and return-limited."""
    t_top, ret_max, sh_mode, dhw_mode, cop_sh, cop_dhw, _ = CHAINS[chain]
    sysdef = tl.SYSTEMS[house]
    sh_tot = ok = 0.0
    for _, sh, _hw in rows:
        if sh <= 0:
            continue
        sh_tot += sh
        ts, tr = tl.curve(sh / 10.0, sysdef)
        if sh_mode == "direct":
            if ret_max is not None and tr > ret_max + EPS:
                continue
            ok += sh * tl.sh_share(ts, tr, t_top)
        else:
            ok += sh * tl.sh_share(ts, tr, 55.0) * (1 - 1 / cop_sh)
    dhw = dhw_direct_share(t_top) if dhw_mode == "element" else (1 - 1 / cop_dhw)
    return ok / sh_tot, dhw


# ---------------------------------------------------------------- installed cost (CHF incl. 8.1 % VAT)
EUR_CHF, VAT_CH, VAT_DE = mc.EUR_CHF, mc.VAT_CH, mc.VAT_DE
BLOCK_EUR = 399.98   # SOURCED: Alphacool ES RTX PRO 4500 Blackwell 1-slot block, MSRP incl. DE VAT (overclocking.com)
BLOCK_CHF = BLOCK_EUR / (1 + VAT_DE) * EUR_CHF * (1 + VAT_CH)
BFE = 36000.0        # SOURCED (r4): BFE 2015 median installed air/water heat-pump system, CHF excl. VAT
BFE_TANK = BFE * 0.03 * (1 + VAT_CH)      # storage tank 2-4 % share (BFE), 3 % taken: 1,000 l buffer proxy
BFE_DHW = BFE * 0.075 * (1 + VAT_CH)      # "Wassererwaermer" 7-8 % share, 7.5 % taken: DHW cylinder proxy
BFE_HP = BFE * 0.42 * (1 + VAT_CH)        # heat pump 42 % share: 9 kW heat-pump unit proxy
HPB_INSTALLED = 6000.0                    # SOURCED: heat-pump water heater 300 l, CH, "rund CHF 6.000 inkl. Montage"

# per box: (low, central, high)
PER_BOX = {
    "air coil (r4)": {"AIR": (1000, 2500, 4000)},
    "cold plates": {"DLC": (4 * BLOCK_CHF + 150 + 500 + 240, 4 * BLOCK_CHF + 250 + 800 + 360,
                            4 * BLOCK_CHF + 400 + 1500 + 600)},
}


def chain_costs(chain, case="central"):
    """Returns (per-box capture cost, per-house extra items dict) for the chain. Items are on top of the
    r4 central box (4 cards + platform) and r4 house integration (38 % BFE proxy)."""
    i = {"low": 0, "central": 1, "high": 2}[case]
    house = {"1,000 l buffer (BFE 3 % proxy)": BFE_TANK}
    if chain.startswith("DLC") or chain == "A0":
        box = PER_BOX["cold plates"]["DLC"][i]
        house["CDU: plate HX + pump group + controls (assumption)"] = (2000, 3000, 6000)[i]
        house["fresh-water station (assumption)"] = (1500, 2000, 3000)[i]
        house["small DHW cylinder + element (BFE 7.5 % proxy)"] = BFE_DHW
    else:
        box = PER_BOX["air coil (r4)"]["AIR"][i]
        if chain in ("AIR", "AIR35"):
            house["fresh-water station (assumption)"] = (1500, 2000, 3000)[i]
            house["small DHW cylinder + element (BFE 7.5 % proxy)"] = BFE_DHW
        elif chain == "AIR+HPB":
            house["heat-pump water heater, installed (sourced CH)"] = HPB_INSTALLED
        else:
            house["water/water heat pump (BFE 42 % proxy)"] = BFE_HP
            house["small DHW cylinder (BFE 7.5 % proxy)"] = BFE_DHW
    return box, house


def installed(n, chain, case="central"):
    box_capture, house_items = chain_costs(chain, case)
    box = mc.N_GPU * mc.CARD[case] + mc.PLATFORM[case] + box_capture
    boxes = n / mc.wall_kw("central")
    total = boxes * box + mc.HOUSE_INTEGRATION[case] + mc.GRID_UPGRADE[case] + sum(house_items.values())
    return total, boxes, box, house_items


def r4_installed(n):
    return mc.installed_per_house(n, "central", "central")[0]


def line(label, r):
    return (f"{label:<48}{r['n']:>2} {r['cov_srv']*100:6.1f}% {r['cov_chain']*100:6.1f}% {r['winter']*100:6.1f}% "
            f"{r['summer']*100:6.1f}% {r['dumped']:>4.0f} {r['util']*100:5.1f}% {r['run_h']:>6.0f} "
            f"{r['blocked_h']:>5} {r['hp_el']+r['e_pump']:>6.0f} {r['el_elem']:>5.0f} {r['be_case']:.4f} {r['be_chg']:.4f}")


HDR = (f"{'chain / house':<48}{'N':>2} {'covSrv':>7} {'covChn':>7} {'Dec-Feb':>7} {'Jun-Aug':>7} {'dump':>4} "
       f"{'util':>6} {'srv-h':>6} {'blkd':>5} {'HP+pmp':>6} {'elem':>5} {'BEcase':>6} {'BEchg':>6}")


def main():
    rows = bs.load()
    print("r5_chain.py  (CHF; electricity %.4f CHF/kWh, heat %.4f CHF/kWh; 1 EUR = %.4f CHF, ECB 20 Nov 2026)"
          % (PRICE, HEAT_VALUE, EUR_CHF))

    print("\n== 0. Regression checks ==")
    for n in (6, 8):
        a = tl.sim(rows, n, tl.SYSTEMS["underfloor 35/28"], tank_loss=LOSS)
        b = sim(rows, n, "A0", "underfloor 35/28", tank_loss=LOSS)
        ok = abs(a["coverage"] - b["cov_srv"]) < 1e-9 and a["run_h"] == b["run_h"] and abs(a["be_case"] - b["be_case"]) < 1e-9 \
            and abs(a["be_charged"] - b["be_chg"]) < 1e-9
        print(f"  A0 vs r4_tank_layout.sim, underfloor + loss, N={n}: r4 {a['coverage']*100:.3f}% {a['run_h']:.0f} h "
              f"{a['be_case']:.4f}/{a['be_charged']:.4f} | r5 {b['cov_srv']*100:.3f}% {b['run_h']:.0f} h "
              f"{b['be_case']:.4f}/{b['be_chg']:.4f} -> {'OK' if ok else 'MISMATCH'}")
    for n in (6, 8):
        r = sim(rows, n, "DLC", "radiator 55/45", tank_loss=LOSS)
        print(f"  DLC radiator 55/45 + loss, N={n}: {r['cov_srv']*100:.1f}% (round-4 critic probe: 64.3% / 73.0%), "
              f"blocked {r['blocked_h']} h (critic: 853)")

    print("\n== 1. Inputs ==")
    for k, v in CHAINS.items():
        t_top, ret_max, shm, dhm, cs, cd, pk = v
        print(f"  {k:<8} top {t_top:4.0f} C, return limit {ret_max if ret_max else '-':>4}, space heat {shm:<6}, "
              f"hot water {dhm:<7}, COP sh {cs if cs else '-'}, COP dhw {cd if cd else '-'}, pump {pk} kW/srv  | {LABEL[k]}")
    print(f"  COP_WW_HIGH = WPZ W10/W55 3.6 -> Carnot efficiency {ETA_WW:.3f} -> source 22 C out / sink 55 C: {COP_WW_HIGH:.2f}"
          " (computed extrapolation, unverified)")
    print(f"  GPU block {BLOCK_EUR} EUR incl. 19% DE VAT -> {BLOCK_CHF:,.0f} CHF incl. 8.1% CH VAT")
    gw = mc.N_GPU * mc.GPU_MAX_W * mc.POWER_CASES["central"][0]
    cpu = mc.POWER_CASES["central"][1]
    print(f"  liquid capture share of wall power (central r4 power model): (GPUs {gw:.0f} + CPU {cpu:.0f} W) / "
          f"{mc.wall_kw('central')*1000:.0f} W = {(gw + cpu) / (mc.wall_kw('central')*1000)*100:.1f}%  (case: 80% recovered)")

    print("\n== 2. Direct shares by chain and house (energy-weighted, before the server count limits it) ==")
    print(f"  {'chain':<9}" + "".join(f"{h:>18}" for h in HOUSES) + f"{'hot water':>11}")
    for ch in CHAINS:
        cells = []
        for h in HOUSES:
            s, d = direct_shares(rows, ch, h)
            cells.append(f"{s*100:17.1f}%")
        print(f"  {ch:<9}" + "".join(cells) + f"{d*100:10.1f}%")
    print("  (heat-pump chains: share of the demand that is SERVER heat, i.e. x (1 - 1/COP); the rest is compressor heat)")

    print("\n== 3. Realism column per chain, tank loss 2.80 kWh/day, follow rule (never dumps) ==")
    print("  covSrv = server heat / demand (case definition); covChn = incl. heat-pump compressor heat;")
    print("  blkd = hours servers must stop (house return above the chain's limit); HP+pmp, elem = kWh el per year")
    print(HDR)
    res = {}
    for n in (6, 8):
        r = bs.simulate(rows, n)
        print(f"{'case assumptions (baseline_sweep)':<48}{n:>2} {r['coverage']*100:6.1f}% {r['coverage']*100:6.1f}% "
              f"{'':>7} {'100.0%':>7} {0:>4} {r['util']*100:5.1f}% {r['run_h']:>6.0f} {0:>5} {0:>6} {0:>5} "
              f"{r['breakeven']:.4f} {r['breakeven']:.4f}")
        for ch in CHAINS:
            for h in HOUSES:
                rr = sim(rows, n, ch, h, tank_loss=LOSS)
                res[(n, ch, h)] = rr
                print(line(f"{ch} | {h}", rr))
        print()

    print("== 4. Installed cost per house and share of list price needed (central costs, central price, "
          "every permit hour sold, simple payback) ==")
    mix = mc.list_value("central", "central")[2]
    print(f"  list value of one server-hour of work (r4, central): {mix:.2f} CHF")
    for n in (6, 8):
        base = r4_installed(n)
        rb = bs.simulate(rows, n)
        op_b = (rb["elec"] - rb["heat_val"]) / rb["run_h"]
        print(f"  N={n} r4 basis (air coil, no storage/DHW items, case run): {base:,.0f} CHF; operation {op_b:.4f}; "
              f"share needed operation {op_b/mix*100:.1f}%, 5 y {(op_b + base/(5*rb['run_h']))/mix*100:.1f}%, "
              f"8 y {(op_b + base/(8*rb['run_h']))/mix*100:.1f}%")
        for ch in ("DLC", "AIR", "AIR35", "AIR+HPB", "AIR+HP"):
            tot, boxes, box, items = installed(n, ch)
            r = res[(n, ch, "underfloor 35/28")]
            op = r["be_chg"]
            s5 = (op + tot / (5 * r["run_h"])) / mix
            s8 = (op + tot / (8 * r["run_h"])) / mix
            print(f"    {ch:<8} {tot:>9,.0f} CHF ({tot/n:,.0f} per 1 kW server; +{tot-base:,.0f} vs r4), box {box:,.0f} x {boxes:.2f}; "
                  f"underfloor run {r['run_h']:,.0f} h; BEchg {op:.4f}; share op {op/mix*100:.1f}%, 5 y {s5*100:.1f}%, 8 y {s8*100:.1f}%")
        lo, _, _, _ = installed(n, "DLC", "low")
        hi, _, _, _ = installed(n, "DLC", "high")
        r = res[(n, "DLC", "underfloor 35/28")]
        print(f"    DLC range low / high: {lo:,.0f} / {hi:,.0f} CHF; 5 y share "
              f"{(r['be_chg'] + lo/(5*r['run_h']))/mix*100:.1f}% / {(r['be_chg'] + hi/(5*r['run_h']))/mix*100:.1f}% "
              "(low/high costs, central price)")
    _, _, _, items = installed(6, "DLC")
    print("  DLC per-house items: " + "; ".join(f"{k} {v:,.0f}" for k, v in items.items()))
    print(f"  DLC per box capture (central): 4 blocks {4*BLOCK_CHF:,.0f} + CPU plate 250 + manifold/QDs/tubing/leak sensor 800"
          f" + 3 h assembly 360 = {chain_costs('DLC')[0]:,.0f} CHF (r4 air coil: 2,500)")

    print("\n== 5. Pitch lines, recommended chain DLC (N=6 / N=8) ==")
    c6, c8 = bs.simulate(rows, 6), bs.simulate(rows, 8)
    for h in HOUSES:
        a, b = res[(6, "DLC", h)], res[(8, "DLC", h)]
        print(f"  {h:<18} coverage {a['cov_srv']*100:.1f}% / {b['cov_srv']*100:.1f}%; Jun-Aug {a['summer']*100:.1f}%; "
              f"util {a['util']*100:.1f}% / {b['util']*100:.1f}%; BEcase {a['be_case']:.4f} / {b['be_case']:.4f}; "
              f"BEchg {a['be_chg']:.4f} / {b['be_chg']:.4f}; servers stop {a['blocked_h']} h")
    print(f"  case column: {c6['coverage']*100:.1f}% / {c8['coverage']*100:.1f}%, util {c6['util']*100:.1f}% / "
          f"{c8['util']*100:.1f}%, BE {c6['breakeven']:.4f}")
    for n in (6, 8):
        r = bs.simulate(rows, n, tank_loss_kwh_day=LOSS, dhw_direct_share=37 / 45)
        print(f"  build-scope check N={n}: baseline_sweep.simulate(dhw_direct_share=37/45, tank_loss 2.80) = "
              f"{r['coverage']*100:.2f}%, util {r['util']*100:.1f}%, BE {r['breakeven']:.4f}")


if __name__ == "__main__":
    main()
