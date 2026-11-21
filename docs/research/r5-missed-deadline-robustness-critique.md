# Round 5 critique: missed-deadline robustness

Critic's view of [r5-missed-deadline-robustness.md](r5-missed-deadline-robustness.md) and `analysis/r5_miss_stress.py`. Assessment only. No files were edited and no git state was changed. The critic's probe scripts were run from the session scratchpad and are reproduced in full below (appendix A), so others can re-run them. Firecrawl calls: 0.

## Bottom line

The work holds up. `python3 analysis/r5_miss_stress.py` re-ran in 2 min 41 s, and its output is **byte-identical** to `docs/research/r5-missed-deadline-robustness-output.txt` (apart from the line that counts simulated years). All regression checks pass. The inline checks (c5, c11, c15) and the laptop probe (c18: 2.06 s on our re-run, against 2.10 s) reproduce. The two sources say what is claimed, with one important caveat on the Microsoft figure. Still, four points weaken the pitch wording:

1. **"Padding 30% brings it back to 0" comes from the overrun model we chose.** Overrun is drawn from U(0, 20%), which is bounded *below* the 30% pad, so 0 is guaranteed by design. With tails it is *near* zero, not zero. My probes with the pad on: 1% of jobs at 2× gives 0–1 a year (0.001%); 10% of jobs at +30–100% gives 0.020–0.025%; a lognormal runtime (σ 0.3) gives 0.009%.
2. **Failures are modelled as independent per-server events only.** The servers in one basement share a grid connection, a router, a hydronic pump and a breaker. **One whole-house outage, with the scheduler told, misses 25–41 accepted jobs if it falls on 15 April or 15 October.** On the 15th of Nov–Mar it misses 0. If the scheduler is not told, a 72 h outage misses 150–386 (Oct–Mar starts). One correlated event therefore outweighs every other stress except overrun.
3. **The Microsoft "AFR 8%" is the share of servers that see ≥1 repair, not an event rate.** The same page gives 20 replacements per 100 servers in 14 months, which is about **0.17 events per server-year**. The failures are clustered, and 78% of them are hard disks (2010 CPU servers). So 0.08 used as a Poisson rate understates the event rate by about 2×. The 0.55 and 1.0 cases still cover it, so the conclusion survives, but the wording does not.
4. **The tile is the team scheduler's own number, and that scheduler will not contain GFS/ICON, failures or overrun.** The archived forecast plus guard (R7) is OPTIONAL in the plan, and restart inside the scheduler is CUT. "Tested with three forecast models … and failures" is an analysis-script result. It must be labelled as one and kept off the tile itself.

## Re-runs

| What | Command | Result |
|---|---|---|
| Full stress run | `python3 analysis/r5_miss_stress.py` | Identical to the committed output file (diff empty apart from the line that counts simulated years); 2 min 41 s on 12 cores |
| c5 ICON = round-2 "best match" | inline command from the research file, plus a GFS day-7 comparison | `[8760]*7 + [0]`; GFS day 7 matches 6,730 / 8,760; ICON day 7 NaN in all 8,760 rows |
| c11 arithmetic | `python3 -c "hw=0.78*419; pg=hw/16384*365/54; print(pg, 4*pg)"` | 0.1348, 0.539 (0.691 counting all 419 unexpected) |
| c15 idle permit hours | `r4_headline.run(n, HEADLINE, 'shaped100', 1)`, sum(ks_cap − ks_on) | 3,198 (N=6), 5,346 (N=8). **But** in 3,739 h (N=6) / 2,509 h (N=8) every server holds a permit *and* runs, so an outage does take compute away then. Deadline slack (24 h for J1, 168 h for J2) explains the 0 at least as much as "spare compute on cold days" |
| c18 laptop restart | `python3 analysis/r5_model_load_probe.py` | 2.63 / 2.06 / 1.84 s, median 2.06 s. Model files sit in the OS page cache (three back-to-back runs), so this is a warm-disk restart, not a cold boot |

## Critic probes (appendix A; *computed*, guard 2 K, 5 seeds, seed 1 = committed CSV)

```
P1 pad 30%, no overrun                 N=6: 0 in all; acc 94.6->94.7%; cover 73.76->73.50%; sold h 28,795->28,694
                                       N=8: 0 in all; acc 93.8->94.0%; cover 86.08->85.91%
P2a 1% of jobs 2x, no pad              N=6: 4-7/yr, 0.019%      N=8: 4-11/yr, 0.019%
P2a 1% of jobs 2x, pad 30%             N=6: 0-1, 0.001%         N=8: 0
P2b 90% U(0,20%)+10% U(30,100%), pad   N=6: 1-11, 0.025%        N=8: 4-10, 0.020%   (acc 84.9% / 85.7%)
P2c lognormal sigma 0.3, no pad        N=6: 45-53, 0.155%       N=8: 34-46, 0.109%
P2c lognormal sigma 0.3, pad 30%       N=6: 1-7, 0.009%         N=8: 0-6, 0.009%
P2d E1 with "1% of jobs 2x", pad 30%   N=6: 0-1, 0.001%         N=8: 0-1, 0.001%
P3 ICON debiased -2 K (guard 2 K)      N=6: 0-6, 0.004%         N=8: 0-14, 0.013%
P3 ICON debiased -3 K (guard 2 K)      N=6: 25-51, 0.107%       N=8: 82-97, 0.234%

P4 whole house down (all N servers) at 00:00 on the 15th of each month, seed 1; missed jobs Jan..Dec
  N=6 24 h told     [0, 0, 0, 38, 15, 2, 0, 0, 3, 25, 0, 0]
  N=6 72 h told     [0, 0, 0, 38, 17, 2, 5, 0, 11, 25, 0, 0]
  N=6 72 h NOT told [274, 277, 307, 236, 76, 21, 34, 24, 23, 150, 289, 267]
  N=8 24 h told     [0, 0, 0, 30, 5, 5, 0, 13, 3, 7, 0, 0]
  N=8 72 h told     [0, 0, 0, 41, 12, 7, 1, 13, 9, 7, 0, 0]
  N=8 72 h NOT told [375, 347, 317, 229, 55, 31, 24, 43, 27, 173, 338, 386]

Combined, restart variants (appendix A, probe 2):
  E1 restart 15 min NOT aware            N=6: 0.389%  N=8: 0.254%
  E1 restart outside execution (plan)    N=6: 0.366%  N=8: 0.242%
  E4 (pad 30%) restart NOT aware/outside N=6: 0      N=8: 0
```

What the probes show:
- **The pad is cheaper than the research file implies.** Without overrun it costs about 0.26 (N=6) / 0.17 (N=8) coverage points and no acceptance. The quoted "89.7 → 87.8%" acceptance drop is mostly overrun itself, not the pad.
- **The pad gives near zero, not zero, under tailed runtimes.**
- **The guard covers a cold bias up to about 2 K. At −3 K it gives 0.1–0.23%.**
- **The combined result does not depend on restart awareness.** That matters because the plan has CUT restart inside the scheduler.
- **A whole-house outage is the missing failure mode.** When the scheduler is told, the cost mostly shows up as refused offers, which the missed metric does not count. Misses come in shoulder months, when the queue is full and the permits are scarce.

## Verdicts in brief

See the structured verdict list returned with this file. Survive as computed: c1–c8, c12–c14, c16, c17, c20, c21, c23–c26. Survive with caveat: c9 (meaning of AFR), c10/c11 (H100 training interruptions, not repairs; "up to" 16K), c15 (interpretation), c18 (warm cache, laptop only), c19 (the summary text says "6–27 a year (0.03–0.06%)", but the table gives 6–13 / 9–23, 0.029–0.037%), c22 (0 is guaranteed by bounded overrun < pad).

## Smaller issues found

- The research file's summary line "6–27 a year" for a restart the dry run ignores does not match its own table (6–13 at N=6, 9–23 at N=8).
- The Q&A says "published data-centre rates (8% to about 0.5 per server per year)". 8% is a share of servers, and 0.5 is our own derivation from GPU training interruptions.
- ICON's day-1 forecast runs 1.1 K warm, warmer than its day 3 (+0.31 K), and it misses 25 heating days at day 1. Its 0 is "cautious by bias", which the research file admits. A founder will note that a warmer forecast also costs 0.45 coverage points.
- 5 seeds × 6 servers × 0.55/yr is about 16 outage events in total for b2 at N=6. b2 and b6 (told vs not told) give identical results, so outages of this size never bound the dry run. The sample of failure events is small.
- Overrun admission is naive: once the estimated remaining time reaches 0, the dry run treats a job as finished while it still runs. A real scheduler would see this and re-estimate. So the unpadded overrun misses are somewhat pessimistic, but no scheduler has that feedback yet.
- Non-weather demand error is untested: occupants, setpoints and solar gains. In the model, "actual" demand is still the case formula applied to a modelled temperature.

## Appendix A: probe scripts (run from the scratchpad; stdlib; import `analysis/r5_miss_stress.py` unchanged)

Probe 1 (`python3 r5critic_missstress_probe.py`, 23 s on 12 cores):

```python
"""Critic probes for round-5 missed-deadline robustness. Imports analysis/r5_miss_stress.py unchanged.

python3 r5critic_missstress_probe.py   (run from anywhere; stdlib only)

P1 pad cost with NO overrun (investigator never ran it)
P2 heavy-tailed / mixed overrun with the 30% pad (investigator's tail is bounded at +2o)
P3 cold bias beyond 1 K (-2 K, -3 K) with the 2 K guard
P4 whole-house outage (all N servers: power, internet, hydronic pump), 24 h / 72 h, at the
   15th of each month 00:00, scheduler told and not told, seed 1
"""
import math
import multiprocessing as mp
import random
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/saif/Work/digitalheat/analysis")
import r5_miss_stress as S  # noqa: E402


class TailRandom(random.Random):
    def uniform(self, a, b):
        if a == 0.0 and abs(b - 0.202) < 1e-9:      # 1% of jobs take 2x nominal, rest nominal
            return 1.0 if self.random() < 0.01 else 0.0
        if a == 0.0 and abs(b - 0.204) < 1e-9:      # 90% U(0,20%), 10% U(30%,100%)
            return random.Random.uniform(self, 0.0, 0.2) if self.random() < 0.9 else random.Random.uniform(self, 0.3, 1.0)
        if a == 0.0 and abs(b - 0.206) < 1e-9:      # lognormal multiplier, median 1, sigma 0.3 (can be <1)
            return math.exp(self.gauss(0.0, 0.3)) - 1.0
        return random.Random.uniform(self, a, b)


S.random = types.SimpleNamespace(Random=TailRandom)


def add_cold(shift):
    name = f"icon_cold{shift:g}"
    key = ("ft", name)
    if key not in S._C:
        ft = S.fc_temps("icon")
        act = ft[0]
        new = [act]
        for k in range(1, 8):
            bias, _ = S.stats(ft[k], act)
            new.append([t - bias - shift for t in ft[k]])
        S._C[key] = new
    return name


def task(a):
    label, n, seed, c = a
    for sh in (2, 3):
        add_cold(sh)
    r = S.run(n, S.cfg(**c), seed)
    return (label, n, seed), r


SC = [
    ("BASE ifs025", dict()),
    ("P1 pad 30%, no overrun", dict(pad=0.30)),
    ("P1 pad 30%, no overrun, ICON", dict(fc="icon", pad=0.30)),
    ("P2a 1% of jobs 2x, no pad", dict(overrun=0.101)),
    ("P2a 1% of jobs 2x, pad 30%", dict(overrun=0.101, pad=0.30)),
    ("P2b 90% U(0,20%)+10% U(30,100%), pad 30%", dict(overrun=0.102, pad=0.30)),
    ("P2c lognormal sigma 0.3, no pad", dict(overrun=0.103)),
    ("P2c lognormal sigma 0.3, pad 30%", dict(overrun=0.103, pad=0.30)),
    ("P2d E1 but 1% of jobs 2x instead of U, pad 30%", dict(fc="icon", fail_rate=0.55, overrun=0.101, restart=15.0, pad=0.30)),
    ("P3 ICON debiased -2 K, guard 2", dict(fc="icon_cold2")),
    ("P3 ICON debiased -3 K, guard 2", dict(fc="icon_cold3")),
]


def main():
    seeds = [1, 2, 3, 4, 5]
    jobs = [(l, n, s, c) for l, c in SC for n in (6, 8) for s in seeds]
    # P4: whole-house outages, seed 1
    for n in (6, 8):
        for m in range(12):
            st = (sum(S.R.MDAYS[:m]) + 14) * 24
            for dur in (24, 72):
                for aw in (True, False):
                    jobs.append((f"P4 house down {dur}h from day {m+1}/15 {'told' if aw else 'NOT told'}", n, 1,
                                 dict(fail_at=(st, n, dur), fail_aware=aw)))
    with mp.Pool() as pool:
        res = dict(pool.map(task, jobs, chunksize=1))
    print("== P1-P3: guard 2 K, 5 seeds (seed 1 = committed CSV) ==")
    for l, c in SC:
        for n in (6, 8):
            rs = [res[(l, n, s)] for s in seeds]
            x = sum(r["missed_n"] for r in rs); y = sum(r["closed_n"] for r in rs)
            acc = sum(r["acc_jobs"] for r in rs) / 5; cov = sum(r["coverage"] for r in rs) / 5
            be = sum(r["breakeven"] for r in rs) / 5
            print(f"  {l:<50} N={n}: missed {' '.join(str(r['missed_n']) for r in rs):<22} pooled {x}/{y:,} = {x/y*100:.3f}%  "
                  f"acc {acc*100:.1f}%  cover {cov*100:.2f}%  sold_h {sum(r['sold_h'] for r in rs)/5:,.0f}")
    print("\n== P4: whole house down (all N servers), seed 1, guard 2 K; BASE seed 1 missed 0 ==")
    for n in (6, 8):
        base = res[("BASE ifs025", n, 1)]
        for dur in (24, 72):
            for aw in (True, False):
                row = []
                for m in range(12):
                    r = res[(f"P4 house down {dur}h from day {m+1}/15 {'told' if aw else 'NOT told'}", n, 1)]
                    row.append(r["missed_n"])
                print(f"  N={n} {dur:>2} h {'told    ' if aw else 'NOT told'} missed by start month Jan..Dec: {row}  "
                      f"(max {max(row)}, of ~{base['closed_n']:,}/yr)")


if __name__ == "__main__":
    main()
```

Probe 2 (restart variants of E1/E4):

```python
import sys, multiprocessing as mp
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/saif/Work/digitalheat/analysis")
import r5_miss_stress as S
SC = [("E1 but restart NOT aware (plan cut restart in scheduler)", dict(fc="icon", fail_rate=0.55, overrun=0.10, restart=15.0, aware=False)),
      ("E4 = E1 + pad 30%, restart NOT aware", dict(fc="icon", fail_rate=0.55, overrun=0.10, restart=15.0, aware=False, pad=0.30)),
      ("E1 with restart outside execution (plan's actual core)", dict(fc="icon", fail_rate=0.55, overrun=0.10)),
      ("E4 with restart outside execution + pad 30%", dict(fc="icon", fail_rate=0.55, overrun=0.10, pad=0.30))]
def task(a):
    l, n, s, c = a
    return (l, n, s), S.run(n, S.cfg(**c), s)
if __name__ == "__main__":
    jobs = [(l, n, s, c) for l, c in SC for n in (6, 8) for s in range(1, 6)]
    with mp.Pool() as p:
        res = dict(p.map(task, jobs, chunksize=1))
    for l, c in SC:
        for n in (6, 8):
            rs = [res[(l, n, s)] for s in range(1, 6)]
            x = sum(r["missed_n"] for r in rs); y = sum(r["closed_n"] for r in rs)
            print(f"  {l:<58} N={n}: {' '.join(str(r['missed_n']) for r in rs):<22} pooled {x}/{y:,} = {x/y*100:.3f}%  acc {sum(r['acc_jobs'] for r in rs)/5*100:.1f}%")
```
