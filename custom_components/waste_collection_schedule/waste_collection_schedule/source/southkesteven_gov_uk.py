import logging
import re
from datetime import datetime, timedelta

import bs4
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

URL = "https://southkesteven.gov.uk"
TEST_CASES = {
    "Long Bennington": {"address_id": 33399},
    "Bourne": {"address_id": "7351"},
    "Grantham": {"address_id": 18029},
}
_LOGGER = logging.getLogger(__name__)
ICON_MAP = {
    "black": "mdi:trash-can",
    "gray": "mdi:recycle",
    "green": "mdi:leaf",
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
            "https://pre.southkesteven.gov.uk/BinSearch.aspx", data={"address": self._address_id}
        )
        r.raise_for_status()

        collections = []
        soup = bs4.BeautifulSoup(r.content, "html.parser")

        date_translate = {
            "Tomorrow": datetime.now().date() + timedelta(days=1),
            "Today": datetime.now().date(),
        }

        # Find next collection
        # find p looks like                     <p>Your next bin collection date is <span class="alert__heading alpha">Wed 19 June 2024</span></p>
        next_collection_p = soup.find(
            lambda tag: tag.name == "p"
            and "Your next bin collection date is" in tag.text
        )
        # above does not work so try this

        if next_collection_p is None:
            _LOGGER.warning(
                "No next collection text found, continuing to look for future collections"
            )
        else:
            date_str = next_collection_p.find("span").text
            date = (
                date_translate.get(date_str)
                or datetime.strptime(date_str, "%a %d %B %Y").date()
            )
            bin_type = NEXT_BIN_TYPE_REGEX.search(
                next_collection_p.find_next("p").text
            ).group(1)
            collections.append(Collection(date, bin_type, ICON_MAP.get(bin_type)))

        # Find all Future collections
        s = soup.find_all("h3", text="Future collections")

        for collections_list in s:
            collections_ul = collections_list.find_next_sibling("ul")
            collection_futher_info_link = (
                collections_ul.find_previous_sibling("ul").find("a")
            )
            if (collection_futher_info_link is None):
                garden_check = (collections_ul.find_previous_sibling("ul").find>
                if garden_check == "Leaves":
                    bin_type = "green"
            else:
                bin_type = FUTURE_BIN_TYPE_REGEX.search(collection_futher_info_link.text).group(
                    1
                )

            for collection in collections_list.find_next_sibling("ul").find_all("li"):
                # like: "Thu 29 August 2024"
                date_str = collection.text

                try:
                    date = (
                        date_translate.get(date_str)
                        or datetime.strptime(date_str, "%a %d %B %Y").date()
                    )
                except ValueError:
                    _LOGGER.warning(
                        f"Failed to parse date {date_str}, skipping this collection"
                    )
                    continue
                collections.append(Collection(date, bin_type, ICON_MAP.get(bin_type)))

        # filter out duplicate entries
        collections = list(
            {
                (collection.date, collection.type): collection
                for collection in collections
            }.values()
        )

        return collections
