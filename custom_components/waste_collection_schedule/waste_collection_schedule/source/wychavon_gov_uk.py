from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "Wychavon District Council"
DESCRIPTION = "Source for Wychavon District Council."
URL = "https://wychavon.gov.uk/"
TEST_CASES = {
    "10013938132": {"uprn": 10013938132},
    "10013938131": {"uprn": "10013938131"},
    "100121280854": {"uprn": 100121280854},
}


ICON_MAP = {
    "Non-recyclable": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


API_URL = "https://selfservice.wychavon.gov.uk/wdcroundlookup/HandleSearchScreen"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        data = {"alAddrsel": self._uprn}

        # get json file
        r = requests.post(API_URL, data=data, verify=False)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table", {"class": "table table-striped"})
        rows = table.find_all("tr")

        entries: list[Collection] = []
        for row in rows:
            if not isinstance(row, Tag):
                continue
            tds: list[Tag] = row.find_all("td")
            if len(tds) < 3:
                continue

            # remove everything inside tds[1] that's not text directly inside the tag
            for tag in tds[1].find_all():
                if not isinstance(tag, Tag):
                    continue
                if tag.name != "br":
                    tag.decompose()

            collection_type = tds[1].text.strip()
            date_strs = [date.text.strip() for date in tds[2] if date.text.strip()]

            for date_str in date_strs:
                try:
                    # Like Thursday 11/07/2024
                    date = datetime.strptime(date_str, "%A %d/%m/%Y").date()
                except ValueError:
                    continue

                entries.append(
                    Collection(
                        date, collection_type, ICON_MAP.get(collection_type.split()[0])
                    )
                )

        return entries
