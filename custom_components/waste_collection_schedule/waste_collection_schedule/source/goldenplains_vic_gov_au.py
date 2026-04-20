import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Golden Plains Shire Council"
URL = "https://www.goldenplains.vic.gov.au"
DESCRIPTION = "Source for Golden Plains Shire Council, VIC, AU"
COUNTRY = "au"

TEST_CASES = {
    "2 Pope Street Bannockburn": {"address": "2 POPE STREET BANNOCKBURN 3331"},
}

AUTOCOMPLETE_URL = "https://www.goldenplains.vic.gov.au/views-autocomplete-filters/addresses/page_3/ezi_address/0"
SCHEDULE_URL = "https://www.goldenplains.vic.gov.au/address-search"

# Maps the CSS class on each card div to a (waste type label, MDI icon) tuple
CARD_TYPES = {
    "recycling": ("Recycling", "mdi:recycle"),
    "rubbish": ("Garbage", "mdi:trash-can"),
    "fogo": ("Glass", "mdi:bottle-wine"),
}


class Source:
    def __init__(self, address: str):
        self._address = re.sub(r"\s+", " ", address).strip()

    def fetch(self) -> list[Collection]:
        # Step 1: validate address against autocomplete and get canonical form
        r = requests.get(
            AUTOCOMPLETE_URL,
            params={"q": self._address},
            timeout=30,
        )
        r.raise_for_status()
        suggestions = r.json()

        if not suggestions:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [],
            )

        # Check for an exact match (case-insensitive) or fall back to suggestions
        canonical = None
        for item in suggestions:
            if item["value"].upper() == self._address.upper():
                canonical = item["value"]
                break

        if canonical is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [item["value"] for item in suggestions],
            )

        # Step 2: fetch the schedule page using the canonical address
        r = requests.get(SCHEDULE_URL, params={"address": canonical}, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        entries: list[Collection] = []

        for css_class, (waste_type, icon) in CARD_TYPES.items():
            card = soup.select_one(f"div.card.{css_class}")
            if not card:
                continue

            p = card.find("p")
            if not p:
                continue

            # Dates are separated by <br> tags, e.g. "27th April 2026"
            for date_str in p.stripped_strings:
                date_str = date_str.strip()
                if not date_str:
                    continue
                # Strip ordinal suffixes: 1st 2nd 3rd 4th etc.
                date_clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
                try:
                    date = datetime.strptime(date_clean, "%d %B %Y").date()
                except ValueError:
                    continue
                entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
