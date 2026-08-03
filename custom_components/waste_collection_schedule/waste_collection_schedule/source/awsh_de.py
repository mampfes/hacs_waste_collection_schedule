"""Abfallwirtschaft Südholstein (awsh.de).

On the shared AWR/AWSH ``collection_dates`` API; see
``service/AwrCollectionDates.py`` for the three-lookup chain that resolves the
address and downloads the calendar.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.AwrCollectionDates import (
    CollectionDatesRetriever,
    clean_waste_type,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, PAPER

BASE_URL = "https://www.awsh.de"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Südholstein"
    DESCRIPTION = "Source for Abfallwirtschaft Südholstein"
    URL = "https://www.awsh.de"
    COUNTRY = "de"
    # Canonical types observed in the calendar feed; the cleaned German labels
    # resolve through the shared multilingual vocabulary.
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER]

    TEST_CASES: ClassVar[dict] = {
        "Reinbek": {"city": "Reinbek", "street": "Ahornweg"},
    }

    PARAMS = (city(), street())
    RAISE_ON_EMPTY = True

    retrieve = CollectionDatesRetriever(base_url=BASE_URL)
    parse = IcsParser()
    transform = ICSTransformer(clean=clean_waste_type)
