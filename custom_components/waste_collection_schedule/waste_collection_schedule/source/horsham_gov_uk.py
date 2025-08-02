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
ICON_MAP = {
    "Refuse Bin for Non-Recycling": "mdi:trash-can",
    "Blue-Top Bin for Recycling": "mdi:recycle",
    "Brown-Top Bin for Garden Waste": "mdi:leaf",
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
                collection_text = result_row[2].text.replace(
                    "\xa0", " "
                )  # This is to remove a non-blanking space
                collection_items = collection_text.split(
                    "AND"
                )  # Sometimes there will be multiple bins, split with the word AND
                for collection_type in collection_items:
                    entries.append(
                        Collection(
                            date=date,
                            t=collection_type.strip(),  # Strip added to remove trailing white space
                            icon=ICON_MAP.get(
                                collection_type.strip()
                            ),  # Strip added to remove trailing white space
                        )
                    )

        return entries
