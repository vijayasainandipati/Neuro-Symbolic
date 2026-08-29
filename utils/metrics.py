"""
Performance and evaluation metrics for NeuroSym Crisis.
Evaluates clustering accuracy, rumor filtering precision/recall/F1, and noise reduction ratio.
"""

from typing import List, Dict, Any, Tuple
import math
from utils.schemas import VerificationStatus


def calculate_noise_reduction(raw_count: int, cluster_count: int) -> float:
    """Calculates percentage noise reduction from raw alerts to event clusters."""
    if raw_count <= 0:
        return 0.0
    reduction = max(0.0, ((raw_count - cluster_count) / raw_count) * 100.0)
    return round(reduction, 2)


def calculate_classification_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
    """
    Computes overall Accuracy, Macro-F1, and per-class Precision, Recall, F1.
    """
    classes = sorted(list(set(y_true + y_pred)))
    if not classes:
        return {"accuracy": 0.0, "macro_f1": 0.0, "per_class": {}}

    total = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = (correct / total) if total > 0 else 0.0

    per_class = {}
    f1_list = []

    for cls in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[cls] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "support": sum(1 for yt in y_true if yt == cls)
        }
        f1_list.append(f1)

    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "total_samples": total
    }


def calculate_rumor_filter_metrics(
    verified_results: List[Any],
    ground_truth_rumors: Dict[str, bool]
) -> Dict[str, float]:
    """
    Specifically evaluates the Rumor & Conflict Detection capability.
    Positive class = Rumor / Conflict / Unsupported claim.
    """
    tp, fp, tn, fn = 0, 0, 0, 0

    for res in verified_results:
        claim_id = getattr(res, "claim_id", "")
        status = getattr(res, "status", "")
        if isinstance(status, VerificationStatus):
            status_str = status.value
        else:
            status_str = str(status)

        # Flagged as rumor/conflict if CONFLICTING or UNSUPPORTED
        pred_is_rumor = status_str in ["CONFLICTING", "UNSUPPORTED"]
        true_is_rumor = ground_truth_rumors.get(claim_id, False)

        if pred_is_rumor and true_is_rumor:
            tp += 1
        elif pred_is_rumor and not true_is_rumor:
            fp += 1
        elif not pred_is_rumor and not true_is_rumor:
            tn += 1
        else:
            fn += 1

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "rumor_accuracy": round(accuracy * 100, 2),
        "rumor_precision": round(precision * 100, 2),
        "rumor_recall": round(recall * 100, 2),
        "rumor_f1": round(f1 * 100, 2),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn
    }
