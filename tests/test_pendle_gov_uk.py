"""Garden waste season regression tests; run this file explicitly with pytest."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.source.pendle_gov_uk import Source


def fetch_on(first_date, title="Blue Collection", future=False, garden=True):
    source = Source(
        "BB9 7LJ",
        "Test address",
        garden_waste_bin=garden,
        future_collection_dates=future,
    )
    with (
        patch.object(
            source,
            "_get_map_config",
            return_value={
                "legend": {"layerGroups": [{"layers": [{"id": "bins"}]}]},
                "doubleClick": {"url": "https://example.invalid/wms"},
            },
        ),
        patch.object(source, "_lookup_addresses", return_value=[]),
        patch.object(source, "_select_address", return_value={"X": 0, "Y": 0}),
        patch.object(
            source,
            "_fetch_collections",
            return_value=[{"title": title, "frequency": 2}],
        ),
        patch.object(source, "_select_zone", side_effect=lambda items: items),
        patch.object(source, "_resolve_next_collection_date", return_value=first_date),
    ):
        return source.fetch()


@pytest.mark.parametrize(
    "title", ["Blue Collection", "Brown Collection", "Green Collection"]
)
@pytest.mark.parametrize(
    "day,active",
    [
        (date(2026, 11, 30), True),
        (date(2026, 12, 1), False),
        (date(2027, 1, 1), False),
        (date(2027, 2, 28), False),
        (date(2028, 2, 29), False),
        (date(2027, 3, 1), True),
    ],
)
def test_garden_waste_season(day, active, title):
    entries = fetch_on(day, title)
    assert any(entry.type == "Green Collection" for entry in entries) == active
    if title != "Green Collection":
        assert [
            (entry.date, entry.type) for entry in entries if entry.type == title
        ] == [(day, title)]


@pytest.mark.parametrize("first_date", [date(2026, 11, 20), date(2027, 2, 19)])
def test_future_dates_cross_season_boundary(first_date):
    entries = fetch_on(first_date, future=True)
    expected_dates = Source._expand_dates(first_date, 2)
    assert [
        entry.date for entry in entries if entry.type == "Blue Collection"
    ] == expected_dates
    assert [entry.date for entry in entries if entry.type == "Green Collection"] == [
        day for day in expected_dates if 3 <= day.month <= 11
    ]


def test_garden_waste_remains_optional():
    assert {entry.type for entry in fetch_on(date(2027, 3, 1), garden=False)} == {
        "Blue Collection"
    }


@pytest.mark.parametrize(
    "title", ["Grey Collection", "Food Collection", "Food Waste Collection"]
)
def test_other_collections_continue_in_winter(title):
    entries = fetch_on(date(2027, 1, 1), title, future=True)
    assert {entry.type for entry in entries} == {title}
    assert len(entries) == 7
