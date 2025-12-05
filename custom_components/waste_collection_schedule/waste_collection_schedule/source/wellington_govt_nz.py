import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFound,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Wellington City Council"
DESCRIPTION = "Source for Wellington City Council."
URL = "https://wellington.govt.nz"
TEST_CASES = {
    "Chelsea St": {"streetName": "Cheltenham Terrace"},  # Friday
    # "Campbell St (ID Only)": {"streetId": "6515"},  # Wednesday
}


ICON_MAP = {
    "Rubbish Collection": "mdi:trash-can",
    "Glass crate": "mdi:glass-fragile",
    "Wheelie bin or recycling bags": "mdi:recycle",
}

PICTURE_MAP = {
    "Rubbish Collection": "https://wellington.govt.nz/assets/images/rubbish-recycling/rubbish-bag.png",
    "Glass crate": "https://wellington.govt.nz/assets/images/rubbish-recycling/glass-crate.png",
    "Wheelie bin or recycling bags": "https://wellington.govt.nz/assets/images/rubbish-recycling/wheelie-bin.png",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 Gecko/20100101 Firefox/136.0",
}


class Source:
    def __init__(self, streetId=None, streetName=None):
        self._streetId = streetId
        self._streetName = streetName
        self._ics = ICS()

    def fetch(self):
        # get token
        if self._streetName:
            url = "https://wellington.govt.nz/layouts/wcc/GeneralLayout.aspx/GetRubbishCollectionStreets"
            data = {"partialStreetName": self._streetName}
            r = requests.post(url, json=data, headers=HEADERS)
            data = json.loads(r.text)
            if len(data["d"]) == 0:
                raise SourceArgumentNotFound("streetName", self._streetName)
            if len(data["d"]) > 1:
                print(data["d"])
                raise SourceArgAmbiguousWithSuggestions(
                    "streetName",
                    self._streetName,
                    [x["Value"].split(",")[0] for x in data["d"]],
                )
            self._streetId = data["d"][0].get("Key")

        if not self._streetId:
            raise Exception("No streetId or streetName supplied")

        url = "https://wellington.govt.nz/~/ical/"
        params = {
            "type": "recycling",
            "streetId": self._streetId,
            "forDate": datetime.date.today(),
        }
        r = requests.get(url, params=params, headers=HEADERS)

        if not r.text.startswith("BEGIN:VCALENDAR"):
            raise SourceArgumentException(
                "streetId", f"{self._streetId} is not a valid streetID"
            )

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            for wasteType in d[1].split("&"):
                wasteType = wasteType.strip()
                entries.append(
                    Collection(
                        d[0],
                        wasteType,
                        picture=PICTURE_MAP.get(wasteType),
                        icon=ICON_MAP.get(wasteType),
                    )
                )
        return entries
