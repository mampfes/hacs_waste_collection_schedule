"""Source for Hemar (ichisystem.eu), Poland."""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Sepan import SepanReportParser, SepanRetriever
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

# Waste-type names as rendered by this deployment's report table (matches the
# wording used by the alba_com_pl deployment of the same underlying
# "SEPAN"/ICHI System platform). Not in Polish shared-vocabulary aliases
# (Polish isn't a resolve() language), so every label is mapped explicitly.
TYPE_VALUE_MAP = {
    "Zmieszane odpady komunalne": GENERAL_WASTE,
    "Metale i tworzywa sztuczne": RECYCLABLES,
    "Papier": PAPER,
    "Szkło": GLASS,
    "Bioodpady": ORGANIC,
    "Bioodpady - Drzewka świąteczne": GARDEN_WASTE,
    "Odpady wystawkowe": BULKY_WASTE,
}

API_BASE = "https://harmonogram.ichisystem.eu/hemar"


@final
class Source(BaseSource):
    TITLE = "Hemar (ichisystem.eu)"
    DESCRIPTION = (
        "Source for the Hemar waste collection schedule platform "
        "(harmonogram.ichisystem.eu) used by several Polish municipalities. "
        'This deployment runs on the same underlying "SEPAN"/ICHI System '
        "platform as sepan_remondis_pl and alba_com_pl."
    )
    URL = "https://harmonogram.ichisystem.eu/hemar/"
    COUNTRY = "pl"

    TEST_CASES: ClassVar[dict] = {
        "Pobiedziska, Boczna 2": {
            "city": "Pobiedziska",
            "street": "Boczna",
            "house_number": "2",
        },
        "Pobiedziska, Dworcowa 1": {
            "city": "POBIEDZISKA",
            "street": "DWORCOWA",
            "house_number": "1",
        },
    }

    REGIONS = (
        region("Pobiedziska", url=API_BASE, city="Pobiedziska"),
        region("Kiszkowo", url=API_BASE, city="Kiszkowo"),
    )

    PARAMS = (
        city("city"),
        street("street"),
        house_number("house_number"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://harmonogram.ichisystem.eu/hemar/ and pick your city, "
            "street, and house number from the dropdowns. Use those exact values "
            "for the city, street, and house_number arguments (matching is "
            "case-insensitive)."
        ),
    }

    retrieve = SepanRetriever(
        base_urls=[API_BASE], city="city", street="street", number="house_number"
    )
    parse = SepanReportParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)

    def __init__(self, city: str, street: str, house_number: str):
        super().__init__(city=city, street=street, house_number=house_number)
