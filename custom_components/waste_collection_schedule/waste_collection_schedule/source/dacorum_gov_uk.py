from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://webapps.dacorum.gov.uk/bincollections/"

# The ASP.NET control names behind the page's element ids.
_POSTCODE_FIELD = "ctl00$MainContent$txtBxPCode"
_FIND_BUTTON = "ctl00$MainContent$btnFindAddr"
_ADDRESS_FIELD = "ctl00$MainContent$lstBxAddrList"
_SCHEDULE_BUTTON = "ctl00$MainContent$btnGetSchedules"


def _hidden_inputs(response) -> dict[str, str]:
    """The ASP.NET state fields (viewstate, event validation) of the page."""
    soup = BeautifulSoup(response.text, "html.parser")
    return {
        str(tag["name"]): str(tag.get("value", ""))
        for tag in soup.find_all("input", {"type": "hidden"})
        if tag.get("name")
    }


def _search_form(response, *keys, postcode, **_) -> dict[str, str]:
    """The form body of the postcode search, built from the landing page."""
    return {
        **_hidden_inputs(response),
        _POSTCODE_FIELD: postcode.strip(),
        _FIND_BUTTON: "Find me",
    }


def _pick_address(response, search_form, *, postcode, uprn, **_) -> dict[str, str]:
    """The form body choosing the address whose option value ends in the UPRN."""
    soup = BeautifulSoup(response.text, "html.parser")
    select = soup.find(id="lstBxAddrList")
    if not isinstance(select, Tag):
        raise SourceArgumentNotFound("postcode", postcode.strip())
    wanted = str(uprn).strip()
    labels = []
    for option in select.find_all("option"):
        value = str(option.get("value", ""))
        parts = value.split(";")
        if len(parts) != 2:
            continue
        labels.append(f"{parts[1]} ({parts[0].strip()})")
        if parts[1] == wanted:
            return {
                **_hidden_inputs(response),
                _POSTCODE_FIELD: postcode.strip(),
                _ADDRESS_FIELD: value,
                _SCHEDULE_BUTTON: "Continue",
            }
    raise SourceArgumentNotFoundWithSuggestions("uprn", wanted, labels)


def _date(heading: Tag) -> str:
    """The first date of the "Next collection on:" table following a bin heading."""
    table = heading.find_next_sibling("div")
    if not isinstance(table, Tag):
        raise ValueError("no schedule table after the bin heading")
    return table.find_all("div")[2].get_text(strip=True)


def _bin(heading: Tag) -> str:
    return heading.get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Dacorum Borough Council"
    DESCRIPTION = "Source for Dacorum Borough Council."
    URL = "https://www.dacorum.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "HP1 1AB", "uprn": 200004054631},
        "Test_002": {"postcode": "HP4 2EZ", "uprn": "100081111531"},
        "Test_003": {
            "postcode": "HP23 6BE",
            "uprn": "100080716575",
        },
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and your UPRN. Find your UPRN at "
            "https://www.findmyaddress.co.uk/ or by searching for your address "
            "on the council's [bin collections page](https://webapps.dacorum.gov.uk/bincollections/)."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(API_URL, pick=_search_form),
            retrievers.Lookup(
                API_URL,
                method="POST",
                data=lambda search_form, **_: search_form,
                pick=_pick_address,
            ),
        ),
        url=API_URL,
        method="POST",
        data=lambda search_form, selected, **_: selected,
        raise_for_status=True,
    )

    parse = parsers.HtmlParser(
        "#MainContent_updPnl div:has(> strong)",
        require=["#MainContent_updPnl"],
    )

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_bin,
        type_value_map={
            "Grey bin": wt.GENERAL_WASTE,
            "Grey bin and kerbside caddy": wt.GENERAL_WASTE,
            "Blue bin": wt.RECYCLABLES,
            "Blue bin and kerbside caddy": wt.RECYCLABLES,
            "Green bin": wt.GARDEN_WASTE,
            "Kerbside caddy": wt.FOOD_WASTE,
        },
        parse_date=date_parsers.for_format("%a, %d %b %Y"),
    )
