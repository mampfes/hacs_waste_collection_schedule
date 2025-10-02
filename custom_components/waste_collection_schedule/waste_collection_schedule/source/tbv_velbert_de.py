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

API_BASE = "https://www.tbv-velbert.de"
API_URL = f"{API_BASE}/abfall/abfalltrennung/abfallkalender"
HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
ICON_MAP = {
    "Restmüll-Gefäß": "mdi:trash-can",
    "Gelbe Tonne": "mdi:recycle",
    "Bio-Tonne": "mdi:leaf",
    "Papier-Tonne": "mdi:package-variant",
}

_LOGGER = logging.getLogger(__name__)

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
    }
}


class Source:
    def __init__(self, street):
        self._street = street

    def fetch(self):
        session = requests.Session()
        s = session.get(API_URL, headers=HEADERS)
        s.raise_for_status()
        soup = BeautifulSoup(s.text, "html.parser")
        form = soup.select_one("div.tx-tbvabfall form")
        if not form:
            raise ValueError("Could not find form in the response.")
        form_data = {}
        action = form.get("action")
        if not isinstance(action, str):
            raise ValueError("Form action is not a string.")
        if action.startswith("/"):
            action = API_BASE + action

        for input in form.select("input"):
            name = input.get("name")
            value = input.get("value")
            if name and value:
                form_data[name] = value

        form_data["tx_tbvabfall_strassensuche[suchbegriff]"] = self._street
        r = requests.post(
            action,
            headers=HEADERS,
            data=form_data,
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
