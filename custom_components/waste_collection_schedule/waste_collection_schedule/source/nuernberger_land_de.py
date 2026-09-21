"""Abfallwirtschaft Nürnberger Land (nuernberger-land.de).

Demonstrates: the plain-vanilla ICS shape plus one extended ``IcsParser``
option — a single static GET keyed by an opaque location id, with
``split_at="/"`` because one VEVENT covers several bin types separated by
"/". HttpGetRetriever + the extended IcsParser + ICSTransformer do all the
work; this module only supplies the URL template and the waste-type map.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://abfuhrkalender.nuernberger-land.de/waste_calendar"
_FILTER = "rm:bio:p:dsd:poison"
_GROUP_RE = re.compile(r'id="tg_group_id"\s+value="(\d+)"')


def _group_prefixed_id(response, source) -> str:
    """Prefix a bare section id with its tour group, as the calendar page shows it."""
    match = _GROUP_RE.search(response.text)
    if not match:
        raise SourceArgumentNotFound("id", source.params["id"])
    return f"{match.group(1)}-{source.params['id']}"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Nürnberger Land"
    DESCRIPTION = "Source for Nürnberger Land"
    URL = "https://nuernberger-land.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Schwarzenbruck, Mühlbergstraße": {"id": "40-16952001"},
        "Burgthann, Brunhildstr": {"id": "39-14398001"},
        "Kirchensittenbach, Erlenweg": {"id": "12-15192001"},
        # Bare section id from before the feed required the tour-group prefix.
        "Schwarzenbruck, Mühlbergstraße (ohne Gruppe)": {"id": 16952001},
    }

    PARAMS = (location_id(field="id"),)

    # The feed wants "<tour group>-<section>". An id that already has the
    # group prefix is used as is; an older bare section id has its group looked
    # up on the calendar page.
    retrieve = TwoStepRetriever(
        direct_key=lambda source: (
            str(source.params["id"]) if "-" in str(source.params["id"]) else None
        ),
        lookup_url=lambda id, **_: f"{_API_URL}/get_calendar_data?id={id}&cid=",
        extract=_group_prefixed_id,
        schedule_url=lambda key, **_: f"{_API_URL}/ical?id={key}&filter={_FILTER}",
    )
    parse = parsers.IcsParser(split_at="/")
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Biotonne": wt.ORGANIC,
            "Gelber Sack": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Giftmobil": wt.HAZARDOUS,
        }
    )
