from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode
from waste_collection_schedule.service.JaduXfp import XfpFormRetriever
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Non-recyclable waste(grey bin)": wt.GENERAL_WASTE,
    "Outdoorfood caddy": wt.FOOD_WASTE,
    "Mixed recycling(blue-lidded bin)": wt.RECYCLABLES,
    "Paper and card recycling(red-lidded bin)": wt.PAPER,
    "Garden bin(green bin)": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Braintree District Council"
    DESCRIPTION = "Braintree District Council, UK - Waste Collection"
    URL = "https://www.braintree.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "30 Boars Tye Road": {  # codespell:ignore tye
            "house_number": 30,
            "post_code": "CM8 3QE",
        },
        "64 Silver Street": {"house_number": "64", "post_code": "CM8 3QG"},
        "18 St Mary's Road": {"house_number": "18", "post_code": "CM8 3PE"},
        "20 Peel Crescent": {"house_number": "20", "post_code": "CM7 2RS"},
    }

    PARAMS = (postcode("post_code"), house_number())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and the start of your address as the "
            "[council's form](https://www.braintree.gov.uk/xfp/form/554) lists it "
            "(usually the house number, or the house name). During the ongoing "
            "local government reorganisation (LGR) in Essex, please keep using the "
            "source for your current area as long as it still works; new sources "
            "for the new North East Essex Council are not expected before April 2028."
        ),
    }

    retrieve = XfpFormRetriever(
        "https://www.braintree.gov.uk/xfp/form/554",
        page="5730",
        question="qe15dda0155d237d1ea161004d1839e3369ed4831",
        postcode="post_code",
        uprn=None,
        address="house_number",
    )
    parse = parsers.HtmlLabelledDates(
        "div.date_display",
        label="h3",
        date="p",
        date_pattern=r"(\d{1,2}/\d{1,2}/\d{4})",
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map=_TYPE_MAP,
    )
