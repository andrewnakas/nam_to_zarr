"""Region job for processing NAM CONUS forecast data.

Downloads GRIB2 files from NOAA AWS S3, extracts variables, and writes to Zarr.
"""

import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import requests
import xarray as xr

from .template_config import NAMCONUSTemplateConfig

logger = logging.getLogger(__name__)


class NAMCONUSRegionJob:
    """Handles downloading and processing NAM CONUS forecast data to Zarr format."""

    def __init__(
        self,
        config: NAMCONUSTemplateConfig,
        reference_time: datetime,
        output_path: Path,
    ):
        """Initialize the region job.

        Args:
            config: Template configuration for NAM CONUS
            reference_time: Reference time for this forecast run
            output_path: Path to output Zarr store
        """
        self.config = config
        self.reference_time = reference_time
        self.output_path = output_path
        self.base_url = "https://noaa-nam-pds.s3.amazonaws.com"

    def get_grib_url(self, forecast_hour: int) -> str:
        """Construct URL for NAM CONUS GRIB2 file.

        Args:
            forecast_hour: Forecast hour to retrieve

        Returns:
            URL string for the GRIB2 file
        """
        # NAM 12km CONUS URL format: nam.YYYYMMDD/nam.tCCz.awphys{FH}.tm00.grib2
        # where CC is cycle (00, 06, 12, 18) and FH is forecast hour (00, 01, 02, etc.)
        # NAM 12km goes from 00-84 hours
        date_str = self.reference_time.strftime("%Y%m%d")
        cycle_str = self.reference_time.strftime("%H")
        fh_str = f"{forecast_hour:02d}"

        url = (
            f"{self.base_url}/nam.{date_str}/"
            f"nam.t{cycle_str}z.awphys{fh_str}.tm00.grib2"
        )
        return url

    def download_and_read_grib(self, forecast_hour: int) -> xr.Dataset | None:
        """Download and read a GRIB2 file.

        Args:
            forecast_hour: Forecast hour to retrieve

        Returns:
            xarray Dataset with the GRIB2 data, or None if download fails
        """
        url = self.get_grib_url(forecast_hour)
        logger.info(f"Downloading GRIB2 file: {url}")

        # Download to temporary file
        temp_file = None
        try:
            # Try to download the file
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".grib2", delete=False) as f:
                f.write(response.content)
                temp_file = f.name

            logger.info(f"Downloaded to {temp_file}, reading with cfgrib...")

            # Read with cfgrib
            ds = xr.open_dataset(
                temp_file,
                engine="cfgrib",
                backend_kwargs={
                    "indexpath": "",  # Disable index file creation
                },
            )
            return ds

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"File not found (404): {url}")
                logger.info("This might indicate:")
                logger.info("  1. The forecast cycle is not yet available")
                logger.info("  2. The URL structure has changed")
                logger.info("  3. The file naming convention is different")
            else:
                logger.error(f"HTTP error downloading {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read GRIB2 file {url}: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_file and Path(temp_file).exists():
                try:
                    Path(temp_file).unlink()
                except Exception:
                    pass

    def extract_variable(
        self, ds: xr.Dataset, var_name: str, var_config: dict[str, Any]
    ) -> xr.DataArray | None:
        """Extract a variable from the GRIB2 dataset.

        Args:
            ds: xarray Dataset from GRIB2 file
            var_name: Variable name in our configuration
            var_config: Variable configuration dictionary

        Returns:
            xarray DataArray with the extracted variable, or None if not found
        """
        grib_name = var_config["grib_name"]

        try:
            # Try to find the variable by GRIB short name
            # cfgrib typically uses GRIB parameter names
            if grib_name in ds:
                da = ds[grib_name]
            else:
                # Try common alternative names
                possible_names = [grib_name.lower(), grib_name.upper()]
                for name in possible_names:
                    if name in ds:
                        da = ds[name]
                        break
                else:
                    logger.warning(f"Variable {grib_name} not found in dataset")
                    return None

            # Add metadata
            da.attrs.update({
                "long_name": var_config["long_name"],
                "units": var_config["units"],
                "standard_name": var_config["standard_name"],
            })

            return da

        except Exception as e:
            logger.error(f"Failed to extract variable {var_name}: {e}")
            return None

    def process_forecast_hour(self, forecast_hour: int) -> xr.Dataset | None:
        """Process a single forecast hour.

        Args:
            forecast_hour: Forecast hour to process

        Returns:
            xarray Dataset with extracted variables for this forecast hour
        """
        logger.info(f"Processing forecast hour {forecast_hour}")

        # Download and read GRIB2 file
        ds_grib = self.download_and_read_grib(forecast_hour)
        if ds_grib is None:
            return None

        # Extract configured variables
        data_vars = {}
        for var_name, var_config in self.config.variables.items():
            da = self.extract_variable(ds_grib, var_name, var_config)
            if da is not None:
                data_vars[var_name] = da

        if not data_vars:
            logger.warning(f"No variables extracted for forecast hour {forecast_hour}")
            return None

        # Create dataset with extracted variables
        ds = xr.Dataset(data_vars)

        # Add forecast hour as coordinate
        ds = ds.expand_dims({"step": [forecast_hour]})

        # Close the GRIB dataset
        ds_grib.close()

        return ds

    def run(self) -> bool:
        """Run the region job to process all forecast hours.

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            f"Starting NAM CONUS region job for {self.reference_time.isoformat()}"
        )

        datasets = []

        # Process each forecast hour
        for forecast_hour in self.config.forecast_hours:
            ds = self.process_forecast_hour(forecast_hour)
            if ds is not None:
                datasets.append(ds)

        if not datasets:
            logger.error("No forecast hours processed successfully")
            return False

        # Concatenate all forecast hours
        logger.info("Combining forecast hours...")
        ds_combined = xr.concat(datasets, dim="step")

        # Add reference time
        ds_combined = ds_combined.expand_dims(
            {"time": [np.datetime64(self.reference_time, "ns")]}
        )

        # Add global attributes
        ds_combined.attrs.update(
            self.config.get_dataset_attrs(self.reference_time.isoformat())
        )

        # Write to Zarr
        logger.info(f"Writing to Zarr: {self.output_path}")
        try:
            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to Zarr with compression
            encoding = {}
            for var in ds_combined.data_vars:
                encoding[var] = {
                    "compressor": {
                        "id": "blosc",
                        "cname": "lz4",
                        "clevel": 5,
                        "shuffle": 1,
                    }
                }

            ds_combined.to_zarr(
                self.output_path,
                mode="w",
                encoding=encoding,
                consolidated=True,
            )

            logger.info("Successfully wrote Zarr dataset")
            return True

        except Exception as e:
            logger.error(f"Failed to write Zarr dataset: {e}")
            return False

        finally:
            ds_combined.close()
