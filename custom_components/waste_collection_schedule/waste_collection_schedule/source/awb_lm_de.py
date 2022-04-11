import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaftsbetrieb Limburg-Weilburg"
DESCRIPTION = "Source for AWB Limburg-Weilburg, Germany"
URL = "https://www.awb-lm.de/"

TEST_CASES = {
    "Bad Camberg - Schillerstr.": { "district":  1, "city": 47, "street": 1384},
    "Limburg - Goethestr.": { "district":  9, "city": 52, "street": 1538, "en": True}
}

HEADERS = {"user-agent": "Mozilla/5.0 (xxxx Windows NT 10.0; Win64; x64)"}


class Source:
    def __init__(self, district, city, street=None, en=False):
        self._district = district
        self._city = city
        self._street = street
        self._en = en
        self._ics = ICS()

    def fetch(self):
        session = requests.Session()

        params = {
            "Abfuhrbezirk": self._district,
            "Ortschaft": self._city,
            "Strasse": self._street,
        }

        r = requests.post(
             "https://www.awb-lm.de/generator/abfuhrtermine.php",
             data=params
        )
        
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, features="html.parser")
        downloads = soup.find_all("a", href=True)
        ics_url = None
        for download in downloads:
            href = download.get("href")
            if "cache/ical" in href:
                ics_url = href

        if ics_url is None:
            raise Exception(f"ics url not found")

        # get ics file
        r = session.get("https://www.awb-lm.de" + ics_url, headers=HEADERS)
        r.raise_for_status()

        # parse ics file
        dates = self._ics.convert(r.text)

        i18n = {
            "Bio-Abfall": "Biowaste",
            "Papier-Abfall": "Waste paper",
            "Gelber Sack": "Yellow bag",
            "Rest-Abfall": "Residual waste",
            "Sonderabfall": "Special waste",
            "Gehölzschnitt": "Copse"
        }

        entries = []
        for d in dates:
            waste_type = d[1].split(" am ")[0]

            if self._en: 
                for de, en in i18n.items():
                    waste_type = waste_type.replace(de, en) 

            entries.append(Collection(d[0], waste_type))

        return entries