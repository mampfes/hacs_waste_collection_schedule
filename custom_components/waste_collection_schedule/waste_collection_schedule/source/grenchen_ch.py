import logging

from waste_collection_schedule.source.localcities_ch import (
    Source as LocalcitiesSource,  # type: ignore[attr-defined]
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Grenchen (CH)"
DESCRIPTION = "Source for waste collection in Grenchen, Switzerland. Deprecated: use localcities_ch instead."
URL = "https://www.grenchen.ch"
COUNTRY = "ch"

TEST_CASES = {
    "Zone Ost": {"zone": "Zone Ost"},
    "Zone West": {"zone": "Zone West"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "This source is deprecated. Please use 'localcities.ch' instead with municipality='grenchen' and municipality_id='3533'.",
    "de": "Diese Quelle ist veraltet. Bitte verwenden Sie 'localcities.ch' mit municipality='grenchen' und municipality_id='3533'.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "Collection zone (Zone Ost or Zone West)",
    },
    "de": {
        "zone": "Abfuhrzone (Zone Ost oder Zone West)",
    },
}


class Source(LocalcitiesSource):
    def __init__(self, zone: str):
        _LOGGER.warning(
            "grenchen_ch source is deprecated, please use localcities_ch instead. "
            "More info: https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/localcities_ch.md"
        )
        super().__init__(municipality="grenchen", municipality_id="3533", zone=zone)
