# Critique: r3 one scheduler, not a script

Critic role: a sceptical DigitalHeat founder. Target: `docs/research/r3-one-scheduler-scope.md`, `analysis/r3_policy_check.py` and `analysis/r3_scope_extra.py`. No web sources were used. Firecrawl calls: 0. Currency: CHF. No conversion was needed.

## What I re-ran

| Command | Result |
|---|---|
| `python3 analysis/r3_policy_check.py` (scratch copy of the output) | Same as `docs/research/r3-one-scheduler-scope-rerun-output.txt` apart from the timing line. Regression checks all OK. 54 s wall, 507 s CPU on this machine |
| Critic check script (stdlib, imports `r3_policy_check`, edits nothing; source below) `counts` | Missed counts for policy A at N=6/8, both offer scenarios, seeds 1-3 (table below) |
| same script, `demo` | July heat-signal demo dates for policy A at N=6/8, both offer scenarios, **seeds 1-3** (the investigator scanned seed 1 only), plus the job-level view of 2025-01-13 |

All section-1/2/3 figures quoted in claims c2-c4 and c6-c14 match the re-run output digit for digit. The arithmetic is sound. My objections are about what the numbers mean and about the plan built on them.

## Findings that change the plan

### F1. Break-even is a constant here, not a result
Whenever nothing is dumped and every run hour is a sold hour, break-even = 0.3325 − 0.8 × 0.133 = **0.2261 CHF**, whatever the policy (*computed*: the critic script prints 0.2261 from `baseline_sweep` constants). So every "d break-even" in section 2 is either exactly 0 or the 15-minute restart assumption. Claim c7's "break-even 0.0000" is true by construction, not evidence that the band is harmless. The pitch must not present 0.2261 as something the scheduler achieved. It is the case formula with dumped = 0, and it excludes hardware cost.

### F2. "Saturating" offers starve the servers on the coldest day
Saturating offers are N × 24 server-hours a day: exactly peak capacity, with no buffer. On 2025-01-13 (coldest day, permits 6 every hour), the **job-level** run of policy A has these working servers per hour (seed 1):

- saturating: `666666666666663655453556`. Server heat is about 104.8 kWh against 115.2 kWh at permit level.
- shaped100: `666666666655466365544355`. Server heat is about 100.8 kWh.

So on the coldest day of the year, servers that hold a heat permit sit idle for lack of admitted work while the backup heater runs. That is roughly 10-14 kWh more backup than the 106.3 kWh quoted for the January demo day (*computed*, approximate because tank carry-over is ignored). This is the 79.58% → 79.2% coverage gap at N=6.

The investigator saw this ("6th server idle on 9 January days") but recommends hiding it ("do not show it as a heat pause") and still quotes the permit-level "6 of 6 servers all 24 h, backup 106.3 kWh" for the demo. If the demo screen shows permit-level numbers while the yearly balance is job-level, the two disagree. That breaks the "same code" claim the plan depends on.

### F3. The real job type is never accepted in summer in the saturating balance
Section 3 of the re-run shows **summer accepted J1 = 0.0% of offers** for M1 and A, at N=6 and N=8, under saturating offers. Under shaped100 it is 89-91%. J1, transcription, is the job that runs for real on the laptop. With saturating offers as the headline run, the yearly scheduler turns away every J1 in June-August, yet the July demo shows a J1 running on slot 1. R6 ("runs iff k ≥ s, not job availability") makes the demo look right because it takes the real job out of the job model. A juror who asks "is your live job one of the 32,000 in your balance?" gets "no". Fix, for about 5 lines: make the real job a pinned, always-ready queue job on slot s, and count its server-hours in the balance. Or make shaped100 the headline offer scenario.

### F4. The July demo date depends on the random seed, not only on the offer scenario
Policy A, slot 1, heat signal, days with pause-then-resume (*computed*, critic script `demo`):

| N | offers | seed 1 | seed 2 | seed 3 |
|---|---|---|---|---|
| 6 | saturating | 6 days incl. 07-19 P04 R20 | same 6 | same 6 |
| 6 | shaped100 | 6 days incl. 07-22 P04 R20 | **3 days: 07-08, 07-17, 07-24; no 07-22** | same as seed 1 |
| 8 | shaped100 | 6 days incl. 07-22 | same as seed 1 | **3 days: 07-18, 07-20, 07-27; no 07-22** |

"Pick the date from the final run" is the right rule. The specific dates in c16/c17 and plan change 7 are not robust, though: they also move with the seed. In addition, the hour labels are UTC+1 all year (`data/README.md`), so the July "04:00 / 20:00" is 05:00 / 21:00 on the wall clock (CEST).

### F5. The LOC estimate undercuts its own anchors
The investigator anchors the admission estimate on `r2_deadline_sim.py` admission (43 lines) + `forward_fail` (25 lines) = 68 non-blank lines, then estimates **35**. The assessment script's own admission block (lines 199-276) is about 78 lines plus `forward_fail`. A realistic core is about 110-150 lines, not 80. This is also the third time a 55-minute slot appears for queue + offers + EDF + expiry (11:20-12:15). The round-2 critique already rejected that slot as not credible (`docs/overnight.md`, round-2 changes).

### F6. The build order misses "minimum by 15:00" and live-driver replay
`docs/overnight.md` requires the same-decisions (trace-equality) test to be green by the 15:00 draft. The proposed build order puts that test at 18:40-21:00. Once admission sits inside `decide()`, the live driver must also replay that day's offers and the same forecast slice, starting from a 00:00 snapshot that includes the job queue. The spec does not say who stores the offers. Without that, the trace test cannot pass. This is an integration task of about 30-60 minutes that the schedule does not contain.

### F7. The forecast caveat is missing from the pitch wording
Fallback stage 1 says "Forecast error is the only failure we model". It must also say that the archived forecast comes from the same model family as the "actual" weather. That understates the error, and the 0-12 missed jobs are flattered by it (round-2 caveat, repeated in the investigator's own limitations but not in the wording).

## Check script used (scratch, not committed)

```python
import sys; sys.path.insert(0, "analysis")
import r3_policy_check as P, r2_deadline_sim as R
from baseline_sweep import HEAT_VALUE, P_EL, PRICE, REC
BAND = dict(rule="band", band=8.0, cap1=True)
A = P.pol(fc="ifs025", guard=2.0, restart=15.0, aware=True, **BAND)
print(PRICE*P_EL - REC*P_EL*HEAT_VALUE)                      # 0.2261
# counts: P.run(n, A, dm, s)['missed_n'], ['done_n'] for n in (6,8), dm, s in 1..3
# demo:   scan P.run(...)['ks_cap'] per July day, slot 1, first PAUSE then RESUME
#         2025-01-13: compare ['ks_cap'] with ['ks_on'] (job level)
```

## Output excerpts

```
c5  N=6 sat  missed 1/1/1 of closed 32408/32641/32112 | N=6 shp 1/1/3 of 31866/31667/31930
    N=8 sat  missed 11/12/7 of 38186/37934/38626      | N=8 shp 3/3/0 of 36664/36934/37060
2025-01-13 N=6 A seed1 sat: permits 666666666666666666666666 working 666666666666663655453556
2025-01-13 N=6 A seed1 shp: permits 666666666666666666666666 working 666666666655466365544355
N=6 shaped100 seed 2: 3 days 07-08:P06R22 07-17:P03R19 07-24:P06R22
N=8 shaped100 seed 3: 3 days 07-18:P06R22 07-20:P01R17 07-27:P04R20
Section 3: summer accepted J1 0.0% (M1, A; saturating; N=6 and N=8); 89-91% under shaped100
Section C (extra output file): M1 N=8 saturating 4.9 s, not 4.6 s
```

## Verdict summary

The evidence holds. The core arithmetic is right and reproducible, and the "one permit function" finding is the most valuable result of the round. What is weak is the demo-and-balance consistency (F2, F3, F4) and the build-time optimism (F5, F6). Cutting the hold rule and moving restart into the accounting are both correct.
