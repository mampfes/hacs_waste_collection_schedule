import datetime
from typing import ClassVar, final
from urllib.parse import urlencode

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

API = "https://webbservice.indecta.se/kunder/sam/kalender/basfiler"

# The calendar marks every collection with an empty cell whose class is the bin
# code. A code ending in `-H` is the same bin in a holiday week.
_HOLIDAY = " - Helgvecka"
_BINS = {
    "HKARL1": "Fyrfackskärl 1",  # food, residual, newspapers and coloured glass
    "HKARL2": "Fyrfackskärl 2",  # packaging and clear glass
    "HMAT": "Matavfall",
    "HREST": "Restavfall",
    "HOSORT": "Blandat Mat- och Restavfall",
    "FKARL1": "Fyrfackskärl 1",
    "FKARL2": "Fyrfackskärl 2",
    "FOSORT": "Blandat Mat- och Restavfall",
    "HREST-HK": "Restavfall med Hemkompost",
    "HKARL1-HK": "Fyrfackskärl 1 med Hemkompost",
    "TRG": "Trädgårdskärl",
    "FREST-HK": "Restavfall med Hemkompost",
    "FKARL1-HK": "Fyrfackskärl 1 med Hemkompost",
    "FREST": "Restavfall",
}

_MARKER = ", ".join(f"td.{code}, td.{code}-H" for code in _BINS)


def _address_id(response, *_keys, street: str = "", city: str = "", **_params) -> str:
    """The `nrA` of the address list line matching street and city."""
    wanted = f"{street}|{city}".lower()
    lines = response.text.splitlines()
    for line in lines:
        if wanted in line.lower():
            return line.split("|")[3]
    raise SourceArgumentNotFoundWithSuggestions(
        "street",
        street,
        [f"{p[0]}, {p[1]}" for p in (x.split("|") for x in lines) if len(p) > 3],
    )


def _code(cell: Tag) -> str:
    return next(c for c in cell["class"] if c.removesuffix("-H") in _BINS)


def _name(cell: Tag) -> str:
    code = _code(cell)
    return _BINS[code.removesuffix("-H")] + (_HOLIDAY if code.endswith("-H") else "")


def _date(cell: Tag) -> datetime.date:
    """The date of the day cell the marker sits in (month from the heading)."""
    day_cell = cell.find_parent("table").find_parent("td")
    day = day_cell.find("div", ["styleInteIdag", "styleIdag"]).get_text(strip=True)
    month_name, year = day_cell.find_previous("td", "styleMonthName").text.split("-")
    return datetime.date(int(year), recurrence.month(month_name) or 0, int(day))


@final
class Source(BaseSource):
    TITLE = "Samverkan Återvinning Miljö (SÅM)"
    DESCRIPTION = "Source for Samverkan Återvinning Miljö (SÅM) waste collection."
    URL = "https://www.samiljo.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name with number and the city as they appear in "
            "the calendar search on https://www.samiljo.se. Collections in a "
            "holiday week are marked 'Helgvecka' in the description."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.OTHER, wt.FOOD_WASTE, wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Test1": {"city": "Reftele", "street": "Storgatan 6"},
        "Test2": {"city": "Värnamo", "street": "Västra Kyrkogårdsgatan 2"},
        "Test3": {"city": "Burseryd", "street": "Storgatan 1"},
    }

    PARAMS = (street("street"), city("city"))

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/laddaadresser.php",
                params=lambda street, **_: {"svar": street},
                encoding="cp1252",
                pick=_address_id,
            ),
        ),
        url=lambda address_id, street, city, **_: (
            f"{API}/onlinekalender.php?"
            + urlencode(
                {"hsG": street, "hsO": city, "nrA": address_id}, encoding="cp1252"
            )
        ),
    )
    parse = parsers.HtmlParser(_MARKER)
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda cell: _name(cell).removesuffix(_HOLIDAY),
        description_getter=lambda cell: _name(cell),
        type_value_map={
            "Fyrfackskärl 1": wt.OTHER,
            "Fyrfackskärl 2": wt.OTHER,
            "Fyrfackskärl 1 med Hemkompost": wt.OTHER,
            "Matavfall": wt.FOOD_WASTE,
            "Restavfall": wt.GENERAL_WASTE,
            "Restavfall med Hemkompost": wt.GENERAL_WASTE,
            "Blandat Mat- och Restavfall": wt.OTHER,
            "Trädgårdskärl": wt.GARDEN_WASTE,
        },
    )
