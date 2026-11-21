"""The two real job types and an interruptible, checkpointing runner.

Both jobs work on BEIR SciFact (5,183 scientific abstracts, 1,109 queries; see
data/README.md). A job is "process items 0..total_items-1"; item i maps onto
the corpus deterministically, cycling when a job is bigger than the corpus, so
any job size can be run and repeated.

    embed   item i = abstract (i mod 5183) -> 384-dim embedding
            model sentence-transformers/all-MiniLM-L6-v2, max 256 tokens
    rerank  item i = (query, abstract) pair -> relevance score
            query (i // 20) mod 1109, abstract (7919*i + 13) mod 5183
            model cross-encoder/ms-marco-MiniLM-L6-v2, max 512 tokens

Interruption contract (what the scheduler can rely on):

    SIGSTOP / SIGCONT   freeze / unfreeze instantly. Nothing is lost; the process
                        keeps its memory (and, on a real server, keeps drawing idle power).
    SIGTERM / SIGINT    finish the current batch, write a checkpoint, exit with
                        code 75 (EXIT_STOPPED). Run again with the same --job-dir to
                        resume from the checkpoint, on this or any other machine that
                        has the job dir.
    hard kill           at most `checkpoint_every_s` seconds of work are lost.
    exit code 0         job complete.

Files in the job dir:
    state.json   durable checkpoint: next_item, job_type, total_items, model revision
    status.json  rewritten after every batch: running/stopped/done, items_done, rate
    out/         one .npy shard per checkpoint (embeddings or scores), named by first item
"""

import json
import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCIFACT = ROOT / "data" / "raw" / "scifact"
EXIT_STOPPED = 75  # EX_TEMPFAIL: stopped at a checkpoint, resumable


@dataclass(frozen=True)
class JobType:
    name: str
    model: str
    revision: str
    batch_size: int
    max_tokens: int
    item: str  # what one item is, for humans


JOB_TYPES = {
    "embed": JobType(
        name="embed",
        model="sentence-transformers/all-MiniLM-L6-v2",
        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        batch_size=32,
        max_tokens=256,
        item="one abstract embedded (title + text, ~215 words, truncated at 256 tokens)",
    ),
    "rerank": JobType(
        name="rerank",
        model="cross-encoder/ms-marco-MiniLM-L6-v2",
        revision="233902d25c440f23af6f7d6e94d2946bac0bee0a",
        batch_size=32,
        max_tokens=512,
        item="one (query, abstract) pair scored",
    ),
}


def load_corpus():
    import pyarrow.parquet as pq

    docs = pq.read_table(SCIFACT / "corpus-00000-of-00001.parquet").to_pylist()
    queries = pq.read_table(SCIFACT / "queries-00000-of-00001.parquet").to_pylist()
    return [f"{d['title']} {d['text']}".strip() for d in docs], [q["text"] for q in queries]


class Worker:
    """Loads one model and turns item ranges into outputs."""

    def __init__(self, job_type, threads=None):
        import torch

        if threads:
            torch.set_num_threads(threads)
        self.threads = torch.get_num_threads()
        self.jt = JOB_TYPES[job_type]
        self.docs, self.queries = load_corpus()
        if job_type == "embed":
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.jt.model, revision=self.jt.revision, device="cpu")
            self.model.max_seq_length = self.jt.max_tokens
        else:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(
                self.jt.model, revision=self.jt.revision, device="cpu", max_length=self.jt.max_tokens
            )

    def inputs(self, start, stop):
        nd, nq = len(self.docs), len(self.queries)
        if self.jt.name == "embed":
            return [self.docs[i % nd] for i in range(start, stop)]
        return [(self.queries[(i // 20) % nq], self.docs[(7919 * i + 13) % nd]) for i in range(start, stop)]

    def process(self, start, stop):
        import numpy as np

        x = self.inputs(start, stop)
        if self.jt.name == "embed":
            out = self.model.encode(x, batch_size=self.jt.batch_size, convert_to_numpy=True)
        else:
            out = self.model.predict(x, batch_size=self.jt.batch_size, convert_to_numpy=True)
        return np.asarray(out, dtype=np.float32)


def _write_json(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    os.replace(tmp, path)  # atomic: a reader never sees a half-written file


def run(job_type, job_dir, total_items, threads=None, checkpoint_every_s=10.0, save_outputs=True, log=print):
    import numpy as np

    job_dir = Path(job_dir)
    (job_dir / "out").mkdir(parents=True, exist_ok=True)
    state_path, status_path = job_dir / "state.json", job_dir / "status.json"
    jt = JOB_TYPES[job_type]

    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state["job_type"] != job_type:
            raise SystemExit(f"{job_dir} holds a {state['job_type']!r} job, not {job_type!r}")
        log(f"resuming {job_type} at item {state['next_item']:,} of {state['total_items']:,}")
    else:
        state = {
            "job_type": job_type, "total_items": total_items, "next_item": 0,
            "model": jt.model, "revision": jt.revision, "created": time.time(), "checkpoints": 0,
        }
        _write_json(state_path, state)

    stop = {"requested": False}

    def request_stop(signum, _frame):
        stop["requested"] = True
        log(f"signal {signum}: stopping at the next checkpoint")

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    t_load = time.time()
    worker = Worker(job_type, threads)
    log(f"{job_type}: model loaded in {time.time() - t_load:.1f}s, {worker.threads} torch threads")

    total = state["total_items"]
    nxt = state["next_item"]
    buf, buf_start, last_ckpt = [], nxt, time.time()
    rate_t, rate_n, rate = time.time(), nxt, 0.0

    def checkpoint():
        nonlocal buf, buf_start, last_ckpt
        if buf and save_outputs:
            np.save(job_dir / "out" / f"shard_{buf_start:010d}.npy", np.concatenate(buf))
        state["next_item"] = nxt
        state["checkpoints"] += 1
        _write_json(state_path, state)
        buf, buf_start, last_ckpt = [], nxt, time.time()

    def status(s):
        _write_json(status_path, {
            "state": s, "pid": os.getpid(), "job_type": job_type, "items_done": nxt,
            "items_checkpointed": state["next_item"], "total_items": total,
            "items_per_s": round(rate, 3), "updated_at": time.time(),
        })

    status("running")
    while nxt < total and not stop["requested"]:
        end = min(nxt + jt.batch_size, total)
        buf.append(worker.process(nxt, end))
        nxt = end
        now = time.time()
        if now - rate_t >= 5:
            rate, rate_t, rate_n = (nxt - rate_n) / (now - rate_t), now, nxt
        if now - last_ckpt >= checkpoint_every_s:
            checkpoint()
        status("running")

    checkpoint()
    done = nxt >= total
    status("done" if done else "stopped")
    log(f"{job_type}: {'done' if done else 'stopped'} at item {nxt:,} of {total:,}")
    return 0 if done else EXIT_STOPPED
