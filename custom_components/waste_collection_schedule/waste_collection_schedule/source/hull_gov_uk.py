from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Hull City Council"
DESCRIPTION = "Source for Hull City Council."
URL = "https://hull.gov.uk/"
TEST_CASES = {
    "21095794": {"uprn": 21095794},
    "21009164": {"uprn": "21009164"},
}


ICON_MAP = {
    "black": "mdi:trash-can",
    "blue": "mdi:package-variant",
    "brown": "mdi:food-apple",
    "bulky": "mdi:sofa",
}


API_URL = "https://www.hull.gov.uk/ajax/bin-collection"
REFERER = "https://www.hull.gov.uk"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        # get json
        r = requests.get(
            API_URL,
            params={"bindate": self._uprn},
            headers={"Referer": REFERER, "User-Agent": USER_AGENT},
        )
        r.raise_for_status()

        data = r.json()
        data = data[0] if isinstance(data[0], list) else data

        entries = []
        for entry in data:
            date = datetime.strptime(entry["next_collection_date"], "%Y-%m-%d").date()
            icon = ICON_MAP.get(
                entry["collection_type"].lower().replace("bin", "").strip()
            )  # Collection icon
            type = entry["collection_type"]
            entries.append(Collection(date=date, t=type, icon=icon))

        return entries
