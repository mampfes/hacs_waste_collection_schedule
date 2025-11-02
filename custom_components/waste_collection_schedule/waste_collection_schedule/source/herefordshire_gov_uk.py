import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Herefordshire City Council"
DESCRIPTION = "Source for herefordshire.gov.uk services for hereford"
URL = "https://herefordshire.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "hr49js", "number": "52"},
}

API_URLS = {
    "address_search": "https://trsewmllv7.execute-api.eu-west-2.amazonaws.com/dev/address",
    "collection": "https://www.herefordshire.gov.uk/rubbish-recycling/check-bin-collection-day",  # ?blpu_uprn=200002607454",
}
HEADER = {"user-agent": "Mozilla/5.0"}
ICON_MAP = {
    "General": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, post_code: str, number: str):
        self._post_code = post_code
        # keep original behaviour, but normalise for comparisons later
        self._number = str(number).capitalize()

    def fetch(self):
        # fetch location id
        r = requests.get(
            API_URLS["address_search"],
            headers=HEADER,
            params={"postcode": self._post_code, "type": "standard"},
        )
        r.raise_for_status()
        addresses = r.json()
        if (
            ("error" in addresses and addresses["error"])
            or "results" not in addresses
            or len(addresses["results"]) == 0
        ):
            raise SourceArgumentNotFound("post_code", self._post_code)

        # cast PAO fields to str to avoid .lower() on non-strings (some APIs return ints)
        target = self._number.lower()
        address_ids = [
            x
            for x in addresses["results"]
            if (
                x["LPI"].get("PAO_TEXT") is not None
                and str(x["LPI"]["PAO_TEXT"]).lower() == target
            )
            or (
                x["LPI"].get("PAO_START_NUMBER") is not None
                and str(x["LPI"]["PAO_START_NUMBER"]).lower() == target
            )
        ]

        if len(address_ids) == 0:
            numbers = {x["LPI"].get("PAO_TEXT") for x in addresses["results"]}
            numbers.update(
                {x["LPI"].get("PAO_START_NUMBER") for x in addresses["results"]}
            )
            numbers -= {None}
            raise SourceArgumentNotFoundWithSuggestions("number", self._number, numbers)

        q = str(API_URLS["collection"])
        r = requests.get(
            q, headers=HEADER, params={"blpu_uprn": address_ids[0]["LPI"]["UPRN"]}
        )
        r.raise_for_status()

        # --- Updated DOM parsing (site changed) ---
        soup = BeautifulSoup(r.text, "html.parser")
        container = soup.find(id="binCollectionDetails")
        if not container:
            # fall back to legacy wrapper if council reverts
            legacy = soup.find(id="wasteCollectionDates")
            if not legacy:
                raise Exception(
                    "Could not find bin collection section on the council page (IDs changed)."
                )
            container = legacy

        # Extract first <li> date under each heading
        def first_li_after_heading(heading_keyword: str):
            # find <h3> that contains the keyword, then take first <li> in the next <ul>
            for h3 in container.find_all("h3"):
                title = h3.get_text(strip=True).lower()
                if heading_keyword.lower() in title:
                    ul = h3.find_next_sibling("ul")
                    if ul:
                        li = ul.find("li")
                        if li:
                            # strip any "(next collection)" etc.
                            text = li.get_text(strip=True)
                            cut = text.find("(")
                            return text[:cut].strip() if cut != -1 else text.strip()
            return None

        waste_date_str = first_li_after_heading("general rubbish")
        recycling_date_str = first_li_after_heading("recycling")

        entries = []
        if waste_date_str:
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date_str, "%A %d %B %Y").date(),
                    t="General rubbish",
                    icon="mdi:trash-can",
                ),
            )
        if recycling_date_str:
            entries.append(
                Collection(
                    date=datetime.strptime(recycling_date_str, "%A %d %B %Y").date(),
                    t="Recycling",
                    icon="mdi:recycle",
                ),
            )
        if not entries:
            raise Exception(
                "No collection dates found for this address, make sure there are any concrete collection dates listed on the website for this address."
            )

        return entries
