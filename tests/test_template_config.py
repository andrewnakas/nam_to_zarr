"""Tests for NAM CONUS template configuration."""

from datetime import datetime

from nam_to_zarr.noaa.nam_conus.forecast import NAMCONUSTemplateConfig


def test_template_config_initialization():
    """Test that template config initializes with default values."""
    config = NAMCONUSTemplateConfig()

    assert config.grid_shape == (1377, 2145)
    assert config.projection == "Lambert_Conformal"
    assert config.update_interval == 6
    assert config.forecast_hours is not None
    assert len(config.forecast_hours) > 0
    assert config.variables is not None


def test_forecast_hours():
    """Test that forecast hours are correctly set."""
    config = NAMCONUSTemplateConfig()

    # Should include 0 and go up to 24
    assert 0 in config.forecast_hours
    assert 24 in config.forecast_hours
    # Should be in 3-hour intervals
    assert all(h % 3 == 0 for h in config.forecast_hours)


def test_variables_configuration():
    """Test that required variables are configured."""
    config = NAMCONUSTemplateConfig()

    required_vars = ["t2m", "u10", "v10", "tp", "msl"]

    for var in required_vars:
        assert var in config.variables
        assert "grib_name" in config.variables[var]
        assert "long_name" in config.variables[var]
        assert "units" in config.variables[var]


def test_dataset_attributes():
    """Test dataset attributes generation."""
    config = NAMCONUSTemplateConfig()
    ref_time = "2024-01-01T00:00:00"

    attrs = config.get_dataset_attrs(ref_time)

    assert "title" in attrs
    assert "institution" in attrs
    assert "reference_time" in attrs
    assert attrs["reference_time"] == ref_time


def test_coordinate_attributes():
    """Test coordinate attributes."""
    config = NAMCONUSTemplateConfig()

    coords = ["time", "step", "x", "y", "latitude", "longitude"]

    for coord in coords:
        attrs = config.get_coord_attrs(coord)
        # Should return a dict (may be empty for unknown coords)
        assert isinstance(attrs, dict)
