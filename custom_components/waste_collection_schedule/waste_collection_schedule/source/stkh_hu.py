import datetime
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GARDEN_WASTE, RECYCLABLES

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource as _Base

# Demonstrates: a text-PDF calendar driven by parsers.PdfTextParser. STKH (Sopron
# és Térsége, Hungary) publishes one PDF per municipality whose text layer is a
# tabular schedule: each waste-type row lists full MM.DD. dates per month. The
# parser returns the page text unchanged; the only source-specific code is the
# preprocessor below, which turns that text into (date, type-key) rows. A plain
# ICSTransformer then maps each Hungarian type label onto a canonical WasteType.
#
# The mixed/residual waste (vegyes) is a fixed weekly recurrence stated only in
# prose ("Vegyes hulladékgyűjtési nap: kedd"), not as dated table rows, so it is
# out of scope here; this source covers the two date-bearing rows (selective and
# green waste) that the text layer pairs explicitly with dates.

# Hungarian table row labels -> a type key the ICSTransformer maps to a WasteType.
_TYPE_KEYS = {
    "szelektív": "szelektiv",
    "zöldhulladék": "zoldhulladek",
}

# A full MM.DD. date cell, e.g. "01.26." or "12.28.".
_DATE_RE = re.compile(r"\b(\d{2})\.(\d{2})\.")

# The calendar year, e.g. "2026. évi hulladéknaptár".
_YEAR_RE = re.compile(r"(\d{4})\.\s*évi")


def _calendar_year(text: str) -> int:
    """Read the schedule year from the document, falling back to the current year."""
    match = _YEAR_RE.search(text)
    if match:
        return int(match.group(1))
    return datetime.date.today().year


def _split_rows(text: str) -> Iterable[tuple[str, str]]:
    """Yield (type-label, dates-segment) for each waste-type row in the table.

    A row begins at a known type label and runs until the next label or the end
    of the table block, so a row whose dates wrap across several extracted lines
    is captured as one segment.
    """
    labels = sorted(_TYPE_KEYS, key=len, reverse=True)
    label_re = re.compile("(" + "|".join(re.escape(label) for label in labels) + ")")

    matches = list(label_re.finditer(text))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        yield match.group(1), text[start:end]


@final
class Source(BaseSource):
    TITLE = "STKH Sopron és Térsége"
    DESCRIPTION = (
        "Waste collection schedule for municipalities served by STKH "
        "(Sopron és Térsége), Hungary, published as a per-municipality PDF."
    )
    URL = "https://www.stkh.hu"
    COUNTRY = "hu"
    CODEOWNERS = ["@markvp"]
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Újkér 2026": {
            "url": "https://stkh.hu/wp-content/uploads/2025/12/9472_Ujker_Hulladeknaptar2026.pdf"
        },
    }

    PARAMS = [text_field("url", "Calendar PDF URL")]

    HOWTO = {
        "en": (
            "Find your municipality's waste calendar (hulladéknaptár) PDF on "
            "https://www.stkh.hu (Szolgáltatásaink), then enter the direct PDF "
            "link as the 'Calendar PDF URL' value."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda url: url)
    parse = PdfTextParser(shape=200)

    def preprocessor(
        self, text: str, source: "_Base | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        """Turn the PDF text into (date, type-key) rows for the transformer."""
        year = _calendar_year(text)
        for label, segment in _split_rows(text):
            type_key = _TYPE_KEYS[label]
            for month_str, day_str in _DATE_RE.findall(segment):
                month, day = int(month_str), int(day_str)
                if 1 <= month <= 12 and 1 <= day <= 31:
                    try:
                        collection_date = datetime.date(year, month, day)
                    except ValueError:
                        continue
                    yield collection_date, type_key

    transformer = ICSTransformer(
        type_value_map={
            "szelektiv": RECYCLABLES,
            "zoldhulladek": GARDEN_WASTE,
        },
    )

    def __init__(self, url: str):
        super().__init__(url=url)
