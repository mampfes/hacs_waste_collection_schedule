import logging
import re
from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]


_LOGGER = logging.getLogger(__name__)

TITLE = "Newcastle City Council"
DESCRIPTION = "Source for waste collection services for Newcastle City Council"
URL = "https://community.newcastle.gov.uk"
TEST_CASES = {"Test_001": {"uprn": "004510053797"}, "Test_002": {"uprn": 4510053797}}


API_URL = "https://community.newcastle.gov.uk/my-neighbourhood/ajax/getBinsNew.php"
REGEX = (
    "[Green|Blue|Brown] [Bb]in \(([A-Za-z]+)( Waste)?\) .*? ([0-9]{2}-[A-Za-z]+-[0-9]{4})"
    )
ICON_MAP = {
    "DOMESTIC": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)
        self._session = requests.Session()

    def fetch(self):
        entries = []
        res = requests.get(f"{API_URL}?uprn={self._uprn}")
        collections = re.findall(REGEX, res.text)

        for collection in collections:
            collection_type = collection[0]
            collection_date = collection[2]
            entries.append(
                Collection(
                    date=datetime.strptime(collection_date, "%d-%b-%Y").date(),
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type.upper()),
                )
            )

        return entries
