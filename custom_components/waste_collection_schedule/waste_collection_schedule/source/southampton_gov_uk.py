import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Southampton City Council"
DESCRIPTION = "Source for southampton.gov.uk services for Southampton City Council"
URL = "https://southampton.gov.uk"
TEST_CASES = {
    "UPRN_001": {"uprn": "100060731893"},
    "UPRN_002": {"uprn": 100060685712},
    "UPRN_003": {"uprn": "100060679858"},
    "UPRN_004": {"uprn": 100060703113},
}
ICON_MAP = {
    "Glass": "mdi:glass-fragile",
    "Recycling": "mdi:recycle",
    "General Waste": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
}
REGEX = (
    r"(Glass|Recycling|General Waste|Garden Waste).*?([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})"
)

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            f"https://www.southampton.gov.uk/whereilive/waste-calendar?UPRN={self._uprn}"
        )
        r.raise_for_status()

        # Limit search scope to avoid duplicates
        calendar_view_only = re.search(
            r"#calendar1.*?listView", r.text, flags=re.DOTALL
        )[0]

        results = re.findall(REGEX, calendar_view_only)

        entries = []
        for item in results:
            entries.append(
                Collection(
                    date=datetime.strptime(item[1], "%m/%d/%Y").date(),
                    t=item[0],
                    icon=ICON_MAP.get(item[0]),
                )
            )

        return entries
