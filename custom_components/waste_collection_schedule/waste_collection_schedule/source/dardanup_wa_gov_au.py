import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Shire of Dardanup"
DESCRIPTION = "Source for Shire of Dardanup (WA) waste collection."
URL = "https://www.dardanup.wa.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "Hale Street (Area 1, Tuesday)": {
        "street": "Hale Street",
        "recycling_in_even_week": True,
    },
    "Burekup": {
        "street": "Burekup",
        "recycling_in_even_week": True,
    },
    "Dardanup West via collection_day": {
        "collection_day": "Monday",
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
        "Visit https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/"
        "find-your-bin-day.aspx and find your street in the list to determine "
        "your collection day. Enter your street name (without house number) as "
        "the 'street' argument, or enter the day directly as 'collection_day' "
        "(for Dardanup West / Ferguson Valley residents). "
        "For recycling_in_even_week: check your last recycling collection date "
        "and see if its ISO week number (https://whatweekisit.org/) was even "
        "(True) or odd (False)."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": (
            "Your street name without a house number, e.g. 'Hale Street' or "
            "'Flinders Street'. Used to look up your collection day automatically."
        ),
        "collection_day": (
            "Your collection day as a string: 'Monday', 'Tuesday', 'Wednesday', "
            "'Thursday', or 'Friday'. Use this instead of 'street' for Dardanup "
            "West (Monday) and Ferguson Valley residents, or if street lookup fails."
        ),
        "recycling_in_even_week": (
            "Set to True if your recycling bin is collected on even ISO week "
            "numbers, False if on odd ISO week numbers. Check your last recycling "
            "collection date to determine this."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street Name",
        "collection_day": "Collection Day (override)",
        "recycling_in_even_week": "Recycling collected on even ISO weeks",
    },
}

COLLECTION_URL = (
    "https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/"
    "find-your-bin-day.aspx"
)

DAY_NAME_TO_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}


def _next_weekday(ref: date, weekday: int) -> date:
    days_ahead = weekday - ref.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return ref + timedelta(days=days_ahead)


def _clean_street(raw: str) -> str:
    """Strip range qualifiers like '(numbers 4-64)' or '(odd numbers 2-46)'."""
    return re.sub(r"\s*\([^)]+\)", "", raw).strip()


class Source:
    def __init__(
        self,
        street: str | None = None,
        collection_day: str | None = None,
        recycling_in_even_week: bool = True,
    ):
        if not street and not collection_day:
            raise SourceArgumentNotFound(
                "street",
                "Provide either 'street' (your street name) or 'collection_day' "
                "('Monday'–'Friday').",
            )
        self._street = street.strip() if street else None
        self._collection_day = (
            collection_day.strip().lower() if collection_day else None
        )
        self._recycling_in_even_week = recycling_in_even_week

    def fetch(self) -> list[Collection]:
        if self._collection_day:
            if self._collection_day not in DAY_NAME_TO_WEEKDAY:
                raise SourceArgumentNotFound(
                    "collection_day",
                    f"'{self._collection_day}' is not a valid day. "
                    f"Use one of: {', '.join(DAY_NAME_TO_WEEKDAY)}.",
                )
            weekday = DAY_NAME_TO_WEEKDAY[self._collection_day]
        else:
            weekday = self._lookup_street_day()

        return self._build_entries(weekday)

    def _lookup_street_day(self) -> int:
        r = requests.get(COLLECTION_URL, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        street_lower = self._street.lower()
        all_streets: list[str] = []
        found_weekday: int | None = None

        for accordion in soup.select("div.accordion div.accordion"):
            current_day: int | None = None

            for child in accordion.children:
                if not hasattr(child, "name"):
                    continue

                if child.name == "h2":
                    heading = child.get_text(strip=True).lower()
                    current_day = None
                    for day_name, wd in DAY_NAME_TO_WEEKDAY.items():
                        if heading.startswith(day_name):
                            current_day = wd
                            break

                elif child.name == "p":
                    para_text = child.get_text(strip=True)
                    if not para_text:
                        continue

                    thursday_match = re.match(
                        r"^(.+?)\s*[-–]\s*(monday|tuesday|wednesday|thursday|friday)",
                        para_text,
                        re.IGNORECASE,
                    )
                    if thursday_match:
                        suburb = thursday_match.group(1).strip().lower()
                        day_str = thursday_match.group(2).strip().lower()
                        all_streets.append(thursday_match.group(1).strip())
                        if suburb in street_lower or street_lower in suburb:
                            found_weekday = DAY_NAME_TO_WEEKDAY.get(day_str)
                        continue

                    if current_day is not None:
                        for raw in para_text.split(","):
                            cleaned = _clean_street(raw)
                            if cleaned:
                                all_streets.append(cleaned)
                                if cleaned.lower() == street_lower:
                                    found_weekday = current_day
                                elif street_lower in cleaned.lower():
                                    found_weekday = current_day

        if found_weekday is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, sorted(set(all_streets))
            )

        return found_weekday

    def _build_entries(self, weekday: int) -> list[Collection]:
        entries: list[Collection] = []
        today = date.today()
        first_day = _next_weekday(today, weekday)

        for week in range(26):
            d = first_day + timedelta(weeks=week)
            iso_week = d.isocalendar()[1]
            even_week = iso_week % 2 == 0

            entries.append(Collection(date=d, t="FOGO", icon=ICON_MAP["FOGO"]))

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
