import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import Compose
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

# The public page http://www.fyrfackronneby.se/hamtningskalender/ embeds an
# iframe from kalender.fyrfackronneby.se, which is the actual service. An
# address search returns an id that the calendar request needs, and the
# calendar then comes back as a page whose script holds the events of a
# fullCalendar widget:
#
#   { title: 'Kärl 1 –  373 liter: Mat, Brännbart, färgat glas, tidningar.', start: '2023-09-12' },
#
# Only the text after the colon names the waste; the bin size in front of it
# varies. The API covers the so called "Fyrfack" (four slot) bins of ordinary
# houses, not apartment buildings or municipal properties.
API = "https://kalender.fyrfackronneby.se"

# Only single-line events count: the page also carries a commented-out
# multi-line "Title 1" / "Title 2" sample.
_EVENT_RE = re.compile(r"\{ title: '([^']*)', start: '([^']*)' \}")


def _split_address(street_address: str) -> tuple[str, str]:
    """The address is given as "<street>, <city>"."""
    street, _, city = str(street_address).partition(",")
    if not city.strip():
        raise SourceArgumentNotFound("street_address", street_address)
    return street.strip(), city.strip()


def _pickup_id(response, *keys, street_address: str, **_) -> str:
    """The id of the search hit matching both the street and the city."""
    street, city = _split_address(street_address)
    soup = BeautifulSoup(response.text, "html.parser")
    hits = []
    for item in soup.select("li[id]"):
        address = item.select_one("span.address")
        place = item.select_one("span.city")
        if address is None or place is None:
            continue
        hits.append(
            f"{address.get_text().strip()}, {place.get_text().strip()}",
        )
        if address.get_text() == street and place.get_text() == city:
            return str(item["id"])
    raise SourceArgumentNotFoundWithSuggestions("street_address", street_address, hits)


def _events(text: str, source) -> list[dict]:
    """One record per calendar event, labelled with the text after the colon."""
    return [
        {"date": start, "label": title.partition(":")[2].strip() or title.strip()}
        for title, start in _EVENT_RE.findall(text)
    ]


# Labels as they appear after the colon. Several waste streams share one bin.
_PACKAGING = [wt.RECYCLABLES, wt.PAPER, wt.GLASS]
_TYPE_MAP: dict = {
    "Mat, Brännbart, färgat glas, tidningar.": [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.PAPER,
    ],
    "Plast, pappersförpackningar, ofärgat glas, metall.": _PACKAGING,
    "Brännbart avfall": wt.GENERAL_WASTE,
    "Restavfall": wt.GENERAL_WASTE,
    "Komposterbart avfall": wt.ORGANIC,
    "Färgat glas": wt.GLASS,
    "Ofärgat glas": wt.GLASS,
    "Metallförpackningar": wt.RECYCLABLES,
    "Plastförpackningar": wt.RECYCLABLES,
    "Pappersförpackningar": wt.PAPER,
    "Tidningar/returpapper": wt.PAPER,
}


@final
class Source(BaseSource):
    TITLE = "Ronneby Miljöteknik"
    DESCRIPTION = "Source for Ronneby Miljöteknik waste collection."
    URL = "http://www.fyrfackronneby.se"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Home": {"street_address": "Hjortsbergavägen 16, Johannishus"},
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address and city separated by a comma, as they "
            "appear when you search for your address on "
            "http://www.fyrfackronneby.se/hamtningskalender/, e.g. "
            "'Hjortsbergavägen 16, Johannishus'."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{API}/search_suggestions.php",
                method="POST",
                data=lambda street_address, **_: {
                    "search_address": _split_address(street_address)[0]
                },
                pick=_pickup_id,
            ),
        ),
        url=f"{API}/get_data.php",
        method="POST",
        data=lambda pickup_id, street_address, **_: {
            "chosen_address": " ".join(_split_address(street_address)),
            "chosen_address_pickupid": pickup_id,
        },
        headers={"Accept-Language": "sv-SE,sv;q=0.9"},
        raise_for_status=True,
    )
    parse = parsers.TextParser()
    preprocess = Compose(_events)
    transform = JsonTransformer(
        date_key="date",
        type_key="label",
        type_value_map=_TYPE_MAP,
        carry_raw_label=True,
    )
