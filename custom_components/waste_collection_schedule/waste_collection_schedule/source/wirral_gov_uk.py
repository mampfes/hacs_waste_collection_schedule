from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Wirral Council"
DESCRIPTION = "Source for wirral.gov.uk services for Wirral Council, UK."
URL = "https://wirral.gov.uk"
TEST_CASES = {
    "Elm Avenue, Upton": {
        "postcode": "CH49 4NP",
        "address_value": "000042037487",
    },
    "Vernon Avenue, Seacombe (with food waste)": {
        "postcode": "CH44 7ES",
        "address_value": "42119794",
    },
}
ICON_MAP = {
    "Green non-recyclable": Icons.GENERAL_WASTE,
    "Grey recycling": Icons.RECYCLING,
    "Grey food waste": Icons.BIO_KITCHEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates, "
        "enter your postcode and select your address. The number at the end of "
        "the resulting web address (.../view/42119794) is your address value. "
        "Use that as the address_value parameter."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your postcode, e.g. CH49 4NP (no longer required).",
        "address_value": (
            "The address (UPRN) value found at the end of the web address "
            "on the Wirral bin collection dates page."
        ),
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "address_value": "Address Value",
    }
}

BIN_URL = "https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates/view/"


class Source:
    def __init__(self, address_value: str, postcode: str | None = None):
        # postcode is kept for backwards compatibility with existing
        # configurations, it is not needed to look up the calendar anymore.
        self._postcode = postcode.strip() if postcode else None
        # Old style values were zero padded to 12 digits, the site uses the
        # plain UPRN.
        self._uprn = str(address_value).strip().lstrip("0")

    def fetch(self) -> list[Collection]:
        r = requests.get(BIN_URL + self._uprn, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for day in soup.select("li.waste-collection__day"):
            time_el = day.select_one("time")
            type_el = day.select_one(".waste-collection__day--type")
            if not time_el or not type_el:
                continue
            try:
                date = datetime.strptime(time_el.get("datetime", ""), "%d-%m-%Y").date()
            except ValueError:
                continue
            bin_type = type_el.get_text(strip=True)
            entries.append(
                Collection(date=date, t=bin_type, icon=ICON_MAP.get(bin_type))
            )

        if not entries:
            raise SourceArgumentNotFound(
                "address_value", self._uprn, "No collections found for this address"
            )
        return entries
