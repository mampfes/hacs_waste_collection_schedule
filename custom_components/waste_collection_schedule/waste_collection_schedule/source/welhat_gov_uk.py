from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.JaduXfp import XfpFormRetriever
from waste_collection_schedule.transformers import HtmlTransformer, label_cleaner


@final
class Source(BaseSource):
    TITLE = "Welwyn Hatfield Borough Council"
    DESCRIPTION = (
        "Source for www.welhat.gov.uk services for Welwyn Hatfield Borough Council, UK."
    )
    URL = "https://www.welhat.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "test 1 - South Red": {"uprn": "100080965745", "postcode": "AL9 5EA"},
        "test 2 - Blue North": {"uprn": "100080977050", "postcode": "AL7 3ET"},
    }

    PARAMS = (uprn(), postcode())

    retrieve = XfpFormRetriever(
        "https://www.welhat.gov.uk/xfp/form/214",
        page="492",
        question="q9f451fe0ca70775687eeedd1e54b359e55f7c10c",
    )
    parse = parsers.HtmlParser("table tbody tr")
    transform = HtmlTransformer(
        date_getter=lambda row: row.select("td")[1].get_text(strip=True),
        type_getter=lambda row: row.select("td")[0].get_text(strip=True),
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        clean=label_cleaner(strip_suffixes=[" Collection Service"]),
        type_value_map={
            "Domestic Waste": wt.GENERAL_WASTE,
            "Domestic Waste Sack": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Food Waste": wt.FOOD_WASTE,
        },
        skip_unparseable_dates=True,
    )
