"""Shared client for The Events Calendar (Tribe) REST API, one venue per place.

Some municipal waste authorities run their collection calendar as a WordPress
site with "The Events Calendar" plugin: each collection is an event whose title
is the waste type, and each collection area (a village, a numbered tour of a
larger town, a street) is a *venue*::

    /wp-json/tribe/events/v1/venues?per_page=50&page=N
    /wp-json/tribe/events/v1/events?venue=<id>&per_page=50&page=N

Both endpoints are paged (50 a page at most, whatever ``per_page`` asks for),
and answer with ``total_pages``. :class:`TribeEventsRetriever` resolves the
user's place name to a venue id, then pages through that venue's upcoming
events and returns one response per page, for ``parsers.EachResponse`` around a
``parsers.JsonParser("events")``.
"""

import html
import re
from typing import TYPE_CHECKING

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Response, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_PER_PAGE = 50
_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _normalize(value: str) -> str:
    """Compare place names regardless of case, umlauts, dashes and spacing.

    Venue names carry a typographic en dash ("Sondershausen – Tour 3") that a
    user types as a hyphen.
    """
    value = html.unescape(value).strip().lower().translate(_UMLAUTS)
    return re.sub(r"[^a-z0-9]", "", value)


class TribeEventsRetriever(RetrieverFunc):
    """Resolve a venue by name, then fetch its events page by page.

    An unresolved name raises with the venue names that contain it (or all of
    them when none do), so the UI can suggest the spelling the site expects.

    Args:
        base_url: the site's scheme and host, e.g. ``https://abfall-kyffhaeuser.de``.
        venue: the source parameter holding the venue name.
    """

    def __init__(self, *, base_url: str, venue: str = "city"):
        self._api = f"{base_url.rstrip('/')}/wp-json/tribe/events/v1"
        self._venue = venue

    def _pages(
        self, source: "BaseSource", endpoint: str, params: dict
    ) -> list[Response]:
        responses: list[Response] = []
        page = 1
        while True:
            response = source.session.get(
                f"{self._api}/{endpoint}",
                params={**params, "per_page": _PER_PAGE, "page": page},
                timeout=30,
            )
            response.raise_for_status()
            responses.append(response)
            if page >= response.json().get("total_pages", 1):
                return responses
            page += 1

    def _venue_id(self, source: "BaseSource") -> int:
        wanted = source.params[self._venue]
        venues = [
            venue
            for response in self._pages(source, "venues", {})
            for venue in response.json().get("venues", [])
        ]
        target = _normalize(wanted)

        for venue in venues:
            if _normalize(venue["venue"]) == target:
                return int(venue["id"])

        # Fall back to a substring match, e.g. "Bad Frankenhausen" matching all
        # of its "Tour" venues, so the user gets a narrowed-down list.
        matches = [
            html.unescape(venue["venue"])
            for venue in venues
            if target in _normalize(venue["venue"])
        ]
        if not matches:
            matches = [html.unescape(venue["venue"]) for venue in venues]
        raise SourceArgumentNotFoundWithSuggestions(
            self._venue, wanted, sorted(matches)
        )

    def __call__(self, source: "BaseSource") -> list[Response]:
        return self._pages(source, "events", {"venue": self._venue_id(source)})
