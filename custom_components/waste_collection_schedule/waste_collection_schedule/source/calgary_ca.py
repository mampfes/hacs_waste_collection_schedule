import datetime
from collections.abc import Iterable, Mapping
from typing import TypedDict, final

from waste_collection_schedule import date_parsers, parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Demonstrates: a recurring schedule published as rules rather than dates, where
# the cadence is "collect on ISO-even / ISO-odd numbered weeks". That parity rule
# diverges from plain fortnightly stepping in 53-week ISO years (e.g. 2026), so
# it cannot be a fortnightly Schedule. Instead a method preprocess() generates
# the weekly candidates within each season window via recurrence.recurring_within
# (no per-source date arithmetic) and applies Calgary's own even/odd-week
# predicate — provider business logic, kept local. Note: Calgary has partly moved
# to Recollect, so this open-data feed may not list every collection any more
# (see doc/ics/recollect.md).

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


def _parity_matches(day: datetime.date, interval: str) -> bool:
    """Calgary's cadence: EVERY week, or only ISO-EVEN / ISO-ODD numbered weeks."""
    if interval == "EVERY":
        return True
    week_is_even = day.isocalendar().week % 2 == 0
    return week_is_even if interval == "EVEN" else not week_is_even


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
    transform = ICSTransformer(type_value_map=TYPE_MAP)

    def __init__(self, street_address: str):
        super().__init__(street_address=street_address)

    def preprocess(
        self, records: list[Mapping[str, str]], source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        # Typed as a plain str-mapping (every field validated by ScheduleRecord is
        # a string) so the by-season key lookups below need no literal keys.
        today = datetime.date.today()
        for entry in records:
            commodity = entry["commodity"]
            for season in ("summer", "winter"):
                day = recurrence.weekday(entry[f"collection_day_{season}"])
                if day is None:
                    continue
                start = _parse_window(entry[f"{season}_start"])
                end = _parse_window(entry[f"{season}_end"])
                interval = entry[f"clect_int_{season}"].strip().upper()
                # One collection-weekday per week within the (still upcoming part
                # of the) season window; parity then thins it to every other week.
                seed = recurrence.next_weekday(day, on_or_after=start)
                for collection_date in recurrence.recurring_within(
                    seed,
                    recurrence.WEEKLY,
                    not_before=max(start, today),
                    until=end,
                ):
                    if _parity_matches(collection_date, interval):
                        yield collection_date, commodity
