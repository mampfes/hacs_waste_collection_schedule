from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import json

TITLE = "Richmondshire (North Yorkshire)"
DESCRIPTION = "To find your UPRN, visit the Richmondshire page and use the address search. Right-click your entry in the house dropdown, choose Inspect, and copy the UPRN from the value"
URL = "https://www.richmondshire.gov.uk/collectionCalendar"
TEST_CASES = {"test 1": {"uprn": 200001767082}, "test 2": {"uprn": 200001767078}, "test3": {"uprn": 200001767079 }}

ICONS = {
    "240L GREY RUBBISH BIN": "mdi:trash-can",
    "55L RECYCLING BOX": "mdi:recycle",
    "140L GARDEN BIN": "mdi:leaf",
}

class Source:
    def __init__(
        self, uprn
    ):  # argX correspond to the args dict in the source configuration
        self._uprn = uprn

    def fetch(self):
        r = requests.get(
            f"https://www.richmondshire.gov.uk/Umbraco/Api/MyAreaApi/GetBinRoundData?uprn={self._uprn}"
        )
#        print(r.text)
        ids = r.json()
#        print (len(ids))

        entries = []

        for id in ids:
            entries.append(
                Collection(
                    date=datetime.strptime(id["start"], "%Y-%m-%dT%H:%M:%S").date(),
                    t=id["title"],
                    icon=ICONS.get(id["title"]),
                )
            )
        return entries
