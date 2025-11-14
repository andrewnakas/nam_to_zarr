#!/usr/bin/env python3
"""Clean up old NAM CONUS Zarr datasets to maintain rolling window."""

import argparse
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_zarr_timestamp(zarr_name: str) -> datetime | None:
    """Extract timestamp from Zarr dataset name.

    Expected format: nam_conus_YYYYMMDD_HH.zarr

    Args:
        zarr_name: Name of the Zarr dataset

    Returns:
        datetime object or None if parsing fails
    """
    try:
        # Extract YYYYMMDD and HH from name like "nam_conus_20251114_00.zarr"
        parts = zarr_name.replace(".zarr", "").split("_")
        if len(parts) < 4:
            return None

        date_str = parts[2]  # YYYYMMDD
        hour_str = parts[3]  # HH

        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(hour_str)

        return datetime(year, month, day, hour, tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def cleanup_old_data(data_dir: Path, retention_hours: int = 48, dry_run: bool = False):
    """Remove Zarr datasets older than retention period.

    Args:
        data_dir: Directory containing Zarr datasets
        retention_hours: Number of hours of data to keep
        dry_run: If True, only print what would be deleted
    """
    if not data_dir.exists():
        print(f"Data directory does not exist: {data_dir}")
        return

    # Find all Zarr datasets
    zarr_dirs = sorted(data_dir.glob("nam_conus_*.zarr"))

    if not zarr_dirs:
        print("No Zarr datasets found")
        return

    # Calculate cutoff time
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(hours=retention_hours)

    print(f"Current time: {now.isoformat()}")
    print(f"Retention period: {retention_hours} hours")
    print(f"Cutoff time: {cutoff_time.isoformat()}")
    print(f"Found {len(zarr_dirs)} Zarr datasets")
    print()

    # Check each dataset
    deleted_count = 0
    kept_count = 0

    for zarr_dir in zarr_dirs:
        zarr_name = zarr_dir.name
        timestamp = parse_zarr_timestamp(zarr_name)

        if timestamp is None:
            print(f"⚠️  Could not parse timestamp from: {zarr_name}")
            continue

        age_hours = (now - timestamp).total_seconds() / 3600

        if timestamp < cutoff_time:
            if dry_run:
                print(f"🗑️  Would delete: {zarr_name} (age: {age_hours:.1f}h)")
            else:
                print(f"🗑️  Deleting: {zarr_name} (age: {age_hours:.1f}h)")
                try:
                    shutil.rmtree(zarr_dir)
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Error deleting {zarr_name}: {e}", file=sys.stderr)
        else:
            print(f"✅ Keeping: {zarr_name} (age: {age_hours:.1f}h)")
            kept_count += 1

    print()
    print(f"Summary: {deleted_count} deleted, {kept_count} kept")

    if dry_run:
        print("(dry run - no files were actually deleted)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Clean up old NAM CONUS Zarr datasets"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing Zarr datasets (default: data)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=48,
        help="Number of hours of data to keep (default: 48)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    cleanup_old_data(
        data_dir=args.data_dir,
        retention_hours=args.hours,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
