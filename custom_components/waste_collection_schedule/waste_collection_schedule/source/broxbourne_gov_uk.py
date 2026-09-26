from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.service.JaduXfp import XfpFormRetriever
from waste_collection_schedule.transformers import HtmlTransformer

# The results table gives each date without a year ("Thu 08 Oct"), and leaves
# the date empty for a service the property does not have.


def _date_text(row: Tag) -> str:
    # The date's own parts are joined by no-break spaces; a note may follow
    # after an ordinary space.
    text = row.select("td")[0].get_text().strip()
    return text.split(" ")[0].replace("\xa0", " ").strip()


@final
class Source(BaseSource):
    TITLE = "Borough of Broxbourne Council"
    DESCRIPTION = "Source for broxbourne.gov.uk services for Broxbourne, UK."
    URL = "https://www.broxbourne.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Old School Cottage (Domestic Waste Only)": {
            "uprn": "148040092",
            "postcode": "EN10 7PX",
        },
        "11 Park Road (All Services)": {"uprn": "148028240", "postcode": "EN11 8PU"},
        "11 Pulham Avenue (All Services)": {"uprn": 148024643, "postcode": "EN10 7TA"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://www.broxbourne.gov.uk/bin-collection-date and enter "
            "your postcode. The UPRN is the option value of your address in the "
            "address dropdown (browser dev tools); you can also look it up on "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = XfpFormRetriever(
        "https://www.broxbourne.gov.uk/xfp/form/205",
        page="490",
        question="qacf7e570cf99fae4cb3a2e14d5a75fd0d6561058",
        landing_url="https://www.broxbourne.gov.uk/bin-collection-date",
    )
    parse = parsers.HtmlParser("table tr", skip=1)
    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=lambda row: row.select("td")[1].get_text(strip=True),
        parse_date=date_parsers.nearest_year("%a %d %b"),
        type_value_map={
            "Domestic": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green Waste": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        },
        skip_unparseable_dates=True,
    )
