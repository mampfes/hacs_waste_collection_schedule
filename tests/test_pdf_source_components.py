"""Offline tests for the components the 2026 PDF sources added.

``PdfMonthRows``, ``retrievers.yearly_links``, ``lookups.normalize_loose``,
``TextGroupedDates(end_pattern=...)``, ``EachResponse(then=...)`` and the
``codes`` / ``weekday_order`` options of ``DayGridCalendarParser`` and
``PdfRoundMonthGrid``.
"""

import base64
import datetime
import json
import os
import re
import sys
from html import escape
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any, ClassVar
from zipfile import ZipFile

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
from waste_collection_schedule.service.EastLindseyCalendar import (
    GardenCalendarParser,
    garden_calendar_urls,
)
from waste_collection_schedule.service.PdfTextCalendar import (
    GERMAN_WEEKDAY_ORDER,
    DayGridCalendarParser,
)

D = datetime.date


def test_marked_pdf_distinguishes_stroke_and_fill_palettes():
    response = SimpleNamespace(content=_marked_calendar_pdf())
    rows = _marked_parser(stroke_colors={"outlined": ((1, 0, 0),)})(response)
    assert {(r["date"], r["type"]) for r in rows} == {
        (D(2026, 1, 26), "general"),
        (D(2026, 1, 26), "outlined"),
    }


def test_marked_pdf_duplicate_day_repair_requires_an_explicit_limit_and_a_missing_number():
    response = SimpleNamespace(
        content=_marked_calendar_pdf(marked_day=(1, 16), duplicate_days={(1, 16): 17})
    )
    with pytest.raises(ValueError, match="differs from grid"):
        _marked_parser()(response)
    rows = _marked_parser(max_duplicate_day_repairs=1)(response)
    assert {r["date"] for r in rows} == {D(2026, 1, 16)}
    two_errors = SimpleNamespace(
        content=_marked_calendar_pdf(duplicate_days={(1, 16): 17, (2, 10): 11})
    )
    with pytest.raises(ValueError, match="differs from grid"):
        _marked_parser(max_duplicate_day_repairs=1)(two_errors)
    with pytest.raises(ValueError, match="Incomplete printed grid"):
        _marked_parser(max_duplicate_day_repairs=1)(
            SimpleNamespace(content=_marked_calendar_pdf(bad_day=(1, 16)))
        )


def test_edinburgh_printed_markers_keep_christmas_shift_and_the_january_grid_date():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule import waste_types as wt
    from waste_collection_schedule.source.edinburgh_gov_uk import Source

    case = "Princess Mary Road"
    with cassette.replaying(fixture_path("edinburgh_gov_uk", case)):
        rows = Source(**Source.TEST_CASES[case]).fetch()
    pairs = {(r.date, r.waste_type.id) for r in rows}
    assert len(rows) == 78
    assert (D(2026, 1, 16), wt.RECYCLABLES.id) in pairs
    assert (D(2026, 1, 16), wt.GLASS.id) in pairs
    assert not any(day == D(2026, 1, 17) for day, _ in pairs)
    assert (D(2026, 12, 26), wt.GENERAL_WASTE.id) in pairs
    assert (D(2026, 12, 25), wt.GENERAL_WASTE.id) not in pairs


def test_edinburgh_rejects_an_expired_calendar():
    from waste_collection_schedule.source.edinburgh_gov_uk import _current_year

    with freeze_time("2027-01-01"), pytest.raises(ValueError, match="this year"):
        list(_current_year([{"date": D(2026, 12, 26)}], None))


def _grand_lieu_calendar():
    """A complete synthetic published table, with a retained holiday pickup."""
    import calendar

    from waste_collection_schedule.parsers import (
        PdfTextFragment,
        PdfVector,
        PdfWordLayout,
    )
    from waste_collection_schedule.service.FrenchColourCalendar import _MONTHS

    line = PdfTextFragment
    colours = ((0.98, 0.84, 0.79), (0.86, 0.89, 0.93))
    lines = [line(0, "2026", 5, 600), line(0, "Jours fériés : samedi suivant", 5, 580)]
    vectors, words = [], []
    for index, (name, day, parity) in enumerate(
        [
            ("GENESTON", "Lundi", 0),
            ("LE BIGNON", "Lundi", 1),
            ("MONTBERT", "Vendredi", 1),
            ("SAINT LUMINE", "Vendredi", 0),
        ]
    ):
        y = 400 - index * 30
        lines.append(line(0, name, 20, y))
        weekday = line(0, day, 70, y)
        words.append(weekday)
        vectors.append(PdfVector(0, 60, y - 5, 80, y + 5, None, colours[parity]))
    for month, name in enumerate(_MONTHS, 1):
        x = 130 + month * 60
        words.append(line(0, name.upper(), x, 550))
        for day in range(1, calendar.monthrange(2026, month)[1] + 1):
            d = D(2026, month, day)
            y = 530 - day * 10
            p = line(0, f"{'LMMJVSD'[d.weekday()]} {day}", x, y)
            lines.append(p)
            vectors.append(
                PdfVector(
                    0,
                    x - 25,
                    y - 4,
                    x + 25,
                    y + 4,
                    None,
                    colours[d.isocalendar().week % 2],
                )
            )
            if d in {D(2026, 4, 6), D(2026, 5, 8), D(2026, 12, 25)}:
                lines.append(line(0, "Férié", x + 10, y))
    return PdfWordLayout(lines, words, vectors)


@pytest.mark.parametrize(
    "commune,expected,absent",
    [
        ("Geneston", D(2026, 5, 25), D(2026, 5, 30)),
        ("Le Bignon", D(2026, 4, 11), D(2026, 4, 6)),
        ("Montbert", D(2026, 5, 9), D(2026, 5, 8)),
        ("Saint Lumine de Coutais", D(2026, 12, 26), D(2026, 12, 25)),
    ],
)
def test_french_calendar_holiday_replacements_and_retained_collections(
    commune, expected, absent
):
    from waste_collection_schedule.service.FrenchColourCalendar import grand_lieu_rows

    rows = grand_lieu_rows(
        [_grand_lieu_calendar()], SimpleNamespace(params={"municipality": commune})
    )
    assert (expected, "general") in rows
    assert (expected, "recycling") in rows
    assert (absent, "general") not in rows


def test_french_calendar_rejects_missing_printed_dates():
    from waste_collection_schedule.service.FrenchColourCalendar import grand_lieu_rows

    document = _grand_lieu_calendar()
    document.lines.remove(next(p for p in document.lines if p.text == "J 1"))
    with pytest.raises(ResponseShapeError, match="incomplete day grid"):
        grand_lieu_rows(
            [document], SimpleNamespace(params={"municipality": "Geneston"})
        )


def test_french_calendar_area_matching_uses_polygon_not_overlapping_bounds():
    from waste_collection_schedule.parsers import PdfPolygon, PdfTextFragment
    from waste_collection_schedule.service.FrenchColourCalendar import (
        _contains,
        _normalise,
    )

    area = PdfPolygon(
        0, 0, 0, 10, 10, None, (1, 0, 0), points=((0, 0), (10, 0), (0, 10), (0, 0))
    )
    assert _contains(area, PdfTextFragment(0, "A", 2, 2))
    assert not _contains(area, PdfTextFragment(0, "B", 8, 8))
    assert _normalise("Beillé") == "beille"


def test_french_calendar_year_does_not_treat_an_address_number_as_a_year():
    from waste_collection_schedule.parsers import PdfTextFragment
    from waste_collection_schedule.service.FrenchColourCalendar import _year

    document = _grand_lieu_calendar()
    document.lines.append(PdfTextFragment(0, "2033 Route de Connerré", 50, 20))
    document.words.append(PdfTextFragment(0, "2033", 50, 20))
    assert _year(document) == 2026


def test_pdf_word_layout_can_retain_service_area_polygon_vertices():
    from io import BytesIO

    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=30, height=30)
    stream = DecodedStreamObject()
    stream.set_data(b"1 0 0 rg 0 0 m 10 0 l 0 10 l h f")
    page[NameObject("/Contents")] = writer._add_object(stream)
    out = BytesIO()
    writer.write(out)
    response = SimpleNamespace(content=out.getvalue())
    ordinary = parsers.PdfWordLayoutParser(min_words=0)(response)[0]
    polygons = parsers.PdfWordLayoutParser(min_words=0, include_points=True)(response)[
        0
    ]
    assert len(ordinary.vectors[0]) == 7
    assert not hasattr(ordinary.vectors[0], "points")
    assert polygons.vectors[0].points[:3] == ((0, 0), (10, 0), (0, 10))


def _page(html: str, url: str = "https://example.org/waste/") -> SimpleNamespace:
    return SimpleNamespace(text=html, url=url)


def _fiscal_week_grid():
    """Two dated years and seven printed day columns, with no PDF dependency."""
    import calendar

    from waste_collection_schedule.parsers import (
        PdfTextFragment,
        PdfVector,
        PdfWordLayout,
    )

    lines, words, vectors = [], [], []
    for index in range(12):
        year, month = 2026 + (index + 6) // 12, (index + 6) % 12 + 1
        cx, cy = 100 + index % 3 * 100, 600 - index // 3 * 120
        lines.append(PdfTextFragment(0, f"{calendar.month_name[month]} {year}", cx, cy))
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            date = D(year, month, day)
            x = cx - 30 + date.weekday() * 10
            y = cy - 20 - ((D(year, month, 1).weekday() + day - 1) // 7) * 10
            words.append(PdfTextFragment(0, str(day), x, y))
            if date.weekday() < 5:
                vectors.append(
                    PdfVector(0, x - 4, y - 4, x + 4, y + 4, None, (1.0, 0.0, 0.0))
                )
    return PdfWordLayout(lines, words, vectors)


@pytest.mark.parametrize("fault", [None, "missing_day", "wrong_column", "wrong_year"])
def test_dardanup_fiscal_grid_validates_printed_dates(fault):
    from waste_collection_schedule.service.DardanupCalendar import month_cells

    layout = _fiscal_week_grid()
    if fault == "missing_day":
        layout.words.pop(0)
    elif fault == "wrong_column":
        layout.words[0] = layout.words[0]._replace(x=layout.words[0].x + 10)
    elif fault == "wrong_year":
        layout.lines[0] = layout.lines[0]._replace(text="July 2025")
    if fault:
        with pytest.raises(ValueError):
            month_cells(layout, 0)
    else:
        cells = month_cells(layout, 0)
        assert len(cells) == 365
        assert min(cells) == D(2026, 7, 1)
        assert max(cells) == D(2027, 6, 30)
        assert cells[D(2026, 12, 31)] == "general"


@pytest.mark.parametrize(
    "case,key,day",
    [
        ("Hale Street (Area 1, Tuesday)", "recycling", D(2027, 1, 5)),
        ("Hale Street Area 2", "general", D(2027, 1, 5)),
        ("Burekup", "recycling", D(2027, 1, 7)),
    ],
)
def test_dardanup_published_phase_survives_iso_week_53(case, key, day):
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule import waste_types as wt
    from waste_collection_schedule.source.dardanup_wa_gov_au import Source

    expected = wt.RECYCLABLES if key == "recycling" else wt.GENERAL_WASTE
    with (
        cassette.replaying(fixture_path("dardanup_wa_gov_au", case)),
        freeze_time("2027-01-04"),
    ):
        entries = Source(**Source.TEST_CASES[case]).fetch()
    assert any(e.date == day and e.type == wt.display_name(expected) for e in entries)


@pytest.mark.parametrize("holiday", [D(2026, 12, 25), D(2027, 1, 1), D(2027, 3, 26)])
def test_dardanup_guide_moves_cancelled_friday_to_saturday(holiday):
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule.source.dardanup_wa_gov_au import Source

    case = "Hale Street (Area 1, Tuesday)"
    with (
        cassette.replaying(fixture_path("dardanup_wa_gov_au", case)),
        freeze_time(holiday),
    ):
        entries = Source(service_area="Area 1", collection_day="Friday").fetch()
    assert not any(e.date == holiday for e in entries)
    assert sum(e.date == holiday + datetime.timedelta(days=1) for e in entries) == 2
    assert all(e.date <= D(2027, 6, 30) for e in entries)


def test_dardanup_rural_service_has_separate_weekdays_and_no_fogo():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule import waste_types as wt
    from waste_collection_schedule.source.dardanup_wa_gov_au import Source

    case = "Rural Ferguson Valley split weekdays"
    with cassette.replaying(fixture_path("dardanup_wa_gov_au", case)):
        entries = Source(**Source.TEST_CASES[case]).fetch()
    assert {
        e.date.weekday() for e in entries if e.type == wt.display_name(wt.GENERAL_WASTE)
    } == {0}
    assert {
        e.date.weekday() for e in entries if e.type == wt.display_name(wt.RECYCLABLES)
    } == {3}
    assert not any(e.type == wt.display_name(wt.ORGANIC) for e in entries)


def test_normalize_loose_drops_accents_case_and_punctuation():
    assert lookups.normalize_loose("OSIEDLE JAMNO-ŁABUSZ") == "osiedle jamno labusz"
    assert lookups.normalize_loose(" Pérouges  hors cité ") == "perouges hors cite"


@pytest.mark.parametrize("case", ["Bannockburn, Monday A", "Bannockburn, Tuesday B"])
def test_lrs_shared_event_cells_keep_both_collections(case):
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule.source.lrsrecycles_com import (
        E_WASTE,
        RECYCLING,
        WASTE,
        Source,
    )

    source = Source(**Source.TEST_CASES[case])
    with cassette.replaying(fixture_path("lrsrecycles_com", case)):
        rows = list(
            source.preprocess(source.parse(source.retrieve(source), source), source)
        )

    assert sum(label == RECYCLING for _, label in rows) == 26
    assert sum(label == WASTE for _, label in rows) == 52
    assert sum(label == E_WASTE for _, label in rows) == 20
    assert (D(2026, 2, 23), E_WASTE) in rows
    assert (D(2026, 2, 24), E_WASTE) in rows


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

    def test_a_pattern_without_a_year_group_is_rejected(self):
        with pytest.raises(ValueError, match="no group for the year"):
            retrievers.yearly_links(r"cal_20\d\d\.pdf$")(_page(self.HTML))

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


def test_tamax_janow_reads_independent_recycling_and_bio_dates():
    from waste_collection_schedule.source.tamax_janow_pl import Source

    response = _recorded_pdf_response("tamax_janow_pl", "Janów")
    with freeze_time("2026-10-31"):
        rows = set(Source.preprocess(Source.parse(response)))
    assert len(rows) == 36
    assert (D(2026, 5, 28), "komunalne") in rows
    assert (D(2026, 5, 28), "segregowane") in rows
    assert (D(2026, 5, 22), "biodegradowalne") in rows
    assert (D(2026, 12, 21), "komunalne") in rows
    assert (D(2026, 12, 23), "biodegradowalne") in rows
    with freeze_time("2027-01-01"), pytest.raises(ValueError, match="current year"):
        Source.preprocess(Source.parse(response))


def test_tamax_route_discovery_keeps_identical_filenames_in_their_municipality():
    from waste_collection_schedule.service.Tamax import CalendarLink

    response = _page(
        '<div class="elementor-tab-title" aria-controls="janow">Gmina Janów (mieszkańcy)</div>'
        '<div id="janow"><p>2026 <a href="/a/2026-TRUDNE-WJAZDY.pdf">PDF</a></p></div>'
        '<div class="elementor-tab-title" aria-controls="lelow">Gmina Lelów (mieszkańcy)</div>'
        '<div id="lelow"><p>2026 <a href="/b/2026-TRUDNE-WJAZDY.pdf">PDF</a></p></div>'
    )
    selector = CalendarLink("Janów", {"Difficult access": "-TRUDNE-WJAZDY.pdf"})
    with freeze_time("2026-10-31"):
        assert (
            selector(response, area="Difficult access")
            == "https://example.org/a/2026-TRUDNE-WJAZDY.pdf"
        )
    with freeze_time("2027-01-01"), pytest.raises(ValueError, match="current-year"):
        selector(response, area="Difficult access")


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


def test_marion_new_year_thursday_is_collected_on_january_second():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule.source.marion_sa_gov_au import (
        ORGANICS,
        WASTE,
        Source,
    )

    case = "Marion (A, Thursday)"
    source = Source(**Source.TEST_CASES[case])
    with cassette.replaying(fixture_path("marion_sa_gov_au", case)):
        rows = list(
            source.preprocess(source.parse(source.retrieve(source), source), source)
        )

    assert (D(2026, 1, 2), WASTE) in rows
    assert (D(2026, 1, 2), ORGANICS) in rows
    assert sum(label == WASTE for _, label in rows) == 53
    assert not any(day == D(2026, 1, 1) for day, _ in rows)


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


def test_tamax_szczekociny_retains_wrapped_month_rows_and_seasonal_bio():
    from waste_collection_schedule.source.tamax_szczekociny_pl import Source

    response = _recorded_pdf_response(
        "tamax_szczekociny_pl", "Rokitno, Ołudza, Wólka Ołudzka, Grabiec"
    )
    with freeze_time("2026-10-31"):
        rows = set(Source.preprocess(Source.parse(response)))
    assert len(rows) == 49
    for day in (3, 17, 30):
        assert (D(2026, 4, day), "komunalne") in rows
    assert (D(2026, 4, 3), "segregowane") in rows
    assert (D(2026, 4, 11), "biodegradowalne") in rows
    assert (D(2026, 4, 20), "biodegradowalne") in rows
    assert not any(
        d.month in (1, 3, 11) and label == "biodegradowalne" for d, label in rows
    )
    assert (D(2026, 12, 7), "biodegradowalne") in rows


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

    def test_an_unknown_code_is_kept_verbatim(self):
        # 2 Jan 2026 is a Friday; "XY" is not in the legend.
        records = self.parser()._grid_records(["1 DO\n2 FR XY\n"], 2026)
        assert records == [(D(2026, 1, 2), "XY")]

    def test_more_blocks_than_months_fails_loudly(self):
        # Jan, Feb and Mar 2026 blocks on a page covering two months.
        page = "1 DO P\n1 SO P\n2 MO P\n1 SO P\n"
        with pytest.raises(ResponseShapeError):
            self.parser()._grid_records([page], 2026)

    def test_codes_or_labels_are_required(self):
        with pytest.raises(ValueError):
            DayGridCalendarParser(labels=[])


class TestYearlyLinksNamesAndLookback:
    HTML = """
        <a href="/download/ameno-2025-uff-1">Ameno 2025 (UFF.)</a>
        <a href="/download/ameno-2026-uff-2">Ameno 2026 (UFF.)</a>
        <a href="/download/arona-zona-c-2026-uff-3">Arona (zona C) 2026 (UFF.)</a>
    """

    @freeze_time("2027-01-15")
    def test_link_name_drops_the_year_and_lookback_keeps_last_year(self):
        pick = retrievers.yearly_links(
            r"/download/[^/]*-(20\d\d)-uff-",
            argument="municipality",
            link_name=lambda text: text.split(" 20")[0],
            lookback=1,
        )
        assert pick(_page(self.HTML), municipality="ameno") == [
            "https://example.org/download/ameno-2026-uff-2"
        ]
        assert pick(_page(self.HTML), municipality="Arona zona C") == [
            "https://example.org/download/arona-zona-c-2026-uff-3"
        ]


def test_tamax_imielno_matches_every_village_across_both_tables_and_preserves_holidays():
    from waste_collection_schedule.source.tamax_imielno_pl import _AREAS, Source

    response = _recorded_pdf_response("tamax_imielno_pl", "Imielno")
    parsed = Source.parse(response)
    with freeze_time("2026-10-31"):
        outputs = {v: set(Source.preprocess(parsed, Source(area=v))) for v in _AREAS}
    assert all(len(rows) == 28 for rows in outputs.values())
    assert (D(2026, 1, 5), "Zmieszane i bio") in outputs["Borszowice"]
    assert (D(2026, 6, 6), "Zmieszane i bio") in outputs["Borszowice"]
    assert (D(2026, 12, 29), "Zmieszane i bio") in outputs["Imielno"]
    assert (D(2026, 5, 9), "Segregowane") in outputs["Imielno"]
    assert (D(2026, 5, 8), "Segregowane") in outputs["Borszowice"]
    assert (D(2026, 12, 10), "Zmieszane i bio") in outputs["Opatkowice Murowane"]
    assert (D(2026, 11, 30), "Wielkogabarytowe") in outputs["Karczunek"]
    with freeze_time("2027-01-01"), pytest.raises(ValueError, match="current year"):
        Source.preprocess(parsed, Source(area="Imielno"))


class TestPdfMonthBlocks:
    LABELS: ClassVar[dict] = {"SECCO": 1, "UMIDO": 1, "VERDE": 1}

    @staticmethod
    def month(page, heading_x, name, year, month, y_top=500.0, pitch=20.0):
        """Rows of one month block: heading, then days 1-15 and 16-end in two columns."""
        names = ("lun", "Mar", "MER", "Giov", "Ven", "Sab", "DOM")
        rows = [(heading_x, y_top + 30, name)]
        last = (D(year + month // 12, month % 12 + 1, 1) - D(year, month, 1)).days
        for day in range(1, last + 1):
            column, line = divmod(day - 1, 15)
            x = heading_x + column * 110
            y = y_top - line * pitch
            weekday = D(year, month, day).weekday()
            label = {0: "SECCO", 3: "UMIDO - VERDE*"}.get(weekday, "")
            rows.append((x, y, f"{day}"))
            rows.append((x + 12, y, f"{names[weekday]} {label}".strip()))
        return rows

    def build(self, *pages):
        out = []
        for page, words in enumerate(pages):
            by_y: dict[float, list] = {}
            for x, y, text in words:
                by_y.setdefault(y, []).append(PdfWord(text, x, x + 6 * len(text)))
            out += [
                PdfRow(page, y, tuple(sorted(w, key=lambda w: w.x0)))
                for y, w in by_y.items()
            ]
        return out

    @freeze_time("2026-10-11")
    def test_dates_a_march_to_february_leaflet_by_its_weekdays(self):
        cover = [(50, 500, "Raccolta differenziata 2026")]
        page1 = [
            *self.month(1, 30, "Dicembre", 2026, 12),
            # A drop cap printed apart from the rest of the heading.
            (300, 530, "G"),
            (307, 530, "ennaio 2027"),
            *self.month(1, 300, "x", 2027, 1)[1:],
        ]
        found = set(
            preprocessors.PdfMonthBlocks(labels=self.LABELS)(self.build(cover, page1))
        )
        assert (D(2026, 12, 7), "SECCO") in found
        assert (D(2026, 12, 3), "VERDE") in found
        assert (D(2027, 1, 4), "SECCO") in found
        assert (D(2027, 1, 7), "UMIDO") in found
        assert all(date.weekday() in (0, 3) for date, _ in found)

    @freeze_time("2026-10-11")
    def test_a_month_misread_from_the_layout_fails_loudly(self):
        # December's days printed under a "Novembre" heading: weekdays don't fit.
        page = [(30, 530, "Novembre"), *self.month(0, 30, "x", 2026, 12)[1:]]
        with pytest.raises(ResponseShapeError):
            list(preprocessors.PdfMonthBlocks(labels=self.LABELS)(self.build(page)))

    @freeze_time("2026-10-11")
    def test_any_order_reads_a_fold_out_sheet_but_rejects_repeats(self):
        # A fold-out sheet printing October-December before January-March.
        page1 = [
            *self.month(0, 30, "Ottobre", 2026, 10),
            *self.month(0, 300, "Gennaio", 2026, 1),
        ]
        with pytest.raises(ResponseShapeError, match="out of order"):
            list(preprocessors.PdfMonthBlocks(labels=self.LABELS)(self.build(page1)))
        found = set(
            preprocessors.PdfMonthBlocks(labels=self.LABELS, any_order=True)(
                self.build(page1)
            )
        )
        assert (D(2026, 10, 5), "SECCO") in found
        assert (D(2026, 1, 5), "SECCO") in found
        twice = [*page1, *self.month(0, 570, "Ottobre", 2026, 10)]
        with pytest.raises(ResponseShapeError, match="repeated"):
            list(
                preprocessors.PdfMonthBlocks(labels=self.LABELS, any_order=True)(
                    self.build(twice)
                )
            )

    def test_day_cells_without_a_heading_fail_loudly(self):
        page = self.month(0, 30, "x", 2026, 12)[1:]
        with pytest.raises(ResponseShapeError):
            list(preprocessors.PdfMonthBlocks(labels=self.LABELS)(self.build(page)))


_EAST_LINDSEY_FIXTURE = (
    Path(__file__).parent / "fixtures/e_lindsey_gov_uk/13_firbeck_avenue_skegness.json"
)


def test_icon_calendar_matches_resized_legend_items_and_rejects_unknown_or_ambiguous_images():
    from PIL import Image
    from waste_collection_schedule.service.PdfIconCalendar import (
        _thumbnail,
        match_image,
    )

    red = _thumbnail(Image.new("RGB", (60, 80), "red"))
    blue = _thumbnail(Image.new("RGB", (60, 80), "blue"))
    smaller_blue = _thumbnail(Image.new("RGB", (15, 20), "blue"))
    assert match_image(smaller_blue, {"paper": blue, "garbage": red}) == "paper"
    with pytest.raises(ValueError, match="Unrecognised"):
        match_image(
            _thumbnail(Image.new("RGB", (60, 80), "green")),
            {"paper": blue, "garbage": red},
        )
    with pytest.raises(ValueError, match="ambiguous"):
        match_image(blue, {"paper": blue, "garbage": blue})


def test_icon_calendar_cache_is_bounded_to_one_response_and_returns_copies(monkeypatch):
    from waste_collection_schedule.service.PdfIconCalendar import IconMonthGridParser

    parser = IconMonthGridParser(page=0, legend={})
    calls = []

    def parse(content):
        calls.append(content)
        return ((D(2026, 7, 4), "Paper"),)

    monkeypatch.setattr(parser, "_parse", parse)
    first = parser(SimpleNamespace(content=b"one"))
    first.clear()
    assert parser(SimpleNamespace(content=b"one")) == [(D(2026, 7, 4), "Paper")]
    parser(SimpleNamespace(content=b"two"))
    parser(SimpleNamespace(content=b"one"))
    assert calls == [b"one", b"two", b"one"]


def test_icon_calendar_selects_the_printed_holiday_replacement_and_requires_complete_weeks():
    from waste_collection_schedule.service.PdfIconCalendar import CollectionWeekday

    source = SimpleNamespace(params={"day": "Friday"})
    rows = [
        (D(2026, 4, 1), "Paper"),
        (D(2026, 4, 2), "Paper"),
        (D(2026, 4, 4), "Paper"),
    ]
    select = CollectionWeekday()
    with freeze_time("2026-04-01"):
        result = list(select(rows, source))
        assert [r["date"] for r in result] == [D(2026, 4, 4)]
        with pytest.raises(ValueError, match="Incomplete printed collection week"):
            list(select(rows[:1] + rows[2:], source))
        with pytest.raises(ValueError, match="week is missing"):
            list(
                select(
                    rows
                    + [
                        (day + datetime.timedelta(days=14), label)
                        for day, label in rows
                    ],
                    source,
                )
            )


def test_petawawa_published_icons_preserve_new_year_and_good_friday_shifts():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule import waste_types as wt
    from waste_collection_schedule.source.ovwrc_com import Source

    with freeze_time("2026-10-30"):
        case = "Petawawa Friday route"
        with cassette.replaying(fixture_path("ovwrc_com", case)):
            rows = Source(**Source.TEST_CASES[case]).fetch()
    pairs = {(r.date, r.waste_type.id) for r in rows}
    assert (D(2026, 1, 3), wt.GENERAL_WASTE.id) in pairs
    assert any(day == D(2026, 7, 4) for day, _ in pairs)
    assert (D(2027, 3, 27), wt.GENERAL_WASTE.id) in pairs
    assert not any(day in (D(2026, 1, 2), D(2027, 3, 26)) for day, _ in pairs)
    trees = [r for r in rows if r.waste_type.id == wt.GARDEN_WASTE.id]
    assert len(trees) == 2
    assert all(r.description == "Natural Christmas trees only" for r in trees)


def test_petawawa_does_not_select_a_future_calendar_before_it_starts():
    import re

    from waste_collection_schedule.source.ovwrc_com import _current_calendar

    matches = [re.search(r"(20\d{2})", year) for year in ("2025", "2026", "2027")]
    with freeze_time("2026-12-20"):
        assert _current_calendar(matches)[1] == "2026"
    with freeze_time("2027-01-02"):
        assert _current_calendar(matches)[1] == "2027"


def _east_lindsey_pdf():
    recording = json.loads(_EAST_LINDSEY_FIXTURE.read_text(encoding="utf-8"))
    return SimpleNamespace(
        content=base64.b64decode(recording["interactions"][2]["content_b64"])
    )


def test_east_lindsey_reads_the_published_winter_dates_and_printed_years():
    # Use the real public Tuesday A PDF, even when the system year changes.
    with freeze_time("2028-01-01"):
        dates = GardenCalendarParser()(_east_lindsey_pdf())
    assert len(dates) == 21
    assert dates[0] == D(2026, 3, 31)
    assert min(day for day in dates if day > D(2026, 10, 13)) == D(2026, 10, 27)
    assert [day for day in dates if day >= D(2026, 11, 1)] == [
        D(2026, 11, 10),
        D(2026, 12, 8),
        D(2027, 1, 19),
        D(2027, 2, 16),
        D(2027, 3, 16),
    ]
    assert D(2026, 11, 24) not in dates  # no projected fortnightly winter date
    assert D(2027, 1, 5) not in dates  # extended Christmas gap in the PDF


def test_east_lindsey_replays_the_complete_lookup_and_calendar_download():
    import cassette
    from waste_collection_schedule.source.e_lindsey_gov_uk import Source

    with cassette.replaying(str(_EAST_LINDSEY_FIXTURE)):
        entries = Source(uprn="100030786099").fetch()
    first = sorted(
        (entry for entry in entries if entry.type != "Garden Waste"),
        key=lambda entry: entry.date,
    )
    assert [(entry.date, entry.type) for entry in first] == [
        (D(2026, 10, 14), "General Waste"),
        (D(2026, 10, 21), "Paper & Cardboard"),
        (D(2026, 11, 4), "Recycling"),
    ]
    garden = [entry for entry in entries if entry.type == "Garden Waste"]
    assert len(garden) == 21
    assert max(entry.date for entry in garden) == D(2027, 3, 16)


def test_east_lindsey_reads_food_waste_from_wastenextfood(tmp_path):
    """``wastenextfood`` is the next food-waste collection (port of #8024).

    The recorded cassette predates that field, so this copies it and adds a
    ``wastenextfood`` value in the same shape as the other ``wastenext*`` dates.
    """
    recording = json.loads(_EAST_LINDSEY_FIXTURE.read_text(encoding="utf-8"))
    html = base64.b64decode(recording["interactions"][1]["content_b64"]).decode()
    match = re.search(r'([A-Z0-9_]+FormData\s*=\s*")([^"]+)(")', html)
    assert match is not None
    payload = json.loads(base64.b64decode(match.group(2)))
    payload["RESULTS_1"]["FIELD12"]["result"][0]["wastenextfood"] = (
        "Wednesday 28th October 2026"
    )
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    html = html[: match.start(2)] + encoded + html[match.end(2) :]
    recording["interactions"][1]["content_b64"] = base64.b64encode(
        html.encode()
    ).decode()
    path = tmp_path / "with_food.json"
    path.write_text(json.dumps(recording), encoding="utf-8")

    import cassette
    from waste_collection_schedule.source.e_lindsey_gov_uk import Source

    with cassette.replaying(str(path)):
        entries = Source(uprn="100030786099").fetch()
    non_garden = sorted(
        (entry for entry in entries if entry.type != "Garden Waste"),
        key=lambda entry: entry.date,
    )
    assert [(entry.date, entry.type, entry.icon) for entry in non_garden] == [
        (D(2026, 10, 14), "General Waste", "mdi:trash-can"),
        (D(2026, 10, 21), "Paper & Cardboard", "mdi:package-variant"),
        (D(2026, 10, 28), "Food Waste", "mdi:food-apple"),
        (D(2026, 11, 4), "Recycling", "mdi:recycle"),
    ]


def test_east_lindsey_without_a_garden_subscription_does_not_fetch_a_pdf():
    for pdf_id in (None, "", "null"):
        payload = {"RESULTS_1": {"FIELD12": {"result": [{"greenpdfid": pdf_id}]}}}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        response = SimpleNamespace(text=f'var XFormData = "{encoded}";')
        assert garden_calendar_urls(None, response) == []


def test_tamax_lelow_reads_iso_month_colours_ash_and_the_dated_bulky_notice():
    from waste_collection_schedule.source.tamax_lelow_pl import Source

    response = _recorded_pdf_response(
        "tamax_lelow_pl", "Lelów (bez ul. Spacerowej), Lgota Błotna, Lgota Gawronna"
    )
    with freeze_time("2026-10-31"):
        rows = {(r["date"], r["type"]) for r in Source.parse(response)}
    assert len(rows) == 51
    assert (D(2026, 1, 12), "Popiół") in rows
    assert (D(2026, 1, 20), "Zmieszane") in rows
    assert (D(2026, 1, 20), "Segregowane") in rows
    assert (D(2026, 1, 20), "Bio") not in rows
    assert (D(2026, 4, 7), "Bio") in rows
    assert (D(2026, 7, 30), "Wielkogabarytowe") in rows
    with freeze_time("2027-01-01"), pytest.raises(ValueError, match="this year"):
        Source.parse(response)


def test_iso_pdf_month_headings_must_agree_with_the_printed_year(monkeypatch):
    from waste_collection_schedule.service import MarkedPdfCalendar
    from waste_collection_schedule.source.tamax_lelow_pl import Source

    response = _recorded_pdf_response(
        "tamax_lelow_pl", "Lelów (bez ul. Spacerowej), Lgota Błotna, Lgota Gawronna"
    )
    normal = MarkedPdfCalendar._normal
    monkeypatch.setattr(
        MarkedPdfCalendar,
        "_normal",
        lambda value: "2027-02" if value.strip() == "2026-02" else normal(value),
    )
    with (
        freeze_time("2026-10-31"),
        pytest.raises(ValueError, match="headings disagree"),
    ):
        Source.parse(response)


def test_fan_out_can_return_the_prepared_response_first():
    prepared = SimpleNamespace(name="lookup")
    retrieve = retrievers.FanOutRetriever(
        prepare=lambda source: prepared,
        targets=lambda source, context: ["a", "b"],
        fetch=lambda source, target, context: target,
        include_prepared=True,
    )
    assert retrieve(None) == [prepared, "a", "b"]


def test_east_lindsey_calendar_http_error_is_not_hidden_by_a_season_anchor(tmp_path):
    import cassette
    from waste_collection_schedule.source.e_lindsey_gov_uk import Source

    recording = json.loads(_EAST_LINDSEY_FIXTURE.read_text(encoding="utf-8"))
    recording["interactions"][2]["status"] = 503
    path = tmp_path / "unavailable_calendar.json"
    path.write_text(json.dumps(recording), encoding="utf-8")
    with cassette.replaying(str(path)), pytest.raises(OSError, match="503"):
        Source(uprn="100030786099").fetch()


@pytest.mark.parametrize("change", ["headers", "legend", "highlight", "no_dates"])
def test_east_lindsey_changed_calendar_layout_fails_loudly(monkeypatch, change):
    layout = parsers.PdfWordLayoutParser(include_form_text=True)(_east_lindsey_pdf())[0]
    if change == "headers":
        layout.lines[:] = [line for line in layout.lines if "2026" not in line.text]
    elif change == "legend":
        layout.lines[:] = [line for line in layout.lines if line.text != "Green Waste"]
    else:
        matches = [v for v in layout.vectors if v.fill_color == (0.573, 0.816, 0.314)]
        if change == "highlight":
            marker = next(v for v in matches if v.x1 - v.x0 > 10)
            layout.words[:] = [
                w
                for w in layout.words
                if not (marker.x0 <= w.x <= marker.x1 and marker.y0 <= w.y <= marker.y1)
            ]
        else:
            layout.vectors[:] = [
                v for v in layout.vectors if v not in matches or v.x1 - v.x0 < 10
            ]
    monkeypatch.setattr(parsers.PdfWordLayoutParser, "__call__", lambda *args: [layout])
    with pytest.raises(ResponseShapeError):
        GardenCalendarParser()(_east_lindsey_pdf())


def _dunanett_recording(case: str = "pusztaszabolcs") -> dict[str, Any]:
    path = Path(__file__).parent / f"fixtures/dunanett_hu/{case}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _dunanett_pdf() -> SimpleNamespace:
    recorded = _dunanett_recording()["interactions"][1]
    return SimpleNamespace(
        content=base64.b64decode(recorded["content_b64"]),
        url=recorded["final_url"],
        text=base64.b64decode(recorded["content_b64"]).decode(
            "utf-8", errors="replace"
        ),
    )


@pytest.mark.parametrize(
    "case,town,weekday,garden",
    [
        (
            "pusztaszabolcs",
            "Pusztaszabolcs",
            3,
            [
                [9, 23],
                [],
                [6, 20],
                [3, 17],
                [1, 15, 29],
                [12, 26],
                [10, 24],
                [7, 21],
                [4, 18],
                [2, 16, 30],
                [13, 27],
                [],
            ],
        ),
        (
            "r_calm_s",
            "Rácalmás",
            1,
            [[8, 23], [], [], [30], [28], [25], [23], [20], [17], [15], [12], []],
        ),
    ],
)
def test_dunanett_complete_annual_dates_and_tree_descriptions(
    case: str, town: str, weekday: int, garden: list[list[int]]
) -> None:
    import cassette
    from waste_collection_schedule.source.dunanett_hu import Source

    path = Path(__file__).parent / f"fixtures/dunanett_hu/{case}.json"
    with cassette.replaying(str(path)):
        entries = Source(municipality=town).fetch()
    # Transcribed from the official annual PDFs, not inferred from a cadence.
    recycling = [
        [16, 30],
        [13, 27],
        [13, 27],
        [10, 24],
        [8, 22],
        [5, 19],
        [3, 17, 31],
        [14, 28],
        [11, 25],
        [9, 23],
        [6, 20],
        [4, 18],
    ]
    expected = {
        (D(2026, month, day), label)
        for label, months in (("Recycling", recycling), ("Garden Waste", garden))
        for month, days in enumerate(months, 1)
        for day in days
    }
    expected |= {
        (day, "General Waste")
        for offset in range(365)
        if (day := D(2026, 1, 1) + datetime.timedelta(days=offset)).weekday() == weekday
    }
    assert len(entries) == len(expected)
    assert {(entry.date, entry.type) for entry in entries} == expected
    trees = [e for e in entries if e.type == "Garden Waste" and e.date.month == 1]
    assert len(trees) == 2
    assert all(e.description and "Christmas trees only" in e.description for e in trees)
    assert all(e.description is None for e in entries if e not in trees)


@pytest.mark.parametrize(
    "change", ["town", "year", "row", "cell", "invalid_date", "weekly", "months"]
)
def test_hu_calendar_strict_rejects_wrong_or_incomplete_documents(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    from pypdf import PdfReader
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_pdf()
    page = PdfReader(BytesIO(response.content)).pages[0]
    layout = page.extract_text(extraction_mode="layout")
    plain = page.extract_text()
    if change == "town":
        layout = layout.replace("Pusztaszabolcs", "Other town")
    elif change == "year":
        response.url = response.url.replace("2026.pdf", "2027.pdf")
    elif change in ("row", "cell", "invalid_date"):
        row = next(line for line in layout.splitlines() if "16,30" in line)
        replacement = {
            "row": "",
            "cell": row.replace("16,30", ""),
            "invalid_date": row.replace("13,27", "31,32", 1),
        }[change]
        layout = layout.replace(row, replacement)
    elif change == "weekly":
        layout = layout.replace("Csütörtök", "unknown")
        plain = plain.replace("Csütörtök", "unknown")
    else:
        layout = layout.replace("Február", "unknown")
    monkeypatch.setattr(
        "pypdf.PdfReader",
        lambda _: SimpleNamespace(
            pages=[
                SimpleNamespace(
                    extract_text=lambda **kwargs: layout if kwargs else plain
                )
            ]
        ),
    )
    with pytest.raises(ResponseShapeError):
        Source.parse.parser([response], Source(municipality="Pusztaszabolcs"))


def test_hu_calendar_tree_restriction_is_detected_and_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pypdf import PdfReader
    from waste_collection_schedule.service import HuWasteCalendar as hu
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_pdf()
    types = {"szelektív": "szelektív", "zöldhulladék": "zöldhulladék"}
    default = hu.CalendarParser(types=types)(response)
    assert (D(2026, 1, 9), "zöldhulladék") in default
    assert not any(label == hu.CHRISTMAS_TREES for _, label in default)
    page = PdfReader(BytesIO(response.content)).pages[0]
    # Remove the actual upstream restriction from both extraction modes.
    layout = re.sub(r"A januári[^\n]+", "", page.extract_text(extraction_mode="layout"))
    plain = re.sub(r"A januári.*?szállítjuk el\.", "", page.extract_text(), flags=re.S)
    monkeypatch.setattr(
        "pypdf.PdfReader",
        lambda _: SimpleNamespace(
            pages=[
                SimpleNamespace(
                    extract_text=lambda **kwargs: layout if kwargs else plain
                )
            ]
        ),
    )
    rows = Source.parse.parser([response], Source(municipality="Pusztaszabolcs"))
    assert (D(2026, 1, 9), "zöldhulladék") in rows
    assert not any(label == hu.CHRISTMAS_TREES for _, label in rows)


@freeze_time("2026-10-15")
def test_dunanett_discovery_uses_latest_correction_and_all_published_future_years() -> (
    None
):
    from waste_collection_schedule.source.dunanett_hu import _calendar_urls

    record = json.loads(
        base64.b64decode(_dunanett_recording()["interactions"][0]["content_b64"])
    )[0]
    corrected = {
        **record,
        "date": "2026-02-01T12:00:00",
        "source_url": record["source_url"].replace("2026.pdf", "2026-javitott.pdf"),
        "title": {"rendered": record["title"]["rendered"] + "-javitott"},
    }
    future = json.loads(json.dumps(record).replace("2026", "2027"))
    stale = json.loads(json.dumps(record).replace("2026", "2025"))
    other = json.loads(json.dumps(record).replace("Pusztaszabolcs", "OtherTown"))
    response = SimpleNamespace(
        json=lambda: [future, record, stale, corrected, other],
        headers={"X-WP-TotalPages": "1"},
    )
    assert _calendar_urls(response, municipality="Pusztaszabolcs") == [
        corrected["source_url"],
        future["source_url"],
    ]


@freeze_time("2027-01-01")
def test_dunanett_discovery_never_reuses_an_expired_calendar() -> None:
    from waste_collection_schedule.source.dunanett_hu import _calendar_urls

    records = json.loads(
        base64.b64decode(_dunanett_recording()["interactions"][0]["content_b64"])
    )
    response = SimpleNamespace(json=lambda: records, headers={"X-WP-TotalPages": "1"})
    with pytest.raises(ResponseShapeError, match="no current annual calendar"):
        _calendar_urls(response, municipality="Pusztaszabolcs")


@pytest.mark.parametrize(
    "change", ["pagination", "headers", "shape", "year", "host", "date"]
)
@freeze_time("2026-10-15")
def test_dunanett_discovery_rejects_malformed_or_truncated_media(change: str) -> None:
    from waste_collection_schedule.source.dunanett_hu import _calendar_urls

    records = json.loads(
        base64.b64decode(_dunanett_recording()["interactions"][0]["content_b64"])
    )
    headers = {"X-WP-TotalPages": "1"}
    if change == "pagination":
        headers["X-WP-TotalPages"] = "2"
    elif change == "headers":
        headers = {}
    elif change == "shape":
        del records[0]["title"]
    elif change == "year":
        records[0]["title"]["rendered"] = records[0]["title"]["rendered"].replace(
            "2026", "2027"
        )
    elif change == "host":
        records[0]["source_url"] = records[0]["source_url"].replace(
            "pusztaszabolcs.hu", "other.hu"
        )
    else:
        records[0]["date"] = "not a timestamp"
    response = SimpleNamespace(json=lambda: records, headers=headers)
    with pytest.raises(ResponseShapeError):
        _calendar_urls(response, municipality="Pusztaszabolcs")


def test_dunanett_unsupported_municipality_has_argument_suggestions() -> None:
    from waste_collection_schedule.source.dunanett_hu import Source

    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as error:
        Source(municipality="Mezőfalva").fetch()
    assert error.value.argument == "municipality"
    assert error.value.suggestions == [
        "Pusztaszabolcs",
        "Rácalmás",
        "Perkáta",
        "Nagyvenyim",
        "Dunaföldvár",
    ]


@pytest.mark.parametrize("interaction", [0, 1], ids=["media_lookup", "calendar_pdf"])
def test_dunanett_http_failures_propagate(tmp_path: Path, interaction: int) -> None:
    import cassette
    from waste_collection_schedule.source.dunanett_hu import Source

    recording = _dunanett_recording()
    recording["interactions"][interaction]["status"] = 503
    path = tmp_path / "unavailable.json"
    path.write_text(json.dumps(recording), encoding="utf-8")
    with cassette.replaying(str(path)), pytest.raises(OSError, match="503"):
        Source(municipality="Pusztaszabolcs").fetch()


@pytest.mark.parametrize("change", ["empty_row", "duplicate_row", "next_year"])
def test_hu_calendar_empty_rows_duplicates_and_year_boundaries(
    monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    from pypdf import PdfReader
    from waste_collection_schedule.service import HuWasteCalendar as hu
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_pdf()
    page = PdfReader(BytesIO(response.content)).pages[0]
    layout = page.extract_text(extraction_mode="layout")
    plain = page.extract_text()
    row = next(
        line
        for line in layout.splitlines()
        if "zöldhulladék" in line and "9,23" in line
    )
    if change == "empty_row":
        # A complete all-dash row is different from a missing or unreadable row.
        empty_row = re.sub(r"\d[\d,]*", lambda m: "-".ljust(len(m[0])), row)
        layout = layout.replace(row, empty_row)
    elif change == "duplicate_row":
        layout = layout.replace(row, f"{row}\n{row}")
    else:
        layout, plain = layout.replace("2026", "2027"), plain.replace("2026", "2027")
        response.url = response.url.replace("2026", "2027")
    monkeypatch.setattr(
        "pypdf.PdfReader",
        lambda _: SimpleNamespace(
            pages=[SimpleNamespace(extract_text=lambda **kw: layout if kw else plain)]
        ),
    )
    rows = Source.parse.parser([response], Source(municipality="Pusztaszabolcs"))
    assert len(rows) == len(set(rows))
    if change == "empty_row":
        assert {label for _, label in rows} == {hu.GENERAL, "szelektív"}
    elif change == "duplicate_row":
        assert len(rows) == 100
    else:
        assert {when.year for when, _ in rows} == {2027}
        weekly = [when for when, label in rows if label == hu.GENERAL]
        assert weekly[0] == D(2027, 1, 7)
        assert weekly[-1] == D(2027, 12, 30)


_DUNANETT_NEW_TOWNS = [
    ("perk_ta", "Perkáta", 3),
    ("nagyvenyim", "Nagyvenyim", 0),
    ("dunaf_ldv_r", "Dunaföldvár", None),
]


@pytest.mark.parametrize("case,town,weekday", _DUNANETT_NEW_TOWNS)
@freeze_time("2026-10-16")
def test_dunanett_new_towns_complete_published_dates(
    case: str, town: str, weekday: int | None
) -> None:
    import cassette
    from waste_collection_schedule.source.dunanett_hu import Source

    # Independently transcribed from the official PDF, article and DOCX.
    recycling, garden = {
        "Perkáta": (
            [
                [9, 23],
                [6, 20],
                [6, 20],
                [3, 17],
                [1, 15, 29],
                [12, 26],
                [10, 24],
                [7, 21],
                [4, 18],
                [2, 16, 30],
                [13, 27],
                [11, 25],
            ],
            [[12, 29], [], [], [6], [4], [1], [27], [24], [21], [19], [16], []],
        ),
        "Nagyvenyim": (
            [
                [14, 28],
                [11, 25],
                [11, 25],
                [8, 22],
                [6, 20],
                [3, 17],
                [1, 15, 29],
                [12, 26],
                [9, 23],
                [7, 21],
                [4, 18],
                [2, 16, 30],
            ],
            [[9, 22], [], [], [16], [14], [11], [9], [6], [3], [1], [26], []],
        ),
        "Dunaföldvár": (
            [
                [15, 29],
                [12, 26],
                [12, 26],
                [9, 23],
                [7, 21],
                [4, 18],
                [2, 16, 30],
                [13, 27],
                [10, 24],
                [8, 22],
                [5, 19],
                [3, 17, 31],
            ],
            [
                [10, 24],
                [],
                [12, 26],
                [9, 23],
                [7, 21],
                [4, 18],
                [2, 16, 30],
                [13, 27],
                [10, 24],
                [8, 22],
                [5, 19],
                [],
            ],
        ),
    }[town]
    expected = {
        (D(2026, month, day), label)
        for label, months in (("Recycling", recycling), ("Garden Waste", garden))
        for month, days in enumerate(months, 1)
        for day in days
    }
    if weekday is not None:
        expected |= {
            (day, "General Waste")
            for offset in range(365)
            if (day := D(2026, 1, 1) + datetime.timedelta(days=offset)).weekday()
            == weekday
        }
    path = Path(__file__).parent / f"fixtures/dunanett_hu/{case}.json"
    with cassette.replaying(str(path)):
        entries = Source(municipality=town).fetch()
    assert len(entries) == len(expected)
    assert {(entry.date, entry.type) for entry in entries} == expected
    for entry in entries:
        tree = entry.type == "Garden Waste" and entry.date.month == 1
        assert bool(entry.description) == tree
        if tree:
            assert "Christmas trees only" in entry.description


def _dunanett_response(case: str, interaction: int = -1) -> SimpleNamespace:
    recorded = _dunanett_recording(case)["interactions"][interaction]
    content = base64.b64decode(recorded["content_b64"])
    return SimpleNamespace(
        content=content,
        text=content.decode("utf-8", errors="replace"),
        url=recorded["final_url"],
        status_code=recorded["status"],
    )


@pytest.mark.parametrize("case,town,weekday", _DUNANETT_NEW_TOWNS)
@freeze_time("2027-01-01")
def test_dunanett_new_indices_reject_expired_calendars(
    case: str, town: str, weekday: int | None
) -> None:
    from waste_collection_schedule.source.dunanett_hu import _annual_targets

    with pytest.raises(ResponseShapeError, match="no current annual calendar"):
        _annual_targets(_dunanett_response(case, 0), municipality=town)


def _annual_index(town: str, years: list[int]) -> SimpleNamespace:
    """Small real-shaped indices, with distinct links even within one year."""
    if town == "Perkáta":
        links = "".join(
            f'<a href="https://cdn.example/{i}.pdf">2431_Perkáta_Hulladéknaptár{year}.pdf</a>'
            for i, year in enumerate(years)
        )
        text = f'<custom-page-description description="{escape(links, quote=True)}"></custom-page-description>'
    elif town == "Nagyvenyim":
        text = (
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(
                f"<url><loc>https://nagyvenyim.hu/{year}/01/{i + 1:02}/tajekoztato-a-hulladekszallitas-{year}-evi-rendjerol/</loc></url>"
                for i, year in enumerate(years)
            )
            + "</urlset>"
        )
    else:
        text = (
            '<div class="list">'
            + "".join(
                f'<div class="item"><a href="/{i}/" title="Szelektív és zöld hulladékgyűjtés {year}. évben"></a><div class="name">Szelektív és zöld hulladékgyűjtés {year}. évben</div></div>'
                for i, year in enumerate(years)
            )
            + "</div>"
        )
    return SimpleNamespace(
        text=text,
        content=text.encode(),
        url=f"https://{'dunafoldvar.hu' if town == 'Dunaföldvár' else 'example.org'}/",
    )


@pytest.mark.parametrize("case,town,weekday", _DUNANETT_NEW_TOWNS)
@freeze_time("2026-10-16")
def test_dunanett_indices_keep_future_years_and_reject_competing_links(
    case: str, town: str, weekday: int | None
) -> None:
    from waste_collection_schedule.source.dunanett_hu import _annual_targets

    targets = _annual_targets(
        _annual_index(town, [2027, 2025, 2026]), municipality=town
    )
    assert [year for _, year in targets] == [2026, 2027]
    with pytest.raises(ResponseShapeError, match="ambiguous"):
        _annual_targets(_annual_index(town, [2026, 2026]), municipality=town)


@pytest.mark.parametrize("case,town,weekday", _DUNANETT_NEW_TOWNS)
@freeze_time("2026-10-16")
def test_dunanett_download_year_must_match_published_link(
    case: str, town: str, weekday: int | None
) -> None:
    from waste_collection_schedule.source.dunanett_hu import Source

    # The current document cannot stand in for the next year's publication,
    # even when its URL is a UUID or a yearless file overwritten in place.
    index = _annual_index(town, [2026, 2027])
    with pytest.raises(ResponseShapeError, match="heading year disagrees"):
        Source.parse(
            [index, _dunanett_response(case), _dunanett_response(case)],
            Source(municipality=town),
        )


@pytest.mark.parametrize(
    "change",
    ["heading", "city", "label", "month", "cell", "date", "row", "weekly", "areas"],
)
def test_hu_html_calendar_rejects_incomplete_or_changed_rules(change: str) -> None:
    from bs4 import BeautifulSoup
    from waste_collection_schedule.service import HuWasteCalendar as hu
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_response("nagyvenyim")
    soup = BeautifulSoup(response.text, "html.parser")
    if change == "heading":
        soup.h1.string = "Other title"
    elif change == "city":
        response.text = response.text.replace("Nagyvenyim", "OtherTown")
    elif change == "label":
        for p in soup.select(".entry-content p"):
            if (
                "Biológiailag lebomló hulladék elszállításának időpontjai"
                in p.get_text()
            ):
                p.decompose()
    elif change in ("month", "cell", "date", "row"):
        rows = soup.select(".entry-content table tr")
        if change == "month":
            rows[0].td.string = "XIII."
        elif change == "cell":
            rows[1].td.decompose()
        elif change == "date":
            rows[1].td.string = "32/33"
        else:
            rows[1].decompose()
    else:
        paragraph = soup.select_one(".entry-content p")
        paragraph.string = paragraph.get_text(" ", strip=True).replace(
            "HÉTFŐI" if change == "areas" else "helyett",
            "KEDDI" if change == "areas" else "and",
        )
    if change != "city":
        response.text = str(soup)
    with pytest.raises(ResponseShapeError):
        hu.MonthTableCalendarParser()(response, Source(municipality="Nagyvenyim"))


@pytest.mark.parametrize("change", ["truncated", "day_row", "date", "heading", "city"])
def test_hu_pdf_month_tables_reject_incomplete_or_invalid_documents(
    monkeypatch, change
):
    from waste_collection_schedule.service import HuWasteCalendar as hu
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_response("dunaf_ldv_r")
    rows = parsers.PdfTableParser(char_margin=1)(response)
    last_header = max(
        i
        for i, row in enumerate(rows)
        if "December" in " ".join(word.text for word in row.words)
    )
    if change == "truncated":
        del rows[last_header : last_header + 2]
    elif change == "day_row":
        del rows[last_header + 1]
    elif change == "date":
        row = rows[last_header + 1]
        rows[last_header + 1] = row._replace(
            words=(row.words[0]._replace(text="32."), *row.words[1:])
        )
    else:
        old = "2026" if change == "heading" else "Dunaföldvár"
        rows = [
            row._replace(
                words=tuple(
                    word._replace(text=word.text.replace(old, "unknown"))
                    for word in row.words
                )
            )
            for row in rows
        ]
    monkeypatch.setattr(parsers.PdfTableParser, "__call__", lambda *args: rows)
    with pytest.raises(ResponseShapeError):
        hu.MonthTableCalendarParser(pdf=True)(
            response, Source(municipality="Dunaföldvár")
        )


def test_dunanett_still_supports_the_previous_docx_publication():
    import cassette
    from waste_collection_schedule.source.dunanett_hu import Source

    path = Path(__file__).parent / "fixtures/dunanett_hu/_docx_2026.json"
    with freeze_time("2026-10-16"), cassette.replaying(str(path)):
        entries = Source(municipality="Dunaföldvár").fetch()
    assert len(entries) == 47
    assert sum(entry.type == "Garden Waste" for entry in entries) == 21


@pytest.mark.parametrize("table_index", [0, 1], ids=["recycling", "garden"])
def test_hu_docx_requires_all_months_in_every_table(table_index: int) -> None:
    from xml.etree import ElementTree

    from waste_collection_schedule.service import HuWasteCalendar as hu
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_response("_docx_2026")
    output = BytesIO()
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with (
        ZipFile(BytesIO(response.content)) as original,
        ZipFile(output, "w") as changed,
    ):
        for entry in original.infolist():
            content = original.read(entry.filename)
            if entry.filename == "word/document.xml":
                # Parse only the checked-in fixture to simulate a truncated document.
                root = ElementTree.fromstring(content)  # nosec B314
                table = root.findall(".//w:tbl", ns)[table_index]
                rows = table.findall("w:tr", ns)
                assert len(rows) == 4
                for row in rows[-2:]:
                    table.remove(row)
                content = ElementTree.tostring(root)
            changed.writestr(entry, content)
    response.content = output.getvalue()
    with pytest.raises(ResponseShapeError, match="month columns"):
        hu.MonthTableCalendarParser(docx=True)(
            response, Source(municipality="Dunaföldvár")
        )


def _changed_docx(response: SimpleNamespace, old: str, new: str) -> SimpleNamespace:
    output = BytesIO()
    with (
        ZipFile(BytesIO(response.content)) as original,
        ZipFile(output, "w") as changed,
    ):
        for entry in original.infolist():
            content = original.read(entry.filename)
            if entry.filename == "word/document.xml":
                assert old in content.decode()
                content = content.decode().replace(old, new).encode()
            changed.writestr(entry, content)
    response.content = output.getvalue()
    return response


@pytest.mark.parametrize(
    "change", ["zip", "xml", "city", "heading", "label", "month", "date", "rows"]
)
def test_hu_docx_calendar_rejects_malformed_documents(change: str) -> None:
    from waste_collection_schedule.service import HuWasteCalendar as hu
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_response("_docx_2026")
    if change == "zip":
        response.content = b"PK not a DOCX"
    else:
        old, new = {
            "xml": ("</w:document>", ""),
            "city": ("unaföldvár", "OtherTown"),
            "heading": ("2026", "unknown"),
            "label": ("Szelektív", "Other"),
            "month": ("Február", "OtherMonth"),
            "date": ("15.", "32."),
            "rows": ("w:tr", "w:row"),
        }[change]
        response = _changed_docx(response, old, new)
    with pytest.raises(ResponseShapeError):
        hu.MonthTableCalendarParser(docx=True)(
            response, Source(municipality="Dunaföldvár")
        )


@pytest.mark.parametrize(
    "case,town,docx",
    [("nagyvenyim", "Nagyvenyim", False), ("dunaf_ldv_r", "Dunaföldvár", True)],
)
def test_hu_month_tables_only_label_trees_when_published(
    case: str, town: str, docx: bool
) -> None:
    from waste_collection_schedule.service import HuWasteCalendar as hu
    from waste_collection_schedule.source.dunanett_hu import Source

    response = _dunanett_response("_docx_2026" if docx else case)
    if docx:
        response = _changed_docx(response, "fenyőfákat", "más hulladékot")
    else:
        response.text = response.text.replace(
            "Januárban csak karácsonyfát szállítanak el!", ""
        )
    records = hu.MonthTableCalendarParser(docx=docx)(
        response, Source(municipality=town)
    )
    assert not any(label == hu.CHRISTMAS_TREES for _, label in records)
    assert (
        len(
            [
                when
                for when, label in records
                if when.month == 1 and label == "zöldhulladék"
            ]
        )
        == 2
    )


@pytest.mark.parametrize("change", ["heading", "links"])
def test_dunanett_docx_article_must_match_index_and_have_one_download(
    change: str,
) -> None:
    from waste_collection_schedule.source.dunanett_hu import _document_url

    response = _dunanett_response("dunaf_ldv_r", 1)
    if change == "heading":
        response.text = response.text.replace("2026", "2025")
    else:
        response.text += '<a href="/other.docx">Naptár</a>'
    with pytest.raises(ResponseShapeError):
        _document_url(response, (response.url, 2026))


@pytest.mark.parametrize(
    "case,town,interaction",
    [
        (case, town, interaction)
        for case, town, _ in _DUNANETT_NEW_TOWNS
        for interaction in range(3 if town == "Dunaföldvár" else 2)
    ],
)
def test_dunanett_new_towns_http_errors_propagate(
    tmp_path: Path, case: str, town: str, interaction: int
) -> None:
    import cassette
    from waste_collection_schedule.source.dunanett_hu import Source

    recording = _dunanett_recording(case)
    recording["interactions"][interaction]["status"] = 503
    path = tmp_path / "unavailable.json"
    path.write_text(json.dumps(recording), encoding="utf-8")
    with cassette.replaying(str(path)), pytest.raises(OSError, match="503"):
        Source(municipality=town).fetch()


@pytest.mark.parametrize("interstitials", [0, 1, 3, 4])
def test_ekoland_asks_again_after_the_one_moment_interstitial(
    monkeypatch, interstitials
):
    """The index page sometimes answers with a self-reloading interstitial.

    It is asked again up to three times, 5 s apart; a fourth interstitial is
    given up on and reported as a changed page.
    """
    from waste_collection_schedule.source import ekolandpolska_com_pl

    page = (
        '<a href="/assets/media/harmonogram-wilkolaz-2026.pdf">Wilkołaz</a>'
        '<a href="/assets/media/harmonogram-wilkolaz-2026-wielorodzinne.pdf">x</a>'
    )
    answers = iter(["<title>One moment, please...</title>"] * interstitials + [page])
    requested, slept = [], []

    def get(url, **_):
        requested.append(url)
        return SimpleNamespace(
            text=next(answers), url=url, status_code=200, raise_for_status=lambda: None
        )

    monkeypatch.setattr(retrievers.time, "sleep", slept.append)
    source = SimpleNamespace(
        session=SimpleNamespace(get=get),
        params={"municipality": "Wilkolaz", "street": "Ostrów"},
    )
    prepare = ekolandpolska_com_pl.Source.retrieve.prepare
    pdf = "https://www.ekolandpolska.com.pl/assets/media/harmonogram-wilkolaz-2026.pdf"
    with freeze_time("2026-10-24"):
        if interstitials > 3:
            with pytest.raises(ValueError, match="no link matching"):
                prepare(source)
        else:
            assert prepare(source) == [pdf]
    attempts = min(interstitials, 3) + 1
    assert len(requested) == attempts
    assert slept == [5] * (attempts - 1)


@pytest.mark.parametrize(
    ("args", "argument"),
    [
        ({"city": "Pisz"}, "street"),
        ({"city": "Pisz", "street": "  "}, "street"),
        (
            {"city": "Pisz", "street": "Lipowa", "building": "wielorodzinna"},
            "house_number",
        ),
    ],
)
def test_pisz_requires_the_address_fields_for_the_selected_building(args, argument):
    from waste_collection_schedule.exceptions import SourceArgumentRequired
    from waste_collection_schedule.source.pisz_pl import Source

    source = Source(**args)
    with pytest.raises(SourceArgumentRequired, match=argument):
        list(source.preprocess("", source))


def test_pisz_missing_flat_number_must_not_return_a_partial_calendar():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule.exceptions import SourceArgumentRequired
    from waste_collection_schedule.source.pisz_pl import Source

    case = "Pisz, Lipowa 12 (flats)"
    args = {k: v for k, v in Source.TEST_CASES[case].items() if k != "house_number"}
    with cassette.replaying(fixture_path("pisz_pl", case)):
        with pytest.raises(SourceArgumentRequired, match="house_number"):
            Source(**args).fetch()


def test_tamax_wlodowice_includes_bio_and_ash_on_red_dates_and_single_digit_bulky_day():
    from waste_collection_schedule.source.tamax_wlodowice_pl import Source

    response = _recorded_pdf_response("tamax_wlodowice_pl", "Zdów, Hucisko")
    with freeze_time("2026-10-31"):
        rows = Source.parse(response)
    bulky = [r["date"] for r in rows if r["type"] == "Wielkogabarytowe"]
    assert bulky == [D(2026, 10, 2)]
    by_date = {}
    for row in rows:
        by_date.setdefault(row["date"], set()).add(row["type"])
    assert sum(r["type"] == "Popiół" for r in rows) == 12
    for types in by_date.values():
        if "Segregowane" in types:
            assert {"Zmieszane", "Segregowane", "Bio", "Popiół"} <= types
    assert len(rows) == 65


class TestPdfRoundMonthGrid:
    """One row per round, one column per month, blocks per area."""

    MONTHS = (
        "Styczeń Luty Marzec Kwiecień Maj Czerwiec Lipiec Sierpień Wrzesień "
        "Październik Listopad Grudzień"
    ).split()
    ROMAN = "I II III IV V VI VII VIII IX X XI XII".split()

    @staticmethod
    def layout(lines, words, page=0):
        frag = parsers.PdfTextFragment
        return parsers.PdfWordLayout(
            [frag(page, text, x, y) for text, x, y in lines],
            [frag(page, text, x, y) for text, x, y in words],
            [],
        )

    def table(self, header, *, extra_words=(), extra_lines=()):
        """Two blocks (Mixed + Paper rows each); month i's column at x=200+40i."""
        lines = [
            ("Harmonogram od 01.01.2026", 300, 800),
            ("Mixed", 150, 700),
            ("Paper", 150, 680),
            ("Mixed", 150, 600),
            ("Paper", 150, 580),
            ("Lipowa, Polna", 40, 705),
            ("1", 40, 690),
            ("3 Maja", 40, 605),
            *extra_lines,
        ]
        words = [(name, 200 + 40 * i, 750) for i, name in enumerate(header)]
        words += [
            ("5,", 200, 700),  # January, Mixed, block 0
            ("19", 212, 701),  # January, Mixed (second day in the cell)
            ("7", 241, 679),  # February, Paper, block 0
            ("3", 640, 603),  # December, Mixed, block 1
            ("9", 280, 645),  # 35pt from the nearest row label: dropped
            ("4", 100, 700),  # left of the table: not a day
            *extra_words,
        ]
        words += [(text, x, y) for text, x, y in lines if text == "3 Maja"]
        return self.layout(lines, words)

    def grid(self, **kwargs):
        options = {
            "labels": {"Mixed": "Mixed", "Paper": "Paper"},
            "block_start": "Mixed",
            "year_pattern": r"od 01\.01\.(20\d\d)",
        }
        options.update(kwargs)
        return preprocessors.PdfRoundMonthGrid(**options)

    def test_bins_days_into_blocks_rows_and_months(self):
        blocks = self.grid(side_margin=100)([self.table(self.MONTHS)])
        assert [(b.year, b.page, b.top) for b in blocks] == [
            (2026, 0, 700),
            (2026, 0, 600),
        ]
        assert blocks[0].rows == [
            (D(2026, 1, 5), "Mixed"),
            (D(2026, 1, 19), "Mixed"),
            (D(2026, 2, 7), "Paper"),
        ]
        assert blocks[1].rows == [(D(2026, 12, 3), "Mixed")]
        # Side text: the block's street cell, without the "lp." number; the
        # "3 Maja" street (a month name) is neither a header nor block 0's.
        assert blocks[0].side_text == "Lipowa, Polna"
        assert blocks[1].side_text == "3 Maja"

    def test_header_is_the_topmost_complete_row_of_months(self):
        stray = [("Maj", 300, 790)]  # a month name in the title, above the table
        blocks = self.grid()([self.table(self.MONTHS, extra_words=stray)])
        assert blocks[0].rows[0] == (D(2026, 1, 5), "Mixed")
        assert blocks[0].side_text == ""  # side_margin not set

    def test_roman_header_callable_labels_and_stop_pattern(self):
        layout = self.table(
            self.ROMAN,
            extra_lines=[("Zbiórka", 300, 640)],
            extra_words=[("Zbiórka", 300, 640)],
        )
        grid = self.grid(
            labels=lambda text: text if text in ("Mixed", "Paper") else None,
            roman_months=True,
            stop_pattern=r"^zbiorka$",
        )
        blocks = grid([layout])
        assert len(blocks) == 1  # the second block is below the stop word
        assert blocks[0].rows[-1] == (D(2026, 2, 7), "Paper")

    def test_cells_with_dotted_or_run_together_days(self):
        # Hungarian calendars print "12." and "2.,"; a narrow cell runs its
        # days together ("3,17,31"). A year or street number is not a day.
        cells = [("12.", 241, 700), ("3,17,31", 280, 680), ("2026", 320, 700)]
        blocks = self.grid()([self.table(self.MONTHS, extra_words=cells)])
        assert (D(2026, 2, 12), "Mixed") in blocks[0].rows
        assert [date for date, label in blocks[0].rows if date.month == 3] == [
            D(2026, 3, 3),
            D(2026, 3, 17),
            D(2026, 3, 31),
        ]
        assert not [date for date, _ in blocks[0].rows if date.month == 4]

    def test_row_tolerance_none_keeps_far_days(self):
        blocks = self.grid(row_tolerance=None)([self.table(self.MONTHS)])
        assert (D(2026, 3, 9), "Paper") in blocks[0].rows

    def test_changed_layout_raises(self):
        with pytest.raises(ResponseShapeError):
            self.grid()([self.table(self.MONTHS[:11])])
        with pytest.raises(ResponseShapeError):
            self.grid(year_pattern=r"rok (20\d\d)")([self.table(self.MONTHS)])
        impossible = [("31", 241, 680)]  # 31 February
        with pytest.raises(ResponseShapeError):
            self.grid()([self.table(self.MONTHS, extra_words=impossible)])


def test_marker_calendar_half_cell_bar_reaches_its_day_numbers():
    from waste_collection_schedule.parsers import PdfVector
    from waste_collection_schedule.service.PdfMarkerCalendar import (
        MarkerCalendarParser,
        _Anchor,
    )

    parser = MarkerCalendarParser([], placement="cell")
    bar = PdfVector(0, 172, 530, 206, 539, None, (0.4, 0.7, 0.3))
    days = [
        _Anchor(0, 16, 180, 547),
        _Anchor(0, 17, 197, 547),
        _Anchor(0, 23, 180, 528.7),
        _Anchor(0, 24, 197, 528.7),
        _Anchor(0, 25, 214, 528.7),
        _Anchor(1, 23, 180, 528.7),
    ]
    assert parser._anchors_of(bar, days) == days[2:4]


def test_marker_calendar_year_pattern_joins_a_year_printed_in_pieces():
    from waste_collection_schedule.service.PdfMarkerCalendar import (
        MarkerCalendarParser,
    )

    split = MarkerCalendarParser([], year_pattern=r"Giugno\s+(20)\s+(\d\d)\b")
    assert split._year("Maggio Giugno 20 26 1 GI 2 VE", "") == 2026
    whole = MarkerCalendarParser([], year_pattern=r"Calendar\s+(20\d\d)")
    assert whole._year("Collection Calendar 2027", "") == 2027


def test_marker_calendar_read_headings_off_numbers_columns_in_order(monkeypatch):
    import datetime

    from waste_collection_schedule.parsers import (
        PdfTextFragment,
        PdfVector,
        PdfWordLayout,
    )
    from waste_collection_schedule.service import PdfMarkerCalendar
    from waste_collection_schedule.service.PdfMarkerCalendar import (
        Marker,
        MarkerCalendarParser,
    )

    # Three day-row columns of 2026 whose headings sit unevenly (104, 246,
    # 396 over columns at 85, 222, 360), each 1st marked with a dot.
    words = [
        PdfTextFragment(0, name, x, 1057)
        for name, x in (("Gennaio", 104), ("Febbraio", 246), ("Marzo", 396))
    ]
    vectors = []
    for x, days in ((85, 31), (222, 28), (360, 31)):
        for day in range(1, days + 1):
            words.append(PdfTextFragment(0, str(day), x, 1030 - 27 * day))
        vectors.append(PdfVector(0, x + 20, 1000, x + 26, 1006, None, (1, 0, 0)))
    layout = PdfWordLayout(lines=[], words=words, vectors=vectors)

    class _Layout:
        def __init__(self, **_):
            pass

        def __call__(self, *_):
            return [layout]

    monkeypatch.setattr(PdfMarkerCalendar, "PdfWordLayoutParser", _Layout)
    response = type("R", (), {"url": "https://example.org/calendario_2026.pdf"})()
    markers = [Marker("Dot", (1, 0, 0))]

    rows = MarkerCalendarParser(markers, read_headings=False, min_markers=3)(response)
    assert rows == [(datetime.date(2026, month, 1), "Dot") for month in (1, 2, 3)]


def test_marker_calendar_continuations_and_text_annotations(monkeypatch):
    from waste_collection_schedule.parsers import PdfTextFragment, PdfWordLayout
    from waste_collection_schedule.service import PdfMarkerCalendar

    words = [
        PdfTextFragment(0, name, x, 400) for name, x in (("Marzo", 60), ("Aprile", 250))
    ]
    words.extend(
        [
            PdfTextFragment(0, "6", 60, 350),
            PdfTextFragment(0, "A", 180, 350),
            PdfTextFragment(0, "3", 250, 350),
            PdfTextFragment(0, "B", 370, 350),
            PdfTextFragment(1, "20", 60, 390),
            PdfTextFragment(1, "A", 180, 390),
            PdfTextFragment(1, "17", 250, 390),
            PdfTextFragment(1, "B", 370, 390),
        ]
    )
    layout = PdfWordLayout(lines=[], words=words, vectors=[])

    class Layout:
        def __init__(self, **_):
            pass

        def __call__(self, *_):
            return [layout]

    monkeypatch.setattr(PdfMarkerCalendar, "PdfWordLayoutParser", Layout)
    response = SimpleNamespace(url="https://example.org/calendar_2026.pdf")
    parser = PdfMarkerCalendar.MarkerCalendarParser(
        [],
        continuation_pages=True,
        text_markers={"A": "Zone A", "B": "Zone B"},
        row_reach=160,
        min_markers=4,
    )
    assert parser(response) == [
        (D(2026, 3, 6), "Zone A"),
        (D(2026, 3, 20), "Zone A"),
        (D(2026, 4, 3), "Zone B"),
        (D(2026, 4, 17), "Zone B"),
    ]


def test_marker_calendar_accepts_a_stroked_icon_without_using_an_unpainted_fill():
    from waste_collection_schedule.parsers import PdfVector
    from waste_collection_schedule.service.PdfMarkerCalendar import Marker, _same_color

    marker = Marker("Paper", (0.145, 0.541, 0.753))
    assert _same_color(PdfVector(0, 0, 0, 12, 16, marker.color, None), marker)
    assert not _same_color(PdfVector(0, 0, 0, 12, 16, marker.color, (0, 0, 0)), marker)


def test_selargius_independent_zones_and_continuation_pages():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule import waste_types as wt
    from waste_collection_schedule.source.selargiusostenibile_it import Source

    outputs = []
    for case, args in Source.TEST_CASES.items():
        with cassette.replaying(fixture_path("selargiusostenibile_it", case)):
            outputs.append({(r.date, r.waste_type.id) for r in Source(**args).fetch()})
    paese_a, paese_b, suplanu_a = outputs
    assert (D(2026, 3, 6), wt.GENERAL_WASTE.id) in paese_a
    assert (D(2026, 3, 6), wt.GENERAL_WASTE.id) not in paese_b
    assert (D(2026, 3, 13), wt.GENERAL_WASTE.id) in paese_b
    assert (D(2026, 3, 5), wt.PAPER.id) in paese_a
    assert (D(2026, 3, 5), wt.PAPER.id) not in suplanu_a
    assert (D(2026, 3, 6), wt.PAPER.id) in suplanu_a
    assert (D(2027, 2, 26), wt.PAPER.id) in suplanu_a
    assert (D(2027, 2, 27), wt.ORGANIC.id) in paese_a


class TestOutlinedDayRows:
    """Text labels dated by the outlined day rows and month headings."""

    TOP = 459.0
    PITCH = 13.7

    def layout(self, *, february_days=28):
        frag = parsers.PdfTextFragment
        vec = parsers.PdfVector
        black = (0.0, 0.0, 0.0)
        vectors = []
        # Outlined month names: a legend title on the left, then January and
        # February over their columns.
        for x0 in (120, 130, 140, 240, 250, 260, 345, 355, 365):
            vectors.append(vec(0, x0, 476, x0 + 6, 484, None, black))
        # Day number and weekday glyphs, one row per day.
        for x0, days in ((211, 31), (316, february_days)):
            for day in range(days):
                y = self.TOP - day * self.PITCH
                vectors.append(vec(0, x0, y - 4, x0 + 5, y + 4, None, black))
                vectors.append(vec(0, x0 + 12, y - 4, x0 + 16, y + 4, None, black))
        words = [
            frag(0, "GENNAIO - GIUGNO 2027", 580, 510),
            frag(0, "UMIDO", 255, self.TOP - 1.8),  # 1 January
            frag(0, "PLASTICA", 291, self.TOP - 1.8),
            frag(0, "VETRO VERDE", 273, self.TOP - 30 * self.PITCH - 1.8),
            frag(0, "CARTA", 378, self.TOP - self.PITCH - 1.8),  # 2 February
            frag(0, "SECCO", 160, self.TOP - 1.8),  # the legend
            frag(0, "Festività", 378, 20),
        ]
        return parsers.PdfWordLayout(words, words, vectors)

    def parser(self):
        from waste_collection_schedule.service.PdfOutlinedCalendar import (
            OutlinedDayRowsParser,
        )

        return OutlinedDayRowsParser(
            ["UMIDO", "PLASTICA", "VETRO", "VERDE", "CARTA", "SECCO"],
            year_pattern=r"GIUGNO (20\d\d)",
            min_labels=1,
        )

    def test_dates_labels_by_row_and_heading(self):
        assert self.parser().read(self.layout()) == [
            (D(2027, 1, 1), "PLASTICA"),
            (D(2027, 1, 1), "UMIDO"),
            (D(2027, 1, 31), "VERDE"),
            (D(2027, 1, 31), "VETRO"),
            (D(2027, 2, 2), "CARTA"),
        ]

    def test_a_column_running_past_its_month_raises(self):
        with pytest.raises(ResponseShapeError):
            self.parser().read(self.layout(february_days=29))


def test_halley_portal_attachment_conversation():
    from types import SimpleNamespace

    from waste_collection_schedule.service import HalleyPortal

    listing = SimpleNamespace(
        url="https://www.comune.example.it/novita/avvisi/avvisi.html",
        text=(
            '<a href="https://www.comune.example.it/novita/avvisi/novita_6.html">'
            "Calendario 2026 raccolta rifiuti</a>"
            '<a href="/novita/avvisi/novita_19.html">'
            "Calendario 2027 raccolta rifiuti differenziata</a>"
            '<a href="/novita/avvisi/novita_17.html">Scadenza carte</a>'
        ),
    )
    news = HalleyPortal.news_pick(r"calendario.*raccolta")(listing)
    assert news == "https://www.comune.example.it/novita/avvisi/novita_19.html"

    page = SimpleNamespace(
        url=news,
        text=(
            "<a href=\"javascript:SCHIOCCIOLA('en=eg696&MESSA=PUBBLICA&DSK=0000"
            "&NOME=Calendario rifiuti 2027.pdf&FORM=pdf','EG0/EGDOCVISJS.HBL')\">"
            "Calendario</a>"
        ),
    )
    attachment = HalleyPortal.attachment_pick(r"\.pdf")(page)
    assert HalleyPortal.download_body(attachment) == (
        '--AZazAZ\r\n&name="protocollo=https&ser=www.comune.example.it&'
        "en=eg696&MESSA=PUBBLICA&DSK=0000&NOME=Calendario rifiuti 2027.pdf"
        '&FORM=pdf&PAGINA="\r\n\n\r\n--AZazAZ--\r\n'
    )


def test_marker_calendar_below_binds_symbols_to_the_day_number_heading_the_cell():
    from waste_collection_schedule.parsers import PdfVector
    from waste_collection_schedule.service.PdfMarkerCalendar import (
        MarkerCalendarParser,
        _Anchor,
    )

    parser = MarkerCalendarParser([], placement="below", row_reach=40)
    # Monday 2 and Tuesday 3 head their cells at y=277; the week above
    # starts at y=327.
    days = [
        _Anchor(0, 1, 416, 327),
        _Anchor(0, 2, 37.6, 277),
        _Anchor(0, 16, 40.5, 226),
        _Anchor(0, 3, 100.6, 277),
    ]
    first = PdfVector(0, 31.3, 244, 40.2, 253.5, None, (0.9, 0.2, 0.1))
    last = PdfVector(0, 85.7, 249, 88.8, 251.4, None, (0.9, 0.2, 0.1))
    next_cell = PdfVector(0, 96, 244, 105, 253, None, (0.9, 0.2, 0.1))
    below_16 = PdfVector(0, 32.3, 193, 41.2, 202.5, None, (0.9, 0.2, 0.1))
    assert parser._anchors_of(first, days) == [days[1]]
    assert parser._anchors_of(last, days) == [days[1]]
    assert parser._anchors_of(next_cell, days) == [days[3]]
    assert parser._anchors_of(below_16, days) == [days[2]]
    # Nothing above within reach: not a day's symbol.
    legend = PdfVector(0, 31, 500, 40, 510, None, (0.9, 0.2, 0.1))
    assert parser._anchors_of(legend, days) == []


def test_marker_calendar_page_headings_accept_a_lone_heading_over_a_month():
    from waste_collection_schedule.parsers import PdfTextFragment
    from waste_collection_schedule.service.PdfMarkerCalendar import (
        MarkerCalendarParser,
        _Anchor,
    )

    grid = [
        _Anchor(0, day, 40 + 60 * ((day - 1) % 7), 330 - 50 * ((day - 1) // 7))
        for day in range(1, 29)
    ]
    prose = [_Anchor(1, 16, 100, 300), _Anchor(1, 3, 120, 300)]
    words = [
        PdfTextFragment(0, "FEBBRAIO", 110, 380),
        PdfTextFragment(0, "26", 220, 380),
        PdfTextFragment(1, "maggio", 100, 320),  # "dal 3 maggio ... 16 kg"
    ]
    anchors = [*grid, *prose]

    months, first = MarkerCalendarParser([], placement="below")._months_from_headings(
        words, anchors
    )
    assert months == {}
    assert first is None

    months, first = MarkerCalendarParser(
        [], placement="below", page_headings=True
    )._months_from_headings(words, anchors)
    assert first == 2
    assert {months[a] for a in grid} == {2}
    assert not any(a in months for a in prose)


_MARKED_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_MARKED_WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


def _marked_calendar_pdf(
    *,
    year=2026,
    columns=7,
    omitted=None,
    duplicate_days=None,
    bad_day=None,
    year_label=True,
    hidden_blue=False,
    marked_day=(1, 26),
    cancelled=None,
    row_band=False,
    heading_year=False,
    stray_number=False,
):
    """A complete printed calendar; January 26 has fill and stroke markers."""
    import calendar
    from io import BytesIO

    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    font = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )
    for month, name in enumerate(_MARKED_MONTHS, 1):
        page = writer.add_blank_page(width=220, height=800)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        commands = []

        def text(value, x, y, color="0 0 0", output_commands=commands):
            output_commands.append(f"BT /F1 9 Tf {color} rg {x} {y} Td ({value}) Tj ET")

        if year_label:
            text(f"YEAR {year}", 20, 760)
        text(f"{name} {year}" if heading_year else name, 20, 700)
        if stray_number and month == 1:
            commands.append("BT /F1 8 Tf 1 1 1 rg 20 610 Td (22) Tj ET")
        for column, label in enumerate(_MARKED_WEEKDAYS[:columns]):
            text(label, 20 + 20 * column, 680)
        for week, days in enumerate(calendar.monthcalendar(year, month)):
            for column, day in enumerate(days[:columns]):
                if not day:
                    continue
                x, y = 20 + 20 * column, 660 - 20 * week
                if (month, day) == cancelled:
                    commands.append(f"q 1 .11 .49 rg {x - 2} {y - 4} 16 14 re f Q")
                    continue
                marked = (month, day) == marked_day
                if marked and hidden_blue:
                    commands.append(f"q 0 0 1 rg {x + 1} {y - 1} 8 8 re f Q")
                if marked:
                    width = 136 if row_band else 16
                    commands.append(f"q 0 0 0 rg {x - 2} {y - 4} {width} 14 re f Q")
                    commands.append(f"q 1 0 0 RG 2 w {x - 2} {y - 4} {width} 14 re S Q")
                if (month, day) != omitted:
                    value = 32 if (month, day) == bad_day else day
                    if duplicate_days:
                        value = duplicate_days.get((month, day), value)
                    text(value, x, y, "1 1 1" if marked else "0 0 0")
        stream = DecodedStreamObject()
        stream.set_data("\n".join(commands).encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def _marked_parser(**kwargs):
    from waste_collection_schedule.service.MarkedPdfCalendar import (
        MarkedPdfCalendarParser,
    )

    columns = kwargs.pop("columns", 7)
    return MarkedPdfCalendarParser(
        months=_MARKED_MONTHS,
        weekdays=_MARKED_WEEKDAYS[:columns],
        year_pattern=r"YEAR (20\d{2})",
        alignment="left",
        colors={
            "general": ((0, 0, 0),),
            "organic": ((1, 0, 0),),
            "recycling": ((0, 0, 1),),
        },
        **kwargs,
    )


@pytest.mark.parametrize("year,columns", [(2026, 7), (2027, 7), (2026, 5), (2027, 5)])
def test_marked_pdf_grid_reads_combined_fill_and_stroke_across_year_layouts(
    year, columns
):
    response = SimpleNamespace(content=_marked_calendar_pdf(year=year, columns=columns))
    rows = _marked_parser(columns=columns)(response)
    assert [(r["date"], r["type"]) for r in rows] == [
        (D(year, 1, 26), "general"),
        (D(year, 1, 26), "organic"),
    ]


@pytest.mark.parametrize("allow_missing", [False, True])
def test_marked_pdf_missing_unmarked_holiday_is_opt_in(allow_missing):
    response = SimpleNamespace(content=_marked_calendar_pdf(omitted=(1, 1)))
    if allow_missing:
        assert len(_marked_parser(allow_unmarked_missing_days=True)(response)) == 2
    else:
        with pytest.raises(ValueError, match="Incomplete printed grid"):
            _marked_parser()(response)


def test_marked_pdf_never_ignores_a_collection_marker_without_its_day_number():
    response = SimpleNamespace(content=_marked_calendar_pdf(omitted=(1, 26)))
    with pytest.raises(ValueError, match="Collection marker has no printed day"):
        _marked_parser(allow_unmarked_missing_days=True)(response)


def test_marked_pdf_rejects_invalid_printed_day():
    response = SimpleNamespace(content=_marked_calendar_pdf(bad_day=(1, 15)))
    with pytest.raises(ValueError, match="Incomplete printed grid"):
        _marked_parser()(response)


def test_marked_pdf_requires_a_published_year():
    with pytest.raises(ValueError, match="Printed calendar year not found"):
        _marked_parser()(
            SimpleNamespace(content=_marked_calendar_pdf(year_label=False))
        )


def _recorded_pdf_response(module, case):
    import cassette
    from fixtures_support import fixture_path

    data = json.loads(Path(fixture_path(module, case)).read_text())
    item = next(item for item in data["interactions"] if ".pdf" in item["url"])
    return cassette.CassetteResponse(item)


def test_outlined_month_rows_keep_printed_holiday_dates_and_combined_bins():
    from waste_collection_schedule.service.NewryMourneDownCalendar import CalendarParser

    response = _recorded_pdf_response(
        "newrymournedown_org", "9 Derrymore Road, Bessbrook"
    )
    with freeze_time("2026-10-30"):
        rows = set(CalendarParser()(response))
    assert len(rows) == 84
    assert (D(2026, 4, 2), "Black bin") in rows
    assert (D(2026, 4, 2), "Brown bin") in rows
    assert (D(2026, 4, 9), "Blue bin") in rows
    assert {day.month for day, _ in rows if day.year == 2026} == set(range(4, 13))
    assert {day.month for day, _ in rows if day.year == 2027} == set(range(1, 5))
    with freeze_time("2027-05-01"), pytest.raises(ValueError, match="expired"):
        CalendarParser()(response)


def _recorded_wednesday_calendar():
    import cassette
    from fixtures_support import FIXTURE_DIR

    path = Path(FIXTURE_DIR) / "newrymournedown_org" / "_wednesday.json"
    return cassette.CassetteResponse(json.loads(path.read_text())["interactions"][0])


def test_outlined_calendar_keeps_the_printed_friday_exception():
    from waste_collection_schedule.service.NewryMourneDownCalendar import CalendarParser

    with freeze_time("2026-10-30"):
        rows = set(CalendarParser()(_recorded_wednesday_calendar()))
    assert (D(2026, 10, 30), "Black bin") in rows
    assert (D(2026, 10, 30), "Brown bin") in rows
    assert any(day == D(2026, 10, 28) for day, _ in rows)


def test_outlined_calendar_rejects_a_month_grid_disagreeing_with_its_route_weekday():
    from waste_collection_schedule.service.NewryMourneDownCalendar import CalendarParser

    response = _recorded_wednesday_calendar()
    response.url = response.url.replace("WED-Z1", "MON-Z1")
    with freeze_time("2026-10-30"), pytest.raises(ValueError, match="route weekday"):
        CalendarParser()(response)


@pytest.mark.parametrize("scale,dx,dy", [(1, 0, 0), (0.6, -50, 70), (2.5, 300, -100)])
def test_outlined_digit_recognition_is_translation_and_scale_independent(scale, dx, dy):
    from io import BytesIO

    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTCurve
    from waste_collection_schedule.service.NewryMourneDownCalendar import _color, _walk
    from waste_collection_schedule.service.PdfVectorDigits import (
        TAHOMA_BOLD,
        VectorDigits,
    )

    response = _recorded_wednesday_calendar()
    # The first April cell prints 1. Its outlined numeral sits in the centre
    # of the first black/brown box, independent of the hidden text layer.
    candidates = [
        x
        for page in extract_pages(BytesIO(response.content))
        for x in _walk(page)
        if isinstance(x, LTCurve)
        and x.fill
        and _color(x.non_stroking_color, (1, 1, 1))
        and 8 < x.height < 13
        and 130 < x.x0 < 140
        and 438 < x.y0 < 440
    ]
    assert len(candidates) == 1
    original = candidates[0]
    shape = SimpleNamespace(
        x0=original.x0 * scale + dx,
        y0=original.y0 * scale + dy,
        width=original.width * scale,
        height=original.height * scale,
        x1=original.x1 * scale + dx,
        original_path=[
            (part[0], *((x * scale + dx, y * scale + dy) for x, y in part[1:]))
            for part in original.original_path
        ],
    )
    decoder = VectorDigits(TAHOMA_BOLD)
    assert decoder.read([shape]) == 1
    shape.original_path.append(("l", (shape.x0, shape.y0)))
    with pytest.raises(ValueError, match="Unknown"):
        decoder.read([shape])


def test_marked_pdf_preserves_ritl_combined_rounds_and_ignores_padding_days():
    from collections import Counter

    from waste_collection_schedule.source.ritl_ca import Source

    response = _recorded_pdf_response("ritl_ca", "Lac-Supérieur Secteur 1")
    rows = Source.parse([response])
    pairs = {(row["date"], row["type"]) for row in rows}
    assert Counter(row["type"] for row in rows) == {
        "general": 19,
        "organic": 39,
        "recycling": 26,
    }
    assert {
        (D(2026, 1, 26), "general"),
        (D(2026, 1, 26), "organic"),
        (D(2026, 5, 11), "organic"),
        (D(2026, 5, 11), "recycling"),
    } <= pairs
    assert all(day.year == 2026 for day, _ in pairs)


@pytest.mark.parametrize(
    "route,count", [("Innentour", 52), ("Aussentour", 26), ("Sigerswil", 26)]
)
def test_marked_pdf_respects_published_grosswangen_route_restrictions(route, count):
    from collections import Counter

    from waste_collection_schedule.source.grosswangen_ch import Source

    source = Source(route=route)
    response = _recorded_pdf_response("grosswangen_ch", "TEST")
    rows = list(source.preprocess(source.parse([response]), source))
    counts = Counter(row["type"] for row in rows)
    assert counts == {
        "general": count,
        "organic": 22,
        "paper": 16,
        "garden": 5,
        "metal": 2,
        "electronics": 2,
    }
    pairs = {(row["date"], row["type"]) for row in rows}
    assert (D(2026, 3, 5), "garden") in pairs
    assert (D(2026, 3, 5), "paper") in pairs
    assert (D(2026, 1, 8), "paper") in pairs
    assert (D(2026, 6, 11), "paper") in pairs
    assert (D(2026, 6, 4), "paper") not in pairs
    if route != "Innentour":
        assert all(
            row["date"].isocalendar().week % 2 == (0 if route == "Sigerswil" else 1)
            for row in rows
            if row["type"] == "general"
        )


@pytest.mark.parametrize(
    "municipality,sector,case,weekday,exceptions",
    [
        ("Mont-Blanc", "Secteur Est", "Mont-Blanc Secteur Est", 1, set()),
        ("Mont-Blanc", "Secteur Ouest", "Mont-Blanc Secteur Ouest", 3, {D(2026, 1, 2)}),
        (
            "Sainte-Agathe-des-Monts",
            "Secteur Centre-ville",
            "Sainte-Agathe-des-Monts Secteur Centre-ville",
            2,
            set(),
        ),
        (
            "Sainte-Agathe-des-Monts",
            "Secteur Nord",
            "Sainte-Agathe-des-Monts Secteur Nord",
            3,
            {D(2026, 1, 2)},
        ),
        (
            "Sainte-Agathe-des-Monts",
            "Secteur Sud / Fatima",
            "Sainte-Agathe-des-Monts Secteur Sud / Fatima",
            4,
            {D(2026, 12, 28)},
        ),
    ],
)
def test_ritl_shared_pdf_keeps_only_the_chosen_sector_and_printed_exceptions(
    municipality, sector, case, weekday, exceptions
):
    from waste_collection_schedule.source.ritl_ca import Source

    response = _recorded_pdf_response("ritl_ca", case)
    source = Source(municipality=municipality, sector=sector)
    with freeze_time("2026-01-01"):
        rows = list(source.preprocess(source.parse([response]), source))
    days = {row["date"] for row in rows}
    assert rows
    assert {day for day in days if day.weekday() != weekday} == exceptions
    assert D(2026, 1, 1) not in days
    if sector == "Secteur Sud / Fatima":
        assert D(2026, 12, 25) not in days
        assert any(
            row["date"] == D(2026, 12, 28) and row["type"] == "recycling"
            for row in rows
        )


def test_marked_pdf_ignores_a_colour_fully_hidden_by_a_later_solid_marker():
    rows = _marked_parser()(
        SimpleNamespace(content=_marked_calendar_pdf(hidden_blue=True))
    )
    assert {row["type"] for row in rows} == {"general", "organic"}


def test_marked_pdf_records_crossed_out_cells_and_the_next_actual_marked_date():
    response = SimpleNamespace(
        content=_marked_calendar_pdf(cancelled=(1, 1), marked_day=(1, 2))
    )
    rows = _marked_parser(
        allow_unmarked_missing_days=True, cancelled_colors=((1, 0.11, 0.49),)
    )(response)
    assert len(rows) == 2
    assert all(row["date"] == D(2026, 1, 2) for row in rows)
    assert rows[0]["cancelled_dates"] == (D(2026, 1, 1),)
    assert rows[0]["next_marked_after_cancelled"] == {D(2026, 1, 1): D(2026, 1, 2)}


@pytest.mark.parametrize("group", [1, 2])
@pytest.mark.parametrize("holiday", [D(2026, 12, 25), D(2027, 1, 1), D(2027, 3, 26)])
def test_victoria_park_uses_printed_holiday_replacements(group, holiday):
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule.source.victoriapark_wa_gov_au import Source

    case = "Group 1 Monday" if group == 1 else "Group 2 Friday"
    with (
        cassette.replaying(fixture_path("victoriapark_wa_gov_au", case)),
        freeze_time(holiday),
    ):
        entries = Source(group=group, day="Friday").fetch()
    assert not any(e.date == holiday for e in entries)
    assert sum(e.date == holiday + datetime.timedelta(days=1) for e in entries) == 2
    assert all(e.date <= D(2027, 6, 30) for e in entries)


def test_victoria_park_does_not_project_beyond_published_guide():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule.source.victoriapark_wa_gov_au import Source

    case = "Group 1 Monday"
    with (
        cassette.replaying(fixture_path("victoriapark_wa_gov_au", case)),
        freeze_time("2027-07-01"),
        pytest.raises(ValueError, match="does not cover today"),
    ):
        Source(**Source.TEST_CASES[case]).fetch()


@pytest.mark.parametrize("group", [1, 2])
@pytest.mark.parametrize("scale", [0.8, 1.2])
def test_victoria_park_raster_grid_tracks_image_scale(group, scale):
    from io import BytesIO

    import cassette
    from fixtures_support import fixture_path
    from PIL import Image
    from waste_collection_schedule.source.victoriapark_wa_gov_au import Source

    case = "Group 1 Monday" if group == 1 else "Group 2 Friday"
    source = Source(**Source.TEST_CASES[case])
    with cassette.replaying(fixture_path("victoriapark_wa_gov_au", case)):
        response = source.retrieve(source)
    expected = source.parse(response, source)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    scaled = img.resize((int(img.width * scale), int(img.height * scale)))
    payload = BytesIO()
    scaled.save(payload, format="PNG")
    actual = source.parse(
        SimpleNamespace(content=payload.getvalue(), url=response.url), source
    )
    assert actual == expected


@pytest.mark.parametrize("year,day", [(2026, 12), (2027, 11)])
def test_marked_pdf_week_bands_span_printed_day_cells(year, day):
    response = SimpleNamespace(
        content=_marked_calendar_pdf(year=year, marked_day=(1, day), row_band=True)
    )
    rows = _marked_parser(row_bands=True)(response)
    expected = {D(year, 1, day) + datetime.timedelta(days=i) for i in range(7)}
    assert {r["date"] for r in rows if r["type"] == "general"} == expected
    assert {r["date"] for r in rows if r["type"] == "organic"} == expected


@pytest.mark.parametrize("year", [2026, 2027])
def test_marked_pdf_year_suffixed_headings_are_opt_in(year):
    response = SimpleNamespace(
        content=_marked_calendar_pdf(year=year, heading_year=True)
    )
    with pytest.raises(ValueError, match="complete annual"):
        _marked_parser()(response)
    rows = _marked_parser(heading_year=True)(response)
    assert {r["date"] for r in rows} == {D(year, 1, 26)}


def test_marked_pdf_font_filter_excludes_editing_text_but_requires_real_day_numbers():
    response = SimpleNamespace(content=_marked_calendar_pdf(stray_number=True))
    with pytest.raises(ValueError, match="differs from grid"):
        _marked_parser()(response)
    assert len(_marked_parser(day_font_size=(8.9, 9.1))(response)) == 2
    with pytest.raises(ValueError, match="Incomplete printed grid"):
        _marked_parser(day_font_size=(8.9, 9.1))(
            SimpleNamespace(
                content=_marked_calendar_pdf(omitted=(1, 1), stray_number=True)
            )
        )


def test_strathfield_published_calendar_is_complete_and_stops_at_year_end():
    import cassette
    from fixtures_support import fixture_path
    from waste_collection_schedule.source.strathfield_nsw_gov_au import Source

    case = "Monday collection"
    source = Source(**Source.TEST_CASES[case])
    with cassette.replaying(fixture_path("strathfield_nsw_gov_au", case)):
        response = source.retrieve(source)
        days = source.parse(response, source)
    with cassette.replaying(fixture_path("strathfield_nsw_gov_au", case)):
        entries = source.fetch()
    assert len(days) == 365
    assert len({r["date"] for r in days}) == 365
    assert (D(2026, 1, 5), "green") in {(r["date"], r["type"]) for r in days}
    assert all(D(2026, 10, 26) <= e.date <= D(2026, 12, 31) for e in entries)


def test_paczkow_joins_day_lists_wrapped_onto_their_own_lines():
    """pypdf before 6.20 extracts a wrapped month cell as separate lines."""
    import datetime

    from waste_collection_schedule.source.paczkow_pl import _tables

    header = (
        "Ulice: Kopernika\n"
        "RODZAJ ODEBRANEGO ODPADU PAŹDZIERNIK 2026 LISTOPAD 2026 GRUDZIEŃ 2026 \n"
    )
    footer = "\nnie mają prawa wchodzenia na teren posesji)"
    joined = "Odpady BIO 09, 23, 30 06, 20 04, 18\n"
    wrapped = "Odpady BIO 09, 23, \n30 \n06, 20 \n04, \n18 \n"

    expected = [
        (datetime.date(2026, month, day), "Odpady BIO")
        for month, days in ((10, (9, 23, 30)), (11, (6, 20)), (12, (4, 18)))
        for day in days
    ]
    for body in (joined, wrapped):
        (table,) = _tables(header + body + footer)
        assert table["areas"] == ["Kopernika"]
        assert table["rows"] == expected

    # A row genuinely missing a month still fails loudly.
    with pytest.raises(ValueError):
        _tables(header + "Odpady BIO 09, 23, 30 06, 20\n" + footer)


def test_eko_region_outlined_table_keeps_ash_and_seasonal_collection_changes():
    from collections import Counter

    from waste_collection_schedule.service.EkoRegionCalendar import CalendarParser

    response = _recorded_pdf_response("eko_region_pl", "Bednarze")
    with freeze_time("2026-10-30"):
        rows = set(CalendarParser()(response))
    assert len(rows) == 61
    assert Counter(label for _, label in rows) == {
        "Metale i tworzywa sztuczne": 12,
        "Papier": 4,
        "Szkło": 4,
        "Bio": 15,
        "Popiół": 6,
        "Zmieszane odpady komunalne": 20,
    }
    assert (D(2026, 1, 10), "Popiół") in rows
    assert (D(2026, 1, 10), "Bio") not in rows
    assert (D(2026, 4, 3), "Popiół") in rows
    assert (D(2026, 4, 17), "Bio") in rows
    assert (D(2026, 11, 2), "Zmieszane odpady komunalne") in rows
    assert (D(2026, 11, 9), "Zmieszane odpady komunalne") not in rows


def test_eko_region_unknown_outlined_glyphs_fail_instead_of_dropping_days(monkeypatch):
    from waste_collection_schedule.service import EkoRegionCalendar

    response = _recorded_pdf_response("eko_region_pl", "Bednarze")
    monkeypatch.delitem(EkoRegionCalendar._GLYPHS, "2")
    with freeze_time("2026-10-30"), pytest.raises(ValueError, match="Unknown outlined"):
        EkoRegionCalendar.CalendarParser()(response)


def test_eko_region_rejects_last_years_calendar():
    from waste_collection_schedule.service.EkoRegionCalendar import CalendarParser

    response = _recorded_pdf_response("eko_region_pl", "Bednarze")
    with freeze_time("2027-01-01"), pytest.raises(ValueError, match="current-year"):
        CalendarParser()(response)
