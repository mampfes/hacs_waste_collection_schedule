"""mags Mönchengladbacher Abfall-, Grün- und Straßenbetriebe AöR (mags.de).

Demonstrates: a static ICS GET whose raw body needs cleaning before it's
parseable at all — the feed emits non-ASCII characters inside the ``UID``
field (breaks strict ICS UID grammar) and a stray ``// GEM`` comment on data
lines. ``HttpGetRetriever`` fetches the raw body unmodified (a retriever must
not inspect/parse it); ``_CleanedIcsParser`` does the line-by-line cleanup the
legacy ``fetch()`` did, then delegates to the same ``service.ICS.ICS``
converter every other ICS source uses (``split_at="/"`` for the combined
rounds). ``ICSTransformer`` does the rest.
"""

import datetime
from typing import TYPE_CHECKING, ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    ELECTRONICS,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

if TYPE_CHECKING:
    from waste_collection_schedule.retrievers import Response

_API_URL = "https://mags.de/ics/icscal.php"


class _CleanedIcsParser:
    """Strip mags.de's non-ASCII UIDs and stray "// GEM" comment before parsing.

    Mirrors the legacy ``fetch()``'s line-by-line cleanup exactly: only ``UID``
    lines get the umlaut substitution (the rest of the calendar is fine as
    UTF-8), every line has "// GEM" stripped, then the cleaned body is handed
    to the shared ``ICS`` converter.
    """

    def __init__(self, split_at: str | None = None):
        self._ics = ICS(split_at=split_at)

    def __call__(
        self, response: "Response", source: "BaseSource | None" = None
    ) -> list[tuple[datetime.date, str]]:
        cleaned_lines: list[str] = []
        for line in response.text.splitlines():
            if line.startswith("UID"):
                line = line.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
            cleaned_lines.append(line.replace("// GEM", ""))
        return self._ics.convert("\n".join(cleaned_lines))


@final
class Source(BaseSource):
    TITLE = "mags Mönchengladbacher Abfall-, Grün- und Straßenbetriebe AöR"
    DESCRIPTION = "Source for Stadt Mönchengladbach"
    URL = "https://mags.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Schlossacker 43": {"street": "Schlossacker", "number": 43, "turnus": 2},
        "Azaleenweg 24": {"street": "Azaleenweg", "number": 24, "turnus": 2},
    }

    PARAMS = (
        street("street"),
        house_number("number"),
        text_field("turnus", label="Turnus", default="2"),
    )

    retrieve = HttpGetRetriever(
        url=_API_URL,
        params=lambda street, number, turnus, **_: {
            "building_number": number,
            "building_number_addition": "",
            "street_name": street,
            "start_month": 1,
            "end_month": 12,
            "start_year": datetime.datetime.now().year,
            "end_year": datetime.datetime.now().year,
            "turnus": turnus,
        },
    )
    parse = _CleanedIcsParser(split_at="/")
    transform = ICSTransformer(
        type_value_map={
            "Restmüll (Grau)": GENERAL_WASTE,
            "Bioabfall (Braun)": ORGANIC,
            "Verpackungen (Gelb)": RECYCLABLES,
            "Altpapier (Blau)": PAPER,
            "Papiermobil": PAPER,
            "Grünschnitt": GARDEN_WASTE,
            "Elektrokleingeräte-Sammlung": ELECTRONICS,
        }
    )

    def __init__(self, street: str, number: str | int, turnus: str | int = 2):
        super().__init__(street=street, number=number, turnus=turnus)
