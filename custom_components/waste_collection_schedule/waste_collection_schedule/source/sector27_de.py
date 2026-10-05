"""Sector 27 Müllkalender (muellkalender.sector27.de), Kreis Recklinghausen.

Each town has an ``idCity`` and a ``licenseKey`` that the public calendar
widget ships with; they are kept here because the fetch needs them. A street
name resolves to a street id (``searchForStreets``), and ``fetchPickups`` then
answers one calendar year per request, rolling into next year from September.
Both endpoints answer JSONP (``callbackFunc({...});``), which ``_jsonp``
unwraps.
"""

import datetime
import json
import re
from typing import ClassVar, final
from zoneinfo import ZoneInfo

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

_BASE_URL = "https://muellkalender.sector27.de/web"

_CITIES = {
    "Datteln": {"idCity": 9, "licenseKey": "DTTLN20137REKE382EHSE"},
    "Marl": {"idCity": 3, "licenseKey": "MRL3102HBBUHENWIP"},
    "Oer-Erkenschwick": {"idCity": 8, "licenseKey": "OSC1115KREHDFESEK"},
}

_TZ = ZoneInfo("Europe/Berlin")
_JSONP_RE = re.compile(r"callbackFunc\((.*)\);", re.DOTALL)


def _jsonp(text: str):
    match = _JSONP_RE.fullmatch(text.strip())
    return json.loads(match.group(1) if match else text)


def _city(city: str) -> dict:
    if city not in _CITIES:
        raise SourceArgumentNotFoundWithSuggestions("city", city, list(_CITIES))
    return _CITIES[city]


def _search_term(street: str) -> str:
    """The street without a house-number range ("Ahsener Straße 113 - 161 (ungerade)").

    The search matches a substring and answers at most ten streets; a range
    suffix makes it match nothing, so it is cut at the first " -", " (" or ";".
    """
    return re.split(r"\s+[-(;]", street.strip())[0]


def _street_params(*, city: str, street: str, **_) -> dict:
    return {**_city(city), "searchFor": _search_term(street)}


def _pick_street(response, *, street: str, **_) -> int:
    target = street.strip().casefold()
    names: list[str] = []
    for entry in _jsonp(response.text):
        name = entry.get("name", "").strip()
        if name.casefold() == target:
            return entry["id"]
        if name:
            names.append(name)
    if names:
        raise SourceArgumentNotFoundWithSuggestions("street", street, names)
    raise SourceArgumentNotFound("street", street)


def _pickup_params(year: int, street_id: int, *, city: str, **_) -> dict:
    # Noon (Berlin time, whatever the host's zone) on 1 January: the widget's "yearRange" view date.
    view_date = int(datetime.datetime(year, 1, 1, 12, tzinfo=_TZ).timestamp())
    return {
        "licenseKey": _city(city)["licenseKey"],
        "cityId": _city(city)["idCity"],
        "streetId": street_id,
        "viewrange": "yearRange",
        "viewdate": view_date,
    }


def _pickups(response, source=None) -> list:
    """Flatten ``{"pickups": {"<timestamp>": [{"label", "pickupDate"}, ...]}}``."""
    return [
        pickup
        for pickups in _jsonp(response.text)["pickups"].values()
        for pickup in pickups
    ]


@final
class Source(BaseSource):
    TITLE = "Sector 27 - Datteln, Marl, Oer-Erkenschwick"
    DESCRIPTION = "Source for Muellkalender in Kreis RE."
    URL = "https://muellkalender.sector27.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Datteln": {"city": "Datteln", "street": "Am Bahnhof"},
        "Datteln Im Overkamp": {"city": "Datteln", "street": "Im Overkamp"},
        "Datteln range street": {
            "city": "Datteln",
            "street": "Ahsener Straße 113 - 161 (ungerade)",
        },
        "Marl": {"city": "Marl", "street": "Ahornweg"},
        "Oer-Erkenschick": {
            "city": "Oer-Erkenschwick",
            "street": "An der Zechenbahn",
        },
    }

    PARAMS = (city("city"), street("street"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose Datteln, Marl or Oer-Erkenschwick and enter your street "
            "exactly as it is listed on https://muellkalender.sector27.de "
            "(for split streets including the house number range, e.g. "
            "'Ahsener Straße 113 - 161 (ungerade)')."
        ),
        "de": (
            "Wähle Datteln, Marl oder Oer-Erkenschwick und gib die Straße so "
            "ein, wie sie auf https://muellkalender.sector27.de aufgeführt ist "
            "(bei geteilten Straßen mit Hausnummernbereich, z. B. "
            "'Ahsener Straße 113 - 161 (ungerade)')."
        ),
    }

    retrieve = retrievers.YearlyRetriever(
        prepare=retrievers.Lookup(
            f"{_BASE_URL}/searchForStreets",
            params=_street_params,
            pick=_pick_street,
        ),
        fetch=retrievers.Request(
            f"{_BASE_URL}/fetchPickups",
            params=_pickup_params,
        ),
        # The widget asks for next year too from September on.
        rollover_month=9,
    )
    parse = parsers.EachResponse(_pickups)

    transform = JsonTransformer(
        date_key="pickupDate",
        type_key="label",
        parse_date=date_parsers.for_format("%Y-%m-%d %H:%M:%S"),
    )
