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

_SERVLET = (
    "https://extdienste01.koblenz.de/WasteManagementAhrweiler/WasteManagementServlet"
)


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaftsbetrieb Landkreis Ahrweiler"
    DESCRIPTION = "Bin collection service from Kreis Ahrweiler/Germany"
    URL = "https://www.meinawb.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Oberzissen": {
            "city": "Oberzissen",
            "street": "Lindenstrasse",
            "house_number": "1",
        },
        "Niederzissen": {
            "city": "Niederzissen",
            "street": "Brohltalstrasse",
            "house_number": "189",
        },
        "Bad Neuenahr": {
            "city": "Bad Neuenahr-Ahrweiler",
            "street": "Hauptstrasse",
            "house_number": "91",
            "address_suffix": "A",
        },
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {
            "city": "Oberzissen",
            "street": "Keine Strasse",
            "house_number": "1",
        },
    }

    PARAMS = (
        city(),
        street(),
        house_number(),
        text_field("address_suffix", "Hausnummerzusatz", default=""),
    )

    # The Athos wizard: choose the Ort (which loads its streets), submit the
    # full address, then download the calendar. Around the turn of the year
    # the first page offers one calendar per period ("Zeitraum"); each is
    # fetched.
    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        iterate_field="Zeitraum",
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda city, **_: {"Ort": city, "Strasse": ""},
            },
            {
                "submit_action": "forward",
                "fields": lambda city, street, house_number, address_suffix, **_: {
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Hausnummerzusatz": address_suffix,
                },
            },
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
    parse = parsers.EachResponse(parsers.IcsParser())
    # Restabfall, Bioabfall, Altpapier and Verpackungen resolve via the shared
    # vocabulary. The commercial PLUS bin carries its rhythm after "**"
    # ("... ** zweiwoechentlich"), which is cut before mapping and kept as the
    # description.
    transform = ICSTransformer(
        clean=lambda label: label.split("**")[0],
        type_value_map={
            "Restabfall Gewerbe / PLUS-Tonne": wt.GENERAL_WASTE,
            "Gruenabfall / Weihnachtsbaeume": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
