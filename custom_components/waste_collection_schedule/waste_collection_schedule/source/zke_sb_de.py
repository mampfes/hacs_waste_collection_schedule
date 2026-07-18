"""ZKE Saarbrücken (zke-sb.de).

Athos "WasteManagementServlet" wizard: CITYCHANGED, STREETCHANGED, a
container-selection ``forward``, then download.

Known gap (documented, not reproduced here): the legacy source re-scrapes
hidden inputs after every step, and a live comparison found one field that
genuinely changes along the way -- ``ApplicationName`` starts as the
address-wizard's own model and becomes
``com.athos.kd.saarbruecken.abfuhrtermine.AbfuhrTerminModel`` once the
"Terminliste" page is reached after ``forward``. The retriever never
re-scrapes, so that value is hardcoded on the download step instead of
picked up dynamically (confirmed live: 75 collections, matching the legacy
source's "Harthweg 7" TEST_CASE exactly).
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = "https://info.zke-sb.de/WasteManagementSaarbruecken/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "ZKE Saarbrücken"
    DESCRIPTION = (
        "Source for Zentraler Kommunaler Entsorgungsbetrieb (ZKE) Saarbrücken."
    )
    URL = "https://www.zke-sb.de"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Harthweg": {
            "street": "Harthweg",
            "house_number": 7,
        },
        "Jahnweg": {
            "street": "Jahnweg",
            "house_number": 6,
        },
        "Netzbachtal": {
            "street": "Netzbachtal",
            "house_number": 1,
        },
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
                "fields": lambda street, **_: {"Ort": street[0].upper()},
            },
            {
                "submit_action": "STREETCHANGED",
                "fields": lambda street, **_: {"Strasse": street},
            },
            {
                "submit_action": "forward",
                "fields": lambda house_number, **_: {
                    "Hausnummer": str(house_number),
                    **{f"ContainerGewaehlt_{i}": "on" for i in range(1, 7)},
                },
            },
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.saarbruecken.abfuhrtermine.AbfuhrTerminModel",
                },
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        clean=lambda label: label.split(":")[0].strip(),
        type_value_map={
            "restmuell": GENERAL_WASTE,
            "biomuell": ORGANIC,
            "papiertonne": PAPER,
            "gelbe tonne": RECYCLABLES,
        },
    )

    def __init__(self, street: str, house_number: "str | int"):
        super().__init__(street=street, house_number=house_number)
