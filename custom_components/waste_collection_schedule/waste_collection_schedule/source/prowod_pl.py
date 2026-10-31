"""PROWOD, gmina Dobrzeń Wielki, Poland.

PROWOD publishes a yearly announcement ("Harmonogram wywozu odpadów na 2026
rok") on https://prowod.pl/556/harmonogramy-wywozu-odpadow.html linking one PDF
calendar per rejon (Dobrzeń Wielki, Dobrzeń Mały / DW II, Chróścice, Kup, Os.
Energetyk, businesses). Each PDF holds a half year per page as month grids
whose day cells are painted in the colour of the fraction collected. A second
fraction on the same day is drawn as a coloured frame around the cell (BIO
with leaf bags, or mixed waste on Os. Energetyk), and Os. Energetyk paints its
combined paper and plastic collection as a yellow-to-blue gradient.
"""

import re
from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import (
    config_params,
    lookups,
    preprocessors,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://prowod.pl"
_INDEX_URL = f"{_URL}/556/harmonogramy-wywozu-odpadow.html"

_YEARLY = re.compile(r"harmonogram-wywozu-odpadow-na-(\d{4})-rok", re.IGNORECASE)

BIO = "BIO"
LEAVES = "Worki z liśćmi"
MIXED = "Odpady zmieszane"
PLASTIC = "Plastik i metale"
PAPER = "Papier i tektura"
GLASS = "Szkło"
ASH = "Popiół"
TEXTILES = "Odzież i tekstylia"

# Day cells are about 20 x 20 points; a few rows are drawn shorter.
_CELL = (17.0, 24.0)
_CELL_HEIGHT = (12.0, 24.0)
_FRAME = (1.5, 4.5)


def _yearly_page(response, *_, **__) -> str:
    """Lookup pick: the newest yearly announcement linking the calendars."""
    soup = BeautifulSoup(response.text, "html.parser")
    pages = {
        int(match.group(1)): urljoin(str(response.url), str(a["href"]))
        for a in soup.select("a[href]")
        if (match := _YEARLY.search(str(a["href"])))
    }
    response_shape.expect(
        bool(pages),
        source_name="prowod_pl",
        detail="no yearly calendar announcement linked",
        raw=response.text[:500],
    )
    return pages[max(pages)]


def _rejon(link: Tag) -> str:
    """'Dobrzeń Mały_DW II - HARMONOGRAM 2026 (PDF | 4,15MB)' -> 'Dobrzeń Mały DW II'."""
    name = re.split(r"HARMONOGRAM", link.get_text(" ", strip=True))[0]
    return name.replace("_", " ").strip(" -")


def _cell(label: str, color: tuple[float, ...], **kwargs) -> Marker:
    return Marker(label, color, width=_CELL, height=_CELL_HEIGHT, **kwargs)


@final
class Source(BaseSource):
    TITLE = "PROWOD"
    DESCRIPTION = "Source for PROWOD (gmina Dobrzeń Wielki) waste collection."
    URL = _URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.TEXTILES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Dobrzeń Mały": {"rejon": "Dobrzeń Mały DW II"},
        "Chróścice": {"rejon": "Chróścice"},
        "Osiedle Energetyk": {"rejon": "os Energetyk"},
    }

    PARAMS = (config_params.district("rejon"),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Enter your rejon as named in the calendar links of the yearly "
            "announcement on https://prowod.pl/556/harmonogramy-wywozu-odpadow.html: "
            "`Dobrzeń Wielki`, `Dobrzeń Mały DW II`, `Chróścice`, `Kup`, "
            "`os Energetyk` or `Firmy niezamieszkałe`. Each calendar lists the "
            "streets of its rejon at the top."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_INDEX_URL, pick=_yearly_page),
            retrievers.Lookup(
                lambda page_url, **_: page_url,
                pick=lookups.link_pick(
                    "rejon",
                    href=r"/download/attachment/\d+/[^/?]+\.pdf",
                    label=_rejon,
                ),
            ),
        ),
        url=lambda page_url, pdf_url, **_: pdf_url,
        timeout=90,
    )
    parse = MarkerCalendarParser(
        [
            # The CMYK calendars.
            _cell(BIO, (0.03, 0.69, 1.0, 0.16)),
            _cell(BIO, (0.1, 0.71, 1.0, 0.5)),
            _cell(MIXED, (0.0, 0.0, 0.0, 1.0)),
            _cell(PLASTIC, (0.03, 0.0, 0.93, 0.0)),
            _cell(PAPER, (0.72, 0.12, 0.0, 0.0)),
            _cell(GLASS, (0.8, 0.0, 0.93, 0.0)),
            _cell(ASH, (0.0, 0.0, 0.0, 0.3), tolerance=0.06),
            _cell(TEXTILES, (0.0, 0.28, 0.15, 0.0)),
            _cell(LEAVES, (0.8, 0.0, 0.93, 0.0), frame=_FRAME),
            # Os. Energetyk (RGB).
            _cell(BIO, (0.78, 0.35, 0.07)),
            _cell(PAPER, (0.0, 0.69, 0.94)),
            _cell(GLASS, (0.0, 0.69, 0.31)),
            _cell(TEXTILES, (1.0, 0.8, 0.8)),
            _cell(GLASS, (0.0, 0.69, 0.31), frame=_FRAME),
            _cell(MIXED, (0.0,), frame=_FRAME),
            # The gradient is drawn as thin bands; the one behind the day
            # number is the middle of the gradient.
            Marker(
                f"{PAPER}|{PLASTIC}",
                (0.48, 0.84, 0.49),
                tolerance=0.06,
                width=_CELL,
                height=(0.0, 1.0),
            ),
        ],
        placement="cell",
        weekdays=("Pn", "Wt", "Śr", "Cz", "Pt", "So", "N"),
        year_pattern=r"(20\d{2})\s*r\.",
    )
    preprocess = preprocessors.SplitLabels(r"\|")
    transform = ICSTransformer(
        type_value_map={
            BIO: wt.ORGANIC,
            LEAVES: wt.GARDEN_WASTE,
            MIXED: wt.GENERAL_WASTE,
            PLASTIC: wt.RECYCLABLES,
            PAPER: wt.PAPER,
            GLASS: wt.GLASS,
            ASH: wt.OTHER,
            TEXTILES: wt.TEXTILES,
        }
    )
