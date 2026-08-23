"""
Model Evaluation Module.

Comprehensive evaluation metrics for all multi-hazard detection models:
  - Segmentation metrics (IoU, Dice, pixel accuracy)
  - Classification metrics (accuracy, precision, recall, F1)
  - Detection metrics (mAP, confidence analysis)
  - Confusion matrices
  - Per-hazard performance reports
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


# ═══════════════════════════════════════════════════════════════════════════
# Segmentation Metrics (Flood model)
# ═══════════════════════════════════════════════════════════════════════════

def pixel_accuracy(pred, target, threshold=0.5):
    """Pixel-wise accuracy."""
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)
    return float((pred == target).mean())


def iou_score(pred, target, threshold=0.5, eps=1e-7):
    """Intersection over Union (IoU / Jaccard Index)."""
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)

    intersection = (pred * target).sum()
    union = pred.sum() + target.sum() - intersection
    return float((intersection + eps) / (union + eps))


def dice_score(pred, target, threshold=0.5, eps=1e-7):
    """Dice Coefficient (F1 for segmentation)."""
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)

    intersection = (pred * target).sum()
    return float((2 * intersection + eps) / (pred.sum() + target.sum() + eps))


# ═══════════════════════════════════════════════════════════════════════════
# Classification Metrics (Landslide, Cyclone, Fire, Defense)
# ═══════════════════════════════════════════════════════════════════════════

def precision_score(pred, target, threshold=0.5, eps=1e-7):
    """Precision = TP / (TP + FP)."""
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)
    tp = (pred * target).sum()
    fp = (pred * (1 - target)).sum()
    return float(tp / (tp + fp + eps))


def recall_score(pred, target, threshold=0.5, eps=1e-7):
    """Recall = TP / (TP + FN)."""
    pred = _binarize(_to_numpy(pred), threshold)
    target = _to_numpy(target)
    tp = (pred * target).sum()
    fn = ((1 - pred) * target).sum()
    return float(tp / (tp + fn + eps))


def f1_score(pred, target, threshold=0.5, eps=1e-7):
    """F1 Score = 2 * (Precision * Recall) / (Precision + Recall)."""
    p = precision_score(pred, target, threshold, eps)
    r = recall_score(pred, target, threshold, eps)
    return float(2 * p * r / (p + r + eps))


def confusion_matrix(pred, target, num_classes=2, threshold=0.5):
    """
    Compute confusion matrix.

    Returns
    -------
    np.ndarray
        Shape (num_classes, num_classes) confusion matrix.
    """
    pred = _to_numpy(pred)
    target = _to_numpy(target)

    if num_classes == 2:
        pred = _binarize(pred, threshold).astype(int)
    else:
        pred = pred.argmax(axis=-1) if pred.ndim > 1 else pred.astype(int)

    target = target.astype(int)
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)

    for t, p in zip(target.ravel(), pred.ravel()):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            cm[t, p] += 1

    return cm


# ═══════════════════════════════════════════════════════════════════════════
# Model Evaluator Class
# ═══════════════════════════════════════════════════════════════════════════

class ModelEvaluator:
    """
    Comprehensive model evaluation for all hazard detection models.

    Generates performance reports with all relevant metrics
    for each model type.
    """

    def evaluate_segmentation(self, model, dataloader, device=None):
        """
        Evaluate a segmentation model (e.g., flood U-Net).

        Returns metrics: pixel accuracy, IoU, Dice coefficient.
        """
        device = device or torch.device("cpu")
        model.eval()

        all_acc, all_iou, all_dice = [], [], []

        with torch.no_grad():
            for images, masks in dataloader:
                images = images.to(device)
                masks = masks.to(device)

                preds = model(images)

                for i in range(preds.shape[0]):
                    p = preds[i].cpu().numpy()
                    t = masks[i].cpu().numpy()
                    all_acc.append(pixel_accuracy(p, t))
                    all_iou.append(iou_score(p, t))
                    all_dice.append(dice_score(p, t))

        return {
            "pixel_accuracy": round(np.mean(all_acc), 4),
            "iou": round(np.mean(all_iou), 4),
            "dice": round(np.mean(all_dice), 4),
            "num_samples": len(all_acc),
        }

    def evaluate_classification(self, model, dataloader, num_classes=2, device=None):
        """
        Evaluate a classification model (e.g., landslide, cyclone, fire, defense).

        Returns metrics: accuracy, precision, recall, F1, confusion matrix.
        """
        device = device or torch.device("cpu")
        model.eval()

        all_preds = []
        all_targets = []

        with torch.no_grad():
            for images, labels in dataloader:
                images = images.to(device)
                outputs = model(images)

                if num_classes == 2:
                    preds = (outputs.squeeze() > 0.5).long()
                else:
                    _, preds = outputs.max(1)

                all_preds.extend(preds.cpu().numpy())
                all_targets.extend(labels.numpy())

        all_preds = np.array(all_preds)
        all_targets = np.array(all_targets)

        accuracy = float((all_preds == all_targets).mean())
        cm = confusion_matrix(all_preds, all_targets, num_classes, threshold=0.5)

        result = {
            "accuracy": round(accuracy, 4),
            "confusion_matrix": cm.tolist(),
            "num_samples": len(all_preds),
        }

        if num_classes == 2:
            result["precision"] = round(precision_score(all_preds, all_targets), 4)
            result["recall"] = round(recall_score(all_preds, all_targets), 4)
            result["f1"] = round(f1_score(all_preds, all_targets), 4)

        return result

    def generate_report(self, model_name, metrics):
        """
        Generate a formatted evaluation report.

        Parameters
        ----------
        model_name : str
            Name of the model being evaluated.
        metrics : dict
            Evaluation metrics from above methods.

        Returns
        -------
        str
            Formatted evaluation report.
        """
        lines = [
            f"{'═' * 50}",
            f"  Evaluation Report: {model_name}",
            f"{'═' * 50}",
            f"  Samples Evaluated: {metrics.get('num_samples', 'N/A')}",
        ]

        if "pixel_accuracy" in metrics:
            lines.append(f"  Pixel Accuracy:    {metrics['pixel_accuracy']:.2%}")
            lines.append(f"  IoU (Jaccard):     {metrics['iou']:.2%}")
            lines.append(f"  Dice Coefficient:  {metrics['dice']:.2%}")

        if "accuracy" in metrics:
            lines.append(f"  Accuracy:          {metrics['accuracy']:.2%}")

        if "precision" in metrics:
            lines.append(f"  Precision:         {metrics['precision']:.2%}")
            lines.append(f"  Recall:            {metrics['recall']:.2%}")
            lines.append(f"  F1 Score:          {metrics['f1']:.2%}")

        lines.append(f"{'═' * 50}")
        return "\n".join(lines)
