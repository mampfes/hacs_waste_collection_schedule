import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalMultiIcsParser,
    RiSKommunalMultiIcsRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a RiSKommunal municipality with one fixed calendar (Gelber
# Sack) plus three independently zoned calendars (Restmüll/Biomüll/Altpapier),
# each zone selecting a different "do" id from a lookup table. Unlike
# rohrbach_lafnitz_at, each feed's own ICS SUMMARY already carries a usable
# waste-type label, so no per-feed label reassignment is needed here -- only
# the *set* of feeds to fetch is data-dependent (the configured zone numbers),
# expressed with RiSKommunalMultiIcsRetriever's ``zone_feeds``. The zoned
# feeds suffix their SUMMARY with the zone (e.g. "Restmüllzone 1", "Biomüll
# Zone 4"), which a bare type_value_map could not exhaustively enumerate;
# stripping the suffix first (as imst_at does for its own zone suffix) lets
# the base label resolve against the shared vocabulary.
_ZONE_SUFFIX_RE = re.compile(r"\s*zone\s*\d+\s*$", re.IGNORECASE)


def _clean(label: str) -> str:
    return _ZONE_SUFFIX_RE.sub("", label.strip()).strip()


_BASE_URL = "https://www.badaussee.at"
_GNR = "3138"

_GELBER_SACK_DO = "MjI1MjYyNTgx"

# "do" ids for the zoned calendars, keyed by the config-flow field name that
# selects them, then by the configured zone number.
_ZONE_DO: dict[str, dict[str, str]] = {
    "restmuell_zone": {
        "1": "MjI1MjYyNTQw",
        "2": "MjI1MjYyNTY4",
        "3": "MjI1MjYyNTY5",
        "4": "MjI1MjYyNTcw",
        "5": "MjI1MjYyNTcx",
        "6": "MjI1MjYyNTcy",
    },
    "biomuell_zone": {
        "1": "MjI1MjYyNTcz",
        "2": "MjI1MjYyNTc0",
        "3": "MjI1MjYyNTc1",
        "4": "MjI1MjYyNTc2",
    },
    "altpapier_zone": {
        "1": "MjI1MjYyNTc3",
        "2": "MjI1MjYyNTc4",
        "3": "MjI1MjYyNTc5",
        "4": "MjI1MjYyNTgw",
    },
}


@final
class Source(BaseSource):
    TITLE = "Bad Aussee"
    DESCRIPTION = "Source for Bad Aussee, Austria."
    URL = _BASE_URL
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {
        "Zone 1": {
            "restmuell_zone": "1",
            "biomuell_zone": "1",
            "altpapier_zone": "1",
        },
        "Zone 4": {
            "restmuell_zone": "4",
            "biomuell_zone": "4",
            "altpapier_zone": "4",
        },
    }

    PARAMS = (
        text_field("restmuell_zone", "Residual Waste Zone", optional=True),
        text_field("biomuell_zone", "Organic Waste Zone", optional=True),
        text_field("altpapier_zone", "Paper Waste Zone", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your zone number for residual waste, organic waste and paper "
            "on the Bad Aussee waste calendar; leave a field blank to skip that "
            "calendar. The Gelber Sack calendar is always included."
        ),
        "de": (
            "Ermitteln Sie Ihre Zonennummer für Restmüll, Biomüll und Altpapier "
            "im Bad Ausseer Abfallkalender; ein Feld leer lassen, um diesen "
            "Kalender zu überspringen. Der Gelbe-Sack-Kalender wird immer "
            "berücksichtigt."
        ),
    }

    # Always include the fixed Gelber Sack calendar, then add whichever zone
    # calendars the user configured (an unrecognised/blank zone is silently
    # skipped, matching the legacy behaviour).
    retrieve = RiSKommunalMultiIcsRetriever(
        base_url=_BASE_URL, gnr=_GNR, do_ids=[_GELBER_SACK_DO], zone_feeds=_ZONE_DO
    )
    parse = RiSKommunalMultiIcsParser()

    # Once the zone suffix is stripped, Gelber Sack, Restmüll, Biomüll and
    # Altpapier are all classified by the shared vocabulary; no explicit
    # type_value_map entry is needed.
    transform = ICSTransformer(clean=_clean)
