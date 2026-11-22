"""Bonn (bonnorange.de).

Athos "WasteManagementServlet" wizard, the plain German shape (compare
``stadt_bamberg_de``): one field-setting step (``Ort`` is the first letter of
the street, A-Z without umlauts), one ``forward`` step to the result list, and
the iCal download with the Bonn-specific ``ApplicationName``. The servlet is
embedded as an iframe on https://www.bonnorange.de/service/privatpersonen/abfuhrtermine/termine.

"Gelbe Grossbehaelter" (large yellow containers, typically 1,100 l at
apartment blocks) is collected on its own dates, separate from the regular
yellow bin, so it is kept as its own type instead of being folded into
RECYCLABLES; users without such a container can hide it.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.service.AthosWasteManagement import (
    AthosCalendarRequired,
)
from waste_collection_schedule.transformers import ICSTransformer

_SERVLET = "https://www5.bonn.de/WasteManagementBonnOrange/WasteManagementServlet"

_UMLAUTS = str.maketrans({"Ä": "A", "Ö": "O", "Ü": "U"})


def _ort(street: str) -> str:
    """The servlet's ``Ort`` select holds the street's initial (A-Z)."""
    return street.strip()[0].upper().translate(_UMLAUTS)


@final
class Source(BaseSource):
    TITLE = "Bonn (bonnorange)"
    DESCRIPTION = "Source for bonnorange AöR, Bonn."
    URL = "https://www.bonnorange.de"
    COUNTRY = "de"

    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.preserved("Gelbe Großbehälter"),
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Berliner Platz 2": {"street": "Berliner Platz", "house_number": 2},
        "Lievelingsweg 110": {"street": "Lievelingsweg", "house_number": 110},
    }

    PARAMS = (
        street(),
        house_number(),
        text_field("address_suffix", "Address suffix", default=""),
    )

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street and house number exactly as listed in the "
        "bonnorange collection calendar: "
        "https://www.bonnorange.de/service/privatpersonen/abfuhrtermine/termine",
        "de": "Straße und Hausnummer genau so eingeben, wie sie im Abfuhrkalender "
        "von bonnorange erscheinen: "
        "https://www.bonnorange.de/service/privatpersonen/abfuhrtermine/termine",
    }

    retrieve = AthosWasteManagementRetriever(
        url=_SERVLET,
        initial_params={"SubmitAction": "wasteDisposalServices", "InFrameMode": "TRUE"},
        steps=[
            {
                "submit_action": "CITYCHANGED",
                "fields": lambda street, house_number, address_suffix="", **_: {
                    "Ort": _ort(street),
                    "Strasse": street.strip(),
                    "Hausnummer": str(house_number),
                    "Hausnummerzusatz": address_suffix,
                },
            },
            {"submit_action": "forward"},
            {
                "submit_action": "filedownload_ICAL",
                "fields": lambda **_: {
                    "ApplicationName": "com.athos.kd.bonn.abfuhrtermine.AbfuhrTerminModel",
                },
                "validate": AthosCalendarRequired(
                    "street", "house_number", "address_suffix"
                ),
            },
        ],
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restabfallbehaelter": wt.GENERAL_WASTE,
            "Bioabfallbehaelter": wt.ORGANIC,
            "Papierbehaelter": wt.PAPER,
            "Gelbe Behaelter": wt.RECYCLABLES,
            "Gelbe Grossbehaelter": wt.preserved("Gelbe Großbehälter"),
            "Sperrmuell": wt.BULKY_WASTE,
            "Weihnachtsbaeume": wt.GARDEN_WASTE,
        }
    )
