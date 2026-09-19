"""Abfallwirtschaftsbetrieb Emsland (awb-emsland.de).

Demonstrates: the Athos "WasteManagementServlet" wizard's plain German
shape (one field-setting step, one container-selection step, one download
step; see the ``awn_de`` docstring), applied to a near-identical deployment
under a different host/path/``ApplicationName``.
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
from waste_collection_schedule.transformers import ICSTransformer

_SERVLET = "https://portal.awb-emsland.de/WasteManagementEmsland/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaftsbetrieb Emsland"
    DESCRIPTION = "Source for AWB Emsland."
    URL = "https://www.awb-emsland.de"
    COUNTRY = "de"

    # A wrong street/house number yields an empty Athos schedule; surface it
    # as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Andervenne Am Gallenberg": {
            "city": "Andervenne",
            "street": "Am Gallenberg",
            "house_number": "2",
        },
        "Neubörger Aschendorfer Straße 1 A": {
            "city": "Neubörger",
            "street": "Aschendorfer Straße",
            "house_number": 1,
            "address_suffix": "A",
        },
        "Lähden Ahornweg 15": {
            "city": "Lähden",
            "street": "Ahornweg",
            "house_number": 15,
        },
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
        iterate_field="Zeitraum",
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda city, street, house_number, address_suffix="", **_: {
                    "Ort": city,
                    "Strasse": street,
                    "Hausnummer": str(house_number),
                    "Hausnummerzusatz": address_suffix,
                },
            },
            {
                "submit_action": "forward",
                "fields": lambda **_: {
                    f"ContainerGewaehlt_{i}": "on" for i in range(1, 11)
                },
            },
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.emsland.AbfuhrTerminModel",
                },
            },
        ],
    )
    parse = parsers.EachResponse(parsers.IcsParser())
    transform = ICSTransformer(
        type_value_map={
            "Restabfallbehaelter": wt.GENERAL_WASTE,
            "Papierbehaelter": wt.PAPER,
            "Wertstoffbehaelter": wt.RECYCLABLES,
            "Bioabfallbehaelter": wt.ORGANIC,
        }
    )
