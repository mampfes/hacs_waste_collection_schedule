from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Wiltshire Council"
DESCRIPTION = "Source for wiltshire.gov.uk services for Wiltshire Council"
URL = "https://wiltshire.gov.uk"
TEST_CASES = {
    "standard_uprn": {"uprn": "100121085972", "postcode": "BA149QP"},
    "short_uprn": {"uprn": "10093279003", "postcode": "SN128FF"},
    "padded_uprn": {"uprn": "010093279003", "postcode": "SN128FF"},
}

SEARCH_URLS = {
    "collection_search": "https://ilforms.wiltshire.gov.uk/wastecollectiondays/collectionlist"
}
COLLECTIONS = {
    "Household waste",
    "Mixed dry recycling (blue lidded bin)",  # some addresses may not have a black box collection
    "Mixed dry recycling (blue lidded bin) and glass (black box or basket)",
    "Chargeable garden waste",  # some addresses also have a chargeable garden waste collection
}
ICON_MAP = {
    "Household waste": "mdi:trash-can",
    "Mixed dry recycling (blue lidded bin)": "mdi:recycle",
    "Mixed dry recycling (blue lidded bin) and glass (black box or basket)": "mdi:recycle",
    "Chargeable garden waste": "mdi:leaf",
}


def add_month(date_):
    if date_.month < 12:
        date_ = date_.replace(month=date_.month + 1)
    else:
        date_ = date_.replace(year=date_.year + 1, month=1)
    return date_


class Source:
    def __init__(
        self, uprn=None, postcode=None
    ):  # argX correspond to the args dict in the source configuration
        self._uprn = str(uprn).zfill(12)  # pad uprn to 12 characters
        self._postcode = postcode

    def fetch(self):
        fetch_month = date.today().replace(day=1)

        entries = []
        for i in range(0, 7):
            entries.extend(self.fetch_month(fetch_month))
            fetch_month = add_month(fetch_month)

        return entries

    def fetch_month(self, fetch_month):
        args = {
            "Postcode": self._postcode,
            "Uprn": self._uprn,
            "Month": fetch_month.month,
            "Year": fetch_month.year,
        }

        r = requests.post(SEARCH_URLS["collection_search"], params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for collection in COLLECTIONS:
            for tag in soup.find_all(attrs={"data-original-title": collection}):
                entries.append(
                    Collection(
                        datetime.strptime(
                            tag["data-original-datetext"], "%A %d %B, %Y"
                        ).date(),
                        collection,
                        icon=ICON_MAP.get(collection),
                    )
                )
        return entries
