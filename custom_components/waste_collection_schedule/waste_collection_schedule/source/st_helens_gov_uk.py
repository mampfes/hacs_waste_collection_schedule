from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.GossForm import GossFormRetriever, GossStep
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "General non-recyclable waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden waste": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "St Helens Council"
    DESCRIPTION = "Source for sthelens.gov.uk services for St Helens Council, UK."
    URL = "https://sthelens.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "WA9 3AA", "uprn": "39095112"},
        "Test_002": {"postcode": "WA11 0AA", "uprn": "39097983"},
        "Test_003": {"postcode": "WA9 4AA", "uprn": 39099338},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and the UPRN of your property. The UPRN is the "
            "value of your address in the address list of "
            "https://www.sthelens.gov.uk/article/3473/Check-your-collection-dates "
            "(browser dev tools), or look it up on https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = GossFormRetriever(
        "https://www.sthelens.gov.uk/article/3473/Check-your-collection-dates",
        form="RESIDENTCOLLECTIONDATES",
        steps=(
            GossStep(
                "PAGE1_FINDADDRESS",
                fields=lambda response, postcode, **_: {
                    "PAGE1_POSTCODE": str(postcode).strip().upper()
                },
                argument="postcode",
            ),
            GossStep(
                "PAGE1_ADDRESSNEXT",
                fields=lambda response, uprn, **_: {"PAGE1_ADDRESS": str(uprn).strip()},
            ),
        ),
    )
    # A heading row per month, then a row per day: day, weekday, container, and
    # what is collected ("General non-recyclable waste & Recycling").
    parse = parsers.HtmlMonthHeadedRows(label_separator="&")
    transform = RowTransformer(type_value_map=_TYPE_MAP)
