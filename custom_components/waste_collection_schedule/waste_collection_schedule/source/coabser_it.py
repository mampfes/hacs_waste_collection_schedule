"""CoABSeR (Consorzio Albese Braidese Servizi Rifiuti), Italy.

CoABSeR publishes one yearly PDF calendar per comune for households on
https://coabser.it/servizi/calendari-utenze-domestiche/, linked directly or from
the comune's own page. The calendar is a text PDF of month columns (January to
June on the first page, July to December on the second) whose day rows ("4 Mer")
carry the codes of the rounds collected that day (RSU, CAR, PLA, ORG, ...); the
text layer runs each day number across the six months of a page.
"""

import re
from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import config_params, lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.preprocessors import TextMonthColumns
from waste_collection_schedule.response_shape import expect
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://coabser.it"
_INDEX_URL = f"{_URL}/servizi/calendari-utenze-domestiche/"

_CALENDAR = re.compile(r"/pdf/calendari_raccolte/[^/]+\.pdf$", re.IGNORECASE)

_TYPE_MAP = {
    "RSU": wt.GENERAL_WASTE,
    "CAR": wt.PAPER,
    "PLA": wt.PLASTIC,
    "ORG": wt.ORGANIC,
    "VET": wt.GLASS,
    "PILE": wt.HAZARDOUS,
}


def _direct_pdf(link: str, *_, **__) -> str | None:
    """Lookup ``given``: a calendar PDF needs no further page."""
    return link if _CALENDAR.search(link) else None


def _calendar_pdf(response, *_, **__) -> str:
    """Lookup pick: the household calendar PDF on the comune's page."""
    soup = BeautifulSoup(response.text, "html.parser")
    links = [
        urljoin(str(response.url), str(a["href"]))
        for a in soup.select("a[href]")
        if _CALENDAR.search(str(a["href"]))
    ]
    expect(
        bool(links),
        source_name="coabser_it",
        detail="no calendar PDF on the comune's page",
        raw=response.text[:500],
    )
    return links[0]


@final
class Source(BaseSource):
    TITLE = "CoABSeR"
    DESCRIPTION = "Source for CoABSeR (Alba, Bra and Roero, Piedmont) household collection calendars."
    URL = _URL
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Sommariva Perno": {"comune": "Sommariva Perno"},
        "Barolo": {"comune": "Barolo"},
        "Cherasco": {"comune": "Cherasco"},
    }

    PARAMS = (config_params.municipality("comune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your comune as listed on "
            "https://coabser.it/servizi/calendari-utenze-domestiche/, for "
            "example `Sommariva Perno`. Alba (no text layer) and Bra (one "
            "calendar per zone in a single PDF) are not supported."
        ),
        "it": (
            "Inserisci il tuo comune come indicato su "
            "https://coabser.it/servizi/calendari-utenze-domestiche/, ad "
            "esempio `Sommariva Perno`. Alba e Bra non sono supportati."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick(
                    "comune",
                    href=r"calendari_raccolte/[^/]+\.pdf$|calendari-utenze-domestiche/[^/]+/?$",
                ),
            ),
            retrievers.Lookup(
                lambda link, **_: link, given=_direct_pdf, pick=_calendar_pdf
            ),
        ),
        url=lambda link, pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = parsers.PdfTextParser(min_chars=500)
    preprocess = TextMonthColumns(
        keys=_TYPE_MAP,
        weekdays=("Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"),
        year_pattern=r"raccolta rifiuti (\d{4})",
    )
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
