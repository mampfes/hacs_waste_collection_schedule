import datetime
from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import RowFilter
from waste_collection_schedule.transformers import HtmlTransformer

CALENDAR_URL = "https://him.as/tommekalender/"

# The calendar tags every collection with a Norwegian data-type attribute. Food
# waste, residual waste, paper, glass, plastic and metal packaging are six
# separate rounds on their own dates, so plastic and metal stay separate.
_TYPE_MAP = {
    "matavfall": wt.FOOD_WASTE,
    "restavfall": wt.GENERAL_WASTE,
    "papir": wt.PAPER,
    "plastemballasje": wt.PLASTIC,
    "glassemballasje": wt.GLASS,
    "metallemballasje": wt.METAL,
}

# Norwegian month names as used in the calendar headings, e.g. "Juli 2026".
_MONTHS = {
    "januar": 1,
    "februar": 2,
    "mars": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


def _is_collection(item, source) -> bool:
    """Only the six known rounds; an unknown data-type is skipped."""
    return item.get("data-type") in _TYPE_MAP


def _date(item) -> datetime.date | None:
    """The date of the day cell and month section a collection item sits in."""
    day = item.find_parent("td").select_one(".tommekalender__calendartable__date")
    section = item.find_parent("div", class_="tommekalender__month")
    heading = section.find("h2") if section is not None else None
    if day is None or heading is None:
        return None
    month_name, _, year = heading.get_text(strip=True).rpartition(" ")
    month = _MONTHS.get(month_name.strip().lower())
    day_text = day.get_text(strip=True)
    if month is None or not year.isdigit() or not day_text.isdigit():
        return None
    return datetime.date(int(year), month, int(day_text))


def _calendar_url(response, *_, address, **__) -> str:
    """The page of the calendar the address search resolves to.

    One hit renders the calendar right away. Zero or several hits render a
    table of candidate addresses instead; several properties (e.g. sections of
    one building) can share the exact same address, so picking it from the
    suggestions would never narrow the search down, and the first exact match
    is followed instead.
    """
    soup = BeautifulSoup(response.text, "html.parser")
    if soup.select_one("table.tommekalender__calendartable"):
        return response.url
    candidates = soup.select("div.table-wrap table tbody tr td a[href]")
    wanted = lookups.normalize_text(address)
    for a in candidates:
        if lookups.normalize_text(a.get_text()) == wanted:
            return urljoin(response.url or CALENDAR_URL, str(a["href"]))
    raise SourceArgumentNotFoundWithSuggestions(
        "address",
        address,
        list(dict.fromkeys(" ".join(a.get_text().split()) for a in candidates)),
    )


@final
class Source(BaseSource):
    TITLE = "Haugaland Interkommunale Miljøverk (HIM)"
    DESCRIPTION = (
        "Source for Haugaland Interkommunale Miljøverk (HIM) waste collection "
        "schedules, covering Haugesund and surrounding municipalities, Norway."
    )
    URL = "https://him.as"
    COUNTRY = "no"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.PLASTIC,
        wt.GLASS,
        wt.METAL,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Leiv Eirikssons Gate 10": {"address": "Leiv Eirikssons Gate 10"},
        "ØVREGATA 170": {"address": "ØVREGATA 170"},
        # Several properties share this address
        "Haraldsgata 100": {"address": "Haraldsgata 100"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://him.as/tommekalender/, search for your address and use "
            "the address exactly as shown, e.g. 'Leiv Eirikssons Gate 10'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                CALENDAR_URL,
                params=lambda address, **_: {"adressesok": address},
                pick=_calendar_url,
            ),
        ),
        url=lambda *keys, **_: keys[-1],
        raise_for_status=True,
    )
    parse = parsers.HtmlParser("li.tommekalender__calendartable__listitem")

    preprocess = RowFilter(_is_collection)

    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda item: item.get("data-type"),
        type_value_map=_TYPE_MAP,
    )
