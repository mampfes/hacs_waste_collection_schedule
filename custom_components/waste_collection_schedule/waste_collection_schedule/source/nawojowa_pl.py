import datetime
import re
from collections.abc import Iterator
from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfRow, PdfTableParser
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

MIXED = "Niesegregowane (zmieszane) odpady komunalne"
SELECTIVE = "Selektywnie zbierane odpady komunalne"
BIO = "Bioodpady"

# The municipality's home page carries a single banner link to the current
# yearly schedule PDF (an opaque, rotating attachment URL).
_INDEX_URL = "https://nawojowa.pl"
_PDF_PATTERN = r"/attch/article_attch-[\d-]+\.pdf"  # codespell:ignore attch

# Each table lists the same four collection areas in this order.
_AREAS = {
    "Nawojowa I": 0,
    "Nawojowa II": 1,
    "Popardowa Niżna": 0,
    "Frycowa": 2,
    "Bącza-Kunina": 2,
    "Homrzyska": 2,
    "Złotne": 2,
    "Żeleźnikowa Mała": 3,
    "Żeleźnikowa Wielka": 3,
    "Popardowa Wyżna": 3,
}

# Words left of this x position hold the area descriptions; the month columns
# start to the right of it.
_DAYS_X0 = 350.0


def _month_days(text: str) -> list[list[int]]:
    """Split a row's day numbers into months.

    Days within one month are comma separated ("14, 27" or "1,15,29"); a token
    without a trailing comma closes the month.
    """
    months: list[list[int]] = []
    current: list[int] = []
    for token in text.split():
        current.extend(int(n) for n in re.findall(r"\d{1,2}", token))
        if token.endswith(","):
            continue
        months.append(current)
        current = []
    return months


def _section_type(text: str) -> str | None:
    folded = lookups.normalize_loose(text)
    if "niesegregowane" in folded:
        return MIXED
    if "selektywnie" in folded:
        return SELECTIVE
    if folded.startswith("bio"):
        return BIO
    return None


def _rows(
    rows: list[PdfRow], source: BaseSource | None = None
) -> Iterator[tuple[datetime.date, str]]:
    area = lookups.resolve(
        _AREAS,
        source.params["area"] if source else "",
        argument="area",
        normalize=lookups.normalize_loose,
    )
    year = datetime.date.today().year
    for row in rows:
        match = re.search(r"31\.12\.(20\d{2})", " ".join(w.text for w in row.words))
        if match:
            year = int(match.group(1))
            break

    waste_type: str | None = None
    index = 0
    for row in rows:
        label = " ".join(w.text for w in row.words if w.x0 < _DAYS_X0)
        section = _section_type(label)
        if section:
            waste_type, index = section, 0
            continue
        days_text = " ".join(w.text for w in row.words if w.x0 >= _DAYS_X0)
        if waste_type is None or not re.fullmatch(r"[\d,\s]+", days_text or "x"):
            continue
        months = _month_days(days_text)
        if len(months) != 12:
            continue
        if index == area:
            for month, days in enumerate(months, 1):
                for day in days:
                    try:
                        yield datetime.date(year, month, day), waste_type
                    except ValueError:
                        continue
        index += 1


@final
class Source(BaseSource):
    TITLE = "Gmina Nawojowa"
    DESCRIPTION = "Source for Gmina Nawojowa waste collection schedule (Poland)"
    URL = "https://nawojowa.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    TEST_CASES: ClassVar[dict] = {
        "Nawojowa I": {"area": "Nawojowa I"},
        "Nawojowa II": {"area": "Nawojowa II"},
        "Frycowa": {"area": "Frycowa"},
        "Zeleznikowa Wielka": {"area": "Żeleźnikowa Wielka"},
    }

    PARAMS = (config_params.dropdown("area", list(_AREAS), label="Area"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your village. Nawojowa is split into Nawojowa I and "
            "Nawojowa II by street; see the street lists in the schedule PDF "
            "linked on https://nawojowa.pl."
        ),
    }

    retrieve = PdfLinkRetriever(
        index_url=_INDEX_URL, pattern=_PDF_PATTERN, select="first"
    )
    parse = PdfTableParser(min_words=50)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            MIXED: wt.GENERAL_WASTE,
            SELECTIVE: wt.RECYCLABLES,
            BIO: wt.ORGANIC,
        }
    )
