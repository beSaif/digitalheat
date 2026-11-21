"""Run (or resume) one real job. The scheduler starts this as a subprocess.

    .venv/bin/python -m workloads.run embed  --job-dir runs/embed-001 --items 20000
    .venv/bin/python -m workloads.run rerank --job-dir runs/rerank-001 --items 20000

Same command with the same --job-dir resumes from the last checkpoint.
See workloads/jobs.py for the pause/stop contract.
"""

import argparse
import sys

from workloads.jobs import JOB_TYPES, run


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job_type", choices=sorted(JOB_TYPES))
    ap.add_argument("--job-dir", required=True)
    ap.add_argument("--items", type=int, default=10_000, help="job size for a new job (ignored on resume)")
    ap.add_argument("--threads", type=int, help="torch CPU threads (default: torch's choice)")
    ap.add_argument("--checkpoint-every", type=float, default=10.0, help="seconds between checkpoints")
    ap.add_argument("--no-outputs", action="store_true", help="don't write result shards (measurement only)")
    a = ap.parse_args()
    sys.exit(run(a.job_type, a.job_dir, a.items, a.threads, a.checkpoint_every, not a.no_outputs,
                 log=lambda m: print(m, flush=True)))


if __name__ == "__main__":
    main()
