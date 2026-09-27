from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import Compose, ExplodeList, SplitByFields
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "St Albans City & District Council"
    DESCRIPTION = "Source for St Albans City & District Council."
    URL = "https://stalbans.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "55 St John's Ct": {"uprn": 100081132201},
        "9 Tyttenhanger Grn": {"uprn": "100080869141"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url=(
            "https://gis.stalbans.gov.uk/NoticeBoard9/VeoliaProxy.NoticeBoard.asmx/"
            "GetServicesByUprnAndNoticeBoard"
        ),
        json=lambda uprn, **_: {"noticeBoard": "default", "uprn": uprn},
    )
    # Services, each with task headers carrying the last and next date.
    parse = parsers.JsonParser("d")
    preprocess = Compose(
        ExplodeList("ServiceHeaders"),
        SplitByFields(src_keys=("Last", "Next"), dst_key="date"),
    )
    transform = JsonTransformer(
        date_key=lambda record: (record.get("date") or "")[:10],
        type_key="TaskType",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        clean=lambda label: label.removeprefix("Collect ").strip(),
        type_value_map={
            "Domestic Refuse": wt.GENERAL_WASTE,
            "Communal Refuse": wt.GENERAL_WASTE,
            "Domestic Recycling": wt.RECYCLABLES,
            "Communal Recycling": wt.RECYCLABLES,
            "Domestic Food": wt.FOOD_WASTE,
            "Communal Food": wt.FOOD_WASTE,
            "Domestic Paper": wt.PAPER,
            "Garden Waste": wt.GARDEN_WASTE,
            "Paid Garden": wt.GARDEN_WASTE,
            "Domestic Paid Garden": wt.GARDEN_WASTE,
        },
    )
