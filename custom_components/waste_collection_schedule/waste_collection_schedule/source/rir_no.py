import json
import time
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "RIR"
DESCRIPTION = (
    "Source for RIR (Romsdalshalvøya Interkommunale Renovasjonsselskap), serving the "
    "municipalities of Aukra, Hustadvika, Gjemnes, Molde and Rauma, Norway."
)
URL = "https://www.rir.no"
COUNTRY = "no"

TEST_CASES = {
    "Øvre veg 10C, Molde": {"address": "Øvre veg 10C, Molde"},
    "Årøsetervegen 56, Molde": {"address": "Årøsetervegen 56, Molde"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "The full address, exactly as suggested by the address search on rir.no/hentekalender.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.rir.no/hentekalender, start typing your address in the search field, and copy the "
    "suggested address exactly (including the postal town) into the 'address' argument.",
}

ADDRESS_SUGGESTION_URL = (
    "https://www.rir.no/actions/rir/location/get-address-suggestion"
)
PICKUP_DATES_URL = (
    "https://www.rir.no/actions/rir/content/get-pickup-dates-by-address-id"
)

# Number of months (including the current one) to look ahead for collection dates.
# RIR typically only publishes the current calendar year, but this also picks up
# next year's calendar once it becomes available late in the year.
MONTHS_AHEAD = 13

# RIR's pickup-dates endpoint occasionally answers a perfectly valid request with an
# empty "Ingen resultater funnet" (no results found) page instead of the real data,
# most likely due to server-side caching/rate-limiting. This has been observed to
# silently drop real, published collection dates (see GitHub issue #7193). To guard
# against this, an empty month response is retried a few times before it is trusted,
# and a short delay is inserted between month requests to avoid tripping the
# rate limiting in the first place.
EMPTY_RESULT_RETRIES = 3
EMPTY_RESULT_RETRY_DELAY = 1.0  # seconds
REQUEST_DELAY = 0.3  # seconds between month requests

ICON_MAP = {
    "Restavfall": Icons.GENERAL_WASTE,
    "Matavfall": Icons.BIO_KITCHEN,
    "Papir": Icons.PAPER,
    "Papp": Icons.PAPER,
    "Papp, papir og kartong": Icons.PAPER,
    "Plastemballasje": Icons.PLASTIC_PACKAGING,
    "Glassemballasje": Icons.GLASS,
    "Metallemballasje": Icons.METAL,
    "Glass- og metallemballasje": Icons.GLASS,
    "Hageavfall": Icons.GARDEN,
    "Farlig avfall": Icons.HAZARDOUS,
    "Batteri": Icons.BATTERY,
    "Trevirke": Icons.GENERAL_WASTE,
    "Klær og sko": Icons.TEXTILE,
    "Elektrisk og elektronisk": Icons.ELECTRONICS,
}


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


class Source:
    def __init__(self, address: str):
        self._address = address

    def _get_address_id(self, session: requests.Session) -> str:
        r = session.get(ADDRESS_SUGGESTION_URL, params={"query": self._address})
        r.raise_for_status()
        options = r.json().get("Options", [])

        address_norm = _normalize(self._address)
        for option in options:
            if _normalize(option["Text"]) == address_norm:
                return str(option["Id"])

        # Only one suggestion was returned: use it even if it doesn't match verbatim
        # (e.g. minor differences in whitespace or capitalisation).
        if len(options) == 1:
            return str(options[0]["Id"])

        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            self._address,
            [option["Text"] for option in options],
        )

    def _get_month_wrappers(
        self, session: requests.Session, address_id: str, year: int, month: int
    ):
        if month == 12:
            last_day = 31
        else:
            last_day = (date(year, month + 1, 1) - date(year, month, 1)).days
        date_from = f"{year}-{month:02d}"
        date_to = f"{year}-{month:02d}-{last_day:02d}"
        date_param = json.dumps(
            {"title": date_from, "dateFrom": date_from, "date": date_to}
        )

        wrappers = []
        for attempt in range(EMPTY_RESULT_RETRIES + 1):
            r = session.get(
                PICKUP_DATES_URL,
                params={"date": date_param, "addressId": address_id},
            )
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            wrappers = soup.select(".collectionCalendar__date-wrapper")
            if wrappers or attempt == EMPTY_RESULT_RETRIES:
                break
            # RIR's endpoint occasionally reports "no results" for a month that does
            # have published collections (see EMPTY_RESULT_RETRIES comment above).
            # Retry a few times before trusting an empty response.
            time.sleep(EMPTY_RESULT_RETRY_DELAY)

        return wrappers

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        address_id = self._get_address_id(session)

        entries: list[Collection] = []
        today = date.today()
        year, month = today.year, today.month
        for i in range(MONTHS_AHEAD):
            if i:
                time.sleep(REQUEST_DELAY)

            wrappers = self._get_month_wrappers(session, address_id, year, month)
            for wrapper in wrappers:
                date_el = wrapper.select_one(".collectionCalendar__date-text")
                if not date_el:
                    continue
                collection_date = datetime.strptime(
                    date_el.get_text(strip=True), "%d.%m.%y"
                ).date()

                for fraction_el in wrapper.select(".collectionCalendar__fraction-text"):
                    fraction = fraction_el.get_text(strip=True).lstrip(", ").strip()
                    if not fraction:
                        continue
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=fraction,
                            icon=ICON_MAP.get(fraction),
                        )
                    )

            month += 1
            if month > 12:
                month = 1
                year += 1

        return entries
