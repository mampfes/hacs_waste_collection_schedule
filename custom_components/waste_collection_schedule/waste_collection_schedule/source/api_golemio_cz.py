import logging
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Praha"
DESCRIPTION = "Prague municipal waste collection via Golemio API."
URL = "https://api.golemio.cz/docs/openapi/"

TEST_CASES = {
    "Chvalská": {
        "lat": 50.104802397741665,
        "lon": 14.538238985303936,
        "radius": 1,
        "api_key": "!secret api_golemio_api_key",
        "ignored_containers": [35895],
    },
    "Smržových - monitored": {
        "lat": 50.10847352,
        "lon": 14.5154944,
        "radius": 1,
        "only_monitored": True,
        "api_key": "!secret api_golemio_api_key",
    },
    "Chvalská - suffix": {
        "lat": 50.104802397741665,
        "lon": 14.538238985303936,
        "radius": 1,
        "api_key": "!secret api_golemio_api_key",
        "suffix": " - Chvalská",
        "ignored_containers": [35895],
    },
    "Radius - auto_suffix": {
        "lat": 50.104802397741665,
        "lon": 14.538238985303936,
        "radius": 300,
        "api_key": "!secret api_golemio_api_key",
        "auto_suffix": True,
        "ignored_containers": [35895, 35901, 35918],
    },
}

API_URL = "https://api.golemio.cz/"

ICON_MAP = {
    1: "mdi:bottle-soda",  # Barevné sklo | Tinted glass |
    2: "mdi:lightning-bolt",  # Elektrozařízení | Electric waste |
    3: "mdi:cog",  # Kovy | Metals |
    4: "mdi:package-variant-closed",  # Nápojové kartóny | Beverage cartons |
    5: "mdi:package-variant",  # Papír | Paper |
    6: "mdi:recycle",  # Plast | Plastics |
    7: "mdi:bottle-soda-outline",  # Čiré sklo | Clear glass |
    8: "mdi:barrel",  # Jedlé tuky a oleje | Edible fats and oils |
    9: "mdi:delete-variant",  # Multikomoditní sběr | Multicommodity |
}

_CZ_DAY_TO_WEEKDAY = {
    "Po": 0,
    "Út": 1,
    "St": 2,
    "Čt": 3,
    "Pá": 4,
    "So": 5,
    "Ne": 6,
}

_LOGGER = logging.getLogger(__name__)


def _generate_next_picks(next_pick: date, pick_days: str, frequency: int, count=10):
    """
    Yield expected pick dates from given `next_pick`, `pick_day` and `frequency`.

    Cleaning Frequency
    | Value | 1st digit - period duration | 2nd digit - frequency |
    Example
    | 13 | 1 | 3 | 3 times per 1 week |
    | 61 | 6 | 1 | Once per 6 weeks |

    >>> [d for d in _generate_next_picks(date(2024, 2, 20), "Po, Út, Pá", 13, 5)]
    [datetime.date(2024, 2, 19), datetime.date(2024, 2, 20), datetime.date(2024, 2, 23), datetime.date(2024, 2, 26), datetime.date(2024, 2, 27)]

    >>> [d for d in _generate_next_picks(date(2024, 2, 20), "Út", 41, 4)]
    [datetime.date(2024, 1, 23), datetime.date(2024, 2, 20), datetime.date(2024, 3, 19), datetime.date(2024, 4, 16)]

    >>> [d for d in _generate_next_picks(date(2024, 2, 26), "Po, Čt", 12, 4)]
    [datetime.date(2024, 2, 22), datetime.date(2024, 2, 26), datetime.date(2024, 2, 29), datetime.date(2024, 3, 4)]

    >>> [d for d in _generate_next_picks(date(2024, 2, 26), "Po, Čt", 42, 5)]
    [datetime.date(2024, 2, 1), datetime.date(2024, 2, 26), datetime.date(2024, 2, 29), datetime.date(2024, 3, 25), datetime.date(2024, 3, 28)]
    """
    period_duration = frequency // 10
    times_per_week = frequency % 10

    weekdays = [
        _CZ_DAY_TO_WEEKDAY[day] for day in map(str.strip, pick_days.split(", "))
    ]

    if times_per_week != len(weekdays):
        _LOGGER.warning(
            "Times per week (%s) and pick days (%s) mismatch, generated dates may be wrong.",
            times_per_week,
            pick_days,
        )

    # check where we are in the days list
    first_pick_index = weekdays.index(next_pick.weekday())
    first_pick_weekday = weekdays[first_pick_index]

    # get one date in the past (can be today) - API only provides future dates
    for i in range(-1, count - 1):
        next_pick_index = (first_pick_index + i) % len(weekdays)

        weeks = period_duration * ((first_pick_index + i) // len(weekdays))
        days = weekdays[next_pick_index] - first_pick_weekday

        yield next_pick + timedelta(weeks=weeks, days=days)


class Source:
    def __init__(
        self,
        lat: float,
        lon: float,
        radius: int,
        api_key: str,
        only_monitored: bool = False,
        ignored_containers: list | None = None,
        auto_suffix: bool = False,
        suffix: str | None = None,
    ):
        self._lat = lat
        self._lon = lon
        self._radius = radius
        self._api_key = api_key
        self._only_monitored = only_monitored
        self._ignored_containers = ignored_containers or []
        self._auto_suffix = auto_suffix
        self._suffix = suffix

    def fetch(self):
        r = requests.get(
            f"{API_URL}v2/sortedwastestations",
            params={
                "latlng": f"{self._lat},{self._lon}",
                "range": self._radius,
                "limit": 1000,
            },
            headers={"X-Access-Token": self._api_key, "Accept": "application/json"},
        )

        r.raise_for_status()
        features = r.json()["features"]

        entries = []

        for feature in features:
            for container in feature["properties"]["containers"]:
                if container["container_id"] in self._ignored_containers:
                    continue

                trash_type = container["trash_type"]
                frequency = container["cleaning_frequency"]
                next_pick = frequency.get("next_pick")
                if not next_pick:
                    # some containers have no next pick date, show warning if they are not ignored
                    _LOGGER.warning(
                        "No next pick date for container ID %s (%s), add it to ignored_containers.",
                        container["container_id"],
                        trash_type["description"],
                    )
                    continue

                next_pick = date.fromisoformat(next_pick)

                # use optionally suffixed trash type as the type display name
                t = trash_type["description"]
                if self._auto_suffix:
                    t = f"{t} - {feature['properties'].get('name', feature['properties']['id'])}"
                if self._suffix:
                    t = f"{t}{self._suffix}"

                for d in _generate_next_picks(
                    next_pick, frequency["pick_days"], frequency["id"]
                ):
                    entries.append(
                        Collection(
                            date=d,
                            t=t,
                            icon=ICON_MAP.get(trash_type["id"]),
                        )
                    )

        return entries
