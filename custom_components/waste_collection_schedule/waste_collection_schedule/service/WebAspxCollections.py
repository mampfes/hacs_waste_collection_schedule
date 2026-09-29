"""The ``WSCollExternal.asmx`` round-calendar service, UK councils' bin calendar.

Several councils (Mid Ulster, Mid and East Antrim, South Norfolk) front their
round data with one ASP.NET SOAP service, each on its own
``collections-<council>.azurewebsites.net`` host. One POST per UPRN,
``getRoundCalendarForUPRN``, answers with an XML envelope whose result element
holds an HTML calendar as escaped text::

    <getRoundCalendarForUPRNResult>&lt;b&gt;Refuse&lt;/b&gt;: ... &lt;table
    id="CalTab00"&gt;...</getRoundCalendarForUPRNResult>

The calendar is one ``table.newCalendarTable`` per month, a Monday-first grid.
A day with a collection carries an SVG whose ``<title>`` names the round, *in
place of the day number*, so a day's date is read from its position in the grid
rather than from the number in the cell. The titles abbreviate the round
("Ref date based on Round Name", "Grn date based on Round Name") and a cell may
list several, one per line. The legend the service prints uses each council's
own bin names, which the cells never repeat, so it is not read.
"""

import calendar
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import HttpPostRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

NAMESPACE = "http://webaspx-collections.azurewebsites.net/"

# The first word of a cell title names the round.
TYPE_VALUE_MAP = {
    "Ref": wt.GENERAL_WASTE,
    "Rec": wt.RECYCLABLES,
    "Grn": wt.GARDEN_WASTE,
    "Gar": wt.GARDEN_WASTE,
    "Foo": wt.FOOD_WASTE,
}

_ENVELOPE = f"""<?xml version="1.0" encoding="utf-8" ?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <getRoundCalendarForUPRN  xmlns="{NAMESPACE}">
            <council>{{council}}</council>
            <UPRN>{{uprn}}</UPRN>
            <from>Chtml</from>
        </getRoundCalendarForUPRN >
    </soap:Body>
</soap:Envelope>
"""


def calendar_retriever(host: str, council: str) -> HttpPostRetriever:
    """The calendar of the ``uprn`` param, from ``host`` for ``council``."""
    return HttpPostRetriever(
        url=f"https://{host}/WSCollExternal.asmx",
        data=lambda uprn, **_: _ENVELOPE.format(
            council=council, uprn=str(uprn).strip()
        ),
        headers={"Content-Type": "text/xml; charset=utf-8"},
    )


class CalendarParser(Parser["list[dict[str, str]]"]):
    """One ``{"date", "type"}`` record per round on each day of the calendar."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[dict[str, str]]":
        response.raise_for_status()
        name = response_shape.source_name(source)
        # The calendar is escaped HTML inside the envelope's result element; the
        # XML parser decodes the entities.
        envelope = BeautifulSoup(response.text, "xml")
        result = envelope.find("getRoundCalendarForUPRNResult")
        page = BeautifulSoup(result.get_text() if result else "", "html.parser")
        months = page.select("div#NewCalendar table")
        response_shape.expect(
            bool(months),
            source_name=name,
            detail="round calendar reply carries no calendar",
            raw=response.text,
        )

        records: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for month in months:
            header = month.find("th")
            try:
                month_name, year = header.get_text(strip=True).split(" ")  # type: ignore[union-attr]
                number = list(calendar.month_name).index(month_name)
                first_weekday, days = calendar.monthrange(int(year), number)
            except (AttributeError, ValueError):
                continue
            # Skip the month and weekday header rows; each week row opens with
            # an empty cell, and the grid starts on a Monday.
            for week, row in enumerate(month.find_all("tr")[2:]):
                for column, cell in enumerate(row.find_all("td")[1:]):
                    day = week * 7 + column - first_weekday + 1
                    if not 1 <= day <= days:
                        continue
                    for title in cell.select("svg title"):
                        for line in title.get_text().splitlines():
                            words = line.split()
                            if not words:
                                continue
                            key = (f"{year}-{number:02d}-{day:02d}", words[0])
                            if key not in seen:
                                seen.add(key)
                                records.append({"date": key[0], "type": key[1]})
        return records
