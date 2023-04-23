from datetime import date
import re
from dateutil.parser import parse as date_parse
from waste_collection_schedule import Collection
import requests

TITLE = "Fareham Council"
DESCRIPTION = "Source for fareham.gov.uk"
URL = "https://www.fareham.gov.uk"
TEST_CASES = {
    "HUNTS_POND_ROAD": {"road_name": "Hunts pond road", "postcode": "PO14 4PL"},
    "CHRUCH_ROAD": {"road_name": "Church road", "postcode": "SO31 6LW"},
    "BRIDGE_ROAD": {"road_name": "Bridge road", "postcode": "SO31 7GD"},
}

API_URL = "https://www.fareham.gov.uk/internetlookups/search_data.aspx"
ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}


class Source:
    def __init__(self, road_name, postcode):
        self._road_name = road_name
        self._postcode = postcode

    def fetch(self):
        entries = []
        params = {
            "type": "JSON",
            "list": "DomesticBinCollections",
            "Road": self._road_name,
            "Postcode": self._postcode,
        }
        headers = {
            "user-agent": "Mozilla/5.0",
        }
        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        # Some queries (Bridge Road test case) return duplicate results, we only want to process
        # unique bin collection dates
        unique_entries = set(
            map(lambda row: row["DomesticBinDay"], response.json()["data"]["rows"])
        )

        for entry in unique_entries:
            for collection in self.extract_collections(entry):
                entries.append(collection)

        return entries

    def extract_collections(self, string):
        """
        Given a string in the forms:
          "Thursday - Collections are 20/04/2023 (Refuse) and 27/04/2023 (Recycling)"
          "Thursday - Collections are today (Refuse) and 27/04/2023 (Recycling)"

        It will extract the dates and waste_types to create Collection objects
        """
        collections = []
        for match in re.finditer(
            r"(?P<date>\d{1,2}\/\d{1,2}\/\d{4}|today) \((?P<waste_type>\w+)\)", string
        ):
            if match.group("date") == "today":
                collection_date = date.today()
            else:
                collection_date = date_parse(match.group("date"), dayfirst=True).date()

            waste_type = match.group("waste_type")
            collections.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP[waste_type],
                )
            )
        return collections
