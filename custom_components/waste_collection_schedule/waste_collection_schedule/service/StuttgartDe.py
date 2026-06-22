import datetime
from html.parser import HTMLParser
from typing import TYPE_CHECKING

from ..parsers import Parser
from ..retrievers import RetrieverFunc

if TYPE_CHECKING:
    from ..base_source import BaseSource


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# Abfall Stuttgart serves the schedule from one HTML form. The form must first
# be fetched to discover the available waste-type checkboxes, which are then
# echoed back in a POST together with the street, house number and date range;
# the response is an HTML page carrying the schedule in a ``#awstable`` table.
# The split:
#
#     retrieve = StuttgartRetriever()   # GET the form, POST the request
#     parse    = StuttgartParser()      # read #awstable into (date, label) rows
#
# StuttgartRetriever reads ``street`` and ``streetnr`` from source.params and
# returns the POST response; StuttgartParser does no I/O.
# --------------------------------------------------------------------------- #

API_URL = "https://service.stuttgart.de/lhs-services/aws/abfuhrtermine"


class _InputCheckboxParser(HTMLParser):
    """Collect the values of every ``<input>`` checkbox with a given name."""

    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self.value: list = []

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            d = dict(attrs)
            if d.get("name", "") == self._name:
                self.value.append(d.get("value"))


class _TableParser(HTMLParser):
    """Read ``(date, type)`` rows out of the ``#awstable`` schedule table."""

    def __init__(self):
        super().__init__()
        self._within_table = False
        self._within_tr = False
        self._within_th = False
        self._within_td = False
        self._col_index = 0
        self._type = ""
        self._date = ""
        self.entries: list[tuple[datetime.date, str]] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "table":
            if d.get("id", "") == "awstable":
                self._within_table = True
        elif tag == "tr":
            if self._within_table:
                self._within_tr = True
        elif tag == "th":
            if self._within_tr:
                if self._col_index == 0:
                    self._type = ""
                self._within_th = True
                self._col_index += 1
        elif tag == "td":
            if self._within_tr:
                self._within_td = True
                self._col_index += 1

    def handle_endtag(self, tag):
        if tag == "table":
            self._within_table = False
            self._type = ""
            self._date = ""
        elif tag == "tr":
            if self._within_tr and len(self._date) > 0:
                date = datetime.datetime.strptime(self._date, "%d.%m.%Y").date()
                self.entries.append((date, self._type))
                self._date = ""
            self._within_tr = False
            self._within_th = False
            self._within_td = False
            self._col_index = 0
        elif tag == "th":
            self._within_th = False
            self._type = self._type.strip()
        elif tag == "td":
            self._within_td = False

    def handle_data(self, data):
        if self._within_th and self._col_index == 1:
            self._type += data
        elif self._within_td and self._col_index == 2:
            self._date += data


class StuttgartRetriever(RetrieverFunc):
    """Discover the waste-type checkboxes, then POST the schedule request.

    Reads ``street`` and ``streetnr`` from source.params.
    """

    def __call__(self, source: "BaseSource"):
        params = source.params
        session = source.session

        # Discover the available waste-type checkboxes from the empty form.
        r = session.get(API_URL)
        r.raise_for_status()
        wastetypes = _InputCheckboxParser(name="calendar[wastetype][]")
        wastetypes.feed(r.text)

        now = datetime.datetime.now()
        args = [
            ("calendar[street]", params["street"]),
            ("calendar[streetnr]", params["streetnr"]),
            ("calendar[datefrom]", now.strftime("%d.%m.%Y")),
            ("calendar[dateto]", f"31.01.{now.year + 1}"),
        ]
        for w in wastetypes.value:
            args.append(("calendar[wastetype][]", w))
        args.append(("calendar[submit]", ""))

        r = session.post(API_URL, data=args)
        r.raise_for_status()
        return r


class StuttgartParser(Parser["list[tuple[datetime.date, str]]"]):
    """Read the ``#awstable`` schedule table into ``(date, label)`` rows.

    Does no I/O, so it runs standalone against a cached page fixture.
    """

    def __call__(
        self, response, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        parser = _TableParser()
        parser.feed(response.text)
        return parser.entries
