import logging
from datetime import datetime

import bs4
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.FirmstepSelfService import (
    get_hidden_form_inputs,
    lookup_addresses,
)

URL = "https://southkesteven.gov.uk"
FORM_URL = (
    "https://selfservice.southkesteven.gov.uk/"
    "renderform?k=2074C945A63DDC0D18F1EB74DA230AC3122958B1&t=213"
)
RENDER_URL = "https://selfservice.southkesteven.gov.uk/RenderForm"
ADDRESS_LOOKUP_URL = "https://selfservice.southkesteven.gov.uk/core/addresslookup"
TEST_CASES = {
    "Bourne": {"address_id": "PE10 0RX"},
    "Long Bennington": {"address_id": "NG23 5EQ"},
    "Grantham": {"address_id": "NG31 6NP"},
}
_LOGGER = logging.getLogger(__name__)
ICON_MAP = {
    "black": "mdi:trash-can",
    "gray": "mdi:recycle",
    "green": "mdi:leaf",
    "purple": "mdi:newspaper",
}


TITLE = "South Kesteven District Council"
DESCRIPTION = "Source for southkesteven.gov.uk services for South Kesteven, UK."


class Source:
    def __init__(self, address_id):
        self._address_id = str(address_id)

    def fetch(self):
        session = requests.Session()
        form_inputs = get_hidden_form_inputs(session, FORM_URL)
        required = {"__RequestVerificationToken", "FormGuid", "ObjectTemplateID", "CurrentSectionID"}
        if not required.issubset(form_inputs.keys()):
            raise ValueError("Unable to read South Kesteven form metadata")

        payload = {
            "__RequestVerificationToken": form_inputs["__RequestVerificationToken"],
            "FormGuid": form_inputs["FormGuid"],
            "ObjectTemplateID": form_inputs["ObjectTemplateID"],
            "Trigger": "submit",
            "CurrentSectionID": form_inputs["CurrentSectionID"],
            "FF5265": self._address_id,
            "FF5265lbltxt": "Collection Address",
            "FF5265searchnlpg": "False",
            "FF5265manualaddressentry": "False",
            "FF5265classification": "",
        }
        data_resp = session.post(RENDER_URL, data=payload, timeout=30)
        data_resp.raise_for_status()
        data_soup = bs4.BeautifulSoup(data_resp.text, "html.parser")

        collections: list[Collection] = []
        for row in data_soup.select("table.Alloy-table tr"):
            cols = row.find_all("td", class_="Alloy-table-col")
            if len(cols) < 2:
                continue
            raw_date = cols[0].get_text(strip=True)
            raw_type = cols[1].get_text(strip=True)
            try:
                dt = datetime.strptime(raw_date, "%A %d %B, %Y").date()
            except ValueError:
                continue
            icon = ICON_MAP.get(raw_type.lower())
            if icon is None:
                lower = raw_type.lower()
                if "refuse" in lower:
                    icon = ICON_MAP["black"]
                elif "recycling" in lower or "paper" in lower:
                    icon = ICON_MAP["gray"]
                elif "green" in lower:
                    icon = ICON_MAP["green"]
                elif "purple" in lower:
                    icon = ICON_MAP["purple"]
            collections.append(Collection(dt, raw_type, icon))

        # If the new flow does not yield rows, try postcode lookup then resubmit.
        if not collections and not self._address_id.startswith("U"):
            addresses = lookup_addresses(
                session, ADDRESS_LOOKUP_URL, self._address_id, search_nlpg="False"
            )
            if addresses:
                self._address_id = next(iter(addresses.keys()))
                return self.fetch()
        if not collections:
            _LOGGER.warning(
                "South Kesteven returned no collection rows for address_id=%s",
                self._address_id,
            )

        # filter out duplicate entries
        collections = list(
            {
                (collection.date, collection.type): collection
                for collection in collections
            }.values()
        )
        return collections
