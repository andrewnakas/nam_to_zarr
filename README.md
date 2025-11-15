# NOAA NAM CONUS Forecast

High-resolution weather forecasts from NOAA's North American Mesoscale (NAM) model, automatically reformatted to cloud-optimized Zarr format and updated every 6 hours.

## Dataset Overview

**Model**: NAM CONUS 12km - North American Mesoscale Model
**Coverage**: Continental United States at 12km resolution (~2145 × 1377 grid points)
**Projection**: Lambert Conformal Conic
**Updates**: Every 6 hours (00, 06, 12, 18 UTC)
**Forecast Range**: 0-84 hours (3.5 days)

- **Hourly** forecasts for first 36 hours (short-range)
- **3-hourly** forecasts from 39-84 hours (medium-range)
- **53 total forecast steps** per cycle

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
  time: 1           # Reference time (forecast initialization)
  step: 53          # Forecast hours (0-36 hourly, 39-84 3-hourly)
  y: 428            # Latitude grid points
  x: 614            # Longitude grid points
  isobaricInhPa: 6  # Pressure levels

Coordinates:
  time: Forecast reference time
  step: Forecast period (hours since reference time)
  latitude: 2D array of latitudes
  longitude: 2D array of longitudes
  isobaricInhPa: Pressure levels [1000, 925, 850, 700, 500, 250] hPa
```

## Automated Updates

This repository uses GitHub Actions to automatically:

1. Download latest NAM CONUS forecasts from NOAA AWS S3 (`s3://noaa-nam-pds/`)
2. Extract GRIB2 data using cfgrib
3. Convert to Zarr format with compression
4. Update the data catalog
5. Maintain only the most recent forecast (rolling update)

**Schedule**: Runs at 03:30, 09:30, 15:30, 21:30 UTC (3.5 hours after each NAM cycle to ensure data availability)

## Technical Details

### Data Format

- **Storage**: Zarr format with automatic compression
- **Coordinate System**: Lambert Conformal Conic projection
- **Grid Spacing**: 12 km
- **File Naming**: `nam_conus_YYYYMMDD_HH.zarr` (e.g., `nam_conus_20231114_12.zarr`)

### Compression

Data is stored with Zarr's default compression for efficient storage and fast cloud access. Typical dataset size: ~500 MB per forecast cycle (compressed).

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
# Current configuration:
hourly_hours = list(range(0, 37))        # Hours 0-36 (hourly)
three_hourly_hours = list(range(39, 85, 3))  # Hours 39-84 (3-hourly)
self.forecast_hours = hourly_hours + three_hourly_hours
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
