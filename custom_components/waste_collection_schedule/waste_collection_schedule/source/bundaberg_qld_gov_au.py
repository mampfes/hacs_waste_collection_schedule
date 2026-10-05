import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://microapps.bundaberg.qld.gov.au/bin_dates/livesearch.php"

# Guide date (Sunday) used to determine Week A vs B for fortnightly recycling
GUIDE_DATE = datetime.date(2020, 10, 18)

# JavaScript Date.getDay() (0=Sun) -> Python weekday() (0=Mon)
_JS_TO_PY_WEEKDAY = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}


def _week_code(d: datetime.date) -> str:
    return "A" if ((d - GUIDE_DATE).days // 7) % 2 == 0 else "B"


def _pick_address(divs, source):
    """The suburb's ``<div>`` (the first one when no suburb is given).

    Each ``<div id=...>`` is ``address,wasteDay,recDay,recWeek`` or, after the
    2022 changeover, ``address,wasteDay,recDay,recWeek,newWaste,newRec,newRecWeek``.
    """
    params = source.params
    query = f"{params['street_number']} {params['street_name']}"
    if not divs:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_number/street_name", query, []
        )
    suburb = (params.get("suburb") or "").upper()
    if not suburb:
        yield divs[0]["id"]
        return
    for div in divs:
        if suburb in div["id"].upper():
            yield div["id"]
            return
    raise SourceArgumentNotFoundWithSuggestions(
        "suburb", suburb, [d.get_text(strip=True) for d in divs]
    )


def _describe(record, source):
    parts = record.split(",")
    # Post-2022 changeover: use the new codes when present.
    if len(parts) >= 7:
        waste_js, rec_js, rec_week = int(parts[4]), int(parts[5]), parts[6].strip()
    elif len(parts) >= 4:
        waste_js, rec_js, rec_week = int(parts[1]), int(parts[2]), parts[3].strip()
    else:
        raise ValueError(f"Unexpected response format: {record}")

    yield Schedule(
        "General Waste",
        recurrence.next_weekday(_JS_TO_PY_WEEKDAY[waste_js]),
        recurrence.WEEKLY,
        52,
    )

    start = recurrence.next_weekday(_JS_TO_PY_WEEKDAY[rec_js])
    if _week_code(start) != rec_week:
        start += recurrence.WEEKLY
    yield Schedule("Recycling", start, recurrence.FORTNIGHTLY, 26)


@final
class Source(BaseSource):
    TITLE = "Bundaberg Regional Council"
    DESCRIPTION = "Source for Bundaberg Regional Council, QLD, Australia."
    URL = "https://www.bundaberg.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "10 Maynard Street Avenell Heights": {
            "street_number": "10",
            "street_name": "Maynard",
            "suburb": "AVENELL HEIGHTS",
        },
        "1 Bourbong Street Bundaberg East": {
            "street_number": "1",
            "street_name": "Bourbong",
            "suburb": "BUNDABERG EAST",
        },
    }

    PARAMS = (
        house_number("street_number"),
        street("street_name"),
        city("suburb", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street number and street name (without the street type, "
            "e.g. 'Maynard' for Maynard Street), and the suburb in capitals, "
            "e.g. 'AVENELL HEIGHTS'. Without a suburb the first matching "
            "address is used. General waste is collected weekly and recycling "
            "fortnightly."
        ),
    }

    retrieve = retrievers.Request(
        API_URL,
        params=lambda street_number, street_name, **_: {
            "q": f"{street_number} {street_name}"
        },
    )

    parse = parsers.HtmlParser("div")

    preprocess = Compose(_pick_address, RecurrenceExpander(_describe))

    transform = ICSTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
