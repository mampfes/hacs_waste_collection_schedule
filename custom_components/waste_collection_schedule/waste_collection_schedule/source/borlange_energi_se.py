import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Borlänge Energi"
DESCRIPTION = "Waste collection schedule for Borlänge, Sweden"
URL = "https://www.borlange-energi.se/avfall-och-atervinning/sophamtning"
COUNTRY = "se"
TEST_CASES = {
    "Mats Knuts Väg": {"pickup_address": "Mats Knuts Väg 100"},
    "Rorsmans Väg 7": {"pickup_address": "Rorsmans Väg 7"},
}

WASTE_PAGE_URL = "https://www.borlange-energi.se/avfall-och-atervinning/sophamtning"

# The "När kommer sopbilen?" widget on the waste page is a Sitevision app
# (applicationId "se.soleil.garbageTruckFetcher"). Its data comes from
# https://www.borlange-energi.se/appresource/<page_id>/<portlet_id>/getcontainerdata
# Both <page_id> and <portlet_id> are Sitevision-internal ids that are
# reassigned whenever the page or the widget placement is rebuilt (this is
# what happened in GitHub issue #7249, where the previously hardcoded
# <portlet_id> started 404ing). To avoid hardcoding values that silently
# rot again, both ids are resolved from the live waste page on every fetch.
PORTLET_ID_PATTERN = re.compile(
    r"applicationId:'se\.soleil\.garbageTruckFetcher\|[^']*'.*?portletId:'([^']+)'"
)
PAGE_ID_PATTERN = re.compile(r"/webapp-resource/([^/\"']+)/")

DEFAULT_ICON = "mdi:trash-can"
MONTHS = {
    "januari": 1,
    "februari": 2,
    "mars": 3,
    "april": 4,
    "maj": 5,
    "juni": 6,
    "juli": 7,
    "augusti": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

ICON_MAP = {
    "Matavfall": Icons.BIO_KITCHEN,
    "Restavfall": Icons.GENERAL_WASTE,
    "Pappersförpackningar": Icons.PAPER,
    "Plastförpackningar": Icons.GLASS,
}


def parse_swedish_date(text: str) -> datetime:
    """Extract date from Swedish text.

    Handles formats like 'Nästa tömning sker torsdag den 15 januari', as well
    as the relative wording the API uses on the day of a collection ('Tömning
    idag') and the day before it ('Tömning imorgon'). Both the joined and
    separated spellings are accepted.
    """
    lowered = text.lower()

    # Expected API values on and just before a collection day, not malformed
    # data, so they must not raise. Anchored on word boundaries so weekday
    # names ending in "dag" are unaffected.
    midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if re.search(r"\bi\s?dag\b", lowered):
        return midnight
    if re.search(r"\bi\s?morgon\b", lowered):
        return midnight + timedelta(days=1)

    match = re.search(r"(\d{1,2})\s+([a-zåäö]+)", lowered)
    if not match:
        raise ValueError(f"Unrecognized date format: {text}")

    day = int(match.group(1))
    month_name = match.group(2)
    if month_name not in MONTHS:
        # The regex only requires a number followed by a word, so input such as
        # "om 3 dagar" reaches here. Raise ValueError like the branch above
        # instead of letting a KeyError escape.
        raise ValueError(f"Unrecognized month name in date: {text}")
    month = MONTHS[month_name]

    year = datetime.now().year
    date = datetime(year, month, day)

    # If the date has already passed this year, use next year
    if date.date() < datetime.now().date():
        date = datetime(year + 1, month, day)

    return date


def _resolve_endpoint(session: requests.Session) -> str:
    """Resolve the current getcontainerdata endpoint from the live waste page.

    Sitevision assigns a page id and a portlet id to the waste collection
    widget, both of which are reassigned whenever the page or the widget
    placement is rebuilt. Instead of hardcoding a URL that silently starts
    404ing the next time that happens, the current ids are discovered fresh
    on every fetch.
    """
    r = session.get(WASTE_PAGE_URL, timeout=30)
    r.raise_for_status()
    html = r.text

    portlet_match = PORTLET_ID_PATTERN.search(html)
    page_match = PAGE_ID_PATTERN.search(html)

    if not portlet_match or not page_match:
        raise ValueError(
            "Could not locate the waste collection widget on the Borlänge "
            "Energi website; the page layout may have changed"
        )

    portlet_id = portlet_match.group(1)
    page_id = page_match.group(1)

    return (
        f"https://www.borlange-energi.se/appresource/{page_id}/"
        f"{portlet_id}/getcontainerdata"
    )


class Source:
    def __init__(self, pickup_address: str):
        if not pickup_address:
            raise SourceArgumentRequired(
                "pickup_address",
                "an address is required to fetch the collection schedule",
            )
        self._pickup_address = pickup_address

    def fetch(self):
        session = requests.Session()
        endpoint = _resolve_endpoint(session)

        params = {"pickupAddress": self._pickup_address}

        r = session.get(endpoint, params=params, timeout=30)
        r.raise_for_status()

        data = r.json()

        if not isinstance(data, list):
            raise ValueError(
                "Unexpected response format from Borlänge Energi (expected a list)"
            )

        if not data:
            raise SourceArgumentNotFound(
                "pickup_address",
                self._pickup_address,
            )

        entries = []

        for item in data:
            date = parse_swedish_date(item["disposalDay"])
            waste_type = item["contentType"]

            entries.append(
                Collection(
                    date=date.date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type, DEFAULT_ICON),
                )
            )

        return entries
