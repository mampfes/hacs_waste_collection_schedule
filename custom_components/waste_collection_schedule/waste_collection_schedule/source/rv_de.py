"""Landkreis Ravensburg (rv.de).

Athos "WasteManagementServlet" wizard, plain German shape with an extra
repeated ``forward`` step: one field-setting step (city/street/house
number), then the wizard advances through the container-selection page
*twice* with an unchanged POST body before the download step (the legacy
source posts ``SubmitAction=forward`` back-to-back without touching the
form state in between, and the live servlet only reaches the calendar page
after both).
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = "https://athos-onlinedienste.rv.de/WasteManagementRavensburgPrivat/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "Landkreis Ravensburg"
    DESCRIPTION = "Source for Landkreis Ravensburg."
    URL = "https://www.rv.de/"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Altshausen Altshauser Weg 1 ": {
            "ort": "Altshausen",
            "strasse": "Altshauser Weg",
            "hnr": 1,
            "hnr_zusatz": "",
        },
        "Hoßkirch, Ob den Gärten 1": {
            "ort": "Hoßkirch",
            "strasse": "Ob den Gärten",
            "hnr": "1",
            "hnr_zusatz": "",
        },
        "Bad Kreznach, Steubenstraße 5645A": {
            "ort": "bAd KrezNach",
            "strasse": "steuBenstraße",
            "hnr": 5645,
            "hnr_zusatz": "A",
        },
    }

    PARAMS = (
        city(field="ort"),
        street(field="strasse"),
        house_number(field="hnr"),
        text_field("hnr_zusatz", "Address suffix", default=""),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda ort, strasse, hnr, hnr_zusatz="", **_: {
                    "Ort": ort,
                    "Strasse": strasse,
                    "Hausnummer": str(hnr),
                    "Hausnummerzusatz": hnr_zusatz,
                },
            },
            {"submit_action": "forward"},
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
        type_value_map={
            "restmuelltonne": GENERAL_WASTE,
            "biotonne": ORGANIC,
            "papiertonne": PAPER,
            "gelbe tonne": RECYCLABLES,
        }
    )

    def __init__(
        self, ort: str, strasse: str, hnr: "str | int", hnr_zusatz: "str | int" = ""
    ):
        super().__init__(ort=ort, strasse=strasse, hnr=hnr, hnr_zusatz=hnr_zusatz)
