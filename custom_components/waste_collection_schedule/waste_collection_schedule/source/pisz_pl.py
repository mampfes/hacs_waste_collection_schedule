"""Gmina Pisz, Poland.

The town publishes its yearly collection schedule as a news item ("HARMONOGRAM
ODBIORU ODPADÓW NA 2026 r") under
https://www.pisz.pl/pl/szczegoly-kategorii/69, with three text PDFs attached:
houses in Pisz (zabudowa jednorodzinna), blocks of flats in Pisz (zabudowa
wielorodzinna, mixed waste by street and house number) and the villages of the
gmina. Each lists, per waste fraction, the streets or villages followed by
their collection dates or by a weekday collected every week.
"""

import re
from typing import ClassVar, final
from urllib.parse import urljoin

import holidays
from bs4 import BeautifulSoup
from waste_collection_schedule import (
    config_params,
    parsers,
    preprocessors,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.pisz.pl"
_INDEX_URL = f"{_URL}/pl/szczegoly-kategorii/69"

_ANNOUNCEMENT = re.compile(r"ODBIORU ODPADÓW NA (\d{4})", re.IGNORECASE)

TOWN = "Pisz"
HOUSES = "jednorodzinna"
FLATS = "wielorodzinna"

MIXED = "Odpady zmieszane"
BIO = "Odpady biodegradowalne"
PAPER = "Makulatura"
GLASS = "Szkło"
PLASTIC = "Tworzywa sztuczne"
SELECTIVE = "Odpady segregowane"
BULKY = "Odpady wielkogabarytowe"
TEXTILES = "Zużyta odzież"

_SECTIONS = {
    r"ODPADY\s+ZMIESZANE\s+I\s+ODPADY\s+BIODEGRADOWALNE": (MIXED, BIO),
    r"KOMUNALNYCH\s+ZMIESZANYCH|ODPADÓW\s+ZMIESZANYCH": MIXED,
    r"ODPADY\s+BIODEGRADOWALNE": BIO,
    r"MAKULATURA,\s*SZKŁO,\s*TWORZYWA\s+SZTUCZNE": (PAPER, GLASS, PLASTIC),
    r"MAKULATURA,\s*TWORZYWA\s+SZTUCZNE": (PAPER, PLASTIC),
    r"(?m)^\s*SZKŁO\s*$": GLASS,
    # The villages' heading names no fractions.
    r"GROMADZONYCH\s+SELEKTYWNIE": SELECTIVE,
    r"WIELKOGABARYTOWYCH": BULKY,
    r"ZUŻYTEJ\s+ODZIEŻY": TEXTILES,
}


def _in_town(city: str) -> bool:
    return city.strip().casefold() == TOWN.casefold()


def _announcement(response, *_, **__) -> str:
    """Lookup pick: the newest yearly schedule announcement."""
    soup = BeautifulSoup(response.text, "html.parser")
    found: dict[int, str] = {}
    for link in soup.select("a[href*='/aktualnosc/']"):
        # The news item's card: the largest box around the link that links no
        # other news item.
        box = link
        while (parent := box.find_parent(["article", "li", "div"])) is not None and {
            a["href"] for a in parent.select("a[href*='/aktualnosc/']")
        } == {link["href"]}:
            box = parent
        if match := _ANNOUNCEMENT.search(box.get_text(" ")):
            found.setdefault(
                int(match.group(1)), urljoin(str(response.url), str(link["href"]))
            )
    response_shape.expect(
        bool(found),
        source_name="pisz_pl",
        detail="no yearly schedule announcement listed",
        raw=response.text[:500],
    )
    return found[max(found)]


def _calendar_pdf(response, *_, city: str, building: str | None = None, **__) -> str:
    """Lookup pick: the attached PDF for the villages, houses or flats."""
    if not _in_town(city):
        wanted = "gminy"
    elif building == FLATS:
        wanted = "wielorodzin"
    else:
        wanted = "jednorodzin"
    soup = BeautifulSoup(response.text, "html.parser")
    links = [
        urljoin(str(response.url), str(a["href"]))
        for a in soup.select("a[href*='attch']")
        if wanted in a.get_text(" ").casefold()
    ]
    response_shape.expect(
        bool(links),
        source_name="pisz_pl",
        detail=f"no attached schedule mentioning {wanted!r}",
        raw=response.text[:500],
    )
    return links[0]


def _place(city: str, street: str | None = None, **_) -> str:
    """The name the schedule lists: the street in Pisz, else the village."""
    return (street or "") if _in_town(city) else city


@final
class Source(BaseSource):
    TITLE = "Gmina Pisz"
    DESCRIPTION = "Source for Gmina Pisz (town of Pisz and its villages), Poland."
    URL = _URL
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.PLASTIC,
        wt.RECYCLABLES,
        wt.TEXTILES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Pisz, Wileńska": {"city": "Pisz", "street": "Wileńska"},
        "Pisz, Lipowa 12 (flats)": {
            "city": "Pisz",
            "street": "Lipowa",
            "house_number": "12",
            "building": FLATS,
        },
        "Rakowo Piskie": {"city": "Rakowo Piskie"},
    }

    PARAMS = (
        config_params.city("city"),
        config_params.street("street", optional=True),
        config_params.house_number("house_number", optional=True),
        config_params.dropdown(
            "building", [HOUSES, FLATS], label="Zabudowa", default=HOUSES
        ),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "In the town enter `Pisz`, your street as printed in the schedule "
            "(for example `Wileńska` or `Dr. Władysława Klementowskiego`) and "
            "whether you live in a house (`jednorodzinna`) or a block of flats "
            "(`wielorodzinna`); blocks of flats also need the house number. In "
            "a village enter only the village, for example `Rakowo Piskie`. "
            "The schedules are attached to the yearly announcement on "
            "https://www.pisz.pl/pl/szczegoly-kategorii/69."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_INDEX_URL, pick=_announcement),
            retrievers.Lookup(lambda page_url, **_: page_url, pick=_calendar_pdf),
        ),
        url=lambda page_url, pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = parsers.PdfTextParser(min_chars=500)
    preprocess = preprocessors.TextNamedBlocks(
        sections=_SECTIONS,
        name=_place,
        number="house_number",
        # A weekday collection falling on a holiday moves to the next
        # working day.
        holidays=lambda year: holidays.country_holidays("PL", years=year),
    )
    transform = ICSTransformer(
        type_value_map={
            MIXED: wt.GENERAL_WASTE,
            BIO: wt.ORGANIC,
            PAPER: wt.PAPER,
            GLASS: wt.GLASS,
            PLASTIC: wt.PLASTIC,
            SELECTIVE: wt.RECYCLABLES,
            BULKY: wt.BULKY_WASTE,
            TEXTILES: wt.TEXTILES,
        }
    )
