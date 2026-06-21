from dataclasses import replace
from typing import final

from waste_collection_schedule import retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.waste_types import RECYCLABLES

# Demonstrates: http_post retriever + classify() escape hatch
# Notable: the API returns a flat date array (no bin type field), so JsonTransformer
# can't be used — classify() receives each date string and returns a fixed type.
# _data (not _json) is used because the endpoint expects form-encoded POST data.

SENTINEL = "0000-00-00"


@final
class Source(BaseSource):
    TITLE = "HubertSchmid Recycling und Umweltschutz GmbH"
    DESCRIPTION = "Abfuhrtermine Blaue Tonne"
    URL = "https://www.hschmid24.de/BlaueTonne/"
    COUNTRY = "de"
    API_URL = "https://www.hschmid24.de/BlaueTonne/php/ajax.php"

    TEST_CASES = {
        "Albatsried(Seeg)": {"city": "Albatsried(Seeg)"},
        "Nesselwang > Attlesee": {"city": "Nesselwang", "ortsteil": "Attlesee"},
        "Buchloe > Hausen > Dorfstraße": {
            "city": "Buchloe",
            "ortsteil": "Hausen",
            "strasse": "Dorfstraße",
        },
    }

    PARAMS = [
        text_field("city", "City"),
        replace(text_field("ortsteil", "District"), required=False),
        replace(text_field("strasse", "Street"), required=False),
    ]

    retrieve = retrievers.http_post
    WASTE_TYPES = [RECYCLABLES]

    def __init__(
        self,
        city: str,
        ortsteil: str | None = None,
        strasse: str | None = None,
    ):
        super().__init__(city=city, ortsteil=ortsteil, strasse=strasse)
        # Form-encoded POST body (not JSON): use _data, not _json.
        self._data = {"l": 3, "p1": city, "p2": ortsteil, "p3": strasse}

    def parse(self, response, source):
        # API returns {"cal": ["YYYY-MM-DD", ...]} with "0000-00-00" as a no-date sentinel.
        return [d for d in response.json()["cal"] if d != SENTINEL]

    def classify(self, record) -> Collection | None:
        # Each record is a plain date string; the only collection type is Blaue Tonne.
        return Collection(date=self.parse_date(record), waste_type=RECYCLABLES)
