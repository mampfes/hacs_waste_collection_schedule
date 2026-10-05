from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The recurring weekly schedule has no end date; project 53 weeks (a year) ahead.
_WEEKS = 53

# The rubbish panel's table has no per-row type column.
_RUBBISH_TYPE = "Residential rubbish and commercial waste"


def _weekday(abbreviation: str) -> int | None:
    """Weekday index of an English three-letter abbreviation ("Tue"), or None."""
    found = {
        index
        for name, index in recurrence.WEEKDAYS.items()
        if name.startswith(abbreviation[:3].lower())
    }
    return found.pop() if len(found) == 1 else None


def _days(text: str) -> set[int]:
    """Expand a day cell ("Tue, Fri", "Mon - Fri") into weekday() indices."""
    result: set[int] = set()
    for token in text.replace("\xa0", " ").split(","):
        token = token.strip().lower()
        if not token:
            continue
        if "-" in token:
            first, _, last = token.partition("-")
            start = _weekday(first.strip())
            end = _weekday(last.strip())
            if start is None or end is None:
                continue
            if start <= end:
                result.update(range(start, end + 1))
            else:  # wrap-around range, e.g. Sat-Mon
                result.update(range(start, 7))
                result.update(range(end + 1))
        elif (day := _weekday(token)) is not None:
            result.add(day)
    return result


def _describe(table, source):
    """One weekly series per (service, weekday) of a rubbish or recycling table."""
    rows = table.find_all("tr")
    if not rows:
        return
    columns = {
        cell.get_text(strip=True).lower(): i
        for i, cell in enumerate(rows[0].find_all(["th", "td"]))
    }
    is_rubbish = table.find_parent("div", id="pnlrubbishcollection") is not None
    service = columns.get("service description")
    series: set[tuple[str, int]] = set()
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        # A row whose cell count differs from the header cannot be aligned
        # positionally with the columns: skip it rather than read a wrong one.
        if len(cells) != len(columns):
            continue
        if is_rubbish:
            label = _RUBBISH_TYPE
        elif service is not None:
            label = cells[service].get_text(strip=True)
        else:
            continue
        if not label:
            continue
        days: set[int] = set()
        for name in ("week days", "weekend days"):
            if (index := columns.get(name)) is not None:
                days |= _days(cells[index].get_text())
        series.update((label, day) for day in days)
    for label, day in sorted(series):
        yield Schedule(label, recurrence.next_weekday(day), recurrence.WEEKLY, _WEEKS)


@final
class Source(BaseSource):
    TITLE = "Westminster City Council"
    DESCRIPTION = "Source for Westminster City Council (London, UK) bin collections."
    URL = "https://www.westminster.gov.uk"
    COUNTRY = "uk"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@parmymansam"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Shirland Mews (short street)": {"usrn": "8400172"},
        "Shirland Road (long street)": {"usrn": 8400243},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "You need the USRN (Unique Street Reference Number) for your street. Find it "
            "by searching your street on https://www.findmyaddress.co.uk or by inspecting "
            "the USRN value in the URL of Westminster's own street-report search at "
            "https://transact.westminster.gov.uk/env/streetreport.aspx"
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.RECYCLABLES,
    ]

    PARAMS = (text_field("usrn", "USRN", coerce=str),)

    retrieve = HttpGetRetriever(
        url="https://transact.westminster.gov.uk/env/streetreport.aspx",
        params=lambda usrn, **_: {"Street": "NA", "USRN": usrn},
    )
    parse = parsers.HtmlParser(
        "#pnlrubbishcollection table, #pnlrecyclingcollections table"
    )
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            _RUBBISH_TYPE: wt.GENERAL_WASTE,
            "Food Recycling Collection": wt.FOOD_WASTE,
            "Recycling Collection": wt.RECYCLABLES,
        },
        carry_raw_label=True,
    )
