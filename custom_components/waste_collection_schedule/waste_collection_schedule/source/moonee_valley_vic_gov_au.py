from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ArcGis import (
    epoch_ms_to_date,
    get_next_n_dates,
    most_recent_weekday,
)

TITLE = "City of Moonee Valley"
DESCRIPTION = "Source for City of Moonee Valley waste collection."
URL = "https://www.mvcc.vic.gov.au/"
TEST_CASES = {
    "309 Buckley St, Aberfeldie VIC 3040": {
        "property_location": "309 BUCKLEY STREET ABERFELDIE 3040"
    },
    "1/157 Military Road, Avondale Heights VIC 3034": {
        "property_location": "1/157 MILITARY ROAD AVONDALE HEIGHTS 3034"
    },
}
API_URL = "https://services8.arcgis.com/Qhxu8dzT7BHYuJZL/arcgis/rest/services/BinCollection_add/FeatureServer/0/query"
WEEKDAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class Source:
    def __init__(self, property_location: str):
        self.property_location = property_location

    def fetch(self) -> list[Collection]:
        # Format address for LIKE query (partial match)
        search_address = self.property_location.strip().replace("  ", " ")

        # Query for the address
        params = {
            "where": f"EZI_ADDRES LIKE '{search_address}%'",
            "outFields": "*",
            "f": "json",
            "returnGeometry": "false",
        }

        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        data = r.json()
        features = data.get("features")

        if not features:
            raise ValueError(f"Address not found: {self.property_location}")

        # Use the first matching address
        attributes = features[0]["attributes"]

        # Extract collection information from ArcGIS attributes
        # Field mapping based on API response:
        # - land_fill: General waste (weekly)
        # - recy_stdat: Recycling start date (fortnightly)
        # - green_st_d: Green waste/FOGO start date (fortnightly)
        # - collectday: Collection day name (e.g., "Tuesday")

        collection_day = attributes.get("collectday", "")

        # Convert ArcGIS timestamps (milliseconds since epoch) to dates
        recycling_timestamp = attributes.get("recy_stdat")
        fogo_timestamp = attributes.get("green_st_d")

        # Get the collection day for weekly waste
        next_collection_date = (
            most_recent_weekday(WEEKDAY_MAP[collection_day])
            if collection_day in WEEKDAY_MAP
            else date.today()
        )

        entries = []

        # General waste (weekly)
        waste_collection_dates = get_next_n_dates(
            next_collection_date, 52, timedelta(days=7)
        )
        entries.extend(
            [
                Collection(
                    date=collection_date, t="General Waste", icon="mdi:trash-can"
                )
                for collection_date in waste_collection_dates
            ]
        )

        # Recycling (fortnightly)
        if recycling_timestamp:
            recycling_date = epoch_ms_to_date(recycling_timestamp)
            recycling_dates = get_next_n_dates(recycling_date, 26, timedelta(days=14))
            entries.extend(
                [
                    Collection(date=collection_date, t="Recycling", icon="mdi:recycle")
                    for collection_date in recycling_dates
                ]
            )

        # FOGO/Green waste (fortnightly)
        if fogo_timestamp:
            fogo_date = epoch_ms_to_date(fogo_timestamp)
            fogo_dates = get_next_n_dates(fogo_date, 26, timedelta(days=14))
            entries.extend(
                [
                    Collection(date=collection_date, t="FOGO", icon="mdi:leaf")
                    for collection_date in fogo_dates
                ]
            )

        return entries
