"""The i-web municipal CMS (Swiss municipalities), its ``/abfalldaten`` page.

i-web renders a municipality's collection calendar as one table,
``#icmsTable-abfallsammlung``, hydrated client-side from a JSON payload in its
``data-entities`` attribute. Each record is one collection event, every field an
HTML fragment::

    {"name": "<a ...>Kehricht</a>",
     "_anlassDate": "<span ...>30.09.2026<br>7.00 Uhr</span>...",
     "abfallkreisIds": ["190", "192"],
     "abfallkreisNameList": "Grafstal, Lindau"}

``_anlassDate`` holds one date, a date and a time or time span ("30.09.2026,
8.30 Uhr - 11.30 Uhr"), or a date span over several days ("26.10.2026 -
27.10.2026"). A municipality split into collection districts (Abfallkreise)
lists for every record the districts it applies to::

    parse = abfalldaten_parser()
    preprocess = AbfalldatenRows(area="city")
    transform = ICSTransformer(type_value_map={...})
"""

import datetime
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.parsers import AttributeJsonParser
from waste_collection_schedule.preprocessors import Preprocessor

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_DATE = r"\d{1,2}\.\d{1,2}\.\d{4}"
_DATE_SPAN = re.compile(rf"({_DATE})(?:\s*-\s*({_DATE}))?")


class _AbfalldatenParser(AttributeJsonParser):
    """``AttributeJsonParser`` that lets an HTTP error status propagate.

    ``AttributeJsonParser`` answers a page without the table with ``[]``. An
    error page (403, 5xx) has no table either, and on a ``RAISE_ON_EMPTY``
    source that empty list would be reported as a wrong argument, so an error
    status is raised here before the page is searched.
    """

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[Any]":
        response.raise_for_status()
        return super().__call__(response, source)


def abfalldaten_parser() -> AttributeJsonParser:
    """The ``/abfalldaten`` schedule records, their fields reduced to text."""
    return _AbfalldatenParser(
        "table#icmsTable-abfallsammlung[data-entities]",
        "data-entities",
        "data",
        require_keys=("_anlassDate",),
        strip_html=True,
    )


def _parse(text: str) -> datetime.date:
    return datetime.datetime.strptime(text, "%d.%m.%Y").date()


class AbfalldatenRows(Preprocessor[Any, "tuple[datetime.date, str]"]):
    """``(date, name)`` rows from the ``/abfalldaten`` records.

    Args:
        area: the ``source.params`` field naming the collection district, as its
            id or its name. Records for other districts are skipped. ``None``
            (the default) keeps every record, for a municipality with one
            district.
        expand_ranges: emit every day of a date span ("16.10.2026 -
            17.10.2026") rather than only its first day.
    """

    def __init__(self, *, area: "str | None" = None, expand_ranges: bool = False):
        self.area = area
        self.expand_ranges = expand_ranges

    def _in_area(self, record: dict, wanted: str) -> bool:
        ids = [str(value) for value in record.get("abfallkreisIds") or []]
        names = [
            name.strip()
            for name in str(record.get("abfallkreisNameList") or "").split(",")
        ]
        return wanted in ids or wanted.casefold() in (n.casefold() for n in names)

    def __call__(
        self, records: Any, source: "BaseSource | None" = None
    ) -> Iterable[tuple[datetime.date, str]]:
        wanted = None
        if self.area is not None and source is not None:
            wanted = str(source.params.get(self.area) or "").strip() or None
        for record in records:
            if wanted is not None and not self._in_area(record, wanted):
                continue
            name = str(record.get("name") or "").strip()
            match = _DATE_SPAN.search(str(record.get("_anlassDate") or ""))
            if not name or match is None:
                continue
            first = _parse(match.group(1))
            last = _parse(match.group(2)) if match.group(2) else first
            if not self.expand_ranges:
                last = first
            day = first
            while day <= last:
                yield day, name
                day += datetime.timedelta(days=1)
