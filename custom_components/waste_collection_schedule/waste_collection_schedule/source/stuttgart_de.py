from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.StuttgartDe import (
    StuttgartParser,
    StuttgartRetriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import ALL_TYPES

# Declarative source on the Stuttgart components. The single HTML form is fetched
# to discover the waste-type checkboxes, echoed back in a POST, and the resulting
# #awstable table parsed into (date, label) rows. The transformer resolves each open-
# ended German label onto a canonical WasteType via the shared vocabulary.


@final
class Source(BaseSource):
    TITLE = "Abfall Stuttgart"
    DESCRIPTION = "Source for waste collections for the city of Stuttgart, Germany."
    URL = "https://service.stuttgart.de"
    COUNTRY = "de"
    # The transformer resolves open-ended German labels via the shared vocabulary,
    # so any canonical type may appear.
    WASTE_TYPES: ClassVar[list] = list(ALL_TYPES)
    # Address lookup: an empty result means the street/number didn't resolve.
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Im Steinengarten 7": {"street": "Im Steinengarten", "streetnr": 7},
    }

    PARAMS = (
        text_field("street", "Straße"),
        text_field("streetnr", "Hausnummer"),
    )

    retrieve = StuttgartRetriever()
    parse = StuttgartParser()
    transform = RowTransformer()

    def __init__(self, street, streetnr):
        super().__init__(street=street, streetnr=streetnr)
