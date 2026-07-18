"""Abfallwirtschaft Stadt Fürth.

Demonstrates: a static, param-built ICS GET that still needs a custom
``parse`` override, because the feed needs two things ``parsers.IcsParser``
does not expose:

* the provider emits non-ASCII UID lines that break the ICS parser unless
  the umlauts are transliterated first (no hook in the standard parser for
  pre-processing the raw ICS text), and
* the summary needs ``split_at="/"`` (one VEVENT covers several bin types
  separated by "/"), an ``ICS()`` option ``IcsParser`` does not currently
  forward.

Both are exactly the shared-component gap called out in the service probe
report: this module works around it locally by calling ``service.ICS.ICS``
directly (the same class ``IcsParser`` wraps) with the option it needs.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://abfallwirtschaft.fuerth.eu/termine.php"

_UMLAUT_MAP = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"))


def _fix_uid_umlauts(ics_text: str) -> str:
    """Transliterate umlauts on UID lines; the ICS parser chokes otherwise."""
    lines = []
    for line in ics_text.splitlines():
        if line.startswith("UID"):
            for src, dest in _UMLAUT_MAP:
                line = line.replace(src, dest)
        lines.append(line)
    return "\n".join(lines) + "\n"


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

    PARAMS = (text_field("id", "Location ID"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Look up your address on https://abfallwirtschaft.fuerth.eu/ and copy "
            "the numeric id from the calendar export link it offers."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda id, **_: f"{_API_URL}?icalexport={id}")

    def parse(self, response, source=None):
        return ICS(split_at="/").convert(_fix_uid_umlauts(response.text))

    transform = ICSTransformer(
        type_value_map={
            "Restabfall": GENERAL_WASTE,
            "Biotonne": ORGANIC,
            "Gelber Sack": RECYCLABLES,
            "Altpapier": PAPER,
        }
    )

    def __init__(self, id: int):
        super().__init__(id=id)
