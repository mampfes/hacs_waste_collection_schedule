from datetime import datetime

import requests
import re
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

from bs4 import BeautifulSoup

import logging

TITLE = "stockport.gov.uk"
DESCRIPTION = "Source for bin collection services for Stockport Council, UK.\n Refactored with thanks from the Manchester equivalent"
URL =  "https://myaccount.stockport.gov.uk/bin-collections/show/"
TEST_CASES = {
    "domestic": {'uprn': '100011460157'},
}

ICONS = {
    "Black bin": "mdi:trash-can",
    "Blue bin": "mdi:recycle",
    "Brown bin": "mdi:glass-fragile",
    "Green bin": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self, uprn: int = None
    ):
        self._uprn = uprn
        if not self._uprn:
            _LOGGER.error(
                "uprn must be provided in config"
            )
        self._session = requests.Session()

    def fetch(self):
        entries = []

        bin_URL = URL + self._uprn

        r = requests.get(
            bin_URL,
            )

        soup = BeautifulSoup(r.text, features="html.parser")

        results = soup.find_all("div", {"class": "collection"})
        bins = soup.find_all("div" ,{"class": re.compile("service-item service-item-.*")})

        bins = str(bins)
        header_string = "<h3>"
        bin_name_start_position = bins.find(header_string)
        while bin_name_start_position != -1:
            bin_name_start_position += len(header_string)
            bin_name_end_position = bins.find(" bin",bin_name_start_position) + 4
            bin_name = bins[bin_name_start_position:bin_name_end_position]
            bin_date_pos = bins.find("<p>",bin_name_start_position)
            bin_date_exc_day_of_week_pos = bins.find(", ",bin_date_pos)+2
            bin_date_end_pos = bins.find("</p>",bin_date_exc_day_of_week_pos)
            bin_date_string = bins[bin_date_exc_day_of_week_pos:bin_date_end_pos]
            bin_date = datetime.strptime(bin_date_string,'%d %B %Y').date()
            entries.append(
                Collection(
                    date=bin_date,
                    t=bin_name,
                    icon=ICONS[bin_name],
                )
            )
            bin_name_start_position = bins.find(header_string,bin_date_end_pos)

        return entries
