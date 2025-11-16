# NOAA NAM CONUS Nest Forecast

High-resolution weather forecasts from NOAA's North American Mesoscale (NAM) model CONUS Nest, automatically reformatted to cloud-optimized Zarr format with projection coordinates and updated every 6 hours.

## Dataset Overview

**Model**: NAM CONUS Nest 3km - North American Mesoscale Model (High-Resolution Nested Grid)
**Coverage**: Continental United States at 3km resolution (1799 × 1059 grid points)
**Projection**: Lambert Conformal Conic with x/y coordinates in meters
**Updates**: Every 6 hours (00, 06, 12, 18 UTC)
**Forecast Range**: 0-60 hours (2.5 days)

- **Hourly** forecasts for all 61 forecast hours (0-60)
- Higher spatial resolution (3km vs 12km) for better local detail
- **61 total forecast steps** per cycle
- Projection coordinates (x, y) provided in meters for geospatial operations

### Key Features

✨ **Projection Coordinates**: X/Y coordinates in meters following Lambert Conformal Conic projection
✨ **CF-Compliant**: Includes grid_mapping variable with full projection specification
✨ **Cloud-Optimized**: Zarr format with chunking for efficient access
✨ **Higher Resolution**: 3km grid spacing vs 12km parent domain

## Variables Available

The dataset includes 19 meteorological variables across surface and pressure levels:

### Surface & Near-Surface Variables

| Variable | Description | Level | Units |
|----------|-------------|-------|-------|
| **t2m** | 2 metre temperature | 2m above ground | K |
| **d2m** | 2 metre dewpoint temperature | 2m above ground | K |
| **r2** | 2 metre relative humidity | 2m above ground | % |
| **u10** | 10 metre U wind component | 10m above ground | m/s |
| **v10** | 10 metre V wind component | 10m above ground | m/s |
| **sp** | Surface pressure | Surface | Pa |
| **prmsl** | Mean sea level pressure | Mean sea level | Pa |
| **tp** | Total precipitation (accumulated) | Surface | kg/m² |
| **tcc** | Total cloud cover | Atmosphere | % |
| **cape** | Convective available potential energy | Surface | J/kg |
| **cin** | Convective inhibition | Surface | J/kg |
| **dswrf** | Downward shortwave radiation flux | Surface | W/m² |
| **dlwrf** | Downward longwave radiation flux | Surface | W/m² |

### Pressure Level Variables

Available at 6 pressure levels (1000, 925, 850, 700, 500, 250 hPa):

| Variable | Description | Units |
|----------|-------------|-------|
| **t** | Temperature | K |
| **gh** | Geopotential height | m |
| **r** | Relative humidity | % |
| **u** | U wind component | m/s |
| **v** | V wind component | m/s |
| **w** | Vertical velocity | Pa/s |

## Data Access

### Using xarray

```python
import xarray as xr

# Open the latest forecast
ds = xr.open_zarr("data/nam_conus_20231114_12.zarr", consolidated=True)

# View dataset structure
print(ds)

# Access 2m temperature
temperature = ds['t2m']

# Get forecast for specific time
# First hour forecast
t2m_hour_0 = ds['t2m'].isel(time=0, step=0)

# 24 hours ahead
t2m_24h = ds['t2m'].isel(time=0, step=24)

# Plot
import matplotlib.pyplot as plt
t2m_hour_0.plot()
plt.show()
```

### Dataset Structure

```python
Dimensions:
  time: 1            # Reference time (forecast initialization)
  step: 61           # Forecast hours (0-60 hourly)
  y: 1059            # Y-axis grid points (north-south)
  x: 1799            # X-axis grid points (east-west)
  isobaricInhPa: 6   # Pressure levels

Coordinates:
  time: Forecast reference time
  step: Forecast period (hours since reference time)
  x: 1D array of x-coordinates in projection meters [~-2.7M to 2.7M m]
  y: 1D array of y-coordinates in projection meters [~-1.6M to 1.6M m]
  latitude: 2D array of latitudes (for reference)
  longitude: 2D array of longitudes (for reference)
  isobaricInhPa: Pressure levels [1000, 925, 850, 700, 500, 250] hPa

Grid Mapping:
  lambert_conformal: Projection metadata (CF-compliant)
    - standard_parallel: [38.5°, 38.5°]
    - longitude_of_central_meridian: -97.5°
    - latitude_of_projection_origin: 38.5°
```

## Automated Updates

This repository uses GitHub Actions to automatically:

1. Download latest NAM CONUS Nest 3km forecasts from NOAA AWS S3 (`s3://noaa-nam-pds/`)
2. Extract GRIB2 data using cfgrib and eccodes
3. Compute Lambert Conformal Conic projection coordinates (x/y in meters) using pyproj
4. Convert to Zarr format with compression and CF-compliant metadata
5. Update the data catalog
6. Maintain only the most recent forecast (rolling update)

**Schedule**: Runs at 03:30, 09:30, 15:30, 21:30 UTC (3.5 hours after each NAM cycle to ensure data availability)

## Technical Details

### Data Format

- **Storage**: Zarr format with automatic compression
- **Coordinate System**: Lambert Conformal Conic projection with x/y in meters
- **Grid Spacing**: 3 km (3000 m)
- **Grid Size**: 1799 × 1059 points (~1.9 million grid cells)
- **File Naming**: `nam_conus_YYYYMMDD_HH.zarr` (e.g., `nam_conus_20231114_12.zarr`)
- **Projection**: CF-compliant grid_mapping variable included

### Projection Coordinates

This dataset provides x/y coordinates in meters following the Lambert Conformal Conic projection, similar to NBM data. This enables:

- **Direct geospatial operations** without coordinate transformation
- **Consistent coordinate system** across different forecast models
- **CF-1.8 compliance** with grid_mapping metadata
- **Easy integration** with GIS tools and libraries (rasterio, rioxarray, etc.)

Example using projection coordinates:

```python
import xarray as xr

ds = xr.open_zarr("data/nam_conus_20231114_12.zarr", consolidated=True)

# Access data using projection coordinates (meters)
# Select a 100km × 100km box around a point
x_center = 500000  # meters
y_center = 1000000  # meters
box_size = 50000   # ±50km = 100km box

subset = ds.sel(
    x=slice(x_center - box_size, x_center + box_size),
    y=slice(y_center - box_size, y_center + box_size)
)
```

### Compression

Data is stored with Zarr's default compression for efficient storage and fast cloud access. Typical dataset size: ~2-3 GB per forecast cycle (compressed).

## Installation

### Prerequisites

- Python 3.11 or later
- System dependencies: `libeccodes-dev`, `libgeos-dev`

### Setup

```bash
# Clone the repository
git clone https://github.com/andrewnakas/nam_to_zarr.git
cd nam_to_zarr

# Install dependencies (using uv - recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install --system -e .

# Or using pip
pip install -e .
```

### Manual Update

```bash
# Run data update manually
python -m nam_to_zarr.noaa.nam_conus.forecast.dataset
```

## Configuration

### Customize Forecast Hours

Edit `src/nam_to_zarr/noaa/nam_conus/forecast/template_config.py`:

```python
# Current configuration (3km CONUS Nest):
self.forecast_hours = list(range(0, 61))  # Hours 0-60 (hourly)

# For subset (e.g., first 24 hours only):
self.forecast_hours = list(range(0, 25))  # Hours 0-24
```

### Adjust Storage Retention

Edit `src/nam_to_zarr/noaa/nam_conus/forecast/dataset.py`:

```python
dataset = NAMCONUSForecastDataset(
    data_dir="data",
    keep_last_n=1,  # Number of forecast cycles to keep
)
```

### Add Variables

Variables can be added in `template_config.py`. Find available variables in NAM GRIB2 files:

```python
self.variables = {
    "new_var": {
        "grib_name": "GRIB_SHORT_NAME",
        "level": "surface",
        "long_name": "Descriptive name",
        "units": "units",
        "standard_name": "CF_standard_name",
    },
}
```

## Data Sources

- **NOAA NAM CONUS**: [s3://noaa-nam-pds/](https://noaa-nam-pds.s3.amazonaws.com/index.html)
- **Model Documentation**: [NOAA EMC NAM](https://www.emc.ncep.noaa.gov/index.php?branch=NAM)
- **AWS Open Data**: [NOAA on AWS](https://registry.opendata.aws/collab/noaa/)

## About NAM

The North American Mesoscale Forecast System (NAM) is a NOAA operational weather prediction model running over North America. The CONUS 12km nest provides high-resolution forecasts over the continental United States, updated four times daily.

**Key Characteristics**:
- High spatial resolution (12 km grid spacing)
- Rapid update cycle (every 6 hours)
- 84-hour forecast length
- Optimized for short to medium-range forecasting
- Captures mesoscale weather features

## Use Cases

- **Weather Forecasting**: High-resolution temperature, precipitation, and wind forecasts
- **Renewable Energy**: Solar radiation and wind speed predictions for energy production
- **Agriculture**: Temperature extremes, precipitation, and humidity for crop management
- **Aviation**: Visibility, wind, and convective activity
- **Severe Weather**: CAPE/CIN for thunderstorm potential
- **Research**: Mesoscale meteorology and model validation

## Example Applications

### Extract Temperature Time Series

```python
import xarray as xr

ds = xr.open_zarr("data/nam_conus_20231114_12.zarr")

# Get temperature at a specific location (lat/lon)
lat, lon = 40.7, -74.0  # New York City
t2m_series = ds['t2m'].sel(x=lon, y=lat, method='nearest')

# Convert to Celsius
t2m_celsius = t2m_series - 273.15

# Plot forecast
t2m_celsius.plot()
```

### Calculate Wind Speed

```python
import numpy as np

ds = xr.open_zarr("data/nam_conus_20231114_12.zarr")

# Calculate wind speed from u/v components
wind_speed = np.sqrt(ds['u10']**2 + ds['v10']**2)
wind_speed.attrs['long_name'] = '10m wind speed'
wind_speed.attrs['units'] = 'm/s'
```

### Access Pressure Level Data

```python
ds = xr.open_zarr("data/nam_conus_20231114_12.zarr")

# Temperature at 500 hPa (mid-troposphere)
t_500 = ds['t'].sel(isobaricInhPa=500)

# Geopotential height at 250 hPa (jet stream level)
gh_250 = ds['gh'].sel(isobaricInhPa=250)
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Run linting and formatting
ruff check .
ruff format .

# Type checking
mypy src
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Acknowledgments

- **NOAA/NCEP** for providing NAM data through the Big Data Program
- **AWS** for hosting NOAA data on S3
- **Zarr** and **xarray** communities for excellent cloud-native data tools
- **[dynamical.org](https://dynamical.org)** for inspiration on cloud-optimized weather data catalogs and best practices
- Inspired by cloud-optimized weather data initiatives

## Citation

If you use this data in research, please cite:

```
NOAA National Centers for Environmental Prediction (NCEP)
North American Mesoscale Forecast System (NAM)
https://www.emc.ncep.noaa.gov/index.php?branch=NAM
```

## Support

- **Issues**: [GitHub Issues](https://github.com/andrewnakas/nam_to_zarr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/andrewnakas/nam_to_zarr/discussions)

## Related Projects

- [herbie-data](https://github.com/blaylockbk/Herbie) - Download weather model data
- [goes2go](https://github.com/blaylockbk/goes2go) - GOES satellite data
- [ecmwf-opendata](https://github.com/ecmwf/ecmwf-opendata) - ECMWF forecasts
