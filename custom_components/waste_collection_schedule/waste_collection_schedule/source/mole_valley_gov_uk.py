from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode
from waste_collection_schedule.preprocessors import TextGroupedDates
from waste_collection_schedule.service.LiveAddresses import LiveAddressesRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The property page lists each round as "Refuse (black bin)" followed by
# "Next collection - (Wed) 07/10/2026". A round with no date has no such
# sentence and yields nothing.
_TYPE_MAP = {
    "Refuse (black bin)": wt.GENERAL_WASTE,
    "Recycling (green bin)": wt.RECYCLABLES,
    "Garden Waste (brown lid)": wt.GARDEN_WASTE,
    "Food Waste": wt.FOOD_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Mole Valley District Council"
    DESCRIPTION = (
        "Source for molevalley.gov.uk services for Mole Valley District Council, UK."
    )
    URL = "https://www.molevalley.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "44 Chapel Court Dorking": {"postcode": "RH4 1BT", "house_number": "44"},
        "79 Ashcombe Road Dorking": {"postcode": "RH4 1LX", "house_number": "79"},
        "21 Rookery Close Fetcham": {"postcode": "KT22 9BG", "house_number": "21"},
    }

    PARAMS = (postcode(), house_number())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and house number or name (e.g. 17 or Rose "
            "Cottage). You can verify your address at "
            "https://myproperty.molevalley.gov.uk/molevalley/"
        ),
    }

    retrieve = LiveAddressesRetriever(
        "https://myproperty.molevalley.gov.uk/molevalley/api/live_addresses/"
    )
    parse = parsers.HtmlTextParser()
    preprocess = TextGroupedDates(
        keys=_TYPE_MAP,
        date_pattern=(
            r"Next collection\s*-\s*\(\w+\)\s*"
            r"(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})"
        ),
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
