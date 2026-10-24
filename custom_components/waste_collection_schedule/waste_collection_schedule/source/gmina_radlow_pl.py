import datetime
from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfWordLayoutParser
from waste_collection_schedule.preprocessors import (
    Compose,
    GridBlock,
    PdfRoundMonthGrid,
)
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

MIXED = "Odpady zmieszane"
BIO = "Bio"
PLASTIC = "Tworzywa sztuczne"
PAPER = "Papier"
GLASS = "Szkło"
ASH = "Popiół"

# Row labels of the yearly table, as printed.
_ROW_LABELS = {
    "Odpady zmieszane": MIXED,
    "Bio": BIO,
    "Tworzywa sztuczne": PLASTIC,
    "Papier": PAPER,
    "Szkło": GLASS,
    "Popiół": ASH,
}

_INDEX_URL = (
    "https://www.gminaradlow.pl/dla-mieszkanca/gospodarowanie-odpadami/"
    "harmonogram-wywozu-odpadow"
)
_PDF_PATTERN = r"harmonogram[^/\"]*?(20\d{2})\.pdf$"

# The table has three village groups, in this order.
_TOWNS = {
    "Radłów": 0,
    "Glów": 0,
    "Brzeźnica": 0,
    "Biskupice Radłowskie": 1,
    "Łęka Siedlecka": 1,
    "Niwka": 1,
    "Wola Radłowska": 1,
    "Zabawa": 2,
    "Wał-Ruda": 2,
    "Sanoka": 2,
    "Siedlec": 2,
    "Zdrochec": 2,
    "Marcinkowice": 2,
    "Przybysławice": 2,
}


def _rows(
    blocks: list[GridBlock], source: BaseSource | None = None
) -> list[tuple[datetime.date, str]]:
    """The configured village's group: the table's blocks in order."""
    group = lookups.resolve(
        _TOWNS,
        source.params["town"] if source else "",
        argument="town",
        normalize=lookups.normalize_loose,
    )
    return blocks[group].rows if group < len(blocks) else []


@final
class Source(BaseSource):
    TITLE = "Gmina Radłów"
    DESCRIPTION = "Source for Gmina Radłów (Małopolska) waste collection schedule"
    URL = "https://www.gminaradlow.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PLASTIC,
        wt.PAPER,
        wt.GLASS,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Radlow": {"town": "Radłów"},
        "Biskupice Radlowskie": {"town": "Biskupice Radłowskie"},
        "Zabawa": {"town": "Zabawa"},
    }

    PARAMS = (config_params.dropdown("town", list(_TOWNS), label="Town"),)

    HOWTO: ClassVar[dict] = {
        "en": "Select your village in Gmina Radłów.",
    }

    retrieve = PdfLinkRetriever(index_url=_INDEX_URL, pattern=_PDF_PATTERN)
    parse = PdfWordLayoutParser(min_words=100)
    preprocess = Compose(
        PdfRoundMonthGrid(
            labels=_ROW_LABELS,
            block_start=MIXED,
            year_pattern=r"ROK\s+(20\d{2})",
            roman_months=True,
            # Row labels sit between the village names and the first month.
            label_x=(120.0, 235.0),
            # The bulky-waste table below the yearly table is not parsed.
            stop_pattern=r"^zbiorka$",
        ),
        _rows,
    )
    transform = ICSTransformer(
        type_value_map={
            MIXED: wt.GENERAL_WASTE,
            BIO: wt.ORGANIC,
            PLASTIC: wt.PLASTIC,
            PAPER: wt.PAPER,
            GLASS: wt.GLASS,
            ASH: wt.OTHER,
        }
    )
