from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    district,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

API = "https://portal.muellabfuhr-deutschland.de/api-portal/mandators"

SERVICE_MAP = [
    "Landkreis Hildburghausen",
    "Landkreis Wittenberg",
    "Burgenlandkreis",
    "Dessau-Rosslau",
    "Weimarer Land",
    "Landkreis Sömmerda",
    "Saalekreis",
]

_TYPE_MAP = {
    # Residual waste (the grey bin is assumed to be the residual bin).
    "Restabfall": wt.GENERAL_WASTE,
    "Restabfalltonne": wt.GENERAL_WASTE,
    "Restmülltonne": wt.GENERAL_WASTE,
    "Restmüll": wt.GENERAL_WASTE,
    "Hausmüll": wt.GENERAL_WASTE,
    "Graue Tonne": wt.GENERAL_WASTE,
    # Assumption: the yellow bin / light packaging is the generic recyclables
    # (packaging) type, not a plastic- or metal-specific one.
    "gelbe Tonne/Leichtverpackungen": wt.RECYCLABLES,
    "Gelbe Tonne": wt.RECYCLABLES,
    "Gelber 1100L Container": wt.RECYCLABLES,
    # The blue bin is assumed to be the paper bin.
    "Papier": wt.PAPER,
    "Papiertonne": wt.PAPER,
    "Altpapier": wt.PAPER,
    "Blaue Tonne": wt.PAPER,
    "Biomüll": wt.ORGANIC,
    "Biotonne": wt.ORGANIC,
    "Bioabfalltonne": wt.ORGANIC,
    "Baum- und Strauchschnitt": wt.GARDEN_WASTE,
    "Container für Baum- und Strauchschnitt": wt.GARDEN_WASTE,
    "Schadstoffmobil": wt.HAZARDOUS,
    # No canonical type, or the bin's content is not verifiable.
    "Biotonne waschen": wt.OTHER,
    "Grüne Tonne": wt.OTHER,
}


def _norm(value) -> str:
    return str(value).lower().strip()


def _client_id(response, *keys, client, **_) -> str:
    clients = response.json()
    for entry in clients:
        if _norm(client) == _norm(entry["name"]):
            return entry["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "client", client, [entry["name"] for entry in clients]
    )


def _root_id(response, *keys, **_) -> str:
    return response.json()["calendarRootLocationId"]


def _resolved(keys) -> list:
    """The ``(id, final)`` pairs of the locations resolved so far."""
    return [key for key in keys[2:] if key is not None]


def _final(keys) -> bool:
    resolved = _resolved(keys)
    return bool(resolved) and resolved[-1][1]


def _location_url(*keys, **_) -> str:
    return f"{API}/{keys[0]}/cal/location/{_resolved(keys)[-1][0]}"


def _child(field):
    """A pick taking the child location named by the ``field`` argument."""

    def pick(response, *keys, **params):
        children = response.json()["children"]
        for child in children:
            if _norm(params[field]) == _norm(child["name"]):
                return child["id"], bool(child.get("isFinal"))
        raise SourceArgumentNotFoundWithSuggestions(
            field, params[field], [child["name"] for child in children]
        )

    return pick


@final
class Source(BaseSource):
    TITLE = "Müllabfuhr Deutschland"
    DESCRIPTION = "Source for Müllabfuhr, Germany"
    URL = "https://portal.muellabfuhr-deutschland.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    REGIONS = tuple(region(name, client=name) for name in SERVICE_MAP)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestcaseI": {
            "client": "Landkreis hildburghausen",
            "city": "Gompertshausen",
        },
        "TestcaseII": {
            "client": "Saalekreis",
            "city": "kabelsketal",
            "district": " Großkugel",
            "street": "Am markt",
        },
        "TestcaseIII": {
            "client": "saalekreis",
            "city": "Kabelsketal",
            "district": "kleinkugel ",
        },
    }

    PARAMS = (
        text_field("client", "Client"),
        city("city"),
        district("district", optional=True),
        street("street", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "de": (
            "Wähle den Landkreis bzw. die Stadt (`client`) und gib Ort, "
            "Ortsteil und Straße so an, wie sie im Abfallkalender auf "
            "https://portal.muellabfuhr-deutschland.de/ stehen. Ortsteil und "
            "Straße sind nur nötig, wenn der Ort weiter unterteilt ist."
        ),
        "en": (
            "Enter the district or city (`client`) and the place, district "
            "and street as they appear in the waste calendar on "
            "https://portal.muellabfuhr-deutschland.de/. District and street "
            "are only needed if the place is subdivided further."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(API, pick=_client_id),
            Lookup(
                lambda client_id, **_: f"{API}/{client_id}/config",
                pick=_root_id,
            ),
            Lookup(
                lambda client_id, root_id, **_: (
                    f"{API}/{client_id}/cal/location/{root_id}"
                ),
                params={"includeChildren": "true"},
                pick=_child("city"),
            ),
            Lookup(
                _location_url,
                params={"includeChildren": "true"},
                pick=_child("district"),
                when=lambda *keys, district=None, **_: (
                    district is not None and not _final(keys)
                ),
            ),
            Lookup(
                _location_url,
                params={"includeChildren": "true"},
                pick=_child("street"),
                when=lambda *keys, street=None, **_: (
                    street is not None and not _final(keys)
                ),
            ),
        ),
        url=lambda *keys, **_: f"{_location_url(*keys)}/pickups",
        raise_for_status=True,
    )

    parse = JsonParser()

    transform = JsonTransformer(
        date_key="date",
        type_key=lambda record: record["fraction"]["name"],
        type_value_map=_TYPE_MAP,
        carry_raw_label=True,
    )
