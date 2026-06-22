import datetime
from collections.abc import Iterable, Mapping
from typing import Literal, TypedDict, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Demonstrates: a recurring schedule published as rules rather than dates, where
# the cadence is "collect on ISO-even / ISO-odd numbered weeks". A describe()
# reads each season window (the only provider-specific part), and the toolkit
# does all the date work: RecurrenceExpander projects a weekly Schedule across
# the window and Schedule.iso_week_parity selects every other week by ISO week
# number (which stays correct across 53-week ISO years like 2026, where naive
# fortnightly stepping would drift). No per-source date arithmetic or parity
# predicate. Note: Calgary has partly moved to Recollect, so this open-data feed
# may not list every collection any more (see doc/ics/recollect.md).

API_URL = "https://data.calgary.ca/resource/jq4t-b745.json"

TYPE_MAP = {"Green": ORGANIC, "Black": GENERAL_WASTE, "Blue": RECYCLABLES}

_parse_window = date_parsers.auto


class ScheduleRecord(TypedDict):
    commodity: str
    summer_start: str
    summer_end: str
    winter_start: str
    winter_end: str
    collection_day_summer: str
    collection_day_winter: str
    clect_int_summer: str
    clect_int_winter: str


def _describe(
    record: Mapping[str, str], source: "BaseSource | None" = None
) -> Iterable[Schedule]:
    """One windowed weekly Schedule per season; EVEN/ODD become an ISO parity.

    Typed as a plain str-mapping (every field ScheduleRecord validates is a
    string) so the by-season key lookups need no literal keys.
    """
    today = datetime.date.today()
    for season in ("summer", "winter"):
        day = recurrence.weekday(record[f"collection_day_{season}"])
        if day is None:
            continue
        start = _parse_window(record[f"{season}_start"])
        end = _parse_window(record[f"{season}_end"])
        interval = record[f"clect_int_{season}"].strip().upper()
        parity: Literal["even", "odd"] | None = None
        if interval == "EVEN":
            parity = "even"
        elif interval == "ODD":
            parity = "odd"
        yield Schedule(
            key=record["commodity"],
            start=recurrence.next_weekday(day, on_or_after=start),
            step=recurrence.WEEKLY,
            not_before=max(start, today),
            until=end,
            iso_week_parity=parity,
        )


@final
class Source(BaseSource):
    TITLE = "Calgary (AB)"
    DESCRIPTION = "Source for Calgary waste collection."
    URL = "https://www.calgary.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True

    # Addresses must be upper case and include a quadrant (e.g. "... SE").
    TEST_CASES = {
        "42 AUBURN SHORES WY SE": {"street_address": "42 AUBURN SHORES WY SE"},
    }

    PARAMS = [text_field("street_address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address in upper case, including the city quadrant "
            "(e.g. `42 AUBURN SHORES WY SE`)."
        ),
    }

    retrieve = HttpGetRetriever(
        url=API_URL,
        params=lambda street_address, **_: {"address": street_address.upper()},
    )
    parse = parsers.JsonParser(shape=list[ScheduleRecord])
    preprocess = preprocessors.RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=TYPE_MAP)

    def __init__(self, street_address: str):
        super().__init__(street_address=street_address)
