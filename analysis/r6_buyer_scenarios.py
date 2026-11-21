"""Round 6, weak point "who buys a heat-shaped contract and what the operator really receives".

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.

    python3 analysis/r6_buyer_scenarios.py              # seeds 1-3, all CPU cores (about 10-60 s)
    python3 analysis/r6_buyer_scenarios.py --seeds 1    # seed 1 only
    python3 analysis/r6_buyer_scenarios.py --procs 1    # no multiprocessing

What it does
  Runs the round-4 headline yearly loop (r4_headline.run, policy HEADLINE: cap + 8 kWh band,
  EDF admission dry run, archived ECMWF ifs025 + 2 K guard, restart outside execution) for
  N = 6 and N = 8 under several BUYER scenarios, then prices the sold server-hours with every
  operator-price anchor we could source, and sizes a typed partner site for refused summer work.

  Buyer scenarios (offered server-hours per day; J1 = 0.5 server-h / 24 h deadline,
  J2 = 4 server-h / 168 h deadline, both ASSUMPTIONS from the plan):
    shaped100   current headline: heat-shaped contract = 100 % of the house's 2020-24 normal
                heat-permit capacity, 50/50 J1/J2 by server-hours (ASSUMPTION, ~10:1 Jan/Jul)
    flat        the same yearly volume, offered evenly every day, 50/50
    llm_flat    LLM-only batch customer: same yearly volume, flat, 100 % J2 (168 h deadline =
                the longest batch window found, Groq 24 h - 7 d, SOURCED)
    llm_shaped  LLM-only but heat-shaped (separates job mix from shape)
    flat_july   a flat customer sized to what the house can take in July (15 server-h/day,
                the shaped100 July rate): a contract nobody has to refuse, 50/50
    pool        an aggregator that takes every permit hour ("saturating" offers, 50/50); this is
                the house as a spot supplier into a larger pool (Heata-style cloud burst covers
                the buyer's SLA elsewhere). Sold hours ~ permit hours.

  Operator price anchors (CHF per sold server-hour unless marked; 1 server-hour = 1 kWh at the
  wall = 4 / 0.955 = 4.19 GPU-hours of the reference box, r4_machine central power):
    list20      20 % of the US public batch list value (r4_machine central) -- the plan's
                ASSUMPTION, no source for the 20 %
    rent041     GPU rental, cheapest listed 0.41 USD per GPU-h x 80 % host share (both SOURCED in
                r4 / r2; data-centre, always-on capacity, NOT shown to apply to a heat-following host)
    rent048     cheapest listed on re-read in round 6 (0.48 USD, same page, 21 Nov 2026)
    rent072     same at RunPod Secure Cloud 0.72 USD per GPU-h
    heata_t2    Heata's own published GPU surcharge, Tier 2 (24-40 GB: our 32 GB card), GBP 1.19
                per GPU-h, excl. VAT, GPU only (no vCPU/RAM added), operator keeps 100 % (direct
                sale). SOURCED docs.heata.co/pricing-billing (2026). A LIST price of a heat-following
                seller whose filed trade debtors were GBP 340 at end-2025 (team research): not a
                realised price.
  Swiss-resident LLM list (J2 only, list value, not an operator price):
                Infomaniak AI Services, synchronous, prices excl. VAT, read 21 Nov 2026:
                Ministral-3-14B CHF 0.30 in / 0.40 out per M tokens; Gemma-4-31B 0.20 / 0.40.
                Billed with the plan's 6 input tokens per output token (r3_income.IN_PER_OUT,
                ASSUMPTION). Different, larger models than the MLPerf Llama-3.1-8B row.

Nothing is edited. It imports (read-only): r4_headline (run, HEADLINE, JT, MDAYS, rates_for),
r2_deadline_sim (offer_rates, WORK_SHARE: set per scenario inside the worker), r4_machine
(list_value, work_per_server_hour, wall_kw, N_GPU, USD_CHF, EUR_CHF), r5_chain (installed: the
cold-plate chain "DLC", central), r3_income (IN_PER_OUT), baseline_sweep (PRICE, HEAT_VALUE, REC).
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # do not touch analysis/__pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import REC  # noqa: E402
import r2_deadline_sim as R  # noqa: E402
import r3_income as I  # noqa: E402
import r4_headline as H  # noqa: E402
import r4_machine as M  # noqa: E402
import r5_chain as C  # noqa: E402

# ---------------------------------------------------------------- sourced / assumed constants
EUR_GBP = 0.83735                      # SOURCED: ECB reference rates 20 Nov 2026 (GBP per EUR)
GBP_CHF = M.EUR_CHF / EUR_GBP          # 0.9223 / 0.83735 = 1.1014 CHF per GBP (computed)
USD_CHF = M.USD_CHF                    # 0.8392, ECB 20 Nov 2026 (sourced in round 1)
GPU_PER_SH = M.N_GPU / M.wall_kw("central")   # 4.19 GPU-hours per 1 kW server-hour (power ASSUMPTION)
HOST_SHARE = 0.80                      # SOURCED in r2 (Salad, Vast.ai): host keeps ~80 % of renter price
RENT_USD = {"rent041": 0.41, "rent048": 0.48, "rent072": 0.72}   # SOURCED: getdeploying.com cheapest (0.41 GPU.ai
                                       # in r4 at ~09:50; 0.48 Lium on re-read in r6), runpod.io Secure 0.72
HEATA_T2_GBP = 1.19                    # SOURCED: docs.heata.co/pricing-billing, Tier 2 GPU surcharge
OP_SHARE = 0.20                        # ASSUMPTION (plan): share of list reaching the operator
SWISS_LLM = {"Ministral-3-14B": (0.30, 0.40), "Gemma-4-31B": (0.20, 0.40)}   # SOURCED, CHF / M tokens
YEARS = 5.0                            # ASSUMPTION (plan): simple payback horizon
CHAIN = "DLC"                          # r5 cold-plate chain, central installed cost

# partner site (section 3)
POOL_KWH_M2_SEASON = (430.0, 480.0)    # SOURCED: BFE/VHF Leitfaden 2018 p.156, Freibad without cover,
                                       # mid-May to mid-Sep (~120 operating days), 24 C, Swiss Mittelland
POOL_SEASON_D = 120.0                  # SOURCED, same page
POOL_AREA_M2 = 50.0 * 21.0             # ASSUMPTION: one heated 50 m pool (St. Jakob Basel has one,
                                       # SOURCED bs.ch), 8 lanes x ~2.6 m wide = 21 m (width assumed)
INDOOR_POOL_JUL_KWH = 24000.0          # SOURCED (read by eye from Abb. 1, p.29, +/- 2,000 kWh):
                                       # "typisches Hallenbad", July heat demand, same Leitfaden
LEAFCLOUD_MIN_GJ = 500.0               # SOURCED: leaf.cloud/leafsites, minimum hot-water demand GJ/yr

SCEN = [
    # key, demand, work share (J1, J2), flat rate or None, label
    ("shaped100", "shaped100", (0.5, 0.5), None, "heat-shaped contract, 50/50 (current headline)"),
    ("flat", "flat", (0.5, 0.5), None, "flat customer, same yearly volume, 50/50"),
    ("llm_flat", "flat", (0.0, 1.0), None, "LLM-only batch customer, flat, same volume"),
    ("llm_shaped", "shaped100", (0.0, 1.0), None, "LLM-only, heat-shaped"),
    ("flat_july", "flat_custom", (0.5, 0.5), 15.0, "flat customer sized to July capacity (15 sh/d)"),
    ("pool", "saturating", (0.5, 0.5), None, "aggregator takes every permit hour (spot supplier)"),
]
SUMMER = (5, 6, 7)   # Jun, Jul, Aug (0-indexed), as in r4_headline.run


def task(cfg):
    key, n, demand, share, flat, seed = cfg
    R.WORK_SHARE = share                       # read at run time by r4_headline.run (module attribute)
    res = H.run(n, H.HEADLINE, demand, seed, flat)
    for f in ("ks_cap", "ks_on", "pin_run"):
        res.pop(f, None)
    res["rates"] = H.rates_for(demand, n, flat)
    res["share"] = share
    return (key, n, seed), res


def money(r, n):
    lv = {pc: M.list_value("central", pc) for pc in ("low", "central", "high")}   # (j1, j2, mix) CHF/sh
    j1h, j2h = r["sold_t"]
    sold = r["sold_h"]
    net = r["elec"] - r["heat_val"]
    inst = C.installed(n, CHAIN)[0]
    need = net + inst / YEARS
    list_v = {pc: j1h * lv[pc][0] + j2h * lv[pc][1] for pc in lv}
    inc = {"list20": OP_SHARE * list_v["central"]}
    for k, usd in RENT_USD.items():
        inc[k] = sold * GPU_PER_SH * usd * HOST_SHARE * USD_CHF
    inc["heata_t2"] = sold * GPU_PER_SH * HEATA_T2_GBP * GBP_CHF
    _, tok = M.work_per_server_hour("central")
    ch_list = {m: j2h * tok / 1e6 * (I.IN_PER_OUT * p_in + p_out) for m, (p_in, p_out) in SWISS_LLM.items()}
    return dict(net=net, inst=inst, need=need, list_v=list_v, inc=inc, ch_list=ch_list,
                need_per_sh=need / sold if sold else float("nan"))


def payback(inst, inc, net):
    m = inc - net
    return inst / m if m > 0 else float("inf")


def fmt_pb(y):
    return "never" if y == float("inf") else f"{y:.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--procs", type=int, default=0)
    a = ap.parse_args()
    seeds = list(range(1, a.seeds + 1))
    cfgs = [(k, n, d, s, f, sd) for (k, d, s, f, _) in SCEN for n in (6, 8) for sd in seeds]
    if a.procs == 1:
        res = dict(task(c) for c in cfgs)
    else:
        import multiprocessing as mp
        with mp.Pool(a.procs or None) as p:
            res = dict(p.map(task, cfgs))

    def mean(key, n, f):
        return sum(res[(key, n, s)][f] for s in seeds) / len(seeds)

    print("r6_buyer_scenarios.py. Currency CHF. 1 USD = %.4f CHF, 1 GBP = %.4f CHF (ECB 20 Nov 2026)." % (USD_CHF, GBP_CHF))
    print(f"Policy = r4_headline.HEADLINE; seeds {seeds}; means over seeds unless marked; missed = seed 1, 'x of y accepted jobs'.")
    print(f"Reference box: {GPU_PER_SH:.2f} GPU-h per 1 kW server-h (central wall power, ASSUMPTION). Installed cost "
          f"(cold-plate chain, central): N=6 {C.installed(6, CHAIN)[0]:,.0f}, N=8 {C.installed(8, CHAIN)[0]:,.0f} CHF.\n")

    # ------------------------------------------------------------ 1. key figures per buyer
    print("== 1. Key figures per buyer scenario (computed) ==")
    hdr = (f"{'scenario':<11}{'N':>2} {'offer sh/d':>10} {'Jan/Jul':>8} {'cover':>7} {'util':>6} {'sold sh':>8} "
           f"{'J1 sh':>7} {'J2 sh':>7} {'acc%':>6} {'sumJ1%':>6} {'missed (seed 1)':>18} {'BE':>7} {'BE+rst':>7} {'starts':>6}")
    print(hdr)
    for key, _, _, _, label in SCEN:
        for n in (6, 8):
            r1 = res[(key, n, 1)]
            rates = r1["rates"]
            yr = sum(rates[m] * R.MDAYS[m] for m in range(12)) / 365.0
            ratio = rates[0] / rates[6] if rates[6] else float("inf")
            j1 = sum(res[(key, n, s)]["sold_t"][0] for s in seeds) / len(seeds)
            j2 = sum(res[(key, n, s)]["sold_t"][1] for s in seeds) / len(seeds)
            sumj1 = "n/a" if r1["share"][0] == 0 else f"{mean(key, n, 'acc_j1_summer')*100:5.1f}"
            print(f"{key:<11}{n:>2} {yr:>10.1f} {ratio:>8.1f} {mean(key, n, 'coverage')*100:>6.2f}% "
                  f"{mean(key, n, 'util')*100:>5.1f}% {mean(key, n, 'sold_h'):>8,.0f} {j1:>7,.0f} {j2:>7,.0f} "
                  f"{mean(key, n, 'acc_jobs')*100:>5.1f}% {sumj1:>6} "
                  f"{r1['missed_n']:>6,} of {r1['closed_n']:>8,} {mean(key, n, 'breakeven'):>7.4f} "
                  f"{mean(key, n, 'be_restart'):>7.4f} {mean(key, n, 'starts'):>6,.0f}")
    print("  offer sh/d = offered server-hours per day (year mean); Jan/Jul = offer-rate ratio; BE = (electricity - heat used) /")
    print("  sold server-h (case formula, CHF); BE+rst = with 15-min restart per start (accounting line, ASSUMPTION).")
    print("  " + "; ".join(f"{k} = {lab}" for k, _, _, _, lab in SCEN) + "\n")

    # ------------------------------------------------------------ 2. what the operator receives
    print("== 2. What the operator receives: income, payback and share of list needed vs available (computed) ==")
    print(f"  need = (electricity - heat) + installed / {YEARS:.0f} y (simple payback, no interest, cold-plate chain central).")
    print("  list = US public batch list value of the sold work (r4_machine central prices); 'avail' = anchor income / list.")
    print(f"{'scenario':<11}{'N':>2} {'need/yr':>8} {'need/sh':>7} {'list/yr':>9} {'op%':>5} {'5y%':>5} | "
          f"{'anchor':<9}{'inc/yr':>9} {'CHF/sh':>7} {'avail%':>7} {'payback y':>9}")
    for key, *_ in SCEN:
        for n in (6, 8):
            ms = [money(res[(key, n, s)], n) for s in seeds]
            sold = mean(key, n, "sold_h")
            net = sum(x["net"] for x in ms) / len(ms)
            inst = ms[0]["inst"]
            need = sum(x["need"] for x in ms) / len(ms)
            lvc = sum(x["list_v"]["central"] for x in ms) / len(ms)
            first = True
            for anc in ("list20", "rent041", "rent048", "rent072", "heata_t2"):
                inc = sum(x["inc"][anc] for x in ms) / len(ms)
                left = (f"{key:<11}{n:>2} {need/1000:>7.1f}k {need/sold:>7.3f} {lvc/1000:>8.1f}k {net/lvc*100:>4.1f}% "
                        f"{need/lvc*100:>4.1f}%" if first else " " * 56)
                print(f"{left} | {anc:<9}{inc/1000:>8.1f}k {inc/sold:>7.3f} {inc/lvc*100:>6.1f}% {fmt_pb(payback(inst, inc, net)):>9}")
                first = False
            if res[(key, n, 1)]["share"][0] == 0:
                for mname in SWISS_LLM:
                    chl = sum(x["ch_list"][mname] for x in ms) / len(ms)
                    print(" " * 56 + f" | Swiss list ({mname}, J2): {chl/1000:,.1f}k CHF/yr list value; 5-y share needed "
                          f"{need/chl*100:.1f}% (vs {need/lvc*100:.1f}% of the US batch list)")
    print("  list20 = 20 % of US batch list (ASSUMPTION); rent041 / rent048 / rent072 = GPU rental 0.41 / 0.48 / 0.72 USD per GPU-h x 80 % host share;")
    print("  heata_t2 = Heata's published Tier-2 GPU list surcharge GBP 1.19 per GPU-h, GPU only, operator keeps 100 % (a list price).\n")

    # ------------------------------------------------------------ 3. refused work and a typed partner site
    print("== 3. Refused work and a typed partner site for it (computed; pool figures SOURCED x area ASSUMPTION) ==")
    pool_d = [POOL_AREA_M2 * q / POOL_SEASON_D for q in POOL_KWH_M2_SEASON]
    leaf_d = LEAFCLOUD_MIN_GJ * 1e9 / 3.6e6 / 365.0
    indoor_d = INDOOR_POOL_JUL_KWH / 31.0
    print(f"  heated outdoor 50 m pool, {POOL_AREA_M2:,.0f} m2 (ASSUMPTION) x {POOL_KWH_M2_SEASON[0]:.0f}-{POOL_KWH_M2_SEASON[1]:.0f} kWh/m2 per "
          f"{POOL_SEASON_D:.0f}-day season: {pool_d[0]:,.0f}-{pool_d[1]:,.0f} kWh/day = {pool_d[0]/24:,.0f}-{pool_d[1]/24:,.0f} kW average = "
          f"{pool_d[0]/24/REC:,.0f}-{pool_d[1]/24/REC:,.0f} servers' recovered heat (0.8 kW each)")
    print(f"  typical indoor pool, July: {INDOOR_POOL_JUL_KWH:,.0f} kWh/month = {indoor_d:,.0f} kWh/day = {indoor_d/24/REC:,.0f} servers; "
          f"Leafcloud minimum host: {LEAFCLOUD_MIN_GJ:.0f} GJ/yr = {leaf_d:,.0f} kWh/day = {leaf_d/24/REC:,.0f} servers")
    print(f"{'scenario':<11}{'N':>2} {'refused sh/yr':>13} {'heat MWh/yr':>11} {'sum J1 ref sh/d':>15} {'heat kWh/d':>10} "
          f"{'houses per outdoor pool':>23} {'per indoor pool (Jul)':>21}")
    for key, *_ in SCEN:
        for n in (6, 8):
            ref = []
            for s in seeds:
                r = res[(key, n, s)]
                ref.append(sum((r["off"][i] - r["acc"][i]) * H.JT[i][1] for i in (0, 1)))
            ref_h = sum(ref) / len(ref)
            r1 = res[(key, n, 1)]
            rates, share = r1["rates"], r1["share"]
            if share[0] > 0:
                off_sum = sum(rates[m] * share[0] * R.MDAYS[m] for m in SUMMER) / sum(R.MDAYS[m] for m in SUMMER)
                ref_sum = off_sum * (1.0 - mean(key, n, "acc_j1_summer"))
                heat_d = ref_sum * REC
                hp = (f"{pool_d[0]/heat_d:>9,.0f}-{pool_d[1]/heat_d:<9,.0f}" if heat_d > 0.05 else f"{'(none refused)':>19}")
                hi = f"{indoor_d/heat_d:>17,.0f}" if heat_d > 0.05 else f"{'-':>17}"
                print(f"{key:<11}{n:>2} {ref_h:>13,.0f} {ref_h*REC/1000:>11.1f} {ref_sum:>15.1f} {heat_d:>10.1f} {hp:>23} {hi:>21}")
            else:
                print(f"{key:<11}{n:>2} {ref_h:>13,.0f} {ref_h*REC/1000:>11.1f} {'n/a (no J1)':>15} {'':>10} {'':>23} {'':>21}")
    print("  refused = offered - accepted work (server-h; refused at intake, never started). Summer J1 refused = expected June-August")
    print("  J1 offers x (1 - summer J1 acceptance): an expectation-based estimate, not counted from the run. Heat = 0.8 kWh per server-h.")
    print("  'pool' offers every hour, so its 'refused' is the unlimited backlog nobody sends; read it as 'not offered', not as lost work.")


if __name__ == "__main__":
    main()
