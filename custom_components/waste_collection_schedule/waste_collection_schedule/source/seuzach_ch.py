"""Source for Gemeinde Seuzach, Switzerland."""

import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.IWebRegular import (
    AbfalldatenRegularParser,
    AbfalldatenRegularRows,
    abfalldaten_with_regular_retriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Gemeinde Seuzach"
    DESCRIPTION = "Source for waste collection services in Seuzach, Switzerland."
    URL = "https://www.seuzach.ch"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {"Seuzach": {}}

    PARAMS = ()

    HOWTO: ClassVar[dict] = {
        "en": (
            "Seuzach publishes a single municipality-wide collection calendar, "
            "so no address or other argument is required."
        ),
        "de": (
            "Seuzach veröffentlicht einen einzigen gemeindeweiten Abfallkalender, "
            "daher ist kein Argument erforderlich."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
    ]

    # Kehrichtabfuhr and Grünabfuhr are weekly, read from the prose of their
    # detail pages; the other collections are dated on the events page.
    retrieve = abfalldaten_with_regular_retriever("https://www.seuzach.ch/abfalldaten")
    parse = AbfalldatenRegularParser()
    preprocess = AbfalldatenRegularRows()
    transform = ICSTransformer(
        type_value_map={
            "Kehrichtabfuhr": wt.GENERAL_WASTE,
            "Grünabfuhr": wt.GARDEN_WASTE,
            "Letzte Grünabfuhr": wt.GARDEN_WASTE,
            "Häckseldienst": wt.GARDEN_WASTE,
            "Papier- / Kartonsammlung": wt.PAPER,
        },
        # "Letzte Grünabfuhr im Jahr 2026": the year is part of the label.
        clean=lambda label: re.sub(r"\s+im Jahr \d{4}$", "", label.strip()),
    )
