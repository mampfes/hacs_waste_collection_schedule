"""Abfallwirtschaft Pforzheim (abfallwirtschaft-pforzheim.de).

Demonstrates: the Athos "WasteManagementServlet" wizard's plain German
shape (one field-setting step, one container-selection step, one download
step; see the ``awn_de`` docstring), with the quirk that this deployment has
no separate city field: ``Ort`` is derived from the street name's first
letter (``street[0].upper()``), exactly as the legacy source computed it.

Known gap (documented, not reproduced here, matching the precedent set by
``bielefeld_de``): the legacy source additionally re-fetched a second
calendar year (``Zeitraum: "Jahresübersicht <year+1>"``) when run in
December, merging both years' events. ``AthosWasteManagementRetriever``
runs the wizard's steps exactly once per fetch, so that December-only
second pass is not reproduced; the single fetch already covers the current
Jahresübersicht.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_SERVLET = "https://onlineservices.abfallwirtschaft-pforzheim.de/WasteManagementPforzheim/WasteManagementServlet"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Pforzheim"
    DESCRIPTION = "Source for Abfallwirtschaft Pforzheim."
    URL = "https://www.abfallwirtschaft-pforzheim.de"
    COUNTRY = "de"

    # A wrong street/house number yields an empty Athos schedule; surface it
    # as an error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Abnobstraße": {
            "street": "Abnobastraße",
            "house_number": 3,
            "address_suffix": "",
        },
        "Im Buchbusch": {
            "street": "Im Buchbusch",
            "house_number": 12,
        },
        "Eisenbahnstraße": {
            "street": "Eisenbahnstraße",
            "house_number": 29,
            "address_suffix": "-33",
        },
    }

    PARAMS = (
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
                "fields": lambda street, house_number, address_suffix="", **_: {
                    "Ort": street[0].upper(),
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
                    "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
                },
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        # The feed appends a variable frequency/size suffix to some summaries
        # (e.g. "Restmuell 7-taeglich", "Grossmuellbehaelter 1100 L"); the
        # legacy source's icon lookup used only the first word
        # (``d[1].split(" ")[0]``) for the same reason. Mirror that here so
        # every variant still resolves to its canonical type.
        clean=lambda label: label.split()[0] if label.split() else label,
        type_value_map={
            "Restmuell": GENERAL_WASTE,
            "Biobehaelter": ORGANIC,
            "Papierbehaelter": PAPER,
            "Gelbe": RECYCLABLES,
            "Grossmuellbehaelter": GENERAL_WASTE,
        },
    )

    def __init__(self, street: str, house_number: int, address_suffix: str = ""):
        super().__init__(
            street=street, house_number=house_number, address_suffix=address_suffix
        )
