from datetime import timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ArcGis import (
    epoch_ms_to_date,
    get_next_n_dates,
    most_recent_weekday,
)

TITLE = "City of Darebin"
DESCRIPTION = "Source for City of Darebin waste collection."
URL = "https://www.darebin.vic.gov.au/"
TEST_CASES = {
    "266 Gower Street PRESTON 3072": {
        "property_location": "266 Gower Street PRESTON 3072"
    },
    "23 EDWARDES STREET RESERVOIR 3073": {
        "property_location": "23 EDWARDES STREET RESERVOIR 3073"
    },
}
API_URL = "https://services-ap1.arcgis.com/1WJBRkF3v1EEG5gz/arcgis/rest/services/Waste_Collection_Date3/FeatureServer/0/query"
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
        params = {
            "where": f"EZI_ADDRESS LIKE '{self.property_location}%'",
            "outFields": "EZI_ADDRESS,OBJECTID",
            "f": "json",
        }
        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        data = r.json()
        features = data.get("features")
        attributes = features[0]["attributes"]
        object_id = attributes["OBJECTID"]

        params = {
            "f": "json",
            "objectIds": object_id,
            "outFields": "Collection_Day,Condition,EZI_ADDRESS,Green_Collection,Recycle_Collection,Street_Sweeping",
        }

        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        data = r.json()
        features = data.get("features")
        attributes = features[0]["attributes"]

        collection_day = attributes["Collection_Day"]

        next_collection_date = most_recent_weekday(WEEKDAY_MAP[collection_day])

        green_collection = epoch_ms_to_date(attributes["Green_Collection"])
        recycle_collection = epoch_ms_to_date(attributes["Recycle_Collection"])
        street_sweeping = epoch_ms_to_date(attributes["Street_Sweeping"])

        green_collection_dates = get_next_n_dates(
            green_collection, 26, timedelta(days=14)
        )
        recycle_collection_dates = get_next_n_dates(
            recycle_collection, 26, timedelta(days=14)
        )
        waste_collection_dates = get_next_n_dates(
            next_collection_date, 52, timedelta(days=7)
        )
        street_sweeping_dates = get_next_n_dates(
            street_sweeping, 1, timedelta(weeks=6)
        )

        entries = []

        entries.extend(
            [
                Collection(date=collection_date, t="Green Waste", icon="mdi:leaf")
                for collection_date in green_collection_dates
            ]
        )
        entries.extend(
            [
                Collection(date=collection_date, t="Recycling", icon="mdi:recycle")
                for collection_date in recycle_collection_dates
            ]
        )
        entries.extend(
            [
                Collection(date=collection_day, t="Rubbish", icon="mdi:trash-can")
                for collection_day in waste_collection_dates
            ]
        )
        entries.extend(
            [
                Collection(date=collection_day, t="Street Sweeping", icon="mdi:broom")
                for collection_day in street_sweeping_dates
            ]
        )
        return entries
