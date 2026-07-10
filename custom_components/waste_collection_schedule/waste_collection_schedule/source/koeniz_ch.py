from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, municipality
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.A_region_ch import (
    TYPE_VALUE_MAP,
    ARegionIcsParser,
    ARegionRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

TITLE = "Köniz"
DESCRIPTION = "Source for Köniz"
URL = "https://koeniz.citymobile.ch"
COUNTRY = "ch"

TEST_CASES = {
    "Wabern": {"municipality": "Wabern"},
    "Spiegel": {"municipality": "Spiegel"},
    "Liebefeld": {"municipality": "Liebefeld"},
    "Köniz": {"municipality": "Köniz"},
}

MUNICIPALITIES = {
    "Wabern": "/index.php?apid=2248967&apparentid=6297623",
    "Spiegel": "/index.php?apid=6520219&apparentid=6297623",
    "Liebefeld": "/index.php?apid=6134271&apparentid=6297623",
    "Schliern": "/index.php?apid=9960784&apparentid=6297623",
    "Köniz": "/index.php?apid=6275384&apparentid=6297623",
    "Gasel": "/index.php?apid=7837203&apparentid=6297623",
    "Nieder-/Oberscherli": "/index.php?apid=1169618&apparentid=6297623",
    "Mittelhäusern": "/index.php?apid=15691286&apparentid=6297623",
    "Niederwangen": "/index.php?apid=3535226&apparentid=6297623",
    "Oberwangen": "/index.php?apid=3880894&apparentid=6297623",
    "Thörishaus": "/index.php?apid=16358162&apparentid=6297623",
}


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY

    TEST_CASES = TEST_CASES

    PARAMS = (
        municipality(field="municipality"),
        district(field="district", optional=True),
    )

    REGIONS = tuple(region(m, municipality=m) for m in MUNICIPALITIES)

    retrieve = ARegionRetriever(service="koeniz", municipalities=MUNICIPALITIES)
    parse = ARegionIcsParser()
    transform = ICSTransformer(type_value_map=TYPE_VALUE_MAP)
