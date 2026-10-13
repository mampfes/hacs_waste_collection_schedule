"""The Potsdam waste calendar (``geben-und-nehmen-markt.de/abfallkalender``).

The city's calendar is a Gatsby site that ships one ``page-data.json`` per
year with the rules of every street (about 17 MB): a weekday, a rhythm and a
start week per container, exceptions for moved days and fixed dates for the
special rounds. The site's JavaScript expands these into dates in the browser;
:class:`PotsdamParser` expands them the same way for the configured district
and street and yields ``(date, waste type)`` rows.

The residents choose their rhythm per container on the site (``rest_rhythm``,
``bio_rhythm``, ``papier_rhythm``), so those are source parameters.
"""

import datetime
import json
import re
from typing import TYPE_CHECKING

from requests import Response

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import YearlyRetriever, YearUrl

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

DATA_URL = "https://www.geben-und-nehmen-markt.de/abfallkalender/potsdam/{year}/page-data/index/page-data.json"

TYPE_NAMES = {
    1: "Restabfall",
    2: "Bioabfall",
    3: "Leichtverpackungen",
    4: "Altpapier",
    5: "Biotonnenreinigung",
    6: "Weihnachtsbaumabholung",
    7: "Grünabfallsammlung",
}

#: Which source parameter holds the rhythm chosen for a container type.
_RHYTHM_PARAMS = {
    1: ("rest_rhythm", 0),
    2: ("bio_rhythm", 0),
    3: ("gelb_rhythm", 3),
    4: ("papier_rhythm", 0),
}

_COMBINED_FROM = "0401"
_COMBINED_UNTIL = "1031"

_YEAR = re.compile(r"/potsdam/(\d{4})/")

retriever = YearlyRetriever(fetch=YearUrl(DATA_URL, timeout=120), rollover_month=12)


def _norm(value: object) -> str:
    return str(value or "").lower().strip()


def _termin(value: str) -> datetime.date:
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _type_matches(
    day: datetime.date, bin_type: int, turnus: int, rest: int, bio: int, paper: int
) -> bool:
    """Whether the chosen rhythms select ``turnus`` for this container type."""
    month_day = day.strftime("%m%d")
    if bin_type == 1:
        return rest == turnus
    if bin_type == 2:
        if bio == turnus:
            return True
        # "Kombileerung": every second week in the season, every third outside
        return bio == 5 and (
            (turnus == 2 and _COMBINED_FROM <= month_day <= _COMBINED_UNTIL)
            or (
                turnus == 3
                and (month_day < _COMBINED_FROM or month_day > _COMBINED_UNTIL)
            )
        )
    if bin_type == 4:
        return paper == turnus
    return bin_type == 3


def _is_weekly_rule(
    entry: dict,
    day: datetime.date,
    exceptions: dict[datetime.date, datetime.date],
    rhythms: tuple[int, int, int],
    check_exception: bool = True,
) -> bool:
    week = day.isocalendar()[1]
    even_week = week % 2 == 0
    weekday = day.weekday() + 1

    if check_exception:
        moved_away = False
        for original, moved_to in exceptions.items():
            if day == moved_to:
                return _is_weekly_rule(entry, original, exceptions, rhythms, False)
            if day == original:
                moved_away = True
        if moved_away:
            return False

    rest, bio, paper = rhythms
    rhythm = entry["rhythmus"]
    kind = entry["typ"]

    def matches(turnus: int) -> bool:
        return _type_matches(day, kind, turnus, rest, bio, paper)

    if rhythm == 1 and matches(2):
        return (
            (entry["tag1"] == weekday and entry["tag2"] == 0)
            or (entry["tag1"] == weekday and not even_week)
            or (entry["tag2"] == weekday and even_week)
        )
    if rhythm == 2 and matches(3):
        return (
            (entry["woche"] == 2 and not even_week)
            or (entry["woche"] == 3 and even_week)
        ) and entry["tag1"] == weekday
    if rhythm == 3 and matches(4):
        return (week - entry["beginn"]) % 4 == 0 and entry["tag1"] == weekday
    if rhythm == 4 and matches(1):
        return (
            entry["tag1"] == weekday or (entry["tag2"] > 0 and entry["tag2"] == weekday)
        ) and week >= entry["beginn"]
    return False


def _is_collection(
    entry: dict,
    day: datetime.date,
    exceptions: dict[datetime.date, datetime.date],
    rhythms: tuple[int, int, int],
) -> bool:
    kind = entry["typ"]
    if kind in (5, 6):
        return day in (_termin(entry["termin1"]), _termin(entry["termin2"]))
    if kind == 7:
        return day == _termin(entry["termin1"])
    return _is_weekly_rule(entry, day, exceptions, rhythms)


def _exceptions(entry: dict) -> dict[datetime.date, datetime.date]:
    try:
        raw = json.loads(entry["ausnahmen"])
    except (json.JSONDecodeError, TypeError):
        return {}
    return {
        datetime.datetime.strptime(
            original, "%d.%m.%Y"
        ).date(): datetime.datetime.strptime(moved_to, "%d.%m.%Y").date()
        for original, moved_to in raw.items()
    }


class PotsdamParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, waste type)`` rows for the configured ``ortsteil`` / ``strasse``."""

    def __call__(
        self, response: Response, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        params = source.params if source is not None else {}
        district = params.get("ortsteil")
        street = params.get("strasse")
        year = int(_YEAR.search(response.url).group(1))  # type: ignore[union-attr]
        rhythms = tuple(
            int(params.get(_RHYTHM_PARAMS[kind][0]) or _RHYTHM_PARAMS[kind][1])
            for kind in (1, 2, 4)
        )

        data = response.json()["result"]["data"]["dbapi"]
        districts = data["allRegionen"][0]["regionen"][0]["ortsteile"]
        found = [o for o in districts if _norm(o["name"]) == _norm(district)]
        if not found:
            raise SourceArgumentNotFoundWithSuggestions(
                "ortsteil", district, sorted(o["name"] for o in districts)
            )
        streets = found[0]["strassen"]
        selected = [s for s in streets if _norm(s["name"]) == _norm(street)]
        if not selected:
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", street, sorted(s["name"] for s in streets)
            )

        rows: list[tuple[datetime.date, str]] = []
        days = [
            datetime.date(year, 1, 1) + datetime.timedelta(days=offset)
            for offset in range(366)
        ]
        for entry in selected[0]["eintraege"]:
            exceptions = _exceptions(entry)
            label = TYPE_NAMES[entry["typ"]]
            rows.extend(
                (day, label)
                for day in days
                if day.year == year and _is_collection(entry, day, exceptions, rhythms)  # type: ignore[arg-type]
            )
        return rows
