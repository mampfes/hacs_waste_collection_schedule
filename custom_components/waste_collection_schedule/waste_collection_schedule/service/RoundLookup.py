"""The "Round Lookup" bin-day portal (Malvern Hills, Wychavon, Worcester City).

Three Worcestershire councils run the same ``<council>roundlookup`` web app. A
property's UPRN is posted to its ``HandleSearchScreen`` form and the answer is
an HTML table, one row per round: an icon, the round name ("Recycling
collection") and the next dates, one per line. A round the household has no
service for says "Not applicable" instead of a date.

:func:`retriever` declares the POST, ``PARSE`` selects the table rows, and
:func:`rows` expands them into one ``(date, label)`` row per listed date;
``TRANSFORM`` reads the dates ("Thursday 22/08/2024") and maps the rounds.
"""

from collections.abc import Iterable

from bs4.element import Tag

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.transformers import RowTransformer, label_cleaner

API_URLS = {
    "Malvern Hills": "https://swict.malvernhills.gov.uk/mhdcroundlookup/HandleSearchScreen",
    "Wychavon": "https://selfservice.wychavon.gov.uk/wdcroundlookup/HandleSearchScreen",
    "Worcester City": "https://selfserve.worcester.gov.uk/wccroundlookup/HandleSearchScreen",
}


def retriever(council: str | None = None) -> retrievers.Request:
    """The search POST for ``council``, or for the source's ``council`` param."""
    return retrievers.Request(
        (lambda **_: API_URLS[council])
        if council
        else lambda council, **_: API_URLS[council],
        method="POST",
        data=lambda uprn, **_: {
            "alAddrsel": uprn,
            "txtPage": "std",
            "txtSearchPerformedFlag": "false",
            "futuredate": "",
            "address": "",
            "btnSubmit": "Next",
        },
    )


PARSE = parsers.HtmlParser("table tr", require=["table"])


def rows(records: Iterable[Tag], source=None) -> Iterable[tuple[str, str]]:
    """One ``(date, label)`` row per date listed in a round's table row."""
    for row in records:
        cells = row.select("td")
        if len(cells) != 3:
            continue
        name_cell = cells[1]
        for note in name_cell.select("div"):
            note.decompose()
        label = name_cell.get_text(" ", strip=True)
        dates = cells[2].get_text("\n", strip=True)
        if "Not applicable" in dates:
            continue
        for line in dates.splitlines():
            if line.strip():
                yield line.strip(), label


TRANSFORM = RowTransformer(
    parse_date=date_parsers.for_format("%A %d/%m/%Y"),
    clean=label_cleaner(strip_suffixes=[" collection"]),
    skip_unparseable_dates=True,
    type_value_map={
        "Non-recyclable waste": wt.GENERAL_WASTE,
        "Recycling": wt.RECYCLABLES,
        "Garden waste": wt.GARDEN_WASTE,
    },
)

WASTE_TYPES = [wt.GENERAL_WASTE, wt.GARDEN_WASTE, wt.RECYCLABLES]
