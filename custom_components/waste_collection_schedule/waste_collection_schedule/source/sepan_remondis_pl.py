import datetime
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.service.Sepan import SepanReportParser, SepanRetriever
from waste_collection_schedule.transformers import RowTransformer

# Not in Polish shared-vocabulary aliases (Polish isn't a resolve() language),
# so every label is mapped explicitly.
TYPE_VALUE_MAP = {
    "Odpady zmieszane": wt.GENERAL_WASTE,
    "Papier": wt.PAPER,
    "Metale i tworzywa sztuczne": wt.RECYCLABLES,
    "Szkło": wt.GLASS,
    "Bioodpady": wt.ORGANIC,
    "Drzewka świąteczne": wt.GARDEN_WASTE,
    "Odpady wystawkowe": wt.BULKY_WASTE,
}


def _base_urls() -> list[str]:
    year = datetime.datetime.now().year
    return [
        f"https://sepan.remondis.pl/harmonogram{year}",
        "https://sepan.remondis.pl/harmonogram",
    ]


@final
class Source(BaseSource):
    TITLE = "Koziegłowy/Objezierze/Oborniki"
    DESCRIPTION = "Source for Koziegłowy/Objezierze/Oborniki city garbage collection"
    URL = "https://sepan.remondis.pl"
    COUNTRY = "pl"
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Street Name": {
            "city": "Poznań",
            "street_name": "ŚWIĘTY MARCIN",
            "street_number": "2",
        },
    }

    PARAMS = (
        city("city"),
        street("street_name"),
        house_number("street_number"),
    )

    # The deployment now exposes a `/years` endpoint and rejects the yearless
    # report request ("Operacja generowania Reportu nie powiodła się"), so the
    # per-year reports are fetched with the address token.
    retrieve = SepanRetriever(
        base_urls=_base_urls,
        city="city",
        street="street_name",
        number="street_number",
        use_years=True,
    )
    parse = SepanReportParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
