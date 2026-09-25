import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Exeter City Council"
DESCRIPTION = "Source for Exeter City services for Exeter City Council, UK."
URL = "https://exeter.gov.uk/"
COUNTRY = "uk"
TEST_CASES = {
    "Test_001": {"uprn": "100040227486"},
    "Test_002": {"uprn": "10013043921"},
    "Test_003": {"uprn": 10023120282},
    "Test_004": {"uprn": 100040241022},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Look up your address on the Exeter City Council 'When is my bin collected?' page; your UPRN is the number at the end of the resulting URL. Alternatively, search for your address on [Find My Address](https://www.findmyaddress.co.uk/).",
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) of your property, e.g. 100040227486",
    }
}
ICON_MAP = {
    "REFUSE": Icons.GENERAL_WASTE,
    "RECYCLING": Icons.RECYCLING,
    "GARDEN WASTE": Icons.GARDEN,
    "FOOD WASTE": Icons.BIO_KITCHEN,
}
SOURCE_CODEOWNERS = ["@AtomBrake"]

API_URL = "https://exeter.gov.uk/repositories/hidden-pages/address-finder/"
# The council's web application firewall rejects the default python-requests User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}
REGEX_ORDINALS = re.compile(r"(?<=\d)(?:st|nd|rd|th)\b")
DATE_FORMATS = ("%A, %d %B %Y", "%A %d %B %Y")

_LOGGER = logging.getLogger(__name__)


def _parse_date(text: str):
    raw_date = REGEX_ORDINALS.sub("", text)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw_date, fmt).date()
        except ValueError:
            continue
    return None


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(
            API_URL,
            params={"qsource": "UPRN", "qtype": "bins", "term": self._uprn},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()

        data = r.json()
        if not data:
            raise SourceArgumentNotFound("uprn", self._uprn)

        soup = BeautifulSoup(data[0]["Results"], "html.parser")

        entries = []
        for heading in soup.find_all("h2"):
            # Each bin type is an <h2> followed by an <h3> holding the next
            # date. Bin types the property doesn't have (e.g. garden waste
            # without a subscription) have no <h3>, so only look for one
            # before the next <h2>.
            date_tag = None
            for sibling in heading.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name == "h3":
                    date_tag = sibling
                    break
            if date_tag is None:
                continue

            waste_type = heading.get_text(strip=True).replace(" collection", "")
            date_text = date_tag.get_text(strip=True)
            date = _parse_date(date_text)
            if date is None:
                _LOGGER.warning(
                    "Could not parse date '%s' for %s", date_text, waste_type
                )
                continue

            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.upper()),
                )
            )

        return entries
