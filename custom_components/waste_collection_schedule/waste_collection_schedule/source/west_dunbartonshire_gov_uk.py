from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


@final
class Source(BaseSource):
    TITLE = "West Dunbartonshire Council"
    DESCRIPTION = (
        "Source for waste collection services from West Dunbartonshire Council"
    )
    URL = "https://www.west-dunbarton.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "2/2 26 Kilbowie Road, Clydebank": {"uprn": "129040292"},
        "6A Victoria Street, Dumbarton": {"uprn": "129033978"},
        "8 Clairinsh, Balloch": {"uprn": "129491488"},
        "Rowan Lea, Gartocharn": {"uprn": "129490987"},
        "20 35 Risk Street, Dumbarton": {"uprn": "129003614"},
    }

    WASTE_TYPES: ClassVar[list] = [wt.RECYCLABLES, wt.ORGANIC, wt.GENERAL_WASTE]

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by searching your address on https://www.findmyaddress.co.uk/ "
            "or by opening the West Dunbartonshire bin collection day page: the UPRN "
            "is the number in the page address after `uprn=`."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://www.west-dunbarton.gov.uk/recycling-and-waste/bin-collection-day",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    parse = parsers.HtmlParser("div.round-info")
    transform = HtmlTransformer(
        date_getter=lambda el: el.select_one("span.date-string").get_text(strip=True),
        type_getter=lambda el: el.select_one("div.round-name").get_text(strip=True),
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map={
            "Blue": wt.RECYCLABLES,
            "Brown Bin": wt.ORGANIC,
            "Non-Recyclable": wt.GENERAL_WASTE,
        },
    )
