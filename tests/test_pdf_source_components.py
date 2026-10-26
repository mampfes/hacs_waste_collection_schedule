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
import sys
from pathlib import Path
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
from waste_collection_schedule.service.EastLindseyCalendar import (
    GardenCalendarParser,
    garden_calendar_urls,
)
from waste_collection_schedule.service.PdfTextCalendar import (
    GERMAN_WEEKDAY_ORDER,
    DayGridCalendarParser,
)

D = datetime.date


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


def test_east_lindsey_without_a_garden_subscription_does_not_fetch_a_pdf():
    for pdf_id in (None, "", "null"):
        payload = {"RESULTS_1": {"FIELD12": {"result": [{"greenpdfid": pdf_id}]}}}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        response = SimpleNamespace(text=f'var XFormData = "{encoded}";')
        assert garden_calendar_urls(None, response) == []


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
    bad_day=None,
    year_label=True,
    hidden_blue=False,
    marked_day=(1, 26),
    cancelled=None,
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
        text(name, 20, 700)
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
                    commands.append(f"q 0 0 0 rg {x - 2} {y - 4} 16 14 re f Q")
                    commands.append(f"q 1 0 0 RG 2 w {x - 2} {y - 4} 16 14 re S Q")
                if (month, day) != omitted:
                    value = 32 if (month, day) == bad_day else day
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
