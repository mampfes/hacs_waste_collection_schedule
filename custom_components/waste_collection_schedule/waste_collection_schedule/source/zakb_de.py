import re
from difflib import get_close_matches

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Zweckverband Abfallwirtschaft Kreis Bergstraße"
DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Kreis Bergstraße."
URL = "https://www.zakb.de"
TEST_CASES = {
    "Abtsteinach, Am Hofböhl 1 ": {
        "ort": "Abtsteinach",
        "strasse": "Am Hofböhl",
        "hnr": "1",
        "hnr_zusatz": "",
    },
    "Gorxheimertal, Am Herrschaftswald 10": {
        "ort": "Gorxheimertal",
        "strasse": "Am Herrschaftswald",
        "hnr": "10",
    },
    "Rimbach, Ahornweg 1 B": {
        "ort": "Rimbach",
        "strasse": "Ahornweg",
        "hnr": "1",
        "hnr_zusatz": "B",
    },
    "Zwingenberg, Diefenbachstraße 57": {
        "ort": "Zwingenberg",
        "strasse": "Diefenbachstraße",
        "hnr": 57,
        "hnr_zusatz": "",
    },
    "Bensheim im Bangert 9 a": {
        "ort": "Bensheim",
        "strasse": "Im Bangert",
        "hnr": 9,
        "hnr_zusatz": "A",
    },
    "Zwingenberg, Wiesenpromenade-West 41": {
        "ort": "Zwingenberg",
        "strasse": "Wiesenpromenade-West",
        "hnr": 41,
    },
}


ICON_MAP = {
    "Restabfallbehaelter": Icons.GENERAL_WASTE,
    "Restabfallcontainer": Icons.GENERAL_WASTE,
    "Bioabfallbehaelter": Icons.BIO_KITCHEN,
    "Papierbehaelter": Icons.PAPER,
    "Papiercontainer": Icons.PAPER,
    "Gelber Sack": Icons.PLASTIC_PACKAGING,
    "Gruensperrmuell": Icons.GARDEN,
}


API_URL = "https://www.zakb.de/online-service/abfallkalender/"


PARAM_TRANSLATIONS = {
    "de": {
        "ort": "Ort",
        "strasse": "Straße",
        "hnr": "Hausnummer",
        "hnr_zusatz": "Hausnummerzusatz",
    },
    "en": {
        "ort": "City",
        "strasse": "Street",
        "hnr": "House number",
        "hnr_zusatz": "House number addition",
    },
}


def _extract_select_options(html: str, select_id: str) -> list[str]:
    match = re.search(rf'<select id="{select_id}".*?</select>', html, re.S)
    if not match:
        return []
    return re.findall(r'value="([^"]*)"', match.group(0))


class Source:
    def __init__(self, ort: str, strasse: str, hnr: str | int, hnr_zusatz: str = ""):
        self._ort: str = ort
        self._strasse: str = strasse
        self._hnr: str = str(hnr)
        self._hnr_zusatz: str = hnr_zusatz
        self._ics = ICS()

    def fetch(self):
        # inizilize session
        session = requests.Session()

        # make request to get session cookie and available cities
        r = session.get(API_URL)
        r.raise_for_status()

        ort_options = _extract_select_options(r.text, "Ort")
        if ort_options and self._ort not in ort_options:
            raise SourceArgumentNotFoundWithSuggestions(
                "ort",
                self._ort,
                get_close_matches(self._ort, ort_options, n=5, cutoff=0.4)
                or ort_options,
            )

        args = {
            "aos[Ort]": self._ort,
            "aos[CheckBoxRestabfallbehaelter]": "on",
            "aos[CheckBoxRestabfallcontainer]": "on",
            "aos[CheckBoxBioabfallbehaelter]": "on",
            "aos[CheckBoxPapierbehaelter]": "on",
            "aos[CheckBoxPapiercontainer]": "on",
            "aos[CheckBoxGruensperrmuell]": "on",
            "aos[CheckBoxGelber+Sack]": "on",
            "aos[CheckBoxDSD-Container]": "on",
            "submitAction": "CITYCHANGED",
            "pageName": "Lageadresse",
        }

        # make request to call CITYCHANGED and get the streets available for this city.
        # The site uses its own street-name spelling (e.g. hyphens instead of spaces),
        # so validate against it and offer suggestions instead of failing deep in ICS parsing.
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        strasse_options = _extract_select_options(r.text, "Strasse")
        if strasse_options and self._strasse not in strasse_options:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse",
                self._strasse,
                get_close_matches(self._strasse, strasse_options, n=5, cutoff=0.4)
                or strasse_options,
            )

        args["aos[Strasse]"] = self._strasse
        args["aos[Hausnummer]"] = self._hnr
        args["aos[Hausnummerzusatz]"] = self._hnr_zusatz

        # make request to set data for session
        args["submitAction"] = "nextPage"
        r = session.post(API_URL, data=args)
        r.raise_for_status()

        # make request to get ical file
        r = session.post(
            API_URL,
            data={"submitAction": "filedownload_ICAL", "pageName": "Terminliste"},
        )
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1].strip(), ICON_MAP.get(d[1].strip())))
        return entries
