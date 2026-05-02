import logging
import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "City of Manningham"
DESCRIPTION = "Source for City of Manningham, Victoria, Australia waste collection."
URL = "https://www.manningham.vic.gov.au"
TEST_CASES = {
    "10 Harold Street Bulleen": {"street_address": "10 Harold Street"},
    "Lower Templestowe Pre-School": {"street_address": "96-106 Swanston Street"},
    "9/114-116 James Street Templestowe": {"street_address": "9/114-116 James Street"},
    "488 Park Road Park Orchards": {"street_address": "488 Park Road"},
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)

SEARCH_URL = "https://mapping.manningham.vic.gov.au/weave/services/v1/index/search"
FEATURES_URL = (
    "https://mapping.manningham.vic.gov.au/weave/services/v1/feature/getFeaturesByIds"
)

DATE_FORMAT = "%d %b %Y"

WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Step 1: Resolve address to property ID
        response = session.get(
            SEARCH_URL,
            params={
                "start": "0",
                "limit": "10",
                "indexes": "index.ManCC_propertylayer",
                "type": "EXACT",
                "crs": "EPSG:28355",
                "query": self._street_address,
            },
            timeout=30,
        )
        response.raise_for_status()
        search_result = response.json()

        total = search_result.get("total", 0)
        if total == 0:
            raise SourceArgumentNotFound("street_address", self._street_address)
        if total > 1:
            suggestions = [_strip_html(r["display1"]) for r in search_result["results"]]
            raise SourceArgAmbiguousWithSuggestions(
                "street_address", self._street_address, suggestions
            )

        property_id = search_result["results"][0]["id"]
        _LOGGER.debug("Manningham property ID: %s", property_id)

        # Step 2: Fetch waste collection data for that property
        response = session.get(
            FEATURES_URL,
            params=[
                ("outCrs", "EPSG:28355"),
                ("datadefinition", "dd_ManCC_prop_layer_index"),
                ("datadefinition", "dd_ManCC_Property_WasteCollection"),
                ("entityId", "ManCC_prop_layer"),
                ("ids", property_id),
            ],
            timeout=30,
        )
        response.raise_for_status()
        feature_data = response.json()

        features = feature_data.get("features", [])
        if not features:
            raise SourceArgumentNotFound("street_address", self._street_address)

        waste_collection = features[0]["properties"].get(
            "dd_ManCC_Property_WasteCollection", []
        )
        if not waste_collection:
            raise SourceArgumentNotFound("street_address", self._street_address)

        data = waste_collection[0]
        today = datetime.now().date()
        end_date = today + timedelta(days=365)
        entries = []

        # Rubbish (red lid) — fortnightly; API returns next collection date
        rubbish_date_str = data.get("ManCC_Collection_Day")
        if rubbish_date_str:
            date = datetime.strptime(rubbish_date_str, DATE_FORMAT).date()
            while date <= end_date:
                entries.append(
                    Collection(date=date, t="Rubbish", icon=ICON_MAP["Rubbish"])
                )
                date += timedelta(days=14)

        # Recycling (yellow lid) — fortnightly; API returns next collection date
        recycling_date_str = data.get("ManCC_Recycling_Day")
        if recycling_date_str:
            date = datetime.strptime(recycling_date_str, DATE_FORMAT).date()
            while date <= end_date:
                entries.append(
                    Collection(date=date, t="Recycling", icon=ICON_MAP["Recycling"])
                )
                date += timedelta(days=14)

        # Garden/FOGO (green lid) — weekly; API returns day-of-week name
        garden_day_str = data.get("ManCC_Garden_Waste_Day")
        if garden_day_str:
            target_weekday = WEEKDAY_MAP.get(garden_day_str)
            if target_weekday is not None:
                days_ahead = (target_weekday - today.weekday()) % 7
                date = today + timedelta(days=days_ahead)
                while date <= end_date:
                    entries.append(
                        Collection(
                            date=date, t="Garden Waste", icon=ICON_MAP["Garden Waste"]
                        )
                    )
                    date += timedelta(days=7)

        return entries
