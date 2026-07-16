import re
from datetime import datetime
from typing import Any

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Müllmann-App"
DESCRIPTION = (
    "Source for Müllmann-App, providing waste collection schedules for several "
    "municipalities around Lake Constance (Bodensee), Germany."
)
URL = "https://muellmann-app.de/"
COUNTRY = "de"

API_URL = "https://muellmann.gering.dev"
# Static API key extracted from the public Müllmann-App web client. It is not
# a per-user secret; every deployment of the app ships with the same key.
API_KEY = "fz2LM67Xurs1sXjmHEIAlhssIS1mBlf8"

EXTRA_INFO = [
    {
        "title": "Aach",
        "url": "https://aach.muellmann-app.de/",
        "default_params": {"city": "Aach"},
    },
    {
        "title": "Allensbach",
        "url": "https://allensbach.muellmann-app.de/",
        "default_params": {"city": "Allensbach"},
    },
    {
        "title": "Bodman-Ludwigshafen",
        "url": "https://bodman.muellmann-app.de/",
        "default_params": {"city": "Bodman-Ludwigshafen"},
    },
    {
        "title": "Gailingen am Hochrhein",
        "url": "https://gailingen.muellmann-app.de/",
        "default_params": {"city": "Gailingen am Hochrhein"},
    },
    {
        "title": "Hohenfels",
        "url": "https://hohenfels.muellmann-app.de/",
        "default_params": {"city": "Hohenfels"},
    },
    {
        "title": "Karlsruhe",
        "url": "https://karlsruhe.muellmann-app.de/",
        "default_params": {"city": "Karlsruhe", "street": "REPLACE_WITH_YOUR_STREET"},
    },
    {
        "title": "Konstanz",
        "url": "https://konstanz.muellmann-app.de/",
        "default_params": {"city": "Konstanz", "street": "REPLACE_WITH_YOUR_STREET"},
    },
    {
        "title": "Moos",
        "url": "https://moos.muellmann-app.de/",
        "default_params": {"city": "Moos"},
    },
    {
        "title": "Mühlhausen-Ehingen",
        "url": "https://muehlhausen.muellmann-app.de/",
        "default_params": {"city": "Mühlhausen-Ehingen"},
    },
    {
        "title": "Mühlingen",
        "url": "https://muehlingen.muellmann-app.de/",
        "default_params": {"city": "Mühlingen"},
    },
    {
        "title": "Orsingen-Nenzingen",
        "url": "https://orsingen.muellmann-app.de/",
        "default_params": {"city": "Orsingen-Nenzingen"},
    },
    {
        "title": "Radolfzell am Bodensee",
        "url": "https://radolfzell.muellmann-app.de/",
        "default_params": {
            "city": "Radolfzell",
            "street": "REPLACE_WITH_YOUR_STREET",
        },
    },
    {
        "title": "Reichenau",
        "url": "https://reichenau.muellmann-app.de/",
        "default_params": {"city": "Reichenau"},
    },
    {
        "title": "Singen (Hohentwiel)",
        "url": "https://singenah.muellmann-app.de/",
        "default_params": {
            "city": "Singen (Hohentwiel)",
            "street": "REPLACE_WITH_YOUR_STREET",
        },
    },
    {
        "title": "Stockach",
        "url": "https://stockach.muellmann-app.de/",
        "default_params": {"city": "Stockach", "street": "REPLACE_WITH_YOUR_STREET"},
    },
]

TEST_CASES = {
    "Radolfzell, Mooser Straße": {"city": "Radolfzell", "street": "Mooser Straße"},
    "Radolfzell, Mooser Str. (abbreviated)": {
        "city": "Radolfzell",
        "street": "Mooser Str.",
    },
    "Konstanz, Abendbergweg": {"city": "Konstanz", "street": "Abendbergweg"},
    "Aach (no street required)": {"city": "Aach"},
    "Radolfzell, Böhringer Straße (needs range_selector)": {
        "city": "Radolfzell",
        "street": "Böhringer Straße",
        "range_selector": "1_55",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the municipality name (see the source's supported places list). "
        "For municipalities with street-level schedules, also provide your street "
        "name. If your street is split into several collection areas, add the "
        "correct 'range_selector' value; the error message you get on first try "
        "will list the valid options for your street."
    ),
    "de": (
        "Geben Sie den Namen der Gemeinde ein (siehe Liste der unterstützten Orte "
        "dieser Quelle). Für Gemeinden mit straßengenauen Abfuhrterminen geben Sie "
        "zusätzlich Ihren Straßennamen an. Ist Ihre Straße in mehrere "
        "Abfuhrbereiche unterteilt, ergänzen Sie den passenden Wert für "
        "'range_selector'; die Fehlermeldung beim ersten Versuch listet die für "
        "Ihre Straße gültigen Werte auf."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "Municipality name, e.g. 'Radolfzell' or 'Konstanz'.",
        "street": (
            "Street name (only required for municipalities with street-level "
            "schedules, e.g. Karlsruhe, Konstanz, Radolfzell, Singen (Hohentwiel), "
            "Stockach)."
        ),
        "range_selector": (
            "Only needed if your street is split into several collection areas. "
            "Leave empty first; the error message will list the valid values for "
            "your street if one is required."
        ),
    },
    "de": {
        "city": "Name der Gemeinde, z. B. 'Radolfzell' oder 'Konstanz'.",
        "street": (
            "Straßenname (nur erforderlich für Gemeinden mit straßengenauen "
            "Abfuhrterminen, z. B. Karlsruhe, Konstanz, Radolfzell, Singen "
            "(Hohentwiel), Stockach)."
        ),
        "range_selector": (
            "Nur nötig, wenn Ihre Straße in mehrere Abfuhrbereiche unterteilt ist. "
            "Zunächst leer lassen; die Fehlermeldung listet die für Ihre Straße "
            "gültigen Werte auf, falls einer benötigt wird."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "Municipality",
        "street": "Street",
        "range_selector": "Range selector (advanced)",
    },
    "de": {
        "city": "Gemeinde",
        "street": "Straße",
        "range_selector": "Bereichs-Schlüssel (erweitert)",
    },
}


_UMLAUT_TABLE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _normalize(value: str) -> str:
    value = value.strip().lower().translate(_UMLAUT_TABLE)
    value = value.replace("strasse", "str").replace("str.", "str")
    return re.sub(r"[^a-z0-9]", "", value)


_ICON_KEYWORDS: list[tuple[str, Icons]] = [
    ("christbaum", Icons.CHRISTMAS_TREE),
    ("flohmarkt", Icons.EVENT),
    ("wertstoffhof", Icons.EVENT),
    ("info", Icons.EVENT),
    ("sperr", Icons.BULKY),
    ("altholz", Icons.BULKY),
    ("problem", Icons.HAZARDOUS),
    ("sondermuell", Icons.HAZARDOUS),
    ("schadstoff", Icons.HAZARDOUS),
    ("elektro", Icons.ELECTRONICS),
    ("eschrott", Icons.ELECTRONICS),
    ("kuehlgeraet", Icons.ELECTRONICS),
    ("tvgeraet", Icons.ELECTRONICS),
    ("altmetall", Icons.METAL),
    ("schrott", Icons.METAL),
    ("gruenschnitt", Icons.GARDEN),
    ("gruenabfall", Icons.GARDEN),
    ("haecksler", Icons.GARDEN),
    ("papier", Icons.PAPER),
    ("blaue tonne", Icons.PAPER),
    ("gelbe tonne", Icons.PLASTIC_PACKAGING),
    ("gelber sack", Icons.PLASTIC_PACKAGING),
    ("wertstoff", Icons.PLASTIC_PACKAGING),
    ("bio", Icons.ORGANIC),
    ("rest", Icons.GENERAL_WASTE),
]


def _icon_for(name: str) -> Icons | None:
    lowered = name.lower()
    for keyword, icon in _ICON_KEYWORDS:
        if keyword in lowered:
            return icon
    return None


class Source:
    def __init__(
        self,
        city: str,
        street: str | None = None,
        range_selector: str | None = None,
    ):
        self._city = city
        self._street = street
        self._range_selector = range_selector
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": API_KEY})

    def _get(self, path: str) -> Any:
        r = self._session.get(f"{API_URL}{path}", timeout=30)
        r.raise_for_status()
        return r.json()

    def _resolve_region(self) -> str:
        regions = self._get("/")
        target = _normalize(self._city)
        for region in regions:
            if target in (_normalize(region["name"]), _normalize(region["key"])):
                return str(region["key"])
        names = [region["name"] for region in regions]
        raise SourceArgumentNotFoundWithSuggestions("city", self._city, names)

    def _resolve_street(self, region_key: str) -> str | None:
        streets = self._get(f"/{region_key}/streets")
        if not streets:
            # This municipality has a single, region-wide collection schedule.
            return None

        if not self._street:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                f"the municipality '{self._city}' requires a street name to "
                "determine the correct collection schedule",
            )

        target = _normalize(self._street)
        for street in streets:
            if target in (_normalize(street["name"]), _normalize(street["key"])):
                return str(street["key"])

        names = [street["name"] for street in streets]
        raise SourceArgumentNotFoundWithSuggestions("street", self._street, names)

    def _resolve_range_selector(self, region_key: str, street_key: str) -> str:
        detail = self._get(f"/{region_key}/streets/{street_key}")
        ranges = detail.get("ranges") or []
        if not ranges:
            return "*"
        if len(ranges) == 1:
            return str(ranges[0]["selector"])

        if self._range_selector:
            for range_info in ranges:
                if range_info["selector"] == self._range_selector:
                    return str(range_info["selector"])
            valid = [range_info["selector"] for range_info in ranges]
            raise SourceArgumentNotFoundWithSuggestions(
                "range_selector", self._range_selector, valid
            )

        # The street is split into several house-number ranges and we cannot
        # safely guess which one applies, so ask the user to pick one.
        suggestions = [
            f"{range_info['selector']} ({range_info.get('name', '')} "
            f"{range_info.get('info', '')})".strip()
            for range_info in ranges
        ]
        raise SourceArgumentNotFoundWithSuggestions(
            "range_selector", self._range_selector, suggestions
        )

    def fetch(self) -> list[Collection]:
        region_key = self._resolve_region()
        street_key = self._resolve_street(region_key)

        if street_key is None:
            events = self._get(f"/{region_key}/events")
        else:
            range_selector = self._resolve_range_selector(region_key, street_key)
            events = self._get(f"/{region_key}/events/{street_key}/{range_selector}")

        types = {
            waste_type["key"]: waste_type["name"]
            for waste_type in self._get(f"/{region_key}/types")
        }

        entries = []
        for event in events:
            type_key = event["type"]
            name = types.get(type_key, type_key)
            date = datetime.strptime(event["date"], "%d.%m.%Y").date()
            entries.append(Collection(date=date, t=name, icon=_icon_for(name)))
        return entries
