import datetime
import re
import requests

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "South Holland District Council"
DESCRIPTION = "Source for South Holland District Council."
URL = "https://www.sholland.gov.uk/"

TEST_CASES = {
    "10002546801": {
        "uprn": 10002546801,
        "postcode": "PE11 2FR",
    },
    "PE12 7AR": {
        "uprn": "100030897036",
        "postcode": "PE12 7AR",
    },
}

ICON_MAP = {
    "refuse": "mdi:trash-can",
    "garden": "mdi:leaf",
    "recycling": "mdi:recycle",
}

API_URL = "https://www.sholland.gov.uk/apiserver/ajaxlibrary"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.sholland.gov.uk/mycollections",
}

class Source:
    def __init__(self, uprn: str | int, postcode: str):
        self._uprn = str(uprn)

    def fetch(self):
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "SouthHolland.Waste.getCollectionDaysAjax",
            "params": {
                "UPRN": self._uprn,
            },
        }

        with requests.Session() as session:
            response = session.post(API_URL, json=payload, headers=HEADERS)
            response.raise_for_status()
            data = response.json()

        if not data.get("result", {}).get("success"):
            raise Exception("API call unsuccessful")

        result = data["result"]
        entries: list[Collection] = []

        date_map = {
            "refuse": result.get("nextRefuseDateDisplay"),
            "recycling": result.get("nextRecyclingDateDisplay"),
            "garden": result.get("nextGardenDateDisplay"),
        }

        for bin_type, date_str in date_map.items():
            if not date_str:
                continue

            clean_date = re.sub(r"(\d)(st|nd|rd|th)", r"\1", date_str)
            parsed = datetime.datetime.strptime(clean_date, "%A %d %B")
            today = datetime.date.today()
            date = parsed.replace(year=today.year).date()

            if date < today:
                date = date.replace(year=today.year + 1)

            entries.append(
                Collection(
                    date=date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries
