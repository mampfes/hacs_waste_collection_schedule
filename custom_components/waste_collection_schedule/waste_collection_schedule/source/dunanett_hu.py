"""Dunanett annual text calendars published by the supported municipalities."""

import re
from dataclasses import replace
from datetime import date, datetime
from html import unescape
from types import SimpleNamespace
from typing import Any, ClassVar, TypedDict, final
from urllib.parse import unquote, urljoin, urlsplit

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
    "Perkáta": "https://perkata.munipolis.hu/p/hulladekszallitas",
    "Nagyvenyim": "https://nagyvenyim.hu/wp-sitemap-posts-post-1.xml",
    "Dunaföldvár": "https://dunafoldvar.hu/hir-kategoria/hulladekokkal-kapcsolatos-informaciok/",
}
_MEDIA_TOWNS = {"Pusztaszabolcs", "Rácalmás"}


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


def _annual_targets(
    response: Any, *, municipality: str, **_: Any
) -> list[tuple[str, int]]:
    """Published current/future calendars; competing links require human review."""
    if municipality in _MEDIA_TOWNS:
        return [
            (
                url,
                int(
                    re.findall(
                        r"20\d{2}", unquote(urlsplit(url).path).rsplit("/", 1)[-1]
                    )[0]
                ),
            )
            for url in _calendar_urls(response, municipality=municipality)
        ]
    candidates: list[tuple[str, str]] = []
    if municipality == "Perkáta":
        for element in parsers.HtmlParser("custom-page-description[description]")(
            response
        ):
            fragment: Any = SimpleNamespace(text=element.get("description", ""))
            candidates.extend(
                (str(a["href"]), a.get_text(" ", strip=True))
                for a in parsers.HtmlParser("a[href]")(fragment)
            )
        pattern = r"(?:\d+_)?perkata_hulladeknaptar(20\d{2})(?:[_ -].*)?\.pdf"
    elif municipality == "Nagyvenyim":
        root = parsers.XmlParser()(response)[0]
        candidates = [
            (node.text or "", (node.text or "").rsplit("/", 2)[-2])
            for node in root.findall("{*}url/{*}loc")
        ]
        pattern = r"tajekoztato-a-hulladekszallitas-(20\d{2})-evi-rendjerol"
    else:
        for card in parsers.HtmlParser(".list .item")(response):
            anchor, title = card.select_one("a[href]"), card.select_one(".name")
            if anchor is not None and title is not None:
                response_shape.expect(
                    hu.fold(str(anchor.get("title", "")))
                    == hu.fold(title.get_text(" ", strip=True)),
                    source_name="dunanett_hu",
                    detail="article card title and name disagree",
                    raw=str(card),
                )
                candidates.append(
                    (str(anchor["href"]), title.get_text(" ", strip=True))
                )
        pattern = r"szelektiv es zold hulladekgyujtes (20\d{2})\. evben"
    calendars: dict[int, str] = {}
    for href, label in candidates:
        match = re.fullmatch(pattern, hu.fold(label))
        if not match:
            continue
        year = int(match[1])
        if year < date.today().year:
            continue
        url = urljoin(response.url, href)
        response_shape.expect(
            urlsplit(url).scheme == "https"
            and (
                municipality == "Perkáta"
                or urlsplit(url).netloc == urlsplit(_site(municipality)).netloc
            ),
            source_name="dunanett_hu",
            detail="invalid annual calendar link",
            raw=url,
        )
        response_shape.expect(
            year not in calendars or calendars[year] == url,
            source_name="dunanett_hu",
            detail=f"ambiguous annual calendars for {municipality} ({year})",
            raw=candidates,
        )
        calendars[year] = url
    response_shape.expect(
        date.today().year in calendars,
        source_name="dunanett_hu",
        detail=f"no current annual calendar for {municipality} ({date.today().year})",
        raw=candidates,
    )
    return [(calendars[year], year) for year in sorted(calendars)]


def _document_url(response: Any, target: tuple[str, int], *_: Any, **__: Any) -> str:
    """Resolve the yearless calendar document from its dated municipal article."""
    headings = parsers.HtmlParser("h1")(response)
    response_shape.expect(
        len(headings) == 1
        and hu.fold(headings[0].get_text(" ", strip=True))
        == f"szelektiv es zold hulladekgyujtes {target[1]}. evben",
        source_name="dunanett_hu",
        detail="annual article heading disagrees with its index",
        raw=response.text[:500],
    )
    urls = {
        urljoin(response.url, str(a["href"]))
        for a in parsers.HtmlParser("a[href]")(response)
        if hu.fold(a.get_text(" ", strip=True)) == "naptar"
        and urlsplit(str(a["href"])).path.lower().endswith((".docx", ".pdf"))
    }
    response_shape.expect(
        len(urls) == 1,
        source_name="dunanett_hu",
        detail="expected one annual PDF or DOCX calendar link",
        raw=sorted(urls),
    )
    return next(iter(urls))


_ANNUAL_PDF = hu.CalendarParser(
    types={"szelektív": "szelektív", "zöldhulladék": "zöldhulladék"},
    strict=True,
    expected_municipality=lambda municipality, **_: municipality,
    year_from_url=lambda municipality, **_: municipality in _MEDIA_TOWNS,
    january_trees=True,
    holiday_moves=True,
)
_MONTH_TABLE_PDF = hu.MonthTableCalendarParser(pdf=True)


def _parse_pdf(
    response: Any, source: BaseSource | None = None
) -> list[tuple[date, str]]:
    parser = (
        _MONTH_TABLE_PDF
        if source is not None and source.params["municipality"] == "Dunaföldvár"
        else _ANNUAL_PDF
    )
    return parser(response, source)


@final
class Source(BaseSource):
    TITLE = "Dunanett Nonprofit Kft."
    DESCRIPTION = (
        "Source for Dunanett waste calendars in five Hungarian municipalities."
    )
    URL = "https://www.dunanett.hu"
    COUNTRY = "hu"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@nevembalint"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    TEST_CASES: ClassVar[dict] = {
        "Pusztaszabolcs": {"municipality": "Pusztaszabolcs"},
        "Rácalmás": {"municipality": "Rácalmás"},
        "Perkáta": {"municipality": "Perkáta"},
        "Nagyvenyim": {"municipality": "Nagyvenyim"},
        "Dunaföldvár": {"municipality": "Dunaföldvár"},
    }
    PARAMS = (replace(municipality(), widget="select", options=list(_SITES)),)
    REGIONS: ClassVar[list] = [
        region(town, url=urljoin(site, "/"), municipality=town)
        for town, site in _SITES.items()
    ]
    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Select one municipality: Pusztaszabolcs, Rácalmás, Perkáta, Nagyvenyim "
            "or Dunaföldvár. Official publication indices are "
            "https://pusztaszabolcs.hu/, https://racalmas.hu/category/hirek/, "
            "https://perkata.munipolis.hu/p/hulladekszallitas, "
            "https://nagyvenyim.hu/ and "
            "https://dunafoldvar.hu/hir-kategoria/hulladekokkal-kapcsolatos-informaciok/. "
            "The provider is https://www.dunanett.hu. The source discovers annual "
            "PDF, HTML or DOCX calendars for current/future years automatically, "
            "uses the latest timestamped PDF upload or the uniquely published link, "
            "and fails on ambiguous links or if the current "
            "year is unavailable rather than reusing an expired calendar. "
            "New calendars may only be published in January, so the source can be "
            "unavailable at the start of the year until publication.\n\n"
            "General waste, recycling and garden waste are included, except in "
            "Dunaföldvár: its document publishes only recycling and garden dates, "
            "so no general-waste schedule is returned there. Where the calendar "
            "restricts January collections to Christmas trees, those events use the "
            "Garden Waste category with a tree-only description: remove decorations "
            "and other waste; ordinary garden waste is not accepted. Bulky waste is "
            "by appointment and has no calendar dates. Permanent glass drop-off "
            "points are not dated collections.\n\n"
            "These are the annual planned dates. Ad-hoc weather cancellations or "
            "street-specific replacement notices are not included; check municipal "
            "news and https://www.dunanett.hu/nonprofit/hireink/. Other Dunanett "
            "municipalities are not supported: current machine-readable annual "
            "calendars could not be verified, or the available calendars are image-only."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Request(
            lambda municipality, **_: (
                f"{_site(municipality)}/wp-json/wp/v2/media"
                if municipality in _MEDIA_TOWNS
                else _site(municipality)
            ),
            params=lambda municipality, **_: (
                {
                    "search": "hulladeknaptar",
                    "per_page": 100,
                    "_fields": "date,source_url,title",
                }
                if municipality in _MEDIA_TOWNS
                else None
            ),
            headers=lambda municipality, **_: {
                "Referer": urljoin(_site(municipality), "/")
            },
            timeout=60,
        ),
        targets=lambda source, response: _annual_targets(response, **source.params),
        fetch=retrievers.Request(
            lambda target, response, document, **_: document or target[0],
            before=(
                retrievers.Lookup(
                    lambda target, response, **_: target[0],
                    when=lambda *_, municipality, **__: municipality == "Dunaföldvár",
                    pick=_document_url,
                    timeout=60,
                ),
            ),
            headers=lambda *_, municipality, **__: {
                "Referer": urljoin(_site(municipality), "/")
            },
            timeout=60,
        ),
        include_prepared=True,
    )
    parse = hu.PublishedCalendarsParser(
        discover=_annual_targets,
        parser=parsers.ByBodyPrefix(
            {
                "%PDF-": _parse_pdf,
                "PK": hu.MonthTableCalendarParser(docx=True),
            },
            default=hu.MonthTableCalendarParser(),
        ),
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
