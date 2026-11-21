"""Which days and what time compression suit the live demo? (round 1, 2026-11-21)

Exploratory only: NOT the scheduler. It replays the 'follow' rule from
analysis/baseline_sweep.py hour by hour (same constants, imported from there)
and counts how often a job bound to one server slot would be paused and
resumed on a January day and a July day. Slot j runs in an hour iff at least
j servers run in that hour (slot 1 = the last server to be switched off).

It also tries one illustrative variant, a tank hysteresis band (stop when the
tank is full, restart only once it has dropped by `band` kWh), to see whether
the pauses become long enough to be watched in a time-compressed demo, and
whether such a band changes the yearly figures. The band is a suggestion to
test, not a decided policy.

    python3 analysis/demo_day_timing.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import load, P_EL, REC, TANK, PRICE, HEAT_VALUE  # noqa: E402

Q1 = REC * P_EL


def hourly(rows, n, band=0.0, summer_cap=None):
    """Return per-hour (time, demand, k, soc_after, unmet). band=0 reproduces 'follow'."""
    soc = 0.0
    charging = True
    out = []
    for t, sh, dhw in rows:
        d = sh + dhw
        cap = n if (summer_cap is None or sh > 0) else min(n, summer_cap)
        kmax = min(cap, int((d + TANK - soc) / Q1 + 1e-9))
        if band > 0:
            if not charging and (soc <= TANK - band + 1e-9 or soc < d):
                charging = True
            k = kmax if charging else 0
            if charging and kmax == 0:
                charging = False
        else:
            k = kmax
        avail = soc + k * Q1
        u = min(d, avail)
        soc = avail - u
        out.append((t, d, k, soc, d - u))
    return out


def year_figures(h, n):
    run_h = sum(x[2] for x in h)
    dem = sum(x[1] for x in h)
    used = dem - sum(x[4] for x in h)
    elec = run_h * P_EL * PRICE
    return used / dem, run_h / (n * 8760), run_h, (elec - used * HEAT_VALUE) / run_h


def day(h, date):
    return [x for x in h if x[0].startswith(date)]


def slot_pattern(d, slot):
    return "".join("#" if x[2] >= slot else "." for x in d)


def transitions(pat):
    pauses = sum(1 for a, b in zip(pat, pat[1:]) if a == "#" and b == ".")
    resumes = sum(1 for a, b in zip(pat, pat[1:]) if a == "." and b == "#")
    runs = [len(s) for s in pat.replace("#", " ").split()]   # lengths of paused stretches
    return pauses, resumes, (min(runs) if runs else 0), (max(runs) if runs else 0)


def describe(h, date, n, slots):
    d = day(h, date)
    print(f"  {date}: demand {sum(x[1] for x in d):6.1f} kWh, server-hours {sum(x[2] for x in d):3d}, "
          f"unmet (backup) {sum(x[4] for x in d):5.1f} kWh, servers per hour: "
          + " ".join(str(x[2]) for x in d))
    for s in slots:
        pat = slot_pattern(d, s)
        p, r, mn, mx = transitions(pat)
        print(f"      slot {s}: {pat}  pauses {p}, resumes {r}, paused stretches {mn}-{mx} h")


if __name__ == "__main__":
    rows = load()
    N = 8
    days = sorted({t[:10] for t, _, _ in rows})
    dem = {dd: 0.0 for dd in days}
    for t, sh, dhw in rows:
        dem[t[:10]] += sh + dhw
    jan = [dd for dd in days if dd[5:7] == "01"]
    jul = [dd for dd in days if dd[5:7] == "07"]
    cold = max(jan, key=lambda dd: dem[dd])
    mild = min(jan, key=lambda dd: dem[dd])
    print(f"January 2025: highest-demand day {cold} ({dem[cold]:.1f} kWh), lowest-demand day {mild} ({dem[mild]:.1f} kWh)")
    print(f"July 2025: demand per day min {min(dem[dd] for dd in jul):.1f} / max {max(dem[dd] for dd in jul):.1f} kWh "
          f"(all {len(jul)} days identical: {len({round(dem[dd], 6) for dd in jul}) == 1})")

    variants = [("follow (band 0), as in baseline_sweep.py", dict()),
                ("band 2 kWh", dict(band=2.0)),
                ("band 4 kWh", dict(band=4.0)),
                ("band 2 kWh + max 1 server when no space heating", dict(band=2.0, summer_cap=1)),
                ("band 4 kWh + max 1 server when no space heating", dict(band=4.0, summer_cap=1))]
    for label, kw in variants:
        h = hourly(rows, N, **kw)
        cov, util, run_h, be = year_figures(h, N)
        print(f"\n== N={N}, {label} ==")
        print(f"  year: coverage {cov*100:.1f}%, utilisation {util*100:.1f}%, server-hours {run_h:.0f}, break-even {be:.4f} CHF/server-h")
        describe(h, cold, N, (8,))
        describe(h, mild, N, (5, 8))
        describe(h, "2025-07-15", N, (1,))
        jd = [transitions(slot_pattern(day(h, dd), 1)) for dd in jul]
        both = sum(1 for p, r, _, _ in jd if p >= 1 and r >= 1)
        print(f"  July: days on which slot 1 is both paused and resumed: {both} of {len(jul)}; "
              f"pauses per day min {min(x[0] for x in jd)} / max {max(x[0] for x in jd)}")

    print("\n== time compression: real seconds per simulated hour ==")
    print(f"{'s per sim-h':>11} {'one day':>8} {'Jan+Jul':>8} {'1 h pause':>10} {'4 h pause':>10} {'8 h pause':>10}")
    for s in (1.0, 1.5, 2.0, 2.5, 3.0, 5.0):
        print(f"{s:>11.1f} {24*s:>7.0f}s {48*s:>7.0f}s {s:>9.1f}s {4*s:>9.1f}s {8*s:>9.1f}s")
