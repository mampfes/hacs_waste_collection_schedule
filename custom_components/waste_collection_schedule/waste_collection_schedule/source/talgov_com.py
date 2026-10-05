import math
from datetime import date
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

ADDRESS_URL = "https://handlersp.talgov.com/autosuggest/UtilSWAddressListUmax.ashx"
SCHEDULE_URL = "https://handlersp.talgov.com/solidwaste/UtilSWRedBlueUmax.ashx"

GARBAGE_RECYCLING = "Garbage/Recycling"
BULKY_YARD_WASTE = "Bulky Items/Yard Waste"

# How many weeks ahead to project the weekly garbage/recycling schedule.
WEEKLY_WEEKS_AHEAD = 26

# How many weeks ahead to scan for the biweekly Red/Blue bulky/yard waste
# schedule (produces roughly half as many actual collection dates).
BULK_WEEKS_AHEAD = 52


def _normalize(address: str) -> str:
    return " ".join(str(address).split()).strip().lower()


def _services(response, *keys, address, **_) -> list[tuple[str, str]]:
    """The autosuggest answers ``[{address, customernumber, serviceid}, ...]``.

    Every entry whose address equals the one asked for is a service of that
    address (a commercial address may have several), so all of them are kept.
    """
    entries = response.json()
    target = _normalize(address)
    matches = [
        (entry["customernumber"], entry["serviceid"])
        for entry in entries
        if _normalize(entry.get("address", "")) == target
    ]
    if matches:
        return matches
    suggestions = sorted(
        {entry["address"].strip() for entry in entries if entry.get("address")}
    )
    if suggestions:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, suggestions[:10]
        )
    raise SourceArgumentNotFound("address", address)


def _week_color(d: date) -> str:
    """Replicate the Red/Blue week calculation used by talgov.com's own
    client-side script (see the `RedBlueWeek` logic on
    https://www.talgov.com/you/swslookup): a simple (non-ISO) week-of-year
    count where week 1 is always "Red".
    """
    year_start = date(d.year, 1, 1)
    days_diff = (d - year_start).days
    # JavaScript's Date.getDay(): Sunday=0 ... Saturday=6.
    js_year_start_weekday = (year_start.weekday() + 1) % 7
    week_no = math.ceil((days_diff + js_year_start_weekday + 1) / 7)
    return "Red" if week_no % 2 == 0 else "Blue"


def _describe(row, source):
    """Weekly garbage/recycling on every pickup day, plus the Red/Blue bulk day."""
    for day_name in (
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ):
        weekday = recurrence.weekday(day_name)
        if row.get(f"pickup{day_name}") == "Yes" and weekday is not None:
            yield Schedule(
                GARBAGE_RECYCLING,
                recurrence.next_weekday(weekday),
                recurrence.WEEKLY,
                WEEKLY_WEEKS_AHEAD,
            )

    parts = (row.get("yw_bulk") or "").split()
    if len(parts) == 2:
        color, day_name = parts
        weekday = recurrence.weekday(day_name)
        if weekday is not None and color in ("Red", "Blue"):
            start = recurrence.next_weekday(weekday)
            weeks = recurrence.recurring(start, recurrence.WEEKLY, BULK_WEEKS_AHEAD)
            yield Schedule(
                BULKY_YARD_WASTE,
                start,
                recurrence.WEEKLY,
                BULK_WEEKS_AHEAD,
                exclude=[d for d in weeks if _week_color(d) != color],
            )


@final
class Source(BaseSource):
    TITLE = "City of Tallahassee"
    DESCRIPTION = "Source for City of Tallahassee, FL waste, recycling and bulky item/yard waste collection."
    URL = "https://www.talgov.com/you/swslookup"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "400 S Monroe St": {"address": "400 S Monroe St"},
        "2001 Trescott Dr (Red Thursday bulk)": {"address": "2001 Trescott Dr"},
        "1004 Piney Z Plantation Rd (Blue Friday bulk)": {
            "address": "1004 Piney Z Plantation Rd"
        },
    }

    PARAMS = (street_address("address"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street address as shown in the City of Tallahassee "
            "[solid waste lookup](https://www.talgov.com/you/swslookup), "
            "e.g. '400 S Monroe St'."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            ADDRESS_URL,
            params=lambda address, **_: {"address": address},
            pick=_services,
        ),
        targets=lambda source, services: services,
        fetch=retrievers.Request(
            SCHEDULE_URL,
            params=lambda service, services, **_: {
                "customernumber": service[0],
                "serviceid": service[1],
            },
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser())
    preprocess = Compose(RecurrenceExpander(_describe), Deduplicate())
    transform = ICSTransformer(
        type_value_map={
            GARBAGE_RECYCLING: [wt.GENERAL_WASTE, wt.RECYCLABLES],
            BULKY_YARD_WASTE: [wt.BULKY_WASTE, wt.GARDEN_WASTE],
        }
    )
