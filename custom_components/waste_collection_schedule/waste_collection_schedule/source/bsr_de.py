import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Berliner Stadtreinigungsbetriebe"
DESCRIPTION = "Source for Berliner Stadtreinigungsbetriebe waste collection."
URL = "https://bsr.de"
TEST_CASES = {
    "Caroline1": {
        "abf_strasse": "Caroline-Michaelis-Str.",
        "abf_hausnr": 8,
    },
    "Hufeland1": {
        "abf_strasse": "Hufelandstr",
        "abf_hausnr": "45a",
    },
    "Hufeland2": {
        "abf_strasse": "Hufelandstr.",
        "abf_hausnr": "45a",
    },
    "Hufeland3": {
        "abf_strasse": "Hufelandstrasse",
        "abf_hausnr": "45a",
    },
    "Hufeland4": {
        "abf_strasse": "Hufelandstraße",
        "abf_hausnr": "45a",
    },
}

URL_BASE = "https://umnewforms.bsr.de/p/de.bsr.adressen.app"

def get_schedule_id(abf_strasse, abf_hausnr):
    with requests.Session() as sess:
        args = {
            "searchQuery": f"{abf_strasse}:::{abf_hausnr}",
        }

        response = sess.get(
            f"{URL_BASE}/plzSet/plzSet", params=args,
        )

    return response.json()[0]["value"]


def download_monthly_ICS(sess, id, month, year):
    args = {
        "year": year,
        "month": month,
    }
    response = sess.get(
        f"{URL_BASE}/abfuhr/kalender/ics/{id}", params=args,
    )

    return response.text


PARAM_TRANSLATIONS = {
    "de": {
        "abf_strasse": "Straße",
        "abf_hausnr": "Hausnummer",
    }
}


ICONS = {
    "Hausmüll": "mdi:trash-can",
    "Biogut": "mdi:leaf",
    "Wertstoffe": "mdi:recycle",
}


def get_icon(text):
    for icon_key, icon_value in ICONS.items():
        if icon_key in text:
            return icon_value
    return None


class Source:
    def __init__(self, abf_strasse, abf_hausnr):
        self._abf_strasse = abf_strasse
        self._abf_hausnr = abf_hausnr
        self._ics = ICS()

    def fetch(self):
        schedule_id = get_schedule_id(self._abf_strasse, self._abf_hausnr)

        # fetch monthly ics files for the next 12 months
        dates = []
        now = datetime.datetime.now()
        with requests.Session() as sess:
            for i in range(12):
                month, year = now.month + i, now.year
                if month > 12:
                    month = month % 12
                    year = year + 1

                ics = download_monthly_ICS(sess, schedule_id, month, year)
                dates.extend(self._ics.convert(ics))

        return [Collection(date=d[0], t=d[1], icon=get_icon(d[1])) for d in dates]
