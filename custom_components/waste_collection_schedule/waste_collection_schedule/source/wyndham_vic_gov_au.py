from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://digital.wyndham.vic.gov.au/myWyndham"


def _pick_property(response, *keys, street_address, **_) -> str:
    """The suggestions are ``<li>address</li><span>property number</span>`` pairs."""
    soup = BeautifulSoup(response.text, "html.parser")
    wanted = street_address.strip().upper()
    names = [li.get_text().strip() for li in soup.select("li.jSuggest")]
    for li in soup.select("li.jSuggest"):
        span = li.find_next_sibling("span")
        if span is not None and li.get_text().strip().upper() == wanted:
            return span.get_text().strip()
    raise SourceArgumentNotFoundWithSuggestions("street_address", wanted, names)


def _label(element) -> str:
    """ "Next Garbage Collection: Tuesday, 6 October 2026" -> "Garbage"."""
    head = element.get_text().strip().split(":")[0]
    return head.removeprefix("Next ").replace(" Collection", "")


def _date(element) -> str:
    return element.get_text().split(":")[1].strip()


@final
class Source(BaseSource):
    TITLE = "Wyndham City Council, Melbourne"
    DESCRIPTION = "Source for Wyndham City Council rubbish collection."
    URL = "https://wyndham.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Truganina South Primary School": {
            "street_address": "3-19 Parkvista Drive TRUGANINA 3029"
        },
        "Westbourne Grammar School": {
            "street_address": "300 Sayers Road TRUGANINA 3029"
        },
        "Werribee Mercy Hospital": {
            "street_address": "300-310 Princes Highway WERRIBEE 3030"
        },
        "Wyndham Park Primary School": {
            "street_address": "59-77 Kookaburra Avenue WERRIBEE 3030"
        },
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as the council's "
            "[myWyndham](https://digital.wyndham.vic.gov.au/myWyndham/) search "
            "suggests it, e.g. '3-19 Parkvista Drive TRUGANINA 3029'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API_URL}/ajax/address-search-suggestions.asp",
                params=lambda street_address, **_: {"ASEARCH": street_address},
                pick=_pick_property,
            ),
        ),
        url=f"{API_URL}/init-map-data.asp",
        params=lambda property_number, **_: {
            "propnum": property_number,
            "radius": "1000",
            "mapfeatures": "23,37,22,33,35",
        },
    )

    parse = parsers.HtmlParser('div.waste:-soup-contains("Next ")')

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_label,
        parse_date=date_parsers.for_format("%A, %d %B %Y"),
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Green Waste": wt.GARDEN_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
