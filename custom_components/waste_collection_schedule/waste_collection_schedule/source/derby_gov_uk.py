import logging
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Derby City Council"
DESCRIPTION = "Source for Derby.gov.uk services for Derby City Council, UK."
URL = "https://derby.gov.uk"
TEST_CASES = {
    # Derby City council wants specific addresses, hopefully these are generic enough.
    "Community Of The Holy Name, Morley Road, Derby, DE21 4TB": {
        "premises_id": "100030339868"
    },
    "6 Wilsthorpe Road, Derby, DE21 4QR": {"post_code": "DE21 4QR", "house_number": 6},
    "Allestree Home Improvements, 512 Duffield Road, Derby, DE22 2DL": {
        "premises_id": "100030310335"
    },
}

ICON_MAP = {
    "Black bin": "mdi:trash-can",
    "Blue bin": "mdi:recycle",
    "Brown bin": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self, premises_id: int = None, post_code: str = None, house_number: str = None
    ):
        self._premises_id = premises_id
        self._post_code = post_code
        self._house_number = house_number
        if not any([self._premises_id, self._post_code and self._house_number]):
            raise Exception(
                "premises_id or post_code and house number must be provided in config"
            )
        self._session = requests.Session()

    def fetch(self):
        entries = []

        if self._premises_id is not None:
            r = requests.get(
                "https://secure.derby.gov.uk/binday/Binday",
                params={
                    "PremisesId": self._premises_id,
                },
            )
        else:
            # Property search endpoint redirects you to the page, so by caching
            # The premises_id in future, we save an extra request every check.
            r = requests.get(
                "https://secure.derby.gov.uk/binday/StreetSearch",
                params={
                    "StreetNamePostcode": self._post_code,
                    "BuildingNameNumber": self._house_number,
                },
            )
            query = urlsplit(r.url).query
            params = parse_qs(query)
            self._premises_id = params["PremisesId"].pop()

        soup = BeautifulSoup(r.text, features="html.parser")
        results = soup.find_all("div", {"class": "binresult"})

        for result in results:
            date = result.find("strong")
            try:
                date = datetime.strptime(date.text, "%A, %d %B %Y:").date()
            except ValueError:
                _LOGGER.info(f"Skipped {date} as it does not match time format")
                continue
            img_tag = result.find("img")
            collection_type = img_tag["alt"]
            entries.append(
                Collection(
                    date=date,
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type),
                )
            )
        return entries
