"""MPO Kraków, Poland.

Demonstrates: a plain text-PDF parse behind an address lookup. The schedule PDF
is reached through two JSON lookups (street name -> street id -> building id),
so ``retrieve`` stays source-specific, but once the PDF is in hand a plain
``PdfTextParser`` returns its text and a small preprocessor walks the linear
"weekday / day month / stacked waste types" blocks into ``(date, label)``
records. ``ICSTransformer`` maps the Polish labels onto canonical WasteTypes.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import config_params
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://kiedywywoz.pl/API/harmo_img/"
_TOKEN = "OkkxhC6b9etJBAq7WTHJ0LhIglO18sip"

# Polish month names (genitive, as printed) -> month number.
_MONTHS = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "października": 10,
    "listopada": 11,
    "grudnia": 12,
}

# A date block ("weekday\nDD monthword") followed by its stacked waste types.
_BLOCK_RE = re.compile(r"(\w+\n\d+\s\w+)\n([\w\s\-]+?)(?=\n\w+\n\d+\s\w+|$)")
_GEN_DATE_RE = re.compile(r"Data generowania:\s(\d{4})-\d{2}-\d{2}")


def _index(data: object, *, key_transform) -> dict[str, str]:
    """Build a {name: id} map from an API list, dropping placeholder rows."""
    if not isinstance(data, list):
        raise SourceArgumentNotFoundWithSuggestions(
            "street_name", "", []
        )  # unexpected API shape; surfaced as a lookup failure
    result: dict[str, str] = {}
    for item in data:
        name = key_transform(item["name"].strip())
        item_id = item["id"]
        if item_id != "0" and item["name"].strip() != "-Brak-":
            # Keep the smallest id when a name repeats (duplicate street rows).
            if name not in result or int(item_id) < int(result[name]):
                result[name] = item_id
    return result


@final
class Source(BaseSource):
    TITLE = "MPO Kraków"
    DESCRIPTION = "Source script for MPO Kraków"
    URL = "https://harmonogram.mpo.krakow.pl/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Romanowicza 1 DM": {"street_name": "Romanowicza", "building_number": "1 DM"},
        "Na Wrzosach 43 DJ": {"street_name": "Na Wrzosach", "building_number": "43 DJ"},
        "Świtezianki 7 DB": {"street_name": "Świtezianki", "building_number": "7 DB"},
        "Przewóz 40d DW": {"street_name": "Przewóz", "building_number": "40d DW"},
    }

    PARAMS = (
        config_params.street(field="street_name"),
        config_params.house_number(field="building_number"),
    )

    parse = PdfTextParser(min_chars=100)

    transform = ICSTransformer(
        type_value_map={
            "Zmieszane": GENERAL_WASTE,
            "Szkło": GLASS,
            "Papier": PAPER,
            "Tworzywa sztuczne": RECYCLABLES,
            "Bio": ORGANIC,
            "Zielone": GARDEN_WASTE,
            "Choinki": GARDEN_WASTE,
        }
    )

    def __init__(self, street_name: str, building_number: str) -> None:
        super().__init__(
            street_name=street_name.strip().title(),
            building_number=building_number.strip().upper(),
        )

    def retrieve(self, source):
        session = source.session
        street_name = source.params["street_name"]
        building_number = source.params["building_number"]

        streets = _index(
            session.post(_API_URL, data={"token": _TOKEN}).json(),
            key_transform=str.title,
        )
        street_id = streets.get(street_name)
        if not street_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name", street_name, sorted(streets)
            )

        numbers = _index(
            session.post(_API_URL, data={"ulica": street_id, "token": _TOKEN}).json(),
            key_transform=str.upper,
        )
        number_id = numbers.get(building_number)
        if not number_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "building_number", building_number, sorted(numbers)
            )

        pdf = session.get(
            f"{_API_URL}pdf/", params={"id_numeru": number_id, "token": _TOKEN}
        )
        pdf.raise_for_status()
        return pdf

    def preprocess(self, text: str, source=None) -> Iterable[tuple[datetime.date, str]]:
        """Walk the linear date blocks, yielding (date, label) per waste type."""
        year_match = _GEN_DATE_RE.search(text)
        year = int(year_match.group(1)) if year_match else datetime.date.today().year

        prev_month = None
        for date_block, types_block in _BLOCK_RE.findall(text):
            # date_block is "weekday\nDD monthword"; drop the weekday and day-of-week.
            parts = date_block.replace("\n", " ").split()
            day = int(parts[1])
            month = _MONTHS.get(parts[2].lower())
            if month is None:
                continue
            # Blocks run chronologically; a month going backwards means a new year.
            if prev_month is not None and prev_month > month:
                year += 1
            prev_month = month

            try:
                collection_date = datetime.date(year, month, day)
            except ValueError:
                continue
            for raw in types_block.replace("\n", ",").split(","):
                label = raw.strip().capitalize()
                if label:
                    yield collection_date, label
