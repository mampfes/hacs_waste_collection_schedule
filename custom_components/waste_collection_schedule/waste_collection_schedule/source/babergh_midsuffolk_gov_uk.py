from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, uprn
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import HtmlTransformer

_COUNCIL_URLS = {
    "midsuffolk": "https://www.midsuffolk.gov.uk",
    "babergh": "https://babergh.gov.uk",
}

_NS = "_com_placecube_digitalplace_local_waste_portlet_CollectionDayFinderPortlet_"


def _page_url(council, **_) -> str:
    return f"{_COUNCIL_URLS[str(council).strip().lower()]}/check-your-collection-day"


def _cells(row) -> list[str]:
    return [" ".join(td.get_text().split()) for td in row.find_all("td")]


@final
class Source(BaseSource):
    TITLE = "Babergh and Mid Suffolk District Councils"
    DESCRIPTION = "Source for Babergh and Mid Suffolk District Council bin collections."
    URL = "https://www.midsuffolk.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region(
            "Mid Suffolk District Council",
            url="https://www.midsuffolk.gov.uk/check-your-collection-day",
            council="midsuffolk",
        ),
        region(
            "Babergh District Council",
            url="https://babergh.gov.uk/check-your-collection-day",
            council="babergh",
        ),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Mid Suffolk - IP14 3AA (Ashgrove)": {
            "uprn": "100091488908",
            "council": "midsuffolk",
        },
        "Babergh - IP8 4AA (Bramford)": {
            "uprn": "100091085564",
            "council": "babergh",
        },
    }

    PARAMS = (
        uprn(),
        dropdown("council", ["midsuffolk", "babergh"], label="Council"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "by entering your address details, and choose your council: "
            "`midsuffolk` (Mid Suffolk District Council) or `babergh` (Babergh "
            "District Council).\n\n"
            "This source only serves the areas covered by the existing Babergh and "
            "Mid Suffolk District Councils. It does not cover the new councils "
            "planned for Suffolk under the local government reorganisation, which "
            "are not expected to be live until at least April 2028."
        ),
    }

    retrieve = HttpPostRetriever(
        _page_url,
        params={
            "p_p_id": "com_placecube_digitalplace_local_waste_portlet_CollectionDayFinderPortlet",
            "p_p_lifecycle": "0",
            "p_p_state": "normal",
            "p_p_mode": "view",
            f"{_NS}mvcRenderCommandName": "/collection_day_finder/get_days",
        },
        data=lambda uprn, **_: {f"{_NS}uprn": str(uprn).strip()},
    )

    # One <tr> per collection: type in the first cell, date in the second.
    parse = parsers.HtmlParser("table.table tbody tr")

    transform = HtmlTransformer(
        date_getter=lambda row: _cells(row)[1] if len(_cells(row)) > 1 else "",
        type_getter=lambda row: _cells(row)[0],
        parse_date=date_parsers.for_format("%A %d %b %Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "Refuse Collection (General Rubbish)": wt.GENERAL_WASTE,
            "Recycling Collection": wt.RECYCLABLES,
            "Garden Waste Collection (Brown Bin)": wt.GARDEN_WASTE,
            "Food Waste Collection": wt.FOOD_WASTE,
            "Paper And Card Collection": wt.PAPER,
        },
    )
