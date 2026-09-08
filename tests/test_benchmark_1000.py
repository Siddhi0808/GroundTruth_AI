"""
GroundTruth AI - 1,000-Query High-Difficulty Evaluation Benchmark Suite
Evaluates 1,000 complex queries spanning 5 distinct test classes:
  1. Paraphrased & Synthesized Supported Facts (300 queries)
  2. Adversarial Logical & Causal Inversions / Negations (200 queries)
  3. High-Overlap Cross-Entity & Role Swaps (200 queries)
  4. Fine-Grained Boundary & Numerical Perturbations (150 queries)
  5. Plausible Adversarial Zero-Evidence Out-of-Corpus (150 queries)
"""

import json
import time
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_recall_fscore_support

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.retriever import retrieve_context
from backend.llm.judge import evaluate_hallucination

def run_1000_benchmark():
    print("=" * 80)
    print("🚀  STARTING GROUNDTRUTH AI 1,000-QUERY HIGH-DIFFICULTY BENCHMARK")
    print("=" * 80)

    # 1. Load test cases (check tests/ and root)
    test_case_paths = [
        Path(__file__).parent / "test_cases_1000.json",
        PROJECT_ROOT / "test_cases_1000.json"
    ]
    benchmark_file = next((p for p in test_case_paths if p.exists()), None)
    if not benchmark_file:
        raise FileNotFoundError("Could not locate test_cases_1000.json in tests/ or root.")

    with open(benchmark_file, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    total_samples = len(benchmark)
    print(f"Loaded {total_samples} test samples from {benchmark_file.name} across 5 categories.")

    actuals = []
    predictions = []
    confidences = []
    latencies = []
    category_results = {}
    detailed_records = []

    start_total_time = time.time()
    batch_start = time.time()

    for idx, item in enumerate(benchmark, 1):
        q_start = time.time()
        query = item["query"]
        response = item["response"]
        expected = item["expected_verdict"]
        cat = item["category"]

        # Retrieve context
        try:
            chunks = retrieve_context(query, top_k=5)
            context_str = "\n\n".join(f"[{c.get('source', '')}] {c.get('content', '')}" for c in chunks)
        except Exception as e:
            chunks = []
            context_str = ""

        # Evaluate through Judge
        try:
            judge_out = evaluate_hallucination(query, response, context_str)
            predicted = judge_out.get("verdict", "Hallucinated")
            confidence = judge_out.get("confidence", 0.0)
            reason = judge_out.get("reason", "")
        except Exception as e:
            predicted = "Hallucinated"
            confidence = 0.5
            reason = f"Evaluation error: {e}"

        q_time = time.time() - q_start
        latencies.append(q_time)
        actuals.append(expected)
        predictions.append(predicted)
        confidences.append(confidence)

        is_correct = (predicted == expected)

        # Track per-category
        if cat not in category_results:
            category_results[cat] = {"correct": 0, "total": 0, "latencies": []}
        category_results[cat]["total"] += 1
        if is_correct:
            category_results[cat]["correct"] += 1
        category_results[cat]["latencies"].append(q_time)

        detailed_records.append({
            "id": item["id"],
            "category": cat,
            "difficulty": item.get("difficulty", "Standard"),
            "query": query,
            "response": response,
            "expected_verdict": expected,
            "predicted_verdict": predicted,
            "is_correct": is_correct,
            "confidence": confidence,
            "reason": reason,
            "retrieved_chunk_count": len(chunks),
            "latency_seconds": round(q_time, 4)
        })

        if idx % 100 == 0 or idx == total_samples:
            batch_dur = time.time() - batch_start
            running_acc = (sum(1 for a, p in zip(actuals, predictions) if a == p) / len(actuals)) * 100
            print(f"  [Progress] Evaluated {idx:04d}/{total_samples} queries | Batch Time: {batch_dur:5.2f}s | Current Acc: {running_acc:5.2f}%")
            batch_start = time.time()

    total_duration = time.time() - start_total_time
    overall_accuracy = accuracy_score(actuals, predictions)

    labels = ["Supported", "Hallucinated"]
    cm = confusion_matrix(actuals, predictions, labels=labels)
    tp, fn, fp, tn = cm[0][0], cm[0][1], cm[1][0], cm[1][1]

    precision_supp, recall_supp, f1_supp, _ = precision_recall_fscore_support(actuals, predictions, labels=["Supported"], average=None)
    precision_hall, recall_hall, f1_hall, _ = precision_recall_fscore_support(actuals, predictions, labels=["Hallucinated"], average=None)

    print("\n" + "=" * 82)
    print("                      📊  OVERALL EVALUATION RESULTS (N=1000)")
    print("=" * 82)
    print(f"Total Evaluations Completed : {total_samples}")
    print(f"Correct Predictions         : {sum(1 for a, p in zip(actuals, predictions) if a == p)} / {total_samples}")
    print(f"Overall Benchmark Accuracy  : {overall_accuracy * 100:.2f}%")
    print(f"Total Execution Time        : {total_duration:.2f} seconds ({total_duration/total_samples:.4f}s per query)")
    print("-" * 82)

    print("\n                         📈  PER-CLASS METRICS")
    print(f"{'Class':<18} {'Precision':<14} {'Recall':<14} {'F1-Score':<14} {'Support':<10}")
    print("-" * 72)
    print(f"{'Supported':<18} {precision_supp[0]*100:6.2f}%{'':<7} {recall_supp[0]*100:6.2f}%{'':<7} {f1_supp[0]*100:6.2f}%{'':<7} {actuals.count('Supported'):<10}")
    print(f"{'Hallucinated':<18} {precision_hall[0]*100:6.2f}%{'':<7} {recall_hall[0]*100:6.2f}%{'':<7} {f1_hall[0]*100:6.2f}%{'':<7} {actuals.count('Hallucinated'):<10}")
    print("-" * 72)

    print("\n                         🔲  2x2 CONFUSION MATRIX")
    print("                            PREDICTED")
    print("                         |    Supported     |   Hallucinated   |   Total    |")
    print("-" * 76)
    print(f"ACTUAL Supported        |      {tp:<11} |      {fn:<11} |    {tp+fn:<7} |")
    print(f"ACTUAL Hallucinated/OOC |      {fp:<11} |      {tn:<11} |    {fp+tn:<7} |")
    print("-" * 76)
    print(f"Total                    |      {tp+fp:<11} |      {fn+tn:<11} |    {total_samples:<7} |")
    print("-" * 76)

    print("\n                    🔍  PER-CATEGORY ACCURACY BREAKDOWN")
    print(f"{'Category Group':<32} {'Correct':<12} {'Total':<10} {'Accuracy':<12}")
    print("-" * 68)
    for cat_name in sorted(category_results.keys()):
        stats = category_results[cat_name]
        c = stats["correct"]
        t = stats["total"]
        acc = (c / t) * 100 if t > 0 else 0.0
        print(f"{cat_name:<32} {c:>4} / {t:<5}   {t:<10} {acc:6.2f}%")
    print("-" * 68)

    print("\nDetailed Scikit-Learn Classification Report:")
    print(classification_report(actuals, predictions, labels=labels, digits=4))

    # Save report
    report = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_samples": total_samples,
            "total_duration_seconds": round(total_duration, 2),
            "avg_latency_seconds": round(total_duration / total_samples, 4),
            "overall_accuracy": round(overall_accuracy * 100, 2)
        },
        "confusion_matrix": {
            "true_supported_predicted_supported": int(tp),
            "true_supported_predicted_hallucinated": int(fn),
            "true_hallucinated_predicted_supported": int(fp),
            "true_hallucinated_predicted_hallucinated": int(tn)
        },
        "per_class_metrics": {
            "supported": {
                "precision": round(float(precision_supp[0]), 4),
                "recall": round(float(recall_supp[0]), 4),
                "f1_score": round(float(f1_supp[0]), 4),
                "support": actuals.count("Supported")
            },
            "hallucinated": {
                "precision": round(float(precision_hall[0]), 4),
                "recall": round(float(recall_hall[0]), 4),
                "f1_score": round(float(f1_hall[0]), 4),
                "support": actuals.count("Hallucinated")
            }
        },
        "per_category_breakdown": {
            cat_name: {
                "correct": category_results[cat_name]["correct"],
                "total": category_results[cat_name]["total"],
                "accuracy": round((category_results[cat_name]["correct"] / category_results[cat_name]["total"]) * 100, 2),
                "avg_latency_seconds": round(sum(category_results[cat_name]["latencies"]) / len(category_results[cat_name]["latencies"]), 4)
            }
            for cat_name in category_results
        },
        "records": detailed_records
    }

    # Save to both tests/ and project root
    for out_dir in [Path(__file__).parent, PROJECT_ROOT]:
        out_file = out_dir / "benchmark_results_1000.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Saved results to: {out_file}")

if __name__ == "__main__":
    run_1000_benchmark()
