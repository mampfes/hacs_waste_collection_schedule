import logging

from waste_collection_schedule.source.iapp_itouchvision_com import (
    Source as iapp_iTouchVision,
)

_LOGGER = logging.getLogger(__name__)
TITLE = "Deprecated: Buckinghamshire"
DESCRIPTION = "Deprecated: use the iapp_iTouchVision instead."
URL = "https://chiltern.gov.uk"

TEST_CASES = {
    "Test_004": {"uprn": 10094593823},
}


class Source(iapp_iTouchVision):
    def __init__(self, uprn):
        super().__init__(uprn, "BUCKINGHAMSHIRE")
        _LOGGER.warning("This source is deprecated. Use iapp_iTouchVision instead.")
