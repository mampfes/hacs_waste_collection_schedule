import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Source for Rhön Grabfeld"
DESCRIPTION = "Source for Rhönn Grabfeld uses service by offizium."
URL = 'https://fs-api-rg.offizium.com/abfalltermine'
TEST_CASES = {
    "City only": {"city": "Ostheim"},
    "City + District": {"city": "Ostheim", "district": "Oberwaldbehrungen"},
    "District only": {"district": "Oberwaldbehrungen"},
    "empty": {}
}


class Source:
    def __init__(self, city: str = None, district: str = None):
        self._city = city
        self._district = district
        self._iconMap = {
            "Restmüll/Gelber Sack/Biotonne": "mdi:trash-can",
            "Papiersammlung": "mdi:package-variant",
            "Problemmüllsammlung": "mdi:biohazard"
        }

    def fetch(self):
        now = datetime.datetime.now().date()

        r = requests.get(URL, params={
            "stadt": self._city,
            "ortsteil": self._district
        })

        r.raise_for_status()

        entries = []
        for event in r.json():
            # filter out Sammelstellen, Wertstoffhof and Wertstoffzentrum
            if event["muellart"] in self._iconMap:
                entries.append(
                    Collection(
                        date=datetime.datetime.fromisoformat(
                            event["termin"]).date(),
                        t=event["muellart"],
                        icon=self._iconMap.get(
                            event["muellart"], "mdi:trash-can")
                    )
                )

        return entries
