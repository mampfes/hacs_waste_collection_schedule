from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

API_BASE = "https://api.asm.easyeco.prod.emberware.it/wp-json/ee/v1"
HEADERS = {"Accept": "application/json"}


def _pick_municipality_id(response, *keys, municipality, **_) -> int:
    municipalities = response.json()
    target = str(municipality).strip().casefold()
    for m in municipalities:
        if target in (
            str(m.get("name", "")).casefold(),
            str(m.get("slug", "")).casefold(),
        ):
            return int(m["id"])
    raise SourceArgumentNotFoundWithSuggestions(
        "municipality",
        municipality,
        sorted(m["name"] for m in municipalities if m.get("name")),
    )


def _street_title(s: dict) -> str:
    return (s.get("title") or {}).get("rendered", "")


def _pick_zone_id(response, *keys, street, **_) -> int:
    """The zone of the street: an exact name, else the one street containing it."""
    streets = response.json()
    entered = str(street).strip()
    target = entered.casefold()

    for s in streets:
        if _street_title(s).casefold() == target:
            return int(s["zone-id"])

    matches = [s for s in streets if target and target in _street_title(s).casefold()]
    if len(matches) == 1:
        return int(matches[0]["zone-id"])
    if not streets:
        raise SourceArgumentNotFound("street", entered)
    raise SourceArgumentNotFoundWithSuggestions(
        "street", entered, [_street_title(s) for s in matches or streets]
    )


def _title(record: dict) -> str:
    return ((record.get("container-type") or {}).get("title") or "").strip()


@final
class Source(BaseSource):
    TITLE = "ASM Pavia"
    DESCRIPTION = (
        "Source for ASM Pavia (porta a porta) waste collection in Pavia and "
        "surrounding municipalities, Italy."
    )
    URL = "https://www.asm.pv.it"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Pavia, Via Piemonte": {"municipality": "Pavia", "street": "Via Piemonte"},
        "Pavia (slug), via piemonte (lowercase)": {
            "municipality": "pavia",
            "street": "via piemonte",
        },
        "Albuzzano": {"municipality": "Albuzzano", "street": "Tutte le vie"},
    }

    PARAMS = (municipality(), street())

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PAPER,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.OTHER,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    HOWTO: ClassVar[dict] = {
        "it": (
            "Apri https://www.asm.pv.it/raccolta-differenziata/porta-a-porta-pavia/ "
            "e scegli il tuo comune e la tua via nella ricerca. Usa gli stessi "
            "valori qui. Per i piccoli comuni serviti da un'unica zona, usa "
            "'Tutte le vie' come via."
        ),
        "en": (
            "Open https://www.asm.pv.it/raccolta-differenziata/porta-a-porta-pavia/ "
            "and pick your municipality and street from the search. Use the same "
            "values here. For small municipalities served by a single zone, use "
            "'Tutte le vie' as the street."
        ),
    }

    # The zone id of the street goes in a request header of the schedule call.
    retrieve = retrievers.Request(
        f"{API_BASE}/garbage-collections",
        headers=lambda municipality_id, zone_id, **_: {
            **HEADERS,
            "zone-id": str(zone_id),
        },
        before=(
            retrievers.Lookup(
                f"{API_BASE}/municipalities",
                headers=HEADERS,
                pick=_pick_municipality_id,
            ),
            retrievers.Lookup(
                lambda municipality_id, **_: (
                    f"{API_BASE}/municipalities/{municipality_id}/streets"
                ),
                # The list is paged, so the street is searched for server side.
                params=lambda *keys, street, **_: {"search": str(street).strip()},
                headers=HEADERS,
                pick=_pick_zone_id,
            ),
        ),
    )

    parse = parsers.JsonParser()

    # An entry without a date or a container title is not a collection.
    preprocess = preprocessors.RowFilter(
        lambda record, source=None: bool(record.get("date") and _title(record))
    )

    transform = JsonTransformer(
        date_key="date",
        type_key=_title,
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Umido (Scarto organico di cucina)": wt.ORGANIC,
            "Carta - Cartone": wt.PAPER,
            "Secco non riciclabile (indifferenziato)": wt.GENERAL_WASTE,
            # One mixed light-packaging round (plastic, metal, ...).
            "Multimateriale leggero": wt.RECYCLABLES,
            "Verde": wt.GARDEN_WASTE,
            "Ingombranti e RAEE": wt.BULKY_WASTE,
            # The mobile eco-station (a travelling drop-off point), no canonical type.
            "Ecomobile": wt.OTHER,
        },
        carry_raw_label=True,
    )
