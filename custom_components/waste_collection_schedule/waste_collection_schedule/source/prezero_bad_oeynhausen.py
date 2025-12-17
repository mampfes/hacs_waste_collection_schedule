import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ICS import ICS

TITLE = "PreZero Bad Oeynhausen"
DESCRIPTION = "Source for PreZero Bad Oeynhausen waste collection calendar"
URL = "https://abfallkalender.prezero.network/bad-oeynhausen"
TEST_CASES = {
    "Bad Oeynhausen Aalstraße": {
        "street": "Aalstraße",
        "house_number": "1",
    },
    "Bad Oeynhausen Ackerstraße": {
        "street": "Ackerstraße",
        "house_number": "2",
    },
}

ICON_MAP = {
    "Biotonne": "mdi:leaf",
    "Gelbe Tonne": "mdi:recycle",
    "Restmülltonne": "mdi:trash-can",
    "Restmülltonne 4-wl.": "mdi:trash-can",
    "Papiertonne": "mdi:package-variant",
    "Schadstoffsammlung": "mdi:bottle-tonic-skull",
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Stadt",
        "street": "Straße",
        "house_number": "Hausnummer",
    },
    "en": {
        "city": "City",
        "street": "Street",
        "house_number": "House Number",
    },
}

PARAM_DESCRIPTIONS = {
    "de": {
        "city": "Stadt-Kennung (Standard: 'bad-oeynhausen', optional für andere PreZero-Städte)",
        "street": "Straßenname (z.B. 'Aalstraße')",
        "house_number": "Hausnummer (z.B. '1')",
    },
    "en": {
        "city": "City identifier (default: 'bad-oeynhausen', optional for other PreZero cities)",
        "street": "Street name (e.g. 'Aalstraße')",
        "house_number": "House number (e.g. '1')",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "de": "Geben Sie Ihre Straße und Hausnummer ein. Die Stadt ist standardmäßig auf Bad Oeynhausen eingestellt.",
    "en": "Enter your street and house number. The city defaults to Bad Oeynhausen.",
}


class Source:
    def __init__(self, street: str, house_number: str, city: str = "bad-oeynhausen"):
        self._city = city
        self._street = street
        self._house_number = house_number
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        # Step 1: Submit form to get redirect with street_id
        base_url = f"https://abfallkalender.prezero.network/{self._city}"
        form_data = {"street": self._street, "houseNo": self._house_number}

        # Submit form
        r = requests.post(base_url, data=form_data, allow_redirects=False)

        # Check if redirect was returned
        if r.status_code not in (301, 302, 303, 307, 308):
            # If no redirect, the street or house number might be invalid
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "Street not found. Please verify the street name is correct and matches exactly as shown on the PreZero Bad Oeynhausen website.",
            )

        # Extract redirect location
        location = r.headers.get("Location")
        if not location:
            # Check if there's a meta refresh redirect in the HTML
            if "http-equiv" in r.text and "refresh" in r.text.lower():
                # Parse meta refresh: <meta http-equiv="refresh" content="0;url='/path'" />
                match = re.search(r'url=[\'"]?([^\'" >]+)', r.text)
                if match:
                    location = match.group(1)

        if not location:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "Could not determine calendar URL. Please verify your street and house number.",
            )

        # Extract street_id from redirect URL
        # Format: /city/calendar/{street_id}/{house_number}?...
        match = re.search(r"/calendar/(\d+)/", location)
        if not match:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "Could not extract street ID from response. The street name might be incorrect.",
            )

        street_id = match.group(1)

        # Step 2: Fetch current and next year's data
        now = datetime.now()
        entries = []

        for year in [now.year, now.year + 1]:
            ical_url = f"https://abfallkalender.prezero.network/{self._city}/download/ical/{street_id}/{self._house_number}/{year}"

            # Download iCal file
            r = requests.post(ical_url)
            r.raise_for_status()

            # Parse iCal
            dates = self._ics.convert(r.text)

            for d in dates:
                waste_type = d[1]
                entries.append(
                    Collection(date=d[0], t=waste_type, icon=ICON_MAP.get(waste_type))
                )

        return entries
