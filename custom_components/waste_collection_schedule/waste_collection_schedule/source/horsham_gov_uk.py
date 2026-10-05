from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _date_text(li) -> str:
    """The DATE cell of the table row this bin-type list item belongs to."""
    return li.find_parent("tr").find_all("td")[1].get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Horsham District Council"
    DESCRIPTION = "Source script for Horsham District Council"
    URL = "https://www.horsham.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Blackthorn Avenue - number": {"uprn": 10013792881},
        "Blackthorn Avenue - string": {"uprn": "10013792881"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering in your address details."
        ),
    }

    retrieve = HttpPostRetriever(
        "https://satellite.horsham.gov.uk/environment/refuse/cal_details.asp",
        data=lambda uprn, **_: {"uprn": str(uprn)},
    )
    # One <tr> per date; each bin type is an <li> in the third cell.
    parse = HtmlParser("td.ApplicationDetail li")
    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=lambda li: li.get_text(strip=True),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "Green Bin for Refuse and Non-Recycling": wt.GENERAL_WASTE,
            "Blue-Top Bin for Recycling": wt.RECYCLABLES,
            "Brown-Top Bin for Garden Waste": wt.GARDEN_WASTE,
            "Orange-Top Bin for Food Waste": wt.FOOD_WASTE,
        },
    )
