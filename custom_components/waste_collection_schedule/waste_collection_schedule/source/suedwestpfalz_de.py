"""Landkreis Südwestpfalz (lksuedwestpfalz.de).

The district's collection calendar is the Athos "WasteManagementServlet"
wizard on the same ``com.athos.nl.mvc.abfterm`` model that ubzzw_de runs, so
this module is only the servlet URL, the step data and the type map: the shared
``AthosWasteManagementRetriever`` does the wizard.

Flow (walked live): GET the servlet, POST ``CITYCHANGED`` with the address
(``Ort`` selects the village, which decides the calendar: several villages
share a postcode but not a schedule), ``STREETCHANGED``, ``forward`` to the
``Terminliste`` page, then ``filedownload_ICAL`` for the ICS. The servlet
normalises a plain space in a street name to the non-breaking space its
``<select>`` uses ("Am Bahndamm" is accepted), and a house-number addition
("61 A") is a separate ``Hausnummerzusatz`` field.

An unknown street or house number is not rejected: the final POST answers 200
with the HTML form instead of an ICS, which ``AthosCalendarRequired`` turns
into an argument error.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.service.AthosWasteManagement import (
    AthosCalendarRequired,
)
from waste_collection_schedule.transformers import ICSTransformer

_SERVLET = "https://abfallwirtschaft.lksuedwestpfalz.de/WasteManagementSuedwestpfalz/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "Landkreis Südwestpfalz"
    DESCRIPTION = "Source for waste collection in the Landkreis Südwestpfalz."
    URL = "https://www.lksuedwestpfalz.de"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Fischbach, Daniel-Theysohn-Straße 15": {
            "city": "Fischbach",
            "street": "Daniel-Theysohn-Straße",
            "house_number": "15",
        },
        "Bruchweiler-Bärenbach, Hauptstraße 61 A": {
            "city": "Bruchweiler-Baerenbach",
            "street": "Hauptstraße",
            "house_number": "61",
            "address_suffix": "A",
        },
        "Dahn, Aeussermuehlstrasse 1": {
            "city": "Dahn",
            "street": "Äußermühlstraße",
            "house_number": 1,
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {
            "city": "Dahn",
            "street": "Nichtvorhanden",
            "house_number": "1",
        },
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "de": (
            "Ort, Straße und Hausnummer wie im Abfuhrkalender unter "
            "https://abfallwirtschaft.lksuedwestpfalz.de/WasteManagementSuedwestpfalz/WasteManagementServlet "
            "angeben. Der Ort steht ohne Umlaute (z. B. Bruchweiler-Baerenbach). "
            "Ein Hausnummernzusatz (z. B. A) kommt in 'Address suffix'."
        ),
        "en": (
            "Enter the village, street and house number exactly as the "
            "calendar at "
            "https://abfallwirtschaft.lksuedwestpfalz.de/WasteManagementSuedwestpfalz/WasteManagementServlet "
            "lists them. Village names use no umlauts (e.g. "
            "Bruchweiler-Baerenbach). Put a house number addition (e.g. A) "
            "in 'Address suffix'."
        ),
    }

    PARAMS = (
        city(),
        street(),
        house_number(),
        text_field("address_suffix", "Address suffix", default=""),
    )

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda city, street, house_number, address_suffix="", **_: {
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Hausnummerzusatz": address_suffix or "",
                },
            },
            {"submit_action": "STREETCHANGED"},
            {"submit_action": "forward"},
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
                },
                "validate": AthosCalendarRequired(
                    "city", "street", "house_number", "address_suffix"
                ),
            },
        ],
    )
    parse = parsers.IcsParser()

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]
    transform = ICSTransformer(
        type_value_map={
            "restmuell": wt.GENERAL_WASTE,
            "biotonne": wt.ORGANIC,
            "papier": wt.PAPER,
            "gelber sack": wt.RECYCLABLES,
        },
    )
