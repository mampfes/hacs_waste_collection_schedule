import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "London Borough of Richmond upon Thames"
DESCRIPTION = "Source for London Borough of Richmond upon Thames"
URL = "https://www.richmond.gov.uk/"

TEST_CASES = {
    "Sheen Common Drive": {"uprn": "100022316011"},
    "Rosemont Road": {"uprn": "100022315214"},
    "Bryanston Avenue": {"uprn": "100022330653"},
}

API_URL = "https://www.richmond.gov.uk/my_richmond"

ICON_MAP = {
    "Glass, can, plastic and carton recycling": "mdi:recycle",
    "Paper and card recycling": "mdi:newspaper-variant",
    "Rubbish and food": "mdi:trash-can",
    "Garden waste": "mdi:leaf",
}

ALLOWED_SERVICES = set(ICON_MAP.keys())


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        params = {"pid": self._uprn}
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        waste_div = soup.find("div", class_="my-waste")

        if not waste_div:
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries = []

        for h4 in waste_div.find_all("h4"):
            service_name = h4.get_text(strip=True)

            if service_name not in ALLOWED_SERVICES:
                continue

            ul_sibling = h4.find_next_sibling("ul")
            if not ul_sibling:
                continue

            li = ul_sibling.find("li")
            if not li:
                continue

            for a in li.find_all("a"):
                a.decompose()

            li_text = li.get_text(strip=True)

            if "No collection contract" in li_text or not li_text:
                continue

            try:
                date_parts = li_text.split()
                if len(date_parts) < 3:
                    continue

                date_str = " ".join(date_parts[-3:])

                collection_date = datetime.datetime.strptime(
                    date_str, "%d %B %Y"
                ).date()

                entries.append(
                    Collection(
                        date=collection_date,
                        t=service_name,
                        icon=ICON_MAP.get(service_name),
                    )
                )
            except (ValueError, IndexError):
                continue

        return entries
