import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "eThekwini Municipality"
DESCRIPTION = "Source for eThekwini Municipality / Durban refuse collection schedules."
URL = "https://www.durban.gov.za/page/refuse-collection-schedules"
COUNTRY = "za"
SOURCE_CODEOWNERS = ["@robtesch"]

ICS_BASE = (
    "https://raw.githubusercontent.com/robtesch/hacs_waste_collection_schedule/"
    "refs/heads/data/durban-gov-za"
)
INDEX_URL = f"{ICS_BASE}/index.json"
ODD_RECYCLING_SUMMARY = "Recycling (odd ISO weeks)"

TEST_CASES = {
    "Outer West Hillcrest": {
        "region": "outer_west",
        "area": "hillcrest",
        "recycling_in_even_week": True,
    },
    "Outer West Drummond": {
        "region": "outer_west",
        "area": "drummond_montesseel",
        "recycling_in_even_week": True,
    },
    "North Umdloti": {
        "region": "north",
        "area": "umdloti",
        "recycling_in_even_week": True,
    },
    "North Central Overport": {
        "region": "north_central",
        "area": "overport_drive",
        "recycling_in_even_week": True,
    },
    "South Central Montclair": {
        "region": "south_central",
        "area": "montclair_w3",
        "recycling_in_even_week": True,
    },
    "Inner West Westville": {
        "region": "inner_west",
        "area": "westville",
        "recycling_in_even_week": True,
    },
    "South Umlazi": {
        "region": "south",
        "area": "umlazi_section",
        "recycling_in_even_week": True,
    },
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit the <a href='https://www.durban.gov.za/page/refuse-collection-schedules'>"
        "refuse collection schedules</a> page, open your region's DOCX file, and find "
        "your suburb or area under the weekday column. Use the matching "
        "<code>region</code> and <code>area</code> values shown in the documentation."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "region": (
            "Regional office area, e.g. outer_west, north, south_central, "
            "north_central, inner_west, or south"
        ),
        "area": (
            "Suburb or collection area slug from the regional schedule DOCX, "
            "e.g. hillcrest or drummond_montesseel"
        ),
        "recycling_in_even_week": (
            "Set to True if orange-bag recycling is collected on even ISO week "
            "numbers, False if collected on odd ISO week numbers. Check your last "
            "recycling collection date to determine this."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "region": "Region",
        "area": "Collection Area",
        "recycling_in_even_week": "Recycling collected on even ISO weeks",
    },
}


def _load_index() -> dict:
    response = requests.get(INDEX_URL, timeout=30)
    response.raise_for_status()
    return response.json()


class Source:
    def __init__(
        self,
        region: str,
        area: str,
        recycling_in_even_week: bool = True,
    ):
        region_key = region.strip().lower()
        area_key = area.strip().lower()
        index = _load_index()
        regions = index.get("regions", {})

        if region_key not in regions:
            raise SourceArgumentNotFoundWithSuggestions(
                "region",
                region,
                sorted(regions.keys()),
            )

        region_areas = regions[region_key].get("areas", {})
        if area_key not in region_areas:
            raise SourceArgumentNotFoundWithSuggestions(
                "area",
                area,
                sorted(region_areas.keys()),
            )

        self._region = region_key
        self._area = area_key
        self._recycling_in_even_week = recycling_in_even_week
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        calendar_url = f"{ICS_BASE}/calendars/{self._region}/{self._area}.ics"
        response = requests.get(calendar_url, timeout=30)
        response.raise_for_status()

        entries: list[Collection] = []
        for collection_date, summary in self._ics.convert(response.text):
            if summary == ODD_RECYCLING_SUMMARY:
                if self._recycling_in_even_week:
                    continue
                summary = "Recycling"
            elif summary == "Recycling" and not self._recycling_in_even_week:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=summary,
                    icon=ICON_MAP.get(summary),
                )
            )
        return entries
