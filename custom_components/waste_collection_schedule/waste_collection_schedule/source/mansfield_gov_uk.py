import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import JsonTransformer, label_cleaner

# Demonstrates: a flat JSON API that wants today's date in the query.


@final
class Source(BaseSource):
    TITLE = "Mansfield District Council"
    DESCRIPTION = "Source for mansfield.gov.uk services for Mansfield District, UK."
    URL = "https://mansfield.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10091487039"},
        "Test_002": {"uprn": "100031399527"},
        "Test_003": {"uprn": 200000666900},
    }

    PARAMS = (uprn(),)

    retrieve = retrievers.HttpGetRetriever(
        url=(
            "https://portal.mansfield.gov.uk/MDCWhiteSpaceWebService/"
            "WhiteSpaceWS.asmx/GetCollectionByUPRNAndDate"
        ),
        params=lambda uprn, **_: {
            "apiKey": "mDc-wN3-B0f-f4P",
            "UPRN": uprn,
            "coldate": datetime.date.today().strftime("%d/%m/%Y"),
        },
    )
    parse = parsers.JsonParser("Collections")
    transform = JsonTransformer(
        date_key="Date",
        type_key="Service",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        clean=label_cleaner(strip_suffixes=[" Collection Service"]),
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling Waste": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Glass Waste": wt.GLASS,
        },
    )
