import logging

# from waste_collection_schedule import Collection
from .edpevent_se import Source as EdpEventSource

TITLE = "Uppsala Vatten och Avfall AB (Deprecated)"
DESCRIPTION = "Deprecated, please use edpevent_se instead."
URL = "https://www.uppsalavatten.se"

# Init logger
_LOGGER = logging.getLogger(__name__)

TEST_CASES = {
    "Test1": {
        "street": "SADELVÄGEN 1",
    },
    "Test2": {
        "street": "BJÖRKLINGE-GRÄNBY 33",
    },
    "Test3": {
        "street": "BJÖRKLINGE-GRÄNBY 20",
    },
}


class Source(EdpEventSource):
    def __init__(self, street):
        super().__init__(street, service_provider="uppsalavatten")
        # Log a warning message indicating that this source is deprecated
        _LOGGER.warning(
            "The Uppsala Vatten och Avfall AB source is deprecated, please use edpevent_se instead"
        )
