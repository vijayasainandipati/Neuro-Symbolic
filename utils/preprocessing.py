"""
Preprocessing utilities for satellite imagery and geospatial data.
"""

import cv2
import numpy as np


def normalize_image(image, target_size=(256, 256)):
    """Resize and normalize an image to [0, 1] float32."""
    image = cv2.resize(image, target_size)
    return image.astype(np.float32) / 255.0


def calculate_ndwi(green_band, nir_band):
    """
    Normalized Difference Water Index.

    NDWI = (Green - NIR) / (Green + NIR)

    Values > 0 indicate water presence.
    """
    green = green_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = green + nir
    denominator[denominator == 0] = 1e-8  # avoid division by zero
    ndwi = (green - nir) / denominator
    return ndwi


def calculate_ndvi(red_band, nir_band):
    """
    Normalized Difference Vegetation Index.

    NDVI = (NIR - Red) / (NIR + Red)
    """
    red = red_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = nir + red
    denominator[denominator == 0] = 1e-8
    ndvi = (nir - red) / denominator
    return ndvi


def tile_image(image, tile_size=256):
    """
    Split a large satellite image into non-overlapping tiles.

    Returns a list of (tile, row_idx, col_idx) tuples.
    """
    h, w = image.shape[:2]
    tiles = []
    for r in range(0, h, tile_size):
        for c in range(0, w, tile_size):
            tile = image[r : r + tile_size, c : c + tile_size]
            # Pad if needed
            if tile.shape[0] < tile_size or tile.shape[1] < tile_size:
                padded = np.zeros(
                    (tile_size, tile_size, *image.shape[2:]), dtype=image.dtype
                )
                padded[: tile.shape[0], : tile.shape[1]] = tile
                tile = padded
            tiles.append((tile, r // tile_size, c // tile_size))
    return tiles
