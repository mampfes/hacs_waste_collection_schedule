import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.recurrence import month as month_number
from waste_collection_schedule.transformers import RowTransformer

VALID_CALENDARS = ["a", "b"]

# The weekday columns of every month table, after the "Bin" column.
VALID_DAYS = ["tuesday", "wednesday", "thursday", "friday"]


def _calendar_url(calendar: str, **_) -> str:
    calendar = str(calendar).strip().lower()
    if calendar not in VALID_CALENDARS:
        raise SourceArgumentNotFoundWithSuggestions(
            "calendar", calendar, suggestions=VALID_CALENDARS
        )
    return f"https://www.bolsover.gov.uk/waste-bins-recycling/bin-calendar-{calendar}"


def _rows(tables, source) -> list[tuple[datetime.date, str]]:
    """One ``(date, bin)`` row per bin of the configured weekday, per month table.

    Each month is a table ("Bin", "Tuesday" .. "Friday") under an ``h2`` naming
    the month and year; a cell is the day of the month. A round of several bins
    reads "Green / Burgundy". Tables that are not month calendars are skipped.
    """
    day = str(source.params["collection_day"]).strip().lower()
    if day not in VALID_DAYS:
        raise SourceArgumentNotFoundWithSuggestions(
            "collection_day", day, suggestions=VALID_DAYS
        )
    column = VALID_DAYS.index(day) + 1

    rows: list[tuple[datetime.date, str]] = []
    for table in tables:
        trs = table.find_all("tr")
        header = [c.get_text(strip=True).lower() for c in trs[0].find_all(["th", "td"])]
        if not header or header[0] != "bin":
            continue
        heading = table.find_previous("h2")
        match = heading and re.match(r"(\w+)\s+(\d{4})", heading.get_text(strip=True))
        month = match and month_number(match.group(1))
        if not match or not month:
            continue
        year = int(match.group(2))

        for tr in trs[1:]:
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) <= column:
                continue
            # A cell may carry an annotation such as "(No collection)".
            text = re.sub(r"\(.*?\)", "", cells[column]).strip()
            if not text.isdigit():
                continue
            try:
                collected = datetime.date(year, month, int(text))
            except ValueError:
                continue
            for label in cells[0].split("/"):
                if label.strip():
                    rows.append((collected, label.strip()))
    return rows


@final
class Source(BaseSource):
    TITLE = "Bolsover District Council"
    DESCRIPTION = "Source for Bolsover District Council, UK."
    URL = "https://www.bolsover.gov.uk"
    COUNTRY = "uk"

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Calendar A, Wednesday": {"calendar": "a", "collection_day": "wednesday"},
        "Calendar B, Thursday": {"calendar": "b", "collection_day": "thursday"},
    }

    PARAMS = (
        dropdown("calendar", VALID_CALENDARS, label="Calendar"),
        dropdown("collection_day", VALID_DAYS, label="Collection Day"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Check your bin calendar letter (A or B) and collection day "
            "(Tuesday to Friday) on the Bolsover website at "
            "https://www.bolsover.gov.uk/services/b/bins-and-recycling/."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(url=_calendar_url)
    parse = parsers.HtmlParser("table")
    preprocess = staticmethod(_rows)
    transform = RowTransformer(
        type_value_map={
            "Black": wt.GENERAL_WASTE,
            "Burgundy": wt.RECYCLABLES,
            "Green": wt.GARDEN_WASTE,
        },
    )
