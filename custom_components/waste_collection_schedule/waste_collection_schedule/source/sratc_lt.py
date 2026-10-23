import datetime
import re
from collections.abc import Iterator
from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import PdfRow, PdfTableParser
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

GENERAL = "Buitinės atliekos"
PACKAGING = "Pakuotės ir antrinės žaliavos"
GLASS = "Stiklas"
GREEN = "Žaliosios atliekos"
BULKY = "Didžiosios atliekos"

# The Šiauliai city schedules page links the yearly "all waste types" PDF for
# individual households, e.g. uploads/2026_Siauliu_m_individualios.pdf.
_INDEX_URL = "https://www.sratc.lt/grafikai-siauliu-miestas/"
_PDF_PATTERN = r"(20\d{2})[^/]*individuali[^/]*\.pdf$"

_MONTHS = {
    name: number
    for number, name in enumerate(
        (
            "sausis",
            "vasaris",
            "kovas",
            "balandis",
            "geguze",
            "birzelis",
            "liepa",
            "rugpjutis",
            "rugsejis",
            "spalis",
            "lapkritis",
            "gruodis",
        ),
        1,
    )
}

# Column headers ("Buitinių atliekų grafikas", ...), matched by their first word.
_COLUMNS = {
    "buitiniu": GENERAL,
    "pakuociu": PACKAGING,
    "stiklo": GLASS,
    "zaliuju": GREEN,
    "didziuju": BULKY,
}


def _fold(value: object) -> str:
    return lookups.normalize_loose(value)


def _entries(name: str) -> list[str]:
    """Split a block's street list on top-level commas.

    "Bielskio g. (nuo 44 iki 88 ir nuo 59 iki 101)., Erškėčių g.," gives
    ["Bielskio g. (nuo 44 iki 88 ir nuo 59 iki 101)", "Erškėčių g."].
    """
    parts: list[str] = []
    depth, current = 0, ""
    for char in name.replace(",,", "„"):  # SB ,,Ramunė” opens with two commas
        depth += {"(": 1, ")": -1}.get(char, 0)
        if char == "," and depth <= 0:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    entries: list[str] = []
    for part in parts:
        part = re.sub(r"\)\.$", ")", re.sub(r"\s+", " ", part).strip())
        if not _fold(part):
            continue
        if part.startswith("(") and entries:
            entries[-1] = f"{entries[-1]} {part}"
        elif part[0].isdigit() and entries:  # "Vyturių g. 10a, 10b."
            entries[-1] = f"{entries[-1]}, {part}"
        else:
            entries.append(part)
    return entries


def _blocks(
    rows: list[PdfRow],
) -> Iterator[tuple[str, list[tuple[str, int, int]]]]:
    """Yield (street list, [(label, month, day), ...]) per street block.

    Every block starts with the column header row and lists one row per month;
    each row repeats the month name in front of every column's day list, so the
    days between two month names belong to one column. Street names are the
    text left of the first month name, anywhere in the block.
    """
    labels: list[str] = []
    name: list[str] = []
    days: list[tuple[str, int, int]] = []
    started = False
    for row in rows:
        folded = [_fold(w.text) for w in row.words]
        header = [
            _COLUMNS[f.split()[0]]
            for f in folded
            if f.split()[:1] and f.split()[0] in _COLUMNS
        ]
        if len(header) == len(_COLUMNS):
            if started:
                yield " ".join(name), days
            labels, name, days, started = header, [], [], True
            continue
        if not started:
            continue
        positions = [i for i, f in enumerate(folded) if f in _MONTHS]
        first = positions[0] if positions else len(row.words)
        name.extend(w.text for w in row.words[:first])
        for column, start in enumerate(positions):
            end = positions[column + 1] if column + 1 < len(positions) else None
            text = " ".join(w.text for w in row.words[start + 1 : end])
            for day in re.findall(r"\d{1,2}", text):
                days.append((labels[column], _MONTHS[folded[start]], int(day)))
    if started:
        yield " ".join(name), days


def _select(
    blocks: list[tuple[str, list[tuple[str, int, int]]]], street: str
) -> list[tuple[str, int, int]]:
    """Pick the block of ``street``: a full entry, a bare street name or text."""
    wanted = _fold(street)
    entries = [(entry, days) for name, days in blocks for entry in _entries(name)]
    for match in (
        lambda entry: _fold(entry) == wanted,
        lambda entry: _fold(entry.split("(")[0]) == wanted,
        lambda entry: f" {wanted} " in f" {_fold(entry)} ",
    ):
        found = [(entry, days) for entry, days in entries if match(entry)]
        schedules = {tuple(days) for _, days in found}
        if len(schedules) == 1:
            return found[0][1]
        if found:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street, sorted({entry for entry, _ in found})
            )
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, sorted({entry for entry, _ in entries})
    )


def _rows(
    rows: list[PdfRow], source: BaseSource | None = None
) -> Iterator[tuple[datetime.date, str]]:
    year = datetime.date.today().year
    for row in rows:
        match = re.search(r"GRAFIKAS\s+(20\d{2})", " ".join(w.text for w in row.words))
        if match:
            year = int(match.group(1))
            break
    blocks = list(_blocks(rows))
    street = source.params["street"] if source else ""
    for label, month, day in _select(blocks, street):
        try:
            yield datetime.date(year, month, day), label
        except ValueError:
            continue


@final
class Source(BaseSource):
    TITLE = "Šiaulių regiono atliekų tvarkymo centras (Šiauliai city)"
    DESCRIPTION = (
        "Source for the Šiauliai city waste collection schedule of individual "
        "households (ŠRATC, Lithuania)"
    )
    URL = "https://www.sratc.lt"
    COUNTRY = "lt"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Plateliu g.": {"street": "Platelių g."},
        "Bielskio g. 44-88": {
            "street": "Bielskio g. (nuo 44 iki 88 ir nuo 59 iki 101)"
        },
        "SB Rasa": {"street": "SB “Rasa”"},
    }

    PARAMS = (config_params.street(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street as printed in the yearly schedule for individual "
            'households ("Visų rūšių atliekų surinkimas") on '
            'https://www.sratc.lt/grafikai-siauliu-miestas/, e.g. "Platelių g.". '
            "Where a street is split by house numbers, use the full entry, e.g. "
            '"Bielskio g. (nuo 44 iki 88 ir nuo 59 iki 101)"; an ambiguous '
            "street lists the possible entries. Apartment blocks "
            "(daugiabučiai) are not supported."
        ),
    }

    retrieve = PdfLinkRetriever(index_url=_INDEX_URL, pattern=_PDF_PATTERN)
    parse = PdfTableParser(min_words=500)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            GENERAL: wt.GENERAL_WASTE,
            PACKAGING: wt.RECYCLABLES,
            GLASS: wt.GLASS,
            GREEN: wt.GARDEN_WASTE,
            BULKY: wt.BULKY_WASTE,
        }
    )
