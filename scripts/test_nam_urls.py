#!/usr/bin/env python3
"""Test script to discover correct NAM URL structure."""

import requests
from datetime import datetime, timedelta, timezone


def test_url(url: str) -> bool:
    """Test if a URL exists."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def main():
    """Test different NAM URL patterns."""
    base_url = "https://noaa-nam-pds.s3.amazonaws.com"

    # Try recent dates
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    print("Testing NAM URL patterns...")
    print(f"Current UTC time: {now}")
    print()

    # Try different date/cycle combinations
    for days_ago in range(0, 3):
        test_date = now - timedelta(days=days_ago)
        date_str = test_date.strftime("%Y%m%d")

        for cycle in ["00", "06", "12", "18"]:
            print(f"\nTesting date {date_str}, cycle {cycle}:")

            # Different product/file name patterns to test
            patterns = [
                f"nam.{date_str}/nam.t{cycle}z.awphys00.tm00.grib2",
                f"nam.{date_str}/nam.t{cycle}z.awip1200.tm00.grib2",
                f"nam.{date_str}/nam.t{cycle}z.awip3200.tm00.grib2",
                f"nam.{date_str}/nam.t{cycle}z.awip3218.tm00.grib2",
                f"nam.{date_str}/nam.t{cycle}z.conusnest.hiresf00.tm00.grib2",
                f"nam.{date_str}/nam.t{cycle}z.awphys00.grb2",
                f"nam.{date_str}/nam_218_{cycle}00_0000_000.grb2",
            ]

            for pattern in patterns:
                url = f"{base_url}/{pattern}"
                if test_url(url):
                    print(f"  ✓ FOUND: {pattern}")
                    # Also test if it's accessible for download
                    try:
                        r = requests.get(url, timeout=10, stream=True)
                        size = len(r.content) / (1024 * 1024)
                        print(f"    Size: {size:.2f} MB")
                    except Exception as e:
                        print(f"    Error downloading: {e}")
                else:
                    print(f"  ✗ Not found: {pattern}")


if __name__ == "__main__":
    main()
