import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from datetime import datetime

TITLE = "Fife Council"
DESCRIPTION = "Source for Fife Council."
URL = "https://www.fife.gov.uk"
TEST_CASES = {
    "SANDYHILL ROAD, ST ANDREWS": {"uprn": 320069186},
    "CERES ROAD, PITSCOTTIE" : {"uprn": 320063641},
    "SHORE ROAD, BALMALCOLM": {"uprn": "320083539"},
    "CANMORE STREET, DUNFERMLINE": {"uprn": "320101510"},
}


ICON_MAP = {
    "Blue": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Brown": "mdi:leaf",
    "Grey": "mdi:package-variant",
    "Green": "mdi:recycle",
}


API_URL = "https://www.fife.gov.uk/api/custom"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = str(uprn)

    def fetch(self):
        session = requests.Session()
        auth = session.get("https://www.fife.gov.uk/api/citizen?preview=false&locale=en").headers["Authorization"]
        session.headers.update({"Authorization": auth})
        
        args = {
            "name": "bin_calendar",
            "data": {"uprn": self._uprn},
        }

        params = {
            "action": "powersuite_bin_calendar_collections",
            "actionedby": "bin_calendar",
            "loadform": True,
            "access": "citizen",
            "locale": "en",
        }

        # get json file
        r = session.post(API_URL, params=params, json=args)
        r.raise_for_status()

        data = r.json()["data"]
        if data["results_returned"] == "false":
            raise Exception("No results returned")

        entries = []
        for d in data["tab_collections"]:
            date = datetime.strptime(d["date"], "%A, %B %d, %Y").date()
            icon = ICON_MAP.get(d["colour"])  # Collection icon
            type = d["type"]
            entries.append(Collection(date=date, t=type, icon=icon))

        return entries
