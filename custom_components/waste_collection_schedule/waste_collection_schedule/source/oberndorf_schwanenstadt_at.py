from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.oberndorf.ooe.gv.at"


@final
class Source(BaseSource):
    TITLE = "Oberndorf bei Schwanenstadt"
    DESCRIPTION = "Source for Oberndorf bei Schwanenstadt waste collection."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Am Hang 2": {"strasse": "Am Hang", "hausnummer": "2"},
        "Bergstraße 5": {"strasse": "Bergstraße", "hausnummer": "5"},
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.oberndorf.ooe.gv.at, pick your street and house number "
            "from the waste-calendar dropdowns on the homepage, and use the same values here."
        ),
        "de": (
            "Öffnen Sie https://www.oberndorf.ooe.gv.at, wählen Sie Ihre Straße und "
            "Hausnummer aus den Abfallkalender-Auswahlfeldern auf der Startseite, und "
            "verwenden Sie dieselben Werte hier."
        ),
    }

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "227435354",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=_BASE_URL,
        lookahead_days=365,
        max_pages=30,
    )
    parse = RiSKommunalParser(lookahead_days=365)

    # Restabfall, Bioabfall, Gelber Sack and Altpapier all resolve via the
    # shared multilingual vocabulary; no explicit type_value_map entries are
    # needed.
    transform = ICSTransformer()
