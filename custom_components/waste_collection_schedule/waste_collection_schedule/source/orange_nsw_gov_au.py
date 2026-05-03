import datetime
import logging

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Orange City Council"
DESCRIPTION = "Source for Orange City Council residential waste collection, NSW, Australia."
URL = "https://www.orange.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Zone A (West of Anson Street)": {"zone": "A"},
    "Zone B (East of Anson Street, Spring Hill, Lucknow, Clifton Grove)": {"zone": "B"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = """
Orange City Council divides the city into two fortnightly recycling zones based on
location relative to Anson Street:

- **Zone A**: Properties west of Anson Street
- **Zone B**: Properties east of Anson Street, properties ON Anson Street,
  and properties in Spring Hill, Lucknow, and Clifton Grove

General waste (red/dark lid) is collected **every Wednesday**.
Recycling (yellow lid) is collected **fortnightly on Wednesdays**, alternating
between Zone A and Zone B.

Visit https://www.orange.nsw.gov.au/waste/ to download the annual waste booklet
and confirm your zone if unsure.
"""

# ---------------------------------------------------------------------------
# Hardcoded 2026 recycling collection dates for each zone.
#
# These dates are derived from the 2026 Orange City Council Waste Booklet:
# https://www.orange.nsw.gov.au/wp-content/uploads/2025/12/WS_WasteBookletOCC_2026_A5_webSpreads.pdf
#
# All collections are on Wednesdays.
# Zone A and Zone B alternate fortnightly.
# Zone A = first Wednesday of the year; Zone B = second Wednesday.
#
# Update this data annually from the booklet published at:
# https://www.orange.nsw.gov.au/waste/
# ---------------------------------------------------------------------------

_ZONE_A_RECYCLING_2026 = [
    datetime.date(2026, 1, 7),
    datetime.date(2026, 1, 21),
    datetime.date(2026, 2, 4),
    datetime.date(2026, 2, 18),
    datetime.date(2026, 3, 4),
    datetime.date(2026, 3, 18),
    datetime.date(2026, 4, 1),
    datetime.date(2026, 4, 15),
    datetime.date(2026, 4, 29),
    datetime.date(2026, 5, 13),
    datetime.date(2026, 5, 27),
    datetime.date(2026, 6, 10),
    datetime.date(2026, 6, 24),
    datetime.date(2026, 7, 8),
    datetime.date(2026, 7, 22),
    datetime.date(2026, 8, 5),
    datetime.date(2026, 8, 19),
    datetime.date(2026, 9, 2),
    datetime.date(2026, 9, 16),
    datetime.date(2026, 9, 30),
    datetime.date(2026, 10, 14),
    datetime.date(2026, 10, 28),
    datetime.date(2026, 11, 11),
    datetime.date(2026, 11, 25),
    datetime.date(2026, 12, 9),
    datetime.date(2026, 12, 23),
]

_ZONE_B_RECYCLING_2026 = [
    datetime.date(2026, 1, 14),
    datetime.date(2026, 1, 28),
    datetime.date(2026, 2, 11),
    datetime.date(2026, 2, 25),
    datetime.date(2026, 3, 11),
    datetime.date(2026, 3, 25),
    datetime.date(2026, 4, 8),
    datetime.date(2026, 4, 22),
    datetime.date(2026, 5, 6),
    datetime.date(2026, 5, 20),
    datetime.date(2026, 6, 3),
    datetime.date(2026, 6, 17),
    datetime.date(2026, 7, 1),
    datetime.date(2026, 7, 15),
    datetime.date(2026, 7, 29),
    datetime.date(2026, 8, 12),
    datetime.date(2026, 8, 26),
    datetime.date(2026, 9, 9),
    datetime.date(2026, 9, 23),
    datetime.date(2026, 10, 7),
    datetime.date(2026, 10, 21),
    datetime.date(2026, 11, 4),
    datetime.date(2026, 11, 18),
    datetime.date(2026, 12, 2),
    datetime.date(2026, 12, 16),
    datetime.date(2026, 12, 30),
]

# Map year -> (zone_a_dates, zone_b_dates).  Add new years here as booklets
# are published.
_HARDCODED_SCHEDULES: dict[int, tuple[list, list]] = {
    2026: (_ZONE_A_RECYCLING_2026, _ZONE_B_RECYCLING_2026),
}


def _all_wednesdays_in_year(year: int):
    """Yield every Wednesday (weekday index 2) in *year*."""
    d = datetime.date(year, 1, 1)
    # Advance to the first Wednesday
    days_ahead = (2 - d.weekday()) % 7
    d += datetime.timedelta(days=days_ahead)
    while d.year == year:
        yield d
        d += datetime.timedelta(weeks=1)


class Source:
    """Waste collection source for Orange City Council, NSW, Australia."""

    def __init__(self, zone: str) -> None:
        self._zone = zone.strip().upper()
        if self._zone not in ("A", "B"):
            raise ValueError(
                f"Invalid zone '{zone}'. Must be 'A' (west of Anson Street) "
                "or 'B' (east of Anson Street / Spring Hill / Lucknow / Clifton Grove)."
            )

    def fetch(self) -> list[Collection]:
        entries: list[Collection] = []
        today = datetime.date.today()
        year = today.year

        # --- General Waste: every Wednesday ---
        for d in _all_wednesdays_in_year(year):
            entries.append(
                Collection(date=d, t="General Waste", icon=ICON_MAP["General Waste"])
            )

        # --- Recycling: fortnightly ---
        if year in _HARDCODED_SCHEDULES:
            zone_a_dates, zone_b_dates = _HARDCODED_SCHEDULES[year]
            recycling_dates = zone_a_dates if self._zone == "A" else zone_b_dates
        else:
            # Estimate fortnightly pattern for years not yet in the hardcoded list.
            # Zone A starts on the first Wednesday; Zone B on the second Wednesday.
            _LOGGER.warning(
                "orange_nsw_gov_au: No hardcoded schedule for %d. "
                "Recycling dates are estimated — please verify against the annual "
                "Orange City Council waste booklet at https://www.orange.nsw.gov.au/waste/ "
                "and update the source if needed.",
                year,
            )
            wednesdays = list(_all_wednesdays_in_year(year))
            start_index = 0 if self._zone == "A" else 1
            recycling_dates = wednesdays[start_index::2]

        for d in recycling_dates:
            entries.append(
                Collection(date=d, t="Recycling", icon=ICON_MAP["Recycling"])
            )

        return entries
