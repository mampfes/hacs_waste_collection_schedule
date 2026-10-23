import logging
from inspect import Parameter, Signature

from waste_collection_schedule.source.kaw_mainz_bingen_de import Source as KawSource

_LOGGER = logging.getLogger(__name__)
_DEPRECATION_WARNING_LOGGED = False

TITLE = "Abfallwirtschaftsbetrieb LK Mainz-Bingen (Deprecated)"
DESCRIPTION = (
    "Deprecated source for Abfallwirtschaftsbetrieb LK Mainz-Bingen. "
    "Please use KAW Mainz und Mainz-Bingen AöR instead."
)
URL = KawSource.URL
TEST_CASES = {
    "Stadt Ingelheim Ingelheim Süd": {
        "bezirk": "Stadt Ingelheim",
        "ort": "Ingelheim Süd",
    },
    "Verbandsgemeinde Rhein-Selz, Mommenheim": {
        "bezirk": "Verbandsgemeinde Rhein-Selz",
        "ort": "mOmMenHeiM",
    },
    "Stadt Bingen, Bingen-Stadt": {
        "bezirk": "Stadt Bingen",
        "ort": "Bingen-Stadt",
    },
}


class Source:
    def __init__(self, bezirk: str, ort: str, strasse: str | None = None):
        global _DEPRECATION_WARNING_LOGGED

        self._source = KawSource(bezirk=bezirk, ort=ort, strasse=strasse)
        if not _DEPRECATION_WARNING_LOGGED:
            _LOGGER.warning(
                "awb_mainz_bingen_de is deprecated, please use kaw_mainz_bingen_de instead"
            )
            _DEPRECATION_WARNING_LOGGED = True

    def fetch(self):
        return self._source.fetch()


Source.__init__.__signature__ = Signature(
    parameters=[
        Parameter("self", Parameter.POSITIONAL_OR_KEYWORD),
        Parameter("bezirk", Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter("ort", Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
    ]
)
