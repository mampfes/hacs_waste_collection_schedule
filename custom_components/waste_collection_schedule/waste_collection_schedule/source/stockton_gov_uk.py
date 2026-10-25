import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.GossForm import (
    GossFormDataParser,
    GossFormRetriever,
    GossStep,
)
from waste_collection_schedule.transformers import HtmlTransformer

_FORM = "LOOKUPBINDATESBYADDRESSSKIPOUTOFREGIONV2"


def _date(element):
    return re.sub(r"(?<=[0-9])(?:st|nd|rd|th)", "", element.get_text(strip=True))


@final
class Source(BaseSource):
    TITLE = "Stockton-on-Tees Borough Council"
    DESCRIPTION = "Source for Stockton-on-Tees Borough Council."
    URL = "https://www.stockton.gov.uk/"
    COUNTRY = "uk"
    TEST_CASES: ClassVar[dict] = {
        "100110203615": {"uprn": "100110203615"},
        "100110160417": {"uprn": "100110160417"},
        "20002027430": {"uprn": 20002027430},
        "100110206644": {"uprn": 100110206644},
    }
    PARAMS = (uprn(),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by entering your address. "
            "Since the v3 pipeline migration, waste types use canonical, localised "
            "names; update filters, automations and customisations using the old labels."
        ),
    }
    retrieve = GossFormRetriever(
        "https://www.stockton.gov.uk/bin-collection-days",
        form=_FORM,
        state_fields=("PAGESESSIONID", "SESSIONID", "NONCE"),
        steps=(
            GossStep(
                "FINDBUTTON",
                fields=lambda response, uprn, **_: {
                    "UPRN": str(uprn),
                    "CUSTODIAN": "738",
                },
                argument="uprn",
            ),
        ),
    )
    parse = GossFormDataParser(
        "COLLECTIONDETAILS2",
        parser=parsers.HtmlParser(
            ".grid__cell p.myaccount-block__date--bin, "
            ".grid__cell:not(:has(p.myaccount-block__date--bin)) p:nth-of-type(2) strong"
        ),
    )
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda element: (
            element.find_parent("div", class_="grid__cell")
            .select_one("p.myaccount-block__title--bin")
            .get_text(strip=True)
        ),
        parse_date=date_parsers.for_format("%a %d %B %Y"),
        skip_unparseable_dates=True,
        type_value_map={
            "Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
