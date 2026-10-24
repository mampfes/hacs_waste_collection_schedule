import datetime
import re
from collections.abc import Iterator
from typing import ClassVar, final

from waste_collection_schedule import config_params, lookups, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import PdfRow, PdfTableParser
from waste_collection_schedule.retrievers import PdfLinkRetriever
from waste_collection_schedule.transformers import ICSTransformer

GENERAL = "Vegyes hulladék"
SELECTIVE = "Szelektív hulladék"
GREEN = "Zöldhulladék"
TREE = "Fenyőfa gyűjtés"

# DTKH's download page for Kiskunfélegyháza links the yearly calendar as
# /dl/content/<id>/6100_Kiskunfélegyháza_Hulladéknaptár<year>.pdf; the id
# changes every year. (The city's own page links a broken /dl/<id>/ path.)
_INDEX_URL = "https://dtkh.hu/letoltheto-dokumentumok-kiskunfelegyhaza"
_PDF_PATTERN = r"/dl/content/\d+/[^/]*Hullad[eé]knapt[aá]r\s*(20\d{2})\.pdf$"

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Row labels of the weekday x month table on page 1.
_ROW_TYPES = {"szelektiv": SELECTIVE, "zoldhulladek": GREEN}

# Street-type words a street-list entry ends with (before any house numbers).
# A printed line ending in one of them ends an entry even without a comma.
_STREET_SUFFIXES = (
    "utca",
    "ut",
    "utja",
    "ter",
    "koz",
    "park",
    "setany",
    "sor",
    "lakopark",
    "lakotelep",
    "telep",
)


def _text(row: PdfRow) -> str:
    return " ".join(w.text for w in row.words)


def _year(rows: list[PdfRow]) -> int:
    for row in rows:
        # "2026. évi hulladéknaptár", "2025/2. félév hulladéknaptár"
        match = re.search(r"(20\d{2})\b.*hulladéknaptár", _text(row), re.I)
        if match:
            return int(match.group(1))
    return datetime.date.today().year


def _month_header(rows: list[PdfRow]) -> list[tuple[float, int]]:
    """[(column centre, month number), ...] from the table's month header row."""
    for row in rows:
        named = [
            ((w.x0 + w.x1) / 2, number)
            for w in row.words
            if (number := recurrence.month(w.text)) is not None
        ]
        if row.page == 0 and len(named) >= 6:
            return named
    return []


def _table(rows: list[PdfRow]) -> dict[tuple[str, int], list[datetime.date]]:
    """Read page 1: {(label, weekday): dates} from the weekday x month table.

    The month header row gives each month's column centre; every row labelled
    "Szelektív" or "Zöldhulladék" belongs to the weekday name printed nearest
    to it vertically (the name sits between its two rows), and each of its
    day lists ("2, 16, 30") to the month whose header it sits under.
    """
    year = _year(rows)
    months = _month_header(rows)
    weekdays: list[tuple[float, int]] = []
    typed: list[tuple[PdfRow, str]] = []
    for row in rows:
        if row.page != 0:
            continue
        first = lookups.normalize_loose(row.words[0].text)
        if len(row.words) == 1 and (day := recurrence.weekday(first)) is not None:
            weekdays.append((row.y, day))
        elif first in _ROW_TYPES:
            typed.append((row, _ROW_TYPES[first]))

    table: dict[tuple[str, int], list[datetime.date]] = {}
    if not months or not weekdays:
        return table
    for row, label in typed:
        weekday = min(weekdays, key=lambda yd: abs(yd[0] - row.y))[1]
        dates = table.setdefault((label, weekday), [])
        for word in row.words[1:]:
            centre = (word.x0 + word.x1) / 2
            month = min(months, key=lambda cm: abs(cm[0] - centre))[1]
            for day in re.findall(r"\d{1,2}", word.text):
                try:
                    date = datetime.date(year, month, int(day))
                except ValueError:
                    continue
                dates.append(date)
    return table


def _general_weekdays(rows: list[PdfRow]) -> set[int]:
    """Weekdays named on the "Vegyes hulladékgyűjtési nap:" line."""
    for row in rows:
        for word in row.words:
            match = re.match(r"Vegyes hulladékgyűjtési nap:(.*)", word.text, re.I)
            if match:
                return {
                    day
                    for name in re.split(r"[,\s]+", match.group(1))
                    if (day := recurrence.weekday(name)) is not None
                }
    return set()


def _tree_weeks(rows: list[PdfRow]) -> list[tuple[datetime.date, datetime.date]]:
    """Christmas-tree weeks: "Fenyőfa gyűjtés: 2026. január 12 - 16. és ..."."""
    for row in rows:
        text = _text(row)
        if not lookups.normalize_loose(text).startswith("fenyofa gyujtes"):
            continue
        weeks = []
        for year, month, start, end in re.findall(
            r"(20\d{2})\.\s*(\w+)\s+(\d{1,2})\s*-\s*(\d{1,2})", text
        ):
            number = recurrence.month(month)
            if number is None:
                continue
            try:
                weeks.append(
                    (
                        datetime.date(int(year), number, int(start)),
                        datetime.date(int(year), number, int(end)),
                    )
                )
            except ValueError:
                continue
        return weeks
    return []


def _street_entries(rows: list[PdfRow]) -> list[tuple[str, int]]:
    """Read the green-waste street list: [(entry, weekday), ...].

    Page 2 prints "Szerda: Ady Endre utca, Álmos utca, ..." as running text
    wrapped over several lines, one paragraph per green-waste weekday. A
    street split by house numbers is one entry ("Dr. Holló Lajos utca 1-41,
    2-42"). Some wrapped lines end an entry without a comma, which a trailing
    street-type word ("utca", "tér", ...) or house number gives away.
    """
    text = ""
    for row in rows:
        if row.page == 0:
            continue
        line = _text(row).strip()
        if not text:
            text = line
            continue
        last = lookups.normalize_loose(text).rsplit(" ", 1)[-1]
        ends_entry = last in _STREET_SUFFIXES or last[-1:].isdigit()
        separator = ", " if ends_entry and not text.endswith(",") else " "
        text = f"{text}{separator}{line}"

    entries: list[tuple[str, int]] = []
    sections = re.split(r"(?:^|,?\s)(Hétfő|Kedd|Szerda|Csütörtök|Péntek)\s*:", text)
    for name, body in zip(sections[1::2], sections[2::2], strict=True):
        weekday = recurrence.weekday(name)
        if weekday is None:
            continue
        for part in body.split(","):
            part = re.sub(r"\s+", " ", part).strip(" .")
            if not lookups.normalize_loose(part):
                continue
            if part[0].isdigit() and entries and entries[-1][1] == weekday:
                entries[-1] = (f"{entries[-1][0]}, {part}", weekday)
            else:
                entries.append((part, weekday))
    return entries


def _street_name(entry: str) -> str:
    """The entry without house numbers: "Nádasdy utca 1-5, 2-10" -> "nadasdy utca"."""
    return re.sub(r"(\s\d.*)$", "", lookups.normalize_loose(entry))


def _green_weekday(entries: list[tuple[str, int]], street: str) -> int:
    wanted = lookups.normalize_loose(street)
    for match in (
        lambda entry: lookups.normalize_loose(entry) == wanted,
        lambda entry: _street_name(entry) == wanted,
        lambda entry: _street_name(entry).rsplit(" ", 1)[0] == wanted,
    ):
        found = [(entry, day) for entry, day in entries if match(entry)]
        if len({day for _, day in found}) == 1:
            return found[0][1]
        if found:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street, sorted({entry for entry, _ in found})
            )
    raise SourceArgumentNotFoundWithSuggestions(
        "street", street, sorted({entry for entry, _ in entries})
    )


def _rows(
    rows: list[PdfRow], source: BaseSource | None = None
) -> Iterator[tuple[datetime.date, str]]:
    params = source.params if source else {}
    weekday = recurrence.weekday(params.get("weekday") or "")
    if weekday is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "weekday", params.get("weekday"), _WEEKDAYS
        )
    year = _year(rows)
    table = _table(rows)

    yield from ((date, SELECTIVE) for date in table.get((SELECTIVE, weekday), []))

    # General waste is collected weekly on the collection day, over the months
    # the sheet covers (a whole year, or a half-year sheet's six months).
    months = [number for _, number in _month_header(rows)]
    if months and weekday in _general_weekdays(rows):
        first = datetime.date(year, min(months), 1)
        until = datetime.date(year + max(months) // 12, max(months) % 12 + 1, 1)
        first += datetime.timedelta(days=(weekday - first.weekday()) % 7)
        for date in recurrence.recurring_within(
            first,
            recurrence.WEEKLY,
            not_before=first,
            until=until - datetime.timedelta(days=1),
        ):
            yield date, GENERAL

    # A sheet with a green-waste street list (2026) collects green waste
    # Wednesday to Friday by street; one without (2025/2) on every weekday,
    # on the resident's own collection day.
    entries = _street_entries(rows)
    street = params.get("street")
    if entries and not street:
        return
    green = _green_weekday(entries, street) if entries else weekday
    yield from ((date, GREEN) for date in table.get((GREEN, green), []))
    for start, end in _tree_weeks(rows):
        date = start + datetime.timedelta(days=(green - start.weekday()) % 7)
        if date <= end:
            yield date, TREE


@final
class Source(BaseSource):
    TITLE = "DTKH Nonprofit Kft. (Kiskunfélegyháza)"
    DESCRIPTION = "Source for the Kiskunfélegyháza waste collection calendar of DTKH."
    URL = "https://dtkh.hu"
    COUNTRY = "hu"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Monday": {"weekday": "Monday"},
        "Thursday, Petofi Sandor utca": {
            "weekday": "Thursday",
            "street": "Petőfi Sándor utca",
        },
        "Friday, Dr Hollo Lajos utca 44-100": {
            "weekday": "Friday",
            "street": "Dr Holló Lajos utca 44-100, 43-91",
        },
    }

    PARAMS = (
        config_params.dropdown("weekday", _WEEKDAYS, label="Collection day"),
        config_params.street(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick the weekday your general waste (vegyes hulladék) is collected; "
            "recyclables (szelektív) are collected every other week on the same "
            "day (Hétfő = Monday, Kedd = Tuesday, Szerda = Wednesday, Csütörtök "
            "= Thursday, Péntek = Friday). Green waste (zöldhulladék) is "
            "collected Wednesday to Friday by street: enter your street as "
            "printed in the street list (Zöld utcajegyzék) on the back of the "
            "yearly calendar at "
            "https://dtkh.hu/letoltheto-dokumentumok-kiskunfelegyhaza, e.g. "
            '"Petőfi Sándor utca". Where a street is split by house numbers, '
            'use the full entry, e.g. "Nádasdy utca 1-5, 2-10"; an ambiguous '
            "street lists the possible entries. Leave the street empty to skip "
            "green waste."
        ),
    }

    retrieve = PdfLinkRetriever(index_url=_INDEX_URL, pattern=_PDF_PATTERN)
    parse = PdfTableParser(min_words=50)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            GENERAL: wt.GENERAL_WASTE,
            SELECTIVE: wt.RECYCLABLES,
            GREEN: wt.GARDEN_WASTE,
            TREE: wt.GARDEN_WASTE,
        }
    )
