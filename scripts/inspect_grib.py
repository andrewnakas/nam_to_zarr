#!/usr/bin/env python3
"""Diagnostic script to inspect NAM GRIB2 file contents."""

import sys
import tempfile
from datetime import datetime, timedelta, timezone

import requests
import xarray as xr


def inspect_grib_file(url: str):
    """Download and inspect a NAM GRIB2 file."""
    print(f"Downloading: {url}")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".grib2", delete=False) as f:
            f.write(response.content)
            temp_file = f.name

        print(f"Downloaded to: {temp_file}")
        print(f"File size: {len(response.content) / (1024*1024):.2f} MB")
        print()

        # Try to read different level types
        level_types = [
            "heightAboveGround",
            "surface",
            "meanSea",
            "atmosphereSingleLayer",
            "isobaricInhPa",
        ]

        for level_type in level_types:
            print(f"\n{'='*60}")
            print(f"Level Type: {level_type}")
            print(f"{'='*60}")

            try:
                ds = xr.open_dataset(
                    temp_file,
                    engine="cfgrib",
                    backend_kwargs={
                        "filter_by_keys": {"typeOfLevel": level_type},
                        "indexpath": "",
                    },
                )

                print(f"Variables ({len(ds.data_vars)}):")
                for var_name in ds.data_vars:
                    var = ds[var_name]
                    attrs_str = []
                    if "long_name" in var.attrs:
                        attrs_str.append(f"long_name: {var.attrs['long_name']}")
                    if "units" in var.attrs:
                        attrs_str.append(f"units: {var.attrs['units']}")
                    if "GRIB_stepType" in var.attrs:
                        attrs_str.append(f"stepType: {var.attrs['GRIB_stepType']}")

                    print(f"  {var_name}: {', '.join(attrs_str)}")
                    print(f"    Shape: {var.shape}, Dims: {var.dims}")

                print(f"\nCoordinates: {list(ds.coords.keys())}")

                ds.close()

            except Exception as e:
                print(f"  Error: {e}")

    except Exception as e:
        print(f"Error: {e}")
        return


def main():
    """Main entry point."""
    # Get most recent forecast
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    hours_ago = 4
    target_time = now - timedelta(hours=hours_ago)
    cycle_hour = (target_time.hour // 6) * 6
    reference_time = target_time.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)

    date_str = reference_time.strftime("%Y%m%d")
    cycle_str = reference_time.strftime("%H")

    print(f"Inspecting NAM forecast for: {reference_time}")
    print()

    # Inspect just the first forecast hour
    url = f"https://noaa-nam-pds.s3.amazonaws.com/nam.{date_str}/nam.t{cycle_str}z.awphys00.tm00.grib2"
    inspect_grib_file(url)


if __name__ == "__main__":
    main()
