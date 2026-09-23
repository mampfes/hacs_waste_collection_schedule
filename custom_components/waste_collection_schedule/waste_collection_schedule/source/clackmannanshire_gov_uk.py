"""Clackmannanshire Council (clacks.gov.uk).

Demonstrates ``IcsSessionRetriever`` for a postcode search followed by a property
page that offers the calendars as downloads: the first step lists the properties
of a postcode and resolves the configured address to its detail page, the second
reads that page's ``.ics`` links, and the feed request fetches them. The first
link is the property's bin calendar; the second is the brown-bin calendar of
residents holding a paid garden waste permit, fetched only when ``garden_waste``
is set (its titles carry the permit year, which is dropped). The calendars are
rolling rather than per-year, hence ``lookahead_month=None``.
"""

import re
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    boolean,
    postcode,
    street_address,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.clacks.gov.uk"
_SEARCH_URL = f"{_BASE_URL}/environment/wastecollection/"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

_YEAR_SUFFIX_RE = re.compile(r"\s*\d{4}\s*$")


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace(",", " ").split())


def _search(postcode: str, **_: Any) -> "dict[str, str]":
    return {"pc": postcode.strip()}


def _property_page(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """The configured address's detail page, from the postcode's property list."""
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find("div", {"class": "highlight"})
    links: list[Tag] = []
    if isinstance(results, Tag):
        links = [
            a
            for a in results.find_all("a")
            if isinstance(a, Tag)
            and str(a.get("href", "")).startswith("/environment/wastecollection/id/")
        ]
    if not links:
        raise SourceArgumentNotFound(
            "postcode",
            context["postcode"],
            "No properties were found for this postcode on the Clackmannanshire "
            "Council website, please check the spelling and try again.",
        )

    wanted = _normalize(str(context["address"]))
    for a in links:
        if _normalize(a.get_text()) == wanted:
            return {"property_url": urljoin(_BASE_URL, str(a["href"]))}
    for a in links:
        if wanted in _normalize(a.get_text()):
            return {"property_url": urljoin(_BASE_URL, str(a["href"]))}
    raise SourceArgumentNotFoundWithSuggestions(
        "address", context["address"], [a.get_text(strip=True) for a in links]
    )


def _calendar_links(response: Any, context: "dict[str, Any]") -> "dict[str, list[str]]":
    """The property's calendar downloads: its bins, then the garden permit's."""
    soup = BeautifulSoup(response.text, "html.parser")
    urls = [
        urljoin(_BASE_URL, str(a["href"]))
        for a in soup.find_all("a", href=True)
        if str(a["href"]).lower().endswith(".ics")
    ]
    if not urls:
        raise SourceArgumentNotFound(
            "address",
            context["address"],
            "No calendar (.ics) links were found for this property.",
        )
    return {"ics_urls": urls}


@final
class Source(BaseSource):
    TITLE = "Clackmannanshire Council"
    DESCRIPTION = "Source for Clackmannanshire Council, UK waste collection."
    URL = _BASE_URL
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown postcode": {"postcode": "ZZ99 9ZZ", "address": "1 Nowhere Road"},
        "Unknown address": {"postcode": "FK10 3EY", "address": "999 Nowhere Road"},
    }

    TEST_CASES: ClassVar[dict] = {
        "16 Crophill, Sauchie": {
            "postcode": "FK10 3EY",
            "address": "16 Crophill, Sauchie",
        },
        "Elim Pentecostal Church, Alloa": {
            "postcode": "FK10 1EB",
            "address": "Elim Pentecostal Church, Alloa",
        },
        "With garden waste permit": {
            "postcode": "FK10 3EY",
            "address": "16 Crophill, Sauchie",
            "garden_waste": True,
        },
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your postcode, e.g. 'FK10 3EY', and the address exactly as shown "
            "in the search results on the council website, e.g. "
            "'16 Crophill, Sauchie'. Set garden waste to true if you hold a paid "
            "garden waste (brown bin) permit, to include its collection dates."
        ),
    }

    PARAMS = (
        postcode(postcode_field="postcode"),
        street_address(field="address"),
        boolean("garden_waste", label="Garden waste (brown bin) permit", default=False),
    )

    retrieve = IcsSessionRetriever(
        headers=_HEADERS,
        steps=[
            {"url": _SEARCH_URL, "params": _search, "extract": _property_page},
            {"url": lambda property_url, **_: property_url, "extract": _calendar_links},
        ],
        feed_url=lambda ics_urls, garden_waste=False, **_: (
            ics_urls[:2] if garden_waste else ics_urls[:1]
        ),
        lookahead_month=None,
    )

    parse = IcsFeedsParser(
        parsers.IcsParser(), clean=lambda title: _YEAR_SUFFIX_RE.sub("", title).strip()
    )

    # Verified against the council's own bin guidance (clacks.gov.uk): blue =
    # plastic, tins, cans and foil; grey = clean, dry paper and card; green =
    # material that cannot be recycled; brown = garden material (permit
    # holders); food caddy = food. Explicit because the shared vocabulary reads
    # "blue bin" as paper.
    transform = ICSTransformer(
        type_value_map={
            "blue bin": wt.RECYCLABLES,
            "grey bin": wt.PAPER,
            "green bin": wt.GENERAL_WASTE,
            "brown bin": wt.GARDEN_WASTE,
            "food caddy": wt.FOOD_WASTE,
        }
    )
