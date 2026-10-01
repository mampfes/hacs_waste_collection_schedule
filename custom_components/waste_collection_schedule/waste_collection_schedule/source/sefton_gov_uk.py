from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = "https://www.sefton.gov.uk/bins-and-recycling/bins-and-recycling/when-is-my-bin-collection-day/"


def _hidden_inputs(response, limit=None) -> dict[str, str]:
    soup = BeautifulSoup(response.content, "html.parser")
    hidden = soup.find_all("input", {"type": "hidden"}, limit=limit)
    return {x["name"]: x["value"] for x in hidden}


def _form_tokens(response, **_) -> dict[str, str]:
    """The anti-forgery fields of the search form (the first two hidden inputs)."""
    return _hidden_inputs(response, limit=2)


def _pick_address(response, tokens, *, house_number_or_name, **_) -> dict[str, str]:
    """The form body selecting the address whose option starts with the house."""
    wanted = str(house_number_or_name).upper()
    soup = BeautifulSoup(response.content, "html.parser")
    options = soup.select("select option")
    for option in options:
        if option.text.upper().strip().startswith(wanted):
            return {
                **_hidden_inputs(response),
                "action": "Select",
                "selectedValue": option["value"],
            }
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number_or_name",
        wanted,
        [option.text.strip() for option in options],
    )


def _bin(table) -> str:
    """The bin name is the first word of the first cell ("Residual 240 wheelie bin")."""
    return table.td.get_text().split()[0]


def _date(table) -> str:
    return table.find_all("td")[2].get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Sefton Council"
    DESCRIPTION = "Source for Sefton Council, UK"
    URL = "https://www.sefton.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Issue2369": {
            "house_number_or_name": "1",
            "streetname": "Ken Mews",
            "postcode": "L20 6GF",
        },
        "Housename": {
            "house_number_or_name": "Gladstone House",
            "streetname": "Rosemary Lane",
            "postcode": "L37 3JB",
        },
        "Issue2496": {
            "house_number_or_name": 22,
            "streetname": "Elton Avenue",
            "postcode": "L23 8UW",
        },
    }

    PARAMS = (
        postcode(),
        street("streetname"),
        house_number("house_number_or_name"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Using a browser, go to [sefton.gov.uk](https://www.sefton.gov.uk/bins-and-recycling/bins-and-recycling/when-is-my-bin-collection-day/). "
            "For _Postcode_ and _Street name_ use the values you'd enter on Sefton's first page. "
            "Search, and then for _House Name or Number_ you need the value that comes before the street name you entered on the first screen. "
            "e.g. if your streetname is 'Liverpool Road' and the select box has an option of '1A Liverpool Road' enter '1A' as your _House Name or Number_."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(API_URL, pick=_form_tokens),
            retrievers.Lookup(
                API_URL,
                method="POST",
                data=lambda tokens, postcode, streetname, **_: {
                    **tokens,
                    "Postcode": postcode,
                    "Streetname": streetname,
                },
                pick=_pick_address,
            ),
        ),
        url=API_URL,
        method="POST",
        data=lambda tokens, selected, **_: selected,
    )

    parse = parsers.HtmlParser("table")

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_bin,
        type_value_map={
            "Residual": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green": wt.GARDEN_WASTE,
        },
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
