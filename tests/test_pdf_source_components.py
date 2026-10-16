"""Offline tests for the components the 2026 PDF sources added.

``PdfMonthRows``, ``retrievers.yearly_links``, ``lookups.normalize_loose``,
``TextGroupedDates(end_pattern=...)``, ``EachResponse(then=...)`` and the
``codes`` / ``weekday_order`` options of ``DayGridCalendarParser``.
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

    response = _dunanett_response("dunaf_ldv_r")
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

    response = _dunanett_response(case)
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
