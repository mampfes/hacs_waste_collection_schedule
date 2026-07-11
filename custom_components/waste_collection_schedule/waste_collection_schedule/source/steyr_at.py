from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.steyr.at"


@final
class Source(BaseSource):
    TITLE = "Stadtbetriebe Steyr GmbH"
    DESCRIPTION = "Source for Stadtbetriebe Steyr GmbH waste collection schedule."
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Wolfernstraße 7": {
            "strasse": "Wolfernstraße",
            "hausnummer": "7",
        },
        "Aichetgasse 1": {
            "strasse": "Aichetgasse",
            "hausnummer": "1",
        },
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": "227376864",
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=(
            "https://www.steyr.at/system/web/kalender.aspx?sprache=1&menuonr=227376864"
        ),
    )
    parse = RiSKommunalParser()

    # Every observed label (Restabfall, Bioabfall, Altpapier, Gelber Sack,
    # Sperrmüll, Altglas, Problemstoff) resolves against the shared vocabulary
    # unmapped; no type_value_map needed.
    transform = ICSTransformer()

    def __init__(self, strasse: str, hausnummer: str):
        super().__init__(strasse=strasse, hausnummer=hausnummer)
