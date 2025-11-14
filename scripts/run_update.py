#!/usr/bin/env python3
"""Manual script to run NAM CONUS data update."""

import logging
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nam_to_zarr.noaa.nam_conus.forecast import NAMCONUSForecastDataset


def main():
    """Run the data update."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting manual NAM CONUS data update")

    # Create dataset manager
    dataset = NAMCONUSForecastDataset(
        data_dir="data",
        keep_last_n=4,
    )

    # Run update
    success = dataset.update()

    if success:
        logger.info("Update completed successfully")
        return 0
    else:
        logger.error("Update failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
