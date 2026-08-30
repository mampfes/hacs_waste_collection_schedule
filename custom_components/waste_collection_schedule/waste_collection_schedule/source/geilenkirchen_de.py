import html
import re
from datetime import date

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Stadt Geilenkirchen"
DESCRIPTION = "Source for the waste collection calendar of the city of Geilenkirchen, North Rhine-Westphalia, Germany."
URL = "https://www.geilenkirchen.de"
COUNTRY = "de"

BASE_URL = "https://www.geilenkirchen.de"
CALENDAR_URL = (
    f"{BASE_URL}/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/"
)

TEST_CASES = {
    "Aldenhovener Strasse": {"street": "Aldenhovener Strasse"},
    "Ahornweg": {"street": "Ahornweg"},
}

SOURCE_CODEOWNERS = ["@bbr111"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit the collection calendar at "
        "https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/ "
        "and use the street search box there to find the exact spelling of your street "
        "(streets are spelled with 'strasse', not 'straße'). Use that exact name as the "
        "'street' argument. If the name you enter cannot be found, or matches more than "
        "one street, the resulting error message lists the closest matches."
    ),
    "de": (
        "Besuchen Sie den Abfallkalender unter "
        "https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/ "
        "und nutzen Sie dort die Straßensuche, um die genaue Schreibweise Ihrer Straße zu "
        "finden (Straßen werden mit 'strasse' statt 'straße' geschrieben). Verwenden Sie "
        "diesen genauen Namen als 'street'-Parameter. Wird der eingegebene Name nicht "
        "gefunden oder trifft auf mehrere Straßen zu, listet die Fehlermeldung die "
        "passendsten Treffer auf."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": (
            "Street name as shown on "
            "https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/, "
            "e.g. 'Aldenhovener Strasse'."
        ),
    },
    "de": {
        "street": (
            "Straßenname wie auf "
            "https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/ "
            "angezeigt, z. B. 'Aldenhovener Strasse'."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
    },
    "de": {
        "street": "Straße",
    },
}


ICON_MAP = {
    "Restabfallcontainer": Icons.GENERAL_WASTE,
    "Restabfall": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.ORGANIC,
    "Leichtverpackungen": Icons.PLASTIC_PACKAGING,
    "Altpapier": Icons.PAPER,
    "Grünschnittabfuhr": Icons.GARDEN,
}

MONTHS_DE = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

DATE_PATTERN = re.compile(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s*(\d{4})")

ROW_PATTERN = re.compile(
    r'<div class="tablerow">(.*?)<div class="clear"></div>\s*</div>', re.S
)
DATE_CELL_PATTERN = re.compile(r'<div class="col col-1">\s*([^<]+?)\s*</div>')
TYPE_LINK_PATTERN = re.compile(r"<a data-fancybox[^>]*>\s*([^<]+?)\s*</a>")
RESULT_LINK_PATTERN = re.compile(
    r'<h3><a href="([^"]*/abfallkalender/details/[^"]+)">\s*([^<]+?)\s*</a></h3>'
)


def _normalize(value: str) -> str:
    value = html.unescape(value).strip().lower()
    value = value.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]", "", value)


class Source:
    def __init__(self, street: str):
        self._street = street
        self._session = requests.Session()

    def _search_streets(self, term: str) -> list[tuple[str, str]]:
        """Return list of (display_name, absolute_detail_url) matching the search term."""
        r = self._session.post(
            CALENDAR_URL, data={"module1428[search]": term}, timeout=30
        )
        r.raise_for_status()
        results = []
        for href, name in RESULT_LINK_PATTERN.findall(r.text):
            url = href if href.startswith("http") else BASE_URL + href
            results.append((html.unescape(name), url))
        return results

    def _resolve_street(self) -> str:
        target = _normalize(self._street)

        results = self._search_streets(self._street)
        if not results:
            # Retry with the common German spelling variant ("ß" -> "ss"),
            # since the city always spells "Strasse" without an "ß".
            fallback_term = self._street.replace("ß", "ss").replace("straße", "strasse")
            if fallback_term != self._street:
                results = self._search_streets(fallback_term)

        if not results and " " in self._street.strip():
            # Retry with just the first word, to surface suggestions.
            results = self._search_streets(self._street.strip().split()[0])

        for name, url in results:
            if _normalize(name) == target:
                return url

        if len(results) == 1:
            return results[0][1]

        suggestions = sorted({name for name, _ in results})
        raise SourceArgumentNotFoundWithSuggestions("street", self._street, suggestions)

    def _parse_date(self, text: str) -> date | None:
        match = DATE_PATTERN.search(text)
        if not match:
            return None
        day, month_name, year = match.groups()
        month = MONTHS_DE.get(month_name.lower())
        if month is None:
            return None
        return date(int(year), month, int(day))

    def fetch(self) -> list[Collection]:
        detail_url = self._resolve_street()

        r = self._session.post(
            detail_url,
            data={
                "module1432[types][]": "0",  # "alle" (all waste types)
                "module1432[timeframe]": "3",  # "bis zum Jahresende" (until year end)
            },
            timeout=30,
        )
        r.raise_for_status()

        entries = []
        for row in ROW_PATTERN.findall(r.text):
            date_match = DATE_CELL_PATTERN.search(row)
            type_match = TYPE_LINK_PATTERN.search(row)
            if not date_match or not type_match:
                continue

            collection_date = self._parse_date(date_match.group(1))
            if collection_date is None:
                continue

            waste_type = html.unescape(type_match.group(1)).strip()

            icon = None
            for key, mapped_icon in ICON_MAP.items():
                if key in waste_type:
                    icon = mapped_icon
                    break

            entries.append(Collection(date=collection_date, t=waste_type, icon=icon))

        return entries
