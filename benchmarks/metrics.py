"""Scoring for the hallucination benchmark.

Binary view (headline metrics): positive class = "Not supported".
    expected positive  <=> expected_verdict == "Hallucinated"
    predicted positive <=> predicted verdict in {"Hallucinated", "Insufficient Evidence"}
Rationale: for a verification layer, both mean "do not trust this answer". The 3-way breakdown is reported
separately so "Insufficient Evidence" is never silently folded away.
"""
from collections import Counter, defaultdict
from typing import Dict, List

SUPPORTED = "Supported"


def _prf(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """Precision/recall/F1 (in %) for one class."""
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p * 100, 2), "recall": round(r * 100, 2), "f1": round(f * 100, 2), "support": tp + fn}


def score(records: List[Dict]) -> Dict:
    """Binary, 3-way and per-category metrics for a list of benchmark records."""
    y_true = [r["expected_verdict"] != SUPPORTED for r in records]   # True = not supported
    y_pred = [r["predicted_verdict"] != SUPPORTED for r in records]
    tp = sum(t and p for t, p in zip(y_true, y_pred))
    tn = sum((not t) and (not p) for t, p in zip(y_true, y_pred))
    fp = sum((not t) and p for t, p in zip(y_true, y_pred))
    fn = sum(t and (not p) for t, p in zip(y_true, y_pred))
    n = len(records)
    not_supported = _prf(tp, fp, fn)
    supported = _prf(tn, fn, fp)
    by_cat = defaultdict(lambda: [0, 0])
    for r, t, p in zip(records, y_true, y_pred):
        by_cat[r["category"]][0] += int(t == p)
        by_cat[r["category"]][1] += 1
    three = [r for r in records if r.get("expected_3way")]
    return {
        "n": n,
        "binary": {
            "positive_class": "Not supported (Hallucinated or Insufficient Evidence)",
            "confusion_matrix": {"actual_supported": {"pred_supported": tn, "pred_not_supported": fp},
                                 "actual_not_supported": {"pred_supported": fn, "pred_not_supported": tp}},
            "accuracy": round((tp + tn) / n * 100, 2) if n else 0.0,
            "not_supported": not_supported,
            "supported": supported,
            "macro_f1": round((not_supported["f1"] + supported["f1"]) / 2, 2),
            "majority_baseline_accuracy": round(max(sum(y_true), n - sum(y_true)) / n * 100, 2) if n else 0.0,
        },
        "three_way_accuracy": round(sum(r["predicted_verdict"] == r["expected_3way"] for r in three) / len(three) * 100, 2)
        if three else None,
        "prediction_distribution": dict(Counter(r["predicted_verdict"] for r in records)),
        "per_category_binary_accuracy": {c: {"correct": v[0], "total": v[1], "accuracy": round(v[0] / v[1] * 100, 2)}
                                         for c, v in sorted(by_cat.items())},
    }
