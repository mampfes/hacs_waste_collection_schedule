import requests

from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Wiltshire Council, UK"
DESCRIPTION = "Source for wiltshire.gov.uk services for Wiltshire Council"
URL = "wiltshire.gov.uk"
TEST_CASES = {
    "house_uprn": {"uprn": "100121085972", "postcode": "BA149QP"},
}
SEARCH_URLS = {
    "collection_search": "https://ilforms.wiltshire.gov.uk/wastecollectiondays/collectionlist"
}
COLLECTIONS = {"Household waste",
               "Mixed dry recycling (blue lidded bin)", # some addresses may not have a black box collection
               "Mixed dry recycling (blue lidded bin) and glass (black box or basket)",
               "Chargeable garden waste" # some addresses also have a chargeable garden waste collection
               }


class Source:
    def __init__(
        self, uprn=None, postcode=None, housenumberorname=None
    ):  # argX correspond to the args dict in the source configuration
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self):
        entries = []
        session = requests.Session()
        args = {
            "Postcode": self._postcode,
            "Uprn": self._uprn,
        }
        r = session.post(SEARCH_URLS["collection_search"], params=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for collection in COLLECTIONS:
            for tag in soup.find_all(
                    attrs={"data-original-title": collection}
            ):

                entries.append(
                    Collection(
                        datetime.strptime(
                            tag['data-original-datetext'], "%A %d %B, %Y").date(),
                        collection,
                    )
                )

        # If current date is within 14 days of month end, also retrieve next month's dates
        futuredate = date.today() + timedelta(days=14)
        if futuredate.month != date.today().month:
            args = {
                "Postcode": self._postcode,
                "Uprn": self._uprn,
                "Month": futuredate.month,
                "Year": futuredate.year
            }
            r = session.post(SEARCH_URLS["collection_search"], params=args)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            for collection in COLLECTIONS:
                for tag in soup.find_all(
                        attrs={"data-original-title": collection}
                ):

                    entries.append(
                        Collection(
                            datetime.strptime(
                                tag['data-original-datetext'], "%A %d %B, %Y").date(),
                            collection,
                        )
                    )

        return entries
