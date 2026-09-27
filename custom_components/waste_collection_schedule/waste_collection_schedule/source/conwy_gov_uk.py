from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Conwy County Borough Council"
    DESCRIPTION = "Source for Conwy County Borough Council."
    URL = "https://www.conwy.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.ELECTRONICS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "50000009637": {"uprn": 50000009637},
        "100101037037": {"uprn": "100101037037"},
        "50000007574": {"uprn": 50000007574},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.conwy.gov.uk/Contensis-Forms/erf/collection-result-soap-xmas2025.asp",
        params=lambda uprn, **_: {"uprn": uprn, "ilangid": 1},
    )
    # One block per date, listing every round collected on it.
    parse = parsers.HtmlLabelledDates(
        ".containererf",
        label="#main1 li",
        date="#main #content",
        parse_date=date_parsers.for_format("%A, %d/%m/%Y"),
        all_labels=True,
    )
    transform = RowTransformer(
        type_value_map={
            "Refuse collection": wt.GENERAL_WASTE,
            "Recycle & food waste collection": [wt.RECYCLABLES, wt.FOOD_WASTE],
            "Garden waste collection (if subscribed)": wt.GARDEN_WASTE,
            "Electrical and textile collection": wt.ELECTRONICS,
        },
    )
