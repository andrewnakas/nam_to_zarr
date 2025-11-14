#!/usr/bin/env python3
"""Test script to verify expanded variable extraction from NAM GRIB2 files."""

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nam_to_zarr.noaa.nam_conus.forecast import NAMCONUSTemplateConfig
from nam_to_zarr.noaa.nam_conus.forecast.region_job import NAMCONUSRegionJob


def main():
    """Test extracting expanded variables."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Testing expanded variable extraction from NAM GRIB2 files")

    # Use a recent reference time (latest 00 UTC cycle)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Round down to latest 6-hour cycle (00, 06, 12, 18)
    hour = (now.hour // 6) * 6
    reference_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)

    # Go back one cycle to ensure data is available
    reference_time = reference_time - timedelta(hours=6)

    logger.info(f"Reference time: {reference_time}")

    # Create config with limited forecast hours for testing
    config = NAMCONUSTemplateConfig()
    config.forecast_hours = [0, 3]  # Just test first two hours for speed

    logger.info(f"Testing with {len(config.variables)} surface variables")
    logger.info(f"Testing with {len(config.pressure_level_variables)} pressure level variables")
    logger.info(f"Testing with {len(config.pressure_levels)} pressure levels: {config.pressure_levels}")

    # Create region job
    output_path = Path("data/test_expanded_variables.zarr")
    job = NAMCONUSRegionJob(config, reference_time, output_path)

    # Run the job
    success = job.run()

    if success:
        logger.info(f"✓ Successfully created Zarr dataset at {output_path}")

        # Try to read and display info about the dataset
        try:
            import xarray as xr
            ds = xr.open_zarr(output_path)
            logger.info(f"\nDataset info:")
            logger.info(f"  Dimensions: {dict(ds.dims)}")
            logger.info(f"  Coordinates: {list(ds.coords)}")
            logger.info(f"  Variables: {list(ds.data_vars)}")

            # Show which variables have pressure levels
            pressure_vars = [v for v in ds.data_vars if "isobaricInhPa" in ds[v].dims]
            surface_vars = [v for v in ds.data_vars if "isobaricInhPa" not in ds[v].dims]

            logger.info(f"\n  Surface variables ({len(surface_vars)}): {surface_vars}")
            logger.info(f"  Pressure level variables ({len(pressure_vars)}): {pressure_vars}")

            if pressure_vars:
                logger.info(f"\n  Pressure levels: {ds.isobaricInhPa.values}")

            ds.close()
        except Exception as e:
            logger.error(f"Could not read created dataset: {e}")

        return 0
    else:
        logger.error("✗ Failed to create Zarr dataset")
        return 1


if __name__ == "__main__":
    sys.exit(main())
