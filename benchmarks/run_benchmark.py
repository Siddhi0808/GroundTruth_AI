"""Reproducible benchmark runner. Records the full configuration next to the metrics.

Examples:
    python -m benchmarks.run_benchmark --dataset benchmarks/datasets/heldout_v1.json --engine heuristic
    python -m benchmarks.run_benchmark --dataset benchmarks/datasets/dev_v1_1000.json --engine heuristic --dedupe
    python -m benchmarks.run_benchmark --dataset benchmarks/datasets/dev_v1_1000.json --engine llm --sample 200 --seed 7

--engine llm requires Ollama; cases where the LLM was unavailable/invalid fall back to the rules and are COUNTED
in metadata (`llm_fallbacks`) so a "LLM" run can never silently become a rules run.
"""
import argparse
import hashlib
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import config, database  # noqa: E402
from backend.llm.judge import INSUFFICIENT, SUPPORTED, evaluate_hallucination  # noqa: E402
from backend.rag.retriever import retrieve_context  # noqa: E402
from benchmarks.metrics import score  # noqa: E402

DEV_3WAY = {"Supported": SUPPORTED, "ZeroEvidence": INSUFFICIENT}


def load_cases(path: Path):
    """Load a dataset (list or {"cases": [...]}) and fill in the 3-way expected label."""
    raw = json.loads(path.read_text())
    cases = raw["cases"] if isinstance(raw, dict) else raw
    for c in cases:  # dev_v1 predates the 3-way label; derive it from the category
        c.setdefault("expected_3way", DEV_3WAY.get(c["category"], "Hallucinated"))
    return cases


def stratified_sample(cases, n, seed):
    """Sample about `n` cases, keeping each category's share of the dataset."""
    rng = random.Random(seed)
    by_cat = {}
    for c in cases:
        by_cat.setdefault(c["category"], []).append(c)
    out = []
    for cat, items in sorted(by_cat.items()):
        k = round(n * len(items) / len(cases))
        out.extend(rng.sample(items, min(k, len(items))))
    return out


def git_state():
    """(short commit, dirty?) of the working tree, or (None, None) outside git."""
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        return commit, dirty
    except Exception:
        return None, None


def main():
    """Run retrieval + judge over every case and write metrics with the full run configuration."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--engine", choices=["heuristic", "llm"], required=True)
    ap.add_argument("--top-k", type=int, default=3, help="default matches the API default")
    ap.add_argument("--dedupe", action="store_true", help="keep only the first of identical (query, response) pairs")
    ap.add_argument("--sample", type=int, default=0, help="stratified sample size (0 = all)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    dataset = Path(args.dataset)
    cases = load_cases(dataset)
    n_total = len(cases)
    unique = {(c["query"], c["response"]) for c in cases}
    if args.dedupe:
        seen, deduped = set(), []
        for c in cases:
            if (c["query"], c["response"]) not in seen:
                seen.add((c["query"], c["response"]))
                deduped.append(c)
        cases = deduped
    if args.sample:
        cases = stratified_sample(cases, args.sample, args.seed)

    database.init_db()
    with database.db_connection() as conn:
        n_chunks, n_docs = database.count_chunks(conn)

    use_llm = args.engine == "llm"
    records, latencies, fallbacks = [], [], Counter()
    for i, c in enumerate(cases, 1):
        t0 = time.perf_counter()
        docs = retrieve_context(c["query"], top_k=args.top_k)
        if not docs:
            out = {"verdict": INSUFFICIENT, "confidence": 0.0, "reason": "no evidence retrieved",
                   "engine": "none", "model": None, "fallback_reason": None}
        else:
            ctx = "\n\n".join(f"[{d['source']}]: {d['content']}" for d in docs)
            out = evaluate_hallucination(c["query"], c["response"], ctx, use_llm=use_llm)
        dt = time.perf_counter() - t0
        latencies.append(dt)
        if use_llm and out["engine"] != "llm":
            fallbacks[out["fallback_reason"] or out["engine"]] += 1
        records.append({**{k: c[k] for k in ("id", "category", "query", "response", "expected_verdict", "expected_3way")},
                        "predicted_verdict": out["verdict"], "confidence": out["confidence"], "reason": out["reason"],
                        "engine": out["engine"], "fallback_reason": out["fallback_reason"],
                        "top_sources": [d["source"] for d in docs], "latency_seconds": round(dt, 4)})
        if i % 25 == 0 or i == len(cases):
            print(f"  {i}/{len(cases)}", flush=True)

    commit, dirty = git_state()
    status = database.database_status()
    metadata = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "git_commit": commit, "git_dirty": dirty,
        "dataset": dataset.name, "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "cases_in_dataset": n_total, "unique_pairs_in_dataset": len(unique),
        "cases_evaluated": len(cases), "dedupe": args.dedupe, "sample": args.sample or None,
        "sample_seed": args.seed if args.sample else None,
        "category_distribution": dict(Counter(c["category"] for c in cases)),
        "engine": args.engine,
        "judge_model": f"ollama:{config.OLLAMA_MODEL}" if use_llm else config.HEURISTIC_ENGINE_NAME,
        "llm_options": {"temperature": config.LLM_TEMPERATURE, "seed": config.LLM_SEED, "num_ctx": config.LLM_NUM_CTX}
        if use_llm else None,
        "llm_fallbacks": dict(fallbacks) if use_llm else None,
        "database_backend": status["backend"], "retrieval_mode": status["retrieval_mode"],
        "corpus_chunks": n_chunks, "corpus_documents": n_docs,
        "embedding_model": config.EMBEDDING_MODEL,
        "chunking": {"size_tokens": config.CHUNK_SIZE_TOKENS, "overlap_tokens": config.CHUNK_OVERLAP_TOKENS},
        "top_k": args.top_k,
        "latency_seconds": {"mean": round(statistics.mean(latencies), 4),
                            "p50": round(statistics.median(latencies), 4),
                            "p95": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 4)},
        "python": platform.python_version(), "machine": platform.machine(),
    }
    result = {"metadata": metadata, "metrics": score(records), "records": records}
    out = Path(args.out) if args.out else ROOT / "benchmarks" / "results" / (
        f"{dataset.stem}_{args.engine}{'_dedup' if args.dedupe else ''}{f'_s{args.sample}' if args.sample else ''}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    m = result["metrics"]["binary"]
    print(json.dumps({"out": str(out), "n": len(cases), "accuracy": m["accuracy"], "macro_f1": m["macro_f1"],
                      "not_supported": m["not_supported"], "supported": m["supported"],
                      "three_way_accuracy": result["metrics"]["three_way_accuracy"],
                      "llm_fallbacks": metadata["llm_fallbacks"]}, indent=1))


if __name__ == "__main__":
    main()
