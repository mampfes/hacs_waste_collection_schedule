import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import Lookup, Request
from waste_collection_schedule.transformers import HtmlTransformer

_BASE_URL = "https://cheltenham-host01.oncreate.app"
_WEBPAGE_TOKEN = "3e546dda8816902a52a5e3f68096b16d45e279f1f634e9433b899675b5349448"
_SUBPAGE_ID = "PAG0000686GBCNH1"
_CELL_ID = "PCL0005127GBCNH1"
_FRAGMENT_ID = "PCF0019732GBCNH1"
_WIDGET_GROUP_ID = "PWG0002596GBCNH1"
_SUBMIT_FRAGMENT_ID = "PCF0016614GBCNH1"
_PAGE_URL = (
    f"{_BASE_URL}/w/webpage/collection-lookup"
    f"?webpage_subpage_id={_SUBPAGE_ID}&webpage_token={_WEBPAGE_TOKEN}"
)

# Identifiers within the schedule response.
_SCHEDULE_OBJECT_ID = "OBJ0000370GBCNH1"
_FRAGMENT_BIN_TYPE = "PCF0019703GBCNH1"
_FRAGMENT_NEXT_DATE = "PCF0019810GBCNH1"

# The XMLHttpRequest header is what makes the server answer with the JSON
# fragment (its HTML under "data") rather than the full page.
_XHR = {"X-Requested-With": "XMLHttpRequest"}

_TYPE_MAP = {
    "Refuse bin": wt.GENERAL_WASTE,
    "Green recycling box": wt.RECYCLABLES,
    "Blue cardboard bag": wt.PAPER,
    "Food caddy": wt.FOOD_WASTE,
    "Garden waste bin": wt.GARDEN_WASTE,
}


def _form_tokens(response, *_, **__) -> tuple[str, str]:
    """The form's CSRF token and the key of its search collection."""
    html = response.json().get("data", "")
    form_check = re.search(r'name="form_check" value="([a-f0-9]+)"', html)
    collection_key = re.search(r'data-unique_key="(C_[a-f0-9]+)"', html)
    if form_check is None or collection_key is None:
        raise ValueError("Cheltenham's collection lookup form has changed")
    return form_check.group(1), collection_key.group(1)


def _answer(tokens, property_id) -> dict[str, str]:
    form_check, collection_key = tokens
    prefix = f"payload[{_SUBPAGE_ID}][{_WIDGET_GROUP_ID}][{_CELL_ID}][search][{collection_key}]"
    return {
        "form_check": form_check,
        "submitted_page_storage_key": "/w/webpage/collection-lookup",
        "submitted_page_id": _SUBPAGE_ID,
        "submitted_widget_group_id": _WIDGET_GROUP_ID,
        "submitted_widget_group_type": "search",
        f"{prefix}[{_FRAGMENT_ID}]": str(property_id),
        f"{prefix}[{_SUBMIT_FRAGMENT_ID}]": "Next",
    }


def _cell(row, fragment_id: str) -> str:
    div = row.find("div", attrs={"data-fragment_id": fragment_id})
    return str(div.get("data-current_value", "")).strip() if div else ""


@final
class Source(BaseSource):
    TITLE = "Cheltenham Borough Council"
    DESCRIPTION = "Source for Cheltenham Borough Council waste collection schedule"
    URL = "https://www.cheltenham.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Second property": {"property_id": 55297},
    }

    PARAMS = (text_field("property_id", "Property ID", coerce=str),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://cheltenham-host01.oncreate.app/w/webpage/collection-lookup, "
            "enter your postcode, select your address, then note the numeric "
            "property ID shown in the page."
        ),
    }

    # 1. the form page (its HTML is in the JSON's "data") gives the CSRF token
    # and the collection key, 2. posting the property id answers the schedule.
    retrieve = Request(
        _PAGE_URL,
        method="POST",
        headers=_XHR,
        data=lambda tokens, property_id, **_: _answer(tokens, property_id),
        before=(Lookup(_PAGE_URL, headers=_XHR, pick=_form_tokens),),
    )
    # The same response also embeds address rows; only the schedule rows carry
    # this object id. A row without a date reads "N/A".
    parse = parsers.HtmlParser(
        f'tr[data-base_object_id="{_SCHEDULE_OBJECT_ID}"]', from_json_key="data"
    )
    transform = HtmlTransformer(
        date_getter=lambda row: _cell(row, _FRAGMENT_NEXT_DATE),
        type_getter=lambda row: _cell(row, _FRAGMENT_BIN_TYPE),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        skip_unparseable_dates=True,
        type_value_map=_TYPE_MAP,
    )
