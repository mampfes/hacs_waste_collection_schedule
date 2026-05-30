import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Kungsbacka kommun"
DESCRIPTION = "Source for Kungsbacka kommun waste collection, Sweden."
URL = "https://sjalvservice.kungsbacka.se/"
COUNTRY = "se"

BASE_URL = "https://sjalvservice.kungsbacka.se"
FLOW_URL = f"{BASE_URL}/oversikt/flow/4587"
SEARCH_URL = f"{BASE_URL}/lmsearch/addresses"
QUERY_ID = "query_182297"

TEST_CASES = {
    "Särö Lundaväg 14": {"street_address": "Särö Lundaväg 14"},
    "Storgatan 1 Kungsbacka": {"street_address": "Storgatan 1 Kungsbacka"},
}

ICON_MAP = {
    "hushållsavfall": Icons.GENERAL_WASTE,
    "matavfall": Icons.BIO_KITCHEN,
    "restavfall": Icons.GENERAL_WASTE,
    "grovavfall": Icons.BULKY,
    "farligtavfall": Icons.HAZARDOUS,
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_address": "Street address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Street address and house number, e.g. 'Lundaväg 14' or 'Lundaväg 14 Särö'.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the street name and house number as shown on the [Kungsbacka self-service portal](https://sjalvservice.kungsbacka.se/oversikt/flow/4587). Swedish characters (ä, å, ö) are supported.",
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

        # Step 1: look up the address to get UUIDs
        r = session.get(SEARCH_URL, params={"q": self._street_address}, timeout=30)
        r.raise_for_status()
        results = r.json()

        if not results:
            raise SourceArgumentNotFound("street_address", self._street_address)

        # Use the first search result
        result = results[0]
        full_address = result[1]
        property_object_identity = result[4]
        address_uuid = result[0]

        # Step 2: fetch the collection schedule via the flow form
        form_data = {
            "submitmode": "true",
            "q182296_searchservice": "ADDRESS",
            "q182296_propertyUnitDesignation": "",
            "q182296_address": full_address,
            "q182296_propertyObjectIdentity": property_object_identity,
            "q182296_addressUUID": address_uuid,
        }
        r2 = session.post(
            FLOW_URL,
            data=form_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            timeout=30,
        )
        r2.raise_for_status()

        # Step 3: parse the HTML response
        soup = BeautifulSoup(r2.content, "html.parser", from_encoding="iso-8859-1")
        query_div = soup.find("div", id=QUERY_ID)
        if not query_div:
            return []

        article = query_div.find("article")
        if not article:
            return []

        entries = []
        for table in article.find_all("table"):
            th = table.find("th")
            if not th:
                continue

            # Extract waste type from header:
            # "Kommande hämtningar av hushållsavfall:" -> "hushållsavfall"
            header = th.get_text().strip()
            match = re.match(r"Kommande h.+?mtningar av (.+?):?\s*$", header)
            waste_type = match.group(1) if match else header.rstrip(":")

            for td in table.find_all("td"):
                date_text = td.get_text().strip()
                # Format: "2026-06-03 - onsdag vecka 23"
                date_part = date_text.split(" - ")[0]
                try:
                    date_obj = datetime.strptime(date_part, "%Y-%m-%d").date()
                except ValueError:
                    continue

                entries.append(
                    Collection(
                        date=date_obj,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
