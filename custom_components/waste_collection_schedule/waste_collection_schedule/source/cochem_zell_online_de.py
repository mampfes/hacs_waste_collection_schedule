import contextlib
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfall Cochem-Zell"
DESCRIPTION = "Source for waste collection in district Cochem-Zell."
URL = "https://www.cochem-zell-online.de/abfallkalender/"
TEST_CASES = {
    "Alf": {"district": "Alf"},
    "Bullay": {"district": "Bullay"},
    "Zell-Stadt": {"district": "Zell-Stadt"},
    "Pünderich": {"district": "Pünderich"},
}

API_URL = "https://abfallkalender10.app.moba.de/Cochem_Zell/api"
REMINDER_DAY = 0  # The calendar event should be on the same day as the waste collection
REMINDER_HOUR = 6  # The calendar event should start on any hour of the correct day, so this does not matter much
FILENAME = "Abfallkalender.ics"
ICON_MAP = {
    "Biotonne": "mdi:leaf",
    "Gruengut": "mdi:forest",
    "Papierabfall": "mdi:package-variant",
    "Restmülltonne": "mdi:trash-can",
    "Umweltmobil": "mdi:truck",
    "Verpackungsabfall": "mdi:recycle",
}


class Source:
    def __init__(self, district: str):
        self._district = district
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        entries = self._fetch_year(now.year)

        if now.month == 12:
            # also get data for next year if we are already in december
            with contextlib.suppress(Exception):
                entries.extend(self._fetch_year(now.year + 1))

        return entries

    def _fetch_year(self, year: int):
        url = "/".join(
            str(param)
            for param in (
                API_URL,
                self._district,
                year,
                REMINDER_DAY,
                REMINDER_HOUR,
                FILENAME,
            )
        )

        r = requests.get(url)
        schedule = self._ics.convert(r.text)

        return [
            Collection(
                date=entry[0], t=entry[1], icon=ICON_MAP.get(entry[1], "mdi:trash-can")
            )
            for entry in schedule
        ]
