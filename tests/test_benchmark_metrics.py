"""The benchmark scorer must compute the confusion matrix and P/R/F1 correctly (checked by hand)."""
from benchmarks.metrics import score


def rec(cat, expected, predicted, three=None):
    return {"category": cat, "expected_verdict": expected, "predicted_verdict": predicted, "expected_3way": three}


def test_hand_computed_example():
    records = (
        [rec("S", "Supported", "Supported")] * 3
        + [rec("S", "Supported", "Hallucinated")] * 1
        + [rec("H", "Hallucinated", "Hallucinated")] * 4
        + [rec("H", "Hallucinated", "Insufficient Evidence")] * 1   # counts as "not supported" (correct in binary)
        + [rec("H", "Hallucinated", "Supported")] * 1
    )
    m = score(records)["binary"]
    assert m["confusion_matrix"] == {"actual_supported": {"pred_supported": 3, "pred_not_supported": 1},
                                     "actual_not_supported": {"pred_supported": 1, "pred_not_supported": 5}}
    assert m["accuracy"] == 80.0
    # Not supported: P = 5/6, R = 5/6
    assert m["not_supported"]["precision"] == 83.33 and m["not_supported"]["recall"] == 83.33
    # Supported: P = 3/4, R = 3/4
    assert m["supported"]["f1"] == 75.0
    assert m["majority_baseline_accuracy"] == 60.0


def test_three_way_accuracy_and_distribution():
    records = [rec("Z", "Hallucinated", "Insufficient Evidence", "Insufficient Evidence"),
               rec("Z", "Hallucinated", "Hallucinated", "Insufficient Evidence")]
    s = score(records)
    assert s["three_way_accuracy"] == 50.0
    assert s["prediction_distribution"] == {"Insufficient Evidence": 1, "Hallucinated": 1}
    assert s["binary"]["accuracy"] == 100.0
