"""Abfallwirtschaft Neckar-Odenwald-Kreis (awn-online.de).

Demonstrates: the Athos "WasteManagementServlet" wizard, the plain German
shape — one field-setting step (city/street/house number), one
container-selection step, one download step. Wired entirely through
``AthosWasteManagementRetriever``; this module only supplies the servlet URL,
the step data and the (empty) waste-type map, exactly like the legacy
source's plain ``Collection(d[0], d[1])`` with no icon map.

The legacy source exposed a boolean per container stream
(``restmuell``/``bioenergietonne``/...) to opt individual streams out. The
pipeline always returns every stream for every waste type (filtering is a
framework/HA concern, not a source one — see ``doc/contributing_source.md``),
so those toggles are dropped and every ``ContainerGewaehlt_N`` is selected.
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

_SERVLET = (
    "https://athos.awn-online.de/WasteManagementNeckarOdenwald/WasteManagementServlet"
)


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Neckar-Odenwald-Kreis"
    DESCRIPTION = "Source for AWN (Abfallwirtschaft Neckar-Odenwald-Kreis)."
    URL = "https://www.awn-online.de"
    COUNTRY = "de"

    # A wrong street/house number yields an empty Athos schedule; surface it
    # as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Adelsheim": {"city": "Adelsheim", "street": "Badstr.", "house_number": 1},
        "Mosbach": {
            "city": "Mosbach",
            "street": "Hauptstr.",
            "house_number": 53,
            "address_suffix": "/1",
        },
        "Billigheim": {
            "city": "Billigheim",
            "street": "Marienhöhe",
            "house_number": 5,
            "address_suffix": "A",
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
                    f"ContainerGewaehlt_{i}": "on" for i in range(1, 8)
                },
            },
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.neckarodenwald.abfuhrtermine.AbfuhrTerminModel",
                },
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer()

    def __init__(
        self,
        city: str,
        street: str,
        house_number: int,
        address_suffix: str = "",
    ):
        super().__init__(
            city=city,
            street=street,
            house_number=house_number,
            address_suffix=address_suffix,
        )
