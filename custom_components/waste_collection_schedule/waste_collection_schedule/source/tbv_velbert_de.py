import datetime
import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "TBV Velbert"
DESCRIPTION = "Source script for tbv-velbert.de, germany"
URL = "https://www.tbv-velbert.de"
TEST_CASES = {
    "Lindenkamp": {"street": "Am Lindenkamp 33"},
    "Rathaus": {"street": "Thomasstraße 1"},
}

API_URL = "https://www.tbv-velbert.de/abfall/abfallkalender-und-abfuhrtermine/abfallabfuhr-suche"
HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
ICON_MAP = {
    "Restmüll-Gefäß": "mdi:trash-can",
    "Gelbe Tonne": "mdi:recycle",
    "Bio-Tonne": "mdi:leaf",
    "Papier-Tonne": "mdi:package-variant",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street):
        self._street = street

    def fetch(self):
        r = requests.post(
            API_URL,
            headers=HEADERS,
            data={
                "tx_tbvabfall_strassensuche[abgeschickt]": 1,
                "tx_tbvabfall_strassensuche[suchbegriff]": self._street,
            },
        )
        _LOGGER.debug(
            f"Fetching waste schedule for '{self._street}' returned status: {r.status_code}."
        )
        r.raise_for_status()

        parser = BeautifulSoup(r.text, "html.parser")
        content_block = parser.find("div", class_="right-side")
        elements = content_block.find_all(["strong", "span"])
        _LOGGER.debug(f"Found {len(elements)} elements in request.")

        entries = []
        for i in range(0, len(elements), 2):
            waste_type = elements[i].get_text()[0:-1]  # strip trailing colon
            waste_dates = (
                elements[i + 1].get_text().split(":")[1]
            )  # get dates after colon
            waste_dates = waste_dates.strip().split(" ")  # convert to list
            waste_dates[:] = [w for w in waste_dates if w]  # remove empty strings
            for d in waste_dates:
                entries.append(
                    Collection(
                        datetime.datetime.strptime(d, "%d.%m.%Y").date(),
                        waste_type,
                        ICON_MAP.get(waste_type),
                    )
                )

        return entries
