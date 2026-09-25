from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.AbfallnaviDe import (
    AbfallnaviParser,
    AbfallnaviRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Tonnenticker Pro is the regio iT AbfallNavi app of the "krwaf" service (AWG
# Kreis Warendorf and GEG Kreis Gütersloh), the same platform abfallnavi_de
# covers. The service id is pinned here, so only city and street are asked for.
_SERVICE = "krwaf"


@final
class Source(BaseSource):
    TITLE = "Tonnenticker Pro"
    DESCRIPTION = "Source for Tonnenticker Pro (RegioIT) waste collection schedules."
    URL = "https://www.regioit.de"
    COUNTRY = "de"
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Steinhagen - Waldbadstrasse": {
            "city": "Steinhagen",
            "street": "Waldbadstraße (Bahnhofstr. bis Rote Erde)",
        },
        "Warendorf - Agnes-Miegel-Weg": {
            "city": "Warendorf",
            "street": "Agnes-Miegel-Weg",
        },
    }

    # An unknown street is reported against the "street" field, with the
    # city's streets as suggestions.
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"city": "Warendorf", "street": "Keine Straße"},
    }

    PARAMS = (city(), street())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your municipality, then use the street name shown in the "
            "Tonnenticker Pro app or on the provider's website."
        ),
        "de": (
            "Wählen Sie Ihren Ort und verwenden Sie den Straßennamen aus der "
            "Tonnenticker Pro App oder von der Website des Anbieters."
        ),
    }

    retrieve = AbfallnaviRetriever(service="service", city="city", street="street")
    parse = AbfallnaviParser()
    # Standard labels resolve via the shared vocabulary; these are AWG's own.
    # The provider's label is kept as the description, so the several paper
    # collectors and the residual-waste rhythms stay distinguishable.
    transform = ICSTransformer(
        type_value_map={
            "Komposttonne": wt.ORGANIC,
            "Restabfall 1,1 cbm": wt.GENERAL_WASTE,
            "Restabfall 1,1 cbm 2-wöchentlich": wt.GENERAL_WASTE,
            "Altpapier-Sammlung AWG": wt.PAPER,
            "Altpapier-Sammlung Kolping Warendorf": wt.PAPER,
            "Altpapier-Sammlung Kolping Freckenhorst": wt.PAPER,
            # a mobile document-shredding appointment, not a bin
            "Aktenvernichter": wt.OTHER,
            # the recycling centre's opening days, not a collection
            "Wertstoffhof": None,
        },
        carry_raw_label=True,
    )

    def __init__(self, city: str, street: str):
        super().__init__(service=_SERVICE, city=city, street=street)
