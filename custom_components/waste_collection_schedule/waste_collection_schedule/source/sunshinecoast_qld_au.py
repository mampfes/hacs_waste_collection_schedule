from datetime import datetime, timedelta
from waste_collection_schedule import Collection

import requests

TITLE = "Sunshine Coast Queensland (QLD)"
DESCRIPTION = "Source script for Sunshine Coast Queensland (QLD)."
URL = "https://www.sunshinecoast.qld.gov.au/living-and-community/waste-and-recycling/bin-collection-days"
TEST_CASES = {
    "Hospital Rd": {"street_name": "hospital rd"},
    "Great Keppel Way": {"street_name": "great keppel way"},
}

API_URL = "https://www.sunshinecoast.qld.gov.au/__server__/api/v1"
ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycle": "mdi:recycle",
    "Organic": "mdi:leaf",
}

"""
    sunshine coast uses a week setting
    week 1 and week 2 starting from a set date
"""
START_DATE=datetime(2021, 12, 11)
def get_week_type(t):
    """Determine the collection week type (1 or 2) based on the reference date."""
    week_diff = (t - START_DATE).days // 7
    return "1" if week_diff % 2 == 0 else "2"


"""" RETURNED VALUES

    JSON DATA:
        [{"id":"<id>","street":"<Street Name>","locality":"<Town>","day":"Wednesday","week":"1","instructions":""}]
"""
def get_next_collection_dates(collection_schedules):
    """Find the next collection dates for all types (general, recycling, garden)."""
    today = datetime.today()
    today_week_type = get_week_type(today)
    today_day = today.strftime("%A")

    # Initialize the collection dates to be empty
    collection_dates = {
        "general": None,
        "recycling": None,
        "garden": None
    }

    # Loop through each schedule to check for collections
    collection_day = str(collection_schedules.get("day", "")).strip()
    collection_week = str(collection_schedules.get("week", "")).strip()

    # Check if today is the collection day
    if today_day == collection_day:
        collection_dates["general"] = today.strftime("%Y-%m-%d")
        if today_week_type == collection_week:
            collection_dates["recycling"] = today.strftime("%Y-%m-%d")
        else:
            collection_dates["garden"] = today.strftime("%Y-%m-%d")

    # Look ahead for the next collection day (if today is not the collection day)
    for i in range(0, 14):  # Start from today
        future_date = today + timedelta(days=i)
        future_week_type = get_week_type(future_date)
        future_day = future_date.strftime("%A")

        if future_day == collection_day:
            if collection_dates["general"] is None:
                collection_dates["general"] = future_date.strftime("%Y-%m-%d")
            if future_week_type == collection_week and collection_dates["recycling"] is None:
                collection_dates["recycling"] = future_date.strftime("%Y-%m-%d")
            elif future_week_type != collection_week and collection_dates["garden"] is None:
                collection_dates["garden"] = future_date.strftime("%Y-%m-%d")

    # Return collection dates, ensuring no None values for each type
    return {key: value for key, value in collection_dates.items() if value is not None}

class Source:
    def __init__(self, street_name ):  # argX correspond to the args dict in the source configuration
        self.street_name = street_name

    def fetch(self):

        r=requests.get(f"{API_URL}/streets/{self.street_name}")

        if len(r.json()) == 0:
            return []

        data = r.json()[0]

        entries = []  # List that holds collection schedule

        # Parse data
        parsed_data = get_next_collection_dates(data)

        entries.append(
            Collection(
                date = datetime.strptime(parsed_data["general"], "%Y-%m-%d").date(),  # Collection date
                t = "Garbage",  # Collection type
                icon = ICON_MAP["Garbage"],  # Collection icon
            )
        )

        entries.append(
            Collection(
                date = datetime.strptime(parsed_data["recycling"], "%Y-%m-%d").date(),  # Collection date
                t = "Recycle",  # Collection type
                icon = ICON_MAP["Recycle"],  # Collection icon
            )
        )

        entries.append(
            Collection(
                date = datetime.strptime(parsed_data["garden"], "%Y-%m-%d").date(),  # Collection date
                t = "Organic",  # Collection type
                icon = ICON_MAP["Organic"],  # Collection icon
            )
        )

        return entries