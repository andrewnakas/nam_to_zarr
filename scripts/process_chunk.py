#!/usr/bin/env python3
"""Process a chunk of NAM CONUS forecast hours.

This script processes a subset of forecast hours to enable parallel/chunked processing
that stays within time and memory constraints.
"""

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nam_to_zarr.noaa.nam_conus.forecast.region_job import NAMCONUSRegionJob
from nam_to_zarr.noaa.nam_conus.forecast.template_config import NAMCONUSTemplateConfig


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
    """Process a chunk of forecast hours."""
    if len(sys.argv) < 4:
        print("Usage: process_chunk.py <start_hour> <end_hour> <chunk_id>")
        print("Example: process_chunk.py 0 20 1")
        sys.exit(1)

    start_hour = int(sys.argv[1])
    end_hour = int(sys.argv[2])
    chunk_id = sys.argv[3]

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Processing chunk {chunk_id}: hours {start_hour}-{end_hour}")

    # Get reference time
    reference_time = get_latest_reference_time()
    logger.info(f"Reference time: {reference_time.isoformat()}")

    # Create config with only the specified forecast hours
    config = NAMCONUSTemplateConfig()
    config.forecast_hours = list(range(start_hour, end_hour + 1))

    logger.info(f"Forecast hours: {len(config.forecast_hours)} hours")

    # Output path for this chunk
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    filename = reference_time.strftime(f"nam_conus_%Y%m%d_%H_chunk{chunk_id}.zarr")
    output_path = data_dir / filename

    # Check if chunk already exists
    if output_path.exists():
        logger.info(f"Chunk already exists: {output_path}")
        return

    # Create and run region job for this chunk
    job = NAMCONUSRegionJob(
        config=config,
        reference_time=reference_time,
        output_path=output_path,
    )

    success = job.run()

    if success:
        logger.info(f"Chunk {chunk_id} completed successfully: {output_path}")
    else:
        logger.error(f"Chunk {chunk_id} failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
