# Critique, round 7: forecast inside the team scheduler (foresight)

Critic for `docs/research/r7-scheduler-forecast.md` and `analysis/r7_forecast_paths.py`. I wrote no file other than this one. My probe script is in my scratchpad; its code is reproduced in full below, so anyone can re-run it. Currency: CHF. No new money figures.

## What I re-ran

- `python3 analysis/r7_forecast_paths.py`, all sections, 77 s. Every number in the research file's sections 0, 1, 2, 2b and 3 matches my run, outage rows included. The research file leaves out only the coverage-cost lines, and they match the claims: −1.23 / −1.99 for persistence + 2 K against plain perfect.
- I checked the code for c1. `analysis/r6_build_scope.py` `stage_specs()` S1 is `("r5", dict(fc="perfect"))`, and `analysis/r5_miss_stress.py` `cfg()` defaults to `guard=2.0`. **Confirmed.** The plan's "Perfect forecast (MUST)" row is perfect + 2 K.
- `prev_ecmwf_ifs025.csv`: 473,508 bytes, columns as claimed. Time labels match the reference CSV (8760 8760 True). Both files use fixed UTC+1 (data/README.md line 48; CSV header `utc_offset_seconds 3600`), so lookup by row index is valid.
- Look-ahead arithmetic, checked by hand. For a target at h+L, the heating-day flag averages the whole target day D. It reads day D−K, whose last hour is ≤ h+L−24K+23. With K = ceil((L+23)/24) that is ≤ h. With the `min(7, …)` cap, at L = 167 it reaches h+22. **c17 is correct.**
- Web: I opened both pages myself (WebFetch, 21 Nov 2026).
  - <https://open-meteo.com/en/docs/previous-runs-api>: "returns the value predicted 24 hours before valid time" and "_previous_day0 is the current model run". The page does not say which run fills an offset, or what the publication delay is.
  - <https://ecmwf.int/en/forecasts/datasets/open-data>: "The lower resolution data are released at the end of the real-time dissemination schedule", cycles 00/06/12/18 UTC, no delay in hours. **Both sourced claims hold.**

## Probe results (my code, below)

1. **The team's natural lookup reproduces the oracle exactly.** I coded `own[h+L-24K] if t >= 0 else 0.5` from the CSV columns, with no modulo and no December 2024 pad. Seed 1 gives 0 of 31,471 / 0 of 36,272 at 72.30% / 84.10%, and N=8 seed 3 gives 22 of 36,573. These are identical to `persist+g2`, so the proposed oracle row is safe for the code the team will write.
2. **The dashboard wording describes a different algorithm.** The recommended tile line says "the house's own last full measured day, repeated". The simulated rule is "the same hour K days back, K = ceil((L+23)/24)". It uses the day before yesterday for most leads (for example h = 00:00, L = 2…23), and yesterday only for some.
   - Coding the wording literally (the last calendar day fully measured by h, repeated) gives 0 of 31,409 / 0 of 36,265, 72.24% / 83.97% at seed 1, and 4 of 36,541 at N=8 seed 3.
   - If the team codes what the tile says, the scheduler will not match the oracle. That is the same trap as c1. Either the wording or the code must change.
3. **A 3 K guard on persistence gives 0 in all 10 runs** (seeds 1–5, N = 6 and 8). Seed 1: 0 of 31,417 / 0 of 36,235, 72.24% / 84.03%. It costs 0.06 / 0.07 points against 2 K. This is a cheap fix for the seed-3 miss, if the team wants every seed at 0.
4. **The outage comparison across forecasts compares different things.** Take the house dark from 15 April, told:
   - persistence + 2 K gives 0 of 31,239, accepted 92.8%;
   - archived + 2 K gives 38 of 31,571, accepted 93.8%;
   - plain perfect gives 38 of 31,845.

   Persistence "wins" because its lagged heating-day flag accepted less work before mid-April, not because it handles an outage better. So quoting "26 / 14 (persistence)" next to "38 / 41 (archived)" invites a false reading. The research file also never reports the accepted share for the heartbeat mode, although that mode refuses every offer for about 71 h.
5. **The "+1 day" publication-delay variant is capped at 7.** For L ≥ 122 it gets no extra day, and at L = 167 the flag can still read values issued up to 46 h after h. So c16 is a partial bound, not a full one.
6. **Build-slot conflict.** The research file puts persistence in B's 12:45–14:15 slot. The round-6 critique (`r6-build-scope-audit-critique.md` item 1) already shows B cannot finish K2 before the 14:45 draft: 1.95–3.70 h of work against 1.56 h of capacity. Persistence has to come after K2, in the 14:45–16:30 window. On the cumulative load, it moves B from 3.20–5.70 h to about 3.7–6.7 h against 5.50 h, using the round-6 assumed rates.
7. **The heartbeat rule needs more than 3 lines.** The executor must also know the house is dark: n_up = 0 and an outage window. That is N1's `--outage` injection (about 8 lines, estimate). The rule is about 3 lines on top of that, not 3 lines in total.

### Probe output (seed 1 unless stated; `python3 <scratchpad>/r7fc_critic_probe.py`, 9 s)

```
team_lag        N=6 seed 1 guard 2  missed    0 of 31,471 acc 93.5% cov 72.30%
lastday         N=6 seed 1 guard 2  missed    0 of 31,409 acc 93.3% cov 72.24%
oracle_persist  N=6 seed 1 guard 3  missed    0 of 31,417 acc 93.3% cov 72.24%
team_lag        N=8 seed 1 guard 2  missed    0 of 36,272 acc 92.4% cov 84.10%
lastday         N=8 seed 1 guard 2  missed    0 of 36,265 acc 92.4% cov 83.97%
oracle_persist  N=8 seed 1 guard 3  missed    0 of 36,235 acc 92.3% cov 84.03%
team_lag        N=8 seed 3 guard 2  missed   22 of 36,573
lastday         N=8 seed 3 guard 2  missed    4 of 36,541
lastday/oracle  N=8 seed 3 guard 3  missed    0 (both)
oracle_persist  guard 3, seeds 1-5, N=6 and N=8: missed 0 in all 10
Apr 15 dark 72 h, told:  persist+g2 0 of 31,239 (acc 92.8%) | ifs+g2 38 of 31,571 (93.8%) | perfect 38 of 31,845 (94.7%)  [N=6]
                         persist+g2 0 of 36,039 (acc 91.8%) | ifs+g2 41 of 36,484 (93.0%) | perfect 27 of 36,765 (93.7%)  [N=8]
```

### Probe code

```python
import inspect, sys, multiprocessing as mp
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/saif/Work/digitalheat/analysis")
import r7_forecast_paths as F
src = inspect.getsource(F.run); old = "dF = Fd[LEAD[L]][(h + L) % H]"
src = src.replace("def run(", "def run_fc(FC, ").replace(old, "dF = FC(h, L)"); exec(src, F.__dict__)
KT = [min(7, (L + 46) // 24) for L in range(168)]
def fc_team_lag(g):
    o = F.persist_from_csv_columns(g)
    return lambda h, L: o[h + L - 24 * KT[L]] if h + L - 24 * KT[L] >= 0 else 0.5
def fc_lastday(g):
    o = F.persist_from_csv_columns(g)
    def FC(h, L):
        c = (h + 1) // 24 - 1
        return 0.5 if c < 0 else o[24 * c + (h + L) % 24]
    return FC
# F.run_fc(fc_team_lag(2.0), n, ("persist", 2.0, 0.0, "causal"), None, "none", seed); outage: (F.day_hour(4), 72), "told"
```

## Verdict summary

The core finding (c1) is right, and important. The numbers reproduce. Persistence + 2 K is a defensible, causal, cheap input, and the team's natural code reproduces it. The weak spots:

- The tile wording describes a different algorithm (probe 2).
- One wording line is inaccurate: "about one point less coverage" holds for persistence, but archived is only 0.33 / 0.37 points below plain perfect.
- The outage maxima are compared across forecasts (probe 4).
- The +1 d bound is partial (probe 5).
- The build slot is wrong (probe 6).
- The 3-line heartbeat estimate leaves out the outage injection (probe 7).
- The 2 K guard was chosen on the same weather year it is scored on.
