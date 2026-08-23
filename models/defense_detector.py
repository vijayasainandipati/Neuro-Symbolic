"""
Defense Object Detection and Threat Assessment Model.

Dual-domain extension: detects military/defense-relevant objects
in satellite imagery (vehicles, installations, movement patterns)
alongside the existing flood detection capabilities.

Architecture
────────────
  CNN Feature Backbone (shared or separate from flood models)
       ↓
  Multi-class Object Classifier
       ↓
  Threat Score Estimator
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DefenseFeatureExtractor(nn.Module):
    """CNN backbone for defense-relevant feature extraction."""

    def __init__(self, in_channels=3):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(256, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4)),
        )

    def forward(self, x):
        return self.features(x)


class DefenseObjectClassifier(nn.Module):
    """
    Multi-class classifier for defense-relevant objects.

    Classes:
      0 - No threat / civilian
      1 - Military vehicle
      2 - Temporary installation
      3 - Troop movement pattern
      4 - Naval vessel
      5 - Aircraft / drone
    """

    NUM_CLASSES = 6
    CLASS_NAMES = [
        "civilian", "military_vehicle", "temporary_installation",
        "troop_movement", "naval_vessel", "aircraft_drone",
    ]

    def __init__(self, in_channels=3):
        super().__init__()
        self.backbone = DefenseFeatureExtractor(in_channels)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, self.NUM_CLASSES),
        )

    def forward(self, x):
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits

    def predict_with_confidence(self, x):
        """
        Return predicted class, confidence, and all probabilities.

        Parameters
        ----------
        x : torch.Tensor
            Input image tensor, shape (1, C, H, W).

        Returns
        -------
        dict with 'predicted_class', 'class_name', 'confidence',
        and 'all_probabilities'.
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1).squeeze()
            confidence, predicted = probs.max(0)

        all_probs = {
            name: round(probs[i].item(), 4)
            for i, name in enumerate(self.CLASS_NAMES)
        }

        return {
            "predicted_class": predicted.item(),
            "class_name": self.CLASS_NAMES[predicted.item()],
            "confidence": round(confidence.item(), 4),
            "all_probabilities": all_probs,
        }


class ThreatScoreEstimator(nn.Module):
    """
    Estimates an overall threat score (0-1) from image features.

    Combines object classification features with spatial pattern
    analysis to produce a single threat score.
    """

    def __init__(self, in_channels=3):
        super().__init__()
        self.backbone = DefenseFeatureExtractor(in_channels)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 4 * 4, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        features = self.backbone(x)
        return self.head(features).squeeze(-1)
