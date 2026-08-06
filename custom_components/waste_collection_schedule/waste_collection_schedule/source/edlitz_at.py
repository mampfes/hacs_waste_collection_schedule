from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.edlitz.at"


@final
class Source(BaseSource):
    TITLE = "Marktgemeinde Edlitz"
    DESCRIPTION = "Source for Marktgemeinde Edlitz, AT"
    URL = "https://edlitz.at"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestSource": {},
    }

    PARAMS = ()

    # Edlitz's municipal calendar happens to hold nothing but the waste rounds
    # today, so the unfiltered request returned the right answer by luck.
    # These are the ids its own Abfuhrtermine page uses, so the day the
    # municipality adds an event the source keeps reading the waste calendar.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "bdatum": "31.12.9999",
            "detailonr": "217108623",
            "menuonr": "218770302",
            "typids": "217108623",
        },
    )
    parse = RiSKommunalParser()

    # Gelber Sack and Restmüll auto-resolve via the shared vocabulary.
    # Biomüllabfuhr is the Biomüll/organic-waste round under its "-abfuhr"
    # (collection) name, so it maps to ORGANIC; "Papier Tonne" (with a
    # space) misses the "papiertonne" alias and needs an explicit entry;
    # "Grüne Tonne" corresponds to the legacy Icons.RECYCLING classification
    # (RECYCLABLES.icon is the same mdi:recycle glyph); "Restmüll mit
    # Panoramastraße" is a location-suffixed residual-waste label. The last
    # two were in the legacy ICON_MAP but not observed in the live window
    # tested; kept for parity in case they appear on other dates.
    transform = ICSTransformer(
        type_value_map={
            "Biomüllabfuhr": wt.ORGANIC,
            "Papier Tonne": wt.PAPER,
            "Grüne Tonne": wt.RECYCLABLES,
            "Restmüll mit Panoramastraße": wt.GENERAL_WASTE,
        },
    )
