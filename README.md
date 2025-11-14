# NAM CONUS to Zarr

Automated reformatting of NOAA's NAM (North American Mesoscale) CONUS forecast data into cloud-optimized Zarr format, running on a 6-hour rolling basis.

## Overview

This project automatically downloads NAM CONUS forecast data from NOAA's AWS S3 bucket, converts it from GRIB2 format to Zarr format, and maintains a rolling archive of the most recent forecasts. The entire process runs via GitHub Actions without requiring dedicated infrastructure.

**This system downloads REAL forecast data from NOAA - not synthetic or simulated data.**

### Key Features

- **Automated Updates**: Runs every 6 hours with low latency (~3.5 hours after each NAM cycle)
- **Rolling Storage**: Maintains the last **48 hours** of forecast data (8 forecast cycles)
- **Full 72-Hour Forecasts**: Complete 3-day forecast (25 time steps at 3-hour intervals)
- **Pressure Level Data**: 6 standard atmospheric levels (1000, 925, 850, 700, 500, 250 mb)
- **Comprehensive Variables**: Temperature, moisture, winds, pressure, precipitation, clouds, radiation
- **Cloud-Optimized**: Data stored in Zarr format for efficient cloud access
- **Real NOAA Data**: Direct downloads from NOAA AWS public dataset

## Data Specifications

- **Source**: NOAA NAM CONUS 12km
- **Grid**: ~2145 × 1377 points at 12 km resolution
- **Projection**: Lambert Conformal Conic
- **Update Frequency**: Every 6 hours (00, 06, 12, 18 UTC)
- **Data Latency**: ~3.5 hours (data available by 03:30, 09:30, 15:30, 21:30 UTC)
- **Forecast Length**: **72 hours** (0-72 hour forecasts in 3-hour intervals)
- **Retention**: **48 hours** (8 most recent cycles)
- **Format**: Zarr v3 with automatic compression

## Variables

### Surface & Near-Surface Variables

Essential variables for weather forecasting (note: availability depends on NAM GRIB2 file contents):

| Variable | Description | Level | Units |
|----------|-------------|-------|-------|
| **Temperature & Moisture** | | | |
| `t2m` | 2-metre temperature | 2m above ground | K |
| `d2m` | 2-metre dewpoint temperature | 2m above ground | K |
| `r2` | 2-metre relative humidity | 2m above ground | % |
| **Winds** | | | |
| `u10` | 10-metre U wind component (eastward) | 10m above ground | m/s |
| `v10` | 10-metre V wind component (northward) | 10m above ground | m/s |
| **Pressure** | | | |
| `sp` | Surface pressure | surface | Pa |
| `prmsl` | Mean sea level pressure | mean sea level | Pa |
| **Precipitation** | | | |
| `tp` | Total precipitation | surface | kg/m² |
| `acpcp` | Accumulated precipitation | surface | kg/m² |
| **Cloud Cover** | | | |
| `tcc` / `tcdc` | Total cloud cover | entire atmosphere | % |
| `lcc` | Low cloud cover | low cloud layer | % |
| `mcc` | Medium cloud cover | middle cloud layer | % |
| `hcc` | High cloud cover | high cloud layer | % |
| **Radiation** | | | |
| `dswrf` | Downward shortwave radiation | surface | W/m² |
| `dlwrf` | Downward longwave radiation | surface | W/m² |
| **Convection** | | | |
| `cape` | Convective available potential energy | surface | J/kg |
| `cin` | Convective inhibition | surface | J/kg |

### Pressure Level Variables

Available at **6 standard pressure levels**: 1000, 925, 850, 700, 500, 250 mb

| Variable | Description | Units |
|----------|-------------|-------|
| `t` | Temperature | K |
| `gh` | Geopotential height | m |
| `r` | Relative humidity | % |
| `q` | Specific humidity | kg/kg |
| `u` | U wind component (eastward) | m/s |
| `v` | V wind component (northward) | m/s |
| `w` | Vertical velocity (omega) | Pa/s |

**Note**: The actual variables extracted depend on what's available in NAM GRIB2 files. The system logs warnings for variables that are configured but not found in the data.

## Installation

### Prerequisites

- Python 3.11 or later
- System dependencies: `libeccodes-dev`, `libgeos-dev`

### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .
```

### Using pip

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libeccodes-dev libgeos-dev

# Install Python package
pip install -e .
```

## Usage

### Automated Updates (GitHub Actions)

The repository is configured to automatically update every 6 hours via GitHub Actions. No manual intervention is required.

The workflow:
1. Downloads the latest NAM CONUS GRIB2 files from NOAA AWS S3
2. Extracts surface and pressure level variables using cfgrib
3. Converts to cloud-optimized Zarr format
4. Stores in the `data/` directory
5. Removes old forecasts (keeps last **8 cycles = 48 hours**)
6. Updates data catalog (catalog.json)
7. Commits and pushes changes

### Manual Update

To manually trigger an update:

```bash
python -m nam_to_zarr.noaa.nam_conus.forecast.dataset
```

Or use the GitHub Actions UI to manually trigger the workflow.

### Reading the Data

```python
import xarray as xr

# Open a Zarr store
ds = xr.open_zarr("data/nam_conus_20251114_00.zarr", consolidated=True)

# Inspect the dataset
print(ds)
print("Variables:", list(ds.data_vars))
print("Dimensions:", dict(ds.dims))

# Access surface variables
temperature_2m = ds['t2m']  # Shape: (1, 25, ~1377, ~2145)
humidity_2m = ds['r2']

# Access a specific forecast hour (e.g., 24-hour forecast)
temp_24h = ds['t2m'].sel(step=24)

# Access pressure level data
temperature_500mb = ds['t'].sel(isobaricInhPa=500)  # Temperature at 500mb
wind_u_850mb = ds['u'].sel(isobaricInhPa=850)      # U wind at 850mb

# Get lat/lon coordinates
lats = ds['latitude'].values
lons = ds['longitude'].values

# Plot surface temperature at 24-hour forecast
import matplotlib.pyplot as plt
ds['t2m'].sel(step=24).squeeze().plot(x='longitude', y='latitude')
plt.title('NAM 24-Hour Temperature Forecast')
plt.show()

# Access multiple pressure levels
temps_multiple_levels = ds['t'].sel(isobaricInhPa=[1000, 850, 500])
```

## Architecture

The project follows a three-layer architecture:

### 1. TemplateConfig (`template_config.py`)
Defines dataset structure with:
- Grid dimensions and projection information
- Variable definitions and metadata
- Coordinate specifications

### 2. RegionJob (`region_job.py`)
Handles data processing:
- Downloads GRIB2 files from NOAA AWS S3
- Reads files with cfgrib/xarray
- Extracts and transforms variables
- Writes to Zarr with compression

### 3. Dataset (`dataset.py`)
Orchestrates the workflow:
- Determines latest available forecast
- Manages rolling storage
- Coordinates end-to-end processing

## Development

### Running Tests

```bash
pytest
```

### Code Quality

This project uses:
- `ruff` for linting and formatting
- `mypy` for type checking
- `pre-commit` for automated checks

```bash
# Install pre-commit hooks
pre-commit install

# Run checks manually
ruff check .
ruff format .
mypy src
```

## Data Access

The processed Zarr datasets are stored in the `data/` directory and are committed to the repository. For large-scale usage, consider:

1. **Direct Access**: Clone the repository and access Zarr stores locally
2. **GitHub Pages**: Set up GitHub Pages to serve the data catalog
3. **Cloud Storage**: Mirror data to S3/GCS for cloud-native access

## Configuration

### Adjusting Forecast Hours

Edit `src/nam_to_zarr/noaa/nam_conus/forecast/template_config.py`:

```python
self.forecast_hours = list(range(0, 85, 3))  # 0-84 hours every 3 hours
```

### Changing Rolling Window

Edit `src/nam_to_zarr/noaa/nam_conus/forecast/dataset.py`:

```python
dataset = NAMCONUSForecastDataset(
    data_dir="data",
    keep_last_n=8,  # Keep last 48 hours (8 cycles)
)
```

### Modifying Variables

Add or remove variables in `template_config.py`:

```python
self.variables = {
    "new_var": {
        "grib_name": "GRIB_PARAMETER_NAME",
        "level": "surface",
        "long_name": "Description",
        "units": "units",
        "standard_name": "cf_standard_name",
    },
}
```

## Data Sources

- **Primary**: NOAA NAM CONUS on AWS - `s3://noaa-nam-pds/`
- **Documentation**: [NAM Model Documentation](https://www.emc.ncep.noaa.gov/index.php?branch=NAM)
- **AWS Registry**: [NOAA Open Data on AWS](https://registry.opendata.aws/collab/noaa/)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- NOAA/NCEP for providing NAM data via the Big Data Program
- The Zarr and xarray communities for excellent tools
- Inspired by similar projects reformatting NWP data to cloud-optimized formats

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and code quality checks
5. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation and issues first

## Roadmap

- [ ] Add support for additional NAM grids (Alaska, Hawaii, Puerto Rico)
- [ ] Implement data validation and quality checks
- [ ] Add visualization dashboard
- [ ] Support for additional variables
- [ ] Integration with cloud storage providers
- [ ] Historical data backfill capability
