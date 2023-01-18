import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stockport Council"
DESCRIPTION = "Source for bin collection services for Stockport Council, UK.\n Refactored with thanks from the Manchester equivalent"
URL = "https://stockport.gov.uk"
TEST_CASES = {
    "domestic": {"uprn": "100011460157"},
}

ICON_MAP = {
    "Black bin": "mdi:trash-can",
    "Blue bin": "mdi:recycle",
    "Brown bin": "mdi:glass-fragile",
    "Green bin": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):

        r = requests.get(
            f"https://myaccount.stockport.gov.uk/bin-collections/show/{self._uprn}"
        )

        soup = BeautifulSoup(r.text, features="html.parser")

        bins = soup.find_all(
            "div", {"class": re.compile("service-item service-item-.*")}
        )

        bins = str(bins)
        header_string = "<h3>"
        bin_name_start_position = bins.find(header_string)

        entries = []
        while bin_name_start_position != -1:
            bin_name_start_position += len(header_string)
            bin_name_end_position = bins.find(" bin", bin_name_start_position) + 4
            bin_name = bins[bin_name_start_position:bin_name_end_position]
            bin_date_pos = bins.find("<p>", bin_name_start_position)
            bin_date_exc_day_of_week_pos = bins.find(", ", bin_date_pos) + 2
            bin_date_end_pos = bins.find("</p>", bin_date_exc_day_of_week_pos)
            bin_date_string = bins[bin_date_exc_day_of_week_pos:bin_date_end_pos]
            bin_date = datetime.strptime(bin_date_string, "%d %B %Y").date()
            entries.append(
                Collection(
                    date=bin_date,
                    t=bin_name,
                    icon=ICON_MAP.get(bin_name),
                )
            )
            bin_name_start_position = bins.find(header_string, bin_date_end_pos)

        return entries
