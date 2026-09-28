from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Dundee City Council"
    DESCRIPTION = "Source script for dundeecity.gov.uk"
    URL = "https://www.dundeecity.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    REGIONS = (region("Dundee MyBins", url="https://www.dundee-mybins.co.uk"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.GLASS,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_1": {"uprn": 9059046613},
        "Test_2": {"uprn": "9059082280"},
        "Test_3": {"uprn": 9059060343},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://www.dundee-mybins.co.uk/get_calendar.php",
        params=lambda uprn, **_: {"rn": uprn},
    )
    parse = JsonParser()
    transform = JsonTransformer(
        date_key="start",
        type_key="title",
        type_value_map={
            "Grey Bin": wt.GENERAL_WASTE,
            "Brown Bin": wt.ORGANIC,
            "Green Bin": wt.GLASS,
            "Burgundy Bin": wt.RECYCLABLES,
            "Blue Bin": wt.PAPER,
        },
    )
