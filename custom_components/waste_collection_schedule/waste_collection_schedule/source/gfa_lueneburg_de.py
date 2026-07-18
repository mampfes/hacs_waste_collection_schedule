"""GFA Lüneburg (gfa-lueneburg.de).

Demonstrates: the Athos "WasteManagementServlet" wizard's plain German
``CITYCHANGED``/``STREETCHANGED``/``forward`` progression (see the
``bmv_at`` docstring), with an explicit ``Zeitraum`` (calendar-year) field
carried through the address steps and dropped before the final download,
exactly like the legacy source's own ``del args[...]`` cleanup.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = "https://portal.gfa-lueneburg.de:8443/WasteManagementLueneburg/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "GFA Lüneburg"
    DESCRIPTION = "Source for GFA Lüneburg."
    URL = "https://www.gfa-lueneburg.de/"
    COUNTRY = "de"

    HOWTO: ClassVar[dict] = {
        "en": (
            "Make sure the address exactly matches the one auto-completed by "
            "the website form: "
            "https://www.gfa-lueneburg.de/service/abfuhrkalender.html"
        ),
        "de": (
            "Stellen Sie sicher, dass die Adresse genau der entspricht, die "
            "vom Website-Formular automatisch vervollständigt wird: "
            "https://www.gfa-lueneburg.de/service/abfuhrkalender.html"
        ),
    }

    TEST_CASES: ClassVar[dict] = {
        "Dahlem Hauptstr. 7": {
            "city": "Dahlem",
            "street": "Hauptstr.",
            "house_number": 7,
        },
        "Wendish Evern Kückenbrook 5 A": {
            "city": "Wendish Evern",
            "street": "Kückenbrook",
            "house_number": "5 A",
        },
    }

    PARAMS = (
        city(),
        street(),
        house_number(),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={
            "SubmitAction": "wasteDisposalServices",
            "InFrameMode": "FALSE",
        },
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda city, street, house_number, **_: {
                    "Zeitraum": f"Jahresübersicht {datetime.now().year}",
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Method": "POST",
                    "Focus": "Ort",
                },
            },
            {
                "submit_action": "STREETCHANGED",
                "fields": lambda city, street, house_number, **_: {
                    "Zeitraum": f"Jahresübersicht {datetime.now().year}",
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Method": "POST",
                    "Focus": "Strasse",
                },
            },
            {"submit_action": "forward"},
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.lueneburg.AbfuhrTerminModel",
                    "IsLastPage": "true",
                    "Method": "POST",
                    "PageName": "Terminliste",
                },
                "remove": ("Zeitraum", "Ort", "Strasse", "Hausnummer"),
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restabfallbehaelter": GENERAL_WASTE,
            "Restmuell": GENERAL_WASTE,
            "Papiertonne": PAPER,
            "Gelber Sack": RECYCLABLES,
            "Gruenabfall": GARDEN_WASTE,
            "Biotonne": ORGANIC,
            "Sperrmuell Altmetall": BULKY_WASTE,
        }
    )

    def __init__(self, city: str, street: str, house_number: int | str):
        super().__init__(city=city, street=street, house_number=house_number)
