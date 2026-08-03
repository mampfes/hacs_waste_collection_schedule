"""Abfallwirtschaft Stadt Fürth.

Demonstrates: a static, param-built ICS GET, fully declarative. The provider
puts one VEVENT per collection day and lists several bin types in a single
summary separated by "/", which ``IcsParser``'s ``split_at`` handles.

The feed has historically emitted UID lines containing umlauts, which older
icalendar releases refuse to parse. That is now repaired inside the shared
converter (``service.ICS._ascii_fold_uids``), so every ICS provider is covered
rather than this one alone.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://abfallwirtschaft.fuerth.eu/termine.php"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Stadt Fürth"
    DESCRIPTION = "Source for Stadt Fürth."
    URL = "https://abfallwirtschaft.fuerth.eu/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Mühltalstrasse 4": {"id": 96983001},
        "Carlo-Schmid-Strasse 27": {"id": 96975001},
    }

    PARAMS = (location_id(field="id"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Look up your address on https://abfallwirtschaft.fuerth.eu/ and copy "
            "the numeric id from the calendar export link it offers."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda id, **_: f"{_API_URL}?icalexport={id}")
    parse = parsers.IcsParser(split_at="/")

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": GENERAL_WASTE,
            "Biotonne": ORGANIC,
            "Gelber Sack": RECYCLABLES,
            "Altpapier": PAPER,
        }
    )
