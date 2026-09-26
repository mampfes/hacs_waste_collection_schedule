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
    TITLE = "South Ribble Borough Council"
    DESCRIPTION = (
        "Source for southribble.gov.uk services for South Ribble Borough Council, UK."
    )
    URL = "https://www.southribble.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "South Ribble Borough Council, Civic Centre, W Paddock, Leyland PR25 1DH": {
            "postcode": "PR25 1DH",
            "uprn": "100012755948",
        },
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://www.southribble.gov.uk/bincollectiondays and enter your "
            "postcode. The UPRN is the option value of your address in the "
            "address dropdown (browser dev tools); an unknown UPRN is reported "
            "with the addresses the form lists for your postcode."
        ),
    }

    retrieve = XfpFormRetriever(
        "https://forms.chorleysouthribble.gov.uk/xfp/form/70",
        page="196",
        question="qc576c657112a8277ba6f954ebc0490c946168363",
        lookup_address=True,
    )
    parse = parsers.HtmlParser("table.data-table tr", skip=1)
    transform = HtmlTransformer(
        date_getter=lambda row: row.select("td")[1].get_text(strip=True),
        type_getter=lambda row: row.select("td")[0].get_text(strip=True),
        parse_date=date_parsers.for_format("%d/%m/%y"),
        clean=label_cleaner(strip_suffixes=[" Collection Service", " Collection"]),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            # Trade refuse, collected at business premises.
            "Trade": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
        skip_unparseable_dates=True,
    )
