"""Aarberg (Bern, Switzerland).

Demonstrates ``IcsSessionRetriever`` for a calendar page that hands out its ICS
link only once a zone is chosen: the first step reads the page's own zone list
(``<select id="zone_id">``, whose options carry the id as their value and the
zone name with a trailing collection count as their text) and resolves the
configured zone to its id, the second loads the page filtered to that zone and
reads the download link out of it, and the feed request follows that link. The
link is a rolling calendar rather than a per-year one, hence
``lookahead_month=None``.
"""

import re
from typing import Any, ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.service.ICS import (
    IcsFeedsParser,
    IcsSessionRetriever,
    resolve_select_option,
)
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.aarberg.ch/de/abfallwirtschaft/abfallkalender/"

# An option's text is the zone plus its collection count: "Aarberg (12)".
_COUNT_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")


def _zone_id(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """The configured zone's id, read off the page's own zone list."""
    soup = BeautifulSoup(response.text, "html.parser")
    select = soup.find("select", {"id": "zone_id"})
    if select is None:
        raise SourceArgumentException(
            "zone", "the calendar page no longer offers a zone list"
        )
    zones: dict[str, str] = {}
    for option in select.find_all("option"):
        value = option.get("value")
        if value:
            zones[_COUNT_SUFFIX.sub("", option.get_text().strip())] = str(value)
    name = resolve_select_option("zone", str(context["zone"]), list(zones))
    return {"zone_id": zones[name]}


def _zone_calendar(zone_id: str, **_: Any) -> "dict[str, str]":
    return {"zone_id": zone_id}


def _ical_link(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """The zone's calendar download link, resolved against the page."""
    soup = BeautifulSoup(response.text, "html.parser")
    link = soup.select_one("div#icalTermine a")
    if link is None or not isinstance(link.get("href"), str):
        raise SourceArgumentException(
            "zone", "the calendar page offers no download link for this zone"
        )
    return {"ical_url": urljoin(_API_URL, str(link["href"]))}


@final
class Source(BaseSource):
    TITLE = "Aarberg"
    DESCRIPTION = "Source for Aarberg, Switzerland."
    URL = "https://www.aarberg.ch/"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Aarberg": {"zone": "Aarberg"},
        "Grafenmoos": {"zone": "Grafenmoos"},
        "Leimern": {"zone": "Leimern"},
        "Mülital": {"zone": "Mülital"},
        "Spins": {"zone": "Spins"},
        "Zälgli": {"zone": "Zälgli"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown zone": {"zone": "Nirgendwo"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "The zone/area within Aarberg, e.g. Aarberg, Grafenmoos, Leimern, "
            "Mülital, Spins, Zälgli."
        ),
        "de": (
            "Die Zone innerhalb von Aarberg, z.B. Aarberg, Grafenmoos, Leimern, "
            "Mülital, Spins, Zälgli."
        ),
        "fr": (
            "La zone à Aarberg, par exemple Aarberg, Grafenmoos, Leimern, "
            "Mülital, Spins, Zälgli."
        ),
        "it": (
            "La zona ad Aarberg, ad esempio Aarberg, Grafenmoos, Leimern, "
            "Mülital, Spins, Zälgli."
        ),
    }

    PARAMS = (text_field("zone", "Zone"),)

    retrieve = IcsSessionRetriever(
        steps=[
            {"url": _API_URL, "extract": _zone_id},
            {"url": _API_URL, "params": _zone_calendar, "extract": _ical_link},
        ],
        feed_url=lambda ical_url, **_: ical_url,
        lookahead_month=None,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        type_value_map={
            "Hauskehricht": wt.GENERAL_WASTE,
            "Grüngut": wt.ORGANIC,
            "Papier und Karton": wt.PAPER,
            "Häckseldienst": wt.GARDEN_WASTE,
        }
    )
