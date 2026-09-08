"""
GroundTruth AI - Evaluation & Benchmark Suite
Tests the end-to-end RAG retrieval + LLM Judge pipeline across a curated
benchmark dataset of supported and hallucinated facts, computing:
  - Accuracy
  - Precision, Recall, F1 Score
  - Confusion Matrix (TP, FP, TN, FN)
  - Detailed per-sample evaluation breakdown
"""

import json
import time
from typing import List, Dict, Any
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_recall_fscore_support

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.retriever import retrieve_context
from backend.llm.judge import evaluate_hallucination

# Benchmark Dataset: balanced ground-truth test cases mapped to the knowledge base
BENCHMARK_DATA: List[Dict[str, Any]] = [
    # 1. Telephone - Supported
    {
        "id": 1,
        "category": "Inventions",
        "query": "Who invented the practical telephone and when was it patented?",
        "response": "Alexander Graham Bell received a patent for the practical telephone in 1876.",
        "ground_truth": "Supported"
    },
    # 2. Telephone - Hallucinated
    {
        "id": 2,
        "category": "Inventions",
        "query": "Who invented the telephone and when?",
        "response": "Thomas Edison invented the telephone in 1879 at Menlo Park.",
        "ground_truth": "Hallucinated"
    },
    # 3. Einstein - Supported
    {
        "id": 3,
        "category": "Physics",
        "query": "What major theory did Albert Einstein develop?",
        "response": "Albert Einstein was a theoretical physicist who developed the theory of relativity.",
        "ground_truth": "Supported"
    },
    # 4. Einstein - Hallucinated
    {
        "id": 4,
        "category": "Physics",
        "query": "When was Albert Einstein born and when did he pass away?",
        "response": "Albert Einstein was born in 1920 and died in 2005.",
        "ground_truth": "Hallucinated"
    },
    # 5. Earth - Supported
    {
        "id": 5,
        "category": "Astronomy",
        "query": "How old is Earth and what is its atmosphere composed of?",
        "response": "Earth is about 4.54 billion years old and has an atmosphere mostly composed of nitrogen and oxygen.",
        "ground_truth": "Supported"
    },
    # 6. Earth - Hallucinated
    {
        "id": 6,
        "category": "Astronomy",
        "query": "What is the atmosphere of Earth composed of?",
        "response": "Earth has an atmosphere composed entirely of pure carbon dioxide and helium.",
        "ground_truth": "Hallucinated"
    },
    # 7. Taj Mahal - Supported
    {
        "id": 7,
        "category": "Architecture",
        "query": "Where is the Taj Mahal located and who built it?",
        "response": "The Taj Mahal is a white marble mausoleum in Agra, India, built by Mughal emperor Shah Jahan.",
        "ground_truth": "Supported"
    },
    # 8. Taj Mahal - Hallucinated
    {
        "id": 8,
        "category": "Architecture",
        "query": "Who built the Taj Mahal and when was construction completed?",
        "response": "The Taj Mahal was commissioned by Emperor Akbar and completed in the year 1850.",
        "ground_truth": "Hallucinated"
    },
    # 9. Isaac Newton - Supported
    {
        "id": 9,
        "category": "Physics",
        "query": "What laws is Sir Isaac Newton best known for?",
        "response": "Sir Isaac Newton is best known for formulating the laws of motion and universal gravitation.",
        "ground_truth": "Supported"
    },
    # 10. Isaac Newton - Hallucinated
    {
        "id": 10,
        "category": "Physics",
        "query": "What did Sir Isaac Newton discover?",
        "response": "Sir Isaac Newton is best known for inventing the steam engine and discovering nuclear fission.",
        "ground_truth": "Hallucinated"
    },
    # 11. Solar System - Supported
    {
        "id": 11,
        "category": "Astronomy",
        "query": "How many planets are in the Solar System?",
        "response": "The eight planets in the Solar System are Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.",
        "ground_truth": "Supported"
    },
    # 12. Solar System - Hallucinated
    {
        "id": 12,
        "category": "Astronomy",
        "query": "How many planets are in the Solar System?",
        "response": "The Solar System has twelve official major planets, including Ceres and Pluto.",
        "ground_truth": "Hallucinated"
    },
    # 13. Eiffel Tower - Supported
    {
        "id": 13,
        "category": "Architecture",
        "query": "Where is the Eiffel Tower and when was it completed?",
        "response": "The Eiffel Tower is located on the Champ de Mars in Paris and was completed in 1889.",
        "ground_truth": "Supported"
    },
    # 14. Eiffel Tower - Hallucinated
    {
        "id": 14,
        "category": "Architecture",
        "query": "Where is the Eiffel Tower and who built it?",
        "response": "The Eiffel Tower is a landmark located in Berlin, Germany, completed in 1965.",
        "ground_truth": "Hallucinated"
    }
]

def run_benchmark(save_path: str = "benchmark_results.json"):
    print("=" * 78)
    print("           🛡️  GROUNDTRUTH AI — BENCHMARK EVALUATION SUITE  🛡️")
    print("=" * 78)
    print(f"Total Test Cases : {len(BENCHMARK_DATA)}")
    print(f"Supported Cases  : {sum(1 for d in BENCHMARK_DATA if d['ground_truth'] == 'Supported')}")
    print(f"Hallucinated Cases: {sum(1 for d in BENCHMARK_DATA if d['ground_truth'] == 'Hallucinated')}")
    print("-" * 78)

    y_true = []
    y_pred = []
    results = []

    start_time = time.time()

    for idx, test_case in enumerate(BENCHMARK_DATA, start=1):
        query = test_case["query"]
        response = test_case["response"]
        expected = test_case["ground_truth"]

        print(f"\n[{idx:02d}/{len(BENCHMARK_DATA):02d}] Category: {test_case['category']}")
        print(f"      Query    : {query}")
        print(f"      Response : {response}")

        # 1. RAG Context Retrieval
        retrieved_docs = retrieve_context(query, top_k=3)
        context_snippets = [f"[{d.get('source', 'Doc')}]: {d.get('content', '')}" for d in retrieved_docs]
        full_context = "\n\n".join(context_snippets) if context_snippets else "No context found."

        # 2. Judge Evaluation
        eval_result = evaluate_hallucination(query, response, full_context)
        predicted = eval_result.get("verdict", "Hallucinated")
        confidence = eval_result.get("confidence", 0.0)
        confidence_pct = round(confidence * 100, 1) if confidence <= 1.0 else round(confidence, 1)
        reason = eval_result.get("reason", "No reason.")

        is_correct = (predicted.lower() == expected.lower())
        status_icon = "✅ PASS" if is_correct else "❌ FAIL"

        print(f"      Expected : {expected}")
        print(f"      Predicted: {predicted} ({confidence_pct}% conf) -> {status_icon}")
        print(f"      Reason   : {reason[:100]}..." if len(reason) > 100 else f"      Reason   : {reason}")

        y_true.append(expected)
        y_pred.append(predicted)

        results.append({
            "id": test_case["id"],
            "category": test_case["category"],
            "query": query,
            "response": response,
            "expected": expected,
            "predicted": predicted,
            "confidence": confidence_pct,
            "correct": is_correct,
            "reason": reason,
            "retrieved_sources": [d.get("source") for d in retrieved_docs]
        })

    elapsed = time.time() - start_time

    # Compute Metrics
    labels = ["Supported", "Hallucinated"]
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, average=None)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    print("\n" + "=" * 78)
    print("                           📊  EVALUATION METRICS")
    print("=" * 78)
    print(f"Total Evaluated        : {len(BENCHMARK_DATA)}")
    print(f"Correct Classifications: {sum(1 for r in results if r['correct'])} / {len(BENCHMARK_DATA)}")
    print(f"Overall Accuracy       : {acc * 100:.2f}%")
    print(f"Total Evaluation Time  : {elapsed:.2f}s ({elapsed / len(BENCHMARK_DATA):.2f}s/query)")
    print("-" * 78)

    print("\n                    📈  PER-CLASS BREAKDOWN")
    print(f"{'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
    print("-" * 65)
    for i, label in enumerate(labels):
        support_cnt = y_true.count(label)
        print(f"{label:<15} {prec[i]*100:>8.2f}%    {rec[i]*100:>8.2f}%    {f1[i]*100:>8.2f}%    {support_cnt:>6}")
    print("-" * 65)

    print("\n                    🔲  CONFUSION MATRIX")
    print(" " * 22 + "PREDICTED")
    print(f"{'':<20} | {'Supported':^14} | {'Hallucinated':^14} | {'Total':^8} |")
    print("-" * 66)
    print(f"ACTUAL Supported    | {cm[0][0]:^14} | {cm[0][1]:^14} | {sum(cm[0]):^8} |")
    print(f"ACTUAL Hallucinated | {cm[1][0]:^14} | {cm[1][1]:^14} | {sum(cm[1]):^8} |")
    print("-" * 66)
    print(f"{'Total':<20} | {cm[0][0]+cm[1][0]:^14} | {cm[0][1]+cm[1][1]:^14} | {len(BENCHMARK_DATA):^8} |")
    print("-" * 66)

    print("\nClassification Report (Detailed):")
    print(classification_report(y_true, y_pred, labels=labels, digits=4))

    # Save to JSON
    summary_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_samples": len(BENCHMARK_DATA),
        "overall_accuracy": round(acc * 100, 2),
        "elapsed_seconds": round(elapsed, 2),
        "confusion_matrix": {
            "labels": labels,
            "matrix": cm.tolist(),
            "actual_supported_predicted_supported": int(cm[0][0]),
            "actual_supported_predicted_hallucinated": int(cm[0][1]),
            "actual_hallucinated_predicted_supported": int(cm[1][0]),
            "actual_hallucinated_predicted_hallucinated": int(cm[1][1]),
        },
        "metrics_per_class": {
            "Supported": {
                "precision": round(prec[0] * 100, 2),
                "recall": round(rec[0] * 100, 2),
                "f1_score": round(f1[0] * 100, 2)
            },
            "Hallucinated": {
                "precision": round(prec[1] * 100, 2),
                "recall": round(rec[1] * 100, 2),
                "f1_score": round(f1[1] * 100, 2)
            }
        },
        "sample_results": results
    }

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print(f"✅ Full benchmark results successfully saved to: {save_path}\n")
    return summary_data

if __name__ == "__main__":
    run_benchmark()
