"""Vogel Disposal Service (Mars, PA) residential collection calendar."""

from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import HtmlTransformer

API_BASE = "https://www.vogeldisposal.com"
LOOKUP_URL = f"{API_BASE}/collectionlookup.aspx"
CALENDAR_URL = f"{API_BASE}/collectioncalendar.aspx"


def _norm(value: str) -> str:
    return " ".join(str(value).upper().replace(".", "").split())


def _municipality(response, *keys, municipality, **_) -> str:
    """The canonical name ("BUTLER TWP, BUTLER COUNTY") of a typed municipality."""
    candidates = response.json().get("d") or []
    wanted = _norm(municipality).split(",")[0]
    for city in candidates:
        if _norm(city).split(",")[0] == wanted:
            return city
    if len(candidates) == 1:
        return candidates[0]
    raise SourceArgumentNotFoundWithSuggestions(
        "municipality", municipality, candidates
    )


def _address(response, *keys, address, **_) -> str:
    """The provider's spelling of a typed street address."""
    suggestions = response.json().get("d") or []
    for candidate in suggestions:
        if _norm(candidate) == _norm(address):
            return candidate
    if len(suggestions) == 1:
        return suggestions[0]
    raise SourceArgumentNotFoundWithSuggestions("address", address, suggestions)


def _pickup_info(response, *keys, address, **_) -> dict:
    """The collection weekdays and frequency the calendar page is drawn from."""
    info = response.json().get("d")
    if isinstance(info, dict) and info.get("success"):
        return info
    raise SourceArgumentNotFound(
        "address", address, "Vogel Disposal has no schedule for this address."
    )


def _day(cell) -> str:
    """The cell's date, written as "5 November 2026" from its month's title."""
    month = cell.find_parent("table", class_="monthTable")
    title = month.select_one(".calendarTitleBar").get_text(" ", strip=True)
    return f"{cell.get_text(strip=True)} {title}"


@final
class Source(BaseSource):
    TITLE = "Vogel Disposal Service"
    DESCRIPTION = (
        "Residential trash and recycling collection schedules for "
        "Vogel Disposal Service (Mars, PA)."
    )
    URL = "https://www.vogeldisposal.com/"
    COUNTRY = "us"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@jcarr"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Butler Twp 1002 Tudor Dr": {
            "municipality": "BUTLER TWP, BUTLER COUNTY",
            "address": "1002 TUDOR DR",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {
            "municipality": "butler twp",
            "address": "99999 NOWHERE RD",
        },
    }

    PARAMS = (municipality(), street_address())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your municipality and street address. Exact spelling is not "
            "required: a rough municipality (for example 'butler twp') and a "
            "partial street address (for example '1002 tudor') are matched "
            "automatically. If the input matches more than one place, the "
            "matching options are shown so you can pick the right one. Since the "
            "v3 pipeline migration, waste types use canonical, localised names. "
            "Update filters, automations and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    # The municipality search is a prefix search that finds nothing for the
    # full canonical name, so it is asked for the first word only.
    retrieve = retrievers.YearlyRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(
                f"{LOOKUP_URL}/GetCities",
                method="POST",
                json=lambda municipality, **_: {
                    "strInput": (str(municipality).split(",")[0].split() or [""])[0]
                },
                pick=_municipality,
            ),
            retrievers.Lookup(
                f"{LOOKUP_URL}/GetSuggestedAddresses",
                method="POST",
                json=lambda city, address, **_: {
                    "strAddress": str(address).strip(),
                    "municipality": city,
                },
                pick=_address,
            ),
            retrievers.Lookup(
                f"{LOOKUP_URL}/GetPickupInfoByAddress",
                method="POST",
                json=lambda city, street, **_: {
                    "municipality": city,
                    "strAddress": street,
                },
                pick=_pickup_info,
            ),
        ),
        # Next year's calendar is published ahead of time; it is fetched all
        # year round, best-effort, so the schedule keeps rolling past December.
        fetch=retrievers.Request(
            CALENDAR_URL,
            params=lambda year, context, **_: {
                "rw": context[2]["frequency"],
                "cd": context[2]["weekdayNumber"],
                "rd": context[2]["recycleDayNumber"],
                "yr": year,
            },
        ),
        rollover_month=1,
    )

    # Collection days are marked by the class of their day cell; a recycling
    # day is a trash day as well.
    parse = parsers.EachResponse(
        parsers.HtmlParser(
            "table.monthTable td.pickupDay, table.monthTable td.recycleDay"
        )
    )

    transform = HtmlTransformer(
        date_getter=_day,
        type_getter=lambda cell: cell["class"][0],
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "pickupDay": wt.GENERAL_WASTE,
            "recycleDay": [wt.GENERAL_WASTE, wt.RECYCLABLES],
        },
    )
