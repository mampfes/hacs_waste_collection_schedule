"""UBZ Umwelt- und Servicebetrieb Zweibrücken (ubzzw.com).

Athos "WasteManagementServlet" wizard: CITYCHANGED, then STREETCHANGED (the
legacy source re-scrapes hidden inputs after every step, but a live
comparison found every field except ``Method``/``SubmitAction`` unchanged
across steps, so a single initial scrape plus accumulated state -- the
retriever's normal mechanic -- reproduces it byte-for-byte). "Zeitraum" is
also dropped: the legacy source posts it explicitly, but omitting it
entirely returns identical collections (confirmed live), and the derived
``Ort`` (the street's first letter) mirrors the legacy source exactly.

Known gap (documented, not reproduced here): the legacy source additionally
re-ran the whole wizard for the following year every December
(``Zeitraum=f"Jahresübersicht {year+1}"``), swallowing any error. Since
"Zeitraum" has no effect on the returned calendar (see above), that extra
run always duplicated the same events under the (never varying) label, so
dropping it does not lose collections -- only the incidental duplicate rows
a December fetch used to add.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = (
    "https://leerungen.ubzzw.com/WasteManagementZweibruecken/WasteManagementServlet"
)


@final
class Source(BaseSource):
    TITLE = "UBZ Umwelt- und Servicebetrieb Zweibrücken"
    DESCRIPTION = "Source for UBZ Zweibrücken waste collection."
    URL = "https://www.ubzzw.com"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Vogesenstraße 75": {"street": "Vogesenstraße", "house_number": "75"},
        "Lindenstraße 5": {"street": "Lindenstraße", "house_number": "5"},
    }

    PARAMS = (
        street(),
        house_number(),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda street, house_number, **_: {
                    "Ort": street[0].upper(),
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Hausnummerzusatz": "",
                },
            },
            {"submit_action": "STREETCHANGED"},
            {"submit_action": "forward"},
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
                },
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        clean=lambda label: re.sub(r"\s+\d.*$", "", label).strip(),
        type_value_map={
            "restabfalltonne": GENERAL_WASTE,
            "biotonne": ORGANIC,
            "papiertonne": PAPER,
            "gelbe tonne / gelber sack": RECYCLABLES,
            "problemstoff-sammlung": HAZARDOUS,
        },
    )

    def __init__(self, street: str, house_number: str):
        super().__init__(street=street, house_number=house_number)
