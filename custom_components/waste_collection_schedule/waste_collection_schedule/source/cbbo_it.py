"""C.B.B.O. (Brescia province, Italy): yearly "Ecocalendario" PDFs per comune.

C.B.B.O. lists its comuni on https://www.cbbo.it/ and links each comune's
calendar from the comune's page (the "eco calendario" button). Most comuni get
a booklet of one month grid per page ("FEBBRAIO 26" over Lun ... Dom), the
collections printed as coloured pictograms in a row under the day number:
``service.PdfMarkerCalendar.MarkerCalendarParser`` with ``placement="below"``
and ``page_headings`` reads it. The legend is the same across comuni, though
some calendars state their colours in CMYK rather than RGB, so a pictogram is
listed once per colour space.

Barbariga's calendar is a single sheet of day rows instead, and San Zeno
Naviglio's runs October to September with its month names set vertically;
neither is read yet.
"""

import re
from typing import Any, ClassVar, final
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.cbbo.it"

_ORGANIC = "Frazione organica"
_RESIDUAL = "Rifiuto non riciclabile"
_PLASTIC = "Imballaggi in plastica"
_PAPER = "Carta e cartone"
_GLASS = "Vetro e lattine"
_SANITARY = "Tessili sanitari"
_GARDEN = "Verde"

_TYPES = {
    _ORGANIC: wt.ORGANIC,
    _RESIDUAL: wt.GENERAL_WASTE,
    _PLASTIC: wt.PLASTIC,
    _PAPER: wt.PAPER,
    _GLASS: wt.GLASS,
    _SANITARY: wt.GENERAL_WASTE,
    _GARDEN: wt.GARDEN_WASTE,
}

# The body of each pictogram (the apple, the bin, the bottle, ...), which its
# other parts and the spazzamento (street sweeping) discs do not match.
_MARKERS = (
    Marker(_ORGANIC, (0.897, 0.231, 0.147), width=(8, 13), height=(8, 13)),
    Marker(_ORGANIC, (0.04, 0.92, 1.0, 0.0), width=(8, 13), height=(8, 13)),
    Marker(_RESIDUAL, (0.428, 0.433, 0.443), width=(9, 14), height=(9, 14)),
    Marker(_RESIDUAL, (0.0, 0.0, 0.0, 0.7), width=(9, 14), height=(9, 14)),
    Marker(_PLASTIC, (1.0, 0.803, 0.02), width=(5, 9), height=(11, 17)),
    Marker(_PAPER, (0.668, 0.598, 0.418), width=(7.5, 11.5), height=(6, 9.5)),
    Marker(_PAPER, (0.34, 0.34, 0.66, 0.03), width=(7.5, 11.5), height=(6, 9.5)),
    Marker(_GLASS, (0.399, 0.732, 0.502), width=(3, 5.5), height=(12, 17)),
    Marker(_SANITARY, (0.44, 0.741, 0.88), width=(12, 18), height=(8, 13)),
    Marker(_GARDEN, (0.25, 0.16, 0.06), width=(13, 15), height=(13, 15)),
)

_COMUNI = (
    "Acquafredda",
    "Calvisano",
    "Capriano del Colle",
    "Carpenedolo",
    "Castenedolo",
    "Flero",
    "Ghedi",
    "Isorella",
    "Mazzano",
    "Montichiari",
    "Montirone",
    "Nuvolento",
    "Nuvolera",
    "Poncarale",
    "Remedello",
    "Visano",
)

# Comuni whose calendar has another layout (see the module docstring).
_UNSUPPORTED = ("Barbariga", "San Zeno Naviglio")

_comune_page = lookups.link_pick(
    "comune",
    href=r"^/(?:index\.php/)?[\w-]+/?$",
    selector="#block-views-block-comuni-block-1 a[href]",
)


def _comune(response: Any, *keys: Any, comune: str, **params: Any) -> str:
    """The comune's page on cbbo.it."""
    wanted = lookups.normalize_loose(comune)
    if wanted in {lookups.normalize_loose(name) for name in _UNSUPPORTED}:
        raise SourceArgumentNotFound(
            "comune",
            comune,
            "C.B.B.O. publishes this comune's calendar in a layout this source "
            "cannot read yet.",
        )
    return _comune_page(response, *keys, comune=comune, **params)


def _calendar(response: Any, _page: str, comune: str, **_: Any) -> str:
    """The "eco calendario" PDF linked from the comune's page."""
    soup = BeautifulSoup(response.text, "html.parser")
    for link in soup.select("a.bottone_cbbo[href]"):
        href = str(link["href"]).strip()
        if re.search(r"/Ecocalendario[^/]*\.pdf$", href, re.IGNORECASE):
            return quote(urljoin(str(response.url), href), safe=":/%")
    raise SourceArgumentNotFound(
        "comune", comune, "No Ecocalendario is linked from the comune's page."
    )


@final
class Source(BaseSource):
    TITLE = "C.B.B.O."
    DESCRIPTION = (
        "Source for C.B.B.O. (Brescia province) door-to-door collection "
        "calendars: Capriano del Colle, Ghedi, Montichiari and more."
    )
    URL = _URL
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Capriano del Colle": {"comune": "Capriano del Colle"},
        "Flero": {"comune": "Flero"},
        "Acquafredda": {"comune": "acquafredda"},
        "Remedello": {"comune": "Remedello"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown comune": {"comune": "Brescia"},
        "Barbariga": {"comune": "Barbariga"},
    }

    REGIONS = tuple(region(name, comune=name) for name in _COMUNI)

    PARAMS = (config_params.municipality("comune"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your comune as listed on https://www.cbbo.it/ (menu "
            "'Comuni'), e.g. `Capriano del Colle`. The dates are read from the "
            "comune's yearly Ecocalendario PDF. Barbariga and San Zeno Naviglio "
            "publish a calendar in another layout and are not supported yet."
        ),
        "it": (
            "Inserisci il tuo comune come indicato su https://www.cbbo.it/ "
            "(menu 'Comuni'), ad esempio `Capriano del Colle`. Le date vengono "
            "lette dall'Ecocalendario annuale in PDF del comune. Barbariga e "
            "San Zeno Naviglio pubblicano un calendario con un'impaginazione "
            "diversa e non sono ancora supportati."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_URL + "/", pick=_comune),
            retrievers.Lookup(lambda page, **_: page, pick=_calendar),
        ),
        url=lambda _page, pdf, **_: pdf,
    )
    parse = MarkerCalendarParser(
        _MARKERS,
        placement="below",
        page_headings=True,
        row_reach=40,
        year_pattern=r"Ecocalendario_(20\d\d)",
    )
    transform = ICSTransformer(type_value_map=_TYPES, carry_raw_label=True)
