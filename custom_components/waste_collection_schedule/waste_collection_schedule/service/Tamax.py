"""Discover current TAMAX calendars from their published download index."""

import datetime
from collections.abc import Mapping
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

URL = "https://www.tamax.net.pl"


class CalendarLink:
    """Select one explicitly supported household route, without a dated URL."""

    def __init__(self, municipality: str, areas: Mapping[str, str]):
        self.municipality = municipality
        self.areas = dict(areas)

    def __call__(self, response, *_, area):
        if area not in self.areas:
            raise SourceArgumentNotFoundWithSuggestions("area", area, list(self.areas))
        matches = set()
        year = str(datetime.date.today().year)
        soup = BeautifulSoup(response.text, "html.parser")
        panels = [
            soup.find(id=title.get("aria-controls"))
            for title in soup.select(".elementor-tab-title")
            if title.get_text(" ", strip=True)
            == f"Gmina {self.municipality} (mieszkańcy)"
        ]
        if len(panels) != 1 or panels[0] is None:
            raise ValueError(
                "TAMAX household municipality section is missing or ambiguous"
            )
        for link in panels[0].select("a[href]"):
            href = link["href"]
            if self.areas[area].casefold() not in href.casefold():
                continue
            label = link.parent.get_text(" ", strip=True)
            if ".pdf" in href.lower() and year in href + label:
                matches.add(urljoin(response.url, href))
        if len(matches) != 1:
            raise ValueError("No unambiguous current-year TAMAX household calendar")
        return matches.pop()
