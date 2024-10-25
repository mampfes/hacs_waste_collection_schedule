# Credit where it's due:
# This is predominantly a refactoring of the Bristol City Council script from the UKBinCollectionData repo
# https://github.com/robbrad/UKBinCollectionData


import json
from datetime import datetime, timedelta, timezone

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Northamptonshire council"
DESCRIPTION = "Source for North Northamptonshire council."
URL = "https://www.northnorthants.gov.uk/"
TEST_CASES = {
    "100030987513": {"uprn": 100030987513},
    "100030987514": {"uprn": 100030987514},
    "10093005361": {"uprn": "10093005361"},
    "Castle Farm House Main Street Rockingham North Northamptonshire LE16 8TG": {
        "uprn": "100030993903"
    },
}


ICON_MAP = {
    "General": "mdi:trash-can",
    "Food": "mdi:food",
    "Garden": "mdi:recycle",
    "Recycling": "mdi:package-variant",
}


API_URL = "https://www.northnorthants.gov.uk/bins/bin-collection-day"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        entries = []
        today = (
            int(
                datetime.now(timezone.utc)
                .replace(hour=23, minute=59, second=59)
                .timestamp()
            )
            * 1000
        )
        dateforurl = datetime.now().strftime("%Y-%m-%d")
        dateforurl2 = (datetime.now() + timedelta(days=42)).strftime("%Y-%m-%d")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)",
        }

        # Get variables for workings
        response = requests.get(
            f"https://cms.northnorthants.gov.uk/bin-collection-search/calendarevents/{self._uprn}/{dateforurl}/{dateforurl2}",
            headers=headers,
        )
        if response.status_code != 200:
            raise ValueError("No bin data found for provided UPRN..")

        json_response = json.loads(response.text)

        output_json = [
            x
            for x in json_response
            if int("".join(filter(str.isdigit, x["start"]))) >= today
        ]

        # output_json.sort(key=myFunc)

        i = 0
        while i < len(output_json):
            sov = output_json[i]["title"].lower()
            if "recycling" in sov:
                bin_type = "Recycling"
            elif "garden" in sov:
                bin_type = "Garden"
            elif "refuse" in sov:
                bin_type = "General"
            elif "food" in sov:
                bin_type = "Food"
            else:
                bin_type = sov
            dateofbin = int("".join(filter(str.isdigit, output_json[i]["start"])))
            day = datetime.fromtimestamp(dateofbin / 1000, timezone.utc).date()
            collection_data = Collection(
                t=bin_type,
                date=day,
                icon=ICON_MAP.get(bin_type),
            )
            entries.append(collection_data)
            i += 1

        return sorted(entries, key=lambda x: x.date)
