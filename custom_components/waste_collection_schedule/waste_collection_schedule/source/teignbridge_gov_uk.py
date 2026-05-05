from datetime import datetime

from curl_cffi import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Teignbridge District Council"
DESCRIPTION = "Source for teignbridge.gov.uk waste collection."
URL = "https://www.teignbridge.gov.uk"
TEST_CASES = {
    "EX4 2JR": {"postcode": "EX4 2JR", "uprn": "010032968474"},
    "TQ12": {"postcode": "TQ12 4QQ", "uprn": "100040270498"},
}

COUNTRY = "uk"

ICON_MAP = {
    "Food waste container": "mdi:food-apple",
    "Black box": "mdi:recycle",
    "Green box": "mdi:glass-fragile",
    "Sack for paper": "mdi:newspaper",
    "Refuse - black bin": "mdi:trash-can",
}

ADDRESS_URL = "https://www.teignbridge.gov.uk/repositories/hidden-pages/address-finder"
BIN_URL = "https://www.teignbridge.gov.uk/repositories/hidden-pages/bin-finder"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit <a href='https://www.teignbridge.gov.uk/recycling-and-waste/forms/download-your-collection-calendar/'>Download your collection calendar</a>, enter your postcode and note the UPRN from the address dropdown.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Postcode (e.g. EX4 2JR)",
        "uprn": "Unique Property Reference Number",
    },
}


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode = postcode
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        # Fetch collection schedule
        r = requests.get(BIN_URL, params={"uprn": self._uprn}, impersonate="chrome124")
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        # Each collection date is in an h3 with class "binCollectionH3"
        headings = soup.find_all("h3", class_="binCollectionH3")

        for h3 in headings:
            # Extract date text (e.g. "7 April 2026")
            date_text = h3.get_text(strip=True)
            # Remove the day name descriptor at the end (e.g. "Tuesday")
            span = h3.find("span", class_="binDayDescriptor")
            if span:
                day_name = span.get_text(strip=True)
                date_text = date_text.replace(day_name, "").strip()

            try:
                collection_date = datetime.strptime(date_text, "%d %B %Y").date()
            except ValueError:
                continue

            # Find the following binInfoContainer
            container = h3.find_next_sibling("div", class_="binInfoContainer")
            if not container:
                continue

            # Extract bin types from img title attributes
            for line in container.find_all("div", class_="binInfoLine"):
                img = line.find("img")
                if img and img.get("title"):
                    bin_type = img["title"]
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type),
                        )
                    )

        return entries
