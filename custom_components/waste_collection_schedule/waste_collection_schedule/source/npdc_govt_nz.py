import datetime

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "New Plymouth District Council"
DESCRIPTION = "Source for New Plymouth District Council waste collection."
URL = "https://www.npdc.govt.nz"
COUNTRY = "nz"
TEST_CASES = {
    "107 Coronation Avenue (Yellow/Wednesday)": {"address": "107 Coronation Avenue"},
    "5 Rata Street (Blue/Thursday)": {"address": "5 Rata Street"},
    "15 Rata Street (Blue/Wednesday)": {"address": "15 Rata Street"},
}

ICON_MAP = {
    "Glass and Landfill": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Food Scraps": Icons.BIO_KITCHEN,
}

# Day-of-week index mapping (0=Sunday … 6=Saturday) matching the JS _dayArray
_DAY_INDEX = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}

# Anchor date from the NPDC bin-collection app JavaScript (refuseMap.js).
# Weeks are counted from this Sunday; odd-numbered weeks are "Blue glass pickup weeks".
_ANCHOR = datetime.date(2015, 6, 28)  # Sunday 28 June 2015

SEARCH_URL = "https://gissearchwebapiproxy.npdcapps.co.nz/api/searchitem/"
COLLECTION_URL = (
    "https://gissearchwebapiproxy.npdcapps.co.nz/api/rubbishdays/ratedrefuseproperties/"
)


def _weeks_since_anchor(d: datetime.date) -> int:
    return (d - _ANCHOR).days // 7


def _is_blue_glass_week(weeks_since: int) -> bool:
    """Return True when the week is a Blue-glass/landfill pickup week (odd offset)."""
    return weeks_since % 2 == 1


def _pick_up_date_for_week(weeks_since: int, day_index: int) -> datetime.date:
    """Return the pickup date for the given week offset and day-of-week index."""
    week_start = _ANCHOR + datetime.timedelta(weeks=weeks_since)
    return week_start + datetime.timedelta(days=day_index)


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        # Step 1: Search for the parcel matching the address
        r = requests.get(SEARCH_URL, params={"q": self._address}, timeout=30)
        r.raise_for_status()
        results = r.json()

        if not results:
            raise SourceArgumentNotFound("address", self._address)

        # Pick the best match — first result from the API
        parcel = results[0]
        parcel_id = parcel.get("parcelId")
        if not parcel_id:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: Fetch collection information for the parcel
        r2 = requests.get(COLLECTION_URL, params={"parcelId": parcel_id}, timeout=30)
        r2.raise_for_status()
        collection_data = r2.json()

        if not collection_data:
            # The parcel exists but has no collection schedule (commercial, rural, etc.)
            suggestions = [r["address"] for r in results[:5] if r.get("address")]
            if len(suggestions) > 1:
                raise SourceArgumentNotFoundWithSuggestions(
                    "address", self._address, suggestions[1:]
                )
            raise SourceArgumentNotFound("address", self._address)

        record = collection_data[0]
        pick_week_colour = record.get("Week", "").lower()  # "blue" or "yellow"
        collect_day = record.get("CollectDay", "").lower()
        day_index = _DAY_INDEX.get(collect_day)

        if day_index is None or not pick_week_colour:
            raise SourceArgumentNotFound("address", self._address)

        # Step 3: Generate upcoming collection dates for the next 52 weeks
        today = datetime.date.today()
        weeks_today = _weeks_since_anchor(today)

        entries: list[Collection] = []

        # Scan from current week through 52 weeks ahead
        for week_offset in range(weeks_today, weeks_today + 53):
            pickup_date = _pick_up_date_for_week(week_offset, day_index)
            if pickup_date < today:
                continue

            blue_glass_week = _is_blue_glass_week(week_offset)

            # Determine what goes out this fortnightly cycle
            # Blue address → Glass+Landfill on odd (blue glass) weeks
            # Yellow address → Glass+Landfill on even (non-blue glass) weeks
            is_glass_landfill_week = (
                pick_week_colour == "blue"
                and blue_glass_week
                or pick_week_colour == "yellow"
                and not blue_glass_week
            )

            if is_glass_landfill_week:
                waste_type = "Glass and Landfill"
            else:
                waste_type = "Recycling"

            entries.append(
                Collection(
                    date=pickup_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

            # Food Scraps go out every week
            entries.append(
                Collection(
                    date=pickup_date,
                    t="Food Scraps",
                    icon=ICON_MAP.get("Food Scraps"),
                )
            )

        return entries
