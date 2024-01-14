import datetime
import urllib

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Nordwestmecklenburg"
DESCRIPTION = "Source for Landkreis Nordwestmecklenburg"
URL = "https://www.geoport-nwm.de"
TEST_CASES = {
    "Rüting": {"district": "Rüting"},
    "Grevenstein u. ...": {"district": "Grevenstein u. Ausbau"},
    "Seefeld": {"district": "Seefeld/ Testorf- Steinfort"},
    "1100l": {"district": "Groß Stieten (1.100 l Behälter)"},
    "kl. Bünsdorf": {"district": "Klein Bünsdorf"},
}

API_URL = "https://www.geoport-nwm.de/nwm-download/Abfuhrtermine/ICS/{year}/{arg}.ics"


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
        r = requests.get(API_URL.format(year=year, arg=arg))
        r.raise_for_status()
        entries = self._ics.convert(r.text)
        for prefix in (
            "Schadstoffmobil",
            "Papiertonne_GER",
            "Papiertonne_Gollan",
            "Papiertonne_Veolia",
        ):
            try:
                r = requests.get(API_URL.format(year=year, arg=f"{prefix}_{arg}"))
                r.raise_for_status()
                new_entries = self._ics.convert(r.text)
                entries.extend(new_entries)
            except (ValueError, requests.exceptions.HTTPError):
                pass
        return entries


def convert_to_arg(district, prefix=""):
    district = district.replace("(1.100 l Behälter)", "1100_l")
    district = district.replace("ü", "ue")
    district = district.replace("ö", "oe")
    district = district.replace("ä", "ae")
    district = district.replace("ß", "ss")
    district = district.replace("/", "")
    # district = district.replace("- ", "-") failed with Seefeld/ Testorf- Steinfort
    district = district.replace(".", "")
    district = district.replace(" ", "_")
    prefix = prefix + "_" if prefix else ""
    arg = urllib.parse.quote(f"{prefix}Ortsteil_{district}")
    return arg
