"""Template configuration for NAM CONUS forecast data.

Defines the grid structure, coordinates, variables, and metadata for NAM CONUS
forecast data reformatting to Zarr format.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class NAMCONUSTemplateConfig:
    """Configuration template for NAM CONUS forecast dataset.

    NAM CONUS uses a Lambert Conformal Conic projection with:
    - Grid: ~2145 x 1377 points (may vary slightly by data version)
    - Resolution: 12 km
    - Updates: 4 times daily (00, 06, 12, 18 UTC)
    - Forecast length: Up to 84 hours
    """

    # Grid dimensions (approximate - will be determined from actual data)
    grid_shape: tuple[int, int] = (1377, 2145)  # (y, x)

    # Projection information
    projection: str = "Lambert_Conformal"

    # Update interval in hours
    update_interval: int = 6

    # Forecast hours to retrieve (0 to 84 in 3-hour steps for efficiency)
    forecast_hours: list[int] = None

    # Variables to extract from GRIB2 files
    variables: dict[str, dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.forecast_hours is None:
            # Get forecast hours: 0-60 every 3 hours, then 60-84 every 3 hours
            # For rolling basis, we'll focus on first 12-24 hours
            self.forecast_hours = list(range(0, 25, 3))  # 0, 3, 6, 9, 12, 15, 18, 21, 24

        if self.variables is None:
            # Use cfgrib shortName as grib_name (this is what xarray will use as variable names)
            self.variables = {
                "t2m": {
                    "grib_name": "t2m",  # cfgrib shortName
                    "level": "2 m above ground",
                    "long_name": "2 metre temperature",
                    "units": "K",
                    "standard_name": "air_temperature",
                },
                "d2m": {
                    "grib_name": "d2m",  # cfgrib shortName
                    "level": "2 m above ground",
                    "long_name": "2 metre dewpoint temperature",
                    "units": "K",
                    "standard_name": "dew_point_temperature",
                },
                "u10": {
                    "grib_name": "u10",  # cfgrib shortName
                    "level": "10 m above ground",
                    "long_name": "10 metre U wind component",
                    "units": "m s**-1",
                    "standard_name": "eastward_wind",
                },
                "v10": {
                    "grib_name": "v10",  # cfgrib shortName
                    "level": "10 m above ground",
                    "long_name": "10 metre V wind component",
                    "units": "m s**-1",
                    "standard_name": "northward_wind",
                },
                "prmsl": {
                    "grib_name": "prmsl",  # cfgrib shortName
                    "level": "mean sea level",
                    "long_name": "Mean sea level pressure",
                    "units": "Pa",
                    "standard_name": "air_pressure_at_mean_sea_level",
                },
            }

    def get_dataset_attrs(self, reference_time: str) -> dict[str, Any]:
        """Get global attributes for the Zarr dataset.

        Args:
            reference_time: ISO format reference time for this forecast

        Returns:
            Dictionary of global attributes
        """
        return {
            "title": "NAM CONUS Forecast",
            "institution": "NOAA/NCEP",
            "source": "NAM CONUS 12km",
            "references": "https://www.emc.ncep.noaa.gov/index.php?branch=NAM",
            "comment": "NAM CONUS forecast data reformatted to Zarr",
            "Conventions": "CF-1.8",
            "reference_time": reference_time,
            "projection": self.projection,
            "grid_resolution": "12 km",
            "update_frequency": f"{self.update_interval} hours",
        }

    def get_coord_attrs(self, coord_name: str) -> dict[str, Any]:
        """Get attributes for a coordinate variable.

        Args:
            coord_name: Name of the coordinate

        Returns:
            Dictionary of coordinate attributes
        """
        coord_attrs = {
            "time": {
                "long_name": "reference time of forecast",
                "standard_name": "forecast_reference_time",
            },
            "step": {
                "long_name": "forecast period",
                "standard_name": "forecast_period",
                "units": "hours",
            },
            "y": {
                "long_name": "y-coordinate in Lambert Conformal projection",
                "standard_name": "projection_y_coordinate",
                "units": "m",
            },
            "x": {
                "long_name": "x-coordinate in Lambert Conformal projection",
                "standard_name": "projection_x_coordinate",
                "units": "m",
            },
            "latitude": {
                "long_name": "latitude",
                "standard_name": "latitude",
                "units": "degrees_north",
            },
            "longitude": {
                "long_name": "longitude",
                "standard_name": "longitude",
                "units": "degrees_east",
            },
        }
        return coord_attrs.get(coord_name, {})
