import re
from collections.abc import Iterable
from typing import Any, ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import lookups, recurrence, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# Demonstrates: a weekday-list scrape projected into a recurring weekly schedule.
#
# The City of Lawrence publishes its curbside collection schedule as five
# weekday tabs (Monday-Friday). Each tab lists the streets collected that
# weekday. Trash and single-stream recycling are collected together on the
# resident's regular weekday, so each matched weekday emits a weekly trash
# schedule and a weekly recycling schedule.
#
# The streets are in the delivered HTML (a CivicPlus tabbed widget), so a plain
# GET plus a small parse method is enough. A street may be listed on more than
# one weekday when it is split into segments (e.g. "Andover Street (State Street
# to Ballard Road)" on Monday and "Andover Street (State Street to Shawsheen
# Road)" on Tuesday); in that case every matching weekday is scheduled.

# Number of weekly occurrences to project per matched weekday (~6 months).
_WEEKS_AHEAD = 26


def _base_street(name: str) -> str:
    """Strip a trailing qualifier like '(State Street to Ballard Road)'."""
    return lookups.normalize_text(re.split(r"\s*\(", name, maxsplit=1)[0])


def _describe(
    record: tuple[int, list[str]], source: "BaseSource | None"
) -> Iterable[Schedule]:
    weekday, streets = record
    assert source is not None
    wanted = lookups.normalize_text(source.params["street"])
    if not any(_base_street(s) == wanted for s in streets):
        return
    start = recurrence.next_weekday(weekday)
    yield Schedule("trash", start, recurrence.WEEKLY, _WEEKS_AHEAD)
    yield Schedule("recycling", start, recurrence.WEEKLY, _WEEKS_AHEAD)


@final
class Source(BaseSource):
    TITLE = "City of Lawrence"
    DESCRIPTION = "Source for City of Lawrence, Massachusetts, USA."
    URL = "https://www.cityoflawrence.com"
    COUNTRY = "us"

    API_URL = "https://www.cityoflawrence.com/161/Collection-Schedule"

    TEST_CASES: ClassVar[dict] = {
        "Monday street (Adams Street)": {"street": "Adams Street"},
        "Tuesday street (Bailey Street)": {"street": "Bailey Street"},
        "Friday street (Ames Street)": {"street": "Ames Street"},
    }

    PARAMS = (text_field("street", label="Street Name"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the City of Lawrence collection schedule at "
            "https://www.cityoflawrence.com/161/Collection-Schedule and find "
            "your street on the Monday to Friday tabs. Enter the street name "
            "exactly as listed (for example 'Adams Street'). Omit any segment "
            "qualifier shown in brackets."
        ),
    }

    SOURCE_CODEOWNERS: ClassVar[list] = ["@markvp"]

    RAISE_ON_EMPTY = True

    retrieve = retrievers.HttpGetRetriever(url=API_URL)

    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(
        type_value_map={"trash": GENERAL_WASTE, "recycling": RECYCLABLES},
    )

    def __init__(self, street: str):
        super().__init__(street=street)
        self._street = street.strip()

    def parse(
        self, response: Any, source: "BaseSource | None" = None
    ) -> list[tuple[int, list[str]]]:
        """Extract (weekday index, [street names]) for each weekday panel.

        The five panels render in weekday order Monday (0) to Friday (4).
        """
        soup = BeautifulSoup(response.text, "html.parser")
        panels = soup.select("div.cpTabPanel")

        records: list[tuple[int, list[str]]] = []
        for weekday, panel in enumerate(panels):
            streets = [
                text
                for li in panel.select("ul li")
                if (text := li.get_text(" ", strip=True))
            ]
            if streets:
                records.append((weekday, streets))

        if not any(
            _base_street(s) == self._street.casefold()
            for _, streets in records
            for s in streets
        ):
            all_streets = {
                _base_street(s).title() for _, streets in records for s in streets
            }
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, sorted(all_streets)
            )

        return records
