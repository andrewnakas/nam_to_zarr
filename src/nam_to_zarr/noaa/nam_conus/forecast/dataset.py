"""Dataset orchestration for NAM CONUS forecast data.

Manages the end-to-end workflow for downloading, processing, and storing
NAM CONUS forecast data in Zarr format on a rolling basis.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .region_job import NAMCONUSRegionJob
from .template_config import NAMCONUSTemplateConfig

logger = logging.getLogger(__name__)


class NAMCONUSForecastDataset:
    """Orchestrates NAM CONUS forecast data processing workflow."""

    def __init__(
        self,
        data_dir: Path | str = "data",
        keep_last_n: int = 4,
    ):
        """Initialize the dataset manager.

        Args:
            data_dir: Directory to store Zarr datasets
            keep_last_n: Number of recent forecasts to keep (rolling basis)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.keep_last_n = keep_last_n
        self.config = NAMCONUSTemplateConfig()

    def get_latest_reference_time(self) -> datetime:
        """Get the latest NAM CONUS reference time.

        NAM CONUS runs at 00, 06, 12, 18 UTC. This returns the most recent
        run time based on current UTC time.

        Returns:
            datetime object for the latest reference time
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)  # Convert to naive UTC

        # NAM runs at 00, 06, 12, 18 UTC
        # Data is typically available ~3 hours after reference time
        # So we look for the run from 3-4 hours ago
        hours_ago = 4
        target_time = now - timedelta(hours=hours_ago)

        # Round down to nearest 6-hour interval
        cycle_hour = (target_time.hour // 6) * 6

        reference_time = target_time.replace(
            hour=cycle_hour, minute=0, second=0, microsecond=0
        )

        return reference_time

    def get_output_path(self, reference_time: datetime) -> Path:
        """Get output path for a given reference time.

        Args:
            reference_time: Reference time for the forecast

        Returns:
            Path to the Zarr store
        """
        # Format: nam_conus_YYYYMMDD_HH.zarr
        filename = reference_time.strftime("nam_conus_%Y%m%d_%H.zarr")
        return self.data_dir / filename

    def cleanup_old_datasets(self):
        """Remove old Zarr datasets, keeping only the most recent ones."""
        # Find all NAM CONUS zarr stores
        zarr_stores = sorted(
            self.data_dir.glob("nam_conus_*.zarr"),
            key=lambda p: p.name,
            reverse=True,
        )

        # Remove old ones beyond keep_last_n
        for store in zarr_stores[self.keep_last_n :]:
            logger.info(f"Removing old dataset: {store}")
            try:
                # Remove zarr store directory
                import shutil

                shutil.rmtree(store)
            except Exception as e:
                logger.error(f"Failed to remove {store}: {e}")

    def process_latest(self) -> bool:
        """Process the latest available NAM CONUS forecast.

        Returns:
            True if successful, False otherwise
        """
        reference_time = self.get_latest_reference_time()
        output_path = self.get_output_path(reference_time)

        # Check if this dataset already exists
        if output_path.exists():
            logger.info(f"Dataset already exists: {output_path}")
            return True

        logger.info(f"Processing NAM CONUS forecast for {reference_time.isoformat()}")

        # Create and run region job
        job = NAMCONUSRegionJob(
            config=self.config,
            reference_time=reference_time,
            output_path=output_path,
        )

        success = job.run()

        if success:
            logger.info("Processing completed successfully")
            # Clean up old datasets
            self.cleanup_old_datasets()
        else:
            logger.error("Processing failed")

        return success

    def update(self) -> bool:
        """Update with the latest forecast data.

        This is the main entry point for the automated workflow.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting NAM CONUS dataset update")
        return self.process_latest()


def main():
    """Main entry point for running the dataset update."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run dataset manager
    dataset = NAMCONUSForecastDataset(
        data_dir="data",
        keep_last_n=4,  # Keep last 24 hours of data (4 runs at 6-hour intervals)
    )

    success = dataset.update()

    if not success:
        logger.error("Dataset update failed")
        exit(1)

    logger.info("Dataset update completed successfully")


if __name__ == "__main__":
    main()
