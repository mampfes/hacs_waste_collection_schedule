import datetime
import json

import requests
from waste_collection_schedule import Collection

TITLE = "South Gloucestershire Council"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for southglos.gov.uk"  # Describe your source
URL = "https://southglos.gov.uk"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Test_001": {"uprn": "643346"},
    "Test_002": {"uprn": "641084"}
}

ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "BLACK BIN": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
    "FOOD BIN": "mdi:food"
}


class Source:
    def __init__(self, uprn: str):  # argX correspond to the args dict in the source configuration
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()
        r = session.get(
            f"https://webapps.southglos.gov.uk/Webservices/SGC.RefuseCollectionService/RefuseCollectionService.svc"
            f"/getCollections/{self._uprn}")
        r.raise_for_status()
        output = r.text.strip('[]')
        output = json.loads(output)
        # Recycling and food are fields starting with C and R
        recycling_and_food_bin_dates = [output['C1'], output['C2'], output['C3'], output['R1'], output['R2'], output['R3']]
        # Black bin dates are fields starting R
        black_bin_dates = [output['R1'], output['R2'], output['R3']]
        # Garden bin dates are fields starting G
        garden_bin_dates = [output['G1'], output['G2'], output['G3']]
        entries = []  # List that holds collection schedule

        for collection in recycling_and_food_bin_dates:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(collection, "%d/%m/%Y").date(),
                    t="RECYCLING",
                    icon=ICON_MAP.get("RECYCLING"),
                )
            )
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(collection, "%d/%m/%Y").date(),
                    t="FOOD BIN",
                    icon=ICON_MAP.get("FOOD BIN"),
                )
            )

        for collection in black_bin_dates:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(collection, "%d/%m/%Y").date(),
                    t="BLACK BIN",
                    icon=ICON_MAP.get("BLACK BIN"),
                )
            )

        if garden_bin_dates[1] != '':  #
            for collection in garden_bin_dates:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(collection, "%d/%m/%Y").date(),
                        t="GARDEN WASTE",
                        icon=ICON_MAP.get("GARDEN WASTE"),
                    )
                )

        return entries
