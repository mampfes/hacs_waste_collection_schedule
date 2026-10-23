import html
import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import Lookup, Request
from waste_collection_schedule.transformers import JsonTransformer

_BASE_URL = "https://doncaster-wasterecycling.oncreate.app"
_PAGE_URL = f"{_BASE_URL}/w/webpage/bin-query"
# The council site renders its pages from JSON/HTML fragments requested by script.
_XHR = {"X-Requested-With": "XMLHttpRequest"}
_PAGE_REQUEST = {"_dummy": 1, "_update_page_content_request": 1}

_TYPE_MAP = {
    "Refuse": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Green Garden Waste Collection Service": wt.GARDEN_WASTE,
}


def _normalise(text: str) -> str:
    """Upper case, drop commas and collapse white space for address comparison."""
    return re.sub(r"\s+", " ", html.unescape(text).replace(",", " ")).strip().upper()


def _postcode(value: str) -> str:
    """The postcode as "AB1 2CD" (outward code, space, three character inward code)."""
    compact = re.sub(r"\s+", "", value).upper()
    return f"{compact[:-3]} {compact[-3:]}" if len(compact) > 3 else compact


def _form(response, *_, **__) -> dict:
    """The search form of the bin query page: where it posts, its fields and the
    two boxes to fill. Its tokens are single use, so every search reads a fresh one."""
    form = BeautifulSoup(response.json()["data"], "html.parser").find(
        "form", class_="page_widget_group"
    )
    if form is None:
        raise ValueError("bin lookup form not found on the council page")
    fields = {
        i["name"]: i.get("value", "")
        for i in form.find_all("input", type="hidden")
        if i.get("name")
    }
    # The field names are generated; find the boxes by their labels.
    boxes = {}
    for label in form.find_all("label"):
        text = label.get_text(" ", strip=True).lower()
        if label.get("for") and text.startswith("postcode"):
            boxes["postcode"] = label["for"]
        elif label.get("for") and text.startswith("property"):
            boxes["property"] = label["for"]
    submit = form.find("input", type="submit")
    if "postcode" not in boxes or submit is None or not submit.get("name"):
        raise ValueError("bin lookup form has changed on the council page")
    fields[submit["name"]] = submit.get("value", "Search")
    return {
        "action": _BASE_URL + html.unescape(form["data-submit_destination"]),
        "fields": fields,
        "boxes": boxes,
    }


def _search_data(form: dict, postcode_value: str, address: str) -> dict:
    data = dict(form["fields"])
    data[form["boxes"]["postcode"]] = postcode_value
    if "property" in form["boxes"]:
        data[form["boxes"]["property"]] = address
    return data


def _results(response, *_, **__) -> dict:
    """The (address, link) pairs of a result page and how many properties matched."""
    soup = BeautifulSoup(response.json()["data"], "html.parser")
    addresses = []
    for a in soup.find_all("a", href=re.compile(r"/address-collections")):
        label = a.get("aria-label", "")
        prefix = "View collection details,"
        addresses.append(
            (
                (label[len(prefix) :] if label.startswith(prefix) else label).strip(),
                a["href"],
            )
        )
    match = re.search(r"Results\s+\d+-\d+\s+of\s+(\d+)\s+found", soup.get_text())
    return {"addresses": addresses, "total": int(match.group(1)) if match else None}


def _first_search(response, *keys, postcode, **__) -> dict:
    results = _results(response)
    if not results["addresses"]:
        raise SourceArgumentNotFound(
            "postcode",
            postcode,
            "the council's lookup returned no properties for this postcode, "
            "please check it and try again.",
        )
    return results


def _too_many(*keys, **_) -> bool:
    first = keys[2]
    return first["total"] is not None and first["total"] > len(first["addresses"])


def _collection_link(keys, address: str) -> str:
    """The link of the one property whose address starts with the house number or name."""
    first, filtered = keys[2], keys[4]
    # If the council's own filter found nothing, the first page still feeds the
    # suggestions.
    addresses = (filtered or {}).get("addresses") or first["addresses"]
    wanted = _normalise(address)
    # '1' matches '1 High Street' but not '10 High Street'.
    matches = [
        (name, link)
        for name, link in addresses
        if _normalise(name).startswith(wanted)
        and not _normalise(name)[len(wanted) :][:1].isalnum()
    ]
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, sorted({name for name, _ in addresses})
        )
    distinct = sorted({name for name, _ in matches})
    if len(distinct) > 1:
        raise SourceArgAmbiguousWithSuggestions("address", address, distinct)
    return matches[0][1]


def _search(form_index: int, first: bool) -> Lookup:
    return Lookup(
        lambda *keys, **_: keys[form_index]["action"],
        method="POST",
        data=lambda *keys, postcode, address, **_: _search_data(
            keys[form_index],
            _postcode(postcode),
            # Too many properties for one page: let the council filter by name
            # too. Its box only matches text inside the house number or name, so
            # send the part before the first comma.
            "" if first else address.split(",")[0].strip(),
        ),
        headers=_XHR,
        pick=_first_search if first else _results,
        when=None if first else _too_many,
    )


def _form_lookup(when=None) -> Lookup:
    return Lookup(
        _PAGE_URL,
        method="POST",
        data=_PAGE_REQUEST,
        headers=_XHR,
        pick=_form,
        when=when,
    )


@final
class Source(BaseSource):
    TITLE = "City of Doncaster Council"
    DESCRIPTION = (
        "Source for doncaster.gov.uk services for the City of Doncaster Council, UK."
    )
    URL = "https://doncaster.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Askern Methodist Church": {
            "postcode": "DN6 0LF",
            "address": "Askern Methodist Church",
        },
        "Seventh Day Adventist Church": {
            "postcode": "DN5 9QU",
            "address": "Seventh Day Adventist Church",
        },
        "Scawthorpe Social Club": {
            "postcode": "dn5 9nt",
            "address": "Scawthorpe Social Club",
        },
    }

    PARAMS = (postcode(), house_number("address"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://doncaster-wasterecycling.oncreate.app/w/webpage/bin-query "
            "and enter your postcode and your house number or name. Use the same "
            "postcode and the house number or name of your property as the "
            "arguments. If several properties match, the error message lists the "
            "exact addresses to choose from."
        ),
    }

    # 1. open the page (sets the session cookie the lookup needs), 2. read the
    # search form, 3. search by postcode, 4-5. if too many properties matched for
    # one page, read the form again and search by name as well, 6. fetch the
    # collection page of the chosen property.
    retrieve = Request(
        lambda *keys, address, **_: _BASE_URL + _collection_link(keys, address),
        method="POST",
        data=_PAGE_REQUEST,
        headers=_XHR,
        before=(
            Lookup(_PAGE_URL, pick=lambda response, *_, **__: None),
            _form_lookup(),
            _search(1, first=True),
            _form_lookup(when=_too_many),
            _search(3, first=False),
        ),
    )
    parse = parsers.AttributeJsonParser(
        "[data-params*=template_data]",
        "data-params",
        "template_data",
        "events",
        from_json_key="data",
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=_TYPE_MAP,
    )
