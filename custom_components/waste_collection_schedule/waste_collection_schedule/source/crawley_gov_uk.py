# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData


import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Crawley Borough Council (myCrawley)"
DESCRIPTION = "Source for Crawley Borough Council (myCrawley)."
URL = "https://crawley.gov.uk/"
TEST_CASES = {
    "Feroners Cl": {"uprn": "100061775179"},
    "Peterborough Road": {"uprn": 100061787552, "usrn": 9700731},
}


ICON_MAP = {
    "Rubbish and Small Electricals Collection": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycling and Textiles Collection": "mdi:recycle",
}


API_URL = "https://my.crawley.gov.uk/en/service/check_my_bin_collection"


class Source:
    def __init__(self, uprn: str | int, usrn: str | int | None = None):
        self._uprn = str(uprn)
        self._usrn = str(usrn) if usrn else None

    def fetch(self):
        today = datetime.now().date()
        day = today.day
        month = today.month
        year = today.year

        api_url = (
            f"https://my.crawley.gov.uk/appshost/firmstep/self/apps/custompage/waste?language=en&uprn={self._uprn}"
            f"&usrn={self._usrn}&day={day}&month={month}&year={year}"
        )
        response = requests.get(api_url)

        soup = BeautifulSoup(response.text, features="html.parser")
        soup.prettify()

        entries = []

        titles = [title.text.strip() for title in soup.select(".block-title")]
        collection_tag = soup.body.find_all(
            "div",
            {"class": "col-md-6 col-sm-6 col-xs-6"},
            string=re.compile("Next collection|Current or last collection"),
        )

        bin_index = 0
        for tag in collection_tag:
            for item in tag.next_elements:
                if str(item).startswith('<div class="date text-right text-grey">'):
                    collection_date = datetime.strptime(
                        item.text + " " + str(year), "%A %d %B %Y"
                    ).date()
                    if collection_date < today and bin_index % 2 == 1:
                        collection_date = collection_date.replace(
                            year=collection_date.year + 1
                        )
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=titles[bin_index // 2],
                            icon=ICON_MAP.get(titles[bin_index // 2]),
                        )
                    )
                    bin_index += 1
                    break

        return entries
