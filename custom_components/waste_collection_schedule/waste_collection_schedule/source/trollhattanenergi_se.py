import datetime
import re
from collections.abc import Iterator
from typing import Any, ClassVar, final

from waste_collection_schedule import lookups, parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

# The public (no login) endpoints of the Trollhättan Energi app backend. The
# current app reads the same schedule behind a BankID login; these older app
# routes are still served anonymously and are the ones used here.
API_URL = "https://app.trollhattanenergi.se/wp-json/app"
# The page that states this year's garden-waste season ("Under 2026 hämtar vi
# ditt trädgårdsavfall mellan veckorna 14–47."). The API itself has no season.
SEASON_URL = (
    "https://www.trollhattanenergi.se/avfall-och-atervinning/sophamtning/"
    "hamtningsdagar/"
)

GARDEN = "Trädgårdsavfall"

# How far ahead the cadence is projected from the API's next date.
HORIZON = datetime.timedelta(days=365)

_SEASON = re.compile(
    r"Under (\d{4}) hämtar vi ditt trädgårdsavfall mellan veckorna "
    r"(\d{1,2})\s*[–-]\s*(\d{1,2})",
    re.IGNORECASE,
)


def _pick_plant(response, *_keys, address: str, **_) -> str:
    """The address search answers ``[{plant_number, address}]`` by substring."""
    rows = [row for row in response.json() if row.get("plant_number")]
    wanted = lookups.normalize_text(address)
    names = {lookups.normalize_text(row["address"]): row for row in rows}
    if wanted in names:
        return names[wanted]["plant_number"]
    # "Albertsvägen 1" for the only "Albertsvägen 1 <area>" there is.
    longer = [row for name, row in names.items() if name.startswith(f"{wanted} ")]
    if len(longer) == 1:
        return longer[0]["plant_number"]
    if not rows:
        raise SourceArgumentNotFound(
            "address",
            address,
            "please enter the street and house number as the address search of "
            "Återvinningsappen shows it, including å, ä and ö.",
        )
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, sorted(row["address"].strip() for row in rows)
    )


def _as_one(parsed: Any, _source: Any) -> list[Any]:
    return [parsed]


def _together(records: list[Any], _source: Any) -> list[tuple[dict, str]]:
    """The plant reply and the season page text, as one record."""
    plant = next(r for r in records if isinstance(r, dict))
    page = next((r for r in records if isinstance(r, str)), "")
    return [(plant, page)]


def _weekdays(interval: str) -> list[int]:
    """Weekdays named in "Fredag jämn vecka" or "Tisdagar och fredagar"."""
    days = []
    for word in re.findall(r"\w+", interval.casefold()):
        day = recurrence.weekday(word)
        if day is None and word.endswith("ar"):
            day = recurrence.weekday(word[:-2])  # plural "tisdagar"
        if day is not None and day not in days:
            days.append(day)
    return days


def _weeks(interval: str) -> int | None:
    """The cadence in weeks, or None for an interval text not understood.

    "Varje torsdag" / "Tisdagar och fredagar" = weekly, "Fredag jämn vecka" /
    "Torsdag ojämn vecka" = every other week, "Fredag var 4:e vecka ojämn
    vecka" = every fourth week. Trollhättan Energi keeps the interval across a
    53-week year (the week parity flips instead), so the cadence is stepped
    from the next date rather than tied to ISO week numbers.
    """
    text = interval.casefold()
    if match := re.search(r"var (\d+):[ae] vecka", text):
        return int(match.group(1))
    if "varannan vecka" in text or re.search(r"\b(o?jämn|udda) vecka", text):
        return 2
    if "varje" in text or re.search(r"dagar\b", text):
        return 1
    return None


def _deviating_weeks(plant: dict) -> list[tuple[datetime.date, datetime.date]]:
    """The "Ändrade hämtningsdagar" weeks, e.g. "2026-12-21 - 2026-12-25"."""
    weeks = []
    for entry in (plant.get("data") or {}).get("dates") or []:
        found = re.findall(r"\d{4}-\d{2}-\d{2}", str(entry.get("date") or ""))
        if len(found) == 2:
            first, last = (datetime.date.fromisoformat(d) for d in found)
            weeks.append((first, last))
    return weeks


def _garden_season(page: str) -> tuple[datetime.date, datetime.date] | None:
    """This year's garden-waste season, Monday of the first to Sunday of the last week."""
    match = _SEASON.search(page)
    if not match:
        return None
    year, first, last = (int(g) for g in match.groups())
    return (
        datetime.date.fromisocalendar(year, first, 1),
        datetime.date.fromisocalendar(year, last, 7),
    )


def _describe(record: tuple[dict, str], _source: Any) -> Iterator[Schedule]:
    """One series per bin: the API's next date, stepped by the interval text.

    In an "Ändrade hämtningsdagar" week the bin goes out a day earlier (a
    Monday collection stays on the Monday). Garden waste runs only within the
    season the provider's page states; outside it only the API's own next date
    is used.
    """
    plant, page = record
    deviating = _deviating_weeks(plant)
    season = _garden_season(page)
    seen: set[tuple[str, str, str]] = set()
    for bin_ in plant.get("bins") or []:
        key = str(bin_.get("type") or "").strip()
        interval = str(bin_.get("interval") or "").strip()
        pickup = str(bin_.get("pickup_date") or "")[:10]
        if not key or not pickup or (key, pickup, interval) in seen:
            continue
        seen.add((key, pickup, interval))
        next_date = datetime.date.fromisoformat(pickup)
        weeks = _weeks(interval)
        until = next_date + HORIZON
        if key == GARDEN:
            if season is None or not season[0] <= next_date <= season[1]:
                weeks = None
            else:
                until = min(until, season[1])
        if weeks is None:
            yield Schedule(key, next_date)
            continue

        step = datetime.timedelta(weeks=weeks)
        days = _weekdays(interval) or [next_date.weekday()]
        # A next date the API already moved into the day before its ordinary day.
        if days[0] == (next_date.weekday() + 1) % 7 and any(
            first <= next_date <= last for first, last in deviating
        ):
            next_date += datetime.timedelta(days=1)
        for day in days if weeks == 1 else days[:1]:
            start = next_date + datetime.timedelta(days=(day - next_date.weekday()) % 7)
            dates = recurrence.recurring_within(
                start, step, not_before=start, until=until
            )
            moved = [
                d
                for d in dates
                if d.weekday() != 0
                and any(first <= d <= last for first, last in deviating)
            ]
            yield Schedule(
                key,
                start,
                step,
                not_before=start,
                until=until,
                exclude=moved,
                extra=[d - datetime.timedelta(days=1) for d in moved],
            )


@final
class Source(BaseSource):
    TITLE = "Trollhättan Energi"
    DESCRIPTION = "Source for Trollhättan Energi, Trollhättan, Sweden."
    URL = "https://www.trollhattanenergi.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.PLASTIC,
        wt.METAL,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Albertsvägen 11": {"address": "Albertsvägen 11"},
        "Torngatan 38": {"address": "Torngatan 38"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street and house number exactly as the address search in "
            "Trollhättan Energi's Återvinningsappen shows it, including å, ä and ö "
            "(for example 'Albertsvägen 11'). Collections are projected about a "
            "year ahead from the next date and interval the app lists for each "
            "bin; garden waste only within this year's season."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            f"{API_URL}/v1/address",
            params=lambda address, **_: {"address": address},
            pick=_pick_plant,
        ),
        targets=lambda _source, plant: [f"{API_URL}/v2/plant/{plant}", SEASON_URL],
        # The season page only bounds garden waste: if it is unavailable the
        # garden bin falls back to its next date instead of failing the fetch.
        fetch=retrievers.Request(
            lambda url, *_, **__: url,
            raise_for_status=False,
        ),
    )
    parse = parsers.EachResponse(
        parsers.ByBodyPrefix(
            {"{": parsers.EachResponse(parsers.JsonParser(), then=_as_one)},
            default=parsers.EachResponse(parsers.HtmlTextParser(), then=_as_one),
        )
    )
    preprocess = Compose(_together, RecurrenceExpander(_describe))
    transform = ICSTransformer(
        carry_raw_label=True,
        type_value_map={
            # Four-compartment bins: paper packaging, food waste, coloured
            # glass and metal packaging (bin 1); residual waste, plastic
            # packaging, clear glass and newspapers (bin 2).
            "Kärl 1": [wt.FOOD_WASTE, wt.PAPER, wt.GLASS, wt.RECYCLABLES],
            "Kärl 2": [wt.GENERAL_WASTE, wt.PAPER, wt.GLASS, wt.RECYCLABLES],
            # Extra residual-waste bin, emptied with bin 2.
            "Kärl 3": wt.GENERAL_WASTE,
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            GARDEN: wt.GARDEN_WASTE,
            # Apartment buildings: one container per material.
            "Glas": wt.GLASS,
            "Kartong/pappförpackning": wt.PAPER,
            "Tidningar": wt.PAPER,
            "Plast": wt.PLASTIC,
            "Metall": wt.METAL,
        },
    )
