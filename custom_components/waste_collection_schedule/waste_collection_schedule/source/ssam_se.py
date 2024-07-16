from datetime import datetime
import json
import logging

import requests
#from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from .edpevent_se import Source as EdpEventSource # type: ignore[attr-defined]

TITLE = "SSAM (Deprecated)"
DESCRIPTION = "Deprecated, please use edpevent_se instead."
URL = "https://ssam.se"
TEST_CASES = {
    "Home": {"street_address": "Asteroidvägen 1, Växjö"},
    "Bostadsrätt": {"street_address": "Långa Gatan 29 -81, Växjö"},
    "Slambrunn": {"street_address": "Svanebro Ormesberga, Ör"},
}
_LOGGER = logging.getLogger(__name__)


class Source(EdpEventSource):
    def __init__(self, street_address):
        super().__init__(street_address, service_provider="ssam")
        # Log a warning message indicating that this source is deprecated
        _LOGGER.warning("The SSAM source is deprecated, please use edpevent_se instead.")