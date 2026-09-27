from typing import ClassVar, final
from urllib.parse import quote

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://kalender.renovasjonsportal.no/api/address"


def _address_id(response, *, address: str, **_) -> str:
    """The first address the search returns."""
    results = response.json()["searchResults"]
    if not results:
        raise SourceArgumentNotFound("address", address)
    return results[0]["id"]


@final
class Source(BaseSource):
    TITLE = "ReMidt Orkland muni"
    DESCRIPTION = "Source for Orkland muni."
    URL = "https://www.remidt.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Follovegen": {"address": "Follovegen 1 B"},
        "Makrellsvingen": {"address": "Makrellsvingen 14 - 20"},
        "Taubaneveien": {"address": "Taubaneveien 46"},
        "Mistfjordveien": {"address": "Mistfjordveien 1299"},
    }

    PARAMS = (street_address(),)

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda address, **_: f"{_API_URL}/{quote(address)}",
                pick=_address_id,
            ),
        ),
        url=lambda address_id, **_: f"{_API_URL}/{address_id}/details/",
        raise_for_status=True,
    )
    parse = parsers.JsonParser("disposals")
    transform = JsonTransformer(
        date_key=lambda disposal: disposal["date"][:10],
        type_key="fraction",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Papir": wt.PAPER,
            "Plastemballasje": wt.RECYCLABLES,
            "Glass og metallemballasje": wt.GLASS,
        },
    )
