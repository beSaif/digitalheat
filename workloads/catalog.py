"""Job types scaled to the 1 kW reference server, for the scheduler and the yearly balance.

Reads a measurement file from data/measurements/ (written by
scripts/measure_workloads.py) and applies the scaling rule of docs/workloads.md:

    reference server items per hour = 3,600,000 J / (J per item on our machine x efficiency_factor)

The heat a server makes does not depend on this: 1 kW in, 0.8 kW recoverable,
whatever it computes. The rule only sets how much useful work one server-hour
delivers, so it drives job runtimes and computing income, not heat.

    .venv/bin/python -m workloads.catalog            # print the table
    from workloads.catalog import reference_job_types
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEASUREMENTS = ROOT / "data" / "measurements"
SERVER_W = 1000.0

# Our assumptions, not measured or sourced. Kept here, in one place, so they show.
JOB_DEFAULTS = {
    "embed": {
        "items_per_job": 10_000_000,  # re-indexing a large document archive; ~0.9 server-hours
        "deadline_h": 48.0,           # batch indexing: results wanted within two days
    },
    "rerank": {
        "items_per_job": 5_000_000,   # offline re-scoring run, e.g. 50k queries x 100 candidates
        "deadline_h": 4.0,            # evaluation run: results wanted the same working day
    },
}


@dataclass(frozen=True)
class ReferenceJobType:
    name: str
    item: str
    j_per_item_measured: float     # on our machine, chosen basis
    items_per_server_hour: float   # on the 1 kW reference server
    items_per_job: int
    server_hours_per_job: float    # runtime of one job on one reference server
    deadline_h: float
    interruptible: bool            # pause instantly (SIGSTOP) or stop at a checkpoint (SIGTERM)
    max_loss_on_kill_s: float      # work lost on a hard kill = checkpoint interval
    movable: bool                  # a stopped job resumes on any server holding its job dir
    source: str


def latest_measurement():
    """combined.json (team average) if present, else the single measurement file."""
    combined = MEASUREMENTS / "combined.json"
    if combined.exists():
        return combined
    files = sorted(MEASUREMENTS.glob("workloads_*.json"))
    if len(files) != 1:
        raise FileNotFoundError(f"{len(files)} measurement files; run scripts/combine_measurements.py")
    return files[0]


def reference_job_types(measurement=None, basis="gross", efficiency_factor=1.0):
    """basis: 'gross' (whole machine incl. idle, default) or 'marginal' (above idle, optimistic).
    efficiency_factor: >1 if the reference server needs more energy per item than our machine."""
    path = Path(measurement or latest_measurement())
    m = json.loads(path.read_text())
    out = {}
    for name, r in m["jobs"].items():
        j = r[f"{basis}_j_per_item"]
        per_h = 3_600_000.0 / (j * efficiency_factor)
        d = JOB_DEFAULTS[name]
        out[name] = ReferenceJobType(
            name=name, item=r["item"], j_per_item_measured=j, items_per_server_hour=per_h,
            items_per_job=d["items_per_job"], server_hours_per_job=d["items_per_job"] / per_h,
            deadline_h=d["deadline_h"], interruptible=True, max_loss_on_kill_s=10.0, movable=True,
            source=f"{path.relative_to(ROOT)} ({m['machine']['cpu']}, {basis}, x{efficiency_factor})",
        )
    return out


if __name__ == "__main__":
    for basis in ("gross", "marginal"):
        print(f"basis: {basis}")
        for jt in reference_job_types(basis=basis).values():
            print(f"  {jt.name:7} {jt.j_per_item_measured:.4f} J/item  "
                  f"{jt.items_per_server_hour / 1e6:6.2f} M items/server-hour  "
                  f"job {jt.items_per_job / 1e6:g} M items = {jt.server_hours_per_job:.2f} server-h  "
                  f"deadline {jt.deadline_h:g} h")
    print(json.dumps(asdict(reference_job_types()["embed"]), indent=1))
