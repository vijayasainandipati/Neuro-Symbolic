"""
Dataset loaders for satellite imagery.

Supported datasets:
  - EuroSAT (10-class land-use classification, 64×64 RGB JPG)
  - WorldFloods / SEN12-FLOOD (flood segmentation masks)

Place satellite images in  data/satellite_images/
Place corresponding masks in data/flood_masks/
"""

import os
import csv
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset


# ── EuroSAT Class Names ─────────────────────────────────────────────────────
EUROSAT_CLASSES = [
    "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway",
    "Industrial", "Pasture", "PermanentCrop", "Residential",
    "River", "SeaLake",
]


class EuroSATDataset(Dataset):
    """
    PyTorch dataset for EuroSAT satellite image classification.

    Reads a CSV split file (train.csv / validation.csv / test.csv) with
    columns: Filename, Label, ClassName.  Images are 64×64 RGB JPEGs
    stored under `root_dir/<ClassName>/<filename>.jpg`.

    Parameters
    ----------
    root_dir : str
        Path to `data/satellite_images/EuroSAT/`.
    csv_file : str
        Name of the split CSV file (e.g. ``train.csv``).
    img_size : int
        Resize images to this square size.
    augment : bool
        Apply random flips / rotations during training.
    """

    def __init__(self, root_dir, csv_file="train.csv", img_size=64, augment=False):
        self.root_dir = root_dir
        self.img_size = img_size
        self.augment = augment

        csv_path = os.path.join(root_dir, csv_file)
        self.samples = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.samples.append((row["Filename"], int(row["Label"])))

        if not self.samples:
            raise FileNotFoundError(f"No samples found in {csv_path}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        filename, label = self.samples[idx]
        img_path = os.path.join(self.root_dir, filename)

        image = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if image is None:
            raise IOError(f"Cannot read image: {img_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (self.img_size, self.img_size))

        if self.augment:
            image = self._augment(image)

        image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        # ImageNet normalization
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        image = (image - mean) / std

        return image, label

    @staticmethod
    def _augment(image):
        if np.random.rand() > 0.5:
            image = cv2.flip(image, 1)
        if np.random.rand() > 0.5:
            image = cv2.flip(image, 0)
        if np.random.rand() > 0.5:
            k = np.random.choice([1, 2, 3])
            image = np.rot90(image, k).copy()
        return image


class FloodDataset(Dataset):
    """PyTorch dataset for satellite flood segmentation."""

    def __init__(self, image_dir, mask_dir, img_size=256, augment=False):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.img_size = img_size
        self.augment = augment

        # Only include files that have a matching mask
        all_images = sorted(os.listdir(image_dir))
        all_masks = set(os.listdir(mask_dir))
        self.images = [f for f in all_images if f in all_masks]

        if len(self.images) == 0:
            raise FileNotFoundError(
                f"No matching image/mask pairs found in "
                f"'{image_dir}' and '{mask_dir}'. "
                "Ensure filenames match between folders."
            )

    def __len__(self):
        return len(self.images)

    def _apply_augmentation(self, image, mask):
        """Basic spatial augmentations applied identically to image & mask."""
        if np.random.rand() > 0.5:
            image = cv2.flip(image, 1)  # horizontal flip
            mask = cv2.flip(mask, 1)
        if np.random.rand() > 0.5:
            image = cv2.flip(image, 0)  # vertical flip
            mask = cv2.flip(mask, 0)
        if np.random.rand() > 0.5:
            k = np.random.choice([1, 2, 3])
            image = np.rot90(image, k).copy()
            mask = np.rot90(mask, k).copy()
        return image, mask

    def __getitem__(self, idx):
        img_name = self.images[idx]
        img_path = os.path.join(self.image_dir, img_name)
        mask_path = os.path.join(self.mask_dir, img_name)

        image = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if image is None:
            raise IOError(f"Cannot read image: {img_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (self.img_size, self.img_size))

        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise IOError(f"Cannot read mask: {mask_path}")
        mask = cv2.resize(mask, (self.img_size, self.img_size))

        if self.augment:
            image, mask = self._apply_augmentation(image, mask)

        # Convert to tensors  (C, H, W)
        image = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        mask = torch.from_numpy(mask).unsqueeze(0).float() / 255.0

        return image, mask
