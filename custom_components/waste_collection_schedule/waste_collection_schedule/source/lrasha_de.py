import datetime
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS


TITLE = "Landkreis Schwäbisch Hall"
DESCRIPTION = "Source for lrasha.de - Landkreis Schwäbisch Hall"  # Describe your source
URL = "https://exchange.cmcitymedia.de/landkreis-schwaebisch-hallt3/wasteCalendarExport.php"    # Insert url to service homepage
TEST_CASES = { # Insert arguments for test cases using test_sources.py script
    "TestName": {"arg1": 100, "arg2": "street"}
}


class Source:
    def __init__(self, location):
        self._location = location

    def fetch(self):
        entries = []

        entries.append(
            Collection(
                datetime.datetime(2020, 4, 11),
                "Waste Type",
            )
        )

        return entries
