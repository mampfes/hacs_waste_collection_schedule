"""PGK Koszalin, Poland (single-family housing in the city of Koszalin).

PGK publishes one page per housing estate (osiedle), linked from a stable index
page. Each estate page lists its collection sectors as boxes: a title linking to
the sector's PDF ("2026r. Osiedle Raduszka środa") over the streets it covers.
The source resolves the estate on the index, then the street on the estate page,
and reads that sector's PDF: one table, a row per month, a column per fraction,
the days listed in each cell ("1,8,15,22,29"). The first two fractions
(mixed waste, metals and plastics) share one merged cell, so a cell counts for
every column heading it spans. The PDF prints the table twice; the copies are
de-duplicated.

Multi-family housing (zabudowa wielorodzinna) is published as one PDF per
fraction for the whole city, a different layout this source does not read.
"""

import re
from typing import Any, ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import (
    lookups,
    parsers,
    preprocessors,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX_URL = (
    "https://www.pgkkoszalin.pl/harmonogramy-wywozu-odpadow/"
    "harmonogram-miasto-koszalin/"
)

# The column headings, as printed (one word of each suffices).
_TYPES = {
    "zmieszane": wt.GENERAL_WASTE,
    "metale": wt.RECYCLABLES,
    "papier": wt.PAPER,
    "szkło": wt.GLASS,
    "bio": wt.ORGANIC,
    "gabaryty": wt.BULKY_WASTE,
}


def _estate_page(response: Any, *_keys: Any, district: str, **_: Any) -> str:
    """The estate page for ``district``, from the index's links."""
    pages: dict[str, str] = {}
    for link in BeautifulSoup(response.text, "html.parser").find_all("a", href=True):
        href = str(link["href"])
        if "/harmonogram-osiedle-" not in href:
            continue
        name = re.sub(r"(?i)^osiedle\s+", "", link.get_text(" ", strip=True))
        if name and not any(
            lookups.normalize_loose(name) == lookups.normalize_loose(known)
            for known in pages
        ):
            pages[name] = href
    response_shape.expect(
        bool(pages),
        source_name="pgkkoszalin_pl",
        detail="no estate (osiedle) page linked from the index",
        raw=response.text[:500],
    )
    return lookups.resolve(
        pages, district, argument="district", normalize=lookups.normalize_loose
    )


def _sector_pdf(response: Any, *_keys: Any, street: str | None = None, **_: Any) -> str:
    """The sector PDF whose box lists ``street`` (or the estate's only one)."""
    boxes: dict[int, dict[str, list[str]]] = {}
    for box in BeautifulSoup(response.text, "html.parser").select(
        ".elementor-icon-box-content"
    ):
        link = box.select_one(".elementor-icon-box-title a[href]")
        if link is None or ".pdf" not in str(link["href"]):
            continue
        year = re.search(r"\b(20\d\d)", link.get_text(" ", strip=True))
        description = box.select_one(".elementor-icon-box-description")
        streets = [
            line.strip()
            for line in (description.get_text("\n") if description else "").split("\n")
            if line.strip() and not re.fullmatch(r"(?i)ulice\s*:?", line.strip())
        ]
        sector = boxes.setdefault(int(year.group(1)) if year else 0, {})
        sector.setdefault(str(link["href"]), []).extend(streets)
    response_shape.expect(
        bool(boxes),
        source_name="pgkkoszalin_pl",
        detail="no sector PDF linked from the estate page",
        raw=response.text[:500],
    )
    # The newest calendar the page links.
    sectors = boxes[max(boxes)]
    if len(sectors) == 1 and not street:
        return next(iter(sectors))
    by_street = {name: url for url, names in sectors.items() for name in names}
    if not street:
        raise SourceArgumentRequiredWithSuggestions(
            "street", "this estate has several collection sectors", sorted(by_street)
        )
    wanted = lookups.normalize_loose(street)
    exact = {
        url
        for name, url in by_street.items()
        if lookups.normalize_loose(name) == wanted
    }
    if len(exact) == 1:
        return exact.pop()
    # "Gnieźnieńska" for "Gnieźnieńska 52-110 (parzyste)": fine while only one
    # sector of the estate lists the street.
    partial = {
        name: url
        for name, url in by_street.items()
        if lookups.normalize_loose(name).startswith(wanted + " ")
    }
    if len(set(partial.values())) == 1:
        return next(iter(partial.values()))
    if partial:
        raise SourceArgAmbiguousWithSuggestions("street", street, sorted(partial))
    raise SourceArgumentNotFoundWithSuggestions("street", street, sorted(by_street))


@final
class Source(BaseSource):
    TITLE = "PGK Koszalin"
    DESCRIPTION = "Source for PGK Koszalin (single-family housing), Poland."
    URL = "https://www.pgkkoszalin.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.ORGANIC,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Raduszka, Polczynska": {"district": "Raduszka", "street": "Połczyńska"},
        "Srodmiescie, Harcerska": {"district": "Śródmieście", "street": "Harcerska"},
        "Wankowicza": {"district": "Wańkowicza"},
    }

    PARAMS = (district("district"), street("street", optional=True))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your estate (osiedle) as listed on "
            "https://www.pgkkoszalin.pl/harmonogramy-wywozu-odpadow/"
            "harmonogram-miasto-koszalin/ (e.g. 'Raduszka'), and your street as "
            "printed on the estate's page (e.g. 'Gnieźnieńska 52-110 (parzyste)'). "
            "The street can be left out for an estate with a single calendar. "
            "Multi-family housing (zabudowa wielorodzinna) is not supported."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_INDEX_URL, pick=_estate_page),
            retrievers.Lookup(lambda page, **_: page, pick=_sector_pdf),
        ),
        url=lambda page, pdf, **_: pdf,
    )
    parse = parsers.PdfTableParser(min_words=30)
    preprocess = preprocessors.Compose(
        preprocessors.PdfMonthRows(labels=_TYPES, year_pattern=r"w roku\s+(20\d\d)"),
        preprocessors.Deduplicate(),
    )
    transform = ICSTransformer(type_value_map=_TYPES)
