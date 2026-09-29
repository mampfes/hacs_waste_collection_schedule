from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.parsers import EachResponse, JsonParser
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

_BASE_URL = "https://arhiv.snaga-mb.si/mso"


def _address_ids(response, **_) -> list[str]:
    """The ids of every address entry matching the street and house number.

    An unknown address is answered with a literal ``null`` body.
    """
    entries = response.json()
    if not entries:
        raise SourceArgumentExceptionMultiple(
            ["street", "house_number"], "Invalid address"
        )
    return [entry["OM"] for entry in entries]


def _iso_date(item) -> str:
    return f"{item['Leto']}-{int(item['Mesec']):02d}-{int(item['Dan']):02d}"


@final
class Source(BaseSource):
    TITLE = "Snaga Maribor"
    DESCRIPTION = "Source for Snaga Maribor."
    URL = "https://snaga-mb.si/"
    COUNTRY = "si"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Ruska ulica 24": {"street": "Ruska ulica", "house_number": 24},
    }

    PARAMS = (street(), house_number())

    retrieve = FanOutRetriever(
        prepare=Lookup(
            f"{_BASE_URL}/tmRSkjpgG.php",
            params=lambda street, house_number, **_: {
                "Naziv": street,
                "HS": house_number,
                "IDo": "0",
            },
            pick=_address_ids,
        ),
        targets=lambda source, ids: ids,
        fetch=Request(
            f"{_BASE_URL}/tmRSk.php", params=lambda id, ids, **_: {"sql": id}
        ),
    )
    parse = EachResponse(JsonParser())
    transform = JsonTransformer(
        date_key=_iso_date,
        type_key="Odp",
        type_value_map={
            "O": wt.GENERAL_WASTE,
            "B": wt.ORGANIC,
            "U": wt.RECYCLABLES,
            "P": wt.PAPER,
            "S": wt.GLASS,
        },
    )
