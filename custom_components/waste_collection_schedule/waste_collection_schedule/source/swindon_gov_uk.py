from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Swindon Borough Council"
    DESCRIPTION = "Swindon Borough Council, UK - Waste Collection"
    URL = "https://www.swindon.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    # Food waste is collected with both the rubbish and the recycling round,
    # and some properties list it on its own too.
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "1 Nyland Road": {"uprn": "100121147490"},
        "74 Standen Way": {"uprn": "200002922415"},
        "1 Eastbury Way": {"uprn": "10010424600"},
        "33 Ulysses Road": {"uprn": "10010427033"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url="https://www.swindon.gov.uk/info/20122/rubbish_and_recycling_collection_days",
        params=lambda uprn, **_: {"uprnSubmit": "Yes", "addressList": uprn},
    )
    parse = parsers.HtmlLabelledDates(
        "div.bin-collection-content",
        label=".content-left h3",
        date="span.nextCollectionDate",
        parse_date=date_parsers.for_format("%A, %d %B %Y"),
    )
    transform = RowTransformer(
        type_value_map={
            "Rubbish bin and food waste": [wt.GENERAL_WASTE, wt.FOOD_WASTE],
            "Recycling and food waste": [wt.RECYCLABLES, wt.FOOD_WASTE],
            "Garden waste": wt.GARDEN_WASTE,
            "Garden waste bin": wt.GARDEN_WASTE,
            "Food bin": wt.FOOD_WASTE,
        },
    )
