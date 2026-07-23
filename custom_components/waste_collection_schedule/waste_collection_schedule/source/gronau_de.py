import re
from datetime import datetime
from html import unescape

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Gronau"
DESCRIPTION = "Source for Abfallkalender Gronau, Germany"
URL = "https://abfallkalender.regioit.de/kalender-wml/"
COUNTRY = "de"

TEST_CASES = {
    "Viktoriastraße": {"street": "Viktoriastraße"},
    "Alter Markt": {"street": "Alter Markt"},
}

PARAM_TRANSLATIONS = {
    "en": {"street": "Street"},
    "de": {"street": "Straße"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name as listed in the Gronau waste calendar (e.g. 'Viktoriastraße').",
    },
    "de": {
        "street": "Straßenname wie im Gronauer Abfallkalender gelistet (z.B. 'Viktoriastraße').",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Open https://abfallkalender.regioit.de/kalender-wml/index.jsp?ort=Gronau and pick your street; use the exact spelling shown there.",
    "de": "Öffnen Sie https://abfallkalender.regioit.de/kalender-wml/index.jsp?ort=Gronau und wählen Sie Ihre Straße; verwenden Sie die genaue Schreibweise.",
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.ORGANIC,
    "Altpapier": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Schadstoffmobil in Ihrer Nähe": Icons.HAZARDOUS,
}

_BASE_URL = "https://abfallkalender.regioit.de/kalender-wml"
_ORT = "Gronau"
# Restmüll, Bioabfall, Altpapier, Gelbe Tonne, Schadstoffmobil (all types
# offered by the calendar; matches the defaults preselected on the site).
_FRAKTIONEN = ["0", "3", "4", "5", "11"]

_STREET_LIST_RE = re.compile(r"streetList\s*=\s*\{(.*?)\};", re.DOTALL)
_STREET_ENTRY_RE = re.compile(r'"((?:[^"\\]|\\.)*)"\s*:\s*(\d+)')


class Source:
    def __init__(self, street: str):
        self._street = street
        self._ics = ICS()

    def _get_street_id(self, session: requests.Session, year: int) -> str:
        r = session.get(
            f"{_BASE_URL}/index.jsp",
            params={
                "ort": _ORT,
                "jahr": str(year),
                "lang": "de",
                "format": "pdf",
                "zeit": "",
            },
        )
        r.raise_for_status()
        r.encoding = "utf-8"

        streets: dict[str, str] = {}
        match = _STREET_LIST_RE.search(r.text)
        if match:
            for name, street_id in _STREET_ENTRY_RE.findall(match.group(1)):
                streets[unescape(name)] = street_id

        if self._street not in streets:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, sorted(streets.keys())
            )

        return streets[self._street]

    def _fetch_year(
        self, session: requests.Session, year: int, street_id: str
    ) -> list[tuple]:
        r = session.get(
            f"{_BASE_URL}/downloadfile.jsp",
            params={
                "format": "ics",
                "zeit": "1:0:0",
                "jahr": str(year),
                "ort": _ORT,
                "strasse": street_id,
                "fraktion": _FRAKTIONEN,
            },
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        return self._ics.convert(r.text)

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        session = requests.Session()

        street_id = self._get_street_id(session, now.year)

        dates = self._fetch_year(session, now.year, street_id)
        if now.month >= 10:
            # Near year end: also pull next year so the 365-day lookahead
            # window used by the ICS conversion is fully covered.
            dates += self._fetch_year(session, now.year + 1, street_id)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], icon=ICON_MAP.get(d[1])))
        return entries
