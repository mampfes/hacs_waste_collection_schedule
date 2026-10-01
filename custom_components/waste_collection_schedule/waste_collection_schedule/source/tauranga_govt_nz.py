import json
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.transformers import RowTransformer

PAGE_URL = "https://www.tauranga.govt.nz/services/rubbish-and-recycling/kerbside-collections/when-to-put-your-bins-out"
ADDRESS_URL = "https://www.tauranga.govt.nz/Services/SearchService.asmx/DoRIDStreetPredictiveSearch"


def _address_key(response, *keys, address, **_) -> tuple[str, str]:
    """The first predictive-search hit, as its ``(First, Second)`` pair."""
    hits = response.json().get("d") or []
    if not hits:
        raise SourceArgumentNotFound("address", address)
    hit = json.loads(hits[0])
    return hit["First"], hit["Second"]


def _form(response, *keys, **_) -> dict[str, str]:
    """The page's ASP.NET form, with the address fields filled in.

    The DNN module id in the field names changes, so the two address fields
    are found by name rather than hardcoded.
    """
    addr_1, addr_2 = keys[0]
    soup = BeautifulSoup(response.text, "html.parser")
    form = {
        tag["name"]: tag.get("value", "")
        for tag in soup.find_all("input")
        if tag.get("name") and tag.get("type") != "text"
    }
    address_field = soup.find(
        "input",
        attrs={"id": lambda x: x and "CollectionDaysSAP" in x and "Address" in x},
    )
    hidden_field = soup.find(
        "input",
        attrs={"id": lambda x: x and "CollectionDaysSAP" in x and "hdnValue" in x},
    )
    if address_field is None or hidden_field is None:
        raise ResponseShapeError(
            "tauranga_govt_nz", "no CollectionDaysSAP form fields on the page"
        )
    form[address_field["name"]] = addr_1  # type: ignore[index]
    form[hidden_field["name"]] = f"{addr_1}||{addr_2}"  # type: ignore[index]
    return form


@final
class Source(BaseSource):
    TITLE = "Tauranga City Council"
    DESCRIPTION = "Source script for Tauranga City Council"
    URL = "https://www.tauranga.govt.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "121 Castlewold Drive": {"address": "121 Castlewold Drive"},
        "70 Santa Monica Drive": {"address": "70 Santa Monica Drive"},
        "21 Wells Avenue": {"address": "21 Wells Avenue"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as you would on the council's "
            "[when to put your bins out](https://www.tauranga.govt.nz/services/rubbish-and-recycling/kerbside-collections/when-to-put-your-bins-out) page."
        ),
    }

    # Resolve the address with the predictive search, read the page's ASP.NET
    # form state, then post the form back with the address filled in.
    retrieve = retrievers.Request(
        PAGE_URL,
        method="POST",
        data=lambda key, form, **_: form,
        before=(
            retrievers.Lookup(
                ADDRESS_URL,
                method="POST",
                json=lambda address, **_: {
                    "prefixText": address,
                    "count": 12,
                    "contextKey": "test",
                },
                pick=_address_key,
            ),
            retrievers.Lookup(PAGE_URL, pick=_form),
        ),
    )

    # One block per date; a block lists each bin type it covers. Blocks for a
    # service the household is not subscribed to read "Not subscribed" and
    # carry no date, so the date pattern skips them.
    parse = parsers.HtmlLabelledDates(
        "div.binTypeContainer",
        label="div.binTypeText p:has(span.dot)",
        date="h5",
        date_pattern=r"(\w+ \d{1,2} \w+)",
        all_labels=True,
    )

    transform = RowTransformer(
        parse_date=date_parsers.nearest_year("%A %d %B"),
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Glass": wt.GLASS,
            "Garden waste": wt.GARDEN_WASTE,
            "Food scraps": wt.FOOD_WASTE,
        },
    )
