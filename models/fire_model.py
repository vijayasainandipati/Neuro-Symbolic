"""
YOLOv8-Style Urban Fire Detection Model.

Model: YOLOv8-inspired object detection + classification CNN
Data: Satellite/aerial imagery with fire regions

Architecture:
  Image (640×640×3)
       ↓
  YOLO-style Backbone CNN (CSPDarknet-inspired)
       ↓
  Feature Pyramid Network (FPN)
       ↓
  Detection Head → Bounding boxes
       ↓
  Fire Region Detection + Confidence

Output Example:
  Fire detected
  Confidence = 0.91

Note: For production use, the ultralytics YOLOv8 package can be
used with a fine-tuned model. This module provides a compatible
architecture that can be trained from scratch or used as a wrapper.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False


class FireBackbone(nn.Module):
    """CSPDarknet-inspired backbone for fire detection."""

    def __init__(self, in_channels=3):
        super().__init__()

        self.stage1 = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.SiLU(inplace=True),
        )
        self.stage2 = self._make_stage(32, 64, num_blocks=1)
        self.stage3 = self._make_stage(64, 128, num_blocks=2)
        self.stage4 = self._make_stage(128, 256, num_blocks=3)
        self.stage5 = self._make_stage(256, 512, num_blocks=2)

    @staticmethod
    def _make_stage(in_ch, out_ch, num_blocks):
        layers = [
            nn.Conv2d(in_ch, out_ch, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.SiLU(inplace=True),
        ]
        for _ in range(num_blocks):
            layers.extend([
                nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.SiLU(inplace=True),
            ])
        return nn.Sequential(*layers)

    def forward(self, x):
        c1 = self.stage1(x)   # /2
        c2 = self.stage2(c1)  # /4
        c3 = self.stage3(c2)  # /8
        c4 = self.stage4(c3)  # /16
        c5 = self.stage5(c4)  # /32
        return c3, c4, c5


class FireFPN(nn.Module):
    """Feature Pyramid Network for multi-scale fire detection."""

    def __init__(self):
        super().__init__()

        self.lateral5 = nn.Conv2d(512, 256, 1)
        self.lateral4 = nn.Conv2d(256, 256, 1)
        self.lateral3 = nn.Conv2d(128, 256, 1)

        self.smooth5 = nn.Conv2d(256, 256, 3, padding=1)
        self.smooth4 = nn.Conv2d(256, 256, 3, padding=1)
        self.smooth3 = nn.Conv2d(256, 256, 3, padding=1)

    def forward(self, c3, c4, c5):
        p5 = self.lateral5(c5)
        p4 = self.lateral4(c4) + F.interpolate(p5, size=c4.shape[2:], mode="nearest")
        p3 = self.lateral3(c3) + F.interpolate(p4, size=c3.shape[2:], mode="nearest")

        p5 = self.smooth5(p5)
        p4 = self.smooth4(p4)
        p3 = self.smooth3(p3)

        return p3, p4, p5


class FireDetectionHead(nn.Module):
    """
    Detection head for fire regions.

    Outputs per-anchor predictions:
      - 4 bounding box coordinates (x, y, w, h)
      - 1 objectness score
      - 2 class scores (fire, smoke)
    """

    def __init__(self, in_channels=256, num_classes=2, num_anchors=3):
        super().__init__()
        self.num_classes = num_classes
        self.num_anchors = num_anchors

        out_channels = num_anchors * (5 + num_classes)  # 5 = 4 bbox + 1 obj

        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(inplace=True),
            nn.Conv2d(in_channels, out_channels, 1),
        )

    def forward(self, x):
        return self.conv(x)


class FireDetector(nn.Module):
    """
    Complete YOLOv8-style fire detection model.

    Detects fire regions and smoke in satellite/aerial imagery
    with bounding boxes and confidence scores.
    """

    CLASS_NAMES = ["fire", "smoke"]

    def __init__(self, in_channels=3, num_classes=2):
        super().__init__()
        self.backbone = FireBackbone(in_channels)
        self.fpn = FireFPN()
        self.head = FireDetectionHead(256, num_classes)
        self.num_classes = num_classes

        # For classification-only mode (simpler inference)
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes + 1),  # +1 for "no fire"
        )

    def forward(self, x):
        """
        Full detection forward pass.

        Returns multi-scale detection outputs.
        """
        c3, c4, c5 = self.backbone(x)
        p3, p4, p5 = self.fpn(c3, c4, c5)

        det_p3 = self.head(p3)
        det_p4 = self.head(p4)
        det_p5 = self.head(p5)

        return det_p3, det_p4, det_p5

    def classify(self, x):
        """
        Simple classification mode — returns fire/smoke/no_fire probabilities.

        Useful for quick screening before running full detection.
        """
        c3, c4, c5 = self.backbone(x)
        logits = self.classifier(c5)
        return torch.softmax(logits, dim=1)

    def predict_fire(self, x):
        """
        High-level fire prediction with confidence.

        Returns
        -------
        dict
            'detected': bool, 'confidence': float,
            'class_probabilities': dict
        """
        with torch.no_grad():
            probs = self.classify(x)
            class_names = self.CLASS_NAMES + ["no_fire"]
            all_probs = {
                class_names[i]: round(probs[0, i].item(), 4)
                for i in range(len(class_names))
            }

            fire_prob = probs[0, 0].item()  # fire class
            smoke_prob = probs[0, 1].item()
            max_threat = max(fire_prob, smoke_prob)

        return {
            "detected": max_threat > 0.5,
            "confidence": round(max_threat, 4),
            "fire_probability": round(fire_prob, 4),
            "smoke_probability": round(smoke_prob, 4),
            "class_probabilities": all_probs,
        }


def get_fire_model(use_ultralytics=False, yolo_weights=None):
    """
    Factory function to create the fire detection model.

    Parameters
    ----------
    use_ultralytics : bool
        If True and ultralytics is installed, use YOLOv8.
    yolo_weights : str or None
        Path to YOLOv8 weights file.

    Returns
    -------
    Model instance.
    """
    if use_ultralytics and HAS_ULTRALYTICS and yolo_weights:
        return YOLO(yolo_weights)
    return FireDetector()
