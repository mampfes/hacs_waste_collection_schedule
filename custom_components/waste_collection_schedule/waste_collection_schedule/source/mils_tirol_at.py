from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://mils-tirol.at"
_SELECTION_URL = "https://mils-tirol.at/Service/Dienstleistungen/Abfallkalender"
_LOOKAHEAD_DAYS = 365


@final
class Source(BaseSource):
    TITLE = "Gemeinde Mils"
    DESCRIPTION = "Source for Gemeinde Mils, Tyrol, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    # An address that does not resolve should say so, not show an empty
    # calendar (#7144).
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Fichtenweg 21": {
            "strasse": "Fichtenweg",
            "hausnummer": "21",
        },
        "Dorfplatz 1": {
            "strasse": "Dorfplatz",
            "hausnummer": "1",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"strasse": "Keine Straße", "hausnummer": "1"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            f"Open {_SELECTION_URL}, pick your street and house number from the "
            "dropdowns, and use the same values for 'strasse' and 'hausnummer'."
        ),
        "de": (
            f"Öffnen Sie {_SELECTION_URL}, wählen Sie Ihre Straße und Hausnummer "
            "aus den Dropdown-Menüs, und verwenden Sie dieselben Werte für "
            "'strasse' und 'hausnummer'."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={"sprache": "1", "menuonr": "226285523"},
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=_SELECTION_URL,
        lookahead_days=_LOOKAHEAD_DAYS,
        max_pages=30,
    )
    parse = RiSKommunalParser(lookahead_days=_LOOKAHEAD_DAYS)
    # Restmüll, Biomüll and Gelber Sack resolve via the shared vocabulary.
    transform = ICSTransformer(
        type_value_map={
            "Altpapier&Kleinkartons": wt.PAPER,
            "Problemstoffsammlung": wt.HAZARDOUS,
        },
    )
