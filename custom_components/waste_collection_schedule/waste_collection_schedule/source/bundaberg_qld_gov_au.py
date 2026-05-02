from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Bundaberg Regional Council"
DESCRIPTION = "Source for Bundaberg Regional Council, QLD, Australia."
URL = "https://www.bundaberg.qld.gov.au"
TEST_CASES = {
    "10 Maynard Street Avenell Heights": {
        "street_number": "10",
        "street_name": "Maynard",
        "suburb": "AVENELL HEIGHTS",
    },
    "1 Bourbong Street Bundaberg East": {
        "street_number": "1",
        "street_name": "Bourbong",
        "suburb": "BUNDABERG EAST",
    },
}

API_URL = "https://microapps.bundaberg.qld.gov.au/bin_dates/livesearch.php"
# Guide date (Sunday) used to determine Week A vs B for fortnightly recycling
GUIDE_DATE = date(2020, 10, 18)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

# JavaScript Date.getDay() (0=Sun) → Python weekday() (0=Mon)
_JS_TO_PY_WEEKDAY = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}


def _week_code(d: date) -> str:
    return "A" if ((d - GUIDE_DATE).days // 7) % 2 == 0 else "B"


class Source:
    def __init__(self, street_number: str, street_name: str, suburb: str = ""):
        self._street_number = str(street_number)
        self._street_name = street_name
        self._suburb = suburb.upper()

    def fetch(self) -> list[Collection]:
        query = f"{self._street_number} {self._street_name}"

        r = requests.get(API_URL, params={"q": query}, headers=HEADERS)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        divs = soup.find_all("div")

        if not divs:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_number/street_name", query, []
            )

        # Pick the best match: exact suburb match if provided, otherwise first result
        match = None
        if self._suburb:
            for div in divs:
                if self._suburb in div["id"].upper():
                    match = div
                    break
            if match is None:
                suggestions = [d.get_text(strip=True) for d in divs]
                raise SourceArgumentNotFoundWithSuggestions(
                    "suburb", self._suburb, suggestions
                )
        else:
            match = divs[0]

        parts = match["id"].split(",")

        # Format: address,wasteDayCode,recDayCode,recWeekCode
        #      or address,wasteDayCode,recDayCode,recWeekCode,newWaste,newRec,newRecWeek
        # Post-2022 changeover: use new codes when present
        if len(parts) >= 7:
            waste_js = int(parts[4])
            rec_js = int(parts[5])
            rec_week = parts[6].strip()
        elif len(parts) >= 4:
            waste_js = int(parts[1])
            rec_js = int(parts[2])
            rec_week = parts[3].strip()
        else:
            raise ValueError(f"Unexpected response format: {match['id']}")

        waste_weekday = _JS_TO_PY_WEEKDAY[waste_js]
        rec_weekday = _JS_TO_PY_WEEKDAY[rec_js]

        today = date.today()
        collections: list[Collection] = []

        # General waste: weekly
        d = today + timedelta(days=(waste_weekday - today.weekday()) % 7)
        for _ in range(52):
            collections.append(
                Collection(d, "General Waste", ICON_MAP["General Waste"])
            )
            d += timedelta(weeks=1)

        # Recycling: fortnightly on rec_weekday in rec_week
        d = today + timedelta(days=(rec_weekday - today.weekday()) % 7)
        if _week_code(d) != rec_week:
            d += timedelta(weeks=1)
        for _ in range(26):
            collections.append(Collection(d, "Recycling", ICON_MAP["Recycling"]))
            d += timedelta(weeks=2)

        return collections
