"""Independent oracle check for the team scheduler (round 8, Sat 21 Nov 2026).

NOT the team scheduler and NOT a port of the analysis scripts. Every rule here is
re-derived from the written case and plan text, without importing or copying any
function from analysis/*.py (no step_permit, forward_fail, simulate, run, ...):

  case formulas      docs/case-brief.md  (demand formula, 1 kW, 80 %, 35 kWh,
                     price, heat value = price / 2.5, utilisation, break-even)
  price              data/raw/elcom_iwb_H4_2025_2026.json (2026, Basel, total)
  demand profile     data/reference_house_2025_hourly.csv (temperatures re-checked)
  offers             analysis/r4_offers_shaped100_seed1.csv (shaped100, seed 1)
  scheduler rules    docs/research/r3-one-scheduler-scope.md section (a), R1-R7
                     ("expire", "permit", "cap + band", "admission dry run",
                     "EDF assign"), docs/overnight.md "Scheduler scope"

Run:   python3 analysis/r8_oracle_check.py            (about 10 s wall on several cores)
       python3 analysis/r8_oracle_check.py --quick    (sections 1-4 only, < 1 s)
       python3 analysis/r8_oracle_check.py --offers-long FILE --n 6
              (team's own offers, one row per offer: hour,server_hours,deadline_h)

Standard library only, no network, writes no file.
"""
import csv
import json
import math
import sys
import time
from bisect import insort
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPS = 1e-9

# ---------------------------------------------------------------- case constants
P_SERVER_KW = 1.0     # "One rack server uses 1 kW of electricity"
RECOVERY = 0.8        # "80% of that heat can be recovered"
TANK_KWH = 35.0       # "about 35 kWh usable capacity ... no losses"
COP_REF = 2.5         # "Value it at the electricity price / 2.5"
J1 = (0.5, 24)        # plan: J1 0.5 server-h, 24 h deadline   (assumption in plan)
J2 = (4.0, 168)       # plan: J2 4 server-h, 168 h deadline    (assumption in plan)
BAND_KWH = 8.0        # plan: cap + 8 kWh band, decided at 10:15
HORIZON = 168         # plan: fc_demand[0..167]

# Deliberate port slips, used only by section 8 to print their fingerprints.
SLIP = dict(band_literal=False, heat_from_permit=False, deadline_shift=0, fifo=False)


def price_chf_per_kwh():
    """ElCom 2026, IWB, Basel, H4, 'total' in Rp/kWh -> CHF/kWh."""
    obs = json.loads((ROOT / "data/raw/elcom_iwb_H4_2025_2026.json").read_text())
    rows = [o for o in obs["data"]["observations"]
            if o["period"] == "2026" and o["municipalityLabel"] == "Basel"]
    assert len(rows) == 1, rows
    return rows[0]["total"] / 100.0


PRICE = price_chf_per_kwh()
HEAT_VALUE = PRICE / COP_REF


# ---------------------------------------------------------------- inputs
def load_profile():
    rows = list(csv.DictReader(open(ROOT / "data/reference_house_2025_hourly.csv")))
    temps = [float(r["temperature_2m_c"]) for r in rows]
    sh_csv = [float(r["space_heating_kwh"]) for r in rows]
    dhw = [float(r["hot_water_kwh"]) for r in rows]
    days = [r["time_local"][:10] for r in rows]
    return rows, temps, sh_csv, dhw, days


def demand_from_case_formula(temps, days):
    """Case brief: max(0, 10 kW x (20 - T) / 25.6) on heating days (day mean < 12 C)."""
    by_day = {}
    for d, t in zip(days, temps):
        by_day.setdefault(d, []).append(t)
    mean = {d: sum(v) / len(v) for d, v in by_day.items()}
    sh = [max(0.0, 10.0 * (20.0 - t) / 25.6) if mean[d] < 12.0 else 0.0
          for d, t in zip(days, temps)]
    return sh, sum(1 for m in mean.values() if m < 12.0)


def load_offers(n):
    """One list per hour of (type, rem_h, deadline_hour) in arrival order.
    The CSV gives counts per type and which type came first in that hour."""
    out = []
    with open(ROOT / "analysis/r4_offers_shaped100_seed1.csv") as f:
        lines = [l for l in f if not l.startswith("#")]
    for r in csv.DictReader(lines):
        h = int(r["hour"])
        a, b, first = int(r[f"n{n}_j1"]), int(r[f"n{n}_j2"]), r[f"n{n}_first"]
        sh_ = SLIP["deadline_shift"]
        j1 = [("J1", J1[0], h + J1[1] + sh_)] * a
        j2 = [("J2", J2[0], h + J2[1] + sh_)] * b
        out.append(j1 + j2 if first == "J1" else j2 + j1)
    assert len(out) == 8760
    return out


def load_offers_long(path):
    """Team offer file, one row per offer: hour,server_hours,deadline_h (header required).
    Lets the team run this independent model on its own job types (e.g. embed / rerank)."""
    out = [[] for _ in range(8760)]
    for r in csv.DictReader(l for l in open(path) if not l.startswith("#")):
        h, rem, dl = int(r["hour"]), float(r["server_hours"]), int(round(float(r["deadline_h"])))
        out[h].append((f"{rem:g}h/{dl}h", rem, h + dl))
    return out


# ---------------------------------------------------------------- re-derived rules
def permit(n, soc, d, space_heat, holding, cap_band):
    """R2 heat permit (+ R3 cap and band). Returns (k, holding).
    R2: k = min(N, floor((demand + tank - soc) / 0.8)).
    R3 cap: at most 1 server when space heating = 0.
    R3 band: "after the tank is full, k = 0 until soc <= tank - band or soc < demand".
    'Full' is read as: the follow permit has fallen to 0 (less than one server's 0.8 kWh
    of room left). Round 8 found that the literal reading (soc >= 35 kWh) does NOT
    reproduce the plan's 379 / 891 starts; see docs/research/r8-scheduler-in-repo.md."""
    q = RECOVERY * P_SERVER_KW
    kmax = min(n, int((d + TANK_KWH - soc) / q + EPS))
    if cap_band and space_heat <= 0.0:
        kmax = min(kmax, 1)
    kmax = max(kmax, 0)
    if not cap_band:
        return kmax, holding
    if holding and (soc <= TANK_KWH - BAND_KWH + EPS or soc < d):
        holding = False
    if holding:
        return 0, holding
    if kmax == 0 and not SLIP["band_literal"]:
        holding = True
    return kmax, holding


def tank_step(soc, heat, d):
    """Lossless tank: heat first serves demand, the rest charges the tank, overflow dumped."""
    avail = soc + heat
    used = min(d, avail)
    soc = avail - used
    dump = max(0.0, soc - TANK_KWH)
    return soc - dump, used, dump


def edf_fill(queue, k):
    """R5: jobs sorted by deadline, each gets at most 1 server-hour this hour,
    until k server-hours are used. queue items: [deadline, seq, rem]. Returns work."""
    cap = float(k)
    work = 0.0
    for job in (sorted(queue, key=lambda j: j[1]) if SLIP["fifo"] else queue):
        if cap <= EPS:
            break
        x = min(job[2], 1.0, cap)
        job[2] -= x
        cap -= x
        work += x
    return work


def expire(queue, t):
    """R1: deadline - t < ceil(rem) -> missed. Returns (kept, n_missed)."""
    kept = [j for j in queue if j[0] - t >= math.ceil(j[2] - EPS)]
    return kept, len(queue) - len(kept)


def dry_run_ok(queue, t0, soc, holding, n, dem, sh, cap_band, wrap):
    """R4: roll R1+R2+R3+R5 forward up to 168 h on the forecast (here: recorded demand);
    True if no job in the queue is forecast to miss."""
    q = [j[:] for j in queue]
    for L in range(HORIZON):
        t = t0 + L
        if not q:
            return True
        if t >= 8760 and not wrap:
            return True                  # beyond the year: nothing to check against
        i = t % 8760
        for j in q:
            if j[0] - t < math.ceil(j[2] - EPS):
                return False
        k, holding = permit(n, soc, dem[i], sh[i], holding, cap_band)
        w = edf_fill(q, k)
        soc, _, _ = tank_step(soc, RECOVERY * w, dem[i])
        q = [j for j in q if j[2] > EPS]
    return all(j[0] - (t0 + HORIZON) >= math.ceil(j[2] - EPS) for j in q) if q else True


def planned_permits(n, soc, holding_after_now, k_now, dem, sh, t0, cap_band, wrap):
    """Reading B of R4 (the one the analysis oracle uses, found in round 8):
    plan the next 168 permits as if EVERY permitted server ran, i.e. the tank is
    charged by k x 0.8 kWh in the plan whatever the queue holds."""
    cf = [k_now]
    s = soc + k_now * RECOVERY
    s -= min(dem[t0 % 8760], s)
    holding = holding_after_now
    for L in range(1, HORIZON):
        t = t0 + L
        if t >= 8760 and not wrap:
            cf.append(0)
            continue
        i = t % 8760
        k, holding = permit(n, s, dem[i], sh[i], holding, cap_band)
        s += k * RECOVERY
        s -= min(dem[i], s)
        cf.append(k)
    return cf


def edf_on_capacity_fails(queue, t0, cf):
    """EDF on a fixed capacity profile, at most 1 server-hour per job per hour,
    a job may work in hour t only while t < deadline. Returns the unfinished jobs."""
    rem = [j[2] for j in queue]
    for L, c in enumerate(cf):
        t = t0 + L
        c = float(c)
        for x, j in enumerate(queue):
            if c <= EPS:
                break
            if rem[x] > EPS and j[0] > t:
                step = min(rem[x], 1.0, c)
                rem[x] -= step
                c -= step
    return [queue[x] for x in range(len(queue)) if rem[x] > EPS]


def admit_reading_b(queue, new_by_type, t0, cf):
    """Stage 1: per job type (in the hour's arrival order) accept as many as the
    cumulative planned capacity minus work already due allows (deadline-wise slack).
    Stage 2: EDF check on the same capacity; drop failing new jobs (newest if none
    of the failing ones is new) until nothing fails. Returns (queue, accepted)."""
    max_off = max([j[0] - t0 for j in queue] + [js[0][0] - t0 for js in new_by_type.values()] + [HORIZON])
    size = max_off + 2
    W = [0.0] * size
    for j in queue:
        W[j[0] - t0] += j[2]
    slack, cum, w = [], 0.0, 0.0
    for L in range(size):
        w += W[L]
        slack.append(cum - w)
        if L < HORIZON:
            cum += cf[L]
    new = []
    for typ, jobs in new_by_type.items():      # job types in the hour's arrival order
        rem, dl_off = jobs[0][2], jobs[0][0] - t0
        room = min(slack[dl_off:])
        k = max(0, min(len(jobs), int(room / rem + EPS)))
        for L in range(dl_off, size):
            slack[L] -= k * rem
        new.extend(jobs[:k])
    q = sorted(queue + new, key=lambda j: (j[0], j[1]))
    while new:
        failing = edf_on_capacity_fails(q, t0, cf)
        if not failing:
            break
        fail_ids = {id(j) for j in failing}
        pick = next((j for j in failing if any(j is x for x in new)), None) or new[-1]
        new = [x for x in new if x is not pick]
        q = [x for x in q if x is not pick]
    return q, len(new)


def year_with_jobs(n, dem, sh, offers, admission, cap_band=True, wrap=True, reading="A"):
    soc, holding = 0.0, False
    queue, seq = [], 0
    offered = accepted = done = missed = 0
    run_h = sold_h = used = dumped = permit_h = 0.0
    starts, k_run_prev = 0, 0
    for t in range(8760):
        queue, m = expire(queue, t)
        missed += m
        new = offers[t]
        offered += len(new)
        cand = []
        for typ, rem, dl in new:
            seq += 1
            cand.append([dl, seq, rem])
        holding_pre = holding
        k, holding = permit(n, soc, dem[t], sh[t], holding, cap_band)
        if admission and cand and reading == "B":
            cf = planned_permits(n, soc, holding, k, dem, sh, t, cap_band, wrap)
            by_type = {}
            for (typ, _, _), j in zip(new, cand):
                by_type.setdefault(typ, []).append(j)
            queue, acc_now = admit_reading_b(queue, by_type, t, cf)
            accepted += acc_now
            cand = []
        elif admission and cand:
            take = len(cand)
            while take > 0:
                trial = list(queue)
                for j in cand[:take]:
                    insort(trial, j)
                if dry_run_ok(trial, t, soc, holding_pre, n, dem, sh, cap_band, wrap):
                    break
                take -= 1
            cand = cand[:take]
        for j in cand:
            insort(queue, j)
        accepted += len(cand)
        permit_h += k
        w = edf_fill(queue, k)
        k_run = math.ceil(w - EPS)           # servers actually switched on this hour
        starts += max(0, k_run - k_run_prev)
        k_run_prev = k_run
        on_h = k if SLIP["heat_from_permit"] else w   # slip: unsold permits still run
        soc, u, dmp = tank_step(soc, RECOVERY * on_h, dem[t])
        if SLIP["band_literal"] and cap_band and soc >= TANK_KWH - 1e-6:
            holding = True
        run_h += on_h
        sold_h += w
        used += u
        dumped += dmp
        before = len(queue)
        queue = [j for j in queue if j[2] > EPS]
        done += before - len(queue)
    # jobs still queued with a deadline inside the year are already expired above;
    # open = jobs queued at year end (their deadline is in 2026)
    open_end = len(queue)
    open_dl_in_year = sum(1 for j in queue if j[0] < 8760)
    return dict(n=n, admission=admission, offered=offered, accepted=accepted, done=done,
                missed=missed, open=open_end, open_dl_in_year=open_dl_in_year,
                run_h=run_h, sold_h=sold_h, used=used, dumped=dumped, soc_end=soc, permit_h=permit_h,
                starts=starts)


def year_unlimited(n, dem, sh, cap_band=False, always=False):
    """Every permit hour filled and sold (the declared 'unlimited jobs' upper line)."""
    soc, holding = 0.0, False
    run_h = used = dumped = 0.0
    starts, kp = 0, 0
    for t in range(8760):
        if always:
            k = n
        else:
            k, holding = permit(n, soc, dem[t], sh[t], holding, cap_band)
        starts += max(0, k - kp)
        kp = k
        soc, u, d = tank_step(soc, RECOVERY * k, dem[t])
        run_h += k
        used += u
        dumped += d
    return dict(n=n, run_h=run_h, used=used, dumped=dumped, soc_end=soc, starts=starts)


def money(run_h, used, sold_h=None):
    sold_h = run_h if sold_h is None else sold_h
    elec = run_h * P_SERVER_KW * PRICE
    heat = used * HEAT_VALUE
    return elec, heat, (elec - heat) / sold_h if sold_h else float("nan")


# ---------------------------------------------------------------- oracle values (plan text)
# Copied by hand from docs/overnight.md, "Key numbers", Sat 21 Nov ~12:30.
ORACLE = {
    "unlimited": {6: dict(coverage=79.6, util=59.1, run_h=31067, elec=10330, heat=3306, be=0.2261),
                  8: dict(coverage=92.9, util=51.8, run_h=36281, elec=12063, heat=3860, be=0.2261),
                  1: dict(coverage=19.5, util=87.1, run_h=7629, elec=2537, heat=812, be=0.2261),
                  13: dict(coverage=100.0, dumped=59839, util=100.0, run_h=113880, elec=37865,
                           heat=4154, be=0.2960)},
    "starts_capband_unlimited": {6: 379, 8: 891},
    "coverage_capband_unlimited": {6: 79.55, 8: 92.94},
    "no_admission": {6: dict(missed=857, closed=33640), 8: dict(missed=1307, closed=39222)},
    "offers_total": {6: 33676, 8: 39244},
    "check_run": {6: dict(missed=0, closed=32174, acc=95.6, coverage=73.53, util=54.61, be=0.2261),
                  8: dict(missed=0, closed=37023, acc=94.4, coverage=86.10, util=47.96, be=0.2261)},
    "total_demand": 31231, "space_heat": 26851, "heating_days": 206,
}


def cmp(label, mine, oracle, tol):
    ok = abs(mine - oracle) <= tol
    print(f"  {'MATCH' if ok else 'DIFF '} {label:<48} independent {mine:>12,.4f}   plan {oracle:>12,.4f}"
          f"   (tol {tol:g})")
    return ok


def _job_run(args):
    n, admission, wrap, reading = args[:4]
    SLIP.update(band_literal=False, heat_from_permit=False, deadline_shift=0, fifo=False)
    if len(args) > 4 and args[4]:
        SLIP.update(args[4])
    offers_path = args[5] if len(args) > 5 else None
    _, temps, sh_csv, dhw, days = load_profile()
    dem = [a + b for a, b in zip(sh_csv, dhw)]
    t0 = time.time()
    offers = load_offers_long(offers_path) if offers_path else load_offers(n)
    r = year_with_jobs(n, dem, sh_csv, offers, admission, cap_band=True, wrap=wrap, reading=reading)
    r["secs"] = time.time() - t0
    r["wrap"] = wrap
    r["reading"] = reading
    return r


def offers_resliced(n, types, seed=1):
    """ILLUSTRATION ONLY (section 9): keep the shaped100 file's offered server-hours per hour,
    re-slice them into other job types (equal shares of work), Poisson counts, random.Random(seed).
    types: list of (label, server_hours, deadline_h)."""
    import random
    rng = random.Random(seed)
    base = load_offers(n)
    out = []
    for h, offs in enumerate(base):
        work = sum(rem for _, rem, _ in offs)
        hour = []
        for lab, rem, dl in types:
            lam = work / len(types) / rem
            # Poisson by inversion (stdlib only)
            k, p, u = 0, math.exp(-lam), rng.random()
            c = p
            while u > c:
                k += 1
                p *= lam / k
                c += p
            hour += [(lab, rem, h + dl)] * k
        out.append(hour)
    return out


def _team_types_run(args):
    n, admission, reading = args
    _, temps, sh_csv, dhw, days = load_profile()
    dem = [a + b for a, b in zip(sh_csv, dhw)]
    offs = offers_resliced(n, [("embed", 0.90, 48), ("rerank", 0.91, 4)])
    return year_with_jobs(n, dem, sh_csv, offs, admission, cap_band=True, wrap=True, reading=reading)


def team_offers_mode(path, n):
    """python3 analysis/r8_oracle_check.py --offers-long FILE --n N"""
    _, temps, sh_csv, dhw, days = load_profile()
    total = sum(a + b for a, b in zip(sh_csv, dhw))
    jobs = [(n, False, True, "-", {}, path), (n, True, True, "A", {}, path), (n, True, True, "B", {}, path)]
    with ProcessPoolExecutor(max_workers=3) as ex:
        res = list(ex.map(_job_run, jobs))
    print(f"Independent model on {path}, N={n}, cap + 8 kWh band, recorded demand as forecast")
    print("  stage                 offered accepted   missed of closed  open  coverage  util   sold-h  dumped  BE      BE15")
    for r, lab in zip(res, ("no admission", "check run, reading A", "check run, reading B")):
        closed = r["done"] + r["missed"]
        el, ht, be = money(r["run_h"], r["used"], r["sold_h"])
        be15 = (el - ht) / (r["sold_h"] - 0.25 * r["starts"])
        print(f"  {lab:<21} {r['offered']:7,} {r['accepted']:8,} {r['missed']:8,} of {closed:7,} {r['open']:5}"
              f"  {100*r['used']/total:6.2f}%  {100*r['run_h']/(n*8760):5.2f}%  {r['sold_h']:7.0f}  {r['dumped']:6.1f}"
              f"  {be:.4f}  {be15:.4f}")


def main():
    if "--offers-long" in sys.argv:
        path = sys.argv[sys.argv.index("--offers-long") + 1]
        n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 6
        team_offers_mode(path, n)
        return
    quick = "--quick" in sys.argv
    diffs = []
    rows, temps, sh_csv, dhw, days = load_profile()
    dem = [a + b for a, b in zip(sh_csv, dhw)]
    total = sum(dem)

    print("== 1. Inputs re-derived from the case text ==")
    print(f"  price: ElCom 2026 IWB Basel H4 total = {PRICE*100:.2f} Rp/kWh = {PRICE:.4f} CHF/kWh;"
          f" heat value = price / {COP_REF} = {HEAT_VALUE:.4f} CHF/kWh")
    sh_re, hdays = demand_from_case_formula(temps, days)
    print(f"  space heating from temperatures (case formula): {sum(sh_re):,.1f} kWh on {hdays} heating days;"
          f" CSV column {sum(sh_csv):,.1f} kWh; max abs hourly diff {max(abs(a-b) for a,b in zip(sh_re, sh_csv)):.5f}"
          f" (CSV rounded to 4 decimals)")
    print(f"  hot water {sum(dhw):,.0f} kWh = {sum(dhw)/365:.2f} kWh/day; total demand {total:,.1f} kWh")
    for lab, mine, orc, tol in (("total demand kWh", total, ORACLE["total_demand"], 1),
                                ("space heating kWh", sum(sh_csv), ORACLE["space_heat"], 1),
                                ("heating days", hdays, ORACLE["heating_days"], 0)):
        if not cmp(lab, mine, orc, tol):
            diffs.append(lab)
    print(f"  case cross-check: one server-day = 24 x {P_SERVER_KW} x {RECOVERY} = {24*P_SERVER_KW*RECOVERY:.1f} kWh"
          f" (case: 19.2); coldest-hour servers = 10 / 0.8 = {10/(P_SERVER_KW*RECOVERY):.1f} (case: 12.5)")

    print("\n== 2. Unlimited demand (every permit hour sold), follow, no cap/band ==")
    print("  N   coverage   dumped   util    srv-h    elec CHF  heat CHF  BE CHF/h   used+dump+soc_end-heat")
    for n in (1, 6, 8, 13):
        r = year_unlimited(n, dem, sh_csv, always=(n == 13))
        elec, heat, be = money(r["run_h"], r["used"])
        ident = r["used"] + r["dumped"] + r["soc_end"] - RECOVERY * r["run_h"]
        cov, util = 100 * r["used"] / total, 100 * r["run_h"] / (n * 8760)
        print(f"  {n:<3} {cov:7.2f}%  {r['dumped']:7.0f}  {util:6.2f}%  {r['run_h']:7.0f}  {elec:9.0f} {heat:9.0f}"
              f"  {be:.4f}     {ident:+.2e}")
        o = ORACLE["unlimited"][n]
        for lab, mine, orc, tol in ((f"N={n} coverage %", cov, o["coverage"], 0.05),
                                    (f"N={n} utilisation %", util, o["util"], 0.05),
                                    (f"N={n} server-h", r["run_h"], o["run_h"], 0.5),
                                    (f"N={n} electricity CHF", elec, o["elec"], 0.5),
                                    (f"N={n} heat value CHF", heat, o["heat"], 0.5),
                                    (f"N={n} break-even CHF/h", be, o["be"], 0.00005)):
            if not cmp(lab, mine, orc, tol):
                diffs.append(lab)
        if "dumped" in o and not cmp(f"N={n} dumped kWh", r["dumped"], o["dumped"], 0.5):
            diffs.append(f"N={n} dumped")
    print(f"  break-even identity (never dump, lossless): PRICE - {RECOVERY} x PRICE/{COP_REF} ="
          f" {PRICE - RECOVERY*HEAT_VALUE:.4f} + {HEAT_VALUE:.4f} x soc_end / sold_h")

    print("\n== 3. Unlimited demand with cap + 8 kWh band ==")
    for n in (6, 8):
        r0 = year_unlimited(n, dem, sh_csv, cap_band=False)
        r = year_unlimited(n, dem, sh_csv, cap_band=True)
        cov = 100 * r["used"] / total
        print(f"  N={n}: starts follow {r0['starts']}, cap+band {r['starts']}; coverage {cov:.2f}%; srv-h {r['run_h']:.0f}")
        if not cmp(f"N={n} starts cap+band (unlimited)", r["starts"], ORACLE["starts_capband_unlimited"][n], 0):
            diffs.append(f"N={n} starts cap+band")
        if not cmp(f"N={n} coverage cap+band (unlimited) %", cov, ORACLE["coverage_capband_unlimited"][n], 0.005):
            diffs.append(f"N={n} coverage cap+band")

    print("\n== 4. Offer file ==")
    for n in (6, 8):
        offs = load_offers(n)
        tot = sum(len(o) for o in offs)
        work = sum(rem for o in offs for _, rem, _ in o)
        nj1 = sum(1 for o in offs for typ, _, _ in o if typ == "J1")
        print(f"  N={n}: {tot:,} offers ({nj1:,} J1, {tot-nj1:,} J2), offered work {work:,.1f} server-h"
              f" = {100*work/(n*8760):.1f}% of N x 8760; {tot/365:.1f} jobs/day")
        if not cmp(f"N={n} offers in file", tot, ORACLE["offers_total"][n], 0):
            diffs.append(f"N={n} offers")
    if quick:
        print("\n--quick: sections 5-6 skipped")
        print(f"\nDIFF lines: {len(diffs)}  {diffs}")
        return

    print("\n== 5. Year with jobs: EDF + expire (+ admission dry run on recorded demand), cap + 8 kWh band ==")
    t0 = time.time()
    jobs = [(6, False, True, "-"), (8, False, True, "-"),
            (6, True, True, "A"), (8, True, True, "A"),
            (6, True, True, "B"), (8, True, True, "B"),
            (6, True, False, "B"), (8, True, False, "B")]
    with ProcessPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(_job_run, jobs))
    print(f"  ({time.time()-t0:.0f} s wall)")
    print("  reading A = plan the queue's own execution 168 h ahead (literal R4 text);"
          " reading B = plan permits as if all are used, slack count + EDF check")
    print("  N rd adm  wrap  offered accepted  acc%   done  missed  open  closed  coverage  util    sold-h  permit-h"
          "  elec   heat   BE      BE15    starts")
    for r in res:
        n = r["n"]
        closed = r["done"] + r["missed"]
        cov, util = 100 * r["used"] / total, 100 * r["run_h"] / (n * 8760)
        elec, heat, be = money(r["run_h"], r["used"], r["sold_h"])
        be15 = (elec - heat) / (r["sold_h"] - 0.25 * r["starts"])
        r.update(be15=be15, closed=closed, cov=cov, util=util, elec=elec, heat=heat, be=be)
        print(f"  {n} {r['reading']:<2} {'yes' if r['admission'] else 'no ':<4} {'yes' if r['wrap'] else 'no ':<4} {r['offered']:7,} {r['accepted']:8,}"
              f" {100*r['accepted']/r['offered']:5.1f} {r['done']:6,} {r['missed']:6,} {r['open']:5} {closed:7,}"
              f"  {cov:6.2f}%  {util:5.2f}%  {r['run_h']:7.0f}  {r['permit_h']:7.0f}  {elec:5.0f}  {heat:5.0f}"
              f"  {be:.4f}  {be15:.4f}  {r['starts']:5}   [{r['secs']:.0f} s]")

    print("\n== 6. Compare with the plan's oracle table ==")
    for r in res:
        n = r["n"]
        if not r["admission"]:
            o = ORACLE["no_admission"][n]
            for lab, mine, orc, tol in ((f"N={n} no admission: missed", r["missed"], o["missed"], 0),
                                        (f"N={n} no admission: closed", r["closed"], o["closed"], 0)):
                if not cmp(lab, mine, orc, tol):
                    diffs.append(lab)
        elif r["wrap"]:
            o = ORACLE["check_run"][n]
            print(f"  -- reading {r['reading']} --" + ("" if r["reading"] == "B" else
                  "  (literal R4 text; differences are a different admission rule, not a bug: not counted)"))
            for lab, mine, orc, tol in ((f"N={n} check run: missed", r["missed"], o["missed"], 0),
                                        (f"N={n} check run: closed (denominator)", r["closed"], o["closed"], 0),
                                        (f"N={n} check run: accepted %", 100 * r["accepted"] / r["offered"], o["acc"], 0.05),
                                        (f"N={n} check run: coverage %", r["cov"], o["coverage"], 0.005),
                                        (f"N={n} check run: utilisation %", r["util"], o["util"], 0.005),
                                        (f"N={n} check run: break-even CHF/h", r["be"], o["be"], 0.00005)):
                if not cmp(lab, mine, orc, tol) and r["reading"] == "B":
                    diffs.append(lab)

    print("\n== 7. Invariants the team printout must satisfy (checked here on the independent run) ==")
    unl = {n: year_unlimited(n, dem, sh_csv, cap_band=True) for n in (6, 8)}
    for r in res:
        if not (r["admission"] and r["wrap"]):
            continue
        print(f"  -- reading {r['reading']} --")
        n = r["n"]
        u = unl[n]
        checks = [
            ("I1 coverage <= unlimited cap+band coverage, same N", r["used"] <= u["used"] + EPS),
            ("I2 dumped == 0 (never-dump permit)", r["dumped"] < 1e-6),
            ("I3 sold h <= permit h <= N x 8760", r["run_h"] <= r["permit_h"] + EPS <= n * 8760 + EPS),
            ("I4 accepted == done + missed + open", r["accepted"] == r["done"] + r["missed"] + r["open"]),
            ("I5 used + dumped + soc_end == 0.8 x sold h", abs(r["used"] + r["dumped"] + r["soc_end"] - RECOVERY * r["run_h"]) < 1e-6),
            ("I6 break-even == 0.2261 + 0.133 x soc_end / sold h", abs(r["be"] - (PRICE - RECOVERY * HEAT_VALUE + HEAT_VALUE * r["soc_end"] / r["run_h"])) < 1e-9),
            ("I7 missed == 0 on the check run", r["missed"] == 0),
        ]
        for lab, ok in checks:
            print(f"  N={n} {'PASS' if ok else 'FAIL'}  {lab}")
            if not ok:
                diffs.append(f"N={n} {lab}")
    print("\n== 8. Fingerprints of likely port slips (what a wrong team printout looks like) ==")
    print("  Each row changes ONE convention in this independent model. Compare the team's printout"
          " with these rows to find the slip. Correct rows: section 5.")
    slips = [("correct (reference)", {}),
             ("band: 'full' read as soc >= 35 kWh", dict(band_literal=True)),
             ("unsold permit hours still run (heat from permit)", dict(heat_from_permit=True)),
             ("deadline one hour later (job may run in deadline hour)", dict(deadline_shift=1)),
             ("deadline one hour earlier", dict(deadline_shift=-1)),
             ("FIFO instead of earliest deadline first", dict(fifo=True))]
    jobs8 = []
    for lab, sl in slips:
        for n in (6, 8):
            jobs8.append((n, False, True, "-", sl))
            jobs8.append((n, True, True, "B", sl))
    with ProcessPoolExecutor(max_workers=6) as ex:
        res8 = list(ex.map(_job_run, jobs8))
    print(f"  {'slip':<56}{'N':>2} {'no-adm missed of closed':>24} {'check: missed of closed':>24} {'acc%':>6}"
          f" {'cover%':>7} {'util%':>6} {'BE':>7}")
    i = 0
    for lab, _ in slips:
        for n in (6, 8):
            a, b = res8[i], res8[i + 1]
            i += 2
            ca, cb = a["done"] + a["missed"], b["done"] + b["missed"]
            el, ht, be = money(b["run_h"], b["used"], b["sold_h"])
            print(f"  {lab:<56}{n:>2} {a['missed']:>8,} of {ca:>11,} {b['missed']:>8,} of {cb:>11,}"
                  f" {100*b['accepted']/b['offered']:6.2f} {100*b['used']/total:7.2f} {100*b['run_h']/(n*8760):6.2f}"
                  f" {be:7.4f}")
    print("  Also: printing accepted instead of closed as the denominator gives"
          " 'of 32,210' / 'of 37,045' (the 36 / 22 jobs still open at year end are not closed);"
          " no year-end wrap in the planned permits gives 0 of 32,042 / 0 of 36,954 (section 5).")

    print("\n== 9. ILLUSTRATION: the same hourly offered work re-sliced into the workloads-branch job types ==")
    print("  embed 0.90 server-h / 48 h and rerank 0.91 server-h / 4 h (docs/workloads.md on branch"
          " origin/workloads, as of the last fetch); equal work shares; Poisson, random.Random(1).")
    print("  Not an oracle: it shows how far the J1/J2 oracle rows are from a scheduler fed these job types.")
    jobs9 = [(n, adm, rd) for n in (6, 8) for adm, rd in ((False, "-"), (True, "B"), (True, "A"))]
    with ProcessPoolExecutor(max_workers=6) as ex:
        res9 = list(ex.map(_team_types_run, jobs9))
    print("  N stage            offered accepted  acc%   missed of closed   coverage  util")
    for (n, adm, rd), r in zip(jobs9, res9):
        closed = r["done"] + r["missed"]
        lab = "no admission" if not adm else f"check run, rd {rd}"
        print(f"  {n} {lab:<16} {r['offered']:7,} {r['accepted']:8,} {100*r['accepted']/r['offered']:5.1f}"
              f" {r['missed']:7,} of {closed:7,}   {100*r['used']/total:6.2f}%  {100*r['run_h']/(n*8760):5.2f}%")

    print(f"\nDIFF/FAIL lines counted (reading B and admission-free rows only): {len(diffs)}")
    for d in diffs:
        print("  -", d)


if __name__ == "__main__":
    main()
