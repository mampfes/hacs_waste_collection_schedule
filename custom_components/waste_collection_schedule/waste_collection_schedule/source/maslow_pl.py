"""Gmina Masłów, Poland.

The municipality's waste page links one article per year ("Harmonogramy odbioru
odpadów na 2026 rok"), which links one PDF per group of villages
("Dąbrowa, Wiśniówka (PDF)"). The source follows the articles from this year
on, and in each the link for the configured area.

Each PDF is a fold-out leaflet printing the same schedule twice, side by side:
a heading per waste round, the dates below it ("13.04 ; 27.04"), the year in the
title. Only the first copy is read (up to the contact note under it): the
second is extracted in a different order, and in 2026 one leaflet's two copies
even disagree on a date.
"""

import re
from typing import Any, ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import lookups, parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_MENU_URL = "https://www.maslow.pl/asp/gospodarka-odpadami,66"
_ARTICLE_PATTERN = r"harmonogram\w*-odbioru-odpadow-na-(20\d\d)-rok"

# The round headings, as printed.
_TYPES = {
    "Odpady segregowane": wt.RECYCLABLES,
    "Zmieszane odpady komunalne": wt.GENERAL_WASTE,
    "Odpady biodegradowalne": wt.ORGANIC,
    "Popiół": wt.OTHER,
    # "..., sprzęt elektryczny i elektroniczny, odzież i tekstylia"
    "Meble i inne odpady wielkogabarytowe": wt.BULKY_WASTE,
}


def _area_pdf(response: Any, *_keys: Any, district: str, **_: Any) -> str:
    """The article's PDF for ``district``: its link text ("Dąbrowa, Wiśniówka"),
    or one village of it ("Wiśniówka") that only one link names."""
    links: dict[str, str] = {}
    for link in BeautifulSoup(response.text, "html.parser").find_all("a", href=True):
        href = str(link["href"])
        if href.lower().endswith(".pdf"):
            name = re.sub(r"\s*\(PDF\)?\s*$", "", link.get_text(" ", strip=True))
            links.setdefault(name, retrievers.urljoin(response.url, href))
    wanted = lookups.normalize_loose(district)
    for name, url in links.items():
        if lookups.normalize_loose(name) == wanted:
            return url
    villages = {
        name: url
        for name, url in links.items()
        if wanted
        in {lookups.normalize_loose(village) for village in re.split(r"[,(]", name)}
    }
    if len(villages) == 1:
        return next(iter(villages.values()))
    if villages:
        raise SourceArgAmbiguousWithSuggestions("district", district, sorted(villages))
    raise SourceArgumentNotFoundWithSuggestions("district", district, sorted(links))


@final
class Source(BaseSource):
    TITLE = "Gmina Masłów"
    DESCRIPTION = "Source for Gmina Masłów, Poland."
    URL = "https://www.maslow.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.OTHER,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Dabrowa, Wisniowka": {"district": "Dąbrowa, Wiśniówka"},
        "Maslow Pierwszy": {"district": "Masłów Pierwszy"},
        "Brzezinki": {"district": "Brzezinki"},
    }

    PARAMS = (district("district"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your area as named by its schedule link on "
            "https://www.maslow.pl/asp/gospodarka-odpadami,66 (in the article "
            "'Harmonogramy odbioru odpadów na <year> rok'), e.g. "
            "'Dąbrowa, Wiśniówka' or 'Zabudowa wielorodzinna'. A single village "
            "named in only one link (e.g. 'Wiśniówka') works too."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _MENU_URL, pick=retrievers.yearly_links(_ARTICLE_PATTERN)
        ),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(
            lambda article, urls, pdf, **_: pdf,
            before=(
                retrievers.Lookup(lambda article, urls, **_: article, pick=_area_pdf),
            ),
        ),
    )
    # Each year's PDF on its own: the year is printed once, in its title.
    parse = parsers.EachResponse(
        parsers.PdfTextParser(min_chars=200),
        then=preprocessors.TextGroupedDates(
            keys=_TYPES,
            date_pattern=r"\b(?P<day>\d{1,2})\.(?P<month>\d{2})\b",
            year_pattern=r"\b(20\d\d)\s+Odpady segregowane",
            end_pattern=r"Kontakt z biurem",
        ),
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
