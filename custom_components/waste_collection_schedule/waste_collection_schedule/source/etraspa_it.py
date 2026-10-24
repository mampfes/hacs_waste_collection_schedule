"""ETRA S.p.A., Veneto, Italy.

ETRA publishes its municipal collection calendars as PDFs whose
collection-day markers are vector-drawn icons with no extractable text layer;
the icon positions and fill colours are read by the shared
``service.EtraSpa.EtraCalendarParser``, which every ETRA municipality using
the same InDesign template can reuse.

Where the PDF is published differs per municipality, so each one is a row in
``_MUNICIPALITIES``:

- San Martino di Lupari links one PDF (zones A and B as sub-columns) from a
  per-year page on the municipality's own website (``PdfLinkRetriever``).
- Bassano del Grappa gets one PDF per zone on ETRA's own website, under a file
  name carrying the year and the zone letter. In early January the new year's
  file may not be up yet, so the previous year's is tried next
  (``FirstMatchRetriever``) rather than failing with a 404.

``FallbackRetriever`` runs only the configured municipality's branch (its
``when`` also validates the municipality and zone before any request), and
``FirstNonEmptyBranch`` hands the PDF to that municipality's zone layout.
"""

from datetime import date
from typing import Any, ClassVar, NamedTuple, final

from waste_collection_schedule import lookups
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.parsers import FirstNonEmptyBranch
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import (
    Branch,
    FallbackRetriever,
    FirstMatchRetriever,
    PdfLinkRetriever,
    Response,
)
from waste_collection_schedule.service.EtraSpa import EtraCalendarParser
from waste_collection_schedule.transformers import ICSTransformer

_SAN_MARTINO_PAGE = (
    "https://www.comune.sanmartinodilupari.pd.it/"
    "documento_pubblico/calendario-etra-{year}/"
)
_BASSANO_PDF = (
    "https://www.etraspa.it/sites/etraspa.it/files/"
    "Bassano_CalendA4_2Z_{year}_{zone}.pdf"
)


def _recent_years(**_: Any) -> tuple[int, int]:
    """This year's calendar first, then last year's while the new one is not up."""
    year = date.today().year
    return (year, year - 1)


def _is_pdf(response: Response) -> bool:
    return response.status_code == 200 and response.content.startswith(b"%PDF")


class _Municipality(NamedTuple):
    url: str
    zones: tuple[str, ...]
    fetch: Any
    parse: EtraCalendarParser


_MUNICIPALITIES: dict[str, _Municipality] = {
    "San Martino di Lupari": _Municipality(
        url="https://www.comune.sanmartinodilupari.pd.it",
        zones=("A", "B"),
        fetch=PdfLinkRetriever(
            index_url=lambda **_: _SAN_MARTINO_PAGE.format(year=date.today().year),
            pattern=r"\.pdf$",
            select="first",
        ),
        # One PDF with "ZONA A" / "ZONA B" sub-columns.
        parse=EtraCalendarParser(zone_param="zone"),
    ),
    "Bassano del Grappa": _Municipality(
        url="https://www.comune.bassano.vi.it",
        zones=("C", "D"),
        fetch=FirstMatchRetriever(
            candidates=_recent_years,
            url=lambda year, zone, **_: _BASSANO_PDF.format(
                year=year, zone=_zone(zone, ("C", "D"))
            ),
            accept=_is_pdf,
        ),
        # One PDF per zone, no sub-columns.
        parse=EtraCalendarParser(zone_param=None),
    ),
}
_DEFAULT_MUNICIPALITY = "San Martino di Lupari"


def _zone(zone: Any, zones: tuple[str, ...]) -> str:
    return lookups.resolve({letter: letter for letter in zones}, zone, argument="zone")


def _serves(name: str) -> Any:
    """``Branch.when``: is ``name`` the configured municipality (and the zone its)?"""

    def when(municipality: Any, zone: Any, **_: Any) -> bool:
        chosen = lookups.resolve(
            {key: key for key in _MUNICIPALITIES}, municipality, argument="municipality"
        )
        if chosen != name:
            return False
        _zone(zone, _MUNICIPALITIES[name].zones)
        return True

    return when


@final
class Source(BaseSource):
    TITLE = "ETRA S.p.A."
    DESCRIPTION = "Waste collection schedule for ETRA S.p.A. municipalities, Italy."
    URL = "https://www.etraspa.it"
    COUNTRY = "it"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@jan-tdy"]
    RAISE_ON_EMPTY = True

    # The vocabulary this feed actually produces (mapped 1:1 in type_value_map
    # below, so nothing falls through to the shared resolver).
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "San Martino di Lupari, zone A": {"zone": "A"},
        "San Martino di Lupari, zone B": {
            "municipality": "San Martino di Lupari",
            "zone": "B",
        },
        "Bassano del Grappa, zone C": {
            "municipality": "Bassano del Grappa",
            "zone": "C",
        },
        "Bassano del Grappa, zone D": {
            "municipality": "Bassano del Grappa",
            "zone": "D",
        },
    }

    PARAMS = (
        dropdown(
            "municipality",
            list(_MUNICIPALITIES),
            label="Municipality",
            default=_DEFAULT_MUNICIPALITY,
        ),
        dropdown(
            "zone",
            sorted(
                {zone for entry in _MUNICIPALITIES.values() for zone in entry.zones}
            ),
            label="Collection zone",
        ),
    )

    REGIONS = tuple(
        region(name, url=entry.url, municipality=name)
        for name, entry in _MUNICIPALITIES.items()
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose your municipality and its collection zone as printed on the "
            "ETRA calendar: A or B in San Martino di Lupari, C or D in Bassano "
            "del Grappa."
        ),
        "it": (
            "Scegli il comune e la zona di raccolta indicata sul calendario ETRA: "
            "A o B a San Martino di Lupari, C o D a Bassano del Grappa."
        ),
    }

    retrieve = FallbackRetriever(
        *(
            Branch(name, entry.fetch, when=_serves(name))
            for name, entry in _MUNICIPALITIES.items()
        )
    )

    parse = FirstNonEmptyBranch(
        {name: entry.parse for name, entry in _MUNICIPALITIES.items()}
    )

    transform = ICSTransformer(
        type_value_map={
            "Secco residuo": wt.GENERAL_WASTE,
            "Plastica e metalli": wt.RECYCLABLES,
            "Carta e cartone": wt.PAPER,
            "Vetro": wt.GLASS,
            "Verde e ramaglie": wt.GARDEN_WASTE,
            "Umido organico": wt.ORGANIC,
        }
    )
