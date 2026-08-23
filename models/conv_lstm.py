"""
ConvLSTM model for satellite image time-series flood prediction.

Combines CNN spatial feature extraction with LSTM temporal learning
to predict flood progression from image sequences.

Architecture
────────────
  Satellite Image Sequence [T, C, H, W]
       ↓
  CNN Feature Extractor (per frame)
       ↓
  LSTM Temporal Learning
       ↓
  FC Head → Flood Probability
"""

import torch
import torch.nn as nn


class _SpatialEncoder(nn.Module):
    """Lightweight CNN to extract spatial features from each frame."""

    def __init__(self, in_channels=3, feature_dim=256):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.fc = nn.Linear(128 * 4 * 4, feature_dim)

    def forward(self, x):
        """x: (B, C, H, W) → (B, feature_dim)"""
        feat = self.cnn(x)
        return self.fc(feat.view(feat.size(0), -1))


class ConvLSTMPredictor(nn.Module):
    """
    ConvLSTM flood predictor for image sequences.

    Parameters
    ----------
    in_channels : int
        Number of image channels (3 for RGB).
    feature_dim : int
        Spatial feature vector size.
    hidden_dim : int
        LSTM hidden state size.
    num_layers : int
        Number of LSTM layers.
    """

    def __init__(self, in_channels=3, feature_dim=256, hidden_dim=128, num_layers=2):
        super().__init__()
        self.spatial_encoder = _SpatialEncoder(in_channels, feature_dim)
        self.lstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        """
        Parameters
        ----------
        x : torch.Tensor
            Shape (B, T, C, H, W) – batch of image sequences.

        Returns
        -------
        torch.Tensor
            Shape (B, 1) – flood probability for each sequence.
        """
        B, T, C, H, W = x.shape

        # Extract spatial features for each timestep
        x = x.view(B * T, C, H, W)
        features = self.spatial_encoder(x)         # (B*T, feature_dim)
        features = features.view(B, T, -1)         # (B, T, feature_dim)

        # Temporal modelling
        lstm_out, _ = self.lstm(features)           # (B, T, hidden_dim)
        last_hidden = lstm_out[:, -1, :]            # (B, hidden_dim)

        return self.classifier(last_hidden)


class ConvLSTMSegmentor(nn.Module):
    """
    ConvLSTM that outputs a per-pixel flood mask from an image sequence.

    Uses a shared CNN encoder per frame, an LSTM over the feature maps,
    and a lightweight decoder.
    """

    def __init__(self, in_channels=3, hidden_channels=64, num_layers=2):
        super().__init__()

        # Per-frame encoder
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )

        # LSTM operates on flattened feature maps per-pixel (channel-wise)
        self.temporal = nn.LSTM(
            input_size=64,
            hidden_size=hidden_channels,
            num_layers=num_layers,
            batch_first=True,
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Conv2d(hidden_channels, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
        )

    def forward(self, x):
        """
        x : (B, T, C, H, W) → (B, 1, H, W) flood mask
        """
        B, T, C, H, W = x.shape

        # Encode each frame
        encoded = []
        for t in range(T):
            encoded.append(self.encoder(x[:, t]))  # (B, 64, H, W)
        encoded = torch.stack(encoded, dim=1)       # (B, T, 64, H, W)

        # Reshape for per-pixel LSTM: (B*H*W, T, 64)
        encoded = encoded.permute(0, 3, 4, 1, 2).contiguous()
        encoded = encoded.view(B * H * W, T, -1)

        lstm_out, _ = self.temporal(encoded)        # (B*H*W, T, hidden)
        last = lstm_out[:, -1, :]                   # (B*H*W, hidden)

        # Reshape back to spatial
        last = last.view(B, H, W, -1).permute(0, 3, 1, 2)  # (B, hidden, H, W)

        return torch.sigmoid(self.decoder(last))
