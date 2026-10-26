"""Lozzolo and Roasio (Vercelli), Italy: COVEVAR collection calendar.

COVEVAR (the waste consortium of the Vercelli province, collection by Iren /
San Germano) prints one "Eco Calendario" for Lozzolo and Roasio together. The
comune of Roasio posts it every year as a news item ("Calendario Raccolta
Rifiuti <year>") on its Siscom portal; the PDF is attached to that item under
a file name without the year, so the source finds the newest such item on the
portal's news list rather than a fixed address.

The PDF prints six month columns per page, one row per day ("1 GI"), each
collection a coloured hexagon to the right of the day. Plain and non-domestic
residual waste share the grey hexagon, told apart by the white glyph inside
it (an "I", or a factory), so those two markers match the glyph. The month
headings sit too unevenly over their columns for ``MarkerCalendarParser`` to
bind them, so the columns are numbered in reading order instead, and the
year, printed as "20" over "26", is read in two pieces.
"""

import re
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import (
    config_params,
    preprocessors,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.comune.roasio.vc.it"
_NEWS_URL = f"{_URL}/Notizie"

_NEWS_TITLE = re.compile(r"calendario.*rifiuti.*?(20\d{2})", re.IGNORECASE)
_CALENDAR_PDF = re.compile(r"SiscomArchivio/.*calendario.*\.pdf$", re.IGNORECASE)

# Hexagon symbols (CMYK fill), and the white glyphs inside the grey one.
_HEX = {"width": (18.8, 19.8), "height": (21.2, 22.3)}
_WHITE = (0.0, 0.0, 0.0, 0.0)
_MARKERS = (
    Marker("Organico", (0.25, 0.44, 0.78, 0.23), **_HEX),
    Marker("Indifferenziato", _WHITE, width=(1.4, 2.3), height=(9.25, 9.8)),
    Marker(
        "Indifferenziato non domestico",
        _WHITE,
        width=(9.3, 9.9),
        height=(9.3, 9.9),
    ),
    Marker("Tessili sanitari", (0.87, 1.0, 0.27, 0.18), **_HEX),
    Marker("Vetro", (0.74, 0.46, 0.0, 0.0), **_HEX),
    Marker("Metalli", (0.73, 0.13, 0.0, 0.0), **_HEX),
    Marker("Metalli commerciali", (0.73, 0.13, 0.0, 0.3), **_HEX),
    Marker("Plastica", (0.26, 0.0, 0.01, 0.0), **_HEX),
    Marker("Carta", (0.0, 0.33, 0.95, 0.0), **_HEX),
    Marker("Cartone commerciale", (0.0, 0.1, 0.4, 0.0), **_HEX),
    Marker("Sfalci verdi", (0.5, 0.0, 0.99, 0.0), **_HEX),
)

_TYPES = {
    "Organico": wt.ORGANIC,
    "Indifferenziato": wt.GENERAL_WASTE,
    "Indifferenziato non domestico": wt.GENERAL_WASTE,
    "Tessili sanitari": wt.GENERAL_WASTE,
    "Vetro": wt.GLASS,
    "Metalli": wt.METAL,
    "Metalli commerciali": wt.METAL,
    "Plastica": wt.PLASTIC,
    "Carta": wt.PAPER,
    "Cartone commerciale": wt.PAPER,
    "Sfalci verdi": wt.GARDEN_WASTE,
}

# Rounds for businesses only ("utenze non domestiche").
_NON_DOMESTIC = frozenset(
    {"Indifferenziato non domestico", "Metalli commerciali", "Cartone commerciale"}
)
_DOMESTIC = "domestica"
_UTENZE = (_DOMESTIC, "non domestica")


def _calendar_news(response: Any, **_: Any) -> str:
    """The newest "Calendario Raccolta Rifiuti <year>" item on the news list."""
    soup = BeautifulSoup(response.text, "html.parser")
    found = [
        (int(match.group(1)), urljoin(str(response.url), str(link["href"])))
        for link in soup.select("a[href*='Dettaglionews']")
        if (match := _NEWS_TITLE.search(link.get_text(" ", strip=True)))
    ]
    response_shape.expect(
        bool(found),
        source_name="lozzolo_roasio_it",
        detail="no 'Calendario Raccolta Rifiuti' item on Roasio's news list",
        raw=str(response.url),
    )
    return max(found)[1] if found else ""


def _calendar_pdf(response: Any, _news: str, **_: Any) -> str:
    """The calendar PDF attached to the news item."""
    soup = BeautifulSoup(response.text, "html.parser")
    links = [
        urljoin(str(response.url), str(link["href"]))
        for link in soup.select("a[href]")
        if _CALENDAR_PDF.search(str(link["href"]))
    ]
    response_shape.expect(
        bool(links),
        source_name="lozzolo_roasio_it",
        detail="the calendar news item has no calendar PDF attached",
        raw=str(response.url),
    )
    return links[0] if links else ""


def _for_utenza(row: Any, source: Any) -> bool:
    utenza = (source.params.get("utenza") if source else None) or _DOMESTIC
    return utenza != _DOMESTIC or row[1] not in _NON_DOMESTIC


@final
class Source(BaseSource):
    TITLE = "Lozzolo, Roasio (COVEVAR)"
    DESCRIPTION = (
        "Source for the COVEVAR door-to-door collection calendar of Lozzolo "
        "and Roasio (Vercelli)."
    )
    URL = _URL
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.METAL,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Lozzolo": {},
        "Roasio non domestica": {"utenza": "non domestica"},
    }

    REGIONS = (region("Lozzolo"), region("Roasio"))

    PARAMS = (
        config_params.dropdown(
            "utenza", list(_UTENZE), label="User type", default=_DOMESTIC
        ),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Lozzolo and Roasio share one calendar, read from the yearly "
            "'Calendario Raccolta Rifiuti' notice on Roasio's website; no "
            "address is needed. Households keep `utenza` at `domestica`; "
            "businesses choose `non domestica` to add the non-domestic residual "
            "waste, commercial metals and commercial cardboard rounds. Sanitary "
            "textiles (tessili sanitari) and garden waste (sfalci verdi) are "
            "only collected for users who have signed up with COVEVAR."
        ),
        "it": (
            "Lozzolo e Roasio hanno lo stesso calendario, letto dall'avviso "
            "annuale 'Calendario Raccolta Rifiuti' sul sito del Comune di "
            "Roasio; non serve l'indirizzo. Le famiglie lasciano `utenza` su "
            "`domestica`; le attività scelgono `non domestica` per aggiungere "
            "indifferenziato non domestico, metalli commerciali e cartone "
            "commerciale. Tessili sanitari e sfalci verdi vengono ritirati solo "
            "per chi ha attivato il servizio presso COVEVAR."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_NEWS_URL, pick=_calendar_news),
            retrievers.Lookup(lambda news, **_: news, pick=_calendar_pdf),
        ),
        url=lambda _news, pdf, **_: pdf,
    )
    parse = MarkerCalendarParser(
        _MARKERS,
        placement="row",
        row_reach=120.0,
        read_headings=False,
        weekdays=("LU", "MA", "ME", "GI", "VE", "SA", "DO"),
        year_pattern=r"(?:Giugno|Dicembre)\s+(20)\s+(\d\d)\b",
        min_markers=100,
    )
    preprocess = preprocessors.RowFilter(_for_utenza)
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
