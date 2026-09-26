"""The ``bbd_whitespace`` Drupal module, UK councils' "bin day" lookup.

Some UK councils (Hart, Erewash) front their Whitespace collection data with a
Drupal module on their own site. One GET per UPRN,
``<site>/bbd-whitespace/one-year-collection-dates?uprn=...``, returns a Drupal
AJAX command list whose ``settings`` command carries a year of collections,
grouped by month::

    [{"command": "settings", "settings": {"collection_dates": {
        "9_2026": [{"date": "2026-09-01", "service": "Refuse Collection Service",
                    "service-identifier": "refuse-collection-service", ...}]}}}]

The module also lists "Christmas Collection Dates", the substitute days around
the new year without saying which round they replace; ``TYPE_VALUE_MAP`` drops
them rather than publish a collection of unknown type.
"""

from typing import TYPE_CHECKING, Any

from waste_collection_schedule import date_parsers, response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import HttpGetRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

PARSE_DATE = date_parsers.for_format("%Y-%m-%d")

# The councils' own round names, "<name> Collection Service".
TYPE_VALUE_MAP = {
    "Refuse Collection Service": wt.GENERAL_WASTE,
    "Domestic Waste Collection Service": wt.GENERAL_WASTE,
    "Recycling Collection Service": wt.RECYCLABLES,
    "Garden Waste Collection Service": wt.GARDEN_WASTE,
    "Food Waste Collection Service": wt.FOOD_WASTE,
    "Food Collection Service": wt.FOOD_WASTE,
    "Christmas Collection Dates": None,
}


def collection_dates_retriever(site: str) -> HttpGetRetriever:
    """The year of collections for the ``uprn`` param, from ``site``."""
    return HttpGetRetriever(
        url=f"{site.rstrip('/')}/bbd-whitespace/one-year-collection-dates",
        params=lambda uprn, **_: {"uprn": uprn, "_wrapper_format": "drupal_ajax"},
    )


class CollectionDatesParser(Parser["list[dict[str, Any]]"]):
    """The collection records of the reply, across all months."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[dict[str, Any]]":
        response.raise_for_status()
        commands = response.json()
        months = next(
            (
                command["settings"]["collection_dates"]
                for command in commands
                if isinstance(command, dict)
                and isinstance(command.get("settings"), dict)
                and "collection_dates" in command["settings"]
            ),
            None,
        )
        if months is None:
            response_shape.expect(
                False,
                source_name=response_shape.source_name(source),
                detail="bbd-whitespace reply carries no collection_dates",
                raw=response.text,
            )
            return []
        # An unknown UPRN answers with an empty list rather than a mapping.
        if not isinstance(months, dict):
            return []
        return [record for month in months.values() for record in month or []]
