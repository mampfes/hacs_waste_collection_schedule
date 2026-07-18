import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import (
    Collection,  # type: ignore[attr-defined]
    Icons,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Waikato District Council"
DESCRIPTION = (
    "Source for Waikato District Council kerbside rubbish and recycling "
    "collection, New Zealand."
)
URL = "https://www.waikatodistrict.govt.nz/"
COUNTRY = "nz"

TEST_CASES = {
    "Rotowaro, Monday": {"address": "42B Mahuta Station Road, Rotowaro"},
    "Raglan, Tuesday": {"address": "90 Upper Wainui Road, Raglan"},
    "Tuakau, Tuesday": {"address": "11 Gordon Paul Place, Tuakau"},
    "Pokeno, Thursday": {"address": "53 Market Street, Pokeno"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your address as it appears on the council's rubbish and "
    "recycling collection page, e.g. '18 Example Drive, Huntly'. If the "
    "address cannot be found uniquely, the error message will list the "
    "closest matches known to the council."
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address within the Waikato District, e.g. "
        "'18 Example Drive, Huntly'.",
    }
}

API_URL = "https://www.waikatodistrict.govt.nz/widgetApi/RubbishAndRecyclingCollections/search"

COLLECTION_TYPE = "Rubbish and Recycling"

ICON_MAP = {
    COLLECTION_TYPE: Icons.GENERAL_WASTE,
}

# Number of weeks of weekly collections to generate.
WEEKS_AHEAD = 26

# Cap the disambiguation suggestions returned to the user.
MAX_SUGGESTIONS = 10

WEEKDAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}

# Collection areas / days that don't have a fixed weekly kerbside collection
# (e.g. monthly resource-recovery drop-off points, self-service transfer
# stations, or properties outside the serviced area).
NO_WEEKLY_SERVICE_DAYS = {"", "selfservice", "monthlydropoff"}

# The API's search matches on a punctuation-free string; strip commas etc.
_PUNCTUATION_RE = re.compile(r"[,\n\r]+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(address: str) -> str:
    address = _PUNCTUATION_RE.sub(" ", address)
    address = _WHITESPACE_RE.sub(" ", address)
    return address.strip().lower()


class Source:
    def __init__(self, address: str):
        self._address: str = address.strip()

    def fetch(self) -> list[Collection]:
        query = _normalize(self._address)

        r = requests.get(API_URL, params={"address": query}, timeout=30)
        r.raise_for_status()
        results = r.json()

        # Deduplicate by normalized address, keeping the first record and the
        # original (nicely cased) address string for suggestions.
        unique: dict[str, dict] = {}
        for entry in results:
            raw_address = entry.get("address")
            if not raw_address:
                continue
            key = _normalize(raw_address)
            unique.setdefault(key, entry)

        if not unique:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        exact = unique.get(query)
        if exact is not None:
            target = exact
        elif len(unique) == 1:
            target = next(iter(unique.values()))
        else:
            suggestions = sorted(e["address"] for e in unique.values())
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, suggestions[:MAX_SUGGESTIONS]
            )

        collection_day = (target.get("collectionDay") or "").strip().lower()
        collection_area = target.get("collectionArea")
        next_date_str = target.get("nextDate")

        if (
            collection_day in NO_WEEKLY_SERVICE_DAYS
            or collection_day not in WEEKDAYS
            or collection_area in (None, "None")
            or not next_date_str
        ):
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition=(
                    "this address does not have a fixed weekly rubbish and "
                    "recycling collection day (it may use a monthly drop-off "
                    "point, a self-service transfer station, or no kerbside "
                    "service). Please check the council's website."
                ),
            )

        next_date = datetime.fromisoformat(next_date_str).date()

        return [
            Collection(
                date=next_date + timedelta(weeks=i),
                t=COLLECTION_TYPE,
                icon=ICON_MAP[COLLECTION_TYPE],
            )
            for i in range(WEEKS_AHEAD)
        ]
