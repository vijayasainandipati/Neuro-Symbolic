"""
Performance metrics for evaluating flood detection models.

Includes:
  - Pixel-wise accuracy
  - Precision, Recall, F1 Score
  - Intersection over Union (IoU / Jaccard Index)
  - Dice Coefficient
  - Confusion matrix

All metrics work on both tensors and numpy arrays.
"""

import numpy as np
import torch


def _to_numpy(x):
    """Convert tensor or array to numpy."""
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().numpy()
    return np.asarray(x)


def _binarize(pred, threshold=0.5):
    """Binarize predictions at the given threshold."""
    return (pred > threshold).astype(np.float32)


def pixel_accuracy(pred, target, threshold=0.5):
    """
    Pixel-wise accuracy.

    Parameters
    ----------
    pred : array-like
        Predicted flood probabilities (0-1).
    target : array-like
        Ground truth binary mask.
    threshold : float
        Binarization threshold.

    Returns
    -------
    float
        Accuracy in [0, 1].
    """
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)
    return float((pred == target).mean())


def precision_score(pred, target, threshold=0.5, eps=1e-7):
    """
    Precision = TP / (TP + FP)

    How many predicted flood pixels are actually flooded.
    """
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)

    tp = (pred * target).sum()
    fp = (pred * (1 - target)).sum()

    return float(tp / (tp + fp + eps))


def recall_score(pred, target, threshold=0.5, eps=1e-7):
    """
    Recall = TP / (TP + FN)

    How many actual flood pixels were correctly detected.
    """
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)

    tp = (pred * target).sum()
    fn = ((1 - pred) * target).sum()

    return float(tp / (tp + fn + eps))


def f1_score(pred, target, threshold=0.5, eps=1e-7):
    """
    F1 Score = 2 * (Precision * Recall) / (Precision + Recall)

    Harmonic mean of precision and recall.
    """
    p = precision_score(pred, target, threshold, eps)
    r = recall_score(pred, target, threshold, eps)
    return float(2 * p * r / (p + r + eps))


def iou_score(pred, target, threshold=0.5, eps=1e-7):
    """
    Intersection over Union (IoU / Jaccard Index).

    IoU = TP / (TP + FP + FN)

    The most important metric for segmentation tasks.
    """
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)

    intersection = (pred * target).sum()
    union = pred.sum() + target.sum() - intersection

    return float(intersection / (union + eps))


def dice_coefficient(pred, target, threshold=0.5, eps=1e-7):
    """
    Dice Coefficient = 2 * |A ∩ B| / (|A| + |B|)

    Equivalent to F1 for binary segmentation.
    """
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)

    intersection = (pred * target).sum()
    return float(2 * intersection / (pred.sum() + target.sum() + eps))


def confusion_matrix(pred, target, threshold=0.5):
    """
    Compute confusion matrix values.

    Returns
    -------
    dict with 'TP', 'FP', 'TN', 'FN' pixel counts.
    """
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)

    tp = float((pred * target).sum())
    fp = float((pred * (1 - target)).sum())
    fn = float(((1 - pred) * target).sum())
    tn = float(((1 - pred) * (1 - target)).sum())

    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn}


def compute_all_metrics(pred, target, threshold=0.5):
    """
    Compute all metrics at once.

    Returns
    -------
    dict with all metric values.
    """
    return {
        "pixel_accuracy": pixel_accuracy(pred, target, threshold),
        "precision": precision_score(pred, target, threshold),
        "recall": recall_score(pred, target, threshold),
        "f1_score": f1_score(pred, target, threshold),
        "iou": iou_score(pred, target, threshold),
        "dice": dice_coefficient(pred, target, threshold),
        "confusion_matrix": confusion_matrix(pred, target, threshold),
    }


def print_metrics(metrics):
    """Pretty-print a metrics dictionary."""
    print("┌─────────────────────────────────────┐")
    print("│     Flood Detection Metrics         │")
    print("├─────────────────────────────────────┤")
    print(f"│  Pixel Accuracy : {metrics['pixel_accuracy']:.4f}            │")
    print(f"│  Precision      : {metrics['precision']:.4f}            │")
    print(f"│  Recall         : {metrics['recall']:.4f}            │")
    print(f"│  F1 Score       : {metrics['f1_score']:.4f}            │")
    print(f"│  IoU (Jaccard)  : {metrics['iou']:.4f}            │")
    print(f"│  Dice Coeff     : {metrics['dice']:.4f}            │")
    print("├─────────────────────────────────────┤")
    cm = metrics['confusion_matrix']
    print(f"│  TP: {cm['TP']:>8.0f}  FP: {cm['FP']:>8.0f}      │")
    print(f"│  FN: {cm['FN']:>8.0f}  TN: {cm['TN']:>8.0f}      │")
    print("└─────────────────────────────────────┘")
