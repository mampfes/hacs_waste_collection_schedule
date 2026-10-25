"""Econet, Italy (Acqui Terme, Ovada and surroundings, Alessandria province).

Econet publishes one yearly "Ecocalendario" PDF per comune on the comune's page
of its door-to-door service (https://www.econetsrl.eu/testi.php?id_testi=25),
linked as ``data/download/PaP/Calendari <year>/<NAME>_<year>.pdf``. Acqui Terme
and Ovada link a "Calendari" subpage instead, with one calendar per collection
zone (Centro Storico, Città, Standard) and the streets of each zone; the
Ecobus timetables listed there are mobile drop-off points, not collections.

Each PDF is a fold-out sheet printing every month as a block of
"day weekday rounds" lines (October to December first, then January to
September), so ``preprocessors.PdfMonthBlocks`` dates each block by its printed
weekdays and reads the months in any order. VERDE (garden waste) is printed on
the days it runs, though in most comuni it is collected on booking only.
"""

import re
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import (
    config_params,
    lookups,
    parsers,
    preprocessors,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.econetsrl.eu"
_COMUNI_URL = f"{_URL}/testi.php?id_testi=25"

_CALENDAR = re.compile(r"/Calendari(?:\s|%20)+(20\d\d)/[^/]+\.pdf$", re.IGNORECASE)

_TYPES = {
    "secco": wt.GENERAL_WASTE,
    "organico": wt.ORGANIC,
    "plastica": wt.RECYCLABLES,
    "carta": wt.PAPER,
    "verde": wt.GARDEN_WASTE,
}

# Comuni with a calendar, as named on the comuni page; Acqui Terme and Ovada
# by zone.
_COMUNI = (
    "Alice bel Colle",
    "Belforte Monferrato",
    "Bistagno",
    "Bosio",
    "Carpeneto",
    "Casaleggio Boiro",
    "Cassine",
    "Cassinelle",
    "Castelletto d'Orba",
    "Cremolino",
    "Lerma",
    "Molare",
    "Montaldeo",
    "Montaldo Bormida",
    "Mornese",
    "Morsasco",
    "Orsara",
    "Prasco",
    "Ricaldone",
    "Rivalta Bormida",
    "Rocca Grimalda",
    "San Cristoforo",
    "Silvano d'Orba",
    "Strevi",
    "Tagliolo Monferrato",
    "Terzo",
    "Trisobbio",
    "Visone",
)
_ZONED = ("Acqui Terme", "Ovada")
_ZONES = ("Centro Storico", "Città", "Standard")


def _calendar_link(
    response: Any, comune: str, zona: "str | None", *, follow: bool
) -> str:
    """The comune's newest calendar PDF, or (``follow``) its calendars subpage."""
    soup = BeautifulSoup(response.text, "html.parser")
    by_year: dict[int, dict[str, str]] = {}
    subpage = None
    for link in soup.select("#contenuto a[href]"):
        href = str(link["href"]).strip()
        text = link.get_text(" ", strip=True)
        url = urljoin(str(response.url), href).replace(" ", "%20")
        match = _CALENDAR.search(url)
        if match is None:
            if follow and "id_testi=" in href and text.lower().startswith("calendari"):
                subpage = url
            continue
        if "ecobus" in href.lower():
            continue
        names = by_year.setdefault(int(match.group(1)), {})
        names[text or url] = url
    if not by_year:
        if subpage:
            return subpage
        raise SourceArgumentNotFound(
            "comune",
            comune,
            "Econet publishes no collection calendar for this comune.",
        )
    calendars = by_year[max(by_year)]
    urls = set(calendars.values())
    if len(urls) == 1:
        return urls.pop()
    zones = {
        name: url for name, url in calendars.items() if not name.startswith("http")
    }
    if not zona:
        raise SourceArgumentRequiredWithSuggestions(
            "zona", "the comune has one calendar per zone", sorted(zones)
        )
    return lookups.resolve(
        zones, zona, argument="zona", normalize=lookups.normalize_loose
    )


def _calendar_or_subpage(
    response: Any, _page: str, comune: str, zona: "str | None" = None, **_: Any
) -> str:
    return _calendar_link(response, comune, zona, follow=True)


def _calendar_on_subpage(
    response: Any,
    _page: str,
    _found: str,
    comune: str,
    zona: "str | None" = None,
    **_: Any,
) -> str:
    return _calendar_link(response, comune, zona, follow=False)


def _is_subpage(_page: str, found: str, **_: Any) -> bool:
    return not found.endswith(".pdf")


@final
class Source(BaseSource):
    TITLE = "Econet"
    DESCRIPTION = (
        "Source for Econet (Acqui Terme, Ovada and surroundings, Alessandria) "
        "door-to-door collection calendars."
    )
    URL = _URL
    COUNTRY = "it"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Strevi": {"comune": "Strevi"},
        "Cassine": {"comune": "Cassine"},
        "Acqui Terme Centro Storico": {
            "comune": "Acqui Terme",
            "zona": "Centro Storico",
        },
        "Ovada Citta": {"comune": "ovada", "zona": "Citta"},
    }

    REGIONS = (
        *(region(name, comune=name) for name in _COMUNI),
        *(
            region(f"{comune} ({zona})", comune=comune, zona=zona)
            for comune in _ZONED
            for zona in _ZONES
        ),
    )

    PARAMS = (
        config_params.municipality("comune"),
        config_params.district("zona", optional=True),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your comune as listed on "
            "https://www.econetsrl.eu/testi.php?id_testi=25, e.g. `Strevi`. "
            "Acqui Terme and Ovada have one calendar per zone: also enter the "
            "zone (`Centro Storico`, `Città` or `Standard`); the streets of "
            "each zone are listed on the comune's 'Calendari' page."
        ),
        "it": (
            "Inserisci il comune come indicato su "
            "https://www.econetsrl.eu/testi.php?id_testi=25, ad esempio "
            "`Strevi`. Acqui Terme e Ovada hanno un calendario per zona: "
            "indica anche la zona (`Centro Storico`, `Città` o `Standard`); "
            "le vie di ogni zona sono elencate nella pagina 'Calendari' del "
            "comune."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _COMUNI_URL,
                pick=lookups.link_pick(
                    "comune",
                    href=r"testi\.php\?id_testi=\d+$",
                    selector="#contenuto table a[href]",
                ),
            ),
            retrievers.Lookup(lambda page, **_: page, pick=_calendar_or_subpage),
            retrievers.Lookup(
                lambda page, found, **_: found,
                when=_is_subpage,
                pick=_calendar_on_subpage,
            ),
        ),
        url=lambda page, found, pdf, **_: pdf or found,
    )
    parse = parsers.PdfTableParser(min_words=100)
    preprocess = preprocessors.PdfMonthBlocks(labels=_TYPES, any_order=True)
    transform = ICSTransformer(type_value_map=_TYPES)
