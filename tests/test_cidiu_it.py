"""Tests for the cidiu_it zone matching.

CIDIU retired its own calendar endpoint and now publishes schedules through the
Junker app, which has one zone per street (or per range of street numbers).
These tests cover how a (street, street number) pair is mapped onto a zone name.
"""

import os
import sys
from unittest.mock import patch

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

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.junker_app import AreaRequired
from waste_collection_schedule.source import cidiu_it
from waste_collection_schedule.source.cidiu_it import Source

ZONES = [
    ("VIA CONDOVE da civico 2 a civico 124 e da civico 1 a civico 123", 1),
    ("CORSO SUSA da 1 a 15", 2),
    ("CORSO SUSA pari da 2 a 314 dispari da 17 a 315", 3),
    ("Viale Antonio Gramsci", 4),
    ("VIA ROMA da civico 1 a civico 99 (tranne civico 51)", 5),
    ("VIA ROMA da civico 51 a civico 51", 6),
    ("Corso Adriatico", 7),
]


def _zone(street, number):
    return Source(street=street, street_number=number, city="x")._find_zone(ZONES)


@pytest.mark.parametrize(
    "street, number, expected",
    [
        ("VIA CONDOVE", "107", ZONES[0][0]),
        ("via condove", 2, ZONES[0][0]),
        ("CORSO SUSA", 7, ZONES[1][0]),
        ("CORSO SUSA", 15, ZONES[1][0]),
        ("CORSO SUSA", 124, ZONES[2][0]),
        ("CORSO SUSA", "17", ZONES[2][0]),
        ("Viale Antonio Gramsci", 18, "Viale Antonio Gramsci"),
        # Junker spells the street out in full; the old calendar did not.
        ("VIALE GRAMSCI", 18, "Viale Antonio Gramsci"),
        ("Corso Adriatico", "3/A", "Corso Adriatico"),
        ("VIA ROMA", 50, ZONES[4][0]),
    ],
)
def test_zone_is_matched(street, number, expected):
    assert _zone(street, number) == expected


def test_street_number_outside_every_range_lists_the_zones():
    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as error:
        _zone("CORSO SUSA", 400)
    assert ZONES[1][0] in error.value.suggestions


def test_unknown_street_lists_the_available_zones():
    with pytest.raises(SourceArgumentNotFoundWithSuggestions):
        _zone("VIA INESISTENTE", 1)


def test_excluded_number_falls_through_to_its_own_zone():
    assert _zone("VIA ROMA", 51) == ZONES[5][0]
    assert _zone("VIA ROMA", 52) == ZONES[4][0]


def test_number_beyond_all_ranges_lists_the_zones():
    with pytest.raises(SourceArgumentNotFoundWithSuggestions):
        _zone("VIA ROMA", 200)


def test_overlapping_zones_are_reported_as_ambiguous():
    zones = [("VIA A da 1 a 10", 1), ("VIA A da 5 a 15", 2)]
    with pytest.raises(SourceArgAmbiguousWithSuggestions):
        Source(street="VIA A", street_number=7, city="x")._find_zone(zones)


def test_fetch_resolves_the_zone_and_asks_junker_for_it():
    calls = []

    class FakeJunker:
        def __init__(self, municipality, area_name=None, use_embed_url=True):
            calls.append((municipality, area_name))

        def fetch(self):
            if calls[-1][1] is None:
                raise AreaRequired(ZONES)
            return ["entries"]

    with patch.object(cidiu_it, "Junker", FakeJunker):
        result = Source(street="CORSO SUSA", street_number=124, city="Rivoli").fetch()

    assert result == ["entries"]
    assert calls == [("Rivoli", None), ("Rivoli", ZONES[2][0])]
