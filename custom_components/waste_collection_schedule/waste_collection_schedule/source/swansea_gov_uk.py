"""Swansea Council (Wales) bin collection dates."""

import json
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule import field_terms as ft
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street, text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.GossForm import GossFormDataParser
from waste_collection_schedule.transformers import RowTransformer

# The postcode search (JSON-RPC answered as JSONP) gives the postcode's
# addresses; the address is then posted to a GOSS form, whose answer carries
# the bin information as HTML in the page's FormData (POSTCODEINPUT_1 /
# DISPLAYBININFO). That has a block per collection week ("pink week", "green
# week") listing what is collected in it, and month calendars whose day cells
# are marked calendar-pink, calendar-green or calendar-both.
POSTCODE_URL = "https://www.swansea.gov.uk/apiserver/postcode"
FORM_URL = "https://www.swansea.gov.uk/recyclingsearch"
_FORM = "RECYCLINGSEARCHMYACCOUNT"
_WEEKS = {
    "calendar-pink": ("pink",),
    "calendar-green": ("green",),
    "calendar-both": ("pink", "green"),
}
_MONTHS = (
    "january february march april may june july august september october "
    "november december"
).split()


def _normalise(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


def _address_text(address: dict) -> str:
    parts = [address.get(f"line{i}", "") for i in range(1, 6)]
    parts += [address.get("town", ""), address.get("postcode", "")]
    return ", ".join(part for part in parts if part)


def _search_params(*_, post_code, **__) -> dict[str, str]:
    rpc = {
        "id": 1,
        "method": "postcodeSearch",
        "params": {"provider": "", "postcode": post_code},
    }
    return {"callback": "cb", "jsonrpc": json.dumps(rpc)}


def _address(response, *, post_code, street_name=None, uprn=None, **_) -> dict:
    """The address the configuration names among the postcode's addresses."""
    text = response.text
    payload = json.loads(text[text.index("(") + 1 : text.rindex(")")])
    addresses = [a for a in payload.get("result") or [] if "udprn" in a]
    if not addresses:
        raise SourceArgumentNotFound("post_code", post_code)
    if uprn:
        wanted = str(uprn).strip().lstrip("0")
        for address in addresses:
            if address["udprn"].lstrip("0") == wanted:
                return address
        raise SourceArgumentNotFoundWithSuggestions(
            "uprn", uprn, [a["udprn"] for a in addresses]
        )
    if street_name:
        needle = _normalise(street_name)
        for address in addresses:
            if needle in _normalise(_address_text(address)):
                return address
        raise SourceArgumentNotFoundWithSuggestions(
            "street_name", street_name, sorted({_address_text(a) for a in addresses})
        )
    # Collections are scheduled per street, so any address in the postcode does.
    return addresses[0]


def _form(response, *_, **__) -> dict[str, str]:
    """The form's action and session tokens."""
    action = re.search(r'action="([^"]*processsubmission[^"]*)"', response.text)
    fields = retrievers.form_inputs(response.text, hidden_only=True)
    if action is None:
        raise ValueError("Swansea recycling search form not found")
    return {"action": action.group(1).replace("&amp;", "&"), **fields}


def _submit(address, form, **_) -> dict[str, str]:
    return {
        f"{_FORM}_PAGESESSIONID": form.get(f"{_FORM}_PAGESESSIONID", ""),
        f"{_FORM}_SESSIONID": form.get(f"{_FORM}_SESSIONID", ""),
        f"{_FORM}_NONCE": form.get(f"{_FORM}_NONCE", ""),
        f"{_FORM}_VARIABLES": "e30=",
        f"{_FORM}_PAGENAME": "POSTCODEINPUT",
        f"{_FORM}_PAGEINSTANCE": "0",
        f"{_FORM}_ADDRESSLOOKUPPOSTCODE": address.get("postcode", ""),
        f"{_FORM}_ADDRESSLINE1": address.get("line1", ""),
        f"{_FORM}_ADDRESSLINE2": address.get("line2", ""),
        f"{_FORM}_ADDRESSLINE3": address.get("line3", ""),
        f"{_FORM}_TOWN": address.get("town", ""),
        f"{_FORM}_POSTCODE": address.get("postcode", ""),
        f"{_FORM}_UPRN": address["udprn"],
        f"{_FORM}_FORMACTION_NEXT": f"{_FORM}_NEXTBUTTON",
    }


def _month(caption: str) -> str:
    """ "11 2026" from "November 2026" or "i18n{sc.commercialwaste.month11} 2026"."""
    year = re.search(r"(\d{4})\s*$", caption)
    number = re.search(r"month(\d{1,2})\}", caption)
    if number is None:
        word = caption[: year.start()].strip().lower() if year else ""
        month = _MONTHS.index(word) + 1 if word in _MONTHS else 0
    else:
        month = int(number.group(1))
    return f"{month} {year.group(1) if year else ''}"


def _items(day, source) -> list[tuple[str, str]]:
    """``(date, item)`` rows: what the marked week collects, on that day."""
    root = list(day.parents)[-1]
    weeks = next((_WEEKS[c] for c in day.get("class") or [] if c in _WEEKS), ())
    caption = day.find_parent("table").find("caption").get_text(strip=True)
    date = f"{day.get_text(strip=True)} {_month(caption)}"
    rows = []
    for week in weeks:
        for item in root.select(
            f"article.myaccount-block__collection--{week} li.myaccount-block__list-item"
        ):
            text = " ".join(item.get_text().split())
            key = re.search(r"\.(\w+)\}$", text)
            rows.append((date, key.group(1) if key else text))
    return rows


@final
class Source(BaseSource):
    TITLE = "Swansea Council"
    DESCRIPTION = "Source script for swansea.gov.uk"
    URL = "https://swansea.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Cwmdonkin Drive": {"street_name": "cwmdonkin", "post_code": "SA20RA"},
        "Cwmdonkin Drive (UPRN)": {"post_code": "SA2 0RA", "uprn": "100100351698"},
        "Postcode only": {"post_code": "sa2 0ra"},
    }

    PARAMS = (
        postcode("post_code"),
        street("street_name", optional=True),
        text_field("uprn", term=ft.UPRN, optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the full postcode of your property. Collections are "
            "scheduled per street, so that is usually enough; to pick one "
            "address, also enter part of it (e.g. the street name) or its "
            "Unique Property Reference Number (UPRN). Since the v3 pipeline "
            "migration, the pink and green collection weeks are reported as "
            "the waste types collected in them (as listed for your address), "
            "using canonical, localised names. Update filters, automations "
            "and customisations using the old labels."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        lambda address, form, **_: form["action"],
        method="POST",
        before=(
            retrievers.Lookup(POSTCODE_URL, params=_search_params, pick=_address),
            retrievers.Lookup(FORM_URL, pick=_form),
        ),
        data=_submit,
    )

    parse = GossFormDataParser(
        "DISPLAYBININFO",
        pages=["POSTCODEINPUT_1"],
        parser=parsers.HtmlParser(
            "table.bin-calendar td.calendar-pink, table.bin-calendar "
            "td.calendar-green, table.bin-calendar td.calendar-both"
        ),
    )
    preprocess = preprocessors.ExplodeList(_items)

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %m %Y"),
        type_value_map={
            "paperandcardboard": wt.PAPER,
            "glassandcans": wt.RECYCLABLES,
            "plastic": wt.PLASTIC,
            "foodwaste": wt.FOOD_WASTE,
            "gardenwaste": wt.GARDEN_WASTE,
            "nonrecyclables": wt.GENERAL_WASTE,
        },
    )
