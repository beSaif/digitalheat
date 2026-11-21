"""Round 5: every pitch / Q&A number of docs/overnight.md in one command (weak point: reproducibility).

ASSESSMENT ONLY. Not the team's scheduler, dashboard or demo. Standard library only.

    python3 analysis/r5_pitch_numbers.py              # everything, seeds 1-3, all CPU cores (~1-2 min)
    python3 analysis/r5_pitch_numbers.py --procs 1    # no multiprocessing (~5 min)
    python3 analysis/r5_pitch_numbers.py --skip-r2    # leave out the round-2 no-guard miss runs (10 years)
    python3 analysis/r5_pitch_numbers.py --md         # also print the checklist as Markdown table rows

Covers the numbers in "Read this first" and "Key numbers" of docs/overnight.md (state after round 4).
Each line: [id] label = value | plan: value as written in the plan | status | MATCH / DIFF.
MATCH means the value, rounded to the last digit the plan shows, equals the plan's figure.

Nothing is edited. It imports (read-only):
  baseline_sweep.py      simulate(), load(), case constants
  r2_deadline_sim.py     base(), err_stats(), offer_rates(), run() (round-2 no-guard miss runs)
  r2_realism.py          sim() (starts, idle power, air-cooled / no direct hot water), INPUTS
  r3_income.py           E_PROBE, IN_PER_OUT, prices (two-machine basis)
  r4_headline.py         run(), HEADLINE, PERFECT, money(), pause_resume_days(), day_index(), MDAYS
  r4_machine.py          wall_kw(), work_per_server_hour(), list_value(), installed_per_house(), costs
  r4_tank_layout.py      sim(), curve(), sh_share(), dhw_share(), SYSTEMS, C_KWH_PER_K, T_TOP, Q1
Round-4 critic scratch probes that only lived in the scratchpad are re-implemented here, unchanged in logic:
  fixed contract (both N on one N's offer rates), flat customer, radiator return-limit lower bound,
  5 % interest variants, ex-VAT share, GPU value per house, peak bandwidth, shaped120/150, 2025-01-13 idle permits.
New in round 5: the CHF computing-income scenario on the reference-server basis (r4_machine work per kWh)
next to the old two-machine basis (laptop J1, B200-slice J2), under the same headline run.
"""
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # do not touch analysis/__pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_sweep as B  # noqa: E402
import r2_deadline_sim as R  # noqa: E402
import r2_realism as RL  # noqa: E402
import r3_income as I  # noqa: E402
import r4_headline as H  # noqa: E402
import r4_machine as M  # noqa: E402
import r4_tank_layout as T  # noqa: E402

# ---------------------------------------------------------------- fixed-contract patch (critic probe, round 4)
# 'fix6_shaped100' = N=6's shaped100 offer rates whatever N is; 'fix8_' likewise. Installed at import so that
# multiprocessing workers (spawn start method on macOS) see it too.
_orig_offer_rates = R.offer_rates


def _patched_offer_rates(demand, n):
    if demand.startswith("fix6_"):
        return _orig_offer_rates(demand[5:], 6)
    if demand.startswith("fix8_"):
        return _orig_offer_rates(demand[5:], 8)
    return _orig_offer_rates(demand, n)


R.offer_rates = _patched_offer_rates

SEEDS_DEFAULT = 3
INTEREST = 0.05           # ASSUMPTION (round-4 critic): interest rate for the annuity variants
OP_SHARE = I.WHOLESALE    # ASSUMPTION: 20 % of list value reaches the operator
SOLD_67 = 0.67            # ASSUMPTION (r3 / r4_machine default): sold share, unsold hours still run
RECORDS = []


# ---------------------------------------------------------------- output helpers
def fmtv(v, f):
    if isinstance(v, str):
        return v
    if isinstance(v, (tuple, list)):
        return " / ".join(fmtv(x, f) for x in v)
    return format(v, f)


def C(cid, label, value, f, plan, status, cmd_note=""):
    """Print one checked number. plan=None: not in the plan (context line); match not judged."""
    shown = fmtv(value, f)
    if plan is None:
        m = "context"
    else:
        m = "MATCH" if shown.replace(",", "") == plan.replace(",", "") else "DIFF"
    RECORDS.append((cid, label, shown, plan or "-", status, m, cmd_note))
    print(f"  [{cid}] {label} = {shown}" + (f" | plan: {plan}" if plan else "") + f" | {status} | {m}")


def head(t):
    print(f"\n== {t} ==")


# ---------------------------------------------------------------- simulation tasks
def task(cfg):
    key, n, pname, demand, seed, flat, pin, keep = cfg
    P = {"headline": H.HEADLINE, "perfect": H.PERFECT}[pname]
    res = H.run(n, P, demand, seed, flat, pin)
    if not keep:
        for f in ("ks_cap", "ks_on", "pin_run"):
            res.pop(f)
    return (key, n, seed), res


def task_r2(cfg):
    n, seed = cfg
    r = R.run(n, "ifs025", "saturating", 0.0, None, "idle", 0.0, seed)
    return (n, seed), dict(missed=r["missed"], missed_n=r["missed_n"])


def pmap(fn, cfgs, procs):
    if procs == 1:
        return [fn(c) for c in cfgs]
    import multiprocessing as mp
    with mp.Pool(procs) as pool:
        return pool.map(fn, cfgs, chunksize=1)


def mean(res, key, n, seeds, f):
    v = [res[(key, n, s)][f] for s in seeds]
    return sum(v) / len(v)


def annuity(i, y):
    return i / (1 - (1 + i) ** -y) if i else 1.0 / y


def payback_years(inst, margin, i):
    if margin <= 0:
        return float("inf")
    if not i:
        return inst / margin
    x = 1 - inst * i / margin
    return float("inf") if x <= 0 else -math.log(x) / math.log(1 + i)


# ---------------------------------------------------------------- radiator return-limit lower bound
def sim_ret(rows, n, sysdef, ret_max, tank_loss=0.0, t_top=T.T_TOP):
    """Round-4 tank critic probe, same logic: layout A, but servers stop (k = 0) in space-heating hours whose
    heating return exceeds ret_max (the CDU cold end cannot cool 45 C coolant with return water above 40 C)."""
    cap = T.C_KWH_PER_K * (t_top - 20.0)
    s_dhw = T.dhw_share(t_top, 55.0)
    soc = used = run_h = dem = 0.0
    blocked_h = 0
    for t, sh, hw in rows:
        dem += sh + hw
        soc -= min(soc, tank_loss / 24.0)
        if sh > 0:
            ts, tr = T.curve(sh / 10.0, sysdef)
            s_sh = T.sh_share(ts, tr, t_top)
            floor_e = T.C_KWH_PER_K * max(0.0, tr - 20.0)
        else:
            tr, s_sh, floor_e = 20.0, 1.0, 0.0
        d_sh, d_hw = sh * s_sh, hw * s_dhw
        nmax = n
        if sh > 0 and tr > ret_max + 1e-9:
            nmax = 0
            blocked_h += 1

        def step(k, s):
            heat = k * T.Q1
            a = min(d_sh, heat); heat -= a
            b = min(d_hw, heat); heat -= b
            c = min(d_sh - a, max(0.0, s - floor_e)); s -= c
            e = min(d_hw - b, s); s -= e
            return a + b + c + e, s + heat
        k = 0
        for kk in range(nmax, -1, -1):
            if step(kk, soc)[1] <= cap + 1e-9:
                k = kk
                break
        u, soc = step(k, soc)
        used += u
        run_h += k
    return dict(coverage=used / dem, util=run_h / (n * 8760), blocked_h=blocked_h)


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[1:]
    nseeds = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else SEEDS_DEFAULT
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    seeds = list(range(1, nseeds + 1))
    rows = B.load()
    print("r5_pitch_numbers.py. Currency CHF. Stand-in reference house 2025. Seeds", seeds)
    print("Statuses: computed = this script (function named); sourced = constant read from the URL named in the plan;")
    print("assumption = our choice; measured = laptop measurement, NOT re-run here; critic probe = round-4 scratch logic, now here.")

    # ---------------- A. inputs
    head("A. Inputs and conversions")
    C("A1", "CHF per USD (ECB 20 Nov 2026: EUR/CHF 0.9223 / EUR/USD 1.0990)", 0.9223 / 1.0990, ".4f", "0.8392",
      "computed from sourced https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html")
    C("A2", "Swiss VAT %", M.VAT_CH * 100, ".1f", "8.1", "sourced https://www.estv.admin.ch/en/vat-rates-switzerland")
    C("A3", "electricity CHF/kWh (ElCom 2026 IWB H4)", B.PRICE, ".4f", "0.3325",
      "sourced https://www.strompreis.elcom.admin.ch/operator/624?period=2026&category=H4 (data/README.md)")
    C("A4", "heat value CHF/kWh (price / 2.5, case rule)", B.HEAT_VALUE, ".4f", None, "computed (case rule)")

    # ---------------- B. unlimited demand (baseline_sweep)
    head("B. Yearly balance, unlimited demand (baseline_sweep.simulate, follow)")
    bs = {n: B.simulate(rows, n) for n in range(1, 14)}
    al13 = B.simulate(rows, 13, "always")
    C("B1", "total heat demand kWh/yr", sum(a + b for _, a, b in rows), ",.0f", "31,231", "computed")
    C("B2", "space heating kWh/yr", sum(a for _, a, _ in rows), ",.0f", "26,851", "computed")
    C("B3", "hot water kWh/yr", sum(b for _, _, b in rows), ",.0f", "4,380", "computed")
    for n, pc, pu, ph, pe, pv in ((1, "19.5", "87.1", "7,629", "2,537", "812"),
                                  (6, "79.6", "59.1", "31,067", "10,330", "3,306"),
                                  (8, "92.9", "51.8", "36,281", "12,063", "3,860")):
        r = bs[n]
        C(f"B4.{n}", f"N={n} coverage % / dumped kWh / utilisation %", (r["coverage"] * 100, r["dumped"], r["util"] * 100),
          ".1f", f"{pc} / 0.0 / {pu}", "computed")
        C(f"B5.{n}", f"N={n} server-h / electricity CHF / heat value CHF", (r["run_h"], r["elec"], r["heat_val"]), ",.0f",
          f"{ph} / {pe} / {pv}", "computed")
        C(f"B6.{n}", f"N={n} break-even CHF/server-h", r["breakeven"], ".4f", "0.2261", "computed")
    C("B7", "N=13 always-on: coverage % / utilisation %", (al13["coverage"] * 100, al13["util"] * 100), ".0f", "100 / 100", "computed")
    C("B8", "N=13 always-on: dumped kWh / server-h / elec CHF / heat CHF", (al13["dumped"], al13["run_h"], al13["elec"], al13["heat_val"]),
      ",.0f", "59,839 / 113,880 / 37,865 / 4,154", "computed")
    C("B9", "N=13 always-on break-even", al13["breakeven"], ".4f", "0.2960", "computed")
    C("B10", "N=2 coverage % / utilisation %", (bs[2]["coverage"] * 100, bs[2]["util"] * 100), ".1f", "32.7 / 73.0", "computed")
    t10, t140 = B.simulate(rows, 6, tank=10), B.simulate(rows, 6, tank=140)
    C("B11", "N=6 tank 10 kWh / 140 kWh coverage %", (t10["coverage"] * 100, t140["coverage"] * 100), ".1f", "78.8 / 80.3", "computed")
    C("B12", "run h/yr of the 6th / 7th / 8th server",
      tuple(bs[k]["run_h"] - bs[k - 1]["run_h"] for k in (6, 7, 8)), ",.0f", "3,796 / 2,933 / 2,281", "computed")
    C("B13", "unlimited: N=8 minus N=6 coverage pts / utilisation pts (Q&A 2 '13 points for 7 points')",
      ((bs[8]["coverage"] - bs[6]["coverage"]) * 100, (bs[6]["util"] - bs[8]["util"]) * 100), ".0f", "13 / 7", "computed")

    # ---------------- simulations for C/D
    rt = R.offer_rates
    yr = lambda v: sum(v[m] * H.MDAYS[m] for m in range(12)) / 365
    ah_per_sh_laptop = 1000.0 / I.E_PROBE
    named_flat = 1.25e6 / (ah_per_sh_laptop * 0.5) / 365 * 0.5
    cfgs = []
    for n in (6, 8):
        for s in seeds:
            k1 = (s == 1)
            cfgs += [("headline", n, "headline", "shaped100", s, None, None, k1),
                     ("perfect", n, "perfect", "shaped100", s, None, None, False),
                     ("s50", n, "headline", "shaped50", s, None, None, False),
                     ("s200", n, "headline", "shaped200", s, None, None, False),
                     ("sat", n, "headline", "saturating", s, None, None, k1),
                     ("flat", n, "headline", "flat", s, None, None, False),
                     ("fix_other", n, "headline", "fix8_shaped100" if n == 6 else "fix6_shaped100", s, None, None, False),
                     ("named", n, "headline", "flat_custom", s, named_flat, None, False),
                     ("pin_year", n, "headline", "shaped100", s, None, dict(slot=1, mode="year"), False)]
        cfgs += [("s120", n, "headline", "shaped120", 1, None, None, False),
                 ("s150", n, "headline", "shaped150", 1, None, None, False)]
    print(f"\n(running {len(cfgs)} simulated years with r4_headline.run ...)", flush=True)
    res = dict(pmap(task, cfgs, procs))
    demo = {}
    for n, month, slot in ((6, "07", 1), (8, "01", 7)):
        c = H.pause_resume_days(res[("headline", n, 1)]["ks_cap"], slot, month)
        pick = min(c, key=lambda x: abs(int(x[0][8:]) - 15)) if month == "07" else \
            next((x for x in c if x[0] == "2025-01-25"), c[0])      # same pick rule as r4_headline.main()
        demo[n] = dict(slot=slot, pick=pick)
    day_cfgs = [("pin_day", n, "headline", "shaped100", s, None,
                 dict(slot=demo[n]["slot"], mode="day", day=H.day_index(demo[n]["pick"][0])), s == 1)
                for n in (6, 8) for s in seeds]
    res.update(dict(pmap(task, day_cfgs, procs)))
    g = lambda key, n, f: mean(res, key, n, seeds, f)

    # ---------------- C. headline
    head("C. Headline run, shaped100, archived ifs025 + 2 K guard, cap + 8 kWh band (r4_headline.run, seed means)")
    C("C1", "coverage % N=6 / N=8 (2 decimals)", (g("headline", 6, "coverage") * 100, g("headline", 8, "coverage") * 100), ".2f",
      "73.67 / 86.14", "computed")
    C("C1b", "coverage % N=6 / N=8 (pitch, 1 decimal)", (g("headline", 6, "coverage") * 100, g("headline", 8, "coverage") * 100), ".1f",
      "73.7 / 86.1", "computed")
    C("C2", "heat dumped kWh N=6 / N=8", (g("headline", 6, "dumped"), g("headline", 8, "dumped")), ".0f", "0 / 0", "computed")
    C("C3", "utilisation % N=6 / N=8", (g("headline", 6, "util") * 100, g("headline", 8, "util") * 100), ".2f", "54.72 / 47.98", "computed")
    C("C3b", "utilisation % (pitch)", (g("headline", 6, "util") * 100, g("headline", 8, "util") * 100), ".1f", "54.7 / 48.0", "computed")
    C("C4", "offers accepted % N=6 / N=8", (g("headline", 6, "acc_jobs") * 100, g("headline", 8, "acc_jobs") * 100), ".1f",
      "94.7 / 93.8", "computed")
    C("C5", "summer (Jun-Aug) J1 accepted % N=6 / N=8",
      (g("headline", 6, "acc_j1_summer") * 100, g("headline", 8, "acc_j1_summer") * 100), ".1f", "89.6 / 90.3", "computed")
    for n, plan in ((6, "0 of 31,908 / 0 of 31,694 / 0 of 31,996"), (8, "0 of 36,771 / 0 of 36,989 / 0 of 37,201")):
        C(f"C6.{n}", f"N={n} missed x of y accepted jobs, seeds {seeds}",
          " / ".join(f"{res[('headline', n, s)]['missed_n']} of {res[('headline', n, s)]['closed_n']:,}" for s in seeds), None,
          plan if nseeds == 3 else None, "computed")
    C("C7", "server-hours sold N=6 / N=8", (g("headline", 6, "sold_h"), g("headline", 8, "sold_h")), ",.0f", "28,761 / 33,626", "computed")
    C("C8", "electricity CHF/yr N=6 / N=8", (g("headline", 6, "elec"), g("headline", 8, "elec")), ",.0f", "9,563 / 11,181", "computed")
    C("C9", "heat value used CHF/yr N=6 / N=8 (dashboard 'heat worth')", (g("headline", 6, "heat_val"), g("headline", 8, "heat_val")),
      ",.0f", "3,060 / 3,578", "computed")
    C("C10", "break-even CHF per sold server-h N=6 / N=8", (g("headline", 6, "breakeven"), g("headline", 8, "breakeven")), ".4f",
      "0.2261 / 0.2261", "computed")
    C("C11", "break-even with 15-min restart line N=6 / N=8", (g("headline", 6, "be_restart"), g("headline", 8, "be_restart")), ".4f",
      "0.2278 / 0.2286", "computed; 15 min is an assumption")
    C("C12", "N=8 extra coverage points under the headline", (g("headline", 8, "coverage") - g("headline", 6, "coverage")) * 100, ".1f",
      "12.5", "computed")
    C("C13", "N=8 contract larger than N=6's, % (yearly mean offer rate)", (yr(rt("shaped100", 8)) / yr(rt("shaped100", 6)) - 1) * 100,
      ".0f", "17", "computed")
    C("C14", "jobs offered per day N=6 / N=8 (expected)",
      tuple(yr(rt("shaped100", n)) * (0.5 / 0.5 + 0.5 / 4.0) for n in (6, 8)), ".0f", "92 / 108", "computed")
    r6 = rt("shaped100", 6)
    C("C15", "N=6 January J1 / J2 jobs per day; July J1 / J2", (r6[0], r6[0] * 0.5 / 4, r6[6], r6[6] * 0.5 / 4), ".1f",
      "143.9 / 18.0 / 15.0 / 1.9", "computed")
    C("C16", "sold share of unlimited-demand permit hours % N=6 / N=8",
      (g("headline", 6, "sold_h") / bs[6]["run_h"] * 100, g("headline", 8, "sold_h") / bs[8]["run_h"] * 100), ".0f", "93 / 93",
      "computed (plan: 'about 93%')")
    C("C17", "starts per year N=6 / N=8 (headline)", (g("headline", 6, "starts"), g("headline", 8, "starts")), ",.0f", None, "computed")
    C("C18", "perfect-forecast check: missed jobs, all seeds, N=6 + N=8",
      sum(res[("perfect", n, s)]["missed_n"] for n in (6, 8) for s in seeds), "d", "0", "computed")

    # ---------------- D. comparisons
    head("D. Comparison and sensitivity rows (r4_headline.run; critic probes re-implemented)")
    C("D1", "saturating: accepted % N=6 / N=8", (g("sat", 6, "acc_jobs") * 100, g("sat", 8, "acc_jobs") * 100), ".1f", "54.9 / 49.2", "computed")
    C("D1b", "saturating: summer J1 accepted %", (g("sat", 6, "acc_j1_summer") * 100, g("sat", 8, "acc_j1_summer") * 100), ".1f",
      "0.0 / 0.0", "computed")
    C("D2", "shaped200: coverage %", (g("s200", 6, "coverage") * 100, g("s200", 8, "coverage") * 100), ".2f", "78.96 / 92.25", "computed")
    C("D2b", "shaped200: accepted %", (g("s200", 6, "acc_jobs") * 100, g("s200", 8, "acc_jobs") * 100), ".1f", "44.1 / 46.3", "computed")
    C("D2c", "shaped200: mean missed %", (g("s200", 6, "missed") * 100, g("s200", 8, "missed") * 100), ".3f", "0.084 / 0.051", "computed")
    C("D2d", "shaped200 seed 1: missed x of y N=6 / N=8",
      " / ".join(f"{res[('s200', n, 1)]['missed_n']} of {res[('s200', n, 1)]['closed_n']:,}" for n in (6, 8)), None,
      "33 of 28,928 / 11 of 35,991", "computed")
    C("D3", "shaped120 seed 1: coverage % N=6 / N=8", (res[("s120", 6, 1)]["coverage"] * 100, res[("s120", 8, 1)]["coverage"] * 100), ".2f",
      "76.46 / 89.72", "computed (was inline command)")
    C("D3b", "shaped150 seed 1: coverage % N=6 / N=8", (res[("s150", 6, 1)]["coverage"] * 100, res[("s150", 8, 1)]["coverage"] * 100), ".2f",
      "78.23 / 91.80", "computed (was inline command)")
    C("D3c", "shaped120 / shaped150 seed 1: accepted % N=6 / N=8 / N=6 / N=8",
      (res[("s120", 6, 1)]["acc_jobs"] * 100, res[("s120", 8, 1)]["acc_jobs"] * 100,
       res[("s150", 6, 1)]["acc_jobs"] * 100, res[("s150", 8, 1)]["acc_jobs"] * 100), ".1f", "81.7 / 82.8 / 64.0 / 65.4",
      "computed (was inline command)")
    C("D3d", "N=8 missed at shaped120 / shaped150, seed 1", (res[("s120", 8, 1)]["missed_n"], res[("s150", 8, 1)]["missed_n"]), "d",
      "12 / 13", "computed (was inline command)")
    C("D4", "shaped50: coverage %", (g("s50", 6, "coverage") * 100, g("s50", 8, "coverage") * 100), ".2f", "37.99 / 44.59", "computed")
    C("D4b", "shaped50: starts per year (plan '3,000-3,400')", (g("s50", 6, "starts"), g("s50", 8, "starts")), ",.0f", None, "computed")
    C("D5", "flat customer, same yearly volume: coverage % (2 dec.)", (g("flat", 6, "coverage") * 100, g("flat", 8, "coverage") * 100),
      ".2f", "53.67 / 60.48", "computed (critic probe, now here)")
    C("D5b", "flat customer: coverage % (pitch)", (g("flat", 6, "coverage") * 100, g("flat", 8, "coverage") * 100), ".1f",
      "53.7 / 60.5", "computed (critic probe, now here)")
    C("D5c", "flat customer: accepted % / summer J1 %",
      (g("flat", 6, "acc_jobs") * 100, g("flat", 8, "acc_jobs") * 100, g("flat", 6, "acc_j1_summer") * 100,
       g("flat", 8, "acc_j1_summer") * 100), ".1f", "64.1 / 62.4 / 0.0 / 0.0", "computed (critic probe, now here)")
    C("D5d", "flat customer: missed jobs, all seeds N=6 + N=8", sum(res[("flat", n, s)]["missed_n"] for n in (6, 8) for s in seeds),
      "d", "0", "computed (critic probe, now here)")
    C("D6", "fixed contract (N=6's offers): coverage % N=6 / N=8",
      (g("headline", 6, "coverage") * 100, g("fix_other", 8, "coverage") * 100), ".2f", "73.67 / 73.88", "computed (critic probe, now here)")
    C("D6b", "fixed contract: N=8 gain in coverage points (Read-this-first '0.2')",
      (g("fix_other", 8, "coverage") - g("headline", 6, "coverage")) * 100, ".1f", "0.2", "computed (critic probe, now here)")
    C("D6c", "fixed contract: coverage % N=6 / N=8 (Q&A '73.7 against 73.9')",
      (g("headline", 6, "coverage") * 100, g("fix_other", 8, "coverage") * 100), ".1f", "73.7 / 73.9", "computed (critic probe, now here)")
    C("D6d", "fixed contract: accepted % N=6 / N=8", (g("headline", 6, "acc_jobs") * 100, g("fix_other", 8, "acc_jobs") * 100), ".1f",
      "94.7 / 94.7", "computed (critic probe, now here)")
    C("D6e", "fixed contract: N=8 utilisation %", g("fix_other", 8, "util") * 100, ".1f", "41.2", "computed (critic probe, now here)")
    C("D6f", "fixed contract: starts per year N=6 / N=8", (g("headline", 6, "starts"), g("fix_other", 8, "starts")), ",.0f",
      "854 / 2,944", "computed (critic probe, now here)")
    C("D6g", "fixed contract: starts ratio N=8 / N=6 (plan says 'triples')", g("fix_other", 8, "starts") / g("headline", 6, "starts"),
      ".1f", None, "computed")
    C("D6h", "fixed contract: restart break-even N=6 / N=8", (g("headline", 6, "be_restart"), g("fix_other", 8, "be_restart")), ".4f",
      "0.2278 / 0.2320", "computed (critic probe, now here)")
    C("D6i", "context: N=6 on N=8's contract, coverage %", g("fix_other", 6, "coverage") * 100, ".2f", None, "computed (critic probe)")
    C("D7", "named customer only (SRF-size archive, flat): coverage %", g("named", 6, "coverage") * 100, ".1f", "4.8", "computed")
    C("D8", "all-year pin, N=6: pinned h/yr / share of sold h %",
      (g("pin_year", 6, "pin_h"), g("pin_year", 6, "pin_h") / g("pin_year", 6, "sold_h") * 100), ",.1f", None, "computed")
    C("D8b", "all-year pin, N=6: pinned h/yr", g("pin_year", 6, "pin_h"), ",.0f", "7,532", "computed")
    C("D8c", "all-year pin, N=6: share of sold hours %", g("pin_year", 6, "pin_h") / g("pin_year", 6, "sold_h") * 100, ".1f", "25.8",
      "computed")
    C("D8d", "all-year pin, N=6: summer J1 accepted % (from 89.6)", g("pin_year", 6, "acc_j1_summer") * 100, ".1f", "0.0", "computed")
    C("D9", "demo-day pin: coverage % N=6 without -> with",
      (g("headline", 6, "coverage") * 100, g("pin_day", 6, "coverage") * 100), ".3f", "73.675 / 73.673", "computed")
    C("D9b", "demo-day pin: coverage % N=8 without -> with",
      (g("headline", 8, "coverage") * 100, g("pin_day", 8, "coverage") * 100), ".3f", "86.136 / 86.187", "computed")
    for n in (6, 8):
        pk = demo[n]["pick"]
        C(f"D10.{n}", f"demo day N={n}: date, slot, pause, resume, hours run (seed 1)",
          f"{pk[0]} slot {demo[n]['slot']} P{pk[2]:02d} R{pk[3]:02d} {res[('pin_day', n, 1)]['pin_h']:.0f} h", None,
          {6: "2025-07-15 slot 1 P02 R18 8 h", 8: "2025-01-25 slot 7 P14 R19 19 h"}[n], "computed")
    di = H.day_index("2025-01-13")
    idle = [sum(a - b for a, b in zip(res[("headline", n, 1)]["ks_cap"][di * 24:di * 24 + 24],
                                      res[("headline", n, 1)]["ks_on"][di * 24:di * 24 + 24])) for n in (6, 8)]
    C("D11", "2025-01-13 permit-holding idle server-hours N=6 / N=8 (seed 1)", tuple(idle), "d", "22 / 16",
      "computed (was inline command)")

    # ---------------- E. break-even table
    head("E. Break-even: who gets the heat, sold share (case formula)")
    b6 = bs[6]
    C("E1", "homeowner gets heat free: electricity per server-h", b6["elec"] / b6["run_h"], ".4f", "0.3325", "computed")
    C("E2", "heat value at stake CHF/yr N=6 / N=8 (unlimited)", (bs[6]["heat_val"], bs[8]["heat_val"]), ",.0f", "3,306 / 3,860", "computed")
    C("E3", "80% / 50% sold, unsold still run: break-even", (b6["breakeven"] / 0.8, b6["breakeven"] / 0.5), ".3f", "0.283 / 0.452",
      "computed (r2_fleet_economics formula)")
    C("E4", "67% sold, unsold still run: break-even", b6["breakeven"] / SOLD_67, ".4f", "0.3375", "computed (r3_income 5B formula)")

    # ---------------- F. pause physics
    head("F. Pause physics (r2_realism.sim, unlimited demand)")
    idle_b = {n: RL.sim(rows, n, idle_frac=RL.INPUTS["idle_cpu"]) for n in (6, 8)}
    C("F1", "paused servers powered at 17.6% idle: break-even N=6 / N=8", (idle_b[6]["be"], idle_b[8]["be"]), ".4f", "0.2659 / 0.2814",
      "computed; idle share sourced (SPECpower), applying it to this server is an assumption")
    C("F1b", "same: summer server-hours sold N=6 / N=8 ('nothing sold in summer')", (idle_b[6]["run_summer"], idle_b[8]["run_summer"]),
      ".0f", "0 / 0", "computed")
    st = {n: (RL.sim(rows, n)["starts"], RL.sim(rows, n, rule="r1band", band=8, summer_cap=1)["starts"]) for n in (6, 8)}
    C("F2", "starts/yr plain follow / cap + 8 kWh band, N=6 then N=8", st[6] + st[8], ",.0f", "1,732 / 379 / 2,208 / 891", "computed")

    # ---------------- G. reference machine and installed cost
    head("G. Reference server and installed cost (r4_machine; critic extras re-implemented)")
    p_c = M.wall_kw("central")
    C("G1", "wall power kW central (low-high)", (p_c, M.wall_kw("low"), M.wall_kw("high")), ".2f", "0.95 / 0.75 / 1.22",
      "assumption built on sourced 165 W / 320 W maxima")
    a_c, tok_c = M.work_per_server_hour("central")
    a_hpe = M.WHISPER_SAMPLES_S_HPE * M.AUDIO_S_PER_SAMPLE / p_c
    C("G2", "audio-h per kWh: Cisco 6.1-0017 / HPE 6.1-0056 (plan 'about 1,300-1,400')", (a_c, a_hpe), ",.0f", None, "computed")
    C("G2b", "same, rounded to hundreds", (round(a_hpe, -2), round(a_c, -2)), ",.0f", "1,300 / 1,400", "computed")
    C("G3", "Wh per audio-hour, reference server", 1000 / a_c, ".1f", "0.7", "computed")
    C("G4", "HPE 2U box lower than Cisco blade, %", (1 - M.WHISPER_SAMPLES_S_HPE / M.WHISPER_SAMPLES_S) * 100, ".0f", "5",
      "computed from sourced MLPerf rows")
    C("G5", "laptop / reference Wh per audio-h factor (1.3 and 1.5 Wh)", (1.3 / (1000 / a_c), 1.5 / (1000 / a_c)), ".1f", None, "computed")
    C("G5b", "factor, rounded", round(1.5 / (1000 / a_c)), "d", "2", "computed (plan 'about 2')")
    C("G6", "million output tokens per kWh", tok_c / 1e6, ".0f", "36", "computed")
    inst6, boxes6 = M.installed_per_house(6, "central", "central")
    inst8, boxes8 = M.installed_per_house(8, "central", "central")
    C("G7", "installed CHF per 1 kW server (central), exact / to 1,000", (inst6 / 6, round(inst6 / 6, -3)), ",.0f", None, "computed")
    C("G7a", "installed CHF per 1 kW server, rounded to 1,000 (plan 'about 34,000')", round(inst6 / 6, -3), ",.0f", "34,000", "computed")
    C("G7b", "installed CHF per house N=6, exact / to 10,000 (plan 'about 200,000')", (inst6, round(inst6, -4)), ",.0f", None, "computed")
    C("G7d", "installed CHF per house N=6 to 10,000 / N=8 to 1,000", (round(inst6, -4), round(inst8, -3)), ",.0f", "200,000 / 264,000",
      "computed")
    C("G7c", "GPU value per house N=6, CHF to 1,000 (plan 'about 121,000')", round(M.N_GPU * M.CARD["central"] * boxes6, -3), ",.0f",
      "121,000", "computed (critic extra, now here)")
    C("G8", "house integration CHF low / central / high, hundreds", tuple(round(M.HOUSE_INTEGRATION[k], -2) for k in ("low", "central", "high")),
      ",.0f", "10,700 / 14,800 / 20,100", "computed from a proxy (BFE 2015) + assumption")
    lv = {pc: M.list_value("central", pc) for pc in ("low", "central", "high")}
    C("G9", "list value of one server-hour, mix 50/50, low / central / high CHF", tuple(lv[pc][2] for pc in ("low", "central", "high")),
      ".1f", "7.7 / 14.3 / 38.2", "computed (prices sourced in round 3)")
    C("G10", "round-3 two-machine list value", tuple(M.R3_LIST[pc] for pc in ("low", "central", "high")), ".1f", "4.3 / 9.4 / 30.7",
      "computed in round 3 (constant echoed by r4_machine)")
    run6, run8 = bs[6]["run_h"], bs[8]["run_h"]
    op = (b6["elec"] - b6["heat_val"]) / run6
    mixc = lv["central"][2]
    need = lambda inst, run_h, y, i=0.0: op + inst * annuity(i, y) / run_h
    C("G11", "share of list needed N=6 central: operation %", op / mixc * 100, ".1f", "1.6", "computed")
    C("G11b", "N=6 5-y / 8-y payback share % (simple)", (need(inst6, run6, 5) / mixc * 100, need(inst6, run6, 8) / mixc * 100), ".1f",
      "10.7 / 7.3", "computed")
    C("G11c", "N=6 5-y / 8-y share % at 5% interest", (need(inst6, run6, 5, INTEREST) / mixc * 100, need(inst6, run6, 8, INTEREST) / mixc * 100),
      ".1f", "12.1 / 8.6", "computed (critic probe, now here); 5% is an assumption")
    C("G11d", "N=6 5-y / 8-y share % at 67% sold", (need(inst6, run6, 5) / mixc / SOLD_67 * 100, need(inst6, run6, 8) / mixc / SOLD_67 * 100),
      ".1f", "16.0 / 10.9", "computed")
    C("G11e", "N=8 operation / 5-y / 8-y share %", (op / mixc * 100, need(inst8, run8, 5) / mixc * 100, need(inst8, run8, 8) / mixc * 100),
      ".1f", "1.6 / 11.8 / 8.0", "computed")
    C("G11f", "N=8 5-y / 8-y share % at 5% interest", (need(inst8, run8, 5, INTEREST) / mixc * 100, need(inst8, run8, 8, INTEREST) / mixc * 100),
      ".1f", "13.4 / 9.5", "computed (critic probe, now here)")
    C("G11g", "pitch rounding: 5-y / 8-y share; at 5% interest", (need(inst6, run6, 5) / mixc * 100, need(inst6, run6, 8) / mixc * 100,
      need(inst6, run6, 5, INTEREST) / mixc * 100, need(inst6, run6, 8, INTEREST) / mixc * 100), ".0f", "11 / 7 / 12 / 9", "computed")
    rng_lo = need(M.installed_per_house(6, "central", "low")[0], run6, 5) / lv["high"][2] * 100
    rng_hi = need(M.installed_per_house(6, "central", "high")[0], run6, 5) / lv["low"][2] * 100
    C("G11h", "5-y share range, low cost + high price .. high cost + low price %", (rng_lo, rng_hi), ".1f", "3.1 / 25.3", "computed")
    C("G11i", "5-y / 8-y share at LOW price, central cost, 67% sold %",
      (need(inst6, run6, 5) / lv["low"][2] / SOLD_67 * 100, need(inst6, run6, 8) / lv["low"][2] / SOLD_67 * 100), ".0f", "30 / 20",
      "computed")
    exvat = need(inst6 / (1 + M.VAT_CH), run6, 5) / mixc * 100, need(inst8 / (1 + M.VAT_CH), run8, 5) / mixc * 100
    C("G12", "5-y share ex VAT N=6 / N=8 %", exvat, ".1f", "10.0 / 11.0", "computed (critic extra, now here)")
    j1c, j2c = lv["central"][0], lv["central"][1]
    C("G13", "LLM only: 5-y / 8-y share %; at 5%", (need(inst6, run6, 5) / j2c * 100, need(inst6, run6, 8) / j2c * 100,
      need(inst6, run6, 5, INTEREST) / j2c * 100, need(inst6, run6, 8, INTEREST) / j2c * 100), ".1f", "31.7 / 21.5 / 35.8 / 25.6",
      "computed (8-y and 5% by critic probe, now here)")
    C("G13b", "LLM only, pitch rounding (Q&A '32-36%')", (need(inst6, run6, 5) / j2c * 100, need(inst6, run6, 5, INTEREST) / j2c * 100),
      ".0f", "32 / 36", "computed")
    C("G13c", "transcription only: 5-y share %", need(inst6, run6, 5) / j1c * 100, ".1f", "6.4", "computed")
    r3hw = 52329.0 / (5 * run6 / 6)            # r3: laptop-class hardware 52,329 CHF/kW over 5 y of N=6 per-server hours
    C("G14", "round 3 like-for-like: share on the mix basis %", (op + r3hw) / M.R3_LIST["central"] * 100, ".1f", "24.0",
      "computed (critic extra, now here)")
    C("G14b", "round 3 share on the J1-only basis %", (op + r3hw) / 11.189 * 100, ".0f", "20", "computed (r3_income section 7)")
    C("G15", "CHF needed per sold server-h N=6: 5 y / 5 y at 5% / 8 y / 8 y at 5%",
      (need(inst6, run6, 5), need(inst6, run6, 5, INTEREST), need(inst6, run6, 8), need(inst6, run6, 8, INTEREST)), ".2f",
      "1.53 / 1.73 / 1.04 / 1.23", "computed (5% by critic probe, now here)")
    gpus_per_kw = M.N_GPU / p_c
    usd_gpu = lambda chf: chf / gpus_per_kw / M.USD_CHF
    C("G16", "USD per GPU-hour the operator needs: 5 y / 8 y / 5 y at 67% sold",
      (usd_gpu(need(inst6, run6, 5)), usd_gpu(need(inst6, run6, 8)), usd_gpu(need(inst6, run6, 5) / SOLD_67)), ".2f",
      "0.43 / 0.30 / 0.65", "computed (critic extra, now here)")
    net67 = lambda pc, n_inst, run_h, net: OP_SHARE * SOLD_67 * run_h * lv[pc][2] - net
    m6c = net67("central", inst6, run6, b6["elec"] - b6["heat_val"])
    m6l = net67("low", inst6, run6, b6["elec"] - b6["heat_val"])
    m8l = net67("low", inst8, run8, bs[8]["elec"] - bs[8]["heat_val"])
    C("G17", "payback y at 20% share, 67% sold, N=6 central / low (simple)", (payback_years(inst6, m6c, 0), payback_years(inst6, m6l, 0)),
      ".1f", "3.9 / 8.1", "computed")
    C("G17b", "same at 5% interest, N=6 central / low; N=8 low", (payback_years(inst6, m6c, INTEREST), payback_years(inst6, m6l, INTEREST),
      payback_years(inst8, m8l, INTEREST)), ".1f", "4.4 / 10.6 / 12.3", "computed (critic probe, now here)")
    renter = M.N_GPU * 0.41 * M.USD_CHF / p_c
    C("G18", "cheapest rental 0.41 USD/GPU-h: payback y per server, all permit h rented",
      (inst6 / 6) / ((0.8 * renter - op) * run6 / 6), ".1f", "7.0", "computed; 0.41 USD sourced (getdeploying.com), 80% host share sourced (round 2)")
    C("G18b", "renter prices USD/GPU-h cheapest / RunPod / median (echo)", (0.41, 0.72, 0.92), ".2f", "0.41 / 0.72 / 0.92",
      "sourced https://getdeploying.com/gpus/nvidia-rtx-pro-4500 and https://www.runpod.io/gpu-models/rtx-pro-4500-se")
    C("G19", "unlimited demand, half J1: audio-h per day per house, to 1,000 (plan 'about 60,000')",
      round(a_c * run6 * M.MIX_J1 / 365, -3), ",.0f", "60,000", "computed")
    C("G19b", "average Mbit/s at 32 kbit/s", a_c * run6 * M.MIX_J1 / 365 * 3600 * 32e3 / 86400 / 1e6, ".0f", "80",
      "computed; codec rate assumption")
    peak = boxes6 * M.WHISPER_SAMPLES_S * M.AUDIO_S_PER_SAMPLE
    C("G19c", "peak-hour Mbit/s half J1 / all J1", (peak * 0.5 * 32e3 / 1e6, peak * 32e3 / 1e6), ".0f", "135 / 271",
      "computed (critic extra, now here)")
    shares_p = []
    for pcase in ("low", "high"):
        inst_p, _ = M.installed_per_house(6, pcase, "central")
        shares_p.append((op + inst_p / (5 * run6)) / M.list_value(pcase, "central")[2] * 100)
    C("G20", "5-y hardware share across wall power low / high %", tuple(shares_p), ".1f", "10.2 / 11.3", "computed")
    C("G21", "market form: CHF per sold server-h (5 y), rounded", need(inst6, run6, 5), ".1f", "1.5", "computed")
    C("G22", "CPU-only LLM (6.1-0032) at the low price, CHF per server-h", 1227.99 * 3600 * 0.04e-6 * M.USD_CHF, ".3f", "0.148",
      "computed; 1 kW is an assumption; 1,227.99 tok/s sourced (MLPerf v6.1 summary)")
    C("G23", "lowest marketplace host rate, CHF per kW-h (Salad 4090 min x 2 GPU/kW)", 0.128 * 2.0 * M.USD_CHF, ".3f", "0.215",
      "computed; host rate sourced in round 2, 2 GPU per kW assumption")

    # ---------------- H. income on two machine bases (NEW)
    head("H. Computing income scenario: two-machine basis (old) vs reference-server basis (new), headline run")
    for n in (6, 8):
        mo = [H.money(res[("headline", n, s)]) for s in seeds]
        old = {pc: sum(x["income"][pc] for x in mo) / len(mo) for pc in ("low", "central", "high")}
        j1h = sum(res[("headline", n, s)]["sold_t"][0] for s in seeds) / len(seeds)
        j2h = sum(res[("headline", n, s)]["sold_t"][1] for s in seeds) / len(seeds)
        list_ref = {pc: j1h * lv[pc][0] + j2h * lv[pc][1] for pc in ("low", "central", "high")}
        new = {pc: OP_SHARE * list_ref[pc] for pc in list_ref}
        net = g("headline", n, "elec") - g("headline", n, "heat_val")
        inst = inst6 if n == 6 else inst8
        C(f"H1.{n}", f"N={n} OLD two-machine basis (laptop J1, B200-slice J2), income at 20%, central, k CHF/yr",
          old["central"] / 1000, ".1f", {6: "53.6", 8: "62.6"}[n], "computed (r4_headline.money); scenario, not income")
        C(f"H1b.{n}", f"N={n} OLD two-machine basis, low / high, k CHF/yr", (old["low"] / 1000, old["high"] / 1000), ".1f", None,
          "computed (r4_headline.money)")
        C(f"H2.{n}", f"N={n} NEW reference-server income at 20%, low / central / high, k CHF/yr",
          tuple(new[pc] / 1000 for pc in ("low", "central", "high")), ".1f", None,
          "computed (NEW: r4_machine.list_value x headline sold hours per job type); scenario, not income")
        C(f"H3.{n}", f"N={n} sold J1 / J2 server-h (headline)", (j1h, j2h), ",.0f", None, "computed")
        C(f"H4.{n}", f"N={n} list value of sold work, reference server, central, k CHF/yr", list_ref["central"] / 1000, ",.1f", None,
          "computed (NEW)")
        C(f"H5.{n}", f"N={n} share needed under the headline: operation / + install 5 y / 8 y / 5 y at 5% (central)",
          (net / list_ref["central"] * 100, (net + inst / 5) / list_ref["central"] * 100, (net + inst / 8) / list_ref["central"] * 100,
           (net + inst * annuity(INTEREST, 5)) / list_ref["central"] * 100), ".1f", None,
          "computed (NEW; same basis as the share-needed line, but headline sold hours instead of every permit hour)")
        C(f"H6.{n}", f"N={n} audio-hours per year implied by sold J1: two-machine (laptop) / reference server, millions",
          (j1h * ah_per_sh_laptop / 1e6, j1h * a_c / 1e6), ".1f", None, "computed (NEW)")
        mrg = new["central"] - net
        C(f"H7.{n}", f"N={n} NEW basis: margin after electricity-heat, k CHF/yr; payback y simple / at 5% (central)",
          (mrg / 1000, payback_years(inst, mrg, 0), payback_years(inst, mrg, INTEREST)), ".1f", None, "computed (NEW)")
    for n in (6, 8):
        run_h = bs[n]["run_h"]
        C(f"H9.{n}", f"N={n} NEW, exact share-needed basis (every permit hour sold, 50/50 mix, unlimited demand), income at 20%, "
          "low / central / high, k CHF/yr", tuple(OP_SHARE * run_h * lv[pc][2] / 1000 for pc in ("low", "central", "high")), ".1f", None,
          "computed (NEW; r4_machine.list_value x baseline run hours)")
        C(f"H9b.{n}", f"N={n} same at 67% sold (r4_machine section 3 convention), central, k CHF/yr",
          OP_SHARE * SOLD_67 * run_h * lv["central"][2] / 1000, ".1f", None, "computed (equals r4_machine 'income' line)")
    C("H8", "SRF-size archive (1.25 M audio-h) in server-h: laptop rule / reference server", (1.25e6 / ah_per_sh_laptop, 1.25e6 / a_c),
      ",.0f", None, "computed; 1.25 M sourced (srf.ch, URL in plan)")
    C("H8b", "SRF archive at laptop rule: server-h / % of one N=6 house-year", (1.25e6 / ah_per_sh_laptop, 1.25e6 / ah_per_sh_laptop / run6 * 100),
      ",.0f", "1,875 / 6", "computed")
    C("H8c", "two-machine basis: audio-h/yr in the N=6 income line, millions", sum(res[("headline", 6, s)]["sold_t"][0] for s in seeds)
      / len(seeds) * ah_per_sh_laptop / 1e6, ".1f", "9.4", "computed")

    # ---------------- I. temperatures / realism column
    head("I. Realism column, layout A, and radiator houses (r4_tank_layout.sim; critic return-limit probe)")
    uf, r55, r70 = T.SYSTEMS["underfloor 35/28"], T.SYSTEMS["radiator 55/45"], T.SYSTEMS["radiator 70/55"]
    la = {n: T.sim(rows, n, uf, tank_loss=2.80) for n in (6, 8)}
    C("I1", "layout A, underfloor + loss 2.80: coverage % N=6 / N=8", (la[6]["coverage"] * 100, la[8]["coverage"] * 100), ".1f",
      "77.6 / 90.6", "computed")
    C("I1b", "June-August coverage % (layout A)", la[6]["summer"] * 100, ".1f", "82.2", "computed")
    C("I1c", "utilisation % N=6 / N=8 (layout A)", (la[6]["util"] * 100, la[8]["util"] * 100), ".1f", "59.4 / 52.1", "computed")
    lr = {n: T.sim(rows, n, r55, tank_loss=2.80) for n in (6, 8)}
    C("I1d", "break-even, case convention: underfloor N=6 / radiator 55/45 N=6", (la[6]["be_case"], lr[6]["be_case"]), ".4f",
      "0.2293 / 0.2294", "computed")
    C("I1e", "break-even, top-up charged to servers N=6 / N=8", (la[6]["be_charged"], la[8]["be_charged"]), ".3f", "0.234 / 0.234",
      "computed (plan 'about 0.234')")
    tl = {n: B.simulate(rows, n, tank_loss_kwh_day=2.80) for n in (6, 8)}
    C("I2", "tank loss only: coverage change pts N=6 / N=8", tuple((tl[n]["coverage"] - bs[n]["coverage"]) * 100 for n in (6, 8)), ".1f",
      "-0.3 / -0.3", "computed")
    C("I2b", "tank loss only: break-even rise N=6 / N=8", tuple(tl[n]["breakeven"] - bs[n]["breakeven"] for n in (6, 8)), ".4f",
      "0.0030 / 0.0031", "computed")
    dd = {n: B.simulate(rows, n, tank_loss_kwh_day=2.80, dhw_direct_share=37 / 45) for n in (6, 8)}
    C("I3", "no-build-scope proxy: dhw_direct_share=37/45 + loss: coverage % N=6 / N=8", (dd[6]["coverage"] * 100, dd[8]["coverage"] * 100),
      ".2f", "77.72 / 90.74", "computed")
    capk = lambda spread: T.C_KWH_PER_K * spread
    C("I4", "usable buffer kWh: summer / floor 35/28 / 50/40 / 55/45 / 70/55 design hour",
      (capk(30), capk(22), capk(10), capk(5), capk(0)), ".1f", "34.9 / 25.6 / 11.6 / 5.8 / 0.0", "computed")
    C("I5", "hot-water direct share % at 55 / 52 / 60 C setpoint", tuple(T.dhw_share(T.T_TOP, s) * 100 for s in (55, 52, 60)), ".1f",
      "82.2 / 88.1 / 74.0", "computed")
    C("I5b", "electric top-up kWh/yr at 55 C", la[6]["boost_el"], ",.0f", "779", "computed")
    base_uf = T.sim(rows, 6, uf)
    c10, c5 = T.sim(rows, 6, uf, tank_cap=10), T.sim(rows, 6, uf, tank_cap=5)
    C("I6", "usable tank 10 / 5 kWh costs coverage pts (floor heating, N=6)",
      ((base_uf["coverage"] - c10["coverage"]) * 100, (base_uf["coverage"] - c5["coverage"]) * 100), ".1f", "1.0 / 1.6", "computed")
    C("I7", "radiator 55/45 + loss, upper bound (servers keep running): coverage % N=6 / N=8",
      (lr[6]["coverage"] * 100, lr[8]["coverage"] * 100), ".0f", "77 / 90", "computed")
    lo = {n: sim_ret(rows, n, r55, 40.0, tank_loss=2.80) for n in (6, 8)}
    C("I7b", "radiator 55/45 + loss, LOWER bound (servers stop if return > 40 C): coverage % N=6 / N=8",
      (lo[6]["coverage"] * 100, lo[8]["coverage"] * 100), ".0f", "64 / 73", "computed (critic probe, now here)")
    C("I7c", "same, one decimal", (lo[6]["coverage"] * 100, lo[8]["coverage"] * 100), ".1f", "64.3 / 73.0", "computed (critic probe, now here)")
    C("I8", "radiator 55/45: heating hours with return > 40 C (exact)", lo[6]["blocked_h"], ",d", None, "computed (critic probe, now here)")
    C("I8a", "same, to 10 h (plan Q&A 'about 850')", round(lo[6]["blocked_h"], -1), ",d", "850", "computed (critic probe, now here)")
    C("I8b", "radiator 55/45 return temperature at the design hour, C", T.curve(1.0, r55)[1], ".0f", "45", "computed (plan '44-45')")
    up70 = T.sim(rows, 6, r70)
    lo70 = {n: sim_ret(rows, n, r70, 40.0) for n in (6, 8)}
    C("I9", "radiator 70/55: upper bound N=6 / lower bound (ret <= 40 C) N=6 / N=8 %",
      (up70["coverage"] * 100, lo70[6]["coverage"] * 100, lo70[8]["coverage"] * 100), ".0f", "59 / 30 / 31",
      "computed (lower bounds: critic probe, now here); plan words 'at most about 59%', 'about 30%'")
    C("I9b", "same, one decimal (round-4 critic table: 59.2 / 29.5 / 31.2)",
      (up70["coverage"] * 100, lo70[6]["coverage"] * 100, lo70[8]["coverage"] * 100), ".1f", "59.2 / 29.5 / 31.2",
      "computed (critic probe, now here)")
    l45 = T.sim(rows, 6, uf, t_top=45.0)
    r55_50, r55_45 = T.sim(rows, 8, r55), T.sim(rows, 8, r55, t_top=45.0)
    C("I10", "45 C loop: June-August % / radiator 55/45 N=8 loss in pts", (l45["summer"] * 100, (r55_50["coverage"] - r55_45["coverage"]) * 100),
      ".1f", "71.1 / 10.6", "computed")
    dmax = 0.0
    for n in (6, 8):
        for sysd in (uf, r55):
            dmax = max(dmax, (T.sim(rows, n, sysd)["coverage"] - T.sim(rows, n, sysd, floor_mode="supply")["coverage"]) * 100)
    C("I12", "higher space-heating draw floor (mixed tank): largest coverage loss, pts", dmax, ".1f", None,
      "computed (plan '<= 0.2 points')")
    C("I13", "layout A temperatures: buffer top C / fresh-water preheat C", (T.T_TOP, T.T_TOP - T.INPUTS["fws_approach_k"]), ".0f", "50 / 47",
      "computed from sourced 55 C outlet (NVIDIA blog) and 5 K / 3 K approaches (Lenovo / suissetec; interpretation)")
    ac = {n: RL.sim(rows, n, boost=("electric", RL.INPUTS["t_cold_c"], 60)) for n in (6, 8)}
    C("I11", "air-cooled, no direct hot water: coverage % N=6 / N=8", (ac[6]["coverage"] * 100, ac[8]["coverage"] * 100), ".1f",
      "70.5 / 81.7", "computed")

    # ---------------- J. forecast and misses
    head("J. Forecast error and round-2 no-guard miss rate (r2_deadline_sim)")
    b = R.base()
    C("J1", "ECMWF ifs025 RMSE K, day 1 / day 7", (R.err_stats(b["ifs"][1], b["act_t"])[2], R.err_stats(b["ifs"][7], b["act_t"])[2]), ".2f",
      "1.16 / 2.85", "computed from archived forecasts (analysis/r2_data/prev_ecmwf_ifs025.csv)")
    C("J1b", "ifs025 day-1 bias K", R.err_stats(b["ifs"][1], b["act_t"])[0], "+.2f", "+0.29", "computed")
    if "--skip-r2" not in argv:
        r2s = list(range(1, 6))
        out = dict(pmap(task_r2, [(n, s) for n in (6, 8) for s in r2s], procs))
        for n in (6, 8):
            v = [out[(n, s)]["missed"] * 100 for s in r2s]
            C(f"J2.{n}", f"N={n} saturating, ifs025, NO guard, no partner, 2025, seeds 1-5: missed % mean / min / max",
              (sum(v) / len(v), min(v), max(v)), ".3f", {6: "0.146 / 0.097 / 0.267", 8: "0.294 / 0.160 / 0.386"}[n],
              "computed (round-2 run); plan's '0.1-0.6%' upper end came from 2024 runs by the round-2 critic, not in a script")
    C("J3", "named-customer volume vs shaped100 contract N=6 %", named_flat / yr(rt("shaped100", 6)) * 100, ".1f", None, "computed")

    # ---------------- K. small derived Q&A numbers
    head("K. Small derived Q&A numbers")
    C("K1", "vendor sizing 5-20% of design load = servers (10 kW design / 0.8 kW per server)", (0.05 * 10 / 0.8, 0.20 * 10 / 0.8), ".1f",
      "0.6 / 2.5", "computed from sourced 5-20% (URL in r4-plan-detail.md section L)")
    C("K2", "heat receipt: J2 (4 server-h) heat kWh / person-days of case hot water", (4 * B.REC * B.P_EL, 4 * B.REC * B.P_EL / 3.0), ".2f",
      "3.20 / 1.07", "computed; job size assumption")
    C("K3", "laptop J1 energy Wh per audio-hour used downstream (r3_income.E_PROBE)", I.E_PROBE, ".1f", "1.5",
      "measured 2026-11-21 by r3_whisper_energy_probe.py, NOT re-run here (plan range 1.3-1.5)")
    C("K4", "J2 input tokens billed per output token", I.IN_PER_OUT, ".0f", "6", "assumption (r3_income.IN_PER_OUT)")
    import r2_fleet_economics as FE
    C("K6", "marketplace host share (Salad 4090 host rate / renter price, lowest tier)", FE.SALAD_4090["min"] / 0.160, ".2f", "0.80",
      "computed from rates sourced in round 2 (r2-host-income-hardware.md)")
    C("K5", "MLPerf throughput: whisper Cisco / HPE samples/s; llama tok/s", (M.WHISPER_SAMPLES_S, M.WHISPER_SAMPLES_S_HPE, M.LLAMA_TOK_S),
      ".2f", "61.10 / 58.08 / 9518.66", "sourced (MLPerf v6.1 loadgen logs, URLs in r4-reference-machine.md section 2.1)")

    # ---------------- summary
    n_m = sum(1 for r in RECORDS if r[5] == "MATCH")
    n_d = [r for r in RECORDS if r[5] == "DIFF"]
    n_c = sum(1 for r in RECORDS if r[5] == "context")
    head("Summary")
    print(f"  {len(RECORDS)} lines: {n_m} MATCH, {len(n_d)} DIFF, {n_c} context (not quoted in the plan or quoted only in words)")
    for r in n_d:
        print(f"  DIFF [{r[0]}] {r[1]}: script {r[2]} vs plan {r[3]}")
    if "--md" in argv:
        print("\n| id | label | value (script) | plan | status | match |\n|---|---|---|---|---|---|")
        for r in RECORDS:
            print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |")


if __name__ == "__main__":
    main()
