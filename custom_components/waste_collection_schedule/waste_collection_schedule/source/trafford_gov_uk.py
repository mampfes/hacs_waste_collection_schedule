"""Waste collection schedules for Trafford Council, England.

Trafford resolves a postcode to an address-specific PDF. The PDF prints each
collection date beside a coloured vector marker rather than a textual bin name,
so ``PdfLayoutParser`` exposes both layers and ``_calendar_rows`` associates the
markers with their dates. Food waste shares the weekly green-bin collection;
garden waste is included on those dates only for paid permit holders.
"""

import json
import re
from collections.abc import Iterable
from datetime import date
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers, preprocessors, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, postcode, street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_LOOKUP_URL = "https://apps.trafford.gov.uk/bincollections/"

_TYPE_MAP = {
    "Blue bin": wt.PAPER,
    "Black bin": wt.RECYCLABLES,
    "Grey bin": wt.GENERAL_WASTE,
    "Food waste": wt.FOOD_WASTE,
    "Garden waste": wt.GARDEN_WASTE,
}

_SYMBOL_COLOURS = {
    "Blue bin": (0.712, 0.141, 0.0, 0.0),
    "Black bin": (0.67, 0.573, 0.52, 0.552),
    "Grey bin": (0.4, 0.3, 0.3, 0.25),
}
_COLOUR_TOLERANCE = 0.025
_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_MONTH_RE = re.compile(rf"^({'|'.join(_MONTHS)})\s+(20\d{{2}})$", re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{2}$")
_COLLECTION_DATA_RE = re.compile(
    r"const\s+collectionData\s*=\s*JSON\.parse\((\"(?:\\.|[^\"\\])*\")\);"
)
_GREEN_SUSPENSION_RE = re.compile(
    r"Green bin collections will be suspended from\s+"
    r"(\d{1,2})\s+to\s+(\d{1,2})\s+([A-Za-z]+)",
    re.IGNORECASE,
)


def _normalise(value: str) -> str:
    return " ".join(value.split()).casefold()


def _collection_data(html: str) -> list[dict[str, Any]]:
    match = _COLLECTION_DATA_RE.search(html)
    response_shape.expect(
        match is not None,
        source_name="Trafford Council",
        detail="postcode lookup returned no collection data",
        raw=html[:500],
    )
    assert match is not None
    return json.loads(json.loads(match.group(1)))


def _calendar_url(response, *_, address: str, **__) -> str:
    """Resolve the configured address to the calendar link in the lookup HTML."""
    data = _collection_data(response.text)
    wanted = _normalise(address)
    exact = next(
        (item for item in data if _normalise(str(item.get("Address", ""))) == wanted),
        None,
    )
    if exact is None:
        suggestions = [
            str(item["Address"])
            for item in data
            if wanted in _normalise(str(item.get("Address", "")))
        ]
        if not suggestions:
            suggestions = [str(item["Address"]) for item in data]
        raise SourceArgumentNotFoundWithSuggestions("address", address, suggestions)

    for collection in exact.get("Collections", []):
        if calendar_url := collection.get("CalendarLink"):
            return str(calendar_url)
    response_shape.expect(
        False,
        source_name="Trafford Council",
        detail=f"postcode lookup returned no calendar for {address}",
        raw=response.text[:500],
    )
    raise AssertionError("unreachable")


def _colour_matches(
    actual: tuple[float, ...] | None, expected: tuple[float, ...]
) -> bool:
    return bool(
        actual
        and len(actual) == len(expected)
        and all(
            abs(actual[index] - expected[index]) <= _COLOUR_TOLERANCE
            for index in range(len(expected))
        )
    )


def _symbol_type(vector: parsers.PdfVector) -> str | None:
    width = vector.x1 - vector.x0
    height = vector.y1 - vector.y0
    if not (8 <= width <= 10 and 8 <= height <= 10):
        return None
    for waste_type, expected in _SYMBOL_COLOURS.items():
        if _colour_matches(vector.fill_color, expected):
            return waste_type
    return None


def _green_suspension(
    text: str, years_by_month: dict[int, int]
) -> tuple[date, date] | None:
    match = _GREEN_SUSPENSION_RE.search(text)
    if match is None:
        return None
    month = _MONTHS.get(match.group(3).casefold())
    if month is None or month not in years_by_month:
        return None
    year = years_by_month[month]
    return (
        date(year, month, int(match.group(1))),
        date(year, month, int(match.group(2))),
    )


def _calendar_rows(
    records: parsers.PdfDocumentLayout, source: BaseSource | None = None
) -> Iterable[tuple[date, str]]:
    """Associate each printed collection date with its coloured bin marker."""
    layout = records
    months: list[tuple[int, float, float, int, int]] = []
    years_by_month: dict[int, int] = {}
    for fragment in layout.fragments:
        if match := _MONTH_RE.fullmatch(fragment.text):
            month = _MONTHS[match.group(1).casefold()]
            year = int(match.group(2))
            months.append((fragment.page, fragment.x, fragment.y, month, year))
            years_by_month[month] = year

    source_name = response_shape.source_name(source)
    response_shape.expect(
        bool(months),
        source_name=source_name,
        detail="no month rows found in Trafford calendar PDF",
        raw=layout.text[:500],
    )

    symbols = [
        (vector, waste_type)
        for vector in layout.vectors
        if (waste_type := _symbol_type(vector)) is not None
    ]
    suspension = _green_suspension(layout.text, years_by_month)
    garden_waste = bool(source and source.params.get("garden_waste"))

    for page, month_x, month_y, month, year in months:
        date_fragments = (
            fragment
            for fragment in layout.fragments
            if fragment.page == page
            and _DATE_RE.fullmatch(fragment.text)
            and fragment.x > month_x
            and abs(fragment.y - month_y) <= 4
        )
        for fragment in date_fragments:
            collection_date = date(year, month, int(fragment.text))
            matches = [
                waste_type
                for vector, waste_type in symbols
                if vector.page == page
                and abs(vector.x1 - fragment.x) <= 1.5
                and abs(vector.y0 - fragment.y) <= 4
            ]
            response_shape.expect(
                len(matches) == 1,
                source_name=source_name,
                detail=(
                    "could not determine one bin type for Trafford collection "
                    f"date {collection_date.isoformat()} (found {len(matches)})"
                ),
                raw=layout.text[:500],
            )

            yield collection_date, matches[0]
            green_suspended = bool(
                suspension and suspension[0] <= collection_date <= suspension[1]
            )
            if green_suspended:
                continue
            yield collection_date, "Food waste"
            if garden_waste:
                yield collection_date, "Garden waste"


@final
class Source(BaseSource):
    TITLE = "Trafford Council"
    DESCRIPTION = "Waste collection schedules for Trafford Council."
    URL = "https://www.trafford.gov.uk/BinCollections/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@rbiddulph"]

    WASTE_TYPES: ClassVar[list] = [
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "130A Flixton Road": {
            "postcode": "M41 5BG",
            "address": "130A Flixton Road, Urmston, Trafford, Manchester, M41 5BG",
        },
        "130A Flixton Road with garden waste permit": {
            "postcode": "M41 5BG",
            "address": "130A Flixton Road, Urmston, Trafford, Manchester, M41 5BG",
            "garden_waste": True,
        },
    }

    PARAMS = (
        postcode(),
        street_address(),
        boolean(
            "garden_waste",
            label="Paid garden-waste permit",
            default=False,
        ),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter the postcode and the full address returned by Trafford Council. "
            "Submit part of the address once to receive matching suggestions. Enable "
            "garden waste only if the green bin displays a valid paid permit; food "
            "waste is collected from green bins without a permit."
        )
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _LOOKUP_URL,
                method="POST",
                data=lambda postcode, **_: {"Postcode": postcode},
                raise_for_status=True,
                pick=_calendar_url,
            ),
        ),
        url=lambda calendar_url, **_: calendar_url,
        raise_for_status=True,
        timeout=60,
    )
    parse = parsers.PdfLayoutParser(min_fragments=50, min_vectors=50)
    preprocess = preprocessors.Compose(
        _calendar_rows,
        preprocessors.Deduplicate(),
        preprocessors.SortRows(),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
