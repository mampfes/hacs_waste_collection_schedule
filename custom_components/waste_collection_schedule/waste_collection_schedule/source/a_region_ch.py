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

TITLE = "A-Region"
DESCRIPTION = "Source for A-Region, Switzerland waste collection."
URL = "https://www.a-region.ch"
COUNTRY = "ch"

TEST_CASES = {
    "Andwil": {"municipality": "Andwil"},
    "Rorschach": {"municipality": "Rorschach", "district": "Unteres Stadtgebiet"},
    "Wolfhalden": {"municipality": "Wolfhalden"},
    "Speicher": {"municipality": "Speicher"},
}


MUNICIPALITIES = {
    "Andwil": "/index.php?ref=search&refid=13875680&apid=5011362",
    "Appenzell": "/index.php?ref=search&refid=13875680&apid=7502696",
    "Berg": "/index.php?ref=search&refid=13875680&apid=3106981",
    "Bühler": "/index.php?ref=search&refid=13875680&apid=4946039",
    "Eggersriet": "/index.php?ref=search&refid=13875680&apid=7419807",
    "Gais": "/index.php?ref=search&refid=13875680&apid=7001813",
    "Gaiserwald": "/index.php?ref=search&refid=13875680&apid=9663627",
    "Goldach": "/index.php?ref=search&refid=13875680&apid=1577133",
    "Grub": "/index.php?ref=search&refid=13875680&apid=10619556",
    "Heiden": "/index.php?ref=search&refid=13875680&apid=13056683",
    "Herisau": "/index.php?ref=search&refid=13875680&apid=10697513",
    "Horn": "/index.php?ref=search&refid=13875680&apid=7102181",
    "Hundwil": "/index.php?ref=search&refid=13875680&apid=7705668",
    "Häggenschwil": "/index.php?ref=search&refid=13875680&apid=1590277",
    "Lutzenberg": "/index.php?ref=search&refid=13875680&apid=301262",
    "Muolen": "/index.php?ref=search&refid=13875680&apid=9000564",
    "Mörschwil": "/index.php?ref=search&refid=13875680&apid=12765590",
    "Rehetobel": "/index.php?ref=search&refid=13875680&apid=15824437",
    "Rorschach": "/index.php?ref=search&refid=13875680&apid=7773833",
    "Rorschacherberg": "/index.php?ref=search&refid=13875680&apid=13565317",
    "Schwellbrunn": "/index.php?ref=search&refid=13875680&apid=10718116",
    "Schönengrund": "/index.php?ref=search&refid=13875680&apid=8373248",
    "Speicher": "/index.php?ref=search&refid=13875680&apid=11899879",
    "Stein": "/index.php?ref=search&refid=13875680&apid=9964399",
    "Steinach": "/index.php?ref=search&refid=13875680&apid=16358152",
    "Teufen": "/index.php?ref=search&refid=13875680&apid=662596",
    "Thal": "/index.php?ref=search&refid=13875680&apid=5087375",
    "Trogen": "/index.php?ref=search&refid=13875680&apid=14835149",
    "Tübach": "/index.php?ref=search&refid=13875680&apid=6762782",
    "Untereggen": "/index.php?ref=search&refid=13875680&apid=5661056",
    "Urnäsch": "/index.php?ref=search&refid=13875680&apid=1891722",
    "Wald": "/index.php?ref=search&refid=13875680&apid=4214292",
    "Waldkirch": "/index.php?ref=search&refid=13875680&apid=15180335",
    "Waldstatt": "/index.php?ref=search&refid=13875680&apid=15561367",
    "Wittenbach": "/index.php?ref=search&refid=13875680&apid=13277954",
    "Wolfhalden": "/index.php?ref=search&refid=13875680&apid=5642491",
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

    retrieve = ARegionRetriever(service="a_region", municipalities=MUNICIPALITIES)
    parse = ARegionIcsParser()
    transform = ICSTransformer(type_value_map=TYPE_VALUE_MAP)
