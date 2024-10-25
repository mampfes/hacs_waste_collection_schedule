# There was an ICS source but the ICS file was not stored permanently and would be removed after a few days.
import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallbehandlungsgesellschaft Havelland mbH (abh)"
DESCRIPTION = "Source for Abfallbehandlungsgesellschaft Havelland mbH."
URL = "https://abfall-havelland.de/"
TEST_CASES = {
    "Wustermark Drosselgasse": {
        "ort": "Wustermark",
        "strasse": "Drosselgasse",
    },
    "Milow Friedhofstr.": {"ort": "Milow", "strasse": "Friedhofstr."},
}


ICON_MAP = {
    "mülltonne": "mdi:trash-can",
    "bio-tonne": "mdi:leaf",
    "papier": "mdi:package-variant",
    "gelbe": "mdi:recycle",
}


API_URL = "https://www.abfall-havelland.de//groups/public/modules/ajax_tourenplan.php"
BASE_URL = "https://www.abfall-havelland.de/"


class Source:
    def __init__(self, ort: str, strasse: str):
        self._ort: str = ort
        self._strasse: str = strasse
        self._ics = ICS(split_at=", ")

    def fetch(self) -> list[Collection]:
        args = {"city": self._ort, "street": self._strasse}

        # get json file
        r = requests.get(API_URL, params=args)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        ics_link_tag = soup.find("a", id="ical")
        if not isinstance(ics_link_tag, Tag):
            raise Exception("No ics link found")
        ics_link = ics_link_tag.attrs["onclick"].split("'")[1]
        if not isinstance(ics_link, str):
            raise Exception("No ics link found")
        r = requests.get(BASE_URL + ics_link)
        r.raise_for_status()
        r.encoding = "utf-8"
        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            bin_type = d[1].replace(" - Abholtermin", "")
            entries.append(
                Collection(d[0], bin_type, ICON_MAP.get(bin_type.split()[0].lower()))
            )

        return entries
