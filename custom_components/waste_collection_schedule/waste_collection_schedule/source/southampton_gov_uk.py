import logging
import re
import time
from datetime import datetime

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

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
    "Glass": Icons.GLASS,
    "Recycling": Icons.RECYCLING,
    "General Waste": Icons.GENERAL_WASTE,
    "Garden Waste": Icons.GARDEN,
    "Food": Icons.BIO_KITCHEN,
}
REGEX = r"(Food|Glass|Recycling|General Waste|Garden Waste).*?([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})"

# The council's site sits behind an Incapsula WAF that intermittently serves a
# JS challenge page instead of the calendar. Retrying a few times (mirroring
# what a browser refresh does) usually gets through.
MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 3

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        url = f"https://www.southampton.gov.uk/whereilive/waste-calendar?UPRN={self._uprn}"

        calendar_view_only = None
        last_status = None
        for attempt in range(1, MAX_RETRIES + 1):
            # Use a browser-like TLS fingerprint: the site's Incapsula WAF
            # intermittently blocks plain requests-library sessions.
            s = requests.Session(impersonate="chrome")
            r = s.get(url)
            last_status = r.status_code

            if r.ok:
                match = re.search(r"#calendar1.*?listView", r.text, flags=re.DOTALL)
                if match:
                    calendar_view_only = match[0]
                    break

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

        if calendar_view_only is None:
            raise Exception(
                "Unable to retrieve the waste calendar from southampton.gov.uk "
                f"after {MAX_RETRIES} attempts (last HTTP status: {last_status}). "
                "This is usually caused by the council's anti-bot protection "
                "(Incapsula) blocking the request; please try again later."
            )

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
