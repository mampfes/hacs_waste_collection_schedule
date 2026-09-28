"""Regular collection days published by the City of Hanahan, South Carolina."""

from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Hanahan, SC"
DESCRIPTION = "Regular curbside collection schedule for the City of Hanahan."
URL = (
    "https://www.cityofhanahan.com/publicworks/page/household-trash-collection-schedule"
)
COUNTRY = "us"
SOURCE_CODEOWNERS = ["@dmkjr"]

TEST_CASES = {
    "Hanahan Proper": {"area": "Hanahan Proper"},
    "Tanner Plantation": {"area": "Tanner Plantation"},
    "Eagle Landing": {"area": "Eagle Landing"},
    "Otranto": {"area": "Otranto"},
    "Spring Valley Mobile Home Park": {"area": "Spring Valley Mobile Home Park"},
    "Tuesday household waste area": {"area": "Tuesday household waste area"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "area": "Collection area from the city's schedule. Use the Tuesday household waste area only for the streets and street segments listed there.",
    },
}
PARAM_TRANSLATIONS = {"en": {"area": "Collection area"}}

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}
WEEKS_AHEAD = 12

# Area names are selected by the user because the city publishes no
# authoritative address-to-route lookup for all five collection types.
AREA_GROUPS = {
    "hanahan proper": "proper",
    "tanner plantation": "tanner",
    "eagle landing": "eagle",
    "otranto": "otranto",
    "spring valley mobile home park": "friday_exception",
    "gold cup springs": "friday_exception",
    "north rhett": "friday_exception",
    "lakeview subdivision": "friday_exception",
    "tuesday household waste area": "tuesday_exception",
}

WASTE_TYPES = {
    "Brown Trash": Icons.BULKY,
    "Yard Debris": Icons.GARDEN,
    "Metals": Icons.METAL,
    "Electronic Scrap": Icons.ELECTRONICS,
    "Household Waste": Icons.GENERAL_WASTE,
}


def _schedule(html: str) -> dict[str, list[tuple[str, str]]]:
    """Read the weekday lists from the city's live schedule page."""
    body = BeautifulSoup(html, "html.parser").select_one(
        ".node-page__body-image-wrapper .field--name-body"
    )
    if body is None:
        raise ValueError("Hanahan schedule content was not found")

    schedule: dict[str, list[tuple[str, str]]] = {}
    day = None
    for element in body.find_all(["p", "ul"], recursive=False):
        if element.name == "p":
            heading = element.get_text(" ", strip=True).rstrip(":").lower()
            day = heading if heading in WEEKDAYS else None
        elif day is not None:
            entries = []
            for item in element.find_all("li", recursive=False):
                line = item.get_text(" ", strip=True).replace("–", "-")
                kind, separator, areas = line.partition("-")
                if separator and kind.strip() in WASTE_TYPES:
                    entries.append((kind.strip(), areas.strip()))
            schedule[day] = entries
            day = None

    if set(schedule) != set(WEEKDAYS) or any(not rows for rows in schedule.values()):
        raise ValueError("Hanahan schedule weekday lists are incomplete")
    return schedule


def _day_for(schedule: dict[str, list[tuple[str, str]]], kind: str, area: str) -> int:
    for weekday, rows in schedule.items():
        if any(
            row_kind == kind and area.lower() in listed.lower()
            for row_kind, listed in rows
        ):
            return WEEKDAYS[weekday]
    raise ValueError(f"Hanahan schedule no longer lists {kind} for {area}")


class Source:
    def __init__(self, area: str):
        self._area = area.strip()
        self._group = AREA_GROUPS.get(self._area.casefold())
        if self._group is None:
            raise SourceArgumentNotFound("area", area)

    def fetch(self) -> list[Collection]:
        response = requests.get(URL, timeout=20)
        response.raise_for_status()
        schedule = _schedule(response.text)

        yard_area = (
            "Tanner Plantation"
            if self._group == "tanner"
            else self._area
            if self._group in ("eagle", "otranto")
            else "Hanahan Proper"
        )
        household_area = {
            "proper": "Hanahan Proper",
            "tanner": "Tanner Plantation",
            "eagle": "Eagle Landing",
            "otranto": "Otranto",
            "friday_exception": self._area,
            "tuesday_exception": "Loftis Rd",
        }[self._group]

        days = {
            "Brown Trash": _day_for(schedule, "Brown Trash", "Citywide"),
            "Yard Debris": _day_for(schedule, "Yard Debris", yard_area),
            "Metals": _day_for(schedule, "Metals", "Citywide"),
            "Electronic Scrap": _day_for(schedule, "Electronic Scrap", "Citywide"),
            "Household Waste": _day_for(schedule, "Household Waste", household_area),
        }
        today = date.today()
        collections = []
        for kind, weekday in days.items():
            first = today + timedelta(days=(weekday - today.weekday()) % 7)
            collections.extend(
                Collection(
                    date=first + timedelta(weeks=week),
                    t=kind,
                    icon=WASTE_TYPES[kind],
                )
                for week in range(WEEKS_AHEAD)
            )
        return sorted(collections, key=lambda collection: collection.date)
