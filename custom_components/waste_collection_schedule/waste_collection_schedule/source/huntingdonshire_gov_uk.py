import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Huntingdonshire District Council"
DESCRIPTION = "Source for Huntingdonshire.gov.uk services for Huntingdonshire District Council."
URL = "https://www.huntingdonshire.gov.uk"
TEST_CASES = {
    "Wells Close, Brampton": {"uprn": "100090123510"},
    "Inkerman Rise, St. Neots": {"uprn": "10000144271"},
}

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        # get json file
        r = requests.get(
            f"https://servicelayer3c.azure-api.net/wastecalendar/collection/search/{self._uprn}?authority=HDC&take=20"
        )

        # extract data from json
        data = json.loads(r.text)

        entries = []

        collections = r.json()["collections"]
        entries = []

        for collection in collections:
            for round_type in collection["roundTypes"]:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            collection["date"], "%Y-%m-%dT%H:%M:%SZ"
                        ).date(),
                        t=round_type.title(),
                        icon=ICON_MAP.get(round_type),
                    )
                )


        return entries
