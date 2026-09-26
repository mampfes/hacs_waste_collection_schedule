from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street_address
from waste_collection_schedule.service.JaduXfp import XfpFormRetriever
from waste_collection_schedule.transformers import RowTransformer

# The results table has one row per date ("Mon 28 September", no year), listing
# every round collected that day as its own paragraph.


@final
class Source(BaseSource):
    TITLE = "Tonbridge and Malling Borough Council"
    DESCRIPTION = "Tonbridge and Malling Borough Council, UK - Waste Collection"
    URL = "https://www.tmbc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "High Street, West Malling": {
            "address": "138 High Street",
            "post_code": "ME19 6NE",
        },
        "Nutfields, Ightham, Sevenoaks": {
            "address": "5 Nutfields, Ightham, Sevenoaks",
            "post_code": "TN15 9EA",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "999 High Street", "post_code": "ME19 6NE"},
    }

    PARAMS = (postcode("post_code"), street_address())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode, and the start of your address as the council's "
            "bin collection form lists it (e.g. '138 High Street')."
        ),
    }

    retrieve = XfpFormRetriever(
        "https://www.tmbc.gov.uk/xfp/form/167",
        page="128",
        question="q752eec300b2ffef2757e4536b77b07061842041a",
        postcode="post_code",
        uprn=None,
        address="address",
    )
    parse = parsers.HtmlLabelledDates(
        "table.waste-collections-table tbody tr",
        label="div.collections p",
        date="td",
        all_labels=True,
    )
    transform = RowTransformer(
        parse_date=date_parsers.nearest_year("%a %d %B"),
        type_value_map={
            "Black domestic waste": wt.GENERAL_WASTE,
            "Green recycling": wt.RECYCLABLES,
            "Brown garden waste": wt.GARDEN_WASTE,
            "Food waste": wt.FOOD_WASTE,
        },
    )
