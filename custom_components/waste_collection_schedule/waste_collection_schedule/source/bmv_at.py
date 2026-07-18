"""Burgenländischer Müllverband (bmv.at).

Demonstrates: the Athos "WasteManagementServlet" wizard's Austrian
(``udb.at``) variant. Same mechanics as the German deployments (initial GET,
scrape hidden state, a sequence of field-setting POSTs, a final download
POST) but a different step shape: each field is set one at a time behind a
``Focus``/``changedEvent`` pair rather than the German
``CITYCHANGED``/``STREETCHANGED``/``forward`` progression, and the final step
must drop the address fields (``remove=``) rather than resend them.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer

_SERVLET = "https://webudb.udb.at/WasteManagementUDB/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "Burgenländischer Müllverband"
    DESCRIPTION = "Source for BMV, Austria"
    URL = "https://www.bmv.at"
    COUNTRY = "at"

    TEST_CASES: ClassVar[dict] = {
        "Allersdorf": {"ort": "ALLERSDORF", "strasse": "HAUSNUMMER", "hausnummer": 9},
        "Bad Sauerbrunn": {
            "ort": "BAD SAUERBRUNN",
            "strasse": "BUCHINGERWEG",
            "hausnummer": 16,
        },
        "Rattersdorf": {
            "ort": "RATTERSDORF",
            "strasse": "SIEBENBRÜNDLGASSE",
            "hausnummer": 30,
        },
    }

    PARAMS = (
        city(field="ort"),
        street(field="strasse"),
        house_number(field="hausnummer"),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        steps=[
            {
                "submit_action": "changedEvent",
                "fields": lambda ort, **_: {
                    "Focus": "Ort",
                    "Ort": ort,
                    "Strasse": "HAUSNUMMER",
                    "Hausnummer": 0,
                },
            },
            {
                "submit_action": "changedEvent",
                "fields": lambda ort, strasse, **_: {
                    "Focus": "Strasse",
                    "Ort": ort,
                    "Strasse": strasse,
                    "Hausnummer": 0,
                },
            },
            {
                "submit_action": "forward",
                "fields": lambda ort, strasse, hausnummer, **_: {
                    "Focus": "Hausnummer",
                    "Ort": ort,
                    "Strasse": strasse,
                    "Hausnummer": hausnummer,
                },
            },
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.udb.AbfuhrTerminModel",
                    "Focus": None,
                    "IsLastPage": "true",
                    "Method": "POST",
                    "PageName": "Terminliste",
                },
                "remove": ("Ort", "Strasse", "Hausnummer"),
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer()

    def __init__(self, ort: str, strasse: str, hausnummer: int):
        super().__init__(ort=ort, strasse=strasse, hausnummer=hausnummer)
