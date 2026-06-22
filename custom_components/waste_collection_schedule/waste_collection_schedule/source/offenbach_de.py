import logging
from typing import final

from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.source.insert_it_de import Source as InsertItSource

_LOGGER = logging.getLogger(__name__)


@final
class Source(InsertItSource):
    """Deprecated alias for the Offenbach municipality of insert_it_de.

    Kept so existing ``offenbach_de`` configurations keep working; new
    configurations should use ``insert_it_de`` with municipality "Offenbach".
    """

    TITLE = "Abfallkalender Offenbach am Main (deprecated)"
    DESCRIPTION = "Source für Abfallkalender Offenbach (deprecated)"
    URL = "https://www.offenbach.de"
    COUNTRY = "de"

    TEST_CASES = {
        "offenbach": {"f_id_location": 7036},  # Kaiserstraße 1
    }

    # The location id flows through to the parent as ``location_id``; declared
    # optional so validate() does not require the renamed field (the parent
    # stores ``location_id``). REGIONS is empty: this alias is not separately
    # listed, the insert_it_de Offenbach region is the canonical listing.
    PARAMS = [text_field("f_id_location", "Standort ID", optional=True)]
    REGIONS: list = []

    def __init__(self, f_id_location):
        _LOGGER.warning(
            "offenbach_de source is deprecated, please use insert_it_de as new "
            "source. More info: https://github.com/mampfes/"
            "hacs_waste_collection_schedule/blob/master/doc/source/insert_it_de.md"
        )
        super().__init__("Offenbach", location_id=f_id_location)
