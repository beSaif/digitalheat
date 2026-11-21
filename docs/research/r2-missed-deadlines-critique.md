# Round 2 — critique of the missed-deadline result (docs/research/r2-missed-deadlines.md)

Critic pass, written as a sceptical DigitalHeat founder. No investigator file was changed, no git state changed. Firecrawl calls used: 0 of 1.

## What I re-checked

| Item | Check | Result |
|---|---|---|
| All tables (C1–C7, C11–C20, C22) | `python3 analysis/r2_deadline_sim.py` (2 min 15 s, 680 years) and `diff` against `r2-missed-deadlines-output.txt` | Identical, 289 lines, no difference |
| C8 | Opened <https://open-meteo.com/en/docs/previous-runs-api> | Confirmed: "_previous_day1 returns the value predicted 24 hours before valid time"; "Most models are archived from January 2024" |
| C9 | Opened <https://content.meteoblue.com/en/research-education/weather-data-accuracy/air-temperature/> | Confirmed: 1.2 K (24 h) and 2.0 K (6 days) for the vendor's multi-model, 2017, more than 11,000 stations; raw models 1.7–2.2 K; 2018 table with more than 8,000 WMO stations: ICON 2.0, GEM 2.4. I did not see "24 h" stated for the 2018 table. Worldwide, MAE not RMSE |
| C21 | Check script, section `c21` (dry-run re-check switched off) | Reproduced: 166 missed at N=8, seed 1, perfect forecast |
| C23 | Arithmetic on section 8 (109 missed of 38,901; J1 0.012%, J2 2.145%) | 34,009 J1 = 87.4% |
| C25 | Downloaded the same request with `models=ecmwf_ifs` | `temperature_2m` identical to the reference (max difference 0.0). But the research file's "no previous-day values (all NaN)" is wrong: 2,207 hours from 2025-10-01 have them |

Both web pages were read through the same summarising fetch tool the investigator used; a read by eye is still owed before slide use.

## Findings

All numbers below are *computed* by the two check scripts at the end of this file (saturating offers, no partner, no margin, 5 seeds, missed % of accepted jobs).

### 1. The headline rests on a warm-biased forecast, not on a small error

| Forecast seen by admission | N=6 | N=8 |
|---|---|---|
| Investigator's headline (ifs025, bias +0.29 K) | 0.146 | 0.294 |
| Same, mean bias per lead removed (day-1 RMSE 1.12 K) | 0.445 | 0.592 |
| Same, 2 K guard band | 0.004 | 0.016 |

A smaller RMSE gave three times the misses at N=6. The warm bias of the 0.25° grid cell (47.5 N, 7.5 E against the reference cell 47.557 N, 7.549 E) is what protects the headline. Any real system that calibrates its forecast against the house removes that protection.

Real-data confirmation: the 9 km IFS (the reference model itself) has archived lead-time values from 1 October 2025. On those 2,207 hours its day-1 error is RMSE 1.00 K, bias −0.18 K; ifs025 on the same hours is 1.26 K, +0.47 K. October to December, misses over accepted jobs, 5 seeds pooled:

| | N=6 | N=8 |
|---|---|---|
| ifs025 | 119 / 65,149 = 0.18% | 280 / 77,056 = 0.36% |
| 9 km IFS (better RMSE, slightly cold) | 272 / 66,440 = 0.41% | 551 / 78,905 = 0.70% |
| 9 km IFS + 2 K guard band | 0 / 64,877 | 13 / 76,315 = 0.017% |

### 2. The heating-day flag in the forecast looks up to 23 hours into the future

`demand_from_temps(ft[k])` computes a target day's heating flag from the K-day series for all 24 hours of that day. For a target hour at lead K days, the later hours of the same day would only be available at lead K+1. Using the K+1 series for the flag (strictly causal, slightly pessimistic):

| | N=6 | N=8 |
|---|---|---|
| Headline | 0.146 (J2 0.76) | 0.294 (J2 1.34) |
| Causal flag | 0.153 (J2 1.19) | 0.511 (J2 1.79) |
| Causal flag + 2 K guard band | 0.002 | 0.009 |

The truth lies between the two rows. At N=8 the headline is optimistic by up to a factor 1.7.

### 3. The per-job percentage is set by the invented job mix

| Offered work, J1 / J2 | N=6 | N=8 |
|---|---|---|
| 50 / 50 (headline) | 0.146 | 0.294 |
| 100 / 0 | 0.325 | 0.512 |
| 20 / 80 | 0.311 | 0.450 |
| 0 / 100 | 0.455 | 0.994 |

Missed share of accepted *work* moves less (0.33 to 0.57% at N=6, 0.51 to 0.93% at N=8) and is the sturdier figure.

### 4. The yearly figure is diluted by months with no risk

Missed over accepted, by month, 5 seeds pooled: N=6 April 0.49%, May 0.76%, October 0.70%, all other months 0.08% or less. N=8 April 1.38%, May 1.12%, October 1.76%, March 0.08%, others 0.13% or less. About three quarters of accepted jobs fall in November to March, when offers (N × 24 server-h/day) equal the full fleet and nearly everything runs at once. In June to August every accepted job is a J2 (about 116 per month × 4 h = 15 server-h/day). The seed range (0.10 to 0.27%) is arrival noise only; the misses come from a handful of days with a wrong heating flag in one weather year.

### 5. Out-of-sample year: the order of magnitude holds, and so does the guard band

2024 (truth: the 2020–24 `ecmwf_ifs` archive file, 29 February dropped; forecast: ifs025 from the same API for 2024; the first 34 to 40 days have no archived forecast and were given a perfect one; 189 heating days, 28,860 kWh). Forecast error 2024: day-1 RMSE 1.34 K, bias +0.65 K; day-7 2.80 K.

| 2024 | N=6 | N=8 |
|---|---|---|
| ifs025, no partner | 0.146 | 0.151 |
| ifs025, 1 h hand-off | 0.000 | 0.003 |
| guard 1 K / 2 K / 3 K | 0.005 / 0.001 / 0.000 | 0.040 / 0.014 / 0.004 |

So "a few tenths of a percent" survives a second year, and the guard band was not just fitted to 2025. The hand-off row shows how event-driven the figure is: 0.07% / 0.13% in 2025, zero in 2024.

### 6. "No coverage cost" for the guard band holds only under saturating offers

With finite contracts the 2 K guard band costs a little: shaped100 coverage 74.1 → 73.8% (N=6) and 86.1 → 86.1% (N=8), accepted jobs 95.2 → 94.4% and 94.5 → 93.7%; flat contract coverage 54.0 → 53.4% and 61.1 → 60.3%.

### 7. Smaller points

- Hand-off rows: seed 1 at N=6 has more misses with a 4 h hand-off (46) than with no partner (34). Ranges overlap (N=8, 1 h: 0.008 to 0.233%). "A partner halves misses" is not a result. The partner is unnamed, never full and starts at once.
- C17: at N=8 the margin does reduce misses steadily (0.294 → 0.245 → 0.200 → 0.137 → 0.101). "Not reliable" is true at N=6 only.
- Server-hours spent on a job that later misses stay in "sold" hours. At most 0.7% of work, so the break-even barely moves, but a customer does not pay for a late job.
- Filler: under the case prices each unpaid filler hour loses 0.2261 CHF (0.3325 electricity minus 0.1064 heat value). Nobody would switch it on. It is a way to show that coverage is a sales result, not an operating mode.
- "Saturating" equals exactly the fleet's maximum (N × 24). The accepted share (56% / 50%) is a property of that choice, not of the scheduler.
- Not modelled, as the investigator says: hardware or network failure, restart cost, runtime uncertainty. These are the usual causes of late jobs. The figure is a lower bound.

## What survives

- A valid, reproducible forecast-error-only missed-deadline figure exists. Honest wording: **roughly 0.1 to 0.6% of accepted jobs over the year without a guard band, 0.5 to 1.8% in April, May and October, below 0.02% with a 2 K guard band** (2025 and 2024, real archived forecasts, saturating offers, no partner, assumed job mix).
- The cause (heating-day cliff) and the fix (guard band) hold under every stress I applied.
- Admission must be a dry run of the scheduler, not a capacity sum (166 misses reproduced).
- Sold-share tables and contract rows as computed.

## What does not survive

- "0.15% / 0.29%" as two-digit headline figures.
- "This error is on the low side, so 2 K synthetic is the prudent upper reading": the sign of the bias matters more than the RMSE.
- "Guard band at no coverage cost" outside saturating offers.
- "The 9 km model has no archived lead-time series."
- "Missed deadlines do not separate N=6 and N=8": with a causal flag it is 0.15% against 0.51%.

## Check scripts (run from a scratch directory; not added to the repo)

Downloads (coordinates only in the request), 2026-11-21:

```bash
V="temperature_2m,temperature_2m_previous_day1,temperature_2m_previous_day2,temperature_2m_previous_day3,temperature_2m_previous_day4,temperature_2m_previous_day5,temperature_2m_previous_day6,temperature_2m_previous_day7"
curl -o prev_ifs025_2024.csv "https://previous-runs-api.open-meteo.com/v1/forecast?latitude=47.56&longitude=7.59&hourly=$V&start_date=2024-01-01&end_date=2024-12-31&timezone=Europe%2FZurich&format=csv&models=ecmwf_ifs025"
curl -o prev_ifs_2025.csv "https://previous-runs-api.open-meteo.com/v1/forecast?latitude=47.56&longitude=7.59&hourly=$V&start_date=2025-01-01&end_date=2025-12-31&timezone=Europe%2FZurich&format=csv&models=ecmwf_ifs"
for s in c21 c25 causal bias y2024 shapedguard mix months; do python3 r2_md_check.py <repo>/analysis <download dir> $s; done
python3 r2_md_check_9km.py <repo>/analysis <download dir>
```

`r2_md_check.py`:

```python
"""Critic checks for r2_deadline_sim.py (not part of the repo; imports it unchanged).
usage: python3 r2_md_check.py <repo>/analysis <dl_dir> <section>
"""
import sys, math
sys.path.insert(0, sys.argv[1])
import r2_deadline_sim as r2
DL, SEC = sys.argv[2], sys.argv[3]
SEEDS = (1, 2, 3, 4, 5)

def show(label, n, fc="ifs025", demand="saturating", handoff=None, **kw):
    rs = [r2.run(n, fc, demand, 0.0, handoff, "idle", 0.0, s) for s in SEEDS]
    m = [r["missed"] * 100 for r in rs]
    f = lambda k: sum(r[k] for r in rs) / len(rs)
    print(f"{label:<34} N={n} {demand:<10} {fc:<9} missed% mean {sum(m)/5:.3f} [{min(m):.3f}-{max(m):.3f}] "
          f"J2 {f('missed_j2')*100:.3f} work {f('missed_work')*100:.3f} missed_n {f('missed_n'):.0f} "
          f"cover {f('coverage')*100:.1f} sold {f('sold_h'):.0f} acc%job {f('acc_jobs')*100:.1f} acc%wrk {f('acc_work')*100:.1f}", flush=True)
    return rs

def read_csv(path):
    rows = []
    for ln in open(path).read().split("\n")[4:]:
        if ln and ln[5:10] != "02-29":
            p = ln.split(",")
            rows.append([float(x) if x not in ("", "NaN") else float("nan") for x in p[1:]])
    return rows

if SEC == "c21":
    r2.forward_fail = lambda *a: []
    r = r2.run(8, "perfect", "saturating", 0.0, None, "idle", 0.0, 1)
    print("C21: no dry-run re-check, perfect forecast, N=8 seed 1: missed_n =", r["missed_n"])

elif SEC == "c25":
    rows = read_csv(DL + "/prev_ifs_2025.csv")
    act = r2.actual_temps()
    e = [rows[i][0] - act[i] for i in range(8760)]
    print("C25: ecmwf_ifs day0 vs reference: max abs diff", max(abs(x) for x in e),
          "; non-NaN previous_day1 values:", sum(1 for r in rows if r[1] == r[1]))

elif SEC == "causal":
    # heating-day flag of a target day taken from the K+1 series (all hours issued <= now)
    def fd(name, seed):
        key = ("causal", name, seed if name.startswith("syn") else 0)
        if key not in r2._CACHE:
            ft = r2.forecast_temps(name, seed)
            guard = float(name[7:]) if name.startswith("ifs025g") else 0.0
            out = [r2.base()["act_d"]]
            for k in range(1, 8):
                kk = min(k + 1, 7)
                dem = []
                for d in range(365):
                    flag = sum(ft[kk][d*24:(d+1)*24]) / 24.0 < 12.0 - guard
                    dem += [(max(0.0, 10.0 * (20.0 - t) / 25.6) if flag else 0.0) + 0.5 for t in ft[k][d*24:(d+1)*24]]
                out.append(dem)
            r2._CACHE[key] = out
        return r2._CACHE[key]
    r2.forecast_demand = fd
    for n in (6, 8):
        show("causal flag (K+1 series)", n)
        show("causal flag + guard 2 K", n, fc="ifs025g2")

elif SEC == "bias":
    b = r2.base()
    for k in range(1, 8):
        bias = r2.err_stats(b["ifs"][k], b["act_t"])[0]
        b["ifs"][k] = [x - bias for x in b["ifs"][k]]
    print("day-1 stats after bias removal:", ["%.2f" % x for x in r2.err_stats(b["ifs"][1], b["act_t"])])
    for n in (6, 8):
        show("ifs025 bias removed per lead", n)
        show("bias removed + guard 2 K", n, fc="ifs025g2")

elif SEC == "y2024":
    act = r2.read_archive_years()["2024"]
    rows = read_csv(DL + "/prev_ifs025_2024.csv")
    assert len(act) == 8760 and len(rows) == 8760
    ifs = [[rows[i][k] for i in range(8760)] for k in range(8)]
    for k in range(1, 8):
        ok = [i for i in range(8760) if ifs[k][i] == ifs[k][i]]
        e = [ifs[k][i] - act[i] for i in ok]
        print(f"2024 ifs025 day {k}: valid hours {len(ok)}, first valid index {ok[0]}, bias {sum(e)/len(e):+.2f}, "
              f"MAE {sum(abs(x) for x in e)/len(e):.2f}, RMSE {math.sqrt(sum(x*x for x in e)/len(e)):.2f}")
        ifs[k] = [ifs[k][i] if ifs[k][i] == ifs[k][i] else act[i] for i in range(8760)]   # NaN -> actual (perfect)
    act_d = r2.demand_from_temps(act)
    r2._CACHE["base"] = dict(act_t=act, act_d=act_d, rows=None, ifs=ifs, ratios=[1] * 7, rho=0.85)
    hd = sum(1 for d in range(365) if sum(act[d*24:(d+1)*24]) / 24 < 12)
    print("2024 truth (ecmwf_ifs archive, 29 Feb dropped): heating days", hd, "demand kWh", round(sum(act_d)))
    for k in (1, 3, 7):
        over = sum(1 for d in range(365) if sum(ifs[k][d*24:(d+1)*24]) / 24 < 12 <= sum(act[d*24:(d+1)*24]) / 24)
        print(f"2024 day {k}: forecast 'heating' but actually not on {over} days")
    for n in (6, 8):
        show("2024 perfect", n, fc="perfect")
        show("2024 ifs025", n)
        show("2024 ifs025 1h handoff", n, handoff=1)
        for g in ("ifs025g1", "ifs025g2", "ifs025g3"):
            show("2024 " + g, n, fc=g)

elif SEC == "shapedguard":
    for n in (6, 8):
        show("shaped100 guard 2 K", n, fc="ifs025g2", demand="shaped100")
        show("flat guard 2 K", n, fc="ifs025g2", demand="flat")

elif SEC == "mix":
    for ws in ((1.0, 0.0), (0.0, 1.0), (0.2, 0.8)):
        r2.WORK_SHARE = ws
        for n in (6, 8):
            show(f"work share J1/J2 = {ws}", n)

elif SEC == "months":
    for n in (6, 8):
        tot = [[0, 0] for _ in range(12)]
        for s in SEEDS:
            r = r2.run(n, "ifs025", "saturating", 0.0, None, "idle", 0.0, s)
            for m in range(12):
                tot[m][0] += r["mon"][m]["missed"]; tot[m][1] += r["mon"][m]["acc"]
        print(f"N={n} missed/accepted by month, 5 seeds pooled: " +
              "  ".join(f"{m+1}:{a}/{b}={a/b*100:.2f}%" for m, (a, b) in enumerate(tot)))
```

`r2_md_check_9km.py`:

```python
"""Critic check: Oct-Dec 2025 with the 9 km IFS archived forecasts (same model as the reference weather)
where they exist (from 2025-10-01), ifs025 elsewhere. usage: python3 r2_md_check_9km.py <repo>/analysis <dl_dir>"""
import sys
sys.path.insert(0, sys.argv[1])
import r2_deadline_sim as r2
rows = [[float(x) if x not in ("", "NaN") else None for x in l.split(",")[1:]]
        for l in open(sys.argv[2] + "/prev_ifs_2025.csv").read().split("\n")[4:] if l]
b = r2.base()
def octdec(label, fc):
    for n in (6, 8):
        mis = acc = tot = 0
        for s in (1, 2, 3, 4, 5):
            r = r2.run(n, fc, "saturating", 0.0, None, "idle", 0.0, s)
            mis += sum(r["mon"][m]["missed"] for m in (9, 10, 11)); acc += sum(r["mon"][m]["acc"] for m in (9, 10, 11))
            tot += r["missed_n"]
        print(f"{label:<28} N={n} {fc:<9} Oct-Dec missed/accepted (5 seeds pooled) {mis}/{acc} = {mis/acc*100:.3f}%   year missed_n mean {tot/5:.0f}", flush=True)
octdec("ifs025 all year", "ifs025"); octdec("ifs025 all year", "ifs025g2")
for k in range(1, 8):
    b["ifs"][k] = [rows[i][k] if rows[i][k] is not None else b["ifs"][k][i] for i in range(8760)]
r2._CACHE = {"base": b}
octdec("9 km IFS from 1 Oct", "ifs025"); octdec("9 km IFS from 1 Oct", "ifs025g2")
```

## Raw output of the check scripts

```text
--- c21
C21: no dry-run re-check, perfect forecast, N=8 seed 1: missed_n = 166
--- c25
C25: ecmwf_ifs day0 vs reference: max abs diff 0.0 ; non-NaN previous_day1 values: 2207
--- causal
causal flag (K+1 series)           N=6 saturating ifs025    missed% mean 0.153 [0.095-0.200] J2 1.185 work 0.550 missed_n 51 cover 79.2 sold 30930 acc%job 56.0 acc%wrk 59.8
causal flag + guard 2 K            N=6 saturating ifs025g2  missed% mean 0.002 [0.000-0.006] J2 0.019 work 0.010 missed_n 1 cover 79.2 sold 30930 acc%job 55.2 acc%wrk 59.4
causal flag (K+1 series)           N=8 saturating ifs025    missed% mean 0.511 [0.423-0.564] J2 1.792 work 0.991 missed_n 200 cover 92.8 sold 36222 acc%job 49.9 acc%wrk 53.2
causal flag + guard 2 K            N=8 saturating ifs025g2  missed% mean 0.009 [0.008-0.010] J2 0.066 work 0.035 missed_n 3 cover 92.8 sold 36222 acc%job 49.3 acc%wrk 52.7
--- bias
day-1 stats after bias removal: ['-0.00', '0.85', '1.12', '0.84']
ifs025 bias removed per lead       N=6 saturating ifs025    missed% mean 0.445 [0.315-0.698] J2 1.312 work 0.767 missed_n 148 cover 79.2 sold 30930 acc%job 56.4 acc%wrk 60.0
bias removed + guard 2 K           N=6 saturating ifs025g2  missed% mean 0.004 [0.000-0.012] J2 0.033 work 0.017 missed_n 1 cover 79.2 sold 30930 acc%job 55.1 acc%wrk 59.4
ifs025 bias removed per lead       N=8 saturating ifs025    missed% mean 0.592 [0.540-0.689] J2 2.190 work 1.211 missed_n 232 cover 92.8 sold 36222 acc%job 49.9 acc%wrk 53.3
bias removed + guard 2 K           N=8 saturating ifs025g2  missed% mean 0.016 [0.013-0.026] J2 0.120 work 0.063 missed_n 6 cover 92.8 sold 36222 acc%job 49.2 acc%wrk 52.7
--- y2024
2024 ifs025 day 1: valid hours 7943, first valid index 817, bias +0.65, MAE 1.00, RMSE 1.34
2024 ifs025 day 2: valid hours 7919, first valid index 841, bias +0.69, MAE 1.10, RMSE 1.44
2024 ifs025 day 3: valid hours 7895, first valid index 865, bias +0.68, MAE 1.22, RMSE 1.60
2024 ifs025 day 4: valid hours 7871, first valid index 889, bias +0.63, MAE 1.43, RMSE 1.88
2024 ifs025 day 5: valid hours 7847, first valid index 913, bias +0.65, MAE 1.61, RMSE 2.11
2024 ifs025 day 6: valid hours 7823, first valid index 937, bias +0.52, MAE 1.88, RMSE 2.45
2024 ifs025 day 7: valid hours 7799, first valid index 961, bias +0.46, MAE 2.18, RMSE 2.80
2024 truth (ecmwf_ifs archive, 29 Feb dropped): heating days 189 demand kWh 28860
2024 day 1: forecast 'heating' but actually not on 0 days
2024 day 3: forecast 'heating' but actually not on 1 days
2024 day 7: forecast 'heating' but actually not on 11 days
2024 perfect                       N=6 saturating perfect   missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 80.8 sold 29133 acc%job 48.1 acc%wrk 56.0
2024 ifs025                        N=6 saturating ifs025    missed% mean 0.146 [0.136-0.178] J2 1.074 work 0.522 missed_n 44 cover 80.7 sold 29107 acc%job 50.7 acc%wrk 55.9
2024 ifs025 1h handoff             N=6 saturating ifs025    missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 80.7 sold 29107 acc%job 50.7 acc%wrk 55.9
2024 ifs025g1                      N=6 saturating ifs025g1  missed% mean 0.005 [0.000-0.017] J2 0.035 work 0.015 missed_n 1 cover 80.8 sold 29133 acc%job 50.6 acc%wrk 55.7
2024 ifs025g2                      N=6 saturating ifs025g2  missed% mean 0.001 [0.000-0.007] J2 0.010 work 0.003 missed_n 0 cover 80.8 sold 29133 acc%job 51.4 acc%wrk 55.7
2024 ifs025g3                      N=6 saturating ifs025g3  missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 80.6 sold 29087 acc%job 51.6 acc%wrk 55.4
2024 perfect                       N=8 saturating perfect   missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 94.4 sold 34064 acc%job 41.9 acc%wrk 49.6
2024 ifs025                        N=8 saturating ifs025    missed% mean 0.151 [0.109-0.227] J2 1.137 work 0.541 missed_n 54 cover 94.4 sold 34064 acc%job 45.2 acc%wrk 49.9
2024 ifs025 1h handoff             N=8 saturating ifs025    missed% mean 0.003 [0.003-0.006] J2 0.021 work 0.011 missed_n 1 cover 94.4 sold 34064 acc%job 45.2 acc%wrk 49.9
2024 ifs025g1                      N=8 saturating ifs025g1  missed% mean 0.040 [0.025-0.053] J2 0.305 work 0.147 missed_n 14 cover 94.4 sold 34064 acc%job 45.4 acc%wrk 49.6
2024 ifs025g2                      N=8 saturating ifs025g2  missed% mean 0.014 [0.003-0.030] J2 0.109 work 0.052 missed_n 5 cover 94.4 sold 34063 acc%job 46.0 acc%wrk 49.6
2024 ifs025g3                      N=8 saturating ifs025g3  missed% mean 0.004 [0.000-0.014] J2 0.036 work 0.016 missed_n 2 cover 94.4 sold 34064 acc%job 46.5 acc%wrk 49.6
--- shapedguard
shaped100 guard 2 K                N=6 shaped100  ifs025g2  missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 73.8 sold 28792 acc%job 94.4 acc%wrk 96.4
flat guard 2 K                     N=6 flat       ifs025g2  missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 53.4 sold 20855 acc%job 63.5 acc%wrk 69.6
shaped100 guard 2 K                N=8 shaped100  ifs025g2  missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 86.1 sold 33603 acc%job 93.7 acc%wrk 95.7
flat guard 2 K                     N=8 flat       ifs025g2  missed% mean 0.000 [0.000-0.000] J2 0.000 work 0.000 missed_n 0 cover 60.3 sold 23536 acc%job 62.1 acc%wrk 67.4
--- mix
work share J1/J2 = (1.0, 0.0)      N=6 saturating ifs025    missed% mean 0.325 [0.281-0.375] J2 0.000 work 0.325 missed_n 202 cover 79.4 sold 31002 acc%job 59.2 acc%wrk 59.2
work share J1/J2 = (1.0, 0.0)      N=8 saturating ifs025    missed% mean 0.512 [0.487-0.543] J2 0.000 work 0.510 missed_n 373 cover 92.9 sold 36264 acc%job 52.1 acc%wrk 52.1
work share J1/J2 = (0.0, 1.0)      N=6 saturating ifs025    missed% mean 0.455 [0.257-0.860] J2 0.455 work 0.417 missed_n 35 cover 79.3 sold 30946 acc%job 60.2 acc%wrk 60.2
work share J1/J2 = (0.0, 1.0)      N=8 saturating ifs025    missed% mean 0.994 [0.866-1.095] J2 0.994 work 0.898 missed_n 91 cover 92.8 sold 36218 acc%job 52.8 acc%wrk 52.8
work share J1/J2 = (0.2, 0.8)      N=6 saturating ifs025    missed% mean 0.311 [0.067-0.467] J2 0.753 work 0.574 missed_n 56 cover 79.2 sold 30934 acc%job 57.1 acc%wrk 60.1
work share J1/J2 = (0.2, 0.8)      N=8 saturating ifs025    missed% mean 0.450 [0.397-0.513] J2 1.265 work 0.933 missed_n 94 cover 92.6 sold 36140 acc%job 50.1 acc%wrk 52.7
--- months
N=6 missed/accepted by month, 5 seeds pooled: 1:0/25193=0.00%  2:0/22500=0.00%  3:0/25184=0.00%  4:68/13791=0.49%  5:51/6731=0.76%  6:0/657=0.00%  7:0/580=0.00%  8:0/582=0.00%  9:4/5203=0.08%  10:119/17004=0.70%  11:0/23181=0.00%  12:0/24964=0.00%
N=8 missed/accepted by month, 5 seeds pooled: 1:0/33447=0.00%  2:0/30100=0.00%  3:23/28213=0.08%  4:193/14017=1.38%  5:70/6249=1.12%  6:0/578=0.00%  7:0/581=0.00%  8:0/581=0.00%  9:6/4579=0.13%  10:273/15542=1.76%  11:7/27854=0.03%  12:0/33660=0.00%
--- 9 km IFS, Oct-Dec
ifs025 all year              N=6 ifs025    Oct-Dec missed/accepted (5 seeds pooled) 119/65149 = 0.183%   year missed_n mean 48
ifs025 all year              N=8 ifs025    Oct-Dec missed/accepted (5 seeds pooled) 280/77056 = 0.363%   year missed_n mean 114
ifs025 all year              N=6 ifs025g2  Oct-Dec missed/accepted (5 seeds pooled) 0/65533 = 0.000%   year missed_n mean 1
ifs025 all year              N=8 ifs025g2  Oct-Dec missed/accepted (5 seeds pooled) 4/77576 = 0.005%   year missed_n mean 4
9 km IFS from 1 Oct          N=6 ifs025    Oct-Dec missed/accepted (5 seeds pooled) 272/66440 = 0.409%   year missed_n mean 79
9 km IFS from 1 Oct          N=8 ifs025    Oct-Dec missed/accepted (5 seeds pooled) 551/78905 = 0.698%   year missed_n mean 169
9 km IFS from 1 Oct          N=6 ifs025g2  Oct-Dec missed/accepted (5 seeds pooled) 0/64877 = 0.000%   year missed_n mean 1
9 km IFS from 1 Oct          N=8 ifs025g2  Oct-Dec missed/accepted (5 seeds pooled) 13/76315 = 0.017%   year missed_n mean 6
--- 9 km IFS error on the hours where it exists (2025-10-01 onward)
day 1 n 2207  ifs9km bias/rmse -0.18 1.00   ifs025 same hours 0.47 1.26
day 3 n 2159  ifs9km bias/rmse -0.05 1.31   ifs025 same hours 0.58 1.55
day 7 n 2063  ifs9km bias/rmse -0.35 2.66   ifs025 same hours 0.33 2.84
```
