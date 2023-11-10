import re
import requests
from datetime import datetime

from bs4 import BeautifulSoup

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis"
DESCRIPTION = "Source for ZVA (Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis)."
URL = "https://www.zva-sek.de"
TEST_CASES = {
    "Fritzlar": {
        "bezirk": "Fritzlar",
        "ortsteil": "Fritzlar-kernstadt",
        "strasse": "Ahornweg",
    },
    "Ottrau": {
        "bezirk": "Ottrau",
        "ortsteil": "immichenhain",
        "strasse": "",
    },
    "Knüllwald": {
        "bezirk": "Knüllwald",
        "ortsteil": "Hergetsfeld",
    },
    "Felsberg": {
        "bezirk": "Felsberg",
        "ortsteil": "Felsberg",
    },
    "Guxhagen": {
        "bezirk": "Guxhagen",
        "ortsteil": "Guxhagen",
    },
}
SERVLET = (
    "https://www.zva-sek.de/module/abfallkalender/generate_ical.php"
)
MAIN_URL = "https://www.zva-sek.de/online-dienste/abfallkalender-{year}/{file}"
API_URL = "https://www.zva-sek.de/module/abfallkalender/{file}"


class Source:
    def __init__(
        self, bezirk: str, ortsteil: str, strasse: str = None
    ):
        self._bezirk = bezirk
        self._ortsteil = ortsteil
        self._street = strasse if strasse != "" else None
        self._ics = ICS()

    def fetch(self):
        session = requests.session()
        year = datetime.now().year

        bezirk_id = None
        ortsteil_id = None

        # get bezirke id
        r = session.get(MAIN_URL.format(
            year=year, file=f"abfallkalender-{year}.html"))
        if (r.status_code == 404):  # try last year URL if this year is not available
            r = session.get(MAIN_URL.format(
                year=year, file=f"abfallkalender-{year-1}.html"))
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, features="html.parser")
        for option in soup.find("select", {"name": "ak_bezirk"}).find_all("option"):
            if option.text.lower() == self._bezirk.lower():
                self._bezirk = option.get("value")
                bezirk_id = option.get("value")
                break

        if not bezirk_id:
            raise Exception(f"bezirk not found")

        # get ortsteil id
        r = session.get(API_URL.format(
            file="get_ortsteile.php"), params={"bez_id": bezirk_id})
        r.raise_for_status()
        last_orts_id = None
        for part in r.text.split(";")[2:-1]:
            # part is "f.ak_ortsteil.options[5].text = 'Alte Kasseler Straße'" or "ak_ortsteil.options[6].value = '2'"
            if ("length" in part):
                continue
            if part.split(" = ")[1][1:-1].lower() == self._ortsteil.lower():
                ortsteil_id = last_orts_id
                break
            last_orts_id = part.split(" = ")[1][1:-1]

        if not ortsteil_id:
            raise Exception(f"ortsteil not found")

        street_id = None

        # get street id if steet given
        if self._street is not None:
            r = session.get(API_URL.format(
                file="get_strassen.php"), params={"ot_id": ortsteil_id.split("-")[0]})
            r.raise_for_status()
            last_street_id = None
            for part in r.text.split(";")[2:-1]: 
                # part is "f.ak_strasse.options[5].text = 'Alte Kasseler Straße'" or "ak_strasse.options[6].value = '2'"
                if ("length" in part):
                    continue
                if part.split(" = ")[1][1:-1].lower() == self._street.lower():
                    street_id = last_street_id
                    break
                last_street_id = part.split(" = ")[1][1:-1]

            if not street_id:
                raise Exception(f"street not found")

        entries = self.get_calendar_data(year, bezirk_id, ortsteil_id, street_id, session)
        if datetime.now().month >= 11:
            try:
                entries += self.get_calendar_data(year+1, bezirk_id, ortsteil_id, street_id, session)
            except Exception as e:
                pass
        return entries
        
    def get_calendar_data(self, year, bezirk_id, ortsteil_id,street_id, session):
        args = {
            "year": str(year),
            "ak_bezirk": bezirk_id,
            "ak_ortsteil": ortsteil_id,
            "alle_arten": "",
            "iCalEnde": 6,
            "iCalBeginn": 17,
        }
        if self._street is not None:
            args["ak_strasse"] = street_id

        r = session.post(
            SERVLET,
            data=args,
        )

        r.raise_for_status()
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], re.sub(
                "[ ]*am [0-9]+.[0-9]+.[0-9]+[ ]*", "", d[1])))
        return entries
