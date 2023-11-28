import logging
from datetime import datetime
from typing import Union

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Lancaster City Council"
DESCRIPTION = "Source for lancaster.gov.uk services for Lancaster City Council, UK."
URL = "https://lancaster.gov.uk"
TEST_CASES = {
    "1 Queen Street Lancaster, LA1 1RS": {"house_number": 1, "postcode": "LA1 1RS"}
}
API_URLS = {"BASE": "https://lcc-wrp.whitespacews.com"}
ICON_MAP = {
    "Domestic Waste": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    "Recycling": "mdi:recycle",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self, postcode: str, house_number: Union[int, str, None] = None
    ) -> None:
        self._house_number = house_number
        self._postcode = postcode
        self._session = requests.Session()

    def fetch(self):
        entries = []

        # start session
        response = self._session.get(API_URLS["BASE"] + "/#!")
        links = [
            a["href"]
            for a in BeautifulSoup(response.text, features="html.parser").select("a")
        ]
        portal_link = ""
        for link in links:
            if "seq=1" in link:
                portal_link = link

        # fill address form
        response = self._session.get(portal_link)
        form = BeautifulSoup(response.text, features="html.parser").find("form")
        form_url = dict(form.attrs).get("action")
        payload = {
            "address_name_number": self._house_number,
            "address_street": "",
            "address_postcode": self._postcode,
        }

        # get (first) found address
        response = self._session.post(form_url, data=payload)
        links = [
            a["href"]
            for a in BeautifulSoup(response.text, features="html.parser").select("a")
        ]
        addr_link = ""
        for link in links:
            if "seq=3" in link:
                addr_link = API_URLS["BASE"] + "/" + link

        # get json formatted bin data for addr
        response = self._session.get(addr_link)
        new_soup = BeautifulSoup(response.text, features="html.parser")
        services = new_soup.find("section", {"id": "scheduled-collections"})
        services_sub = services.find_all("li")
        for i in range(0, len(services_sub), 3):
            try:
                dt = datetime.strptime(
                    services_sub[i + 1].text.strip(), "%d/%m/%Y"
                ).date()
            except ValueError:
                _LOGGER.info(
                    f"Skipped {services_sub[i + 1].text.strip()} as it does not match time format"
                )
                continue
            bin_type = BeautifulSoup(services_sub[i + 2].text, features="lxml").find(
                "p"
            )
            entries.append(
                Collection(
                    date=dt,
                    t=bin_type.text.strip().removesuffix(" Collection Service"),
                    icon=ICON_MAP[
                        bin_type.text.strip().removesuffix(" Collection Service")
                    ],
                )
            )

        return entries
