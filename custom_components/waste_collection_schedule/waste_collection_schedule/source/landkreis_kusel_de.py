"""Landkreis Kusel (landkreis-kusel.de).

Demonstrates: a two-step "scrape a <select> for the location id, then GET the
ICS feed with it" shape, where the id and the date window are *query*
arguments rather than path segments, which is what ``IcsLookupRetriever``
exists for. It also carries a year-boundary quirk the legacy source already
had: if the primary host's earliest event isn't in the current year, the same
two steps are repeated against a year-suffixed alternate host and the feeds
are merged (``stale_year_base_url``).
"""

from datetime import datetime, timedelta
from typing import ClassVar, final

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsLookupRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://abfallwirtschaft.landkreis-kusel.de"


def _make_comparable(ortsgemeinde: str) -> str:
    return (
        ortsgemeinde.lower()
        .replace("-", "")
        .replace(".", "")
        .replace("/", "")
        .replace(" ", "")
    )


def _pick_location(lookup, source) -> str:
    ortsgemeinde = source.params["ortsgemeinde"]
    soup = BeautifulSoup(lookup.text, "html.parser")
    select = soup.find("select", {"class": "form-select"})
    if not select or isinstance(select, NavigableString):
        raise ValueError("Invalid response from API")

    wanted = _make_comparable(ortsgemeinde)
    for option in select.find_all("option"):
        if _make_comparable(option.text) == wanted:
            value = option.get("value")
            if value:
                return str(value)

    raise SourceArgumentNotFoundWithSuggestions(
        "ortsgemeinde",
        ortsgemeinde,
        [option.text for option in select.find_all("option")],
    )


def _feed_params(key: str, **_) -> dict:
    """The location and the rolling one-year window the feed is asked for."""
    now = datetime.now()
    return {
        "location": key,
        "startDate": now.strftime("%Y-%m-%d"),
        "endDate": (now + timedelta(days=365)).strftime("%Y-%m-%d"),
    }


@final
class Source(BaseSource):
    TITLE = "Landkreis Kusel"
    DESCRIPTION = "Source for Landkreis Kusel."
    URL = "https://www.landkreis-kusel.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Adenbach": {"ortsgemeinde": "Adenbach"},
        "St. Julian - Eschenau": {"ortsgemeinde": "St. Julian - Eschenau"},
        "rutsweiler glan (wrong spelling)": {"ortsgemeinde": "rutsweiler glan"},
        "Kusel": {"ortsgemeinde": "Kusel"},
    }

    PARAMS = (municipality("ortsgemeinde"),)

    RAISE_ON_EMPTY = True

    retrieve = IcsLookupRetriever(
        base_url=_API_URL,
        extract=_pick_location,
        feed_path="/ical",
        params=_feed_params,
        # The site publishes each year on its own host ("abfall26" for 2026)
        # once the new calendar takes over; merged in when the primary feed has
        # aged out of the current year.
        stale_year_base_url=lambda year, **_: _API_URL.replace(
            "abfallwirtschaft", f"abfall{str(year)[2:]}"
        ),
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "LVP-Abfälle": RECYCLABLES,
            "Glas": GLASS,
            "Bioabfall": ORGANIC,
            "Papier": PAPER,
            "Umweltmobil": BULKY_WASTE,
        },
        # The feed's SUMMARY is e.g. "LVP-Abfälle (Gelbe Säcke) ()"; only the
        # first word identifies the waste type (matches the legacy source's
        # own ``d[1].split(" ")[0]``).
        clean=lambda label: label.split(" ")[0],
    )
