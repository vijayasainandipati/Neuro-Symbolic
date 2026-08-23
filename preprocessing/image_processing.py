"""
Image processing utilities for satellite imagery.

Handles preprocessing for all hazard types:
  - Flood: NDWI computation, water body enhancement
  - Landslide: Terrain feature extraction, slope analysis
  - Cyclone: Large-scale patch preparation for ViT
  - Fire: Thermal band processing, smoke detection prep
  - Defense: Object detection preprocessing

Data sources: ESA Sentinel-2, NASA MODIS/Landsat, DEM elevation data.
"""

import cv2
import numpy as np


def normalize_image(image, target_size=(256, 256)):
    """
    Resize and normalize an image to [0, 1] float32.

    Parameters
    ----------
    image : np.ndarray
        Input image (BGR or RGB).
    target_size : tuple
        (width, height) for resizing.

    Returns
    -------
    np.ndarray
        Normalized float32 image.
    """
    image = cv2.resize(image, target_size)
    return image.astype(np.float32) / 255.0


def calculate_ndwi(green_band, nir_band):
    """
    Normalized Difference Water Index for flood detection.

    NDWI = (Green - NIR) / (Green + NIR)
    Values > 0 indicate water presence.
    """
    green = green_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = green + nir
    denominator[denominator == 0] = 1e-8
    return (green - nir) / denominator


def calculate_ndvi(red_band, nir_band):
    """
    Normalized Difference Vegetation Index for landslide/fire detection.

    NDVI = (NIR - Red) / (NIR + Red)
    Low/negative NDVI indicates bare soil (landslide) or burned area (fire).
    """
    red = red_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = nir + red
    denominator[denominator == 0] = 1e-8
    return (nir - red) / denominator


def calculate_nbr(nir_band, swir_band):
    """
    Normalized Burn Ratio for fire damage assessment.

    NBR = (NIR - SWIR) / (NIR + SWIR)
    Low NBR values indicate burned areas.
    """
    nir = nir_band.astype(np.float32)
    swir = swir_band.astype(np.float32)
    denominator = nir + swir
    denominator[denominator == 0] = 1e-8
    return (nir - swir) / denominator


def tile_image(image, tile_size=256):
    """
    Split a large satellite image into non-overlapping tiles.

    Used for processing large Sentinel-2 scenes tile-by-tile.

    Returns
    -------
    list[tuple]
        (tile, row_idx, col_idx) tuples.
    """
    h, w = image.shape[:2]
    tiles = []
    for r in range(0, h, tile_size):
        for c in range(0, w, tile_size):
            tile = image[r : r + tile_size, c : c + tile_size]
            if tile.shape[0] < tile_size or tile.shape[1] < tile_size:
                padded = np.zeros(
                    (tile_size, tile_size, *image.shape[2:]), dtype=image.dtype
                )
                padded[: tile.shape[0], : tile.shape[1]] = tile
                tile = padded
            tiles.append((tile, r // tile_size, c // tile_size))
    return tiles


def augment_image(image, flip=True, rotate=True, brightness=True):
    """
    Data augmentation for training satellite image models.

    Applies random transformations to increase dataset diversity.

    Parameters
    ----------
    image : np.ndarray
        Input image.
    flip : bool
        Apply random horizontal/vertical flips.
    rotate : bool
        Apply random 90-degree rotations.
    brightness : bool
        Apply random brightness adjustment.

    Returns
    -------
    np.ndarray
        Augmented image.
    """
    augmented = image.copy()

    if flip:
        if np.random.random() > 0.5:
            augmented = cv2.flip(augmented, 1)  # horizontal
        if np.random.random() > 0.5:
            augmented = cv2.flip(augmented, 0)  # vertical

    if rotate:
        k = np.random.randint(0, 4)
        augmented = np.rot90(augmented, k)

    if brightness:
        factor = np.random.uniform(0.8, 1.2)
        augmented = np.clip(augmented * factor, 0, 255).astype(augmented.dtype)

    return augmented


def preprocess_for_flood(image, target_size=(256, 256)):
    """Preprocess image for U-Net flood segmentation."""
    img = cv2.resize(image, target_size)
    return img.astype(np.float32) / 255.0


def preprocess_for_landslide(image, target_size=(224, 224)):
    """Preprocess image for ResNet50 landslide classification."""
    img = cv2.resize(image, target_size)
    img = img.astype(np.float32) / 255.0
    # ImageNet normalization
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    img = (img - mean) / std
    return img.astype(np.float32)


def preprocess_for_cyclone(image, target_size=(256, 256)):
    """Preprocess image for Vision Transformer cyclone analysis."""
    img = cv2.resize(image, target_size)
    return img.astype(np.float32) / 255.0


def preprocess_for_fire(image, target_size=(640, 640)):
    """Preprocess image for YOLOv8 fire detection."""
    img = cv2.resize(image, target_size)
    return img.astype(np.float32) / 255.0


def preprocess_for_defense(image, target_size=(640, 640)):
    """Preprocess image for YOLOv8 defense object detection."""
    img = cv2.resize(image, target_size)
    return img.astype(np.float32) / 255.0
