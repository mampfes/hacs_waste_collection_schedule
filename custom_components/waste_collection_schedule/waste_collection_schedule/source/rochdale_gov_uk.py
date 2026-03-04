import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Rochdale Borough Council"
DESCRIPTION = "Source for Rochdale Borough Council."
URL = "https://www.rochdale.gov.uk/"
TEST_CASES = {
    "144 Claybank Street, Heywood": {"postcode": "OL104TJ", "uprn": 10094359340},
    "OL12 7TX 23030658": {"postcode": "OL12 7TX", "uprn": "23030658"},
}

ICON_MAP = {
    "Food": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Rubbish": "mdi:trash-can",
    "Cans": "mdi:bottle-soda",
}

API_URL = "https://rochdale-self.achieveservice.com/service/api/service/calendars"


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode.replace(" ", "").upper()
        self._uprn: str | int = uprn

    def fetch(self) -> list[Collection]:
        # Prepare request payload
        params = {
            "address": self._uprn,
            "postcode": self._postcode,
        }

        # Make API request
        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        # Parse JSON response
        data = r.json()
        if "collections" not in data:
            raise Exception("Invalid response: 'collections' key not found")

        # Process collection data
        entries = []
        for item in data["collections"]:
            try:
                date = parse(item["collectionDate"], dayfirst=True).date()
                coll_type = item["collectionType"]
                icon = ICON_MAP.get(coll_type.split()[0], "mdi:trash-can")
                entries.append(Collection(date=date, t=coll_type, icon=icon))
            except (KeyError, ValueError) as e:
                raise Exception(f"Error processing collection data: {e}")

        return entries
