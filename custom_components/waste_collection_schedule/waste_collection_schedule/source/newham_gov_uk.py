import re
from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "London Borough of Newham"
DESCRIPTION = "Source for newham.gov.uk services for London Borough of Newham, UK."
URL = "https://www.newham.gov.uk"
TEST_CASES = {
    "Test_001": {"property": "000046029461"},
    "Test_002": {"property": "000046250697"},
    "Test_003": {"property": 46012509},
}

ICON_MAP = {
    "DOMESTIC": Icons.GENERAL_WASTE,
    "RECYCLING": Icons.RECYCLING,
    "FOOD WASTE": Icons.BIO_KITCHEN,
}

API_URL = "https://bincollection.newham.gov.uk/Details/Index/{property}"

# "Next<nbsp>Tuesday<nbsp>01/09/2026" - the day name is optional, the date is
# always dd/mm/yyyy. Allow at most one word between "Next" and the date, and
# never "Previous", so that a card with an empty "Next" cannot match the
# "Previous" date that follows it.
NEXT_DATE = re.compile(r"Next\s*(?:(?!Previous)[A-Za-z]+\s*)?(\d{2}/\d{2}/\d{4})")

# The server presents only its leaf certificate, so the chain cannot be verified.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Source:
    def __init__(self, property):
        self._property = str(property).zfill(12)

    def fetch(self):
        r = requests.get(API_URL.format(property=self._property), verify=False)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")

        # An unknown (but well formed) property ID still returns HTTP 200 with a
        # fully rendered page; only the address card is left empty. Without this
        # check every collection card is skipped and fetch() returns [] silently.
        # Key the lookup on the header text, not on card order: every collection
        # card carries the "card" class too, so a positional lookup would read a
        # collection card (and pass) if the page were ever reordered.
        address = None
        for card in soup.find_all("div", class_="card"):
            header = card.find("div", {"class": "card-header"})
            if header is not None and "address" in header.get_text(strip=True).lower():
                address = card.find("p", {"class": "card-text"})
                break
        if address is None or not address.get_text(strip=True):
            raise SourceArgumentNotFound(
                "property",
                self._property,
                "this property ID does not exist on bincollection.newham.gov.uk.",
            )

        entries = []

        # Each collection type is its own card; the type is in bold in the card
        # header ("Your <b>Domestic</b> Collection Day"). Cards without a bold
        # header (e.g. green and garden waste) carry no schedule.
        for card in soup.find_all("div", class_="card"):
            header = card.find("div", {"class": "card-header"})
            if header is None:
                continue
            bin_type_element = header.find("b")
            if bin_type_element is None:
                continue
            bin_type = bin_type_element.get_text(strip=True)
            # ICON_MAP doubles as the allowlist of collection types: a type
            # Newham adds later is skipped until it is given an icon here.
            if bin_type.upper() not in ICON_MAP:
                continue

            body = card.find("p", {"class": "card-text"})
            if body is None:
                continue
            match = NEXT_DATE.search(body.get_text())
            if match is None:
                # The card is rendered even when no collection is scheduled.
                continue

            entries.append(
                Collection(
                    date=datetime.strptime(match.group(1), "%d/%m/%Y").date(),
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type.upper()),
                )
            )

        return entries
