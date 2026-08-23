"""
Vision Transformer (ViT) for Tropical Cyclone Impact Assessment.

Model: Vision Transformer (ViT)
Data: Large-scale satellite imagery (Sentinel-2 / MODIS)

Why ViT:
  Cyclone damage patterns are large-scale spatial features that
  benefit from the global attention mechanism of transformers,
  unlike CNNs which have limited receptive fields.

Architecture:
  Satellite Tiles (256×256×3)
       ↓
  Patch Embedding (16×16 patches → 256 tokens)
       ↓
  Positional Encoding
       ↓
  Transformer Encoder (N layers of self-attention)
       ↓
  [CLS] Token → Classification Head
       ↓
  Damage Classification (4 classes)

Damage Categories:
  0 - No Damage
  1 - Minor Damage (vegetation loss, minor flooding)
  2 - Moderate Damage (structural damage, road blockage)
  3 - Severe Damage (total destruction, widespread flooding)
"""

import math
import torch
import torch.nn as nn


class _PatchEmbedding(nn.Module):
    """Split image into patches and project to embedding dimension."""

    def __init__(self, img_size=256, patch_size=16, in_channels=3, embed_dim=512):
        super().__init__()
        self.num_patches = (img_size // patch_size) ** 2
        self.proj = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size, stride=patch_size,
        )

    def forward(self, x):
        x = self.proj(x)
        return x.flatten(2).transpose(1, 2)


class CycloneViT(nn.Module):
    """
    Vision Transformer for cyclone damage classification.

    Captures long-range spatial dependencies in satellite imagery
    that are characteristic of cyclone damage patterns.

    Parameters
    ----------
    img_size : int
        Input image size (square).
    patch_size : int
        Size of each patch.
    in_channels : int
        Number of input channels.
    embed_dim : int
        Transformer embedding dimension.
    num_heads : int
        Number of attention heads.
    num_layers : int
        Number of transformer encoder layers.
    mlp_dim : int
        Hidden dimension in feed-forward network.
    num_classes : int
        Number of damage categories (default: 4).
    dropout : float
        Dropout rate.
    """

    DAMAGE_CLASSES = ["no_damage", "minor_damage", "moderate_damage", "severe_damage"]

    def __init__(
        self,
        img_size=256,
        patch_size=16,
        in_channels=3,
        embed_dim=512,
        num_heads=8,
        num_layers=6,
        mlp_dim=1024,
        num_classes=4,
        dropout=0.1,
    ):
        super().__init__()

        self.num_classes = num_classes
        self.patch_embed = _PatchEmbedding(img_size, patch_size, in_channels, embed_dim)
        num_patches = self.patch_embed.num_patches

        # Learnable [CLS] token and positional embeddings
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, embed_dim))
        self.pos_drop = nn.Dropout(dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=mlp_dim,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.norm = nn.LayerNorm(embed_dim)

        # Multi-class classification head
        self.head = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes),
        )

        self._init_weights()

    def _init_weights(self):
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

    def forward(self, x):
        """
        x : (B, C, H, W) → (B, num_classes) damage logits
        """
        B = x.shape[0]

        # Patch embedding
        tokens = self.patch_embed(x)

        # Prepend [CLS] token
        cls = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls, tokens], dim=1)

        # Add positional encoding
        tokens = self.pos_drop(tokens + self.pos_embed)

        # Transformer
        tokens = self.transformer(tokens)
        tokens = self.norm(tokens)

        # Classification from [CLS] token
        cls_output = tokens[:, 0]
        return self.head(cls_output)

    def predict_damage(self, x):
        """
        Predict cyclone damage level with confidence scores.

        Returns
        -------
        dict
            'class_idx': int, 'class_name': str, 'confidence': float,
            'all_probabilities': dict
        """
        with torch.no_grad():
            logits = self.forward(x)
            probs = torch.softmax(logits, dim=1)

            class_idx = probs.argmax(dim=1).item()
            confidence = probs[0, class_idx].item()

            all_probs = {
                self.DAMAGE_CLASSES[i]: round(probs[0, i].item(), 4)
                for i in range(self.num_classes)
            }

        return {
            "class_idx": class_idx,
            "class_name": self.DAMAGE_CLASSES[class_idx],
            "confidence": round(confidence, 4),
            "all_probabilities": all_probs,
        }

    def get_attention_maps(self, x):
        """
        Extract attention maps for interpretability.

        Returns list of attention weight tensors, one per layer.
        """
        B = x.shape[0]
        tokens = self.patch_embed(x)
        cls = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls, tokens], dim=1)
        tokens = self.pos_drop(tokens + self.pos_embed)

        attention_maps = []
        for layer in self.transformer.layers:
            # Extract self-attention weights
            attn_layer = layer.self_attn
            attn_output, attn_weights = attn_layer(
                tokens, tokens, tokens, need_weights=True
            )
            attention_maps.append(attn_weights.detach().cpu())
            tokens = layer(tokens)

        return attention_maps


def get_cyclone_model(num_classes=4, pretrained_backbone=False):
    """
    Factory function to create cyclone damage assessment model.

    Parameters
    ----------
    num_classes : int
        Number of damage categories.
    pretrained_backbone : bool
        (Reserved for future ViT pretrained weights support.)
    """
    return CycloneViT(num_classes=num_classes)
