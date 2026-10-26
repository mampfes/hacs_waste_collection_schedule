from typing import ClassVar, final

from waste_collection_schedule import preprocessors
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.source.kaw_mainz_bingen_de import Source as KawSource


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaftsbetrieb LK Mainz-Bingen (Deprecated)"
    DESCRIPTION = "Deprecated source for Abfallwirtschaftsbetrieb LK Mainz-Bingen. Please use KAW Mainz und Mainz-Bingen AöR instead."
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
    URL = KawSource.URL
    COUNTRY = "de"
    TEST_CASES = {
        **TEST_CASES,
        "Saved legacy street": {
            "bezirk": "Stadt Bingen",
            "ort": "Bingen-Stadt",
            "strasse": "Hafenstraße",
        },
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown district": {"bezirk": "zzzznotreal", "ort": "Mommenheim"}
    }
    PARAMS = KawSource.PARAMS
    HOWTO: ClassVar[dict] = {
        "en": "This legacy source name remains deprecated; prefer kaw_mainz_bingen_de. Existing bezirk, ort and saved strasse arguments remain accepted. The current KAW API only needs district and municipality. Collection dates and canonical waste types are unchanged."
    }
    retrieve = KawSource.retrieve
    parse = KawSource.parse
    preprocess = preprocessors.Compose(
        preprocessors.LogOnce(
            "awb_mainz_bingen_de is deprecated; use kaw_mainz_bingen_de instead",
            logger=__name__,
        ),
        KawSource.preprocess,
    )
    transform = KawSource.transform
