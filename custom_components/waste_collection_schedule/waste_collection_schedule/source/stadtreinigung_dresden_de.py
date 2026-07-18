"""Stadtreinigung Dresden (dresden.de).

Demonstrates: a static, param-built ICS GET whose date-range query params are
computed fresh at request time (today .. today + 365 days) rather than being
literal, and whose feed needs two things ``parsers.IcsParser`` does not
expose: rejecting a bad ``standort`` (the endpoint answers 200 with a non-ICS
body instead of an HTTP error) and dropping a housekeeping "calendar ends
soon" VEVENT that carries no waste type at all. Both are handled in a small
source-defined ``parse`` around the plain ``ICS()`` service class; retrieval
itself is the standard ``HttpGetRetriever``.
"""

import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_ICAL_URL = (
    "https://stadtplan.dresden.de/project/cardo3Apps/IDU_DDStadtplan/abfall/ical.ashx"
)

# Housekeeping VEVENT the feed emits once the published window nears its end;
# it carries no waste type and must be dropped rather than surfaced.
_END_OF_CALENDAR_NOTICE = "abfallkalender endet bald"


def _date_range_params(standort) -> dict:
    today = datetime.date.today()
    return {
        "STANDORT": standort,
        "DATUM_VON": today.strftime("%d.%m.%Y"),
        "DATUM_BIS": (today + datetime.timedelta(days=365)).strftime("%d.%m.%Y"),
    }


@final
class Source(BaseSource):
    TITLE = "Stadtreinigung Dresden"
    DESCRIPTION = "Source for Stadtreinigung Dresden waste collection."
    URL = "https://www.dresden.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Neumarkt 6": {"standort": 80542},
    }

    PARAMS = (location_id("standort"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://www.dresden.de/apps_ext/AbfallApp/wastebins and search "
            "for your address. Then download the PDF calendar: the URL will "
            "contain '?STANDORT=<number>'. Use that number as the location ID."
        ),
        "de": (
            "Öffne https://www.dresden.de/apps_ext/AbfallApp/wastebins und suche "
            "deine Adresse. Lade den PDF-Kalender herunter: die URL enthält "
            "'?STANDORT=<Zahl>'. Diese Zahl ist die Standort-ID."
        ),
    }

    retrieve = HttpGetRetriever(
        url=_ICAL_URL, params=lambda standort, **_: _date_range_params(standort)
    )

    def parse(self, response, source=None):
        if not response.text.startswith("BEGIN:VCALENDAR"):
            raise SourceArgumentNotFound(
                "standort",
                self.params["standort"],
                "no calendar found for this location, please check this value is correct.",
            )
        events = ICS(regex=r"^Leerung (.*)", split_at=r", ").convert(response.text)
        return [
            (date, title)
            for date, title in events
            if title.strip().lower() != _END_OF_CALENDAR_NOTICE
        ]

    transform = ICSTransformer(
        type_value_map={
            "bio-tonne": ORGANIC,
            "blaue tonne": PAPER,
            "gelbe tonne": RECYCLABLES,
            "restabfall": GENERAL_WASTE,
        }
    )

    def __init__(self, standort: int):
        super().__init__(standort=standort)
