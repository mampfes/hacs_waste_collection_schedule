from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import RECYCLABLES

# Demonstrates: http_post retriever + DateListParser for a single-stream feed.
# Notable: the API returns a flat date array with no bin type field, so
# DateListParser pairs every date with the round's label and a plain
# RowTransformer maps that label to a canonical WasteType. The array is padded
# with the SQL zero date, dropped via drop_values.
# _data (not _json) is used because the endpoint expects form-encoded POST data.

SENTINEL = "0000-00-00"
BLAUE_TONNE = "Blaue Tonne"


@final
class Source(BaseSource):
    TITLE = "HubertSchmid Recycling und Umweltschutz GmbH"
    DESCRIPTION = "Abfuhrtermine Blaue Tonne"
    URL = "https://www.hschmid24.de/BlaueTonne/"
    COUNTRY = "de"
    API_URL = "https://www.hschmid24.de/BlaueTonne/php/ajax.php"

    TEST_CASES: ClassVar[dict] = {
        "Albatsried(Seeg)": {"city": "Albatsried(Seeg)"},
        "Nesselwang > Attlesee": {"city": "Nesselwang", "ortsteil": "Attlesee"},
        "Buchloe > Hausen > Dorfstraße": {
            "city": "Buchloe",
            "ortsteil": "Hausen",
            "strasse": "Dorfstraße",
        },
    }

    PARAMS = (
        text_field("city", "City"),
        text_field("ortsteil", "District", optional=True),
        text_field("strasse", "Street", optional=True),
    )

    retrieve = retrievers.http_post
    parse = parsers.DateListParser("cal", label=BLAUE_TONNE, drop_values=(SENTINEL,))
    transform = RowTransformer(type_value_map={BLAUE_TONNE: RECYCLABLES})

    def __init__(
        self,
        city: str,
        ortsteil: str | None = None,
        strasse: str | None = None,
    ):
        super().__init__(city=city, ortsteil=ortsteil, strasse=strasse)
        # Form-encoded POST body (not JSON): use _data, not _json.
        self._data = {"l": 3, "p1": city, "p2": ortsteil, "p3": strasse}
