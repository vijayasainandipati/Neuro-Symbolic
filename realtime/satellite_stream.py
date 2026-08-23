"""
Satellite data streaming module.

Provides functions to fetch real satellite imagery from:
  - Copernicus Open Access Hub (Sentinel-1 / Sentinel-2)
  - NASA Earthdata (MODIS, Landsat)

For production use, register for API credentials at:
  https://scihub.copernicus.eu/
  https://earthdata.nasa.gov/
"""

import os
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
# Set these via environment variables for security
COPERNICUS_USER = os.environ.get("COPERNICUS_USER", "")
COPERNICUS_PASS = os.environ.get("COPERNICUS_PASS", "")
NASA_EARTHDATA_TOKEN = os.environ.get("NASA_EARTHDATA_TOKEN", "")

SENTINEL_SEARCH_URL = "https://scihub.copernicus.eu/dhus/search"
SENTINEL_OData_URL = "https://scihub.copernicus.eu/dhus/odata/v1"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "satellite_images")


def search_sentinel2(bbox, start_date=None, end_date=None, max_cloud=30, rows=5):
    """
    Query Copernicus Open Access Hub for Sentinel-2 products.

    Parameters
    ----------
    bbox : tuple
        (lon_min, lat_min, lon_max, lat_max) bounding box.
    start_date : str, optional
        ISO date string (YYYY-MM-DD). Defaults to 7 days ago.
    end_date : str, optional
        ISO date string (YYYY-MM-DD). Defaults to today.
    max_cloud : int
        Max cloud cover percentage (0-100).
    rows : int
        Max results to return.

    Returns
    -------
    list[dict]
        List of product metadata dicts.
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
        f'platformname:Sentinel-2 AND '
        f'footprint:"Intersects({footprint})" AND '
        f'beginPosition:[{start_date}T00:00:00.000Z TO {end_date}T23:59:59.999Z] AND '
        f'cloudcoverpercentage:[0 TO {max_cloud}]'
    )

    params = {"q": query, "rows": rows, "format": "json"}

    resp = requests.get(
        SENTINEL_SEARCH_URL,
        params=params,
        auth=(COPERNICUS_USER, COPERNICUS_PASS),
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    entries = data.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]

    products = []
    for entry in entries:
        products.append(
            {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "link": entry.get("link", [{}])[0].get("href"),
                "summary": entry.get("summary"),
            }
        )

    logger.info("Found %d Sentinel-2 products.", len(products))
    return products


def download_product(product_id, output_path=None):
    """
    Download a Sentinel product by its UUID.

    Parameters
    ----------
    product_id : str
        The UUID of the product on Copernicus Hub.
    output_path : str, optional
        File path to save the product. Defaults to OUTPUT_DIR/<product_id>.zip.

    Returns
    -------
    str
        Path to the downloaded file.
    """
    if not COPERNICUS_USER or not COPERNICUS_PASS:
        raise EnvironmentError(
            "Copernicus credentials not set. "
            "Export COPERNICUS_USER and COPERNICUS_PASS."
        )

    url = f"{SENTINEL_OData_URL}/Products('{product_id}')/$value"

    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"{product_id}.zip")

    logger.info("Downloading product %s → %s", product_id, output_path)

    with requests.get(
        url,
        auth=(COPERNICUS_USER, COPERNICUS_PASS),
        stream=True,
        timeout=300,
    ) as resp:
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

    logger.info("Download complete: %s", output_path)
    return output_path


def get_satellite_image(bbox=None, save_dir=None):
    """
    High-level convenience: search for the latest Sentinel-2 image
    over a bounding box, download it, and return the local path.

    Parameters
    ----------
    bbox : tuple, optional
        (lon_min, lat_min, lon_max, lat_max). Defaults to Kerala, India.
    save_dir : str, optional
        Directory for saving. Defaults to data/satellite_images/.

    Returns
    -------
    str or None
        Path to downloaded file, or None if nothing found / creds missing.
    """
    if bbox is None:
        # Default: Kerala, India (flood-prone region)
        bbox = (75.0, 8.0, 77.5, 12.5)

    products = search_sentinel2(bbox, max_cloud=20, rows=1)
    if not products:
        logger.warning("No satellite products found for bbox %s", bbox)
        return None

    out_dir = save_dir or OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{products[0]['id']}.zip")

    return download_product(products[0]["id"], output_path=out_path)
