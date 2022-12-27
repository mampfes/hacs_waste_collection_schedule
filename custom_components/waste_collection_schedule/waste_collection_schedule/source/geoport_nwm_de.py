import datetime
import requests
import urllib
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Nordwestmecklenburg"
DESCRIPTION = "Source for Landkreis Nordwestmecklenburg"
URL = "https://www.geoport-nwm.de/de/abfuhrtermine-geoportal.html"
TEST_CASES = {
    "Rüting": {"district": "Rüting"},
    "Grevenstein u. ...": {"district": "Grevenstein u. Ausbau"},
    "Seefeld": {"district": "Seefeld/ Testorf- Steinfort"},
    "1100l": {"district": "Groß Stieten (1.100 l Behälter)"},
    "kl. Bünsdorf": {"district": "Klein Bünsdorf"}
}


class Source:
    def __init__(self, district):
        self._district = district
        self._ics = ICS()

    def fetch(self):
        today = datetime.date.today()
        dates = []
        if today.month == 12:
            # On Dec 27 2022, the 2022 schedule was no longer available for test case "Seefeld", all others worked
            try:
                dates = self.fetch_year(today.year)
            except Exception:
                pass
            try:
                dates.extend(self.fetch_year(today.year + 1))
            except Exception:
                pass
        else:
            dates = self.fetch_year(today.year)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries

    def fetch_year(self, year):
        arg = convert_to_arg(self._district)
        r = requests.get(
            f"https://www.geoport-nwm.de/nwm-download/Abfuhrtermine/ICS/{year}/{arg}.ics")
        r.raise_for_status()
        return self._ics.convert(r.text)


def convert_to_arg(district):
    district = district.replace("(1.100 l Behälter)", "1100_l")
    district = district.replace("ü", "ue")
    district = district.replace("ö", "oe")
    district = district.replace("ä", "ae")
    district = district.replace("ß", "ss")
    district = district.replace("/", "")
    district = district.replace("- ", "-")
    district = district.replace(".", "")
    district = district.replace(" ", "_")
    arg = urllib.parse.quote("Ortsteil_" + district)
    return arg
