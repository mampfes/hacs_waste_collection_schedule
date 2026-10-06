from datetime import date, datetime

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
    "Elm Avenue, Upton (no postcode, plain UPRN)": {
        "address_value": "42037487",
    },
}
ICON_MAP = {
    "Green non-recyclable": Icons.GENERAL_WASTE,
    "Grey recycling": Icons.RECYCLING,
    "Grey food waste": Icons.BIO_KITCHEN,
    "Brown garden waste": Icons.GARDEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates, "
        "enter your postcode and select your address. The number at the end of "
        "the resulting web address (.../view/42037487) is your address value. "
        "Use that as the address_value parameter."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your postcode, e.g. CH49 4NP (no longer required).",
        "address_value": (
            "The number at the end of the web address of your address "
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


def _parse_date(value: str) -> date | None:
    # The site currently sends DD-MM-YYYY; other councils on the same
    # platform send ISO dates, so accept both.
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


class Source:
    def __init__(self, address_value: str | int, postcode: str | None = None):
        # The postcode is no longer needed to look up the calendar. It stays
        # an optional, unused argument so existing configurations keep working.
        # Values copied from the old calendar were zero padded to 12 digits;
        # the new page takes the plain number.
        self._address_value = str(address_value).strip().lstrip("0")

    def fetch(self) -> list[Collection]:
        r = requests.get(BIN_URL + self._address_value, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for day in soup.select("li.waste-collection__day"):
            time_el = day.select_one("time[datetime]")
            type_el = day.select_one(".waste-collection__day--type")
            if not time_el or not type_el:
                continue
            collection_date = _parse_date(str(time_el["datetime"]))
            if collection_date is None:
                continue
            bin_type = type_el.get_text(strip=True)
            entries.append(
                Collection(
                    date=collection_date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        if not entries:
            raise SourceArgumentNotFound(
                "address_value",
                self._address_value,
                "no collections were found for this address on "
                "https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates",
            )
        return entries
