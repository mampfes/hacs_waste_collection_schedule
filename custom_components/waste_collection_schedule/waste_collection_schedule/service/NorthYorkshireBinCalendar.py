"""North Yorkshire Council "bin calendar" (northyorks.gov.uk/bin-calendar).

North Yorkshire Council replaced the seven former district councils' own bin
lookups (Craven, Hambleton, Harrogate, Richmondshire, Ryedale, Scarborough,
Selby) with one Drupal module on its own site. The schedule is one POST per
property, ``/bin-calendar/<district>/results/<uprn>/ajax``, answered with a
Drupal AJAX command list whose ``insert`` command carries the results page as
an HTML string. That page lists the upcoming collections in a table, one row
per date, naming every round collected that day in the third cell (each round
after its own ``<i>`` icon)::

    retrieve = bin_calendar_retriever("Craven")
    parse = BinCalendarParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map=TYPE_VALUE_MAP,
    )

A property the district does not know is answered with a page saying so rather
than with an error status, and is reported as a wrong ``uprn``.
"""

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import HttpPostRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

URL = "https://www.northyorks.gov.uk/bin-calendar/{district}/results/{uprn}/ajax"
LOOKUP_PAGE = "https://www.northyorks.gov.uk/bin-calendar/lookup"

# The two pages the module answers an unusable UPRN with: one it does not know
# at all, and one it knows but cannot match to a collection round.
_NOT_FOUND = (
    "Unfortunately we were unable to find your property",
    "find your waste collection dates",
)

# The rounds the module names, across every district. Ryedale and Selby
# collect paper and containers separately; the other districts have one mixed
# recycling round.
TYPE_VALUE_MAP = {
    "Household waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden waste": wt.GARDEN_WASTE,
    "Paper, card and cardboard": wt.PAPER,
    "Glass, cans, plastic and cartons": wt.RECYCLABLES,
}


def _uprn_path(uprn: Any) -> str:
    # The module matches the UPRN as a number: one written with its leading
    # zeros ("010070735142", as the Hambleton lookup printed them) is not found.
    return str(uprn).strip().lstrip("0") or "0"


def bin_calendar_retriever(district: str) -> HttpPostRetriever:
    """The results request for one district, keyed by the ``uprn`` param."""
    return HttpPostRetriever(
        url=lambda uprn, **_: URL.format(district=district, uprn=_uprn_path(uprn)),
        params={"_wrapper_format": "drupal_ajax"},
        # Asked with a browser's Accept, Drupal wraps the command list in a
        # <textarea> (its iframe-upload transport) instead of answering JSON.
        headers={"Accept": "application/json"},
    )


class BinCalendarParser(Parser["list[tuple[str, str]]"]):
    """Read ``(date text, round)`` rows out of the AJAX reply's results page."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[str, str]]":
        name = response_shape.source_name(source)
        commands = response.json()
        html = next(
            (
                command["data"]
                for command in commands
                if isinstance(command, dict) and isinstance(command.get("data"), str)
            ),
            None,
        )
        if html is None:
            response_shape.expect(
                False,
                source_name=name,
                detail="bin calendar reply carries no results page",
                raw=response.text,
            )
            return []
        if any(marker in html for marker in _NOT_FOUND):
            raise SourceArgumentNotFound(
                "uprn",
                source.params.get("uprn") if source is not None else None,
                f"look your property up at {LOOKUP_PAGE}; the UPRN is the "
                "number at the end of the results page's URL",
            )

        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("#upcoming-collection table")
        if table is None:
            response_shape.expect(
                False,
                source_name=name,
                detail="bin calendar results page has no upcoming-collection table",
                raw=html,
            )
            return []

        rows: list[tuple[str, str]] = []
        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            date_text = cells[0].get_text(strip=True)
            for icon in cells[2].find_all("i"):
                label = str(icon.next_sibling or "").strip()
                if label:
                    rows.append((date_text, label))
        return rows
