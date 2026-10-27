import re
from collections.abc import Sequence
from typing import ClassVar, final
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup
from waste_collection_schedule import lookups, parsers, preprocessors, response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import (
    FanOutRetriever,
    Lookup,
    Request,
)
from waste_collection_schedule.transformers import JsonTransformer

TITLE = "Nemėžio komunalininkas"
DESCRIPTION = "Waste collection schedules for Vilnius District, Lithuania."
URL = "https://www.nkom.lt/kita.html"
COUNTRY = "lt"

SOURCE_CODEOWNERS = ["@BobrLab"]


def _schedule_kind(href: str) -> str | None:
    path = unquote(urlparse(href).path)
    if not path.lower().endswith(".pdf"):
        return None
    filename = lookups.normalize_loose(path)
    if "grafikas" not in filename:
        return None
    if "pakuociu" in filename:
        return "packaging"
    if "misriu" in filename:
        return "mixed"
    return None


def _schedule_period(href: str) -> tuple[int, int]:
    match = re.search(r"\b(20\d{2})\b.*?\((\d{1,2})-(\d{1,2})\)", unquote(href))
    if match is None:
        return (0, 0)
    return (int(match.group(1)), int(match.group(3)))


def _schedule_links(response, **_params) -> Sequence[str]:
    schedules: dict[str, tuple[tuple[int, int], str]] = {}
    soup = BeautifulSoup(response.text, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = urljoin(URL, str(anchor["href"]))
        kind = _schedule_kind(href)
        if kind is None:
            continue
        period = _schedule_period(href)
        if kind not in schedules or period > schedules[kind][0]:
            schedules[kind] = (period, href)

    missing = {"mixed", "packaging"} - schedules.keys()
    response_shape.expect(
        not missing,
        source_name="nkom_lt",
        detail=(
            f"could not find current schedule PDF(s): {', '.join(sorted(missing))}"
        ),
        raw=response.text,
    )
    return [schedule[1] for _, schedule in sorted(schedules.items())]


def _select_locality(rows, source):
    location = source.params["location"]
    wanted = lookups.normalize_loose(location)
    matching = [
        row for row in rows if wanted and wanted in lookups.normalize_loose(row.label)
    ]
    if not matching:
        raise SourceArgumentNotFound("location", location)

    events = []
    seen = set()
    for row in matching:
        for column, event_date in row.cells:
            if row.column_count == 3:
                waste_type = "mixed"
            elif row.column_count == 6:
                waste_type = "packaging" if column < 3 else "glass"
            else:
                raise response_shape.ResponseShapeError(
                    "nkom_lt",
                    f"unsupported month-column count: {row.column_count}",
                )
            event = (event_date, waste_type)
            if event not in seen:
                seen.add(event)
                events.append({"date": event_date, "type": waste_type})
    return events


_MONTH_GRID = preprocessors.PdfMonthDayGrid(
    year_pattern=r"\b(20\d{2})\b",
    month_locale="lt",
    column_counts=(3, 6),
    column_tolerance=35,
    row_tolerance=3,
)


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY
    SOURCE_CODEOWNERS = SOURCE_CODEOWNERS
    TEST_CASES: ClassVar[dict] = {
        "Nemėžio grafikai": {"location": "Nemėžis"},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Open https://www.nkom.lt/kita.html and use a town, village, or street name as it appears in the 'Vietovė' column of the schedule."
    }
    PARAMS = (city("location"),)
    WASTE_TYPES: ClassVar[list[wt.WasteType]] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
    ]
    RAISE_ON_EMPTY = True

    retrieve = FanOutRetriever(
        prepare=Lookup(URL, pick=_schedule_links),
        targets=lambda _source, urls: urls,
        fetch=Request(url=lambda url, _urls, **_: url),
    )
    parse = parsers.EachResponse(
        parsers.PdfWordLayoutParser(),
        then=_MONTH_GRID,
    )
    preprocess = staticmethod(_select_locality)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "mixed": wt.GENERAL_WASTE,
            "packaging": wt.RECYCLABLES,
            "glass": wt.GLASS,
        },
    )
