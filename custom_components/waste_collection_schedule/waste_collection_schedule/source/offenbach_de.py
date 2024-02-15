import logging

from waste_collection_schedule.source.insert_it_de import \
    Source as InsertItSource

_LOGGER = logging.getLogger(__name__)

TITLE = "Abfallkalender Offenbach am Main (deprecated)"
DESCRIPTION = "Source für Abfallkalender Offenbach (deprecated)"
URL = "https://www.offenbach.de"

TEST_CASES = {
    "offenbach": {"f_id_location": 7036},  # KaiserStraße 1
}


class Source(InsertItSource):
    def __init__(self, f_id_location):
        _LOGGER.warning(
            "offenbach_de source is deprecated, please use insert_it_de as new source. More info: https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/insert_it_de.md"
        )
        super().__init__("Offenbach", location_id=f_id_location)
