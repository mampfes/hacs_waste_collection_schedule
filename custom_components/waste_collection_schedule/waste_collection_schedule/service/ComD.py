"""Pipeline components for the COM-D (com-d.pl) municipal schedule pages.

COM-D publishes the waste schedules of several Polish municipalities under
``https://www.com-d.pl/komunalne/harm/<municipality>/<locality>``. A locality
page lists one row per waste fraction ("Frakcja") linking to a category page,
and each category page draws a calendar whose collection days are
``td.highlighted[data-date]`` cells. A category may carry several calendars
(for example single-family and multi-family housing), each introduced by a
"Częstotliwość" (frequency) line.

* :class:`ComdCategoryLookup` is the ``prepare`` of a
  :class:`~waste_collection_schedule.retrievers.FanOutRetriever`: it reads the
  locality page and returns the category page URLs, blaming ``location`` (with
  the municipality's valid localities) when the page does not exist.
* :class:`ComdCategoryParser` reads one category page into
  ``(date, label)`` rows for an ``ICSTransformer``, optionally keeping only the
  calendar of one dwelling type.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import Response

BASE_URL = "https://www.com-d.pl"


class ComdCategoryLookup:
    """List the category page URLs of one locality.

    Args:
        municipality: the municipality's slug in the COM-D URL
            (``sroda-slaska``).
        argument: the config param holding the locality slug.
    """

    def __init__(self, municipality: str, *, argument: str = "location"):
        self.municipality = municipality
        self.argument = argument
        self.base = f"{BASE_URL}/komunalne/harm/{municipality}"

    def __call__(self, source: BaseSource, keys: Sequence[Any] = ()) -> list[str]:
        location = source.params[self.argument]
        response = source.session.get(f"{self.base}/{location}", timeout=30)
        if response.status_code == 404:
            raise SourceArgumentNotFoundWithSuggestions(
                self.argument, location, self._localities(source)
            )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = next(
            (t for t in soup.find_all("table") if t.find("th", string="Frakcja")),
            None,
        )
        response_shape.expect(
            table is not None,
            source_name=response_shape.source_name(source),
            detail="schedule table (Frakcja) not found",
            raw=response.text,
        )
        assert table is not None
        hrefs = sorted(
            {link["href"] for link in table.select(f'a[href*="/{self.municipality}/"]')}
        )
        if not hrefs:
            raise SourceArgumentNotFound(
                self.argument, location, "no schedules are published for it"
            )
        return [urljoin(BASE_URL, str(href)) for href in hrefs]

    def _localities(self, source: BaseSource) -> list[str]:
        response = source.session.get(self.base, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return sorted(
            {
                str(link["href"]).rsplit("/", 1)[-1]
                for link in soup.find_all("a", href=True)
                if f"{self.municipality}/" in str(link["href"])
            }
        )


class ComdCategoryParser(Parser["list[tuple[datetime.date, str]]"]):
    """Collection days of one COM-D category page, labelled with its fraction.

    The label is the fraction name the page prints under "Harmonogram
    dotyczy". Calendars are associated with the frequency line preceding them
    in document order; a line naming a dwelling type scopes the calendars
    after it to that type, any other line scopes them to every type.

    Args:
        property_types: ``{param value: text in the frequency line}`` of the
            dwelling types, e.g. ``{"single_family": "zabudowa jednorodzinna"}``.
        argument: the config param holding the dwelling type; any value not in
            ``property_types`` (``all``) keeps every calendar.
    """

    def __init__(
        self, property_types: Mapping[str, str], *, argument: str = "property_type"
    ):
        self.property_types = dict(property_types)
        self.argument = argument

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        wanted = source.params.get(self.argument) if source is not None else None
        soup = BeautifulSoup(response.text, "html.parser")
        label_tag = soup.select_one("p.text-right span.label")
        response_shape.expect(
            label_tag is not None,
            source_name=response_shape.source_name(source),
            detail="fraction label not found",
            raw=response.text,
        )
        assert label_tag is not None
        label = label_tag.get_text(strip=True)

        current: str | None = None
        available: set[str] = set()
        days: list[tuple[str | None, str]] = []
        for element in soup.select("p, td.highlighted[data-date]"):
            if element.name == "p":
                text = " ".join(element.get_text(" ", strip=True).split()).casefold()
                if not text.startswith("częstotliwość"):
                    continue
                current = next(
                    (k for k, v in self.property_types.items() if v in text), None
                )
                if current is None and "zabudowa" in text:
                    response_shape.expect(
                        False,
                        source_name=response_shape.source_name(source),
                        detail=f"unrecognized dwelling type heading: {text}",
                    )
                if current is not None:
                    available.add(current)
            else:
                days.append((current, str(element["data-date"])))

        if wanted in self.property_types:
            if available and wanted not in available:
                raise SourceArgumentNotFoundWithSuggestions(
                    self.argument, wanted, ["all", *sorted(available)]
                )
            days = [(k, d) for k, d in days if k is None or k == wanted]
        return sorted({(datetime.date.fromisoformat(day), label) for _, day in days})
