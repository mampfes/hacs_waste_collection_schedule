from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Torbay Council"
DESCRIPTION = "Source for waste collection services for Torbay Council, Devon, UK."
URL = "https://www.torbay.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "30 Dart Avenue, Torquay, TQ2 7NG": {"uprn": "100040542066"},
    "5 First Avenue, St Marychurch, Torquay, TQ1 4JB": {"uprn": "100040543309"},
}

ICON_MAP = {
    "Domestic Collection Service": Icons.GENERAL_WASTE,
    "Recycling Collection Service": Icons.RECYCLING,
    "Garden Collection Service": Icons.GARDEN,
}

FORM_URL = "https://selfservice-torbay.servicebuilder.co.uk/renderform?t=62&k=09B72FF904A21A4B01A72AB6CCF28DC95105031C"
SUBMIT_URL = "https://selfservice-torbay.servicebuilder.co.uk/RenderForm"

PARAM_TRANSLATIONS = {
    "en": {"uprn": "UPRN"},
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Your Unique Property Reference Number (UPRN). Find yours at https://www.findmyaddress.co.uk/",
    },
}


class Source:
    def __init__(self, uprn: str) -> None:
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Step 1: Load the form page to get a session cookie and CSRF token
        resp = session.get(FORM_URL, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
        guid_tag = soup.find("input", {"id": "form-guid"})
        if not token_tag or not guid_tag:
            raise ValueError("Could not find CSRF token or form GUID on form page.")
        token = token_tag["value"]
        guid = guid_tag["value"]

        # Step 2: Submit the form with the UPRN (prefixed with "U" as required by the portal)
        resp2 = session.post(
            SUBMIT_URL,
            data={
                "__RequestVerificationToken": token,
                "FormGuid": guid,
                "ObjectTemplateID": "62",
                "Trigger": "submit",
                "CurrentSectionID": "0",
                "TriggerCtl": "",
                "FF1168": f"U{self._uprn}",
            },
            timeout=30,
        )
        resp2.raise_for_status()

        soup2 = BeautifulSoup(resp2.text, "html.parser")
        container = soup2.find(id="resiCollectionDetails")
        if not container:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
            )

        entries = []
        for row in container.find_all(class_="resirow"):
            cols = row.find_all("div", class_="col")
            if len(cols) < 3:
                continue
            date_text = cols[1].get_text(strip=True)
            service = cols[2].get_text(strip=True)
            try:
                date = datetime.strptime(date_text, "%A %d %B %Y").date()
            except ValueError:
                continue
            entries.append(
                Collection(
                    date=date,
                    t=service,
                    icon=ICON_MAP.get(service),
                )
            )
        return entries
