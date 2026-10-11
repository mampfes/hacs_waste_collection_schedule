from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, house_number, postcode
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.WhitespaceWRP import (
    WhitespaceParser,
    WhitespaceRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Credit where it's due: the original scraper was a refactoring of the Woking
# Borough Council script from https://github.com/robbrad/UKBinCollectionData

_TYPE_MAP = {
    "Rubbish": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden": wt.GARDEN_WASTE,
    "Food waste": wt.FOOD_WASTE,
    "Batteries-small electricals-textiles": [wt.ELECTRONICS, wt.TEXTILES],
}


def _base_url(borough, **_) -> str:
    return f"https://asjwsw-wrp{str(borough).lower().strip()}municipal-live.whitespacews.com"


@final
class Source(BaseSource):
    TITLE = "Joint Waste Solutions"
    DESCRIPTION = "Manages Waste and Recycling services for Elmbridge, Mole Valley, Surrey Heath & Woking"
    URL = "https://www.jointwastesolutions.org/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region(
            "Woking Borough Council",
            url="https://www.woking.gov.uk",
            borough="woking",
        ),
        region(
            "Surrey Heath Borough Council",
            url="https://www.surreyheath.gov.uk",
            borough="surreyheath",
        ),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.ELECTRONICS,
        wt.TEXTILES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test Woking #1": {"house": "4", "postcode": "GU21 4PQ"},
        "Test Woking #2": {"house": 9, "postcode": "GU22 8RW"},
        "Test Woking #3": {"house": "49", "postcode": "GU22 0AY"},
        "Test Woking #4": {"house": 5, "postcode": "GU21 4HW", "borough": "woking"},
        "surrey heath #1": {
            "house": "1",
            "postcode": "GU15 1JT",
            "borough": "surreyheath",
        },
    }

    PARAMS = (
        house_number("house"),
        postcode(),
        dropdown(
            "borough",
            ["woking", "surreyheath"],
            label="Borough",
            default="woking",
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide the house name or number and the postcode as shown on the "
            "council's bin-day lookup, and choose your borough: `woking` or "
            "`surreyheath`."
        ),
    }

    retrieve = WhitespaceRetriever(
        name_number="house", postcode="postcode", base_url=_base_url
    )
    parse = WhitespaceParser()
    transform = RowTransformer(
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
