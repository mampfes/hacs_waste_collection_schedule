import re
from datetime import datetime

import bs4
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

URL = "https://southkesteven.gov.uk"
TEST_CASES = {
    "Test_001": {"address_id": 70158},
}
ICON_MAP = {
    "Black": "mdi:trash-can",
    "gray": "mdi:recycle",
    "purple": "mdi:newspaper",
}


TITLE = "South Kesteven District Council"
DESCRIPTION = "Source for southkesteven.gov.uk services for South Kesteven, UK."


# Extract bin type form text like "What goes in the black bin"
FUTURE_BIN_TYPE_REGEX = re.compile(r"What goes in the (\w+) bin")

# Extract bin type form text like "This is a black bin day - [...]"
NEXT_BIN_TYPE_REGEX = re.compile(r"This is a (\w+) bin day")


class Source:
    def __init__(self, address_id):
        self._address_id = address_id

    def fetch(self):
        r = requests.post(
            "https://pre.southkesteven.gov.uk/BinSearch.aspx", data={"address": "70158"}
        )
        r.raise_for_status()

        collections = []
        print(r.text)
        soup = bs4.BeautifulSoup(r.content, "html.parser")

        # Find next collection
        # find p looks like                     <p>Your next bin collection date is <span class="alert__heading alpha">Wed 19 June 2024</span></p>
        next_collection_p = soup.find(
            "p", text=re.compile("Your next bin collection date is")
        )
        # above does not work so try this

        if next_collection_p is not None:
            date_str = next_collection_p.find("span").text
            date = datetime.strptime(date_str, "%A %d %B %Y").date()
            bin_type = NEXT_BIN_TYPE_REGEX.search(
                next_collection_p.find_next("p").text
            ).group(1)
            collections.append(Collection(date, bin_type, ICON_MAP.get(bin_type)))
        else:
            raise ValueError("No next collection found")

        # Find all Future collections
        s = soup.find_all("h3", text="Future collections")

        for collections_list in s:
            collections_ul = collections_list.find_next_sibling("ul")
            collection_futher_info_link = (
                collections_ul.find_previous_sibling("ul").find("a").text
            )
            bin_type = FUTURE_BIN_TYPE_REGEX.search(collection_futher_info_link).group(
                1
            )

            print(collection_futher_info_link)

            for collection in collections_list.find_next_sibling("ul").find_all("li"):
                # like: "Thu 29 August 2024"
                date_str = collection.text

                date = datetime.strptime(date_str, "%a %d %B %Y").date()
                collections.append(Collection(date, bin_type, ICON_MAP.get(bin_type)))

        return []
