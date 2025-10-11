import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wandsworth Council"  # Title will show up in README.md and info.md
# Describe your source
DESCRIPTION = "Source for www.wandsworth.gov.uk services for Wandsworth Council, UK"
# Insert url to service homepage. URL will show up in README.md and info.md
URL = "https://www.wandsworth.gov.uk/"
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Strickland Row": {"uprn": "100022697634"},
    "Fullerton Road": {"uprn": "100022645572"},
}

API_URL = "https://www.wandsworth.gov.uk/my-property/?UPRN=100022697634&propertyidentified=Select"

ICON_MAP = {
    "Food waste": "mdi:food-apple",
    "Recycling": "mdi:recycle",
    "Rubbish/Garden waste": "mdi:trash-can",
    "Small electrical items": "mdi:battery",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        r = requests.get(API_URL.format(uprn=self._uprn))
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        results = []

        for heading in soup.find_all("h4", class_="collection-heading"):
            waste_type = heading.get_text(strip=True)

            # Find the next sibling <div class="collections">
            collections_div = heading.find_next_sibling(
                "div", class_="collections")
            if not collections_div:
                continue

            # Find the <div> that contains "Next:"
            next_div = collections_div.find(
                "div", string=lambda s: s and "Next:" in s)
            if not next_div:
                # fallback: search through inner divs
                for div in collections_div.find_all("div", class_="collection"):
                    strong = div.find("strong")
                    if strong and "Next:" in strong.get_text():
                        next_div = div
                        break

            if next_div:
                date_text = next_div.get_text(
                    strip=True).replace("Next:", "").strip()

                try:
                    parsed_date = parser.parse(date_text).date()
                except Exception:
                    parsed_date = date_text

            results.append(
                Collection(
                    date=parsed_date,  # Collection date
                    t=waste_type,  # Collection type
                    icon=ICON_MAP.get(waste_type),  # Collection icon
                )
            )
        return results
