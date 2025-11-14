#!/usr/bin/env python3
"""Comprehensive inspection of NAM GRIB2 file to catalog all available variables."""

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import requests
import xarray as xr


def inspect_all_levels(url: str):
    """Download and comprehensively inspect all variables in NAM GRIB2 file."""
    print(f"Downloading: {url}")
    print("=" * 80)

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".grib2", delete=False) as f:
            f.write(response.content)
            temp_file = f.name

        print(f"File size: {len(response.content) / (1024*1024):.2f} MB\n")

        # Catalog all level types and variables
        level_catalog = defaultdict(lambda: defaultdict(list))

        # Try different level type filters
        level_types_to_try = [
            ("surface", {"typeOfLevel": "surface"}),
            ("meanSea", {"typeOfLevel": "meanSea"}),
            ("atmosphereSingleLayer", {"typeOfLevel": "atmosphereSingleLayer"}),
            ("heightAboveGround_2", {"typeOfLevel": "heightAboveGround", "level": 2}),
            ("heightAboveGround_10", {"typeOfLevel": "heightAboveGround", "level": 10}),
            ("heightAboveGround_80", {"typeOfLevel": "heightAboveGround", "level": 80}),
            ("isobaricInhPa_1000", {"typeOfLevel": "isobaricInhPa", "level": 1000}),
            ("isobaricInhPa_925", {"typeOfLevel": "isobaricInhPa", "level": 925}),
            ("isobaricInhPa_850", {"typeOfLevel": "isobaricInhPa", "level": 850}),
            ("isobaricInhPa_700", {"typeOfLevel": "isobaricInhPa", "level": 700}),
            ("isobaricInhPa_500", {"typeOfLevel": "isobaricInhPa", "level": 500}),
            ("isobaricInhPa_250", {"typeOfLevel": "isobaricInhPa", "level": 250}),
            ("cloudBase", {"typeOfLevel": "cloudBase"}),
            ("cloudTop", {"typeOfLevel": "cloudTop"}),
            ("tropopause", {"typeOfLevel": "tropopause"}),
        ]

        for level_name, filter_keys in level_types_to_try:
            try:
                ds = xr.open_dataset(
                    temp_file,
                    engine="cfgrib",
                    backend_kwargs={
                        "filter_by_keys": filter_keys,
                        "indexpath": "",
                    },
                )

                print(f"\n{'='*80}")
                print(f"Level: {level_name}")
                print(f"Filter: {filter_keys}")
                print(f"{'='*80}")
                print(f"Variables ({len(ds.data_vars)}):")

                for var_name in sorted(ds.data_vars):
                    var = ds[var_name]
                    long_name = var.attrs.get('long_name', 'N/A')
                    units = var.attrs.get('units', 'N/A')
                    shape = var.shape

                    print(f"  {var_name:15s} | {long_name:50s} | {units:15s} | shape: {shape}")

                    level_catalog[level_name][var_name] = {
                        'long_name': long_name,
                        'units': units,
                        'shape': shape
                    }

                ds.close()

            except Exception as e:
                print(f"\n{level_name}: No data or error - {str(e)[:100]}")

        # Summary
        print(f"\n\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"Total level types found: {len(level_catalog)}")
        for level_name, variables in sorted(level_catalog.items()):
            print(f"  {level_name:30s}: {len(variables):3d} variables")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


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

    # Inspect first forecast hour
    url = f"https://noaa-nam-pds.s3.amazonaws.com/nam.{date_str}/nam.t{cycle_str}z.awphys00.tm00.grib2"
    inspect_all_levels(url)


if __name__ == "__main__":
    main()
