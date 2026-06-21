from datetime import datetime, timezone
from typing import TypedDict, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

# Demonstrates: date_parsers.from_epoch for a JSON API that returns collection
# dates as Unix milliseconds, plus a dropdown whose human-readable options the
# source resolves to the provider's numeric sector id in __init__.

API_URL = "https://mrcjoliette.qc.ca/wp-content/plugins/mrcjoliette-gmr/json/collectes_public_cal.json.php"

CITIES = {
    6042: "Crabtree",
    4246: "Crabtree - Domaine",
    6041: "Joliette - Mardi",
    4252: "Joliette - Mercredi",
    4253: "Joliette - Jeudi",
    6050: "Joliette - Centre-ville",
    6043: "Notre-Dame-de-Lourdes",
    6051: "Notre-Dame-de-Lourdes - Domaine",
    6044: "Notre-Dame-des-Prairies",
    6052: "Notre-Dame-des-Prairies - Domaine",
    6045: "Saint-Ambroise-de-Kildare",
    3963: "Saint-Charles-Borromée - Mercredi",
    6053: "Saint-Charles-Borromée - Jeudi",
    4250: "Saint-Charles-Borromée - Domaine",
    6046: "Sainte-Mélanie",
    6047: "Saint-Paul",
    6048: "Saint-Thomas",
    6049: "Village Saint-Pierre",
}
_NAME_TO_ID = {name: city_id for city_id, name in CITIES.items()}

_TYPE_MAP = {
    "bac_bleu": RECYCLABLES,
    "bac_brun": ORGANIC,
    "bac_noir": GENERAL_WASTE,
    "encombrants": BULKY_WASTE,
    "residus_verts": GARDEN_WASTE,
}


class _Event(TypedDict):
    """The fields the transformer reads from each calendar entry."""

    color: str
    start: int


@final
class Source(BaseSource):
    TITLE = "MRC Joliette (QC)"
    DESCRIPTION = "Source script for mrcjoliette.qc.ca"
    URL = "https://mrcjoliette.qc.ca"
    COUNTRY = "ca"
    API_URL = API_URL
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Joliette Mardi": {"city_id": "Joliette - Mardi"},
        "Saint-Charles-Borromée Mercredi": {
            "city_id": "Saint-Charles-Borromée - Mercredi"
        },
        "Crabtree": {"city_id": "Crabtree"},
    }

    PARAMS = [dropdown("city_id", list(CITIES.values()), label="City/Sector")]

    HOWTO = {
        "en": "Find your sector on the MRC Joliette collection map at https://mrcjoliette.qc.ca/gmr/carte-des-collectes/ and pick it from the list.",
        "fr": "Trouvez votre secteur sur la carte des collectes de la MRC Joliette (https://mrcjoliette.qc.ca/gmr/carte-des-collectes/) et choisissez-le dans la liste.",
    }

    parse = parsers.JsonParser("result", shape=list[_Event])

    transform = JsonTransformer(
        date_key="start",
        type_key="color",
        parse_date=date_parsers.from_epoch(unit="ms"),
        type_value_map=_TYPE_MAP,
    )

    def __init__(self, city_id: str):
        if city_id not in _NAME_TO_ID:
            raise SourceArgumentNotFoundWithSuggestions(
                "city_id", city_id, list(CITIES.values())
            )
        super().__init__(city_id=city_id)
        self._sector_id = _NAME_TO_ID[city_id]

    def retrieve(self, source):
        # The API wants the calendar year as a millisecond epoch window; compute
        # it fresh each fetch so a long-running instance rolls over the new year.
        now = datetime.now(timezone.utc)
        start = int(datetime(now.year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        end = int(
            datetime(now.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp()
            * 1000
        )
        self._params = {
            "id": self._sector_id,
            "from": start,
            "to": end,
            "utc_offset_from": 0,
            "utc_offset_to": 0,
        }
        return retrievers.http_get(self)

    def preprocess(self, records, source=None):
        # Skip entries without a colour/start (the transformer needs both).
        for record in records:
            if isinstance(record, dict) and record.get("color") and record.get("start"):
                yield record
