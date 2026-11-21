"""Round 8 probe: can a bigger heating-day guard (4, 6 K) or a 'warmest of the last days'
persistence rescue P1 out of sample? ASSESSMENT ONLY, standard library, writes no files.

    python3 analysis/r8_guard_probe.py     # about 20 s on all cores; offer seeds 1-3, 'normal' offers

P1 gK : P1 (r8_guard_heldout.fd 'P1') with a K-kelvin heating-day guard.
minE gG: planning demand for target t at lead K = min over e = 0..E of own[t - 24K - 24e],
         own = case formula with threshold 12 - G (the lowest of the last E+1 persisted days,
         i.e. fewest permits). Rules found AFTER looking at all six years: nothing here is held out.
Prints seed 1, 2, 3 misses per year and the 3-seed mean coverage. Imports r8_guard_heldout.
"""
import sys, multiprocessing as mp
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_guard_heldout as G, r2_deadline_sim as R
H, HZ = G.H, G.HZ
def fd_min(y, g, extra):
    a = G.act_dem(y)
    own = R.demand_from_temps(G.temps()[y], 12.0 - g)
    T2 = H + HZ
    def v(i): return own[i] if 0 <= i < H else 0.5
    return [a] + [[min(v(t - 24*k - 24*e) for e in range(extra + 1)) for t in range(T2)] for k in range(1, 8)]
def task(a):
    y, n, kind, g, s = a
    if kind == "P1":
        Fd = G.fd(y, "P1", g)
    else:
        Fd = fd_min(y, g, int(kind[-1]))
    r = G.run_year(n, G.act_dem(y), Fd, G.offers(y, n, s, "normal"))
    return a, (r["missed"], r["closed"], r["cov"], r["acc"])
if __name__ == "__main__":
    tasks = [(y, n, k, g, s) for y in G.YEARS for n in (6, 8) for (k, g) in (("P1", 4.0), ("P1", 6.0), ("min1", 0.0), ("min1", 2.0), ("min2", 2.0)) for s in (1, 2, 3)]
    with mp.get_context("fork").Pool() as p:
        res = dict(p.map(task, tasks))
    for n in (6, 8):
        for k, g in (("P1", 4.0), ("P1", 6.0), ("min1", 0.0), ("min1", 2.0), ("min2", 2.0)):
            cells = []
            for y in G.YEARS:
                rr = [res[(y, n, k, g, s)] for s in (1, 2, 3)]
                cells.append(f"{y} {[r[0] for r in rr]} cov {sum(r[2] for r in rr)/3*100:.2f}")
            print(f"N={n} {k} g{g:.0f}: " + " | ".join(cells))
