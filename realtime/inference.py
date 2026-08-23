"""
Real-time flood inference module.

Loads the trained FloodCNN model and runs prediction on a single
satellite image, returning the mean flood probability.
"""

import os
import cv2
import torch
import numpy as np

from models.flood_cnn import FloodCNN

# ── Model Loading ────────────────────────────────────────────────────────────
_DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), "..", "models", "flood_model.pth")

_model = None


def _load_model(weights_path=None):
    """Lazy-load model weights (once)."""
    global _model
    if _model is not None:
        return _model

    weights = weights_path or _DEFAULT_WEIGHTS
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _model = FloodCNN().to(device)

    if os.path.isfile(weights):
        _model.load_state_dict(
            torch.load(weights, map_location=device, weights_only=True)
        )
        _model.eval()
        print(f"[inference] Loaded flood model from {weights}")
    else:
        print(
            f"[inference] WARNING – weights not found at {weights}. "
            "Model will use random weights (train first)."
        )

    return _model


def predict(image_input, weights_path=None, return_mask=False):
    """
    Run flood detection on a single image.

    Parameters
    ----------
    image_input : str or numpy.ndarray
        File path to an image, or a pre-loaded BGR numpy array.
    weights_path : str, optional
        Override default model weights path.
    return_mask : bool
        If True, also return the full (256×256) probability mask.

    Returns
    -------
    float
        Mean flood probability in [0, 1].
    numpy.ndarray (optional)
        256×256 flood probability mask (if return_mask=True).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = _load_model(weights_path)

    # Load image
    if isinstance(image_input, str):
        img = cv2.imread(image_input, cv2.IMREAD_COLOR)
        if img is None:
            raise IOError(f"Cannot read image: {image_input}")
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        raise TypeError(f"Unsupported image_input type: {type(image_input)}")

    img = cv2.resize(img, (256, 256))
    tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
    tensor = tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(tensor)

    flood_prob = output.mean().item()
    flood_prob = round(float(flood_prob), 4)

    if return_mask:
        mask = output.squeeze().cpu().numpy()
        return flood_prob, mask

    return flood_prob
