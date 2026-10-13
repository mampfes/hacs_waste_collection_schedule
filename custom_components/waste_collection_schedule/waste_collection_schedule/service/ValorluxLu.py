"""The Valorlux (Luxembourg) blue-bag calendar.

``/api/calendar/all`` returns every commune's collection dates in one JSON
document: ``cities`` maps a commune to its tours (a commune served by a single
tour uses the empty string as the tour name), and each tour to a list of
``d/mm/yy`` dates. ``otherAddresses`` and ``addresses`` only list the streets of
a tour and carry no dates, so they are ignored. :class:`ValorluxParser` picks the
configured commune and tour out of it.
"""

from typing import TYPE_CHECKING

from requests import Response

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_URL = "https://www.valorlux.lu/api/calendar/all"
LABEL = "PMC"

retriever = Request(
    API_URL,
    headers={
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.valorlux.lu/",
    },
)


class ValorluxParser(Parser["list[tuple[str, str]]"]):
    """``(date, label)`` rows of the configured commune and tour."""

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[str, str]]":
        params = source.params if source else {}
        commune = params.get("commune")
        zone = params.get("zone")

        data = response.json()
        communes = data.get("cities", {})
        names = sorted(communes)
        if not commune:
            raise SourceArgumentRequiredWithSuggestions("commune", "", names)
        if commune not in communes:
            raise SourceArgumentNotFoundWithSuggestions("commune", commune, names)

        tours = communes[commune]
        zones = list(tours)
        if len(zones) > 1 and not zone:
            raise SourceArgumentRequiredWithSuggestions("zone", "", zones)
        if zone and zone not in zones:
            raise SourceArgumentNotFoundWithSuggestions("zone", zone, zones)
        dates = tours[zone] if zone else tours[zones[0]]
        return [(value, LABEL) for value in dates]
