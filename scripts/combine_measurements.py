"""Average the workload measurements from all team machines.

Reads every data/measurements/workloads_*.json and writes
data/measurements/combined.json, which workloads/catalog.py uses by default.

- Throughput (items/s) is averaged over all machines. It is shown for
  comparison only: the reference server's throughput comes from energy per item.
- Energy per item (gross, marginal) is averaged over machines that had a power
  meter (--no-meter runs have none).

    python3 scripts/combine_measurements.py
"""

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEAS = ROOT / "data" / "measurements"
FIELDS = ["items_per_s", "gross_j_per_item", "marginal_j_per_item"]


def stats(values):
    if not values:
        return None
    return {"n": len(values), "mean": statistics.mean(values), "min": min(values), "max": max(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0}


def main():
    files = sorted(MEAS.glob("workloads_*.json"))
    if not files:
        raise SystemExit("no measurement files in data/measurements/")
    runs = [(f, json.loads(f.read_text())) for f in files]

    print(f"{'file':52} {'job':7} {'items/s':>8} {'J/item gross':>13} {'J/item marg.':>13}")
    combined = {}
    for f, m in runs:
        for jt, r in m["jobs"].items():
            fmt = lambda v: "-" if v is None else f"{v:.4f}"  # noqa: E731
            print(f"{f.name:52} {jt:7} {r['items_per_s']:8.2f} {fmt(r['gross_j_per_item']):>13} "
                  f"{fmt(r['marginal_j_per_item']):>13}")
            c = combined.setdefault(jt, {"item": r["item"], "model": r["model"], "revision": r["revision"],
                                         "machines": [], **{k: [] for k in FIELDS}})
            c["machines"].append(f"{m.get('label', '?')}: {m['machine']['cpu']}")
            for k in FIELDS:
                if r.get(k) is not None:
                    c[k].append(r[k])

    jobs = {}
    print("\naverage")
    for jt, c in combined.items():
        s = {k: stats(c[k]) for k in FIELDS}
        if not s["gross_j_per_item"]:
            raise SystemExit(f"{jt}: no machine with a power meter; energy per item is unknown")
        jobs[jt] = {"item": c["item"], "model": c["model"], "revision": c["revision"],
                    "machines": c["machines"], "stats": s,
                    **{k: s[k]["mean"] for k in FIELDS}}
        g = s["gross_j_per_item"]
        print(f"  {jt:7} {s['items_per_s']['mean']:8.2f} items/s (n={s['items_per_s']['n']})   "
              f"gross {g['mean']:.4f} J/item (n={g['n']}, {g['min']:.4f}-{g['max']:.4f})   "
              f"marginal {s['marginal_j_per_item']['mean']:.4f}")

    out = MEAS / "combined.json"
    out.write_text(json.dumps({
        "what": "mean over team machines, written by scripts/combine_measurements.py",
        "files": [f.name for f, _ in runs],
        "machine": {"cpu": f"mean of {len(runs)} machine(s)"},
        "jobs": jobs,
    }, indent=1))
    print(f"\nwritten {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
