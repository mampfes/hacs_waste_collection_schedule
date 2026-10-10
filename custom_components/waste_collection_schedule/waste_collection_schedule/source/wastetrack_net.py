"""WasteTrack self-service locator (v2.wastetrack.net), by 3Logix.

Demonstrates: a three-request conversation expressed as a LookupChainRetriever.
A council's public key buys a session token, the token and the free-text
address search the locator for a site id, and the token and site id fetch the
site's services table. The server only answers requests whose Origin is the
council's own website, so the key-to-website registry is needed while fetching
and stays in Python.

Each table row is a service, its cadence in words ("Weekly on Thursdays",
"Every 2 weeks on Thursdays") and its next date ("15/10/2026", or "Today" /
"Tomorrow" when it is that close). RecurrenceExpander projects the cadence
forward from the next date.
"""

import datetime
import re
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import date_parsers, parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import api_key, street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API = "https://v2.wastetrack.net/self_service"

# Council key -> council website. The server rejects (HTTP 500) any request
# whose Origin is not the website the key was issued to.
_COUNCIL_SITES = {
    "da1d834c-3d97-4f96-9d60-4107ef0a53e6": "https://www.georgesriver.nsw.gov.au",
}

# How far ahead to project each service's cadence.
_HORIZON = datetime.timedelta(weeks=26)

_parse_date = date_parsers.for_format("%d/%m/%Y")


def _headers(*_, key, **__) -> dict[str, str]:
    site = _COUNCIL_SITES.get(key)
    if site is None:
        raise SourceArgumentNotFound("key", key)
    return {"Origin": site, "Referer": f"{site}/"}


def _normalise(text: str) -> str:
    return " ".join(text.replace(",", " ").split()).lower()


def _pick_token(response, **_) -> str:
    return response.json()["token"]


def _pick_site(response, token, *, address, **_) -> str:
    """The site id of the address, from the locator's list of matches."""
    soup = BeautifulSoup(response.text, "html.parser")
    sites: dict[str, str] = {}
    for item in soup.select("li.wtss-site"):
        radio = item.select_one("input[name=wtss_site]")
        label = item.select_one(".wtss-site-fullstreet")
        if radio is not None and label is not None:
            sites[" ".join(label.get_text(" ").split())] = str(radio["value"])
    if not sites:
        raise SourceArgumentNotFound("address", address)
    if len(sites) == 1:
        return next(iter(sites.values()))
    wanted = _normalise(address)
    for name, site_id in sites.items():
        if _normalise(name) == wanted:
            return site_id
    raise SourceArgAmbiguousWithSuggestions("address", address, list(sites))


def _next_date(text: str) -> datetime.date | None:
    word = text.strip().lower()
    today = datetime.date.today()
    if word == "today":
        return today
    if word == "tomorrow":
        return today + datetime.timedelta(days=1)
    try:
        return _parse_date(text)
    except ValueError:
        return None


def _step(cadence: str) -> datetime.timedelta | None:
    text = cadence.strip().lower()
    if text.startswith("weekly"):
        return recurrence.WEEKLY
    if text.startswith("fortnightly"):
        return recurrence.FORTNIGHTLY
    match = re.match(r"every\s+(\d+)\s+weeks?", text)
    if match:
        return recurrence.WEEKLY * int(match.group(1))
    return None


def _weekdays(cadence: str) -> list[int]:
    """The weekdays a cadence names, "Mondays, Wednesdays, and Fridays" -> [0, 2, 4]."""
    days = (
        recurrence.weekday(word.rstrip("s")) for word in re.findall(r"\w+", cadence)
    )
    return [day for day in days if day is not None]


def _lines(cell: Tag) -> list[str]:
    return [line.strip() for line in cell.get_text("\n").splitlines() if line.strip()]


def _schedules(service: str, cadence: str, next_text: str):
    start = _next_date(next_text)
    if start is None:
        return
    step = _step(cadence)
    if step is None:
        # A cadence the source does not know: publish the one date given.
        yield Schedule(service, start)
        return
    count = _HORIZON // step
    days = _weekdays(cadence)
    if len(days) <= 1:
        yield Schedule(service, start, step, count)
        return
    # Several days on one cadence share one "next" date, the earliest of them.
    for day in days:
        yield Schedule(
            service, recurrence.next_weekday(day, on_or_after=start), step, count
        )


def _describe(row: Tag, source):
    cells = row.find_all("td")
    if len(cells) < 3:
        return
    service_cell, cadence_cell, next_cell = cells[-3:]
    service = service_cell.get_text(" ", strip=True)
    if not service:
        return
    # A site with several rounds of one service (a busy commercial property)
    # lists one cadence and one next date per line, in the same order.
    cadences, next_dates = _lines(cadence_cell), _lines(next_cell)
    if not next_dates:
        return
    if len(cadences) != len(next_dates):
        next_dates = next_dates[:1] * len(cadences)
    for cadence, next_text in zip(cadences, next_dates, strict=True):
        yield from _schedules(service, cadence, next_text)


@final
class Source(BaseSource):
    TITLE = "WasteTrack (3Logix)"
    DESCRIPTION = (
        "Source for councils using the WasteTrack self-service locator by 3Logix."
    )
    URL = "https://v2.wastetrack.net"
    COUNTRY = "au"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@stickx"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Georges River Civic Centre - 16 MacMahon Street Hurstville": {
            "address": "16 MacMahon Street, Hurstville",
            "key": "da1d834c-3d97-4f96-9d60-4107ef0a53e6",
        },
        "Georges River - 10 Gungah Bay Road Oatley": {
            "address": "10 Gungah Bay Road, Oatley",
            "key": "da1d834c-3d97-4f96-9d60-4107ef0a53e6",
        },
    }

    REGIONS = (
        region(
            "Georges River Council",
            url="https://www.georgesriver.nsw.gov.au",
            key="da1d834c-3d97-4f96-9d60-4107ef0a53e6",
        ),
    )

    PARAMS = (street_address(), api_key("key"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as the council's bin day lookup shows it, "
            "e.g. '16 MacMahon Street, Hurstville'. The key is pre-filled when you "
            "pick your council."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API}/request_token",
                params=lambda key, **_: {"key": key},
                headers=_headers,
                pick=_pick_token,
            ),
            Lookup(
                f"{_API}/locator_search",
                method="POST",
                data=lambda token, *, key, address, **_: {
                    "key": key,
                    "token": token,
                    "search": address,
                },
                headers=_headers,
                pick=_pick_site,
            ),
        ),
        url=f"{_API}/locator_show",
        method="POST",
        data=lambda token, site_id, *, key, **_: {
            "key": key,
            "token": token,
            "wtss_site": site_id,
        },
        headers=_headers,
        raise_for_status=True,
    )
    parse = parsers.HtmlParser(
        "table.wtss-service-locator-results tbody tr",
        require=["table.wtss-service-locator-results"],
    )
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden Organics": wt.GARDEN_WASTE,
        }
    )
