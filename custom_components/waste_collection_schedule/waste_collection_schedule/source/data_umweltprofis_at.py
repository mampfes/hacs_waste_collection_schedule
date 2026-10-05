"""Umweltprofis (umweltprofis.at).

Demonstrates: an address-resolving pipeline source for a provider that has no
export URL, only a web module. ``UmweltprofisRetriever`` walks the module's
district, municipality, street and house-number lookups from the names the user
configured, submits the choice and reads the schedule page the module answers
with; ``UmweltprofisParser`` pairs that page's type and date columns into the
``(date, label)`` tuples ``ICSTransformer`` resolves through the shared
multilingual vocabulary.

This replaced the ``data.umweltprofis.at`` personal ICS/XML export (``url`` /
``xmlurl``), which the provider shut down: the host has answered ``503`` since
at least August 2026 and its keys can no longer be issued.

No ``type_value_map``: the shared resolver already recognises this provider's
labels.
"""

from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    district,
    house_number,
    street,
)
from waste_collection_schedule.service.Umweltprofis import (
    UmweltprofisParser,
    UmweltprofisRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Umweltprofis"
    DESCRIPTION = "Source for Umweltprofis"
    URL = "https://www.umweltprofis.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Rohrbach": {
            "district": "Rohrbach",
            "city": "Aigen-Schlägl",
            "street": "Almesbergerweg",
            "house_number": "1",
        },
        "Gmunden": {
            "district": "Gmunden",
            "city": "Altmünster",
            "street": "Abteistraße",
            "house_number": "1",
        },
        "Vöcklabruck": {
            "district": "Vöcklabruck",
            "city": "Ampflwang im Hausruckwald",
            "street": "Aigen",
            "house_number": "1",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as it is offered at "
            "https://www.umweltprofis.at/allgemein/module/wann_wird_mein_abfall_abgeholt.html: "
            "district (Bezirk), municipality, street and house number. Where "
            "a type is offered at several intervals (for example Restabfall "
            "2- or 4-weekly), the first one the page lists is used."
        ),
        "de": (
            "Geben Sie Ihre Adresse genau so an, wie sie unter "
            "https://www.umweltprofis.at/allgemein/module/wann_wird_mein_abfall_abgeholt.html "
            "angeboten wird: Bezirk, Gemeinde, Straße und Hausnummer. Wird "
            "eine Abfallart in mehreren Intervallen angeboten (z. B. Restabfall "
            "2- oder 4-wöchentlich), wird das erste auf der Seite genannte "
            "verwendet."
        ),
    }

    PARAMS = (district(), city(), street(), house_number())

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = UmweltprofisRetriever()
    parse = UmweltprofisParser()
    transform = ICSTransformer()
