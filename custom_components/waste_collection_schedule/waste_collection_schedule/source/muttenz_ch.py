"""Source for Gemeinde Muttenz, Switzerland."""

import html
import json
import re
from datetime import date, datetime, timedelta
from io import BytesIO

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from pypdf import PdfReader
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Gemeinde Muttenz"
DESCRIPTION = "Source for waste collection services in Muttenz, Switzerland."
URL = "https://www.muttenz.ch"
COUNTRY = "ch"

# Public events table (town-wide special collections, e.g. Papiersammlung,
# Gruenabfuhr, Kunststoffsammlung, ...). No login/address needed.
EVENTS_URL = "https://www.muttenz.ch/abfalldaten"

# The regular household/commercial refuse collection ("Haus- und
# Gewerbekehrichtabfuhr") is *not* published as a list of dates. It runs
# once a week, on a weekday that depends on where in Muttenz an address is
# (currently a simple north/south split around Prattelerstrasse /
# St.-Jakob-Strasse, described in the yearly "Abfallkalender" PDF).
#
# That weekday/zone split is intentionally *not* hardcoded in this module:
# it is discovered fresh on every fetch() by resolving the "Aktueller
# Abfallkalender" link on this stable info page (the PDF's own filename
# changes every year) and parsing the current document. If the municipality
# ever changes which weekday(s) apply, or restructures the document, fetch()
# raises instead of silently returning stale dates.
INFO_PAGE_URL = "https://www.muttenz.ch/_rte/regelmaessigeranlass/855"

WEEKDAY_RRULE = {
    "Montag": MO,
    "Dienstag": TU,
    "Mittwoch": WE,
    "Donnerstag": TH,
    "Freitag": FR,
    "Samstag": SA,
    "Sonntag": SU,
}
GERMAN_WEEKDAYS = list(WEEKDAY_RRULE.keys())

# TEST_CASES reflect the weekdays currently listed in the live Abfallkalender
# (verified at implementation time). fetch() re-validates this on every run
# against the current document, so if Muttenz ever changes this split, the
# test cases (and any existing user configuration using them) will start
# raising a clear error instead of silently returning wrong dates.
TEST_CASES = {
    "Dienstag": {"zone": "Dienstag"},
    "Mittwoch": {"zone": "Mittwoch"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "The regular household/commercial refuse collection ('Haus- und "
        "Gewerbekehrichtabfuhr') runs once a week, on a fixed German "
        "weekday that depends on where in Muttenz you live. This source "
        "fetches the current official 'Abfallkalender' on every update and "
        "reads the weekday(s) it lists there directly, rather than "
        "assuming a fixed split. Check the official calendar linked from "
        "https://www.muttenz.ch/abfalldaten to find out which weekday "
        "applies to your address, then enter that German weekday name "
        "(e.g. 'Dienstag' or 'Mittwoch') here."
    ),
    "de": (
        "Die reguläre Haus- und Gewerbekehrichtabfuhr erfolgt einmal pro "
        "Woche an einem fixen Wochentag, der davon abhängt, wo in Muttenz "
        "Sie wohnen. Diese Quelle lädt bei jeder Aktualisierung den "
        "aktuellen offiziellen Abfallkalender und liest die dort "
        "aufgeführten Wochentage direkt aus, anstatt eine feste Aufteilung "
        "anzunehmen. Den für Ihre Adresse zutreffenden Wochentag finden "
        "Sie im offiziellen Abfallkalender, verlinkt ab "
        "https://www.muttenz.ch/abfalldaten. Geben Sie diesen Wochentag "
        "(z.B. 'Dienstag' oder 'Mittwoch') hier ein."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {"zone": "Collection weekday"},
    "de": {"zone": "Abfuhrtag"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": (
            "The German weekday name of your regular refuse collection day "
            "(e.g. 'Dienstag' or 'Mittwoch'), as currently shown for your "
            "address in the official Abfallkalender. Re-validated against "
            "the live calendar on every update."
        )
    },
    "de": {
        "zone": (
            "Der deutsche Wochentagsname Ihres regulären "
            "Kehrichtabfuhrtags (z.B. 'Dienstag' oder 'Mittwoch'), wie er "
            "aktuell für Ihre Adresse im offiziellen Abfallkalender "
            "aufgeführt ist. Wird bei jeder Aktualisierung gegen den "
            "aktuellen Kalender neu validiert."
        )
    },
}

# Regular weekly refuse collection label.
KEHRICHT_LABEL = "Kehrichtabfuhr"

# How far into the future to generate the weekly recurring Kehrichtabfuhr.
WEEKLY_HORIZON_DAYS = 365

_ICON_KEYWORDS = {
    "kehricht": Icons.GENERAL_WASTE,
    "papier": Icons.PAPER,
    "gruen": Icons.GARDEN,
    "grün": Icons.GARDEN,
    "kunststoff": Icons.PLASTIC_PACKAGING,
    "altmetall": Icons.METAL,
    "haeckel": Icons.GARDEN,
    "häcksel": Icons.GARDEN,
    "sonderabfall": Icons.HAZARDOUS,
    "weihnachtsbaum": Icons.CHRISTMAS_TREE,
    "umwelttag": Icons.EVENT,
}

_TAG_RE = re.compile(r"<[^>]+>")
_DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
_DATA_ENTITIES_RE = re.compile(r'data-entities="([^"]*)"')

# Finds the link to the *current* year's Abfallkalender PDF on the stable
# info page. Deliberately does not hardcode any filename/year.
_CALENDAR_LINK_RE = re.compile(
    r'href="([^"]+\.pdf)"[^>]*>\s*Aktueller(?:&nbsp;|\s)+Abfallkalender',
    re.IGNORECASE,
)

# Isolates the "Haus- und Gewerbekehricht" info block in the extracted PDF
# text, up to the start of the next bin-type paragraph.
_KEHRICHT_BLOCK_RE = re.compile(
    r"Haus-\s*und\s*Gewerbekehricht(.*?)(?:\n(?:Grünabfuhr|Altmetallabfuhr|Papier)\s)",
    re.DOTALL,
)

_WEEKDAY_ALTERNATION = "|".join(GERMAN_WEEKDAYS)
_WEEKDAY_PAIR_RE = re.compile(
    rf"({_WEEKDAY_ALTERNATION}):\s*(.+?)(?=(?:{_WEEKDAY_ALTERNATION}):|\Z)",
    re.DOTALL,
)


def _strip_tags(value: str) -> str:
    return _TAG_RE.sub("", value).strip()


def _normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _icon_for(name: str) -> Icons | None:
    lname = name.lower()
    for keyword, icon in _ICON_KEYWORDS.items():
        if keyword in lname:
            return icon
    return None


def _current_kehricht_zones() -> dict[str, str]:
    """Discover this year's Kehrichtabfuhr weekday/zone split live.

    Resolves the "Aktueller Abfallkalender" PDF link from the stable info
    page (the PDF's own URL changes every year, so it is never hardcoded),
    downloads it, and parses the weekday -> area-description pairs from the
    "Haus- und Gewerbekehricht" section. Raises a clear error if the
    document structure no longer matches what this source expects, instead
    of silently falling back to a hardcoded assumption.
    """
    info_response = requests.get(INFO_PAGE_URL, timeout=30)
    info_response.raise_for_status()

    link_match = _CALENDAR_LINK_RE.search(info_response.text)
    if not link_match:
        raise Exception(
            "Could not find the 'Aktueller Abfallkalender' link on "
            f"{INFO_PAGE_URL}. The Muttenz website structure may have "
            "changed; please open an issue at "
            "https://github.com/mampfes/hacs_waste_collection_schedule/issues."
        )
    pdf_url = html.unescape(link_match.group(1))

    pdf_response = requests.get(pdf_url, timeout=30)
    pdf_response.raise_for_status()

    reader = PdfReader(BytesIO(pdf_response.content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    block_match = _KEHRICHT_BLOCK_RE.search(text)
    if not block_match:
        raise Exception(
            "Could not find the 'Haus- und Gewerbekehricht' section in the "
            f"current Abfallkalender ({pdf_url}). The document layout may "
            "have changed; please open an issue at "
            "https://github.com/mampfes/hacs_waste_collection_schedule/issues."
        )

    zones = {
        day: _normalize_ws(desc)
        for day, desc in _WEEKDAY_PAIR_RE.findall(block_match.group(1))
    }
    if not zones:
        raise Exception(
            "Could not parse any weekday/zone entries from the current "
            f"Abfallkalender ({pdf_url}). The document layout may have "
            "changed; please open an issue at "
            "https://github.com/mampfes/hacs_waste_collection_schedule/issues."
        )
    return zones


class Source:
    def __init__(self, zone: str):
        if not isinstance(zone, str) or not zone.strip():
            raise SourceArgumentNotFoundWithSuggestions(
                "zone", zone, suggestions=GERMAN_WEEKDAYS
            )
        # Normalise casing (e.g. "dienstag" -> "Dienstag") but do not
        # validate against a hardcoded list here -- validity depends on the
        # live document and is checked in fetch().
        self._zone = zone.strip().capitalize()

    def fetch(self) -> list[Collection]:
        entries: list[Collection] = []

        # 1. Regular weekly household/commercial refuse collection. The
        # weekday/zone split is fetched and parsed fresh from the current
        # official Abfallkalender on every call.
        current_zones = _current_kehricht_zones()
        if self._zone not in current_zones:
            raise SourceArgumentNotFoundWithSuggestions(
                "zone",
                self._zone,
                suggestions=list(current_zones.keys()),
            )

        weekday = WEEKDAY_RRULE[self._zone]
        zone_description = current_zones[self._zone]

        today = date.today()
        for occurrence in rrule(
            WEEKLY,
            byweekday=weekday,
            dtstart=today,
            until=today + timedelta(days=WEEKLY_HORIZON_DAYS),
        ):
            entries.append(
                Collection(
                    date=occurrence.date(),
                    t=KEHRICHT_LABEL,
                    icon=_icon_for(KEHRICHT_LABEL),
                    description=zone_description,
                )
            )

        # 2. Town-wide special collections (Papier, Grünabfuhr,
        # Kunststoffsammlung, Altmetallabfuhr, Häckseltag,
        # Sonderabfallsammlung, Weihnachtsbaumabfuhr, Umwelttag) are
        # published as an events table on the official webpage and do not
        # depend on the collection zone.
        response = requests.get(EVENTS_URL, timeout=30)
        response.raise_for_status()

        for match in _DATA_ENTITIES_RE.findall(response.text):
            try:
                data = json.loads(html.unescape(match))
            except json.JSONDecodeError:
                continue

            for item in data.get("data", []):
                if "_anlassDate" not in item or "name" not in item:
                    continue

                name = _strip_tags(item["name"])
                date_matches = _DATE_RE.findall(item.get("_anlassDate", ""))
                if not name or not date_matches:
                    continue

                try:
                    collection_date = datetime.strptime(
                        date_matches[0], "%d.%m.%Y"
                    ).date()
                except ValueError:
                    continue

                entries.append(
                    Collection(
                        date=collection_date,
                        t=name,
                        icon=_icon_for(name),
                    )
                )

        return entries
