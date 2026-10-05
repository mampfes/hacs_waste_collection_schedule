import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, field_terms, regions, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://muellmann.gering.dev"
# Public API key shipped with the provider's web client.
HEADERS = {"X-API-Key": "fz2LM67Xurs1sXjmHEIAlhssIS1mBlf8"}


def _normalize(value):
    value = (
        value.strip()
        .lower()
        .translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    )
    value = value.replace("strasse", "str").replace("str.", "str")
    return re.sub(r"[^a-z0-9]", "", value)


def _region_key(response, *, city, **_):
    entries = response.json()
    for entry in entries:
        if _normalize(city) in (_normalize(entry["name"]), _normalize(entry["key"])):
            return str(entry["key"])
    raise SourceArgumentNotFoundWithSuggestions(
        "city", city, [entry["name"] for entry in entries]
    )


def _street_key(response, *_, city, street=None, **kwargs):
    entries = response.json()
    if not entries:
        return None
    if not street:
        raise SourceArgumentNotFound(
            "street",
            street,
            f"the municipality '{city}' requires a street name to determine the correct collection schedule",
        )
    for entry in entries:
        if _normalize(street) in (_normalize(entry["name"]), _normalize(entry["key"])):
            return str(entry["key"])
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, [entry["name"] for entry in entries]
    )


def _range(response, *_, range_selector=None, **kwargs):
    ranges = response.json().get("ranges") or []
    if not ranges:
        return "*"
    if len(ranges) == 1:
        return str(ranges[0]["selector"])
    if range_selector:
        for entry in ranges:
            if entry["selector"] == range_selector:
                return str(entry["selector"])
        suggestions = [entry["selector"] for entry in ranges]
    else:
        suggestions = [
            f"{entry['selector']} ({entry.get('name', '')} {entry.get('info', '')})".strip()
            for entry in ranges
        ]
    raise SourceArgumentNotFoundWithSuggestions(
        "range_selector", range_selector, suggestions
    )


def _types(response, *_, **kwargs):
    return {entry["key"]: entry["name"] for entry in response.json()}


def _events_url(region_key, street_key, selector, types, **_):
    if street_key is None:
        return f"{API_URL}/{region_key}/events"
    return f"{API_URL}/{region_key}/events/{street_key}/{selector}"


def _events(response, region_key, street_key, selector, types, **_):
    return [
        (event["date"], types.get(event["type"], event["type"]))
        for event in response.json()
    ]


def _clean(label):
    normalized = _normalize(label)
    for keyword, key in (
        ("christbaum", "garden"),
        ("flohmarkt", "event"),
        ("wertstoffhof", "event"),
        ("info", "event"),
        ("sperr", "bulky"),
        ("altholz", "bulky"),
        ("problem", "hazardous"),
        ("sondermuell", "hazardous"),
        ("schadstoff", "hazardous"),
        ("elektro", "electronics"),
        ("eschrott", "electronics"),
        ("kuehlgeraet", "electronics"),
        ("tvgeraet", "electronics"),
        ("altmetall", "metal"),
        ("schrott", "metal"),
        ("gruenschnitt", "garden"),
        ("gruenabfall", "garden"),
        ("haecksler", "garden"),
        ("papier", "paper"),
        ("blauetonne", "paper"),
        ("gelbetonne", "recyclables"),
        ("gelbersack", "recyclables"),
        ("wertstoff", "recyclables"),
        ("bio", "organic"),
        ("rest", "general"),
    ):
        if keyword in normalized:
            return label if key in ("event", "metal") else key
    return label


@final
class Source(BaseSource):
    TITLE = "Müllmann-App"
    DESCRIPTION = (
        "Source for Müllmann-App, providing waste collection schedules for several "
        "municipalities around Lake Constance (Bodensee), Germany."
    )
    URL = "https://muellmann-app.de/"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
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
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Enter the municipality name (see the source's supported places list). For "
        "municipalities with street-level schedules, also provide your street name. If "
        "your street is split into several collection areas, add the correct "
        "'range_selector' value; the error message you get on first try will list the "
        "valid options for your street.",
        "de": "Geben Sie den Namen der Gemeinde ein (siehe Liste der unterstützten Orte "
        "dieser Quelle). Für Gemeinden mit straßengenauen Abfuhrterminen geben Sie "
        "zusätzlich Ihren Straßennamen an. Ist Ihre Straße in mehrere Abfuhrbereiche "
        "unterteilt, ergänzen Sie den passenden Wert für 'range_selector'; die "
        "Fehlermeldung beim ersten Versuch listet die für Ihre Straße gültigen Werte "
        "auf.",
    }
    RAISE_ON_EMPTY = True

    PARAMS = (
        text_field("city", term=field_terms.MUNICIPALITY),
        text_field("street", term=field_terms.STREET, optional=True),
        text_field("range_selector", term=field_terms.AREA_ID, optional=True),
    )
    REGIONS = regions.from_yaml("muellmann_app_de", city="city", street="street")
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Street required": {"city": "Konstanz"},
        "Range required": {"city": "Radolfzell", "street": "Böhringer Straße"},
        "Unknown range": {
            "city": "Radolfzell",
            "street": "Böhringer Straße",
            "range_selector": "__unknown_range__",
        },
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.ELECTRONICS,
        wt.OTHER,
    ]
    retrieve = retrievers.Chain(
        retrievers.Lookup(f"{API_URL}/", headers=HEADERS, pick=_region_key),
        retrievers.Lookup(
            lambda region_key, **_: f"{API_URL}/{region_key}/streets",
            headers=HEADERS,
            pick=_street_key,
        ),
        retrievers.Lookup(
            lambda region_key, street_key, **_: (
                f"{API_URL}/{region_key}/streets/{street_key}"
            ),
            headers=HEADERS,
            pick=_range,
            when=lambda region_key, street_key, **_: street_key is not None,
        ),
        retrievers.Lookup(
            lambda region_key, *_, **kwargs: f"{API_URL}/{region_key}/types",
            headers=HEADERS,
            pick=_types,
        ),
        retrievers.Lookup(_events_url, headers=HEADERS, pick=_events),
    )
    parse = staticmethod(lambda keys, source: keys[-1])
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        clean=_clean,
        type_value_map={
            "Altmetall": wt.OTHER,
            "general": wt.GENERAL_WASTE,
            "organic": wt.ORGANIC,
            "paper": wt.PAPER,
            "recyclables": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
            "bulky": wt.BULKY_WASTE,
            "hazardous": wt.HAZARDOUS,
            "electronics": wt.ELECTRONICS,
        },
        carry_raw_label=True,
    )
