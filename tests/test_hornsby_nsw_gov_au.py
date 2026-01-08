"""
Test script for hornsby_nsw_gov_au waste collection source.

Run with: uv run python tests/test_hornsby_nsw_gov_au.py
"""

import os
import sys
from dataclasses import dataclass
from datetime import date

# Mock the Collection class before importing the source
@dataclass
class Collection:
    date: date
    t: str
    icon: str = None

# Create a mock module for waste_collection_schedule
class MockWCS:
    Collection = Collection

sys.modules['waste_collection_schedule'] = MockWCS()

# Now import the source directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../custom_components/waste_collection_schedule/waste_collection_schedule")))

from source import hornsby_nsw_gov_au


def test_fetch_with_valid_address():
    """Test fetching waste collection data for a valid address."""
    source = hornsby_nsw_gov_au.Source(address="1 Cherrybrook Road, West Pennant Hills, 2125")
    entries = source.fetch()

    assert len(entries) > 0, "Expected at least one collection entry"

    # Check that we have the expected waste types
    waste_types = {e.t for e in entries}
    print(f"\nFound waste types: {waste_types}")
    print(f"Total entries: {len(entries)}")

    # Print first few entries
    print("\nFirst 10 entries:")
    for entry in entries[:10]:
        print(f"  {entry.date} - {entry.t}")

    # We should have at least Green Waste and Recycling
    assert "Green Waste" in waste_types or "Recycling" in waste_types, (
        f"Expected Green Waste or Recycling in waste types, got: {waste_types}"
    )


def test_address_resolution():
    """Test that address resolution works correctly."""
    urls = hornsby_nsw_gov_au._resolve_pdf_urls_for_address(
        "1 Cherrybrook Road, West Pennant Hills, 2125"
    )

    assert "weekly" in urls, "Expected 'weekly' key in resolved URLs"
    assert urls["weekly"] is not None, "Expected weekly PDF URL to be set"
    assert urls["weekly"].endswith(".pdf"), "Expected weekly URL to be a PDF"

    print(f"\nResolved URLs:")
    print(f"  Weekly: {urls['weekly']}")
    print(f"  Bulky: {urls.get('bulky', 'Not available')}")


def test_multiple_addresses():
    """Test fetching for multiple test addresses."""
    test_addresses = [
        "1 Cherrybrook Road, West Pennant Hills, 2125",
        "10 Albion Street, Pennant Hills, 2120",
    ]

    for address in test_addresses:
        print(f"\n--- Testing address: {address} ---")
        source = hornsby_nsw_gov_au.Source(address=address)
        entries = source.fetch()

        print(f"Found {len(entries)} entries")
        waste_types = {e.t for e in entries}
        print(f"Waste types: {waste_types}")

        assert len(entries) > 0, f"Expected entries for address: {address}"


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Hornsby NSW Gov AU Waste Collection Source")
    print("=" * 60)

    print("\n[1] Testing address resolution...")
    test_address_resolution()
    print("✓ Address resolution passed")

    print("\n[2] Testing fetch with valid address...")
    test_fetch_with_valid_address()
    print("✓ Fetch test passed")

    print("\n[3] Testing multiple addresses...")
    test_multiple_addresses()
    print("✓ Multiple addresses test passed")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
