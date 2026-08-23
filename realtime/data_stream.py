"""
Satellite Data Streaming Module.

Provides functions to load and stream satellite imagery from:
  - Local dataset directories
  - Copernicus Open Access Hub (ESA Sentinel-1/2)
  - NASA Earthdata (MODIS, Landsat)

For production, register for API credentials at:
  https://scihub.copernicus.eu/
  https://earthdata.nasa.gov/

For the prototype, supports loading images from local datasets
for real-time simulation.
"""

import os
import logging
import glob
import random
from datetime import datetime, timedelta

import cv2
import numpy as np
import requests

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
COPERNICUS_USER = os.environ.get("COPERNICUS_USER", "")
COPERNICUS_PASS = os.environ.get("COPERNICUS_PASS", "")
NASA_EARTHDATA_TOKEN = os.environ.get("NASA_EARTHDATA_TOKEN", "")

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")


class DataStream:
    """
    Multi-source data streamer for real-time hazard monitoring.

    Streams satellite imagery from local datasets or remote APIs,
    cycling through available images to simulate real-time feeds.
    """

    def __init__(self, datasets_dir=None):
        self.datasets_dir = datasets_dir or DATASETS_DIR
        self._image_indices = {}  # hazard_type → current index
        self._image_lists = {}   # hazard_type → list of image paths

    def get_next_image(self, hazard_type="flood"):
        """
        Get the next available image for a given hazard type.

        Cycles through images in the dataset directory.

        Parameters
        ----------
        hazard_type : str
            One of 'flood', 'landslide', 'cyclone', 'fire', 'defense_objects'.

        Returns
        -------
        np.ndarray or None
            Image as numpy array, or None if no images available.
        """
        if hazard_type not in self._image_lists:
            self._load_image_list(hazard_type)

        images = self._image_lists.get(hazard_type, [])
        if not images:
            return self._generate_synthetic_image(hazard_type)

        idx = self._image_indices.get(hazard_type, 0)
        img_path = images[idx % len(images)]
        self._image_indices[hazard_type] = idx + 1

        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if img is None:
            logger.warning("Cannot read image: %s", img_path)
            return self._generate_synthetic_image(hazard_type)

        return img

    def _load_image_list(self, hazard_type):
        """Load list of images for a hazard type from datasets directory."""
        hazard_dir = os.path.join(self.datasets_dir, hazard_type)

        if not os.path.isdir(hazard_dir):
            # Try the EuroSAT data as fallback
            eurosat_dir = os.path.join(
                self.datasets_dir, "..", "data", "satellite_images", "EuroSAT"
            )
            if os.path.isdir(eurosat_dir):
                images = []
                for subdir in os.listdir(eurosat_dir):
                    subdir_path = os.path.join(eurosat_dir, subdir)
                    if os.path.isdir(subdir_path):
                        images.extend(glob.glob(os.path.join(subdir_path, "*.jpg")))
                        images.extend(glob.glob(os.path.join(subdir_path, "*.png")))
                        images.extend(glob.glob(os.path.join(subdir_path, "*.tif")))
                self._image_lists[hazard_type] = images
                self._image_indices[hazard_type] = 0
                logger.info(
                    "Loaded %d EuroSAT images as fallback for %s",
                    len(images), hazard_type,
                )
                return

            self._image_lists[hazard_type] = []
            logger.warning("No dataset directory found for %s", hazard_type)
            return

        images = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff"):
            images.extend(glob.glob(os.path.join(hazard_dir, "**", ext), recursive=True))

        self._image_lists[hazard_type] = sorted(images)
        self._image_indices[hazard_type] = 0
        logger.info("Loaded %d images for %s", len(images), hazard_type)

    def _generate_synthetic_image(self, hazard_type):
        """
        Generate a synthetic satellite-like image for simulation
        when no real data is available.
        """
        size = 256
        img = np.random.randint(40, 120, (size, size, 3), dtype=np.uint8)

        if hazard_type == "flood":
            # Add blue-ish water regions
            cv2.rectangle(img, (30, 30), (200, 200), (180, 100, 50), -1)
            cv2.circle(img, (128, 128), 60, (200, 140, 60), -1)

        elif hazard_type == "landslide":
            # Add brown debris patterns
            pts = np.array([[50, 50], [200, 30], [230, 200], [60, 220]])
            cv2.fillPoly(img, [pts], (70, 90, 140))

        elif hazard_type == "cyclone":
            # Add spiral cloud pattern
            for r in range(20, 120, 10):
                angle = r * 3
                x = int(128 + r * np.cos(np.radians(angle)))
                y = int(128 + r * np.sin(np.radians(angle)))
                cv2.circle(img, (x, y), 15, (230, 230, 240), -1)

        elif hazard_type == "fire":
            # Add orange/red fire regions
            cv2.circle(img, (100, 100), 40, (30, 80, 220), -1)
            cv2.circle(img, (160, 140), 30, (20, 60, 200), -1)

        elif hazard_type == "defense_objects":
            # Add rectangular vehicle shapes
            for _ in range(random.randint(2, 6)):
                x = random.randint(20, 220)
                y = random.randint(20, 220)
                cv2.rectangle(img, (x, y), (x + 20, y + 10), (100, 100, 100), -1)

        # Add noise for realism
        noise = np.random.normal(0, 10, img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        return img

    def get_environmental_data(self, region_name="Unknown"):
        """
        Simulate environmental/contextual data for a region.

        In production, this would fetch from weather APIs (NASA, NOAA)
        and DEM elevation services.

        Returns
        -------
        dict
            Simulated environmental parameters.
        """
        return {
            "region": region_name,
            "population_density": random.randint(100, 2000),
            "elevation": round(random.uniform(1, 100), 1),
            "terrain_slope": round(random.uniform(0, 45), 1),
            "rainfall_mm": round(random.uniform(0, 300), 1),
            "soil_moisture": round(random.uniform(0.1, 0.9), 2),
            "wind_speed_kmh": round(random.uniform(0, 150), 1),
            "temperature_c": round(random.uniform(15, 45), 1),
            "infrastructure_density": round(random.uniform(0.1, 0.9), 2),
            "distance_to_border_km": round(random.uniform(0.5, 50), 1),
        }

    def search_sentinel2(self, bbox, start_date=None, end_date=None, max_cloud=30):
        """
        Query Copernicus Open Access Hub for Sentinel-2 products.

        Parameters
        ----------
        bbox : tuple
            (lon_min, lat_min, lon_max, lat_max) bounding box.
        start_date : str
            ISO date string (YYYY-MM-DD).
        end_date : str
            ISO date string (YYYY-MM-DD).
        max_cloud : int
            Max cloud cover percentage (0-100).

        Returns
        -------
        list[dict]
            Product metadata.
        """
        if not COPERNICUS_USER or not COPERNICUS_PASS:
            logger.warning(
                "Copernicus credentials not set. "
                "Export COPERNICUS_USER and COPERNICUS_PASS."
            )
            return []

        if end_date is None:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

        footprint = (
            f"POLYGON(("
            f"{bbox[0]} {bbox[1]},"
            f"{bbox[2]} {bbox[1]},"
            f"{bbox[2]} {bbox[3]},"
            f"{bbox[0]} {bbox[3]},"
            f"{bbox[0]} {bbox[1]}))"
        )

        query = (
            f"platformname:Sentinel-2 AND "
            f'footprint:"Intersects({footprint})" AND '
            f"beginPosition:[{start_date}T00:00:00.000Z TO {end_date}T23:59:59.999Z] AND "
            f"cloudcoverpercentage:[0 TO {max_cloud}]"
        )

        try:
            resp = requests.get(
                "https://scihub.copernicus.eu/dhus/search",
                params={"q": query, "rows": 5, "format": "json"},
                auth=(COPERNICUS_USER, COPERNICUS_PASS),
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            entries = data.get("feed", {}).get("entry", [])
            if isinstance(entries, dict):
                entries = [entries]
            return entries
        except requests.RequestException as e:
            logger.error("Sentinel-2 search failed: %s", e)
            return []
