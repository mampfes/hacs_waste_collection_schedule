from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.JaduXfp import XfpFormRetriever
from waste_collection_schedule.transformers import HtmlTransformer, label_cleaner

# Chorley and South Ribble share one XFP forms host, each with its own form.


@final
class Source(BaseSource):
    TITLE = "Chorley Council"
    DESCRIPTION = "Source for chorley.gov.uk services for Chorley Council, UK."
    URL = "https://www.chorley.gov.uk"
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
        "20 Leatherland Drive": {
            "postcode": "PR6 7YD",
            "uprn": "010091497098",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "UPRN not at postcode": {"postcode": "PR6 7YD", "uprn": "100012755948"},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://www.chorley.gov.uk/bincollectiondays and enter your "
            "postcode. The UPRN is the option value of your address in the "
            "address dropdown (browser dev tools); an unknown UPRN is reported "
            "with the addresses the form lists for your postcode."
        ),
    }

    retrieve = XfpFormRetriever(
        "https://forms.chorleysouthribble.gov.uk/xfp/form/71",
        page="198",
        question="qc576c657112a8277ba6f954ebc0490c946168363",
        lookup_address=True,
    )
    parse = parsers.HtmlParser("table.data-table tr", skip=1)
    transform = HtmlTransformer(
        date_getter=lambda row: row.select("td")[1].get_text(strip=True),
        type_getter=lambda row: row.select("td")[0].get_text(strip=True),
        parse_date=date_parsers.for_format("%d/%m/%y"),
        clean=label_cleaner(strip_suffixes=[" Collection Service"]),
        type_value_map={
            "Residual Waste": wt.GENERAL_WASTE,
            "Dry Mixed Recycling": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
            "Paper and Card": wt.PAPER,
        },
        skip_unparseable_dates=True,
    )
