"""The Luxembourg waste calendar open data set (``data.public.lu``).

One semicolon-separated CSV lists every collection of every commune (about
7 MB), with the columns ``Date``, ``Type de collecte``, ``Commune``,
``Localité`` and ``Rue``. The file cannot be filtered server side, so
:class:`CalendarParser` narrows it to the household: the commune first, then
the locality and the street for the communes that split their schedule that
far. A row without a locality, or with the street "Toutes les rues", applies to
everything below it.
"""

from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import CsvParser, Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

CSV_URL = "https://data.public.lu/fr/datasets/r/c3805ec5-7836-49a4-9983-effaf81910d0"

ALL_STREETS = "Toutes les rues"


def _cell(row: dict[str, str], column: str) -> str:
    return (row.get(column) or "").strip()


class CalendarParser(Parser["list[dict[str, str]]"]):
    """The distinct collection rows of the configured commune, locality, street."""

    def __init__(
        self,
        commune: str = "commune",
        locality: str = "localite",
        street: str = "rue",
    ):
        self.commune = commune
        self.locality = locality
        self.street = street
        self._csv = CsvParser(
            delimiter=";", require=["Date", "Type de collecte", "Commune"]
        )

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[dict[str, str]]":
        rows = self._csv(response, source)
        params = source.params if source else {}

        rows = self._narrow(
            rows, "Commune", self.commune, str(params.get(self.commune) or "")
        )
        rows = self._narrow(
            rows,
            "Localité",
            self.locality,
            str(params.get(self.locality) or ""),
            keep_blank=True,
        )
        rows = self._narrow(
            rows,
            "Rue",
            self.street,
            str(params.get(self.street) or ""),
            keep_blank=True,
            wildcard=ALL_STREETS,
        )

        seen: set[tuple[str, str]] = set()
        result = []
        for row in rows:
            key = (_cell(row, "Date"), _cell(row, "Type de collecte"))
            if all(key) and key not in seen:
                seen.add(key)
                result.append(row)
        return result

    @staticmethod
    def _narrow(
        rows: "list[dict[str, str]]",
        column: str,
        argument: str,
        wanted: str,
        *,
        keep_blank: bool = False,
        wildcard: str = "",
    ) -> "list[dict[str, str]]":
        """Keep the rows for ``wanted`` in ``column``.

        With ``keep_blank`` the rows that leave the column empty (and with
        ``wildcard`` the rows carrying that catch-all value) apply to every value
        and are kept too. A column that only holds those has nothing to choose
        from and is ignored.
        """
        wanted = wanted.strip()
        generic = {""} | ({wildcard} if wildcard else set())
        options = sorted(
            {_cell(r, column) for r in rows} - (generic if keep_blank else set())
        )
        if keep_blank and not options:
            return rows
        if not wanted:
            if keep_blank:
                raise SourceArgumentRequiredWithSuggestions(
                    argument, "required to narrow down the schedule", options
                )
            raise SourceArgumentNotFoundWithSuggestions(argument, wanted, options)
        if wanted not in options:
            raise SourceArgumentNotFoundWithSuggestions(argument, wanted, options)
        return [
            r
            for r in rows
            if _cell(r, column) == wanted
            or (keep_blank and _cell(r, column) in generic)
        ]
