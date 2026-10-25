"""DTKH Nonprofit Kft.: yearly waste calendars of the settlements it serves.

DTKH serves about 230 settlements between the Danube and the Tisza. Each one
publishes a yearly calendar PDF on the same template: a table with one column
per month and one row per waste round ("Szelektív", "Zöldhulladék",
"fenyőgyűjtés", in some towns "Műanyag" and "papír"), the cells listing that
month's collection days. Larger towns repeat the rows once per collection
weekday ("Hétfő", "Kedd", ...), some villages once per area ("Lakitelek -
üdülő"). The general waste (vegyes hulladék) day is printed below the table.

The settlement's download box on https://dtkh.hu/telepules only shows once the
settlement has been chosen in the site's session (a POST to /city), so the
retriever looks the settlement id up in the page's drop-down, chooses it, and
downloads the box's newest "Hulladéknaptár <year>". The shared
``preprocessors.PdfRoundMonthGrid`` reads the table into one block per weekday
or area; this module only picks the block and adds the weekly general waste.
"""

import datetime
import re
from collections import Counter
from collections.abc import Iterator
from typing import Any, ClassVar, final

from bs4 import Tag
from waste_collection_schedule import (
    config_params,
    lookups,
    recurrence,
    response_shape,
    retrievers,
)
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import (
    PdfTextFragment,
    PdfWordLayout,
    PdfWordLayoutParser,
)
from waste_collection_schedule.preprocessors import GridBlock, PdfRoundMonthGrid
from waste_collection_schedule.transformers import ICSTransformer

GENERAL = "Vegyes hulladék"
SELECTIVE = "Szelektív hulladék"
PAPER = "Papír"
GREEN = "Zöldhulladék"
TREE = "Fenyőfa gyűjtés"

_SETTLEMENTS_URL = "https://dtkh.hu/telepules"
_CHOOSE_URL = "https://dtkh.hu/city"
_CALENDAR = "Hulladéknaptár"

# Row labels of the month table, by the first words of the label's line
# ("Zöldhulladék lágy", "Szelektív - Dél" and "Műanyag" in the towns that
# collect plastic and paper apart).
_ROW_TYPES = {
    "szelektiv": SELECTIVE,
    "muanyag": SELECTIVE,
    "papir": PAPER,
    "zoldhulladek": GREEN,
    "zold": GREEN,
    "fenyogyujtes": TREE,
    "fenyofa": TREE,
}

# Text left of the table that names no block: the header cell, the general
# waste line and the notes printed beside it.
_NOT_A_NAME = re.compile(
    r"^(?:hulladek|tipusa|telepules|vegyes|szolgaltato|kerjuk|kihelyezni"
    r"|forgalmat|ne akadalyozza|mely|20\d\d)"
)

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
    "zug",
    "dulo",
    "lakopark",
    "lakotelep",
    "telep",
)


def _row_type(text: str) -> str | None:
    """The round a table line labels, read off its first words."""
    words = lookups.normalize_loose(text.split(":")[0]).split()
    for word in words[:2]:
        if word in _ROW_TYPES:
            return _ROW_TYPES[word]
        if word.isdigit():
            break
    return None


_GRID = PdfRoundMonthGrid(
    labels=_row_type,
    block_start=SELECTIVE,
    year_pattern=r"(?i)(20\d\d)\b[^\n]*hullad[eé]knapt[aá]r",
    side_margin=40,
)


def _city_id(response: Any, **params: Any) -> str:
    """The settlement's id in the page's settlement drop-down."""
    url = lookups.link_pick(
        "city",
        href=r"^\d+$",
        selector="#city_filter option",
        attribute="value",
    )(response, **params)
    return url.rsplit("/", 1)[-1]


def _document_kind(tag: Tag) -> str:
    """A download's title without its year: "Hulladéknaptár 2026" -> "Hulladéknaptár"."""
    title = str(tag.get("title") or tag.get_text(" ", strip=True))
    if re.match(r"Hullad[eé]knapt[aá]r\s+20\d\d", title, re.I):
        return _CALENDAR
    return title


_PICK_CALENDAR = lookups.link_pick(
    "document",
    href=r"/dl/",
    selector=".box-cityinfo a.dl-link",
    label=_document_kind,
    newest=True,
)


def _calendar_url(response: Any, *_keys: Any, **_params: Any) -> str:
    """The newest yearly calendar in the chosen settlement's download box."""
    return _PICK_CALENDAR(response, document=_CALENDAR)


def _block_name(block: GridBlock) -> str:
    """What the table prints left of a block: its weekday or area."""
    parts = []
    for line in block.side_text.splitlines():
        if _row_type(line):
            continue
        text = line.strip(" :")
        if not text or _NOT_A_NAME.match(lookups.normalize_loose(text)):
            continue
        parts.append(text)
    name = " ".join(parts)
    first, _, rest = name.partition(" ")
    if recurrence.weekday(first) is not None:
        # "Hétfő", or "Hétfő I." where a weekday has two rounds; drop notes
        # printed beside it ("Csütörtök ne akadályozza!").
        suffix = re.match(r"[IV]+\.?(?=\s|$)", rest)
        return f"{first} {suffix.group(0)}".strip(" .:") if suffix else first
    return name


def _select(blocks: list[GridBlock], params: dict) -> GridBlock:
    named = [(_block_name(block), block) for block in blocks]
    if len(named) == 1:
        return named[0][1]
    wanted = params.get("district") or params.get("city")
    norm = lookups.normalize_loose(wanted or "")
    day = recurrence.weekday(str(wanted or ""))
    for match in (
        lambda name: lookups.normalize_loose(name) == norm,
        lambda name: day is not None and recurrence.weekday(name) == day,
        lambda name: lookups.normalize_loose(name).startswith(norm),
    ):
        found = [block for name, block in named if norm and match(name)]
        if len(found) == 1:
            return found[0]
    raise SourceArgumentNotFoundWithSuggestions(
        "district", params.get("district"), [name for name, _ in named if name]
    )


def _text_lines(layout: PdfWordLayout, page: int) -> list[str]:
    """The page's printed lines, top to bottom (fragments at one height joined)."""
    lines: list[list[PdfTextFragment]] = []
    for line in sorted(
        (line for line in layout.lines if line.page == page),
        key=lambda line: (-line.y, line.x),
    ):
        if lines and abs(lines[-1][0].y - line.y) < 2:
            lines[-1].append(line)
        else:
            lines.append([line])
    return [
        " ".join(part.text for part in sorted(row, key=lambda p: p.x)) for row in lines
    ]


def _general_weekdays(layout: PdfWordLayout) -> set[int]:
    """Weekdays printed with "Vegyes hulladékgyűjtési nap:".

    The days may share the label's line or follow on the next ones
    ("hétfő, kedd, szerda," / "csütörtök, péntek"); a line that also names an
    area ("Belterület SZERDA") makes the day depend on the address, so none
    is taken.
    """
    for page in sorted({line.page for line in layout.lines}):
        lines = [line for line in layout.lines if line.page == page]
        for label in lines:
            if not lookups.normalize_loose(label.text).startswith(
                "vegyes hulladekgyujtesi nap"
            ):
                continue
            days: set[int] = set()
            for line in lines:
                text = label.text.split(":", 1)[-1] if line is label else line.text
                if not -16 < line.y - label.y < 4 or (
                    line is not label and line.x < label.x - 40
                ):
                    continue
                names = [name for name in re.split(r"[,\s]+", text) if name]
                found = [recurrence.weekday(name) for name in names]
                if names and all(day is not None for day in found):
                    days.update(day for day in found if day is not None)
                elif line is not label and any(day is not None for day in found):
                    return set()
            return days
    return set()


def _tree_weeks(layout: PdfWordLayout) -> list[tuple[datetime.date, datetime.date]]:
    """Christmas-tree weeks: "Fenyőfa gyűjtés: 2026. január 12 - 16. és ..."."""
    for line in layout.lines:
        if not lookups.normalize_loose(line.text).startswith("fenyofa gyujtes"):
            continue
        weeks = []
        for year, month, start, end in re.findall(
            r"(20\d{2})\.\s*(\w+)\s+(\d{1,2})\s*-\s*(\d{1,2})", line.text
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


def _street_entries(layout: PdfWordLayout) -> list[tuple[str, int]]:
    """Read the green-waste street list: [(entry, weekday), ...].

    Some towns print a "Zöld utcajegyzék" on the back: "Szerda: Ady Endre
    utca, Álmos utca, ..." as running text wrapped over several lines, one
    paragraph per green-waste weekday. A street split by house numbers is one
    entry ("Dr. Holló Lajos utca 1-41, 2-42"). Some wrapped lines end an entry
    without a comma, which a trailing street-type word ("utca", "tér", ...) or
    house number gives away. The list ends at the next street list heading.
    """
    text = ""
    reading = False
    for page in sorted({line.page for line in layout.lines}):
        for line in _text_lines(layout, page):
            folded = lookups.normalize_loose(line)
            if folded.endswith("utcajegyzek"):
                reading = folded == "zold utcajegyzek"
                continue
            if not reading or re.search(r"napjatol", folded):
                continue
            if not text:
                text = line.strip()
                continue
            last = lookups.normalize_loose(text).rsplit(" ", 1)[-1]
            ends_entry = last in _STREET_SUFFIXES or last[-1:].isdigit()
            separator = ", " if ends_entry and not text.endswith(",") else " "
            text = f"{text}{separator}{line.strip()}"

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


def _weekly(year: int, weekday: int) -> list[datetime.date]:
    first = datetime.date(year, 1, 1)
    first += datetime.timedelta(days=(weekday - first.weekday()) % 7)
    return recurrence.recurring_within(
        first,
        recurrence.WEEKLY,
        not_before=first,
        until=datetime.date(year, 12, 31),
    )


def _rows(
    layouts: list[PdfWordLayout], source: BaseSource | None = None
) -> Iterator[tuple[datetime.date, str]]:
    params = source.params if source else {}
    blocks = _GRID(layouts, source)
    block = _select(blocks, params)
    layout = layouts[0]
    # One round of one block runs on one weekday. Rows of several weekdays
    # read into one block (Mindszent prints its weekdays inside the table)
    # would give the household another weekday's dates.
    for label in (SELECTIVE, PAPER, GREEN):
        days = Counter(date.weekday() for date, row in block.rows if row == label)
        response_shape.expect(
            len(days) < 2 or days.most_common(2)[1][1] < 0.2 * days.total(),
            source_name=response_shape.source_name(source),
            detail=f"{label} rows of several weekdays in one table block",
        )
    # The general waste day: the block's weekday, or in a town with one table
    # but several collection days, the weekday given as district.
    weekday = recurrence.weekday(_block_name(block).split(" ")[0])
    if weekday is None:
        weekday = recurrence.weekday(str(params.get("district") or ""))

    yield from (
        (date, label) for date, label in block.rows if label not in (GREEN, TREE)
    )

    general = _general_weekdays(layout)
    if weekday is not None:
        general &= {weekday}
    if len(general) == 1:
        yield from ((date, GENERAL) for date in _weekly(block.year, general.pop()))

    # Where a street list assigns green waste to a weekday by street, the
    # green rows come from that weekday's block, not the general waste day's.
    entries = _street_entries(layout)
    green_block = block
    if entries:
        street = params.get("street")
        if not street:
            return
        green = _green_weekday(entries, street)
        green_block = next(
            (
                other
                for other in blocks
                if recurrence.weekday(_block_name(other).split(" ")[0]) == green
            ),
            block,
        )
    greens = [date for date, label in green_block.rows if label == GREEN]
    yield from ((date, GREEN) for date in greens)
    # A tree collection on a green-waste day is one collection (Nyárlőrinc).
    trees = [date for date, label in block.rows if label == TREE]
    yield from ((date, TREE) for date in trees if date not in greens)

    # Towns without a "fenyőgyűjtés" row print the Christmas-tree weeks as
    # text; the trees go out on the green-waste day of those weeks.
    green_day = recurrence.weekday(_block_name(green_block).split(" ")[0])
    if green_day is None or trees:
        return
    for start, end in _tree_weeks(layout):
        date = start + datetime.timedelta(days=(green_day - start.weekday()) % 7)
        # A tree week's day is often a green-waste day already (Baja).
        if date <= end and date not in greens:
            yield date, TREE


@final
class Source(BaseSource):
    TITLE = "DTKH Nonprofit Kft."
    DESCRIPTION = (
        "Source for the waste collection calendars of the settlements served by DTKH."
    )
    URL = "https://dtkh.hu"
    COUNTRY = "hu"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Agasegyhaza": {"city": "Ágasegyháza"},
        "Lakitelek udulo": {"city": "Lakitelek", "district": "Lakitelek - üdülő"},
        "Dunaharaszti, Kedd": {"city": "Dunaharaszti", "district": "Kedd"},
        "Kiskunfelegyhaza, Thursday, Petofi Sandor utca": {
            "city": "Kiskunfélegyháza",
            "district": "Thursday",
            "street": "Petőfi Sándor utca",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown settlement": {"city": "Budapest"},
        "Unknown district": {"city": "Baja", "district": "Szombat"},
    }

    PARAMS = (
        config_params.city(),
        config_params.district(optional=True),
        config_params.street(optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your settlement as listed at https://dtkh.hu/telepules, e.g. "
            '"Kiskunfélegyháza". Where the yearly calendar (Hulladéknaptár) '
            "prints one table per collection weekday or per area, also enter "
            "yours as district: the weekday your general waste (vegyes "
            "hulladék) is collected (Hétfő = Monday, Kedd = Tuesday, Szerda = "
            "Wednesday, Csütörtök = Thursday, Péntek = Friday; either name "
            'works), or the area as printed, e.g. "Lakitelek - üdülő"; a '
            "wrong or missing district lists the possible ones. Towns that "
            "print a green-waste street list (Zöld utcajegyzék, e.g. "
            "Kiskunfélegyháza) collect green waste by street: enter your street "
            'as printed there, e.g. "Petőfi Sándor utca", or the full entry '
            'where a street is split by house numbers ("Nádasdy utca 1-5, '
            '2-10"); leave it empty to skip green waste. Not supported: '
            "calendars without the month table (Kecskemét, Szeged, Kalocsa, "
            "Mindszent) or with a misprinted one (Kiskunhalas, Sándorfalva, "
            "Újszentiván), and Úri, whose calendar is not a PDF."
        ),
    }

    retrieve = retrievers.Request(
        lambda city_id, pdf_url, **_: pdf_url,
        before=(
            retrievers.Lookup(_SETTLEMENTS_URL, pick=_city_id),
            retrievers.Lookup(
                _CHOOSE_URL,
                method="POST",
                data=lambda city_id, **_: {
                    "id_city": city_id,
                    "referer": _SETTLEMENTS_URL,
                },
                pick=_calendar_url,
            ),
        ),
    )
    parse = PdfWordLayoutParser(min_words=100)
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(
        type_value_map={
            GENERAL: wt.GENERAL_WASTE,
            SELECTIVE: wt.RECYCLABLES,
            PAPER: wt.PAPER,
            GREEN: wt.GARDEN_WASTE,
            TREE: wt.GARDEN_WASTE,
        }
    )
