from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Shire of Harvey"
DESCRIPTION = "Source for Shire of Harvey (WA) waste collection."
URL = "https://www.harvey.wa.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Australind (south of Paris Road)": {
        "suburb": "Australind (south of Paris Road)",
        "recycling_in_even_week": True,
    },
    "Harvey (east of railway)": {
        "suburb": "Harvey (east of railway to Highway including Weir Road)",
        "recycling_in_even_week": False,
    },
    "Roelands": {
        "suburb": "Roelands including Raymond Road",
        "recycling_in_even_week": True,
    },
}

ICON_MAP = {
    "FOGO": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "General Waste": "mdi:trash-can",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://www.harvey.wa.gov.au/services/rubbish-and-waste-services/"
        "bin-collection-residential-and-commercial and find your suburb in the "
        "collection day list. Use the exact text shown. "
        "For recycling_in_even_week: check your last recycling collection date and "
        "see if its ISO week number (https://whatweekisit.org/) was even (True) or odd (False)."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "suburb": (
            "Your suburb/area as listed on the Shire of Harvey bin collection page, "
            "e.g. 'Yarloop' or 'Australind (south of Paris Road)'."
        ),
        "recycling_in_even_week": (
            "Set to True if your recycling bin is collected on even ISO week numbers, "
            "False if collected on odd ISO week numbers. Check your last recycling "
            "collection date to determine this."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "suburb": "Suburb / Collection Area",
        "recycling_in_even_week": "Recycling collected on even ISO weeks",
    },
}

COLLECTION_URL = (
    "https://www.harvey.wa.gov.au/services/rubbish-and-waste-services/"
    "bin-collection-residential-and-commercial"
)

DAY_NAME_TO_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _next_weekday(ref: date, weekday: int) -> date:
    """Return the next occurrence of *weekday* (0=Mon...6=Sun) on or after *ref*."""
    days_ahead = weekday - ref.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return ref + timedelta(days=days_ahead)


class Source:
    def __init__(self, suburb: str, recycling_in_even_week: bool = True):
        self._suburb = suburb.strip()
        self._recycling_in_even_week = recycling_in_even_week

    def fetch(self) -> list[Collection]:
        r = requests.get(COLLECTION_URL, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # The accordion items each contain a day heading and a <ul> of suburb names
        collection_day: int | None = None
        all_suburbs: list[str] = []

        for item in soup.select(".accordion-item"):
            button = item.select_one(".accordion-button")
            if button is None:
                continue
            heading = button.get_text(strip=True).lower()
            day_weekday: int | None = None
            for day_name, weekday in DAY_NAME_TO_WEEKDAY.items():
                if heading.startswith(day_name):
                    day_weekday = weekday
                    break
            if day_weekday is None:
                continue

            suburbs = [li.get_text(strip=True) for li in item.select("li")]
            all_suburbs.extend(suburbs)

            for s in suburbs:
                if s.lower() == self._suburb.lower():
                    collection_day = day_weekday
                    break

            if collection_day is not None:
                break

        if collection_day is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "suburb", self._suburb, all_suburbs
            )

        entries: list[Collection] = []
        today = date.today()
        # Generate ~26 weeks of collection entries
        first_day = _next_weekday(today, collection_day)

        for week in range(26):
            d = first_day + timedelta(weeks=week)
            iso_week = d.isocalendar()[1]
            even_week = iso_week % 2 == 0

            # FOGO collected every week
            entries.append(Collection(date=d, t="FOGO", icon=ICON_MAP["FOGO"]))

            # Recycling and General Waste alternate fortnightly
            if even_week == self._recycling_in_even_week:
                entries.append(
                    Collection(date=d, t="Recycling", icon=ICON_MAP["Recycling"])
                )
            else:
                entries.append(
                    Collection(
                        date=d, t="General Waste", icon=ICON_MAP["General Waste"]
                    )
                )

        return entries
