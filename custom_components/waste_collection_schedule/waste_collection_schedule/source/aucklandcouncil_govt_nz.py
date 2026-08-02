import datetime
import re

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Auckland Council"
DESCRIPTION = "Source for Auckland Council."
URL = "https://www.aucklandcouncil.govt.nz"

TEST_CASES = {
    "429 Sea View Road": {"area_number": "12342453293"},  # Monday
    "8 Dickson Road": {"area_number": 12342306525},  # Thursday
    "with Food Scraps": {"area_number": 12341998652},
    "3 Andrew Road": {"area_number": "12345375455"},  # friday with foodscraps
}

API_URL = "https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{}.html"

MONTH = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

# icon class used on the page -> waste type reported by this source
COLLECTION_TYPES = {
    "rubbish": "rubbish",
    "recycle": "recycling",
    "food-waste": "food scraps",
}


def toDate(formattedDate: str, year: int | None = None) -> datetime.date:
    # formattedDate looks like "Wednesday, 8 October"
    parts = formattedDate.replace(",", "").split()
    # ["Wednesday", "8", "October"]
    day = int(parts[1])
    month = MONTH[parts[2]]
    if year is None:
        today = datetime.date.today()
        year = today.year
        # Handle December rollover into January
        if month == 1 and today.month == 12:
            year += 1
    return datetime.date(year, month, day)


def parse_page(html: str) -> list[Collection]:
    soup = BeautifulSoup(html, "html.parser")
    entries: list[Collection] = []

    # Find only the household collection section
    # Look for the card with "Household collection" title
    household_section = None
    schedule_cards = soup.find_all("div", class_="acpl-schedule-card")

    for card in schedule_cards:
        title_element = card.find("h4", class_="card-title")
        if title_element and "Household collection" in title_element.get_text():
            household_section = card
            break

    if not household_section:
        return entries

    # Look for collection information only within the household section
    collection_paragraphs = household_section.find_all("p", class_="mb-0 lead")

    for p in collection_paragraphs:
        # Look for icon elements
        icon = p.find("i", class_=lambda x: x and "acpl-icon" in x)
        if not icon:
            continue

        # Extract the collection type from icon classes
        collection_type = None
        for cls in icon.get("class") or []:
            if cls in COLLECTION_TYPES:
                collection_type = COLLECTION_TYPES[cls]
                break

        if not collection_type:
            continue

        # Look for date in bold text within the paragraph
        # (absent when this address has no such collection)
        date_bold = p.find("b")
        if not date_bold:
            continue

        date_text = date_bold.get_text(strip=True)

        # Extract date from text using regex
        date_match = re.search(r"([A-Za-z]+,\s+\d+\s+[A-Za-z]+)", date_text)
        if not date_match:
            continue

        try:
            collection_date = toDate(date_match.group(1))
        except (ValueError, KeyError):
            continue

        entries.append(Collection(collection_date, collection_type))

    return entries


class Source:
    def __init__(self, area_number: str | int):
        self._area_number = str(area_number)

    def fetch(self) -> list[Collection]:
        # The site's WAF answers HTTP 406 to plain requests/urllib clients, so
        # impersonate a real browser (TLS fingerprint included).
        session = requests.Session(impersonate="chrome")
        r = session.get(API_URL.format(self._area_number), timeout=30)
        r.raise_for_status()

        entries = parse_page(r.text)

        if not entries:
            # An unknown area number still returns HTTP 200, but with empty
            # collection dates. Fail loudly instead of reporting an empty
            # schedule as a successful fetch.
            raise SourceArgumentNotFound(
                "area_number",
                self._area_number,
                "no collection dates were found on the Auckland Council page, please check the area number.",
            )

        return entries
