from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import area_id
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://www.shellharbourwaste.com.au/wp-json/rb_co/v1/get-waste-url"


def _page_url(response, *keys, **_) -> str:
    """The zone lookup answers ``{"url": ".../zone-1a/", "title": "Monday A"}``."""
    return response.json()["url"]


@final
class Source(BaseSource):
    TITLE = "Shellharbour City Council"
    DESCRIPTION = "Source script for shellharbourwaste.com.au"
    URL = "https://shellharbourwaste.com.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestName1": {"zoneID": "Monday A"},
        "TestName2": {"zoneID": "Friday A"},
    }

    PARAMS = (area_id("zoneID"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your collection zone as shown on "
            "https://www.shellharbourwaste.com.au/find-my-bin-day/ "
            "(e.g. 'Monday A')."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                API_URL,
                params=lambda zoneID, **_: {"zone": zoneID},
                pick=_page_url,
            ),
        ),
        url=lambda page_url, **_: page_url,
        headers={"Referer": "https://www.shellharbourwaste.com.au/find-my-bin-day/"},
    )

    parse = parsers.HtmlParser("div.waste-block__content")

    transform = HtmlTransformer(
        date_getter=lambda el: el.find("time", class_="waste-block__time").text.strip(),
        type_getter=lambda el: el.find("h3", class_="waste-block__title").text.strip(),
        # Strip the trailing bin-colour hint, "General Waste (Red lid)"
        clean=lambda label: label.split(" (")[0],
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
