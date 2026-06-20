from dataclasses import replace

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
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

# Demonstrates: parsers.IcsEventsParser + the classify() escape hatch.
# Notable: per-route filtering (yellow_route / paper_route) needs the ICS
# LOCATION / DESCRIPTION fields, which the (date, summary) tuples from
# parsers.IcsParser discard. parsers.IcsEventsParser exposes the full IcsEvent,
# and classify() does the route filtering plus route-suffix normalisation
# ("Gelbe Tonne 2", "Papier Ost", ...); the cleaned bin name is then classified
# by the shared multilingual vocabulary (resolve), not a per-source map.


class Source(BaseSource):
    TITLE = "MZV Rotenburg"
    DESCRIPTION = "Source for MZV Rotenburg."
    URL = "https://www.mzv-rotenburg-bebra.de"
    COUNTRY = "de"
    API_URL = "https://www.mzv-rotenburg-bebra.de/entsorgung.php"

    TEST_CASES = {
        "Rotenburg an der Fulda": {"city": "rote"},
        "Bebra": {"city": "bebra"},
        "Rotenburg an der Fulda 2 Ost": {
            "city": "rote",
            "yellow_route": "2",
            "paper_route": "Ost",
        },
    }

    PARAMS = [
        text_field("city", "City"),
        replace(text_field("yellow_route", "Gelbe Tonne Route"), required=False),
        replace(text_field("paper_route", "Papier Route"), required=False),
    ]

    HOWTO = {
        "de": (
            "Der Ort muss genau wie im `ort`-URL-Parameter der Links auf "
            "https://www.mzv-rotenburg-bebra.de//webapp.html geschrieben werden "
            "(z.B. `rote`, `bebra`). yellow_route / paper_route filtern nach "
            "Sammelroute, falls der Ort mehrere Routen hat."
        ),
    }

    # classify() produces these — declared explicitly (no transformer to derive from).
    WASTE_TYPES = [
        RECYCLABLES,
        ORGANIC,
        GENERAL_WASTE,
        PAPER,
        BULKY_WASTE,
        ELECTRONICS,
    ]

    _ics_parser = parsers.IcsEventsParser()

    def __init__(
        self,
        city: str,
        yellow_route: str | None = None,
        paper_route: str | None = None,
    ):
        super().__init__(city=city, yellow_route=yellow_route, paper_route=paper_route)
        self._city = city
        self._yellow_route = yellow_route
        self._paper_route = paper_route
        self._params = {"ort": city}
        self._headers = {"User-Agent": "Mozilla/5.0"}

    def parse(self, response, source):
        # The endpoint returns an ICS feed for a valid `ort`; an unknown city
        # yields non-ICS content. Detect that and raise with the list of valid
        # city names (recovered from the web-app page), matching the upstream
        # behaviour, instead of silently returning no events.
        if "BEGIN:VCALENDAR" not in response.text:
            try:
                cities = self._get_possible_cities()
            except Exception:
                raise SourceArgumentNotFound(
                    "city",
                    self._city,
                    "make sure the city is spelled exactly like in the link of "
                    "the website https://www.mzv-rotenburg-bebra.de//webapp.html",
                )
            raise SourceArgumentNotFoundWithSuggestions("city", self._city, cities)
        return self._ics_parser(response, source)

    @staticmethod
    def _get_possible_cities() -> list[str]:
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

    def classify(self, record) -> Collection | None:
        summary = (record.title or "").strip()
        if not summary:
            return None

        # The route label may appear in the summary, location or description.
        route_context = " ".join(
            part for part in (record.title, record.location, record.description) if part
        ).lower()

        bin_type = summary.removeprefix("Entsorgung ").strip().lower()

        if bin_type.startswith("gelbe tonne"):
            if self._yellow_route and self._yellow_route.lower() not in route_context:
                return None
            bin_type = "gelbe tonne"
        elif bin_type.startswith("papier"):
            if self._paper_route and self._paper_route.lower() not in route_context:
                return None
            bin_type = "papier"

        return Collection(
            date=record.date, waste_type=resolve(bin_type) or preserved(bin_type)
        )
