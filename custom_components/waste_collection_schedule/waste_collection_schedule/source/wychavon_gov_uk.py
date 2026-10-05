from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service import RoundLookup

# Deprecated in favour of roundlookup_uk (council "Wychavon"). Kept working
# until it is removed.


@final
class Source(BaseSource):
    TITLE = "Wychavon District Council (Deprecated)"
    DESCRIPTION = "Source for Wychavon District Council."
    URL = "https://wychavon.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "10013938132": {"uprn": 10013938132},
        "10013938131": {"uprn": "10013938131"},
        "100121280854": {"uprn": 100121280854},
    }

    PARAMS = (uprn(),)

    WASTE_TYPES: ClassVar[list] = RoundLookup.WASTE_TYPES

    HOWTO: ClassVar[dict] = {
        "en": (
            "Deprecated: use the roundlookup_uk source (council Wychavon) instead. "
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details."
        ),
    }

    retrieve = RoundLookup.retriever("Wychavon")
    parse = RoundLookup.PARSE
    preprocess = staticmethod(RoundLookup.rows)
    transform = RoundLookup.TRANSFORM
