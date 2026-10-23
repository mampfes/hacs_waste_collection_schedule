from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality
from waste_collection_schedule.service.KawMainzBingen import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "KAW Mainz und Mainz-Bingen AöR"
    DESCRIPTION = "Source for KAW Mainz und Mainz-Bingen AöR."
    URL = "https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender"
    COUNTRY = "de"
    TEST_CASES: ClassVar[dict] = {
        "Stadt Ingelheim Ingelheim Süd": {
            "bezirk": "Stadt Ingelheim",
            "ort": "Ingelheim Süd",
        },
        "Verbandsgemeinde Rhein-Selz, Mommenheim": {
            "bezirk": "Verbandsgemeinde Rhein-Selz",
            "ort": "mOmMenHeiM",
        },
        "Stadt Bingen, Bingen-Stadt": {"bezirk": "Stadt Bingen", "ort": "Bingen-Stadt"},
    }
    PARAMS = (
        district("bezirk"),
        municipality("ort"),
    )
    # BaseSource still accepts a saved legacy `strasse` kwarg. The current API
    # only uses district and municipality, so do not offer an unused UI field.

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Glass": wt.GLASS,
            "Biomüll": wt.ORGANIC,
            "Papier": wt.PAPER,
            "Papiertonne": wt.PAPER,
            "Gelbe/r Tonne / Sack": wt.RECYCLABLES,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Problemmüll": wt.HAZARDOUS,
            "Problemmüllbus": wt.HAZARDOUS,
        },
        location_key="location",
        description_key="description",
    )
