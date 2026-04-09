import logging
import ssl
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from waste_collection_schedule import Collection

TITLE = "Horsham District Council"
DESCRIPTION = "Source script for Horsham District Council"
URL = "https://www.horsham.gov.uk"
TEST_CASES = {
    "Blackthorn Avenue - number": {"uprn": 10013792881},
    "Blackthorn Avenue - string": {"uprn": "10013792881"},
}
API_URL = "https://satellite.horsham.gov.uk/environment/refuse/cal_details.asp"
# Updated 1st April 2026 as Food Waste was added, and the names for the refuse bins had been updated
ICON_MAP = {
    "Green Bin for Refuse and Non-Recycling": "mdi:trash-can",
    "Blue-Top Bin for Recycling": "mdi:recycle",
    "Brown-Top Bin for Garden Waste": "mdi:leaf",
    "Orange-Top Bin for Food Waste": "mdi:food",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
_LOGGER = logging.getLogger(__name__)


class LegacyTLSAdapter(HTTPAdapter):
    # Modern python libraries reject Horsham server settings and return connection reset errors,
    # Try and force requests to use downgraded settings
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("AES256-SHA256")  # Explicitly use this cipher
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # Explicitly use this TLS version
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2  # Explicitly use this TLS version
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self):

        # Use customised TLS/cipher settings
        s = requests.Session()
        s.mount("https://", LegacyTLSAdapter())
        _LOGGER.warning(
            "Forcing requests to use legacy TLSv1.2 & AES256-SHA256 to match horsham.gov.uk website"
        )

        r = s.post(
            API_URL,
            data={"uprn": self._uprn},
        )
        soup = BeautifulSoup(r.text, features="html.parser")
        results = soup.find_all("tr")

        entries = []
        for result in results:
            result_row = result.find_all("td")
            if (
                len(result_row) == 0
            ):  # This removes the first header row, or any rows with no data
                continue
            else:
                date = datetime.strptime(
                    result_row[1].text, "%d/%m/%Y"
                ).date()  # Pull out the rows date

                # The website now uses <li> elements for each bin type
                list_items = result_row[2].find_all("li")
                collection_items = [li.get_text(strip=True) for li in list_items]
                for collection_type in collection_items:
                    if not collection_type:
                        continue
                    entries.append(
                        Collection(
                            date=date,
                            t=collection_type,
                            icon=ICON_MAP.get(collection_type),
                        )
                    )

        return entries
