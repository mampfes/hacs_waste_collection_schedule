"""Standard response parsers for waste collection sources.

Each parser is a function (or factory) that integrates with the
retrieve → parse → transform pipeline in BaseSource.

Simple parsers (assign directly):

    parse = parsers.json    # response.json() — list or dict of records
    parse = parsers.ics     # list of (date, summary) tuples

Factory parsers (call to configure, then assign):

    parse = parsers.html("tr", skip=1)  # list of <tr> elements, header skipped
"""

import datetime
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup


def json(*keys):
    """Parse response as JSON, optionally drilling into a nested key path.

    With no arguments, returns the top-level parsed value::

        parse = parsers.json()          # response.json()

    With one or more keys, walks the parsed value before returning::

        parse = parsers.json("collections")          # response.json()["collections"]
        parse = parsers.json("data", "items")        # response.json()["data"]["items"]

    If the response is already a list at the top level, omit keys entirely.
    """

    def _parse(self, response: requests.Response):
        data = response.json()
        for key in keys:
            data = data[key]
        return data

    return _parse


def text(self, response: requests.Response) -> str:
    """Return response as plain text."""
    return response.text


def html(selector: str, skip: int = 0):
    """Return a parser that extracts matching elements from HTML.

    Use with HtmlTransformer. The returned parser selects all elements
    matching ``selector`` (CSS selector syntax) and skips the first ``skip``
    results (handy for stripping header rows)::

        parse = parsers.html("tr", skip=1)   # all rows, skip header
        parse = parsers.html("ul.bins > li") # list items

    Each element is passed individually to the transformer.

    Args:
        selector: CSS selector string passed to BeautifulSoup.select().
        skip:     Number of leading elements to drop (default 0).
    """

    def _parse(self, response: requests.Response) -> list:
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.select(selector)[skip:]

    return _parse


def ics(self, response: requests.Response) -> List[Tuple[datetime.date, str]]:
    """Parse response as an iCalendar feed.

    Returns a list of (date, summary) tuples for all events in the next year.
    Use this with the default http_get retriever::

        parse = parsers.ics

        def classify(self, record) -> Collection | None:
            date, summary = record
            return Collection(date=date, waste_type=self._classify_type(summary))
    """
    from waste_collection_schedule.service.ICS import ICS

    return ICS().convert(response.text)


def ics_events(self, response: requests.Response) -> list:
    """Parse response as an iCalendar feed, exposing full event fields.

    Like :func:`ics`, but returns ``IcsEvent(date, title, location,
    description)`` records instead of bare ``(date, summary)`` tuples. Use this
    with ``classify()`` when the source must inspect the ICS ``LOCATION`` or
    ``DESCRIPTION`` fields — for example to filter events by collection route::

        parse = parsers.ics_events

        def classify(self, record) -> Collection | None:
            # record.title / record.location / record.description available
            return Collection(date=record.date, waste_type=...)
    """
    from waste_collection_schedule.service.ICS import ICS

    return ICS().convert_events(response.text)
