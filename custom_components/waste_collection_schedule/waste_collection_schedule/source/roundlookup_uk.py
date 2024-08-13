import logging
from datetime import datetime
from typing import Literal

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


_LOGGER = logging.getLogger(__name__)

TITLE = "Malvern Hills District Council"
DESCRIPTION = "Source for Malvern Hills District Council."
URL = "https://www.malvernhills.gov.uk/"
TEST_CASES = {
    "1Malvern Hill: s00120597618": {"uprn": 100120597618, "council": "Malvern Hills"},
    "Malvern Hills: 100121268004": {
        "uprn": "100121268004",
        "council": "Malvern Hills",
    },
    "Worcester City: 100120656169": {
        "uprn": 100120656169,
        "council": "Worcester City",
    },
    "Wychavon: 10095592085": {"uprn": 10095592085, "council": "Wychavon"},
}


ICON_MAP = {
    "Non-recyclable": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


SERVICE_MAP = {
    "Malvern Hills": {
        "api_url": "https://swict.malvernhills.gov.uk/mhdcroundlookup/HandleSearchScreen",
        "url": "https://www.malvernhills.gov.uk/",
    },
    "Wychavon": {
        "api_url": "https://selfservice.wychavon.gov.uk/wdcroundlookup/HandleSearchScreen",
        "url": "https://www.wychavon.gov.uk/",
    },
    "Worcester City": {
        "api_url": "https://selfserve.worcester.gov.uk/wccroundlookup/HandleSearchScreen",
        "url": "https://www.worcester.gov.uk/",
    },
}

EXTRA_INFO = [
    {
        "url": value["url"],
        "title": key,
        "default_params": {"council": key},
    }
    for key, value in SERVICE_MAP.items()
]

COUNIL_LITERAL = Literal["Malvern Hills", "Wychavon", "Worcester City"]


class Source:
    def __init__(self, uprn: str | int, council: COUNIL_LITERAL) -> None:
        self._api_url = SERVICE_MAP.get(council, {}).get("api_url", "")
        if not self._api_url:
            raise ValueError(
                f"District '{council}' not supported, use one of {SERVICE_MAP.keys()}"
            )
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        data: dict[str, str | int] = {
            "alAddrsel": self._uprn,
            "txtPage": "std",
            "txtSearchPerformedFlag": "false",
            "futuredate": "",
            "address": "",
            "btnSubmit": "Next",
        }

        r = requests.post(self._api_url, data=data, verify=False)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.select_one("table")
        if not table:
            raise ValueError("collection table not, maybe wrong/unsupported address")

        entries = []
        for tr in table.select("tr"):
            tds = tr.select("td")
            if not len(tds) == 3:
                continue

            bin_type_tag = tds[1]
            # remove all divs
            div = bin_type_tag.select_one("div")
            if div:
                div.decompose()

            bin_type = bin_type_tag.text.strip().removesuffix("collection").strip()
            date_text = tds[2].text.strip()
            if "Not applicable" in date_text:
                continue
            icon = ICON_MAP.get(bin_type.split()[0])

            # Thursday 22/08/2024
            for date_str in date_text.split("\n"):
                date_str = date_str.strip()
                if not date_str:
                    continue
                try:
                    date = datetime.strptime(date_str, "%A %d/%m/%Y").date()
                except ValueError:
                    _LOGGER.warning(
                        "Could not parse date '%s', unknown format", date_str
                    )
                    continue
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
