import base64
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Wermelskirchen"
DESCRIPTION = "Source for Abfallabholung Wermelskirchen, Germany"
URL = "https://www.bavweb.de/Bergischer-Abfallwirtschaftsverband/Abfuhrkalender-Service/Wermelskirchen/"
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

TYPE_MAP = {
    "Restmülltonne 2-wöchentlich": "Restabfall 2-woechentlich",
    "Restmülltonne 4-wöchentlich": "Restabfall 4-woechentlich",
    "Restmülltonne 6-wöchentlich": "Restabfall 6-woechentlich",
    "Gelber Sack / Tonne": "Gelber Sack",
    "Papiertonne": "Papier",
    "Schadstoffmobil": "Schadstoffsammlung",
    "Weihnachtsbaum": "Abfuhr Weihnachtsbaum",
}


PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "house_number": "Hausnummer",
    }
}


class Source:
    def __init__(self, street, house_number):
        self._street = street
        self._house_number = str(house_number)
        self._ics = ICS()

    def _normalize_street(self):
        if "Ã" in self._street:
            try:
                return self._street.encode("latin1").decode("utf-8")
            except UnicodeError:
                return self._street
        return self._street

    def fetch(self):
        now = datetime.now()
        street = self._normalize_street()
        street_token = base64.b64encode(
            f"Wermelskirchen42929{street}".encode("latin1")
        ).decode("ascii")
        url = "https://abfallkalender.regioit.de/kalender-bav/downloadfile.jsp"
        params = {
            "format": "ics",
            "jahr": str(now.year),
            "ort": "Wermelskirchen",
            "strStatic": street_token,
            "zeit": "1:00:00",
            "fraktion": [8, 12, 13, 15, 16, 22, 23, 24],
        }
        r = requests.get(url, params=params)
        r.raise_for_status()

        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            waste_type = TYPE_MAP.get(d[1], d[1])
            info = ICON_MAP.get(waste_type, {"icon": None, "image": None})
            entries.append(
                Collection(d[0], waste_type, picture=info["image"], icon=info["icon"])
            )
        return entries
