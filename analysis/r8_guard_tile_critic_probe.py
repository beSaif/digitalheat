"""Round 8 CRITIC probe for r8_guard_heldout.py (weak point: guard tuned on the test year,
tile cannot discriminate). ASSESSMENT ONLY, standard library, writes no files.

    python3 analysis/r8_guard_tile_critic_probe.py      # about 1 min on all cores

A. How many independent 'cliff' events does each year hold? A cliff day = actual day mean
   >= 12 degC (no heating) while the planning input's day mean for that day is < 10 degC
   (a heating day even with the 2 K guard). Counted for P1 at lag 1 and 2 days, and for the
   archived ECMWF day-1 / day-2 forecast (2024 from 10 Feb, 2025 all year). These days, not the
   ~150,000 closed jobs, are the effective sample for 'misses'.
B. Does O3 + 2 K on held-out 2024 depend on the 2024 forecast's warm bias (+0.65 K day 1)?
   Shift every archived 2024 forecast value by -delta (fallback persistence hours unchanged)
   and re-run with guard 2 K and 3 K, offer seeds 1-5, 'normal' offers.
   delta 0.36 = 2024 day-1 bias brought to 2025's (+0.29 K); 0.65 = zero day-1 bias;
   1.0 = a 0.35 K cold bias. Same shifts on 2025 for comparison (delta 0.29 = zero bias).
C. Tile arithmetic: offered jobs, accepted jobs, closed jobs, refused job share vs refused
   server-hour share, 2025 seed 1, the three stages.
Imports r8_guard_heldout and r2_deadline_sim without editing them.
"""
import multiprocessing as mp
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_guard_heldout as G  # noqa: E402
import r2_deadline_sim as R  # noqa: E402

H, HZ = G.H, G.HZ


def day_means(series):
    out = []
    for d in range(H // 24):
        v = series[d * 24:(d + 1) * 24]
        if any(x is None for x in v):
            out.append(None)
        else:
            out.append(sum(v) / 24.0)
    return out


def fc_raw(y, k):
    if y == "2025":
        return R.base()["ifs"][k]
    return G.read_ifs2024()[k]


def fd_shift(y, g, delta):
    a = G.act_dem(y)
    out = [a]
    T2 = H + HZ
    for k in range(1, 8):
        if y == "2024":
            col = G.read_ifs2024()[k]
            per = G.persisted_temps(y, k)
            tt = [p if v is None else v - delta for v, p in zip(col, per)]
        else:
            tt = [v - delta for v in R.base()["ifs"][k]]
        d = R.demand_from_temps(tt, 12.0 - g)
        out.append([d[t % H] for t in range(T2)])
    return out


def task(a):
    y, n, g, delta, s = a
    r = G.run_year(n, G.act_dem(y), fd_shift(y, g, delta), G.offers(y, n, s, "normal"))
    return a, (r["missed"], r["closed"], r["cov"])


def main():
    print("r8_guard_tile_critic_probe.py (critic). Assessment only.\n")
    print("== A. Cliff days: actual day mean >= 12 while the planning input's day mean < 10 (2 K guard) ==")
    for y in G.YEARS:
        T = G.temps()[y]
        act = day_means(T)
        p1 = [None] + act[:-1]
        p2 = [None, None] + act[:-2]
        c1 = sum(1 for d in range(365) if p1[d] is not None and act[d] >= 12 and p1[d] < 10)
        c2 = sum(1 for d in range(365) if p2[d] is not None and act[d] >= 12 and p2[d] < 10)
        line = f"  {y}: P1 lag-1 cliff days {c1:>2}, lag-2 {c2:>2}"
        if y in ("2024", "2025"):
            for k in (1, 2):
                f = day_means(fc_raw(y, k))
                ok = [d for d in range(41 if y == "2024" else 0, 365) if f[d] is not None]
                cf = sum(1 for d in ok if act[d] >= 12 and f[d] < 10)
                cp = sum(1 for d in ok if act[d] >= 12 and (p1 if k == 1 else p2)[d] is not None
                         and (p1 if k == 1 else p2)[d] < 10)
                line += f" | ECMWF day-{k}: {cf} cliff days (P1 lag-{k} on the same days: {cp}; {len(ok)} days)"
        print(line)

    print("\n== B. O3 with the archived forecast shifted colder by delta K (offer seeds 1-5, normal offers) ==")
    cases = [("2024", d) for d in (0.0, 0.36, 0.65, 1.0)] + [("2025", d) for d in (0.0, 0.29, 0.65, 1.0)]
    tasks = [(y, n, g, d, s) for (y, d) in cases for n in (6, 8) for g in (2.0, 3.0) for s in range(1, 6)]
    for y in ("2024", "2025"):
        G.act_dem(y)
    G.read_ifs2024()
    with mp.get_context("fork").Pool() as p:
        res = dict(p.map(task, tasks, chunksize=2))
    for (y, d) in cases:
        for n in (6, 8):
            cells = []
            for g in (2.0, 3.0):
                rr = [res[(y, n, g, d, s)] for s in range(1, 6)]
                cells.append(f"g{g:.0f}: {sum(r[0] for r in rr):>3} of {sum(r[1] for r in rr):>7,} "
                             f"{[r[0] for r in rr]} cov {sum(r[2] for r in rr) / 5 * 100:.2f}%")
            print(f"  {y} delta -{d:.2f} K N={n}: " + " | ".join(cells))

    print("\n== C. Tile arithmetic, 2025 seed 1 ==")
    for n in (6, 8):
        for lab, src, g in (("check", "check", 0.0), ("P1+2K", "P1", 2.0), ("O3+2K", "O3", 2.0)):
            r = G.run_year(n, G.act_dem("2025"), G.fd("2025", src, g), G.offers("2025", n, 1, "normal"))
            refj = sum(r["ref_j"])
            print(f"  N={n} {lab:<6} offered {r['offered']:,} | accepted {r['accepted']:,} | closed {r['closed']:,} "
                  f"(open at year end {r['accepted'] - r['closed']}) | refused {refj:,} jobs = "
                  f"{refj / r['offered'] * 100:.1f}% of jobs, {r['ref_share_w'] * 100:.1f}% of server-h | "
                  f"accepted share {r['acc'] * 100:.1f}% -> 100 - accepted = {100 - r['acc'] * 100:.1f}%")


if __name__ == "__main__":
    main()
