"""Tests for the shared waste-info.com.au register matching.

The three sources using this (canadabay, cumberland, innerwest) can only be
exercised against live council data, which moves. These lock down the rules the
matcher promises: case and spacing are ignored, a building name may sit between
the number and the street, and a number still has to match in full.
"""

import os
import sys

import pytest

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "waste_collection_schedule",
        )
    )
)

from waste_collection_schedule.service.WasteInfo import (
    norm,
    property_matches,
    same,
    street_number_suggestions,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("Merrylands  Road", "merrylands road"),
        ("  Berala\n", "berala"),
        (283, "283"),
        (0, "0"),
        (None, ""),
    ],
)
def test_norm(value, expected):
    assert norm(value) == expected


def test_zero_is_not_empty():
    # "0 Smith Street" is a real address; `value or ""` used to erase it.
    assert not same(0, None)
    assert same(0, "0")


@pytest.mark.parametrize("suburb", ["Berala", "berala", "  BERALA "])
def test_same_ignores_case_and_spacing(suburb):
    assert same("Berala", suburb)


def test_property_matches_canonical_row():
    assert property_matches(
        "76 Tennyson Road Mortlake", "76", "Tennyson Road", "Mortlake"
    )


def test_property_matches_ignores_case_and_spacing():
    assert property_matches(
        "76  tennyson road  MORTLAKE", "76", "Tennyson  Road", "mortlake"
    )


def test_property_matches_with_building_name():
    assert property_matches(
        "4-12 five dock library Garfield Street Five Dock",
        "4-12",
        "Garfield Street",
        "Five Dock",
    )


def test_property_matches_requires_the_whole_number():
    # "1m/4-12 ..." is a different property from "4-12 ...".
    assert not property_matches(
        "1m/4-12 Garfield Street Five Dock", "4-12", "Garfield Street", "Five Dock"
    )


def test_property_matches_requires_the_right_suburb():
    assert not property_matches(
        "76 Tennyson Road Mortlake", "76", "Tennyson Road", "Concord"
    )


def test_street_number_suggestions_keeps_register_wording():
    rows = [
        "76 Tennyson Road Mortlake",
        "4-12 Five Dock Library Garfield Street Five Dock",
        "1A Gipps Street Concord",
    ]
    assert street_number_suggestions(rows, "garfield  street") == [
        "4-12 Five Dock Library"
    ]


def test_street_number_suggestions_uses_the_last_occurrence():
    rows = ["1 Garfield Street Cafe Garfield Street Five Dock"]
    assert street_number_suggestions(rows, "Garfield Street") == [
        "1 Garfield Street Cafe"
    ]


def test_street_number_suggestions_skips_rows_with_no_number():
    assert (
        street_number_suggestions(["Garfield Street Five Dock"], "Garfield Street")
        == []
    )


def test_street_number_suggestions_without_a_street():
    assert street_number_suggestions(["76 Tennyson Road Mortlake"], "") == []
