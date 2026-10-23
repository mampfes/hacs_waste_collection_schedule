"""Sector 27 Müllkalender (muellkalender.sector27.de), Kreis Recklinghausen.

The provider's Livewire calendar is driven by
:class:`~waste_collection_schedule.service.Sector27.Sector27Retriever`; a
pickup is only a coloured square, so the waste type comes from its colour.
"""

from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.Sector27 import (
    Sector27Parser,
    Sector27Retriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Sector 27 - Datteln, Marl, Oer-Erkenschwick"
    DESCRIPTION = "Source for Muellkalender in Kreis RE."
    URL = "https://muellkalender.sector27.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Datteln": {"city": "Datteln", "street": "Am Bahnhof"},
        "Datteln Im Overkamp": {"city": "Datteln", "street": "Im Overkamp"},
        "Datteln range street": {
            "city": "Datteln",
            "street": "Ahsener Straße 113 - 161 (ungerade)",
        },
        "Marl": {"city": "Marl", "street": "Ahornweg"},
        "Oer-Erkenschick": {
            "city": "Oer-Erkenschwick",
            "street": "An der Zechenbahn",
        },
    }

    PARAMS = (city("city"), street("street"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Choose Datteln, Marl or Oer-Erkenschwick and enter your street "
            "exactly as it is listed on https://muellkalender.sector27.de "
            "(for split streets including the house number range, e.g. "
            "'Ahsener Straße 113 - 161 (ungerade)')."
        ),
        "de": (
            "Wähle Datteln, Marl oder Oer-Erkenschwick und gib die Straße so "
            "ein, wie sie auf https://muellkalender.sector27.de aufgeführt ist "
            "(bei geteilten Straßen mit Hausnummernbereich, z. B. "
            "'Ahsener Straße 113 - 161 (ungerade)')."
        ),
    }

    retrieve = Sector27Retriever(rollover_month=9)
    parse = Sector27Parser()

    # The calendar's legend: black residual, brown bio, blue paper, yellow bin.
    transform = ICSTransformer(
        type_value_map={
            "bg-black": wt.GENERAL_WASTE,
            "bg-yellow-700": wt.ORGANIC,
            "bg-blue-700": wt.PAPER,
            "bg-yellow-400": wt.RECYCLABLES,
        },
    )
