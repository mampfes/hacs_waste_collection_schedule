from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer

_BASE = "https://www.123abfallkalender.de/abfallkalender/rpecasvg-ebsdorfergrund"

# District name -> slug of its calendar page.
_DISTRICTS = {
    "Beltershausen": "1-beltershausen",
    "Dreihausen": "2-dreihausen",
    "Ebsdorf": "3-ebsdorf",
    "Frauenberg": "4-frauenberg",
    "Hachborn": "5-hachborn",
    "Heskem": "6-heskem",
    "Ilschhausen": "7-ilschhausen",
    "Leidenhofen": "8-leidenhofen",
    "Mölln": "9-molln",
    "Rauischholzhausen": "10-rauischholzhausen",
    "Roßberg": "11-rossberg",
    "Wermertshausen": "12-wermertshausen",
    "Wittelsberg": "13-wittelsberg",
}


@final
class Source(BaseSource):
    TITLE = "123abfallkalender"
    DESCRIPTION = "Source script for 123abfallkalender.de (Ebsdorfergrund)"
    URL = "https://www.123abfallkalender.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {name: {"district": name} for name in _DISTRICTS}

    PARAMS = (dropdown("district", list(_DISTRICTS)),)

    REGIONS = tuple(
        region(name, url=f"{_BASE}/{slug}", district=name)
        for name, slug in _DISTRICTS.items()
    )

    HOWTO: ClassVar[dict] = {
        "en": "Select your district from the list.",
        "de": "Wählen Sie Ihren Ortsteil aus der Liste.",
    }

    retrieve = retrievers.Request(
        lambda district, **_: f"{_BASE}/{_DISTRICTS[district]}.ics",
        params={"alert": "never"},
    )
    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Biomüll": wt.ORGANIC,
            "Altpapier": wt.PAPER,
            "Gelbe Tonne": wt.RECYCLABLES,
            "MR Sondermüll": wt.HAZARDOUS,
            "EBS Sondermüll": wt.HAZARDOUS,
            "Praxis GmbH": wt.OTHER,
        },
        carry_raw_label=True,
    )
