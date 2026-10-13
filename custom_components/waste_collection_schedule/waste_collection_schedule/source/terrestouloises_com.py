from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.regions import Region
from waste_collection_schedule.service.TerresTouloisesCalendar import (
    COMMUNES,
    CalendarParser,
    calendar_retriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Terres Touloises"
    DESCRIPTION = "Source script for terrestouloises.com (Communauté de Communes Terres Touloises, France)"
    URL = "https://www.terrestouloises.com"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Bois-de-Haye": {"commune": "Bois-de-Haye"},
        "Ansauville (self-service bins)": {"commune": "Ansauville"},
        "Ecrouves (inline holiday exception)": {"commune": "Ecrouves"},
        "Gondreville": {"commune": "Gondreville"},
    }
    REGIONS = tuple(
        Region(
            title=commune,
            params={"commune": commune},
            url="https://www.terrestouloises.com",
        )
        for commune in COMMUNES
    )
    PARAMS = (municipality("commune"),)

    retrieve = calendar_retriever
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Ordures ménagères": wt.GENERAL_WASTE,
            "Emballages": wt.RECYCLABLES,
        },
    )
