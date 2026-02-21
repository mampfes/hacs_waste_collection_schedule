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
        collection_groups = services.find_all("u1", class_="displayinlineblock")
        for group in collection_groups:
            li_elements = group.find_all("li")
            if len(li_elements) < 3:
                continue
            date_li = li_elements[1]
            date_text = date_li.find("p").text.strip()
            type_li = li_elements[2]
            type_text = type_li.find("p").text.strip()
            try:
                dt = datetime.strptime(date_text, "%d/%m/%Y").date()
                collection_type = type_text.removesuffix(" Collection Service")
                entries.append(
                    Collection(
                        date=dt,
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type, "mdi:trash-can"),
                    )
                )
            except ValueError:
                _LOGGER.info(
                    f"Skipped {date_text} as it does not match time format"
                )
        return entries
