import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.service.Sepan import (
    SepanPositionalReportParser,
    SepanRetriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Waste-type names by report-table column position. This deployment's report
# tables don't reliably expose parseable header text (unlike the alba_com_pl /
# ichisystem_eu deployments of the same underlying "SEPAN"/ICHI System
# platform), so - as in the pre-refactor implementation - rows are read
# positionally: row 1 = January ... row 12 = December, column 1..7 = the
# fixed categories below.
NAME_MAP = {
    1: "Zmieszane odpady komunalne",
    2: "Papier",
    3: "Metale i tworzywa sztuczne",
    4: "Szkło",
    5: "Bioodpady",
    6: "Drzewka świąteczne",
    7: "Odpady wystawkowe",
}

# Not in Polish shared-vocabulary aliases (Polish isn't a resolve() language),
# so every label is mapped explicitly.
TYPE_VALUE_MAP = {
    "Zmieszane odpady komunalne": GENERAL_WASTE,
    "Papier": PAPER,
    "Metale i tworzywa sztuczne": RECYCLABLES,
    "Szkło": GLASS,
    "Bioodpady": ORGANIC,
    "Drzewka świąteczne": GARDEN_WASTE,
    "Odpady wystawkowe": BULKY_WASTE,
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

    # This deployment has never exposed a `/years` endpoint (unlike
    # alba_com_pl / ichisystem_eu), so only the single "current" report is
    # fetched, matching the pre-refactor implementation.
    retrieve = SepanRetriever(
        base_urls=_base_urls,
        city="city",
        street="street_name",
        number="street_number",
        use_years=False,
    )
    parse = SepanPositionalReportParser(name_map=NAME_MAP)
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)

    def __init__(self, city: str, street_name: str, street_number: str):
        super().__init__(
            city=city, street_name=street_name, street_number=street_number
        )
