from datetime import date, timedelta
from typing import ClassVar, NamedTuple, final

from waste_collection_schedule import preprocessors, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    street_address,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.KmlZones import KmlWeekdayZoneParser
from waste_collection_schedule.transformers import RowTransformer


class _Town(NamedTuple):
    page: str  # slug of https://mydisposal.com/towns/<page>/
    map_id: str  # Google My Maps id of the pickup-day map embedded on that page
    weekly_recycling: bool  # False: every other week
    yard_waste_until: tuple[int, int]  # (month, day); the season starts April 1


# Homewood towns whose page embeds a pickup-day map (one polygon per weekday).
# Needed at fetch time, so it stays in Python rather than doc/regions/.
TOWNS: dict[str, _Town] = {
    "Dolton": _Town("dolton", "1mN_duGstdApbt5Fb0twHzw78vt3fzkI", False, (11, 30)),
    "Flossmoor": _Town(
        "flossmoor", "1r-O__F2p0cW4XWXbRrdwMMQOcdvcVms", False, (11, 30)
    ),
    "Homer Glen": _Town(
        "homer-glen", "1NMUPq-VadGsqy2AQhUdKko2zQq8-9eU", True, (11, 30)
    ),
    # Lansing's page: "April 1 - the second full week of December".
    "Lansing": _Town("lansing", "1VC7gS9GeotWHzhs6uIvzcL650w9VTlQ", False, (12, 11)),
    "Lockport Township": _Town(
        "lockport-township", "1NNXtfjuBQceQZEYZS1vnwCbCslSeluTL", True, (11, 30)
    ),
    "Markham": _Town("markham", "168uKcYDIv6tZbXvBLJrUkmHZsSJdrjo", False, (11, 30)),
    "Minooka": _Town(
        "minooka-garbage", "1Vy6mZN6VbMAUz1zVYdyqQ6ziwJmysMM", False, (11, 30)
    ),
    "Munster": _Town("munster", "1VtetT5kg5q_LeGlFaDvnvw0vhF6UWWHK", False, (11, 30)),
    "New Lenox": _Town(
        "new-lenox", "1qEGNbb8klcfBsoWBnAwNW0zk4YgUCeg", False, (11, 30)
    ),
    "Oak Forest": _Town(
        "oak-forest-garbage", "12bQvO6756zsOhv8FnBXZWzBo-mj2e7E", False, (11, 30)
    ),
    "Richton Park": _Town(
        "richton-park", "1cIvFkLEXMqF0CPkzOfBTLiquMp8ERk4", False, (12, 31)
    ),
    "South Holland": _Town(
        "south-holland", "17SXCKynvYYpgeLqfqj0ER1nPXJtrQuI", False, (11, 30)
    ),
    "Tinley Park": _Town(
        "tinley-park", "1qBkaebgaZ_2QhY5_98bYFu4bT8HNdRg", False, (11, 30)
    ),
}

# The six holidays Homewood's town pages list as delaying pickup by one day.
HOLIDAYS = (
    "New Year",
    "Memorial",
    "Independence",
    "Labor",
    "Thanksgiving",
    "Christmas",
)
WEEKS = 26


def _schedule(record, source):
    town = TOWNS[source.params["municipality"]]
    today = date.today()
    start = recurrence.next_weekday(record["weekday"], on_or_after=today)
    yield preprocessors.Schedule(key="garbage", start=start, count=WEEKS)

    if town.weekly_recycling:
        yield preprocessors.Schedule(key="recycling", start=start, count=WEEKS)
    elif source.params.get("recycling_date"):
        try:
            anchor = date.fromisoformat(source.params["recycling_date"])
        except ValueError:
            raise SourceArgumentException(
                "recycling_date", "Use the format YYYY-MM-DD."
            ) from None
        # Snap to the zone weekday, so a holiday-shifted date still sets the week.
        anchor += timedelta(days=record["weekday"] - anchor.weekday())
        yield preprocessors.Schedule(
            key="recycling",
            start=anchor,
            step=recurrence.FORTNIGHTLY,
            count=WEEKS // 2,
            anchor=True,
        )

    month, day = town.yard_waste_until
    for year in (today.year, today.year + 1):
        yield preprocessors.Schedule(
            key="yard",
            start=start,
            not_before=max(date(year, 4, 1), today),
            until=min(date(year, month, day), start + timedelta(weeks=WEEKS)),
        )


def _holiday_delay(collection_date, key, source):
    """A weekday holiday delays that day's and the rest of the week's pickups."""
    week = collection_date.isocalendar()[:2]
    for holiday, name in recurrence.us_federal_holidays(
        [collection_date.year], observed=False
    ).items():
        if (
            any(h in name for h in HOLIDAYS)
            and holiday.weekday() < 5
            and holiday.isocalendar()[:2] == week
            and holiday <= collection_date
        ):
            return collection_date + timedelta(days=1)
    return collection_date


@final
class Source(BaseSource):
    TITLE = "Homewood Disposal Service (NuWay)"
    DESCRIPTION = "Source for Homewood Disposal Service (also known as NuWay Disposal), Chicagoland and Northwest Indiana."
    URL = "https://mydisposal.com"
    COUNTRY = "us"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@Tom-Neverwinter"]
    RAISE_ON_EMPTY = True
    TEST_CASES: ClassVar[dict] = {
        "Homer Glen Village Hall": {
            "address": "14240 W 151st St, Homer Glen, IL 60491",
            "municipality": "Homer Glen",
        },
        "Tinley Park Village Hall": {
            "address": "16250 S Oak Park Ave, Tinley Park, IL 60477",
            "municipality": "Tinley Park",
            "recycling_date": "2026-11-03",
        },
        "Munster Town Hall": {
            "address": "1005 Ridge Rd, Munster, IN 46321",
            "municipality": "Munster",
        },
    }
    REGIONS: ClassVar[list] = [
        region(
            f"{name}, {'IN' if name == 'Munster' else 'IL'}",
            url=f"https://mydisposal.com/towns/{town.page}/",
            municipality=name,
        )
        for name, town in TOWNS.items()
    ]
    PARAMS = (
        street_address(),
        dropdown("municipality", list(TOWNS)),
        text_field("recycling_date", "Recent recycling pickup date", optional=True),
    )
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address and pick your municipality; the pickup day comes from the map on your town's mydisposal.com page. Most towns collect recycling every other week: enter the date (YYYY-MM-DD) of any recycling pickup to get recycling dates, or leave it empty to skip recycling. Homer Glen and Lockport Township recycle weekly and need no date.",
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Request(
            "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates",
            params=lambda address, **_: {
                "SingleLine": address,
                "outSR": '{"wkid": 4326}',
                "maxLocations": "1",
                "f": "json",
            },
        ),
        targets=lambda source, response: (
            "https://www.google.com/maps/d/kml?forcekml=1&mid="
            + TOWNS[source.params["municipality"]].map_id,
        ),
        fetch=retrievers.Request(lambda target, response, **_: target),
        include_prepared=True,
    )
    parse = KmlWeekdayZoneParser(
        folder=".",
        groups={"garbage": r"(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY)"},
        weekdays={
            name.upper(): i for i, name in enumerate(recurrence.weekday_names("en")[:5])
        },
    )
    preprocess = preprocessors.Compose(
        preprocessors.RecurrenceExpander(_schedule),
        preprocessors.HolidayShift(_holiday_delay),
        preprocessors.SortRows(),
    )
    transform = RowTransformer(
        type_value_map={
            "garbage": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "yard": wt.GARDEN_WASTE,
        }
    )
