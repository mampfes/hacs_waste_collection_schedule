from datetime import datetime

import requests
import re
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Sunderland City Council"
DESCRIPTION = "Source for sunderland.gov.uk services for Sunderland City Council, UK."
URL = "https://www.sunderland.gov.uk/"
API_URL = "https://webapps.sunderland.gov.uk/WEBAPPS/WSS/Sunderland_Portal/Forms/bindaychecker.aspx"
HEADERS = {"user-agent": "Mozilla/5.0"}
TEST_CASES = {
    "Test_001": {"postcode": "SR4 7PU", "address": "191 Cleveland Road"},
    "Test_002": {"postcode": "SR3 2DW", "address": "43 Hill Street"},
    "Test_003": {"postcode": "SR4 8RJ", "address": "17 Sutherland Drive"},
}
ICON_MAP = {"Recycle": "mdi:recycle", "House": "mdi:trash-can", "Garden": "mdi:leaf"}


class Source:
    def __init__(self, postcode: str, address: str):
        self._postcode = str(postcode).replace(" ", "+")
        self._address = str(address)
        self._ddlAddress: str = None

    def get_viewstate(self, content: str) -> dict:
        tags = {}
        soup = BeautifulSoup(content, "html.parser")
        hidden_tags = soup.findAll("input", type="hidden")
        for tag in hidden_tags:
            tags[tag.get("name")] = tag.get("value")
        return tags

    def fetch(self):
        s = requests.Session()

        # visit webpage to get viewstate info
        r = s.get(API_URL, headers=HEADERS)
        r.raise_for_status

        # update payload and perform address search
        payload = self.get_viewstate(r.content)
        payload.update(
            {
                "ctl00$ContentPlaceHolder1$tbPostCode$controltext": self._postcode,
                "ctl00$ContentPlaceHolder1$tbPostCode$_Mandatory": "true",
                "ctl00$ContentPlaceHolder1$btnLLPG": "Find+Address",
            }
        )
        r = s.post(API_URL, data=payload, headers=HEADERS)
        r.raise_for_status

        # search results for address and get unique house code
        soup = BeautifulSoup(r.content, "html.parser")
        options = soup.findAll("option")
        for item in options:
            if re.match(self._address, item.text, re.IGNORECASE):
                self._ddlAddress = item.get("value")

        # update payload and get schedule
        payload = self.get_viewstate(r.content)
        payload.update(
            {
                "ctl00$ContentPlaceHolder1$tbPostCode$controltext": self._postcode,
                "ctl00$ContentPlaceHolder1$tbPostCode$_Mandatory": "true",
                "ctl00$ContentPlaceHolder1$ddlAddresses": self._ddlAddress,
            }
        )
        r = s.post(API_URL, data=payload, headers=HEADERS)
        r.raise_for_status

        # extract collection dates
        entries = []
        soup = BeautifulSoup(r.content, "html.parser")
        for waste in ICON_MAP:
            containers = soup.findAll("div", {"id": f"ContentPlaceHolder1_pnl{waste}"})
            for item in containers:
                dt = item.find("span", {"id": f"ContentPlaceHolder1_Label{waste}"})
                entries.append(
                    Collection(
                        date=datetime.strptime(dt.text.strip(), "%A %d %B %Y").date(),
                        t=waste,
                        icon=ICON_MAP.get(waste),
                    )
                )

        return entries
