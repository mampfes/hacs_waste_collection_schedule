import calendar  # noqa: F401
import os
import sys
from datetime import date
from types import SimpleNamespace

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    ),
)

from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import PdfMonthGridRow
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.source.nkom_lt import Source, _schedule_links


def test_source_selects_the_configured_locality_and_maps_columns():
    rows = [
        PdfMonthGridRow(
            2026,
            0,
            400,
            3,
            "Nemėžis, Kuprioniškės",
            [(0, date(2026, 10, 7))],
        ),
        PdfMonthGridRow(
            2026,
            0,
            350,
            6,
            "Nemėžis, Kuprioniškės",
            [
                (0, date(2026, 10, 9)),
                (3, date(2026, 10, 1)),
            ],
        ),
        PdfMonthGridRow(
            2026,
            0,
            325,
            6,
            "Nemėžis, another route",
            [
                (0, date(2026, 10, 9)),
                (3, date(2026, 10, 1)),
            ],
        ),
        PdfMonthGridRow(
            2026,
            0,
            300,
            6,
            "Other village",
            [(0, date(2026, 10, 10))],
        ),
    ]

    events = Source.preprocess(rows, Source(location="Nemėžis"))

    assert events == [
        {"date": date(2026, 10, 7), "type": "mixed"},
        {"date": date(2026, 10, 9), "type": "packaging"},
        {"date": date(2026, 10, 1), "type": "glass"},
    ]


def test_source_reports_a_location_not_present_in_the_schedule():
    with pytest.raises(SourceArgumentNotFound, match="Missing"):
        Source.preprocess(
            [PdfMonthGridRow(2026, 0, 400, 3, "Nemėžis", [(0, date(2026, 10, 7))])],
            Source(location="Missing"),
        )


def test_schedule_lookup_selects_the_latest_pdf_for_each_waste_group():
    page = SimpleNamespace(
        text="""
        <a href="/grafikai/Grafikas-misriu-2025-(10-12).pdf">old mixed</a>
        <a href="/grafikai/Grafikas-misriu-2026-(10-12).pdf">new mixed</a>
        <a href="/grafikai/Grafikas-pakuociu-2026-(10-12).pdf">packaging</a>
        """,
        url="https://www.nkom.lt/kita.html",
    )

    assert _schedule_links(page) == [
        "https://www.nkom.lt/grafikai/Grafikas-misriu-2026-(10-12).pdf",
        "https://www.nkom.lt/grafikai/Grafikas-pakuociu-2026-(10-12).pdf",
    ]


def test_schedule_lookup_reports_missing_pdf_links_as_shape_error():
    page = SimpleNamespace(text="<html></html>", url="https://www.nkom.lt/kita.html")

    with pytest.raises(ResponseShapeError, match="schedule PDF"):
        _schedule_links(page)
