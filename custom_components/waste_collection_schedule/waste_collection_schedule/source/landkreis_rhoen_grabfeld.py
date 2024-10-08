import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Landkreis Rhön Grabfeld"
DESCRIPTION = "Source for Rhönn Grabfeld uses service by offizium."
URL = "https://www.abfallinfo-rhoen-grabfeld.de/"
COUNTRY = "de"
TEST_CASES = {
    "City only": {"city": "Ostheim"},
    "City + District": {"city": "Ostheim", "district": "Oberwaldbehrungen"},
    "District only": {"district": "Oberwaldbehrungen"},
    "empty": {},
}

API_URL = "https://fs-api-rg.offizium.com/abfalltermine"

EVENT_BLACKLIST = [
    "Wertstoffhof Mellrichstadt",
    "Wertstoffhof Bad Königshofen",
    "Wertstoffzentrum Bad Neustadt",
    "Wertstoffsammelstelle Ostheim",
    "Wertstoffsammelstelle Bischofsheim",
]

ICON_MAP = {
    "Restmüll/Biotonne": "mdi:trash-can",
    "Gelbe Tonne": "mdi:recycle-variant",
    "Papiersammlung": "mdi:package-variant",
    "Problemmüllsammlung": "mdi:biohazard",
}


PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "district": "Ortsteil",
    }
}


class Source:
    def __init__(self, city: str | None = None, district: str | None = None):
        self._city = city
        self._district = district

    def fetch(self):
        r = requests.get(
            API_URL, params={"stadt": self._city, "ortsteil": self._district}
        )

        r.raise_for_status()

        entries = []
        for event in r.json():
            # filter out Sammelstellen, Wertstoffhof and Wertstoffzentrum
            if event["muellart"] not in EVENT_BLACKLIST:
                entries.append(
                    Collection(
                        date=datetime.datetime.fromisoformat(event["termin"]).date(),
                        t=event["muellart"],
                        icon=ICON_MAP.get(event["muellart"], "mdi:trash-can"),
                    )
                )

        return entries
