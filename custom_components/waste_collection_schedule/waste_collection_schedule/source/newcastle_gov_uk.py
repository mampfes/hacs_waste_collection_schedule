import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Newcastle City Council"
DESCRIPTION = "Source for waste collection services for Newcastle City Council"
URL = "https://community.newcastle.gov.uk"
TEST_CASES = {"Test_001": {"uprn": "004510053797"}, "Test_002": {"uprn": 4510053797}}


API_URL = "https://community.newcastle.gov.uk/my-neighbourhood/ajax/getBinsNew.php"

# Match each bin-type section in the HTML response.
# Group 1: waste type (e.g. "Domestic", "Recycling", "Garden")
# Group 2: remainder of that bin's section up to the next bin heading
SECTION_RE = re.compile(
    r"(?:Green|Blue|Brown) [Bb]in \(([A-Za-z]+)(?: Waste)?\)(.*?)(?=(?:Green|Blue|Brown) [Bb]in|\Z)",
    re.DOTALL,
)

# Match the "Next collection :" text portion of a section (up to the next HTML tag).
# Taking the LAST date on that line correctly handles the "was DD-Mon-YYYY, now DD-Mon-YYYY"
# phrasing used by the council during public-holiday substitutions.
NEXT_COLLECTION_RE = re.compile(r"Next collection\s*:[^<]*")
DATE_RE = re.compile(r"\d{2}-[A-Za-z]+-\d{4}")

ICON_MAP = {
    "DOMESTIC": Icons.GENERAL_WASTE,
    "RECYCLING": Icons.RECYCLING,
    "GARDEN": Icons.GARDEN,
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        entries = []
        res = requests.get(f"{API_URL}?uprn={self._uprn}")

        for section_match in SECTION_RE.finditer(res.text):
            collection_type = section_match.group(1)
            section_text = section_match.group(2)

            nc_line = NEXT_COLLECTION_RE.search(section_text)
            if not nc_line:
                continue

            dates = DATE_RE.findall(nc_line.group(0))
            if not dates:
                continue

            # When a collection is shifted due to a public holiday the council
            # displays "was <original-date>, now <rescheduled-date>".  The
            # rescheduled date is always the last date on that line.
            collection_date = dates[-1]

            entries.append(
                Collection(
                    date=datetime.strptime(collection_date, "%d-%b-%Y").date(),
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type.upper()),
                )
            )

        return entries
