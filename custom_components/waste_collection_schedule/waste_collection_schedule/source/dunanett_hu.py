"""Dunanett annual text calendars published by the supported municipalities."""

import re
from dataclasses import replace
from datetime import date, datetime
from html import unescape
from typing import Any, ClassVar, TypedDict, final
from urllib.parse import unquote, urlsplit

from waste_collection_schedule import parsers, response_shape, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.regions import region
from waste_collection_schedule.service import HuWasteCalendar as hu
from waste_collection_schedule.transformers import ICSTransformer

# Runtime lookup: these municipalities publish the machine-readable calendars.
_SITES = {
    "Pusztaszabolcs": "https://pusztaszabolcs.hu",
    "Rácalmás": "https://racalmas.hu",
}


class _Title(TypedDict):
    rendered: str


class _Media(TypedDict):
    date: str
    source_url: str
    title: _Title


def _site(municipality: str) -> str:
    if municipality not in _SITES:
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", municipality, list(_SITES)
        )
    return _SITES[municipality]


def _calendar_urls(response: Any, *, municipality: str, **_: Any) -> list[str]:
    """Latest published annual calendar per year, requiring the current year."""
    records = response_shape.validate(
        response.json(), list[_Media], source_name="dunanett_hu"
    )
    # A bounded lookup is intentional: never accept a truncated media catalogue.
    headers = {key.lower(): value for key, value in response.headers.items()}
    response_shape.expect(
        headers.get("x-wp-totalpages") in ("0", "1"),
        source_name="dunanett_hu",
        detail="media lookup is missing pagination headers or exceeds one page",
        raw=dict(response.headers),
    )
    pattern = (
        rf"(?:\d+[_ -]+)?{re.escape(hu.fold(municipality))}[_ -]+"
        r"hulladeknaptar[_ -]*(20\d{2})(?:[_ -].*)?"
    )
    calendars: dict[int, tuple[datetime, str]] = {}
    for record in records:
        url = record["source_url"]
        parsed = urlsplit(url)
        filename = hu.fold(unquote(parsed.path.rsplit("/", 1)[-1]))
        match = re.fullmatch(pattern + r"\.pdf", filename)
        title = re.fullmatch(pattern, hu.fold(unescape(record["title"]["rendered"])))
        if not match or not title:
            continue
        year = int(match.group(1))
        response_shape.expect(
            title.group(1) == str(year)
            and parsed.scheme == "https"
            and parsed.netloc == urlsplit(_SITES[municipality]).netloc,
            source_name="dunanett_hu",
            detail="calendar title, filename year or municipality host disagree",
            raw=record,
        )
        if year < date.today().year:
            continue
        try:
            published = datetime.fromisoformat(record["date"])
        except ValueError:
            raise response_shape.ResponseShapeError(
                "dunanett_hu", "invalid media publication timestamp"
            ) from None
        candidate = (published, url)
        if year not in calendars or candidate > calendars[year]:
            calendars[year] = candidate
    response_shape.expect(
        date.today().year in calendars,
        source_name="dunanett_hu",
        detail=f"no current annual calendar for {municipality} ({date.today().year})",
        raw=records,
    )
    return [calendars[year][1] for year in sorted(calendars)]


@final
class Source(BaseSource):
    TITLE = "Dunanett Nonprofit Kft."
    DESCRIPTION = (
        "Source for Dunanett waste calendars in Pusztaszabolcs and Rácalmás, Hungary."
    )
    URL = "https://www.dunanett.hu"
    COUNTRY = "hu"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@nevembalint"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    TEST_CASES: ClassVar[dict] = {
        "Pusztaszabolcs": {"municipality": "Pusztaszabolcs"},
        "Rácalmás": {"municipality": "Rácalmás"},
    }
    PARAMS = (replace(municipality(), widget="select", options=list(_SITES)),)
    REGIONS: ClassVar[list] = [
        region(town, url=site, municipality=town) for town, site in _SITES.items()
    ]
    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Select Pusztaszabolcs or Rácalmás. Annual calendars are published at "
            "https://pusztaszabolcs.hu/2026/01/2026-evi-hulladeknaptar and "
            "https://racalmas.hu/category/hirek/; the provider is https://www.dunanett.hu. "
            "The source discovers municipal PDF uploads automatically, uses the latest "
            "published version for each current/future year, and fails if the current "
            "year is unavailable rather than reusing an expired calendar.\n\n"
            "General waste, recycling and garden waste are included. Where the PDF "
            "restricts January collections to Christmas trees, those events use the "
            "Garden Waste category with a tree-only description: remove decorations "
            "and other waste; ordinary garden waste is not accepted. Bulky waste is "
            "by appointment and has no calendar dates.\n\n"
            "These are the annual planned dates. Ad-hoc weather cancellations or "
            "street-specific replacement notices are not included; check municipal "
            "news and https://www.dunanett.hu/nonprofit/hireink/. Other Dunanett "
            "municipalities are not yet supported because their current calendars "
            "are image-only or use different document formats."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            lambda municipality, **_: f"{_site(municipality)}/wp-json/wp/v2/media",
            params={
                "search": "hulladeknaptar",
                "per_page": 100,
                "_fields": "date,source_url,title",
            },
            headers=lambda municipality, **_: {"Referer": f"{_site(municipality)}/"},
            pick=_calendar_urls,
            timeout=60,
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(
            lambda url, urls, **_: url,
            headers=lambda url, urls, municipality, **_: {
                "Referer": f"{_site(municipality)}/"
            },
            timeout=60,
        ),
    )
    parse = parsers.EachResponse(
        hu.CalendarParser(
            types={"szelektív": "szelektív", "zöldhulladék": "zöldhulladék"},
            strict=True,
            expected_municipality=lambda municipality, **_: municipality,
            year_from_url=True,
            january_trees=True,
            holiday_moves=True,
        )
    )
    transform = ICSTransformer(
        type_value_map={
            hu.GENERAL: wt.GENERAL_WASTE,
            "szelektív": wt.RECYCLABLES,
            "zöldhulladék": wt.GARDEN_WASTE,
            hu.CHRISTMAS_TREES: wt.GARDEN_WASTE,
        },
        description_key=lambda record: (
            hu.CHRISTMAS_TREE_DESCRIPTION if record[1] == hu.CHRISTMAS_TREES else None
        ),
    )
