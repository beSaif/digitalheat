/*
 * DigitalHeat live demo: one AI part on this device, with the same models as the measured workloads
 * (workloads/jobs.py): all-MiniLM-L6-v2 embeds abstracts, ms-marco-MiniLM-L6-v2 scores (question,
 * abstract) pairs. Models and runtime are served by the operator laptop, so no internet is needed.
 *
 * in:  { task, kind: "embed", texts: string[] } | { task, kind: "rerank", query: string, texts: string[] }
 * out: { task, type: "loading" } · { task, type: "item", i, values } per item · { task, type: "done", ms, values[] }
 */
import { AutoModelForSequenceClassification, AutoTokenizer, env, pipeline } from "./transformers.min.js";

env.allowRemoteModels = false;
env.allowLocalModels = true;
env.localModelPath = "/ai/models/"; // a path, not a URL: transformers.js only checks local files by path
env.backends.onnx.wasm.wasmPaths = new URL("./", import.meta.url).href;
env.backends.onnx.wasm.numThreads = 1;

const EMBED = "Xenova/all-MiniLM-L6-v2";
const RERANK = "Xenova/ms-marco-MiniLM-L-6-v2";
let embedder = null;
let reranker = null;

async function getEmbedder(task) {
  if (!embedder) {
    postMessage({ task, type: "loading" });
    embedder = await pipeline("feature-extraction", EMBED, { dtype: "q8" });
  }
  return embedder;
}

async function getReranker(task) {
  if (!reranker) {
    postMessage({ task, type: "loading" });
    const [tokenizer, model] = await Promise.all([AutoTokenizer.from_pretrained(RERANK), AutoModelForSequenceClassification.from_pretrained(RERANK, { dtype: "q8" })]);
    reranker = { tokenizer, model };
  }
  return reranker;
}

onmessage = async (e) => {
  const msg = e.data;
  try {
    const t0 = performance.now();
    const out = [];
    if (msg.kind === "embed") {
      const f = await getEmbedder(msg.task);
      const t1 = performance.now();
      for (let i = 0; i < msg.texts.length; i++) {
        const v = await f(msg.texts[i], { pooling: "mean", normalize: true, truncation: true, max_length: 256 });
        const values = Array.from(v.data);
        out.push(values);
        postMessage({ task: msg.task, type: "item", i, values });
      }
      postMessage({ task: msg.task, type: "done", ms: performance.now() - t1, load: t1 - t0, values: out });
    } else if (msg.kind === "rerank") {
      const { tokenizer, model } = await getReranker(msg.task);
      const t1 = performance.now();
      for (let i = 0; i < msg.texts.length; i++) {
        const inputs = tokenizer(msg.query, { text_pair: msg.texts[i], truncation: true, max_length: 512 });
        const { logits } = await model(inputs);
        const score = logits.data[0];
        out.push(score);
        postMessage({ task: msg.task, type: "item", i, values: score });
      }
      postMessage({ task: msg.task, type: "done", ms: performance.now() - t1, load: t1 - t0, values: out });
    }
  } catch (err) {
    postMessage({ task: msg.task, type: "error", message: String(err && err.message ? err.message : err) });
  }
};
