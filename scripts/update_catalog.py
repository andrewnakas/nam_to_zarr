#!/usr/bin/env python3
"""Update catalog of available NAM CONUS Zarr datasets."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_zarr_info(zarr_path: Path) -> dict:
    """Get information about a Zarr dataset.

    Args:
        zarr_path: Path to Zarr dataset

    Returns:
        Dictionary with dataset information
    """
    # Parse timestamp from name: nam_conus_YYYYMMDD_HH.zarr
    name = zarr_path.name
    parts = name.replace(".zarr", "").split("_")

    try:
        date_str = parts[2]  # YYYYMMDD
        hour_str = parts[3]  # HH

        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(hour_str)

        timestamp = datetime(year, month, day, hour, tzinfo=timezone.utc)

        # Get size
        size_bytes = sum(f.stat().st_size for f in zarr_path.rglob("*") if f.is_file())
        size_mb = size_bytes / (1024 * 1024)

        return {
            "name": name,
            "path": str(zarr_path.relative_to(zarr_path.parent.parent)),
            "reference_time": timestamp.isoformat(),
            "cycle_hour": hour,
            "size_mb": round(size_mb, 2),
        }
    except (ValueError, IndexError) as e:
        print(f"Error parsing {name}: {e}", file=sys.stderr)
        return None


def update_catalog(data_dir: Path = Path("data"), output_file: Path = Path("catalog.json")):
    """Update the catalog of available datasets.

    Args:
        data_dir: Directory containing Zarr datasets
        output_file: Path to output catalog JSON file
    """
    if not data_dir.exists():
        print(f"Data directory does not exist: {data_dir}")
        return

    # Find all Zarr datasets
    zarr_dirs = sorted(data_dir.glob("nam_conus_*.zarr"), reverse=True)

    datasets = []
    for zarr_dir in zarr_dirs:
        info = get_zarr_info(zarr_dir)
        if info:
            datasets.append(info)

    # Create catalog
    catalog = {
        "title": "NAM CONUS Forecast Data Catalog",
        "description": "Rolling 48-hour archive of NAM CONUS 12km forecast data in Zarr format",
        "updated": datetime.now(timezone.utc).isoformat(),
        "update_frequency": "Every 6 hours (00, 06, 12, 18 UTC cycles)",
        "retention_period": "48 hours",
        "forecast_length": "72 hours",
        "grid_resolution": "12 km",
        "datasets": datasets,
        "count": len(datasets),
    }

    # Write catalog
    with open(output_file, "w") as f:
        json.dump(catalog, f, indent=2)

    print(f"✅ Updated catalog with {len(datasets)} datasets")
    print(f"   Written to: {output_file}")

    if datasets:
        print(f"   Latest: {datasets[0]['reference_time']}")
        print(f"   Oldest: {datasets[-1]['reference_time']}")
        total_size = sum(d["size_mb"] for d in datasets)
        print(f"   Total size: {total_size:.1f} MB")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Update NAM CONUS data catalog")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing Zarr datasets",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("catalog.json"),
        help="Output catalog file",
    )

    args = parser.parse_args()
    update_catalog(data_dir=args.data_dir, output_file=args.output)


if __name__ == "__main__":
    main()
