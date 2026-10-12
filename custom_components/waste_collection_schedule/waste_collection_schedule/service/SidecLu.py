"""The SIDEC (Luxembourg) collection calendar.

``/fr/Collectes/Calendrier`` renders one year as twelve month tables for the
commune in the ``myCommune`` query parameter. A collection is a small image in
the day's cell whose file name carries both the waste stream and the day of the
month (``caption-dechets_menagers-7.gif``), so :class:`SidecParser` reads the
rows off those file names. The commune dropdown on the same page doubles as
the list of valid values.
"""

import datetime
import re
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from requests import Response

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Lookup, Request, YearlyRetriever

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

CALENDAR_URL = "https://www.sidec.lu/fr/Collectes/Calendrier"

_COMMUNE_ID = re.compile(r"\((\d+)\)")
_CAPTION = re.compile(r"caption-(?P<label>.+)-(?P<day>\d+)\.gif")


def _commune_id(commune: str | None) -> str | None:
    match = _COMMUNE_ID.search(commune or "")
    return match.group(1) if match else None


def _suggest_communes(response: Response, *, commune: str | None = None, **_) -> str:
    """Raise with the dropdown's communes: the value has no ``(id)``."""
    soup = BeautifulSoup(response.text, "html.parser")
    select = soup.find("select", {"name": "myCommune"})
    options = select.find_all("option") if select else []
    suggestions = sorted(
        f"{option.text.strip()} ({option['value']})"
        for option in options
        if option.get("value")
    )
    raise SourceArgumentNotFoundWithSuggestions("commune", commune, suggestions)


class SidecParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, label)`` rows of one year's calendar page."""

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        soup = BeautifulSoup(response.text, "html.parser")
        year_input = soup.find("input", {"name": "annee"})
        year = int(str(year_input["value"])) if year_input else None
        if year is None:
            heading = soup.select_one("#col-2 h4")
            found = re.search(r"\d{4}", heading.get_text()) if heading else None
            if found is None:
                return []
            year = int(found.group(0))

        rows: list[tuple[datetime.date, str]] = []
        for month, month_div in enumerate(soup.select("#col-2 .calendar"), start=1):
            for image in month_div.select(".calendar-day img"):
                match = _CAPTION.search(str(image.get("src", "")).rsplit("/", 1)[-1])
                if match is None:
                    continue
                try:
                    day = datetime.date(year, month, int(match["day"]))
                except ValueError:
                    continue
                rows.append((day, match["label"].replace("_", " ")))
        return rows


#: the commune id out of ``"Mersch (2611)"``, then one calendar page per year
#: (next year too from October)
retriever = YearlyRetriever(
    prepare=Lookup(
        CALENDAR_URL,
        given=lambda commune, **_: _commune_id(commune),
        pick=_suggest_communes,
    ),
    fetch=Request(
        CALENDAR_URL,
        params=lambda year, commune_id, **_: {"annee": year, "myCommune": commune_id},
    ),
    rollover_month=10,
)
