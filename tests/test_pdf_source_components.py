"""Offline tests for the components the 2026 PDF sources added.

``PdfMonthRows``, ``retrievers.yearly_links``, ``lookups.normalize_loose``,
``TextGroupedDates(end_pattern=...)``, ``EachResponse(then=...)`` and the
``codes`` / ``weekday_order`` options of ``DayGridCalendarParser``.
"""

import datetime
import os
import sys
from types import SimpleNamespace
from typing import ClassVar

import pytest
from freezegun import freeze_time

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule import (
    lookups,
    parsers,
    preprocessors,
    retrievers,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import PdfRow, PdfWord
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.service.PdfTextCalendar import (
    GERMAN_WEEKDAY_ORDER,
    DayGridCalendarParser,
)

D = datetime.date


def _page(html: str, url: str = "https://example.org/waste/") -> SimpleNamespace:
    return SimpleNamespace(text=html, url=url)


def test_normalize_loose_drops_accents_case_and_punctuation():
    assert lookups.normalize_loose("OSIEDLE JAMNO-ŁABUSZ") == "osiedle jamno labusz"
    assert lookups.normalize_loose(" Pérouges  hors cité ") == "perouges hors cite"


class TestYearlyLinks:
    HTML = """
        <a href="/files/cal_2025.pdf">2025</a>
        <a href="/files/cal_2026.pdf">2026</a>
        <a href="/files/cal_2026_corr.pdf">2026 (again)</a>
        <a href="https://cdn.example.org/cal_2027.pdf">2027</a>
        <a href="/files/flyer.pdf">flyer</a>
    """

    @freeze_time("2026-10-11")
    def test_keeps_this_year_on_one_link_per_year(self):
        pick = retrievers.yearly_links(r"cal_(20\d\d)[^/]*\.pdf$")
        assert pick(_page(self.HTML)) == [
            "https://example.org/files/cal_2026.pdf",
            "https://cdn.example.org/cal_2027.pdf",
        ]

    @freeze_time("2028-02-01")
    def test_falls_back_to_the_newest_when_none_is_current(self):
        pick = retrievers.yearly_links(r"cal_(20\d\d)[^/]*\.pdf$")
        assert pick(_page(self.HTML)) == ["https://cdn.example.org/cal_2027.pdf"]

    def test_no_matching_link_fails_loudly(self):
        with pytest.raises(ValueError, match="page layout may have changed"):
            retrievers.yearly_links(r"nothing_(20\d\d)\.pdf$")(_page(self.HTML))

    @freeze_time("2026-10-11")
    def test_argument_matches_the_link_text(self):
        html = """
            <a href="/a_2026.pdf">Pérouges hors cité</a>
            <a href="/b_2026.pdf">Meximieux OUEST</a>
        """
        pick = retrievers.yearly_links(r"_(20\d\d)\.pdf$", argument="commune")
        assert pick(_page(html), commune="perouges HORS-cite") == [
            "https://example.org/a_2026.pdf"
        ]
        with pytest.raises(SourceArgumentNotFoundWithSuggestions):
            pick(_page(html), commune="Meximieux")

    @freeze_time("2026-10-11")
    def test_callable_pattern_and_the_year_in_either_place(self):
        html = """
            <a href="/KOLEDAR-TOREK-2025.pdf">old</a>
            <a href="/KOLEDAR-2026-TOREK.pdf">new</a>
            <a href="/KOLEDAR-2026-SREDA.pdf">other</a>
        """
        pick = retrievers.yearly_links(
            lambda day, **_: rf"/KOLEDAR-(?:(20\d\d)-)?{day}(?:-(20\d\d))?\.pdf$"
        )
        assert pick(_page(html), day="TOREK") == [
            "https://example.org/KOLEDAR-2026-TOREK.pdf"
        ]


def _row(page, y, *words):
    return PdfRow(page, y, tuple(PdfWord(text, x0, x1) for text, x0, x1 in words))


class TestPdfMonthRows:
    LABELS: ClassVar[dict] = {"zmieszane": 1, "metale": 1, "szkło": 1, "bio": 1}

    def rows(self):
        return [
            _row(0, 800, ("Harmonogram w roku 2026", 100, 300)),
            _row(0, 760, ("metale i tworzywa", 190, 260)),
            _row(
                0, 750, ("zmieszane", 150, 190), ("szkło", 320, 340), ("bio", 380, 390)
            ),
            # One cell across the first two columns; then two cells merged
            # into one run by extraction ("3,17,31 3,10,17,24,31").
            _row(
                0,
                700,
                ("tel. 943, 26", 10, 60),
                ("sierpień", 100, 130),
                ("3,10,17,24,31", 160, 250),
                ("3,17,31 3,10,17,24,31", 316, 411),
            ),
            _row(0, 680, ("lipiec", 100, 130), ("6", 320, 330)),
        ]

    def test_reads_cells_by_position(self):
        pre = preprocessors.PdfMonthRows(
            labels=self.LABELS, year_pattern=r"w roku\s+(20\d\d)"
        )
        found = set(pre(self.rows(), None))
        august = [3, 10, 17, 24, 31]
        assert found == (
            {(D(2026, 8, d), "zmieszane") for d in august}
            | {(D(2026, 8, d), "metale") for d in august}
            | {(D(2026, 8, d), "szkło") for d in (3, 17, 31)}
            | {(D(2026, 8, d), "bio") for d in august}
            | {(D(2026, 7, 6), "szkło")}
        )

    def test_applies_holiday_moves(self):
        rows = [
            *self.rows(),
            _row(0, 100, ("17. avgust se nadomešča 18. avgusta", 10, 300)),
        ]
        pre = preprocessors.PdfMonthRows(
            labels=self.LABELS,
            year_pattern=r"w roku\s+(20\d\d)",
            moved_pattern=r"(?P<from_day>\d{1,2})\.\s*(?P<from_month>[^\W\d_]+)\s+se\s+"
            r"nadomešča\s+(?P<to_day>\d{1,2})\.\s*(?P<to_month>[^\W\d_]+)",
        )
        found = set(pre(rows, None))
        assert (D(2026, 8, 18), "bio") in found
        assert (D(2026, 8, 17), "bio") not in found

    def test_layout_changes_fail_loudly(self):
        pre = preprocessors.PdfMonthRows(
            labels=self.LABELS, year_pattern=r"w roku\s+(20\d\d)"
        )
        with pytest.raises(ResponseShapeError):
            list(pre(self.rows()[1:], None))  # no year
        with pytest.raises(ResponseShapeError):
            list(pre([self.rows()[0], self.rows()[3]], None))  # no headings


class TestTextGroupedDatesEnd:
    TEXT = (
        "Wola 2026 Odpady segregowane 5.01 3.02 Popiół 16.01 "
        "Kontakt z biurem 7.00-15.00, 6.30 "
        "Wola 2026 Odpady segregowane 5.01 9.02 Popiół 16.01"
    )

    def make(self, end):
        return preprocessors.TextGroupedDates(
            keys=["Odpady segregowane", "Popiół"],
            date_pattern=r"\b(?P<day>\d{1,2})\.(?P<month>\d{2})\b",
            year_pattern=r"(20\d\d)",
            end_pattern=end,
        )

    def test_reads_only_up_to_the_end(self):
        assert list(self.make(r"Kontakt z biurem")(self.TEXT, None)) == [
            (D(2026, 1, 5), "Odpady segregowane"),
            (D(2026, 2, 3), "Odpady segregowane"),
            (D(2026, 1, 16), "Popiół"),
        ]

    def test_a_missing_end_fails_loudly(self):
        with pytest.raises(ResponseShapeError):
            list(self.make(r"Contact us")(self.TEXT, None))


def test_each_response_then_preprocesses_each_document_on_its_own():
    class Text:
        def __call__(self, response, source=None):
            return response.content

    responses = [
        SimpleNamespace(content="Calendar 2026 Bio 30.12", status_code=200),
        SimpleNamespace(content="Calendar 2027 Bio 6.01", status_code=200),
    ]
    parse = parsers.EachResponse(
        Text(),
        then=preprocessors.TextGroupedDates(
            keys=["Bio"],
            date_pattern=r"\b(?P<day>\d{1,2})\.(?P<month>\d{2})\b",
            year_pattern=r"Calendar (20\d\d)",
        ),
    )
    assert parse(responses) == [(D(2026, 12, 30), "Bio"), (D(2027, 1, 6), "Bio")]


class TestDayGridCodesAndWeekdays:
    CODES: ClassVar[dict] = {
        "B": "Bio",
        "B1": "Bio4",
        "GB": "Clean",
        "P": "Paper",
        "PS": "Haz",
        "SM": "Bulky",
    }

    def parser(self, months_per_page=2):
        return DayGridCalendarParser(
            labels=[],
            codes=self.CODES,
            months_per_page=months_per_page,
            line_pattern=r"^(\d{1,2})\s+([A-Za-z]{2})\b\s*(.*)",
            weekday_order=GERMAN_WEEKDAY_ORDER,
        )

    def test_splits_glued_codes_and_dates_blocks_by_weekday(self):
        # February's block is extracted before January's.
        page = "1 SO\n2 MO BB1GB\n1 DO\n2 FR PSMPS\n"
        assert sorted(self.parser()._grid_records([page], 2026)) == sorted(
            [
                (D(2026, 2, 2), "Bio"),
                (D(2026, 2, 2), "Bio4"),
                (D(2026, 2, 2), "Clean"),
                (D(2026, 1, 2), "Paper"),
                (D(2026, 1, 2), "Bulky"),
                (D(2026, 1, 2), "Haz"),
            ]
        )

    def test_a_block_fitting_no_month_fails_loudly(self):
        with pytest.raises(ResponseShapeError):
            self.parser()._grid_records(["1 MO B\n"], 2026)  # 1 Jan/Feb 2026: Thu/Sun

    def test_codes_or_labels_are_required(self):
        with pytest.raises(ValueError):
            DayGridCalendarParser(labels=[])
