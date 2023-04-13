import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

from datetime import datetime

TITLE = "Abfallwirtschaftsbetrieb Kiel (ABK)"
DESCRIPTION = "Source for Abfallwirtschaftsbetrieb Kiel (ABK)."
URL = "https://abki.de/"
TEST_CASES = {
    "auguste-viktoria-straße, 14": {"street": "auguste-viktoria-straße", "number": 14},
    "Achterwehrer Straße, 1 A": {"street": "Achterwehrer Straße", "number": "1 a"},
}


ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
}


ICAL_URL = "https://abki.de/abki-services/abki-leerungen-ical"
REQUEST_DATA_ARG = "{year}-{street}-{number}-stand-{date}"


class Source:
    def __init__(self, street: str, number: str | int):
        self._street: str = street.replace(" ", "-").lower()
        self._number: str = str(number).replace(" ", "-").lower()
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        args = {
            "street": self._street,
            "number": self._number,
            "date": now.strftime("%d-%m-%Y"),
        }

        # get ICS file
        request_data = REQUEST_DATA_ARG.format(year=now.year, **args)
        r = requests.get(ICAL_URL, params={"data": request_data})

        dates = self._ics.convert(r.text)
        
        # if december, also try to get next year
        if now.month == 12:
            request_data = REQUEST_DATA_ARG.format(year=now.year+1, **args)
            try:
                r = requests.get(ICAL_URL, params={"data": request_data})
                dates += self._ics.convert(r.text)
            except:
                pass

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1].split(" ")[0])))

        return entries
