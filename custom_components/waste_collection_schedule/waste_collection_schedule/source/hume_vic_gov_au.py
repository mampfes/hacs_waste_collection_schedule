import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesProjection,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


def _normalise_address(address: str) -> str:
    """Hume's search finds nothing for an address carrying a comma or the state."""
    address = address.replace(",", "")
    address = re.sub(r"victoria (\d{4})", r" \1", address, flags=re.IGNORECASE)
    address = re.sub(r" vic (\d{4})", r" \1", address, flags=re.IGNORECASE)
    return " ".join(address.split())


@final
class Source(BaseSource):
    TITLE = "Hume City Council"
    DESCRIPTION = "Source for hume.vic.gov.au Waste Collection Services"
    URL = "https://hume.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "19 Potter": {
            "address": "19 Potter Street Craigieburn 3064",
            "predict": True,
        },
        "1/90 Vineyard": {"address": "1/90 Vineyard Road Sunbury, VIC 3429"},
        "9-19 McEwen": {"address": "9-19 MCEWEN DRIVE SUNBURY VICTORIA 3429"},
        "33 Toyon": {"address": "33 TOYON ROAD KALKALLO  3064"},
    }

    PARAMS = (
        street_address(field="address"),
        boolean(
            "predict",
            "Project future collection dates",
            default=False,
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Enter your address as it appears on the Hume City Council 'Know my "
        "bin day' page. Council only publishes the next collection date for each "
        "bin. Turn on 'predict' to project the following four weeks from the "
        "collection frequency the council states.",
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.hume.vic.gov.au",
        normalise=_normalise_address,
        headers={
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.hume.vic.gov.au/Residents/Waste/Know-my-bin-day",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    preprocess = OpenCitiesProjection(weeks=4, when="predict")
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
    )
