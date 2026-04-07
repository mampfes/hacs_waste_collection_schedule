from datetime import date, timedelta

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Town of Victoria Park"
DESCRIPTION = "Source for www.victoriapark.wa.gov.au Waste Collection Services"
URL = "https://www.victoriapark.wa.gov.au"
TEST_CASES = {
    "Group 1 Monday": {"group": 1, "day": "Monday"},
    "Group 2 Friday": {"group": 2, "day": "Friday"},
    "Group 1 Wednesday": {"group": 1, "day": "Wednesday"},
}

COUNTRY = "au"

ICON_MAP = {
    "FOGO": "mdi:leaf",
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

# Reference date: Monday 30 June 2025 is a YELLOW week for Group 1 (FOGO + Recycling)
# and a RED week for Group 2 (FOGO + General Waste).
# Weeks alternate every 7 days from this reference.
REFERENCE_MONDAY = date(2025, 6, 30)

VALID_DAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the <a href='https://www.victoriapark.wa.gov.au/residents/waste-and-recycling/bins-and-collections.aspx'>Bins and Collections</a> page to find your collection group (1 or 2) and day.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "group": "Collection group (1 or 2) — check the calendar on the council website",
        "day": "Collection day (Monday to Friday)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "group": "Collection Group",
        "day": "Collection Day",
    },
}


class Source:
    def __init__(self, group: int, day: str):
        if group not in (1, 2):
            raise SourceArgumentNotFoundWithSuggestions("group", str(group), ["1", "2"])
        day_title = day.strip().title()
        if day_title not in VALID_DAYS:
            raise SourceArgumentNotFoundWithSuggestions(
                "day", day, list(VALID_DAYS.keys())
            )
        self._group = group
        self._day_offset = VALID_DAYS[day_title]

    def fetch(self) -> list[Collection]:
        today = date.today()
        entries = []

        # Find the next occurrence of the collection day on or after today minus 1 week
        start = today - timedelta(days=7)
        # Align to the collection day
        days_until = (self._day_offset - start.weekday()) % 7
        collection_date = start + timedelta(days=days_until)

        # Generate collections for ~52 weeks
        while collection_date < today + timedelta(days=365):
            # Determine if this is a yellow or red week for Group 1
            weeks_since_ref = (collection_date - REFERENCE_MONDAY).days // 7
            is_yellow_group1 = weeks_since_ref % 2 == 0

            if self._group == 1:
                is_yellow = is_yellow_group1
            else:
                is_yellow = not is_yellow_group1

            # FOGO goes out every week
            entries.append(
                Collection(date=collection_date, t="FOGO", icon=ICON_MAP["FOGO"])
            )

            # Yellow week = Recycling, Red week = General Waste
            if is_yellow:
                entries.append(
                    Collection(
                        date=collection_date,
                        t="Recycling",
                        icon=ICON_MAP["Recycling"],
                    )
                )
            else:
                entries.append(
                    Collection(
                        date=collection_date,
                        t="General Waste",
                        icon=ICON_MAP["General Waste"],
                    )
                )

            collection_date += timedelta(days=7)

        return entries
