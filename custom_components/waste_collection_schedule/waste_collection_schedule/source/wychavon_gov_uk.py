import logging

from waste_collection_schedule.source.roundlookup_uk import \
    Source as Roundlookup  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)
TITLE = "Wychavon District Council (Deprecated)"
DESCRIPTION = "Source for Wychavon District Council."
URL = "https://wychavon.gov.uk/"
TEST_CASES = {
    "10013938132": {"uprn": 10013938132},
    "10013938131": {"uprn": "10013938131"},
    "100121280854": {"uprn": 100121280854},
}


ICON_MAP = {
    "Non-recyclable": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


class Source(Roundlookup):
    def __init__(self, uprn: str | int):
        super().__init__(uprn, "Wychavon")
        _LOGGER.warning(
            "This source is deprecated, please use the 'roundlookup_uk' source instead"
        )
