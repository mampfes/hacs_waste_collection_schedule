import requests
import html
import json

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "KAEV Niederlausitz"
DESCRIPTION = "Source for Kommunaler Abfallentsorgungsverband Niederlausitz waste collection."
URL = "https://www.kaev.de/"
URL_ADDRESS = 'https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/ajax.aspx/getAddress'
TEST_CASES = {
    "Luckau / OT Zieckau": {
        "abf_strasse": "Zieckau",
        "abf_ort": "Luckau",
        "abf_ot": "Zieckau",
    },
    "Luckau Bersteweg": {
        "abf_strasse": "Bersteweg",
        "abf_ort": "Luckau",
        "abf_ot": "Luckau",
    },
    "Staakow": {
        "abf_strasse": "Waldstraße",
        "abf_ort": "Staakow",
        "abf_ot": "Staakow",
    },
}

def get_kalender_id(search):
    s=requests.Session()
    s.get('https://www.kaev.de/')
    payload={"query": search}
    resp = s.post(URL_ADDRESS, json=payload).json()
    abf_cal = json.loads(resp["d"])
    return abf_cal

class Source:
    def __init__(self, abf_ort, abf_ot, abf_strasse):
        self._abf_ort = abf_ort
        self._abf_ot = abf_ot
        self._abf_strasse = abf_strasse
        self._ics = ICS()

    def fetch(self):
        search_string_list = [self._abf_ort + " / " + self._abf_strasse,self._abf_ort + " / OT " + self._abf_ot , self._abf_ort + " / GT " + self._abf_ot, self._abf_ort]
        
        for search_string in search_string_list:
            abf_kalender = get_kalender_id(search_string)
            print(search_string)
            if len(abf_kalender) == 1:
                for abf_daten in abf_kalender:
                    print(search_string)
                    calurl = "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/iCal.aspx?Ort=" + abf_daten["name"] + "&OrtId=" + str(abf_daten["ortId"]) + "&OrtsteilId=" + str(abf_daten["ortsteilId"])
                    calurl = html.escape(calurl)
                break
            elif "/" not in search_string:
                for abf_daten in abf_kalender[0:1]:
                    print(search_string)
                    abf_kalender = abf_kalender[0:1]
                    calurl = "https://www.kaev.de/Templates/Content/DetailTourenplanWebsite/iCal.aspx?Ort=" + abf_daten["name"] + "&OrtId=" + str(abf_daten["ortId"])
                    calurl = html.escape(calurl)
                break

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
