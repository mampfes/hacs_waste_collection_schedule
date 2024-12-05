from datetime import datetime

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Include work around for SSL UNSAFE_LEGACY_RENEGOTIATION_DISABLED error
from waste_collection_schedule.service.SSLError import get_legacy_session
from const import (
    Icons,
)

TITLE = "Aberdeenshire Council"
DESCRIPTION = "Source for Aberdeenshire Council, UK."
URL = "https://aberdeenshire.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "000151124612"},
    "Test_002": {"uprn": "000151004105"},
    "Test_003": {"uprn": "0151035884"},
    "Test_004": {"uprn": 151170625},
}
ICON_MAP = {
    "Mixed recycling and food waste": Icons.ICON_RECYCLE,
    "Refuse and food waste": Icons.ICON_GENERAL_TRASH,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details."
    },
    "de": {
        "uprn": "Eine einfache Möglichkeit, Ihre Unique Property Reference Number (UPRN) zu finden, besteht darin, auf https://www.findmyaddress.co.uk/ zu gehen und Ihre Adressdaten einzugeben."
    },
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        response = get_legacy_session().get(
            f"https://online.aberdeenshire.gov.uk/Apps/Waste-Collections/Routes/Route/{self._uprn}"
        )
        soup = BeautifulSoup(response.text, "html.parser")

        entries = []

        tr = soup.findAll("tr")
        for item in tr[1:]:  # Ignore table header row
            td = item.findAll("td")
            entries.append(
                Collection(
                    date=datetime.strptime(td[0].text.split(" ")[0], "%d/%m/%Y").date(),
                    t=td[1].text,
                    icon=ICON_MAP.get(td[1].text),
                )
            )

        return entries
