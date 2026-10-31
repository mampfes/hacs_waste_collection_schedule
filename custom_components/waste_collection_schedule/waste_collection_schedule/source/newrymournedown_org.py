"""Newry, Mourne and Down District Council postcode/address calendar lookup."""

import re
from typing import ClassVar, final
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from waste_collection_schedule import config_params, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.NewryMourneDownCalendar import CalendarParser
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.newrymournedown.org"
_PAGE = f"{_URL}/weekly-bin-collection-and-calendar"


def _postcode_form(postcode, **_):
    match = re.fullmatch(r"(BT\d{2})\s*(\d[A-Z]{2})", postcode.upper().strip())
    if match is None:
        raise SourceArgumentException(
            "postcode", "Enter a complete BT postcode, e.g. BT35 7DN"
        )
    return {
        "PostcodeBT": match[1],
        "PostcodeEND": match[2],
        "postback": "1",
        "submit_btn": "Search",
    }


def _calendar_link(response, *_, house_number, **__):
    choices = {}
    for link in BeautifulSoup(response.text, "html.parser").select(
        'a[href*="/bin-collections/"]'
    ):
        row = link.find_parent("li")
        if row is None:
            continue
        address = row.get_text(" ", strip=True)
        match = re.match(r"(\d+\w*)\s", address)
        if match:
            choices.setdefault(match[1].upper(), set()).add(
                urljoin(response.url, link["href"])
            )
    key = str(house_number).strip().upper()
    if key not in choices:
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", house_number, sorted(choices)
        )
    if len(choices[key]) != 1:
        raise SourceArgumentException(
            "house_number", "More than one calendar matches this address"
        )
    return next(iter(choices[key]))


def _given_calendar(*_, url=None, **__):
    if not url:
        return None
    parsed = urlparse(url.strip())
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ("newrymournedown.org", "www.newrymournedown.org")
        or not re.fullmatch(r"/bin-collections/[^/]+\.pdf", parsed.path, re.I)
    ):
        raise SourceArgumentException(
            "url", "Use the council's HTTPS bin-collections PDF link"
        )
    return url.strip()


@final
class Source(BaseSource):
    TITLE = "Newry, Mourne and Down District Council"
    DESCRIPTION = "Source for Newry, Mourne and Down District Council bin calendars."
    URL = _URL
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    TEST_CASES: ClassVar[dict] = {
        "9 Derrymore Road, Bessbrook": {"postcode": "BT35 7DN", "house_number": "9"},
        "Published Wednesday calendar": {
            "url": f"{_URL}/bin-collections/WED-Z1.pdf?v=5"
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unlisted house number": {"postcode": "BT35 7DN", "house_number": "66"},
        "Invalid postcode": {"postcode": "not a postcode", "house_number": "9"},
        "Unsupported calendar URL": {"url": "https://example.com/calendar.pdf"},
    }
    PARAMS = (
        config_params.alternatives(
            [config_params.postcode(), config_params.house_number()],
            [config_params.text_field("url", "Council calendar PDF URL")],
        ),
    )
    HOWTO: ClassVar[dict] = {
        "en": (
            "Either enter the postcode and house number shown by the council's lookup at "
            "https://www.newrymournedown.org/weekly-bin-collection-and-calendar. "
            "Or paste your council bin-collections PDF link into url instead. "
            "The direct PDF option works independently of the address portal, "
            "which can be temporarily unavailable. Dates, including holiday changes, come from the printed calendar. "
            "Black bins are general waste, blue bins recycling, and brown bins "
            "combined food/garden waste (Organic). Unnumbered properties and "
            "ambiguous house numbers are not supported by this address lookup."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _PAGE,
                method="POST",
                data=_postcode_form,
                pick=_calendar_link,
                given=_given_calendar,
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = CalendarParser()
    transform = ICSTransformer(
        type_value_map={
            "Black bin": wt.GENERAL_WASTE,
            "Blue bin": wt.RECYCLABLES,
            "Brown bin": wt.ORGANIC,
        }
    )
