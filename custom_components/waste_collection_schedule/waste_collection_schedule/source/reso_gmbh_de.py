"""RESO GmbH (reso-gmbh.de).

Demonstrates: a static, param-built ICS POST whose feed is generated one
calendar year at a time. Near year-end the provider's own calendar app also
shows the first weeks of the following year, so this mirrors that by fetching
the next year too (best-effort: swallowed if the following year isn't
published yet) once the current month reaches December. No configured
retriever expresses "POST, then conditionally POST again for a second year",
hence a source-defined retrieve()/parse() pair; parsing itself is the plain
IcsParser with the same ``split_at`` the legacy ``ICS()`` call used.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://reso-gmbh.abfallkalender.services/php/Kalender-2-ICS.php"

_TOWNS = (
    "Bad-König",
    "Brensbach",
    "Breuberg",
    "Brombachtal",
    "Erbach",
    "Fränkisch-Crumbach",
    "Höchst",
    "Lützelbach",
    "Michelstadt",
    "Mossautal",
    "Oberzent",
    "Reichelsheim",
)


def _post_args(ort: str, ortsteil: str, year: int) -> dict:
    return {
        "Ort": ort,
        "Ortsteil": ortsteil,
        "Jahr": year,
        "art": 1,
        "downOderurl2": "Semikolon",
    }


@final
class Source(BaseSource):
    TITLE = "RESO"
    DESCRIPTION = "Source for RESO."
    URL = "https://reso-gmbh.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Reichelsheim Kerngemeinde": {
            "ort": "Reichelsheim",
            "ortsteil": "Kerngemeinde",
        },
    }

    REGIONS = tuple(region(town, ort=town) for town in _TOWNS)

    PARAMS = (
        municipality(field="ort"),
        district(field="ortsteil"),
    )

    def retrieve(self, source):
        ort = source.params["ort"]
        ortsteil = source.params["ortsteil"]
        now = datetime.now()

        responses = [
            source.session.post(_API_URL, data=_post_args(ort, ortsteil, now.year))
        ]
        if now.month == 12:
            try:
                extra = source.session.post(
                    _API_URL, data=_post_args(ort, ortsteil, now.year + 1)
                )
                extra.raise_for_status()
                responses.append(extra)
            except Exception:
                pass
        return responses

    def parse(self, raw, source):
        ics_parser = IcsParser(split_at=r" \+ ")
        entries = []
        for response in raw:
            response.raise_for_status()
            entries.extend(ics_parser(response, source))
        return entries

    transform = ICSTransformer(
        type_value_map={
            "restmüll": GENERAL_WASTE,
            "biotonne": ORGANIC,
            "papiertonne": PAPER,
            "gelber-sack": RECYCLABLES,
        }
    )

    def __init__(self, ort: str, ortsteil: str):
        super().__init__(ort=ort, ortsteil=ortsteil)
