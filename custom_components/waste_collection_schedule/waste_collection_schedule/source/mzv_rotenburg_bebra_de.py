from typing import ClassVar, final

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import (
    city,
    text_field,
)
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    ELECTRONICS,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
    preserved,
    resolve,
)

WEBAPP_URL = "https://www.mzv-rotenburg-bebra.de//webapp.html"

# Demonstrates: parsers.ArgumentGuard + parsers.IcsEventsParser + the classify()
# escape hatch.
# Notable: the endpoint answers an unknown `ort` with an ordinary web page and
# HTTP 200, so parsers.ArgumentGuard checks for the calendar marker first and
# raises against the `city` argument (listing the valid names off the web-app
# page) rather than reporting an empty calendar.
# Per-route filtering (yellow_route / paper_route) needs the ICS LOCATION /
# DESCRIPTION fields, which the (date, summary) tuples from parsers.IcsParser
# discard. parsers.IcsEventsParser exposes the full IcsEvent, and classify() does
# the route filtering plus route-suffix normalisation ("Gelbe Tonne 2",
# "Papier Ost", ...); the cleaned bin name is then classified by the shared
# multilingual vocabulary (resolve), not a per-source map.

_CITY_HINT = (
    "make sure the city is spelled exactly like in the link of the website "
    "https://www.mzv-rotenburg-bebra.de//webapp.html"
)


def _possible_cities(source=None) -> list[str]:
    """List the `ort` values linked from the provider's web-app page."""
    r = requests.get(WEBAPP_URL, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()

    soup = BeautifulSoup(r.content, "html.parser")
    cities: list[str] = []
    for link in soup.find_all("a", href=True):
        if not isinstance(link, Tag):
            continue
        href = str(link.get("href", ""))
        if "entsorgung.php?ort=" in href:
            cities.append(href.split("?ort=")[1])
    return cities


@final
class Source(BaseSource):
    TITLE = "MZV Rotenburg"
    DESCRIPTION = "Source for MZV Rotenburg."
    URL = "https://www.mzv-rotenburg-bebra.de"
    COUNTRY = "de"
    API_URL = "https://www.mzv-rotenburg-bebra.de/entsorgung.php"

    TEST_CASES: ClassVar[dict] = {
        "Rotenburg an der Fulda": {"city": "rote"},
        "Bebra": {"city": "bebra"},
        "Rotenburg an der Fulda 2 Ost": {
            "city": "rote",
            "yellow_route": "2",
            "paper_route": "Ost",
        },
    }

    PARAMS = (
        city(),
        text_field("yellow_route", "Gelbe Tonne Route", optional=True),
        text_field("paper_route", "Papier Route", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "de": (
            "Der Ort muss genau wie im `ort`-URL-Parameter der Links auf "
            "https://www.mzv-rotenburg-bebra.de//webapp.html geschrieben werden "
            "(z.B. `rote`, `bebra`). yellow_route / paper_route filtern nach "
            "Sammelroute, falls der Ort mehrere Routen hat."
        ),
    }

    # classify() produces these — declared explicitly (no transformer to derive from).
    WASTE_TYPES: ClassVar[list] = [
        RECYCLABLES,
        ORGANIC,
        GENERAL_WASTE,
        PAPER,
        BULKY_WASTE,
        ELECTRONICS,
    ]

    # min_events=1: a valid feed has at least one event; an HTML error page (no
    # events) is logged and raises ResponseShapeError.
    parse = parsers.ArgumentGuard(
        parsers.IcsEventsParser(min_events=1),
        argument="city",
        contains="BEGIN:VCALENDAR",
        suggestions=_possible_cities,
        hint=_CITY_HINT,
    )

    def __init__(
        self,
        city: str,
        yellow_route: str | None = None,
        paper_route: str | None = None,
    ):
        super().__init__(city=city, yellow_route=yellow_route, paper_route=paper_route)
        self._params = {"ort": city}
        self._headers = {"User-Agent": "Mozilla/5.0"}

    def classify(self, record) -> Collection | None:
        summary = (record.title or "").strip()
        if not summary:
            return None

        # The route label may appear in the summary, location or description.
        route_context = " ".join(
            part for part in (record.title, record.location, record.description) if part
        ).lower()

        bin_type = summary.removeprefix("Entsorgung ").strip().lower()

        yellow_route = self.params["yellow_route"]
        paper_route = self.params["paper_route"]
        if bin_type.startswith("gelbe tonne"):
            if yellow_route and yellow_route.lower() not in route_context:
                return None
            bin_type = "gelbe tonne"
        elif bin_type.startswith("papier"):
            if paper_route and paper_route.lower() not in route_context:
                return None
            bin_type = "papier"

        return Collection(
            date=record.date, waste_type=resolve(bin_type) or preserved(bin_type)
        )
