import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
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

# Labels as rendered by this SEPAN/ICHI System deployment's report table. Not
# in Polish shared-vocabulary aliases (Polish isn't a resolve() language), so
# every label is mapped explicitly rather than relying on auto-resolution.
TYPE_VALUE_MAP = {
    "Zmieszane odpady komunalne": GENERAL_WASTE,
    "Metale i tworzywa sztuczne": RECYCLABLES,
    "Papier": PAPER,
    "Szkło": GLASS,
    "Bioodpady": ORGANIC,
    "Bioodpady - Drzewka świąteczne": GARDEN_WASTE,
    "Odpady wystawkowe": BULKY_WASTE,
}

# The ALBA deployment's harmonogram path is year-suffixed; try the current
# year first and fall back to the last known-good folder if the council
# hasn't rolled over yet (see issue #6749).
_KNOWN_YEAR_SUFFIX = "2025_swarzedz"


def _base_urls() -> list[str]:
    year = datetime.datetime.now().year
    return [
        f"https://sepan-wroclaw.alba.com.pl/harmonogram{year}_swarzedz",
        f"https://sepan-wroclaw.alba.com.pl/harmonogram{_KNOWN_YEAR_SUFFIX}",
    ]


@final
class Source(BaseSource):
    TITLE = "ALBA Swarzędz"
    DESCRIPTION = "Source for ALBA waste collection in Swarzędz municipality, Poland."
    URL = "https://www.alba.com.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@kamilos-dev"]

    TEST_CASES: ClassVar[dict] = {
        "Bogucin, Boczna 7": {
            "city": "BOGUCIN",
            "street": "BOCZNA",
            "number": "7",
        },
        "Gortatowo, Królewska 12": {
            "city": "GORTATOWO",
            "street": "KRÓLEWSKA",
            "number": "12",
        },
        "Swarzędz, Józefa Rivoliego 2": {
            "city": "SWARZĘDZ",
            "street": "JÓZEFA RIVOLIEGO",
            "number": "2",
        },
    }

    # The original source accepted empty values (deferring to the platform's
    # own "argument required, here are your options" lookup); optional here
    # preserves that instead of failing config validation up front.
    PARAMS = (
        city("city", optional=True),
        street("street", optional=True),
        house_number("number", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.alba.com.pl/odbior_odpadow_wywoz_smieci/swarzedz "
            "and use the schedule search form. Select your city, street and house "
            "number from the dropdowns and use those exact values (uppercase) as "
            "the source arguments."
        ),
    }

    retrieve = SepanRetriever(
        base_urls=_base_urls, city="city", street="street", number="number"
    )
    parse = SepanReportParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)

    def __init__(self, city: str = "", street: str = "", number: str = ""):
        super().__init__(city=city, street=street, number=number)
