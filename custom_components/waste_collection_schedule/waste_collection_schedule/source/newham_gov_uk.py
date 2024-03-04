from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Newham"
DESCRIPTION = "Source for newham.gov.uk services for London Borough of Newham, UK."
URL = "https://www.newham.gov.uk"
TEST_CASES = {
    "Test_001": {"property": "000046029461"},
    "Test_002": {"property": "000046250697"},
    "Test_003": {"property": 46012509},
}

ICON_MAP = {"DOMESTIC": "mdi:trash-can", "RECYCLING": "mdi:glass-fragile"}


class Source:
    def __init__(self, property):
        self._property = str(property).zfill(12)

    def fetch(self):
        s = requests.Session()
        r = s.get(f"https://bincollection.newham.gov.uk/Details/Index/{self._property}")

        # Make a BS4 object
        soup = BeautifulSoup(r.text, features="html.parser")
        soup.prettify()

        # Form an array for the bins
        entries = []

        # Find section with bins in
        sections = soup.find_all("div", {"class": "card h-100"})

        # there may also be a recycling one too
        sections_recycling = soup.find_all(
            "div", {"class": "card h-100 card-recycling"}
        )
        if len(sections_recycling) > 0:
            sections.append(sections_recycling[0])

        # For each bin section, get the text and the list elements
        for item in sections:
            header = item.find("div", {"class": "card-header"})
            bin_type_element = header.find_next("b")
            if bin_type_element is None:
                continue
            bin_type = bin_type_element.text
            array_expected_types = ["Domestic", "Recycling"]
            if bin_type not in array_expected_types:
                continue
            date_string = (
                item.find_next("p", {"class": "card-text"})
                .find_next("mark")
                .next_sibling.strip()
            )
            next_collection = datetime.strptime(date_string, "%d/%m/%Y").date()

            entries.append(
                Collection(
                    date=next_collection,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type.split(" ")[0].upper()),
                )
            )

        return entries
