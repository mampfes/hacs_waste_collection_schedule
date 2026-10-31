"""Ray Whelan's published blue-week recycling calendars."""

import calendar as calendar_module
import datetime
import re
from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import config_params, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.MarkedPdfCalendar import MarkedPdfCalendarParser
from waste_collection_schedule.transformers import JsonTransformer

_URL = "https://www.raywhelan.ie"
_DAYS = list(calendar_module.day_name)


def _calendar_link(response, *_, calendar, day):
    if calendar not in ("GB", "T"):
        raise SourceArgumentNotFoundWithSuggestions("calendar", calendar, ["GB", "T"])
    if recurrence.weekday(day) is None:
        raise SourceArgumentNotFoundWithSuggestions("day", day, _DAYS)
    links = BeautifulSoup(response.text, "html.parser").select("a[href]")
    matches = {
        urljoin(response.url, link["href"])
        for link in links
        if re.search(rf"\b{calendar}\s+Calendar\b", link.get_text(" "), re.I)
    }
    if len(matches) != 1:
        raise ValueError("The selected recycling calendar link is missing or ambiguous")
    return matches.pop()


def _collection_day(records, source):
    weekday = recurrence.weekday(source.params["day"])
    years = {record["date"].year for record in records}
    if datetime.date.today().year not in years:
        raise ValueError("The published recycling calendar does not cover this year")
    yield from (record for record in records if record["date"].weekday() == weekday)


@final
class Source(BaseSource):
    TITLE = "Ray Whelan"
    DESCRIPTION = "Source for Ray Whelan recycling collection weeks, Ireland."
    URL = _URL
    COUNTRY = "ie"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "GB Monday recycling": {"calendar": "GB", "day": "Monday"},
        "T Thursday recycling": {"calendar": "T", "day": "Thursday"},
    }
    PARAMS = (
        config_params.dropdown("calendar", ["GB", "T"], "Calendar code"),
        config_params.dropdown("day", _DAYS, "Collection day"),
    )
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.raywhelan.ie/ and choose Collection Calendars. "
            "Select the GB or T calendar assigned to your route and enter your "
            "usual collection day. Ask Ray Whelan if you do not know your route. "
            "Only the recycling dates in the blue weeks are supported. The PDFs "
            "do not give dated general-waste or organic collections, or specific "
            "holiday replacements; check provider notices for changes."
        )
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda **_: (
                    f"{_URL}/{datetime.date.today().year}-collection-calendars/"
                ),
                pick=_calendar_link,
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
    )
    parse = MarkedPdfCalendarParser(
        months=list(calendar_module.month_name)[1:],
        weekdays=list("MTWTFSS"),
        year_pattern=r"CALENDAR (20\d{2})",
        colors={"Recycling": [(0.9961, 0.7882, 0.0, 0.0)]},
        row_bands=True,
        heading_year=True,
        # The T PDF contains stray, invisible editing text at 9.149 pt.
        # Its actual calendar numerals are 9.28 or 10 pt.
        day_font_size=(9.2, 10.1),
    )
    preprocess = staticmethod(_collection_day)
    transform = JsonTransformer(
        date_key="date", type_key="type", type_value_map={"Recycling": wt.RECYCLABLES}
    )
