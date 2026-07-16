import difflib
import io
import json
import re
import unicodedata
from datetime import date, timedelta

from curl_cffi import requests
from pdfminer.high_level import extract_text
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "SICTOM du Val de Saône"
DESCRIPTION = "Source for SICTOM du Val de Saône waste collection schedules in Haute-Saône, France."
URL = "https://www.sictomvds.com"
COUNTRY = "fr"
SOURCE_CODEOWNERS = ["@KingKemar"]

TEST_CASES = {
    "Velleminfroy": {"commune": "Velleminfroy"},
    "Ancier": {"commune": "Ancier"},
    "Mantoche": {"commune": "Mantoche"},
}

PARAM_TRANSLATIONS = {
    "en": {"commune": "Municipality"},
    "fr": {"commune": "Commune"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "commune": "Name of the municipality as shown on the SICTOM map (e.g. 'Velleminfroy')."
    },
    "fr": {
        "commune": "Nom de la commune tel qu'affiché sur la carte SICTOM (ex. 'Velleminfroy')."
    },
}

ICON_MAP = {
    "Ordures ménagères": Icons.GENERAL_WASTE,
    "Tri": Icons.RECYCLING,
}

_JS_URL = "https://www.sictomvds.com/map/image-map-pro.min.js"

# Only these three public holidays defer collection by one day; all others are worked normally.
_DEFERRED_HOLIDAYS = {(1, 1), (5, 1), (12, 25)}

_DAYS_FR = {
    "LUNDI": 0,
    "MARDI": 1,
    "MERCREDI": 2,
    "JEUDI": 3,
    "VENDREDI": 4,
    "SAMEDI": 5,
}


def _normalize(s: str) -> str:
    s = s.strip().casefold()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _normalize_text(text: str) -> str:
    """Strip accents from extracted PDF text for reliable regex matching."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _load_mapping(session) -> tuple[dict[str, str], list[str]]:
    """Return ({normalized_title: pdf_url}, [original_titles])."""
    r = session.get(_JS_URL)
    r.raise_for_status()
    # Locate the data call (second occurrence of imageMapPro)
    m = re.search(r"imageMapPro\((\{.*?\})\);", r.text[100_000:], re.DOTALL)
    if not m:
        raise ValueError("Could not locate imageMapPro config in JS")
    config = json.loads(m.group(1))
    mapping: dict[str, str] = {}
    titles: list[str] = []
    for spot in config.get("spots", []):
        title = spot.get("title", "")
        link = (spot.get("actions") or {}).get("link", "")
        if link.lower().endswith(".pdf"):
            mapping[_normalize(title)] = link
            titles.append(title)
    return mapping, titles


def _parse_schedule(pdf_bytes: bytes) -> list[tuple[str, int, int]]:
    """
    Return list of (waste_type, weekday, parity) parsed from a collection PDF.
    weekday: 0=Mon … 5=Sat. parity: 0=even ISO weeks (PAIRES), 1=odd (IMPAIRES).
    """
    raw_text = extract_text(io.BytesIO(pdf_bytes))
    text = _normalize_text(raw_text).upper()

    results = []

    # TRI (recyclables) — text example: "COLLECTES DU TRITOUS LES JEUDIS SEMAINES PAIRES"
    m_tri = re.search(
        r"COLLECTES\s+DU\s+TRI\s*(?:TOUS\s+LES\s+)?"
        r"(LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI)S?\s+SEMAINES?\s+(PAIRES|IMPAIRES)",
        text,
    )
    if m_tri:
        day = _DAYS_FR[m_tri.group(1)]
        parity = 0 if m_tri.group(2) == "PAIRES" else 1
        results.append(("Tri", day, parity))

    # Ordures ménagères — text example: "COLLECTES DES  ORDURES MENAGERES TOUS LES MERCREDIS SEMAINES PAIRES"
    m_om = re.search(
        r"COLLECTES\s+DES\s+ORDURES\s+MENAGERES\s*(?:TOUS\s+LES\s+)?"
        r"(LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI)S?\s+SEMAINES?\s+(PAIRES|IMPAIRES)",
        text,
    )
    if m_om:
        day = _DAYS_FR[m_om.group(1)]
        parity = 0 if m_om.group(2) == "PAIRES" else 1
        results.append(("Ordures ménagères", day, parity))

    return results


def _project_dates(weekday: int, parity: int, days: int = 365) -> list[date]:
    """Yield collection dates for the next `days` days matching weekday and ISO-week parity."""
    today = date.today()
    end = today + timedelta(days=days)
    days_ahead = (weekday - today.weekday()) % 7
    current = today + timedelta(days=days_ahead)
    result = []
    while current <= end:
        if current.isocalendar()[1] % 2 == parity:
            d = current
            if (d.month, d.day) in _DEFERRED_HOLIDAYS:
                d += timedelta(days=1)
            result.append(d)
        current += timedelta(weeks=1)
    return result


class Source:
    def __init__(self, commune: str):
        self._commune = commune
        self._session = requests.Session(impersonate="chrome")

    def fetch(self) -> list[Collection]:
        mapping, titles = _load_mapping(self._session)

        norm = _normalize(self._commune)
        if norm not in mapping:
            norm_titles = [_normalize(t) for t in titles]
            close = difflib.get_close_matches(norm, norm_titles, n=5, cutoff=0.5)
            suggestions = [titles[norm_titles.index(c)] for c in close]
            raise SourceArgumentNotFoundWithSuggestions(
                "commune", self._commune, suggestions
            )

        pdf_url = mapping[norm]
        r = self._session.get(pdf_url)
        r.raise_for_status()

        schedule = _parse_schedule(r.content)

        entries: list[Collection] = []
        for waste_type, weekday, parity in schedule:
            for d in _project_dates(weekday, parity):
                entries.append(Collection(d, waste_type, icon=ICON_MAP.get(waste_type)))

        return entries
