"""Gemeng Bäertref (Berdorf), Luxembourg.

Demonstrates: a yearly calendar PDF whose URL rotates (opaque hashed path on a
third-party host) but is always linked from a stable landing page, so
``PdfLinkRetriever`` finds the current year's PDF instead of a hardcoded URL
that would break every January. The PDF itself is a fixed 2-page grid (page 0
Jan-Jun, page 1 Jul-Dec) with no month headers -- the month advances when the
day number resets -- so the page-wise parse stays source-specific. Each grid
cell names its waste types in free text (German/French), matched to labels that
``ICSTransformer`` maps onto canonical WasteTypes; labels with no canonical
equivalent (a textile round, the mixed organic-and-inert round) are preserved
verbatim. A second pass backfills SuperDrecksKëscht (hazardous) dates listed in
the info-text, which the coloured calendar overlay can hide in the grid.
"""

import re
from datetime import date
from io import BytesIO
from typing import ClassVar, final

from pypdf import PdfReader
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import HAZARDOUS, RECYCLABLES

_DATA_URL = "https://www.berdorf.lu/service-citoyens/dechets"

# German weekday abbreviations used in the PDF.
_WEEKDAYS = {"MO", "DI", "MI", "DO", "FR", "SA", "SO"}
# A grid line: "2FR H.müll / D.men.  Bio" -> day, weekday, free-text content.
_LINE_RE = re.compile(r"^(\d{1,2})([A-Za-z]{2,3})\s*(.*)")
# The PDF filename carries the calendar year: "offallkalenner-2026.pdf".
_PDF_RE = re.compile(r"offallkalenner-(\d{4})\.pdf", re.IGNORECASE)
# A full date in the info-text section, e.g. "17.02.2026".
_DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")

_SDK = "SuperDrecksKëscht"


def _waste_labels(content: str) -> list[str]:
    """Return the waste-type labels named in one grid cell's free text."""
    labels: list[str] = []
    if "H.müll" in content or "D.men." in content:
        labels.append("Hausmüll")
    if re.search(r"\bBio\b", content):
        labels.append("Biotonne")
    if "Glas" in content or "verre" in content:
        labels.append("Glas")
    if re.search(r"[Pp]apier", content):
        labels.append("Papier")
    if "PMC" in content:
        labels.append("PMC")
    if "Org.&inert" in content or "D.org.&inertes" in content:
        labels.append("Organische und inerte Abfälle")
    if "Sperrmüll" in content or "D.encombrants" in content:
        labels.append("Sperrmüll")
    if _SDK in content or re.search(r"\bSDK\b", content):
        labels.append(_SDK)
    if "Kleiders" in content:
        labels.append("Altkleidersammlung")
    return labels


def _sdk_dates(full_text: str) -> list[date]:
    """SuperDrecksKëscht dates from the info-text (backfills obscured grid cells)."""
    match = re.search(
        r"SuperDrecksK[eë]scht.*?Termine:?\s*([\d.,\s]+)", full_text, re.DOTALL
    )
    if not match:
        return []
    dates: list[date] = []
    for dm in _DATE_RE.finditer(match.group(1)):
        try:
            dates.append(date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1))))
        except ValueError:
            pass
    return dates


def _year_from_url(url: str) -> int:
    match = _PDF_RE.search(url)
    return int(match.group(1)) if match else date.today().year


@final
class Source(BaseSource):
    TITLE = "Gemeng Bäertref"
    DESCRIPTION = (
        "Source for Berdorf commune (Gemeng Bäertref) waste collection schedule, "
        "Luxembourg."
    )
    URL = "https://www.berdorf.lu"
    COUNTRY = "lu"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Berdorf": {},
    }

    retrieve = PdfLinkRetriever(
        index_url=_DATA_URL, pattern=r"offallkalenner-(\d{4})\.pdf"
    )

    transform = ICSTransformer(
        type_value_map={
            "PMC": RECYCLABLES,
            _SDK: HAZARDOUS,
        }
    )

    def __init__(self) -> None:
        super().__init__()

    def parse(self, response, source=None) -> list[tuple[date, str]]:
        year = _year_from_url(response.url)
        reader = PdfReader(BytesIO(response.content))
        page_texts = [page.extract_text() for page in reader.pages]

        records: list[tuple[date, str]] = []
        for page_num, page_text in enumerate(page_texts):
            # Page 0 covers Jan-Jun, page 1 Jul-Dec; the month advances when the
            # day number resets to a lower value (the PDF has no month headers).
            month = 7 if page_num == 1 else 1
            prev_day = 0
            for line in page_text.split("\n"):
                m = _LINE_RE.match(line.strip())
                if not m or m.group(2).upper() not in _WEEKDAYS:
                    continue
                day = int(m.group(1))
                if day < prev_day:
                    month += 1
                prev_day = day
                for label in _waste_labels(m.group(3).strip()):
                    try:
                        records.append((date(year, month, day), label))
                    except ValueError:
                        pass

        # Backfill SuperDrecksKëscht dates the coloured overlay can hide.
        seen_sdk = {d for d, label in records if label == _SDK}
        for d in _sdk_dates("\n".join(page_texts)):
            if d not in seen_sdk:
                records.append((d, _SDK))

        return records
