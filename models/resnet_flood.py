"""
ResNet50-based flood classifier with transfer learning.

Uses a pretrained ResNet50 backbone (ImageNet weights) and replaces
the final classification head for binary flood detection.

Architecture
────────────
  Input Image (256×256×3)
       ↓
  ResNet50 Backbone (pretrained, frozen early layers)
       ↓
  Adaptive Average Pool
       ↓
  FC 2048 → 256 → 1
       ↓
  Sigmoid → Flood Probability
"""

import torch
import torch.nn as nn
import torchvision.models as models


class ResNetFloodClassifier(nn.Module):
    """ResNet50 transfer-learning flood classifier."""

    def __init__(self, pretrained=True, freeze_backbone=True):
        super().__init__()

        # Load pretrained ResNet50
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        backbone = models.resnet50(weights=weights)

        # Freeze early layers to preserve learned features
        if freeze_backbone:
            for name, param in backbone.named_parameters():
                if "layer4" not in name and "fc" not in name:
                    param.requires_grad = False

        # Remove the original fully-connected head
        self.features = nn.Sequential(*list(backbone.children())[:-1])

        # Custom classification head
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(2048, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        features = self.features(x)
        return self.classifier(features)

    def extract_features(self, x):
        """Return the 2048-d feature vector (before classifier)."""
        with torch.no_grad():
            return self.features(x).squeeze(-1).squeeze(-1)


class ResNetFloodSegmentor(nn.Module):
    """
    ResNet50 encoder + lightweight decoder for segmentation.

    Combines the power of pretrained ResNet features with
    an upsampling decoder to produce flood masks.
    """

    def __init__(self, pretrained=True):
        super().__init__()

        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        resnet = models.resnet50(weights=weights)

        # Encoder stages from ResNet
        self.enc0 = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu)  # 64, /2
        self.pool0 = resnet.maxpool                                        # 64, /4
        self.enc1 = resnet.layer1  # 256,  /4
        self.enc2 = resnet.layer2  # 512,  /8
        self.enc3 = resnet.layer3  # 1024, /16
        self.enc4 = resnet.layer4  # 2048, /32

        # Decoder (progressive upsampling with channel reduction)
        self.up4 = self._up_block(2048, 1024)
        self.up3 = self._up_block(1024, 512)
        self.up2 = self._up_block(512, 256)
        self.up1 = self._up_block(256, 64)
        self.up0 = self._up_block(64, 32)

        self.out_conv = nn.Conv2d(32, 1, kernel_size=1)

    @staticmethod
    def _up_block(in_ch, out_ch):
        return nn.Sequential(
            nn.ConvTranspose2d(in_ch, out_ch, kernel_size=2, stride=2),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        # Encoder
        e0 = self.enc0(x)       # /2
        p0 = self.pool0(e0)     # /4
        e1 = self.enc1(p0)      # /4
        e2 = self.enc2(e1)      # /8
        e3 = self.enc3(e2)      # /16
        e4 = self.enc4(e3)      # /32

        # Decoder
        d4 = self.up4(e4)       # /16
        d3 = self.up3(d4 + e3)  # /8
        d2 = self.up2(d3 + e2)  # /4
        d1 = self.up1(d2 + e1)  # /2
        d0 = self.up0(d1)       # /1

        return torch.sigmoid(self.out_conv(d0))
