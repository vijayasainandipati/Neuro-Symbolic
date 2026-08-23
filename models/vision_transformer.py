"""
Vision Transformer (ViT) for satellite flood classification.

Modern transformer architecture that captures global spatial
relationships in satellite imagery.

Architecture
────────────
  Input Image (256×256×3)
       ↓
  Patch Embedding (16×16 patches → 256 tokens)
       ↓
  Positional Encoding
       ↓
  Transformer Encoder (N layers)
       ↓
  [CLS] Token → Classification Head
       ↓
  Sigmoid → Flood Probability
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
        # x: (B, C, H, W) → (B, embed_dim, H/P, W/P) → (B, N, embed_dim)
        x = self.proj(x)
        return x.flatten(2).transpose(1, 2)


class VisionTransformerFlood(nn.Module):
    """
    ViT-based flood classifier for satellite imagery.

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
    dropout : float
        Dropout rate.
    """

    def __init__(
        self,
        img_size=256,
        patch_size=16,
        in_channels=3,
        embed_dim=512,
        num_heads=8,
        num_layers=6,
        mlp_dim=1024,
        dropout=0.1,
    ):
        super().__init__()

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

        # Classification head
        self.head = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, 1),
            nn.Sigmoid(),
        )

        self._init_weights()

    def _init_weights(self):
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

    def forward(self, x):
        """
        x : (B, C, H, W) → (B, 1) flood probability
        """
        B = x.shape[0]

        # Patch embedding
        tokens = self.patch_embed(x)  # (B, N, embed_dim)

        # Prepend [CLS] token
        cls = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls, tokens], dim=1)  # (B, N+1, embed_dim)

        # Add positional encoding
        tokens = self.pos_drop(tokens + self.pos_embed)

        # Transformer
        tokens = self.transformer(tokens)
        tokens = self.norm(tokens)

        # Classification from [CLS] token
        cls_output = tokens[:, 0]
        return self.head(cls_output)

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

        attentions = []
        for layer in self.transformer.layers:
            # Extract attention weights from self-attention
            attn_layer = layer.self_attn
            attn_output, attn_weights = attn_layer(
                tokens, tokens, tokens, need_weights=True
            )
            attentions.append(attn_weights.detach())
            # Still need to run through the full layer for correct output
            tokens = layer(tokens)

        return attentions
