"""Waste collection schedules for Nuneaton and Bedworth Borough Council, England.

The council's street directory resolves a street to its collection round and
links the round's yearly calendar PDF (e.g. "Bin calendar Wednesday A"). The
PDF colours each collection day with the bin(s) emptied that day, so
``_calendar_rows`` maps the coloured cells of the twelve month grids back to
dates. Each month's year is derived from the weekday its 1st falls on, as the
calendar runs from October to September.

The green bin (garden and food waste) is a paid subscription; its dates are
the "Green & Brown" days, and the "Brown only - no green" days are the
January break the calendar prints.
"""

import calendar
import re
from collections.abc import Iterable
from datetime import date
from typing import ClassVar, final
from urllib.parse import urljoin

from waste_collection_schedule import parsers, preprocessors, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.nuneatonandbedworth.gov.uk"
_SEARCH_URL = f"{_BASE_URL}/directory/search"
_DIRECTORY_ID = 3

_TYPE_MAP = {
    "Green & Brown": [wt.GARDEN_WASTE, wt.RECYCLABLES],
    "Black": wt.GENERAL_WASTE,
    "Brown only": wt.RECYCLABLES,
}

# Cell colours of the legend ("Green & Brown", "Black", "Brown only - no
# green"). The legend is a single text run, so the colours cannot be paired
# with their labels from the PDF; ``_calendar_rows`` checks they are still
# the legend's colours instead.
_CELL_COLOURS = {
    "Green & Brown": (0.552, 0.778, 0.247),
    "Black": (0.684, 0.686, 0.69),
    "Brown only": (0.543, 0.37, 0.237),
}
_COLOUR_TOLERANCE = 0.03

_MONTHS = {name: number for number, name in enumerate(calendar.month_name) if name}
_RECORD_RE = re.compile(
    r'<a[^>]+class="list__link"[^>]+href="(/directory-record/[^"]+)"[^>]*>([^<]+)</a>'
)
_CALENDAR_RE = re.compile(r'href="([^"]*/downloads/file/\d+/[^"]*calendar[^"]*)"')
_YEAR_RE = re.compile(r"20\d\d")


def _normalise(value: str) -> str:
    return " ".join(value.replace(",", " ").split()).casefold()


def _street_record(response, *_, street: str, **__) -> str:
    """Pick the directory record of the configured street."""
    records = [
        (" ".join(name.split()), href)
        for href, name in _RECORD_RE.findall(response.text)
    ]
    wanted = _normalise(street)
    exact = [href for name, href in records if _normalise(name) == wanted]
    if len(exact) == 1:
        return urljoin(_BASE_URL, exact[0])
    # "Church Street" exists in both towns, listed as "Church Street, Bedworth"
    # and "Church Street, Nuneaton": suggest the qualified names.
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, [name for name, _ in records]
    )


def _calendar_url(response, *_, **__) -> str:
    """Pick the calendar download linked from the street's directory record."""
    match = _CALENDAR_RE.search(response.text)
    response_shape.expect(
        match is not None,
        source_name="Nuneaton and Bedworth Borough Council",
        detail="street record has no bin calendar link",
        raw=response.text[:500],
    )
    assert match is not None
    return urljoin(_BASE_URL, match.group(1))


def _colour_label(colour: tuple[float, ...] | None) -> str | None:
    if not colour or len(colour) != 3:
        return None
    for label, expected in _CELL_COLOURS.items():
        if all(
            abs(actual - wanted) <= _COLOUR_TOLERANCE
            for actual, wanted in zip(colour, expected, strict=True)
        ):
            return label
    return None


def _month_year(month: int, first_column: int, candidates: Iterable[int]) -> int | None:
    years = [
        year for year in candidates if date(year, month, 1).weekday() == first_column
    ]
    return years[0] if len(years) == 1 else None


def _calendar_rows(
    records: parsers.PdfDocumentLayout, source: BaseSource | None = None
) -> Iterable[tuple[date, str]]:
    """Map each coloured day cell of the month grids to its date."""
    layout = records
    source_name = response_shape.source_name(source)

    # Each month grid hangs below a title bar holding the month name.
    titles = []
    for fragment in layout.fragments:
        month = _MONTHS.get(fragment.text.strip())
        if month is None:
            continue
        bar = next(
            (
                vector
                for vector in layout.vectors
                if vector.page == fragment.page
                and 140 < vector.x1 - vector.x0 < 220
                and 10 < vector.y1 - vector.y0 < 25
                and vector.x0 <= fragment.x + 2 <= vector.x1
                and vector.y0 <= fragment.y + 2 <= vector.y1
            ),
            None,
        )
        if bar is not None:
            titles.append((month, bar))
    response_shape.expect(
        len(titles) == 12,
        source_name=source_name,
        detail=f"expected 12 month grids in the calendar PDF, found {len(titles)}",
        raw=layout.text[:500],
    )

    legend = {
        label
        for vector in layout.vectors
        if vector.x1 - vector.x0 > 60
        and 15 < vector.y1 - vector.y0 < 40
        and (label := _colour_label(vector.fill_color)) is not None
    }
    response_shape.expect(
        legend == set(_CELL_COLOURS),
        source_name=source_name,
        detail="the calendar legend colours changed",
        raw=layout.text[:500],
    )

    years = {int(year) for year in _YEAR_RE.findall(layout.text)}
    candidates = sorted({year + delta for year in years for delta in (-1, 0, 1)})
    response_shape.expect(
        bool(candidates),
        source_name=source_name,
        detail="no year found in the calendar PDF",
        raw=layout.text[:500],
    )

    cells = [
        (vector, label)
        for vector in layout.vectors
        if 15 < vector.x1 - vector.x0 < 40
        and 8 < vector.y1 - vector.y0 < 25
        and (label := _colour_label(vector.fill_color)) is not None
    ]

    for month, bar in titles:
        width = (bar.x1 - bar.x0) / 7
        # The weekday row (M T W T F S S) sits directly below the title bar.
        weekday_row = next(
            (
                vector
                for vector in layout.vectors
                if vector.page == bar.page
                and abs(vector.x0 - bar.x0) < 2
                and abs(vector.y1 - bar.y0) < 2
                and abs((vector.x1 - vector.x0) - width) < 3
            ),
            None,
        )
        response_shape.expect(
            weekday_row is not None,
            source_name=source_name,
            detail=f"no weekday row below {calendar.month_name[month]}",
            raw=layout.text[:500],
        )
        assert weekday_row is not None
        height = weekday_row.y1 - weekday_row.y0
        top = weekday_row.y0  # top edge of the first week row

        first_row = [
            fragment
            for fragment in layout.fragments
            if fragment.page == bar.page
            and bar.x0 - 2 <= fragment.x <= bar.x1
            and top - height < fragment.y < top
            and fragment.text.split()[:1] == ["1"]
        ]
        response_shape.expect(
            len(first_row) == 1,
            source_name=source_name,
            detail=f"no first week found for {calendar.month_name[month]}",
            raw=layout.text[:500],
        )
        first_column = min(6, max(0, int((first_row[0].x - bar.x0) // width)))
        year = _month_year(month, first_column, candidates)
        response_shape.expect(
            year is not None,
            source_name=source_name,
            detail=f"could not determine the year of {calendar.month_name[month]}",
            raw=layout.text[:500],
        )
        assert year is not None
        weeks = calendar.monthcalendar(year, month)

        for vector, label in cells:
            if vector.page != bar.page:
                continue
            cx = (vector.x0 + vector.x1) / 2
            cy = (vector.y0 + vector.y1) / 2
            if not (bar.x0 < cx < bar.x1 and top - len(weeks) * height < cy < top):
                continue
            week = int((top - cy) // height)
            day = weeks[week][int((cx - bar.x0) // width)]
            response_shape.expect(
                day != 0,
                source_name=source_name,
                detail=(
                    f"coloured cell outside {calendar.month_name[month]} {year} "
                    "in the calendar PDF"
                ),
                raw=layout.text[:500],
            )
            yield date(year, month, day), label


@final
class Source(BaseSource):
    TITLE = "Nuneaton and Bedworth Borough Council"
    DESCRIPTION = "Source for Nuneaton and Bedworth Borough Council."
    URL = "https://www.nuneatonandbedworth.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Gloucester Close": {"street": "Gloucester Close"},
        "Church Street, Bedworth": {"street": "Church Street, Bedworth"},
    }

    PARAMS = (street(),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your street as the council's 'Find your bin collection day' "
            "directory lists it. Where a street name exists in both towns, add the "
            "town, e.g. 'Church Street, Bedworth'. Garden waste (green bin) dates "
            "only apply if you subscribe to the green bin service."
        ),
        "de": (
            "Gib deine Straße so ein, wie sie im Verzeichnis 'Find your bin "
            "collection day' des Councils steht. Gibt es den Straßennamen in beiden "
            "Orten, ergänze den Ort, z. B. 'Church Street, Bedworth'. Die Termine "
            "für Gartenabfall (grüne Tonne) gelten nur mit Abonnement."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _SEARCH_URL,
                params=lambda street, **_: {
                    "directoryID": _DIRECTORY_ID,
                    "keywords": street.split(",")[0].strip(),
                    "search": "Search directory",
                },
                raise_for_status=True,
                pick=_street_record,
            ),
            retrievers.Lookup(
                lambda record_url, **_: record_url,
                raise_for_status=True,
                pick=_calendar_url,
            ),
        ),
        url=lambda record_url, calendar_url, **_: calendar_url,
        raise_for_status=True,
        timeout=60,
    )
    parse = parsers.PdfLayoutParser(min_fragments=50, min_vectors=100)
    preprocess = preprocessors.Compose(
        _calendar_rows,
        preprocessors.Deduplicate(),
        preprocessors.SortRows(),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
