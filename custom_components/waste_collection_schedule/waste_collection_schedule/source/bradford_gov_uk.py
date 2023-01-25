import ssl
from datetime import datetime

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Bradford Metropolitan District Council"
DESCRIPTION = (
    "Source for Bradford.gov.uk services for Bradford Metropolitan Council, UK."
)
URL = "https://bradford.gov.uk"
TEST_CASES = {
    "Ilkley": {"uprn": "100051250665"},
    "Bradford": {"uprn": "100051239296"},
    "Baildon": {"uprn": "10002329242"},
}

API_URL = "https://onlineforms.bradford.gov.uk/ufs/"
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    """Transport adapter" that allows us to use custom ssl_context."""

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def fetch(self):
        entries = []

        s = requests.Session()
        # In openssl3 some context is needed to access this host
        # or an UNSAFE_LEGACY_RENEGOTIATION_DISABLED error will occur
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4
        s.mount("https://", CustomHttpAdapter(ctx))

        s.cookies.set(
            "COLLECTIONDATES", self._uprn, domain="onlineforms.bradford.gov.uk"
        )
        r = s.get(f"{API_URL}/collectiondates.eb")

        soup = BeautifulSoup(r.text, features="html.parser")
        div = soup.find_all("table", {"role": "region"})
        for region in div:
            displayClass = list(
                filter(lambda x: x.endswith("-Override-Panel"), region["class"])
            )
            if len(displayClass) > 0:
                heading = region.find_all(
                    "td", {"class": displayClass[0].replace("Panel", "Header")}
                )
                type = "UNKNOWN"
                if "General" in heading[0].text:
                    type = "REFUSE"
                elif "Recycling" in heading[0].text:
                    type = "RECYCLING"
                elif "Garden" in heading[0].text:
                    type = "GARDEN"
                lines = region.find_all("div", {"type": "text"})
                for entry in lines:
                    try:
                        entries.append(
                            Collection(
                                date=datetime.strptime(
                                    entry.text.strip(), "%a %b %d %Y"
                                ).date(),
                                t=type,
                                icon=ICON_MAP.get(type),
                            )
                        )
                    except ValueError:
                        pass  # ignore date conversion failure for not scheduled collections

        return entries
