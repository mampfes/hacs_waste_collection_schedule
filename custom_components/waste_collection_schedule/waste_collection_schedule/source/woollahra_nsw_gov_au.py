from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

BASE_URL = "https://www.woollahra.nsw.gov.au"
DEEPLINK = f"{BASE_URL}/Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates"
PAGE_LINK = "/$b9015858-988c-48a4-9473-7c193df083e4$/Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates"


def _cleanup(label: str) -> str:
    """The seasonal clean-ups ("Spring Clean-Up ...") are one kind of service."""
    return "Clean-Up" if "clean" in label.lower() else label


@final
class Source(BaseSource):
    TITLE = "Woollahra Municipal Council (NSW)"
    DESCRIPTION = "Source for Woollahra Municipal Council rubbish collection."
    URL = "https://www.woollahra.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "13 Paddington Street Paddington": {
            "address": "13 Paddington Street PADDINGTON NSW 2021",
        },
        "22 Oxford Street Paddington": {
            "address": "22 Oxford Street PADDINGTON NSW 2021",
        },
    }

    PARAMS = (street_address(field="address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    retrieve = OpenCitiesRetriever(
        domain=BASE_URL,
        page_link=PAGE_LINK,
        warm_up_url=DEEPLINK,
        headers={
            "accept": "application/json, text/javascript, */*; q=0.01",
            "referer": DEEPLINK,
            "x-requested-with": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        clean=_cleanup,
        type_value_map={
            "Clean-Up": wt.BULKY_WASTE,
            # A recurring problem-waste promo tile in the same response as the
            # dated collections: not a kerbside collection.
            "Recycle problem waste": None,
        },
    )
