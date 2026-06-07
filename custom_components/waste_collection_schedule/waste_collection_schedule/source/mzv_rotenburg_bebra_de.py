from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    OTHER,
    PAPER,
    RECYCLABLES,
)

# Demonstrates: ICSTransformer + parsers.ics + http_get (default retriever)
# Notable: the ICS summaries carry an "Entsorgung " prefix; type_value_map keys
# include it so no pre-processing is needed. Route-specific filtering
# (yellow_route / paper_route) is omitted in this prototype — that would
# require classify() since the LOCATION field is not exposed by parsers.ics.


class Source(BaseSource):
    TITLE = "MZV Rotenburg"
    DESCRIPTION = "Source for MZV Rotenburg."
    URL = "https://www.mzv-rotenburg-bebra.de"
    COUNTRY = "de"
    API_URL = "https://www.mzv-rotenburg-bebra.de/entsorgung.php"

    TEST_CASES = {
        "Rotenburg an der Fulda": {"city": "rote"},
        "Bebra": {"city": "bebra"},
    }

    PARAMS = [text_field("city", "City")]

    # Explicit WASTE_TYPES: OTHER covers ICS summaries not matched by the map below.
    WASTE_TYPES = [RECYCLABLES, ORGANIC, GENERAL_WASTE, PAPER, BULKY_WASTE, OTHER]

    parse = parsers.ics

    transformer = ICSTransformer(
        type_value_map={
            "Entsorgung Gelbe Tonne": RECYCLABLES,
            "Entsorgung Bioabfall": ORGANIC,
            "Entsorgung Restabfall": GENERAL_WASTE,
            "Entsorgung Papier": PAPER,
            "Entsorgung Sperrmüll": BULKY_WASTE,
            "Entsorgung Weiße Ware": BULKY_WASTE,
            "Entsorgung Kühlgeräte": BULKY_WASTE,
        },
    )

    def __init__(self, city: str):
        self._params = {"ort": city}
        self._headers = {"User-Agent": "Mozilla/5.0"}
