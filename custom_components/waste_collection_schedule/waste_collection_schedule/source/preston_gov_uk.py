"""Preston City Council (England) bin collection dates."""

import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import field_terms as ft
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.transformers import HtmlTransformer

# An ASP.NET WebForms page: the GET hands out the postback state, the search
# posts it back with the street or postcode (and the UPRN, which picks the
# property), and the answer carries one <div id="container"> per round: a
# <b> heading ("Food waste:") and a <li><span>Monday 02/11/2026</span> per date.
SRV_URL = (
    "https://selfservice.preston.gov.uk/service/Forms/FindMyNearest.aspx?Service=bins"
)


def _state(response, **_) -> dict[str, str]:
    """The page's hidden postback fields (VIEWSTATE, EVENTVALIDATION, ...)."""
    return retrievers.form_inputs(response.text, hidden_only=True)


def _search(state, *, street, uprn=None, **_) -> dict[str, str]:
    return {
        **state,
        "__EVENTTARGET": "ctl00$MainContent$btnSearch",
        "__EVENTARGUMENT": "",
        "ctl00$MainContent$hdnService": "bins",
        "ctl00$MainContent$txtAddress": street,
        "ctl00$MainContent$hdnUPRN": str(uprn or "").strip(),
    }


def _round(item) -> str:
    """The round heading of a date item, without its colon and double spaces."""
    heading = item.find_parent("ul").find("b")
    return re.sub(r"\s+", " ", heading.get_text(strip=True)).rstrip(":").strip()


@final
class Source(BaseSource):
    TITLE = "Preston City Council"
    DESCRIPTION = "Source for preston.gov.uk services for Preston City Council, UK."
    URL = "https://preston.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"street": "town hall, lancaster road"},
        "Test_002": {"street": "PR1 2RL", "uprn": "10002220003"},
    }

    PARAMS = (
        street_address("street"),
        text_field("uprn", term=ft.UPRN, optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name or postcode as you would on "
            "https://selfservice.preston.gov.uk/service/Forms/FindMyNearest.aspx?Service=bins. "
            "If it matches more than one property, also enter your Unique "
            "Property Reference Number (UPRN), which you can find at "
            "https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, "
            "waste types use canonical, localised names. Update filters, "
            "automations and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        SRV_URL,
        method="POST",
        before=(retrievers.Lookup(SRV_URL, pick=_state),),
        data=_search,
    )

    # A search that matched no single property comes back without any round.
    parse = parsers.ArgumentGuard(
        parsers.HtmlParser("#MainContent_lblMoreCollectionDates #container ul > li"),
        argument="street",
        contains='id="container"',
        hint="enter the UPRN as well if the street or postcode matches several properties",
    )

    transform = HtmlTransformer(
        date_getter=lambda item: item.find("span").get_text(strip=True),
        type_getter=_round,
        description_getter=_round,
        parse_date=date_parsers.for_format("%A %d/%m/%Y"),
        type_value_map={
            "Food waste": wt.FOOD_WASTE,
            "Black/grey bin (general waste)": wt.GENERAL_WASTE,
            "Yellow lidded recycling container (glass/cans/plastics)": wt.RECYCLABLES,
            "Red lidded recycling container (paper/card)": wt.PAPER,
            "Brown bin (garden waste)": wt.GARDEN_WASTE,
            "Commercial - general waste": wt.GENERAL_WASTE,
            "Commercial - cardboard and paper": wt.PAPER,
            "Commercial - plastic cans and glass": wt.RECYCLABLES,
            "Commercial - food waste": wt.FOOD_WASTE,
        },
    )
