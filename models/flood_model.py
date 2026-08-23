"""
U-Net CNN for Pixel-Wise Flood Segmentation.

Model: U-Net with optional pretrained ResNet34 encoder
Data: ESA Sentinel-2 satellite imagery

Architecture:
  Input Satellite Image (256×256×3)
       ↓
  Encoder CNN (4 down-sampling blocks)
       ↓
  Feature Extraction (Bottleneck)
       ↓
  Decoder CNN (4 up-sampling blocks with skip connections)
       ↓
  Flood Segmentation Map (pixel-level)

The U-Net architecture works particularly well for satellite
flood detection because it preserves spatial resolution through
skip connections, enabling precise pixel-level flood boundary
delineation.
"""

import torch
import torch.nn as nn

try:
    import segmentation_models_pytorch as smp
    HAS_SMP = True
except ImportError:
    HAS_SMP = False


class _ConvBlock(nn.Module):
    """Double convolution block: Conv → BN → ReLU × 2."""

    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class FloodUNet(nn.Module):
    """
    Lightweight U-Net for flood mask prediction.

    Produces a single-channel sigmoid probability map
    where each pixel value represents flood probability.
    """

    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()

        # ── Encoder ──────────────────────────────────────────
        self.enc1 = _ConvBlock(in_channels, 32)
        self.enc2 = _ConvBlock(32, 64)
        self.enc3 = _ConvBlock(64, 128)
        self.enc4 = _ConvBlock(128, 256)

        self.pool = nn.MaxPool2d(2)

        # ── Bottleneck ───────────────────────────────────────
        self.bottleneck = _ConvBlock(256, 512)

        # ── Decoder ──────────────────────────────────────────
        self.up4 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec4 = _ConvBlock(512, 256)

        self.up3 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec3 = _ConvBlock(256, 128)

        self.up2 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec2 = _ConvBlock(128, 64)

        self.up1 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
        self.dec1 = _ConvBlock(64, 32)

        # ── Output ───────────────────────────────────────────
        self.out_conv = nn.Conv2d(32, out_channels, kernel_size=1)

    def forward(self, x):
        # Encoder path
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        # Bottleneck
        b = self.bottleneck(self.pool(e4))

        # Decoder path with skip connections
        d4 = self.dec4(torch.cat([self.up4(b), e4], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))

        return torch.sigmoid(self.out_conv(d1))


def get_flood_model(use_pretrained_encoder=True):
    """
    Factory function to create the best available flood model.

    If segmentation_models_pytorch is available, uses a pretrained
    ResNet34 encoder for better accuracy via transfer learning.
    Otherwise, falls back to the lightweight custom U-Net.

    Returns
    -------
    nn.Module
        Flood segmentation model.
    """
    if HAS_SMP and use_pretrained_encoder:
        model = smp.Unet(
            encoder_name="resnet34",
            encoder_weights="imagenet",
            in_channels=3,
            classes=1,
            activation="sigmoid",
        )
        return model
    else:
        return FloodUNet(in_channels=3, out_channels=1)
