#!/usr/bin/env python3
"""Generate a data catalog from available Zarr stores."""

import json
import logging
from datetime import datetime
from pathlib import Path

import xarray as xr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_catalog(data_dir: Path = Path("data"), catalog_dir: Path = Path("catalog")):
    """Generate catalog of available datasets.

    Args:
        data_dir: Directory containing Zarr stores
        catalog_dir: Directory to write catalog files
    """
    catalog_dir.mkdir(parents=True, exist_ok=True)

    # Find all zarr stores
    zarr_stores = sorted(data_dir.glob("nam_conus_*.zarr"))

    if not zarr_stores:
        logger.warning("No Zarr stores found")
        return

    catalog_entries = []

    for store_path in zarr_stores:
        logger.info(f"Processing {store_path.name}")

        try:
            # Open zarr store
            ds = xr.open_zarr(store_path, consolidated=True)

            # Extract metadata
            reference_time = ds.attrs.get("reference_time", "unknown")
            entry = {
                "name": store_path.name,
                "path": str(store_path),
                "reference_time": reference_time,
                "variables": list(ds.data_vars.keys()),
                "dimensions": dict(ds.dims),
                "size_mb": sum(
                    f.stat().st_size for f in store_path.rglob("*") if f.is_file()
                )
                / (1024 * 1024),
            }

            catalog_entries.append(entry)

            ds.close()

        except Exception as e:
            logger.error(f"Failed to process {store_path.name}: {e}")

    # Write catalog
    catalog_file = catalog_dir / "catalog.json"
    with open(catalog_file, "w") as f:
        json.dump(
            {
                "generated": datetime.utcnow().isoformat(),
                "datasets": catalog_entries,
            },
            f,
            indent=2,
        )

    logger.info(f"Catalog written to {catalog_file}")
    logger.info(f"Total datasets: {len(catalog_entries)}")


if __name__ == "__main__":
    generate_catalog()
