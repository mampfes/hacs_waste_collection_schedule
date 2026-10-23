import datetime
import re
from collections.abc import Iterator
from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfWordLayout, PdfWordLayoutParser
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

MIXED = "Odpady zmieszane"
BIO = "Bio"
PLASTIC = "Tworzywa sztuczne"
PAPER = "Papier"
GLASS = "Szkło"
ASH = "Popiół"

# Row labels of the yearly table, matched on their first word.
_ROW_LABELS = {
    "odpady": MIXED,
    "bio": BIO,
    "tworzywa": PLASTIC,
    "papier": PAPER,
    "szklo": GLASS,
    "popiol": ASH,
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

_MONTHS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")

# Row labels sit between the village names and the first month column.
_LABEL_X = (120.0, 235.0)

_PL_TRANS = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def _fold(value: object) -> str:
    return lookups.normalize_text(str(value).translate(_PL_TRANS))


def _rows(
    pages: list[PdfWordLayout], source: BaseSource | None = None
) -> Iterator[tuple[datetime.date, str]]:
    group = lookups.resolve(
        _TOWNS,
        source.params["town"] if source else "",
        argument="town",
        normalize=_fold,
    )
    words = list(pages[0].words) if pages else []
    text = " ".join(w.text for w in words)
    year_match = re.search(r"ROK\s+(20\d{2})", text)
    year = int(year_match.group(1)) if year_match else datetime.date.today().year

    # Month columns from the first roman-numeral header row.
    header = next(
        (w for w in sorted(words, key=lambda w: -w.y) if w.text == "XII"), None
    )
    if header is None:
        return
    columns = {
        w.text: w.x for w in words if abs(w.y - header.y) < 2 and w.text in _MONTHS
    }
    if len(columns) != 12:
        return
    col_x = [columns[m] for m in _MONTHS]

    # Bulky waste table below the yearly table is not parsed.
    bulky = next((w.y for w in words if _fold(w.text) == "zbiorka"), 0.0)

    labels: list[tuple[float, str]] = []
    for w in words:
        if _LABEL_X[0] <= w.x <= _LABEL_X[1] and bulky < w.y < header.y:
            kind = _ROW_LABELS.get(_fold(w.text).rstrip(","))
            if kind:
                labels.append((w.y, kind))
    labels.sort(key=lambda lab: -lab[0])

    # Each group starts at its "Odpady zmieszane" row; keep the wanted group.
    groups: list[list[tuple[float, str]]] = []
    for label in labels:
        if label[1] == MIXED or not groups:
            groups.append([])
        groups[-1].append(label)
    if group >= len(groups):
        return
    rows = groups[group]

    for w in words:
        if not (bulky < w.y < header.y) or w.x < col_x[0] - 15:
            continue
        number = w.text.rstrip(",")
        if not number.isdigit():
            continue
        # A wrapped cell belongs to the nearest row label; skip other groups.
        nearest = min(labels, key=lambda lab: abs(lab[0] - w.y))
        if nearest not in rows:
            continue
        kind = nearest[1]
        month = min(range(12), key=lambda i: abs(col_x[i] - w.x)) + 1
        try:
            yield datetime.date(year, month, int(number)), kind
        except ValueError:
            continue


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
    preprocess = staticmethod(_rows)
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
