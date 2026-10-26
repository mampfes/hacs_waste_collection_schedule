import calendar
import re
from datetime import date
from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, preprocessors, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.MarkedPdfCalendar import MarkedPdfCalendarParser
from waste_collection_schedule.transformers import JsonTransformer

_PAGE = "https://www.strathfield.nsw.gov.au/Live/Waste/Residential-Bin-Collection"


def _calendars(response, **_):
    soup = BeautifulSoup(response.text, "html.parser")
    urls = []
    for a in soup.select("a[href]"):
        url = urljoin(response.url, str(a["href"]))
        year = re.search(r"calendar-(20\d{2})", url, re.I)
        if (
            year
            and "english.pdf" in url.lower()
            and date.today().year <= int(year[1]) <= date.today().year + 1
            and url not in urls
        ):
            urls.append(url)
    if not urls:
        raise ValueError("Strathfield has no current published English waste calendar")
    return urls


def _weekday(record, source):
    text = source.params["collection_day"]
    day = recurrence.weekday(text)
    if day is None or day > 4:
        raise SourceArgumentNotFoundWithSuggestions(
            "collection_day", text, list(calendar.day_name)[:5]
        )
    return record["date"] >= date.today() and record["date"].weekday() == day


@final
class Source(BaseSource):
    TITLE = "Strathfield Council"
    DESCRIPTION = "Source for Strathfield Council, NSW, Australia."
    URL = "https://www.strathfield.nsw.gov.au"
    TEST_CASES: ClassVar[dict] = {
        "Monday collection": {"collection_day": "Monday"},
        "Tuesday collection": {"collection_day": "Tuesday"},
        "Wednesday collection": {"collection_day": "Wednesday"},
    }
    COUNTRY = "au"
    ERROR_TEST_CASES: ClassVar[dict] = {"Invalid weekday": {"collection_day": "Sunday"}}
    PARAMS = (text_field("collection_day", "Collection weekday"),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    HOWTO: ClassVar[dict] = {
        "en": "Enter the Monday-Friday collection day from your rates notice or the council's street guide. The current linked calendar supplies green/yellow weeks and actual dates. Dates stop at the published end instead of projecting a fixed anchor two years ahead. Types now use canonical, localised names; update filters and customisations using old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(_PAGE, pick=_calendars),
        targets=lambda source, urls: urls,
        fetch=retrievers.Request(lambda url, urls, **_: url),
    )
    parse = parsers.EachResponse(
        MarkedPdfCalendarParser(
            pages=(0,),
            months=tuple(calendar.month_name)[1:],
            weekdays=("M", "T", "W", "T", "F", "S", "S"),
            year_pattern=r"(20\d{2}) WASTE CALENDAR",
            colors={"yellow": ((0.96, 0.70, 0.14),), "green": ((0.67, 0.77, 0.62),)},
            tolerance=0.16,
            row_bands=True,
        )
    )
    preprocess = preprocessors.Compose(
        preprocessors.RowFilter(_weekday),
        preprocessors.Deduplicate(key=lambda r: (r["date"], r["type"])),
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "yellow": [wt.GENERAL_WASTE, wt.RECYCLABLES],
            "green": [wt.GENERAL_WASTE, wt.GARDEN_WASTE],
        },
    )
