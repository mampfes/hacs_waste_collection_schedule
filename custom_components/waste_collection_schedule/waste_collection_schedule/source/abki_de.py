import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

from datetime import datetime
import logging

TITLE = "Abfallwirtschaftsbetrieb Kiel (ABK)"
DESCRIPTION = "Source for Abfallwirtschaftsbetrieb Kiel (ABK)."
URL = "https://abki.de/"
TEST_CASES = {
    "auguste-viktoria-straße, 14": {"street": "auguste-viktoria-straße", "number": 14},
    "Achterwehrer Straße, 1 A": {"street": "Achterwehrer Straße", "number": "1 a"},
    "Boltenhagener Straße, 4-8": {"street": "Boltenhagener Straße", "number": "4-8"},
}


ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bioabfall": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
}


ICAL_URL = "https://abki.de/abki-services/abki-leerungen-ical"
_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street: str, number: str | int):
        self._street: str = street
        self._number: str = str(number)
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        session = requests.Session()

        # get street id
        params = f'filter[logic]=and&filter[filters][0][value]={self._street}&filter[filters][0][field]=Strasse&filter[filters][0][operator]=startswith&filter[filters][0][ignoreCase]=true'
        r = session.get(
            "https://abki.de/abki-services/strassennamen", params=params)  # , params=params)
        r.raise_for_status()

        streets = r.json()
        if len(streets) > 1:
            _LOGGER.warning(
                "Multiple streets found please be more specific, using first one: "+streets[0]["Strasse"])
        if len(streets) < 1:
            raise ValueError("No street found", self._street)

        street_id = streets[0]["IDSTREET"]

        # get number id
        r = session.get("https://abki.de/abki-services/streetnumber",
                        params={"IDSTREET": street_id})
        r.raise_for_status()
        numbers = r.json()
        number_id, standort_id = None, None
        for number in numbers:
            if number["NUMBER"].lower().replace(" ", "").replace("-", "") == self._number.lower().replace(" ", "").replace("-", ""):
                number_id = number["id"]
                standort_id = number["IDSTANDORT"]
                break
        
        if number_id is None:
            raise ValueError("No number found", self._number)

        # get ics file link
        r = session.get("https://abki.de/abki-services/leerungen-data", params={
            "Zeitraum": now.year,
            "Strasse_input": self._street,
            "Strasse": street_id,
            "IDSTANDORT_input": 2,
            "IDSTANDORT": standort_id,
            "Hausnummernwahl": number_id
        })
        r.raise_for_status()
        request_data = r.json()["dataFile"]

        # get ICS file
        r = session.get(ICAL_URL, params={"data": request_data})

        dates = self._ics.convert(r.text)

        # if december, also try to get next year
        if now.month == 12:
            try:
                r = session.get("https://abki.de/abki-services/leerungen-data", params={
                    "Zeitraum": now.year+1,
                    "Strasse_input": self._street,
                    "Strasse": street_id,
                    "IDSTANDORT_input": 2,
                    "IDSTANDORT": standort_id,
                    "Hausnummernwahl": number_id
                })
                r.raise_for_status()
                request_data = r.json()["dataFile"]
                r = session.get(ICAL_URL, params={"data": request_data})
                dates += self._ics.convert(r.text)
            except:
                pass

        entries = []
        for d in dates:
            entries.append(Collection(
                d[0], d[1], ICON_MAP.get(d[1].split(" ")[0])))

        return entries
