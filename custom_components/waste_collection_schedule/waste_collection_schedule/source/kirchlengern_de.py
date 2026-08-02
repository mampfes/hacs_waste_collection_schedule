"""Source for Gemeinde Kirchlengern, Germany, waste collection."""

from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Gemeinde Kirchlengern"
DESCRIPTION = "Source for Gemeinde Kirchlengern, Germany, waste collection."
URL = "https://www.kirchlengern.de"
COUNTRY = "de"

TEST_CASES = {
    "Alter Postweg": {"strasse": "Alter Postweg"},
    "Am Bahnhof": {"strasse": "Am Bahnhof"},
    "Alter Markt": {"strasse": "Alter Markt"},
}

SOURCE_CODEOWNERS = ["@bbr111"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street name exactly as it appears in the waste calendar tool "
        "on the Kirchlengern website "
        "(Bürgerservice → Abfallkalender/Abfallberatung). If the street is not "
        "found, the error message lists all valid street names."
    ),
    "de": (
        "Geben Sie Ihren Straßennamen genau so ein, wie er im Abfallkalender-Tool "
        "auf der Webseite der Gemeinde Kirchlengern erscheint "
        "(Bürgerservice → Abfallkalender/Abfallberatung). Wird die Straße nicht "
        "gefunden, listet die Fehlermeldung alle gültigen Straßennamen auf."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {"strasse": "Street"},
    "de": {"strasse": "Straße"},
}

PARAM_DESCRIPTIONS = {
    "en": {"strasse": "Street name, e.g. 'Alter Postweg'."},
    "de": {"strasse": "Straßenname, z.B. 'Alter Postweg'."},
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biotonne": Icons.BIO_KITCHEN,
    "Papier": Icons.PAPER,
    "Gelbe Säcke": Icons.PLASTIC_PACKAGING,
    "Elektroschrott": Icons.ELECTRONICS,
    "Sondermüll": Icons.HAZARDOUS,
    "Sperrmüll": Icons.BULKY,
    "Hausratsammlung": Icons.BULKY,
}

BASE_URL = "https://www.kirchlengern.de"
SELECT_URL = (
    f"{BASE_URL}/Bürgerservice/Abfallkalender-Abfallberatung/index.php"
    "?set=fix&ort=393.2&call=sfm&La=1&sNavID=3158.35&mNavID=3158.3"
    "&ffmod=abf&ffsm=1"
)
ICS_URL = f"{BASE_URL}/output/abfall_export.php"

HEADERS = {
    "Referer": f"{BASE_URL}/",
    "User-Agent": "Mozilla/5.0",
}

SUMMARY_PREFIX = "_KI "
SUMMARY_SUFFIX = ": Kirchlengern"


def _fix_encoding(text: str, encoding: str) -> str:
    """Repair double-encoded text.

    The provider serves text that was UTF-8 encoded once and then encoded again
    as ``encoding``. Re-encoding the string with that encoding and decoding it as
    UTF-8 restores the original characters. If the round-trip fails (i.e. the text
    was already correct), the original string is returned unchanged.
    """
    try:
        return text.encode(encoding).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _match_icon(waste_type: str):
    for key, icon in ICON_MAP.items():
        if key in waste_type:
            return icon
    return None


class Source:
    def __init__(self, strasse: str):
        self._strasse: str = strasse

    def _get_street_id(self, session: requests.Session) -> str:
        r = session.get(SELECT_URL, headers=HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        select = soup.find("select", {"name": "strasse"})
        streets: dict[str, str] = {}
        if select:
            for option in select.find_all("option"):
                value = option.get("value")
                label = _fix_encoding(option.text.strip(), "latin-1")
                if not value or not label:
                    continue
                streets[label] = value

        for label, value in streets.items():
            if label.lower() == self._strasse.strip().lower():
                return value

        raise SourceArgumentNotFoundWithSuggestions(
            "strasse", self._strasse, sorted(streets.keys())
        )

    def _get_years(self, session: requests.Session, street_id: str) -> list[str]:
        r = session.get(SELECT_URL, headers=HEADERS, params={"strasse": street_id})
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        select = soup.find("select", {"name": "vJ"})
        years: list[str] = []
        if select:
            for option in select.find_all("option"):
                value = (option.get("value") or "").strip()
                if value.isdigit():
                    years.append(value)
        return years

    def _fetch_year(
        self, session: requests.Session, street_id: str, year: str
    ) -> list[tuple]:
        r = session.get(
            ICS_URL,
            headers=HEADERS,
            params={
                "csv_export": "1",
                "mode": "vcal",
                "ort": "393.2",
                "strasse": street_id,
                "vtyp": "2",
                "vMo": "01",
                "vJ": year,
                "bMo": "12",
            },
        )
        r.raise_for_status()

        results: list[tuple] = []
        calendar = Calendar.from_ical(r.text)
        for event in calendar.walk("VEVENT"):
            start = event.get("DTSTART")
            summary = event.get("SUMMARY")
            if start is None or summary is None:
                continue
            day = start.dt
            if isinstance(day, datetime):
                day = day.date()
            if not isinstance(day, date):
                continue

            waste_type = _fix_encoding(str(summary), "iso-8859-15")
            if waste_type.startswith(SUMMARY_PREFIX):
                waste_type = waste_type[len(SUMMARY_PREFIX) :]
            if waste_type.endswith(SUMMARY_SUFFIX):
                waste_type = waste_type[: -len(SUMMARY_SUFFIX)]
            waste_type = waste_type.strip()

            results.append((day, waste_type))
        return results

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        street_id = self._get_street_id(session)
        years = self._get_years(session, street_id)
        if not years:
            years = [str(datetime.now().year)]

        seen: set = set()
        entries: list[Collection] = []
        for year in years:
            for day, waste_type in self._fetch_year(session, street_id, year):
                key = (day, waste_type)
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    Collection(day, waste_type, icon=_match_icon(waste_type))
                )

        return entries
