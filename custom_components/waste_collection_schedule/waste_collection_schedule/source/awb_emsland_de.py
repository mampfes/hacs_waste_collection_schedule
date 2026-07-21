"""Abfallwirtschaftsbetrieb Emsland (awb-emsland.de).

Demonstrates: the Athos "WasteManagementServlet" wizard's plain German
shape (one field-setting step, one container-selection step, one download
step; see the ``awn_de`` docstring), applied to a near-identical deployment
under a different host/path/``ApplicationName``.

Known gap (documented, not reproduced here, matching the precedent set by
``bielefeld_de``): the legacy source additionally scraped every ``Zeitraum``
(calendar-year) hidden input the initial page offered and re-ran the whole
three-step wizard once per year, merging events across all of them.
``AthosWasteManagementRetriever`` runs the wizard's steps exactly once per
fetch, using whatever single ``Zeitraum`` default the scraped hidden state
carries (the same fallback the legacy source used when it found no
``Zeitraum`` inputs at all).
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
            "house_number": "1",
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
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restabfallbehaelter": GENERAL_WASTE,
            "Papierbehaelter": PAPER,
            "Wertstoffbehaelter": RECYCLABLES,
            "Bioabfallbehaelter": ORGANIC,
        }
    )

    def __init__(
        self,
        city: str,
        street: str,
        house_number: int | str,
        address_suffix: str = "",
    ):
        super().__init__(
            city=city,
            street=street,
            house_number=house_number,
            address_suffix=address_suffix,
        )
