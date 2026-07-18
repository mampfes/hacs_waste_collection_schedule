"""Redbridge Council, London, UK.

Demonstrates: the plainest text-PDF path. The council generates a per-property
calendar PDF (keyed by UPRN) whose text layer is a month-by-month grid, so a
plain ``PdfTextParser`` returns the whole text and a small preprocessor walks
it into ``(date, service)`` records. ``ICSTransformer`` maps the four service
names onto canonical WasteTypes. No layout mode, no coordinates: when a text
PDF reads cleanly, this is all a source needs.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import config_params
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import PdfTextParser
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

_API_URL = "https://my.redbridge.gov.uk/RecycleRefuse/GetFile"

# The service names the PDF prints, keyed by their leading word.
_KNOWN_SERVICES = {"REFUSE", "RECYCLING", "GARDEN", "FOOD"}

_MONTH_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{4})$",
    re.IGNORECASE,
)
_WEEKDAY_HEADER_RE = re.compile(
    r"^(Sun\s+Mon\s+Tue\s+Wed\s+Thu\s+Fri\s+Sat)$", re.IGNORECASE
)
# A day row: one or more day numbers separated by spaces, e.g. "1 2" or "3 4 5".
_DAY_ROW_RE = re.compile(r"^(?:\d{1,2})(?:\s+\d{1,2})*$")


def _is_boundary(line: str) -> bool:
    """True for a line that ends the service block following a day row."""
    lower = line.lower()
    return bool(
        _MONTH_RE.match(line)
        or _WEEKDAY_HEADER_RE.match(line)
        or _DAY_ROW_RE.match(line)
        or "your collection schedule" in lower
    )


@final
class Source(BaseSource):
    TITLE = "Redbridge Council"
    DESCRIPTION = "Source for redbridge.gov.uk services for Redbridge Council, UK."
    URL = "https://redbridge.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "council office recycling only": {"uprn": 10034922090},
        "refuse and recycling only": {"uprn": 10013585215},
        "a church vicarage, garden, recycling, refuse": {"uprn": 10034912354},
    }

    PARAMS = (config_params.uprn(),)

    retrieve = HttpGetRetriever(url=_API_URL, params=lambda uprn: {"uprn": uprn})
    parse = PdfTextParser(min_chars=100)

    transform = ICSTransformer(
        type_value_map={
            "REFUSE": GENERAL_WASTE,
            "RECYCLING": RECYCLABLES,
            "GARDEN": GARDEN_WASTE,
            "FOOD": FOOD_WASTE,
        }
    )

    def __init__(self, uprn: "str | int") -> None:
        super().__init__(uprn=str(uprn))

    def preprocess(self, text: str, source=None) -> Iterable[tuple[datetime.date, str]]:
        """Walk the calendar text, yielding (date, service-key) per collection.

        The grid renders as a month header, a weekday header, then day rows;
        the services printed after a day row belong to the last (largest) day
        number on that row.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        month = year = None
        i = 0
        while i < len(lines):
            line = lines[i]
            header = _MONTH_RE.match(line)
            if header:
                month = datetime.datetime.strptime(header.group(1), "%B").month
                year = int(header.group(2))
                i += 1
                continue
            if not (month and year and _DAY_ROW_RE.match(line)):
                i += 1
                continue

            days = [int(t) for t in line.split() if 1 <= int(t) <= 31]
            services: list[str] = []
            j = i + 1
            while j < len(lines) and not _is_boundary(lines[j]):
                key = lines[j].split(" ")[0].upper()
                if key in _KNOWN_SERVICES:
                    services.append(key)
                j += 1

            if days and services:
                try:
                    collection_date = datetime.date(year, month, max(days))
                except ValueError:
                    collection_date = None
                if collection_date is not None:
                    for key in services:
                        yield collection_date, key
            i = j
