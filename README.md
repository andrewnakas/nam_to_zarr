# NAM CONUS to Zarr

Automated reformatting of NOAA's NAM (North American Mesoscale) CONUS forecast data into cloud-optimized Zarr format, running on a 6-hour rolling basis.

## Overview

This project automatically downloads NAM CONUS forecast data from NOAA's AWS S3 bucket, converts it from GRIB2 format to Zarr format, and maintains a rolling archive of the most recent forecasts. The entire process runs via GitHub Actions without requiring dedicated infrastructure.

### Key Features

- **Automated Updates**: Runs every 6 hours aligned with NAM update cycles (00, 06, 12, 18 UTC)
- **Rolling Storage**: Maintains the last 24 hours of forecast data (4 forecast cycles)
- **Cloud-Optimized**: Data stored in Zarr format for efficient cloud access
- **Comprehensive Variables**: Includes temperature, wind, precipitation, pressure, and more
- **GitHub-Based**: Fully automated through GitHub Actions

## Data Specifications

- **Source**: NOAA NAM CONUS 12km
- **Grid**: ~2145 × 1377 points at 12 km resolution
- **Projection**: Lambert Conformal Conic
- **Update Frequency**: Every 6 hours (00, 06, 12, 18 UTC)
- **Forecast Length**: 24 hours (0-24 hour forecasts in 3-hour intervals)
- **Format**: Zarr (compressed with Blosc/LZ4)

## Variables

The following meteorological variables are extracted from NAM CONUS:

| Variable | Description | Units |
|----------|-------------|-------|
| t2m | 2 metre temperature | K |
| d2m | 2 metre dewpoint temperature | K |
| u10 | 10 metre U wind component | m/s |
| v10 | 10 metre V wind component | m/s |
| sp | Surface pressure | Pa |
| msl | Mean sea level pressure | Pa |
| tp | Total precipitation | kg/m² |
| gust | Wind gust | m/s |
| vis | Visibility | m |
| tcc | Total cloud cover | % |
| prate | Precipitation rate | kg/m²/s |
| cape | Convective available potential energy | J/kg |

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
2. Converts to Zarr format
3. Stores in the `data/` directory
4. Removes old forecasts (keeps last 4 cycles)
5. Commits and pushes changes

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
ds = xr.open_zarr("data/nam_conus_20231114_00.zarr", consolidated=True)

# Inspect the dataset
print(ds)

# Access a variable
temperature = ds['t2m']

# Plot
temperature.isel(time=0, step=0).plot()
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
