from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.transformers import ICSTransformer

_TYPE_MAP = {
    "Odpady zmieszane": wt.GENERAL_WASTE,
    "Papier": wt.PAPER,
    "Metale i tworzywa sztuczne": wt.RECYCLABLES,
    "Szkło": wt.GLASS,
    "Bioodpady": wt.ORGANIC,
    "Odpady wystawkowe": wt.BULKY_WASTE,
    "Drzewka świąteczne": wt.GARDEN_WASTE,
}


def _upper(value) -> str:
    return str(value).strip().upper()


@final
class Source(BaseSource):
    TITLE = "Poznań"
    DESCRIPTION = "Source for Poznań city garbage collection"
    URL = "https://www.poznan.pl/mim/odpady"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Street Name": {"street_name": "ŚWIĘTY MARCIN", "street_number": "2"},
    }

    PARAMS = (
        street("street_name"),
        house_number("street_number"),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.ORGANIC,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name and building number exactly as offered on "
            "https://www.poznan.pl/mim/odpady/harmonogramy.html."
        ),
    }

    retrieve = retrievers.Request(
        "https://www.poznan.pl/mim/odpady/harmonogramy.html",
        method="POST",
        data=lambda street_name, street_number, **_: {
            "action": "search",
            "co": "waste_schedule",
            "ws_street": _upper(street_name),
            "ws_number": _upper(street_number),
        },
    )
    parse = parsers.HtmlMonthColumns(
        require=("rodzaj odpadów",), month_attr="data-value"
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
