"""RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft (rsag.de).

A JSON id cascade feeding an ICS download: the city id narrows the street
list, the street id addresses the calendar, and the calendar path also carries
every waste-type id and the months wanted. Each level needs the one above it,
so the shared ``LookupChainRetriever`` runs the three lookups in order and
builds the download URL from all three.

The waste-type labels returned (e.g. "Restmülltonne 4-wö.",
"Bio-Container Regelabfuhr für Wohnanlagen") don't match the canonical
vocabulary exactly, so ``clean`` normalises each label to the short generic
term the legacy substring-matching ICON_MAP effectively grouped it under
(Restmüll / Biotonne / Papier / Wertstoff / Weihnachtsbaum) before mapping.
"""

import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_BASE = "https://www.rsag.de/api"


def _normalise(s: str) -> str:
    """Lowercase and strip for fuzzy matching."""
    return s.strip().lower()


def _clean_type(label: str) -> str:
    """Group a verbose RSAG label under the short term it belongs to.

    Mirrors the legacy substring-matching ICON_MAP: the API returns labels
    like "Restmülltonne 4-wö." or "Bio-Container Regelabfuhr für
    Wohnanlagen" for what is, for icon/type purposes, plain Restmüll/Biotonne.
    """
    lower = label.lower()
    if "restmüll" in lower:
        return "Restmüll"
    if "bio" in lower:
        return "Biotonne"
    if "papier" in lower:
        return "Papier"
    if "wertstoff" in lower:
        return "Wertstoff"
    if "weihnachtsbaum" in lower:
        return "Weihnachtsbaum"
    return label


def _pick_id(entries: list[dict], wanted: str, id_key: str, argument: str) -> int:
    """Return the id of the entry whose ``name`` matches ``wanted``."""
    names = []
    for entry in entries:
        names.append(entry["name"])
        if _normalise(entry["name"]) == _normalise(wanted):
            return entry[id_key]
    raise SourceArgumentNotFoundWithSuggestions(argument, wanted, names)


def _resolve_city(source: BaseSource, keys: tuple) -> int:
    """City name -> city id."""
    response = source.session.get(f"{_API_BASE}/city/all")
    response.raise_for_status()
    return _pick_id(response.json(), source.params["city"], "city_id", "city")


def _resolve_street(source: BaseSource, keys: tuple) -> int:
    """Street name -> street id, within the resolved city."""
    response = source.session.get(f"{_API_BASE}/street/filter/{keys[0]}")
    response.raise_for_status()
    return _pick_id(response.json(), source.params["street"], "street_id", "street")


def _resolve_waste_types(source: BaseSource, keys: tuple) -> str:
    """Every waste-type id, comma-joined for the calendar path.

    Not a lookup against a user argument: the download URL has to name the
    types wanted, and the source asks for all of them.
    """
    response = source.session.get(f"{_API_BASE}/wastetype/all")
    response.raise_for_status()
    return ",".join(str(entry["wastetype_id"]) for entry in response.json())


def _months_window() -> str:
    """The rolling 12-month window the calendar path takes, as ``YYYY-MM`` values."""
    today = datetime.date.today()
    months = []
    for i in range(12):
        month = today.replace(day=1) + datetime.timedelta(days=32 * i)
        months.append(month.replace(day=1).strftime("%Y-%m"))
    return ",".join(months)


@final
class Source(BaseSource):
    TITLE = "RSAG Rhein-Sieg Abfallwirtschaftsgesellschaft"
    DESCRIPTION = "Source for RSAG waste collection in the Rhein-Sieg-Kreis, Germany."
    URL = "https://www.rsag.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Königswinter, Winzerstraße": {
            "city": "Königswinter",
            "street": "Winzerstraße",
        },
        "Siegburg, Annostraße": {
            "city": "Siegburg",
            "street": "Annostraße",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.rsag.de/abfallkalender/abfuhrtermine and select "
            "your city and street. Use the exact city and street names shown "
            "in the form."
        ),
        "de": (
            "Besuchen Sie https://www.rsag.de/abfallkalender/abfuhrtermine und "
            "wählen Sie Ihren Ort und Ihre Straße. Verwenden Sie die genauen "
            "Namen wie in der Auswahlliste."
        ),
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
    )

    retrieve = LookupChainRetriever(
        steps=(_resolve_city, _resolve_street, _resolve_waste_types),
        url=lambda city_id, street_id, waste_type_ids, **_: (
            f"{_API_BASE}/pickup/filter/{street_id}/{waste_type_ids}"
            f"/{_months_window()}/ics"
        ),
        raise_for_status=True,
    )
    parse = IcsParser()
    transform = ICSTransformer(
        clean=_clean_type,
        type_value_map={"Wertstoff": RECYCLABLES, "Weihnachtsbaum": GARDEN_WASTE},
    )

    def __init__(self, city: str, street: str):
        super().__init__(city=city, street=street)
