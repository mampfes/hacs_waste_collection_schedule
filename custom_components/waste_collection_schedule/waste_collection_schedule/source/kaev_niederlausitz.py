import requests
import html
import json

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "KAEV Niederlausitz"
DESCRIPTION = "Source for Kommunaler Abfallverband Niederlausitz waste collection."
URL = "https://www.kaev.de/"
COUNTRY = "de"
TEST_CASES = {
    "Luckau / OT Zieckau": {
        "abf_suche": "Luckau / OT Zieckau",
    },
    "Luckau Bersteweg": {
        "abf_suche": "Luckau / Bersteweg",
    },
    "Staakow": {
        "abf_suche": "Staakow",
    },
}

API_URL = 'https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/ajax.aspx/getAddress'

def get_kalender_id(search):
    s=requests.Session()
    s.get('https://www.kaev.de/')
    payload={"query": search}
    resp = s.post(API_URL, json=payload).json()
    abf_cal = json.loads(resp["d"])
    return abf_cal

class Source:
    def __init__(self, abf_suche):
        self._abf_suche = abf_suche
        self._ics = ICS()

    def fetch(self):
        abf_kalender = get_kalender_id(self._abf_suche)
        if len(abf_kalender) == 1:
            for abf_daten in abf_kalender:
                calurl = "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/iCal.aspx?Ort=" + abf_daten["name"] + "&OrtId=" + str(abf_daten["ortId"]) + "&OrtsteilId=" + str(abf_daten["ortsteilId"])
                calurl = html.escape(calurl)
        elif "/" not in self._abf_suche:
            for abf_daten in abf_kalender[0:1]:
                    abf_kalender = abf_kalender[0:1]
                    calurl = "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/iCal.aspx?Ort=" + abf_daten["name"] + "&OrtId=" + str(abf_daten["ortId"])
                    calurl = html.escape(calurl)

        if len(abf_kalender) > 1:
            raise Exception("Error: Mehrere Einträge gefunden")

        if len(abf_kalender) == 0:
            raise Exception("Error: Keine Einträge gefunden")
        
        r=requests.get(calurl)
        r.encoding = "utf-8"

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1].removesuffix(", ")))
        return entries