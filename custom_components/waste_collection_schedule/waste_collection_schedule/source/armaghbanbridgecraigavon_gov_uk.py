import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer, label_cleaner

# The bin-day result page has one row per service: a heading
# (<h2>Domestic Collections</h2>) followed by a div.col-sm-12.col-md-9 holding
# one <h4> per date ("Friday 23/10/2026"). Every date <h4> is read with the
# service heading that precedes it.

API_URL = "https://www.armaghbanbridgecraigavon.gov.uk/resident/binday-result/"

_DATE = re.compile(r"\d{2}/\d{2}/\d{4}")


def _date(h4):
    match = _DATE.search(h4.get_text(strip=True))
    return match.group() if match else None


def _service(h4):
    heading = h4.find_previous("h2")
    return heading.get_text(strip=True) if heading else ""


@final
class Source(BaseSource):
    TITLE = "Armagh City Banbridge & Craigavon"
    DESCRIPTION = "Source for Armagh City Banbridge & Craigavon."
    URL = "https://www.armaghbanbridgecraigavon.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    TEST_CASES: ClassVar[dict] = {
        "BT667ES": {"address_id": 185622007},
        "BT63 5GY": {"address_id": "187318004"},
    }

    PARAMS = (location_id("address_id"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find the parameter of your address using "
            "https://www.armaghbanbridgecraigavon.gov.uk/resident/when-is-my-bin-day/, "
            "after selecting your address. The address ID is the number at the end "
            "of the URL after `address=`."
        ),
    }

    retrieve = HttpGetRetriever(
        url=API_URL, params=lambda address_id, **_: {"address": address_id}
    )
    parse = parsers.HtmlParser("div.col-sm-12.col-md-9 h4")
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_service,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=label_cleaner(strip_suffixes=[" Collections"]),
        type_value_map={
            "Domestic": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            # One brown bin for garden and food waste.
            "Garden & Food": wt.ORGANIC,
        },
    )
