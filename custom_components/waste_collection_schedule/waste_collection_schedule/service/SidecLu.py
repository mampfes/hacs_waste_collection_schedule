"""The SIDEC (Luxembourg) collection calendar.

The calendar on the SIDEC homepage reads one JSON file per year,
``/collectes/<year>.json``: ``{"year": 2026, "communes": {"Mersch": {"menager":
["2026-01-05", ...], "bio": [...], ...}}}``. Each commune maps every waste
stream to its ISO dates, so :class:`SidecParser` only has to pick the
configured commune out of it. The commune names of the current year double as
the list of valid values.
"""

import datetime
import re
from typing import TYPE_CHECKING

from requests import Response

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request, YearlyRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

YEAR_URL = "https://sidec.lu/collectes/{year}.json"

#: the previous website's commune values carried an id, ``"Mersch (2611)"``;
#: the name alone identifies the commune now, so old configurations keep working
_LEGACY_ID = re.compile(r"\s*\(\d+\)\s*$")


def _commune_name(commune: str | None) -> str:
    return _LEGACY_ID.sub("", commune or "").strip()


class SidecParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, stream)`` rows of the configured commune across the fetched years.

    The first response is the current year; a commune missing there is a
    configuration error and lists the valid communes. A following year that
    does not (yet) list the commune is skipped.
    """

    def __call__(
        self, responses: "list[Response]", source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        commune = (source.params.get("commune") if source else None) or ""
        name = _commune_name(commune)
        rows: list[tuple[datetime.date, str]] = []
        for index, response in enumerate(responses):
            communes = response.json().get("communes", {})
            if name not in communes:
                if index == 0:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "commune", commune, sorted(communes)
                    )
                continue
            for stream, dates in communes[name].items():
                if not isinstance(dates, list):
                    continue  # e.g. "fournisseur": "mixte"
                rows.extend(
                    (datetime.date.fromisoformat(value), stream) for value in dates
                )
        return rows


#: one JSON file per year (next year too from October, best-effort)
retriever = YearlyRetriever(
    fetch=Request(lambda year, *_, **__: YEAR_URL.format(year=year)),
    rollover_month=10,
)
