from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, uprn
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.FccEnvironment import (
    SERVICES,
    FccEnvironmentParser,
    FccEnvironmentRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "non-recyclable waste": wt.GENERAL_WASTE,
    "refuse": wt.GENERAL_WASTE,
    "recycling": wt.RECYCLABLES,
    "garden": wt.GARDEN_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "FCC Environment"
    DESCRIPTION = (
        "Consolidated source for waste collection services for ~60 local "
        "authorities. Currently supports: West Devon (Generic Provider), "
        "South Hams (Generic Provider), Market Harborough (Custom Provider)"
    )
    URL = "https://fccenvironment.co.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region(
            "Harborough District Council",
            url="https://harborough.gov.uk",
            region="harborough",
        ),
        region(
            "South Hams District Council",
            url="https://southhams.gov.uk/",
            region="southhams",
        ),
        region(
            "West Devon Borough Council",
            url="https://www.westdevon.gov.uk/",
            region="westdevon",
        ),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "14_LE16_9QX": {"uprn": "100030491624"},  # region omitted: default value
        "4_LE16_9QX": {"uprn": "100030491614", "region": "harborough"},
        "16_LE16_7NA": {"uprn": "100030493289", "region": "harborough"},
        "10_LE16_8ER": {"uprn": "200001136341", "region": "harborough"},
        "9_PL20_7SH": {"uprn": "10001326315", "region": "westdevon"},
        "3_PL20_7RY": {"uprn": "10001326041", "region": "westdevon"},
        "2_PL21_9BN": {"uprn": "100040279446", "region": "southhams"},
        "4_SL21_0HZ": {"uprn": "100040281987", "region": "southhams"},
    }

    PARAMS = (
        uprn(),
        dropdown("region", list(SERVICES), default="harborough"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and choose your council as the region (harborough, southhams or "
            "westdevon; Harborough is the default)."
        ),
    }

    retrieve = FccEnvironmentRetriever()
    parse = FccEnvironmentParser(_TYPE_MAP)
    transform = RowTransformer(type_value_map=_TYPE_MAP)
