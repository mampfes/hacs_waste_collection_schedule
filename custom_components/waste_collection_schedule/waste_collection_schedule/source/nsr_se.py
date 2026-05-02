import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "NSR - Nordvästra Skånes Renhållnings AB"
DESCRIPTION = "Source for NSR waste collection schedule in northwest Skåne, Sweden."
URL = "https://nsr.se"
COUNTRY = "se"

API_URL = "https://nsr.se/api/wastecalendar"

TEST_CASES = {
    "Kattarp villa": {"address": "Signestorpsvägen 1"},
    "Helsingborg city": {"address": "Drottninggatan 100, Helsingborg"},
    "Kattarp with garden waste": {"address": "Signestorpsvägen 13"},
}

EXTRA_INFO = [
    {
        "title": "NSR Tömningskalender",
        "url": "https://nsr.se/privat/allt-om-din-sophamtning/nar-toms-mitt-karl/tomningskalender/",
        "country": "se",
    },
]

ICON_MAP = {
    "KÄRL 1": "mdi:trash-can",
    "KÄRL 2": "mdi:recycle",
    "Trädgårdsavfall": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address as shown on the NSR website "
    "(e.g. 'Storgatan 1'). Do not include postal code. "
    "Search at https://nsr.se/privat/allt-om-din-sophamtning/nar-toms-mitt-karl/tomningskalender/",
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street name and number (e.g. 'Storgatan 1')",
    },
}


class Source:
    def __init__(self, address: str):
        if not address:
            raise SourceArgumentRequired("address", "A street address is required")
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        # Split "Street 1, City" into street and optional city filter
        if "," in self._address:
            street, city_filter = (
                p.strip() for p in self._address.split(",", maxsplit=1)
            )
        else:
            street = self._address
            city_filter = ""

        # Step 1: Search for the address (API only accepts street, not city)
        r = requests.get(
            f"{API_URL}/search",
            params={"query": street},
            timeout=30,
        )
        r.raise_for_status()

        data = r.json()
        results = data.get("fp", [])

        if not results:
            raise SourceArgumentNotFound("address", self._address)

        # Step 2: Filter by city if provided
        if city_filter:
            filtered = [
                e for e in results if e.get("Ort", "").lower() == city_filter.lower()
            ]
            if filtered:
                results = filtered

        # Step 3: Find exact match or suggest alternatives
        match = None
        for entry in results:
            addr = entry.get("Adress", "")
            if addr.lower() == street.lower():
                match = entry
                break

        if match is None:
            if len(results) == 1:
                match = results[0]
            else:
                suggestions = [
                    f"{e['Adress']}, {e['Ort']}" for e in results if "Adress" in e
                ]
                raise SourceArgumentNotFoundWithSuggestions(
                    "address", self._address, suggestions
                )

        # Step 4: Fetch ICS calendar
        address_id = match["id"]
        r = requests.get(
            f"{API_URL}/calendar",
            params={
                "query": street,
                "id": address_id,
                "calendar_type": "ical",
                "action": "fetchDataFromFetchPlannerCalendar",
                "level": "ajax",
                "type": "json",
            },
            timeout=30,
        )
        r.raise_for_status()

        # Step 5: Parse ICS data (NSR feed duplicates every event)
        ics = ICS()
        dates = ics.convert(r.text)

        seen = set()
        entries = []
        for dt, waste_type in dates:
            key = (dt, waste_type)
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                Collection(
                    date=dt,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
