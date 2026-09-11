import os
import sys

import pytest

# Insert repo root to sys.path for absolute imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.waste_collection_schedule.waste_collection_schedule.source import (
    hobsonsbay_vic_gov_au,
)

# Reference the exceptions through the source module: importing them by their
# other module path would create distinct classes that pytest.raises misses.
SourceArgumentException = hobsonsbay_vic_gov_au.SourceArgumentException
SourceArgumentNotFoundWithSuggestions = (
    hobsonsbay_vic_gov_au.SourceArgumentNotFoundWithSuggestions
)

SUBURBS = [
    "Altona",
    "Altona Meadows",
    "Altona North",
    "Brooklyn",
    "Laverton",
    "Newport",
    "Seabrook",
    "Seaholme",
    "South Kingsville",
    "Spotswood",
    "Williamstown",
    "Williamstown North",
]


@pytest.mark.parametrize(
    "street_address,expected",
    [
        ("399 Queen St, Altona Meadows", ("399", "Queen St", "Altona Meadows")),
        ("48 Pier St, Altona", ("48", "Pier St", "Altona")),
        # the comma is optional
        ("20 Merrett Dr Williamstown", ("20", "Merrett Dr", "Williamstown")),
        # a longer suburb wins over one that is a prefix of it
        ("1 Central Ave, Altona North", ("1", "Central Ave", "Altona North")),
        (
            "2 Ferguson St Williamstown North",
            ("2", "Ferguson St", "Williamstown North"),
        ),
        # unit numbers and untidy spacing survive
        ("1/20 Merrett Dr, Williamstown", ("1/20", "Merrett Dr", "Williamstown")),
        # untidy spacing is collapsed and the council's own casing is returned
        ("  48   Pier  St ,  altona ", ("48", "Pier St", "Altona")),
    ],
)
def test_split_address(street_address, expected):
    assert hobsonsbay_vic_gov_au.split_address(street_address, SUBURBS) == expected


def test_unknown_suburb_suggests_served_suburbs():
    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as excinfo:
        hobsonsbay_vic_gov_au.split_address("1 Bourke St, Melbourne", SUBURBS)
    assert "Altona Meadows" in str(excinfo.value)


@pytest.mark.parametrize(
    "street_address,expected_exception",
    [
        # no suburb at all, so the suburb match fails first
        ("Altona", SourceArgumentNotFoundWithSuggestions),
        # a known suburb, but nothing left to read as number plus street
        ("12 Williamstown", SourceArgumentException),
    ],
)
def test_missing_number_or_street_is_reported(street_address, expected_exception):
    with pytest.raises(expected_exception):
        hobsonsbay_vic_gov_au.split_address(street_address, SUBURBS)
