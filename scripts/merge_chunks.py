#!/usr/bin/env python3
"""Merge chunked NAM CONUS forecast Zarr stores into a single dataset.

This script combines multiple chunk files (created by process_chunk.py) into
a single consolidated Zarr store.
"""

import logging
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import xarray as xr


def get_latest_reference_time() -> datetime:
    """Get the latest NAM CONUS reference time."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    hours_ago = 4
    target_time = now - timedelta(hours=hours_ago)
    cycle_hour = (target_time.hour // 6) * 6
    reference_time = target_time.replace(
        hour=cycle_hour, minute=0, second=0, microsecond=0
    )
    return reference_time


def main():
    """Merge chunk files into final dataset."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Get reference time
    reference_time = get_latest_reference_time()
    logger.info(f"Merging chunks for reference time: {reference_time.isoformat()}")

    data_dir = Path("data")

    # Find all chunk files for this reference time
    date_pattern = reference_time.strftime("nam_conus_%Y%m%d_%H_chunk*.zarr")
    chunk_files = sorted(data_dir.glob(date_pattern))

    if not chunk_files:
        logger.error(f"No chunk files found matching: {date_pattern}")
        sys.exit(1)

    logger.info(f"Found {len(chunk_files)} chunk files:")
    for chunk_file in chunk_files:
        logger.info(f"  - {chunk_file.name}")

    # Load all chunks
    logger.info("Loading chunk datasets...")
    chunks = []
    for chunk_file in chunk_files:
        logger.info(f"Loading {chunk_file.name}...")
        ds = xr.open_zarr(chunk_file)
        chunks.append(ds)
        logger.info(f"  Loaded: {len(ds.step)} forecast hours")

    # Concatenate along the step (forecast hour) dimension
    logger.info("Concatenating chunks along step dimension...")
    ds_combined = xr.concat(chunks, dim="step")

    # Sort by step to ensure correct order
    ds_combined = ds_combined.sortby("step")

    logger.info(f"Combined dataset: {len(ds_combined.step)} total forecast hours")
    logger.info(f"  Dimensions: {dict(ds_combined.sizes)}")
    logger.info(f"  Variables: {list(ds_combined.data_vars.keys())}")

    # Write to final output
    final_filename = reference_time.strftime("nam_conus_%Y%m%d_%H.zarr")
    final_output = data_dir / final_filename

    # Remove if exists
    if final_output.exists():
        logger.info(f"Removing existing output: {final_output}")
        shutil.rmtree(final_output)

    logger.info(f"Writing merged dataset to: {final_output}")
    ds_combined.to_zarr(final_output, mode="w", consolidated=True)

    logger.info("Merge completed successfully")

    # Close datasets
    for ds in chunks:
        ds.close()
    ds_combined.close()

    # Clean up chunk files
    logger.info("Cleaning up chunk files...")
    for chunk_file in chunk_files:
        logger.info(f"Removing {chunk_file.name}")
        shutil.rmtree(chunk_file)

    logger.info("Cleanup completed")


if __name__ == "__main__":
    main()
