from datetime import datetime
import json
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Denbighshire County Council"
DESCRIPTION = "Source for Denbighshire County Council."
URL = "https://www.denbighshire.gov.uk/"
TEST_CASES = {
    "10003928409": {"uprn": "10003928409"},
    "100100183412": {"uprn": "100100183412"},
}

ICON_MAP = {
    "garden": "mdi:leaf",
    "food": "mdi:food",
    "household": "mdi:trash-can",
    "recycle": "mdi:recycle",
}

API_URL = "https://www.denbighshire.gov.uk/api/Custom/RefuseApi/GetCollectionDates"

class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        h = { "referer": "https://www.denbighshire.gov.uk/en/bins-and-recycling/bin-collections.aspx" }
        r = requests.get(API_URL, params={"uprn": self._uprn}, headers=h)
        r.raise_for_status()
        
        message = json.loads(r.json()['message'])
        entries = []

        for type in ['Household', 'Recycling', 'Food']:
            date_str = message[f"{type}Date"]
            date = datetime.strptime(date_str, "%A %d/%m/%Y").date()

            icon = ICON_MAP.get(type.lower())
            entries.append(Collection(date=date, t=type.lower(), icon=icon))

            # garden waste is collected on the same day as household, but isn't returned in the API
            if type == "Household":
                also = "Garden"
                icon = ICON_MAP.get(also.lower())
                entries.append(Collection(date=date, t=also.lower(), icon=icon))

        return entries
