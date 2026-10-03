import re
from collections.abc import Iterable
from typing import ClassVar, Literal, final

from waste_collection_schedule import date_parsers, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

API = "https://pubapp.northernbeaches.nsw.gov.au/waste"

# "Wednesday, 8 April": the next service, without a year.
_NEXT_DATE = re.compile(r"<strong>\w+day,?\s+(\d{1,2}\s+\w+)</strong>")
# The calendar link ends in the weekday and the fortnightly zone: ".../ThursdayB.pdf".
_ZONE = re.compile(r"bin-collection-days/\w+([AB])\.pdf")

_parse_next_date = date_parsers.nearest_year("%d %B")

# Weekly collections for about six months, as the legacy source projected.
_WEEKS = 26


def _pick_property(response, *keys, address, **_) -> str:
    """The autocomplete answers ``[{"id": ..., "value": address}, ...]``."""
    results = response.json()
    if not results:
        raise SourceArgumentNotFound("address", address)
    for result in results:
        if result["value"].lower() == address.lower():
            return result["id"]
    if len(results) == 1:
        return results[0]["id"]
    raise SourceArgAmbiguousWithSuggestions(
        "address", address, [result["value"] for result in results]
    )


def _record(page: str, source: "BaseSource | None" = None) -> list[str]:
    return [page]


def _describe(page: str, source: "BaseSource | None" = None) -> Iterable[Schedule]:
    """General waste weekly; recycling and garden organics on alternate weeks.

    The page names only the next service day. Which of the two fortnightly
    streams falls on which ISO-week parity is the zone letter of the calendar
    link: zone B has recycling on even weeks, zone A on odd weeks.
    """
    found = _NEXT_DATE.search(page)
    if not found:
        return
    start = _parse_next_date(found.group(1))
    zone = _ZONE.search(page)
    recycling: Literal["even", "odd"] = "even" if zone and zone[1] == "B" else "odd"
    garden: Literal["even", "odd"] = "odd" if recycling == "even" else "even"
    yield Schedule("General Waste", start, recurrence.WEEKLY, _WEEKS)
    yield Schedule(
        "Recycling", start, recurrence.WEEKLY, _WEEKS, iso_week_parity=recycling
    )
    yield Schedule(
        "Garden Organics", start, recurrence.WEEKLY, _WEEKS, iso_week_parity=garden
    )


@final
class Source(BaseSource):
    TITLE = "Northern Beaches Council (NSW)"
    DESCRIPTION = "Source for Northern Beaches Council waste collection."
    URL = "https://www.northernbeaches.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Manly": {"address": "25 Pittwater Road MANLY"},
        "Brookvale": {"address": "25 Old Pittwater Road BROOKVALE"},
        "Dee Why": {"address": "10 Howard Avenue DEE WHY"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as shown on the Northern Beaches Council "
            "website, including the suburb in uppercase, e.g. "
            "'25 Pittwater Road MANLY'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/waste.ashx",
                params=lambda address, **_: {"term": address},
                pick=_pick_property,
            ),
        ),
        url=f"{API}/wastesearch.ashx",
        method="POST",
        data=lambda key, **_: {"property": key},
    )

    parse = parsers.TextParser()

    preprocess = Compose(_record, RecurrenceExpander(_describe))

    transform = ICSTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Organics": wt.GARDEN_WASTE,
        },
    )
