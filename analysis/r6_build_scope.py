"""Round 6: build-scope audit. What will the team's own scheduler show at 21:00?

ASSESSMENT ONLY. This is NOT the team's scheduler and must not become it. It writes no
repository files (one temp file in the system temp dir, deleted again).

    python3 analysis/r6_build_scope.py             # all sections (about 1-2 min, all cores)
    python3 analysis/r6_build_scope.py --loc-only  # sections 1-3 only (instant)
    python3 analysis/r6_build_scope.py --procs 1   # no multiprocessing

Standard library only. Imports, without editing them:
  r2_deadline_sim, r3_policy_check, r4_headline, r5_miss_stress  (for line counts and runs)

Sections
  1  Line census: non-blank, non-comment, non-docstring lines of the analysis-script code
     that implements each scheduler rule (the anchors for the person-hour estimate).
  2  Person-hour estimate per MUST / OPTIONAL row (and the never-cut items around the core),
     from the anchor line counts and two ASSUMED coding rates.
  3  Revised Saturday table from 11:30: build hours per role vs assigned task hours, with the
     cut line. Windows and focus factor are ASSUMPTIONS.
  4  What the team scheduler's OWN missed-deadline line will read at each stage reached by
     21:00 (expected values, computed with the analysis functions, headline shaped100 offers,
     seed 1 = the offer CSV), incl. a whole-house outage the scheduler is told about.
  5  Offer CSV reproducibility: regenerate with r4_headline.write_offers and compare bytes
     (the CSV is NOT tracked in git as of the round-6 snapshot).
"""
import ast
import multiprocessing as mp
import os
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# ---------------------------------------------------------------- 1. line census
_SRC = {}


def src(name):
    if name not in _SRC:
        text = (HERE / name).read_text()
        tree = ast.parse(text)
        doc = set()
        funcs = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.setdefault(node.name, (node.lineno, node.end_lineno))
                b0 = node.body[0] if node.body else None
                if isinstance(b0, ast.Expr) and isinstance(getattr(b0, "value", None), ast.Constant) \
                        and isinstance(b0.value.value, str):
                    doc.update(range(b0.lineno, b0.end_lineno + 1))
        _SRC[name] = (text.split("\n"), funcs, doc)
    return _SRC[name]


def is_code(name, i):
    lines, _, doc = src(name)
    s = lines[i - 1].strip()
    return bool(s) and not s.startswith("#") and i not in doc


def count(name, a, b, token=None):
    """Code lines in [a, b] (1-based, inclusive); with token: only lines containing it."""
    lines = src(name)[0]
    return sum(1 for i in range(a, b + 1) if is_code(name, i) and (token is None or token in lines[i - 1]))


def fspan(name, func):
    return src(name)[1][func]


def find(name, a, b, marker, exact=False):
    lines = src(name)[0]
    for i in range(a, b + 1):
        s = lines[i - 1]
        if (s.strip() == marker) if exact else (marker in s):
            return i
    raise KeyError(f"{name}:{marker}")


def block(name, func, start, end, end_inclusive=True, exact_end=False):
    a, b = fspan(name, func)
    i = find(name, a, b, start)
    j = find(name, i + 1, b, end, exact=exact_end)
    return i, (j if end_inclusive else j - 1)


P3, R2, H4, S5, PR = ("r3_policy_check.py", "r2_deadline_sim.py", "r4_headline.py",
                      "r5_miss_stress.py", "pause_resume_probe.py")


def census():
    c = {}
    a, b = fspan(P3, "step_permit")
    band = find(P3, a, b, 'if rule == "band"')
    hold = find(P3, a, b, 'if rule == "hold"')
    rais = find(P3, a, b, "raise ValueError")
    c["permit_follow"] = (count(P3, a, band - 1), f"{P3} step_permit() lines {a}-{band-1} (cap, kmax, follow)")
    c["permit_band"] = (count(P3, band, hold - 1), f"{P3} step_permit() lines {band}-{hold-1} (band branch)")
    c["permit_hold"] = (count(P3, hold, rais - 1), f"{P3} step_permit() lines {hold}-{rais-1} (hold branch, CUT)")
    i, j = block(P3, "run", "avail = soc + ran * Q1", "dumped += dump")
    c["energy"] = (count(P3, i, j), f"{P3} run() lines {i}-{j} (tank balance, dump)")
    i, j = block(P3, "run", "jobs that can no longer finish", "jobs = keep")
    c["expire"] = (count(P3, i, j), f"{P3} run() lines {i}-{j} (expire = missed)")
    i, j = block(P3, "run", "if arr[0] or arr[1]:", "# execution on the actual permits", end_inclusive=False)
    c["adm_block"] = (count(P3, i, j), f"{P3} run() lines {i}-{j} (forecast permits, slack, accept, take-back)")
    c["adm_stats"] = (count(P3, i, j, "summer") + count(P3, i, j, "mon[m]") + count(P3, i, j, "off_w"),
                      f"{P3} run() lines {i}-{j} containing summer / mon[m] / off_w (statistics only)")
    ai, aj = block(P3, "run", 'if P["aware"] and r > 0:', "cf = cfe")
    c["adm_aware"] = (count(P3, ai, aj), f"{P3} run() lines {ai}-{aj} (restart-aware derating, CUT)")
    a, b = fspan(P3, "run")
    c["adm_branch"] = (count(P3, i, j, 'P["adm"]') + count(P3, i, j, "arule"),
                       f"{P3} run() lines {i}-{j} containing P[\"adm\"] / arule (variant switches)")
    a, b = fspan(R2, "forward_fail")
    c["forward_fail"] = (count(R2, a, b), f"{R2} forward_fail() lines {a}-{b} (EDF dry run)")
    i, j = block(P3, "run", "if r <= 0:", "else:", end_inclusive=False, exact_end=True)
    c["edf_exec"] = (count(P3, i, j), f"{P3} run() lines {i}-{j} (EDF execution, restart 0)")
    i2, j2 = block(P3, "run", "warm = float(min(cap, on_prev))", "ran = work + new_starts * r")
    c["restart_exec"] = (count(P3, i2, j2) + 1, f"{P3} run() lines {i2-1}-{j2} (restart inside execution, CUT)")
    a, b = fspan(H4, "run")
    c["pin"] = (count(H4, a, b, "pin"), f"{H4} run() lines {a}-{b} containing 'pin' (R6 demo-date pin)")
    a, b = fspan(S5, "read_offer_csv")
    c["offers_csv"] = (count(S5, a, b), f"{S5} read_offer_csv() lines {a}-{b}")
    a, b = fspan(R2, "read_prev_runs")
    c["fc_read"] = (count(R2, a, b), f"{R2} read_prev_runs() lines {a}-{b}")
    a, b = fspan(R2, "demand_from_temps")
    c["fc_formula"] = (count(R2, a, b), f"{R2} demand_from_temps() lines {a}-{b} (case formula + guard threshold)")
    a, b = fspan(P3, "fc_demand")
    c["fc_demand"] = (count(P3, a, b), f"{P3} fc_demand() lines {a}-{b}")
    a, b = fspan(P3, "run")
    c["fc_lead"] = (count(P3, a, b, "LEAD") + count(P3, a, b, "lambda L"), f"{P3} run() lines containing LEAD / lambda L (causal lead)")
    a, b = fspan(R2, "forecast_temps")
    k = find(R2, a, b, 'if name == "persist":')
    c["persist"] = (count(R2, k, k + 1), f"{R2} forecast_temps() lines {k}-{k+1} (persistence)")
    a, b = fspan(S5, "run")
    c["pad"] = (count(S5, a, b, "pad") - count(S5, a, b, "o, pad"), f"{S5} run() lines containing 'pad' (runtime pad)")
    i, j = block(S5, "run", "while oi < len(outs)", "down_h += n - n_up")
    c["outage_exec"] = (count(S5, i, j) - count(S5, i, j, "down_h"), f"{S5} run() lines {i}-{j} (servers up this hour)")
    c["outage_dry"] = (count(S5, a, b, "nav") + count(S5, a, b, "fail_aware"),
                       f"{S5} run() lines containing nav / fail_aware (dry run sees the outage)")
    a, b = fspan(S5, "outages")
    c["outage_gen"] = (count(S5, a, b), f"{S5} outages() lines {a}-{b} (random failure generator, not needed)")
    a, b = fspan(H4, "pause_resume_days")
    c["demo_finder"] = (count(H4, a, b), f"{H4} pause_resume_days() lines {a}-{b}")
    a, b = fspan(P3, "run")
    c["run_total"] = (count(P3, a, b), f"{P3} run() lines {a}-{b} (whole yearly loop incl. statistics)")
    i = find(P3, a, b, "closed = [done[i] + missed[i]")
    c["keyfig"] = (count(P3, i, b), f"{P3} run() lines {i}-{b} (key-figure dict)")
    for f in ("worker", "spawn", "ps", "exp_signals", "exp_checkpoint"):
        a, b = fspan(PR, f)
        c["probe_" + f] = (count(PR, a, b), f"{PR} {f}() lines {a}-{b}")
    a, b = fspan(PR, "exp_checkpoint")
    c["probe_ckpt_prints"] = (count(PR, a, b, "print("), f"{PR} exp_checkpoint() lines containing print(")
    return c


# ---------------------------------------------------------------- 2. person-hours
RATE_PORT = 40.0   # ASSUMPTION: lines/h when re-writing logic that exists in an analysis script
RATE_FRESH = 20.0  # ASSUMPTION: lines/h for logic written from a spec, incl. first debugging


def rows(c):
    """(id, class, rule, LOC for the team's version, how LOC was derived, check h lo, check h hi, owner, check)."""
    v = {k: x[0] for k, x in c.items()}
    adm = v["adm_block"] - v["adm_stats"] - v["adm_aware"] - v["adm_branch"] + v["forward_fail"] + 3 + 2
    return [
        ("M1", "MUST", "R2 heat permit (one function) + tank balance", v["permit_follow"] + v["energy"],
         "permit_follow + energy", 0.25, 0.5, "A", "N=6 79.58%, 31,067 server-h (baseline_sweep)"),
        ("M2", "MUST", "R5 EDF assign, pause the rest (job queue, done/paused ids)", v["edf_exec"] + 10,
         "edf_exec + 10 (Job record, paused-id list, trace fields; assumption)", 0.25, 0.5, "A",
         "done + missed + open = accepted; sold h <= permit h"),
        ("M3", "MUST", "R1 expire = missed", v["expire"], "expire", 0.1, 0.25, "A",
         "without admission, shaped100: about 2.6% / 2.9% missed (r3 row F)"),
        ("M4", "MUST", "R6 pin on demo date, excluded from denominator", v["pin"] + 2,
         "pin + 2 (denominator exclusion; assumption)", 0.25, 0.5, "A",
         "coverage 73.675% -> 73.673% (N=6, r4_headline s.5)"),
        ("M5", "MUST", "Offers read from the offer CSV (both drivers)", v["offers_csv"], "offers_csv", 0.1, 0.25,
         "A", "33,676 / 39,244 offers"),
        ("M6", "MUST", "R4 admission dry run, perfect forecast (incl. EDF dry run)", adm,
         "adm_block - stats - restart-aware - variant switches + forward_fail + 3 (perfect source) + 2 (read "
         "forecast_demand[L] and n_avail[L] from obs: the hooks for O3 and N1)",
         0.5, 1.5, "A or B", "exactly 0 missed; 0 of 31,908 / 0 of 36,771 accepted, seed 1"),
        ("O1", "OPTIONAL", "R3 cap + band (inside the same permit function)", v["permit_band"] + 2,
         "permit_band + 2 (cap test, state var)", 0.25, 0.5, "A", "379 / 891 starts at 8 kWh (unlimited)"),
        ("O2", "OPTIONAL", "R7 persistence forecast", v["persist"] + v["fc_formula"] + v["fc_lead"],
         "persist + fc_formula + fc_lead", 0.25, 0.5, "A", "stage-2 line in section 4"),
        ("O3", "OPTIONAL", "R7 archived ifs025 + 2 K guard (builder outside decide())",
         v["fc_read"] + v["fc_formula"] + v["fc_demand"] + v["fc_lead"] + 3,
         "fc_read + fc_formula + fc_demand + fc_lead + 3 (168-h vector per hour)", 0.5, 1.0, "A",
         "stage-3 line in section 4; day-1 RMSE 1.16 K"),
        ("O3c", "OPTIONAL", "  live driver calls the same forecast_vector() (with the hook)", 3,
         "assumption (import + 1 call)", 0.1, 0.25, "B", "trace test still green with forecast on"),
        ("O4", "OPTIONAL", "Runtime pad (book runtime x 1.3)", v["pad"], "pad", 0.5, 1.0, "A",
         "re-run every key figure (pad moves acceptance and coverage)"),
        ("O5", "OPTIONAL", "Accounting lines: restart, tank loss, DHW share, two columns", 14,
         "assumption: 2 + 1 + 1 + 10 printer", 0.25, 0.5, "D", "BE 0.2278 / 0.2286 with 15-min restart line"),
        ("O6", "OPTIONAL", "Demo-day finder on the final run (pin applied)", v["demo_finder"], "demo_finder",
         0.1, 0.25, "A", "N=6 2025-07-15 slot 1, P 02 R 18 (r4_headline s.5)"),
        ("N1", "PROPOSED", "Whole-house outage, scheduler told (driver builds n_avail[0..167])",
         v["outage_exec"] + 2,
         "outage_exec (interval -> servers up) + 2 (CLI flag, printer line); core hook counted in M6",
         0.25, 0.5, "B", "section 4 outage lines (April/October 24-72 h)"),
        ("N1x", "PROPOSED", "  same without the hook (edit decide() after the fact)",
         v["outage_exec"] + v["outage_dry"] + 4,
         "outage_exec + outage_dry + 4", 0.5, 1.0, "A", "trace test re-run, 17:15 checks re-run"),
        ("K1", "NEVER-CUT", "Yearly driver accumulators + key-figure dict", v["keyfig"] + 10,
         "keyfig + 10 (loop, accumulators; assumption)", 0.25, 0.5, "A", "seven figures from one command"),
        ("K2", "NEVER-CUT", "Key-figure printer (7 figures, x of y, BE twice, label)", 30,
         "assumption (no anchor: r3/r4 printers carry statistics)", 0.25, 0.5, "D", "matches r4_headline s.3 seed 1"),
        ("K3", "NEVER-CUT", "Live driver: spawn in own session, SIGSTOP/SIGCONT, ps state T",
         v["probe_spawn"] + v["probe_ps"] + 15, "probe spawn + ps + 15 (hour loop calling decide)", 0.5, 1.0, "C",
         "ps -o state= shows T after PAUSE"),
        ("K4", "NEVER-CUT", "Live replay from 00:00 snapshot incl. job queue + offers", 30,
         "assumption (r3 critic: 30-60 min)", 0.25, 0.5, "C", "same 24 trace lines as yearly run"),
        ("K5", "NEVER-CUT", "Trace-equality test + SHA-256 header", 25, "assumption (r3 scope file)", 0.25, 0.5, "C",
         "test green"),
        ("K6", "NEVER-CUT", "J1 batch loop, atomic checkpoint, --resume", v["probe_worker"] + 20,
         "probe worker + 20 (mlx_whisper call, audio list)", 0.25, 0.5, "B", "resume continues from checkpoint"),
        ("K7", "NEVER-CUT", "Checkpoint-restart mode behind a flag + its test",
         v["probe_exp_checkpoint"] - v["probe_ckpt_prints"],
         "probe exp_checkpoint minus its print() lines", 0.25, 0.5, "B/C", "one tested restart"),
        ("K8", "NEVER-CUT", "Terminal view of one day (job-level numbers)", 40, "assumption", 0.25, 0.5, "C",
         "readable from the back"),
        ("K8s", "NEVER-CUT", "  reduced: formatted trace line per hour, no layout", 15, "assumption", 0.1, 0.25, "C",
         "one line per simulated hour, PID state shown"),
        ("K9", "OPTIONAL", "Dashboard page: six tiles from the printer's JSON (static HTML)", 40, "assumption",
         0.25, 0.5, "C", "same values as the printer"),
    ]


SPEED = {"unassisted": 1.0, "AI-assisted": 2.0}   # ASSUMPTION: an AI coding assistant doubles both line rates;
                                                 # check time is not reduced


def ph(loc, clo, chi, speed=1.0):
    return loc / (RATE_PORT * speed) + clo, loc / (RATE_FRESH * speed) + chi


# ---------------------------------------------------------------- 3. revised table budget
FOCUS = 0.75   # ASSUMPTION: share of a build window that becomes finished, checked work


def hm(s):
    h, m = s.split(":")
    return int(h) + int(m) / 60.0


# windows from 11:30 to 21:00: (start, end, kind). kind 'build' counts toward capacity.
WINDOWS = {
    "A": [("11:30", "12:15", "build"), ("12:15", "12:45", "lunch"), ("12:45", "14:45", "build"),
          ("14:45", "15:00", "push draft"), ("15:00", "18:00", "build"), ("18:00", "18:40", "dinner"),
          ("18:40", "19:45", "build"), ("19:45", "21:00", "rehearse")],
    "B": [("11:30", "12:15", "build"), ("12:15", "12:45", "lunch"), ("12:45", "14:45", "build"),
          ("14:45", "15:00", "push draft"), ("15:00", "18:00", "build"), ("18:00", "18:40", "dinner"),
          ("18:40", "20:15", "build"), ("20:15", "21:00", "rehearse")],
    "C": [("11:30", "12:15", "build"), ("12:15", "12:45", "lunch"), ("12:45", "14:15", "build"),
          ("14:15", "14:45", "draft check"), ("14:45", "15:00", "push draft"), ("15:00", "18:00", "build"),
          ("18:00", "18:40", "dinner"), ("18:40", "19:45", "build"), ("19:45", "21:00", "rehearse")],
    "D": [("11:30", "12:15", "build"), ("12:15", "12:45", "lunch"), ("12:45", "14:15", "build"),
          ("14:15", "14:45", "draft check"), ("14:45", "15:30", "submit draft"), ("15:30", "18:00", "build"),
          ("18:00", "18:40", "dinner"), ("18:40", "19:45", "build"), ("19:45", "21:00", "rehearse")],
}

# non-code tasks per role (hours lo, hi): ASSUMPTIONS sized on the slots of docs/overnight.md
NONCODE_CURRENT = {
    "B": [("energy run (>= 5 min, plugged) + r3_income", 0.5, 0.75), ("scaling write-up with MLPerf rows", 0.5, 0.75),
          ("3 repeat runs + notes", 0.5, 0.75), ("model-load time, live audio sizing", 0.25, 0.5),
          ("README check on a clean laptop", 0.5, 0.75)],
    "C": [("60-90 s raw pause recording", 0.25, 0.5), ("wifi-off rehearsal of the one-command demo", 0.25, 0.5)],
    "D": [("README skeleton -> README", 0.75, 1.0), ("assumptions list complete with status", 0.75, 1.0),
          ("does-not-pay-off sentences, description", 0.5, 0.75), ("pitch script to the second", 1.0, 1.5),
          ("slides (4 max)", 1.0, 1.5), ("mentor slot", 0.5, 0.5)],
}
NONCODE_REVISED = {
    "B": [("energy run (>= 5 min, plugged) + r3_income", 0.5, 0.75), ("scaling write-up with MLPerf rows", 0.5, 0.75),
          ("model-load time, live audio sizing", 0.25, 0.5), ("README check on a clean laptop", 0.5, 0.75)],
    "C": [("60-90 s raw pause recording", 0.25, 0.5), ("wifi-off rehearsal of the one-command demo", 0.25, 0.5)],
    "D": [("README + real-vs-analysis table (edit r6-real-vs-analysis.md)", 0.5, 0.75),
          ("assumptions list (edit from docs/overnight.md)", 0.5, 1.0),
          ("does-not-pay-off sentences, description (edit)", 0.25, 0.5), ("pitch script to the second", 1.0, 1.5),
          ("slides (4 max; 1 more hour after the freeze if needed)", 1.0, 1.5)],
}

# docs/overnight.md Saturday table as it stands (rows read off the 11:20-21:00 cells)
ASSIGN_CURRENT = {
    "A": ["M2", "M5", "M3", "M6", "O2", "O3", "O4", "O5", "O6"],
    "B": [],
    "C": ["K4", "K5", "K8", "K7", "O3c"],
    "D": ["K2"],
}
# revised table (this file's proposal); order = priority, cut from the end
ASSIGN_REVISED = {
    "A": ["M2", "M3", "M4", "M6", "O6"],
    "B": ["M5", "K1", "K2", "O3", "O3c", "N1"],
    "C": ["K8s", "K4", "K5", "K7", "K9"],
    "D": [],
}
DONE_BY_1130 = ["M1", "O1", "K3", "K6"]   # ASSUMPTION: the 09:30-11:20 slots of docs/overnight.md landed
                                          # (permit + band, J1 loop with checkpoint, live driver on a stub +
                                          # Integration 1). If not, add them first; see the research file.


def budget(R, assign, noncode, speed):
    byid = {r[0]: r for r in R}
    out = []
    for role in "ABCD":
        gross = sum(hm(b) - hm(a) for a, b, k in WINDOWS[role] if k == "build")
        cap = gross * FOCUS
        lo = hi = 0.0
        lines = []
        for lab, l, h in noncode.get(role, []):
            lo += l
            hi += h
            lines.append((lab, l, h, lo, hi, "non-code"))
        for rid in assign[role]:
            r = byid[rid]
            l, h = ph(r[3], r[5], r[6], speed)
            lo += l
            hi += h
            lines.append((f"{rid} {r[2].strip()}", l, h, lo, hi, r[1]))
        out.append((role, gross, cap, lines))
    return out


def print_budget(R, assign, noncode, speed_name):
    speed = SPEED[speed_name]
    tl_lo = tl_hi = tcap = 0.0
    for role, gross, cap, lines in budget(R, assign, noncode, speed):
        tcap += cap
        print(f"  role {role}: build windows {gross:.2f} h gross -> {cap:.2f} h effective")
        cut_marked = False
        for lab, l, h, clo, chi, cls in lines:
            flag = ""
            if not cut_marked and chi > cap + 1e-9:
                flag = "   <-- high estimate passes capacity"
                cut_marked = True
            if (clo + chi) / 2 > cap + 1e-9:
                flag = "   <-- midpoint passes capacity (cut line)"
            if clo > cap + 1e-9:
                flag = "   <-- even the low estimate passes capacity"
            print(f"     {lab:<66} {l:>5.2f}-{h:<5.2f} cum {clo:>5.2f}-{chi:<5.2f} [{cls}]{flag}")
        lo, hi = (lines[-1][3], lines[-1][4]) if lines else (0.0, 0.0)
        tl_lo += lo
        tl_hi += hi
        mid = (lo + hi) / 2
        verdict = ("fits even at the high estimate" if hi <= cap + 1e-9 else
                   ("fits at the midpoint" if mid <= cap + 1e-9 else
                    ("fits at the low estimate only" if lo <= cap + 1e-9 else "does NOT fit")))
        print(f"     role {role} load {lo:.2f}-{hi:.2f} h (midpoint {mid:.2f}) vs capacity {cap:.2f} h -> {verdict}")
    print(f"  ALL ROLES: load {tl_lo:.2f}-{tl_hi:.2f} h vs capacity {tcap:.2f} h")


# ---------------------------------------------------------------- 4. stage preview
def _task(spec):
    import r3_policy_check as P3m
    import r5_miss_stress as S
    label, n, kind, kw = spec
    if kind == "r5":
        r = S.run(n, S.cfg(**kw), 1)
        return (label, n), dict(missed=r["missed_n"], closed=r["closed_n"], acc=r["acc_jobs"], cov=r["coverage"],
                                accepted=r["accepted"], offered=r["offered"])
    r = P3m.run(n, P3m.pol(**kw), "shaped100", 1)
    return (label, n), dict(missed=r["missed_n"], closed=r["done_n"] + r["missed_n"], acc=r["acc_jobs"],
                            cov=r["coverage"], accepted=r["accepted"], offered=r["offered"])


def day_hour(month, day=15):
    import r2_deadline_sim as R
    return (sum(R.MDAYS[:month - 1]) + day - 1) * 24


def stage_specs():
    band = dict(rule="band", band=8.0, cap1=True)
    S = [
        ("S0 no admission (every offer accepted)", "r3", dict(adm="all", **band)),
        ("S1 admission, perfect forecast", "r5", dict(fc="perfect")),
        ("S2 admission, persistence, no guard", "r3", dict(fc="persist", guard=0.0, **band)),
        ("S2g admission, persistence + 2 K guard", "r3", dict(fc="persist", guard=2.0, **band)),
        ("S3n admission, archived ifs025, no guard", "r5", dict(guard=0.0)),
        ("S3 admission, archived ifs025 + 2 K guard (plan)", "r5", dict()),
        ("S3p S3 + runtime pad 30%, no overrun", "r5", dict(pad=0.30)),
    ]
    for m, mname in ((1, "Jan"), (4, "Apr"), (10, "Oct")):
        for dur in (24, 72):
            S.append((f"S3+H house down {dur} h from 15 {mname} 00:00, told", "r5h", dict(m=m, dur=dur, aware=True)))
    S.append(("S3+H house down 72 h from 15 Apr, NOT told", "r5h", dict(m=4, dur=72, aware=False)))
    S.append(("S3+H house down 72 h from 15 Oct, NOT told", "r5h", dict(m=10, dur=72, aware=False)))
    specs = []
    for lab, kind, kw in S:
        for n in (6, 8):
            if kind == "r5h":
                st = day_hour(kw["m"])
                specs.append((lab, n, "r5", dict(fail_at=(st, n, kw["dur"]), fail_aware=kw["aware"])))
            else:
                specs.append((lab, n, kind, kw))
    return [x[0] for x in S], specs


def all_months_outage_specs():
    specs = []
    for n in (6, 8):
        for m in range(1, 13):
            for dur in (24, 72):
                specs.append((f"M{m:02d} {dur}h", n, "r5", dict(fail_at=(day_hour(m), n, dur), fail_aware=True)))
    return specs


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[1:]
    procs = int(argv[argv.index("--procs") + 1]) if "--procs" in argv else None
    t0 = time.time()
    print("r6_build_scope.py. Assessment only; not the team scheduler. Stand-in reference house 2025. Currency CHF (no money figures here).\n")

    c = census()
    print("== 1. Line census of the analysis code that implements each rule ==")
    print("  (non-blank, non-comment, non-docstring lines; counted with ast + text markers)")
    for k, (n, where) in c.items():
        print(f"  {k:<20} {n:>4}  {where}")

    R = rows(c)
    print(f"\n== 2. Person-hours per row (ASSUMED rates: port {RATE_PORT:.0f} lines/h, fresh {RATE_FRESH:.0f} lines/h, plus check time) ==")
    print(f"  {'id':<4} {'class':<9} {'LOC':>4} {'unassisted':>11} {'AI-assisted':>12}  owner  rule  |  LOC basis  |  check")
    tot = {}
    for rid, cls, rule, loc, basis, clo, chi, owner, chk in R:
        lo, hi = ph(loc, clo, chi)
        lo2, hi2 = ph(loc, clo, chi, SPEED["AI-assisted"])
        t = tot.setdefault(cls, [0, 0.0, 0.0, 0.0, 0.0])
        if not rid.endswith(("s", "x")):
            t[0] += loc
            t[1] += lo
            t[2] += hi
            t[3] += lo2
            t[4] += hi2
        print(f"  {rid:<4} {cls:<9} {loc:>4} {lo:>5.2f}-{hi:<5.2f} {lo2:>5.2f}-{hi2:<5.2f}  {owner:<6} {rule}  |  {basis}  |  {chk}")
    for cls, (loc, lo, hi, lo2, hi2) in tot.items():
        print(f"  total {cls:<9} {loc:>4} lines, {lo:.1f}-{hi:.1f} person-h unassisted, {lo2:.1f}-{hi2:.1f} AI-assisted "
              f"(reduced/alternative rows K8s, N1x not summed)")
    core_must = sum(r[3] for r in R if r[1] == "MUST")
    core_opt = sum(r[3] for r in R if r[0] in ("O1", "O3"))
    print(f"  core decide() size, MUST rows M1-M6: {core_must} lines; + cap/band + archived forecast builder: {core_must + core_opt}")

    print(f"\n== 3. Saturday from 11:30: capacity vs load per role (FOCUS {FOCUS} = ASSUMPTION) ==")
    print(f"  already done by 11:30 (ASSUMPTION): {', '.join(DONE_BY_1130)}")
    byid = {r[0]: r for r in R}
    for sp in SPEED:
        rem_must = [byid[x] for x in ("M2", "M3", "M4", "M5", "M6")]
        rem_nc = [byid[x] for x in ("K1", "K2", "K4", "K5", "K7", "K8s")]
        a = [ph(r[3], r[5], r[6], SPEED[sp]) for r in rem_must]
        b = [ph(r[3], r[5], r[6], SPEED[sp]) for r in rem_nc]
        print(f"  [{sp}] remaining MUST rows M2-M6: {sum(x[0] for x in a):.2f}-{sum(x[1] for x in a):.2f} h; "
              f"remaining never-cut code K1, K2, K4, K5, K7, K8s: {sum(x[0] for x in b):.2f}-{sum(x[1] for x in b):.2f} h")
    for title, assign, nc in (("3a. CURRENT table in docs/overnight.md", ASSIGN_CURRENT, NONCODE_CURRENT),
                              ("3b. REVISED table (this round)", ASSIGN_REVISED, NONCODE_REVISED)):
        for sp in SPEED:
            print(f"\n  -- {title}, {sp} rates --")
            print_budget(R, assign, nc, sp)
    if "--loc-only" in argv:
        print(f"\n(done in {time.time()-t0:.1f} s)")
        return

    print("\n== 4. Expected missed-deadline line of the team scheduler, by stage reached at 21:00 ==")
    print("  headline shaped100 offers, seed 1 (= the offer CSV), cap + 8 kWh band, restart outside execution, no pin")
    labels, specs = stage_specs()
    mspecs = all_months_outage_specs()
    if procs == 1:
        res = dict(_task(s) for s in specs + mspecs)
    else:
        with mp.Pool(procs) as pool:
            res = dict(pool.map(_task, specs + mspecs, chunksize=1))
    for lab in labels:
        cells = []
        for n in (6, 8):
            r = res[(lab, n)]
            cells.append(f"N={n}: {r['missed']:>3} of {r['closed']:>6,} accepted jobs missed ({r['missed']/max(1,r['closed'])*100:.3f}%), "
                         f"accepted {r['acc']*100:.1f}% of {r['offered']:,} offers, coverage {r['cov']*100:.2f}%")
        print(f"  {lab:<52} " + " | ".join(cells))
    print("\n  whole-house outage, told, seed 1, missed jobs by start month (15th, 00:00), Jan..Dec:")
    for n in (6, 8):
        for dur in (24, 72):
            row = [res[(f"M{m:02d} {dur}h", n)]["missed"] for m in range(1, 13)]
            print(f"    N={n} {dur:>2} h: {row}  max {max(row)}")

    print("\n== 4b. Seed-1 key figures (what a scheduler fed only the seed-1 offer CSV prints) vs the pitch's 3-seed means ==")
    import r5_miss_stress as S5m
    from baseline_sweep import HEAT_VALUE, PRICE
    pitch = {6: (73.67, 54.72, 28761, 0.2278), 8: (86.14, 47.98, 33626, 0.2286)}   # docs/overnight.md, r4_headline s.3
    for n in (6, 8):
        r = S5m.run(n, S5m.cfg(), 1)
        elec = r["run_h"] * PRICE
        heat = r["used"] * HEAT_VALUE
        be15 = (elec - heat) / (r["sold_h"] - r["starts"] * 0.25)
        p_ = pitch[n]
        print(f"  N={n} seed 1: coverage {r['coverage']*100:.2f}% (pitch {p_[0]:.2f}%), utilisation {r['util']*100:.2f}% "
              f"(pitch {p_[1]:.2f}%), sold {r['sold_h']:,.0f} h (pitch {p_[2]:,}), electricity {elec:,.0f} CHF, heat value "
              f"{heat:,.0f} CHF, break-even {r['breakeven']:.4f} CHF ({be15:.4f} with 15-min restart line; pitch {p_[3]:.4f}), "
              f"accepted {r['acc_jobs']*100:.1f}%, starts {r['starts']:,}, missed {r['missed_n']} of {r['closed_n']:,}")

    print("\n== 5. Offer CSV reproducibility ==")
    import r4_headline as H4m
    fd, tmp = tempfile.mkstemp(prefix="r6_buildscope_offers_", suffix=".csv")
    os.close(fd)
    try:
        H4m.write_offers(tmp, seed=1)
        same = Path(tmp).read_bytes() == (HERE / "r4_offers_shaped100_seed1.csv").read_bytes()
    finally:
        os.remove(tmp)
    print(f"  r4_headline.write_offers(seed=1) byte-identical to analysis/r4_offers_shaped100_seed1.csv: {same}")
    print(f"\n(done in {time.time()-t0:.1f} s)")


if __name__ == "__main__":
    main()
