import re
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

# Suburb + street name + street number (the suburb is a fixed dropdown; the
# combined "street_number street_name SUBURB" string is what IntraMaps expects
# as a single address search string). Two verge-collection columns are a
# single explicit date (no recurrence). The three household-bin columns
# (FOGO, Recycle, Waste) each carry their OWN cadence per record -- the same
# column is "weekly" in one suburb and "fortnightly" in another, and
# occasionally neither word appears at all (a single, non-recurring pickup) --
# so the cadence is read from that record's own text rather than assumed from
# the column, windowed one year out from today to match the council's own
# horizon. The only source-specific code is _describe, which tells the
# columns apart and reads each one's cadence.

SUBURBS = (
    "BALDIVIS",
    "COOLOONGUP",
    "EAST ROCKINGHAM",
    "GARDEN ISLAND",
    "GOLDEN BAY",
    "HILLMAN",
    "KARNUP",
    "KERALUP",
    "PERON",
    "PORT KENNEDY",
    "ROCKINGHAM",
    "SAFETY BAY",
    "SECRET HARBOUR",
    "SHOALWATER",
    "SINGLETON",
    "WAIKIKI",
    "WARNBRO",
)

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://maps.rockingham.wa.gov.au",
    project="1917ad36-6a1d-4145-9eeb-736f8fa9646d",
)

# IntraMaps column name -> canonical waste type.
_VERGE_GREEN_WASTE = "Verge_Collection_Green_Waste"
_VERGE_GENERAL = "Verge_Collection_General"
_FOGO = "FOGO Bin (FOGO lid)"
_RECYCLE = "Recycle (Yellow Lid)"
_WASTE = "Waste (Red Lid)"

_TYPE_MAP = {
    _WASTE: GENERAL_WASTE,
    _RECYCLE: RECYCLABLES,
    _FOGO: ORGANIC,
    _VERGE_GREEN_WASTE: GARDEN_WASTE,
    _VERGE_GENERAL: BULKY_WASTE,
}

_VERGE_COLUMNS = {_VERGE_GREEN_WASTE, _VERGE_GENERAL}

_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")
_WEEKDAY_RE = re.compile(
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", re.IGNORECASE
)

# The council's own bin-day tool projects recurring collections one year
# ahead of today; match that horizon (windowed Schedule) rather than the
# repo's usual fixed count, so the converted source finds the same range of
# dates as the legacy fetch().
_HORIZON = timedelta(days=365)


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    if column in _VERGE_COLUMNS:
        # A single explicit date (e.g. "Monday, 23 November 2026"); no
        # recurrence. Extract just the date rather than parsing the whole
        # string, in case the provider adds wording dateutil can't handle
        # unaided.
        match = _DATE_RE.search(text)
        if not match:
            return
        try:
            event_date = date_parsers.auto(match.group(1))
        except (ValueError, TypeError):
            return
        yield Schedule(column, event_date, count=1)
        return

    # FOGO / Recycle / Waste: an explicit date if one is given (e.g.
    # "Collected fortnightly Wednesday 15 July 2026"), else a bare weekday
    # name (e.g. "Collected weekly on Wednesday").
    date_match = _DATE_RE.search(text)
    if date_match:
        try:
            start = date_parsers.auto(date_match.group(1))
        except (ValueError, TypeError):
            return
    else:
        weekday_match = _WEEKDAY_RE.search(text)
        if not weekday_match:
            return
        weekday = recurrence.weekday(weekday_match.group(1))
        if weekday is None:
            return
        start = recurrence.next_weekday(weekday)

    # The cadence word, not the column, decides weekly vs. fortnightly: the
    # same column is one or the other depending on suburb. Neither word
    # present (a council data quirk, e.g. "Collected monday Monday ...")
    # means a single, non-recurring pickup.
    text_lower = text.lower()
    if "fortnightly" in text_lower:
        yield Schedule(
            column, start, recurrence.FORTNIGHTLY, until=date.today() + _HORIZON
        )
    elif "weekly" in text_lower:
        yield Schedule(column, start, recurrence.WEEKLY, until=date.today() + _HORIZON)
    else:
        yield Schedule(column, start, count=1)


@final
class Source(BaseSource):
    TITLE = "City of Rockingham"
    DESCRIPTION = "Source for the City of Rockingham rubbish collection."
    URL = (
        "https://rockingham.wa.gov.au/your-services/waste-and-recycling/bin-collection"
    )
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "IGA Baldivis Quarter": {
            "suburb": "Baldivis",
            "street_name": "Makybe Drive",
            "street_number": "59",
        },
        "The Warnbro Tavern": {
            "suburb": "Warnbro",
            "street_name": "Hokin Street",
            "street_number": "7",
        },
        "The Shoalwater Tavern": {
            "suburb": "Shoalwater",
            "street_name": "Second Avenue",
            "street_number": "62",
        },
    }

    PARAMS = (
        dropdown("suburb", list(SUBURBS), label="Suburb"),
        text_field("street_name", "Street Name"),
        text_field("street_number", "Street Number"),
    )

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, suburb: str, street_name: str, street_number: str):
        suburb_upper = suburb.strip().upper()
        if suburb_upper not in SUBURBS:
            raise SourceArgumentNotFoundWithSuggestions("suburb", suburb, list(SUBURBS))

        address = f"{street_number} {street_name} {suburb_upper}"
        super().__init__(
            suburb=suburb,
            street_name=street_name,
            street_number=street_number,
            address=address,
        )
