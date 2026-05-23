import logging
from datetime import datetime

import bs4
import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.FirmstepSelfService import (
    get_hidden_form_inputs,
    lookup_addresses,
)

URL = "https://www.derbyshiredales.gov.uk/"
FORM_URL = (
    "https://selfserve.derbyshiredales.gov.uk/"
    "renderform?k=9644C066D2168A4C21BCDA351DA2642526359DFF&t=103"
)
RENDER_URL = "https://selfserve.derbyshiredales.gov.uk/RenderForm"
ADDRESS_LOOKUP_URL = "https://selfserve.derbyshiredales.gov.uk/core/addresslookup"
TEST_CASES = {
    "Matlock": {"address_id": "DE4 3GS"},
    "Bakewell": {"address_id": "U10070089522"},
    "Wirksworth": {"address_id": "U10070097828"},
}

_LOGGER = logging.getLogger(__name__)
ICON_MAP = {
    "domestic": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "garden": Icons.GARDEN,
    "food": Icons.BIO_KITCHEN,
}

TITLE = "Derbyshire Dales District Council"
DESCRIPTION = "Source for derbyshiredales.gov.uk services for Derbyshire Dales, UK."
COUNTRY = "uk"

PARAM_TRANSLATIONS = {
    "en": {
        "address_id": "A Unique Property Reference Number (UPRN) or Postcode",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address_id": "Your property's UPRN, find it at https://www.findmyaddress.co.uk/. You can also use a Postcode",
    }
}


class Source:
    def __init__(self, address_id):
        self._address_id = str(address_id)

    def fetch(self):
        session = requests.Session()
        form_inputs = get_hidden_form_inputs(session, FORM_URL)
        required = {
            "__RequestVerificationToken",
            "FormGuid",
            "ObjectTemplateID",
            "CurrentSectionID",
        }
        if not required.issubset(form_inputs.keys()):
            raise ValueError("Unable to read Derbyshire Dales form metadata")

        payload = {
            "__RequestVerificationToken": form_inputs["__RequestVerificationToken"],
            "FormGuid": form_inputs["FormGuid"],
            "ObjectTemplateID": form_inputs["ObjectTemplateID"],
            "Trigger": "submit",
            "CurrentSectionID": form_inputs["CurrentSectionID"],
            "FF2924": self._address_id,
            "FF2924lbltxt": "Collection Address",
            "FF2924-text": "False",
        }
        data_resp = session.post(RENDER_URL, data=payload, timeout=30)
        data_resp.raise_for_status()
        data_soup = bs4.BeautifulSoup(data_resp.text, "html.parser")

        rows = data_soup.select("div.ss_confPanel div.row[style*='padding-left']")
        collections: list[Collection] = []
        for row in rows:
            date_col = row.find("div", class_="col-sm-5")
            type_col = row.find("div", class_="col-sm-6")
            if not date_col or not type_col:
                continue
            raw_date = date_col.get_text(separator=" ", strip=True)
            raw_type = type_col.get_text(strip=True)
            try:
                dt = datetime.strptime(raw_date, "%A %d %B, %Y").date()
            except ValueError:
                continue

            lower = raw_type.lower()
            label = ""
            icon = ICON_MAP.get(lower)
            isRecycling = False

            if icon is None:
                if "domestic" in lower:
                    label = "Domestic Waste"
                    icon = ICON_MAP["domestic"]
                elif "recycling" in lower:
                    label = "Recycling Waste"
                    icon = ICON_MAP["recycling"]
                    isRecycling = True
                elif "food" in lower:
                    label = "Food Waste"
                    icon = ICON_MAP["food"]
                # Skip duplicating recycling sacks
                elif "sacks" in lower:
                    continue
                else:
                    continue

            collections.append(Collection(dt, label, icon))

            # Garden waste is on the same date
            if isRecycling:
                collections.append(Collection(dt, "Garden Waste", ICON_MAP["garden"]))

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
                "Derbyshire Dales returned no collection rows for address_id=%s",
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
