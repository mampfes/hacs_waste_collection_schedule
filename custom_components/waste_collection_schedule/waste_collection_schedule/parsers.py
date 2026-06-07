"""Standard response parsers for waste collection sources.

Each parser is a function that takes a raw HTTP response and returns
parsed data in a format suitable for the source's classify() method.
"""

import datetime
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup


def json(self, response: requests.Response):
    """Parse response as JSON."""
    return response.json()


def text(self, response: requests.Response) -> str:
    """Return response as plain text."""
    return response.text


def html(self, response: requests.Response) -> BeautifulSoup:
    """Parse response as HTML."""
    return BeautifulSoup(response.text, "html.parser")


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
