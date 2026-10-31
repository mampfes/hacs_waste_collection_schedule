from typing import ClassVar, final

from waste_collection_schedule import date_parsers, lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.transformers import JsonTransformer

ADDRESS_URL = "https://gis.komunala-kranj.si/mapguide/KaliopaFDOService/Service.asmx/GetResultsSimplified"
SCHEDULE_URL = (
    "https://gis.komunala-kranj.si/ddmoduli/EkoloskiOtoki.asmx/GetKoledarOdvozov"
)
API_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
}
# How far ahead the calendar service is asked for, as on the provider's map.
DAYS_AHEAD = 60
_MAX_SUGGESTIONS = 10


def _address_id(response, address, **_):
    """The house number id of the address; the search matches prefixes."""
    matches = {
        str(item.get("Text", "")).strip(): str(item.get("Id", ""))
        for item in response.json().get("d", [])
        if item.get("Id")
    }
    if not matches:
        raise SourceArgumentNotFound("address", address)
    if len(matches) == 1:
        return next(iter(matches.values()))
    wanted = lookups.normalize_text(address)
    for text, identifier in matches.items():
        if lookups.normalize_text(text) == wanted:
            return identifier
    raise SourceArgAmbiguousWithSuggestions(
        "address", address, sorted(matches)[:_MAX_SUGGESTIONS]
    )


@final
class Source(BaseSource):
    TITLE = "Komunala Kranj"
    DESCRIPTION = "Source for Komunala Kranj."
    URL = "https://www.komunala-kranj.si/"
    COUNTRY = "si"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Kranj": {"address": "Koroška cesta 1, Kranj, 4000 Kranj"},
        "BESNICA": {"address": "Vogel 10, Spodnja Besnica, 4201 Zgornja Besnica"},
    }
    PARAMS = (street_address(),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the address exactly as the Komunala Kranj address search shows it, "
            "e.g. 'Koroška cesta 1, Kranj, 4000 Kranj'. Since the v3 pipeline "
            "migration, waste types use canonical, localised names. Update filters, "
            "automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = retrievers.Request(
        SCHEDULE_URL,
        params=lambda address_id, **_: {
            "a": "komunalakranj",
            "hsMid": address_id,
            "stDni": str(DAYS_AHEAD),
        },
        headers=API_HEADERS,
        before=(
            retrievers.Lookup(
                ADDRESS_URL,
                params=lambda address, **_: {
                    "a": "hisnestevilkekranj",
                    "mapName": "map",
                    "locale": "SI",
                    "query": address,
                },
                headers=API_HEADERS,
                pick=_address_id,
            ),
        ),
    )
    parse = parsers.JsonParser("d")
    transform = JsonTransformer(
        date_key="Datum",
        type_key=lambda item: str(item.get("VrstaOdpadka") or "").strip(),
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        type_value_map={
            "MEŠANI KOMUNALNI ODPADKI": wt.GENERAL_WASTE,
            "ODPADNA EMBALAŽA": wt.RECYCLABLES,
            "BIOLOŠKI ODPADKI": wt.ORGANIC,
        },
    )
