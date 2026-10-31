"""City of Edinburgh's dated kerbside calendars, found by current street record."""

import datetime
from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import config_params, lookups, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.MarkedPdfCalendar import MarkedPdfCalendarParser
from waste_collection_schedule.transformers import JsonTransformer

_URL = "https://www.edinburgh.gov.uk"


def _street_record(response, *_, street):
    choices = {
        a.get_text(" ", strip=True): urljoin(response.url, a["href"])
        for a in BeautifulSoup(response.text, "html.parser").select("a[href]")
        if "/directory-record/" in a["href"]
    }
    matches = [
        url
        for name, url in choices.items()
        if lookups.normalize_loose(name) == lookups.normalize_loose(street)
    ]
    if len(matches) != 1:
        raise SourceArgumentNotFoundWithSuggestions("street", street, sorted(choices))
    return matches[0]


def _calendar_link(response, *_, **__):
    links = {
        urljoin(response.url, a["href"])
        for a in BeautifulSoup(response.text, "html.parser").select("a[href]")
        if "/downloads/file/" in a["href"] and "kerbside-calendar" in a["href"]
    }
    if len(links) != 1:
        raise ValueError("Street record has no unambiguous kerbside calendar PDF")
    return links.pop()


def _current_year(records, source):
    if {record["date"].year for record in records} != {datetime.date.today().year}:
        raise ValueError("The council's published calendar does not cover this year")
    yield from records


@final
class Source(BaseSource):
    TITLE = "City of Edinburgh Council"
    DESCRIPTION = (
        "Source for Edinburgh kerbside recycling, glass and non-recyclable waste."
    )
    URL = _URL
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    TEST_CASES: ClassVar[dict] = {
        "Princess Mary Road": {"street": "Princess Mary Road"},
        "Ferry Road 700 - 764 Even": {"street": "Ferry Road 700 - 764 Even"},
        "Gilmerton Road 401-543 Odd & 406 - 500 Even": {
            "street": "Gilmerton Road 401-543 Odd & 406 - 500 Even"
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Ambiguous street query": {"street": "Ferry"},
    }
    PARAMS = (config_params.street(),)
    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your street at https://www.edinburgh.gov.uk/bin-collection-days "
            "under Recycling and waste. Enter the full record name, including any "
            "house-number range and Odd/Even suffix. The source follows the current "
            "street record and reads its annual PDF, including holiday changes. "
            "Green-bin recycling, the glass box and grey-bin waste are supported; "
            "food, garden and communal-bin services are not included. The published "
            "January grid has a duplicated day number; the complete weekday grid "
            "determines that date. An expired calendar fails explicitly."
        )
    }
    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{_URL}/directory/search",
                params=lambda street: {
                    "directoryID": "10251",
                    "keywords": street,
                    "search": "Search directory",
                },
                pick=_street_record,
            ),
            retrievers.Lookup(lambda record_url, **_: record_url, pick=_calendar_link),
        ),
        url=lambda _record_url, pdf_url, **_: pdf_url,
    )
    parse = MarkedPdfCalendarParser(
        months=recurrence.month_names("en"),
        weekdays=list("MTWTFSS"),
        year_pattern=r"JANUARY (20\d{2})",
        colors={"Grey bin": [(0, 0, 0)]},
        stroke_colors={"Recycling and glass": [(0, 0, 0)]},
        heading_year=True,
        max_duplicate_day_repairs=1,
    )
    preprocess = staticmethod(_current_year)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Grey bin": wt.GENERAL_WASTE,
            "Recycling and glass": [wt.RECYCLABLES, wt.GLASS],
        },
    )
