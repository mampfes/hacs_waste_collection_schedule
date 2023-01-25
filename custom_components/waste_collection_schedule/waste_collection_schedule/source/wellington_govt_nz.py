import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Wellington City Council"
DESCRIPTION = "Source for Wellington City Council."
URL = "https://wellington.govt.nz"
TEST_CASES = {
    "Chelsea St": {"streetName": "chelsea street"},  # Friday
    "Campbell St (ID Only)": {"streetId": "6515"},  # Wednesday
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
            r = requests.post(url, json=data)
            data = json.loads(r.text)
            if len(data["d"]) == 0:
                raise Exception(f"No result found for streetName {self._streetName}")
            if len(data["d"]) > 1:
                raise Exception(
                    f"More then one result returned for streetName {self._streetName}, be more specific or use streetId instead"
                )
            self._streetId = data["d"][0].get("Key")

        if not self._streetId:
            raise Exception("No streetId supplied")

        url = "https://wellington.govt.nz/~/ical/"
        params = {
            "type": "recycling",
            "streetId": self._streetId,
            "forDate": datetime.date.today(),
        }
        r = requests.get(url, params=params)

        if not r.text.startswith("BEGIN:VCALENDAR"):
            raise Exception(f"{self._streetId} is not a valid streetID")

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
