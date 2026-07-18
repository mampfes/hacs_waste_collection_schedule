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

TITLE = "ZAB Bazenheid"
DESCRIPTION = "Source for Zweckverband Abfallverwertung Bazenheid (ZAB)"
URL = "https://zab.citymobile.ch"
COUNTRY = "ch"

TEST_CASES = {
    "Wängi": {"municipality": "Wängi"},
    "Sirnach": {"municipality": "Sirnach", "district": "Papier und Karton Sirnach"},
    "Eschlikon": {
        "municipality": "Eschlikon",
        "district": "Kehrichtsammlung Eschlikon",
    },
}

MUNICIPALITIES = {
    "Aadorf": "/index.php?apid=9726871&apparentid=2326631",
    "Bettwiesen": "/index.php?apid=12085057&apparentid=2326631",
    "Bichelsee-Balterswil": "/index.php?apid=11535568&apparentid=2326631",
    "Braunau": "/index.php?apid=12198875&apparentid=2326631",
    "Bütschwil-Ganterschwil": "/index.php?apid=8392002&apparentid=2326631",
    "Degersheim": "/index.php?apid=16588818&apparentid=2326631",
    "Ebnat-Kappel": "/index.php?apid=6034813&apparentid=2326631",
    "Eschlikon": "/index.php?apid=4813431&apparentid=2326631",
    "Fischingen": "/index.php?apid=9382046&apparentid=2326631",
    "Flawil": "/index.php?apid=8527584&apparentid=2326631",
    "Gossau": "/index.php?apid=3414158&apparentid=2326631",
    "Jonschwil": "/index.php?apid=5841810&apparentid=2326631",
    "Kirchberg": "/index.php?apid=13015555&apparentid=2326631",
    "Lichtensteig": "/index.php?apid=6846579&apparentid=2326631",
    "Lütisburg": "/index.php?apid=13024565&apparentid=2326631",
    "Mosnang": "/index.php?apid=782123&apparentid=2326631",
    "Münchwilen": "/index.php?apid=312606&apparentid=2326631",
    "Neckertal": "/index.php?apid=2949770&apparentid=2326631",
    "Nesslau": "/index.php?apid=15203333&apparentid=2326631",
    "Niederbüren": "/index.php?apid=9191724&apparentid=2326631",
    "Niederhelfenschwil": "/index.php?apid=10484022&apparentid=2326631",
    "Oberbüren": "/index.php?apid=3972728&apparentid=2326631",
    "Oberuzwil": "/index.php?apid=4440141&apparentid=2326631",
    "Rickenbach": "/index.php?apid=5878077&apparentid=2326631",
    "Sirnach": "/index.php?apid=10773272&apparentid=2326631",
    "Tobel-Tägerschen": "/index.php?apid=13036162&apparentid=2326631",
    "Uzwil": "/index.php?apid=6575733&apparentid=2326631",
    "Wängi": "/index.php?apid=1811155&apparentid=2326631",
    "Wattwil": "/index.php?apid=6490334&apparentid=2326631",
    "Wil": "/index.php?apid=9385302&apparentid=2326631",
    "Wilen": "/index.php?apid=9820263&apparentid=2326631",
    "Wuppenau": "/index.php?apid=9826075&apparentid=2326631",
    "Zuzwil": "/index.php?apid=215802&apparentid=2326631",
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

    retrieve = ARegionRetriever(service="zab", municipalities=MUNICIPALITIES)
    parse = ARegionIcsParser()
    transform = ICSTransformer(type_value_map=TYPE_VALUE_MAP)
