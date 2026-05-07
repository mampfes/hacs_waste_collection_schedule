import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "BinDay (South & Vale)"
URL = "https://www.southoxon.gov.uk/"
EXTRA_INFO = [
    {
        "title": "South Oxfordshire District Council",
        "url": "https://www.southoxon.gov.uk/",
    },
    {
        "title": "Vale of White Horse District Council",
        "url": "https://www.whitehorsedc.gov.uk/",
    },
]
DESCRIPTION = """Consolidated source for waste collection services from:
        South Oxfordshire District Council
        Vale of White Horse District Council
        """
TEST_CASES = {
    "VOWH": {"uprn": "100120903018"},
    "SO": {"uprn": "100120883950"},
}

ICON_MAP = {
    "recycling": "mdi:recycle",
    "refuse": "mdi:trash-can",
    "garden": "mdi:leaf",
    "food": "mdi:food-apple",
    "textile": "mdi:hanger",
    "clothes": "mdi:hanger",
    "electric": "mdi:hair-dryer",
    "batter": "mdi:battery",
    "bulky": "mdi:sofa",
}

API_URL = "https://forms.southandvale.gov.uk/api/property/bins/{uprn}"

_LOGGER = logging.getLogger(__name__)


def _icon_for_bin_type(bin_type: str) -> str | None:
    lower = bin_type.lower()
    for keyword, icon in ICON_MAP.items():
        if keyword in lower:
            return icon
    return None


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://forms.southandvale.gov.uk/binday.eb",
        }

        r = requests.get(
            API_URL.format(uprn=self._uprn),
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()

        data = r.json()

        if data.get("setStatus") != "OK":
            raise ValueError(
                f"BinDay API returned non-OK status: {data.get('setStatus')}: {data.get('setMessage')}"
            )

        entries = []

        for week in data["setData"]["week"]:
            for day in week["day"]:
                collection_date = datetime.strptime(
                    day["collection_date"], "%d/%m/%Y"
                ).date()
                for bin_info in day["bins"]:
                    bin_type = bin_info["bin_type"]
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=bin_type,
                            icon=_icon_for_bin_type(bin_type),
                        )
                    )

        return entries
