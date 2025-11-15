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

    # Pressure levels to extract (in hPa/mb)
    pressure_levels: list[int] = None

    # Variables to extract from GRIB2 files
    variables: dict[str, dict[str, Any]] = None

    # Pressure level variables
    pressure_level_variables: dict[str, dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.forecast_hours is None:
            # NAM CONUS provides full 84-hour (3.5 day) forecast:
            # - Hourly forecasts for first 36 hours (0-36)
            # - 3-hourly forecasts from 39-84 hours
            hourly_hours = list(range(0, 37))  # 0, 1, 2, ..., 35, 36
            three_hourly_hours = list(range(39, 85, 3))  # 39, 42, 45, ..., 81, 84
            self.forecast_hours = hourly_hours + three_hourly_hours

        if self.pressure_levels is None:
            # Standard pressure levels for atmospheric analysis
            # 1000mb (surface), 925mb (boundary layer), 850mb (low level)
            # 700mb (mid-level), 500mb (mid-troposphere), 250mb (jet stream level)
            self.pressure_levels = [1000, 925, 850, 700, 500, 250]

        if self.variables is None:
            # Surface and near-surface variables
            # Use cfgrib shortName as grib_name (this is what xarray will use as variable names)
            self.variables = {
                # === Temperature and Moisture ===
                "t2m": {
                    "grib_name": "t2m",
                    "level": "2 m above ground",
                    "long_name": "2 metre temperature",
                    "units": "K",
                    "standard_name": "air_temperature",
                },
                "d2m": {
                    "grib_name": "d2m",
                    "level": "2 m above ground",
                    "long_name": "2 metre dewpoint temperature",
                    "units": "K",
                    "standard_name": "dew_point_temperature",
                },
                "r2": {
                    "grib_name": "r2",
                    "level": "2 m above ground",
                    "long_name": "2 metre relative humidity",
                    "units": "%",
                    "standard_name": "relative_humidity",
                },

                # === Winds ===
                "u10": {
                    "grib_name": "u10",
                    "level": "10 m above ground",
                    "long_name": "10 metre U wind component",
                    "units": "m s**-1",
                    "standard_name": "eastward_wind",
                },
                "v10": {
                    "grib_name": "v10",
                    "level": "10 m above ground",
                    "long_name": "10 metre V wind component",
                    "units": "m s**-1",
                    "standard_name": "northward_wind",
                },

                # === Pressure ===
                "sp": {
                    "grib_name": "sp",
                    "level": "surface",
                    "long_name": "Surface pressure",
                    "units": "Pa",
                    "standard_name": "surface_air_pressure",
                },
                "prmsl": {
                    "grib_name": "prmsl",
                    "level": "mean sea level",
                    "long_name": "Mean sea level pressure",
                    "units": "Pa",
                    "standard_name": "air_pressure_at_mean_sea_level",
                },

                # === Precipitation ===
                "tp": {
                    "grib_name": "tp",
                    "level": "surface",
                    "long_name": "Total precipitation",
                    "units": "kg m**-2",
                    "standard_name": "precipitation_amount",
                },

                # === Clouds ===
                "tcc": {
                    "grib_name": "tcc",
                    "level": "atmosphere single layer",
                    "long_name": "Total cloud cover",
                    "units": "%",
                    "standard_name": "cloud_area_fraction",
                },

                # === Radiation ===
                "dswrf": {
                    "grib_name": "sdswrf",
                    "level": "surface",
                    "long_name": "Downward shortwave radiation flux",
                    "units": "W m**-2",
                    "standard_name": "surface_downwelling_shortwave_flux",
                },
                "dlwrf": {
                    "grib_name": "sdlwrf",
                    "level": "surface",
                    "long_name": "Downward longwave radiation flux",
                    "units": "W m**-2",
                    "standard_name": "surface_downwelling_longwave_flux",
                },

                # === Convection/Instability ===
                "cape": {
                    "grib_name": "cape",
                    "level": "surface",
                    "long_name": "Convective available potential energy",
                    "units": "J kg**-1",
                    "standard_name": "atmosphere_convective_available_potential_energy",
                },
                "cin": {
                    "grib_name": "cin",
                    "level": "surface",
                    "long_name": "Convective inhibition",
                    "units": "J kg**-1",
                    "standard_name": "atmosphere_convective_inhibition",
                },
            }

        if self.pressure_level_variables is None:
            # Variables on pressure/isobaric levels
            self.pressure_level_variables = {
                # === Temperature ===
                "t": {
                    "grib_name": "t",
                    "long_name": "Temperature",
                    "units": "K",
                    "standard_name": "air_temperature",
                },

                # === Geopotential Height ===
                "gh": {
                    "grib_name": "gh",
                    "long_name": "Geopotential height",
                    "units": "m",
                    "standard_name": "geopotential_height",
                },

                # === Humidity ===
                "r": {
                    "grib_name": "r",
                    "long_name": "Relative humidity",
                    "units": "%",
                    "standard_name": "relative_humidity",
                },

                # === Winds ===
                "u": {
                    "grib_name": "u",
                    "long_name": "U component of wind",
                    "units": "m s**-1",
                    "standard_name": "eastward_wind",
                },
                "v": {
                    "grib_name": "v",
                    "long_name": "V component of wind",
                    "units": "m s**-1",
                    "standard_name": "northward_wind",
                },

                # === Vertical Motion ===
                "w": {
                    "grib_name": "w",
                    "long_name": "Vertical velocity",
                    "units": "Pa s**-1",
                    "standard_name": "lagrangian_tendency_of_air_pressure",
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
            "isobaricInhPa": {
                "long_name": "pressure",
                "standard_name": "air_pressure",
                "units": "hPa",
                "positive": "down",
                "axis": "Z",
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
