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
- Vigonza gets ETRA's A5 booklet (``EtraBookletParser``), linked from ETRA's
  per-year calendar page under a file name that changes between years. Its
  four zones pick a collection column (1 and 2: zone A, 3 and 4: zone B) and
  the glass round labelled with the same number. Until the new year's page is
  up, last year's page is tried next; its booklet ends with next January.

``FallbackRetriever`` runs only the configured municipality's branches (their
``when`` also validates the municipality and zone before any request), in
order until one yields records, and ``FirstNonEmptyBranch`` hands the PDF to
that municipality's zone layout.
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
from waste_collection_schedule.service.EtraSpa import (
    EtraBookletParser,
    EtraCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_SAN_MARTINO_PAGE = (
    "https://www.comune.sanmartinodilupari.pd.it/"
    "documento_pubblico/calendario-etra-{year}/"
)
_BASSANO_PDF = (
    "https://www.etraspa.it/sites/etraspa.it/files/"
    "Bassano_CalendA4_2Z_{year}_{zone}.pdf"
)
_ETRA_CALENDARS = "https://www.etraspa.it/calendari-la-raccolta-differenziata-{year}"
_VIGONZA_BOOKLET = r"CALENDARIO_VIGONZA[^/]*?(20\d\d)[^/]*\.pdf$"


def _recent_years(**_: Any) -> tuple[int, int]:
    """This year's calendar first, then last year's while the new one is not up."""
    year = date.today().year
    return (year, year - 1)


def _is_pdf(response: Response) -> bool:
    return response.status_code == 200 and response.content.startswith(b"%PDF")


def _etra_calendars(years_back: int) -> Any:
    """ETRA's calendar page for this year (``0``) or an earlier one."""
    return lambda **_: _ETRA_CALENDARS.format(year=date.today().year - years_back)


class _Municipality(NamedTuple):
    url: str
    zones: tuple[str, ...]
    # Tried in order until one yields records.
    fetches: tuple[Any, ...]
    parse: EtraCalendarParser | EtraBookletParser


_MUNICIPALITIES: dict[str, _Municipality] = {
    "San Martino di Lupari": _Municipality(
        url="https://www.comune.sanmartinodilupari.pd.it",
        zones=("A", "B"),
        fetches=(
            PdfLinkRetriever(
                index_url=lambda **_: _SAN_MARTINO_PAGE.format(year=date.today().year),
                pattern=r"\.pdf$",
                select="first",
            ),
        ),
        # One PDF with "ZONA A" / "ZONA B" sub-columns.
        parse=EtraCalendarParser(zone_param="zone"),
    ),
    "Bassano del Grappa": _Municipality(
        url="https://www.comune.bassano.vi.it",
        zones=("C", "D"),
        fetches=(
            FirstMatchRetriever(
                candidates=_recent_years,
                url=lambda year, zone, **_: _BASSANO_PDF.format(
                    year=year, zone=_zone(zone, ("C", "D"))
                ),
                accept=_is_pdf,
            ),
        ),
        # One PDF per zone, no sub-columns.
        parse=EtraCalendarParser(zone_param=None),
    ),
    "Vigonza": _Municipality(
        url="https://www.comune.vigonza.pd.it",
        zones=("1", "2", "3", "4"),
        fetches=tuple(
            PdfLinkRetriever(
                index_url=_etra_calendars(years_back), pattern=_VIGONZA_BOOKLET
            )
            for years_back in (0, 1)
        ),
        # A5 booklet: "ZONA A" / "ZONA B" columns plus a glass column whose
        # rounds are labelled "Zona 1" to "Zona 4".
        parse=EtraBookletParser(
            zones={
                "1": ("ZONA A", "1"),
                "2": ("ZONA A", "2"),
                "3": ("ZONA B", "3"),
                "4": ("ZONA B", "4"),
            }
        ),
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
        "Vigonza, zone 1": {"municipality": "Vigonza", "zone": "1"},
        "Vigonza, zone 3": {"municipality": "Vigonza", "zone": "3"},
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
            "del Grappa, 1 to 4 in Vigonza (see the street list 'Il territorio' "
            "at the end of the calendar: zones 1 and 2 are zone A, 3 and 4 "
            "zone B, and the number also picks your glass round)."
        ),
        "it": (
            "Scegli il comune e la zona di raccolta indicata sul calendario ETRA: "
            "A o B a San Martino di Lupari, C o D a Bassano del Grappa, da 1 a 4 "
            "a Vigonza (vedi l'elenco delle vie 'Il territorio' in fondo al "
            "calendario: le zone 1 e 2 sono la zona A, le zone 3 e 4 la zona B, "
            "e il numero indica anche il giro del vetro)."
        ),
    }

    retrieve = FallbackRetriever(
        *(
            Branch((name, index), fetch, when=_serves(name))
            for name, entry in _MUNICIPALITIES.items()
            for index, fetch in enumerate(entry.fetches)
        )
    )

    parse = FirstNonEmptyBranch(
        {
            (name, index): entry.parse
            for name, entry in _MUNICIPALITIES.items()
            for index in range(len(entry.fetches))
        }
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
