"""
ResNet50 + CNN Classifier for Landslide Detection.

Model: ResNet50 with transfer learning (ImageNet pretrained)
Data: Satellite imagery with terrain features

Architecture:
  Satellite Image (224×224×3)
       ↓
  Terrain Feature Extraction (NDVI, slope, elevation)
       ↓
  ResNet50 CNN (pretrained backbone)
       ↓
  Binary Classification Head
       ↓
  Landslide Probability (0-1)

Example output:
  Landslide probability = 0.87

Uses transfer learning from ImageNet to leverage pretrained
features for terrain pattern recognition. The model learns to
identify bare soil, debris flows, and slope failures from
satellite imagery.
"""

import torch
import torch.nn as nn
import torchvision.models as models


class LandslideResNet(nn.Module):
    """
    ResNet50-based landslide classifier with transfer learning.

    Uses a pretrained ResNet50 backbone and a custom classification
    head for binary landslide detection.
    """

    def __init__(self, pretrained=True, freeze_backbone=True, in_channels=3):
        super().__init__()

        # Load pretrained ResNet50
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        backbone = models.resnet50(weights=weights)

        # Freeze early layers to preserve learned features
        if freeze_backbone:
            for name, param in backbone.named_parameters():
                if "layer4" not in name and "fc" not in name:
                    param.requires_grad = False

        # Handle non-3-channel inputs (e.g., with terrain features)
        if in_channels != 3:
            backbone.conv1 = nn.Conv2d(
                in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False
            )

        # Remove the original fully-connected head
        self.features = nn.Sequential(*list(backbone.children())[:-1])

        # Custom classification head for landslide detection
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(2048, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        features = self.features(x)
        return self.classifier(features)

    def extract_features(self, x):
        """Return the 2048-d feature vector (before classifier)."""
        with torch.no_grad():
            return self.features(x).squeeze(-1).squeeze(-1)

    def predict_with_confidence(self, x):
        """
        Predict landslide probability with confidence estimate.

        Returns
        -------
        dict
            'probability': float, 'prediction': str, 'confidence': float
        """
        with torch.no_grad():
            prob = self.forward(x).item()

        prediction = "landslide" if prob > 0.5 else "stable"
        confidence = prob if prob > 0.5 else (1 - prob)

        return {
            "probability": round(prob, 4),
            "prediction": prediction,
            "confidence": round(confidence, 4),
        }


class LandslideTerrainModel(nn.Module):
    """
    Multi-input model combining satellite imagery with terrain data.

    Fuses visual features from ResNet50 with numerical terrain
    features (slope, elevation, soil type) for improved accuracy.
    """

    def __init__(self, num_terrain_features=5, pretrained=True):
        super().__init__()

        # Visual feature extractor
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        resnet = models.resnet50(weights=weights)
        self.visual_backbone = nn.Sequential(*list(resnet.children())[:-1])

        # Terrain feature processor
        self.terrain_net = nn.Sequential(
            nn.Linear(num_terrain_features, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 128),
            nn.ReLU(inplace=True),
        )

        # Fusion classifier
        self.fusion_classifier = nn.Sequential(
            nn.Linear(2048 + 128, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 1),
            nn.Sigmoid(),
        )

    def forward(self, image, terrain_features):
        """
        Parameters
        ----------
        image : torch.Tensor
            Satellite image (B, 3, 224, 224).
        terrain_features : torch.Tensor
            Terrain data (B, num_terrain_features).
            Features: [slope, elevation, aspect, curvature, soil_type]
        """
        visual = self.visual_backbone(image).flatten(1)
        terrain = self.terrain_net(terrain_features)
        fused = torch.cat([visual, terrain], dim=1)
        return self.fusion_classifier(fused)


def get_landslide_model(use_terrain=False, pretrained=True):
    """
    Factory function to create the landslide detection model.

    Parameters
    ----------
    use_terrain : bool
        If True, creates the multi-input terrain model.
    pretrained : bool
        Use ImageNet pretrained weights.
    """
    if use_terrain:
        return LandslideTerrainModel(pretrained=pretrained)
    return LandslideResNet(pretrained=pretrained)
