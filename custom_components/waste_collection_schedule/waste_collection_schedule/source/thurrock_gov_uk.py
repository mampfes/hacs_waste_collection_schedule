import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import Compose, SplitLabels
from waste_collection_schedule.transformers import ICSTransformer

# Streets beginning with A use the base URL (no letter suffix).
# All other letters append "-<letter>" to the base URL.
STREETS_BASE_URL = (
    "https://www.thurrock.gov.uk/household-bin-collection-days/street-names"
)
BINDAYS_URL = "https://www.thurrock.gov.uk/bindays"

# ASCII hyphen-minus, en-dash or em-dash between the two ends of a week.
_DATE_RANGE = re.compile(r"^(?P<start>\d+ [A-Za-z]+)\s*[-–—]\s*(?P<end>\d+ [A-Za-z]+)$")


def _streets_url(street: str, **_) -> str:
    first = street.strip()[:1].lower()
    return STREETS_BASE_URL if first in ("", "a") else f"{STREETS_BASE_URL}-{first}"


def _cells(row) -> list[str]:
    return [cell.get_text().replace("\xa0", " ").strip() for cell in row.find_all("td")]


def _week(text: str, today: datetime.date) -> tuple[datetime.date, datetime.date]:
    """A week such as "28 September - 2 October" (the page gives no year)."""
    match = _DATE_RANGE.match(text)
    if match is None:
        raise ValueError(f"Cannot parse date range: {text!r}")
    start = datetime.datetime.strptime(f"{match['start']} {today.year}", "%d %B %Y")
    end = datetime.datetime.strptime(f"{match['end']} {today.year}", "%d %B %Y")
    # A week straddling New Year (30 December - 3 January).
    if start.month == 12 and end.month == 1:
        end = end.replace(year=start.year + 1)
    return start.date(), end.date()


def _days(records, source):
    """One (date, bin colours) row per collection of this street's round.

    ``records`` are the rows of the street list (street and town, collection
    weekday, round) followed by the rows of the borough-wide week table (week,
    bins of round A, bins of round B).
    """
    wanted_street = str(source.params["street"]).casefold()
    wanted_town = str(source.params["town"]).casefold()
    streets: list[str] = []
    towns: list[str] = []
    household: tuple[int, int] | None = None
    weeks: list[list[str]] = []
    for row in records:
        cells = _cells(row)
        if len(cells) != 3:
            continue
        if _DATE_RANGE.match(cells[0]):
            weeks.append(cells)
            continue
        # The street may itself contain ", " (a parenthetical note).
        parts = cells[0].rsplit(", ", 1)
        weekday = recurrence.weekday(cells[1])
        if len(parts) != 2 or weekday is None or cells[2] not in ("A", "B"):
            continue
        name, town = (part.strip().casefold() for part in parts)
        streets.append(parts[0].strip())
        towns.append(parts[1].strip())
        if household is None and wanted_street in name and wanted_town in town:
            household = (weekday, 1 if cells[2] == "A" else 2)

    if household is None:
        if any(wanted_town in town.casefold() for town in towns):
            raise SourceArgumentNotFoundWithSuggestions(
                "street", source.params["street"], streets
            )
        raise SourceArgumentNotFoundWithSuggestions(
            "town", source.params["town"], sorted(set(towns))
        )

    weekday, column = household
    today = datetime.date.today()
    for cells in weeks:
        start, end = _week(cells[0], today)
        day = recurrence.next_weekday(weekday, on_or_after=start)
        if day <= end:
            yield day, cells[column]


@final
class Source(BaseSource):
    TITLE = "Thurrock"
    DESCRIPTION = "Source for Thurrock."
    URL = "https://www.thurrock.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Camden Close Chadwell St Mary": {
            "street": "Camden Close",
            "town": "Chadwell St Mary",
        },
        "Abberton Way West Thurrock (street starting with A)": {
            "street": "Abberton Way",
            "town": "West Thurrock",
        },
    }

    PARAMS = (street(), city("town"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name and town exactly as listed on "
            "https://www.thurrock.gov.uk/household-bin-collection-days "
            "(e.g. street 'Camden Close', town 'Chadwell St Mary')."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        targets=lambda source, context: [
            _streets_url(**source.params),
            BINDAYS_URL,
        ],
        fetch=retrievers.Request(lambda url, context, **_: url),
    )
    parse = parsers.EachResponse(parsers.HtmlParser("table tr"))
    preprocess = Compose(
        _days,
        SplitLabels(r"\s*/\s*|\s+and\s+"),
    )
    transform = ICSTransformer(
        type_value_map={
            "Grey": wt.GENERAL_WASTE,
            "Green": wt.RECYCLABLES,
            "Blue": wt.PAPER,
            "Brown": wt.GARDEN_WASTE,
        },
    )
