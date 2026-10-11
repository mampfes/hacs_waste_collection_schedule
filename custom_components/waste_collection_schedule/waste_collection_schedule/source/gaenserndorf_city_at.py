from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import integer, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Lookup
from waste_collection_schedule.service.Jolioo import CalendarParser, call
from waste_collection_schedule.transformers import RowTransformer

# The app's key and secret ship inside the Gänserndorf app.
_KEY = "e74b7a2955428b2ab520"
_SECRET = "3646728f96cf464aff7e"

_TYPE_MAP = {
    "Restmüll": wt.GENERAL_WASTE,
    "Restmüll Wohnblöcke 2-Wochen-Tour": wt.GENERAL_WASTE,
    "Biomüll": wt.ORGANIC,
    "Altpapier": wt.PAPER,
    "Altpapier Großcontainer": wt.PAPER,
    "Leicht- & Metallverpackungen/Gelbe Tonne/Gelber Sack": wt.RECYCLABLES,
    "Sondermüll": wt.HAZARDOUS,
}


def _calendar_id(response, *_, street, calendar_index=0, **__) -> int:
    """The id of the calendar that serves the street (case-insensitive)."""
    streets = response.json()["data"].get("street_structure", [])
    match = next(
        (
            s
            for s in streets
            if s["garbage_calendar_street"].lower() == str(street).lower()
        ),
        None,
    )
    if match is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street, sorted(s["garbage_calendar_street"] for s in streets)
        )
    calendars = match["garbage_calendars_available"]
    index = calendar_index or 0
    if index >= len(calendars):
        raise SourceArgumentNotFoundWithSuggestions(
            "calendar_index", index, [str(i) for i in range(len(calendars))]
        )
    return calendars[index]


@final
class Source(BaseSource):
    TITLE = "Gänserndorf City / Gänserndorf App"
    DESCRIPTION = (
        "Source for waste collection schedule for the city of Gänserndorf, Austria. "
        "Uses the Jolioo mobile app API."
    )
    URL = "https://www.gaenserndorf.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    # "Altpapier" and "Altpapier Großcontainer" (and the two residual-waste
    # rounds) can fall on one day; the original label stays in the description
    # and the duplicates collapse by default.
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Baumschulweg": {"street": "Baumschulweg"},
        "Ahornweg": {"street": "Ahornweg"},
        "Siebenbrunner Straße (first calendar)": {
            "street": "Siebenbrunner Straße",
            "calendar_index": 0,
        },
    }

    PARAMS = (
        street(),
        integer("calendar_index", "Calendar Index", default=0),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the name of your street as shown in the Gänserndorf App. "
            "`calendar_index` (starting at 0) picks the calendar when a street "
            "maps to several."
        ),
        "de": (
            "Gib den Straßennamen so an, wie er in der Gänserndorf-App steht. "
            "`calendar_index` (ab 0) wählt den Kalender, wenn eine Straße "
            "mehreren Kalendern zugeordnet ist."
        ),
    }

    retrieve = call(
        _KEY,
        _SECRET,
        "garbagecalendar",
        lambda calendar_id, **_: {
            "language": "de",
            "garbage_calendar_id": str(calendar_id),
        },
        before=(
            Lookup(
                call(
                    _KEY,
                    _SECRET,
                    "garbagecalendarindexwithstreets",
                    {"language": "de", "garbage_calendar_id": "1"},
                ),
                pick=_calendar_id,
            ),
        ),
    )
    parse = CalendarParser(children_only=True)
    transform = RowTransformer(type_value_map=_TYPE_MAP, carry_raw_label=True)
