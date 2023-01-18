from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Wermelskirchen"
DESCRIPTION = "Source for Abfallabholung Wermelskirchen, Germany"
URL = "https://www.wermelskirchen.de"
TEST_CASES = {
    "Rathaus": {"street": "Telegrafenstraße", "house_number": "29"},
    "Krankenhaus": {"street": "Königstraße", "house_number": "100"},
    "Mehrzweckhalle": {"street": "An der Mehrzweckhalle", "house_number": "1"},
}

ICON_MAP = {
    "Restabfall 2-woechentlich": {
        "icon": "mdi:trash-can",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/1/b/csm_Restmuell_6b2b32c774.png",
    },
    "Restabfall 4-woechentlich": {
        "icon": "mdi:trash-can",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/1/b/csm_Restmuell_6b2b32c774.png",
    },
    "Restabfall 6-woechentlich": {
        "icon": "mdi:trash-can",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/1/b/csm_Restmuell_6b2b32c774.png",
    },
    "Gelber Sack": {
        "icon": "mdi:recycle-variant",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/f/4/csm_GelbeTonne_24ffc276b2.png",
    },
    "Papier": {
        "icon": "mdi:package-variant",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/2/3/csm_Papiertonne_919ed3b5da.png",
    },
    "Biotonne": {
        "icon": "mdi:leaf",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/6/f/csm_Biotonne_wk_ae1b0e61aa.png",
    },
    "Schadstoffsammlung": {
        "icon": "mdi:bottle-tonic-skull",
        "image": "https://abfallkalender.citkomm.de/fileadmin/_processed_/4/2/csm_sondermuell_62f5701a7b.png",
    },
    "Weihnachtsbaum": {"icon": "mdi:pine-tree", "image": ""},
}


class Source:
    def __init__(self, street, house_number):
        self._street = street
        self._house_number = str(house_number)
        self._ics = ICS()

    def fetch(self):
        # the url contains the current year, but this doesn't really seems to matter at least for the ical, since the result is always the same
        # still replace it for compatibility sake
        now = datetime.now()
        url = f"https://abfallkalender.citkomm.de/wermelskirchen/abfallkalender-{str(now.year)}/ics/FrontendIcs.html"
        params = {
            "tx_citkoabfall_abfallkalender[strasse]": self._street,
            "tx_citkoabfall_abfallkalender[hausnummer]": self._house_number,
            "tx_citkoabfall_abfallkalender[abfallarten][0]": 86,
            "tx_citkoabfall_abfallkalender[abfallarten][1]": 85,
            "tx_citkoabfall_abfallkalender[abfallarten][2]": 84,
            "tx_citkoabfall_abfallkalender[abfallarten][3]": 82,
            "tx_citkoabfall_abfallkalender[abfallarten][4]": 81,
            "tx_citkoabfall_abfallkalender[abfallarten][5]": 80,
            "tx_citkoabfall_abfallkalender[abfallarten][6]": 79,
            "tx_citkoabfall_abfallkalender[abfallarten][7]": 76,
            "tx_citkoabfall_abfallkalender[abfallarten][8]": 75,
            "tx_citkoabfall_abfallkalender[abfallarten][9]": 74,
        }
        r = requests.get(url, params=params)
        r.raise_for_status()

        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            info = ICON_MAP.get(d[1], {"icon": None, "image": None})
            entries.append(
                Collection(d[0], d[1], picture=info["image"], icon=info["icon"])
            )
        return entries
