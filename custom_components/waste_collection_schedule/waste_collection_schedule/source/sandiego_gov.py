import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of San Diego"
DESCRIPTION = "Source for the City of San Diego."
URL = "https://www.sandiego.gov/"
TEST_CASES = {
    "Test_001": {"id": "a4Ot0000000fEYZEA2"},
    "Test_002": {"id": "a4Ot0000001EEsyEAG"},
    "Test_003": {"id": "a4Ot0000000eANbEAM"},
}
ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Organics": "mdi:leaf",
    "Recyclables": "mdi:recycle",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION: dict = {
    "en": "The id can be found by visiting https://getitdone.sandiego.gov/apex/CollectionMapLookup) and searching for your address. Click on the Bookmarkable Page` button and when the Schedule Detail page has loaded you can see the id in the url.",
}
PARAM_TRANSLATIONS: dict = {
    "en": {
        "id": "The unique identifier for your properties collection schedule",
    }
}
PARAM_DESCRIPTIONS: dict = {
    "en": {
        "id": "The unique identifier for your properties collection schedule",
    }
}


class Source:
    def __init__(self, id: str):
        self._id: str = id

    def fetch(self):
        s = requests.Session()

        r = s.get(f"https://getitdone.sandiego.gov/CollectionDetail?id={self._id}")
        r.raise_for_status()

        soup = BeautifulSoup(r.content, "html.parser")
        columns = soup.find_all("div", {"class": "four columns"})

        entries = []
        for item in columns[1:]:
            waste_type = item.find("h3").text
            waste_date = re.search(r"(\d+/\d+/\d+)", item.text)
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date.group(1), "%m/%d/%Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
