"""Discover current TAMAX calendars from their municipality download pages.

TAMAX publishes each municipality's calendars on its own page under
``/harmonogramy/<voivodeship>/<municipality>/``. The ``/harmonogramy/``
overview repeats the same sections but is not kept in step: after the
half-yearly re-upload in July 2026 it still linked Koniusza's and Książ
Wielki's January calendars. Sources therefore look their link up on the
municipality page, and ``CalendarLink`` refuses the overview.
"""

import datetime
from collections.abc import Mapping
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

URL = "https://www.tamax.net.pl"


class CalendarLink:
    """Select one explicitly supported household route, without a dated URL.

    Each area maps to a text identifying its PDF link, matched
    case-insensitively in the link's ``href``, or with ``match_label=True`` in
    the link's printed label (for a PDF renamed every half-year). The link must
    name the current year unless ``require_year=False`` (a sheet running into
    the next year under its first year's label).
    """

    def __init__(
        self,
        municipality: str,
        areas: Mapping[str, str],
        *,
        match_label: bool = False,
        require_year: bool = True,
    ):
        self.municipality = municipality
        self.areas = dict(areas)
        self.match_label = match_label
        self.require_year = require_year

    def __call__(self, response, *_, area):
        if area not in self.areas:
            raise SourceArgumentNotFoundWithSuggestions("area", area, list(self.areas))
        if urlsplit(str(response.url)).path.rstrip("/") == "/harmonogramy":
            raise ValueError(
                "The TAMAX /harmonogramy/ overview is not kept up to date; "
                "look the calendar up on the municipality's own page"
            )
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
            label = link.parent.get_text(" ", strip=True)
            if (
                self.areas[area].casefold()
                not in (label if self.match_label else href).casefold()
            ):
                continue
            if ".pdf" in href.lower() and (
                not self.require_year or year in href + label
            ):
                matches.add(urljoin(response.url, href))
        if len(matches) != 1:
            raise ValueError("No unambiguous current-year TAMAX household calendar")
        return matches.pop()
