"""Projection utilities for NAM CONUS data.

Handles Lambert Conformal Conic projection coordinate computation.
"""

import logging
from typing import Any

import numpy as np
import xarray as xr

try:
    from pyproj import Proj
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_projection_from_grib(ds: xr.Dataset, grib_file: str) -> dict[str, Any] | None:
    """Extract Lambert Conformal Conic projection parameters from GRIB file.

    Args:
        ds: xarray Dataset loaded from GRIB file (used for validation)
        grib_file: Path to GRIB2 file

    Returns:
        Dictionary of projection parameters, or None if extraction fails
    """
    try:
        import eccodes as ecc
    except ImportError:
        logger.warning("eccodes not available, cannot extract projection metadata")
        return None

    try:
        with open(grib_file, 'rb') as f:
            gid = ecc.codes_grib_new_from_file(f)

            if gid is None:
                logger.warning("No GRIB message found in file")
                return None

            # Extract projection parameters
            grid_type = ecc.codes_get(gid, 'gridType')

            if grid_type != 'lambert':
                logger.warning(f"Unexpected grid type: {grid_type}")
                ecc.codes_release(gid)
                return None

            # Get projection parameters
            proj_params = {
                'grid_type': grid_type,
                'nx': ecc.codes_get(gid, 'Nx'),
                'ny': ecc.codes_get(gid, 'Ny'),
                # LaD: Latitude where Dx and Dy are specified (microdegrees)
                'lad': ecc.codes_get(gid, 'LaD') / 1e6,
                # LoV: Orientation of the grid (central meridian, microdegrees)
                'lov': ecc.codes_get(gid, 'LoV') / 1e6,
                # Standard parallels (microdegrees)
                'latin1': ecc.codes_get(gid, 'Latin1') / 1e6,
                'latin2': ecc.codes_get(gid, 'Latin2') / 1e6,
                # First grid point
                'lat_first': ecc.codes_get(gid, 'latitudeOfFirstGridPointInDegrees'),
                'lon_first': ecc.codes_get(gid, 'longitudeOfFirstGridPointInDegrees'),
                # Grid spacing in meters
                'dx': ecc.codes_get(gid, 'DxInMetres'),
                'dy': ecc.codes_get(gid, 'DyInMetres'),
                # Scan direction
                'i_scans_negatively': ecc.codes_get(gid, 'iScansNegatively'),
                'j_scans_positively': ecc.codes_get(gid, 'jScansPositively'),
            }

            ecc.codes_release(gid)

            logger.info(f"Extracted projection: {grid_type} {proj_params['nx']}x{proj_params['ny']}, "
                       f"resolution {proj_params['dx']:.0f}m")

            return proj_params

    except Exception as e:
        logger.error(f"Failed to extract projection from GRIB: {e}")
        return None


def compute_projection_coordinates(
    lat: np.ndarray,
    lon: np.ndarray,
    proj_params: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray]:
    """Compute x/y projection coordinates from lat/lon using projection parameters.

    Args:
        lat: Latitude array (2D)
        lon: Longitude array (2D)
        proj_params: Projection parameters from extract_projection_from_grib

    Returns:
        Tuple of (x, y) coordinate arrays in meters (1D)

    Raises:
        ImportError: If pyproj is not available
        ValueError: If coordinate computation fails
    """
    if not PYPROJ_AVAILABLE:
        raise ImportError("pyproj is required for projection coordinate computation")

    # Create Lambert Conformal Conic projection
    # Convert longitude from 0-360 to -180-180
    lon_center = proj_params['lov']
    if lon_center > 180:
        lon_center = lon_center - 360

    # Create pyproj projection
    proj = Proj(
        proj='lcc',
        lat_0=proj_params['lad'],  # Latitude of projection origin
        lon_0=lon_center,  # Longitude of projection origin
        lat_1=proj_params['latin1'],  # First standard parallel
        lat_2=proj_params['latin2'],  # Second standard parallel
        x_0=0,  # False easting
        y_0=0,  # False northing
        datum='WGS84',
        units='m'
    )

    # Convert longitude from 0-360 to -180-180 for projection
    lon_proj = np.where(lon > 180, lon - 360, lon)

    # Project the first grid point to get the origin offset
    x_all, y_all = proj(lon_proj, lat)

    # Extract the coordinate vectors
    # For a regular grid, we can extract 1D coordinates from the 2D arrays
    # Use the first row for x and first column for y

    # Get coordinates along first row (y=0) for x values
    x_coords_2d = x_all[0, :]  # First row gives x variation
    # Get coordinates along first column (x=0) for y values
    y_coords_2d = y_all[:, 0]  # First column gives y variation

    logger.info(f"Computed projection coordinates: "
               f"x [{x_coords_2d.min():.0f}, {x_coords_2d.max():.0f}] m, "
               f"y [{y_coords_2d.min():.0f}, {y_coords_2d.max():.0f}] m")

    return x_coords_2d, y_coords_2d


def add_projection_coordinates(
    ds: xr.Dataset,
    proj_params: dict[str, Any]
) -> xr.Dataset:
    """Add x/y projection coordinates to dataset.

    Args:
        ds: Dataset with latitude/longitude coordinates
        proj_params: Projection parameters from extract_projection_from_grib

    Returns:
        Dataset with x/y projection coordinates added
    """
    if 'latitude' not in ds.coords or 'longitude' not in ds.coords:
        logger.warning("Dataset missing latitude/longitude coordinates")
        return ds

    try:
        # Compute projection coordinates
        x_coords, y_coords = compute_projection_coordinates(
            ds.latitude.values,
            ds.longitude.values,
            proj_params
        )

        # Add as coordinates (1D)
        ds = ds.assign_coords({
            'x': ('x', x_coords),
            'y': ('y', y_coords),
        })

        # Add coordinate attributes
        ds['x'].attrs.update({
            'long_name': 'x-coordinate in Lambert Conformal projection',
            'standard_name': 'projection_x_coordinate',
            'units': 'm',
        })

        ds['y'].attrs.update({
            'long_name': 'y-coordinate in Lambert Conformal projection',
            'standard_name': 'projection_y_coordinate',
            'units': 'm',
        })

        # Add grid_mapping variable with projection information
        ds['lambert_conformal'] = xr.DataArray(
            np.int32(0),
            attrs={
                'grid_mapping_name': 'lambert_conformal_conic',
                'standard_parallel': [proj_params['latin1'], proj_params['latin2']],
                'longitude_of_central_meridian': proj_params['lov'] if proj_params['lov'] <= 180
                                                   else proj_params['lov'] - 360,
                'latitude_of_projection_origin': proj_params['lad'],
                'false_easting': 0.0,
                'false_northing': 0.0,
                'semi_major_axis': 6378137.0,  # WGS84
                'inverse_flattening': 298.257223563,  # WGS84
            }
        )

        # Add grid_mapping attribute to data variables
        for var in ds.data_vars:
            if 'y' in ds[var].dims and 'x' in ds[var].dims:
                ds[var].attrs['grid_mapping'] = 'lambert_conformal'

        logger.info("Added projection coordinates to dataset")

    except Exception as e:
        logger.error(f"Failed to add projection coordinates: {e}")

    return ds
