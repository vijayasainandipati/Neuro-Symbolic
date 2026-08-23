"""
YOLOv8-Style Defense Object Detection Model.

Model: YOLOv8-inspired detection + classification CNN
Data: Drone/satellite surveillance imagery

Detects:
  - Tanks
  - Trucks
  - Military vehicles
  - Equipment
  - Temporary installations
  - Troop movement patterns

Architecture:
  Drone/Satellite Image (640×640×3)
       ↓
  YOLO Backbone CNN (CSPDarknet-inspired)
       ↓
  Feature Pyramid Network (FPN)
       ↓
  Object Detection Head
       ↓
  Bounding Boxes + Classification

Output Example:
  Vehicle count = 6
  Movement detected

For restricted zone monitoring and border vehicle movement
detection using satellite/drone imagery.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False


class DefenseBackbone(nn.Module):
    """CSPDarknet-inspired backbone for defense object detection."""

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
        c1 = self.stage1(x)
        c2 = self.stage2(c1)
        c3 = self.stage3(c2)
        c4 = self.stage4(c3)
        c5 = self.stage5(c4)
        return c3, c4, c5


class DefenseFPN(nn.Module):
    """Feature Pyramid Network for multi-scale defense detection."""

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


class DefenseDetectionHead(nn.Module):
    """Detection head for defense objects."""

    def __init__(self, in_channels=256, num_classes=6, num_anchors=3):
        super().__init__()
        out_channels = num_anchors * (5 + num_classes)

        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(inplace=True),
            nn.Conv2d(in_channels, out_channels, 1),
        )

    def forward(self, x):
        return self.conv(x)


class DefenseObjectDetector(nn.Module):
    """
    Complete YOLOv8-style defense object detection model.

    Detects military vehicles, equipment, installations, and
    troop movement patterns in surveillance imagery.

    Classes:
      0 - Tank
      1 - Truck
      2 - Military Vehicle
      3 - Equipment
      4 - Temporary Installation
      5 - Troop Formation
    """

    NUM_CLASSES = 6
    CLASS_NAMES = [
        "tank", "truck", "military_vehicle",
        "equipment", "temporary_installation", "troop_formation",
    ]

    def __init__(self, in_channels=3):
        super().__init__()
        self.backbone = DefenseBackbone(in_channels)
        self.fpn = DefenseFPN()
        self.head = DefenseDetectionHead(256, self.NUM_CLASSES)

        # Classification-only mode
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, self.NUM_CLASSES),
        )

        # Threat score estimator
        self.threat_head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        """Full detection forward pass."""
        c3, c4, c5 = self.backbone(x)
        p3, p4, p5 = self.fpn(c3, c4, c5)

        det_p3 = self.head(p3)
        det_p4 = self.head(p4)
        det_p5 = self.head(p5)

        return det_p3, det_p4, det_p5

    def classify(self, x):
        """Classification-only mode — returns class probabilities."""
        c3, c4, c5 = self.backbone(x)
        logits = self.classifier(c5)
        return torch.softmax(logits, dim=1)

    def estimate_threat(self, x):
        """Estimate overall threat score (0-1)."""
        c3, c4, c5 = self.backbone(x)
        return self.threat_head(c5)

    def predict_with_confidence(self, x):
        """
        Full prediction with class, confidence, and threat score.

        Returns
        -------
        dict with classification, threat score, and vehicle count estimate.
        """
        with torch.no_grad():
            probs = self.classify(x)
            threat = self.estimate_threat(x)

            class_idx = probs.argmax(dim=1).item()
            confidence = probs[0, class_idx].item()

            all_probs = {
                self.CLASS_NAMES[i]: round(probs[0, i].item(), 4)
                for i in range(self.NUM_CLASSES)
            }

        return {
            "class_idx": class_idx,
            "class_name": self.CLASS_NAMES[class_idx],
            "confidence": round(confidence, 4),
            "threat_score": round(threat.item(), 4),
            "all_probabilities": all_probs,
        }


def get_defense_model(use_ultralytics=False, yolo_weights=None):
    """
    Factory function to create the defense detection model.

    Parameters
    ----------
    use_ultralytics : bool
        If True and ultralytics is installed, use YOLOv8.
    yolo_weights : str or None
        Path to YOLOv8 weights file.
    """
    if use_ultralytics and HAS_ULTRALYTICS and yolo_weights:
        return YOLO(yolo_weights)
    return DefenseObjectDetector()
