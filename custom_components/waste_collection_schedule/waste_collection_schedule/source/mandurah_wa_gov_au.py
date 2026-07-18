import re
from datetime import timedelta
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    Compose,
    HolidayShift,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# Weekly general waste (a bare weekday name) plus fortnightly recycling (an
# explicit "next date"), with a Christmas Day collection shifted to Boxing Day.
# The only source-specific code is _describe (telling the two columns apart)
# and _adjust_for_christmas (the holiday shift).

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://maps.mandurah.wa.gov.au",
    instance="IntraMaps910",
    config_id="00000000-0000-0000-0000-000000000000",
    project="a510900b-e9b6-48e2-a541-8f4ea5bc2214",
    lite_config_id="e7feb691-ab8c-40e9-a7ab-bd73b298b789",
    module_id="8e8074e1-317a-4de0-ac28-4d9739285994",
    default_selection_layer="6aac01c4-fdb9-4b3b-830e-31bc2814aaea",
)

# IntraMaps column name -> canonical waste type.
_TYPE_MAP = {
    "Refuse Day": GENERAL_WASTE,
    "Next Recycle Day is ": RECYCLABLES,
}

# The recycling value is free text such as "next Friday - 17 Jul 2026" or
# "Wednesday - 22 Jul 2026"; pull out just the date rather than parsing the
# whole string (the "next Friday" wording otherwise defeats dateutil).
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    if column == "Refuse Day":
        weekday = recurrence.weekday(text)
        if weekday is None:
            return
        yield Schedule(column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26)
        return

    match = _DATE_RE.search(text)
    if not match:
        return
    try:
        next_date = date_parsers.auto(match.group(1))
    except (ValueError, TypeError):
        return
    yield Schedule(column, next_date, recurrence.FORTNIGHTLY, 13)


def _adjust_for_christmas(collection_date, key, source):
    """Shift a 25 December collection to Boxing Day."""
    if collection_date.month == 12 and collection_date.day == 25:
        return collection_date + timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "City of Mandurah"
    DESCRIPTION = "Source for City of Mandurah waste collection."
    URL = "https://www.mandurah.wa.gov.au/live/waste-and-recycling/bin-collections"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Bouvard - Bouvard Estuary Foreshore": {
            "address": "Estuary RD BOUVARD",
        },
        "Clifton - Old Coast Road Buffer": {
            "address": "Old Coast RD CLIFTON",
        },
        "Coodanup - Coodanup Community College": {
            "address": "Steerforth DR COODANUP",
        },
        "Dawesville - Dawesville Foreshore": {
            "address": "Estuary RD DAWESVILLE",
        },
        "Dudley Park - Dudley Park Bowling Club": {
            "address": "Gillark ST DUDLEY PARK",
        },
        "Erskine - Erskine Ablution": {
            "address": "Bridgewater BVD ERSKINE",
        },
        "Falcon - Falcon Pavilion": {
            "address": "Flame ST FALCON",
        },
        "Greenfields - Bortolo Pavilion": {
            "address": "Bortolo DR GREENFIELDS",
        },
        "Halls Head - Halls Head Community Recreation Centre": {
            "address": "Fuchsia PL HALLS HEAD",
        },
        "Herron - Herron Foreshore": {
            "address": "Hexham CL HERRON",
        },
        "Lakelands - Lakelands Library and Community Centre": {
            "address": "49 Banksiadale GTE LAKELANDS",
        },
        "Madora Bay - Madora Bay Central Ablution": {
            "address": "Sabina DR MADORA BAY",
        },
        "Mandurah - Mandurah Administration Centre": {
            "address": "3 Peel ST MANDURAH",
        },
        "Meadow Springs - Quarry Adventure Park": {
            "address": "Pebble Beach BVD MEADOW SPRINGS",
        },
        "Parklands - Lakes Lawn Cemetery": {
            "address": "Stock RD PARKLANDS",
        },
        "San Remo - San Remo Beach": {
            "address": "Acheron RD SAN REMO",
        },
        "Silver Sands - Henson Reserve": {
            "address": "Henson ST SILVER SANDS",
        },
        "Wannanup - Port Bouvard Marina": {
            "address": "Rees PL WANNANUP",
        },
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb. "
            "Search at https://www.mandurah.wa.gov.au/live/waste-and-recycling/"
            "bin-collections"
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = Compose(
        RecurrenceExpander(_describe), HolidayShift(_adjust_for_christmas)
    )

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
