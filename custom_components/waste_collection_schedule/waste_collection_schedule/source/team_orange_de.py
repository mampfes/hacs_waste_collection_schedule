"""Waste collection schedules for team orange (Landkreis Würzburg).
Reverse-engineered from the athos WasteManagementServlet behind the Regiogate
CMS wrapper (https://www.team-orange.info/muellabfuhr/abfallkalender/).
Modeled on source/regioentsorgung_de.py (same com.athos servlet family).
"""

import re
from html.parser import HTMLParser

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Team Orange (Landkreis Würzburg)"
DESCRIPTION = "Source for team orange waste collection in Landkreis Würzburg."
URL = "https://www.team-orange.info"
COUNTRY = "de"
TEST_CASES = {
    "Altertheim": {"ort": "Altertheim", "strasse": "Am Berg", "hausnummer": 1},
    "Reichenberg (Rathaus)": {
        "ort": "Reichenberg",
        "strasse": "Kirchgasse",
        "hausnummer": 5,
    },
}

SOURCE_CODEOWNERS = ["@ChrisKoh83"]

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "de": "Ort, Straße und Hausnummer entnehmen Sie bitte dem "
    "Abfallkalender auf https://www.team-orange.info/muellabfuhr/abfallkalender/.",
    "en": "Please take Ort (municipality), Strasse (street) and Hausnummer "
    "(street number) from the calendar at "
    "https://www.team-orange.info/muellabfuhr/abfallkalender/.",
}

PARAM_DESCRIPTIONS = {
    "de": {
        "ort": "Ort (Gemeinde im Landkreis Würzburg)",
        "strasse": "Straße",
        "hausnummer": "Hausnummer",
    },
    "en": {
        "ort": "Municipality in Landkreis Würzburg",
        "strasse": "Street",
        "hausnummer": "Street number",
    },
}

# Waste types like "Restmüll 02-wöchentl." or
# "Problemmüll 13-16 Uhr Wertstoffhof Klingholz" — match by substring.
ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Papier": Icons.PAPER,
    "Bioabfall": Icons.ORGANIC,
    "Gelbe Tonne": Icons.RECYCLING,
    "LVP": Icons.RECYCLING,
    "Problemmüll": Icons.HAZARDOUS,
    "Elektro": Icons.ELECTRONICS,
    "Schrott": Icons.METAL,
}


def _get_icon(waste_type: str):
    for key, icon in ICON_MAP.items():
        if key in waste_type:
            return icon
    return None


# The calendar app is an iframe into the classic athos servlet (not Regiogate) —
# that is why no JS/browser automation is required.
API_URL = (
    "https://athosweb.team-orange.info/WasteManagementWuerzburg/WasteManagementServlet"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)",
}

PARAM_TRANSLATIONS = {
    "de": {
        "ort": "Ort",
        "strasse": "Straße",
        "hausnummer": "Hausnummer",
    },
}


class FormStateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.select_options = {}
        self._current_select = None
        self._current_option_value = None
        self._current_option_text = []

    def _finalize_option(self):
        if self._current_select is None or self._current_option_value is None:
            return
        # athos serves HTML entities and non-breaking spaces
        text = " ".join(part.strip() for part in self._current_option_text).strip()
        text = text.replace("\xa0", " ")
        self.select_options[self._current_select].append(
            (self._current_option_value, text)
        )
        self._current_option_value = None
        self._current_option_text = []

    def finalize(self):
        self._finalize_option()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "select" and "name" in attributes:
            self._finalize_option()
            self._current_select = attributes["name"]
            self.select_options.setdefault(self._current_select, [])
        elif tag == "option" and self._current_select is not None:
            self._finalize_option()
            self._current_option_value = attributes.get("value", "")
            self._current_option_text = []

    def handle_data(self, data):
        if self._current_option_value is not None:
            self._current_option_text.append(data)

    def handle_endtag(self, tag):
        if tag == "option":
            self._finalize_option()
        elif tag == "select":
            self._finalize_option()
            self._current_select = None

    def get_options(self, field_name):
        return [
            text or value
            for value, text in self.select_options.get(field_name, [])
            if (text or value)
        ]


def parse_form_state(content):
    parser = FormStateParser()
    parser.feed(content)
    parser.finalize()
    parser.close()
    return parser


def normalize_option_value(value):
    return " ".join(str(value).split()).casefold()


def resolve_option(field_name, value, options):
    if value in options:
        return value

    normalized_options = {normalize_option_value(option): option for option in options}
    normalized_value = normalize_option_value(value)

    if normalized_value in normalized_options:
        return normalized_options[normalized_value]

    if options:
        raise SourceArgumentNotFoundWithSuggestions(field_name, value, options)
    raise SourceArgumentNotFound(
        field_name,
        value,
        "please check the other address arguments and try again.",
    )


def _hidden_value(text, name):
    # Tolerate optional whitespace around "=" and either attribute order
    # (name before value, or value before name), as the servlet HTML may vary.
    pattern = re.compile(
        rf'(?:name\s*=\s*["\']?{re.escape(name)}["\']?[^>]*?value\s*=\s*["\']([^"\']*)["\']'
        rf'|value\s*=\s*["\']([^"\']*)["\'][^>]*?name\s*=\s*["\']?{re.escape(name)}["\']?)',
        re.I,
    )
    m = pattern.search(text)
    return (m.group(1) or m.group(2)) if m else ""


def _session_state(text):
    """Extract SessionId/ApplicationName, failing fast if either is missing."""
    sid = _hidden_value(text, "SessionId")
    app = _hidden_value(text, "ApplicationName")
    if not sid or not app:
        raise SourceArgumentNotFound(
            "SessionId" if not sid else "ApplicationName",
            "<Antwort des Abfallkalenders>",
            "Die Antwort des Athos-Servlets enthält keine gültige Sitzung. "
            "Möglicherweise hat sich die Website von team orange geändert.",
        )
    return sid, app


class Source:
    def __init__(self, ort, strasse, hausnummer):
        self.ort = ort
        self.strasse = strasse
        self.hausnummer = str(hausnummer)
        self._ics = ICS()

    def _post(self, session, sid, app, action, ort, strasse, hausnummer):
        data = {
            "ApplicationName": app,
            "SessionId": sid,
            "SubmitAction": action,
            "Ort": ort,
            "Strasse": strasse,
            "Hausnummer": hausnummer,
            "InFrameMode": "TRUE",
        }
        r = session.post(API_URL, data=data)
        r.raise_for_status()
        r.encoding = "utf-8"
        return r

    def fetch(self):
        session = requests.Session()
        session.headers.update(HEADERS)

        # Step 1: initial page -> Ort list
        r = session.get(
            API_URL,
            params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        ort = resolve_option(
            "ort", self.ort, parse_form_state(r.text).get_options("Ort")
        )
        sid, app = _session_state(r.text)

        # Step 2: pick Ort -> Strasse list
        r = self._post(session, sid, app, "CITYCHANGED", ort, "", "")
        strasse = resolve_option(
            "strasse", self.strasse, parse_form_state(r.text).get_options("Strasse")
        )
        sid, app = _session_state(r.text)

        # Step 3: pick Strasse -> Hausnummer list
        r = self._post(session, sid, app, "STREETCHANGED", ort, strasse, "")
        hausnummer = resolve_option(
            "hausnummer",
            self.hausnummer,
            parse_form_state(r.text).get_options("Hausnummer"),
        )
        sid, app = _session_state(r.text)

        # Step 4: forward -> Terminliste (offers ical / pdf download)
        r = self._post(session, sid, app, "forward", ort, strasse, hausnummer)
        r.raise_for_status()
        sid, app = _session_state(r.text)

        # Step 5: download the iCal file (per-address, generated on demand)
        data = {
            "ApplicationName": app,
            "SessionId": sid,
            "SubmitAction": "filedownload_ICAL",
            "InFrameMode": "TRUE",
            "ICalErinnerung": "keine Erinnerung",
            "Ort": ort,
            "Strasse": strasse,
            "Hausnummer": hausnummer,
        }
        r = session.post(API_URL, data=data)
        r.raise_for_status()

        entries = [
            Collection(date, type_, icon=_get_icon(type_))
            for date, type_ in self._ics.convert(r.text)
        ]
        # The servlet returns events in varying order across requests; sort for
        # deterministic output (required by the -d double-fetch test).
        entries.sort(key=lambda c: (c.date, c.type))
        return entries
